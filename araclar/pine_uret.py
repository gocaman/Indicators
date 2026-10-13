"""Pine indikatörlerini üretir.
  python araclar/pine_uret.py            -> "0. OTOMATİK EN İYİ STRATEJİ - BIST.txt" (swing: 4S/G/H)
  python araclar/pine_uret.py --scalper  -> "0. OTOMATİK SCALPER - BIST.txt" (gün içi: 5dk/15dk/1S)
veri/ altındaki sonuç dosyası varsa (backtest.py / scalper.py yazar) her hissenin hazır en iyi kombini koda gömülür.
"""
import json
import sys
from pathlib import Path

SCALPER = "--scalper" in sys.argv
KOK = Path(__file__).resolve().parent.parent
SONUC = KOK / "veri" / ("scalper_sonuclar.json" if SCALPER else "bist100_sonuclar.json")
CIKTI = KOK / ("0. OTOMATİK SCALPER - BIST.txt" if SCALPER else "0. OTOMATİK EN İYİ STRATEJİ - BIST.txt")
HAZIR = json.loads(SONUC.read_text(encoding="utf-8")) if SONUC.exists() else None
NAMES = ["01 RSI Karpuzlu", "02 Dip Bulucu (Banker)", "03 Dip Bulucu-2 (VixFix)", "04 AlphaTrend", "05 SuperTrend",
 "06 AlphaTrend+SuperTrend", "07 Parabolic SAR", "08 MACD Dip", "09 ALMA", "10 T3 Tillson",
 "11 Bollinger Orta Bant", "12 Bollinger20 x EMA50", "13 EMA 5x13", "14 EMA 5x22", "15 WMA 9x15",
 "16 SMMA 21x55", "17 Darvas Kutusu", "18 Fisher Dip", "19 CCI Dip", "20 TSI Dip",
 "21 MACD Kesişimi", "22 Erik Kombo", "23 EMA Kombo", "24 Bollinger Kombo"]
EK_NAMES = ["25 VWAP Kesişimi", "26 İlk Mum Kırılımı", "27 RSI(2) Dip", "28 Stokastik RSI",
            "29 EMA 9x21 + VWAP", "30 Hızlı SuperTrend", "31 Bollinger Sıkışma"]
NS = 31 if SCALPER else 24                 # ortak karar hariç strateji sayısı
NAMES = NAMES + (EK_NAMES if SCALPER else []) + [f"{NS + 1} Ortak Karar"]
NC = (NS + 1) + NS * (NS - 1) // 2        # aday sayısı (tekler + ikili kombinler)
# strateji no (1 tabanlı) -> grafiğe çizilecek çizgiler
LINES = {4:[1],5:[2],6:[1,2],7:[3],9:[4],10:[5],11:[6],12:[6,7],13:[8,9],14:[8,10],15:[11,12],16:[13,14],17:[15,16],22:[8,18],23:[8,17],24:[6,19]}
CIZGI_ADLARI = ["AlphaTrend", "SuperTrend", "PSAR", "ALMA", "T3", "SMA20 (BB orta)", "EMA50", "EMA5", "EMA13", "EMA22", "WMA9", "WMA15", "SMMA21", "SMMA55", "Darvas üst", "Darvas alt", "EMA14", "SMA10", "SMA200"]
CIZGI_DEGER = ["alpha", "stDeger", "psar", "alma", "t3", "sma20", "ema50", "ema5", "ema13", "ema22", "wma9", "wma15", "smma21", "smma55", "dUst", "dAlt", "ema14", "sma10", "sma200"]
if SCALPER:
    LINES.update({25:[20], 26:[21,22], 29:[23,24], 30:[25], 31:[6]})
    CIZGI_ADLARI += ["VWAP", "İlk mum üst", "İlk mum alt", "EMA9", "EMA21", "Hızlı ST"]
    CIZGI_DEGER += ["vwap", "orUst", "orAlt", "ema9", "ema21", "st2Deger"]
NL = len(CIZGI_DEGER)
# (Pine kodu, ad, giriş değişkeni, saniye)
TFS = ([("5","5 Dakika","tf5",300),("15","15 Dakika","tf15",900),("60","1 Saat","tf60",3600)] if SCALPER else
       [("60","1 Saat","tf60",3600),("240","4 Saat","tf240",14400),("D","Günlük","tfD",86400),("W","Haftalık","tfW",604800)])
NT = len(TFS)

def tuple_names(t):
    return [f"m{t}", f"e{t}", f"n{t}", f"w{t}", f"o{t}", f"t{t}", f"s{t}", f"y{t}", f"at{t}"] + [f"l{t}_{j:02d}" for j in range(1, NL+1)]

names_lit = ", ".join(f'"{n}"' for n in NAMES)
L = []
w = L.append

w('''//@version=5
// ══════════════════════════════════════════════════════════════════════════════
//  OTOMATİK EN İYİ STRATEJİ - BIST
//  Hangi hisseyi açarsan aç, bu repodaki 24 strateji + aralarındaki 276 ikili kombin,
//  4 zaman diliminde (1S / 4S / Günlük / Haftalık) o hissenin geçmişinde test edilir.
//  En iyi sonucu veren strateji/kombin ve zaman dilimi OTOMATİK seçilir:
//  AL/SAT etiketleri ve stratejinin çizgileri grafiğe kendiliğinden yerleşir.
//  Sağ altta küçük bir not kutusu sonucu ve nasıl değerlendirileceğini yazar.
//  Geçmiş performans geleceği garanti etmez. Yatırım tavsiyesi değildir.
// ══════════════════════════════════════════════════════════════════════════════
indicator("OTOMATİK EN İYİ STRATEJİ - BIST", shorttitle = "OTO-BIST", overlay = true, max_labels_count = 500, max_polylines_count = 20, max_bars_back = 1000)

// ════════════════════════════ AYARLAR ════════════════════════════
G1 = "1) TEST"
hazirKullan = input.bool(true, "BIST 100 için hazır test sonuçlarını kullan (hızlı)", group = G1, tooltip = "Açıkken listedeki hisselerde test yapılmaz, GitHub'da her ay hesaplanan en iyi kombin anında çizilir. Kapatırsan indikatör testi grafikte kendisi yapar.")
testBas = input.time(timestamp("01 Jan 2020 00:00 +0300"), "Test başlangıç tarihi", group = G1)
olcut = input.string("Toplam getiri", "En iyiyi seçme ölçütü", options = ["Toplam getiri", "Ortalama getiri", "Kazanma oranı"], group = G1)
minIslem = input.int(6, "Seçilmek için en az işlem", minval = 1, group = G1)
maxBar = input.int(40, "Bir işlemde en fazla bekleme (bar)", minval = 1, maxval = 500, group = G1, tooltip = "Strateji SAT vermese bile bu kadar bar sonra işlem kapatılır.")
komisyon = input.float(0.2, "Komisyon + kayma (al+sat toplam, %)", minval = 0, step = 0.05, group = G1)
hacimYok = input.bool(false, "Hacim verisi yok (AlphaTrend RSI kullansın)", group = G1)
kombinTest = input.bool(true, "İkili kombinleri de test et", group = G1, tooltip = "Kapatırsan sadece 25 tek strateji test edilir; indikatör daha hızlı açılır.")

G2 = "2) TEST EDİLECEK ZAMAN DİLİMLERİ"
tf60 = input.bool(false, "1 Saat", group = G2, inline = "tf", tooltip = "1 saatlik test işlemciyi en çok yoran testtir. İndikatör yavaşlarsa kapalı tut.")
tf240 = input.bool(true, "4 Saat", group = G2, inline = "tf")
tfD = input.bool(true, "Günlük", group = G2, inline = "tf")
tfW = input.bool(true, "Haftalık", group = G2, inline = "tf")

G3 = "3) GÖRÜNÜM"
notMod = input.string("Kısa", "Not kutusu", options = ["Kısa", "Detaylı", "Kapalı"], group = G3, tooltip = "Detaylı: seçimin nasıl yapıldığını ve sonucun nasıl değerlendirileceğini de yazar.")
notYer = input.string("Sağ alt", "Not kutusu konumu", options = ["Sağ alt", "Sağ üst", "Sol alt", "Sol üst"], group = G3)
cizgiGoster = input.bool(true, "Seçilen stratejinin çizgilerini çiz", group = G3)
etiketBar = input.int(300, "Etiketler son kaç barda gösterilsin", minval = 50, maxval = 900, group = G3)

G4 = "4) ORTAK KARAR (25. strateji)"
ortakBar = input.int(3, "Son kaç bardaki sinyaller sayılsın", minval = 1, maxval = 20, group = G4)
ortakEsik = input.int(4, "En az kaç strateji aynı yönde", minval = 2, maxval = 24, group = G4)

// ════════════════════════════ YARDIMCI FONKSİYONLAR ════════════════════════════
f_xsa(float src, int len, int wei) =>
    var float out = na
    ma = ta.sma(src, len)
    out := na(out) ? ma : (src * wei + out * (len - wei)) / len
    out

f_t3(float src, int len, float a) =>
    e1 = ta.ema(src, len)
    e2 = ta.ema(e1, len)
    e3 = ta.ema(e2, len)
    e4 = ta.ema(e3, len)
    e5 = ta.ema(e4, len)
    e6 = ta.ema(e5, len)
    c1 = -a * a * a
    c2 = 3 * a * a + 3 * a * a * a
    c3 = -6 * a * a - 3 * a - 3 * a * a * a
    c4 = 1 + 3 * a + a * a * a + 3 * a * a
    c1 * e6 + c2 * e5 + c3 * e4 + c4 * e3

f_sinir(float x) =>
    x > 0.99 ? 0.999 : x < -0.99 ? -0.999 : x

f_orta(int len) =>
    math.avg(ta.highest(high, len), ta.lowest(low, len))

// AL'da pozisyona gir, SAT'ta ya da maxBar dolunca çık. Pozisyon durumunu döndürür.
f_durum(bool al, bool sat) =>
    var bool poz = false
    var int girisBar = 0
    if poz and (sat or bar_index - girisBar >= maxBar)
        poz := false
    else if al and not poz
        poz := true
        girisBar := bar_index
    poz

// Aday listesi: 0-24 tek stratejiler, sonra 24 stratejinin tüm ikili kombinleri (276)
f_adayKur(int[] A, int[] B) =>
    if array.size(A) == 0
        for i = 0 to @NS@
            array.push(A, i)
            array.push(B, -1)
        for i = 0 to @NSm2@
            for j = i + 1 to @NSm1@
                array.push(A, i)
                array.push(B, j)

f_skor(int n, int w, float t, float e) =>
    n < minIslem ? -1e10 : olcut == "Toplam getiri" ? (e - 1) * 100 : olcut == "Ortalama getiri" ? t / n : w * 100.0 / n

// i < j olan ikili kombinin aday numarası (f_adayKur sırasıyla aynı)
f_ciftNo(int i, int j) =>
    @NS1@ + i * @NSm1@ - int(i * (i - 1) / 2) + (j - i - 1)

// Adayın bu mumdaki durum değişimini işler; güncel en iyi aday numarasını döndürür
f_isle(int c, int[] cA, int[] cB, bool[] poz, bool[] onceki, float[] giris, int[] adet, int[] kaz, float[] top, float[] ser, float[] serY, float[] skor, int enIyi, bool sonYil) =>
    a = array.get(cA, c)
    b = array.get(cB, c)
    simdi = array.get(poz, a) ? (b < 0 ? true : array.get(poz, math.max(b, 0))) : false
    once = array.get(onceki, a) ? (b < 0 ? true : array.get(onceki, math.max(b, 0))) : false
    yeniEnIyi = enIyi
    if simdi and not once
        array.set(giris, c, close)
    else if not simdi and once and not na(array.get(giris, c))
        r = (close / array.get(giris, c) - 1) * 100 - komisyon
        array.set(giris, c, na)
        array.set(adet, c, array.get(adet, c) + 1)
        if r > 0
            array.set(kaz, c, array.get(kaz, c) + 1)
        array.set(top, c, array.get(top, c) + r)
        array.set(ser, c, array.get(ser, c) * (1 + r / 100))
        if sonYil
            array.set(serY, c, array.get(serY, c) * (1 + r / 100))
        eski = array.get(skor, c)
        yeni = f_skor(array.get(adet, c), array.get(kaz, c), array.get(top, c), array.get(ser, c))
        array.set(skor, c, yeni)
        if c == enIyi and yeni < eski
            for d = 0 to @NCm1@
                if array.get(skor, d) > array.get(skor, yeniEnIyi)
                    yeniEnIyi := d
        else if yeni > array.get(skor, yeniEnIyi)
            yeniEnIyi := c
    yeniEnIyi

// ════════════════════════════ TÜM STRATEJİLER + TEST (her zaman diliminde ayrı çalışır) ════════════════════════════
f_hepsi(bool aktif) =>
    ema5 = ta.ema(close, 5)
    ema13 = ta.ema(close, 13)
    ema14 = ta.ema(close, 14)
    ema22 = ta.ema(close, 22)
    ema34 = ta.ema(close, 34)
    ema50 = ta.ema(close, 50)
    sma10 = ta.sma(close, 10)
    sma20 = ta.sma(close, 20)
    sma200 = ta.sma(close, 200)
    rsi14 = ta.rsi(close, 14)
    mfi14 = ta.mfi(hlc3, 14)
    [mL, mS, mH] = ta.macd(close, 12, 26, 9)
    [m2L, m2S, m2H] = ta.macd(close, 10, 20, 9)
    // 01 RSI Karpuzlu
    rsiK = ta.rsi(close, 22)
    rsiKema = ta.ema(rsiK, 66)
    b01 = ta.crossover(rsiK, rsiKema)
    s01 = ta.crossunder(rsiK, rsiKema)
    // 02 Dip Bulucu (Banker)
    stoch27 = (close - ta.lowest(low, 27)) / (ta.highest(high, 27) - ta.lowest(low, 27)) * 100
    fx1 = f_xsa(stoch27, 5, 1)
    fx2 = f_xsa(fx1, 3, 1)
    fonTrend = (3 * fx1 - 2 * fx2 - 50) * 1.032 + 50
    typ = (2 * close + high + low + open) / 5
    lol34 = ta.lowest(low, 34)
    hoh34 = ta.highest(high, 34)
    bogaAyi = ta.ema((typ - lol34) / (hoh34 - lol34) * 100, 13)
    b02 = ta.crossover(fonTrend, bogaAyi) and bogaAyi < 25
    s02 = ta.crossunder(fonTrend, bogaAyi)
    // 03 Dip Bulucu-2 (VixFix)
    wvfTepe = ta.highest(close, 22)
    wvf = (wvfTepe - low) / wvfTepe * 100
    wvfUst = ta.sma(wvf, 20) + 2.0 * ta.stdev(wvf, 20)
    wvfYuksek = ta.highest(wvf, 50) * 0.85
    wvfDip = wvf >= wvfUst or wvf >= wvfYuksek
    b03 = wvfDip and not wvfDip[1]
    s03 = false
    // 04 AlphaTrend
    atAtr = ta.sma(ta.tr, 14)
    atKosul = hacimYok ? rsi14 >= 50 : mfi14 >= 50
    float alpha = 0.0
    alpha := atKosul ? (low - atAtr < nz(alpha[1]) ? nz(alpha[1]) : low - atAtr) : (high + atAtr > nz(alpha[1]) ? nz(alpha[1]) : high + atAtr)
    atAlHam = ta.crossover(alpha, alpha[2])
    atSatHam = ta.crossunder(alpha, alpha[2])
    atK1 = ta.barssince(atAlHam)
    atK2 = ta.barssince(atSatHam)
    atO1 = ta.barssince(atAlHam[1])
    atO2 = ta.barssince(atSatHam[1])
    b04 = atAlHam and atO1 > atK2
    s04 = atSatHam and atO2 > atK1
    var bool atYukari = false
    if b04
        atYukari := true
    if s04
        atYukari := false
    // 05 SuperTrend (10, 3)
    [stDeger, stYon] = ta.supertrend(3.0, 10)
    stYukari = stYon < 0
    b05 = stYukari and not stYukari[1]
    s05 = not stYukari and stYukari[1]
    // 06 AlphaTrend + SuperTrend
    ikisi = atYukari and stYukari
    b06 = ikisi and not ikisi[1]
    s06 = not ikisi and ikisi[1]
    // 07 Parabolic SAR
    psar = ta.sar(0.02, 0.02, 0.2)
    psarYon = psar < close ? 1 : -1
    b07 = psarYon == 1 and psarYon[1] == -1
    s07 = psarYon == -1 and psarYon[1] == 1
    // 08 MACD Dip
    b08 = ta.crossover(mL, mS) and mL <= 0
    s08 = ta.crossunder(mL, mS)
    // 09 ALMA
    alma = ta.alma(close, 14, 0.85, 6)
    almaYukari = alma >= alma[1]
    b09 = almaYukari and not almaYukari[1]
    s09 = not almaYukari and almaYukari[1]
    // 10 T3 Tillson
    t3 = f_t3((high + low + 2 * close) / 4, 8, 0.7)
    t3Yukari = t3 > t3[1]
    b10 = t3Yukari and not t3Yukari[1]
    s10 = not t3Yukari and t3Yukari[1]
    // 11 Bollinger Orta Bant
    b11 = ta.crossover(close, sma20)
    s11 = ta.crossunder(close, sma20)
    // 12 Bollinger20 x EMA50
    b12 = ta.crossover(sma20, ema50)
    s12 = ta.crossunder(sma20, ema50)
    // 13 EMA 5x13
    b13 = ta.crossover(ema5, ema13)
    s13 = ta.crossunder(ema5, ema13)
    // 14 EMA 5x22
    b14 = ta.crossover(ema5, ema22)
    s14 = ta.crossunder(ema5, ema22)
    // 15 WMA 9x15
    wma9 = ta.wma(close, 9)
    wma15 = ta.wma(close, 15)
    b15 = ta.crossover(wma9, wma15)
    s15 = ta.crossunder(wma9, wma15)
    // 16 SMMA 21x55
    smma21 = ta.rma(close, 21)
    smma55 = ta.rma(close, 55)
    b16 = ta.crossover(smma21, smma55)
    s16 = ta.crossunder(smma21, smma55)
    // 17 Darvas Kutusu (7)
    dLL = ta.lowest(low, 7)
    dK1 = ta.highest(high, 7)
    dK2 = ta.highest(high, 6)
    dK3 = ta.highest(high, 5)
    dNH = ta.valuewhen(high > dK1[1], high, 0)
    dKutu = ta.barssince(high > dK1[1]) == 5 and dK3 < dK2
    dUst = ta.valuewhen(dKutu, dNH, 0)
    dAlt = ta.valuewhen(dKutu, dLL, 0)
    b17 = ta.crossover(close, dUst)
    s17 = ta.crossunder(close, dAlt)
    // 18 Fisher Dip
    fH = ta.highest(hl2, 7)
    fL = ta.lowest(hl2, 7)
    float fDeger = 0.0
    fDeger := f_sinir(0.66 * ((hl2 - fL) / (fH - fL) - 0.5) + 0.67 * nz(fDeger[1]))
    float fish = 0.0
    fish := 0.5 * math.log((1 + fDeger) / (1 - fDeger)) + 0.5 * nz(fish[1])
    fTet = fish[1]
    b18 = ta.crossover(fish, fTet) and fTet <= -1.5
    s18 = ta.crossunder(fish, fTet) and fTet >= 1.5
    // 19 CCI Dip
    cci = ta.cci(hlc3, 20)
    b19 = ta.crossover(cci, -100)
    s19 = ta.crossunder(cci, 100)
    // 20 TSI Dip
    tsi = ta.tsi(close, 3, 9)
    b20 = tsi <= -0.8 and tsi[1] > -0.8
    s20 = tsi >= 0.8 and tsi[1] < 0.8
    // 21 MACD Kesişimi (haftalık grafikte = eski "Haftalık MACD")
    b21 = ta.crossover(mL, mS)
    s21 = ta.crossunder(mL, mS)
    // 22 Erik Kombo
    erikKesisim = ta.crossover(ema5, sma10)
    rsi5 = ta.rsi(close, 5)
    rsi9 = ta.rsi(close, 9)
    hma9 = ta.hma(close, 9)
    donusum9 = f_orta(9)
    kijun26 = f_orta(26)
    b22 = erikKesisim and close > donusum9 and mL > mS and rsi5 > rsi9 and mfi14 > 50 and hma9 < close and close > kijun26
    s22 = ta.crossunder(ema5, sma10)
    // 23 EMA Kombo
    b23 = ta.crossover(ema5, ema14) and close > ema34 and m2L > m2S and rsi14 > 50
    s23 = ta.crossunder(ema5, ema14)
    // 24 Bollinger Kombo
    b24 = ta.crossover(close, sma20) and close >= sma200 and m2L > m2S
    s24 = ta.crossunder(close, sma20)
''')
if SCALPER:
    w('''    // 25 VWAP Kesişimi (gün içi VWAP)
    vwap = ta.vwap(hlc3)
    b25 = ta.crossover(close, vwap)
    s25 = ta.crossunder(close, vwap)
    // 26 İlk Mum Kırılımı: günün ilk mumunun tepesi kırılınca AL, dibi kırılınca SAT
    var float orUst = na
    var float orAlt = na
    if session.isfirstbar
        orUst := high
        orAlt := low
    b26 = ta.crossover(close, orUst) and not session.isfirstbar
    s26 = ta.crossunder(close, orAlt)
    // 27 RSI(2) Dip
    rsi2 = ta.rsi(close, 2)
    b27 = ta.crossover(rsi2, 10)
    s27 = ta.crossover(rsi2, 70)
    // 28 Stokastik RSI
    srsi = ta.rsi(close, 14)
    sK = ta.sma(ta.stoch(srsi, srsi, srsi, 14), 3)
    sD = ta.sma(sK, 3)
    b28 = ta.crossover(sK, sD) and sK < 20
    s28 = ta.crossunder(sK, sD) and sK > 80
    // 29 EMA 9x21 + VWAP
    ema9 = ta.ema(close, 9)
    ema21 = ta.ema(close, 21)
    b29 = ta.crossover(ema9, ema21) and close > vwap
    s29 = ta.crossunder(ema9, ema21)
    // 30 Hızlı SuperTrend (7, 2)
    [st2Deger, st2Yon] = ta.supertrend(2.0, 7)
    st2Yukari = st2Yon < 0
    b30 = st2Yukari and not st2Yukari[1]
    s30 = not st2Yukari and st2Yukari[1]
    // 31 Bollinger Sıkışma Kırılımı
    bbSapma = ta.stdev(close, 20)
    bbGen = 4.0 * bbSapma / sma20
    sikisma = bbGen <= ta.lowest(bbGen, 50) * 1.1
    b31 = ta.crossover(close, sma20 + 2.0 * bbSapma) and sikisma[1]
    s31 = ta.crossunder(close, sma20)
''')
w(f"    // {NS + 1} Ortak Karar")
w("    alDizi = array.from(" + ", ".join(f"b{i:02d}" for i in range(1,NS+1)) + ")")
w("    satDizi = array.from(" + ", ".join(f"s{i:02d}" for i in range(1,NS+1)) + ")")
w(f'''    var int[] sonAl = array.new_int({NS}, -100000)
    var int[] sonSat = array.new_int({NS}, -100000)
    int alSay = 0
    int satSay = 0
    for i = 0 to {NS - 1}''')
w('''        if array.get(alDizi, i)
            array.set(sonAl, i, bar_index)
        if array.get(satDizi, i)
            array.set(sonSat, i, bar_index)
        if bar_index - array.get(sonAl, i) < ortakBar
            alSay += 1
        if bar_index - array.get(sonSat, i) < ortakBar
            satSay += 1
    bOrtak = alSay >= ortakEsik and nz(alSay[1]) < ortakEsik and alSay > satSay
    sOrtak = satSay >= ortakEsik and nz(satSay[1]) < ortakEsik and satSay > alSay
    // ── pozisyon durumları
''')
for i in range(1,NS+1):
    w(f"    p{i:02d} = f_durum(b{i:02d}, s{i:02d})")
w(f"    p{NS+1:02d} = f_durum(bOrtak, sOrtak)")
w("    poz = array.from(" + ", ".join(f"p{i:02d}" for i in range(1,NS+2)) + ")")
w('''    // ── adayların testi: AL'da kapanıştan gir, SAT'ta kapanıştan çık
    var int[] cA = array.new_int()
    var int[] cB = array.new_int()
    f_adayKur(cA, cB)
    var bool[] onceki = array.new_bool(@NS1@, false)
    var float[] giris = array.new_float(@NC@, na)
    var int[] adet = array.new_int(@NC@, 0)
    var int[] kaz = array.new_int(@NC@, 0)
    var float[] top = array.new_float(@NC@, 0.0)
    var float[] ser = array.new_float(@NC@, 1.0)
    var float[] serY = array.new_float(@NC@, 1.0)
    var float[] skor = array.new_float(@NC@, -1e10)
    var int enIyi = 0
    var int[] islendi = array.new_int(@NC@, -1)
    var float alTutBas = na
    if aktif and time >= testBas
        if na(alTutBas)
            alTutBas := close
        sonYil = time >= timenow - @SONGUN@ * 86400000
        // Hız: sadece bu mumda durumu DEĞİŞEN stratejilere ve onların kombinlerine bakılır
        for k = 0 to @NS@
            if array.get(poz, k) != array.get(onceki, k)
                for m = -1 to (kombinTest and k < @NS@ ? @NSm1@ : -1)
                    // Pine v5'te "and" iki tarafı da hesaplar: c = -1 iken dizi okunmasın diye iç içe if
                    c = m == -1 ? k : m == k ? -1 : f_ciftNo(math.min(k, m), math.max(k, m))
                    if c >= 0
                        if array.get(islendi, c) != bar_index
                            array.set(islendi, c, bar_index)
                            enIyi := f_isle(c, cA, cB, poz, onceki, giris, adet, kaz, top, ser, serY, skor, enIyi, sonYil)
    for k = 0 to @NS@
        array.set(onceki, k, array.get(poz, k))
    float maske = 0.0
    for k = 0 to @NS@
        if array.get(poz, k)
            maske += math.pow(2, k)
    nB = array.get(adet, enIyi)
    ortB = nB > 0 ? array.get(top, enIyi) / nB : 0.0
    alTut = (close / alTutBas - 1) * 100
''')
lines_vals = CIZGI_DEGER
assert len(lines_vals) == NL
w("    [maske, enIyi, nB, array.get(kaz, enIyi), ortB, (array.get(ser, enIyi) - 1) * 100, array.get(skor, enIyi), (array.get(serY, enIyi) - 1) * 100, alTut, " + ", ".join(lines_vals) + "]")
w("")
w("// ════════════════════════════ HAZIR SONUÇLAR (araclar/backtest.py her ay yazar) ════════════════════════════")
if HAZIR:
    hs = HAZIR["hisseler"]
    kodlar = list(hs.keys())
    e = [hs[k]["en_iyi"] for k in kodlar]
    w(f'HAZIR_TARIH = "{HAZIR["tarih"]}"')
    w("hIdx = switch syminfo.ticker")
    for i, k in enumerate(kodlar):
        w(f'    "{k}" => {i}')
    w("    => -1")
    w("// hazır sonucun zaman dilimi (basit/simple değer): gerekmeyen zaman dilimlerinde sadece 50 mum hesaplanır")
    w("hTfS = switch syminfo.ticker")
    for i, k in enumerate(kodlar):
        w(f'    "{k}" => {e[i]["tf"]}')
    w("    => -1")
    fmt = lambda xs: ", ".join(str(x) for x in xs)
    w(f"var int[] hAday = array.from({fmt(x['aday'] for x in e)})")
    w(f"var int[] hTf = array.from({fmt(x['tf'] for x in e)})")
    w(f"var int[] hN = array.from({fmt(x['islem'] for x in e)})")
    # scalper'da: hAlTut = kâr faktörü, hYil = kontrol dönemi getirisi, hYillik = günlük işlem sayısı
    if SCALPER:
        alanlar = {"hKaz": lambda x: x["kazanma"], "hTop": lambda x: x["toplam"], "hAlTut": lambda x: x["kar_faktoru"],
                   "hYil": lambda x: x["kontrol"]["toplam"], "hYillik": lambda x: x["gunluk_islem"]}
    else:
        alanlar = {"hKaz": lambda x: x["kazanma"], "hTop": lambda x: x["toplam"], "hAlTut": lambda x: x["al_tut"],
                   "hYil": lambda x: x["son_yil"], "hYillik": lambda x: x["yillik"]}
    for ad, al in alanlar.items():
        w(f"var float[] {ad} = array.from({fmt(float(al(x)) for x in e)})")
    w("var string[] hBas = array.from(" + ", ".join('"' + x["baslangic"] + '"' for x in e) + ")")
else:
    w('HAZIR_TARIH = "-"')
    w("hIdx = -1")
    w("hTfS = -1")
    w("var int[] hAday = array.from(0)")
    w("var int[] hTf = array.from(2)")
    w("var int[] hN = array.from(0)")
    for ad in ("hKaz", "hTop", "hAlTut", "hYil", "hYillik"):
        w(f"var float[] {ad} = array.from(0.0)")
    w('var string[] hBas = array.from("-")')
w('hazir = hazirKullan and hIdx >= 0 and syminfo.prefix == "BIST"')
w("hI = math.max(hIdx, 0)")
w("")
w("// ════════════════════════════ 4 ZAMAN DİLİMİNDE ÇALIŞTIR ════════════════════════════")
for t,(tf,ad,flag,_) in enumerate(TFS):
    w(f"[{', '.join(tuple_names(t))}] = request.security(syminfo.tickerid, \"{tf}\", f_hepsi({flag} and not hazir), calc_bars_count = (hazir ? hTfS == {t} : {flag}) ? (hazir ? 1500 : 5000) : 50)")
w(f'''
var string[] adlar = array.from({names_lit})
var string[] tfKod = array.from({", ".join(chr(34) + x[0] + chr(34) for x in TFS)})
var string[] tfAd = array.from({", ".join(chr(34) + x[1] + chr(34) for x in TFS)})
var int[] tfSaniye = array.from({", ".join(str(x[3]) for x in TFS)})
var int[] cA = array.new_int()
var int[] cB = array.new_int()
f_adayKur(cA, cB)

f_adayAd(int c) =>
    a = array.get(cA, c)
    b = array.get(cB, c)
    b < 0 ? array.get(adlar, a) : array.get(adlar, a) + " + " + array.get(adlar, math.max(b, 0))

// En iyi zaman dilimi: en yüksek skoru veren
skorlarTf = array.from({", ".join(f"{x[2]} ? nz(s{i}, -1e10) : -1e10" for i, x in enumerate(TFS))})
gecerli = hazir or array.max(skorlarTf) > -1e9
secTf = hazir ? array.get(hTf, hI) : array.indexof(skorlarTf, array.max(skorlarTf))
''')
def sw(name, rettype, arms, default):
    w(f"{name} =>")
    w("    switch t")
    for k,v in arms:
        w(f"        {k} => {v}")
    w(f"        => {default}")
# per-TF scalar getters
for fld, idx, default in [("aday",1,"0"),("adet",2,"0.0"),("kaz",3,"0.0"),("ort",4,"0.0"),("top",5,"0.0"),("yil",6+1,"0.0"),("altut",8,"0.0")]:
    w(f"f_{fld}(int t) =>")
    w("    switch t")
    for t in range(NT):
        w(f"        {t} => {tuple_names(t)[idx]}")
    w(f"        => {default}")
w("")
w("// t zaman diliminin i bar önceki pozisyon maskesi")
w("f_maske(int t, int i) =>")
w("    switch t")
for t in range(NT):
    w(f"        {t} => m{t}[i]")
w("        => 0.0")
w("")
w("f_bit(float m, int k) =>")
w("    na(m) ? false : math.floor(m / math.pow(2, k)) % 2 == 1")
w("")
w("// aday c, t zaman diliminde i bar önce pozisyonda mı?")
w('''f_poz(int t, int c, int i) =>
    m = f_maske(t, i)
    a = array.get(cA, c)
    b = array.get(cB, c)
    f_bit(m, a) ? (b < 0 ? true : f_bit(m, b)) : false
''')
w("// çizgi değerleri: t zaman dilimi, çizgi no (1-19), i bar önce")
w("f_cizgi(int t, int lid, int i) =>")
w("    switch t * 100 + lid")
for t in range(NT):
    for j in range(1, NL+1):
        w(f"        {t*100+j} => l{t}_{j:02d}[i]")
w("        => float(na)")
w("")
w("// strateji (0 tabanlı) -> çizgi numaraları")
for slot in (0,1):
    w(f"f_strCizgi{slot+1}(int s) =>")
    w("    switch s")
    for k,v in LINES.items():
        if len(v) > slot:
            w(f"        {k-1} => {v[slot]}")
    w("        => 0")
w('''
var string[] cizgiAd = array.from(@CIZGIAD@)
var color[] renkler = array.from(color.new(#2962FF, 0), color.new(#FF9800, 0), color.new(#9C27B0, 0), color.new(#00BCD4, 0))

f_yuzde(float x) =>
    na(x) ? "-" : (x >= 0 ? "+" : "") + str.tostring(x, "0.0") + "%"

// ════════════════════════════ GRAFİĞE OTOMATİK YERLEŞTİRME ════════════════════════════
secAday = hazir ? array.get(hAday, hI) : gecerli ? int(f_aday(secTf)) : 0
tfUygun = gecerli and array.get(tfSaniye, secTf) >= timeframe.in_seconds()

var label[] etiketler = array.new<label>()
var polyline[] cizgiler = array.new<polyline>()
var table notTablo = na

if barstate.islast and (not barstate.isrealtime or barstate.isnew)
    while array.size(etiketler) > 0
        label.delete(array.pop(etiketler))
    while array.size(cizgiler) > 0
        polyline.delete(array.pop(cizgiler))
    lim = math.min(etiketBar, bar_index - 1)
    if tfUygun
        // AL / SAT etiketleri
        float girisFiyat = na
        for i = lim to 0
            simdi = f_poz(secTf, secAday, i)
            once = f_poz(secTf, secAday, i + 1)
            if simdi and not once
                girisFiyat := close[i]
                array.push(etiketler, label.new(bar_index - i, low[i], "AL", yloc = yloc.belowbar, style = label.style_label_up, color = color.new(#089981, 0), textcolor = color.white, size = size.small))
            if not simdi and once
                sonuc = na(girisFiyat) ? "" : "\\n" + f_yuzde((close[i] / girisFiyat - 1) * 100 - komisyon)
                array.push(etiketler, label.new(bar_index - i, high[i], "SAT" + sonuc, yloc = yloc.abovebar, style = label.style_label_down, color = color.new(#F23645, 0), textcolor = color.white, size = size.small))
                girisFiyat := na
        // Seçilen stratejinin çizgileri
        if cizgiGoster
            a = array.get(cA, secAday)
            b = array.get(cB, secAday)
            cizNo = array.from(f_strCizgi1(a), f_strCizgi2(a), b < 0 ? 0 : f_strCizgi1(b), b < 0 ? 0 : f_strCizgi2(b))
            cizilen = array.new_int()
            for j = 0 to 3
                lid = array.get(cizNo, j)
                if lid > 0 and not array.includes(cizilen, lid)
                    array.push(cizilen, lid)
                    noktalar = array.new<chart.point>()
                    for i = lim to 0
                        v = f_cizgi(secTf, lid, i)
                        if not na(v)
                            array.push(noktalar, chart.point.from_index(bar_index - i, v))
                    if array.size(noktalar) > 1
                        array.push(cizgiler, polyline.new(noktalar, line_color = array.get(renkler, array.size(cizilen) - 1), line_width = 2))
                    sonDeger = f_cizgi(secTf, lid, 0)
                    if not na(sonDeger)
                        array.push(etiketler, label.new(bar_index + 1, sonDeger, array.get(cizgiAd, lid - 1), style = label.style_label_left, color = color.new(color.black, 100), textcolor = array.get(renkler, array.size(cizilen) - 1), size = size.tiny))

    // ── Not kutusu (küçük, köşede)
    if notMod != "Kapalı"
        nYer = switch notYer
            "Sağ üst" => position.top_right
            "Sol alt" => position.bottom_left
            "Sol üst" => position.top_left
            => position.bottom_right
        if not na(notTablo)
            table.delete(notTablo)
        notTablo := table.new(nYer, 1, 9, bgcolor = color.new(#131722, 15), border_width = 0, frame_color = color.new(#363A45, 0), frame_width = 1)
        soluk = color.new(#9598A1, 0)
        if not gecerli
            table.cell(notTablo, 0, 0, "Yeterli işlem yok: test tarihini geriye al\\nya da 'en az işlem' sayısını düşür.", text_color = soluk, text_size = size.tiny, text_halign = text.align_left)
        else
            nCanli = f_adet(secTf)
            n = hazir ? array.get(hN, hI) : nCanli
            kazOran = hazir ? array.get(hKaz, hI) : nCanli > 0 ? f_kaz(secTf) * 100.0 / nCanli : 0.0
            topG = hazir ? array.get(hTop, hI) : f_top(secTf)
            alTut = hazir ? array.get(hAlTut, hI) : f_altut(secTf)
            yil = hazir ? array.get(hYil, hI) : f_yil(secTf)
            k1 = topG > alTut
            k2 = kazOran >= 50
            k3 = yil > 0
            puan = (k1 ? 1 : 0) + (k2 ? 1 : 0) + (k3 ? 1 : 0)
            karar = puan == 3 ? "GÜÇLÜ" : puan == 2 ? "ORTA" : "ZAYIF"
            kararRenk = puan == 3 ? color.new(#22AB94, 0) : puan == 2 ? color.new(#FF9800, 0) : color.new(#F23645, 0)
            simdiPoz = f_poz(secTf, secAday, 0)
            table.cell(notTablo, 0, 0, "★ " + f_adayAd(secAday) + " • " + array.get(tfAd, secTf) + (hazir ? " • hazır test " + HAZIR_TARIH : ""), text_color = color.white, text_size = size.small, text_halign = text.align_left)
            table.cell(notTablo, 0, 1, str.tostring(n) + " işlem • %" + str.tostring(kazOran, "0") + " kazanç • Toplam " + f_yuzde(topG) + " (Al-Tut " + f_yuzde(alTut) + ")", text_color = soluk, text_size = size.tiny, text_halign = text.align_left)
            table.cell(notTablo, 0, 2, "Karar: " + karar + " (" + str.tostring(puan) + "/3) • Son 1 yıl " + f_yuzde(yil) + " • Şu an: " + (simdiPoz ? "AL'da" : "beklemede"), text_color = kararRenk, text_size = size.tiny, text_halign = text.align_left)
            r = 3
            if not tfUygun
                table.cell(notTablo, 0, r, "⚠ Sinyalleri görmek için grafiği " + array.get(tfAd, secTf) + " yap", text_color = color.new(#FF9800, 0), text_size = size.tiny, text_halign = text.align_left)
                r += 1
            if notMod == "Detaylı"
                nasil = hazir ? "NASIL SEÇİLDİ: BIST 100 hisseleri her ay GitHub'da test edilir\\n(son: " + HAZIR_TARIH + "). Bu hissede 24 strateji + 276 kombin, 4S/G/H\\nzaman dilimlerinde " + array.get(hBas, hI) + "'den beri denendi; yıllık\\ngetirisi en yüksek olan seçildi (en az 6 işlem). Yıllık: " + f_yuzde(array.get(hYillik, hI)) : "NASIL SEÇİLDİ: 24 strateji + 276 ikili kombin, seçili zaman\\ndilimlerinde " + str.tostring(year(testBas)) + "'den beri test edildi. " + olcut + " en\\nyüksek olan seçildi (en az " + str.tostring(minIslem) + " işlem şartıyla)."
                table.cell(notTablo, 0, r, nasil, text_color = soluk, text_size = size.tiny, text_halign = text.align_left)
                table.cell(notTablo, 0, r + 1, "KURAL: AL'da kapanıştan girilir, SAT'ta (ya da en fazla\\n" + str.tostring(maxBar) + " bar sonra) çıkılır. Her işlemden %" + str.tostring(komisyon) + " komisyon düşülür.", text_color = soluk, text_size = size.tiny, text_halign = text.align_left)
                table.cell(notTablo, 0, r + 2, "NASIL KARAR VERİLİR (3 şart):\\n" + (k1 ? "✓" : "✗") + " Toplam getiri Al-Tut'tan yüksek\\n" + (k2 ? "✓" : "✗") + " Kazanma oranı %50 veya üstü\\n" + (k3 ? "✓" : "✗") + " Son 1 yılda da kârda\\n3/3 GÜÇLÜ: sinyale güvenilebilir • 2/3 ORTA: dikkatli ol\\n0-1/3 ZAYIF: bu hissede sinyale güvenme", text_color = soluk, text_size = size.tiny, text_halign = text.align_left)
                table.cell(notTablo, 0, r + 3, "Geçmiş sonuç geleceği garanti etmez. Yatırım tavsiyesi değildir.", text_color = color.new(#787B86, 0), text_size = size.tiny, text_halign = text.align_left)
    else if not na(notTablo)
        table.delete(notTablo)

// ════════════════════════════ ALARMLAR ════════════════════════════
plot(na, "OTO-BIST", display = display.none)
pozSimdi = gecerli ? f_poz(secTf, secAday, 0) : false
pozOnce = gecerli ? f_poz(secTf, secAday, 1) : false
alertcondition(pozSimdi and not pozOnce, "Otomatik seçim - AL", "{{ticker}}: Otomatik seçilen strateji AL verdi")
alertcondition(not pozSimdi and pozOnce, "Otomatik seçim - SAT", "{{ticker}}: Otomatik seçilen strateji SAT verdi")
if barstate.isconfirmed and gecerli and pozSimdi != pozOnce
    alert(syminfo.ticker + (pozSimdi ? " AL • " : " SAT • ") + f_adayAd(secAday) + " • " + array.get(tfAd, secTf), alert.freq_once_per_bar_close)
''')
metin = "\n".join(L) + "\n"
for a, b in {"@NS1@": NS + 1, "@NSm1@": NS - 1, "@NSm2@": NS - 2, "@NS@": NS, "@NCm1@": NC - 1, "@NC@": NC,
             "@SONGUN@": 30 if SCALPER else 365,
             "@CIZGIAD@": ", ".join(chr(34) + x + chr(34) for x in CIZGI_ADLARI)}.items():
    metin = metin.replace(a, str(b))
if SCALPER:
    import scalper_metin
    metin = scalper_metin.uyarla(metin)


CIKTI.write_text(metin, encoding="utf-8")
print("Pine dosyası yazıldı" + (f" ({len(HAZIR['hisseler'])} hazır hisse)" if HAZIR else " (hazır sonuç yok)"))
