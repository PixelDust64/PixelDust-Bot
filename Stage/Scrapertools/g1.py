# Stage/Scrapertools/g1.py
from bs4 import BeautifulSoup

def extrair_conteudo(html_bruto):
    """
    Estratégia específica para o domínio G1.
    Foca nas classes 'content-text' e valida campos obrigatórios.
    """
    soup = BeautifulSoup(html_bruto, 'html.parser')
    
    # Busca especificamente o corpo da matéria no G1
    corpo_noticia = soup.find_all('div', class_='content-text__container')
    
    if not corpo_noticia:
        # Fallback caso o layout mude
        corpo_noticia = soup.select('article')

    texto_final = ""
    for trecho in corpo_noticia:
        texto_final += trecho.get_text(separator=' ', strip=True) + "\n"

    # Estratégia 6: Validação de Dados (Verifica se extraiu algo útil)
    if len(texto_final.strip()) < 100:
        return False, "Conteúdo extraído é muito curto ou inválido para o G1."

    return True, texto_final[:5000]