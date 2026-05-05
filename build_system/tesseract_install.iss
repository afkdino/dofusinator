; ===========================================================================
; Pascal Script para download/install automatico do Tesseract OCR
; v1.0.1 - deteccao robusta (paths comuns + registry + PATH do sistema)
; ===========================================================================

[Code]
const
  TESSERACT_URL = 'https://github.com/UB-Mannheim/tesseract/wiki/tesseract-ocr-w64-setup-5.3.4.20240503.exe';
  TESSERACT_FILE = 'tesseract-installer.exe';

// ---------------------------------------------------------------------------
// Detecta Tesseract via caminhos de instalacao comuns
// ---------------------------------------------------------------------------
function IsTesseractInCommonPaths(): Boolean;
var
  Paths: array[0..7] of String;
  i: Integer;
begin
  Paths[0] := ExpandConstant('{pf}\Tesseract-OCR\tesseract.exe');           // Program Files
  Paths[1] := ExpandConstant('{pf32}\Tesseract-OCR\tesseract.exe');         // Program Files (x86)
  Paths[2] := ExpandConstant('{localappdata}\Programs\Tesseract-OCR\tesseract.exe'); // User local
  Paths[3] := ExpandConstant('{sd}\Tesseract-OCR\tesseract.exe');           // C:\Tesseract-OCR
  Paths[4] := ExpandConstant('{sd}\Tesseract\tesseract.exe');               // C:\Tesseract
  Paths[5] := ExpandConstant('{userpf}\Tesseract-OCR\tesseract.exe');       // User Program Files
  Paths[6] := 'C:\Program Files\Tesseract-OCR\tesseract.exe';               // Hardcoded fallback
  Paths[7] := 'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe';         // Hardcoded fallback

  Result := False;
  for i := 0 to High(Paths) do
  begin
    if FileExists(Paths[i]) then
    begin
      Log('[Tesseract] Encontrado em: ' + Paths[i]);
      Result := True;
      Exit;
    end;
  end;
end;

// ---------------------------------------------------------------------------
// Detecta Tesseract via registry do Windows
// ---------------------------------------------------------------------------
function CheckTesseractInRegistry(const RegRoot: Integer; const KeyName: String): Boolean;
var
  InstallDir: String;
  TesseractPath: String;
begin
  Result := False;

  // Tenta ler 'InstallDir' ou valor default da chave
  if RegQueryStringValue(RegRoot, KeyName, 'InstallDir', InstallDir) or
     RegQueryStringValue(RegRoot, KeyName, '', InstallDir) or
     RegQueryStringValue(RegRoot, KeyName, 'Path', InstallDir) then
  begin
    if InstallDir <> '' then
    begin
      TesseractPath := AddBackslash(InstallDir) + 'tesseract.exe';
      if FileExists(TesseractPath) then
      begin
        Log('[Tesseract] Encontrado via registry: ' + TesseractPath);
        Result := True;
      end;
    end;
  end;
end;

function IsTesseractInRegistry(): Boolean;
begin
  Result := False;

  if CheckTesseractInRegistry(HKLM, 'SOFTWARE\Tesseract-OCR') then begin Result := True; Exit; end;
  if CheckTesseractInRegistry(HKLM, 'SOFTWARE\WOW6432Node\Tesseract-OCR') then begin Result := True; Exit; end;
  if CheckTesseractInRegistry(HKCU, 'SOFTWARE\Tesseract-OCR') then begin Result := True; Exit; end;
  if CheckTesseractInRegistry(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Tesseract-OCR') then begin Result := True; Exit; end;
end;

// ---------------------------------------------------------------------------
// Detecta Tesseract no PATH do sistema (where tesseract)
// ---------------------------------------------------------------------------
function IsTesseractInPath(): Boolean;
var
  ResultCode: Integer;
  TempFile: String;
  Output: AnsiString;
begin
  Result := False;
  TempFile := ExpandConstant('{tmp}\where_tesseract.txt');

  // 'where tesseract' procura no PATH e retorna 0 se achou
  if Exec(
       ExpandConstant('{cmd}'),
       '/c where tesseract > "' + TempFile + '" 2>nul',
       '', SW_HIDE, ewWaitUntilTerminated, ResultCode
     ) then
  begin
    if (ResultCode = 0) and FileExists(TempFile) then
    begin
      if LoadStringFromFile(TempFile, Output) and (Length(Output) > 0) then
      begin
        Log('[Tesseract] Encontrado no PATH: ' + Output);
        Result := True;
      end;
    end;
  end;

  // Cleanup
  if FileExists(TempFile) then
    DeleteFile(TempFile);
end;

// ---------------------------------------------------------------------------
// Funcao principal: combina os 3 metodos
// ---------------------------------------------------------------------------
function IsTesseractInstalled(): Boolean;
begin
  Result := IsTesseractInCommonPaths() or
            IsTesseractInRegistry() or
            IsTesseractInPath();

  if Result then
    Log('[Tesseract] INSTALADO - skip auto-install')
  else
    Log('[Tesseract] NAO ENCONTRADO - oferecera instalacao');
end;

// ---------------------------------------------------------------------------
// Download e instalacao do Tesseract
// ---------------------------------------------------------------------------
function DownloadAndInstallTesseract(): Boolean;
var
  TempFile: String;
  ResultCode: Integer;
  DownloadPage: TDownloadWizardPage;
begin
  Result := False;
  TempFile := ExpandConstant('{tmp}\') + TESSERACT_FILE;

  DownloadPage := CreateDownloadPage(
    'Baixando Tesseract OCR',
    'O Tesseract e necessario pra leitura do chat do Dofus. ' +
    'Estamos baixando a versao oficial (UB Mannheim build).',
    nil
  );
  DownloadPage.Clear;
  DownloadPage.Add(TESSERACT_URL, TESSERACT_FILE, '');
  DownloadPage.Show;

  try
    try
      DownloadPage.Download;
    except
      MsgBox(
        'Falha ao baixar Tesseract: ' + GetExceptionMessage + #13#10 +
        'Voce podera instalar manualmente depois em: ' + #13#10 +
        TESSERACT_URL,
        mbError, MB_OK
      );
      Exit;
    end;
  finally
    DownloadPage.Hide;
  end;

  // Roda o instalador silenciosamente (/S = NSIS silent flag)
  if not Exec(TempFile, '/S', '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
  begin
    MsgBox(
      'Nao foi possivel executar o instalador do Tesseract.' + #13#10 +
      'Codigo: ' + IntToStr(ResultCode) + #13#10 + #13#10 +
      'Voce pode instalar manualmente abrindo: ' + TempFile,
      mbError, MB_OK
    );
    Exit;
  end;

  // Verifica resultado
  if IsTesseractInstalled() then
  begin
    Result := True;
  end
  else
  begin
    MsgBox(
      'O Tesseract foi baixado mas a instalacao parece nao ter completado.' + #13#10 +
      'Voce podera tentar manualmente abrindo: ' + TempFile,
      mbInformation, MB_OK
    );
  end;
end;

// ---------------------------------------------------------------------------
// Hook chamado apos a instalacao principal
// ---------------------------------------------------------------------------
procedure CurStepChanged(CurStep: TSetupStep);
var
  ShouldInstall: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    if IsTesseractInstalled() then
    begin
      // Ja tem - silencioso, nao incomoda o user
      Log('[Tesseract] Detectado no sistema - pulando oferta de instalacao');
    end
    else
    begin
      ShouldInstall := MsgBox(
        'O Dofusinator usa o Tesseract OCR pra ler o chat do Dofus.' + #13#10 + #13#10 +
        'Detectamos que o Tesseract NAO esta instalado.' + #13#10 + #13#10 +
        'Deseja baixar e instalar agora? (recomendado, ~50MB)' + #13#10 +
        'Voce tambem pode instalar manualmente depois.',
        mbConfirmation, MB_YESNO
      );

      if ShouldInstall = IDYES then
      begin
        if DownloadAndInstallTesseract() then
        begin
          MsgBox(
            'Tesseract instalado com sucesso!' + #13#10 +
            'O Dofusinator vai detectar automaticamente.',
            mbInformation, MB_OK
          );
        end;
      end;
    end;
  end;
end;
