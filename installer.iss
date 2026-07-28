; Script de Inno Setup para ShortcutsScreenBrightness
; #define MyAppVersion "1.0.0"

[Setup]
AppId={{E6B5D7A1-4F2A-4B8C-9E1D-7C8A9F0E1D2C}
AppName=ShortcutsScreenBrightness
AppVersion=1.0.0
AppPublisher=yprevot
AppPublisherURL=https://github.com/yprevot/ShortcutsScreenBrightness
AppSupportURL=https://github.com/yprevot/ShortcutsScreenBrightness
AppUpdatesURL=https://github.com/yprevot/ShortcutsScreenBrightness
DefaultDirName={autopf}\ShortcutsScreenBrightness
DefaultGroupName=ShortcutsScreenBrightness
DisableProgramGroupPage=yes
LicenseFile=LICENSE
OutputBaseFilename=ShortcutsScreenBrightness_Setup_v1.0.0
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\ShortcutsScreenBrightness.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\ShortcutsScreenBrightness\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ShortcutsScreenBrightness"; Filename: "{app}\ShortcutsScreenBrightness.exe"
Name: "{group}\{cm:UninstallProgram,ShortcutsScreenBrightness}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\ShortcutsScreenBrightness"; Filename: "{app}\ShortcutsScreenBrightness.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\ShortcutsScreenBrightness.exe"; Description: "{cm:LaunchProgram,ShortcutsScreenBrightness}"; Flags: nowait postinstall skipifsilent
