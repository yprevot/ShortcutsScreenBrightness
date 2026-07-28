"""
generate_msix_manifest.py - Genera la estructura de manifiesto y assets requeridos
para empaquetar ShortcutsScreenBrightness como paquete MSIX para la Microsoft Store.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from icon_maker import make_tray_icon

PACKAGE_DIR = os.path.join(os.path.dirname(__file__), "msix_package")
ASSETS_DIR  = os.path.join(PACKAGE_DIR, "Assets")

def build_package_structure():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    
    # 1. Generar iconos exigidos por la MS Store en PNG
    sizes = {
        "Square44x44Logo.png": 44,
        "Square150x150Logo.png": 150,
        "StoreLogo.png": 50,
        "Wide310x150Logo.png": (310, 150)
    }
    
    for filename, dim in sizes.items():
        filepath = os.path.join(ASSETS_DIR, filename)
        if isinstance(dim, tuple):
            from PIL import Image, ImageDraw
            img = Image.new("RGBA", dim, (11, 11, 24, 255))
            sun = make_tray_icon(80, size=120)
            img.paste(sun, ((dim[0]-120)//2, (dim[1]-120)//2), sun)
            img.save(filepath)
        else:
            img = make_tray_icon(80, size=dim*2)
            img.save(filepath)
        print(f" [OK] Creado asset: Assets/{filename}")

    # 2. Generar AppxManifest.xml
    manifest_content = """<?xml version="1.0" encoding="utf-8"?>
<Package
  xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
  xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
  xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
  IgnorableNamespaces="uap rescap">

  <Identity
    Name="ShortcutsScreenBrightness"
    Publisher="CN=DEVELOPER_PUBLISHER_ID_HERE"
    Version="1.0.0.0" />

  <Properties>
    <DisplayName>ShortcutsScreenBrightness</DisplayName>
    <PublisherDisplayName>Tu Nombre o Empresa</PublisherDisplayName>
    <Logo>Assets\\StoreLogo.png</Logo>
    <Description>Controlador de brillo moderno para monitores vía DDC/CI con teclas de acceso rápido.</Description>
  </Properties>

  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.17763.0" MaxVersionTested="10.0.22621.0" />
  </Dependencies>

  <Resources>
    <Resource Language="es-es" />
    <Resource Language="en-us" />
  </Resources>

  <Applications>
    <Application Id="ShortcutsScreenBrightnessApp" Executable="ShortcutsScreenBrightness.exe" EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements
        DisplayName="ShortcutsScreenBrightness"
        Description="Control de brillo DDC/CI multi-monitor"
        BackgroundColor="#0b0b18"
        Square150x150Logo="Assets\\Square150x150Logo.png"
        Square44x44Logo="Assets\\Square44x44Logo.png">
        <uap:DefaultTile Wide310x150Logo="Assets\\Wide310x150Logo.png" />
      </uap:VisualElements>
    </Application>
  </Applications>

  <Capabilities>
    <!-- Requerido para aplicaciones Win32 convertidas (acceso a hardware/hotkeys) -->
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>
</Package>
"""
    manifest_path = os.path.join(PACKAGE_DIR, "AppxManifest.xml")
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest_content)
    print(" [OK] AppxManifest.xml generado correctamente.")

if __name__ == "__main__":
    build_package_structure()
