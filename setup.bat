@echo off
echo ========================================
echo   DofusBR-Translator - Setup
echo ========================================
echo.

REM Verifica se Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Instale Python 3.10+ em https://python.org
    echo Marque "Add Python to PATH" na instalacao.
    pause
    exit /b 1
)

echo [OK] Python encontrado.
python --version
echo.

REM Cria virtualenv
if not exist venv (
    echo Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar venv. Tentando instalacao global...
        goto INSTALL_DEPS
    )
)

call venv\Scripts\activate.bat

:INSTALL_DEPS
echo.
echo Instalando dependencias Python...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Setup Python concluido!
echo ========================================
echo.
echo PROXIMOS PASSOS MANUAIS:
echo.
echo 1) Instale o Tesseract OCR:
echo    https://github.com/UB-Mannheim/tesseract/wiki
echo.
echo 2) Durante a instalacao, marque:
echo    - Additional language data: French (fra)
echo    - Additional language data: Portuguese (por)
echo    - Additional language data: Spanish (spa)
echo    - Additional language data: English (eng)
echo.
echo 3) Anote o caminho onde Tesseract foi instalado
echo    (geralmente C:\Program Files\Tesseract-OCR\tesseract.exe)
echo.
echo 4) Para rodar o app:
echo    run.bat
echo.
pause
