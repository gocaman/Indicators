"""Şu an AL'da olan BIST 100 hisselerini bulur (OTO-BIST'in her hisse için seçtiği en iyi strateji ile).

Her hissede, hazır sonuçlardaki en iyi strateji/kombin, zaman dilimi ve stop/hedef ayarı kullanılır:
  - normal mod: veri/bist100_sonuclar.json (4 saat / günlük / haftalık)
  - gün içi mod: veri/scalper_sonuclar.json (5 dk / 15 dk / 1 saat; gün sonunda pozisyon kapanır)
Son mumda pozisyon açıksa (strateji AL durumunda ve stop/hedefe değmemişse) hisse listeye girer.
Sonuç: veri/al_verenler.json ve veri/AL_VERENLER.md

Kullanım: python araclar/al_tarama.py
"""
import json
import sys
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import backtest as bt  # noqa: E402
import risk  # noqa: E402
import scalper as sc  # noqa: E402

VERI = bt.KOK / "veri"


def _indir(kod, aralik, **kw):
    import yfinance as yf
    for deneme in range(3):
        try:
            df = yf.download(f"{kod}.IS", interval=aralik, auto_adjust=True, progress=False, **kw)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if df.empty:
                return None
            df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
            df = df[df["Close"] > 0]
            if df.index.tz is not None:
                df.index = df.index.tz_convert("Europe/Istanbul").tz_localize(None)
            return df
        except Exception as e:  # ağ/limit hatası
            print(f"  {kod} {aralik}: hata ({e}), tekrar deneniyor", flush=True)
            time.sleep(5 * (deneme + 1))
    return None


def veri_normal(kod, tf):
    if tf == 2:
        return _indir(kod, "1d", start="2019-01-01")
    if tf == 3:
        return _indir(kod, "1wk", start="2017-06-01")
    s = _indir(kod, "1h", period="730d")
    return bt.dort_saatlik(s) if s is not None else None


def veri_gun_ici(kod, tf):
    aralik, sure = {0: ("5m", "60d"), 1: ("15m", "60d"), 2: ("60m", "730d")}[tf]
    return _indir(kod, aralik, period=sure)


def acik_islem(d, df, mod):
    """Son mumda açık işlem varsa (giriş indeksi, güncel stop, hedef), yoksa None."""
    if not d[-1]:
        return None
    once = np.concatenate([[False], d[:-1]])
    g = int(np.flatnonzero(d & ~once)[-1])
    o, h, l, c = (df[x].to_numpy(float) for x in ("Open", "High", "Low", "Close"))
    atr = bt.atr14(df)
    sl, tp, izs = mod
    if sl == 0 or np.isnan(atr[g]):
        return g, None, None
    stop0 = c[g] - sl * atr[g]
    hedef = c[g] + tp * (c[g] - stop0) if tp else None
    for t in range(g + 1, len(c)):
        stop = max(stop0, h[g:t].max() - izs * atr[t - 1]) if izs else stop0
        if l[t] <= stop or (hedef is not None and h[t] >= hedef):
            return None  # stop ya da hedefle kapanmış
    stop = max(stop0, h[g:].max() - izs * atr[-1]) if izs else stop0
    return g, stop, hedef


def istatistik(d, df, e, komisyon, gun_ici):
    """Seçilen stratejinin geçmiş işlemlerinden: yükseliş ne kadar sürede, ne kadar geldi? (tarihsel ortalama, tahmin değildir)

    Süreler takvim saatidir (gece/hafta sonu dahil); gün içi modda pozisyon gün sonunda kapandığı için kısadır.
    """
    isinma = sc.ISINMA if gun_ici else bt.ISINMA
    bas_i = max(int(np.searchsorted(df.index.values, np.datetime64(e["baslangic"]))), isinma)
    o, h, l, c = (df[x].to_numpy(float) for x in ("Open", "High", "Low", "Close"))
    g, k, f, _ = risk.risk_islemler(d, o, h, l, c, bt.atr14(df), bas_i, tuple(e.get("mod", (0, 0, 0))))
    if len(g) < 3:
        return None
    r = (f / c[g] - 1) * 100 - komisyon
    saat = (df.index[k] - df.index[g]).total_seconds().to_numpy() / 3600.0
    kaz = r > 0
    return {
        "islem": int(len(r)), "kazanma": round(float(kaz.mean() * 100), 1),
        "ort_kazanc": round(float(r[kaz].mean()), 2) if kaz.any() else 0.0,
        "ort_kayip": round(float(r[~kaz].mean()), 2) if (~kaz).any() else 0.0,
        "ort_getiri": round(float(r.mean()), 2),
        "tipik_saat": round(float(np.median(saat[kaz] if kaz.any() else saat)), 1),
        "ort_saat": round(float(saat.mean()), 1),
        "test_gun": int(max((df.index[-1] - df.index[bas_i]).days, 1)),
        "test_bas": df.index[bas_i].strftime("%Y-%m-%d"),
    }


def karar(e, gun_ici):
    if gun_ici:
        k = [e["kontrol"]["toplam"] > 0, e["kazanma"] >= 50, e.get("kar_faktoru", 0) >= 1.3]
    else:
        kontrol = e["kontrol"]["toplam"] if "kontrol" in e else e.get("son_yil", 0)
        k = [e["toplam"] > e["al_tut"], e["kazanma"] >= 50, kontrol > 0]
    p = sum(k)
    return ("GÜÇLÜ" if p == 3 else "ORTA" if p == 2 else "ZAYIF"), p


def tara(sonuclar, gun_ici):
    if sonuclar is None:
        return []
    satirlar = []
    for kod, x in sonuclar["hisseler"].items():
        e = x["en_iyi"]
        df = veri_gun_ici(kod, e["tf"]) if gun_ici else veri_normal(kod, e["tf"])
        if df is None or len(df) < 60:
            print(f"{kod}: veri yok", flush=True)
            continue
        if gun_ici:
            # Seans sürerken verinin son mumu günün son mumu değildir: gün sonu sanılıp pozisyon
            # kapatılmasın diye aynı güne geçici bir mum eklenir, hesaptan sonra atılır.
            adim = df.index[-1] - df.index[-2]
            gecici = df.index[-1] + adim < df.index[-1].normalize() + pd.Timedelta(hours=18)
            df2 = pd.concat([df, df.iloc[[-1]].set_axis([df.index[-1] + pd.Timedelta(minutes=1)])]) if gecici else df
            poz = sc.stratejiler(df2)[:, :len(df)]
        else:
            poz = bt.stratejiler(df)
        a, b = e["aday_ab"]
        d = poz[a] if b < 0 else (poz[a] & poz[b])
        sonuc = acik_islem(d, df, tuple(e.get("mod", (0, 0, 0))))
        if sonuc is None:
            continue
        g, stop, hedef = sonuc
        c = df["Close"].to_numpy(float)
        kr, puan = karar(e, gun_ici)
        ist = istatistik(d, df, e, sonuclar["ayarlar"]["komisyon"], gun_ici)
        if ist is not None:
            ist["gecen_saat"] = round(float((df.index[-1] - df.index[g]).total_seconds() / 3600.0), 1)
        satirlar.append({
            "hisse": kod, "strateji": e["ad"], "tf": e["tf_ad"],
            "giris_zaman": df.index[g].strftime("%Y-%m-%d %H:%M"), "giris": round(float(c[g]), 2),
            "son": round(float(c[-1]), 2), "getiri": round(float((c[-1] / c[g] - 1) * 100), 2),
            "stop": None if stop is None else round(float(stop), 2),
            "hedef": None if hedef is None else round(float(hedef), 2),
            "bar_once": int(len(c) - 1 - g), "karar": kr, "puan": puan, "ist": ist,
        })
        print(f"{kod}: AL'da ({e['ad']} • {e['tf_ad']})", flush=True)
    satirlar.sort(key=lambda s: (-s["puan"], s["bar_once"]))
    return satirlar


def md_tablo(baslik, satirlar):
    sat = [f"## {baslik} ({len(satirlar)} hisse)", ""]
    if not satirlar:
        return sat + ["Şu an AL'da olan hisse yok.", ""]
    sat += ["| Hisse | Karar | Strateji | Zaman dilimi | Giriş | Son | Getiri | Stop | Hedef | AL ne zaman |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for s in satirlar:
        sat.append(f"| {s['hisse']} | {s['karar']} | {s['strateji']} | {s['tf']} | {s['giris']} | {s['son']} | "
                   f"{s['getiri']:+.2f}% | {s['stop'] or '-'} | {s['hedef'] or '-'} | {s['giris_zaman']} ({s['bar_once']} mum önce) |")
    return sat + [""]


def sure_yazi(saat, gun_ici):
    if saat < 1.5:
        return f"{saat * 60:.0f} dk"
    if saat < 36:
        return f"{saat:.0f} saat"
    return f"{saat / 24:.0f} gün"


def beklenti_listesi(sonuc):
    """AL'da olan ve geçmişte ortalama işlemi kârlı olan hisseler, en kısa tipik yükseliş süresi başta."""
    liste = []
    for mod, anahtar in (("Normal", "normal"), ("Gün içi", "gun_ici")):
        for s in sonuc[anahtar]:
            i = s.get("ist")
            if i and i["ort_getiri"] > 0 and s["karar"] != "ZAYIF":
                liste.append({**s, "mod": mod})
    liste.sort(key=lambda s: (s["ist"]["tipik_saat"], -s["ist"]["ort_kazanc"]))
    return liste


def md_beklenti(sonuc):
    liste = beklenti_listesi(sonuc)
    sat = [f"## Beklenen yükselişler ({len(liste)} hisse)", "",
           "_AL'da olan, geçmişte ortalama işlemi kârlı ve kararı ZAYIF olmayan hisseler; en kısa sürede beklenen yükseliş başta. "
           "Süre ve oran, aynı stratejinin geçmiş KAZANAN işlemlerinin ortalamasıdır; garanti ya da tahmin değildir._", ""]
    if not liste:
        return sat + ["Şu an listelenecek hisse yok.", ""]
    sat += ["| Hisse | Mod | Tipik süre | Beklenen yükseliş | Kazanma | Kaybederse | AL'dan beri |", "|---|---|---|---|---|---|---|"]
    for s in liste:
        i = s["ist"]
        sat.append(f"| {s['hisse']} | {s['mod']} | {sure_yazi(i['tipik_saat'], s['mod'] == 'Gün içi')} | +{i['ort_kazanc']:.1f}% | "
                   f"%{i['kazanma']:.0f} ({i['islem']} işlem / {i['test_gun']} gün) | {i['ort_kayip']:.1f}% | "
                   f"{sure_yazi(i['gecen_saat'], s['mod'] == 'Gün içi')} |")
    return sat + [""]


def main():
    oku = lambda ad: json.loads((VERI / ad).read_text(encoding="utf-8")) if (VERI / ad).exists() else None
    simdi = datetime.now(timezone.utc)
    sonuc = {"zaman": simdi.strftime("%Y-%m-%dT%H:%M:%SZ"),
             "normal": tara(oku("bist100_sonuclar.json"), False),
             "gun_ici": tara(oku("scalper_sonuclar.json"), True)}
    VERI.mkdir(exist_ok=True)
    (VERI / "al_verenler.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    yerel = pd.Timestamp(simdi).tz_convert("Europe/Istanbul").strftime("%d.%m.%Y %H:%M")
    md = [f"# Şu an AL'da olan BIST 100 hisseleri", "",
          f"_Tarama: {yerel} (TSİ). Her hissede OTO-BIST'in seçtiği en iyi strateji kullanılır. "
          "Karar: GÜÇLÜ 3/3, ORTA 2/3, ZAYIF 0-1/3. Yatırım tavsiyesi değildir._", ""]
    md += md_tablo("Normal mod (4 saat / günlük / haftalık)", sonuc["normal"])
    md += md_tablo("Gün içi mod (5 dk / 15 dk / 1 saat)", sonuc["gun_ici"])
    md += md_beklenti(sonuc)
    (VERI / "AL_VERENLER.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Normal: {len(sonuc['normal'])}, gün içi: {len(sonuc['gun_ici'])} hisse AL'da")


if __name__ == "__main__":
    main()
