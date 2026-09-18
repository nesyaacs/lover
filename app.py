from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import database
import os

app = Flask(__name__)
app.secret_key = 'mensiv_scrapbook_romantic_secret_key_2026'

# Batas maksimal ukuran file media (gambar & lagu): 10MB per file
MEDIA_MAX_BYTES = 10 * 1024 * 1024
MEDIA_FOLDERS = ('static/images', 'static/audio')

# Ensure database tables exist
database.init_db()

# Cek ukuran media saat server jalan — warning jika ada file > 10MB
_project_dir = os.path.dirname(__file__)
for _folder in MEDIA_FOLDERS:
    _dir = os.path.join(_project_dir, _folder)
    if not os.path.isdir(_dir):
        continue
    for _name in sorted(os.listdir(_dir)):
        _path = os.path.join(_dir, _name)
        if os.path.isfile(_path) and os.path.getsize(_path) > MEDIA_MAX_BYTES:
            _mb = round(os.path.getsize(_path) / (1024 * 1024), 1)
            print(f"[PERINGATAN] {_folder}/{_name} ({_mb} MB) melebihi batas 10MB — halaman akan memuat lebih lambat.")

@app.route('/')
def index():
    initial_name = session.get('visitor_name', '')
    initial_comments = database.get_comments(20)
    return render_template('index.html', initial_name=initial_name, initial_comments=initial_comments)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin'))
        
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if database.verify_admin(username, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = 'Username atau password yang kamu masukkan salah!'
            
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
        
    stats = database.get_stats()
    visitors = database.get_visitors(100)
    comments = database.get_comments(100)
    return render_template('admin.html', stats=stats, visitors=visitors, comments=comments)

@app.route('/api/visit', methods=['POST'])
def api_visit():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'status': 'error', 'message': 'Nama tidak boleh kosong'}), 400
    
    session['visitor_name'] = name
    ip_addr = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    
    database.add_visitor(name=name, ip_address=ip_addr, user_agent=user_agent)
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
        
        comment_id = database.add_comment(name=name, message=message, emotion=emotion)
        
        return jsonify({
            'status': 'success',
            'message': 'Pesan manismu berhasil tersimpan!',
            'comment': {
                'id': comment_id,
                'name': name,
                'message': message,
                'emotion': emotion,
                'created_at': 'Baru saja'
            }
        })
    else:
        comments = database.get_comments(50)
        return jsonify({'status': 'success', 'comments': comments})

@app.route('/admin/comments/<int:comment_id>/delete', methods=['POST'])
def admin_delete_comment(comment_id):
    if not session.get('admin_logged_in'):
        return jsonify({'status': 'error', 'message': 'Akses ditolak. Silakan login sebagai admin.'}), 401

    deleted = database.delete_comment(comment_id)
    if deleted:
        stats = database.get_stats()
        return jsonify({'status': 'success', 'message': 'Komentar berhasil dihapus.', 'stats': stats})
    else:
        return jsonify({'status': 'error', 'message': 'Komentar tidak ditemukan.'}), 404

@app.route('/api/logs', methods=['GET'])
def api_logs():
    if not session.get('admin_logged_in'):
        return jsonify({'status': 'error', 'message': 'Akses ditolak. Silakan login sebagai admin.'}), 401
        
    visitors = database.get_visitors(100)
    comments = database.get_comments(100)
    stats = database.get_stats()
    return jsonify({
        'status': 'success',
        'stats': stats,
        'visitors': visitors,
        'comments': comments
    })

if __name__ == '__main__':
    print("Starting Interactive Scrapbook App on http://127.0.0.1:5000 ...")
    app.run(debug=True, port=5000)
