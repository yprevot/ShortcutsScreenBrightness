@echo off
chcp 65001 >nul
echo.
echo  ==============================================================
echo     ShortcutsScreenBrightness - Crear Instalador de Windows
echo  ==============================================================
echo.

echo  [1/2] Compilando ejecutable con PyInstaller...
call build.bat

echo.
echo  [2/2] Buscando Inno Setup Compiler (ISCC.exe)...

set "ISCC_EXE="
if exist "C:\Program Files\Inno Setup 7\ISCC.exe" set "ISCC_EXE=C:\Program Files\Inno Setup 7\ISCC.exe"
if exist "C:\Program Files (x86)\Inno Setup 7\ISCC.exe" set "ISCC_EXE=C:\Program Files (x86)\Inno Setup 7\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if not defined ISCC_EXE goto :no_iscc

echo  Ejecutando Inno Setup Compiler desde: "%ISCC_EXE%"
"%ISCC_EXE%" installer.iss

if errorlevel 1 goto :err_inno

echo.
echo  ==============================================================
echo   [OK] INSTALADOR CREADO CON EXITO!
echo   Archivo de instalacion listo en:
echo   Output\ShortcutsScreenBrightness_Setup_v1.0.0.exe
echo  ==============================================================
echo.
goto :done

:no_iscc
echo.
echo  [!] Inno Setup Compiler no se encontro.
echo      Descarga e instala Inno Setup desde: https://jrsoftware.org/isdl.php
echo.
goto :done

:err_inno
echo.
echo  [X] Error durante la creacion del instalador.
echo.

:done
