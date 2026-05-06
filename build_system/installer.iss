; ===========================================================================
; Dofusinator Installer (Inno Setup)
; ===========================================================================
;
; Pre-requisitos pra compilar este script:
;   1. Compile o .exe primeiro com: pyinstaller Dofusinator.spec
;   2. Inno Setup 6.1+ instalado (https://jrsoftware.org/isdl.php)
;
; Pra compilar:
;   - GUI: abrir este .iss no Inno Setup, F9
;   - CLI: iscc.exe installer.iss
;
; Output: dist/DofusinatorSetup.exe

#define APP_NAME "Dofusinator"
#define APP_VERSION "1.0.34"
#define APP_PUBLISHER "@afkdino"
#define APP_COPYRIGHT "Copyright (c) 2026 Guilherme G. Ferreira"
#define APP_DESCRIPTION "Dofusinator - Real-time chat translator for Dofus Retro (FR/PT/EN/ES)"
#define APP_EXE "Dofusinator.exe"
#define APP_GUID "{{A7F3E2D8-5C4B-4F1E-9D7A-3B8E6F2C9A0E}"

[Setup]
; AppId precisa ser um GUID unico - identifica esta versao no registry
AppId={#APP_GUID}
AppName={#APP_NAME}
AppVersion={#APP_VERSION}
AppVerName={#APP_NAME} {#APP_VERSION}
AppPublisher={#APP_PUBLISHER}
AppCopyright={#APP_COPYRIGHT}
AppComments={#APP_DESCRIPTION}

; Instala em AppData\Local (nao precisa admin)
DefaultDirName={localappdata}\{#APP_NAME}
DefaultGroupName={#APP_NAME}
DisableProgramGroupPage=auto
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Output
OutputDir=..\dist
OutputBaseFilename=DofusinatorSetup_{#APP_VERSION}
Compression=lzma2/ultra
SolidCompression=yes

; Visual customizado com identidade Dofusinator
WizardStyle=modern
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#APP_EXE}
DisableWelcomePage=no
DisableReadyPage=no

; Imagens customizadas (BMP) com identidade do app
; - WizardImageFile: lateral grande (164×314) — gradiente + logo + texto
; - WizardSmallImageFile: header pequeno (55×58) — ícone do app
;
; v1.0.18+: arte mais elaborada (gradiente, vignette, ornamentos, tipografia)
; WizardImageStretch=no preserva nitidez em high-DPI (sem esticar bitmap).
; WizardImageBackColor matchea a cor do topo do gradiente — preenche qualquer
; padding restante de forma invisível, dando efeito edge-to-edge natural.
WizardImageFile=..\assets\installer_wizard_image.bmp
WizardSmallImageFile=..\assets\installer_wizard_small_image.bmp
WizardImageStretch=no
WizardImageBackColor=$172436

; Idioma
; ShowLanguageDialog=auto faz o instalador detectar o idioma do Windows
; e oferecer escolha entre os disponíveis
ShowLanguageDialog=auto

[Languages]
; 4 idiomas suportados (mesmos do app)
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[CustomMessages]
; Mensagens customizadas traduzidas em 4 idiomas
; Usa o prefixo do idioma: pt-BR=brazilianportuguese, en=english, fr=french, es=spanish

brazilianportuguese.DesktopIconDesc=Criar atalho na &area de trabalho
english.DesktopIconDesc=Create a &desktop shortcut
french.DesktopIconDesc=Cr&eer un raccourci sur le bureau
spanish.DesktopIconDesc=Crear acceso directo en el e&scritorio

brazilianportuguese.StartupIconDesc=Iniciar o {#APP_NAME} junto com o Windows
english.StartupIconDesc=Start {#APP_NAME} with Windows
french.StartupIconDesc=Demarrer {#APP_NAME} avec Windows
spanish.StartupIconDesc=Iniciar {#APP_NAME} con Windows

brazilianportuguese.AdditionalShortcutsGroup=Atalhos adicionais:
english.AdditionalShortcutsGroup=Additional shortcuts:
french.AdditionalShortcutsGroup=Raccourcis supplementaires:
spanish.AdditionalShortcutsGroup=Accesos directos adicionales:

brazilianportuguese.StartupGroup=Inicializacao:
english.StartupGroup=Startup:
french.StartupGroup=Demarrage:
spanish.StartupGroup=Inicio:

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIconDesc}"; GroupDescription: "{cm:AdditionalShortcutsGroup}"; Flags: checkedonce
Name: "startupicon"; Description: "{cm:StartupIconDesc}"; GroupDescription: "{cm:StartupGroup}"; Flags: unchecked

[Files]
; PyInstaller --onedir gera dist\Dofusinator\ com .exe + DLLs + assets bundled.
; Copia a pasta INTEIRA (recursivo) pra pasta de instalacao.
Source: "..\dist\Dofusinator\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Assets, sounds e slang_dictionary JA estao dentro de dist\Dofusinator\
; (bundlados pelo PyInstaller via spec). Mantemos esses Source extras como
; FALLBACK caso por algum motivo o PyInstaller nao tenha bundlado.
Source: "..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs onlyifdoesntexist; \
    Check: DirExists(ExpandConstant('{src}\..\assets'))
Source: "..\sounds\*"; DestDir: "{app}\sounds"; Flags: ignoreversion recursesubdirs createallsubdirs onlyifdoesntexist; \
    Check: DirExists(ExpandConstant('{src}\..\sounds'))
Source: "..\slang_dictionary.json"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist; \
    Check: FileExists(ExpandConstant('{src}\..\slang_dictionary.json'))

[Icons]
; Menu Iniciar
Name: "{group}\{#APP_NAME}"; Filename: "{app}\{#APP_EXE}"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\Desinstalar {#APP_NAME}"; Filename: "{uninstallexe}"

; Desktop (opcional - controlado pela task 'desktopicon')
Name: "{userdesktop}\{#APP_NAME}"; Filename: "{app}\{#APP_EXE}"; \
    IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon

; Startup (opcional - controlado pela task 'startupicon')
Name: "{userstartup}\{#APP_NAME}"; Filename: "{app}\{#APP_EXE}"; \
    IconFilename: "{app}\assets\icon.ico"; Tasks: startupicon

[Run]
; Pos-instalacao: oferecer abrir o app
Filename: "{app}\{#APP_EXE}"; Description: "Abrir {#APP_NAME}"; \
    Flags: nowait postinstall skipifsilent unchecked

[UninstallDelete]
; Limpa pastas que o app cria runtime
Type: filesandordirs; Name: "{app}\.sound_cache"
Type: filesandordirs; Name: "{app}\debug"
Type: files; Name: "{app}\settings.json"
Type: files; Name: "{app}\cache.json"
Type: files; Name: "{app}\history.json"
Type: files; Name: "{app}\custom_terms.json"
Type: files; Name: "{app}\debug.log"

; ===========================================================================
; Pascal Script: Tesseract info post-install (importado de tesseract_info.iss)
; v1.0.3+: removido auto-install, agora so mostra dialogo informativo
; ===========================================================================

#include "tesseract_info.iss"

// ===========================================================================
// Pascal Script: Grava idioma escolhido no install em settings.json
// (Sub-bloco 2.3 do Bloco 2 - integracao i18n com installer)
//
// NOTA: NAO declaramos [Code] de novo - tesseract_info.iss ja abriu essa secao
// via #include acima. Inno Setup so aceita UMA secao [Code] por compilacao.
//
// IMPORTANTE: dentro de [Code] os comentarios sao Pascal (// ou { }), NAO
// script (;). Bug fixado em v1.0.16 era exatamente isso - comentarios com ;
// dentro de [Code] eram interpretados como codigo Pascal e quebravam.
// ===========================================================================

procedure SaveInstallerLanguage();
var
  AppDataDir: String;
  SettingsPath: String;
  LangCode: String;
  ActiveLang: String;
  SettingsContent: AnsiString;
  NewSettings: String;
begin
  // Mapeia idioma do Inno → codigo do app
  ActiveLang := ActiveLanguage();
  if ActiveLang = 'brazilianportuguese' then
    LangCode := 'pt'
  else if ActiveLang = 'english' then
    LangCode := 'en'
  else if ActiveLang = 'french' then
    LangCode := 'fr'
  else if ActiveLang = 'spanish' then
    LangCode := 'es'
  else
    LangCode := 'pt'; // fallback

  // Caminho do settings.json (criado pelo app no primeiro start, mas vamos
  // criar antecipadamente pra ja vir com o idioma correto)
  AppDataDir := ExpandConstant('{localappdata}\Dofusinator');
  SettingsPath := AppDataDir + '\settings.json';

  // Garante que a pasta existe
  if not DirExists(AppDataDir) then
  begin
    if not CreateDir(AppDataDir) then
    begin
      Log('[InstallerLang] Falha ao criar ' + AppDataDir);
      Exit;
    end;
  end;

  // Se settings.json ja existe (reinstalacao), nao sobrescreve - apenas
  // injeta/atualiza ui_language. Pra simplificar e nao precisar parsear JSON
  // em Pascal, sobrescrevemos apenas se o arquivo NAO existir (primeira instalacao).
  if FileExists(SettingsPath) then
  begin
    Log('[InstallerLang] settings.json ja existe, pulando (reinstalacao)');
    Exit;
  end;

  // Cria settings.json minimo com idioma + first_run flag
  NewSettings :=
    '{' + #13#10 +
    '  "ui_language": "' + LangCode + '",' + #13#10 +
    '  "first_run_completed": false' + #13#10 +
    '}' + #13#10;

  SettingsContent := AnsiString(NewSettings);
  if SaveStringToFile(SettingsPath, NewSettings, False) then
    Log('[InstallerLang] settings.json criado com ui_language=' + LangCode)
  else
    Log('[InstallerLang] Falha ao criar ' + SettingsPath);
end;

// Hook ssPostInstall: tesseract_info.iss ja tem um CurStepChanged.
// O Inno permite definir CurStepChanged uma unica vez, entao precisamos
// delegar — o procedure abaixo eh chamado via patch no tesseract_info.iss
// OU podemos simplesmente fazer override aqui.
// Pra evitar conflito, removo o CurStepChanged de tesseract_info e centralizo aqui:

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 1. Salva idioma do install em settings.json (Sub-bloco 2.3)
    SaveInstallerLanguage();

    // 2. Mostra info do Tesseract se nao instalado
    ShowTesseractInfoIfNeeded();
  end;
end;
