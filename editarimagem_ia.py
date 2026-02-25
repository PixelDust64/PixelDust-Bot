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

# --- CONFIGURAÇÕES ---
BASE_DIR = Path(__file__).parent
TEMPLATE_PATH = BASE_DIR / "imagetemplates" / "flux2_kleinedit.json"

def detectar_comfy():
    """Encontra a porta ativa do ComfyUI, tentando primeiro localhost e depois o IP estático."""

    # Obtém as configurações do arquivo .env com valores padrão
    ip_estatico = os.getenv('EXTERMAL_COMFY_STATIC_IP', '192.168.0.26')
    local_ip = os.getenv('LOCAL_COMFY_STATIC_IP', '127.0.0.1')
    try:
        port_start = int(os.getenv('COMFY_PORT_START', '8188'))
        port_end = int(os.getenv('COMFY_PORT_END', '8197')) + 1  # +1 porque range() não inclui o valor final
    except ValueError:
        print("Erro: Valores de porta inválidos no .env. Usando os padrões 8188-8197.")
        port_start = 8188
        port_end = 8198

    COMFY_RANGE = range(port_start, port_end)

    # --- Etapa 1: Tentar Localhost (Mais rápido) ---
    for porta in COMFY_RANGE:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            if s.connect_ex((local_ip, porta)) == 0:
                print(f"ComfyUI encontrado em LOCALHOST na porta {porta}")
                return f"http://{local_ip}:{porta}"

    # --- Etapa 2: Tentar IP Estático (Fallback se localhost falhar) ---
    for porta in COMFY_RANGE:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.1)
            if s.connect_ex((ip_estatico, porta)) == 0:
                print(f"ComfyUI encontrado no IP Estático {ip_estatico} na porta {porta}")
                return f"http://{ip_estatico}:{porta}"

    return None


def upload_imagem(url, image_path):
    """Envia a imagem para o servidor ComfyUI."""
    with open(image_path, "rb") as f:
        files = {"image": f}
        res = requests.post(f"{url}/upload/image", files=files)
        return res.json()["name"]


def editar_imagem_ia(image_path, prompt_usuario):
    url = detectar_comfy()
    if not url:
        return None, "Servidor ComfyUI não detectado para edição (Flux 2)."

    try:
        if not TEMPLATE_PATH.exists():
            return None, f"Template {TEMPLATE_PATH.name} não encontrado."

        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            workflow = json.load(f)

        # 1. Faz o upload da imagem original para o Comfy
        filename_no_comfy = upload_imagem(url, image_path)

        # 2. Mapeamento do Workflow Flux 2 Klein Edit:
        # Nó "76": LoadImage (onde entra a foto do user)
        # Nó "75:74": CLIPTextEncode (Prompt de edição)
        # Nó "75:73": RandomNoise (Seed)

        workflow["76"]["inputs"]["image"] = filename_no_comfy
        workflow["75:74"]["inputs"]["text"] = f" {prompt_usuario}, high quality, "
        workflow["75:73"]["inputs"]["noise_seed"] = int(time.time() * 1000) % 1125899906842624

        # 3. Envia o Prompt
        p = {"prompt": workflow}
        res_prompt = requests.post(f"{url}/prompt", json=p).json()
        prompt_id = res_prompt['prompt_id']

        # 4. Polling (Espera finalizar)
        max_tentativas = 100
        for _ in range(max_tentativas):
            history = requests.get(f"{url}/history/{prompt_id}").json()
            if prompt_id in history:
                # Nó "9" é o SaveImage no seu JSON
                file_info = history[prompt_id]['outputs']['9']['images'][0]
                filename = file_info['filename']

                img_data = requests.get(f"{url}/view?filename={filename}").content
                return base64.b64encode(img_data).decode('utf-8'), f"✨ Editado via Flux 2 Klein"

            time.sleep(3)

        return None, "Timeout ao editar imagem."

    except Exception as e:
        return None, f"Erro no processamento Flux 2: {str(e)}"