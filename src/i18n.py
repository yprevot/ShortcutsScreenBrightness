"""
i18n.py - Módulo de internacionalización para ShortcutsScreenBrightness
Soporta detección nativa del idioma en Windows (10, 11, 8, 7, XP) mediante Win32 API y locale.
"""
import ctypes
import locale
import os

# ── Diccionario de Traducciones ─────────────────────────────────────────────
TRANSLATIONS = {
    "es": {
        "app_name": "ShortcutsScreenBrightness",
        "app_tooltip": "ShortcutsScreenBrightness — Control de Brillo",
        "status_ddc_ok": "DDC/CI",
        "status_ddc_error": "DDC/CI no disponible",
        "monitors_section": "Monitores",
        "brightness_label": "Brillo del monitor",
        "all_monitors": "🖥  Todos los monitores ({count})",
        "no_ddc_suffix": "  (sin DDC/CI)",
        "no_monitors_found": "Sin monitores detectados",
        "hk_step_large": "±6 brillo",
        "hk_step_small": "±1 brillo",
        "startup_switch": "Iniciar con Windows",
        "exit_btn": "Salir",
        "tray_show": "Mostrar / Ocultar",
        "tray_open": "⚙  Abrir control de brillo",
        "tray_brightness": "Brillo",
        "tray_autostart": "Iniciar con Windows",
        "tray_exit": "✕  Salir",
        "already_running_title": "ShortcutsScreenBrightness",
        "already_running_msg": (
            "ShortcutsScreenBrightness ya está en ejecución.\n"
            "Busca el ícono ☀ en la bandeja del sistema (esquina inferior derecha)."
        ),
        "ddc_error_osd": (
            "No se encontraron monitores DDC/CI.\n"
            "Verifica: OSD del monitor -> Setup -> DDC/CI = On"
        ),
        "ddc_error_generic": (
            "Ningún monitor respondió a DDC/CI.\n"
            "Verifica:\n"
            "  • DDC/CI = On en el OSD del monitor\n"
            "  • Cable HDMI / DisplayPort / USB-C (DP Alt Mode)\n"
            "  • Conexión directa sin adaptadores incompatibles"
        ),
    },
    "en": {
        "app_name": "ShortcutsScreenBrightness",
        "app_tooltip": "ShortcutsScreenBrightness — Brightness Control",
        "status_ddc_ok": "DDC/CI",
        "status_ddc_error": "DDC/CI not available",
        "monitors_section": "Monitors",
        "brightness_label": "Monitor brightness",
        "all_monitors": "🖥  All monitors ({count})",
        "no_ddc_suffix": "  (no DDC/CI)",
        "no_monitors_found": "No monitors detected",
        "hk_step_large": "±6 brightness",
        "hk_step_small": "±1 brightness",
        "startup_switch": "Start with Windows",
        "exit_btn": "Exit",
        "tray_show": "Show / Hide",
        "tray_open": "⚙  Open Brightness Control",
        "tray_brightness": "Brightness",
        "tray_autostart": "Start with Windows",
        "tray_exit": "✕  Exit",
        "already_running_title": "ShortcutsScreenBrightness",
        "already_running_msg": (
            "ShortcutsScreenBrightness is already running.\n"
            "Look for the ☀ icon in the system tray (bottom right corner)."
        ),
        "ddc_error_osd": (
            "No DDC/CI monitors found.\n"
            "Check: Monitor OSD -> Setup -> DDC/CI = On"
        ),
        "ddc_error_generic": (
            "No monitor responded to DDC/CI.\n"
            "Check:\n"
            "  • DDC/CI = On in your monitor's OSD\n"
            "  • HDMI / DisplayPort / USB-C (DP Alt Mode) cable\n"
            "  • Direct connection without incompatible docks/hubs"
        ),
    },
}


def detect_language() -> str:
    """
    Detecta el idioma del sistema operativo.
    Soporta Windows 11, 10, 8, 7, XP mediante GetUserDefaultUILanguage (kernel32),
    fallback a locale y variables de entorno.
    Devuelve 'es' si es español, 'en' para cualquier otro idioma.
    """
    lang_code = ""

    # Método 1: Win32 Kernel32 API (compatible con Windows XP hasta Windows 11)
    try:
        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0xFF
        # Primary Language ID: 0x0a (10) es Español / Spanish
        if lang_id == 0x0A:
            return "es"
        elif lang_id == 0x09:
            return "en"
    except Exception:
        pass

    # Método 2: Módulo locale de Python
    try:
        loc = locale.getdefaultlocale()[0]
        if loc:
            lang_code = loc.lower()
    except Exception:
        pass

    # Método 3: Variable de entorno (Linux / macOS / Git Bash)
    if not lang_code:
        lang_code = os.environ.get("LANG", "").lower()

    if lang_code.startswith("es") or "spanish" in lang_code:
        return "es"

    return "en"


# Modo activo: 'es', 'en'
ACTIVE_MODE = "es"
CURRENT_LANG = "es"


def set_language_mode(mode: str):
    """
    Establece el modo de idioma ('auto', 'es', 'en').
    Si es 'auto', detecta dinámicamente el idioma del SO.
    """
    global ACTIVE_MODE, CURRENT_LANG
    ACTIVE_MODE = mode
    if mode == "auto":
        CURRENT_LANG = detect_language()
    elif mode in TRANSLATIONS:
        CURRENT_LANG = mode
    else:
        CURRENT_LANG = "en"


def get_language_mode() -> str:
    return ACTIVE_MODE


def t(key: str, **kwargs) -> str:
    """
    Obtiene la traducción para la clave dada en el idioma activo.
    """
    lang_dict = TRANSLATIONS.get(CURRENT_LANG, TRANSLATIONS["en"])
    text = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        return text.format(**kwargs)
    return text
