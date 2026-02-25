import requests
import json
import os
from dotenv import load_dotenv


load_dotenv("keys.env")

# Carrega a URL do LM Studio (A URL deve estar configurada no seu bot.py ou .env)
# Assumindo que a URL é a mesma do seu chat.py
LM_STUDIO_URL = os.getenv("LM_STUDIO_GLOBAL")
MODEL_NAME = os.getenv("MODEL_NAMEGLOBAL")

HEADERS = {"Content-Type": "application/json"}

# O System Prompt adaptado do App.tsx, mas ajustado para um LLM mais simples como o Gemma-3
SYSTEM_PROMPT_PIXELART = """
Você é um Gerador de Arte Pixelizada de classe mundial. Sua única tarefa é gerar o código SVG 64x64 de alta qualidade para um ativo de jogo.

REGRAS CRÍTICAS DE SAÍDA:
1. ESTRUTURA: A saída DEVE ser SOMENTE o código SVG.
2. ELEMENTOS: Use APENAS a tag <rect> para criar os pixels.
3. VIEWBOX: A tag <svg> deve ter viewBox="0 0 64 64".
4. ESTILO: Use shape-rendering="crispEdges" e cores vibrantes com alto contraste.
5. FORMATO: Retorne SOMENTE o código SVG, sem nenhuma explicação ou formatação de código (como ```svg).
6. CONTEÚDO: O ativo deve estar centrado no espaço 64x64.

EXEMPLO DE INÍCIO (Seja fiel a este formato):
<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">
"""


def gerar_svg_pixel_art(prompt_usuario):
    """Gera o código SVG 64x64 usando IA local."""
    
    full_prompt = f"Crie um SVG de arte pixelizada 64x64 de: '{prompt_usuario}'"

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_PIXELART},
            {"role": "user", "content": full_prompt}
        ],
        "temperature": 0.5, # Temperatura moderada para permitir criatividade, mas manter a precisão do código
        "max_tokens": 8192 # Aumentar max_tokens para códigos SVG longos
    }

    try:
        response = requests.post(LM_STUDIO_URL, json=payload, headers=HEADERS, timeout=190)
        
        if response.status_code != 200:
            return None, f"Erro da API LM Studio: Código {response.status_code}. Verifique a URL e o servidor."

        json_response = response.json()
        
        # --- LINHA CORRIGIDA ---
        # Acessa 'choices' (LISTA), pega o primeiro elemento [0], e acessa 'message' e 'content'
        choices = json_response.get('choices', [])
        if not choices:
            return None, "A API não retornou escolhas de conteúdo. O prompt pode ter sido bloqueado."
        
        raw_text = choices[0].get('message', {}).get('content', '')
        # --- FIM DA LINHA CORRIGIDA ---
        
        # Filtro de segurança para extrair SOMENTE o código SVG
        svg_match = raw_text.strip().lstrip('```xml').lstrip('```svg').lstrip('```').rstrip('```')
        
        # Encontra a primeira tag <svg> e a última </svg>
        start = svg_match.find('<svg')
        end = svg_match.rfind('</svg>')
        
        if start != -1 and end != -1:
            return svg_match[start : end + len('</svg>')], None
        else:
            return None, "A IA não conseguiu gerar o código SVG válido. Tente um prompt mais simples."

    except Exception as e:
        return None, f"Erro de conexão: {e}. Verifique o servidor LM Studio."