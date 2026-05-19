import time
import random
import os
import sys
import logging
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    ElementClickInterceptedException
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("falai-bot")


class FalaiBot:
    URL = "https://www.falai.com.vc/"

    def __init__(self, email, senha, headless=False):
        self.email = email
        self.senha = senha
        self.driver = self._criar_driver(headless)
        self.wait = WebDriverWait(self.driver, 20)
        self.stats = {"respondidas": 0, "erros": 0, "inicio": datetime.now()}

    def _criar_driver(self, headless):
        opt = Options()
        if headless:
            opt.add_argument("--headless=new")
        opt.add_argument("--window-size=1366,768")
        opt.add_argument("--disable-gpu")
        opt.add_argument("--no-sandbox")
        opt.add_argument("--disable-dev-shm-usage")
        # Anti-detecção
        opt.add_argument("--disable-blink-features=AutomationControlled")
        opt.add_experimental_option("excludeSwitches", ["enable-automation"])
        opt.add_experimental_option("useAutomationExtension", False)
        prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False}
        opt.add_experimental_option("prefs", prefs)

        driver = webdriver.Chrome(options=opt)

        # Esconde navigator.webdriver
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en'] });
            """
        })
        return driver

    def _rand(self, a=0.5, b=2.0):
        time.sleep(random.uniform(a, b))

    def _logar(self):
        log.info("Abrindo site...")
        self.driver.get(self.URL)
        self._rand(2, 4)

        try:
            btn_cookie = self.driver.find_element(By.CSS_SELECTOR, ".acceptcookies")
            btn_cookie.click()
            log.info("Cookies aceitos")
            self._rand()
        except:
            pass

        try:
            btn_conta = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'minha conta')]"))
            )
            btn_conta.click()
            log.info("Dropdown aberto")
            self._rand(1, 2)
        except Exception as e:
            log.error(f"Falha ao abrir dropdown: {e}")
            raise

        try:
            email_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            senha_input = self.driver.find_element(By.ID, "password")
            email_input.clear()
            email_input.send_keys(self.email)
            self._rand()
            senha_input.clear()
            senha_input.send_keys(self.senha)
            self._rand()

            btn_entrar = self.driver.find_element(By.ID, "btnLogar")
            btn_entrar.click()
            log.info("Login enviado")
            self._rand(3, 5)
        except Exception as e:
            log.error(f"Falha no preenchimento: {e}")
            raise

        try:
            erro = self.driver.find_element(By.CSS_SELECTOR, "#modalMsg .modal-body")
            if erro.is_displayed():
                msg = erro.text.strip()
                log.error(f"Erro no login: {msg}")
                raise Exception(f"Login falhou: {msg}")
        except TimeoutException:
            pass
        except NoSuchElementException:
            pass

        log.info(f"Login OK - URL: {self.driver.current_url[:80]}")
        return True

    def _achar_botao(self, textos):
        for texto in textos:
            for tag in ["button", "a", "span", "div"]:
                try:
                    elem = self.driver.find_element(
                        By.XPATH,
                        f"//{tag}[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{texto.lower()}')]"
                    )
                    if elem.is_displayed():
                        return elem
                except:
                    pass
        return None

    def _responder_pagina(self):
        self._rand(1, 2)
        page_text = self.driver.page_source.lower()

        if any(p in page_text for p in ["obrigado", "obrigada", "finalizada", "concluída",
                                          "terminou", "agradecemos", "survey complete"]):
            log.info("Pesquisa concluida")
            return "COMPLETE"

        radios = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
        visiveis = [r for r in radios if r.is_displayed() and r.is_enabled()]
        if visiveis:
            escolha = random.choice(visiveis)
            try:
                label_id = escolha.get_attribute("id")
                if label_id:
                    try:
                        self.driver.find_element(By.CSS_SELECTOR, f"label[for='{label_id}']").click()
                    except:
                        escolha.click()
                else:
                    escolha.click()
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", escolha)
            log.info(f"Radio respondido ({len(visiveis)} opcoes)")
            self._rand()
            return "OK"

        checks = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        visiveis = [c for c in checks if c.is_displayed() and c.is_enabled()]
        if visiveis:
            marca = random.sample(visiveis, min(random.randint(1, 3), len(visiveis)))
            for c in marca:
                try:
                    label_id = c.get_attribute("id")
                    if label_id:
                        try:
                            self.driver.find_element(By.CSS_SELECTOR, f"label[for='{label_id}']").click()
                        except:
                            c.click()
                    else:
                        c.click()
                except ElementClickInterceptedException:
                    self.driver.execute_script("arguments[0].click();", c)
            log.info(f"{len(marca)} checkbox(es) marcado(s)")
            self._rand()
            return "OK"

        selects = self.driver.find_elements(By.TAG_NAME, "select")
        for sel in selects:
            if not sel.is_displayed():
                continue
            try:
                s = Select(sel)
                opcoes = [o for o in s.options if o.get_attribute("value")]
                if opcoes:
                    s.select_by_value(random.choice(opcoes).get_attribute("value"))
                    log.info("Select preenchido")
                    self._rand()
                    return "OK"
            except:
                pass

        ranges = self.driver.find_elements(By.CSS_SELECTOR, "input[type='range']")
        for r in ranges:
            if r.is_displayed():
                min_v = int(r.get_attribute("min") or 0)
                max_v = int(r.get_attribute("max") or 10)
                mid = (min_v + max_v) // 2
                self.driver.execute_script(
                    f"arguments[0].value = {mid}; arguments[0].dispatchEvent(new Event('input'));"
                    f"arguments[0].dispatchEvent(new Event('change'));",
                    r
                )
                log.info(f"Range {mid}")
                self._rand()
                return "OK"

        textos = self.driver.find_elements(By.CSS_SELECTOR, "textarea, input[type='text'], input[type='email']")
        visiveis = [t for t in textos if t.is_displayed() and t.is_enabled()]
        if visiveis:
            respostas = [
                "Sim, concordo", "Acho importante", "Poderia ser melhor",
                "Estou satisfeito", "Nao tenho opiniao", "Prefiro nao responder",
                "Talvez", "Sim", "Nao", "Regular", "Bom", "Otimo"
            ]
            for t in visiveis[:3]:
                t.clear()
                t.send_keys(random.choice(respostas))
                self._rand()
            log.info(f"Texto preenchido ({len(visiveis[:3])} campo(s))")
            return "OK"

        return "NO_INTERACTION"

    def _avancar(self):
        textos = [
            "Próximo", "Proximo", "Enviar", "OK", "Confirmar",
            "Salvar", "Continuar", "Avançar", "Avancar",
            "Finalizar", "Concluir", "Next", "Submit", "Continue",
            "Send", "Done", "Sim", "Nao", "Pular"
        ]
        for _ in range(3):
            btn = self._achar_botao(textos)
            if btn:
                try:
                    btn.click()
                    log.info(f"Botao '{btn.text.strip()[:20]}'")
                    self._rand(0.5, 1.5)
                    return True
                except ElementClickInterceptedException:
                    self.driver.execute_script("arguments[0].click();", btn)
                    self._rand()
                    return True
                except Exception as e:
                    log.warning(f"Erro no botao: {e}")
                    self._rand()
        return False

    def _navegar_pesquisas(self):
        log.info("Procurando pesquisas...")
        textos = [
            "Pesquisa", "Responder", "Participar", "Disponível",
            "Disponivel", "Nova pesquisa", "Iniciar", "Começar",
            "Start", "Survey", "responder"
        ]
        btn = self._achar_botao(textos)
        if btn:
            try:
                btn.click()
                log.info(f"Link: '{btn.text.strip()[:30]}'")
                self._rand(2, 4)
                return True
            except:
                pass
        return False

    def rodar(self):
        log.info(f"Iniciando bot: {self.email}")

        try:
            self._logar()
        except Exception as e:
            log.error(f"Login falhou: {e}")
            self.driver.quit()
            return

        log.info("Loop de pesquisas...")
        max_sem = 0

        while True:
            try:
                url = self.driver.current_url.lower()
                if any(p in url for p in ["painel", "dashboard", "home", "falai.com.vc"]):
                    if not self._navegar_pesquisas():
                        max_sem += 1
                        log.info(f"Sem pesquisa ({max_sem})")
                        if max_sem >= 3:
                            log.info("Recarregando...")
                            self.driver.get(self.URL)
                            self._rand(3, 5)
                            try:
                                self._logar()
                            except:
                                pass
                            max_sem = 0
                        self._rand(5, 10)
                        continue

                max_sem = 0
                res = self._responder_pagina()

                if res == "COMPLETE":
                    self.stats["respondidas"] += 1
                    log.info(f"Concluida! Total: {self.stats['respondidas']}")
                    self._rand(2, 4)
                    self.driver.get(self.URL)
                    self._rand(2, 3)
                    continue

                if not self._avancar():
                    log.info("Sem acao. Tentando navegar...")
                    if not self._navegar_pesquisas():
                        self._rand(3, 6)
                        self.driver.refresh()
                        self._rand(3, 5)

            except KeyboardInterrupt:
                log.info("Parando...")
                break
            except Exception as e:
                self.stats["erros"] += 1
                log.error(f"Erro: {e}")
                self._rand(3, 6)
                try:
                    self.driver.refresh()
                except:
                    log.error("Driver morreu")
                    break

        t = datetime.now() - self.stats["inicio"]
        log.info(f"=== FIM ===")
        log.info(f"Respondidas: {self.stats['respondidas']}")
        log.info(f"Erros: {self.stats['erros']}")
        log.info(f"Tempo: {t}")
        self.driver.quit()


if __name__ == "__main__":
    email = os.environ.get("FALAI_EMAIL", "")
    senha = os.environ.get("FALAI_SENHA", "")

    if not email:
        email = input("Email do Falai: ").strip()
    if not senha:
        import getpass
        senha = getpass.getpass("Senha do Falai: ")

    headless = "--headless" in sys.argv or "-h" in sys.argv

    bot = FalaiBot(email, senha, headless=headless)
    bot.rodar()
