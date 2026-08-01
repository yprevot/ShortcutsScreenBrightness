"""
brightness_ctrl.py - Control de brillo para monitores DDC/CI y pantallas de Laptop (WMI)
Comunica con monitores externos a traves de DDC/CI (monitorcontrol) y pantallas internas
de laptops a traves de la API WMI de Windows (WmiMonitorBrightness).

Multi-monitor hibrido y autodeteccion en caliente (Hot-Plug):
  - Descubre TODOS los monitores ACTIVOS (Laptop WMI y externos DDC/CI).
  - Asigna nombres EDID exactos por DeviceID evitando intercambio de nombres.
  - Numeracion secuencial 1, 2, 3... basada estrictamente en monitores activos.
  - La UI se actualiza INMEDIATAMENTE desde cache.
  - El comando se envia solo despues de DEBOUNCE_MS ms sin mas cambios.
"""
import threading
import json
import subprocess
import ctypes
from ctypes import wintypes
import winreg
from typing import Optional, List, Dict

from i18n import t

DEBOUNCE_MS = 80


def _read_luminance(monitor) -> int:
    """Lee el brillo de un monitor DDC/CI, compatible con monitorcontrol v3 y v4."""
    lum = monitor.get_luminance()
    return lum.current_value if hasattr(lum, "current_value") else int(lum)


class MonitorInfo:
    """Datos de un monitor detectado (DDC/CI o Laptop WMI)."""

    def __init__(self, index: int, name: str, brightness: int, ddc_ok: bool, is_wmi: bool = False, instance_name: str = ""):
        self.index         = index
        self.name          = name
        self.brightness    = brightness
        self.ddc_ok        = ddc_ok
        self.is_wmi        = is_wmi
        self.instance_name = instance_name

    def __repr__(self):
        status = "WMI Laptop" if self.is_wmi else ("OK" if self.ddc_ok else "NO DDC")
        return f"Monitor({self.index}, '{self.name}', {self.brightness}%, {status})"


# ── Soporte WMI para Pantallas Internas de Laptop ────────────────────────────
def _get_wmi_laptop_monitors() -> List[Dict]:
    """Obtiene datos de brillo de la pantalla integrada de laptop via WMI."""
    monitors = []
    # 1. Intentar via win32com (ultra rapido ~20ms)
    try:
        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()
        try:
            wmi = win32com.client.GetObject('winmgmts:\\\\.\\root\\wmi')
            items = wmi.ExecQuery('SELECT * FROM WmiMonitorBrightness')
            for item in items:
                if getattr(item, "Active", True):
                    monitors.append({
                        "brightness": int(item.CurrentBrightness),
                        "instance": str(item.InstanceName)
                    })
        finally:
            pythoncom.CoUninitialize()
        if monitors:
            return monitors
    except Exception as e:
        print(f"[BrightnessCtrl] Error WMI win32com: {e}")

    # 2. Fallback via PowerShell
    try:
        cmd = "Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBrightness | Select-Object -Property CurrentBrightness, InstanceName, Active | ConvertTo-Json"
        out = subprocess.check_output(["powershell", "-NoProfile", "-Command", cmd], text=True, timeout=3).strip()
        if out:
            data = json.loads(out)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                if item.get("Active", True):
                    monitors.append({
                        "brightness": int(item.get("CurrentBrightness", 50)),
                        "instance": str(item.get("InstanceName", ""))
                    })
    except Exception as e:
        print(f"[BrightnessCtrl] Error WMI PowerShell fallback: {e}")

    return monitors


def _set_wmi_brightness(instance_name: str, val: int):
    """Establece el brillo de la pantalla de laptop via WMI."""
    val = max(0, min(100, int(val)))
    # 1. Intentar via win32com
    try:
        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()
        try:
            wmi = win32com.client.GetObject('winmgmts:\\\\.\\root\\wmi')
            methods = wmi.ExecQuery('SELECT * FROM WmiMonitorBrightnessMethods')
            for m in methods:
                if not instance_name or str(m.InstanceName) == instance_name:
                    in_params = m.Methods_('WmiSetBrightness').InParameters.SpawnInstance_()
                    in_params.Timeout = 1
                    in_params.Brightness = val
                    m.ExecMethod_('WmiSetBrightness', in_params)
                    print(f"[BrightnessCtrl] WMI Laptop => {val}%")
                    return
        finally:
            pythoncom.CoUninitialize()
    except Exception as e:
        print(f"[BrightnessCtrl] Error al establecer brillo WMI win32com: {e}")

    # 2. Fallback via PowerShell
    try:
        cmd = f"(Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {val})"
        subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, timeout=3)
        print(f"[BrightnessCtrl] WMI Laptop (PowerShell) => {val}%")
    except Exception as e:
        print(f"[BrightnessCtrl] Error al establecer brillo WMI PowerShell: {e}")


# ── Parser EDID preciso por DeviceID ─────────────────────────────────────────
def _get_edid_name_from_id(dev_id: str) -> str:
    """Busca el nombre EDID exacto en el registro para un DeviceID especifico."""
    if not dev_id:
        return ""
    parts = dev_id.split("\\")
    if len(parts) >= 3:
        pnp_code = parts[1]
        instance_id = parts[2].split("_")[0]  # Remover sufijo _0 si existe
        reg_path = rf"SYSTEM\CurrentControlSet\Enum\DISPLAY\{pnp_code}\{instance_id}"
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
            friendly_name = ""
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

            # 2. Buscar en FriendlyName
            if not friendly_name:
                try:
                    fname, _ = winreg.QueryValueEx(key, "FriendlyName")
                    if fname and fname not in ("Generic PnP Monitor", "Monitor PnP genérico"):
                        friendly_name = fname
                except Exception:
                    pass

            winreg.CloseKey(key)

            # 3. Fallback por PNP ID conocido
            if not friendly_name:
                if "BOE" in pnp_code.upper() or "INT" in pnp_code.upper():
                    friendly_name = "Integrated Monitor"
                elif "LHC" in pnp_code.upper() or "TTN" in pnp_code.upper():
                    friendly_name = "P2712V"
                else:
                    friendly_name = pnp_code
            return friendly_name
        except Exception:
            pass
    return ""


def _get_active_external_devices() -> List[tuple]:
    """Obtiene la lista de (DeviceID, ModelName) únicamente para monitores externos activos en Windows."""
    class DISPLAY_DEVICE(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("DeviceName", wintypes.WCHAR * 32),
            ("DeviceString", wintypes.WCHAR * 128),
            ("StateFlags", wintypes.DWORD),
            ("DeviceID", wintypes.WCHAR * 128),
            ("DeviceKey", wintypes.WCHAR * 128)
        ]

    user32 = ctypes.windll.user32
    external_devices = []
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
                    if dev_id and "BOE" not in dev_id.upper():
                        name = _get_edid_name_from_id(dev_id)
                        if not name:
                            name = f"Display {len(external_devices) + 1}"
                        external_devices.append((dev_id, name))
                j += 1
        i += 1
    return external_devices


# Valor especial para "aplicar a todos los monitores"
TARGET_ALL = -1


class BrightnessController:
    """
    Controla el brillo de uno o multiples monitores (Laptop WMI y/o DDC/CI externos).

    Atributos publicos:
      monitors:       lista de MonitorInfo (solo los activos y controlables)
      ddc_monitors:   lista de MonitorInfo (identica a monitors)
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

        self.rescan_monitors()

    # -- Redescubrimiento en caliente (Hot-Plug) ------------------------------
    def rescan_monitors(self) -> bool:
        """
        Vuelve a detectar monitores activos (Laptop WMI y DDC/CI externos).
        Devuelve True si la lista o estado de monitores controlables cambio.
        """
        new_ddc_monitors: List[MonitorInfo] = []
        display_number = 1

        # 1. Detectar pantallas integradas de Laptop via WMI
        wmi_laptops = _get_wmi_laptop_monitors()
        for w_item in wmi_laptops:
            inst_name = w_item["instance"]
            model_name = _get_edid_name_from_id(inst_name) or "Integrated Monitor"
            display_name = f"Monitor {display_number} - ({model_name})"
            brightness = w_item["brightness"]

            info = MonitorInfo(
                index=display_number - 1,
                name=display_name,
                brightness=brightness,
                ddc_ok=True,
                is_wmi=True,
                instance_name=inst_name
            )
            new_ddc_monitors.append(info)
            display_number += 1

        # 2. Detectar monitores externos DDC/CI activos
        external_devices = _get_active_external_devices()
        try:
            from monitorcontrol import get_monitors
            raw_monitors = list(get_monitors())

            for idx, monitor in enumerate(raw_monitors):
                model_str = external_devices[idx][1] if idx < len(external_devices) else ""
                display_name = f"Monitor {display_number} - ({model_str})" if model_str else f"Monitor {display_number}"

                try:
                    with monitor as m:
                        brightness = _read_luminance(m)
                        info = MonitorInfo(
                            index=display_number - 1,
                            name=display_name,
                            brightness=brightness,
                            ddc_ok=True,
                            is_wmi=False
                        )
                        new_ddc_monitors.append(info)
                        display_number += 1
                except Exception as e:
                    print(f"[BrightnessCtrl] Monitor DDC/CI no responde ({e})")
        except Exception as e:
            print(f"[BrightnessCtrl] Error DDC/CI en rescan: {e}")

        with self._lock:
            old_sig = [(m.index, m.name, m.brightness) for m in self.ddc_monitors]
            new_sig = [(m.index, m.name, m.brightness) for m in new_ddc_monitors]
            changed = (old_sig != new_sig)

            self.monitors = new_ddc_monitors
            self.ddc_monitors = new_ddc_monitors

            if self.ddc_monitors:
                self._available = True
                valid_indices = [m.index for m in self.ddc_monitors]
                if self.target_index != TARGET_ALL and self.target_index not in valid_indices:
                    self.target_index = self.ddc_monitors[0].index
                    self._brightness = self.ddc_monitors[0].brightness
                    self._pending = self._brightness
                elif self.target_index == TARGET_ALL:
                    self._brightness = self.ddc_monitors[0].brightness
                    self._pending = self._brightness
            else:
                self._available = False
                self.target_index = TARGET_ALL
                self._error_msg = t("ddc_error_generic")

            if changed:
                print(f"[BrightnessCtrl] Monitores activos actualizados ({len(self.ddc_monitors)}): {self.ddc_monitors}")

            return changed

    # -- Propiedades ----------------------------------------------------------
    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def error_message(self) -> str:
        return self._error_msg

    @property
    def current(self) -> int:
        """Brillo en cache del monitor activo (o del primero si es 'Todos')."""
        return self._brightness

    # -- Seleccion de monitor -------------------------------------------------
    def set_target(self, index: int):
        """
        Cambia el monitor objetivo.
        index = TARGET_ALL (-1) para aplicar a todos los monitores controlables.
        index = indice real del monitor para uno especifico.
        """
        self.target_index = index
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
        """Relee el brillo de los monitores en background."""
        def _read():
            if not self._available:
                return
            try:
                # 1. Releer WMI Laptop
                wmi_laptops = _get_wmi_laptop_monitors()
                if wmi_laptops:
                    w_brightness = wmi_laptops[0]["brightness"]
                    for mi in self.ddc_monitors:
                        if mi.is_wmi:
                            mi.brightness = w_brightness

                # 2. Releer DDC/CI
                try:
                    from monitorcontrol import get_monitors
                    raw = list(get_monitors())
                    ddc_idx = 0
                    for mi in self.ddc_monitors:
                        if not mi.is_wmi:
                            if ddc_idx < len(raw):
                                try:
                                    with raw[ddc_idx] as m:
                                        mi.brightness = _read_luminance(m)
                                except Exception:
                                    pass
                                ddc_idx += 1
                except Exception:
                    pass

                # 3. Actualizar cache principal
                indices = self.get_target_indices()
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
        """Envia brillo a los monitores objetivo (Laptop WMI y/o DDC/CI externos)."""
        with self._worker_lock:
            with self._lock:
                value = self._pending

            indices = self.get_target_indices()

            # Separar objetivos WMI y DDC/CI
            wmi_targets = [mi for mi in self.ddc_monitors if mi.index in indices and mi.is_wmi]
            ddc_targets = [mi for mi in self.ddc_monitors if mi.index in indices and not mi.is_wmi]

            # 1. Aplicar a pantallas WMI Laptop
            for mi in wmi_targets:
                _set_wmi_brightness(mi.instance_name, value)
                mi.brightness = value

            # 2. Aplicar a monitores DDC/CI externos
            if ddc_targets:
                try:
                    from monitorcontrol import get_monitors
                    raw = list(get_monitors())
                    # Mapear monitores DDC/CI a raw_monitors
                    non_wmi_count = 0
                    for mi_all in self.ddc_monitors:
                        if not mi_all.is_wmi:
                            if mi_all.index in indices:
                                if non_wmi_count < len(raw):
                                    try:
                                        with raw[non_wmi_count] as m:
                                            m.set_luminance(value)
                                        mi_all.brightness = value
                                    except Exception as e:
                                        print(f"[BrightnessCtrl] Error monitor DDC/CI {mi_all.index}: {e}")
                            non_wmi_count += 1
                except Exception as e:
                    print(f"[BrightnessCtrl] Error DDC/CI al aplicar brillo {value}%: {e}")

            print(f"[BrightnessCtrl] Brillo => {value}% (monitores target: {indices})")
