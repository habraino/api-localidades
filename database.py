import sqlite3
from contextlib import contextmanager

DATABASE_URL = "localidades.db"

@contextmanager
def get_db():
    """Context manager para conexões com o banco de dados"""
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row  # Permite acesso por nome de coluna
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Inicializa o banco de dados criando as tabelas"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Criar tabela de distritos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS distritos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Criar tabela de lugares
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lugares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                distrito_id INTEGER NOT NULL,
                FOREIGN KEY (distrito_id) REFERENCES distritos (id) ON DELETE CASCADE,
                UNIQUE(nome, distrito_id)
            )
        ''')
        
        # Criar índices para buscas mais rápidas
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lugares_nome ON lugares(nome)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lugares_distrito ON lugares(distrito_id)')