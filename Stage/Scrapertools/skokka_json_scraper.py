import asyncio
import json
import os
from playwright.async_api import async_playwright

# Tentativa de importação do stealth
try:
    import playwright_stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

# ==========================================
# CONFIGURAÇÃO INICIAL
# ==========================================
# Coloque aqui a URL base (sem o parâmetro de página)
BASE_SEARCH_URL = "https://br.skokka.com/acompanhantes/manaus-am/?q=boca"

async def extrair_dados_pagina(page, url):
    """Extrai os anúncios de uma única página."""
    print(f"[*] Extraindo: {url}")
    results = []
    
    try:
        # Navega para a URL
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(4) # Espera carregar modais e anúncios

        # --- BYPASS DE POP-UPS ---
        try:
            btn_18 = page.get_by_role("button", name="ACEITAR", exact=True)
            if await btn_18.is_visible(): await btn_18.click()
            
            btn_cookies = page.get_by_role("button", name="ACEITAR TODOS OS COOKIES")
            if await btn_cookies.is_visible(): await btn_cookies.click()
        except: pass

        # Scroll para ativar lazy-load
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)

        # Localiza os anúncios
        anuncios_locators = await page.locator(".listing-item").all()
        
        for ad in anuncios_locators:
            try:
                title_el = ad.locator(".listing-title")
                title = await title_el.inner_text() if await title_el.count() > 0 else "N/A"
                
                link_el = ad.locator(".listing-title a")
                link = await link_el.get_attribute("href") if await link_el.count() > 0 else "N/A"
                if link and link.startswith("/"): link = "https://br.skokka.com" + link

                desc_el = ad.locator(".item-description")
                description = await desc_el.inner_text() if await desc_el.count() > 0 else "N/A"

                tagcard_strongs = ad.locator(".tagcard strong")
                age = "N/I"
                location = "N/I"
                count = await tagcard_strongs.count()
                if count >= 1: age = await tagcard_strongs.nth(0).inner_text()
                if count >= 2: location = await tagcard_strongs.nth(1).inner_text()

                price_el = ad.locator(".badge-pill")
                price = (await price_el.inner_text()).replace("De", "").strip() if await price_el.count() > 0 else "Sob consulta"

                results.append({
                    "titulo": title.strip(),
                    "link": link,
                    "descricao": description.strip(),
                    "idade": age.strip(),
                    "localizacao": location.strip(),
                    "preco": price
                })
            except: continue

    except Exception as e:
        print(f"[!] Erro na página {url}: {e}")

    return results

async def main():
    async with async_playwright() as p:
        print("[*] Iniciando Playwright...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Stealth Bypass
        if STEALTH_AVAILABLE:
            try:
                if hasattr(playwright_stealth, 'stealth_async'): await playwright_stealth.stealth_async(page)
                else: playwright_stealth.stealth(page)
            except: pass
        
        all_ads = []
        seen_links = set() # Para detectar duplicados e parar a paginação
        pagina_atual = 1
        
        while True:
            # Constrói a URL de paginação corretamente
            # Se já tem '?', usa '&p=', se não tem, usa '?p='
            sep = "&" if "?" in BASE_SEARCH_URL else "?"
            url_paginada = f"{BASE_SEARCH_URL}{sep}p={pagina_atual}"
            
            print(f"\n--- Coletando Página {pagina_atual} ---")
            novos_anuncios = await extrair_dados_pagina(page, url_paginada)

            if not novos_anuncios:
                print("[!] Nenhum anúncio encontrado. Encerrando paginação.")
                break

            # Verificação de Critério de Parada (Duplicados)
            duplicados_nesta_pagina = 0
            for ad in novos_anuncios:
                if ad['link'] in seen_links:
                    duplicados_nesta_pagina += 1
                else:
                    seen_links.add(ad['link'])
                    all_ads.append(ad)

            # Se todos os anúncios da página já foram vistos, significa que o site voltou ao início
            if duplicados_nesta_pagina == len(novos_anuncios):
                print("[#] Todos os anúncios desta página são repetidos. Fim da lista atingido.")
                break
            
            print(f"[+] Coletados {len(novos_anuncios) - duplicados_nesta_pagina} novos anúncios.")
            
            # Segurança para não ficar em loop infinito (Opcional)
            if pagina_atual >= 100: 
                print("[!] Limite de segurança de 100 páginas atingido.")
                break

            pagina_atual += 1
        # Salva o JSON final
        output_file = 'resultado_skokka_completo.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_ads, f, indent=4, ensure_ascii=False)

        await browser.close()
        print(f"\n{'='*50}\nSUCESSO! Total de {len(all_ads)} anúncios coletados.\nArquivo: {output_file}\n{'='*50}")

if __name__ == "__main__":
    asyncio.run(main())