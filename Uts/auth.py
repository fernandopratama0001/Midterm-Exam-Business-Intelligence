"""Halaman login + otentikasi sederhana (kata sandi disimpan sebagai hash PBKDF2, bukan teks asli)."""
import hashlib, hmac, os, time
import streamlit as st

# Akun bawaan: admin / unimor2026  -> GANTI sebelum dipakai sungguhan (lihat buat_user.py & README).
DEFAULT_USERS = {"admin": "pbkdf2_sha256$200000$e0676bb92ae20a48$e8cec7ac1bdff6d71723e5cf08707db62f743b569efc7ff6dd99f75cfd4e85db"}
MAX_GAGAL, KUNCI_DETIK = 5, 30

def buat_hash(password, iterasi=200000):
    salt = os.urandom(8).hex(); h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterasi).hex()
    return f"pbkdf2_sha256${iterasi}${salt}${h}"

def cek_password(password, tersimpan):
    try:
        _, it, salt, h = tersimpan.split("$"); calc = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(it)).hex()
        return hmac.compare_digest(calc, h)
    except Exception: return False

def muat_user():
    try:
        u = dict(st.secrets["users"])   # .streamlit/secrets.toml  -> [users] nama = "hash"
        if u: return u
    except Exception: pass
    return DEFAULT_USERS

def sudah_login(): return bool(st.session_state.get("auth_user"))
def keluar():
    for k in ("auth_user", "gagal", "kunci", "identitas_ok"): st.session_state.pop(k, None)

CSS = """<style>
[data-testid="stSidebar"],[data-testid="stHeader"]{background:transparent}
.stApp::before{content:'';position:fixed;inset:0;background:url(data:image/png;base64,LOGO64) no-repeat 88% 55%/680px;opacity:.07;pointer-events:none}
.brand{padding:34px 10px 10px;text-align:left}
.ringw{position:relative;width:210px;height:210px;margin-bottom:22px;display:flex;align-items:center;justify-content:center}
.ringw:before{content:'';position:absolute;inset:0;border-radius:50%;background:conic-gradient(from 0deg,#53AEDC,#FFE600,#FF6B5E,#53AEDC);animation:spin 9s linear infinite;filter:blur(1px)}
.ringw:after{content:'';position:absolute;inset:6px;border-radius:50%;background:#0B1220}
.ringw img{position:relative;z-index:2;width:158px;animation:float 5s ease-in-out infinite;filter:drop-shadow(0 8px 22px #53aedc99)}
@keyframes spin{to{transform:rotate(360deg)}}@keyframes float{50%{transform:translateY(-8px)}}
.brand h1{margin:0;font-size:2.5rem;line-height:1.15;background:linear-gradient(90deg,#53AEDC,#FFE600);-webkit-background-clip:text;color:transparent}
.brand .s{color:#9fb3c8;margin:.7rem 0 1rem;max-width:480px}.brand .m{color:#FFE600;letter-spacing:.25em;font-size:.8rem;margin-bottom:1rem}
.fc{display:inline-block;margin:0 8px 8px 0;padding:4px 14px;border-radius:99px;font-size:.82rem;border:1px solid #53aedc66;color:#bfe3f5;background:#53aedc14}
.lt{font-size:1.5rem;font-weight:800;color:#fff;margin:0}.ls{color:#9fb3c8;margin:0 0 6px}
div[data-testid="stForm"]{background:linear-gradient(150deg,#15233fcc,#0e1729cc);border:1px solid #53aedc55;border-radius:22px;padding:26px 26px 18px;box-shadow:0 18px 50px #000a;backdrop-filter:blur(8px)}
div[data-testid="stForm"] button{width:100%}
.foot{color:#6f86a0;font-size:.8rem;text-align:center;margin-top:14px}
</style>"""

def halaman_login(logo64=""):
    st.markdown(CSS.replace("LOGO64", logo64), unsafe_allow_html=True)
    img = f'<img src="data:image/png;base64,{logo64}"/>' if logo64 else "🎓"
    kiri, kanan = st.columns([1.15, 1], vertical_alignment="center")
    kiri.markdown(f'<div class="brand"><div class="ringw">{img}</div><div class="m">SAPIENTIA ET VERITAS</div><h1>Sistem Analisis<br>Business Intelligence</h1><p class="s">Universitas Timor — ubah data transaksi menjadi temuan, pola belanja, segmen pelanggan, dan rencana aksi.</p><span class="fc">🧹 Preprocessing</span><span class="fc">🛒 Apriori</span><span class="fc">👥 RFM + K-Means</span><span class="fc">🎯 Rekomendasi</span></div>', unsafe_allow_html=True)
    with kanan:
        sisa = st.session_state.get("kunci", 0) - time.time()
        with st.form("login"):
            st.markdown('<p class="lt">👋 Selamat datang</p><p class="ls">Masuk untuk mengakses sistem analisis.</p>', unsafe_allow_html=True)
            u = st.text_input("Nama pengguna", placeholder="mis. admin"); p = st.text_input("Kata sandi", type="password", placeholder="••••••••")
            ok = st.form_submit_button("🔐 Masuk", type="primary")
        if ok:
            if sisa > 0: st.error(f"Terlalu banyak percobaan gagal. Coba lagi dalam {int(sisa) + 1} detik.")
            else:
                users = muat_user(); benar = u in users and cek_password(p, users[u])
                if not u in users: cek_password(p, DEFAULT_USERS["admin"])  # samakan waktu proses
                if benar: st.session_state["auth_user"] = u; st.session_state["gagal"] = 0; st.rerun()
                else:
                    g = st.session_state.get("gagal", 0) + 1; st.session_state["gagal"] = g
                    if g >= MAX_GAGAL: st.session_state["kunci"] = time.time() + KUNCI_DETIK; st.session_state["gagal"] = 0; st.error(f"Terlalu banyak percobaan gagal. Dikunci {KUNCI_DETIK} detik.")
                    else: st.error(f"Nama pengguna atau kata sandi salah. Sisa percobaan: {MAX_GAGAL - g}.")
        st.markdown('<div class="foot">© Universitas Timor · Akses terbatas</div>', unsafe_allow_html=True)
