import os
import json
import base64
from dotenv import load_dotenv
from openai import OpenAI
import ferramentas  # Importa o arquivo de ferramentas

# --- CONFIGURAÇÃO ---
load_dotenv("keys.env")

LM_STUDIO_URL = os.getenv("LM_STUDIO_GLOBAL")
MODEL_NAME = os.getenv("MODEL_NAMEGLOBAL")

# Cliente compatível com OpenAI
# O LM Studio usa o endpoint /v1. Removemos o final da URL para a lib OpenAI funcionar
client = OpenAI(
    base_url=LM_STUDIO_URL.replace("/chat/completions", ""), 
    api_key="lm-studio"
)

# --- FUNÇÃO DE VISÃO (CORREÇÃO DO PROBLEMA) ---
def transcrever_imagem(image_path, prompt_usuario):
    """Lê uma imagem local, converte para Base64 e envia para o modelo de visão."""
    try:
        with open(image_path, "rb") as img_file:
            base64_image = base64.b64encode(img_file.read()).decode('utf-8')

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_usuario},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Erro na visão: {e}")
        return f"Erro ao processar imagem: {str(e)}"

# --- FUNÇÃO DO AGENTE (FUNCTION CALLING) ---
def perguntar_ao_agente(mensagem_usuario, contexto_notas="", bot_instance=None, chat_id=None):
    """Gerencia o loop de pensamento e uso de ferramentas da IA."""
    
    prompt_sistema = """Você é o PixelDust, um assistente Autônomo multimodal.
    Você tem acesso a ferramentas para PESQUISAR na web, GERAR IMAGENS e criar PIXEL ART.
    Contexto das Notas do Usuário abaixo:
    """ + contexto_notas

    mensagens = [
        {"role": "system", "content": prompt_sistema},
        {"role": "user", "content": mensagem_usuario}
    ]

    while True:
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=mensagens,
                tools=ferramentas.schemas,
                tool_choice="auto",
                temperature=0.7
            )

            msg_ia = response.choices[0].message
            mensagens.append(msg_ia)

            if msg_ia.tool_calls:
                for tool_call in msg_ia.tool_calls:
                    func_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    call_id = tool_call.id
                    
                    if func_name in ferramentas.mapa_funcoes:
                        funcao_py = ferramentas.mapa_funcoes[func_name]
                        # Executa a ferramenta
                        resultado_str = funcao_py(**args, bot=bot_instance, chat_id=chat_id)
                        
                        mensagens.append({
                            "role": "tool",
                            "tool_call_id": call_id,
                            "content": str(resultado_str)
                        })
                # Continua o loop para a IA responder após usar a ferramenta
            else:
                return msg_ia.content

        except Exception as e:
            return f"Erro no processamento do Agente: {str(e)}"

# Função de compatibilidade (Legacy)
def perguntar_ao_gemma(mensagem, contexto=""):
    return perguntar_ao_agente(mensagem, contexto)