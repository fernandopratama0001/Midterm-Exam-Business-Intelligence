# UNIMOR · Sistem Analisis Business Intelligence (Streamlit + Plotly)
    pip install -r requirements.txt
    streamlit run app.py
Berkas WAJIB satu folder: app.py, analisis.py, auth.py, identitas.py, logo_data.py, foto_data.py (logo & foto tertanam).
Alur: Login -> Halaman Identitas -> Sistem Analisis. Ubah data identitas di dict IDENTITAS pada identitas.py.
Letakkan P8__UTS_Business_Intelligence.xlsx di folder yang sama atau unggah di halaman utama.

## Login
Akun bawaan: **admin / unimor2026** (GANTI sebelum dipakai sungguhan).

Membuat akun baru (otomatis tersimpan ke .streamlit/secrets.toml):
1. Buka terminal di folder aplikasi (folder yang berisi app.py).
2. Jalankan: `python buat_user.py namauser katasandi`   contoh: `python buat_user.py dosen Rahasia123`
3. Hentikan Streamlit (Ctrl+C), jalankan lagi `streamlit run app.py`, lalu login.
Ulangi langkah 2 untuk akun lain. Nama yang sama = kata sandi diganti. Setelah ada akun sendiri, akun bawaan admin tidak aktif lagi.
Catatan: login ini pembatas akses dasar (kata sandi di-hash PBKDF2, 5x salah = terkunci 30 detik). Untuk data sensitif/internet publik, tambahkan HTTPS/autentikasi server.
