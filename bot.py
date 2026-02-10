import telebot
import base64 
import imagem_ia 
import os
import time
import pesquisa
from dotenv import load_dotenv
import anotador
import chat
import pdf_helper
import pixelart_svg
import io
import cairosvg

# --- CARREGAR CONFIGURAÇÕES ---
load_dotenv("keys.env")
TOKEN = os.getenv("TOKEN").replace('"', '').strip()
MEU_ID = int(os.getenv("MEU_ID").replace('"', '').strip())

bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=10)
user_mode = {}  # Armazena o modo de cada usuário: {user_id: 'anotar' ou 'chat'}

# --- MIDDLEWARE DE SEGURANÇA ---
def tem_acesso(message):
    uid = message.chat.id
    if uid == MEU_ID: return True
    return anotador.verificar_acesso(uid) is not None

# --- COMANDOS DE ADMINISTRAÇÃO ---

@bot.message_handler(commands=['add'])
def cmd_add_user(message):
    if message.chat.id != MEU_ID: return
    
    try:
        # Formato: /add 12345678 NomeDoAmigo
        partes = message.text.split(" ", 2)
        novo_id = int(partes[1])
        nome = partes[2]
        anotador.autorizar_usuario(novo_id, nome)
        bot.reply_to(message, f"✅ Usuário {nome} ({novo_id}) autorizado com sucesso!")
        bot.send_message(novo_id, "🎉 Você foi autorizado a usar o PixelDustbot!\nUse /start para ver os comandos.")
    except Exception as e:
        bot.reply_to(message, "❌ Erro. Use: `/add ID NOME`", parse_mode="Markdown")

# --- COMANDOS DE USUÁRIO ---

@bot.message_handler(commands=['start'])
def cmd_start(message):
    uid = message.chat.id
    if not tem_acesso(message):
        bot.reply_to(message, f"🚫 Acesso negado. Passe seu ID ({uid}) para o administrador.")
        return

    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('/anotar', '/chat', '/listar', '/limpar')
    bot.reply_to(message, "Olá! Escolha o modo de operação ou envie uma nota/arquivo:", reply_markup=markup)

@bot.message_handler(commands=['anotar', 'chat'])
def cmd_switch(message):
    if not tem_acesso(message): return
    mode = message.text.replace('/', '').lower()
    user_mode[message.chat.id] = mode
    bot.reply_to(message, f"{'📝' if mode=='anotar' else '🤖'} Modo {mode.upper()} ativado.")

@bot.message_handler(commands=['listar'])
def cmd_listar(message):
    uid = message.chat.id
    if not tem_acesso(message): return
    notas = anotador.listar_notas(uid)
    if not notas:
        bot.send_message(uid, "Você ainda não tem notas salvas.")
        return
    resposta = "📅 **Suas notas:**\n\n" + "\n".join([f"• {n[0]}: {n[1]}" for n in notas])
    bot.send_message(uid, resposta[:4000], parse_mode="Markdown")

# --- TRATAMENTO DE MULTIMÍDIA ---

# No arquivo bot.py

# ... (outros handlers) ...

# --- TRATAMENTO DE MULTIMÍDIA ---

@bot.message_handler(content_types=['photo', 'document'])
def handle_files(message):
    uid = message.chat.id
    if not tem_acesso(message): return

    bot.send_chat_action(uid, 'typing')
    modo = user_mode.get(uid, 'anotar')
    resultado = ""
    
    # 1. Se for FOTO
    if message.content_type == 'photo':
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        path = f"temp_{uid}.jpg"
        with open(path, "wb") as f: f.write(downloaded)
        resultado = chat.transcrever_imagem(path, message.caption or "Transcreva esta imagem.")
        os.remove(path)

    # 2. Se for DOCUMENTO (e for um PDF)
    elif message.content_type == 'document' and message.document.file_name.lower().endswith('.pdf'):
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        path = f"temp_{uid}.pdf"
        with open(path, "wb") as f: f.write(downloaded)
        
        texto = pdf_helper.extrair_texto_pdf(path)
        
        # Lógica para PDF pesquisável vs. PDF scaneado
        if not texto or len(texto) < 10:
            img_path = pdf_helper.converter_pdf_em_imagem(path)
            resultado = chat.transcrever_imagem(img_path, "Transcreva este documento.")
            if os.path.exists(img_path): os.remove(img_path)
        else:
            resultado = chat.perguntar_ao_gemma(f"Resuma este PDF: {texto[:3000]}")
        os.remove(path)
    
    # Se enviou um documento que NÃO é PDF, responde
    else:
        bot.reply_to(message, "Envie uma foto ou um arquivo PDF. Outros formatos não são suportados.")
        return

    # Salva ou responde (com o resultado de foto ou PDF)
    if modo == 'anotar':
        anotador.salvar_nota(uid, f"[ARQUIVO]: {resultado}")
        bot.reply_to(message, "✅ Conteúdo processado e salvo!")
    else:
        bot.reply_to(message, resultado)

# --- TEXTO PRINCIPAL ---
# ... (o restante do seu código)

# --- TEXTO PRINCIPAL ---

@bot.message_handler(commands=['noticias', 'pesquisar'])
def cmd_pesquisar(message):
    # 1. Verifica se o usuário está na lista de autorizados
    if not tem_acesso(message): return
    
    # 2. Pega o que foi digitado após o comando
    entrada = message.text.split(maxsplit=1)
    if len(entrada) < 2:
        bot.reply_to(message, "📌 Envie um termo ou um link.\nEx: `/noticias uea` ou `/noticias https://google.com`.", parse_mode="Markdown")
        return
        
    query = entrada[1].strip()
    bot.send_chat_action(message.chat.id, 'typing') 
    
    # 3. Chama a função unificada do pesquisa.py
    tipo, sucesso, resultado = pesquisa.executar_pesquisa(query)
    
    if tipo == "NOTICIAS":
        try:
            bot.reply_to(message, resultado, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception:
            bot.reply_to(message, resultado, disable_web_page_preview=True)
        
    elif tipo == "SITE":
        if sucesso:
            bot.reply_to(message, "🌐 Site acessado com sucesso! A IA está lendo o conteúdo...")
            bot.send_chat_action(message.chat.id, 'typing')
            
            # Manda o conteúdo para a (IA) resumir
            prompt = f"Abaixo está o conteúdo extraído do site {query}. Resuma os pontos principais de forma clara:\n\n{resultado}"
            resposta_ia = chat.perguntar_ao_gemma(prompt)
            
            texto_final = f"✅ **Análise do Site:**\n\n{resposta_ia}"
            
            # --- SISTEMA DE SEGURANÇA PARA MARKDOWN ---
            try:
                # Tenta enviar formatado
                bot.reply_to(message, texto_final, parse_mode="Markdown")
            except Exception as e:
                # Se a IA quebrou o Markdown (erro 400), envia como texto simples
                print(f"Erro de formatação detectado, enviando sem Markdown: {e}")
                bot.reply_to(message, texto_final) 
        else:
            # Erro de acesso (ex: site fora do ar)
            erro_msg = f"❌ **Erro ao acessar o site direto:**\n\n{resultado}"
            try:
                bot.reply_to(message, erro_msg, parse_mode="Markdown")
            except Exception:
                bot.reply_to(message, erro_msg)

@bot.message_handler(commands=['gerarimagem'])
def cmd_gerar_imagem(message):
    uid = message.chat.id
    if not tem_acesso(message): return
    
    # 1. Extrai o comando completo
    comando_completo = message.text.replace("/gerarimagem", "").strip()
    
    # 2. Divide em Modelo | Positivo | Negativo
    partes = [p.strip() for p in comando_completo.split('|', 2)]
    
    if len(partes) < 3:
        bot.reply_to(message, 
            "❌ **Faltando parâmetros!**\nUse: `/gerarimagem modelo | prompt positivo | prompt negativo`\nEx: `/gerarimagem 2halfblood | um dragão azul voando | blurry, bad eyes`",
            parse_mode="Markdown")
        return
    
    modelo = partes[0]
    prompt_pos = partes[1]
    prompt_neg = partes[2]
    
    bot.reply_to(message, 
        f"🎨 Iniciando geração para o modelo '{modelo}'...\n_Isso pode levar até 30 segundos._",
        parse_mode="Markdown")
    bot.send_chat_action(uid, 'upload_photo') # Mostra "enviando foto..."

    # 3. Chama a função de geração
    img_base64, info = imagem_ia.gerar_imagem(modelo, prompt_pos, prompt_neg)
    
# 3. Chama a função de geração
    img_base64, info = imagem_ia.gerar_imagem(modelo, prompt_pos, prompt_neg)
    
    if img_base64:
        try:
            # 4. Converte e Envia a imagem
            img_bytes = base64.b64decode(img_base64)
            
            # Envia a imagem SEM a legenda
            bot.send_photo(uid, img_bytes)
            
            # Envia uma pequena mensagem de confirmação se a imagem for enviada com sucesso
            # Você pode remover esta linha se quiser apenas a imagem sem texto algum
            # bot.send_message(uid, "✅ Imagem Gerada!")
        
        except Exception as e:
            bot.send_message(uid, f"Erro ao enviar a imagem. O Base64 pode ter vindo incompleto. Erro: {e}")
            
    else:
        # 5. Em caso de erro na API, ele AINDA envia o erro completo (o que é bom)
        bot.send_message(uid, f"❌ **Falha na Geração:**\n_{info}_", parse_mode="Markdown")


# Adicione no topo

# ... (outros handlers) ...

@bot.message_handler(commands=['pixelart'])
def cmd_pixel_art(message):
    uid = message.chat.id
    if not tem_acesso(message): return
    
    prompt = message.text.replace("/pixelart", "").strip()
    
    if not prompt:
        bot.reply_to(message, "🎨 Por favor, diga qual item 64x64 você quer criar.\nEx: `/pixelart Espada de diamante`", parse_mode="Markdown")
        return

    bot.reply_to(message, "🛠️ Forjando ativo 64x64... Isso pode levar alguns segundos.", parse_mode="Markdown")
    bot.send_chat_action(uid, 'upload_photo') 

    # 1. Gera o SVG (svg_content é o código SVG que gerado)
    svg_content, erro = pixelart_svg.gerar_svg_pixel_art(prompt)
    
    if erro:
        bot.reply_to(message, f"❌ **Falha na Forja:**\n_{erro}_", parse_mode="Markdown")
        return

    # --- NOVO BLOCO DE CONVERSÃO E ENVIO COMO STICKER ---
    try:
        # 1. Converte o código SVG para bytes PNG no tamanho 512x512 (Padrão Sticker)
        png_bytes = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'),
                                    output_width=512,  # EXATAMENTE 512
                                    output_height=512) # EXATAMENTE 512
        
        # 2. Envia como STICKER
        bot.send_sticker(uid, png_bytes)
        
        # 3. Envia a legenda separadamente (Stickers não podem ter legenda)
        bot.send_message(uid, f"✅ Ativo Forjado como Sticker! **Prompt:** _{prompt}_", parse_mode="Markdown")

    except Exception as e:
        # Se a conversão falhar (muito comum sem a biblioteca correta), envia o código SVG como fallback
        bot.send_message(uid, f"Erro ao gerar Sticker. Falha na conversão SVG->PNG. Aqui está o código:\n\n```xml\n{svg_content[:2000]}...\n```\n\nErro: _{e}_", parse_mode="Markdown")



@bot.message_handler(commands=['limpar'])
def cmd_limpar(message):
    uid = message.chat.id
    if not tem_acesso(message): return
    
    # 1. Pergunta de Confirmação (Boas Práticas!)
    # Como apagar tudo é perigoso, é bom pedir confirmação com um botão
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Sim, Apagar TUDO", callback_data='confirm_limpar'),
        telebot.types.InlineKeyboardButton("❌ Não, Cancelar", callback_data='cancel_limpar')
    )
    
    bot.reply_to(message, "⚠️ **Confirma a limpeza?**\nIsso apagará todas as suas anotações permanentemente. Esta ação não pode ser desfeita.", reply_markup=markup, parse_mode="Markdown")


# 2. Novo Handler para os Botões de Confirmação
@bot.callback_query_handler(func=lambda call: call.data in ['confirm_limpar', 'cancel_limpar'])
def callback_limpar_confirmacao(call):
    uid = call.message.chat.id
    
    if call.data == 'confirm_limpar':
        # Chama a função de limpeza segura (que apaga apenas as notas do uid)
        anotador.limpar_todas(uid)
        
        # Edita a mensagem anterior com a confirmação
        bot.edit_message_text("🗑️ **Todas as suas anotações foram permanentemente apagadas!**", 
                              uid, call.message.message_id, parse_mode="Markdown")
    else:
        # Ação cancelada
        bot.edit_message_text("❌ Limpeza cancelada. Suas anotações estão seguras.", 
                              uid, call.message.message_id, parse_mode="Markdown")
    
    # É obrigatório responder ao callback do Telegram
    bot.answer_callback_query(call.id)





@bot.message_handler(func=lambda message: True)
def handle_text(message):
    uid = message.chat.id
    if not tem_acesso(message): return

    modo = user_mode.get(uid, 'anotar')
    
    if modo == 'anotar':
        anotador.salvar_nota(uid, message.text)
        bot.reply_to(message, "✅ Anotado!")
    else:
        bot.send_chat_action(uid, 'typing')
        # Contexto privado (só as notas deste usuário)
        notas = anotador.listar_notas(uid, limite=8)
        contexto = "\n".join([f"[{n[0]}] {n[1]}" for n in notas])
        resposta = chat.perguntar_ao_gemma(message.text, contexto)
        bot.reply_to(message, resposta)



if __name__ == "__main__":
    anotador.init_db()
    anotador.autorizar_usuario(MEU_ID, "Dono", "admin")
    print("🚀 PixelDust Servidor Multi-usuário Iniciado!")
    
    # Apenas assim:
    bot.infinity_polling()