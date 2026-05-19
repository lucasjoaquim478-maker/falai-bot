# Falai Bot - Respondedor Automático de Pesquisas

Bot profissional para responder automaticamente pesquisas no **Falai.com.vc** usando Selenium.

## Funcionalidades

- Login automático com email/senha
- Detecta e responde: radio buttons, checkboxes, selects, ratings, textos
- Navegação entre páginas da pesquisa
- Detecta conclusão e volta ao dashboard
- Suporta headless mode (roda sem abrir janela)
- Modo interativo (Windows: `executar.bat`, PowerShell: `executar.ps1`)

## Requisitos

- Python 3.8+
- Google Chrome instalado
- Conta no Falai.com.vc

## Instalação

```bash
pip install -r requirements.txt
```

## Como Usar

### Windows - Simples
Duplo clique em `executar.bat` e digite email/senha na primeira vez.

### PowerShell
```powershell
.\executar.ps1
```

### Manual
```bash
python bot.py
```
Ou com variáveis de ambiente:
```bash
set FALAI_EMAIL=seu@email.com
set FALAI_SENHA=sua_senha
python bot.py
```

### Headless (sem janela)
```bash
python bot.py --headless
```

## Personalização

Edite `bot.py` para ajustar:
- Tempos de espera (`_rand()`)
- Respostas de texto padrão
- Seletor de elementos

## Observações

- O bot tenta agir como humano (pausas aleatórias)
- Sites podem detectar automação - use com moderação
- Não compartilhe seu `config.txt`
