import os
import json
import sqlite3
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from werkzeug.security import generate_password_hash, check_password_hash

# ============================================================
# KONFIGURASI
# ============================================================
DB_PATH = os.path.join(os.path.dirname(__file__), 'scrapbook.db')

# Isi dari Environment Variables Vercel (Project Settings > Environment Variables):
#   SUPABASE_URL   -> contoh: https://xxxx.supabase.co
#   SUPABASE_KEY   -> anon/public key dari Supabase (Settings > API)
#   ADMIN_USERNAME -> username admin (default: nesya)
#   ADMIN_PASSWORD -> password admin  (default: neysadmin)
#
# Kalau SUPABASE_URL & SUPABASE_KEY terisi -> pakai Supabase (wajib untuk Vercel).
# Kalau kosong -> fallback otomatis ke SQLite (cocok untuk jalan lokal).
SUPABASE_URL = os.environ.get('SUPABASE_URL', '').strip().rstrip('/')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '').strip()
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'nesya')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'neysadmin')


def use_supabase():
    """True jika terhubung ke Supabase, False jika pakai SQLite lokal."""
    return bool(SUPABASE_URL and SUPABASE_KEY)


# ============================================================
# HELPERS SUPABASE (REST / PostgREST, hanya stdlib, tanpa pip baru)
# ============================================================
def _sb_request(method, table, params=None, payload=None, prefer='return=minimal', want_count=False):
    url = f'{SUPABASE_URL}/rest/v1/{table}'
    if params:
        url = f'{url}?{urlencode(params)}'

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': prefer,
    }
    body = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = Request(url, data=body, headers=headers, method=method)

    try:
        with urlopen(req, timeout=30) as resp:
            raw = resp.read().decode('utf-8', 'replace')
            content_range = resp.headers.get('Content-Range', '')
    except HTTPError as e:
        detail = e.read().decode('utf-8', 'replace')
        raise RuntimeError(f'Supabase {method} {table} gagal ({e.code}): {detail}') from e

    if want_count:
        if '/' in content_range:
            try:
                return int(content_range.split('/')[-1])
            except ValueError:
                return 0
        return 0

    if raw.strip():
        try:
            return json.loads(raw)
        except ValueError:
            return []
    return []


# ============================================================
# INISIALISASI
# ============================================================
def init_db():
    # Mode Supabase: tabel dibuat manual lewat SQL Editor (lihat supabase.sql).
    # Jadi di sini tidak dilakukan apa-apa.
    if use_supabase():
        return None

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            visited_at TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            message TEXT NOT NULL,
            emotion TEXT DEFAULT '💐',
            created_at TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    conn.commit()

    cursor.execute('SELECT COUNT(*) FROM admin_users')
    if cursor.fetchone()[0] == 0:
        add_admin_user('nesya', 'neysadmin')

    conn.close()


# ============================================================
# ADMIN
# ============================================================
def add_admin_user(username, password):
    if use_supabase():
        print('[INFO] Mode Supabase: admin login diatur lewat env ADMIN_USERNAME & ADMIN_PASSWORD di Vercel.')
        return None

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
    if use_supabase():
        return username.strip() == ADMIN_USERNAME and password == ADMIN_PASSWORD

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM admin_users WHERE username = ?', (username.strip(),))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return False
    return check_password_hash(row['password_hash'], password)


def get_admin_users():
    if use_supabase():
        return []
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, created_at FROM admin_users ORDER BY id ASC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_admin_user(user_id):
    if use_supabase():
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM admin_users WHERE id = ?', (user_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


# ============================================================
# VISITOR / PENGUNJUNG
# ============================================================
def add_visitor(name, ip_address='127.0.0.1', user_agent=''):
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if use_supabase():
        _sb_request('POST', 'visitors', payload={
            'name': name.strip(),
            'visited_at': now_str,
            'ip_address': ip_address,
            'user_agent': user_agent,
        })
        return None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO visitors (name, visited_at, ip_address, user_agent) VALUES (?, ?, ?, ?)',
        (name.strip(), now_str, ip_address, user_agent)
    )
    conn.commit()
    conn.close()


def get_visitors(limit=100):
    if use_supabase():
        return _sb_request('GET', 'visitors', params={
            'select': '*',
            'order': 'id.desc',
            'limit': str(limit),
        })

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM visitors ORDER BY id DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ============================================================
# KOMENTAR / UCAPAN (WISHES & PRAYERS)
# ============================================================
def add_comment(name, message, emotion='💐'):
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if use_supabase():
        rows = _sb_request('POST', 'comments', prefer='return=representation', payload={
            'name': name.strip(),
            'message': message.strip(),
            'emotion': emotion,
            'created_at': now_str,
        })
        return rows[0]['id'] if rows else None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO comments (name, message, emotion, created_at) VALUES (?, ?, ?, ?)',
        (name.strip(), message.strip(), emotion, now_str)
    )
    conn.commit()
    comment_id = cursor.lastrowid
    conn.close()
    return comment_id


def get_comments(limit=50):
    if use_supabase():
        return _sb_request('GET', 'comments', params={
            'select': '*',
            'order': 'id.desc',
            'limit': str(limit),
        })

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM comments ORDER BY id DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_comment(comment_id):
    if use_supabase():
        rows = _sb_request('DELETE', 'comments', params={
            'id': f'eq.{comment_id}',
        }, prefer='return=representation')
        return len(rows) > 0

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


# ============================================================
# STATISTIK
# ============================================================
def get_stats():
    if use_supabase():
        visitors = _sb_request('GET', 'visitors', params={'select': 'id'}, prefer='count=exact', want_count=True)
        comments = _sb_request('GET', 'comments', params={'select': 'id'}, prefer='count=exact', want_count=True)
        return {
            'total_visitors': visitors,
            'total_comments': comments,
        }

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM visitors')
    visitor_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM comments')
    comment_count = cursor.fetchone()[0]
    conn.close()
    return {
        'total_visitors': visitor_count,
        'total_comments': comment_count,
    }


# ============================================================
# KONEKSI SQLITE (hanya dipakai saat mode lokal)
# ============================================================
def get_db_connection():
    if os.environ.get('VERCEL') and not use_supabase():
        raise RuntimeError(
            'Mode Vercel terdeteksi tapi SUPABASE_URL / SUPABASE_KEY belum di-set '
            'di Project Settings > Environment Variables, lalu Redeploy.'
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


if __name__ == '__main__':
    init_db()
    print('Database initialized!')