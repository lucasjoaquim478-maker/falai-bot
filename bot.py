import time
import random
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    ElementClickInterceptedException, StaleElementReferenceException,
    JavascriptException, WebDriverException
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("falai-bot")


class FalaiBot:
    URL = "https://www.falai.com.vc/"

    def __init__(self, email, senha, headless=False, debug_dir="debug"):
        self.email = email
        self.senha = senha
        self.headless = headless
        self.debug_dir = Path(debug_dir)
        self.debug_dir.mkdir(exist_ok=True)
        self.driver = None
        self.wait = None
        self.stats = {"respondidas": 0, "erros": 0, "inicio": datetime.now()}
        self._init_driver()

    def _init_driver(self):
        import subprocess
        subprocess.run("taskkill /f /im chromedriver.exe 2>nul", shell=True, capture_output=True)
        self._rand(1, 2)

        opt = Options()
        if self.headless:
            opt.add_argument("--headless=new")
        opt.add_argument("--window-size=1366,768")
        opt.add_argument("--disable-gpu")
        opt.add_argument("--no-sandbox")
        opt.add_argument("--disable-dev-shm-usage")
        opt.add_argument("--disable-blink-features=AutomationControlled")
        opt.add_argument("--disable-extensions")
        opt.add_argument("--remote-debugging-port=0")
        opt.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        opt.add_experimental_option("useAutomationExtension", False)
        opt.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        })

        self.driver = webdriver.Chrome(options=opt)
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en'] });
                Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
            """
        })
        self.wait = WebDriverWait(self.driver, 20)

    def _rand(self, a=0.5, b=2.0):
        time.sleep(random.uniform(a, b))

    def _debug(self, name):
        try:
            ts = datetime.now().strftime("%H%M%S")
            self.driver.save_screenshot(str(self.debug_dir / f"{ts}_{name}.png"))
            with open(str(self.debug_dir / f"{ts}_{name}.html"), "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
        except:
            pass

    # ==================== LOGIN ====================

    def _logar(self):
        log.info("=" * 50)
        log.info("LOGIN")
        log.info("=" * 50)
        self.driver.get(self.URL)
        self._rand(2, 4)

        try:
            btn = self.driver.find_element(By.CSS_SELECTOR, ".acceptcookies")
            btn.click()
            log.info("Cookies aceitos")
            self._rand()
        except:
            pass

        log.info("Aguardando jQuery...")
        try:
            self.wait.until(lambda d: d.execute_script("return typeof jQuery !== 'undefined'"))
        except:
            log.warning("jQuery nao detectado, tentando mesmo assim")

        log.info("Enviando login via AJAX...")
        self._debug("antes_login")
        self._rand(1, 2)

        # Verificar URL atual
        url_atual = self.driver.current_url
        log.info(f"URL antes do login: {url_atual}")
        if "portal" in url_atual:
            log.info("Ja esta no portal, login desnecessario")
            return True

        js = """
        const email = arguments[0];
        const senha = arguments[1];
        const done = arguments[2];

        function tentarLogin() {
            // Tenta via jQuery
            if (typeof jQuery !== 'undefined') {
                jQuery.post("back.php", {
                    email: email,
                    s: senha,
                    info: "logar",
                    pesquisaID: '',
                    statusID: '',
                    PainelistaID: '',
                    entrevistadoID: ''
                }, function(data) {
                    if (data && data.dados && data.dados.redirect) {
                        window.location.href = data.dados.redirect;
                        done(true);
                    } else {
                        done(JSON.stringify(data || 'null').slice(0,200));
                    }
                }).fail(function(jq) {
                    done('jq_fail:' + (jq.status || '') + ' ' + (jq.responseText || '').slice(0,100));
                });
            } else {
                // Fallback: fetch nativo
                var form = new FormData();
                form.append('email', email);
                form.append('s', senha);
                form.append('info', 'logar');
                form.append('pesquisaID', '');
                form.append('statusID', '');
                form.append('PainelistaID', '');
                form.append('entrevistadoID', '');

                fetch('back.php', { method: 'POST', body: form })
                    .then(r => r.json())
                    .then(data => {
                        if (data && data.dados && data.dados.redirect) {
                            window.location.href = data.dados.redirect;
                            done(true);
                        } else {
                            done(JSON.stringify(data || 'null').slice(0,200));
                        }
                    })
                    .catch(e => done('fetch_fail:' + (e.message || '').slice(0,100)));
            }
        }

        // Preenche campos tambem (alguns sites precisam)
        var u = document.getElementById('username');
        var p = document.getElementById('password');
        if (u) u.value = email;
        if (p) p.value = senha;

        tentarLogin();
        """

        try:
            sucesso = self.driver.execute_async_script(js, self.email, self.senha)
            self._rand(3, 5)
        except Exception as e:
            self._debug("erro_login")
            raise

        if sucesso is True:
            log.info(f"Login OK! URL: {self.driver.current_url[:80]}")
            self._debug("pos_login")
            self._rand(2, 3)
            return True

        if sucesso and isinstance(sucesso, str):
            log.warning(f"Resposta do servidor: {sucesso[:150]}")

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

        raise Exception("Login falhou - sem redirect do servidor")

    # ==================== NAVEGACAO ====================

    def _extrair_texto(self, el):
        """Extrai texto de um elemento incluindo filhos"""
        try:
            return el.text.strip()
        except:
            return ""

    def _extrair_href(self, el):
        """Extrai href de um elemento"""
        try:
            return el.get_attribute("href") or ""
        except:
            return ""

    def _extrair_html(self, el):
        """Extrai outerHTML de um elemento"""
        try:
            return (el.get_attribute("outerHTML") or "")[:300]
        except:
            return ""

    def _clicar(self, el):
        """Tenta clicar de varias formas"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({behavior:'instant',block:'center'});", el)
            self._rand(0.3, 0.8)
            try:
                el.click()
            except:
                self.driver.execute_script("arguments[0].click();", el)
            return True
        except Exception as e:
            log.warning(f"Falha no clique: {e}")
            return False

    def _listar_elementos(self):
        """Lista todos elementos clicaveis da pagina"""
        js = """
        function getText(el) {
            var t = el.textContent || el.value || '';
            if (!t.trim() && el.type === 'submit') t = el.value || '';
            return t.trim().slice(0, 100);
        }

        var todos = document.querySelectorAll('a, button, input, [role="button"], [onclick], li, td, span, div, h1, h2, h3, h4, h5, p, label');
        var resultado = [];
        for (var i = 0; i < todos.length; i++) {
            var el = todos[i];
            try {
                var style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') continue;
                var texto = getText(el);
                if (!texto && !el.getAttribute('href') && !el.getAttribute('onclick')) continue;
                resultado.push({
                    tag: el.tagName.toLowerCase(),
                    texto: texto,
                    href: el.getAttribute('href') || '',
                    onclick: (el.getAttribute('onclick') || '').slice(0, 50),
                    classe: (el.getAttribute('class') || '').slice(0, 60),
                    id: el.getAttribute('id') || '',
                    type: el.getAttribute('type') || '',
                    role: el.getAttribute('role') || ''
                });
            } catch(e) {}
        }
        return resultado;
        """
        try:
            return self.driver.execute_script(js)
        except Exception as e:
            log.warning(f"Erro listar elementos via JS: {e}")
            # Fallback: selenium puro
            els = []
            for tag in ["a", "button", "span", "div", "li", "label"]:
                for el in self.driver.find_elements(By.TAG_NAME, tag):
                    try:
                        if el.is_displayed():
                            txt = el.text.strip()
                            href = el.get_attribute("href") or ""
                            if txt or href:
                                els.append({
                                    "tag": tag,
                                    "texto": txt[:100],
                                    "href": href[:100],
                                    "onclick": "",
                                    "classe": (el.get_attribute("class") or "")[:60],
                                    "id": el.get_attribute("id") or "",
                                    "type": el.get_attribute("type") or "",
                                    "role": el.get_attribute("role") or ""
                                })
                    except:
                        pass
            return els

    def _logar_elementos(self, elementos):
        """Loga todos elementos encontrados"""
        log.info(f"Elementos visiveis: {len(elementos)}")
        # Agrupa por tag
        for tag in ["button", "a", "span", "div", "input", "li", "td"]:
            els = [e for e in elementos if e["tag"] == tag and e["texto"]]
            if els:
                log.info(f"  <{tag}>: {len(els)} com texto")
                for e in els[:8]:
                    log.info(f"    '{e['texto'][:50]}' href={e['href'][:40]} class={e['classe'][:30]}")

    def _achar_botao_pesquisa(self, elementos):
        """Procura o botao de pesquisa usando multiplas estrategias"""
        import re

        # Ignorar elementos de navegacao/naturais
        ignorar = {"pesquisas disponíveis", "pesquisas disponiveis", "extrato",
                    "informações cadastrais", "informacoes cadastrais",
                    "indique um amigo", "portal de recompensas", "blog", "sair",
                    "home", "sobre", "cadastre-se", "minha conta", "entrar",
                    "clique aqui"}

        # PRIORIDADE 1: Codigos de pesquisa (GZRK975, UHPQ8UX) - texto ORIGINAL
        for el in elementos:
            txt_orig = el["texto"]
            cods = re.findall(r'[A-Z0-9]{6,8}', txt_orig)
            if cods and txt_orig.lower() not in ignorar:
                log.info(f"[PRIORIDADE-1] Codigo '{cods[0]}' em '{txt_orig[:40]}'")
                return el

        # PRIORIDADE 2: "responder agora" ou "responda agora"
        for el in elementos:
            txt = el["texto"].lower()
            if ("responder agora" in txt or "responda agora" in txt) and txt not in ignorar:
                log.info(f"[PRIORIDADE-2] '{el['texto'][:40]}'")
                return el

        # PRIORIDADE 3: Palavras-chave de pesquisa (texto original)
        for el in elementos:
            txt = el["texto"].lower()
            if any(kw in txt for kw in ["respond", "pesquis", "particip",
                                          "disponiv", "inici", "agora",
                                          "survey", "comec", "avali"]):
                if txt not in ignorar and len(txt) > 3:
                    log.info(f"[PRIORIDADE-3] '{el['texto'][:40]}'")
                    return el

        # PRIORIDADE 4: Links externos (exceto blog, redes sociais)
        for el in elementos:
            txt = el["texto"].lower()
            href = el["href"]
            if href and "falai.com.vc" not in href and href.startswith("http"):
                if "blog" not in txt and "facebook" not in href and "instagram" not in href and "tiktok" not in href:
                    log.info(f"[PRIORIDADE-4] externo '{el['texto'][:30]}'")
                    return el

        # PRIORIDADE 5: Elementos com digitos + letras (codigos parciais)
        for el in elementos:
            txt_orig = el["texto"]
            cods = re.findall(r'[A-Z0-9]{4,}', txt_orig)
            if cods and txt_orig.lower() not in ignorar:
                log.info(f"[PRIORIDADE-5] Codigo parcial '{txt_orig[:30]}'")
                return el

        return None

    def _navegar_pesquisas(self):
        log.info("=" * 50)
        log.info("NAVEGANDO - Buscando pesquisas")
        log.info(f"URL: {self.driver.current_url[:100]}")
        log.info(f"Titulo: {self.driver.title[:60]}")
        self._debug("dashboard")

        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            log.info(f"TEXTO PAGINA: {body.text[:1500].replace(chr(10),' | ')}")
        except:
            pass

        elementos = self._listar_elementos()
        self._logar_elementos(elementos)

        if not elementos:
            log.warning("Nenhum elemento encontrado!")
            return False

        alvo = self._achar_botao_pesquisa(elementos)

        if alvo:
            log.info(f"Alvo: '{alvo['texto'][:50]}' tag=<{alvo['tag']}>")

            # Extrair URL do ConviteID e navegar direto pra pesquisa
            try:
                link_el = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'ConviteID')]"))
                )
                url = link_el.get_attribute("href")
                if url:
                    log.info(f"ConviteID: {url[:100]}")
                    self.driver.get(url)
                    self._rand(4, 6)
                    if self._em_pesquisa():
                        return True
                    if len(self.driver.window_handles) > 1:
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        if self._em_pesquisa():
                            return True
            except TimeoutException:
                log.info("ConviteID nao encontrado")
            except Exception as e:
                log.warning(f"Erro ConviteID: {e}")
        return False

    def _em_pesquisa(self):
        url = self.driver.current_url.lower()
        if "falai.com.vc" in url or "painel" in url or "home" in url or "login" in url:
            return False
        try:
            src = self.driver.page_source.lower()
            if any(p in src for p in ["pergunta", "questão", "questao", "marque",
                                        "escolha", "selecione", "próximo", "proximo",
                                        "enviar", "radio", "checkbox", "input",
                                        "option", "select", "survey", "quiz"]):
                return True
        except:
            pass
        return True  # URL diferente de falai = assumir que eh pesquisa

    # ==================== RESPONDER ====================

    def _responder_pagina(self):
        self._rand(1, 2)
        url = self.driver.current_url.lower()
        page = self.driver.page_source.lower()

        log.info(f"Respondendo... URL: {url[:80]}")

        if any(p in page for p in ["finalizada", "concluída",
                                      "terminou", "survey complete",
                                      "suas respostas foram salvas",
                                      "pesquisa encerrada", "encerrada",
                                      "você já respondeu", "voce ja respondeu"]):
            log.info("Pesquisa ja concluida/finalizada")
            return "COMPLETE"

        # Procura em iframes primeiro
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        for i, iframe in enumerate(iframes):
            try:
                self.driver.switch_to.frame(iframe)
                log.info(f"Verificando iframe {i}")
                res = self._responder_conteudo()
                self.driver.switch_to.default_content()
                if res != "NO_INTERACTION":
                    return res
            except:
                pass
            finally:
                self.driver.switch_to.default_content()

        # Responde na pagina principal
        return self._responder_conteudo()

    def _responder_conteudo(self):
        # Tenta radios visiveis (inputs normais)
        radios = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
        visiveis = [r for r in radios if r.is_displayed() and r.is_enabled()]
        if visiveis:
            escolha = random.choice(visiveis)
            self._clicar_radio(escolha)
            log.info(f"Radio ({len(visiveis)} opcoes)")
            self._rand()
            return "OK"

        # Tenta radios ocultos (Etalks/FastQuest: input display:none + label visivel)
        todos_radios = [r for r in radios if r.is_enabled()]
        if todos_radios:
            escolha = random.choice(todos_radios)
            # Tenta clicar no label associado
            radio_id = escolha.get_attribute("id")
            clicou = False
            if radio_id:
                try:
                    lbl = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{radio_id}']")
                    if lbl.is_displayed():
                        lbl.click()
                        clicou = True
                except:
                    pass
            if not clicou:
                self.driver.execute_script("arguments[0].click();", escolha)
            log.info(f"Radio oculto ({len(todos_radios)} opcoes)")
            self._rand()
            return "OK"

        # Tenta checkboxes visiveis
        checks = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        visiveis = [c for c in checks if c.is_displayed() and c.is_enabled()]
        if visiveis:
            qtd = min(random.randint(1, 3), len(visiveis))
            for c in random.sample(visiveis, qtd):
                self._clicar_radio(c)
            log.info(f"{qtd} checkbox(es)")
            self._rand()
            return "OK"

        # Tenta checkboxes ocultos
        todos_checks = [c for c in checks if c.is_enabled()]
        if todos_checks:
            qtd = min(random.randint(1, 3), len(todos_checks))
            for c in random.sample(todos_checks, qtd):
                cid = c.get_attribute("id")
                clicou = False
                if cid:
                    try:
                        lbl = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{cid}']")
                        if lbl.is_displayed():
                            lbl.click()
                            clicou = True
                    except:
                        pass
                if not clicou:
                    self.driver.execute_script("arguments[0].click();", c)
            log.info(f"{qtd} checkbox(es) oculto(s)")
            self._rand()
            return "OK"

        selects = [s for s in self.driver.find_elements(By.TAG_NAME, "select") if s.is_displayed()]
        if selects:
            for sel in selects:
                try:
                    s = Select(sel)
                    opts = [o for o in s.options if o.get_attribute("value")]
                    if opts:
                        s.select_by_value(random.choice(opts).get_attribute("value"))
                        log.info("Select")
                        self._rand()
                        return "OK"
                except:
                    pass

        ranges = [r for r in self.driver.find_elements(By.CSS_SELECTOR, "input[type='range']") if r.is_displayed()]
        for r in ranges:
            min_v = int(r.get_attribute("min") or 0)
            max_v = int(r.get_attribute("max") or 10)
            mid = (min_v + max_v) // 2
            self.driver.execute_script(
                f"arguments[0].value = {mid}; arguments[0].dispatchEvent(new Event('input')); arguments[0].dispatchEvent(new Event('change'));", r
            )
            log.info(f"Range {mid}")
            self._rand()
            return "OK"

        textos = [t for t in self.driver.find_elements(By.CSS_SELECTOR, "textarea, input[type='text'], input[type='email'], input[type='tel']")
                  if t.is_displayed() and t.is_enabled()]
        if textos:
            respostas = [
                "Sim", "Nao", "Talvez", "Sim, concordo", "Nao concordo",
                "Regular", "Bom", "Otimo", "Excelente", "Ruim",
                "Muito bom", "Satisfeito", "Insatisfeito", "Neutro",
                "Diariamente", "Semanalmente", "Mensalmente", "Raramente",
                "Nunca", "Sim, gostei", "Nao gostei", "Indiferente"
            ]
            for t in textos[:3]:
                t.clear()
                t.send_keys(random.choice(respostas))
                self._rand()
            log.info(f"Texto ({len(textos[:3])})")
            return "OK"

        # Tenta estrelas/rating
        estrelas = self.driver.find_elements(By.CSS_SELECTOR, "[class*='star'], [class*='rating'], [class*='estrela']")
        clicaveis = [e for e in estrelas if e.is_displayed()]
        if clicaveis:
            self._clicar(random.choice(clicaveis))
            log.info("Estrela/Rating")
            self._rand()
            return "OK"

        # Tenta tabelas de opcao
        celulas = self.driver.find_elements(By.CSS_SELECTOR, "td, th")
        clicaveis = [c for c in celulas if c.is_displayed() and c.text.strip()]
        if clicaveis:
            for c in random.sample(clicaveis, min(3, len(clicaveis))):
                self._clicar(c)
                self._rand()
            log.info("Celula tabela")
            return "OK"

        # Tenta labels de check-group (Etalks/FastQuest)
        labels = self.driver.find_elements(By.CSS_SELECTOR, ".check-group label, .check-label label, label[class*='check']")
        clicaveis = [l for l in labels if l.is_displayed() and l.text.strip()]
        if clicaveis:
            escolha = random.choice(clicaveis)
            self._clicar(escolha)
            log.info(f"Label check-group ({len(clicaveis)} opcoes): {escolha.text.strip()[:30]}")
            self._rand()
            return "OK"

        # Tenta qualquer label clicavel associado a input oculto
        labels_geral = self.driver.find_elements(By.CSS_SELECTOR, "label")
        clicaveis = [l for l in labels_geral if l.is_displayed() and l.text.strip() and l.get_attribute("for")]
        if clicaveis:
            escolha = random.choice(clicaveis)
            inp_id = escolha.get_attribute("for")
            try:
                inp = self.driver.find_element(By.ID, inp_id)
                if inp.tag_name.lower() in ["input", "select", "textarea"] and not inp.is_selected():
                    self._clicar(escolha)
                    log.info(f"Label generico ({len(clicaveis)} opcoes): {escolha.text.strip()[:30]}")
                    self._rand()
                    return "OK"
            except:
                pass

        return "NO_INTERACTION"

    def _clicar_radio(self, el):
        try:
            label_id = el.get_attribute("id")
            if label_id:
                try:
                    lbl = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{label_id}']")
                    lbl.click()
                    return
                except:
                    pass
            el.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", el)
        except:
            pass

    # ==================== BOTOES ====================

    def _avancar(self):
        textos = [
            "Próximo", "Proximo", "Próxima", "Proxima",
            "Enviar", "OK", "Confirmar", "Salvar",
            "Continuar", "Avançar", "Avancar",
            "Finalizar", "Concluir", "Next", "Submit",
            "Continue", "Send", "Done", "Sim", "Nao",
            "Pular", "Pular pergunta", "Nao quero responder",
            "Prefiro nao responder", "Talvez depois",
            "Enviar respostas", "Enviar pesquisa",
            "Concluir pesquisa", "Finalizar pesquisa",
            "Terminar", "Terminar pesquisa"
        ]
        trans = "translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZÃÁÀÂÄÉÈÊẼËÍÌÎÏÓÒÔÖÕÚÙÛÜÇÑ','abcdefghijklmnopqrstuvwxyzãáàâäéèêẽëíìîïóòôöõúùûüçñ')"
        for _ in range(3):
            for texto in textos:
                lower = texto.lower()
                for tag in ["button", "a", "span", "input", "div"]:
                    for expr in [f"//{tag}[contains({trans},'{lower}')]",
                                 f"//{tag}[contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZÃÁÀÂÄÉÈÊẼËÍÌÎÏÓÒÔÖÕÚÙÛÜÇÑ','abcdefghijklmnopqrstuvwxyzãáàâäéèêẽëíìîïóòôöõúùûüçñ'),'{lower}')]"]:
                        try:
                            el = self.driver.find_element(By.XPATH, expr)
                            if el.is_displayed():
                                if self._clicar(el):
                                    log.info(f"Botao '{texto}'")
                                    self._rand(0.5, 1.5)
                                    return True
                        except:
                            continue
            self._rand()
        return False

    # ==================== LOOP PRINCIPAL ====================

    def rodar(self):
        log.info("=" * 60)
        log.info("FALAI BOT - Iniciando")
        log.info(f"Email: {self.email}")
        log.info(f"Headless: {self.headless}")
        log.info("=" * 60)

        try:
            self._logar()
        except Exception as e:
            log.error(f"LOGIN FALHOU: {e}")
            self._debug("erro_login")
            self.driver.quit()
            return

        log.info("=" * 60)
        log.info("INICIANDO LOOP DE PESQUISAS")
        log.info("=" * 60)

        ciclos_sem_pesquisa = 0
        em_pesquisa = False
        url_anterior = ""
        cliques_seguidos = 0

        while True:
            try:
                url_atual = self.driver.current_url.lower()
                if url_atual != url_anterior:
                    log.info(f"URL mudou: {url_atual[:100]}")
                    url_anterior = url_atual
                    self._debug("url_change")
                    cliques_seguidos = 0

                # Detectar se esta em pagina de pesquisa
                nesta_pesquisa = self._em_pesquisa()

                if not nesta_pesquisa and not em_pesquisa:
                    # Esta no Falai, procurar pesquisa
                    if self._navegar_pesquisas():
                        ciclos_sem_pesquisa = 0
                        em_pesquisa = True
                        self._rand(3, 5)
                        continue
                    else:
                        ciclos_sem_pesquisa += 1
                        log.info(f"Sem pesquisa disponivel (ciclo {ciclos_sem_pesquisa})")

                        if ciclos_sem_pesquisa >= 5:
                            log.info("Recarregando pagina...")
                            self.driver.get(self.URL)
                            self._rand(4, 6)
                            try:
                                self._logar()
                            except:
                                pass
                            ciclos_sem_pesquisa = 0

                        self._rand(8, 15)
                        continue

                if nesta_pesquisa:
                    em_pesquisa = True
                    ciclos_sem_pesquisa = 0

                # Responder pesquisa
                resultado = self._responder_pagina()

                if resultado == "COMPLETE":
                    self.stats["respondidas"] += 1
                    em_pesquisa = False
                    log.info(f"PESQUISA CONCLUIDA! Total: {self.stats['respondidas']}")
                    self._debug("concluida")
                    self._rand(3, 5)
                    cliques_seguidos = 0
                    # Voltar ao Falai
                    self.driver.get(self.URL)
                    self._rand(3, 4)
                    continue

                if resultado == "OK":
                    cliques_seguidos = 0

                if not self._avancar():
                    log.info("Sem botoes de acao")
                    if nesta_pesquisa:
                        # Tenta scroll e refresh
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        self._rand(2, 3)
                        if not self._avancar():
                            log.info("Ainda sem acao, verificando se acabou...")
                            if any(p in self.driver.page_source.lower() for p in ["concluída", "finalizada", "encerrada"]):
                                self.stats["respondidas"] += 1
                                em_pesquisa = False
                                log.info(f"Detectado fim! Total: {self.stats['respondidas']}")
                                self.driver.get(self.URL)
                                self._rand(3, 4)
                                continue
                            self._rand(3, 5)
                            self.driver.refresh()
                            self._rand(3, 5)
                    else:
                        self._rand(5, 10)
                elif resultado == "NO_INTERACTION":
                    cliques_seguidos += 1
                    log.info(f"Proximo clicado sem responder ({cliques_seguidos}x)")
                    if cliques_seguidos >= 5:
                        log.warning("5x sem responder — forçando saida da pesquisa")
                        self._debug("stuck")
                        self.stats["respondidas"] += 1
                        em_pesquisa = False
                        cliques_seguidos = 0
                        self.driver.get(self.URL)
                        self._rand(3, 4)

            except KeyboardInterrupt:
                log.info("Parando pelo usuario...")
                break
            except Exception as e:
                self.stats["erros"] += 1
                log.error(f"ERRO: {type(e).__name__}: {e}")
                self._debug("erro_loop")
                self._rand(4, 8)
                try:
                    self.driver.refresh()
                except:
                    log.error("Driver perdeu conexao")
                    break

        # Fim
        tempo = datetime.now() - self.stats["inicio"]
        log.info("=" * 60)
        log.info("BOT FINALIZADO")
        log.info(f"Pesquisas respondidas: {self.stats['respondidas']}")
        log.info(f"Erros: {self.stats['erros']}")
        log.info(f"Tempo total: {tempo}")
        log.info("=" * 60)
        self.driver.quit()


if __name__ == "__main__":
    email = os.environ.get("FALAI_EMAIL", "lucasjoaquim478@gmail.com")
    senha = os.environ.get("FALAI_SENHA", "Lucas12@")

    headless = "--visible" not in sys.argv and "-v" not in sys.argv
    debug = "--debug" in sys.argv

    bot = FalaiBot(email, senha, headless=headless, debug_dir="debug" if debug else "_debug")
    bot.rodar()
