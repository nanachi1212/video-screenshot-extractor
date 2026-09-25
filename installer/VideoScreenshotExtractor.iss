; Script generated for Video Screenshot Extractor (影片配圖擷取器)
#ifndef MyAppVersion
#define MyAppVersion "2.8.0"
#endif

#define MyAppName "Video Screenshot Extractor"
#define MyAppNameZh "影片配圖擷取器"
#define MyAppPublisher "nanachi1212"
#define MyAppURL "https://github.com/nanachi1212/video-screenshot-extractor"
#define MyAppExeName "VideoScreenshotExtractor.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{D1A39D9B-F4E5-4C82-9B7E-97F29906666E}
AppName={#MyAppNameZh}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppNameZh}
AllowNoIcons=yes
OutputDir=..\release
OutputBaseFilename=VideoScreenshotExtractor-Setup-v{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\VideoScreenshotExtractor\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppNameZh}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppNameZh}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppNameZh}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppNameZh}}"; Flags: nowait postinstall skipifsilent
