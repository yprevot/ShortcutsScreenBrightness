"""
ui_window.py - Ventana principal de control de brillo + OSD
Soporta tema claro/oscuro sincronizado con el sistema operativo Windows.
Incluye selector de monitor (individual o todos).
"""
import tkinter as tk
import math
import threading
from typing import Callable, Optional

try:
    import darkdetect
except ImportError:
    darkdetect = None

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

from brightness_ctrl import TARGET_ALL
from i18n import t, set_language_mode, get_language_mode

# ══════════════════════════════════════════════════════════════════════════════
#  Paleta de colores dual (Dark / Light)
# ══════════════════════════════════════════════════════════════════════════════
THEMES = {
    "dark": {
        "bg_root":    "#0b0b18",
        "bg_card":    "#14142a",
        "bg_surface": "#1c1c38",
        "bg_hover":   "#22224a",
        "accent":     "#f5a623",
        "accent2":    "#ff7b25",
        "accent_dim": "#7a5010",
        "text_pri":   "#eeeeff",
        "text_sec":   "#7777aa",
        "text_dim":   "#44446a",
        "slider_trk": "#252550",
        "border":     "#2a2a55",
        "success":    "#4caf7d",
        "error":      "#ff6b6b",
        "btn_down":   "#1a0a0a",
        "btn_up":     "#0a1a0a",
        "quit_hover": "#2a1010",
        "monitor_sel":"#1e1e44",
        "monitor_act":"#2a2a60",
    },
    "light": {
        "bg_root":    "#f0f0f5",
        "bg_card":    "#ffffff",
        "bg_surface": "#e8e8f0",
        "bg_hover":   "#d8d8e8",
        "accent":     "#e08a10",
        "accent2":    "#d06c00",
        "accent_dim": "#c49550",
        "text_pri":   "#1a1a2e",
        "text_sec":   "#555580",
        "text_dim":   "#8888aa",
        "slider_trk": "#d0d0e0",
        "border":     "#c0c0d5",
        "success":    "#2e8b57",
        "error":      "#d44040",
        "btn_down":   "#ffe0e0",
        "btn_up":     "#e0ffe0",
        "quit_hover": "#ffe0e0",
        "monitor_sel":"#e0e0f0",
        "monitor_act":"#c8c8e8",
    },
}


def _detect_system_theme() -> str:
    """Detecta el tema del sistema operativo. Devuelve 'dark' o 'light'."""
    if darkdetect:
        try:
            theme = darkdetect.theme()
            if theme and theme.lower() == "light":
                return "light"
        except Exception:
            pass
    return "dark"


def _get_theme() -> dict:
    """Devuelve la paleta de colores segun el tema del SO."""
    return THEMES[_detect_system_theme()]


def _hex_lerp(c1: str, c2: str, t: float) -> str:
    """Interpola entre dos colores hex."""
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# ══════════════════════════════════════════════════════════════════════════════
#  OSD Notification
# ══════════════════════════════════════════════════════════════════════════════
class OSDNotification:
    """Notificacion overlay al cambiar brillo con hotkeys."""

    OSD_W, OSD_H = 200, 76
    FADE_STEP = 0.07
    HOLD_MS = 1400

    def __init__(self, root: tk.Tk):
        self.root = root
        self._win: Optional[tk.Toplevel] = None
        self._timer = None
        self._alpha = 0.0
        self._target = 0.92
        self._fading = False

    def show(self, brightness: int):
        self.root.after(0, lambda: self._show(brightness))

    def _show(self, brightness: int):
        if self._timer:
            self.root.after_cancel(self._timer)
            self._timer = None
        if self._win is None or not self._win.winfo_exists():
            self._build()
        self._update_content(brightness)
        self._win.deiconify()
        self._win.lift()
        self._fading = False
        self._fade(direction=+1)
        self._timer = self.root.after(self.HOLD_MS, self._begin_fade_out)

    def _build(self):
        T = _get_theme()
        sw = self.root.winfo_screenwidth()
        x = sw - self.OSD_W - 20
        y = 20

        self._win = tk.Toplevel(self.root)
        self._win.overrideredirect(True)
        self._win.attributes("-topmost", True)
        self._win.attributes("-alpha", 0.0)
        self._win.geometry(f"{self.OSD_W}x{self.OSD_H}+{x}+{y}")
        self._win.configure(bg=T["bg_root"])

        outer = tk.Frame(self._win, bg=T["border"], padx=1, pady=1)
        outer.pack(fill="both", expand=True)
        card = tk.Frame(outer, bg=T["bg_card"], padx=14, pady=10)
        card.pack(fill="both", expand=True)

        top = tk.Frame(card, bg=T["bg_card"])
        top.pack(fill="x")
        self._icon_lbl = tk.Label(top, text="☀", font=("Segoe UI", 18),
                                   bg=T["bg_card"], fg=T["accent"])
        self._icon_lbl.pack(side="left")
        self._pct_lbl = tk.Label(top, text="50%",
                                  font=("Segoe UI", 24, "bold"),
                                  bg=T["bg_card"], fg=T["text_pri"])
        self._pct_lbl.pack(side="left", padx=(8, 0))

        bar_bg = tk.Frame(card, bg=T["slider_trk"], height=5)
        bar_bg.pack(fill="x", pady=(6, 0))
        self._bar = tk.Frame(bar_bg, bg=T["accent"], height=5)
        self._bar.place(x=0, y=0, relheight=1, relwidth=0.5)
        self._alpha = 0.0

    def _update_content(self, brightness: int):
        T = _get_theme()
        t = brightness / 100.0
        color = _hex_lerp(T["accent_dim"], T["accent"], t)
        self._icon_lbl.configure(fg=color)
        self._pct_lbl.configure(text=f"{brightness}%")
        self._bar.place(relwidth=max(0.02, t))

    def _begin_fade_out(self):
        self._fading = True
        self._fade(direction=-1)

    def _fade(self, direction: int):
        self._alpha = max(0.0, min(self._target, self._alpha + direction * self.FADE_STEP))
        if self._win and self._win.winfo_exists():
            self._win.attributes("-alpha", self._alpha)
        if direction > 0 and self._alpha < self._target:
            self.root.after(16, lambda: self._fade(+1))
        elif direction < 0 and self._alpha > 0:
            self.root.after(16, lambda: self._fade(-1))
        elif direction < 0 and self._alpha <= 0:
            if self._win:
                self._win.withdraw()


# ══════════════════════════════════════════════════════════════════════════════
#  BrightnessWindow — ventana flotante principal
# ══════════════════════════════════════════════════════════════════════════════
class BrightnessWindow:
    """Ventana flotante de control de brillo con tema sincronizado y selector de monitor."""

    WIN_W, WIN_H = 320, 580
    TASKBAR_H = 52

    def __init__(self, root: tk.Tk, brightness_ctrl, config, quit_callback: Callable):
        self.root = root
        self.brightness_ctrl = brightness_ctrl
        self.config = config
        self.quit_callback = quit_callback
        self.visible = False
        self._focus_timer = None
        self.tray_app = None

        # Arrastre de ventana
        self._drag_x = 0
        self._drag_y = 0

        # Cargar preferencia de idioma guardada (por defecto 'es')
        saved_lang = self.config.get("language", "es")
        if saved_lang not in ("es", "en"):
            saved_lang = "es"
        set_language_mode(saved_lang)

        self.T = _get_theme()  # Tema actual

        if CTK_AVAILABLE:
            mode = _detect_system_theme()
            ctk.set_appearance_mode(mode)
            ctk.set_default_color_theme("dark-blue")
            self._build_ctk()
        else:
            self._build_tk()

        # Iniciar monitoreo en caliente (Hot-Plug) de conexión/desconexión de pantallas
        self._start_hotplug_check()

    def set_tray_app(self, tray_app):
        self.tray_app = tray_app

    # ── Drag logic ───────────────────────────────────────────────────────────
    def _start_drag(self, event):
        """Registra la posición del mouse al iniciar el arrastre de la ventana."""
        self._drag_x = event.x
        self._drag_y = event.y

    def _do_drag(self, event):
        """Mueve la ventana según la posición del mouse."""
        x = self.win.winfo_x() + (event.x - self._drag_x)
        y = self.win.winfo_y() + (event.y - self._drag_y)
        self.win.geometry(f"+{x}+{y}")

    # ── Constructor CTK ──────────────────────────────────────────────────────
    def _build_ctk(self):
        T = self.T
        self.win = ctk.CTkToplevel(self.root)
        self.win.title("ShortcutsScreenBrightness")
        self.win.geometry(f"{self.WIN_W}x{self.WIN_H}")
        self.win.resizable(False, False)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(fg_color=T["bg_root"])
        self.win.withdraw()

        # Arrastre de ventana global (en la ventana de nivel superior)
        self.win.bind("<ButtonPress-1>", self._start_drag)
        self.win.bind("<B1-Motion>", self._do_drag)

        # ── Tarjeta exterior ─────────────────────────────────────────────────
        card = ctk.CTkFrame(self.win, fg_color=T["bg_card"], corner_radius=18,
                             border_width=1, border_color=T["border"])
        card.pack(fill="both", expand=True, padx=6, pady=6)
        self._card = card

        card.bind("<ButtonPress-1>", self._start_drag)
        card.bind("<B1-Motion>", self._do_drag)

        # ── Header Renglón 1: Título y Botón Cerrar ─────────────────────────
        hdr = ctk.CTkFrame(card, fg_color=T["bg_card"])
        hdr.pack(fill="x", padx=18, pady=(16, 0))

        hdr.bind("<ButtonPress-1>", self._start_drag)
        hdr.bind("<B1-Motion>", self._do_drag)

        self.sun_cv = tk.Canvas(hdr, width=38, height=38,
                                bg=T["bg_card"], highlightthickness=0)
        self.sun_cv.pack(side="left")
        self.sun_cv.bind("<ButtonPress-1>", self._start_drag)
        self.sun_cv.bind("<B1-Motion>", self._do_drag)
        self._draw_sun(50)

        info = ctk.CTkFrame(hdr, fg_color=T["bg_card"])
        info.pack(side="left", padx=(6, 0))
        info.bind("<ButtonPress-1>", self._start_drag)
        info.bind("<B1-Motion>", self._do_drag)

        title_lbl = ctk.CTkLabel(info, text="Shortcuts Screen Brightness",
                                 font=ctk.CTkFont("Segoe UI", 13, "bold"),
                                 text_color=T["text_pri"])
        title_lbl.pack(anchor="w")
        title_lbl.bind("<ButtonPress-1>", self._start_drag)
        title_lbl.bind("<B1-Motion>", self._do_drag)

        # Botón cerrar (X)
        ctk.CTkButton(hdr, text="✕", width=28, height=28,
                       fg_color=T["bg_card"], hover_color=T["bg_surface"],
                       text_color=T["text_sec"], font=ctk.CTkFont("Segoe UI", 13),
                       corner_radius=14, command=self.hide
                       ).pack(side="right")

        # ── Header Renglón 2: Selector de idioma exclusivo ────────────────────
        lang_row = ctk.CTkFrame(card, fg_color=T["bg_card"])
        lang_row.pack(fill="x", padx=18, pady=(10, 0))
        lang_row.bind("<ButtonPress-1>", self._start_drag)
        lang_row.bind("<B1-Motion>", self._do_drag)

        self.lang_lbl = ctk.CTkLabel(lang_row, text=t("language_label"),
                                     font=ctk.CTkFont("Segoe UI", 11),
                                     text_color=T["text_sec"])
        self.lang_lbl.pack(side="left")
        self.lang_lbl.bind("<ButtonPress-1>", self._start_drag)
        self.lang_lbl.bind("<B1-Motion>", self._do_drag)

        lang_map = {"es": "ES", "en": "EN"}
        current_lang_str = lang_map.get(get_language_mode(), "ES")

        self.lang_menu = ctk.CTkOptionMenu(
            lang_row,
            values=["ES", "EN"],
            width=86,
            height=26,
            corner_radius=8,
            fg_color=T["bg_surface"],
            button_color=T["bg_hover"],
            button_hover_color=T["border"],
            text_color=T["accent"],
            dropdown_fg_color=T["bg_surface"],
            dropdown_text_color=T["text_pri"],
            dropdown_hover_color=T["bg_hover"],
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            dynamic_resizing=False,
            command=self._on_language_change
        )
        self.lang_menu.set(current_lang_str)
        self.lang_menu.pack(side="right")

        # ── Selector de monitores ────────────────────────────────────────────
        mon_fr = ctk.CTkFrame(card, fg_color=T["bg_surface"], corner_radius=10)
        mon_fr.pack(fill="x", padx=18, pady=(12, 0))

        mon_hdr = ctk.CTkFrame(mon_fr, fg_color=T["bg_surface"])
        mon_hdr.pack(fill="x", padx=12, pady=(8, 4))
        self.monitors_hdr_lbl = ctk.CTkLabel(mon_hdr, text=t("monitors_section"),
                                             font=ctk.CTkFont("Segoe UI", 11, "bold"),
                                             text_color=T["text_sec"])
        self.monitors_hdr_lbl.pack(side="left")

        # Scrollable frame para la lista de monitores
        self._monitor_btns = []
        self._monitor_list_fr = ctk.CTkFrame(mon_fr, fg_color=T["bg_surface"])
        self._monitor_list_fr.pack(fill="x", padx=8, pady=(0, 8))

        self._build_monitor_list()

        # ── Porcentaje grande (Tamaño reducido a 40pt) ────────────────────────
        pct_fr = ctk.CTkFrame(card, fg_color=T["bg_card"])
        pct_fr.pack(pady=(12, 0))

        self.pct_lbl = ctk.CTkLabel(pct_fr, text="50%",
                                     font=ctk.CTkFont("Segoe UI", 40, "bold"),
                                     text_color=T["accent"])
        self.pct_lbl.pack()

        self.desc_lbl = ctk.CTkLabel(pct_fr, text=t("brightness_label"),
                                      font=ctk.CTkFont("Segoe UI", 12),
                                      text_color=T["text_sec"])
        self.desc_lbl.pack()

        # ── Slider ───────────────────────────────────────────────────────────
        sl_fr = ctk.CTkFrame(card, fg_color=T["bg_card"])
        sl_fr.pack(fill="x", padx=18, pady=(16, 0))

        icons_row = ctk.CTkFrame(sl_fr, fg_color=T["bg_card"])
        icons_row.pack(fill="x")
        ctk.CTkLabel(icons_row, text="🌑", font=ctk.CTkFont("Segoe UI", 14),
                     text_color=T["text_dim"]).pack(side="left")
        ctk.CTkLabel(icons_row, text="☀", font=ctk.CTkFont("Segoe UI", 18),
                     text_color=T["accent"]).pack(side="right")

        self.slider = ctk.CTkSlider(sl_fr, from_=0, to=100, number_of_steps=100,
                                     fg_color=T["slider_trk"],
                                     progress_color=T["accent"],
                                     button_color=T["accent"],
                                     button_hover_color=T["accent2"],
                                     height=22,
                                     command=self._on_slider)
        self.slider.set(50)
        self.slider.pack(fill="x", pady=(8, 0))
        # Detener la propagación al arrastrar el slider para que no mueva la ventana
        self.slider.bind("<B1-Motion>", lambda e: "break", add="+")

        # ── Botones rapidos de porcentaje ────────────────────────────────────
        qb_fr = ctk.CTkFrame(card, fg_color=T["bg_card"])
        qb_fr.pack(fill="x", padx=18, pady=(12, 0))

        for label, val in [("0%", 0), ("25%", 25), ("50%", 50), ("75%", 75), ("100%", 100)]:
            ctk.CTkButton(qb_fr, text=label, width=48, height=30,
                          fg_color=T["bg_surface"], hover_color=T["bg_hover"],
                          text_color=T["text_sec"], font=ctk.CTkFont("Segoe UI", 11),
                          corner_radius=8,
                          command=lambda v=val: self._set(v)
                          ).pack(side="left", expand=True, padx=2)

        # ── Controles +/- ───────────────────────────────────────────────────
        adj_fr = ctk.CTkFrame(card, fg_color=T["bg_card"])
        adj_fr.pack(fill="x", padx=18, pady=(8, 0))

        btn_data = [
            ("▼6", -6, T["btn_down"]),
            ("▼1", -1, T["btn_down"]),
            ("1▲", +1, T["btn_up"]),
            ("6▲", +6, T["btn_up"]),
        ]
        for label, delta, hover in btn_data:
            ctk.CTkButton(adj_fr, text=label, width=58, height=34,
                          fg_color=T["bg_surface"], hover_color=hover,
                          text_color=T["text_sec"], font=ctk.CTkFont("Segoe UI", 12, "bold"),
                          corner_radius=10,
                          command=lambda d=delta: self._adjust(d)
                          ).pack(side="left", expand=True, padx=2)

        # ── Info hotkeys ─────────────────────────────────────────────────────
        hk_fr = ctk.CTkFrame(card, fg_color=T["bg_surface"], corner_radius=10)
        hk_fr.pack(fill="x", padx=18, pady=(12, 0))

        self.hk_desc_lbls = []
        for keys, desc in [("Ctrl+Alt  ↑↓", t("hk_step_large")),
                            ("Ctrl+Alt  →←", t("hk_step_small"))]:
            row = ctk.CTkFrame(hk_fr, fg_color=T["bg_surface"])
            row.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(row, text=keys,
                         font=ctk.CTkFont("Segoe UI", 11, "bold"),
                         text_color=T["accent"]).pack(side="left")
            desc_lbl = ctk.CTkLabel(row, text=desc,
                                     font=ctk.CTkFont("Segoe UI", 11),
                                     text_color=T["text_sec"])
            desc_lbl.pack(side="right")
            self.hk_desc_lbls.append(desc_lbl)

        # ── Footer ───────────────────────────────────────────────────────────
        ft_fr = ctk.CTkFrame(card, fg_color=T["bg_card"])
        ft_fr.pack(fill="x", padx=18, pady=(14, 18))

        self.startup_var = tk.BooleanVar(value=self.config.is_startup_enabled())
        self.startup_switch = ctk.CTkSwitch(ft_fr, text=t("startup_switch"),
                                             variable=self.startup_var,
                                             font=ctk.CTkFont("Segoe UI", 12),
                                             text_color=T["text_sec"],
                                             button_color=T["accent"],
                                             button_hover_color=T["accent2"],
                                             progress_color=T["accent"],
                                             onvalue=True, offvalue=False,
                                             command=self._toggle_startup
                                             )
        self.startup_switch.pack(side="left")

        self.exit_btn = ctk.CTkButton(ft_fr, text=t("exit_btn"), width=64, height=28,
                                       fg_color=T["bg_card"], hover_color=T["quit_hover"],
                                       text_color=T["text_sec"], font=ctk.CTkFont("Segoe UI", 11),
                                       corner_radius=8,
                                       command=self._quit
                                       )
        self.exit_btn.pack(side="right")

        # Estado DDC/CI — manejado en la lista de monitores (_build_monitor_list)

        self.win.bind("<FocusOut>", self._on_focus_out)

    # ── Lista de monitores ───────────────────────────────────────────────────
    def _build_monitor_list(self):
        T = self.T
        # Limpiar botones anteriores
        for btn in self._monitor_btns:
            btn.destroy()
        self._monitor_btns.clear()

        bc = self.brightness_ctrl
        ddc = bc.ddc_monitors  # Solo monitores activos y controlables

        if not ddc:
            lbl = ctk.CTkLabel(self._monitor_list_fr, text=t("no_monitors_found"),
                               font=ctk.CTkFont("Segoe UI", 11),
                               text_color=T["text_dim"])
            lbl.pack(fill="x", pady=2)
            self._monitor_btns.append(lbl)
            return

        # Boton "Todos" (solo si hay mas de 1 monitor activo)
        if len(ddc) > 1:
            is_active = bc.target_index == TARGET_ALL
            btn = ctk.CTkButton(
                self._monitor_list_fr,
                text=t("all_monitors", count=len(ddc)),
                height=32,
                fg_color=T["monitor_act"] if is_active else T["bg_surface"],
                hover_color=T["monitor_sel"],
                text_color=T["accent"] if is_active else T["text_sec"],
                font=ctk.CTkFont("Segoe UI", 11, "bold" if is_active else "normal"),
                corner_radius=8, anchor="w",
                command=lambda: self._select_monitor(TARGET_ALL)
            )
            btn.pack(fill="x", pady=1)
            self._monitor_btns.append(btn)

        # Un boton por cada monitor activo
        for mi in ddc:
            is_active = bc.target_index == mi.index
            icon = "🟢"

            btn = ctk.CTkButton(
                self._monitor_list_fr,
                text=f"{icon}  {mi.name}:  {mi.brightness}%",
                height=30,
                fg_color=T["monitor_act"] if is_active else T["bg_surface"],
                hover_color=T["monitor_sel"],
                text_color=T["accent"] if is_active else T["text_sec"],
                font=ctk.CTkFont("Segoe UI", 11, "bold" if is_active else "normal"),
                corner_radius=8, anchor="w",
                command=lambda idx=mi.index: self._select_monitor(idx)
            )
            btn.pack(fill="x", pady=1)
            self._monitor_btns.append(btn)

    def _select_monitor(self, index: int):
        """Cambia el monitor objetivo y refresca la UI."""
        self.brightness_ctrl.set_target(index)
        self._build_monitor_list()
        brightness = self.brightness_ctrl.current
        self._update_ui(brightness)

    def _on_language_change(self, selected_str: str):
        """Callback cuando el usuario cambia la opción en el selector de idioma."""
        mode_map = {"ES": "es", "EN": "en"}
        mode = mode_map.get(selected_str, "es")
        self.config.set("language", mode)
        set_language_mode(mode)
        self._retranslate_ui()
        if self.tray_app:
            self.tray_app.update_tray_menu()

    def _retranslate_ui(self):
        """Actualiza dinámicamente los textos traducibles de la UI."""
        if not CTK_AVAILABLE:
            return

        if hasattr(self, "lang_lbl"):
            self.lang_lbl.configure(text=t("language_label"))
        self.monitors_hdr_lbl.configure(text=t("monitors_section"))
        self.desc_lbl.configure(text=t("brightness_label"))
        self.startup_switch.configure(text=t("startup_switch"))
        self.exit_btn.configure(text=t("exit_btn"))

        if len(self.hk_desc_lbls) >= 2:
            self.hk_desc_lbls[0].configure(text=t("hk_step_large"))
            self.hk_desc_lbls[1].configure(text=t("hk_step_small"))

        self._build_monitor_list()

    # ── Fallback TK puro ─────────────────────────────────────────────────────
    def _build_tk(self):
        """Version de respaldo con tkinter puro."""
        T = self.T
        self.win = tk.Toplevel(self.root)
        self.win.title("ShortcutsScreenBrightness")
        self.win.geometry(f"{self.WIN_W}x{self.WIN_H}")
        self.win.configure(bg=T["bg_card"])
        self.win.resizable(False, False)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.withdraw()

        tk.Label(self.win, text="ShortcutsScreenBrightness", bg=T["bg_card"], fg=T["accent"],
                 font=("Segoe UI", 14, "bold")).pack(pady=(20, 4))
        self.status_lbl = tk.Label(self.win, text="DDC/CI", bg=T["bg_card"], fg=T["text_sec"],
                                    font=("Segoe UI", 11))
        self.status_lbl.pack()

        self.pct_lbl = tk.Label(self.win, text="50%", bg=T["bg_card"], fg=T["accent"],
                                 font=("Segoe UI", 48, "bold"))
        self.pct_lbl.pack(pady=(20, 0))

        self.sun_cv = tk.Canvas(self.win, width=42, height=42,
                                bg=T["bg_card"], highlightthickness=0)
        self.sun_cv.pack()
        self._draw_sun(50)

        self.slider_var = tk.IntVar(value=50)
        self.slider = tk.Scale(self.win, from_=0, to=100, orient="horizontal",
                               variable=self.slider_var, length=250,
                               bg=T["bg_card"], fg=T["accent"], highlightbackground=T["bg_card"],
                               troughcolor=T["slider_trk"], activebackground=T["accent2"],
                               command=lambda v: self._on_slider(int(v)))
        self.slider.pack(pady=(10, 0))

        btn_fr = tk.Frame(self.win, bg=T["bg_card"])
        btn_fr.pack(pady=8)
        for txt, d in [("▼6", -6), ("▼1", -1), ("1▲", +1), ("6▲", +6)]:
            tk.Button(btn_fr, text=txt, bg=T["bg_surface"], fg=T["text_sec"],
                      font=("Segoe UI", 11), relief="flat",
                      command=lambda dv=d: self._adjust(dv)).pack(side="left", padx=3)

        tk.Button(self.win, text="Salir", bg=T["bg_surface"], fg=T["error"],
                  font=("Segoe UI", 11), relief="flat",
                  command=self._quit).pack(pady=10)

        self.win.bind("<FocusOut>", self._on_focus_out)
        self.startup_var = tk.BooleanVar(value=self.config.is_startup_enabled())
        self._monitor_btns = []

    # ── Sol animado ──────────────────────────────────────────────────────────
    def _draw_sun(self, brightness: int):
        T = self.T
        c = self.sun_cv
        c.delete("all")
        c.configure(bg=T["bg_card"])
        cx, cy = 21, 21
        t = max(0.05, brightness / 100.0)
        r = int(80 + 175 * t)
        g = int(50 + 135 * t)
        b = int(10 + 40 * t)
        color = f"#{min(255, r):02x}{min(255, g):02x}{min(255, b):02x}"

        for i in range(8):
            ang = i * 45 * math.pi / 180
            x1 = cx + 12 * math.cos(ang)
            y1 = cy + 12 * math.sin(ang)
            x2 = cx + 20 * math.cos(ang)
            y2 = cy + 20 * math.sin(ang)
            c.create_line(x1, y1, x2, y2, fill=color, width=2, capstyle="round")

        c.create_oval(cx - 9, cy - 9, cx + 9, cy + 9, fill=color, outline="")

    # ── Callbacks ────────────────────────────────────────────────────────────
    def _on_slider(self, value):
        """Callback del slider - actualiza UI al instante, hardware con debounce."""
        v = int(float(value))
        self.brightness_ctrl.set_brightness(v)
        self._update_ui(v)

    def _set(self, value: int):
        value = max(0, min(100, value))
        self.brightness_ctrl.set_brightness(value)
        self._update_ui(value)

    def _adjust(self, delta: int):
        new_val = self.brightness_ctrl.adjust(delta)
        self._update_ui(new_val)

    def _update_ui(self, brightness: int):
        T = self.T
        self._draw_sun(brightness)
        color = _hex_lerp(T["accent_dim"], T["accent"], max(0.1, brightness / 100))
        if CTK_AVAILABLE:
            self.pct_lbl.configure(text=f"{brightness}%", text_color=color)
            self.slider.set(brightness)
            self._build_monitor_list()
        else:
            self.pct_lbl.configure(text=f"{brightness}%", fg=color)
            self.slider_var.set(brightness)

    def update_brightness_display(self, brightness: int):
        """Actualiza la UI desde cualquier hilo de forma segura."""
        self.root.after(0, lambda: self._update_ui(brightness))

    def _toggle_startup(self):
        self.config.set_startup(self.startup_var.get())

    def _quit(self):
        self.win.withdraw()
        self.quit_callback()

    def _on_focus_out(self, _event=None):
        if self._focus_timer:
            self.root.after_cancel(self._focus_timer)
        self._focus_timer = self.root.after(150, self._check_and_hide)

    def _check_and_hide(self):
        try:
            if self.visible and self.win.focus_get() is None:
                self.hide()
        except Exception:
            pass

    # ── Detección en caliente (Hot-Plug) de pantallas ─────────────────────────
    def _start_hotplug_check(self):
        """Inicia el temporizador periódico para detectar conexión/desconexión de monitores."""
        self.root.after(2500, self._check_hotplug)

    def _check_hotplug(self):
        """Verifica en segundo plano si cambió la lista de monitores."""
        def _bg_scan():
            try:
                changed = self.brightness_ctrl.rescan_monitors()
                if changed:
                    self.root.after(0, self._on_monitors_changed)
            except Exception as e:
                print(f"[UI] Error en rescan hotplug: {e}")
            finally:
                self.root.after(2500, self._check_hotplug)

        import threading
        threading.Thread(target=_bg_scan, daemon=True).start()

    def _on_monitors_changed(self):
        """Callback ejecutado en el hilo principal de la UI cuando cambian los monitores."""
        brightness = self.brightness_ctrl.current
        self._update_ui(brightness)
        if CTK_AVAILABLE:
            self._build_monitor_list()

    # ── Mostrar / Ocultar ────────────────────────────────────────────────────
    def show(self):
        """Muestra la ventana usando cache (instantaneo)."""
        # Detectar tema del SO al abrir
        new_theme = _detect_system_theme()
        if CTK_AVAILABLE and new_theme != ctk.get_appearance_mode().lower():
            ctk.set_appearance_mode(new_theme)
        self.T = _get_theme()

        # Rescanear monitores al abrir por si hubo cambios mientras estaba oculta
        self.brightness_ctrl.rescan_monitors()

        brightness = self.brightness_ctrl.current
        self._update_ui(brightness)

        if CTK_AVAILABLE:
            self._build_monitor_list()

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = sw - self.WIN_W - 14
        y = sh - self.WIN_H - self.TASKBAR_H

        self.win.geometry(f"{self.WIN_W}x{self.WIN_H}+{x}+{y}")
        self.win.deiconify()
        self.win.lift()
        self.win.focus_force()
        self.visible = True

        self.brightness_ctrl.refresh_from_hardware()

    def hide(self):
        self.win.withdraw()
        self.visible = False

    def toggle(self):
        if self.visible:
            self.hide()
        else:
            self.show()
