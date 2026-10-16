"""Tambah / ganti akun login.   Pemakaian:  python buat_user.py namauser katasandi
Hasilnya otomatis ditulis ke .streamlit/secrets.toml (tidak perlu salin-tempel)."""
import os, re, sys
import auth

if len(sys.argv) != 3: sys.exit("Pemakaian: python buat_user.py namauser katasandi\nContoh   : python buat_user.py dosen Rahasia123")
nama, sandi = sys.argv[1], sys.argv[2]
if not re.fullmatch(r"[A-Za-z0-9_.-]+", nama): sys.exit("Nama pengguna hanya boleh huruf, angka, titik, strip, atau garis bawah (tanpa spasi).")
if len(sandi) < 6: sys.exit("Kata sandi minimal 6 karakter.")
jalur = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".streamlit", "secrets.toml"); os.makedirs(os.path.dirname(jalur), exist_ok=True)
baris = open(jalur, encoding="utf-8").read().splitlines() if os.path.exists(jalur) else []
if "[users]" not in [b.strip() for b in baris]: baris += ["[users]"]
baris = [b for b in baris if not re.match(rf"\s*{re.escape(nama)}\s*=", b)]            # hapus akun lama bernama sama
baris.insert([b.strip() for b in baris].index("[users]") + 1, f'{nama} = "{auth.buat_hash(sandi)}"')
open(jalur, "w", encoding="utf-8").write("\n".join(baris) + "\n")
print(f"✅ Akun '{nama}' tersimpan di {jalur}\nJalankan ulang Streamlit (Ctrl+C lalu: streamlit run app.py), lalu login memakai akun ini.")
