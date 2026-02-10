import websocket # pip install websocket-client
import uuid
import json
import urllib.request
import urllib.parse
import requests
import time
import os

# CONFIGURAÇÃO DO COMFYUI
SERVER_ADDRESS = "127.0.0.1:8188" # Ajuste se for diferente
CLIENT_ID = str(uuid.uuid4())

def queue_prompt(prompt_workflow):
    p = {"prompt": prompt_workflow, "client_id": CLIENT_ID}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"http://{SERVER_ADDRESS}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"http://{SERVER_ADDRESS}/view?{url_values}") as response:
        return response.read()

def upload_image(image_path):
    """Envia a imagem local (do Telegram) para o ComfyUI"""
    with open(image_path, 'rb') as f:
        files = {'image': f}
        response = requests.post(f"http://{SERVER_ADDRESS}/upload/image", files=files)
    
    # Retorna o nome que o ComfyUI deu para o arquivo (ex: ComfyUI_0001.png)
    return response.json().get("name")

def processar_edicao_flux(caminho_imagem_original, prompt_edicao):
    """
    Carrega o workflow, injeta a imagem e o texto, e aguarda o resultado.
    """
    
    # 1. Carrega o workflow que você salvou no Passo 1
    # Certifique-se que o arquivo flux_edit_workflow.json está na pasta
    try:
        with open("flux_edit_workflow.json", "r", encoding="utf-8") as f:
            workflow = json.load(f)
    except FileNotFoundError:
        return None, "Erro: Arquivo flux_edit_workflow.json não encontrado."

    # 2. Upload da imagem original para o Comfy
    comfy_filename = upload_image(caminho_imagem_original)
    
    # --- AQUI É A PARTE CRÍTICA: EDITE OS IDs ---
    # Abra seu JSON e veja qual numero é o "Load Image" e qual é o "Image Edit" (texto)
    
    # Exemplo: Se o nó de carregar imagem for o "12"
    # workflow["12"]["inputs"]["image"] = comfy_filename
    
    # Exemplo: Se o nó onde vai o texto for o "35" (Flux Guidance ou CLIP Text Encode)
    # workflow["35"]["inputs"]["text"] = prompt_edicao
    
    # VOCÊ PRECISA AJUSTAR ESSES IDs ABAIXO BASEADO NO SEU ARQUIVO JSON:
    # Vou tentar adivinhar baseado na sua print, mas pode variar.
    
    # Procura dinâmica (tenta achar os nós automaticamente para facilitar)
    node_imagem_id = None
    node_texto_id = None
    
    for node_id, node_data in workflow.items():
        class_type = node_data.get("class_type", "")
        
        # Acha onde carregar imagem
        if class_type == "LoadImage":
            node_imagem_id = node_id
            
        # Acha onde pôr o texto (No seu print parece ser um nó customizado "Image Edit")
        # Se for um CLIPTextEncode padrão, mude para "CLIPTextEncode"
        if "Klein" in class_type or "Edit" in class_type or class_type == "CLIPTextEncode":
            # Verifica se tem input de texto
            if "text" in node_data.get("inputs", {}) or "image" in node_data.get("inputs", {}): 
                 # Cuidado: o nó da sua print tem um input 'image' que é texto no widget
                 # Verifique no JSON qual a chave do texto. Geralmente é "text" ou "string".
                 # Vou assumir que no nó Klein o campo de texto chama "image" ou "text"
                 pass 
                 # Nota: Vou deixar manual abaixo para você configurar
    
    # --- CONFIGURAÇÃO MANUAL (EDITE AQUI) ---
    # Olhe seu JSON. Onde está "car_interior_white.jpeg"? É esse ID.
    ID_LOAD_IMAGE = "10" 
    
    # Olhe seu JSON. Onde está o texto "Change the camera angle..."? É esse ID.
    ID_TEXT_PROMPT = "25" 
    
    # Injeção dos dados
    try:
        workflow[ID_LOAD_IMAGE]["inputs"]["image"] = comfy_filename
        
        # Ajuste a chave "image" abaixo se no seu JSON o campo de texto tiver outro nome (ex: "text", "prompt")
        # No seu print o widget chama "image", o que é confuso, mas comum em custom nodes.
        workflow[ID_TEXT_PROMPT]["inputs"]["image"] = prompt_edicao 
        
        # Seed aleatória para variar
        if "noise_seed" in workflow[ID_TEXT_PROMPT]["inputs"]:
            import random
            workflow[ID_TEXT_PROMPT]["inputs"]["noise_seed"] = random.randint(1, 10000000000)

    except KeyError as e:
        return None, f"Erro de ID no JSON do Workflow. Verifique o ID: {e}"

    # 3. Conecta no WebSocket para esperar o resultado
    ws = websocket.WebSocket()
    ws.connect(f"ws://{SERVER_ADDRESS}/ws?clientId={CLIENT_ID}")
    
    # Manda processar
    queue_prompt(workflow)
    
    print("⏳ ComfyUI processando... (Flux é pesado, aguarde)")
    
    # Loop de espera
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id']:
                    # Acabou!
                    break
        else:
            continue

    # 4. Busca o histórico para pegar o nome da imagem gerada
    history = requests.get(f"http://{SERVER_ADDRESS}/history").json()
    # Pega a última imagem gerada (simplificação)
    # Em produção ideal, usaríamos o prompt_id para filtrar
    
    # Pega o último job
    last_job = list(history.values())[-1]
    outputs = last_job.get("outputs", {})
    
    image_data = None
    for node_id in outputs:
        node_output = outputs[node_id]
        if "images" in node_output:
            for image in node_output["images"]:
                image_data = get_image(image['filename'], image['subfolder'], image['type'])
                break
        if image_data: break
        
    return image_data, None