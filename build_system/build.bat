@echo off
chcp 65001 > nul
REM ===========================================================================
REM Dofusinator - Build Script (v1.0.34+)
REM ===========================================================================
REM
REM Compila o .exe + empacota com Velopack pra gerar Setup.exe + nupkg.
REM
REM Pre-requisitos (instalar uma vez na sua maquina):
REM   - Python 3.10+ no PATH
REM   - PyInstaller: pip install pyinstaller
REM   - .NET SDK 8+ (https://dotnet.microsoft.com/download)
REM   - vpk CLI: dotnet tool install -g vpk
REM   - velopack: pip install velopack
REM
REM Como rodar:
REM   build.bat              (build completo: PyInstaller + vpk pack)
REM   build.bat clean        (limpa builds antigos)
REM   build.bat exe          (so PyInstaller, sem empacotar)
REM   build.bat pack         (so vpk pack, assume exe ja existe)
REM
REM Pra publicar release no GitHub: usa publish.bat (separado pra seguranca).
REM
REM v1.0.34: Reescrito removendo Inno Setup. Velopack assume.

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
cd /d "%PROJECT_ROOT%"

REM === Cores no console ===
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "CYAN=[96m"
set "RESET=[0m"

echo.
echo %CYAN%========================================%RESET%
echo %CYAN%  Dofusinator - Build System (Velopack)%RESET%
echo %CYAN%========================================%RESET%
echo.

REM === Argumento opcional ===
if "%1"=="clean" goto clean
if "%1"=="exe" goto build_exe_only
if "%1"=="pack" goto pack_only

REM === Build completo (default) ===
goto build_all

:clean
echo %YELLOW%[CLEAN] Removendo builds antigos...%RESET%
if exist "build" rd /s /q build
if exist "dist" rd /s /q dist
if exist "build_system\build" rd /s /q build_system\build
if exist "build_system\Releases" rd /s /q build_system\Releases
if exist "*.spec.bak" del *.spec.bak
if exist "__pycache__" rd /s /q __pycache__
if exist "src\__pycache__" rd /s /q src\__pycache__
if exist "build_system\__pycache__" rd /s /q build_system\__pycache__
echo %GREEN%[OK] Limpeza concluida.%RESET%
goto end

:build_all
call :check_prereqs
if errorlevel 1 goto end
call :build_exe
if errorlevel 1 goto end
call :build_velopack
goto end

:build_exe_only
call :check_prereqs
if errorlevel 1 goto end
call :build_exe
goto end

:pack_only
call :build_velopack
goto end

REM ============================================================
REM SUBROUTINES
REM ============================================================

:check_prereqs
echo %CYAN%[CHECK] Verificando pre-requisitos...%RESET%

where python >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERRO] Python nao encontrado no PATH.%RESET%
    exit /b 1
)
echo   %GREEN%OK%RESET% Python encontrado

python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%[WARN] PyInstaller nao encontrado. Instalando...%RESET%
    pip install pyinstaller
    if errorlevel 1 (
        echo %RED%[ERRO] Falha ao instalar PyInstaller.%RESET%
        exit /b 1
    )
)
echo   %GREEN%OK%RESET% PyInstaller pronto

REM Confere se velopack ta instalado
python -c "import velopack" >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%[WARN] velopack nao encontrado. Instalando...%RESET%
    pip install velopack
    if errorlevel 1 (
        echo %RED%[ERRO] Falha ao instalar velopack.%RESET%
        exit /b 1
    )
)
echo   %GREEN%OK%RESET% velopack pronto

REM Confere se vpk CLI esta acessivel
where vpk >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERRO] vpk CLI nao encontrado no PATH.%RESET%
    echo   Instala com: dotnet tool install -g vpk
    echo   ^(precisa do .NET SDK 8+ instalado primeiro^)
    exit /b 1
)
echo   %GREEN%OK%RESET% vpk CLI pronto

REM Verifica se assets/icon.ico existe
if not exist "assets\icon.ico" (
    echo %YELLOW%[WARN] assets\icon.ico nao encontrado. Build vai prosseguir sem icone.%RESET%
)

REM Verifica se splash.gif existe (recomendado pra Velopack)
if not exist "assets\splash.gif" (
    echo %YELLOW%[WARN] assets\splash.gif nao encontrado. Setup nao tera splash.%RESET%
)

echo.
exit /b 0

:build_exe
echo %CYAN%[BUILD] Compilando Dofusinator (onedir) via PyInstaller...%RESET%
echo   ^(Isso pode levar 1-3 minutos^)
echo.

cd /d "%PROJECT_ROOT%"

REM Limpeza profunda antes de buildar
echo %CYAN%[CLEAN] Limpando caches do PyInstaller...%RESET%
if exist "build" rd /s /q build
if exist "dist" rd /s /q dist
if exist "src\__pycache__" rd /s /q src\__pycache__
if exist "build_system\__pycache__" rd /s /q build_system\__pycache__

python -m PyInstaller --noconfirm --clean build_system\Dofusinator.spec
if errorlevel 1 (
    echo.
    echo %RED%[ERRO] PyInstaller falhou.%RESET%
    exit /b 1
)

if not exist "dist\Dofusinator\Dofusinator.exe" (
    echo %RED%[ERRO] dist\Dofusinator\Dofusinator.exe nao foi gerado.%RESET%
    exit /b 1
)

echo.
echo %GREEN%[OK] Dofusinator gerado em: dist\Dofusinator\%RESET%
echo.
exit /b 0

:build_velopack
echo %CYAN%[VELOPACK] Empacotando com vpk pack...%RESET%

if not exist "dist\Dofusinator\Dofusinator.exe" (
    echo %RED%[ERRO] dist\Dofusinator\Dofusinator.exe nao existe. Rode 'build.bat exe' primeiro.%RESET%
    exit /b 1
)

REM Pega versao do app_info.py (parsing simples)
for /f "tokens=2 delims==" %%a in ('findstr /b "APP_VERSION" src\app_info.py') do (
    set "RAW_VERSION=%%a"
)
REM Remove aspas e espacos
set "VERSION=%RAW_VERSION: =%"
set "VERSION=%VERSION:"=%"

if "%VERSION%"=="" (
    echo %RED%[ERRO] Nao consegui extrair versao do src\app_info.py%RESET%
    exit /b 1
)

echo   Versao: %VERSION%
echo.

cd /d "%PROJECT_ROOT%\build_system"

REM Roda vpk pack
REM   --packId         identificador unico do app
REM   --packVersion    versao semantica (vem do app_info.py)
REM   --packDir        pasta com a build do PyInstaller
REM   --mainExe        nome do executavel principal
REM   --packTitle      nome amigavel exibido no Setup.exe
REM   --packAuthors    nome do publisher
REM   --icon           icone do app
REM   --splashImage    splash mostrada durante install
REM   --outputDir      pasta de saida dos pacotes
vpk pack ^
    --packId Dofusinator ^
    --packVersion %VERSION% ^
    --packDir ..\dist\Dofusinator ^
    --mainExe Dofusinator.exe ^
    --packTitle "Dofusinator" ^
    --packAuthors "afkdino" ^
    --icon ..\assets\icon.ico ^
    --splashImage ..\assets\splash.gif ^
    --outputDir Releases

if errorlevel 1 (
    echo %RED%[ERRO] vpk pack falhou.%RESET%
    cd /d "%PROJECT_ROOT%"
    exit /b 1
)

cd /d "%PROJECT_ROOT%"

echo.
echo %GREEN%[OK] Pacote Velopack gerado em: build_system\Releases\%RESET%

dir /b build_system\Releases\

echo.
echo %CYAN%========================================%RESET%
echo %GREEN%  Build completo!%RESET%
echo %CYAN%========================================%RESET%
echo.
echo Arquivos prontos:
echo   - dist\Dofusinator\                              ^(pasta com .exe + DLLs^)
echo   - build_system\Releases\Dofusinator-win-Setup.exe ^(instalador pra distribuir^)
echo   - build_system\Releases\*.nupkg                  ^(pacotes Velopack^)
echo.
echo Pra publicar release no GitHub: rode publish.bat
echo.
exit /b 0

:end
endlocal
