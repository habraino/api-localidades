import sqlite3

def get_distrito_by_nome(conn, nome: str):
    """Busca distrito pelo nome"""
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM distritos WHERE nome = ?", (nome,))
    row = cursor.fetchone()
    return dict(row) if row else None

def get_or_create_distrito(conn, nome: str):
    """Obtém ou cria um distrito"""
    distrito = get_distrito_by_nome(conn, nome)
    if not distrito:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO distritos (nome) VALUES (?)", (nome,))
        return {"id": cursor.lastrowid, "nome": nome}
    return distrito

def get_lugar_by_nome_distrito(conn, nome: str, distrito_id: int):
    """Verifica se um lugar já existe em um distrito"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nome, distrito_id FROM lugares WHERE nome = ? AND distrito_id = ?",
        (nome, distrito_id)
    )
    row = cursor.fetchone()
    return dict(row) if row else None

def create_lugar(conn, nome: str, distrito_id: int):
    """Cria um novo lugar"""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO lugares (nome, distrito_id) VALUES (?, ?)",
        (nome, distrito_id)
    )
    return {"id": cursor.lastrowid, "nome": nome, "distrito_id": distrito_id}

def get_all_distritos_with_lugares(conn):
    """Retorna todos os distritos com seus lugares"""
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM distritos ORDER BY nome")
    distritos = [dict(row) for row in cursor.fetchall()]
    
    for distrito in distritos:
        cursor.execute(
            "SELECT id, nome, distrito_id FROM lugares WHERE distrito_id = ? ORDER BY nome",
            (distrito['id'],)
        )
        distrito['lugares'] = [dict(row) for row in cursor.fetchall()]
    
    return distritos

def get_lugares_by_distrito(conn, distrito_id: int):
    """Retorna todos os lugares de um distrito"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nome, distrito_id FROM lugares WHERE distrito_id = ? ORDER BY nome",
        (distrito_id,)
    )
    return [dict(row) for row in cursor.fetchall()]

def get_all_lugares(conn):
    """Retorna todos os lugares"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.id, l.nome, l.distrito_id, d.nome as distrito_nome 
        FROM lugares l
        JOIN distritos d ON l.distrito_id = d.id
        ORDER BY l.nome
    """)
    return [dict(row) for row in cursor.fetchall()]

def delete_lugar(conn, lugar_id: int):
    """Remove um lugar"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM lugares WHERE id = ?", (lugar_id,))
    return cursor.rowcount > 0

def search_lugares(conn, query: str):
    """Busca lugares por nome (case insensitive)"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.id, l.nome, l.distrito_id, d.nome as distrito_nome 
        FROM lugares l
        JOIN distritos d ON l.distrito_id = d.id
        WHERE l.nome LIKE ?
        ORDER BY l.nome
        LIMIT 50
    """, (f'%{query}%',))
    return [dict(row) for row in cursor.fetchall()]

def get_total_count(conn):
    """Retorna total de distritos e lugares"""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM distritos")
    total_distritos = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM lugares")
    total_lugares = cursor.fetchone()['total']
    
    return {"total_distritos": total_distritos, "total_lugares": total_lugares}