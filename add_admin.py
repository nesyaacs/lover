"""Script untuk menambah akun admin.

Cara pakai (dari folder mensiv):
    python add_admin.py <username> <password>

Contoh:
    python add_admin.py nesya rahasia123
"""
import sys
import database

def main():
    if len(sys.argv) != 3:
        print("Cara pakai: python add_admin.py <username> <password>")
        sys.exit(1)

    username = sys.argv[1].strip()
    password = sys.argv[2]

    if not username or not password:
        print("Username dan password tidak boleh kosong.")
        sys.exit(1)

    database.init_db()
    try:
        database.add_admin_user(username, password)
        print(f"Admin '{username}' berhasil ditambahkan ke database.")
    except Exception as e:
        print(f"Gagal menambah admin: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()