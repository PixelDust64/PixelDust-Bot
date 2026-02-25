import requests
import base64
import json
import os
import time
import socket
from pathlib import Path
from dotenv import load_dotenv

# --- Carrega as variáveis de ambiente do arquivo .env ---
load_dotenv()

# --- CONFIGURAÇÕES DE CAMINHOS ---
BASE_DIR = Path(__file__).parent
TEMPLATE_PATH = BASE_DIR / "imagetemplates" / "XLvpred.json"

def detectar_servico():
    """
    Varre as portas e IPs definidos estritamente no .env.
    Não há IPs ou portas fixas aqui.
    """
    
    # --- Leitura das Variáveis de Ambiente (Configuração Comfy) ---
    comfy_ips = [os.getenv('LOCAL_COMFY_STATIC_IP'), os.getenv('EXTERMAL_COMFY_STATIC_IP')]
    c_start = int(os.getenv('COMFY_PORT_START'))
    c_end = int(os.getenv('COMFY_PORT_END'))
    comfy_range = range(c_start, c_end + 1)

    # --- Leitura das Variáveis de Ambiente (Configuração Forge) ---
    forge_ips = [os.getenv('LOCAL_FORGE_STATIC_IP'), os.getenv('EXTERMAL_FORGE_STATIC_IP')]
    f_start = int(os.getenv('FORGE_PORT_START'))
    f_end = int(os.getenv('FORGE_PORT_END'))
    forge_range = range(f_start, f_end + 1)

    # 1. Tenta encontrar ComfyUI (Conforme a prioridade definida)
    for ip in comfy_ips:
        if not ip: continue  # Pula se a variável estiver vazia no .env
        for porta in comfy_range:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                if s.connect_ex((ip, porta)) == 0:
                    return "COMFY", f"http://{ip}:{porta}"

    # 2. Tenta encontrar Forge Neo
    for ip in forge_ips:
        if not ip: continue
        for porta in forge_range:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                if s.connect_ex((ip, porta)) == 0:
                    return "FORGE", f"http://{ip}:{porta}"
    
    return None, None

def gerar_imagem(modelo, prompt_usuario, negativo_usuario):
    """Função principal que utiliza a detecção dinâmica."""
    tipo, url_base = detectar_servico()
    
    if not tipo:
        return None, "Nenhum servidor detectado nas configurações do seu .env."

    prompt_positivo = f"masterpiece, high quality, absurdres, newest, {prompt_usuario}"
    
    negativo_completo = (
        ", ((signature, watermark, name logo, username, text)), worst quality, low quality, "
        "sketch, (fusing:1.1), (fusing_vore:1.1), (multi_limb:1.2), bad hands, bad anatomy, "
        "fused fingers, fused legs, amputee, missing_limbs, smearing, blurry, "
        "signature, patreon name, text, bad art, bad quality, " + negativo_usuario
    )

    if tipo == "FORGE":
        return _executar_forge(url_base, modelo, prompt_positivo, negativo_completo)
    else:
        return _executar_comfy(url_base, modelo, prompt_positivo, negativo_completo)

def _executar_forge(url, modelo, pos, neg):
    payload = {
        "prompt": pos,
        "negative_prompt": neg,
        "steps": 28,
        "sampler_name": "Euler a",
        "cfg_scale": 4,
        "width": 1024,
        "height": 1152,
        "override_settings": {"sd_model_checkpoint": modelo}
    }
    try:
        response = requests.post(f"{url}/sdapi/v1/txt2img", json=payload, timeout=300)
        if response.status_code == 200:
            return response.json()['images'][0], f"🎨 Canal: Forge Neo ({url})"
    except Exception as e:
        return None, f"Erro no Forge: {e}"
    return None, "Erro na resposta do Forge."

def _executar_comfy(url, modelo, pos, neg):
    try:
        if not TEMPLATE_PATH.exists():
            return None, f"Template não encontrado."
            
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            workflow = json.load(f)

        if "nodes" in workflow:
            workflow = {str(n['id']): n for n in workflow['nodes']}

        # Configuração dos nós baseada no seu workflow XLvpred
        if "1" in workflow:
            ckpt = modelo if modelo.endswith(".safetensors") else modelo + ".safetensors"
            workflow["1"]["inputs"]["ckpt_name"] = ckpt
        
        if "3" in workflow: workflow["3"]["inputs"]["text"] = pos
        if "4" in workflow: workflow["4"]["inputs"]["text"] = neg
        if "5" in workflow:
            workflow["5"]["inputs"]["seed"] = int(time.time() * 1000) % 1125899906842624

        p = {"prompt": workflow}
        res_prompt = requests.post(f"{url}/prompt", json=p).json()
        prompt_id = res_prompt['prompt_id']

        # Polling para pegar o resultado
        for _ in range(150):
            history = requests.get(f"{url}/history/{prompt_id}").json()
            if prompt_id in history:
                outputs = history[prompt_id]['outputs']
                node_id = "8" if "8" in outputs else list(outputs.keys())[0]
                file_info = outputs[node_id]['images'][0]
                filename = file_info['filename']
                
                img_data = requests.get(f"{url}/view?filename={filename}").content
                return base64.b64encode(img_data).decode('utf-8'), f"⚙️ Canal: ComfyUI ({url})"
            time.sleep(2)

        return None, "Timeout ComfyUI."
    except Exception as e:
        return None, f"Erro ComfyUI: {e}"