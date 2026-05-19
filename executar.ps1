param(
    [string]$Email = "",
    [string]$Senha = ""
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Verifica Python
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "[!] Python nao encontrado. Instale Python 3.10+ em python.org" -ForegroundColor Red
    pause
    exit 1
}

# Instala dependencias se faltar
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

# Pede credenciais se nao foram passadas
if (-not $Email) { $Email = Read-Host "Email do Falai" }
if (-not $Senha) { $Senha = Read-Host "Senha do Falai" -AsSecureString; $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($Senha); $Senha = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR) }

# Gera um bot.py temporario com as credenciais
$codigo = @"
import time, random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://www.falai.com.vc/"
EMAIL = "$Email"
SENHA = "$Senha"

def agir():
    time.sleep(random.uniform(0.8, 2.5))

def logar(driver):
    driver.get(URL)
    agir()
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'minha conta')]"))).click()
        agir()
    except: pass
    try:
        driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys(EMAIL)
        agir()
        driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(SENHA)
        agir()
        driver.find_element(By.XPATH, "//button[contains(text(),'Entrar')]").click()
        print("[+] Login OK")
        time.sleep(3)
    except Exception as e: print(f"[-] Login: {e}")

def responder(driver):
    while True:
        time.sleep(2)
        try:
            opcoes = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'], label.option, .radio-label")
            if opcoes: random.choice(opcoes).click(); print("[*] Resposta"); agir()
            botoes = driver.find_elements(By.XPATH, "//button[contains(text(),'Proximo') or contains(text(),'Pr\u00f3ximo') or contains(text(),'Enviar') or contains(text(),'OK') or contains(text(),'Confirmar') or contains(text(),'Salvar')]")
            if botoes: botoes[0].click(); print("[*] Avancou"); agir()
            p = driver.page_source.lower()
            if "obrigado" in p or "finalizada" in p or "conclu" in p:
                print("[+] Concluida"); time.sleep(10); driver.get(URL); time.sleep(3)
        except Exception as e: print(f"[-] {e}"); time.sleep(5)

opt = Options()
opt.add_argument("--disable-blink-features=AutomationControlled")
opt.add_experimental_option("excludeSwitches", ["enable-automation"])
driver = webdriver.Chrome(options=opt)
try: logar(driver); responder(driver)
except KeyboardInterrupt: print("\n[!] Parando")
finally: driver.quit()
"@

$tempPy = Join-Path $env:TEMP "falai_bot_run.py"
Set-Content -Path $tempPy -Value $codigo -Encoding UTF8

Write-Host "[*] Iniciando bot Falai..." -ForegroundColor Green
python $tempPy

Remove-Item $tempPy -Force -ErrorAction SilentlyContinue
pause
