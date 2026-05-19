@echo off
title Falai Bot
color 0A
setlocal enabledelayedexpansion

echo ========================================
echo         FALAI BOT - Auto Responder
echo ========================================
echo.

:: ==================== AUTO-UPDATE ====================
set "REPO=lucasjoaquim478-maker/falai-bot"
set "BRANCH=master"
set "ZIP_URL=https://github.com/%REPO%/archive/refs/heads/%BRANCH%.zip"
set "API_URL=https://api.github.com/repos/%REPO%/releases/latest"

:: Pasta temporaria
set "TEMP_DIR=%TEMP%\falai-bot-update"
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%" 2>nul

:: Verificar versao local
set LOCAL_VER=0
if exist version.json (
    for /f "tokens=2 delims=:" %%a in ('findstr "version" version.json') do (
        set "LOCAL_VER=%%a"
        set "LOCAL_VER=!LOCAL_VER:"=!"
        set "LOCAL_VER=!LOCAL_VER: =!"
        set "LOCAL_VER=!LOCAL_VER:,=!"
    )
)

:: Verificar versao remota (via GitHub releases)
echo [*] Verificando atualizacoes...
for /f "skip=1 delims=" %%a in ('powershell -Command "try { $r = Invoke-WebRequest -Uri '%API_URL%' -UseBasicParsing -TimeoutSec 10; $j = $r.Content | ConvertFrom-Json; $j.tag_name } catch { '' }" 2^>nul') do set "REMOTE_VER=%%a"
if "!REMOTE_VER!"=="" (
    echo [*] Nao foi possivel verificar versao (offline)
) else (
    set "REMOTE_VER=!REMOTE_VER:v=!"
    if !REMOTE_VER! GTR !LOCAL_VER! (
        echo [!] Nova versao encontrada: !REMOTE_VER! (local: !LOCAL_VER!)
        echo [*] Baixando atualizacao...
        powershell -Command "& { param($u,$d) [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri $u -OutFile $d -UseBasicParsing }" -u "%ZIP_URL%" -d "%TEMP_DIR%\update.zip"
        if exist "%TEMP_DIR%\update.zip" (
            echo [*] Extraindo...
            powershell -Command "Expand-Archive -Path '%TEMP_DIR%\update.zip' -DestinationPath '%TEMP_DIR%' -Force 2>$null"
            :: Robocopy pra copiar tudo
            robocopy "%TEMP_DIR%\%REPO:-master=%" "%~dp0" /E /IS /IT /R:2 /W:3 /XF config.txt
            echo [*] Atualizado para versao !REMOTE_VER!
            :: Atualiza version.json
            > version.json echo {"version": !REMOTE_VER!}
        ) else (
            echo [!] Falha ao baixar atualizacao
        )
    ) else (
        echo [*] Versao atual: !LOCAL_VER! (mais recente)
    )
)

:: ==================== FIM AUTO-UPDATE ====================

:: Verificar Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] Python nao encontrado!
    echo     Baixe em: https://python.org
    pause
    exit /b 1
)

:: Instalar dependencias
echo [*] Verificando dependencias...
pip install -r requirements.txt --quiet 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [*] Instalando dependencias...
    pip install -r requirements.txt
)
echo.

:: Pular config se ja existe
if exist config.txt (
    echo [*] Usando config.txt existente...
    goto run
)

:: Pedir credenciais
set /p email="Email do Falai: "
set /p senha="Senha do Falai: "

:: Salvar config (usando !var! pra nao quebrar caracteres especiais)
>config.txt echo !email!
>>config.txt echo !senha!
echo [*] Config salva em config.txt

:run
echo.
echo [*] Iniciando bot...
echo [*] Pressione CTRL+C para parar
echo.

set /a line=0
for /f "usebackq delims=" %%a in ("config.txt") do (
    if !line! equ 0 set "email=%%a"
    if !line! equ 1 set "senha=%%a"
    set /a line+=1
)

set "FALAI_EMAIL=!email!"
set "FALAI_SENHA=!senha!"
python bot.py

if %ERRORLEVEL% NEQ 0 (
    echo [!] Erro ao executar o bot
    pause
)
