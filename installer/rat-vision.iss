#ifndef MyAppVersion
  #define MyAppVersion "1.2.0-beta.1"
#endif
#define MyAppName "RAT VISION"
#define MyAppExeName "RAT VISION.exe"

[Setup]
AppId={{643B70D9-1E56-4E6D-B2AC-73C1DD6F9714}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=RAT VISION
DefaultDirName={localappdata}\Programs\RAT VISION
DefaultGroupName=RAT VISION
PrivilegesRequired=lowest
OutputDir=..\release\out
OutputBaseFilename=RAT-VISION-Setup-v{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\ratvision\resources\brand\ratvision.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\RAT VISION\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\third_party\licenses\*"; DestDir: "{app}\third_party\licenses"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\RAT VISION"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\RAT VISION"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch RAT VISION"; Flags: nowait postinstall skipifsilent
Filename: "{app}\{#MyAppExeName}"; Parameters: ""; Flags: nowait skipifdoesntexist; Check: ShouldRelaunch

[Code]
function ShouldRelaunch(): Boolean;
begin
  Result := ExpandConstant('{param:RELAUNCH|0}') = '1';
end;
