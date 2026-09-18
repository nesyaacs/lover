import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'scrapbook.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table for visitor logging
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            visited_at TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT
        )
    ''')
    
    # Table for wishes / comments from friends & loved ones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            message TEXT NOT NULL,
            emotion TEXT DEFAULT '💐',
            created_at TEXT NOT NULL
        )
    ''')

    # Table for admin accounts (password disimpan sebagai hash)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    conn.commit()

    # Seed akun admin default (admin / admin123) hanya jika belum ada admin sama sekali
    cursor.execute('SELECT COUNT(*) FROM admin_users')
    if cursor.fetchone()[0] == 0:
        add_admin_user('admin', 'admin123')

    conn.close()

def add_admin_user(username, password):
    """Menambah akun admin baru. Password disimpan sebagai hash (bukan teks)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    password_hash = generate_password_hash(password)
    cursor.execute(
        'INSERT INTO admin_users (username, password_hash, created_at) VALUES (?, ?, ?)',
        (username.strip(), password_hash, now_str)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

def verify_admin(username, password):
    """Cek login admin terhadap database. Mengembalikan True/False."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM admin_users WHERE username = ?', (username.strip(),))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return False
    return check_password_hash(row['password_hash'], password)

def get_admin_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, created_at FROM admin_users ORDER BY id ASC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_admin_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM admin_users WHERE id = ?', (user_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

def add_visitor(name, ip_address='127.0.0.1', user_agent=''):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        'INSERT INTO visitors (name, visited_at, ip_address, user_agent) VALUES (?, ?, ?, ?)',
        (name.strip(), now_str, ip_address, user_agent)
    )
    conn.commit()
    conn.close()

def get_visitors(limit=100):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM visitors ORDER BY id DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_comment(name, message, emotion='💐'):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        'INSERT INTO comments (name, message, emotion, created_at) VALUES (?, ?, ?, ?)',
        (name.strip(), message.strip(), emotion, now_str)
    )
    conn.commit()
    comment_id = cursor.lastrowid
    conn.close()
    return comment_id

def get_comments(limit=50):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM comments ORDER BY id DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_comment(comment_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM visitors')
    visitor_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM comments')
    comment_count = cursor.fetchone()[0]
    
    conn.close()
    return {
        'total_visitors': visitor_count,
        'total_comments': comment_count
    }

if __name__ == '__main__':
    init_db()
    print("Database initialized!")
