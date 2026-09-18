from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from supabase import create_client, Client
import os

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'mensiv_scrapbook_romantic_secret_key_2026'

# --- KONFIGURASI SUPABASE ---
SUPABASE_URL = "ISI_URL_SUPABASE_KAMU_DI_SINI"
SUPABASE_KEY = "ISI_ANON_KEY_SUPABASE_KAMU_DI_SINI"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    initial_name = session.get('visitor_name', '')
    
    # Ambil 20 ucapan terbaru dari tabel 'comments'
    try:
        response = supabase.table('comments').select('*').order('id', desc=True).limit(20).execute()
        initial_comments = response.data
    except Exception:
        initial_comments = []

    return render_template('index.html', initial_name=initial_name, initial_comments=initial_comments)

@app.route('/api/visit', methods=['POST'])
def api_visit():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'status': 'error', 'message': 'Nama tidak boleh kosong'}), 400
    
    session['visitor_name'] = name
    
    # Simpan data pengunjung ke tabel 'visitors'
    try:
        supabase.table('visitors').insert({'name': name}).execute()
    except Exception:
        pass

    return jsonify({
        'status': 'success',
        'message': f'Selamat datang, {name}! Kunjunganmu telah tercatat.'
    })

@app.route('/api/comments', methods=['GET', 'POST'])
def api_comments():
    if request.method == 'POST':
        data = request.get_json() or {}
        name = data.get('name', '').strip() or session.get('visitor_name', 'Anonim')
        message = data.get('message', '').strip()
        emotion = data.get('emotion', '❤️')
        
        if not message:
            return jsonify({'status': 'error', 'message': 'Pesan tidak boleh kosong'}), 400
        
        # Simpan ucapan permanen ke Supabase
        try:
            res = supabase.table('comments').insert({
                'name': name,
                'message': message,
                'emotion': emotion
            }).execute()
            
            new_comment = res.data[0] if res.data else {
                'name': name,
                'message': message,
                'emotion': emotion,
                'created_at': 'Baru saja'
            }

            return jsonify({
                'status': 'success',
                'message': 'Pesan manismu berhasil tersimpan!',
                'comment': new_comment
            })
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Gagal menyimpan: {str(e)}'}), 500
    else:
        try:
            res = supabase.table('comments').select('*').order('id', desc=True).limit(50).execute()
            return jsonify({'status': 'success', 'comments': res.data})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
