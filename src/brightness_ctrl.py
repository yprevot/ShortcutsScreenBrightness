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
                self._error_msg = (
                    "No se encontraron monitores.\n"
                    "Verifica: OSD del monitor -> Setup -> DDC/CI = On"
                )
                print(f"[BrightnessCtrl] {self._error_msg}")
                return

            print(f"[BrightnessCtrl] {len(raw_monitors)} monitor(es) detectados. Probando DDC/CI...")

            for idx, monitor in enumerate(raw_monitors):
                try:
                    with monitor as m:
                        brightness = _read_luminance(m)
                        # Intentar obtener nombre del modelo
                        try:
                            caps = str(m.get_vcp_capabilities())
                            name = f"Monitor {idx + 1}"
                            # Buscar patron model(...) en capabilities
                            if "model(" in caps.lower():
                                start = caps.lower().index("model(") + 6
                                end = caps.index(")", start)
                                model_name = caps[start:end].strip()
                                if model_name:
                                    name = model_name
                        except Exception:
                            name = f"Monitor {idx + 1}"

                        info = MonitorInfo(idx, name, brightness, ddc_ok=True)
                        self.monitors.append(info)
                        self.ddc_monitors.append(info)
                        print(f"[BrightnessCtrl] Monitor {idx}: '{name}' DDC/CI OK -- {brightness}%")

                except Exception as e:
                    info = MonitorInfo(idx, f"Monitor {idx + 1} (sin DDC/CI)", 0, ddc_ok=False)
                    self.monitors.append(info)
                    print(f"[BrightnessCtrl] Monitor {idx}: DDC/CI no responde ({e})")

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
                self._error_msg = (
                    "Ningun monitor respondio a DDC/CI.\n"
                    "Verifica DDC/CI = On en el OSD de cada monitor."
                )
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
