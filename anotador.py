import sqlite3
from datetime import datetime

DB_NAME = "notas.db"
# Timeout de 10 segundos para conexões, resolvendo o erro 'database is locked' em multithreading.
TIMEOUT = 10 

def init_db():
    """Inicializa o banco de dados, criando as tabelas se não existirem."""
    conn = sqlite3.connect(DB_NAME, timeout=TIMEOUT)
    
    # Tabela de Notas
    conn.execute('''CREATE TABLE IF NOT EXISTS notas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, data TEXT, conteudo TEXT)''')
    
    # Tabela de Usuários Autorizados
    conn.execute('''CREATE TABLE IF NOT EXISTS autorizados 
                 (user_id INTEGER PRIMARY KEY, nome TEXT, nivel TEXT)''')
    
    conn.commit()
    conn.close()

def verificar_acesso(user_id):
    """Verifica se o usuário está autorizado a usar o bot."""
    conn = sqlite3.connect(DB_NAME, timeout=TIMEOUT)
    cursor = conn.cursor()
    cursor.execute("SELECT nivel FROM autorizados WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def autorizar_usuario(user_id, nome, nivel="user"):
    """Adiciona ou atualiza um usuário na lista de autorizados."""
    conn = sqlite3.connect(DB_NAME, timeout=TIMEOUT)
    conn.execute("INSERT OR REPLACE INTO autorizados (user_id, nome, nivel) VALUES (?, ?, ?)", 
                 (user_id, nome, nivel))
    conn.commit()
    conn.close()

def salvar_nota(user_id, texto):
    """Salva uma nova anotação no banco de dados."""
    conn = sqlite3.connect(DB_NAME, timeout=TIMEOUT)
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    conn.execute("INSERT INTO notas (user_id, data, conteudo) VALUES (?, ?, ?)", (user_id, data_atual, texto))
    conn.commit()
    conn.close()

def listar_notas(user_id, limite=15):
    """Lista as últimas notas do usuário, retornando (ID, Data, Conteúdo)."""
    conn = sqlite3.connect(DB_NAME, timeout=TIMEOUT)
    cursor = conn.cursor()
    cursor.execute("SELECT id, data, conteudo FROM notas WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limite))
    notas = cursor.fetchall()
    conn.close()
    return notas

def limpar_todas(user_id):
    """Apaga TODAS as anotações pertencentes a um user_id específico."""
    conn = sqlite3.connect(DB_NAME, timeout=TIMEOUT)
    cursor = conn.cursor() # Usar cursor para obter o rowcount
    
    cursor.execute("DELETE FROM notas WHERE user_id = ?", (user_id,))
    
    mudancas = cursor.rowcount # CORREÇÃO: Usamos .rowcount do cursor
    conn.commit()
    conn.close()
    return mudancas > 0

def editar_nota(nota_id, novo_conteudo, user_id):
    """Atualiza o conteúdo de uma nota existente, verificando a posse."""
    conn = sqlite3.connect(DB_NAME, timeout=TIMEOUT)
    cursor = conn.cursor() # Usar cursor para obter o rowcount
    data_edicao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    conteudo_final = f"EDITADO ({data_edicao}): {novo_conteudo}"

    cursor.execute("""
        UPDATE notas 
        SET conteudo = ? 
        WHERE id = ? AND user_id = ?
    """, (conteudo_final, nota_id, user_id))
    
    mudancas = cursor.rowcount # CORREÇÃO: Usamos .rowcount do cursor
    conn.commit()
    conn.close()
    return mudancas > 0