@echo off
chcp 65001 >nul
echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║   ShortcutsScreenBrightness — Instalador de dependencias ║
echo  ║   Monitor Titan Army P2712V                              ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

:: Verificar que Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python no encontrado. Descárgalo de https://python.org
    pause
    exit /b 1
)

echo  [OK] Python detectado.
echo.
echo  Instalando dependencias...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo  [ERROR] Falló la instalación de algunas dependencias.
    echo  Intenta ejecutar como Administrador.
    pause
    exit /b 1
)

echo.
echo  ═══════════════════════════════════════════════════
echo  [OK] Instalación completada.
echo.
echo  Para iniciar la app:
echo     python src\main.py
echo.
echo  Para compilar a .exe:
echo     build.bat
echo  ═══════════════════════════════════════════════════
echo.
pause
