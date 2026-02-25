import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv("keys.env")

LM_STUDIO_URL = os.getenv("LM_STUDIO_GLOBAL")
MODEL_NAME = os.getenv("MODEL_NAMEGLOBAL")

def perguntar_ao_gemma(mensagem, contexto_notas=""):
    prompt_sistema = "Você é um assistente pessoal inteligente."
    if contexto_notas:
        prompt_sistema += f"\nContexto das notas do usuário:\n{contexto_notas}"

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": mensagem}
        ],
        "temperature": 0.7
    }
    
    try:
        # Usa o endpoint OpenAI-compatible (que você configurou para terminar em /completions)
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=60)
        res_data = response.json()
        
        if 'choices' in res_data:
            return res_data['choices'][0]['message']['content']
        else:
            # Se não tem 'choices', é um erro do servidor local (ex: 'input' required)
            print(f"❌ Erro do LM Studio: {res_data}")
            return "Erro: O modelo não retornou uma resposta válida. Verifique o terminal do servidor."
            
    except Exception as e:
        print(f"⚠️ Erro de conexão com o servidor local: {e}")
        return "Erro de conexão com o servidor local."

def transcrever_imagem(image_path, prompt_usuario):
    with open(image_path, "rb") as img_file:
        base64_image = base64.b64encode(img_file.read()).decode('utf-8')

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_usuario},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        "temperature": 0.1 # Menor para ser mais fiel na transcrição
    }
    
    try:
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=90)
        res_data = response.json()
        
        if 'choices' in res_data:
            return res_data['choices'][0]['message']['content']
        else:
            print(f"❌ Erro do LM Studio (Vision): {res_data}")
            return "Erro ao processar imagem."
    except Exception as e:
        print(f"⚠️ Erro de conexão na transcrição: {e}")
        return "Erro de conexão com o servidor local ao processar imagem."