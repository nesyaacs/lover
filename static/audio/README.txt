CARA PAKAI LAGU DI WEBSITE (10MB MAKSIMAL):

1. PAKAI FILE MP3 (default / paling aman):
   - Simpan file mp3 di folder ini dengan nama: romantic_bgm.mp3
   - Maksimal ukuran: 10MB.
   - Sumber aktif di static/js/main.js -> MUSIC_CONFIG = { source: 'mp3' }

2. PAKAI LINK YOUTUBE (opsional):
   - Buka static/js/main.js, ubah menjadi:
     MUSIC_CONFIG = { source: 'youtube', youtubeVideoId: 'ID_ANDI_11_KARAKTER' }
   - ID diambil dari link https://www.youtube.com/watch?v=XXXXXX
     (bagian 11 karakter setelah v=).
   - Catatan: lagu dari music.youtube.com kadang tidak boleh di-embed.

CATATAN:
- Kalau MP3 tidak ada / YouTube gagal, otomatis diputar melodi sintetis.
- Musik mulai berputar setelah pengunjung mengisi nama di modal masuk.
- Batas maksimal SEMUA media (gambar di static/images + lagu di sini) = 10MB
  per file; app.py menampilkan peringatan di console jika ada yang lebih besar.