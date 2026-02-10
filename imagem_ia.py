import requests
import base64
import io

# URL do seu servidor Stable Diffusion/AUTOMATIC1111/Fooocus
# *** VOCÊ DEVE MUDAR ESTA URL PARA ONDE SUA API DE IMAGEM ESTÁ RODANDO ***
API_URL = "http://localhost:7860/sdapi/v1/txt2img"

# Configurações baseadas no seu prompt
BASE_PAYLOAD = {
    "steps": 28,
    "sampler_name": "Euler a",
    "cfg_scale": 4,
    "seed": -1, # Usar seed aleatória (-1)
    "width": 1024,
    "height": 1152,
    "clip_skip": 2,
    "denoising_strength": 0.7,
    "override_settings": {
        "sd_model_checkpoint": "2halfblood"
    }
    # Outros parâmetros como Token Merging seriam incluídos aqui se a API suportasse
}

def gerar_imagem(modelo, prompt_positivo_usuario, prompt_negativo_usuario):
    # Combina os prompts de qualidade com o prompt do usuário
    prompt_completo = (
        "masterpiece, high quality, absurdres, newest, " + 
        prompt_positivo_usuario
    ).strip()
    
    # Adiciona o filtro de qualidade negativa ao prompt negativo do usuário
    negativo_completo = (
        ", ((signature, watermark, name logo, username, text)), worst quality, low quality, "
        "(fusing:1.1), (fusing_vore:1.1), (multi_limb:1.2), bad hands, bad anatomy, "
        "fused fingers, fused legs, amputee, missing_limbs, smearing, blurry, "
        "signature, patreon name, text, bad art, bad quality, " + 
        prompt_negativo_usuario
    ).strip()

    payload = BASE_PAYLOAD.copy()
    payload["prompt"] = prompt_completo
    payload["negative_prompt"] = negativo_completo
    
    # Se você for usar múltiplos modelos, pode mudar aqui:
    # payload["override_settings"]["sd_model_checkpoint"] = modelo 

    try:
        response = requests.post(API_URL, json=payload, timeout=300) # Timeout de 5 minutos
        
        if response.status_code != 200:
            return None, f"Erro da API de Imagem: Código {response.status_code}. Verifique a URL e se o servidor está rodando."

        r = response.json()
        
        # A API retorna a imagem em base64 dentro da lista 'images'
        img_base64 = r['images'][0]
        
        # O Stable Diffusion/A1111 também retorna os parâmetros na info
        info = r.get('info', 'Parâmetros de geração não disponíveis.')
        
        return img_base64, info

    except requests.exceptions.Timeout:
        return None, "A geração de imagem excedeu o tempo limite (5 minutos). Tente um prompt mais simples."
    except Exception as e:
        return None, f"Erro de conexão com a API: {e}. Verifique se a URL '{API_URL}' está correta e a porta está aberta."