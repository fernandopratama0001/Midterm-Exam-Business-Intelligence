"""Logika analisis: preprocessing, Apriori, RFM + K-Means. Murni pandas/numpy/scikit-learn."""
import itertools, numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def baca(file):
    xl = pd.ExcelFile(file)
    g = lambda n: xl.parse(n) if n in xl.sheet_names else None
    return (g('Data_Raw') if 'Data_Raw' in xl.sheet_names else xl.parse(0)), g('Data_Produk'), g('Data_Pelanggan')

def audit(raw):
    return {'Baris': len(raw), 'Kolom': raw.shape[1], 'Tanggal awal': str(raw.Transaction_Date.min()), 'Tanggal akhir': str(raw.Transaction_Date.max()),
            'Transaksi unik': raw.Transaction_ID.nunique(), 'Pelanggan unik': raw.Customer_ID.nunique(), 'Produk unik': raw.Product_Name.nunique(),
            'Baris duplikat': int(raw.duplicated().sum()), 'Total Line_Total (belum valid)': float(raw.Line_Total.sum())}

def preprocess(raw, cat=None, cust=None):
    """Mengembalikan (data_bersih, log). Data asli tidak diubah."""
    log = []; L = lambda m, a, n, b=None, s=None: log.append(dict(Masalah=m, Tindakan=a, Jumlah=int(n), Baris_Sebelum=b, Baris_Sesudah=s))
    df = raw.copy(); n0 = len(df); df = df.drop_duplicates(); L('Baris duplikat persis', 'Dihapus', n0 - len(df), n0, len(df))
    if cat is None:  # katalog diturunkan dari data bila sheet Data_Produk tidak ada
        g = df.groupby('Product_Name'); cat = pd.DataFrame({'Product_Name': g.size().index,
            'Product_ID': g.Product_ID.agg(lambda s: s.dropna().mode().iat[0] if s.notna().any() else None).values,
            'Category': g.Category.agg(lambda s: s.dropna().str.strip().str.title().mode().iat[0]).values,
            'Reference_Unit_Price_Rp': g.Unit_Price.agg(lambda s: s[(s > 0) & (s < 1e5)].median()).values})
    pm = cat.set_index('Product_Name'); ref = pm.Reference_Unit_Price_Rp
    k = (df.Product_ID.isna() | (df.Category != df.Product_Name.map(pm.Category))).sum()
    df['Product_ID'] = df.Product_Name.map(pm.Product_ID); df['Category'] = df.Product_Name.map(pm.Category)
    L('Product_ID kosong & kategori tidak konsisten', 'Diisi/dibakukan dari katalog produk', k)
    pay = df.Payment_Method.str.strip().str.upper().map({'TUNAI': 'Tunai', 'DEBIT': 'Debit', 'TRANSFER': 'Transfer', 'QRIS': 'QRIS'}).fillna('Tidak Diketahui')
    L('Metode bayar tidak konsisten / kosong', 'Dibakukan; kosong -> "Tidak Diketahui"', (pay != df.Payment_Method).sum()); df['Payment_Method'] = pay
    n = df.Customer_ID.isna().sum(); df['Customer_ID'] = df.groupby('Transaction_ID').Customer_ID.transform(lambda s: s.ffill().bfill())
    L('Customer_ID kosong', 'Dipulihkan dari baris lain pada nota yang sama', n - df.Customer_ID.isna().sum())
    cm = cust.set_index('Customer_ID') if cust is not None else None
    for c in ['Region', 'Customer_Type']:
        n = df[c].isna().sum()
        if cm is not None: df[c] = df[c].fillna(df.Customer_ID.map(cm[c]))
        df[c] = df[c].fillna('Tidak Diketahui'); L(f'{c} kosong', 'Diisi dari data pelanggan; sisanya "Tidak Diketahui"', n)
    rp = df.Product_Name.map(ref); bad = df.Unit_Price.isna() | (df.Unit_Price <= 0) | (df.Unit_Price / rp > 2) | (df.Unit_Price / rp < .5)
    df.loc[bad, 'Unit_Price'] = rp[bad]; L('Harga kosong/negatif/ekstrem', 'Diganti harga referensi', bad.sum())
    d = 1 - df.Discount_Rate.fillna(0); qb = df.Quantity.isna() | (df.Quantity <= 0) | (df.Quantity > 50)
    raw_q = df.Line_Total / (df.Unit_Price * d); est = raw_q.round()
    ok = qb & est.between(1, 10) & ((raw_q - est).abs() < .05); df.loc[ok, 'Quantity'] = est[ok]
    L('Quantity kosong/<=0/ekstrem', 'Dipulihkan dari Line_Total÷(harga×(1−diskon))', ok.sum())
    n = len(df); df = df[~(qb & ~ok)]; L('Quantity tak valid & tak bisa dipulihkan', 'Baris dihapus', n - len(df), n, len(df))
    d = 1 - df.Discount_Rate.fillna(0); old = df.Line_Total; df['Net_Sales'] = (df.Quantity * df.Unit_Price * d).round()
    L('Line_Total kosong/tidak sesuai rumus', 'Dihitung ulang = Qty×Harga×(1−Diskon)', (old.isna() | ((old - df.Net_Sales).abs() > 1)).sum())
    n = len(df); keys = [c for c in df.columns if c not in ('Quantity', 'Net_Sales', 'Line_Total')]
    df = df.drop(columns='Line_Total').groupby(keys, dropna=False, as_index=False).agg(Quantity=('Quantity', 'sum'), Net_Sales=('Net_Sales', 'sum'))
    L('Produk sama >1× dalam satu nota', 'Digabung', n - len(df), n, len(df))
    df['Transaction_Date'] = pd.to_datetime(df.Transaction_Date); df['Month'] = df.Transaction_Date.dt.to_period('M').astype(str)
    df['basket_size'] = df.groupby('Transaction_ID').Product_ID.transform('nunique')
    return df.reset_index(drop=True), pd.DataFrame(log)

def apriori(df, min_sup=.01, min_conf=.15, max_len=4):
    B = pd.crosstab(df.Transaction_ID, df.Product_Name).clip(upper=1).astype(bool); N = len(B); items = list(B.columns); M = B.values
    sup = {}; cur = [(i,) for i in range(len(items)) if M[:, i].mean() >= min_sup]
    for t in cur: sup[t] = M[:, t[0]].mean()
    k = 1
    while cur and k < max_len:
        cand = {tuple(sorted(set(a) | set(b))) for a in cur for b in cur if len(set(a) | set(b)) == k + 1}; cur = []
        for c in cand:
            s = M[:, list(c)].all(axis=1).mean()
            if s >= min_sup: sup[c] = s; cur.append(c)
        k += 1
    rules = []
    for it, s in sup.items():
        for r in range(1, len(it)) if len(it) > 1 else []:
            for a in itertools.combinations(it, r):
                c = tuple(x for x in it if x not in a); conf = s / sup[a]
                if conf >= min_conf: rules.append(dict(Jika=' + '.join(items[i] for i in a), Maka=' + '.join(items[i] for i in c), Support=s, Confidence=conf, Lift=conf / sup[c], Jumlah_Nota=int(round(s * N))))
    R = pd.DataFrame(rules, columns=['Jika', 'Maka', 'Support', 'Confidence', 'Lift', 'Jumlah_Nota'])
    return R.sort_values(['Lift', 'Confidence'], ascending=False).reset_index(drop=True), len(sup), B

def rfm_features(df):
    k = df.dropna(subset=['Customer_ID']); ref = k.Transaction_Date.max().normalize() + pd.Timedelta(days=1)
    rfm = k.groupby('Customer_ID').agg(Recency=('Transaction_Date', lambda s: (ref - s.max()).days), Frequency=('Transaction_ID', 'nunique'), Monetary=('Net_Sales', 'sum'))
    return rfm, ref

def evaluasi_k(rfm, kmin=2, kmax=8):
    X = StandardScaler().fit_transform(np.log1p(rfm[['Recency', 'Frequency', 'Monetary']])); ev = []
    for k in range(kmin, kmax + 1):
        km = KMeans(k, n_init=10, random_state=42).fit(X); ev.append(dict(k=k, inertia=km.inertia_, silhouette=silhouette_score(X, km.labels_)))
    return X, pd.DataFrame(ev)

def klaster(rfm, X, k):
    rfm = rfm.copy(); rfm['Cluster'] = KMeans(k, n_init=10, random_state=42).fit_predict(X)
    p = rfm.groupby('Cluster').agg(Pelanggan=('Recency', 'size'), Recency=('Recency', 'median'), Frequency=('Frequency', 'median'), Monetary=('Monetary', 'median'), Total_Belanja=('Monetary', 'sum'))
    churn = p.Recency.idxmax(); rest = p.drop(churn); loyal = rest.Recency.idxmin(); val = rest.drop(loyal).Monetary.idxmax() if len(rest) > 1 else None
    lab = {c: ('Berisiko Churn' if c == churn else 'Loyal Aktif' if c == loyal else 'Bernilai Tinggi Mulai Pasif' if c == val else 'Pelanggan Biasa (Potensial)' if len(rest) <= 3 else f'Segmen {c}') for c in p.index}
    rfm['Segmen'] = rfm.Cluster.map(lab); p['Segmen'] = p.index.map(lab)
    return rfm, p.sort_values('Total_Belanja', ascending=False)

def aturan_per_segmen(df, B, min_sup=.01, top=3):
    out = []
    for sg, g in df.groupby('Segmen'):
        Bs = B.loc[B.index.isin(g.Transaction_ID)]; ns = len(Bs)
        if ns < 100: continue
        M = Bs.values; rows = []
        for i, j in itertools.permutations(range(M.shape[1]), 2):
            s = (M[:, i] & M[:, j]).mean()
            if s >= min_sup: c = s / M[:, i].mean(); rows.append((sg, Bs.columns[i], Bs.columns[j], s, c, c / M[:, j].mean()))
        out += sorted(rows, key=lambda r: -r[5])[:top]
    return pd.DataFrame(out, columns=['Segmen', 'Jika', 'Maka', 'Support', 'Confidence', 'Lift'])

# ======================= Fitur lanjutan (v2) =======================
HARI = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
BULAN = {'januari': 1, 'jan': 1, 'februari': 2, 'feb': 2, 'maret': 3, 'mar': 3, 'april': 4, 'apr': 4, 'mei': 5, 'juni': 6, 'jun': 6, 'juli': 7, 'jul': 7,
         'agustus': 8, 'agu': 8, 'september': 9, 'sep': 9, 'oktober': 10, 'okt': 10, 'november': 11, 'nov': 11, 'desember': 12, 'des': 12}

def kualitas_mentah(raw):
    """Persentase baris Data_Raw yang tidak punya masalah (duplikat, kosong, nilai mustahil, penulisan tidak konsisten)."""
    core = ['Product_ID', 'Customer_ID', 'Region', 'Customer_Type', 'Quantity', 'Unit_Price', 'Line_Total', 'Payment_Method', 'Category', 'Product_Name']
    bad = raw.duplicated() | raw[core].isna().any(axis=1) | (raw.Quantity <= 0) | (raw.Quantity > 50) | (raw.Unit_Price <= 0) | (raw.Unit_Price > 1e5)
    for c in ['Category', 'Payment_Method']:
        s = raw[c].dropna(); canon = s.groupby(s.str.strip().str.lower()).agg(lambda x: x.mode().iat[0])
        bad |= raw[c].notna() & (raw[c] != raw[c].str.strip().str.lower().map(canon))
    return float(100 * (1 - bad.mean()))

def skor_rfm(rfm):
    """Skor 0-100 per dimensi (Recency dibalik: makin baru makin tinggi)."""
    s = pd.DataFrame(index=rfm.index)
    s['Recency'] = (1 - rfm.Recency.rank(pct=True)) * 100; s['Frequency'] = rfm.Frequency.rank(pct=True) * 100; s['Monetary'] = rfm.Monetary.rank(pct=True) * 100
    return s

def lift_matrix(B, items):
    M = B[items].values.astype(float); p = M.mean(axis=0); co = (M.T @ M) / len(M)
    L = co / np.outer(p, p); np.fill_diagonal(L, np.nan); return pd.DataFrame(L, index=items, columns=items)

def insight(df, R, prof):
    out = []; tot = df.Net_Sales.sum(); p = df.groupby('Product_Name').Net_Sales.sum().sort_values(ascending=False)
    out.append(('🏆', 'Produk andalan', f'{p.index[0]} menyumbang {p.iloc[0] / tot:.1%} penjualan; 3 produk teratas = {p.head(3).sum() / tot:.1%}.'))
    m = df.groupby('Month').Net_Sales.sum(); out.append(('📅', 'Musim penjualan', f'Puncak di {m.idxmax()} (Rp {m.max() / 1e6:.1f} jt), terendah {m.idxmin()} (Rp {m.min() / 1e6:.1f} jt).'))
    c = df.groupby('Category').Net_Sales.sum().sort_values(ascending=False); out.append(('🧺', 'Kategori dominan', f'{c.index[0]} = {c.iloc[0] / tot:.1%} dari total penjualan.'))
    if len(R): r = R.iloc[0]; out.append(('🔗', 'Pasangan terkuat', f'{r.Jika} → {r.Maka}: lift {r.Lift:.2f}, confidence {r.Confidence:.0%}.'))
    t = prof.iloc[0]; out.append(('👑', 'Segmen penyumbang terbesar', f'{t.Segmen}: {t.Total_Belanja / prof.Total_Belanja.sum():.0%} belanja dari {int(t.Pelanggan)} pelanggan (recency median {t.Recency:.0f} hari).'))
    wk = df.groupby(df.Transaction_Date.dt.dayofweek).Net_Sales.sum(); out.append(('🗓️', 'Hari tersibuk', f'{HARI[wk.idxmax()]} (Rp {wk.max() / 1e6:.1f} jt); tersepi {HARI[wk.idxmin()]}.'))
    return out

def tanya(df, R, teks):
    """Penjawab pertanyaan berbasis aturan kata kunci (BUKAN model bahasa). Mengembalikan (judul, jawaban, tabel, jenis)."""
    q = teks.lower(); f = df; filt = []
    for w, n in BULAN.items():
        if f'{w}' in q.replace(',', ' ').split():
            f = f[f.Transaction_Date.dt.month == n]; filt.append(f'bulan {w.title()}'); break
    for c in df.Category.unique():
        if c.lower() in q: f = f[f.Category == c]; filt.append(f'kategori {c}')
    for s in df.Segmen.unique():
        key = s.lower().split()[0]
        if key in q and key not in ('pelanggan',): f = f[f.Segmen == s]; filt.append(f'segmen {s}')
    prod = [p for p in df.Product_Name.unique() if p.lower() in q]; ket = ' · '.join(filt) or 'seluruh data'
    if f.empty: return 'Tidak ada data', 'Tidak ada transaksi yang cocok dengan filter pada pertanyaan Anda.', None, None
    if prod and any(k in q for k in ['bareng', 'bersama', 'kombinasi', 'bundling', 'pasangan', 'sering']):
        r = R[R.Jika.str.contains(prod[0]) | R.Maka.str.contains(prod[0])].head(8)
        if r.empty: return f'Pasangan {prod[0]}', f'Belum ada aturan untuk {prod[0]} pada ambang saat ini.', None, None
        r = r.assign(Aturan=r.Jika + ' → ' + r.Maka)[['Aturan', 'Lift', 'Confidence']]
        return f'Pasangan produk {prod[0]}', f'Ditemukan {len(r)} aturan; terkuat: {r.Aturan.iloc[0]} (lift {r.Lift.iloc[0]:.2f}).', r.set_index('Aturan')[['Lift']], 'bar'
    if any(k in q for k in ['tren', 'per bulan', 'bulanan', 'naik', 'turun']):
        t = f.groupby('Month').Net_Sales.sum().to_frame('Penjualan'); return f'Tren penjualan ({ket})', f'Total Rp {f.Net_Sales.sum():,.0f}; puncak {t.Penjualan.idxmax()}.'.replace(',', '.'), t, 'line'
    for kata, kol, jd in [('wilayah', 'Region', 'wilayah'), ('region', 'Region', 'wilayah'), ('bayar', 'Payment_Method', 'metode bayar'), ('kategori', 'Category', 'kategori'), ('segmen', 'Segmen', 'segmen'), ('tipe', 'Customer_Type', 'tipe pelanggan')]:
        if kata in q:
            t = f.groupby(kol).Net_Sales.sum().sort_values(ascending=False).to_frame('Penjualan'); return f'Penjualan per {jd} ({ket})', f'{t.index[0]} terbesar: {t.Penjualan.iloc[0] / t.Penjualan.sum():.1%}.', t, 'bar'
    if 'pelanggan' in q and any(k in q for k in ['top', 'terbesar', 'terbaik', 'loyal']):
        t = f.groupby('Customer_ID').Net_Sales.sum().nlargest(10).to_frame('Belanja'); return f'10 pelanggan terbesar ({ket})', f'Terbesar: {t.index[0]} (Rp {t.Belanja.iloc[0]:,.0f}).'.replace(',', '.'), t, 'bar'
    t = f.groupby('Product_Name').Net_Sales.sum().nlargest(10).to_frame('Penjualan'); return f'Produk terlaris ({ket})', f'{t.index[0]} memimpin dengan Rp {t.Penjualan.iloc[0]:,.0f}.'.replace(',', '.'), t, 'bar'

HARI = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

def wawasan(df, R, B, prof, rfm):
    """Semua angka untuk Temuan & Rekomendasi dihitung dari hasil analisis (tidak ada angka karangan)."""
    tot = df.Net_Sales.sum(); w = {'total': tot}
    pr = df.groupby('Product_Name').Net_Sales.sum().sort_values(ascending=False); w['top_prod'] = (pr.index[0], pr.iloc[0] / tot); w['top3'] = pr.head(3).sum() / tot
    ct = df.groupby('Category').Net_Sales.sum().sort_values(ascending=False); w['top_cat'] = (ct.index[0], ct.iloc[0] / tot)
    m = df.groupby('Month').Net_Sales.sum(); w['best_month'] = (m.idxmax(), m.max()); w['low_month'] = (m.idxmin(), m.min())
    hd = df.groupby(df.Transaction_Date.dt.dayofweek).Net_Sales.sum(); w['best_day'] = (HARI[hd.idxmax()], hd.max() / tot); w['low_day'] = (HARI[hd.idxmin()], hd.min() / tot)
    py = df.groupby('Payment_Method').Net_Sales.sum().sort_values(ascending=False); w['top_pay'] = (py.index[0], py.iloc[0] / tot)
    c = rfm.Monetary.sort_values(ascending=False); w['pareto'] = c.head(max(1, int(len(c) * .2))).sum() / c.sum()
    w['basket'] = df.drop_duplicates('Transaction_ID').basket_size.mean(); w['multi'] = (df.drop_duplicates('Transaction_ID').basket_size > 1).mean()
    sp = df.groupby(['Segmen', 'Product_Name']).Net_Sales.sum().reset_index().sort_values('Net_Sales', ascending=False).drop_duplicates('Segmen')
    w['seg_prod'] = dict(zip(sp.Segmen, sp.Product_Name))
    nota = df.groupby('Product_Name').Transaction_ID.nunique(); val = df.groupby('Product_Name').Net_Sales.sum() / nota
    bund, seen = [], set()
    for _, r in R.iterrows():
        if '+' in r.Jika or '+' in r.Maka: continue
        key = frozenset([r.Jika, r.Maka])
        if key in seen: continue
        seen.add(key); n_a = int(B[r.Jika].sum()); pool = int((B[r.Jika] & ~B[r.Maka]).sum())
        bund.append(dict(Jika=r.Jika, Maka=r.Maka, Confidence=r.Confidence, Lift=r.Lift, Nota=int(r.Jumlah_Nota), Pool=pool, NilaiNota=float(val[r.Maka])))
        if len(bund) == 3: break
    w['bundles'] = bund
    w['top_cust'] = rfm.sort_values('Monetary', ascending=False).head(5).reset_index()
    return w
