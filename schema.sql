-- Schema database scrapbook (mensiv)
-- Jalankan dengan: sqlite3 scrapbook.db < schema.sql
-- atau biarkan otomatis dibuat oleh database.init_db().

-- Pengunjung / kunjungan
CREATE TABLE IF NOT EXISTS visitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    visited_at TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT
);

-- Ucapan & doa dari teman/sahabat
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    message TEXT NOT NULL,
    emotion TEXT DEFAULT '💐',
    created_at TEXT NOT NULL
);

-- Akun admin (password disimpan sebagai hash, bukan teks)
CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);