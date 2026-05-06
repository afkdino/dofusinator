@echo off
chcp 65001 > nul
REM ===========================================================================
REM Dofusinator - Publish Script
REM ===========================================================================
REM
REM Sobe release oficial pro GitHub. Roda DEPOIS de validar localmente que
REM o build.bat funciona e o Setup.exe instala/abre corretamente.
REM
REM IMPORTANTE: este script faz coisa DESTRUTIVA (cria release oficial no
REM             GitHub). So roda quando tiver certeza absoluta da versao.
REM
REM Pre-requisitos:
REM   - Tudo do build.bat
REM   - Repo do GitHub criado e acessivel
REM   - GitHub CLI (gh) instalado E autenticado, OU credenciais HTTPS no git
REM
REM Como rodar:
REM   publish.bat        (publish da versao atual no app_info.py)
REM
REM v1.1.0/Fase 5: ativo. Primeira release publica feita em 2026-05-06.

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "REPO_URL=https://github.com/afkdino/dofusinator"
cd /d "%PROJECT_ROOT%"

set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "CYAN=[96m"
set "RESET=[0m"

echo.
echo %CYAN%========================================%RESET%
echo %CYAN%  Dofusinator - Publish Release%RESET%
echo %CYAN%========================================%RESET%
echo.

REM Pega versao do app_info.py
for /f "tokens=2 delims==" %%a in ('findstr /b "APP_VERSION" src\app_info.py') do (
    set "RAW_VERSION=%%a"
)
set "VERSION=%RAW_VERSION: =%"
set "VERSION=%VERSION:"=%"

if "%VERSION%"=="" (
    echo %RED%[ERRO] Nao consegui extrair versao do src\app_info.py%RESET%
    exit /b 1
)

echo Publicando versao: %CYAN%%VERSION%%RESET%
echo Repo: %CYAN%%REPO_URL%%RESET%
echo.
echo %YELLOW%ATENCAO: isso vai criar/atualizar uma release no GitHub.%RESET%
echo Pressione Ctrl+C pra cancelar agora, ou qualquer tecla pra continuar...
pause >nul

cd /d "%PROJECT_ROOT%\build_system"

REM === STEP 1: Baixar releases anteriores (necessario pra delta updates) ===
echo.
echo %CYAN%[1/3] Baixando releases anteriores pra calcular delta...%RESET%
vpk download github ^
    --repoUrl %REPO_URL% ^
    --outputDir Releases
if errorlevel 1 (
    echo %YELLOW%[WARN] Download falhou - provavelmente primeira release, OK.%RESET%
)

REM === STEP 2: Build + Pack ===
echo.
echo %CYAN%[2/3] Buildando e empacotando v%VERSION%...%RESET%
cd /d "%PROJECT_ROOT%"
call build_system\build.bat
if errorlevel 1 (
    echo %RED%[ERRO] Build falhou.%RESET%
    exit /b 1
)

REM === STEP 3: Upload pro GitHub ===
echo.
echo %CYAN%[3/3] Subindo release pro GitHub...%RESET%
cd /d "%PROJECT_ROOT%\build_system"
vpk upload github ^
    --repoUrl %REPO_URL% ^
    --outputDir Releases ^
    --publish ^
    --releaseName "Dofusinator v%VERSION%" ^
    --tag v%VERSION%

if errorlevel 1 (
    echo %RED%[ERRO] Upload pro GitHub falhou.%RESET%
    cd /d "%PROJECT_ROOT%"
    exit /b 1
)

cd /d "%PROJECT_ROOT%"

echo.
echo %CYAN%========================================%RESET%
echo %GREEN%  Publish completo!%RESET%
echo %CYAN%========================================%RESET%
echo.
echo Release v%VERSION% disponivel em:
echo   %REPO_URL%/releases/tag/v%VERSION%
echo.
endlocal
