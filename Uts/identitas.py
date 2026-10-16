"""Halaman identitas (tampil setelah login, sebelum halaman analisis). Ubah data di dict IDENTITAS."""
import streamlit as st
try: from foto_data import FOTO_B64
except Exception: FOTO_B64 = ""

IDENTITAS = {"Nama": "Fernando Aditya Pratama", "NPM": "51230137", "Universitas": "Universitas Timor",
             "Program Studi": "Teknologi Informasi", "Mata Kuliah": "Business Intelligence"}
IKON = {"Nama": "🧑‍🎓", "NPM": "🆔", "Universitas": "🏛️", "Program Studi": "💻", "Mata Kuliah": "📊"}
WARNA = {"Nama": "#53AEDC", "NPM": "#FFE600", "Universitas": "#34D399", "Program Studi": "#A78BFA", "Mata Kuliah": "#FF6B5E"}

CSS = """<style>
.stApp::before{content:'';position:fixed;inset:0;background:url(data:image/png;base64,LOGO64) no-repeat 92% 60%/640px;opacity:.06;pointer-events:none}
.pf{text-align:center;padding:26px 18px;border-radius:24px;background:linear-gradient(155deg,#15233fdd,#0e1729dd);border:1px solid #53aedc55;box-shadow:0 18px 50px #000a}
.ph{position:relative;width:226px;height:226px;margin:0 auto 18px;display:flex;align-items:center;justify-content:center}
.ph:before{content:'';position:absolute;inset:0;border-radius:50%;background:conic-gradient(from 0deg,#53AEDC,#FFE600,#FF6B5E,#A78BFA,#53AEDC);animation:sp 8s linear infinite}
.ph:after{content:'';position:absolute;inset:7px;border-radius:50%;background:#0B1220}
.ph img{position:relative;z-index:2;width:196px;height:196px;border-radius:50%;object-fit:cover;box-shadow:0 8px 28px #000b}
@keyframes sp{to{transform:rotate(360deg)}}
.pn{font-size:1.45rem;font-weight:800;color:#fff;margin:0}.pm{display:inline-block;margin-top:8px;padding:3px 16px;border-radius:99px;background:#FFE60022;border:1px solid #FFE60088;color:#FFE600;font-weight:700;letter-spacing:.08em}
.pu{display:flex;gap:10px;align-items:center;justify-content:center;margin-top:16px;color:#9fb3c8;font-size:.88rem}.pu img{height:34px}
.ti{margin:0;font-size:2rem;font-weight:800;background:linear-gradient(90deg,#53AEDC,#FFE600);-webkit-background-clip:text;color:transparent}.su{color:#9fb3c8;margin:.2rem 0 1rem}
.ic{display:flex;gap:14px;align-items:center;padding:14px 16px;border-radius:16px;background:#101a2e;border:1px solid #ffffff12;border-left:4px solid var(--c);margin-bottom:10px}
.ic .e{font-size:1.7rem}.ic small{color:#9fb3c8;display:block;letter-spacing:.06em;text-transform:uppercase;font-size:.7rem}.ic b{color:#fff;font-size:1.08rem}
.ab{padding:14px 16px;border-radius:16px;background:#53aedc14;border:1px dashed #53aedc66;color:#cfe0f1;font-size:.9rem;margin:6px 0 14px}
</style>"""

def halaman_identitas(logo64=""):
    st.markdown(CSS.replace("LOGO64", logo64), unsafe_allow_html=True)
    foto = f'<img src="data:image/jpeg;base64,{FOTO_B64}"/>' if FOTO_B64 else '<span style="font-size:5rem;position:relative;z-index:2">🧑‍🎓</span>'
    lg = f'<img src="data:image/png;base64,{logo64}"/>' if logo64 else ""
    kiri, kanan = st.columns([1, 1.7], vertical_alignment="center")
    kiri.markdown(f'<div class="pf"><div class="ph">{foto}</div><p class="pn">{IDENTITAS["Nama"]}</p><span class="pm">NPM {IDENTITAS["NPM"]}</span><div class="pu">{lg}<span>{IDENTITAS["Universitas"]}<br>{IDENTITAS["Program Studi"]}</span></div></div>', unsafe_allow_html=True)
    with kanan:
        st.markdown('<p class="ti">🪪 Identitas Mahasiswa</p><p class="su">Pengembang Sistem Analisis Business Intelligence</p>', unsafe_allow_html=True)
        for k, v in IDENTITAS.items():
            st.markdown(f'<div class="ic" style="--c:{WARNA[k]}"><div class="e">{IKON[k]}</div><div><small>{k}</small><b>{v}</b></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="ab">Sistem ini memproses data transaksi melalui pembersihan data, <b>Apriori</b>, dan segmentasi <b>RFM + K-Means</b>, lalu menyusun temuan dan rekomendasi dari hasil analisis.</div>', unsafe_allow_html=True)
        a, b = st.columns([2, 1])
        if a.button("🚀 Masuk ke Sistem Analisis", type="primary"): st.session_state["identitas_ok"] = True; st.rerun()
        if b.button("🚪 Keluar"):
            import auth; auth.keluar(); st.rerun()
