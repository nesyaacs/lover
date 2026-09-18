from flask import Flask, render_template, request, jsonify, session
from supabase import create_client, Client
from datetime import datetime
import os

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'mensiv_scrapbook_romantic_secret_key_2026'

# --- KONFIGURASI SUPABASE ---
# Pastikan ganti teks di bawah dengan API Credentials dari Supabase kamu
SUPABASE_URL = "https://xyz.supabase.co" 
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY and "http" in SUPABASE_URL:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Inisialisasi Supabase Gagal: {e}")

@app.route('/')
def index():
    initial_name = session.get('visitor_name', '')
    initial_comments = []
    
    if supabase:
        try:
            response = supabase.table('comments').select('*').order('id', desc=True).limit(20).execute()
            initial_comments = response.data or []
        except Exception as e:
            print(f"Error fetch comments: {e}")

    return render_template('index.html', initial_name=initial_name, initial_comments=initial_comments)

@app.route('/api/visit', methods=['POST'])
def api_visit():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'status': 'error', 'message': 'Nama tidak boleh kosong'}), 400
    
    session['visitor_name'] = name
    ip_addr = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if supabase:
        try:
            supabase.table('visitors').insert({
                'name': name,
                'visited_at': now_str,
                'ip_address': ip_addr,
                'user_agent': user_agent
            }).execute()
        except Exception as e:
            print(f"Error insert visitor: {e}")

    return jsonify({
        'status': 'success',
        'message': f'Selamat datang, {name}!'
    })

@app.route('/api/comments', methods=['GET', 'POST'])
def api_comments():
    if request.method == 'POST':
        data = request.get_json() or {}
        name = data.get('name', '').strip() or session.get('visitor_name', 'Anonim')
        message = data.get('message', '').strip()
        emotion = data.get('emotion', '💐')
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if not message:
            return jsonify({'status': 'error', 'message': 'Pesan tidak boleh kosong'}), 400
        
        if not supabase:
            return jsonify({'status': 'error', 'message': 'Koneksi database belum terhubung'}), 500

        try:
            res = supabase.table('comments').insert({
                'name': name,
                'message': message,
                'emotion': emotion,
                'created_at': now_str
            }).execute()
            
            new_comment = res.data[0] if res.data else {
                'name': name,
                'message': message,
                'emotion': emotion,
                'created_at': now_str
            }

            return jsonify({
                'status': 'success',
                'message': 'Pesan berhasil tersimpan!',
                'comment': new_comment
            })
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Gagal menyimpan: {str(e)}'}), 500
    else:
        if not supabase:
            return jsonify({'status': 'success', 'comments': []})
        try:
            res = supabase.table('comments').select('*').order('id', desc=True).limit(50).execute()
            return jsonify({'status': 'success', 'comments': res.data or []})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
