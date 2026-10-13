"""OTOMATİK SCALPER: BIST 100 hisselerinde gün içi (5 dk / 15 dk / 1 saat) strateji testi.

Swing testinden farkları:
- Gece taşıma yok: pozisyon her günün son mumunda kapanır, son mumda yeni işlem açılmaz.
- 24 stratejiye ek olarak gün içine özel 7 strateji (VWAP, ilk mum kırılımı, RSI(2), Stokastik RSI,
  EMA 9x21 + VWAP, hızlı SuperTrend, Bollinger sıkışma) ve bunların hepsinin ikili kombinleri.
- Eğitim / kontrol ayrımı (walk-forward): seçim dönemin ilk %70'inde yapılır, kalan %30'da
  (strateji bu veriyi "görmeden") tekrar ölçülür. Sadece kontrol döneminde de kâr eden seçilir.
- Kâr faktörü, en büyük düşüş, günlük işlem sayısı ve ortalama bekleme süresi raporlanır.

Yahoo sınırı: 5 ve 15 dakikalık veri son 60 gün, 1 saatlik veri son 730 gün.

Kullanım:
    python araclar/scalper.py              # Yahoo Finance'ten veri çeker
    python araclar/scalper.py --sentetik   # internetsiz deneme
"""
import json
import sys
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import backtest as bt
from backtest import (KOK, asagi_kes, buyuk, ema, gecikme, highest, kucuk, kucuk_esit, lowest, rsi, sma,
                      stdev, supertrend, yukari_kes)

MAX_BAR = 30
KOMISYON = 0.15        # %, al+sat toplam (komisyon + kayma)
MIN_ISLEM_EGITIM = 10  # eğitim döneminde en az işlem
MIN_ISLEM_KONTROL = 3  # kontrol döneminde en az işlem
EGITIM_ORAN = 0.70
ISINMA = 200

EK_ADLAR = ["25 VWAP Kesişimi", "26 İlk Mum Kırılımı", "27 RSI(2) Dip", "28 Stokastik RSI",
            "29 EMA 9x21 + VWAP", "30 Hızlı SuperTrend", "31 Bollinger Sıkışma"]
ADLAR = bt.ADLAR[:24] + EK_ADLAR + ["32 Ortak Karar"]
NS = 31  # ortak karar hariç strateji sayısı
ADAYLAR = [(k, -1) for k in range(NS + 1)] + [(i, j) for i in range(NS - 1) for j in range(i + 1, NS)]
# Pine scalper'daki zaman dilimi sırası
TF_ADLARI = {0: "5 Dakika", 1: "15 Dakika", 2: "1 Saat"}


def aday_adi(c):
    a, b = ADAYLAR[c]
    return ADLAR[a] if b < 0 else f"{ADLAR[a]} + {ADLAR[b]}"


def gun_sinirlari(index):
    gunler = pd.DatetimeIndex(index).normalize()
    ilk = np.ones(len(gunler), bool); ilk[1:] = gunler[1:] != gunler[:-1]
    son = np.ones(len(gunler), bool); son[:-1] = gunler[1:] != gunler[:-1]
    return gunler, ilk, son


def ek_sinyaller(df, b, s):
    h, l, c, v = (df[k].to_numpy(float) for k in ("High", "Low", "Close", "Volume"))
    gunler, ilk, son = gun_sinirlari(df.index)
    hlc3 = (h + l + c) / 3
    pv = pd.Series(hlc3 * v).groupby(gunler).cumsum().values
    vv = pd.Series(v).groupby(gunler).cumsum().values
    with np.errstate(divide="ignore", invalid="ignore"):
        vwap = pv / vv
    b[25], s[25] = yukari_kes(c, vwap), asagi_kes(c, vwap)

    or_ust = pd.Series(np.where(ilk, h, np.nan)).ffill().values
    or_alt = pd.Series(np.where(ilk, l, np.nan)).ffill().values
    b[26] = yukari_kes(c, or_ust) & ~ilk
    s[26] = asagi_kes(c, or_alt)

    r2 = rsi(c, 2)
    b[27], s[27] = yukari_kes(r2, np.full(len(c), 10.0)), yukari_kes(r2, np.full(len(c), 70.0))

    sr = rsi(c, 14)
    with np.errstate(divide="ignore", invalid="ignore"):
        stoch = 100 * (sr - lowest(sr, 14)) / (highest(sr, 14) - lowest(sr, 14))
    k_ = sma(stoch, 3); d_ = sma(k_, 3)
    b[28] = yukari_kes(k_, d_) & kucuk(k_, 20)
    s[28] = asagi_kes(k_, d_) & buyuk(k_, 80)

    e9, e21 = ema(c, 9), ema(c, 21)
    b[29], s[29] = yukari_kes(e9, e21) & buyuk(c, vwap), asagi_kes(e9, e21)

    _, yon = supertrend(h, l, c, 2.0, 7)
    yuk = yon < 0
    b[30], s[30] = yuk & ~gecikme(yuk), ~yuk & gecikme(yuk)

    s20 = sma(c, 20); sd = stdev(c, 20)
    with np.errstate(divide="ignore", invalid="ignore"):
        gen = 4.0 * sd / s20
    sikisma = kucuk_esit(gen, lowest(gen, 50) * 1.1)
    b[31] = yukari_kes(c, s20 + 2.0 * sd) & gecikme(sikisma)
    s[31] = asagi_kes(c, s20)
    return son


def durum_gun_ici(al, sat, son):
    """AL'da gir; SAT'ta, MAX_BAR dolunca ya da günün son mumunda çık. Son mumda giriş yok."""
    poz = np.zeros(len(al), bool)
    p = False; giris = 0
    for i in range(len(al)):
        if p and (sat[i] or i - giris >= MAX_BAR or son[i]):
            p = False
        elif al[i] and not p and not son[i]:
            p = True; giris = i
        poz[i] = p
    return poz


def stratejiler(df):
    b, s = bt.sinyaller(df)
    son = ek_sinyaller(df, b, s)
    b[32], s[32] = bt.ortak_karar(b, s, NS)
    return np.array([durum_gun_ici(b[k], s[k], son) for k in range(1, NS + 2)])


def olcumler(r, bekleme, gun_sayisi):
    if len(r) == 0:
        return None
    ser = np.cumprod(1 + r / 100)
    tepe = np.maximum.accumulate(np.concatenate([[1.0], ser]))[1:]
    kazanc, kayip = r[r > 0].sum(), -r[r < 0].sum()
    return {
        "islem": int(len(r)),
        "kazanma": round(float((r > 0).mean() * 100), 1),
        "ortalama": round(float(r.mean()), 3),
        "toplam": round(float((ser[-1] - 1) * 100), 1),
        "kar_faktoru": round(float(kazanc / kayip), 2) if kayip > 0 else 99.0,
        "max_dusus": round(float(((ser / tepe) - 1).min() * 100), 1),
        "gunluk_islem": round(len(r) / max(gun_sayisi, 1), 2),
        "ort_bekleme": round(float(np.mean(bekleme)), 1),
    }


def zaman_dilimi_test(df, tf):
    poz = stratejiler(df)
    kapanis = df["Close"].to_numpy(float)
    gunler = pd.DatetimeIndex(df.index).normalize()
    bas_i = ISINMA
    if bas_i >= len(df) - 100:
        return []
    bolme = bas_i + int((len(df) - bas_i) * EGITIM_ORAN)
    gun_e = len(np.unique(gunler[bas_i:bolme])); gun_k = len(np.unique(gunler[bolme:]))
    sonuclar = []
    for c, (a, b) in enumerate(ADAYLAR):
        d = poz[a] if b < 0 else (poz[a] & poz[b])
        tr_ = bt.islemler(d, kapanis, bas_i)
        if len(tr_) < MIN_ISLEM_EGITIM + MIN_ISLEM_KONTROL:
            continue
        g = np.array([x[0] for x in tr_]); k = np.array([x[1] for x in tr_])
        r = (kapanis[k] / kapanis[g] - 1) * 100 - KOMISYON
        egitim = g < bolme
        if egitim.sum() < MIN_ISLEM_EGITIM or (~egitim).sum() < MIN_ISLEM_KONTROL:
            continue
        o_e = olcumler(r[egitim], (k - g)[egitim], gun_e)
        o_k = olcumler(r[~egitim], (k - g)[~egitim], gun_k)
        o_t = olcumler(r, k - g, gun_e + gun_k)
        # eğitim dönemindeki günlük bileşik getiri: farklı uzunluktaki dönemleri karşılaştırılabilir yapar
        skor = ((1 + o_e["toplam"] / 100) ** (1 / max(gun_e, 1)) - 1) * 100
        sonuclar.append({
            "aday": c, "ad": aday_adi(c), "tf": tf, "tf_ad": TF_ADLARI[tf], "skor": round(skor, 4),
            "baslangic": str(df.index[bas_i].date()), "kontrol_bas": str(df.index[bolme].date()),
            **o_t, "egitim": o_e, "kontrol": o_k,
            "kontrol_gecti": bool(o_k["toplam"] > 0 and o_k["kar_faktoru"] > 1.0),
        })
    return sonuclar


def veri_cek(kod):
    import yfinance as yf
    sembol = f"{kod}.IS"
    sonuc = {}
    for tf, (aralik, sure) in {0: ("5m", "60d"), 1: ("15m", "60d"), 2: ("60m", "730d")}.items():
        for deneme in range(3):
            try:
                df = yf.download(sembol, period=sure, interval=aralik, auto_adjust=True, progress=False)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                if df.empty:
                    break
                df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
                df = df[df["Close"] > 0]
                if df.index.tz is not None:
                    df.index = df.index.tz_convert("Europe/Istanbul").tz_localize(None)
                sonuc[tf] = df
                break
            except Exception as e:
                print(f"  {kod} {aralik}: hata ({e}), tekrar deneniyor", flush=True)
                time.sleep(5 * (deneme + 1))
    return sonuc


def sentetik_veri(kod):
    rng = np.random.default_rng(sum(map(ord, kod)))

    def uret(gun, bar_gun, dakika):
        zaman = []
        for g in pd.bdate_range("2025-06-02", periods=gun):
            zaman += [g + pd.Timedelta(hours=10) + pd.Timedelta(minutes=dakika * i) for i in range(bar_gun)]
        n = len(zaman)
        c = 50 * np.exp(np.cumsum(rng.normal(0.00005, 0.004, n)))
        o = c * (1 + rng.normal(0, 0.001, n))
        h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.002, n)))
        l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.002, n)))
        v = rng.integers(1e4, 1e6, n).astype(float)
        return pd.DataFrame({"Open": o, "High": h, "Low": l, "Close": c, "Volume": v}, index=pd.DatetimeIndex(zaman))

    return {0: uret(42, 96, 5), 1: uret(42, 32, 15), 2: uret(480, 8, 60)}


def main():
    sentetik = "--sentetik" in sys.argv
    kodlar = [x.strip() for x in (KOK / "araclar" / "bist100.txt").read_text(encoding="utf-8").splitlines()
              if x.strip() and not x.startswith("#")]
    if "--ilk" in sys.argv:
        kodlar = kodlar[: int(sys.argv[sys.argv.index("--ilk") + 1])]
    hisseler = {}
    for kod in kodlar:
        t0 = time.time()
        veri = sentetik_veri(kod) if sentetik else veri_cek(kod)
        tum = []
        for tf in (0, 1, 2):
            df = veri.get(tf)
            if df is not None and len(df) > ISINMA + 150:
                tum += zaman_dilimi_test(df, tf)
        if not tum:
            print(f"{kod}: veri yok/yetersiz, atlandı", flush=True)
            continue
        gecen = [x for x in tum if x["kontrol_gecti"]]
        havuz = gecen or tum
        havuz.sort(key=lambda x: x["skor"], reverse=True)
        hisseler[kod] = {"en_iyi": havuz[0], "ilk5": havuz[:5], "kontrolu_gecen_aday": len(gecen)}
        e = havuz[0]
        print(f"{kod}: {e['ad']} • {e['tf_ad']} • {e['islem']} işlem • %{e['kazanma']} kazanma • KF {e['kar_faktoru']} • "
              f"kontrol {e['kontrol']['toplam']:+.1f}% ({time.time() - t0:.1f} sn)", flush=True)
    if not hisseler:
        sys.exit("Hiçbir hisse için sonuç üretilemedi; eski sonuçlar korunuyor.")
    cikti = {
        "tarih": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "ayarlar": {"max_bar": MAX_BAR, "komisyon": KOMISYON, "egitim_orani": EGITIM_ORAN,
                    "min_islem_egitim": MIN_ISLEM_EGITIM, "min_islem_kontrol": MIN_ISLEM_KONTROL,
                    "olcut": "eğitim dönemi günlük bileşik getiri; kontrol döneminde kârlı ve KF>1 olanlar öncelikli"},
        "sentetik": sentetik,
        "hisseler": hisseler,
    }
    hedef = KOK / "veri" / ("deneme_scalper.json" if sentetik else "scalper_sonuclar.json")
    hedef.parent.mkdir(exist_ok=True)
    hedef.write_text(json.dumps(cikti, ensure_ascii=False, indent=1), encoding="utf-8")
    if not sentetik:
        sat = [f"# BIST 100 gün içi (scalper) en iyi strateji listesi ({cikti['tarih']})", "",
               "Gece taşıma yok (pozisyon gün sonunda kapanır). Komisyon+kayma %0,15. Seçim dönemin ilk %70'inde yapıldı; "
               "**Kontrol** sütunu stratejinin hiç görmediği son %30'daki sonuçtur. Karar: kontrolde kârlı mı, "
               "kâr faktörü ≥ 1,3 mü, kazanma ≥ %50 mi (3 şart).", "",
               "| Hisse | En iyi strateji / kombin | Zaman | İşlem | Günlük işlem | Kazanma | Kâr faktörü | En büyük düşüş | Toplam | Kontrol | Karar |",
               "|---|---|---|---|---|---|---|---|---|---|---|"]
        for kod, v in sorted(hisseler.items(), key=lambda kv: -kv[1]["en_iyi"]["kontrol"]["toplam"]):
            e = v["en_iyi"]
            puan = (e["kontrol"]["toplam"] > 0) + (e["kar_faktoru"] >= 1.3) + (e["kazanma"] >= 50)
            karar = ["ZAYIF", "ZAYIF", "ORTA", "GÜÇLÜ"][puan]
            sat.append(f"| {kod} | {e['ad']} | {e['tf_ad']} | {e['islem']} | {e['gunluk_islem']} | %{e['kazanma']:.0f} | "
                       f"{e['kar_faktoru']} | {e['max_dusus']}% | {e['toplam']:+.1f}% | {e['kontrol']['toplam']:+.1f}% | {karar} |")
        (KOK / "veri" / "SCALPER_SONUCLAR.md").write_text("\n".join(sat) + "\n", encoding="utf-8")
    print(f"\n{len(hisseler)} hisse yazıldı: {hedef}")


if __name__ == "__main__":
    main()
