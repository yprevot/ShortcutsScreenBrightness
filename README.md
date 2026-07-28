# ShortcutsScreenBrightness ☀️

Una aplicación ligera y moderna para la bandeja del sistema de Windows 10/11 que permite controlar el brillo de monitores externos mediante el protocolo estándar **DDC/CI** (Display Data Channel / Command Interface) y atajos de teclado globales.

![Windows 11 Compatible](https://img.shields.io/badge/Windows-10%20%2F%2011-blue?logo=windows)
![Python Version](https://img.shields.io/badge/Python-3.9%2B-green?logo=python)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ Características

- 🖥️ **Soporte Multi-Monitor Universal**: Detecta y permite ajustar el brillo de cualquier monitor compatible con DDC/CI (Titan Army, Dell, LG, ASUS, Samsung, BenQ, AOC, etc.).
- 🚀 **Control Individual o Global**: Selecciona un monitor específico o la opción *"Todos los monitores"* para ajustar todos a la vez.
- 🎨 **Tema Dinámico (Light / Dark)**: Se sincroniza automáticamente con el tema del sistema operativo Windows.
- ⚡ **Respuesta Instantánea (Debounced I/O)**: La interfaz responde al instante mediante caché interno, eliminando retrasos al deslizar la barra de brillo.
- ⌨️ **Atajos de Teclado Globales**:
  - `Ctrl + Alt + Flecha Arriba` ➔ Incrementar brillo (+6%)
  - `Ctrl + Alt + Flecha Abajo` ➔ Disminuir brillo (-6%)
  - `Ctrl + Alt + Flecha Derecha` ➔ Incrementar brillo (+1%)
  - `Ctrl + Alt + Flecha Izquierda` ➔ Disminuir brillo (-1%)
- 🔔 **Notificación OSD Flotante**: Muestra un indicador visual discreto en pantalla al cambiar el brillo usando teclas de acceso rápido.
- 📌 **Integración en Bandeja del Sistema**: Ícono interactivo en la barra de tareas de Windows.
- ⚙️ **Inicio Automático**: Opción para iniciar automáticamente al encender Windows.

---

## 🌐 Compatibilidad con otros monitores y marcas

**Sí, es totalmente funcional con monitores de prácticamente cualquier marca** (Dell, LG, ASUS, Acer, Samsung, BenQ, AOC, ViewSonic, Gigabyte, etc.).

### Requisitos de Hardware y Conexión:
1. **DDC/CI Activado en el OSD del Monitor**:
   - En el menú físico del monitor (OSD), asegúrate de que la opción **DDC/CI** esté en **On / Activado**.
2. **Tipo de Conexión Compatible**:
   - **DisplayPort / HDMI / DVI / VGA**: Soporte nativo de DDC/CI.
   - **USB-C / Thunderbolt**: Funciona siempre que el cable/puerto soporte **DisplayPort Alt Mode**.

---

## 🛠️ Instalación y Uso

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
   *(O bien ejecutando `install.bat`)*

3. Iniciar la aplicación:
   ```bash
   python src/main.py
   ```

### Opción 2: Compilar como ejecutable `.exe` independiente

Para generar un archivo ejecutable que no requiera Python instalado:
```cmd
build.bat
```
El ejecutable generado se guardará en `dist/ShortcutsScreenBrightness/ShortcutsScreenBrightness.exe`.

---

## 📦 Estructura del Proyecto

```
ShortcutsScreenBrightness/
├── src/
│   ├── main.py           # Punto de entrada y gestión de hilos
│   ├── ui_window.py      # Interfaz gráfica CustomTkinter + OSD + Temas
│   ├── brightness_ctrl.py# Controlador DDC/CI multi-monitor y debounce
│   ├── hotkeys.py        # Captura de atajos de teclado globales
│   ├── tray_app.py       # Menú e ícono en la bandeja del sistema
│   ├── icon_maker.py     # Generador dinámico de íconos
│   └── config.py         # Configuración y registro de inicio automático
├── install.bat           # Script para instalación de dependencias
├── build.bat             # Script para compilar ejecutable PyInstaller
├── requirements.txt      # Dependencias de Python
└── README.md             # Documentación del proyecto
```

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.
