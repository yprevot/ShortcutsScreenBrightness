"""
hotkeys.py - Gestor de hotkeys globales para ShortcutsScreenBrightness
Registra combinaciones de teclas a nivel de sistema operativo para controlar
el brillo del monitor desde cualquier aplicación.

Combinaciones:
  Ctrl + Alt + ↑  →  Brillo +6
  Ctrl + Alt + ↓  →  Brillo -6
  Ctrl + Alt + →  →  Brillo +1
  Ctrl + Alt + ←  →  Brillo -1

Nota: Si los hotkeys no responden, ejecutar como Administrador puede ayudar.
      Intel Graphics puede usar Ctrl+Alt+Flechas para rotar pantalla;
      desactívalo en el panel de control de Intel si hay conflicto.
"""
import threading
from typing import Callable


class HotkeyManager:
    """Gestiona los atajos de teclado globales vía la librería 'keyboard'."""

    # Definición de hotkeys
    HOTKEYS = {
        "ctrl+alt+up":    +6,   # Brillo +6
        "ctrl+alt+down":  -6,   # Brillo -6
        "ctrl+alt+right": +1,   # Brillo +1
        "ctrl+alt+left":  -1,   # Brillo -1
    }

    def __init__(self, brightness_ctrl, osd_callback: Callable[[int], None]):
        """
        Args:
            brightness_ctrl: Instancia de BrightnessController
            osd_callback:    Función llamada con el nuevo brillo tras cada ajuste
        """
        self.brightness_ctrl = brightness_ctrl
        self.osd_callback    = osd_callback
        self._registered     = False
        self._lock           = threading.Lock()

    # ── API pública ──────────────────────────────────────────────────────────
    def register(self):
        """Registra todos los hotkeys globales."""
        try:
            import keyboard
            for combo, delta in self.HOTKEYS.items():
                keyboard.add_hotkey(
                    combo,
                    self._make_handler(delta),
                    suppress=True   # Evita que la tecla llegue a otras apps
                )
            self._registered = True
            print("[HotkeyManager] Hotkeys registrados:")
            for combo, delta in self.HOTKEYS.items():
                sign = "+" if delta > 0 else ""
                print(f"  {combo:20s} → Brillo {sign}{delta}")
        except ImportError:
            print("[HotkeyManager] 'keyboard' no instalado. Ejecuta: pip install keyboard")
        except Exception as e:
            print(f"[HotkeyManager] Error al registrar hotkeys: {e}")
            print("  Tip: Intenta ejecutar la app como Administrador.")

    def unregister(self):
        """Elimina todos los hotkeys registrados."""
        if self._registered:
            try:
                import keyboard
                keyboard.remove_all_hotkeys()
                self._registered = False
                print("[HotkeyManager] Hotkeys eliminados.")
            except Exception:
                pass

    # ── Privado ──────────────────────────────────────────────────────────────
    def _make_handler(self, delta: int) -> Callable:
        """Crea un callback para el hotkey con el delta dado."""
        def handler():
            with self._lock:
                new_val = self.brightness_ctrl.adjust(delta)
            if self.osd_callback:
                self.osd_callback(new_val)
        return handler
