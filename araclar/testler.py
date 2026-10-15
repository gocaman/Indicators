"""Çevrimdışı testler (internet gerekmez): python araclar/testler.py

1) Python dosyaları derlenir, iş akışı YAML dosyaları okunur.
2) Üretilen Pine metni: yer tutucu / çift tanım / tırnak kontrolü, gömülü sonuç dizilerinin uzunluğu,
   aday numaralarının strateji adlarıyla eşleşmesi (hem normal hem gün içi sonuçlar).
3) Pine'daki "mum mum işlem takibi" ile risk.py'deki referans simülasyon, sentetik veride aynı işlemleri bulur.
4) AL taramasının "açık işlem" bulucusu, mum mum takiple aynı girişi ve stopu verir.
"""
import json
import py_compile
import re
import sys
from pathlib import Path

import numpy as np
import yaml

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import al_tarama as at  # noqa: E402
import backtest as bt  # noqa: E402
import risk  # noqa: E402
import scalper as sc  # noqa: E402

PINE = KOK / "0. OTOMATİK EN İYİ STRATEJİ - BIST.txt"
hatalar = []
sayac = {"ok": 0}


def kontrol(kosul, mesaj):
    if kosul:
        sayac["ok"] += 1
    else:
        hatalar.append(mesaj)
        print("HATA:", mesaj)


# ───────────────────────── 1) dosyalar ─────────────────────────
def test_dosyalar():
    for p in sorted((KOK / "araclar").glob("*.py")):
        try:
            py_compile.compile(str(p), doraise=True)
            kontrol(True, "")
        except py_compile.PyCompileError as e:
            kontrol(False, f"derlenemedi: {p.name}: {e}")
    for p in sorted((KOK / ".github" / "workflows").glob("*.yml")):
        try:
            y = yaml.safe_load(p.read_text(encoding="utf-8"))
            kontrol("jobs" in y, f"{p.name}: jobs yok")
        except Exception as e:
            kontrol(False, f"{p.name}: YAML okunamadı: {e}")


# ───────────────────────── 2) Pine metni ─────────────────────────
def test_pine_metni():
    t = PINE.read_text(encoding="utf-8")
    satirlar = t.split("\n")
    kontrol(t.startswith("//@version=5"), "Pine v5 başlığı yok")
    kontrol(not re.search(r"@[A-Z0-9]+@", t), "doldurulmamış yer tutucu kaldı")
    kontrol(t.count("request.security(") == 3, "request.security sayısı 3 olmalı")
    # tırnaklar: yorum olmayan her satırda çift sayıda
    for i, l in enumerate(satirlar, 1):
        if l.strip().startswith("//"):
            continue
        kontrol(len(re.findall(r'(?<!\\)"', l)) % 2 == 0, f"satır {i}: tırnak sayısı tek")
    # üst düzey çift tanım (Pine aynı kapsamda yeniden tanıma izin vermez)
    tanim = {}
    for i, l in enumerate(satirlar, 1):
        if not l or l[0] in " /\t":
            continue
        m = re.match(r"(?:var\s+)?(?:(?:int|float|bool|string|color|label|line|table|polyline)(?:\[\])?\s+)?([A-Za-z_]\w*)\s*=[^=]", l)
        if m:
            tanim.setdefault(m.group(1), []).append(i)
        m = re.match(r"([A-Za-z_]\w*)\(.*\)\s*=>", l)
        if m:
            tanim.setdefault(m.group(1), []).append(i)
        m = re.match(r"\[([^\]]+)\]\s*=", l)
        if m:
            for ad in [x.strip() for x in m.group(1).split(",")]:
                tanim.setdefault(ad, []).append(i)
    for ad, yerler in tanim.items():
        kontrol(len(yerler) == 1, f"çift tanım: {ad} satırları {yerler}")
    # yeni mum mum takip bloğunda kullanılan her isim, kullanılmadan önce tanımlı olmalı
    ilk = {ad: yerler[0] for ad, yerler in tanim.items()}
    blok = [i for i, l in enumerate(satirlar, 1) if "AL / SAT / STOP / HEDEF etiketleri" in l]
    kontrol(len(blok) == 1, "takip bloğu bulunamadı")
    if blok:
        b0 = blok[0]
        for ad in ("m0", "m1", "m2", "cA", "cB", "secAday", "secTf", "f_bit", "mSl", "mTp", "mIzs", "atrG",
                   "riskAktif", "tfUygun", "komisyon", "f_yuzde"):
            kontrol(ad in ilk and ilk[ad] < b0, f"'{ad}' takip bloğundan önce tanımlı değil")
    # eski geçmiş-döngüsü kalıntıları
    kontrol("f_poz(" not in t.replace("f_poz(int t, int c, int i)", ""), "f_poz hâlâ çağrılıyor")
    kontrol("for i = lim to 0" not in t, "eski geri dönük döngü duruyor")


def aday_ad(i, adlar):
    a_b = [(k, -1) for k in range(32)] + [(i1, j1) for i1 in range(30) for j1 in range(i1 + 1, 31)]
    a, b = a_b[i]
    return adlar[a] if b < 0 else adlar[a] + " + " + adlar[b]


def sade(ad):
    return re.sub(r"\b\d\d (?=\D)", "", ad).strip()


def test_gomulu_sonuclar():
    t = PINE.read_text(encoding="utf-8")
    adlar = re.search(r"var string\[\] adlar = array\.from\((.*?)\)\n", t).group(1)
    adlar = re.findall(r'"([^"]*)"', adlar)
    kontrol(len(adlar) == 32, f"strateji adı sayısı {len(adlar)}")
    kodlar = re.search(r'HAZIR_KODLAR = gunIci \? "([^"]*)" : "([^"]*)"', t)
    tfler = re.search(r'HAZIR_TFLER = gunIci \? "([^"]*)" : "([^"]*)"', t)
    ayar = {"gunIci": 0, "normal": 1}
    dosyalar = {"gunIci": "scalper_sonuclar.json", "normal": "bist100_sonuclar.json"}
    for mod, k in ayar.items():
        sonuc = json.loads((KOK / "veri" / dosyalar[mod]).read_text(encoding="utf-8"))["hisseler"]
        kod_dizi = kodlar.group(k + 1) if False else (kodlar.group(1) if mod == "gunIci" else kodlar.group(2))
        tf_dizi = tfler.group(1) if mod == "gunIci" else tfler.group(2)
        n = len(sonuc)
        kontrol(len(kod_dizi) == 6 * n, f"{mod}: hisse kodu uzunluğu {len(kod_dizi)} != {6 * n}")
        kontrol(len(tf_dizi) == n, f"{mod}: zaman dilimi dizisi uzunluğu")
        liste = [kod_dizi[6 * i:6 * i + 6].strip() for i in range(n)]
        kontrol(liste == list(sonuc.keys()), f"{mod}: hisse sırası")
        # dizi uzunlukları
        satir = [l for l in t.split("\n") if l.startswith("var int[] hAday = ")][0]
        kismi = satir.split(" : ")[0 if mod == "gunIci" else 1] if " : " in satir else satir
        sayilar = re.findall(r"array\.from\(([^)]*)\)", satir)[0 if mod == "gunIci" else 1]
        degerler = [int(x) for x in sayilar.split(",")]
        kontrol(len(degerler) == n, f"{mod}: hAday uzunluğu {len(degerler)} != {n}")
        for i, h in enumerate(liste):
            e = sonuc[h]["en_iyi"]
            kontrol(0 <= degerler[i] < 497, f"{mod} {h}: aday numarası aralık dışı")
            beklenen = sade(e["ad"])
            bulunan = sade(aday_ad(degerler[i], adlar))
            kontrol(bulunan == beklenen, f"{mod} {h}: Pine adayı '{bulunan}' != sonuç '{beklenen}'")
            tf_beklenen = e["tf"] if mod == "gunIci" else e["tf"] - 1
            kontrol(int(tf_dizi[i]) == tf_beklenen, f"{mod} {h}: zaman dilimi")
    # tüm float dizilerinin uzunlukları eşit mi
    for ad in ("hN", "hKaz", "hTop", "hAlTut", "hYil", "hYillik", "hMSl", "hMTp", "hMIzs", "hBas", "hTf"):
        satir = [l for l in t.split("\n") if l.startswith(f"var ") and f"[] {ad} = " in l][0]
        g = re.findall(r"array\.from\(([^)]*)\)", satir)
        kontrol(len(g[0].split(",")) == 97 and len(g[1].split(",")) == 97, f"{ad}: iki modda da 97 eleman olmalı")


# ───────────────────── 3) mum mum takip = referans simülasyon ─────────────────────
def mum_mum(d, o, h, l, c, atr, mod):
    """pine_uret.py'deki 'AL / SAT / STOP / HEDEF' bloğunun birebir Python karşılığı."""
    sl, tp, izs = mod
    risk_aktif = sl > 0
    nan = np.nan
    gF = gStop0 = gHedef = gTepe = nan
    once = False
    islemler = []
    giris_i = None
    for t in range(len(c)):
        poz = bool(d[t]); prev = once
        giris = poz and not prev
        cikis = (not poz) and prev
        onceki_atr = atr[t - 1] if t > 0 else nan
        gSt = max(gStop0, gTepe - izs * onceki_atr) if izs > 0 else gStop0
        devam = (poz or cikis) and (not giris) and not np.isnan(gF)
        stop_v = risk_aktif and devam and l[t] <= gSt
        hedef_v = risk_aktif and devam and (not stop_v) and not np.isnan(gHedef) and h[t] >= gHedef
        if giris:
            gF = c[t]
            gStop0 = c[t] - sl * atr[t]
            gHedef = c[t] + tp * sl * atr[t] if tp > 0 else nan
            giris_i = t
        elif stop_v or hedef_v:
            cik = min(o[t], gSt) if stop_v else max(o[t], gHedef)
            islemler.append((giris_i, t, cik, 1 if stop_v else 2))
            gF = nan
        elif cikis and not np.isnan(gF):
            islemler.append((giris_i, t, c[t], 0))
            gF = nan
        gTepe = nan if np.isnan(gF) else max(h[t] if np.isnan(gTepe) else gTepe, h[t])
        once = poz
    acik = None
    if not np.isnan(gF):
        acik = (giris_i, gF, gStop0, gHedef, gTepe)
    return islemler, acik


def test_mum_mum():
    karsilastirilan = 0
    for kod in ("AAA", "BBB", "CCC", "DDD", "EEE", "FFF"):
        for tf, df in bt.sentetik_veri(kod).items():
            poz = bt.stratejiler(df)
            o, h, l, c = (df[x].to_numpy(float) for x in ("Open", "High", "Low", "Close"))
            atr = bt.atr14(df)
            rng = np.random.default_rng(len(kod) + tf)
            adaylar = [(int(a), -1) for a in rng.integers(0, 25, 6)] + [tuple(sorted(rng.integers(0, 24, 2))) for _ in range(4)]
            for a, b in adaylar:
                if a == b:
                    continue
                d = poz[a] if b < 0 else (poz[a] & poz[b])
                for mod in risk.MODLAR:
                    G, K, F, N = risk.risk_islemler(d, o, h, l, c, atr, 0, mod)
                    ref = [(int(g), int(k), float(f), int(n)) for g, k, f, n in zip(G, K, F, N)]
                    sim, acik = mum_mum(d, o, h, l, c, atr, mod)
                    # referans yalnızca kapanmış işlemleri verir; mum mum takip açık olanı ayrıca tutar
                    # referans, seri sonunda hiç sinyalle kapanmamış son işlemi atlar; mum mum takip ise o işlem
                    # stopa ya da hedefe değdiyse onu da yazar. Bu tek fazlalığa izin verilir.
                    fazla = len(sim) == len(ref) + 1 and sim[-1][3] != 0
                    if fazla:
                        sim = sim[:-1]
                    kontrol(len(sim) == len(ref), f"işlem sayısı farklı: {kod} tf{tf} aday {a},{b} mod {mod}: {len(sim)} != {len(ref)}")
                    if len(sim) == len(ref):
                        for x, y in zip(sim, ref):
                            ayni = x[0] == y[0] and x[1] == y[1] and x[3] == y[3] and abs(x[2] - y[2]) < 1e-9
                            kontrol(ayni, f"işlem farklı: {kod} tf{tf} aday {a},{b} mod {mod}: {x} != {y}")
                    karsilastirilan += len(ref)
    kontrol(karsilastirilan > 500, f"karşılaştırılan işlem çok az: {karsilastirilan}")
    print(f"  mum mum takip: {karsilastirilan} işlem referansla birebir aynı")


# ───────────────────── 4) AL taramasındaki açık işlem ─────────────────────
def test_tarama():
    sinanan = acik_sayisi = 0
    for kod in ("AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "HHH"):
        for tf, df in bt.sentetik_veri(kod).items():
            poz = bt.stratejiler(df)
            o, h, l, c = (df[x].to_numpy(float) for x in ("Open", "High", "Low", "Close"))
            atr = bt.atr14(df)
            for a in range(0, 24, 2):
                d = poz[a]
                for mod in risk.MODLAR:
                    sim, acik = mum_mum(d, o, h, l, c, atr, mod)
                    tarama = at.acik_islem(d, df, mod)
                    sinanan += 1
                    if acik is None:
                        kontrol(tarama is None, f"tarama açık işlem buldu ama takip bulmadı: {kod} tf{tf} a{a} {mod}")
                        continue
                    acik_sayisi += 1
                    kontrol(tarama is not None, f"takip açık işlem buldu ama tarama bulmadı: {kod} tf{tf} a{a} {mod}")
                    if tarama is None:
                        continue
                    g, stop, hedef = tarama
                    kontrol(g == acik[0], f"giriş mumu farklı: {kod} tf{tf} a{a} {mod}: {g} != {acik[0]}")
                    if mod[0] > 0 and mod[2] > 0:
                        beklenen = max(acik[2], acik[4] - mod[2] * atr[-1])
                        kontrol(stop is not None and abs(stop - beklenen) < 1e-9, f"stop farklı: {kod} tf{tf} a{a} {mod}: {stop} != {beklenen}")
    kontrol(acik_sayisi > 20, f"açık işlem içeren durum az: {acik_sayisi}")
    print(f"  tarama: {sinanan} durum, {acik_sayisi} tanesinde açık işlem; giriş ve stop mum mum takiple aynı")


def main():
    for ad, f in (("dosyalar", test_dosyalar), ("pine metni", test_pine_metni),
                  ("gömülü sonuçlar", test_gomulu_sonuclar), ("mum mum takip", test_mum_mum), ("AL taraması", test_tarama)):
        once = len(hatalar)
        f()
        print(f"{'OK ' if len(hatalar) == once else 'HATA'} {ad}")
    print(f"\n{sayac['ok']} kontrol geçti, {len(hatalar)} hata")
    sys.exit(1 if hatalar else 0)


if __name__ == "__main__":
    main()
