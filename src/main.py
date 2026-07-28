"""
main.py - Punto de entrada de ShortcutsScreenBrightness
Monitor Brightness Control con atajos de teclado globales.
"""
import sys
import os
import socket
import threading
import tkinter as tk
from config import Config
from brightness_ctrl import BrightnessController
from tray_app import TrayApp
from hotkeys import HotkeyManager
from i18n import t

# ── Instancia única ──────────────────────────────────────────────────────────
def _ensure_single_instance() -> socket.socket:
    """
    Previene que se abran múltiples instancias usando un socket local.
    Devuelve el socket de bloqueo (mantenerlo vivo durante toda la ejecución).
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        sock.bind(("127.0.0.1", 47833))
        return sock
    except OSError:
        # Ya está corriendo — mostrar aviso y salir
        try:
            root = tk.Tk()
            root.withdraw()
            from tkinter import messagebox
            messagebox.showinfo(
                t("already_running_title"),
                t("already_running_msg")
            )
            root.destroy()
        except Exception:
            pass
        sys.exit(0)


# ── Helpers de ruta ──────────────────────────────────────────────────────────
def _add_src_to_path():
    """Agrega el directorio src/ al sys.path para los imports."""
    src = os.path.dirname(os.path.abspath(__file__))
    if src not in sys.path:
        sys.path.insert(0, src)


# ── Entry point ──────────────────────────────────────────────────────────────
def main():
    # Asegurar una sola instancia
    lock_socket = _ensure_single_instance()

    # Configurar imports
    _add_src_to_path()

    from config         import Config
    from brightness_ctrl import BrightnessController
    from tray_app       import TrayApp
    from hotkeys        import HotkeyManager

    # 1. Configuración persistente
    config = Config()

    # 2. Root de tkinter (oculto — necesario para ventanas Toplevel)
    root = tk.Tk()
    root.withdraw()
    root.title("ShortcutsScreenBrightness")

    # 3. Controlador de brillo DDC/CI
    brightness_ctrl = BrightnessController()

    # 4. App de bandeja + ventana UI
    tray_app = TrayApp(root, brightness_ctrl, config)

    # 5. Hotkeys globales
    hotkey_mgr = HotkeyManager(
        brightness_ctrl = brightness_ctrl,
        osd_callback    = tray_app.show_osd,
    )
    hotkey_mgr.register()

    # 6. pystray en hilo secundario (no puede correr en el hilo de tkinter)
    tray_thread = threading.Thread(target=tray_app.run, daemon=True)
    tray_thread.start()

    # 7. tkinter en el hilo principal (bloquea hasta cierre)
    try:
        root.mainloop()
    finally:
        hotkey_mgr.unregister()
        lock_socket.close()


if __name__ == "__main__":
    main()
