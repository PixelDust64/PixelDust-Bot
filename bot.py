import telebot
import base64 
import os
import time
import threading 
import imagem_ia   
import editarimagem_ia
import pesquisa
from dotenv import load_dotenv
import anotador
import chat
import pdf_helper
import pixelart_svg
import io
# import cairosvg
from telebot import util



# --- CARREGAR CONFIGURAÇÕES ---
load_dotenv("keys.env")
TOKEN = os.getenv("TOKEN").replace('"', '').strip()
MEU_ID = int(os.getenv("MEU_ID").replace('"', '').strip())

# O número de threads pode ser ajustado, 10 é um bom começo
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=10)
user_mode = {}  # Armazena o modo de cada usuário: {user_id: 'anotar' ou 'chat'}

# --- MIDDLEWARE DE SEGURANÇA ---
def tem_acesso(message):
    uid = message.chat.id
    if uid == MEU_ID: return True
    # Assumindo que verificar_acesso no anotador retorna algo não-None se permitido
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
    # Limita o tamanho da resposta antes de enviar
    resposta = "📅 **Suas notas:**\n\n" + "\n".join([f"• {n[0]}: {n[1]}" for n in notas])
    bot.send_message(uid, resposta[:4000], parse_mode="Markdown")


# --- COMANDOS DE PESQUISA/NOTÍCIAS ---

@bot.message_handler(commands=['noticias', 'pesquisar'])
def cmd_pesquisar(message):
    if not tem_acesso(message): return
    
    entrada = message.text.split(maxsplit=1)
    if len(entrada) < 2:
        bot.reply_to(message, "📌 Envie um termo ou um link.\nEx: `/noticias uea` ou `/noticias https://google.com`.", parse_mode="Markdown")
        return
        
    query = entrada[1].strip()
    bot.send_chat_action(message.chat.id, 'typing') 
    
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
            
            prompt = f"Abaixo está o conteúdo extraído do site {query}. Resuma os pontos principais de forma clara:\n\n{resultado}"
            resposta_ia = chat.perguntar_ao_gemma(prompt) # Chama a função chat com tratamento de erro
            
            texto_final = f"✅ **Análise do Site:**\n\n{resposta_ia}"
            
            # DIVIDIR O TEXTO PARA NÃO DAR ERRO NO TELEGRAM
            pedacos = util.split_string(texto_final, 3000)
            for pedaco in pedacos:
                try:
                    bot.reply_to(message, pedaco, parse_mode="Markdown")
                except Exception:
                    bot.reply_to(message, pedaco) # Fallback sem markdown se der erro
        else:
            erro_msg = f"❌ **Erro ao acessar o site direto:**\n\n{resultado}"
            try:
                bot.reply_to(message, erro_msg, parse_mode="Markdown")
            except Exception:
                bot.reply_to(message, erro_msg)


@bot.message_handler(commands=['gerarimagem'])
def cmd_gerar_imagem(message):
    uid = message.chat.id
    if not tem_acesso(message): return
    
    comando_completo = message.text.replace("/gerarimagem", "").strip()
    partes = [p.strip() for p in comando_completo.split('|', 2)]
    
    if len(partes) < 3:
        bot.reply_to(message, "❌ Use: `/gerarimagem modelo | positivo | negativo`", parse_mode="Markdown")
        return
    
    modelo, prompt_pos, prompt_neg = partes[0], partes[1], partes[2]
    bot.reply_to(message, f"🎨 Processando no modelo '{modelo}'...\n_Aguarde, isso pode levar mais tempo na primeira execução._", parse_mode="Markdown")

    resultado_ia = [None, None]
    
    def tarefa_geracao():
        img, info = imagem_ia.gerar_imagem(modelo, prompt_pos, prompt_neg)
        resultado_ia[0] = img
        resultado_ia[1] = info

    thread_ia = threading.Thread(target=tarefa_geracao)
    thread_ia.start()

    while thread_ia.is_alive():
        bot.send_chat_action(uid, 'upload_photo')
        thread_ia.join(timeout=4)

    img_base64, info = resultado_ia[0], resultado_ia[1]
    
    if img_base64:
        try:
            bot.send_photo(uid, base64.b64decode(img_base64), caption=info)
        except Exception as e:
            bot.send_message(uid, f"❌ Erro ao processar arquivo final: {e}")
    else:
        bot.send_message(uid, f"❌ **Falha na Geração:**\n_{info}_", parse_mode="Markdown")


@bot.message_handler(content_types=['photo'])
def handle_photo_edit(message):
    uid = message.chat.id
    if not tem_acesso(message): return

    legenda = message.caption or ""
    
    if legenda.startswith('/editar'):
        try:
            if '|' in legenda:
                prompt_edicao = legenda.split('|', 1)[1].strip()
            else:
                prompt_edicao = legenda.replace('/editar', '').strip()

            if not prompt_edicao:
                bot.reply_to(message, "📌 Por favor, diga o que deseja editar.\nEx: `/editar | deixe careca`")
                return

            bot.reply_to(message, "🛠️ Iniciando edição com **Flux 2 Klein**... Isso pode demorar cerca de 1 minuto.")
            bot.send_chat_action(uid, 'upload_photo')

            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            temp_path = f"edit_input_{uid}.jpg"
            
            with open(temp_path, 'wb') as f:
                f.write(downloaded_file)

            resultado = [None, None]
            def thread_work():
                resultado[0], resultado[1] = editarimagem_ia.editar_imagem_ia(temp_path, prompt_edicao)

            t = threading.Thread(target=thread_work)
            t.start()

            while t.is_alive():
                bot.send_chat_action(uid, 'upload_photo')
                t.join(timeout=4)

            img_base64, info = resultado[0], resultado[1]

            if img_base64:
                bot.send_photo(uid, base64.b64decode(img_base64), caption=info)
            else:
                bot.send_message(uid, f"❌ Falha na edição: {info}")

            if os.path.exists(temp_path): os.remove(temp_path)

        except Exception as e:
            bot.reply_to(message, f"Erro processando comando: {e}")


#@bot.message_handler(commands=['pixelart'])
#def cmd_pixel_art(message):
#    uid = message.chat.id
#    if not tem_acesso(message): return
#    
#    prompt = message.text.replace("/pixelart", "").strip()
#    
#    if not prompt:
#        bot.reply_to(message, "🎨 Por favor, diga qual item 64x64 você quer criar.\nEx: `/pixelart Espada de diamante`", parse_mode="Markdown")
#        return
#
#    bot.reply_to(message, "🛠️ Forjando ativo 64x64... Isso pode levar alguns segundos.", parse_mode="Markdown")
#    bot.send_chat_action(uid, 'upload_photo') 
#
#    svg_content, erro = pixelart_svg.gerar_svg_pixel_art(prompt)
#    
#    if erro:
#        bot.reply_to(message, f"❌ **Falha na Forja:**\n_{erro}_", parse_mode="Markdown")
#        return
#
#    try:
#        png_bytes = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'),
#                                    output_width=512,
#                                    output_height=512)
#        
#        bot.send_sticker(uid, png_bytes)
#        bot.send_message(uid, f"✅ Ativo Forjado como Sticker! **Prompt:** _{prompt}_", parse_mode="Markdown")
#
#    except Exception as e:
#        bot.send_message(uid, f"Erro ao gerar Sticker. Falha na conversão SVG->PNG. Erro: _{e}_", parse_mode="Markdown")


@bot.message_handler(commands=['limpar'])
def cmd_limpar(message):
    uid = message.chat.id
    if not tem_acesso(message): return
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Sim, Apagar TUDO", callback_data='confirm_limpar'),
        telebot.types.InlineKeyboardButton("❌ Não, Cancelar", callback_data='cancel_limpar')
    )
    
    bot.reply_to(message, "⚠️ **Confirma a limpeza?**\nIsso apagará todas as suas anotações permanentemente. Esta ação não pode ser desfeita.", reply_markup=markup, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data in ['confirm_limpar', 'cancel_limpar'])
def callback_limpar_confirmacao(call):
    uid = call.message.chat.id
    
    if call.data == 'confirm_limpar':
        anotador.limpar_todas(uid)
        bot.edit_message_text("🗑️ **Todas as suas anotações foram permanentemente apagadas!**", 
                              uid, call.message.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text("❌ Limpeza cancelada. Suas anotações estão seguras.", 
                              uid, call.message.message_id, parse_mode="Markdown")
    
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
        notas = anotador.listar_notas(uid, limite=8)
        contexto = "\n".join([f"[{n[0]}] {n[1]}" for n in notas])
        
        resposta = chat.perguntar_ao_gemma(message.text, contexto)
        
        # DIVIDIR O TEXTO SE FOR MAIOR QUE 4000 CARACTERES (Limite do Telegram)
        pedacos = util.split_string(resposta, 3000)
        for pedaco in pedacos:
            bot.reply_to(message, pedaco)







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






if __name__ == "__main__":
    anotador.init_db()
    anotador.autorizar_usuario(MEU_ID, "Dono", "admin")
    print("🚀 PixelDust Servidor Multi-usuário Iniciado!")
    
    bot.infinity_polling()
