"""Risk yönetimli işlem simülasyonu ve canlı karne (ileriye dönük gerçek performans takibi).

Çıkış modu = (stop ATR katı, hedef R katı, iz süren stop ATR katı); 0 = kapalı.
Mod (0, 0, 0): sadece stratejinin kendi SAT sinyali (eski davranış).

Bir mumda kurallar (Pine'daki çizimle aynı):
- Giriş: strateji durumu yanlış -> doğru olduğu mumun kapanışı. ATR = giriş mumunun ATR(14)'ü.
- Stop: giriş - stop_k * ATR. İz süren stop açıksa: max(stop, girişten önceki mumlara kadar en yüksek - izs_k * önceki mumun ATR'si).
- Hedef: giriş + hedef_r * (giriş - ilk stop).
- Aynı mumda hem stop hem hedef değerse stop sayılır (temkinli varsayım).
- Açılış stopun altındaysa (boşluk) çıkış açılıştan, hedefin üstündeyse yine açılıştan yapılır.
- Stop/hedef olmazsa stratejinin SAT'ında kapanıştan çıkılır. Risk ile çıkıldıktan sonra strateji
  yeniden "AL" durumuna geçene kadar yeni işlem açılmaz.
"""
import json
from datetime import datetime, timezone

import numpy as np

MODLAR = [(0.0, 0.0, 0.0)] + [(sl, tp, izs) for sl in (1.5, 2.5) for tp in (0.0, 2.0, 3.0) for izs in (0.0, 3.0)
                              if not (tp == 0.0 and izs == 0.0)]


def mod_adi(mod):
    sl, tp, izs = mod
    if sl == 0:
        return "Sinyal çıkışı"
    parca = [f"stop {sl:g} ATR"]
    if tp:
        parca.append(f"hedef {tp:g}R")
    if izs:
        parca.append(f"iz stop {izs:g} ATR")
    return " + ".join(parca)


def risk_islemler(durum, o, h, l, c, atr, bas_i, mod):
    """(giriş indeksleri, çıkış indeksleri, çıkış fiyatları, çıkış nedeni 0=sinyal 1=stop 2=hedef)."""
    once = np.concatenate([[False], durum[:-1]])
    girisler = np.flatnonzero(durum & ~once)
    cikislar = np.flatnonzero(~durum & once)
    sl, tp, izs = mod
    G, K, F, N = [], [], [], []
    j = 0
    for g in girisler:
        while j < len(cikislar) and cikislar[j] <= g:
            j += 1
        if j >= len(cikislar):
            break
        k = cikislar[j]
        if g < bas_i:
            continue
        if sl == 0 or np.isnan(atr[g]):
            G.append(g); K.append(k); F.append(c[k]); N.append(0)
            continue
        e = c[g]
        stop0 = e - sl * atr[g]
        hedef = e + tp * (e - stop0) if tp else np.inf
        H, L, O = h[g + 1:k + 1], l[g + 1:k + 1], o[g + 1:k + 1]
        if izs:
            tepe = np.maximum.accumulate(h[g:k])          # mum t için: girişten t-1'e kadar en yüksek
            stop = np.maximum(stop0, tepe - izs * atr[g:k])
        else:
            stop = np.full(len(H), stop0)
        vur_s = L <= stop
        vur_h = H >= hedef
        vur = np.flatnonzero(vur_s | vur_h)
        if len(vur):
            t = vur[0]
            if vur_s[t]:
                fiyat, neden = min(O[t], stop[t]), 1
            else:
                fiyat, neden = max(O[t], hedef), 2
            G.append(g); K.append(g + 1 + t); F.append(fiyat); N.append(neden)
        else:
            G.append(g); K.append(k); F.append(c[k]); N.append(0)
    return np.array(G, int), np.array(K, int), np.array(F, float), np.array(N, int)


# ───────────────────────────── canlı karne ─────────────────────────────
def karne_satiri(kod, eski, veri_tf, komisyon, durum_fonk, atr_fonk):
    """Önceki çalışmada seçilen stratejinin, o tarihten bu yana (görmediği veride) ne yaptığını ölçer."""
    tf = eski["tf"]
    df = veri_tf.get(tf)
    if df is None or len(df) < 50:
        return None
    bas = np.datetime64(eski["secim_tarihi"])
    zaman = df.index.values
    bas_i = int(np.searchsorted(zaman, bas, side="right"))
    if bas_i >= len(df) - 1:
        return None
    poz = durum_fonk(df)
    a, b = eski["aday_ab"]
    d = poz[a] if b < 0 else (poz[a] & poz[b])
    o, h, l, c = (df[x].to_numpy(float) for x in ("Open", "High", "Low", "Close"))
    mod = tuple(eski.get("mod", (0.0, 0.0, 0.0)))
    g, k, f, n = risk_islemler(d, o, h, l, c, atr_fonk(df), bas_i, mod)
    r = (f / c[g] - 1) * 100 - komisyon if len(g) else np.array([])
    return {
        "hisse": kod, "secim_tarihi": eski["secim_tarihi"], "olcum_tarihi": str(df.index[-1].date()),
        "aday": eski["ad"], "tf": eski["tf_ad"], "islem": int(len(r)),
        "kazanan": int((r > 0).sum()), "getiri": round(float((np.prod(1 + r / 100) - 1) * 100), 2) if len(r) else 0.0,
        "al_tut": round(float((c[-1] / c[bas_i - 1] - 1) * 100), 2),
    }


def karne_yaz(yol_json, yol_md, yeni_satirlar, baslik):
    gecmis = json.loads(yol_json.read_text(encoding="utf-8")) if yol_json.exists() else []
    # aynı seçim tarihi + hisse için en son ölçüm geçerli (dönem uzadıkça güncellenir)
    anahtar = {(x["hisse"], x["secim_tarihi"]): i for i, x in enumerate(gecmis)}
    for s in yeni_satirlar:
        i = anahtar.get((s["hisse"], s["secim_tarihi"]))
        if i is None:
            gecmis.append(s)
        else:
            gecmis[i] = s
    yol_json.write_text(json.dumps(gecmis, ensure_ascii=False, indent=1), encoding="utf-8")

    donemler = {}
    for s in gecmis:
        donemler.setdefault(s["secim_tarihi"], []).append(s)
    sat = [f"# {baslik}", "",
           "Her çalışmada seçilen stratejinin, seçildiği tarihten sonra (hiç görmediği veride) gerçekte ne yaptığı.",
           "Geçmiş testin aksine bu tablo şans eseri iyi görünemez; indikatörün gerçek doğruluğu budur.", "",
           "| Seçim tarihi | Ölçüm tarihi | Hisse | İşlem yapılan | İşlem | Kazanma | Ort. strateji getirisi | Ort. Al-Tut | Stratejinin önde olduğu hisse |",
           "|---|---|---|---|---|---|---|---|---|"]
    toplam_islem = toplam_kazanan = 0
    for tarih in sorted(donemler, reverse=True):
        x = donemler[tarih]
        islemli = [s for s in x if s["islem"] > 0]
        n = sum(s["islem"] for s in x); kz = sum(s["kazanan"] for s in x)
        toplam_islem += n; toplam_kazanan += kz
        ort_g = np.mean([s["getiri"] for s in x]); ort_a = np.mean([s["al_tut"] for s in x])
        onde = sum(s["getiri"] > s["al_tut"] for s in x)
        sat.append(f"| {tarih} | {max(s['olcum_tarihi'] for s in x)} | {len(x)} | {len(islemli)} | {n} | "
                   f"{(kz / n * 100 if n else 0):.0f}% | {ort_g:+.2f}% | {ort_a:+.2f}% | {onde}/{len(x)} |")
    sat += ["", f"**Toplam:** {toplam_islem} gerçek işlem, kazanma oranı "
                f"{(toplam_kazanan / toplam_islem * 100 if toplam_islem else 0):.0f}%.",
            "", f"_Son güncelleme: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC_"]
    yol_md.write_text("\n".join(sat) + "\n", encoding="utf-8")
