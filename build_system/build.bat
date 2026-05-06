@echo off
chcp 65001 > nul
REM ===========================================================================
REM Dofusinator - Build Script
REM ===========================================================================
REM
REM Compila o .exe + gera o instalador .exe final.
REM
REM Pre-requisitos (instalar uma vez na sua maquina):
REM   - Python 3.10+ no PATH
REM   - PyInstaller: pip install pyinstaller
REM   - Inno Setup 6.1+ (https://jrsoftware.org/isdl.php)
REM
REM Como rodar:
REM   build.bat              (build completo)
REM   build.bat clean        (limpa builds antigos)
REM   build.bat exe          (so o exe, sem instalador)
REM   build.bat installer    (so o instalador, assume exe existe)
REM
REM v1.1.0: Limpeza mais profunda do cache do PyInstaller pra evitar
REM         ModuleNotFoundError fantasmas (cache stale entre versoes do
REM         spec que muda hidden_imports).

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
echo %CYAN%  Dofusinator - Build System%RESET%
echo %CYAN%========================================%RESET%
echo.

REM === Argumento opcional ===
if "%1"=="clean" goto clean
if "%1"=="exe" goto build_exe_only
if "%1"=="installer" goto build_installer_only

REM === Build completo (default) ===
goto build_all

:clean
echo %YELLOW%[CLEAN] Removendo builds antigos...%RESET%
if exist "build" rd /s /q build
if exist "dist" rd /s /q dist
if exist "build_system\build" rd /s /q build_system\build
REM v1.1.0: limpa tambem caches do PyInstaller que ficam em outros lugares
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
call :build_installer
goto end

:build_exe_only
call :check_prereqs
if errorlevel 1 goto end
call :build_exe
goto end

:build_installer_only
call :build_installer
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

REM v1.1.0: confere se velopack ta instalado
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

REM Procura Inno Setup ISCC
set "ISCC_PATH="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if "%ISCC_PATH%"=="" (
    echo %YELLOW%[WARN] Inno Setup nao encontrado.%RESET%
    echo   Baixe em: https://jrsoftware.org/isdl.php
    echo   ^(necessario apenas pra etapa do instalador, build do .exe segue^)
)
if not "%ISCC_PATH%"=="" echo   %GREEN%OK%RESET% Inno Setup: %ISCC_PATH%

REM Verifica se assets/icon.ico existe
if not exist "assets\icon.ico" (
    echo %YELLOW%[WARN] assets\icon.ico nao encontrado. Build vai prosseguir sem icone.%RESET%
)

echo.
exit /b 0

:build_exe
echo %CYAN%[BUILD] Compilando Dofusinator (onedir) via PyInstaller...%RESET%
echo   ^(Isso pode levar 1-3 minutos^)
echo.

cd /d "%PROJECT_ROOT%"

REM v1.1.0: Limpeza profunda ANTES de buildar pra eliminar caches stale
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

REM --onedir gera dist\Dofusinator\Dofusinator.exe (pasta com DLLs ao lado)
if not exist "dist\Dofusinator\Dofusinator.exe" (
    echo %RED%[ERRO] dist\Dofusinator\Dofusinator.exe nao foi gerado.%RESET%
    exit /b 1
)

echo.
echo %GREEN%[OK] Dofusinator gerado em: dist\Dofusinator\%RESET%

REM Mostra tamanho da pasta inteira
echo   Conteudo:
dir /b "dist\Dofusinator\" | find /c /v "" > "%TEMP%\file_count.txt"
set /p file_count=<"%TEMP%\file_count.txt"
del "%TEMP%\file_count.txt"
echo   %file_count% arquivos/pastas em dist\Dofusinator\
echo.
exit /b 0

:build_installer
echo %CYAN%[INSTALLER] Gerando instalador via Inno Setup...%RESET%

if not exist "dist\Dofusinator\Dofusinator.exe" (
    echo %RED%[ERRO] dist\Dofusinator\Dofusinator.exe nao existe. Rode 'build.bat exe' primeiro.%RESET%
    exit /b 1
)

set "ISCC_PATH="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if "%ISCC_PATH%"=="" (
    echo %RED%[ERRO] Inno Setup nao encontrado.%RESET%
    echo   Baixe e instale: https://jrsoftware.org/isdl.php
    exit /b 1
)

cd /d "%PROJECT_ROOT%\build_system"
"%ISCC_PATH%" installer.iss
if errorlevel 1 (
    echo %RED%[ERRO] Inno Setup falhou.%RESET%
    cd /d "%PROJECT_ROOT%"
    exit /b 1
)
cd /d "%PROJECT_ROOT%"

echo.
echo %GREEN%[OK] Instalador gerado em: dist\DofusinatorSetup_*.exe%RESET%

dir /b dist\DofusinatorSetup_*.exe

echo.
echo %CYAN%========================================%RESET%
echo %GREEN%  Build completo!%RESET%
echo %CYAN%========================================%RESET%
echo.
echo Arquivos prontos:
echo   - dist\Dofusinator\            ^(pasta com .exe + DLLs^)
echo   - dist\DofusinatorSetup_*.exe  ^(instalador pra distribuir^)
echo.
exit /b 0

:end
endlocal
