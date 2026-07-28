"""
icon_maker.py - Generador de íconos para ShortcutsScreenBrightness
Crea el ícono de sol para la bandeja del sistema y la ventana.
"""
import math
from PIL import Image, ImageDraw


def _lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    """Interpolación lineal entre dos colores RGBA."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(4))


def make_tray_icon(brightness: int = 50, size: int = 64) -> Image.Image:
    """
    Crea un ícono de sol para la bandeja del sistema.
    El color e intensidad cambian según el nivel de brillo.
    """
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2
    t = max(0.05, brightness / 100.0)

    # Paleta: oscuro → ámbar dorado
    dim    = (80,  50, 10, 255)
    bright = (255, 185, 40, 255)
    color  = _lerp_color(dim, bright, t)

    # Rayos del sol (8 direcciones)
    ray_inner = int(size * 0.28)
    ray_outer = int(size * 0.46)
    ray_width = max(2, int(size * 0.06))

    for i in range(8):
        angle = i * 45 * math.pi / 180
        x1 = cx + ray_inner * math.cos(angle)
        y1 = cy + ray_inner * math.sin(angle)
        x2 = cx + ray_outer * math.cos(angle)
        y2 = cy + ray_outer * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=ray_width)

    # Círculo central
    r = int(size * 0.20)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

    return img.resize((32, 32), Image.LANCZOS)


def save_icon_ico(path: str, brightness: int = 80):
    """Guarda el ícono como .ico para uso en PyInstaller."""
    sizes = [16, 24, 32, 48, 64, 128, 256]
    imgs  = [make_tray_icon(brightness, s) for s in sizes]
    imgs[0].save(path, format="ICO", sizes=[(s, s) for s in sizes],
                 append_images=imgs[1:])
