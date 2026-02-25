import asyncio
import json
import os
import random
import re
from playwright.async_api import async_playwright

# Tentativa de importação do stealth
try:
    import playwright_stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

# ==========================================
# CONFIGURAÇÕES
# ==========================================
INPUT_FILE = 'resultado_skokka_completo.json'
OUTPUT_FILE = 'resultado_skokka_detalhado.json'

def limpar_texto(texto):
    """Remove terminadores de linha incomuns e espaços extras."""
    if not texto:
        return ""
    # Substitui terminadores Unicode problemáticos por quebras comuns
    texto = texto.replace('\u2028', '\n').replace('\u2029', '\n')
    return texto.strip()

async def extrair_detalhes_perfil(page, ad_data):
    """Visita o link do anúncio e extrai informações detalhadas, incluindo a data e ID corrigidos."""
    url = ad_data['link']
    print(f"[*] Analisando perfil: {url}")
    
    try:
        # Navega para o perfil
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Delay aleatório para evitar detecção
        await asyncio.sleep(random.uniform(2, 4))

        # --- BYPASS DE POP-UPS ---
        try:
            btn_18 = page.get_by_role("button", name="ACEITAR", exact=True)
            if await btn_18.is_visible(): await btn_18.click()
        except: pass

        # --- EXTRAÇÃO DA DATA E ID (CORRIGIDO) ---
        # Conforme o print, a classe correta é .date-id
        container_data = page.locator(".date-id")
        
        if await container_data.is_visible():
            texto_full = await container_data.inner_text()
            # Exemplo de texto: "23 FEVEREIRO - Id anúncio: br192ch31"
            
            if " - " in texto_full:
                partes = texto_full.split(" - ")
                ad_data['data_anuncio'] = limpar_texto(partes[0])
                
                # Extrai o ID removendo o prefixo "Id anúncio:"
                if len(partes) > 1 and "Id anúncio:" in partes[1]:
                    id_limpo = partes[1].replace("Id anúncio:", "").strip()
                    ad_data['id_anuncio'] = limpar_texto(id_limpo)
            else:
                # Caso o formato seja diferente, tentamos regex como fallback
                match_id = re.search(r'Id anúncio:\s*(\w+)', texto_full)
                ad_data['id_anuncio'] = match_id.group(1) if match_id else "N/A"
                ad_data['data_anuncio'] = limpar_texto(texto_full.split('Id')[0])
        else:
            ad_data['data_anuncio'] = "N/A"
            ad_data['id_anuncio'] = "N/A"

        # --- EXTRAÇÃO DOS DEMAIS DADOS ---

        # 1. Sobre Mim
        sobre_mim_el = page.locator(".col.service-detail p")
        if await sobre_mim_el.count() > 0:
            ad_data['sobre_mim'] = limpar_texto(await sobre_mim_el.nth(0).inner_text())
        else:
            ad_data['sobre_mim'] = "N/A"

        # 2. Características (Tags)
        tags_el = page.locator(".tags-sections-detail")
        ad_data['caracteristicas'] = limpar_texto(await tags_el.inner_text()) if await tags_el.count() > 0 else "N/A"

        # 3. Telefone (Título da página)
        titulo_pagina = await page.title()
        ad_data['telefone'] = limpar_texto(titulo_pagina.split('-')[0]) if '-' in titulo_pagina else "N/A"

        # 4. Caminho/Localização (Breadcrumbs)
        breadcrumbs = page.locator("#breadcrumbs-navigation")
        ad_data['caminho_localizacao'] = limpar_texto(await breadcrumbs.inner_text()) if await breadcrumbs.count() > 0 else "N/A"

        # 5. Detalhes de Serviço (Preços, Pagamentos)
        detalhes_adicionais = page.locator(".row.sticky-mobile")
        ad_data['detalhes_servico'] = limpar_texto(await detalhes_adicionais.inner_text()) if await detalhes_adicionais.count() > 0 else "N/A"

        print(f"[OK] ID: {ad_data.get('id_anuncio')} | Data: {ad_data.get('data_anuncio')}")
        return True

    except Exception as e:
        print(f"[!] Erro ao abrir perfil {url}: {e}")
        return False

async def main():
    if not os.path.exists(INPUT_FILE):
        print(f"[!] Erro: Arquivo {INPUT_FILE} não encontrado!")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        database = json.load(f)

    print(f"[*] Iniciando enriquecimento de {len(database)} perfis...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        if STEALTH_AVAILABLE:
            try:
                if hasattr(playwright_stealth, 'stealth_async'): await playwright_stealth.stealth_async(page)
                else: playwright_stealth.stealth(page)
            except: pass

        for i, ad in enumerate(database):
            # Sanitiza campos básicos já existentes
            ad['titulo'] = limpar_texto(ad.get('titulo', ''))
            
            # Tenta extrair os novos dados
            await extrair_detalhes_perfil(page, ad)
            
            # Salva o progresso a cada 5 perfis
            if i % 5 == 0:
                with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(database, f, indent=4, ensure_ascii=False)
                print(f"--- Progresso salvo: {i}/{len(database)} ---")

        # Salva o arquivo final consolidado
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(database, f, indent=4, ensure_ascii=False)

        await browser.close()
        print(f"\n{'='*50}\nFINALIZADO! Arquivo: {OUTPUT_FILE}\n{'='*50}")

if __name__ == "__main__":
    asyncio.run(main())