import time
import random
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

URL = "https://www.falai.com.vc/"
EMAIL = "seu@email.com"      # <-- ALTERE AQUI
SENHA = "sua_senha"          # <-- ALTERE AQUI

def agir(humano=True):
    if humano:
        time.sleep(random.uniform(0.8, 2.5))

def logar(driver):
    driver.get(URL)
    agir()
    try:
        btn_conta = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'minha conta')]"))
        )
        btn_conta.click()
        agir()
    except:
        print("[-] Botao 'minha conta' nao encontrado")

    try:
        email_input = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
        senha_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        email_input.send_keys(EMAIL)
        agir()
        senha_input.send_keys(SENHA)
        agir()
        btn_entrar = driver.find_element(By.XPATH, "//button[contains(text(),'Entrar')]")
        btn_entrar.click()
        print("[+] Login enviado")
        agir(False)
        time.sleep(3)
    except Exception as e:
        print(f"[-] Erro no login: {e}")

def responder(driver):
    while True:
        try:
            time.sleep(2)
            page = driver.page_source.lower()

            if "pesquisa" in page or "pesquisas" in page:
                links = driver.find_elements(By.XPATH, "//a[contains(text(),'Pesquisa') or contains(text(),'Responder') or contains(text(),'participar')]")
                if links:
                    links[0].click()
                    print("[*] Entrando na pesquisa")
                    agir()

            opcoes = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'], label.option, .radio-label")
            if opcoes:
                escolha = random.choice(opcoes)
                escolha.click()
                print("[*] Opcao marcada")
                agir()

            botoes = driver.find_elements(By.XPATH, "//button[contains(text(),'Proximo') or contains(text(),'Próximo') or contains(text(),'Enviar') or contains(text(),'OK') or contains(text(),'Confirmar') or contains(text(),'Salvar')]")
            if botoes:
                botoes[0].click()
                print("[*] Avancando/Enviando")
                agir()

            if "obrigado" in page or "finalizada" in page or "concluída" in page:
                print("[+] Pesquisa concluida! Aguardando proxima...")
                time.sleep(10)
                driver.get(URL)
                agir(False)
                time.sleep(3)

        except Exception as e:
            print(f"[-] Erro no loop: {e}")
            time.sleep(5)

def main():
    opt = Options()
    opt.add_argument("--disable-blink-features=AutomationControlled")
    opt.add_experimental_option("excludeSwitches", ["enable-automation"])

    driver = webdriver.Chrome(options=opt)
    print("[*] Iniciando...")

    try:
        logar(driver)
        time.sleep(3)
        responder(driver)
    except KeyboardInterrupt:
        print("\n[!] Parando...")
    finally:
        driver.quit()

if __name__ == "__main__":
    if EMAIL == "seu@email.com" or SENHA == "sua_senha":
        print("[!] Edite EMAIL e SENHA no bot.py antes de rodar")
        sys.exit(1)
    main()
