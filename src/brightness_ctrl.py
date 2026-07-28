"""
brightness_ctrl.py - Control de brillo via protocolo DDC/CI
Comunica con monitores externos a traves de la libreria monitorcontrol.

Multi-monitor:
  Al iniciar, descubre TODOS los monitores DDC/CI compatibles y los expone
  como una lista. La UI permite seleccionar uno individual o "Todos".

Estrategia anti-delay (debounce + worker unico):
  - La UI se actualiza INMEDIATAMENTE desde cache.
  - El comando DDC/CI se envia solo despues de DEBOUNCE_MS ms sin mas cambios.
  - Un unico hilo worker serializa los comandos DDC/CI.
"""
import threading
from typing import Optional, List, Dict

from i18n import t

DEBOUNCE_MS = 80


def _read_luminance(monitor) -> int:
    """Lee el brillo de un monitor, compatible con monitorcontrol v3 y v4."""
    lum = monitor.get_luminance()
    return lum.current_value if hasattr(lum, "current_value") else int(lum)


class MonitorInfo:
    """Datos de un monitor DDC/CI detectado."""

    def __init__(self, index: int, name: str, brightness: int, ddc_ok: bool):
        self.index      = index
        self.name       = name
        self.brightness = brightness
        self.ddc_ok     = ddc_ok

    def __repr__(self):
        status = "OK" if self.ddc_ok else "NO DDC"
        return f"Monitor({self.index}, '{self.name}', {self.brightness}%, {status})"


def _get_edid_monitor_names() -> List[str]:
    """Lee del Registro de Windows los nombres de modelo EDID reales únicamente de monitores ACTIVOS."""
    import ctypes
    from ctypes import wintypes
    import winreg

    class DISPLAY_DEVICE(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("DeviceName", wintypes.WCHAR * 32),
            ("DeviceString", wintypes.WCHAR * 128),
            ("StateFlags", wintypes.DWORD),
            ("DeviceID", wintypes.WCHAR * 128),
            ("DeviceKey", wintypes.WCHAR * 128)
        ]

    names = []
    user32 = ctypes.windll.user32
    i = 0
    while True:
        adapter = DISPLAY_DEVICE()
        adapter.cb = ctypes.sizeof(DISPLAY_DEVICE)
        if not user32.EnumDisplayDevicesW(None, i, ctypes.byref(adapter), 0):
            break

        if adapter.StateFlags & 0x1:  # DISPLAY_DEVICE_ATTACHED_TO_DESKTOP
            j = 0
            while True:
                mon = DISPLAY_DEVICE()
                mon.cb = ctypes.sizeof(DISPLAY_DEVICE)
                if not user32.EnumDisplayDevicesW(adapter.DeviceName, j, ctypes.byref(mon), 0):
                    break
                if mon.StateFlags & 0x1:  # DISPLAY_DEVICE_ACTIVE
                    dev_id = mon.DeviceID
                    friendly_name = ""
                    if dev_id:
                        parts = dev_id.split("\\")
                        if len(parts) >= 3:
                            pnp_code = parts[1]
                            reg_path = rf"SYSTEM\CurrentControlSet\Enum\DISPLAY\{pnp_code}\{parts[2]}"
                            try:
                                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                                # 1. Buscar en EDID
                                try:
                                    edid_key = winreg.OpenKey(key, "Device Parameters")
                                    edid, _ = winreg.QueryValueEx(edid_key, "EDID")
                                    for offset in (54, 72, 90, 108):
                                        block = edid[offset:offset + 18]
                                        if block[0:3] == b'\x00\x00\x00' and block[3] in (0xfc, 0xfe):
                                            name_str = block[5:].decode('latin-1', errors='ignore').split('\n')[0].split('\x00')[0].strip()
                                            if name_str and name_str not in ("Generic PnP Monitor", "Monitor PnP genérico"):
                                                friendly_name = name_str
                                                break
                                except Exception:
                                    pass

                                # 2. Buscar en FriendlyName / DeviceDesc si EDID no dio nombre especifico
                                if not friendly_name:
                                    try:
                                        fname, _ = winreg.QueryValueEx(key, "FriendlyName")
                                        if fname and fname not in ("Generic PnP Monitor", "Monitor PnP genérico"):
                                            friendly_name = fname
                                    except Exception:
                                        pass

                                winreg.CloseKey(key)
                            except Exception:
                                pass

                            # 3. Fallback por PNP ID conocido si es genérico
                            if not friendly_name:
                                if "BOE" in pnp_code.upper() or "INT" in pnp_code.upper():
                                    friendly_name = "Integrated Monitor"
                                elif "LHC" in pnp_code.upper() or "TTN" in pnp_code.upper():
                                    friendly_name = "P2712V"
                                else:
                                    friendly_name = pnp_code

                    if not friendly_name:
                        friendly_name = f"Display {len(names) + 1}"

                    names.append(friendly_name)
                j += 1
        i += 1
    return names


# Valor especial para "aplicar a todos los monitores"
TARGET_ALL = -1


class BrightnessController:
    """
    Controla el brillo de uno o multiples monitores via DDC/CI.

    Atributos publicos:
      monitors:       lista de MonitorInfo (todos los detectados, con y sin DDC/CI)
      ddc_monitors:   lista de MonitorInfo (solo los que responden DDC/CI)
      target_index:   indice del monitor activo, o TARGET_ALL para todos
    """

    def __init__(self):
        self._brightness: int        = 50
        self._pending: int           = 50
        self._lock                   = threading.Lock()
        self._worker_lock            = threading.Lock()
        self._debounce_timer: Optional[threading.Timer] = None
        self._available: bool        = False
        self._error_msg: str         = ""

        self.monitors: List[MonitorInfo]     = []
        self.ddc_monitors: List[MonitorInfo] = []
        self.target_index: int               = TARGET_ALL

        self._initialize()

    # -- Inicializacion -------------------------------------------------------
    def _initialize(self):
        """Descubre todos los monitores y prueba DDC/CI en cada uno."""
        try:
            from monitorcontrol import get_monitors
            raw_monitors = list(get_monitors())
            if not raw_monitors:
                self._error_msg = t("ddc_error_osd")
                print(f"[BrightnessCtrl] {self._error_msg}")
                return

            real_names = _get_edid_monitor_names()
            print(f"[BrightnessCtrl] {len(raw_monitors)} monitor(es) detectados. Nombres EDID: {real_names}")

            for idx, monitor in enumerate(raw_monitors):
                model_str = real_names[idx] if idx < len(real_names) else ""
                if model_str:
                    display_name = f"Monitor {idx + 1} - ({model_str})"
                else:
                    display_name = f"Monitor {idx + 1}"

                try:
                    with monitor as m:
                        brightness = _read_luminance(m)
                        # Intentar obtener nombre especifico VCP si no habia EDID
                        try:
                            caps = str(m.get_vcp_capabilities())
                            if "model(" in caps.lower():
                                start = caps.lower().index("model(") + 6
                                end = caps.index(")", start)
                                model_name = caps[start:end].strip()
                                if model_name and not model_name.lower().startswith("monitor"):
                                    display_name = f"Monitor {idx + 1} - ({model_name})"
                        except Exception:
                            pass

                        info = MonitorInfo(idx, display_name, brightness, ddc_ok=True)
                        self.monitors.append(info)
                        self.ddc_monitors.append(info)
                        print(f"[BrightnessCtrl] Monitor {idx}: '{display_name}' DDC/CI OK -- {brightness}%")

                except Exception as e:
                    info = MonitorInfo(idx, display_name, 0, ddc_ok=False)
                    self.monitors.append(info)
                    print(f"[BrightnessCtrl] Monitor {idx}: '{display_name}' DDC/CI no responde ({e})")

            if self.ddc_monitors:
                self._available = True
                # Usar el primer DDC/CI valido como inicial
                first = self.ddc_monitors[0]
                self._brightness = first.brightness
                self._pending    = first.brightness

                if len(self.ddc_monitors) == 1:
                    # Solo un monitor DDC/CI: seleccionarlo directamente
                    self.target_index = first.index
                else:
                    # Multiples: empezar con "Todos"
                    self.target_index = TARGET_ALL
            else:
                self._error_msg = t("ddc_error_generic")
                print(f"[BrightnessCtrl] {self._error_msg}")

        except ImportError:
            self._error_msg = "Libreria 'monitorcontrol' no instalada."
            print(f"[BrightnessCtrl] {self._error_msg}")
        except Exception as e:
            self._error_msg = f"Error DDC/CI inesperado: {e}"
            print(f"[BrightnessCtrl] {self._error_msg}")

    # -- Propiedades ----------------------------------------------------------
    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def error_message(self) -> str:
        return self._error_msg

    @property
    def current(self) -> int:
        """Brillo en cache del monitor activo (o promedio si es 'Todos')."""
        return self._brightness

    # -- Seleccion de monitor -------------------------------------------------
    def set_target(self, index: int):
        """
        Cambia el monitor objetivo.
        index = TARGET_ALL (-1) para aplicar a todos los DDC/CI.
        index = indice real del monitor para uno especifico.
        """
        self.target_index = index
        # Actualizar cache con el brillo del monitor seleccionado
        if index == TARGET_ALL and self.ddc_monitors:
            self._brightness = self.ddc_monitors[0].brightness
        else:
            for m in self.ddc_monitors:
                if m.index == index:
                    self._brightness = m.brightness
                    break
        self._pending = self._brightness

    def get_target_indices(self) -> List[int]:
        """Devuelve la lista de indices de monitores a los que se aplicara el brillo."""
        if self.target_index == TARGET_ALL:
            return [m.index for m in self.ddc_monitors]
        return [self.target_index]

    # -- API publica ----------------------------------------------------------
    def get_brightness(self) -> int:
        return self._brightness

    def refresh_from_hardware(self):
        """Relee el brillo del monitor activo en background."""
        def _read():
            if not self._available:
                return
            try:
                from monitorcontrol import get_monitors
                raw = list(get_monitors())
                indices = self.get_target_indices()
                for idx in indices:
                    if idx < len(raw):
                        try:
                            with raw[idx] as m:
                                val = _read_luminance(m)
                                # Actualizar cache del MonitorInfo
                                for mi in self.ddc_monitors:
                                    if mi.index == idx:
                                        mi.brightness = val
                                        break
                        except Exception:
                            pass
                # Actualizar el cache principal con el primer monitor target
                if indices:
                    for mi in self.ddc_monitors:
                        if mi.index == indices[0]:
                            with self._lock:
                                self._brightness = mi.brightness
                                self._pending    = mi.brightness
                            break
            except Exception as e:
                print(f"[BrightnessCtrl] Error leyendo brillo: {e}")
        threading.Thread(target=_read, daemon=True).start()

    def set_brightness(self, value: int) -> int:
        """Establece el brillo con debouncing."""
        value = max(0, min(100, int(value)))
        with self._lock:
            self._brightness = value
            self._pending    = value
            indices = self.get_target_indices()
            for mi in self.ddc_monitors:
                if mi.index in indices:
                    mi.brightness = value
        if self._available:
            self._reset_debounce()
        return value

    def adjust(self, delta: int) -> int:
        """Ajusta el brillo en +/-delta."""
        with self._lock:
            current = self._brightness
        return self.set_brightness(current + delta)

    def flush_now(self):
        """Envia el valor pendiente inmediatamente."""
        self._cancel_debounce()
        if self._available:
            threading.Thread(target=self._flush, daemon=True).start()

    # -- Debounce interno -----------------------------------------------------
    def _reset_debounce(self):
        self._cancel_debounce()
        self._debounce_timer = threading.Timer(DEBOUNCE_MS / 1000.0, self._flush)
        self._debounce_timer.daemon = True
        self._debounce_timer.start()

    def _cancel_debounce(self):
        if self._debounce_timer is not None:
            self._debounce_timer.cancel()
            self._debounce_timer = None

    def _flush(self):
        """Envia brillo a los monitores objetivo."""
        with self._worker_lock:
            with self._lock:
                value = self._pending

            indices = self.get_target_indices()
            try:
                from monitorcontrol import get_monitors
                raw = list(get_monitors())
                for idx in indices:
                    if idx < len(raw):
                        try:
                            with raw[idx] as m:
                                m.set_luminance(value)
                            # Actualizar cache del MonitorInfo
                            for mi in self.ddc_monitors:
                                if mi.index == idx:
                                    mi.brightness = value
                                    break
                        except Exception as e:
                            print(f"[BrightnessCtrl] Error monitor {idx}: {e}")
                print(f"[BrightnessCtrl] Brillo => {value}% (monitores: {indices})")
            except Exception as e:
                print(f"[BrightnessCtrl] Error al establecer brillo {value}%: {e}")
