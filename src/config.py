"""
config.py - Configuración persistente para ShortcutsScreenBrightness
Guarda preferencias del usuario en un archivo JSON y maneja el autoarranque de Windows.
"""
import json
import os
import sys
import winreg

# Ruta del archivo de configuración en el directorio del usuario
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".shortcutsscreenbrightness.json")
APP_NAME    = "ShortcutsScreenBrightness"

# Path al ejecutable actual (funciona tanto en .py como en .exe compilado)
def _get_exe_path() -> str:
    if getattr(sys, "frozen", False):
        return sys.executable
    return f'"{sys.executable}" "{os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "main.py"))}"'


class Config:
    """Gestiona la configuración persistente de la app."""

    DEFAULTS = {
        "startup":         False,
        "last_brightness": 50,
        "step_large":      6,
        "step_small":      1,
    }

    def __init__(self):
        self.data: dict = dict(self.DEFAULTS)
        self._load()

    # ── Persistencia ────────────────────────────────────────────────────────
    def _load(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
        except Exception:
            pass

    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get(self, key: str, default=None):
        return self.data.get(key, default if default is not None else self.DEFAULTS.get(key))

    def set(self, key: str, value):
        self.data[key] = value
        self.save()

    # ── Autoarranque con Windows ─────────────────────────────────────────────
    _REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

    def is_startup_enabled(self) -> bool:
        """Devuelve True si la app está registrada para iniciar con Windows."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._REG_PATH,
                                0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, APP_NAME)
                return True
        except (FileNotFoundError, OSError):
            return False

    def set_startup(self, enable: bool) -> bool:
        """Habilita o deshabilita el autoarranque con Windows."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._REG_PATH,
                                0, winreg.KEY_ALL_ACCESS) as key:
                if enable:
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _get_exe_path())
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                    except FileNotFoundError:
                        pass
            self.set("startup", enable)
            return True
        except Exception as e:
            print(f"[Config] Error en autoarranque: {e}")
            return False
