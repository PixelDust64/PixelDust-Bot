@echo off
setlocal

REM Nome da pasta do ambiente virtual
set VENV_NAME=venv
REM Nome do arquivo de dependências
set REQS_FILE=req.txt

echo ----------------------------------------------------
echo         INICIADOR PIXELDUSTBOT (WINDOWS)
echo ----------------------------------------------------

REM --- 1. VERIFICAR E CRIAR VIRTUAL ENV ---
if not exist "%VENV_NAME%" (
    echo Criando ambiente virtual em: %VENV_NAME%...
    python -m venv %VENV_NAME%
    if errorlevel 1 goto :error_venv
    echo Ambiente virtual criado com sucesso.
) else (
    echo Ambiente virtual encontrado.
)

REM --- 2. ATIVAR VIRTUAL ENV ---
echo Ativando ambiente virtual...
call "%VENV_NAME%\Scripts\activate.bat"
if errorlevel 1 goto :error_activate

REM --- 3. INSTALAR/ATUALIZAR DEPENDENCIAS ---
if exist "%REQS_FILE%" (
    echo Instalando/Atualizando dependencias de %REQS_FILE%...
    pip install -r %REQS_FILE%
    if errorlevel 1 goto :error_pip
    echo Dependencias instaladas/atualizadas.
) else (
    echo Aviso: Arquivo %REQS_FILE% nao encontrado. Pulando instalacao de dependencias.
)

REM --- 4. INICIAR O BOT ---
echo.
echo ====================================================
echo             INICIANDO BOT.PY
echo ====================================================
python bot.py

goto :end

REM --- GESTAO DE ERROS ---
:error_venv
echo.
echo ====================================================
echo ERRO FATAL: Falha ao criar o ambiente virtual.
echo Certifique-se de que o Python esteja instalado e no PATH.
goto :pause

:error_activate
echo.
echo ====================================================
echo ERRO FATAL: Falha ao ativar o ambiente virtual.
goto :pause

:error_pip
echo.
echo ====================================================
echo ERRO FATAL: Falha ao instalar dependencias do PIP.
echo Verifique sua conexao com a internet.
goto :pause

:pause
pause

:end
endlocal