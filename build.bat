@echo off
chcp 65001 >nul
echo.
echo  ==============================================================
echo     ShortcutsScreenBrightness - Compilar a .exe standalone
echo  ==============================================================
echo.

:: 1. Verificar PyInstaller
python -c "import PyInstaller" 2>NUL
if %errorlevel% neq 0 (
    echo  [!] PyInstaller no esta instalado. Instalando...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo  [X] Error instalando PyInstaller.
        pause
        exit /b 1
    )
)

:: 2. Generar icono si no existe
if not exist "assets\icon.ico" (
    echo  Generando icono de la aplicacion...
    python -c "import sys; sys.path.insert(0, 'src'); from icon_maker import save_icon_ico; save_icon_ico('assets/icon.ico')"
)

:: 3. Compilar con PyInstaller
echo.
echo  Compilando ShortcutsScreenBrightness.exe...
echo.

pyinstaller --noconfirm --onedir --windowed --name "ShortcutsScreenBrightness" --icon "assets\icon.ico" --paths "src" --collect-all "customtkinter" --collect-all "darkdetect" --clean src\main.py

if %errorlevel% neq 0 (
    echo.
    echo  [X] Error durante la compilacion.
    pause
    exit /b 1
)

echo.
echo  ==============================================================
echo   [OK] Compilacion completada con exito.
echo   Ejecutable en:
echo   dist\ShortcutsScreenBrightness\ShortcutsScreenBrightness.exe
echo  ==============================================================
echo.
