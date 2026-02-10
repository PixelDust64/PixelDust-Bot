import feedparser
import requests
import urllib.parse
import urllib3  # Importado para desativar avisos de SSL
from bs4 import BeautifulSoup

# Desativa os avisos de "Insecure Request" no terminal
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# SEUS HEADERS REAIS (Firefox no Ubuntu)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

def is_url(texto):
    """Verifica se o texto enviado é um link."""
    return texto.startswith(("http://", "https://", "www."))

def buscar_noticias(termo):
    """Busca notícias via RSS (Google News)."""
    termo_encoded = urllib.parse.quote(termo)
    url = f"https://news.google.com/rss/search?q={termo_encoded}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    
    feed = feedparser.parse(url)
    if not feed.entries:
        return "Nenhuma notícia encontrada."

    resposta = f"📰 **Notícias sobre {termo}:**\n\n"
    for i, entry in enumerate(feed.entries[:5], 1):
        resposta += f"{i}. [{entry.title}]({entry.link})\n\n"
    return resposta

def acessar_site_direto(url):
    """Tenta acessar um site específico ignorando erros de SSL."""
    if url.startswith("www."):
        url = "https://" + url
        
    try:
        # verify=False permite acessar sites com certificado vencido ou inválido
        response = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        
        if response.status_code != 200:
            return False, f"Bloqueio ou Erro HTTP: {response.status_code}"

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Limpeza do HTML (Remove o que não é conteúdo textual útil)
        for tags in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tags.decompose()

        texto_limpo = soup.get_text(separator=' ', strip=True)
        
        # Detecção de Bloqueio por conteúdo
        bloqueios = ["captcha", "cloudflare", "access denied", "just a moment", "security check"]
        if any(b in texto_limpo.lower() for b in bloqueios):
            return False, "Bloqueio de segurança (Cloudflare/Captcha) detectado."

        return True, texto_limpo[:5000]

    except Exception as e:
        return False, f"Erro na conexão: {str(e)}"

def executar_pesquisa(texto):
    """Decide se busca notícias ou acessa site direto."""
    if is_url(texto):
        sucesso, resultado = acessar_site_direto(texto)
        return "SITE", sucesso, resultado
    else:
        resultado = buscar_noticias(texto)
        return "NOTICIAS", True, resultado