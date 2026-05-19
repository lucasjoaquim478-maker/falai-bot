param(
    [string]$Email = "",
    [string]$Senha = "",
    [switch]$Headless
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

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
