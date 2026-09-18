from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from supabase import create_client, Client
from datetime import datetime
import os

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'mensiv_scrapbook_romantic_secret_key_2026'

# --- MASUKKAN CREDENTIAL SUPABASE KAMU DI SINI ---
SUPABASE_URL = "URL_SUPABASE_KAMU"
SUPABASE_KEY = "ANON_KEY_SUPABASE_KAMU"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    initial_name = session.get('visitor_name', '')
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
    ip_addr = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        supabase.table('visitors').insert({
            'name': name,
            'visited_at': now_str,
            'ip_address': ip_addr,
            'user_agent': user_agent
        }).execute()
    except Exception as e:
        print(f"Error visit: {e}")

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
        emotion = data.get('emotion', '💐')
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if not message:
            return jsonify({'status': 'error', 'message': 'Pesan tidak boleh kosong'}), 400
        
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
                'message': 'Pesan manismu berhasil tersimpan!',
                'comment': new_comment
            })
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Gagal menyimpan ucapan: {str(e)}'}), 500
    else:
        try:
            res = supabase.table('comments').select('*').order('id', desc=True).limit(50).execute()
            return jsonify({'status': 'success', 'comments': res.data})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/comments/<int:comment_id>/delete', methods=['POST'])
def admin_delete_comment(comment_id):
    if not session.get('admin_logged_in'):
        return jsonify({'status': 'error', 'message': 'Akses ditolak.'}), 401

    try:
        supabase.table('comments').delete().eq('id', comment_id).execute()
        return jsonify({'status': 'success', 'message': 'Komentar berhasil dihapus.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
