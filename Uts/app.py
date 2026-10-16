"""UNIMOR · Sistem Analisis Business Intelligence (Streamlit + Plotly). Jalankan: streamlit run app.py"""
import base64, io, os
import numpy as np, pandas as pd, streamlit as st
import plotly.express as px, plotly.graph_objects as go
from plotly.subplots import make_subplots
import analisis as A
import auth, identitas

HERE = os.path.dirname(os.path.abspath(__file__)); DEFAULT = os.path.join(HERE, "P8__UTS_Business_Intelligence.xlsx")
try: from logo_data import LOGO_B64 as logo64
except Exception: logo64 = ""
if not logo64:  # cadangan: cari file logo di beberapa lokasi
    for p in [os.path.join(HERE, "assets", "logo_unimor.png"), os.path.join(HERE, "logo_unimor.png")]:
        if os.path.exists(p): logo64 = base64.b64encode(open(p, "rb").read()).decode(); break
LOGO_BYTES = base64.b64decode(logo64) if logo64 else None
try:
    from PIL import Image; ICON = Image.open(io.BytesIO(LOGO_BYTES)) if LOGO_BYTES else "📊"
except Exception: ICON = "📊"
st.set_page_config(page_title="UNIMOR · Sistem Analisis BI", page_icon=ICON, layout="wide")
BLUE, YEL, RED, MINT, VIO = "#53AEDC", "#FFE600", "#FF6B5E", "#34D399", "#A78BFA"
SEGCOL = {"Loyal Aktif": MINT, "Bernilai Tinggi Mulai Pasif": YEL, "Pelanggan Biasa (Potensial)": BLUE, "Berisiko Churn": RED}; PAL = [BLUE, YEL, MINT, VIO, RED, "#F97316", "#22D3EE", "#F472B6"]
rp = lambda v: "Rp " + f"{v:,.0f}".replace(",", "."); rj = lambda v: f"Rp {v / 1e6:,.1f} jt".replace(",", "_").replace(".", ",").replace("_", ".")
bln = lambda m: ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"][int(m[5:]) - 1] + " " + m[:4]
try:
    if LOGO_BYTES: st.logo(LOGO_BYTES, size="large")
except Exception: pass

st.markdown("""<style>
.stApp{background:radial-gradient(1100px 560px at 8% -8%,#12315a88,transparent),radial-gradient(900px 480px at 100% 0,#53aedc22,transparent),#0B1220}
.block-container,[data-testid="stMainBlockContainer"]{padding-top:5.2rem!important;max-width:1250px}
.hero{display:flex;gap:24px;align-items:center;padding:22px 28px;border-radius:22px;background:linear-gradient(120deg,#12315a,#0b1220 75%);border:1px solid #53aedc55;box-shadow:0 12px 40px #0009}
.hero img{height:96px;filter:drop-shadow(0 4px 12px #53aedc66)}.hero h1{margin:0;font-size:2.1rem;background:linear-gradient(90deg,#53AEDC,#FFE600);-webkit-background-clip:text;color:transparent}
.hero p{margin:.3rem 0 0;color:#9fb3c8}.chip{display:inline-block;margin:8px 6px 0 0;padding:2px 12px;border-radius:99px;font-size:.78rem;border:1px solid #53aedc66;color:#bfe3f5}
.kpi{border-radius:16px;padding:16px 18px;background:linear-gradient(145deg,#15233f,#0e1729);border:1px solid #ffffff14;border-top:3px solid var(--c)}
.kpi small{color:#9fb3c8}.kpi b{display:block;font-size:1.55rem;color:#fff}.kpi span{color:var(--c);font-size:.8rem}
.ins{border-radius:16px;padding:16px;background:#101a2e;border:1px solid #ffffff12;border-left:4px solid var(--c);height:100%}.ins h4{margin:0 0 4px;color:var(--c)}.ins p{margin:0;color:#cfe0f1;font-size:.92rem}
.rec{border-radius:18px;overflow:hidden;background:#0f1a2e;border:1px solid #ffffff18;height:100%}.rec .h{padding:12px 16px;background:var(--c);color:#0B1220;font-weight:800}
.rec .b{padding:14px 16px;color:#d6e4f3;font-size:.92rem}.rec .m{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 10px}.rec .m span{background:#ffffff12;border-radius:8px;padding:2px 9px;font-size:.8rem}
.tl{border-left:3px solid #53AEDC;margin:8px 0 0 10px;padding-left:22px}.tl div{position:relative;margin:0 0 20px;color:#d6e4f3}.tl div:before{content:'';position:absolute;left:-31px;top:5px;width:13px;height:13px;border-radius:50%;background:var(--c);box-shadow:0 0 0 4px #53aedc33}.tl b{color:var(--c)}
.lb{display:flex;align-items:center;gap:12px;padding:10px 14px;border-radius:14px;background:#101a2e;border:1px solid #ffffff12;margin-bottom:8px}.lb .r{font-size:1.5rem}
div[data-testid="stPopover"] button,.stButton button{width:100%;white-space:nowrap}
</style>""", unsafe_allow_html=True)
if not auth.sudah_login():
    auth.halaman_login(logo64); st.stop()
if not st.session_state.get("identitas_ok"):
    identitas.halaman_identitas(logo64); st.stop()
_a, _b = st.columns([6, 1], vertical_alignment="center")
_a.caption(f"👤 Masuk sebagai **{st.session_state['auth_user']}**")
if _b.button("🚪 Keluar"): auth.keluar(); st.session_state.pop("h", None); st.rerun()
img = f'<img src="data:image/png;base64,{logo64}"/>' if logo64 else ""
st.markdown(f"""<div class="hero">{img}<div><h1>Sistem Analisis Business Intelligence</h1><p>Universitas Timor · <i>Sapientia et Veritas</i> — dari data transaksi mentah menjadi temuan, pola belanja, segmen pelanggan, dan rencana aksi.</p><span class="chip">🧹 Preprocessing</span><span class="chip">🛒 Apriori</span><span class="chip">👥 RFM + K-Means</span><span class="chip">🎯 Rekomendasi</span></div></div>""", unsafe_allow_html=True)

def tema(fig, h=420):
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=h, margin=dict(l=10, r=10, t=44, b=10), font=dict(color="#cfe0f1")); return fig
def kpi(label, val, sub, c): return f'<div class="kpi" style="--c:{c}"><small>{label}</small><b>{val}</b><span>{sub}</span></div>'
def ins(icon, title, text, c): return f'<div class="ins" style="--c:{c}"><h4>{icon} {title}</h4><p>{text}</p></div>'

def jalankan(src, ms, mc, k):
    with st.status("Menjalankan pipeline analisis…", expanded=True) as s:
        st.write("📥 Membaca file Excel…"); raw, cat, cust = A.baca(src)
        st.write("🧹 Membersihkan data (duplikat, nilai kosong, harga & quantity tidak valid)…"); df, log = A.preprocess(raw, cat, cust); au = A.audit(raw)
        st.write("🛒 Menambang pola belanja dengan Apriori…"); R, nsup, B = A.apriori(df, ms, mc)
        st.write("👥 Membentuk segmen pelanggan (RFM + K-Means)…"); rfm, ref = A.rfm_features(df); X, ev = A.evaluasi_k(rfm); rfm, prof = A.klaster(rfm, X, k)
        df = df.merge(rfm.Segmen, left_on="Customer_ID", right_index=True, how="left"); df["Segmen"] = df.Segmen.fillna("Tidak Teridentifikasi")
        st.write("💡 Menyusun temuan & rekomendasi dari hasil…"); segR = A.aturan_per_segmen(df, B, ms); w = A.wawasan(df, R, B, prof, rfm)
        s.update(label="Analisis selesai ✅", state="complete", expanded=False)
    st.session_state["h"] = dict(au=au, df=df, log=log, R=R, nsup=nsup, rfm=rfm, prof=prof, ev=ev, ref=ref, segR=segR, w=w, k=k, ms=ms, mc=mc, raw=len(raw)); st.toast("Analisis selesai 🎉")

st.write("")
cu, cb = st.columns([2, 1.5], vertical_alignment="bottom")
up = cu.file_uploader("📂 Unggah data transaksi (Excel: Data_Raw, opsional Data_Produk & Data_Pelanggan)", type=["xlsx", "xls"])
src = up if up is not None else (DEFAULT if os.path.exists(DEFAULT) else None)
with cb:
    b1, b2 = st.columns(2)
    with b1.popover("⚙️ Pengaturan lanjutan"):
        ms = st.slider("Min. support (%)", 0.5, 10.0, 1.0, 0.5) / 100; mc = st.slider("Min. confidence (%)", 5, 80, 15, 5) / 100; k = st.slider("Jumlah segmen (k)", 2, 8, 4)
    go_btn = b2.button("🚀 Jalankan Analisis", type="primary", disabled=src is None)
if src is None: st.info("Unggah file Excel untuk memulai.")
if go_btn:
    try: jalankan(src, ms, mc, k)
    except Exception as e: st.error(f"Gagal memproses file: {e}")
if "h" not in st.session_state: st.stop()
h = st.session_state["h"]; df, R, prof, rfm, w, ev = h["df"], h["R"], h["prof"], h["rfm"], h["w"], h["ev"]
SC = lambda s: SEGCOL.get(s, VIO)

k_ = st.columns(5); nt = df.Transaction_ID.nunique()
for col, (a, b, c_, d) in zip(k_, [("💰 Total penjualan", rj(w["total"]), f"{len(df):,} baris item".replace(",", "."), BLUE), ("🧾 Transaksi", f"{nt:,}".replace(",", "."), f"{w['basket']:.2f} produk/nota".replace(".", ",", 1), YEL), ("🧑‍🤝‍🧑 Pelanggan", f"{df.Customer_ID.nunique():,}".replace(",", "."), f"{h['k']} segmen", MINT), ("🏆 Produk #1", w["top_prod"][0], f"{w['top_prod'][1]:.1%} penjualan", VIO), ("🔗 Aturan Apriori", str(len(R)), f"{h['nsup']} itemset", RED)]):
    col.markdown(kpi(a, b, c_, d), unsafe_allow_html=True)
st.write("")
T = st.tabs(["✨ Temuan", "🌌 Penjualan", "🕸️ Pola Belanja", "🧬 Segmen Pelanggan", "🎯 Rekomendasi", "🧹 Kualitas Data"])

with T[0]:
    st.subheader("Temuan utama (dibuat otomatis dari hasil analisis)")
    b0 = w["bundles"][0] if w["bundles"] else None; big = prof.iloc[0]; ch = prof[prof.Segmen == "Berisiko Churn"]
    cards = [("🏆", "Produk andalan", f"<b>{w['top_prod'][0]}</b> menyumbang {w['top_prod'][1]:.1%} penjualan; tiga produk teratas {w['top3']:.0%}.", BLUE),
             ("🧺", "Kategori terkuat", f"Kategori <b>{w['top_cat'][0]}</b> memimpin dengan {w['top_cat'][1]:.1%} dari total penjualan.", YEL),
             ("📅", "Musim penjualan", f"Puncak <b>{bln(w['best_month'][0])}</b> ({rj(w['best_month'][1])}); terendah <b>{bln(w['low_month'][0])}</b> ({rj(w['low_month'][1])}).", MINT),
             ("🗓️", "Hari paling ramai", f"<b>{w['best_day'][0]}</b> menyumbang {w['best_day'][1]:.1%} penjualan; <b>{w['low_day'][0]}</b> terendah ({w['low_day'][1]:.1%}).", VIO),
             ("🔗", "Pola beli bersama", (f"Pembeli <b>{b0['Jika']}</b> membeli juga <b>{b0['Maka']}</b> pada {b0['Confidence']:.0%} nota (lift {b0['Lift']:.2f}). " if b0 else "Tidak ada aturan lolos ambang. ") + f"{w['multi']:.0%} nota berisi lebih dari 1 produk.", RED),
             ("👥", "Segmen penentu", f"<b>{big.Segmen}</b>: {int(big.Pelanggan)} pelanggan, {big.Total_Belanja / prof.Total_Belanja.sum():.0%} belanja. 20% pelanggan teratas menyumbang {w['pareto']:.0%} (" + ("terkonsentrasi)" if w['pareto'] > .6 else "relatif merata)"), "#F97316")]
    for row in (cards[:3], cards[3:]):
        for col, cd in zip(st.columns(3), row): col.markdown(ins(*cd), unsafe_allow_html=True)
        st.write("")
    st.subheader("🏅 Pelanggan teratas (berdasarkan total belanja)")
    for i, r in w["top_cust"].iterrows():
        st.markdown(f'<div class="lb"><div class="r">{["🥇","🥈","🥉","🏅","🏅"][i]}</div><div style="flex:1"><b>{r.Customer_ID}</b> <span style="color:{SC(r.Segmen)}">● {r.Segmen}</span></div><div>{rp(r.Monetary)} · {int(r.Frequency)}× belanja · terakhir {int(r.Recency)} hari lalu</div></div>', unsafe_allow_html=True)

with T[1]:
    a, b = st.columns(2)
    d = df.assign(Hari=df.Transaction_Date.dt.dayofweek).pivot_table(index="Hari", columns="Month", values="Net_Sales", aggfunc="sum").reindex(range(7))
    f1 = go.Figure(go.Heatmap(z=d.values / 1e6, x=[bln(m) for m in d.columns], y=A.HARI, colorscale=[[0, "#0f1b2e"], [.5, "#2b6ea0"], [1, YEL]], colorbar=dict(title="Rp jt")))
    a.plotly_chart(tema(f1.update_layout(title="🔥 Kalender panas penjualan (hari × bulan)"), 400))
    m = df.groupby("Month").Net_Sales.sum() / 1e6
    f2 = go.Figure(go.Scatter(x=[bln(x) for x in m.index], y=m.values, mode="lines+markers", fill="tozeroy", line=dict(color=BLUE, width=3), fillcolor="rgba(83,174,220,.18)"))
    b.plotly_chart(tema(f2.update_layout(title="📈 Tren penjualan bulanan (Rp juta)"), 400))
    tm = df.groupby(["Category", "Product_Name"]).Net_Sales.sum().reset_index()
    st.plotly_chart(tema(px.treemap(tm, path=["Category", "Product_Name"], values="Net_Sales", color="Category", color_discrete_sequence=PAL, title="🧩 Peta penjualan: kategori → produk"), 460))
    sk = df.groupby(["Category", "Payment_Method"]).Net_Sales.sum().reset_index(); cs, ps = list(sk.Category.unique()), list(sk.Payment_Method.unique())
    f3 = go.Figure(go.Sankey(node=dict(label=cs + ps, color=[PAL[i % 8] for i in range(len(cs + ps))], pad=18), link=dict(source=sk.Category.map(cs.index), target=sk.Payment_Method.map(lambda x: len(cs) + ps.index(x)), value=sk.Net_Sales, color="rgba(83,174,220,.25)")))
    st.plotly_chart(tema(f3.update_layout(title="🌊 Aliran uang: kategori → metode pembayaran"), 420))

with T[2]:
    st.caption(f"Min. support {h['ms']:.1%} · min. confidence {h['mc']:.0%} → {h['nsup']} frequent itemset, {len(R)} aturan. Asosiasi bukan sebab-akibat.")
    S = R[~R.Jika.str.contains(r"\+") & ~R.Maka.str.contains(r"\+")].copy(); S["k"] = S.apply(lambda r: "|".join(sorted([r.Jika, r.Maka])), axis=1); S = S.drop_duplicates("k").head(15)
    if S.empty: st.warning("Tidak ada aturan berpasangan tunggal pada ambang ini.")
    else:
        nodes = sorted(set(S.Jika) | set(S.Maka)); ang = np.linspace(0, 2 * np.pi, len(nodes), endpoint=False); pos = {v: (np.cos(t), np.sin(t)) for v, t in zip(nodes, ang)}
        sales = df.groupby("Product_Name").Net_Sales.sum(); cat = df.drop_duplicates("Product_Name").set_index("Product_Name").Category; cl = sorted(cat.unique()); fg = go.Figure()
        for _, r in S.iterrows():
            fg.add_trace(go.Scatter(x=[pos[r.Jika][0], pos[r.Maka][0]], y=[pos[r.Jika][1], pos[r.Maka][1]], mode="lines", line=dict(width=1 + r.Lift * 1.6, color="rgba(255,230,0,.45)"), hoverinfo="text", text=f"{r.Jika} → {r.Maka}<br>lift {r.Lift:.2f} · confidence {r.Confidence:.0%}", showlegend=False))
        fg.add_trace(go.Scatter(x=[pos[v][0] for v in nodes], y=[pos[v][1] for v in nodes], mode="markers+text", text=nodes, textposition="top center", hoverinfo="text", showlegend=False,
                                marker=dict(size=[16 + 34 * sales.get(v, 0) / sales.max() for v in nodes], color=[PAL[cl.index(cat[v]) % 8] for v in nodes], line=dict(width=2, color="#fff"))))
        st.plotly_chart(tema(fg.update_layout(title="🕸️ Jaringan produk yang dibeli bersamaan (tebal garis = lift, ukuran titik = penjualan)", xaxis=dict(visible=False), yaxis=dict(visible=False)), 560))
    t = R.copy(); t["Support"] *= 100; t["Confidence"] *= 100
    st.dataframe(t, hide_index=True, column_config={"Support": st.column_config.NumberColumn(format="%.2f%%"), "Confidence": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f%%"), "Lift": st.column_config.ProgressColumn(min_value=0, max_value=float(max(R.Lift.max(), 1)) if len(R) else 1, format="%.2f")})
    if len(h["segR"]): st.markdown("**Pola khas per segmen**"); st.dataframe(h["segR"].assign(Support=lambda d: d.Support * 100, Confidence=lambda d: d.Confidence * 100), hide_index=True, column_config={"Support": st.column_config.NumberColumn(format="%.2f%%"), "Confidence": st.column_config.NumberColumn(format="%.0f%%"), "Lift": st.column_config.NumberColumn(format="%.2f")})

with T[3]:
    a, b = st.columns([1.3, 1])
    a.plotly_chart(tema(px.scatter_3d(rfm.reset_index(), x="Recency", y="Frequency", z="Monetary", color="Segmen", color_discrete_map=SEGCOL, opacity=.8, title="🌌 Ruang RFM 3D (putar & zoom)").update_traces(marker_size=3).update_scenes(zaxis_type="log"), 520))
    rd = prof.copy(); rd["Kebaruan"] = (rd.Recency.max() - rd.Recency) / rd.Recency.max(); fr = go.Figure()
    for _, r in rd.iterrows():
        v = [r.Kebaruan, r.Frequency / rd.Frequency.max(), r.Monetary / rd.Monetary.max()]; fr.add_trace(go.Scatterpolar(r=v + v[:1], theta=["Kebaruan", "Frekuensi", "Nilai belanja", "Kebaruan"], fill="toself", name=r.Segmen, line=dict(color=SC(r.Segmen)), opacity=.7))
    b.plotly_chart(tema(fr.update_layout(title="🕸️ Sidik jari tiap segmen"), 520))
    dn = make_subplots(rows=1, cols=2, specs=[[{"type": "domain"}, {"type": "domain"}]], subplot_titles=["Porsi pelanggan", "Porsi belanja"])
    for i, c_ in enumerate(["Pelanggan", "Total_Belanja"]): dn.add_trace(go.Pie(labels=prof.Segmen, values=prof[c_], hole=.55, marker=dict(colors=[SC(s) for s in prof.Segmen]), sort=False), 1, i + 1)
    st.plotly_chart(tema(dn.update_layout(title="🍩 Siapa yang menghasilkan uang? (pelanggan vs belanja)"), 380))
    with st.expander("📐 Evaluasi pemilihan k (Elbow & Silhouette)"):
        fe = make_subplots(specs=[[{"secondary_y": True}]]); fe.add_trace(go.Scatter(x=ev.k, y=ev.inertia, name="Inertia", line=dict(color=BLUE)), secondary_y=False); fe.add_trace(go.Scatter(x=ev.k, y=ev.silhouette, name="Silhouette", line=dict(color=YEL)), secondary_y=True)
        st.plotly_chart(tema(fe, 340)); bs = ev.loc[ev.silhouette.idxmax()]; st.caption(f"Silhouette tertinggi di k={int(bs.k)} ({bs.silhouette:.2f}); dipakai k={h['k']} ({ev.set_index('k').silhouette[h['k']]:.2f}). Label segmen otomatis — periksa sebelum dipakai.")

with T[4]:
    st.subheader("🎯 Rencana aksi — seluruhnya diturunkan dari hasil analisis di atas")
    tot = prof.Total_Belanja.sum(); churnR = prof[prof.Segmen == "Berisiko Churn"].Recency.max() if (prof.Segmen == "Berisiko Churn").any() else None
    def aksi(r):
        p = w["seg_prod"].get(r.Segmen, "-")
        if r.Segmen == "Loyal Aktif": return ("🛡️ PERTAHANKAN", f"Pelanggan aktif (terakhir belanja {r.Recency:.0f} hari lalu, {r.Frequency:.0f}× belanja). Beri apresiasi: poin/keanggotaan dan akses awal untuk <b>{p}</b>, produk andalan segmen ini.")
        if r.Segmen == "Bernilai Tinggi Mulai Pasif": return ("⏰ REAKTIVASI PRIORITAS", f"Belanja median {rp(r.Monetary)} per pelanggan, tetapi terakhir belanja {r.Recency:.0f} hari lalu" + (f" (segmen churn: {churnR:.0f} hari)" if churnR else "") + f". Kirim pengingat/voucher personal untuk <b>{p}</b> sebelum mereka menyerupai segmen churn.")
        if r.Segmen == "Pelanggan Biasa (Potensial)": return ("📈 TINGKATKAN FREKUENSI", f"Rata-rata {r.Frequency:.0f}× belanja. Dorong kunjungan ulang lewat paket hemat dari aturan Apriori dan promo <b>{p}</b>.")
        if r.Segmen == "Berisiko Churn": return ("💌 WIN-BACK HEMAT", f"Hanya {r.Frequency:.0f}× belanja dan terakhir {r.Recency:.0f} hari lalu; kontribusi {r.Total_Belanja / tot:.1%}. Gunakan kampanye berbiaya rendah (mis. pesan otomatis soal <b>{p}</b>), bukan promo besar.")
        return ("🔍 TELAAH", f"Tentukan strategi sesuai profil: recency {r.Recency:.0f} hari, frekuensi {r.Frequency:.0f}.")
    cols = st.columns(2)
    for i, (_, r) in enumerate(prof.iterrows()):
        tg, tx = aksi(r)
        cols[i % 2].markdown(f'<div class="rec" style="--c:{SC(r.Segmen)}"><div class="h">{tg} · {r.Segmen}</div><div class="b"><div class="m"><span>👥 {int(r.Pelanggan)} pelanggan</span><span>💰 {r.Total_Belanja / tot:.0%} belanja</span><span>🕒 {r.Recency:.0f} hari</span><span>🔁 {r.Frequency:.0f}×</span></div>{tx}</div></div><br>', unsafe_allow_html=True)
    st.subheader("🛍️ Paket & penataan produk dari pola belanja")
    bc = st.columns(max(len(w["bundles"]), 1))
    for col, b_ in zip(bc, w["bundles"]):
        col.markdown(f'<div class="rec" style="--c:{YEL}"><div class="h">📦 {b_["Jika"]} + {b_["Maka"]}</div><div class="b"><div class="m"><span>confidence {b_["Confidence"]:.0%}</span><span>lift {b_["Lift"]:.2f}</span><span>{b_["Nota"]} nota</span></div>{b_["Confidence"]:.0%} nota berisi <b>{b_["Jika"]}</b> juga memuat <b>{b_["Maka"]}</b>. Masih ada <b>{b_["Pool"]} nota</b> berisi {b_["Jika"]} tanpa {b_["Maka"]} sebagai target cross-sell; rata-rata nilai {b_["Maka"]} per nota {rp(b_["NilaiNota"])}. Tempatkan berdekatan atau tawarkan sebagai paket.</div></div>', unsafe_allow_html=True)
    st.subheader("🗺️ Peta jalan 90 hari")
    seg1 = prof[prof.Segmen == "Bernilai Tinggi Mulai Pasif"]; s1 = seg1.iloc[0].Segmen if len(seg1) else prof.iloc[0].Segmen
    st.markdown(f"""<div class="tl" style="--c:{YEL}"><div style="--c:{MINT}"><b>Minggu 1–2 · Reaktivasi</b><br>Jalankan kampanye untuk segmen <b>{s1}</b> ({'belanja besar yang mulai pasif' if len(seg1) else 'segmen dengan total belanja terbesar'}).</div>
<div style="--c:{YEL}"><b>Minggu 3–4 · Paket pertama</b><br>{"Luncurkan paket <b>" + w["bundles"][0]["Jika"] + " + " + w["bundles"][0]["Maka"] + "</b> (lift " + f'{w["bundles"][0]["Lift"]:.2f}' + ")." if w["bundles"] else "Uji paket dari aturan terbaik."}</div>
<div style="--c:{BLUE}"><b>Bulan 2 · Dorong hari & bulan lemah</b><br>Penjualan terendah jatuh pada <b>{w["low_day"][0]}</b> dan bulan <b>{bln(w["low_month"][0])}</b>; jadwalkan promo di waktu serupa. Puncak ada pada {w["best_day"][0]} dan {bln(w["best_month"][0])}: pastikan stok <b>{w["top_prod"][0]}</b> aman. Kanal bayar dominan: <b>{w["top_pay"][0]}</b> ({w["top_pay"][1]:.0%}).</div>
<div style="--c:{VIO}"><b>Bulan 3 · Ukur & ulangi</b><br>Jalankan ulang analisis dengan data baru; bandingkan jumlah pelanggan tiap segmen dan nilai belanjanya.</div></div>""", unsafe_allow_html=True)
    st.caption("Ini usulan berbasis data, bukan prediksi. Dampak (mis. kenaikan penjualan) perlu diuji dan asumsinya harus dinyatakan terpisah dari fakta di atas.")

with T[5]:
    a, b, c_ = st.columns(3); a.markdown(kpi("Baris awal", f"{h['raw']:,}".replace(",", "."), "Data_Raw", RED), unsafe_allow_html=True); b.markdown(kpi("Baris bersih", f"{len(df):,}".replace(",", "."), "setelah preprocessing", MINT), unsafe_allow_html=True); c_.markdown(kpi("Total awal vs bersih", rj(w["total"]), f"awal {rj(h['au']['Total Line_Total (belum valid)'])} (belum valid)", YEL), unsafe_allow_html=True)
    st.write(""); st.dataframe(h["log"], hide_index=True)
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as xw:
        h["log"].to_excel(xw, sheet_name="Log_Preprocessing", index=False); df.to_excel(xw, sheet_name="Data_Clean", index=False); R.to_excel(xw, sheet_name="Aturan_Apriori", index=False); rfm.reset_index().to_excel(xw, sheet_name="RFM_KMeans", index=False); prof.to_excel(xw, sheet_name="Profil_Segmen", index=False)
    d1, d2 = st.columns(2); d1.download_button("⬇️ Unduh Data_Clean.csv", df.to_csv(index=False).encode(), "Data_Clean.csv", "text/csv"); d2.download_button("⬇️ Unduh Hasil_Analisis.xlsx", bio.getvalue(), "Hasil_Analisis.xlsx")
