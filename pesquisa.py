import feedparser
import requests
import urllib.parse
import urllib3
import time
import os
import importlib.util
from bs4 import BeautifulSoup

# Configurações de Segurança
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Referer': 'https://www.google.com/'
}

SCRAPER_TOOLS_PATH = "Stage/Scrapertools"

def normalizar_url(texto):
    """Garante que a URL tenha o protocolo correto sem alterar o conteúdo."""
    texto = texto.strip()
    # Se começar com br. ou www. ou skokka., adiciona o protocolo
    if not texto.startswith(("http://", "https://")):
        texto = "https://" + texto
    return texto

def is_url(texto):
    """Verifica se o texto é uma URL válida."""
    try:
        resultado = urllib.parse.urlparse(normalizar_url(texto))
        return all([resultado.scheme, resultado.netloc])
    except:
        return False

def obter_dominio(url):
    """Extrai o nome do domínio para identificar o módulo de bypass."""
    parsed = urllib.parse.urlparse(url)
    dominio = parsed.netloc.replace('www.', '').split('.')
    if len(dominio) >= 2:
        return dominio[1].lower() if dominio[0] == 'br' else dominio[0].lower()
    return dominio[0].lower()

def carregar_modulo_especifico(dominio):
    """Carrega o script de bypass específico da pasta Scrapertools."""
    nome_arquivo = f"{dominio}.py"
    caminho_arquivo = os.path.join(SCRAPER_TOOLS_PATH, nome_arquivo)
    
    if os.path.exists(caminho_arquivo):
        try:
            spec = importlib.util.spec_from_file_location(dominio, caminho_arquivo)
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
            return modulo
        except Exception as e:
            print(f"[ERRO] Módulo {dominio}: {e}")
    return None

def buscar_noticias(termo):
    """Busca notícias via Google News RSS."""
    termo_encoded = urllib.parse.quote(termo)
    url = f"https://news.google.com/rss/search?q={termo_encoded}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    feed = feedparser.parse(url)
    if not feed.entries:
        return "Nenhuma notícia encontrada."
    resposta = f"📰 **Notícias sobre {termo}:**\n\n"
    for i, entry in enumerate(feed.entries[:5], 1):
        resposta += f"{i}. [{entry.title}]({entry.link})\n\n"
    return resposta

def acessar_site_direto(url_crua):
    """Executa a requisição e delega a extração para o módulo correto."""
    url = normalizar_url(url_crua)
    dominio = obter_dominio(url)
    modulo_custom = carregar_modulo_especifico(dominio)

    # Cookies de bypass para sites adultos/consents
    session_cookies = {
        'age_check': '1', 'is_adult': '1', 'view_adult': '1', 'cookie_consent': 'accepted'
    }

    try:
        print(f"[INFO] Acessando URL: {url}") # Log para debug
        time.sleep(1.0)
        
        response = requests.get(
            url, 
            headers=HEADERS, 
            cookies=session_cookies, 
            timeout=20, 
            verify=False
        )
        
        if response.status_code != 200:
            return False, f"O site retornou erro {response.status_code}. Verifique se a URL está correta."

        if modulo_custom and hasattr(modulo_custom, 'extrair_conteudo'):
            return modulo_custom.extrair_conteudo(response.text)

        # Fallback genérico
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(["script", "style", "nav", "footer"]): tag.decompose()
        return True, soup.get_text(separator=' ', strip=True)[:5000]

    except Exception as e:
        return False, f"Erro de conexão: {str(e)}"

def executar_pesquisa(texto):
    """Ponto de entrada do comando."""
    if is_url(texto):
        sucesso, resultado = acessar_site_direto(texto)
        return "SITE", sucesso, resultado
    else:
        resultado = buscar_noticias(texto)
        return "NOTICIAS", True, resultado