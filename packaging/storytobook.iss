; Inno Setup script for the StoryToBook Windows installer.
;
; Build it with:
;     iscc /DMyAppDir=..\dist\StoryToBook /DMyVersion=1.0.0 packaging\storytobook.iss
;
; The resulting Setup.exe is a normal installer: it adds a Start Menu entry,
; an optional desktop shortcut and an uninstaller.

#ifndef MyAppDir
  #define MyAppDir "..\dist\StoryToBook"
#endif

#ifndef MyVersion
  #define MyVersion "1.0.0"
#endif

#define MyAppName "StoryToBook"
#define MyAppExeName "StoryToBook.exe"
#define MyPublisher "StoryToBook contributors"
#define MyURL "https://github.com/Manohargov/StoryToBookApp"

[Setup]
AppId={{7C3F6C58-1E4E-4B2A-9D2F-3A5B8C9D0E11}
AppName={#MyAppName}
AppVersion={#MyVersion}
AppVerName={#MyAppName} {#MyVersion}
AppPublisher={#MyPublisher}
AppPublisherURL={#MyURL}
AppSupportURL={#MyURL}
AppUpdatesURL={#MyURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=..\dist\installer
OutputBaseFilename=StoryToBook-{#MyVersion}-windows-x64-setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=..\packaging\assets\StoryToBook.ico
LicenseFile=..\LICENSE
CloseApplications=yes
RestartApplications=no
VersionInfoVersion={#MyVersion}
VersionInfoCompany={#MyPublisher}
VersionInfoDescription={#MyAppName} installer
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyVersion}
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "{#MyAppDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion isreadme
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Start {#MyAppName}"; Flags: nowait postinstall skipifsilent
