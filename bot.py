import time
import random
import json
import os
import sys
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    ElementClickInterceptedException, StaleElementReferenceException
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
        self.wait = WebDriverWait(self.driver, 15)
        self.stats = {"respondidas": 0, "erros": 0, "inicio": datetime.now()}

    def _criar_driver(self, headless):
        opt = Options()
        if headless:
            opt.add_argument("--headless=new")
        opt.add_argument("--disable-blink-features=AutomationControlled")
        opt.add_argument("--window-size=1366,768")
        opt.add_experimental_option("excludeSwitches", ["enable-automation"])
        opt.add_experimental_option("useAutomationExtension", False)
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        }
        opt.add_experimental_option("prefs", prefs)
        return webdriver.Chrome(options=opt)

    def _rand(self, a=0.5, b=2.0):
        time.sleep(random.uniform(a, b))

    def _logar(self):
        log.info("Abrindo site...")
        self.driver.get(self.URL)
        self._rand(1, 3)

        # Aceitar cookies se aparecer
        try:
            btn = self.driver.find_element(By.CSS_SELECTOR, ".acceptcookies")
            btn.click()
            log.info("Cookies aceitos")
            self._rand()
        except:
            pass

        # Abrir dropdown "minha conta"
        try:
            btn_conta = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'minha conta')]"))
            )
            btn_conta.click()
            log.info("Dropdown 'minha conta' aberto")
            self._rand()
        except Exception as e:
            log.error(f"Falha ao abrir dropdown: {e}")
            raise

        # Preencher credenciais
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
            self._rand(2, 4)
        except Exception as e:
            log.error(f"Falha no login: {e}")
            raise

        # Verificar se apareceu erro
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

        # Aguardar redirect (mudanca de URL)
        try:
            self.wait.until(lambda d: "back.php" not in d.current_url)
        except:
            pass

        log.info(f"Login OK - URL atual: {self.driver.current_url}")
        return True

    def _achar_botao(self, textos):
        """Tenta encontrar um botoes por varios textos possiveis"""
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
        """Tenta responder uma pagina de pesquisa"""
        self._rand(1, 2)
        page_text = self.driver.page_source.lower()

        # Log URL para debug
        log.debug(f"URL: {self.driver.current_url[:100]}")

        # Se for pagina de agradecimento/fim
        if any(p in page_text for p in ["obrigado", "finalizada", "concluída", "terminou",
                                          "obrigada", "agradecemos", "survey complete"]):
            log.info("Pagina de conclusao detectada")
            return "COMPLETE"

        # 1. Tenta radio buttons (escolha unica)
        radios = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
        if radios:
            # Filtrar visiveis e habilitados
            visiveis = [r for r in radios if r.is_displayed() and r.is_enabled()]
            if visiveis:
                escolha = random.choice(visiveis)
                try:
                    # Clica no label associado se existir
                    label_id = escolha.get_attribute("id")
                    if label_id:
                        try:
                            label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{label_id}']")
                            label.click()
                        except:
                            escolha.click()
                    else:
                        escolha.click()
                    log.info(f"Radio marcado ({len(visiveis)} opcoes)")
                    self._rand()
                except ElementClickInterceptedException:
                    self.driver.execute_script("arguments[0].click();", escolha)
                    log.info("Radio clicado via JS")
                    self._rand()
                return "OK"

        # 2. Tenta checkboxes (multipla escolha) - marca algumas
        checks = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        visiveis_checks = [c for c in checks if c.is_displayed() and c.is_enabled()]
        if visiveis_checks:
            marca = random.sample(visiveis_checks, min(random.randint(1, 3), len(visiveis_checks)))
            for c in marca:
                try:
                    label_id = c.get_attribute("id")
                    if label_id:
                        try:
                            label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{label_id}']")
                            label.click()
                        except:
                            c.click()
                    else:
                        c.click()
                except ElementClickInterceptedException:
                    self.driver.execute_script("arguments[0].click();", c)
            log.info(f"{len(marca)} checkbox(es) marcado(s)")
            self._rand()
            return "OK"

        # 3. Tenta selects (dropdown)
        selects = self.driver.find_elements(By.TAG_NAME, "select")
        visiveis_selects = [s for s in selects if s.is_displayed()]
        for sel in visiveis_selects:
            try:
                select_obj = Select(sel)
                opcoes = select_obj.options
                validas = [o for o in opcoes if o.get_attribute("value")]
                if validas:
                    escolha = random.choice(validas)
                    select_obj.select_by_value(escolha.get_attribute("value"))
                    log.info("Select preenchido")
                    self._rand()
            except:
                pass
            return "OK"

        # 4. Tenta rating (estrelas, numeros)
        ratings = self.driver.find_elements(By.CSS_SELECTOR, ".rating, .star, [class*='rating'], [class*='star']")
        rating_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='range']")
        if ratings or rating_inputs:
            if ratings:
                clicaveis = [r for r in ratings if r.is_displayed()]
                if clicaveis:
                    clicaveis[0].click()
                    log.info("Rating clicado")
                    self._rand()
                    return "OK"
            if rating_inputs:
                for r in rating_inputs:
                    if r.is_displayed():
                        mid = (int(r.get_attribute("min") or 0) + int(r.get_attribute("max") or 10)) // 2
                        self.driver.execute_script(
                            f"arguments[0].value = {mid}; arguments[0].dispatchEvent(new Event('input'));",
                            r
                        )
                        log.info(f"Range setado para {mid}")
                        self._rand()
                        return "OK"

        # 5. Tenta textareas / inputs de texto
        textos = self.driver.find_elements(By.CSS_SELECTOR, "textarea, input[type='text'], input[type='email']")
        visiveis_textos = [t for t in textos if t.is_displayed() and t.is_enabled()]
        if visiveis_textos:
            respostas_texto = [
                "Sim, concordo",
                "Acho importante",
                "Poderia ser melhor",
                "Estou satisfeito",
                "Nao tenho opiniao formada",
                "Prefiro nao responder",
                "Talvez",
                "Sim",
                "Nao",
            ]
            for t in visiveis_textos[:3]:
                t.clear()
                t.send_keys(random.choice(respostas_texto))
                self._rand()
            log.info(f"Texto preenchido ({len(visiveis_textos[:3])} campo(s))")
            return "OK"

        return "NO_INTERACTION"

    def _avancar(self):
        """Tenta clicar em botoes de proximo/enviar"""
        textos_botao = [
            "Próximo", "Proximo", "Enviar", "OK", "Confirmar",
            "Salvar", "Continuar", "Avançar", "Avancar",
            "Finalizar", "Concluir", "Next", "Submit", "Continue",
            "Send", "Done", "Sim", "Nao", "Pular", "Pular pergunta"
        ]
        for tentativa in range(3):
            btn = self._achar_botao(textos_botao)
            if btn:
                try:
                    btn.click()
                    log.info(f"Botao '{btn.text.strip()[:20]}' clicado")
                    self._rand(0.5, 1.5)
                    return True
                except ElementClickInterceptedException:
                    self.driver.execute_script("arguments[0].click();", btn)
                    log.info("Botao clicado via JS")
                    self._rand()
                    return True
                except Exception as e:
                    log.warning(f"Erro ao clicar botao: {e}")
                    self._rand()
                    continue
        return False

    def _navegar_pesquisas(self):
        """Procura por pesquisas disponiveis no dashboard"""
        log.info("Procurando pesquisas disponiveis...")
        textos_pesquisa = [
            "Pesquisa", "Responder", "Participar", "Disponível",
            "Disponivel", "Nova pesquisa", "Iniciar", "Começar",
            "Start", "Survey", "responder"
        ]
        btn = self._achar_botao(textos_pesquisa)
        if btn:
            try:
                btn.click()
                log.info(f"Link de pesquisa clicado: '{btn.text.strip()[:30]}'")
                self._rand(2, 4)
                return True
            except Exception as e:
                log.warning(f"Erro ao clicar pesquisa: {e}")
        return False

    def rodar(self):
        """Loop principal"""
        log.info(f"Iniciando bot - Email: {self.email}")

        try:
            self._logar()
        except Exception as e:
            log.error(f"Nao foi possivel logar: {e}")
            self.driver.quit()
            return

        log.info("Iniciando loop de pesquisas...")
        max_sem_pesquisa = 0

        while True:
            try:
                # Tentar navegar para pesquisa se estiver no dashboard
                if "painel" in self.driver.current_url.lower() or "dashboard" in self.driver.current_url.lower() or "home" in self.driver.current_url.lower():
                    if not self._navegar_pesquisas():
                        max_sem_pesquisa += 1
                        log.info(f"Nenhuma pesquisa encontrada ({max_sem_pesquisa})")
                        if max_sem_pesquisa >= 3:
                            log.info("Recarregando pagina...")
                            self.driver.get(self.URL)
                            self._rand(3, 5)
                            try:
                                self._logar()
                            except:
                                pass
                            max_sem_pesquisa = 0
                        self._rand(5, 10)
                        continue

                max_sem_pesquisa = 0
                resultado = self._responder_pagina()

                if resultado == "COMPLETE":
                    self.stats["respondidas"] += 1
                    log.info(f"Pesquisa concluida! Total: {self.stats['respondidas']}")
                    # Voltar ao dashboard
                    self._rand(2, 4)
                    self.driver.get(self.URL)
                    self._rand(2, 3)
                    continue

                if resultado == "NO_INTERACTION":
                    log.info("Nada para interagir, tentando avancar...")

                if not self._avancar():
                    log.info("Sem botoes de acao. Tentando navegar...")
                    if not self._navegar_pesquisas():
                        self._rand(3, 6)
                        self.driver.refresh()
                        self._rand(3, 5)

            except KeyboardInterrupt:
                log.info("Parando pelo usuario...")
                break
            except Exception as e:
                self.stats["erros"] += 1
                log.error(f"Erro no loop: {e}")
                self._rand(3, 6)
                try:
                    self.driver.refresh()
                except:
                    log.error("Driver morreu, encerrando...")
                    break

        tempo = datetime.now() - self.stats["inicio"]
        log.info(f"=== FINALIZADO ===")
        log.info(f"Respondidas: {self.stats['respondidas']}")
        log.info(f"Erros: {self.stats['erros']}")
        log.info(f"Tempo: {tempo}")
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
