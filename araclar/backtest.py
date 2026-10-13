"""BIST 100 hisselerinde 24 strateji + 276 ikili kombini 4 Saat / Günlük / Haftalık
zaman dilimlerinde test eder ve her hisse için en iyisini veri/bist100_sonuclar.json'a yazar.

Strateji kuralları "0. OTOMATİK EN İYİ STRATEJİ - BIST.txt" (Pine) ile aynıdır.
Test kuralı: AL'da kapanıştan gir, SAT'ta (ya da en fazla MAX_BAR bar sonra) kapanıştan çık,
her işlemden KOMISYON düş.

Kullanım:
    python araclar/backtest.py              # Yahoo Finance'ten veri çeker
    python araclar/backtest.py --sentetik   # internetsiz deneme (rastgele veri)
"""
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import risk

KOK = Path(__file__).resolve().parent.parent
TEST_BAS = pd.Timestamp("2020-01-01")
MAX_BAR = 40
KOMISYON = 0.2  # %, al+sat toplam
MIN_ISLEM = 6
ORTAK_BAR = 3
ORTAK_ESIK = 4
ISINMA = 200  # göstergelerin oturması için testten önce gereken bar

ADLAR = ["01 RSI Karpuzlu", "02 Dip Bulucu (Banker)", "03 Dip Bulucu-2 (VixFix)", "04 AlphaTrend", "05 SuperTrend",
         "06 AlphaTrend+SuperTrend", "07 Parabolic SAR", "08 MACD Dip", "09 ALMA", "10 T3 Tillson",
         "11 Bollinger Orta Bant", "12 Bollinger20 x EMA50", "13 EMA 5x13", "14 EMA 5x22", "15 WMA 9x15",
         "16 SMMA 21x55", "17 Darvas Kutusu", "18 Fisher Dip", "19 CCI Dip", "20 TSI Dip",
         "21 MACD Kesişimi", "22 Erik Kombo", "23 EMA Kombo", "24 Bollinger Kombo", "25 Ortak Karar"]
# Pine'daki zaman dilimi sırası: 0=1 Saat, 1=4 Saat, 2=Günlük, 3=Haftalık
TF_ADLARI = {1: "4 Saat", 2: "Günlük", 3: "Haftalık"}

ADAYLAR = [(k, -1) for k in range(25)] + [(i, j) for i in range(23) for j in range(i + 1, 24)]


def aday_adi(c):
    a, b = ADAYLAR[c]
    return ADLAR[a] if b < 0 else f"{ADLAR[a]} + {ADLAR[b]}"


# ───────────────────────────── Pine ta.* karşılıkları ─────────────────────────────
def _s(x):
    return pd.Series(np.asarray(x, dtype=float))


def sma(x, n):
    return _s(x).rolling(n).mean().values


def _ozyineli(x, n, alpha):
    """Pine ema/rma: ilk değer SMA ile başlar."""
    x = np.asarray(x, dtype=float)
    out = np.full(len(x), np.nan)
    tohum = sma(x, n)
    onceki = np.nan
    for i in range(len(x)):
        if np.isnan(onceki):
            if not np.isnan(tohum[i]):
                onceki = tohum[i]
                out[i] = onceki
        else:
            if not np.isnan(x[i]):
                onceki = alpha * x[i] + (1 - alpha) * onceki
            out[i] = onceki
    return out


def ema(x, n):
    return _ozyineli(x, n, 2.0 / (n + 1))


def rma(x, n):
    return _ozyineli(x, n, 1.0 / n)


def wma(x, n):
    w = np.arange(1, n + 1, dtype=float)
    return _s(x).rolling(n).apply(lambda v: np.dot(v, w) / w.sum(), raw=True).values


def hma(x, n):
    return wma(2 * wma(x, n // 2) - wma(x, n), int(math.floor(math.sqrt(n))))


def highest(x, n):
    return _s(x).rolling(n).max().values


def lowest(x, n):
    return _s(x).rolling(n).min().values


def stdev(x, n):
    return _s(x).rolling(n).std(ddof=0).values


def gecikme(x, k=1):
    x = np.asarray(x)
    out = np.empty_like(x, dtype=float) if x.dtype != bool else np.zeros(len(x), dtype=bool)
    if x.dtype == bool:
        out[k:] = x[:-k]
        return out
    out[:] = np.nan
    out[k:] = x[:-k]
    return out


def degisim(x):
    x = np.asarray(x, dtype=float)
    return x - gecikme(x)


def yukari_kes(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    a1, b1 = gecikme(a), gecikme(b)
    with np.errstate(invalid="ignore"):
        r = (a > b) & (a1 <= b1)
    return np.nan_to_num(r, nan=0).astype(bool)


def asagi_kes(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    a1, b1 = gecikme(a), gecikme(b)
    with np.errstate(invalid="ignore"):
        r = (a < b) & (a1 >= b1)
    return np.nan_to_num(r, nan=0).astype(bool)


def buyuk(a, b):
    with np.errstate(invalid="ignore"):
        return np.nan_to_num(np.asarray(a, float) > np.asarray(b, float), nan=0).astype(bool)


def buyuk_esit(a, b):
    with np.errstate(invalid="ignore"):
        return np.nan_to_num(np.asarray(a, float) >= np.asarray(b, float), nan=0).astype(bool)


def kucuk(a, b):
    with np.errstate(invalid="ignore"):
        return np.nan_to_num(np.asarray(a, float) < np.asarray(b, float), nan=0).astype(bool)


def kucuk_esit(a, b):
    with np.errstate(invalid="ignore"):
        return np.nan_to_num(np.asarray(a, float) <= np.asarray(b, float), nan=0).astype(bool)


def barssince(kosul):
    out = np.full(len(kosul), np.nan)
    son = -1
    for i, k in enumerate(kosul):
        if k:
            son = i
        if son >= 0:
            out[i] = i - son
    return out


def valuewhen(kosul, deger):
    out = np.full(len(kosul), np.nan)
    son = np.nan
    for i, k in enumerate(kosul):
        if k:
            son = deger[i]
        out[i] = son
    return out


def rsi(x, n):
    d = degisim(x)
    up = rma(np.where(np.isnan(d), np.nan, np.maximum(d, 0)), n)
    dn = rma(np.where(np.isnan(d), np.nan, -np.minimum(d, 0)), n)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = 100 - 100 / (1 + up / dn)
    r = np.where(dn == 0, 100.0, np.where(up == 0, 0.0, r))
    return np.where(np.isnan(up) | np.isnan(dn), np.nan, r)


def mfi(src, hacim, n):
    d = degisim(src)
    ust = _s(hacim * np.where(kucuk_esit(d, 0), 0, src)).rolling(n).sum().values
    alt = _s(hacim * np.where(np.nan_to_num(d, nan=1) >= 0, 0, src)).rolling(n).sum().values
    d_nan = np.isnan(d)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = 100 - 100 / (1 + ust / alt)
    r[d_nan] = np.nan
    return r


def macd(x, hizli, yavas, sinyal):
    m = ema(x, hizli) - ema(x, yavas)
    return m, ema(m, sinyal)


def cci(x, n):
    ort = sma(x, n)
    sapma = _s(x).rolling(n).apply(lambda v: np.mean(np.abs(v - v.mean())), raw=True).values
    with np.errstate(divide="ignore", invalid="ignore"):
        return (x - ort) / (0.015 * sapma)


def tsi(x, kisa, uzun):
    d = degisim(x)
    pay = ema(ema(d, uzun), kisa)
    payda = ema(ema(np.abs(d), uzun), kisa)
    with np.errstate(divide="ignore", invalid="ignore"):
        return pay / payda


def alma(x, n, ofset, sigma):
    m = ofset * (n - 1)
    s = n / sigma
    w = np.exp(-((np.arange(n) - m) ** 2) / (2 * s * s))
    return _s(x).rolling(n).apply(lambda v: np.dot(v, w) / w.sum(), raw=True).values


def t3(x, n, a):
    e1 = ema(x, n); e2 = ema(e1, n); e3 = ema(e2, n); e4 = ema(e3, n); e5 = ema(e4, n); e6 = ema(e5, n)
    c1 = -a ** 3
    c2 = 3 * a * a + 3 * a ** 3
    c3 = -6 * a * a - 3 * a - 3 * a ** 3
    c4 = 1 + 3 * a + a ** 3 + 3 * a * a
    return c1 * e6 + c2 * e5 + c3 * e4 + c4 * e3


def tr(h, l, c):
    c1 = gecikme(c)
    r = np.maximum(h - l, np.maximum(np.abs(h - c1), np.abs(l - c1)))
    r[0] = h[0] - l[0]
    return r


def supertrend(h, l, c, carpan, n):
    src = (h + l) / 2
    atr = rma(tr(h, l, c), n)
    ust = src + carpan * atr
    alt = src - carpan * atr
    yon = np.full(len(c), np.nan)
    st = np.full(len(c), np.nan)
    for i in range(len(c)):
        if i > 0:
            p_alt = 0.0 if np.isnan(alt[i - 1]) else alt[i - 1]
            p_ust = 0.0 if np.isnan(ust[i - 1]) else ust[i - 1]
            if not (alt[i] > p_alt or c[i - 1] < p_alt):
                alt[i] = p_alt
            if not (ust[i] < p_ust or c[i - 1] > p_ust):
                ust[i] = p_ust
        if i == 0 or np.isnan(atr[i - 1]):
            yon[i] = 1
        elif st[i - 1] == ust[i - 1]:
            yon[i] = -1 if c[i] > ust[i] else 1
        else:
            yon[i] = 1 if c[i] < alt[i] else -1
        st[i] = alt[i] if yon[i] == -1 else ust[i]
    return st, yon


def sar(h, l, c, bas, artis, tavan):
    out = np.full(len(c), np.nan)
    sonuc = np.nan; uc = np.nan; ivme = np.nan; asagida = False
    for i in range(len(c)):
        ilk = False
        if i == 1:
            if c[1] > c[0]:
                asagida = True; uc = h[1]; sonuc = l[0]
            else:
                asagida = False; uc = l[1]; sonuc = h[0]
            ilk = True; ivme = bas
        if i == 0:
            continue
        sonuc = sonuc + ivme * (uc - sonuc)
        if asagida:
            if sonuc > l[i]:
                ilk = True; asagida = False; sonuc = max(h[i], uc); uc = l[i]; ivme = bas
        else:
            if sonuc < h[i]:
                ilk = True; asagida = True; sonuc = min(l[i], uc); uc = h[i]; ivme = bas
        if not ilk:
            if asagida:
                if h[i] > uc:
                    uc = h[i]; ivme = min(ivme + artis, tavan)
            else:
                if l[i] < uc:
                    uc = l[i]; ivme = min(ivme + artis, tavan)
        if asagida:
            sonuc = min(sonuc, l[i - 1])
            if i > 1:
                sonuc = min(sonuc, l[i - 2])
        else:
            sonuc = max(sonuc, h[i - 1])
            if i > 1:
                sonuc = max(sonuc, h[i - 2])
        out[i] = sonuc
    return out


def durum(al, sat):
    """Pine f_durum: AL'da gir, SAT'ta ya da MAX_BAR dolunca çık."""
    poz = np.zeros(len(al), dtype=bool)
    p = False; giris = 0
    for i in range(len(al)):
        if p and (sat[i] or i - giris >= MAX_BAR):
            p = False
        elif al[i] and not p:
            p = True; giris = i
        poz[i] = p
    return poz


# ───────────────────────────── 24 strateji ─────────────────────────────
def sinyaller(df):
    """24 stratejinin AL (b) ve SAT (s) sinyalleri: {1..24: bool dizisi}."""
    o, h, l, c, v = (df[k].to_numpy(dtype=float) for k in ("Open", "High", "Low", "Close", "Volume"))
    hl2 = (h + l) / 2
    hlc3 = (h + l + c) / 3
    ema5, ema13, ema14, ema22, ema34, ema50 = (ema(c, n) for n in (5, 13, 14, 22, 34, 50))
    sma10, sma20, sma200 = sma(c, 10), sma(c, 20), sma(c, 200)
    rsi14 = rsi(c, 14)
    mfi14 = mfi(hlc3, v, 14)
    mL, mS = macd(c, 12, 26, 9)
    m2L, m2S = macd(c, 10, 20, 9)
    b, s = {}, {}

    rk = rsi(c, 22); rke = ema(rk, 66)
    b[1], s[1] = yukari_kes(rk, rke), asagi_kes(rk, rke)

    with np.errstate(divide="ignore", invalid="ignore"):
        st27 = (c - lowest(l, 27)) / (highest(h, 27) - lowest(l, 27)) * 100

    def xsa(src, n, w):
        m = sma(src, n)
        out = np.full(len(src), np.nan)
        onc = np.nan
        for i in range(len(src)):
            onc = m[i] if np.isnan(onc) else (src[i] * w + onc * (n - w)) / n
            out[i] = onc
        return out

    fx1 = xsa(st27, 5, 1); fx2 = xsa(fx1, 3, 1)
    fon = (3 * fx1 - 2 * fx2 - 50) * 1.032 + 50
    typ = (2 * c + h + l + o) / 5
    lol, hoh = lowest(l, 34), highest(h, 34)
    with np.errstate(divide="ignore", invalid="ignore"):
        boga = ema((typ - lol) / (hoh - lol) * 100, 13)
    b[2] = yukari_kes(fon, boga) & kucuk(boga, 25)
    s[2] = asagi_kes(fon, boga)

    tepe = highest(c, 22)
    wvf = (tepe - l) / tepe * 100
    wust = sma(wvf, 20) + 2.0 * stdev(wvf, 20)
    wyuk = highest(wvf, 50) * 0.85
    wdip = buyuk_esit(wvf, wust) | buyuk_esit(wvf, wyuk)
    b[3] = wdip & ~gecikme(wdip); s[3] = np.zeros(len(c), bool)

    at_atr = sma(tr(h, l, c), 14)
    kosul = np.nan_to_num(mfi14, nan=-1) >= 50
    alpha = np.full(len(c), np.nan)
    for i in range(len(c)):
        onc = alpha[i - 1] if i > 0 and not np.isnan(alpha[i - 1]) else 0.0  # Pine nz(alpha[1])
        if np.isnan(at_atr[i]):
            continue
        if kosul[i]:
            u = l[i] - at_atr[i]
            alpha[i] = onc if u < onc else u
        else:
            d = h[i] + at_atr[i]
            alpha[i] = onc if d > onc else d
    a2 = gecikme(alpha, 2)
    al_h, sat_h = yukari_kes(alpha, a2), asagi_kes(alpha, a2)
    k1, k2 = barssince(al_h), barssince(sat_h)
    o1, o2 = barssince(gecikme(al_h)), barssince(gecikme(sat_h))
    b[4] = al_h & buyuk(o1, k2); s[4] = sat_h & buyuk(o2, k1)
    at_yuk = np.zeros(len(c), bool); dur = False
    for i in range(len(c)):
        if b[4][i]:
            dur = True
        if s[4][i]:
            dur = False
        at_yuk[i] = dur

    st_deger, st_yon = supertrend(h, l, c, 3.0, 10)
    st_yuk = st_yon < 0
    b[5], s[5] = st_yuk & ~gecikme(st_yuk), ~st_yuk & gecikme(st_yuk)

    ikisi = at_yuk & st_yuk
    b[6], s[6] = ikisi & ~gecikme(ikisi), ~ikisi & gecikme(ikisi)

    ps = sar(h, l, c, 0.02, 0.02, 0.2)
    pyon = np.where(buyuk(c, ps), 1, -1)
    p1 = gecikme(pyon.astype(float))
    b[7], s[7] = (pyon == 1) & (p1 == -1), (pyon == -1) & (p1 == 1)

    b[8] = yukari_kes(mL, mS) & kucuk_esit(mL, 0); s[8] = asagi_kes(mL, mS)

    al_ = alma(c, 14, 0.85, 6)
    ay = buyuk_esit(al_, gecikme(al_))
    b[9], s[9] = ay & ~gecikme(ay), ~ay & gecikme(ay)

    t3_ = t3((h + l + 2 * c) / 4, 8, 0.7)
    ty = buyuk(t3_, gecikme(t3_))
    b[10], s[10] = ty & ~gecikme(ty), ~ty & gecikme(ty)

    b[11], s[11] = yukari_kes(c, sma20), asagi_kes(c, sma20)
    b[12], s[12] = yukari_kes(sma20, ema50), asagi_kes(sma20, ema50)
    b[13], s[13] = yukari_kes(ema5, ema13), asagi_kes(ema5, ema13)
    b[14], s[14] = yukari_kes(ema5, ema22), asagi_kes(ema5, ema22)
    w9, w15 = wma(c, 9), wma(c, 15)
    b[15], s[15] = yukari_kes(w9, w15), asagi_kes(w9, w15)
    r21, r55 = rma(c, 21), rma(c, 55)
    b[16], s[16] = yukari_kes(r21, r55), asagi_kes(r21, r55)

    dLL = lowest(l, 7); dK1 = highest(h, 7); dK2 = highest(h, 6); dK3 = highest(h, 5)
    yeni_tepe = buyuk(h, gecikme(dK1))
    dNH = valuewhen(yeni_tepe, h)
    kutu = (barssince(yeni_tepe) == 5) & buyuk(dK2, dK3)
    dUst = valuewhen(kutu, dNH); dAlt = valuewhen(kutu, dLL)
    b[17], s[17] = yukari_kes(c, dUst), asagi_kes(c, dAlt)

    fH, fL = highest(hl2, 7), lowest(hl2, 7)
    fd = np.zeros(len(c)); fi = np.zeros(len(c))
    for i in range(len(c)):
        pd_ = fd[i - 1] if i > 0 and not np.isnan(fd[i - 1]) else 0.0
        with np.errstate(divide="ignore", invalid="ignore"):
            x = 0.66 * ((hl2[i] - fL[i]) / (fH[i] - fL[i]) - 0.5) + 0.67 * pd_
        if not np.isnan(x):
            x = 0.999 if x > 0.99 else (-0.999 if x < -0.99 else x)
        fd[i] = x
        pf = fi[i - 1] if i > 0 and not np.isnan(fi[i - 1]) else 0.0
        fi[i] = 0.5 * math.log((1 + x) / (1 - x)) + 0.5 * pf if not np.isnan(x) else np.nan
    ft = gecikme(fi)
    b[18] = yukari_kes(fi, ft) & kucuk_esit(ft, -1.5)
    s[18] = asagi_kes(fi, ft) & buyuk_esit(ft, 1.5)

    cc = cci(hlc3, 20)
    b[19], s[19] = yukari_kes(cc, np.full(len(c), -100.0)), asagi_kes(cc, np.full(len(c), 100.0))

    ts = tsi(c, 3, 9); ts1 = gecikme(ts)
    b[20] = kucuk_esit(ts, -0.8) & buyuk(ts1, -0.8)
    s[20] = buyuk_esit(ts, 0.8) & kucuk(ts1, 0.8)

    b[21], s[21] = yukari_kes(mL, mS), asagi_kes(mL, mS)

    don9 = (highest(h, 9) + lowest(l, 9)) / 2
    kij26 = (highest(h, 26) + lowest(l, 26)) / 2
    b[22] = (yukari_kes(ema5, sma10) & buyuk(c, don9) & buyuk(mL, mS) & buyuk(rsi(c, 5), rsi(c, 9))
             & buyuk(mfi14, 50) & buyuk(c, hma(c, 9)) & buyuk(c, kij26))
    s[22] = asagi_kes(ema5, sma10)
    b[23] = yukari_kes(ema5, ema14) & buyuk(c, ema34) & buyuk(m2L, m2S) & buyuk(rsi14, 50)
    s[23] = asagi_kes(ema5, ema14)
    b[24] = yukari_kes(c, sma20) & buyuk_esit(c, sma200) & buyuk(m2L, m2S)
    s[24] = asagi_kes(c, sma20)
    return b, s


def ortak_karar(b, s, adet):
    """Son ORTAK_BAR bar içinde en az ORTAK_ESIK strateji aynı yönde sinyal verdiyse AL/SAT."""
    n = len(b[1])
    son_al = np.full(adet, -100000); son_sat = np.full(adet, -100000)
    al_say = np.zeros(n, int); sat_say = np.zeros(n, int)
    for i in range(n):
        for k in range(adet):
            if b[k + 1][i]:
                son_al[k] = i
            if s[k + 1][i]:
                son_sat[k] = i
        al_say[i] = int(np.sum(i - son_al < ORTAK_BAR))
        sat_say[i] = int(np.sum(i - son_sat < ORTAK_BAR))
    a1 = np.nan_to_num(gecikme(al_say.astype(float)))
    s1 = np.nan_to_num(gecikme(sat_say.astype(float)))
    return ((al_say >= ORTAK_ESIK) & (a1 < ORTAK_ESIK) & (al_say > sat_say),
            (sat_say >= ORTAK_ESIK) & (s1 < ORTAK_ESIK) & (sat_say > al_say))


def stratejiler(df):
    """25 adayın (24 strateji + ortak karar) pozisyon durumları."""
    b, s = sinyaller(df)
    b[25], s[25] = ortak_karar(b, s, 24)
    return np.array([durum(b[k], s[k]) for k in range(1, 26)])


# ───────────────────────────── test ─────────────────────────────
def islemler(durumlar, kapanis, bas_i):
    """Durum dizisinden (giriş, çıkış) indekslerini çıkarır; girişi bas_i'den önce olanları atar."""
    once = np.concatenate([[False], durumlar[:-1]])
    giris = np.flatnonzero(durumlar & ~once)
    cikis = np.flatnonzero(~durumlar & once)
    sonuc = []
    j = 0
    for g in giris:
        while j < len(cikis) and cikis[j] <= g:
            j += 1
        if j >= len(cikis):
            break
        if g >= bas_i:
            sonuc.append((g, cikis[j]))
    return sonuc


EGITIM_ORAN = 0.70     # seçim dönemin ilk %70'inde yapılır, son %30 kontrol (saf test)
MIN_ISLEM_KONTROL = 2
ILK_K = 10              # risk modları en iyi kaç aday için denensin


def atr14(df):
    h, l, c = (df[k].to_numpy(float) for k in ("High", "Low", "Close"))
    return rma(tr(h, l, c), 14)


def _olc(r, gun):
    if len(r) == 0:
        return {"islem": 0, "kazanma": 0.0, "toplam": 0.0, "yillik": 0.0}
    ser = float(np.prod(1 + r / 100))
    return {"islem": int(len(r)), "kazanma": round(float((r > 0).mean() * 100), 1),
            "toplam": round((ser - 1) * 100, 1),
            "yillik": round(((ser ** (365.25 / max(gun, 1)) - 1) * 100) if ser > 0 else -100.0, 1)}


def zaman_dilimi_test(df, tf):
    poz = stratejiler(df)
    o, h, l, kapanis = (df[x].to_numpy(float) for x in ("Open", "High", "Low", "Close"))
    atr = atr14(df)
    zaman = df.index
    bas_i = max(ISINMA, int(np.searchsorted(zaman, TEST_BAS)))
    if bas_i >= len(df) - 30:
        return []
    bolme = bas_i + int((len(df) - bas_i) * EGITIM_ORAN)
    gun = max((zaman[-1] - zaman[bas_i]).days, 1)
    gun_e = max((zaman[bolme] - zaman[bas_i]).days, 1)
    gun_k = max((zaman[-1] - zaman[bolme]).days, 1)
    al_tut = (kapanis[-1] / kapanis[bas_i] - 1) * 100
    al_tut_k = (kapanis[-1] / kapanis[bolme] - 1) * 100
    son_yil_bas = zaman[-1] - pd.Timedelta(days=365)

    def degerlendir(c, mod):
        a, b = ADAYLAR[c]
        d = poz[a] if b < 0 else (poz[a] & poz[b])
        g, k, f, n = risk.risk_islemler(d, o, h, l, kapanis, atr, bas_i, mod)
        if len(g) < MIN_ISLEM:
            return None
        r = (f / kapanis[g] - 1) * 100 - KOMISYON
        egitim = g < bolme
        if egitim.sum() < MIN_ISLEM - 1 or (~egitim).sum() < MIN_ISLEM_KONTROL:
            return None
        o_e, o_k, o_t = _olc(r[egitim], gun_e), _olc(r[~egitim], gun_k), _olc(r, gun)
        yil = zaman[k] >= son_yil_bas
        ser_y = float(np.prod(1 + r[yil] / 100)) if yil.any() else 1.0
        return {
            "aday": c, "aday_ab": [a, b], "ad": aday_adi(c), "tf": tf, "tf_ad": TF_ADLARI[tf],
            "mod": list(mod), "mod_ad": risk.mod_adi(mod),
            "skor": o_e["yillik"],                      # seçim SADECE eğitim dönemine göre
            "islem": o_t["islem"], "kazanma": o_t["kazanma"], "ortalama": round(float(r.mean()), 2),
            "toplam": o_t["toplam"], "yillik": o_t["yillik"], "son_yil": round((ser_y - 1) * 100, 1),
            "al_tut": round(float(al_tut), 1), "baslangic": str(zaman[bas_i].date()),
            "kontrol_bas": str(zaman[bolme].date()), "egitim": o_e,
            "kontrol": {**o_k, "al_tut": round(float(al_tut_k), 1)},
            "stop_cikis": int((n == 1).sum()), "hedef_cikis": int((n == 2).sum()),
        }

    # 1) tüm adaylar sadece sinyal çıkışıyla
    tum = [x for x in (degerlendir(c, risk.MODLAR[0]) for c in range(len(ADAYLAR))) if x]
    # 2) eğitimde en iyi ILK_K aday için stop / hedef / iz stop ayarlarını dene (parametre iyileştirme)
    tum.sort(key=lambda x: x["skor"], reverse=True)
    ek = []
    for x in tum[:ILK_K]:
        for mod in risk.MODLAR[1:]:
            y = degerlendir(x["aday"], mod)
            if y:
                ek.append(y)
    return tum + ek


# ───────────────────────────── veri ─────────────────────────────
def dort_saatlik(df1s):
    """1 saatlik veriyi BIST 4 saatlik mumlarına çevirir (10:00-14:00, 14:00-18:00)."""
    df = df1s.copy()
    idx = df.index.tz_convert("Europe/Istanbul") if df.index.tz is not None else df.index
    df.index = idx
    anahtar = [d.replace(hour=10 if d.hour < 14 else 14, minute=0, second=0) for d in idx]
    g = df.groupby(anahtar)
    out = pd.DataFrame({"Open": g["Open"].first(), "High": g["High"].max(), "Low": g["Low"].min(),
                        "Close": g["Close"].last(), "Volume": g["Volume"].sum()})
    out.index = pd.DatetimeIndex(out.index).tz_localize(None)
    return out


def temizle(df):
    if df is None or df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    df = df[df["Close"] > 0]
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    return df


def yahoo_veri(kod):
    import yfinance as yf
    sembol = f"{kod}.IS"
    sonuc = {}
    for deneme in range(3):
        try:
            g = yf.download(sembol, start="2019-01-01", interval="1d", auto_adjust=True, progress=False)
            h = yf.download(sembol, start="2017-06-01", interval="1wk", auto_adjust=True, progress=False)
            s = yf.download(sembol, period="730d", interval="1h", auto_adjust=True, progress=False)
            if isinstance(s.columns, pd.MultiIndex):
                s.columns = s.columns.get_level_values(0)
            sonuc[2] = temizle(g)
            sonuc[3] = temizle(h)
            sonuc[1] = dort_saatlik(s[["Open", "High", "Low", "Close", "Volume"]].dropna()) if not s.empty else None
            return sonuc
        except Exception as e:  # ağ/limit hatası: biraz bekleyip tekrar dene
            print(f"  {kod}: hata ({e}), tekrar deneniyor", flush=True)
            time.sleep(5 * (deneme + 1))
    return sonuc


def sentetik_veri(kod):
    rng = np.random.default_rng(abs(hash(kod)) % 2**32)

    def uret(n, frekans, bas):
        idx = pd.date_range(bas, periods=n, freq=frekans)
        getiri = rng.normal(0.0008, 0.02, n)
        c = 10 * np.exp(np.cumsum(getiri))
        o = c * (1 + rng.normal(0, 0.005, n))
        h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.01, n)))
        l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.01, n)))
        v = rng.integers(1e5, 1e7, n).astype(float)
        return pd.DataFrame({"Open": o, "High": h, "Low": l, "Close": c, "Volume": v}, index=idx)

    return {2: uret(1900, "B", "2019-01-01"), 3: uret(470, "W", "2017-06-01"), 1: uret(1000, "12h", "2024-10-01")}


def main():
    sentetik = "--sentetik" in sys.argv
    kodlar = [x.strip() for x in (KOK / "araclar" / "bist100.txt").read_text(encoding="utf-8").splitlines()
              if x.strip() and not x.startswith("#")]
    if "--ilk" in sys.argv:
        kodlar = kodlar[: int(sys.argv[sys.argv.index("--ilk") + 1])]
    hedef = KOK / "veri" / ("deneme_sonuclar.json" if sentetik else "bist100_sonuclar.json")
    eski = json.loads(hedef.read_text(encoding="utf-8")) if hedef.exists() and not sentetik else None
    bugun = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    hisseler, karne = {}, []
    for kod in kodlar:
        t0 = time.time()
        veri = sentetik_veri(kod) if sentetik else yahoo_veri(kod)
        # canlı karne: önceki seçimin o tarihten bu yana gerçek sonucu
        if eski and kod in eski.get("hisseler", {}):
            e0 = dict(eski["hisseler"][kod]["en_iyi"])
            e0.setdefault("aday_ab", list(ADAYLAR[e0["aday"]]))
            e0.setdefault("secim_tarihi", eski["tarih"])
            try:
                satir = risk.karne_satiri(kod, e0, veri, KOMISYON, stratejiler, atr14)
                if satir:
                    karne.append(satir)
            except Exception as hata:  # karne asıl testi durdurmasın
                print(f"  {kod}: karne hesaplanamadı ({hata})", flush=True)
        tum = []
        for tf in (1, 2, 3):
            df = veri.get(tf)
            if df is not None and len(df) > ISINMA + 50:
                tum += zaman_dilimi_test(df, tf)
        if not tum:
            print(f"{kod}: veri yok/yetersiz, atlandı", flush=True)
            continue
        # seçim yalnızca eğitim dönemine göre (kontrol dönemi seçimi etkilemez)
        tum.sort(key=lambda x: x["skor"], reverse=True)
        tum[0]["secim_tarihi"] = bugun
        hisseler[kod] = {"en_iyi": tum[0], "ilk5": tum[:5]}
        e = tum[0]
        print(f"{kod}: {e['ad']} • {e['tf_ad']} • {e['mod_ad']} • eğitim yıllık %{e['skor']} • "
              f"kontrol {e['kontrol']['toplam']:+.1f}% ({time.time() - t0:.1f} sn)", flush=True)
    if not hisseler:
        sys.exit("Hiçbir hisse için sonuç üretilemedi; eski sonuçlar korunuyor.")
    cikti = {
        "tarih": bugun,
        "ayarlar": {"test_bas": str(TEST_BAS.date()), "max_bar": MAX_BAR, "komisyon": KOMISYON,
                    "min_islem": MIN_ISLEM, "egitim_orani": EGITIM_ORAN,
                    "cikis_modlari": [risk.mod_adi(m) for m in risk.MODLAR],
                    "olcut": "yalnızca eğitim dönemi yıllık getirisi; kontrol dönemi saf test"},
        "sentetik": sentetik,
        "hisseler": hisseler,
    }
    hedef.parent.mkdir(exist_ok=True)
    hedef.write_text(json.dumps(cikti, ensure_ascii=False, indent=1), encoding="utf-8")
    if not sentetik:
        satirlar = [f"# BIST 100 en iyi strateji/kombin listesi ({cikti['tarih']})", "",
                    "Seçim yalnızca dönemin ilk %70'ine (eğitim) bakılarak yapıldı; 24 strateji + 276 kombin, sonra en iyi 10 aday için "
                    "11 farklı stop / hedef / iz stop ayarı denendi. **Kontrol** = seçimde hiç kullanılmayan son %30. "
                    "Komisyon %0,2 düşülmüş. Karar: Al-Tut'u geçiyor mu, kazanma ≥ %50 mi, kontrol döneminde kârda mı (3 şart).", "",
                    "| Hisse | En iyi strateji / kombin | Zaman | Çıkış | İşlem | Kazanma | Toplam | Al-Tut | Kontrol | Karar |",
                    "|---|---|---|---|---|---|---|---|---|---|"]
        for kod, v in sorted(hisseler.items(), key=lambda kv: -kv[1]["en_iyi"]["kontrol"]["toplam"]):
            e = v["en_iyi"]
            puan = (e["toplam"] > e["al_tut"]) + (e["kazanma"] >= 50) + (e["kontrol"]["toplam"] > 0)
            karar = ["ZAYIF", "ZAYIF", "ORTA", "GÜÇLÜ"][puan]
            satirlar.append(f"| {kod} | {e['ad']} | {e['tf_ad']} | {e['mod_ad']} | {e['islem']} | %{e['kazanma']:.0f} | "
                            f"{e['toplam']:+.0f}% | {e['al_tut']:+.0f}% | {e['kontrol']['toplam']:+.1f}% | {karar} |")
        (KOK / "veri" / "BIST100_SONUCLAR.md").write_text("\n".join(satirlar) + "\n", encoding="utf-8")
        if karne:
            risk.karne_yaz(KOK / "veri" / "karne_swing.json", KOK / "veri" / "KARNE_SWING.md", karne,
                           "Canlı karne: OTO-BIST (genel)")
    print(f"\n{len(hisseler)} hisse yazıldı: {hedef}")


if __name__ == "__main__":
    main()
