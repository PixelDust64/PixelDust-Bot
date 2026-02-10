import json
import base64
import io
import cairosvg

# Importando seus módulos existentes
import pesquisa
import imagem_ia
import pixelart_svg

# --- 1. DEFINIÇÃO DOS SCHEMAS (O "Menu" para a IA) ---
# A IA lerá isso para saber quais ferramentas ela tem disponível.
schemas = [
    {
        "type": "function",
        "function": {
            "name": "pesquisar_web",
            "description": "Usa o Google News ou acessa sites para buscar informações atuais, notícias ou dados que você não sabe.",
            "parameters": {
                "type": "object",
                "properties": {
                    "termo": {"type": "string", "description": "O que pesquisar ou a URL para ler."}
                },
                "required": ["termo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "gerar_imagem",
            "description": "Gera uma imagem usando Stable Diffusion (Forge/A1111).",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt_positivo": {"type": "string", "description": "Descrição visual detalhada em INGLÊS."},
                    "prompt_negativo": {"type": "string", "description": "O que evitar na imagem (ex: ugly, blurry)."}
                },
                "required": ["prompt_positivo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "criar_pixelart_sticker",
            "description": "Gera um ativo/sticker em Pixel Art 64x64 de um objeto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "objeto": {"type": "string", "description": "O objeto a ser desenhado (ex: espada, poção)."}
                },
                "required": ["objeto"]
            }
        }
    }
]

# --- 2. FUNÇÕES EXECUTORAS (A Ação Real) ---

def executar_pesquisa(termo, **kwargs):
    print(f"🔍 Agente pesquisando: {termo}")
    # Usa sua função existente em pesquisa.py
    tipo, sucesso, resultado = pesquisa.executar_pesquisa(termo)
    return resultado

def executar_imagem(prompt_positivo, prompt_negativo="", bot=None, chat_id=None, **kwargs):
    print(f"🎨 Agente desenhando: {prompt_positivo}")
    
    # Feedback visual para o usuário
    if bot and chat_id:
        bot.send_chat_action(chat_id, 'upload_photo')
        bot.send_message(chat_id, f"🎨 _Gerando imagem..._\nPrompt: `{prompt_positivo}`", parse_mode="Markdown")

    # Usa seu módulo existente imagem_ia.py
    # Nota: Assumindo modelo fixo ou padrão do seu código
    img_base64, info = imagem_ia.gerar_imagem("2halfblood", prompt_positivo, prompt_negativo)

    if img_base64:
        # Se temos o bot, enviamos a imagem direto daqui!
        if bot and chat_id:
            img_bytes = base64.b64decode(img_base64)
            bot.send_photo(chat_id, img_bytes)
            return "SUCESSO: Imagem gerada e JÁ enviada para o usuário no Telegram."
        return "SUCESSO: Imagem gerada internamente."
    else:
        return f"ERRO na geração: {info}"

def executar_pixelart(objeto, bot=None, chat_id=None, **kwargs):
    print(f"👾 Agente pixelando: {objeto}")
    
    if bot and chat_id:
        bot.send_message(chat_id, f"👾 Forjando Pixel Art de: {objeto}...")

    # Usa seu módulo pixelart_svg.py
    svg_content, erro = pixelart_svg.gerar_svg_pixel_art(objeto)
    
    if erro: 
        return f"ERRO: {erro}"

    # Converte e envia
    if bot and chat_id:
        try:
            png_bytes = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'), output_width=512, output_height=512)
            bot.send_sticker(chat_id, png_bytes)
            return "SUCESSO: Sticker Pixel Art enviado."
        except Exception as e:
            return f"ERRO conversão SVG: {e}"
    
    return "SUCESSO: SVG gerado."

# --- 3. MAPEAMENTO ---
# Relaciona o nome que a IA chama com a função Python real
mapa_funcoes = {
    "pesquisar_web": executar_pesquisa,
    "gerar_imagem": executar_imagem,
    "criar_pixelart_sticker": executar_pixelart
}