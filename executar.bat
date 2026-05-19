@echo off
title Falai Bot
color 0A

echo ========================================
echo         FALAI BOT - Auto Responder
echo ========================================
echo.

:: Verificar Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] Python nao encontrado!
    echo     Baixe em: https://python.org
    pause
    exit /b 1
)

:: Instalar dependencias se necessario
pip show selenium >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [*] Instalando dependencias...
    pip install -r requirements.txt
    echo.
)

:: Pular config se ja existe
if exist config.txt (
    echo [*] Usando config.txt existente...
    goto run
)

:: Pedir credenciais
set /p email="Email do Falai: "
set /p senha="Senha do Falai: "

:: Salvar config
echo %email% > config.txt
echo %senha% >> config.txt
echo [*] Config salva em config.txt

:run
echo.
echo [*] Iniciando bot...
echo [*] Pressione CTRL+C para parar
echo.

set /p email=<config.txt
set /p senha=<config.txt
set /p senha=<config.txt

set FALAI_EMAIL=%email%
set FALAI_SENHA=%senha%
python bot.py

if %ERRORLEVEL% NEQ 0 (
    echo [!] Erro ao executar o bot
    pause
)
