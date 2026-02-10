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
    response = requests.post(LM_STUDIO_URL, json=payload, timeout=60)
    return response.json()['choices'][0]['message']['content']

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
    response = requests.post(LM_STUDIO_URL, json=payload, timeout=90)
    return response.json()['choices'][0]['message']['content']