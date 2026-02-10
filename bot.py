import telebot
import os
import time
from dotenv import load_dotenv
import anotador
import chat
import pdf_helper

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
    resposta = "📅 **Suas notas:**\n\n" + "\n".join([f"• {n[0]} ({n[1]}): {n[2]}" for n in notas])
    bot.send_message(uid, resposta[:4000], parse_mode="Markdown")

@bot.message_handler(commands=['limpar'])
def cmd_limpar(message):
    uid = message.chat.id
    if not tem_acesso(message): return
    
    # Pergunta de Confirmação
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Sim, Apagar TUDO", callback_data='confirm_limpar'),
        telebot.types.InlineKeyboardButton("❌ Não, Cancelar", callback_data='cancel_limpar')
    )
    
    bot.reply_to(message, "⚠️ **Confirma a limpeza?**\nIsso apagará todas as suas anotações permanentemente.", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data in ['confirm_limpar', 'cancel_limpar'])
def callback_limpar_confirmacao(call):
    uid = call.message.chat.id
    
    if call.data == 'confirm_limpar':
        anotador.limpar_todas(uid)
        bot.edit_message_text("🗑️ **Todas as suas anotações foram apagadas!**", uid, call.message.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text("❌ Limpeza cancelada.", uid, call.message.message_id, parse_mode="Markdown")
    
    bot.answer_callback_query(call.id)

# --- TRATAMENTO DE ARQUIVOS (FOTOS E PDF) ---

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
        
        # Certifique-se de que a função transcrever_imagem ainda existe no seu chat.py
        # ou substitua por uma chamada ao agente pedindo para descrever a imagem.
        if hasattr(chat, 'transcrever_imagem'):
            resultado = chat.transcrever_imagem(path, message.caption or "Transcreva esta imagem.")
        else:
            resultado = "⚠️ Função de visão computacional não encontrada no chat.py atualizado."
        
        if os.path.exists(path): os.remove(path)

    # 2. Se for PDF
    elif message.content_type == 'document' and message.document.file_name.lower().endswith('.pdf'):
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        path = f"temp_{uid}.pdf"
        with open(path, "wb") as f: f.write(downloaded)
        
        texto = pdf_helper.extrair_texto_pdf(path)
        
        if not texto or len(texto) < 10:
            img_path = pdf_helper.converter_pdf_em_imagem(path)
            if hasattr(chat, 'transcrever_imagem'):
                resultado = chat.transcrever_imagem(img_path, "Transcreva este documento escaneado.")
            else:
                resultado = "⚠️ OCR indisponível no momento."
            if os.path.exists(img_path): os.remove(img_path)
        else:
            # Usa o agente novo para resumir
            resultado = chat.perguntar_ao_agente(f"Resuma este conteúdo de PDF: {texto[:3000]}", bot_instance=bot, chat_id=uid)
        
        if os.path.exists(path): os.remove(path)
    
    else:
        bot.reply_to(message, "Envie uma foto ou um arquivo PDF.")
        return

    if modo == 'anotar':
        anotador.salvar_nota(uid, f"[ARQUIVO]: {resultado}")
        bot.reply_to(message, "✅ Conteúdo processado e salvo!")
    else:
        # Se a resposta for muito longa (limite telegram), corta
        if len(resultado) > 4000: resultado = resultado[:4000] + "..."
        bot.reply_to(message, resultado)

# --- TEXTO PRINCIPAL (AGENTE) ---

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    uid = message.chat.id
    if not tem_acesso(message): return

    modo = user_mode.get(uid, 'anotar')
    
    if modo == 'anotar':
        anotador.salvar_nota(uid, message.text)
        bot.reply_to(message, "✅ Anotado!")
    
    else:
        # MODO CHAT - AGORA USA O AGENTE COM FERRAMENTAS
        bot.send_chat_action(uid, 'typing')
        
        # 1. Recupera contexto de notas (Memória simples)
        notas = anotador.listar_notas(uid, limite=8)
        contexto = "\n".join([f"[{n[0]}] {n[2]}" for n in notas]) # Aqui passamos o ID e o Conteúdo real
        
        # 2. Chama o Agente Inteligente
        # Passamos 'bot' e 'uid' para que as ferramentas (gerar_imagem, etc)
        # possam enviar o feedback visual diretamente ao usuário enquanto a IA pensa.
        try:
            resposta = chat.perguntar_ao_agente(
                mensagem_usuario=message.text, 
                contexto_notas=contexto,
                bot_instance=bot, 
                chat_id=uid
            )
            
            # 3. Envia a resposta textual final da IA
            if resposta and len(resposta.strip()) > 0:
                try:
                    bot.reply_to(message, resposta, parse_mode="Markdown")
                except Exception:
                    # Fallback caso o Markdown esteja quebrado
                    bot.reply_to(message, resposta)
                    
        except Exception as e:
            bot.reply_to(message, f"😵 Ocorreu um erro no meu cérebro:\n{str(e)}")

if __name__ == "__main__":
    anotador.init_db()
    anotador.autorizar_usuario(MEU_ID, "Dono", "admin")
    print("🚀 PixelDust (Agente Autônomo) Iniciado!")
    bot.infinity_polling()

    