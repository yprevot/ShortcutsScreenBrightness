# ShortcutsScreenBrightness ☀️

Una aplicación ligera, elegante y moderna para la bandeja del sistema de Windows (11, 10, 8, 7, XP) que permite controlar el brillo de monitores internos y externos mediante el protocolo estándar **DDC/CI** (Display Data Channel / Command Interface) y atajos de teclado globales.

![Windows 11 Compatible](https://img.shields.io/badge/Windows-10%20%2F%2011-blue?logo=windows)
![Python Version](https://img.shields.io/badge/Python-3.9%2B-green?logo=python)
![i18n Supported](https://img.shields.io/badge/i18n-ES%20%7C%20EN-orange)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ Características Principales

- 💻 **Soporte Multi-Monitor Híbrido (WMI Laptop + DDC/CI Externos)**: Soporte completo e integrado para pantallas de laptop (vía API WMI de Windows `WmiMonitorBrightness`) y monitores externos vía protocolo DDC/CI.
- 🔌 **Autodetección en Caliente (Hot-Plug & Unplug)**: Detecta automáticamente cuando conectas o desconectas una segunda, tercera o cuarta pantalla en tiempo real sin necesidad de reiniciar la aplicación.
- 🏷️ **Mapeo EDID 1:1 e Identificación Precisa**: Mapeo exacto vía `EnumDisplayMonitors` para evitar intercambio de nombres entre la pantalla de la laptop y los monitores externos, identificando el modelo real (ej. `Monitor 1 - (Integrated Monitor)` / `Monitor 2 - (P2712V)`).
- 🔢 **Numeración Secuencial Limpia**: Muestra únicamente las pantallas activas y controlables ordenadas limpiamente (Monitor 1, Monitor 2...).
- 🔄 **Sincronización en Tiempo Real**: Al deslizar la barra de brillo o presionar hotkeys, el valor del monitor y de la lista se actualiza instantáneamente en el mismo milisegundo.
- 🌐 **Multilingüe Automático y Selector de Idioma (ES / EN)**:
  - Detecta automáticamente el idioma de la interfaz del sistema operativo Windows (`GetUserDefaultUILanguage`).
  - Selector desplegable para alternar entre **Español (ES)** e **Inglés (EN)** en tiempo real.
  - Sincroniza dinámicamente tanto la ventana como el menú contextual del **System Tray**.
- 🖐️ **Ventana Flotante Arrastrable (Window Dragging)**: Haz clic y arrastra libremente la aplicación a cualquier pantalla o posición del monitor con aislamiento inteligente de controles.
- 🎨 **Tema Adaptativo de Sistema (Dark / Light Mode)**: Paleta de colores HSL que se adapta automáticamente al tema claro u oscuro de Windows (`darkdetect`).
- ⚡ **Arquitectura Anti-Delay (Debounced I/O)**: Respuesta de interfaz a 0ms mediante caché local, enviando comandos al hardware tras 80ms de inactividad.
- ⌨️ **Atajos de Teclado Globales**:
  - `Ctrl + Alt + Flecha Arriba` ➔ Incrementar brillo (+6%)
  - `Ctrl + Alt + Flecha Abajo` ➔ Disminuir brillo (-6%)
  - `Ctrl + Alt + Flecha Derecha` ➔ Incrementar brillo (+1%)
  - `Ctrl + Alt + Flecha Izquierda` ➔ Disminuir brillo (-1%)
- 🔔 **Notificación OSD Flotante**: Indicador visual discreto sobre la pantalla al ajustar el brillo con el teclado.
- 📌 **Integración en la Bandeja del Sistema**: Ícono en la barra de tareas con menú traducible.
- ⚙️ **Inicio Automático con Windows**: Registro en el arranque del sistema.

---

## 💻 Guía de Ejecución en Entorno Local (Desarrollo)

Sigue estos pasos para clonar, instalar y ejecutar **ShortcutsScreenBrightness** en tu computadora local.

### 📋 Requisitos Previos

- **Sistema Operativo**: Windows 10, Windows 11 (compatible también con Windows 7 y 8).
- **Python**: Versión 3.9 o superior. Puedes descargarlo desde [python.org](https://www.python.org/downloads/). *(Asegúrate de marcar la casilla "Add Python to PATH" durante la instalación)*.

---

### 🚀 Pasos para Ejecutar Localmente

#### 1. Clonar el Repositorio
Abre la consola de comandos (PowerShell / CMD) y ejecuta:
```bash
git clone https://github.com/yprevot/ShortcutsScreenBrightness.git
cd ShortcutsScreenBrightness
```

#### 2. Crear un Entorno Virtual (Opcional pero Recomendado)
Para mantener limpias las dependencias de tu sistema:
```bash
# Crear entorno virtual .venv
python -m venv .venv

# Activar el entorno virtual en Windows
.venv\Scripts\activate
```

#### 3. Instalar Dependencias del Proyecto
Puedes instalar las librerías necesarias con el script automático o mediante pip:

- **Opción A (Script Automático)**:
  ```cmd
  install.bat
  ```
- **Opción B (Comando Pip)**:
  ```bash
  pip install -r requirements.txt
  ```

#### 4. Ejecutar la Aplicación en Modo Local
Una vez instaladas las dependencias, inicia la aplicación ejecutando:
```bash
python src/main.py
```
- La aplicación creará un **ícono en la bandeja del sistema (junto al reloj de Windows)**.
- Haz clic en el ícono de la bandeja o presiona `Ctrl + Alt + Flecha Arriba/Abajo` para abrir el panel flotante de control.

---

## 🏗️ Compilación y Creación de Instaladores

### Opción A: Compilar ejecutable portátil (.exe)

Para generar una versión ejecutable sin necesidad de tener Python instalado:
```cmd
build.bat
```
El binario ejecutable se guardará en `dist/ShortcutsScreenBrightness/ShortcutsScreenBrightness.exe`.

### Opción B: Generar el Instalador de Windows (.exe Setup)

El proyecto incluye scripts automáticos para empaquetar un instalador nativo tipo *"Siguiente ➔ Siguiente ➔ Instalar"* usando **Inno Setup**:

1. Descarga e instala [Inno Setup](https://jrsoftware.org/isdl.php) (gratuito).
2. Ejecuta el script de empaquetado:
   ```cmd
   make_installer.bat
   ```
3. El instalador resultante se guardará en `Output/ShortcutsScreenBrightness_Setup_v1.0.0.exe`.

---

## 🌐 Compatibilidad de Monitores y Marcas

**ShortcutsScreenBrightness** funciona con monitores externos de cualquier marca (Titan Army, Dell, LG, ASUS, Acer, Samsung, BenQ, AOC, ViewSonic, Gigabyte, etc.).

### Requisitos de Hardware:
1. **DDC/CI Activado en el OSD del Monitor**:
   - En el menú físico de tu monitor, comprueba que **DDC/CI** esté en **Activado / On**.
2. **Conexión Compatible**:
   - **DisplayPort / HDMI / DVI / VGA**: Soporte nativo de DDC/CI.
   - **USB-C / Thunderbolt**: Requiere cable o puerto compatible con **DisplayPort Alt Mode**.

---

## 📦 Estructura del Proyecto

```
ShortcutsScreenBrightness/
├── src/
│   ├── main.py           # Punto de entrada y prevención de instancias duplicadas
│   ├── i18n.py           # Motor de traducción e internacionalización (ES / EN)
│   ├── ui_window.py      # Interfaz gráfica CustomTkinter, OSD y arrastre de ventana
│   ├── brightness_ctrl.py# Controlador DDC/CI, lector EDID y debouncing
│   ├── hotkeys.py        # Captura de atajos globales de teclado
│   ├── tray_app.py       # Menú e ícono en la bandeja del sistema
│   ├── icon_maker.py     # Generador dinámico de íconos de bandeja
│   └── config.py         # Gestión de preferencias e inicio automático
├── install.bat           # Script de instalación automática de dependencias
├── build.bat             # Script de compilación a ejecutable (.exe)
├── make_installer.bat    # Script de automatización de instalador Inno Setup
├── installer.iss         # Definición de paquete Inno Setup
├── LICENSE               # Licencia MIT oficial
├── requirements.txt      # Archivo de dependencias de Python
├── .gitignore            # Exclusión de archivos de build y temporales
└── README.md             # Documentación oficial del proyecto
```

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.
