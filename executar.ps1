param(
    [string]$Email = "",
    [string]$Senha = "",
    [switch]$Headless
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$REPO = "lucasjoaquim478-maker/falai-bot"
$BRANCH = "master"
$ZIP_URL = "https://github.com/$REPO/archive/refs/heads/$BRANCH.zip"
$API_URL = "https://api.github.com/repos/$REPO/releases/latest"

# ==================== AUTO-UPDATE ====================
$localVer = 0
if (Test-Path "version.json") {
    try {
        $localVer = [int]((Get-Content "version.json" -Raw | ConvertFrom-Json).version)
    } catch {}
}

Write-Host "[*] Verificando atualizacoes..." -ForegroundColor Yellow
try {
    $release = Invoke-RestMethod -Uri $API_URL -TimeoutSec 10 -ErrorAction Stop
    $remoteVer = [int]($release.tag_name -replace "v", "")
    if ($remoteVer -gt $localVer) {
        Write-Host "[!] Nova versao: $remoteVer (local: $localVer)" -ForegroundColor Cyan
        $tempDir = "$env:TEMP\falai-bot-update"
        $zipFile = "$tempDir\update.zip"
        if (Test-Path $tempDir) { Remove-Item -Recurse -Force $tempDir }
        New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
        Write-Host "[*] Baixando..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $ZIP_URL -OutFile $zipFile -UseBasicParsing
        Expand-Archive -Path $zipFile -DestinationPath $tempDir -Force
        $src = Get-ChildItem "$tempDir\*-$BRANCH" | Select-Object -First 1
        if ($src) {
            robocopy $src.FullName $scriptDir /E /IS /IT /R:2 /W:3 /XF config.txt
            Set-Content -Path "$scriptDir\version.json" -Value "{`"version`": $remoteVer}" -Encoding UTF8
            Write-Host "[*] Atualizado para v$remoteVer" -ForegroundColor Green
        }
    } else {
        Write-Host "[*] Versao atual: $localVer (mais recente)" -ForegroundColor Green
    }
} catch {
    Write-Host "[*] Offline, pulando atualizacao" -ForegroundColor DarkGray
}
# ==================== FIM AUTO-UPDATE ====================

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "[!] Python nao encontrado. Instale Python 3.8+ em python.org" -ForegroundColor Red
    pause
    exit 1
}

if (-not (Test-Path "requirements.txt")) {
    Write-Host "[!] requirements.txt nao encontrado" -ForegroundColor Red
    pause
    exit 1
}

$reqs = pip list --format=columns 2>$null
if ($reqs -notmatch "selenium") {
    Write-Host "[*] Instalando dependencias..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

if (-not $Email) { $Email = Read-Host "Email do Falai" }
if (-not $Senha) { $Senha = Read-Host "Senha do Falai" -AsSecureString; $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($Senha); $Senha = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR) }

$env:FALAI_EMAIL = $Email
$env:FALAI_SENHA = $Senha

$argsList = @()
if ($Headless) { $argsList += "--headless" }

Write-Host "[*] Iniciando bot Falai..." -ForegroundColor Green
python bot.py $argsList

pause
