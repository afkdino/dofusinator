; ===========================================================================
; Tesseract OCR - Informacao pos-instalacao
; v1.0.3 - removido auto-install (erro 216 inconsistente)
;          agora mostra dialogo informativo apenas se nao detectar
; ===========================================================================

[Code]

// ---------------------------------------------------------------------------
// Detecta Tesseract via 8 caminhos comuns + registry + PATH
// ---------------------------------------------------------------------------
function IsTesseractInCommonPaths(): Boolean;
var
  Paths: array[0..7] of String;
  i: Integer;
begin
  Paths[0] := ExpandConstant('{pf}\Tesseract-OCR\tesseract.exe');
  Paths[1] := ExpandConstant('{pf32}\Tesseract-OCR\tesseract.exe');
  Paths[2] := ExpandConstant('{localappdata}\Programs\Tesseract-OCR\tesseract.exe');
  Paths[3] := ExpandConstant('{sd}\Tesseract-OCR\tesseract.exe');
  Paths[4] := ExpandConstant('{sd}\Tesseract\tesseract.exe');
  Paths[5] := ExpandConstant('{userpf}\Tesseract-OCR\tesseract.exe');
  Paths[6] := 'C:\Program Files\Tesseract-OCR\tesseract.exe';
  Paths[7] := 'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe';

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

function CheckTesseractInRegistry(const RegRoot: Integer; const KeyName: String): Boolean;
var
  InstallDir: String;
  TesseractPath: String;
begin
  Result := False;

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

function IsTesseractInPath(): Boolean;
var
  ResultCode: Integer;
  TempFile: String;
  Output: AnsiString;
begin
  Result := False;
  TempFile := ExpandConstant('{tmp}\where_tesseract.txt');

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
        Log('[Tesseract] Encontrado no PATH');
        Result := True;
      end;
    end;
  end;

  if FileExists(TempFile) then
    DeleteFile(TempFile);
end;

function IsTesseractInstalled(): Boolean;
begin
  Result := IsTesseractInCommonPaths() or
            IsTesseractInRegistry() or
            IsTesseractInPath();

  if Result then
    Log('[Tesseract] INSTALADO no sistema')
  else
    Log('[Tesseract] NAO ENCONTRADO');
end;

// ---------------------------------------------------------------------------
// Hook pos-instalacao auxiliar: chamado pelo CurStepChanged central no installer.iss
// (renomeado em v1.0.15 pra evitar conflito de nome com SaveInstallerLanguage)
// ---------------------------------------------------------------------------
procedure ShowTesseractInfoIfNeeded();
var
  ShouldOpenBrowser: Integer;
begin
  if not IsTesseractInstalled() then
  begin
    ShouldOpenBrowser := MsgBox(
      'O Dofusinator usa o Tesseract OCR pra ler o chat do Dofus.' + #13#10 + #13#10 +
      'Detectamos que o Tesseract NAO esta instalado no seu sistema.' + #13#10 +
      'Sem ele, o app abre normalmente mas a leitura do chat nao funciona.' + #13#10 + #13#10 +
      'INSTALACAO MANUAL (recomendada):' + #13#10 +
      '1. Acesse: https://github.com/UB-Mannheim/tesseract/wiki' + #13#10 +
      '2. Baixe o instalador "tesseract-ocr-w64-setup-X.X.X.exe"' + #13#10 +
      '3. Durante a instalacao, MARQUE os idiomas: French, Portuguese,' + #13#10 +
      '   English (alem do default)' + #13#10 +
      '4. Apos instalar, abra o Dofusinator que ele detecta automaticamente' + #13#10 + #13#10 +
      'Deseja abrir a pagina de download agora?',
      mbInformation, MB_YESNO
    );

    if ShouldOpenBrowser = IDYES then
    begin
      ShellExec(
        'open',
        'https://github.com/UB-Mannheim/tesseract/wiki',
        '', '', SW_SHOWNORMAL, ewNoWait, ShouldOpenBrowser
      );
    end;
  end;
end;
