# ShortcutsScreenBrightness ☀️

Una aplicación ligera, elegante y moderna para la bandeja del sistema de Windows (11, 10, 8, 7, XP) que permite controlar el brillo de monitores internos y externos mediante el protocolo estándar **DDC/CI** (Display Data Channel / Command Interface) y atajos de teclado globales.

![Windows 11 Compatible](https://img.shields.io/badge/Windows-10%20%2F%2011-blue?logo=windows)
![Python Version](https://img.shields.io/badge/Python-3.9%2B-green?logo=python)
![i18n Supported](https://img.shields.io/badge/i18n-ES%20%7C%20EN-orange)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ Características Principales

- 🖥️ **Soporte Multi-Monitor con Detección EDID 1:1**: Identifica con precisión los monitores físicamente conectados mostrando su número y modelo real (ej. `Monitor 1 - (Integrated Monitor)` / `Monitor 2 - (P2712V)` Titan Army, Dell, LG, ASUS, Samsung, BenQ, etc.).
- 🔄 **Sincronización en Tiempo Real**: Al deslizar la barra de brillo o presionar hotkeys, el valor del monitor y de la lista se actualiza instantáneamente en el mismo milisegundo.
- 🌐 **Multilingüe Automático y Selector de Idioma (ES / EN)**:
  - Detecta automáticamente el idioma de la interfaz del sistema operativo Windows (`GetUserDefaultUILanguage`).
  - Incluye un selector desplegable en la aplicación para alternar entre **Español (ES)** e **Inglés (EN)** en tiempo real.
  - Sincroniza dinámicamente tanto los elementos visuales de la ventana como el menú contextual del **System Tray**.
- 🖐️ **Ventana Flotante Arrastrable (Window Dragging)**: Haz clic y arrastra libremente la aplicación a cualquier pantalla o posición del monitor. Los controles de brillo (slider y botones) están aislados para no mover la ventana al usarlos.
- 🎨 **Tema Adaptativo de Sistema (Dark / Light Mode)**: Paleta de colores HSL que detecta y se adapta automáticamente al tema claro u oscuro de Windows (`darkdetect`).
- ⚡ **Arquitectura Anti-Delay (Debounced I/O)**: Respuesta de interfaz a 0ms mediante caché local, enviando comandos DDC/CI al hardware tras 80ms de inactividad para proteger los monitores.
- ⌨️ **Atajos de Teclado Globales**:
  - `Ctrl + Alt + Flecha Arriba` ➔ Incrementar brillo (+6%)
  - `Ctrl + Alt + Flecha Abajo` ➔ Disminuir brillo (-6%)
  - `Ctrl + Alt + Flecha Derecha` ➔ Incrementar brillo (+1%)
  - `Ctrl + Alt + Flecha Izquierda` ➔ Disminuir brillo (-1%)
- 🔔 **Notificación OSD Flotante**: Indicador visual discreto sobre la pantalla al ajustar el brillo con el teclado.
- 📌 **Integración en la Bandeja del Sistema**: Ícono en la barra de tareas con menú traducible al instante.
- ⚙️ **Inicio Automático con Windows**: Registro en el arranque del sistema.

---

## 🌐 Compatibilidad de Monitores y Marcas

**ShortcutsScreenBrightness** es compatible con prácticamente cualquier monitor del mercado (Titan Army, Dell, LG, ASUS, Acer, Samsung, BenQ, AOC, ViewSonic, Gigabyte, etc.).

### Requisitos de Hardware:
1. **DDC/CI Activado en el OSD del Monitor**:
   - En el menú físico de tu monitor, comprueba que **DDC/CI** esté en **Activado / On**.
2. **Conexión Compatible**:
   - **DisplayPort / HDMI / DVI / VGA**: Soporte nativo de DDC/CI.
   - **USB-C / Thunderbolt**: Requiere cable/puerto compatible con **DisplayPort Alt Mode**.

---

## 🛠️ Instalación y Ejecución

### Opción 1: Ejecutar desde el código fuente (Python)

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/yprevot/ShortcutsScreenBrightness.git
   cd ShortcutsScreenBrightness
   ```
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
   *(O ejecutando `install.bat`)*

3. Iniciar la aplicación:
   ```bash
   python src/main.py
   ```

### Opción 2: Compilar Ejecutable `.exe`

Para generar una versión ejecutable sin necesidad de tener Python instalado:
```cmd
build.bat
```
El ejecutable binario se generará en la carpeta `dist/ShortcutsScreenBrightness/ShortcutsScreenBrightness.exe`.

---

## 📦 Estructura del Código

```
ShortcutsScreenBrightness/
├── src/
│   ├── main.py           # Punto de entrada y prevención de instancias duplicadas
│   ├── i18n.py           # Diccionarios y motor de traducción multilingüe (ES / EN)
│   ├── ui_window.py      # Interfaz gráfica CustomTkinter + OSD + Arrastre de ventana
│   ├── brightness_ctrl.py# Controlador DDC/CI multi-monitor, lector EDID y debouncing
│   ├── hotkeys.py        # Captura de atajos globales del teclado
│   ├── tray_app.py       # Menú e ícono dinámico en la bandeja del sistema
│   ├── icon_maker.py     # Generación dinámica del ícono de bandeja
│   └── config.py         # Gestión de preferencias e inicio automático
├── install.bat           # Instalador automático de entorno
├── build.bat             # Compilador de ejecutable PyInstaller
├── requirements.txt      # Dependencias del proyecto
└── README.md             # Documentación oficial
```

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.
