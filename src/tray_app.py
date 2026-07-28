"""
tray_app.py - Aplicación en la bandeja del sistema (system tray)
Gestiona el ícono en la barra de tareas de Windows, el menú contextual
y coordina la ventana de control y las notificaciones OSD.
"""
import threading
import tkinter as tk
from typing import Callable

import pystray
from pystray import MenuItem as Item, Menu

from icon_maker import make_tray_icon
from ui_window import BrightnessWindow, OSDNotification
from i18n import t


class TrayApp:
    """
    Aplicación principal de bandeja del sistema.
    pystray corre en un hilo separado; tkinter corre en el hilo principal.
    """

    APP_NAME    = "ShortcutsScreenBrightness"
    APP_TOOLTIP = "ShortcutsScreenBrightness"

    def __init__(self, root: tk.Tk, brightness_ctrl, config):
        self.root            = root
        self.brightness_ctrl = brightness_ctrl
        self.config          = config
        self._icon: pystray.Icon = None

        # Construir componentes UI (ambos en el hilo principal via root)
        self.osd        = OSDNotification(root)
        self.ui_window  = BrightnessWindow(
            root, brightness_ctrl, config,
            quit_callback=self._do_quit
        )
        self.ui_window.set_tray_app(self)

        # Crear ícono de pystray
        self._build_icon()

    # ── Construcción del ícono y menú ────────────────────────────────────────
    def _build_icon(self):
        self._icon = pystray.Icon(
            name    = self.APP_NAME,
            icon    = make_tray_icon(self.brightness_ctrl.current),
            title   = f"{t('app_tooltip')}  |  {self.brightness_ctrl.current}%",
            menu    = self._build_menu(),
        )

    def _build_menu(self) -> Menu:
        return Menu(
            Item(
                lambda item: f"{t('tray_brightness')}:  {self.brightness_ctrl.current}%",
                action  = None,
                enabled = False,
            ),
            Menu.SEPARATOR,
            Item(t("tray_open"), self._open_window, default=True),
            Menu.SEPARATOR,
            Item(
                t("tray_autostart"),
                action  = self._toggle_startup,
                checked = lambda item: self.config.is_startup_enabled(),
            ),
            Menu.SEPARATOR,
            Item(t("tray_exit"), self._quit_from_menu),
        )

    # ── Callbacks del menú ───────────────────────────────────────────────────
    def _open_window(self, icon=None, item=None):
        """Abre/cierra la ventana de control (thread-safe)."""
        self.root.after(0, self.ui_window.toggle)

    def _toggle_startup(self, icon=None, item=None):
        current = self.config.is_startup_enabled()
        self.config.set_startup(not current)
        # Actualizar el check del menú
        if self._icon:
            self._icon.update_menu()

    def update_tray_menu(self):
        """Actualiza los textos traducidos del menú de la bandeja."""
        def _do():
            try:
                if self._icon:
                    self._icon.title = f"{t('app_tooltip')}  |  {self.brightness_ctrl.current}%"
                    self._icon.menu = self._build_menu()
                    self._icon.update_menu()
            except Exception as e:
                print(f"[TrayApp] Error actualizando menú: {e}")
        threading.Thread(target=_do, daemon=True).start()

    def _quit_from_menu(self, icon=None, item=None):
        self._icon.stop()
        self.root.after(0, self._do_quit)

    def _do_quit(self):
        """Limpieza completa y cierre."""
        try:
            if self._icon:
                self._icon.stop()
        except Exception:
            pass
        try:
            self.root.quit()
        except Exception:
            pass
        import sys
        sys.exit(0)

    # ── OSD y actualización del ícono ────────────────────────────────────────
    def show_osd(self, brightness: int):
        """
        Muestra la notificación OSD y actualiza el ícono/tooltip.
        Se puede llamar desde cualquier hilo.
        """
        self.osd.show(brightness)
        self._update_tray_icon(brightness)
        # Actualizar la ventana de control si está abierta
        if self.ui_window.visible:
            self.ui_window.update_brightness_display(brightness)

    def _update_tray_icon(self, brightness: int):
        """Actualiza el ícono y tooltip del tray en background."""
        def _do():
            try:
                if self._icon:
                    self._icon.icon  = make_tray_icon(brightness)
                    self._icon.title = f"{self.APP_TOOLTIP}  |  {brightness}%"
            except Exception:
                pass
        threading.Thread(target=_do, daemon=True).start()

    # ── Ejecución ─────────────────────────────────────────────────────────────
    def run(self):
        """Arranca el ícono de la bandeja (bloquea el hilo actual)."""
        self._icon.run(setup=lambda icon: setattr(icon, "visible", True))
