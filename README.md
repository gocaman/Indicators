# İndikatörler

## ⭐ OTOMATİK EN İYİ STRATEJİ - BIST (tek indikatör)

Dosya: **`0. OTOMATİK EN İYİ STRATEJİ - BIST.txt`**

**İki mod, tek indikatör:** Grafiğin zaman dilimine göre mod kendiliğinden değişir.
| Grafik | Mod | Test edilen zaman dilimleri |
|---|---|---|
| 1 saat ve altı (1dk, 5dk, 15dk, 30dk, 1S, 2S) | **GÜN İÇİ** (scalper) | 5 dk / 15 dk / 1 saat, 31 strateji, gece taşıma yok |
| 4 saat ve üstü (4S, Günlük, Haftalık) | **NORMAL** | 4 saat / Günlük / Haftalık, 24 strateji |

Hangi modda olduğunu ve o hisse için en iyi zaman dilimini aklında tutman gerekmez. Grafiğin üstündeki mavi başlığın son satırı bunu her zaman yazar, ör. `GÜN İÇİ MOD (5dk/15dk/1S) • 👉 Grafiği 15 Dakika yap`. Doğru zaman dilimindeysen `✓ Grafik doğru: 15 Dakika` yazar.

BIST 100'de **herhangi bir hisseyi açtığında** indikatör kendiliğinden şunları yapar:
1. Bu repodaki **24 stratejiyi** ve bunların **276 ikili kombinini** (ör. "EMA 5x13 + SuperTrend") o hissenin geçmişinde test eder.
2. Testi moduna göre 3 zaman diliminin her birinde ayrı ayrı yapar (normal: 4 Saat / Günlük / Haftalık).
3. En iyi sonucu veren strateji/kombin ve zaman dilimini **otomatik seçer** ve grafiğe yerleştirir:
   - AL / SAT etiketleri (SAT etiketinde o işlemin getirisi yazar),
   - seçilen indikatörlerin çizgileri (SuperTrend, AlphaTrend, EMA'lar vb.).
4. Sağ altta **küçük bir not** gösterir:
   ```
   ★ EMA 5x13 + SuperTrend • Günlük
   18 işlem • %61 kazanç • Toplam +84% (Al-Tut +40%)
   Karar: GÜÇLÜ (3/3) • Son 1 yıl +12% • Şu an: AL'da
   ```
   Ayarlardan **Not kutusu = Detaylı** seçersen seçimin nasıl yapıldığını ve nasıl karar verileceğini de yazar. **Kapalı** seçersen tamamen gizlenir.

Ücretsiz TradingView hesabında tek indikatör hakkıyla çalışır. Ücretsiz hesap tek grafik açtırdığı için indikatör grafiğin zaman dilimini kendisi değiştiremez. En iyi sonuç başka bir zaman diliminde çıkarsa not kutusu bunu söyler (ör. "⚠ Sinyalleri görmek için grafiği Günlük yap").

### BIST 100 hazır sonuçları (hızlı açılış)
Her ayın 1'inde GitHub'da otomatik bir görev (`.github/workflows/bist100-test.yml`) çalışır:
1. Yahoo Finance'ten BIST 100 hisselerinin verisini çeker. Hisse listesi `araclar/bist100.txt` dosyasındadır.
2. Her hissede 24 stratejiyi ve 276 kombini 4 Saat, Günlük ve Haftalık'ta test eder (`araclar/backtest.py`). 4 Saatlik test son 2 yılla sınırlıdır, çünkü Yahoo daha eskisini vermez.
3. Her hissenin en iyi kombinini indikatöre gömer (`araclar/pine_uret.py`). Özet tablo `veri/BIST100_SONUCLAR.md` dosyasına yazılır.

Bu sayede listedeki bir hisseyi açtığında indikatör test yapmaz ve hazır sonucu **anında** çizer. Not kutusunda "hazır test" ve tarih yazar. Listede olmayan bir hissede indikatör testi bugünkü gibi kendisi yapar.

Görevi elle çalıştırmak için GitHub'da **Actions → BIST100 strateji testi → Run workflow**'a bas. Görev bitince güncel indikatör kodunu TradingView'deki koda yeniden yapıştırman gerekir. TradingView kodu GitHub'dan kendisi çekemez.

### Değerlendirme: nasıl karar verilir?
Not kutusundaki **Karar** satırı 3 şartı kontrol eder:

| Şart | Neden önemli |
|---|---|
| ✓ Toplam getiri **Al-Tut**'tan yüksek | Strateji, hisseyi alıp hiç dokunmadan beklemekten daha iyi olmalı. TL enflasyonu yüzünden BIST'te bu çok önemli. |
| ✓ Kazanma oranı **%50 veya üstü** | İşlemlerin çoğu kârla kapanmalı. |
| ✓ **Son 1 yılda da** kârda | Eskiden işe yarayıp artık çalışmayan stratejiyi eler. |

- **3/3 GÜÇLÜ:** Sinyale güvenilebilir.
- **2/3 ORTA:** Dikkatli ol, başka bir onay ara.
- **0–1/3 ZAYIF:** Bu hissede sinyallere güvenme.

> Önemli: 300'den fazla aday arasından en iyisini seçmek, "geçmişe fazla uyan" (şans eseri iyi görünen) bir sonuç doğurabilir. "Son 1 yıl" ve "Al-Tut" şartları bu riski azaltmak için var. Ayrıca işlem sayısı az olan (varsayılan 6'dan az) adaylar hiç seçilmez.

### Kurulum
1. Dosyanın tüm içeriğini kopyala.
2. TradingView'de **Pine Editor**'ü aç, yeni indikatör oluştur, içini silip kodu yapıştır.
3. **Kaydet** ve **Grafiğe ekle**'ye bas.
   (Pine Editor telefon uygulamasında yoksa bu adımı bir kez bilgisayardan ya da telefon tarayıcısının masaüstü modundan yap. Sonra telefonda "Göstergeler → Benim komut dosyalarım" altında çıkar.)
4. Artık hangi hisseyi açarsan aç indikatör kendini o hisseye göre ayarlar.

### Ayarlar (dişli simgesi)
| Ayar | Ne işe yarar |
|---|---|
| Test başlangıç tarihi | Varsayılan 2020 |
| En iyiyi seçme ölçütü | Toplam getiri / Ortalama getiri / Kazanma oranı |
| Seçilmek için en az işlem | Normal / gün içi için ayrı: 6 / 10. Az işlemle şans eseri iyi görünen sonuçları eler. |
| En fazla bekleme | SAT gelmese bile işlem bu kadar bar sonra kapanır (normal 40, gün içi 30). |
| Komisyon + kayma | Her işlemden düşülür (normal %0,2, gün içi %0,15). |
| Canlı testte zaman dilimleri | Listede olmayan hissede 3 zaman diliminden birini kapatmak için (yavaşlarsa). |
| Not kutusu | Kısa / Detaylı / Kapalı ve konumu |

### Şu an AL veren BIST 100 hisseleri (tek tek aramadan)
Borsa açıkken saatte bir GitHub'da tarama yapılır (`araclar/al_tarama.py`, `.github/workflows/al-tarama.yml`). Her hissede OTO-BIST'in seçtiği en iyi strateji, zaman dilimi ve stop/hedef ayarı kullanılır. Son mumda açık işlemi olan hisseler, karar puanına göre sıralanarak listelenir: giriş fiyatı, son fiyat, getiri, stop ve hedef. Normal mod ve gün içi mod ayrı tablodadır.
Sonuç `tarama` dalındaki `veri/AL_VERENLER.md` dosyasına yazılır.

### Alarm
**Alarm oluştur** ekranında koşul olarak bu indikatörü seç ve **"Herhangi bir alert() fonksiyon çağrısı"**nı seç. Otomatik seçilen strateji AL/SAT verdiğinde, stratejinin adı ve zaman dilimiyle birlikte bildirim gelir.

### Risk yönetimi ve seviyeler (her iki modda)
Ayarlarda **5) RİSK YÖNETİMİ VE SEVİYELER** bölümünde değiştirilebilir.
- **Stop:** Giriş fiyatından ATR(14)'ün 1,5 katı aşağısı. ATR, hissenin ortalama mum boyudur. Oynak hissede stop otomatik olarak uzaklaşır.
- **Hedef 1 / Hedef 2:** Göze alınan riskin 1,5 ve 3 katı kazanç (R:R 1:1,5 ve 1:3).
- **İz süren stop (Chandelier):** Girişten beri görülen en yüksek fiyatın 3 ATR altı. Fiyat yükseldikçe yukarı çekilir, aşağı inmez. Kazancı korumak için kullanılır.
- **Lot:** "İşlem başına göze alınan zarar (TL)" ayarına göre, stop olursa en fazla o kadar kaybedeceğin lot sayısı.
- **Açık işlem yoksa:** Çizgiler bir plandır: "OLASI GİRİŞ (AL bekleniyor)", "OLASI STOP", "OLASI HEDEF". Yani şimdi AL sinyali gelse, şu anki fiyattan girilirse stop ve hedef nerede olurdu. Soluk ve noktalı çizilir. Gerçek AL gelince "GİRİŞ / STOP / HEDEF" olarak düz çizilir.
- **Destek / direnç:** Son tepe ve diplerden, fiyata en yakın 3'er seviye.
- **Piyasa durumu:** ADX ≥ 25 ise trend vardır. Fiyat EMA200'ün üstündeyse TREND YUKARI, altındaysa TREND AŞAĞI, ADX 25'in altındaysa YATAY yazar. Trend stratejileri trendde, dip stratejileri yatay piyasada daha iyi çalışır.
- **Grafiğin üstündeki başlık:** Seçilen stratejinin geçmiş işlem sayısını, kazanma oranını ve toplam getirisini de gösterir.

> Not: Tablodaki geçmiş test sonuçları, strateji kendi SAT sinyalinde çıkılarak hesaplanır. Stop ve hedefler şu an sadece yol gösterici seviyelerdir; teste dahil değildir.

### Kendini geliştirme: eğitim / kontrol, stop-hedef iyileştirme ve canlı karne
Her iki modun GitHub'daki testleri şu şekilde çalışır:
1. **Eğitim / kontrol ayrımı:** Seçim sadece dönemin ilk %70'ine bakılarak yapılır. Son %30 **kontrol dönemidir**: seçimde hiç kullanılmaz, seçilen stratejinin gerçek sınavıdır. Not kutusunda "Kontrol" olarak görünür.
2. **Stop / hedef iyileştirme:** Eğitimde en iyi 10 aday için 11 farklı çıkış ayarı denenir: stop 1,5 veya 2,5 ATR; hedef yok, 2R veya 3R; iz süren stop açık veya kapalı. En iyisi o hissenin ayarı olur. Grafikte işlemler bu ayarla çizilir; stopla kapanan işlemde **STOP**, hedefle kapananda **HEDEF** etiketi çıkar. Not kutusunda "Çıkış (en iyi bulunan)" satırı yazar.
3. **Canlı karne:** Her çalışmada, bir önceki çalışmada seçilen stratejinin o tarihten sonra gerçekte ne yaptığı ölçülür. Sonuçlar `veri/KARNE_SWING.md` ve `veri/KARNE_SCALPER.md` dosyalarına yazılır. Geçmiş test her zaman iyi görünür; karne ise indikatörün gerçek doğruluğunu gösterir. Zamanla doldukça hangi yaklaşımın gerçekten işe yaradığı ortaya çıkar.

> Stop/hedef çıkışları grafikte birebir ancak grafik, seçilen zaman diliminde açıkken çizilir (not kutusu hangisi olduğunu söyler).

### Güncellemeler TradingView'e nasıl gelir?
TradingView kodu kendisi güncelleyemez. Yeni sürümü sen yapıştırırsın, 1 dakikalık iş:
1. Kopyalama sayfasını aç ve **Kodu kopyala**'ya bas.
2. TradingView'i bilgisayarda (ya da telefonda masaüstü görünümünde) aç, **Pine Editor**'de OTO-BIST indikatörünü aç.
3. İçindekileri tamamen sil, yapıştır ve **Save**'e bas. **Add to chart**'a basma; grafikteki indikatör kendiliğinden güncellenir.
4. Telefon uygulaması güncel sürümü kendisi alır. Almazsa grafiği kapatıp yeniden aç.

Ne zaman yapıştırmalı: sonuçlar her ayın 1'inde (normal mod) ve her cumartesi (gün içi mod) yenilenir. Yapıştırmazsan indikatör eski sonuçlarla çalışmaya devam eder, bozulmaz.

## ⚡ GÜN İÇİ MOD (scalper)

Eskiden ayrı bir indikatördü (OTO-SCALP). Artık OTO-BIST'in içindedir: grafiği 1 saat veya altına aldığında kendiliğinden açılır. Eski OTO-SCALP indikatörünü grafikten kaldırabilirsin.

**Normal moddan farkları:**
- **Gece taşıma yok:** Pozisyon her günün son mumunda kapanır, son mumda yeni işlem açılmaz.
- **Gün içine özel 7 strateji daha:** VWAP kesişimi, ilk mum kırılımı, RSI(2) dip, Stokastik RSI, EMA 9x21 + VWAP, hızlı SuperTrend (7,2), Bollinger sıkışma kırılımı. Toplam 31 strateji, 465 ikili kombin ve ortak karar.
- **Daha sıkı test (eğitim / kontrol):**
  - Her hissede seçim **sadece** dönemin ilk %70'ine (eğitim) bakılarak yapılır. Ayrıca günde en az 0,5 işlem şartı aranır, yani gerçekten gün içi işlem yapan stratejiler seçilir.
  - Kalan %30, seçimde hiç kullanılmayan **kontrol dönemidir**. Seçilen stratejinin orada ne yaptığı olduğu gibi gösterilir. Bu, "geçmişe fazla uyan" stratejileri ortaya çıkarmanın en dürüst yoludur.
  - Kâr faktörü, en büyük düşüş, günlük işlem sayısı ve ortalama bekleme süresi de ölçülür.
- **Komisyon + kayma:** Varsayılan %0,15 (al+sat toplam). Gün içinde işlem sayısı yüksek olduğu için bu değer sonucu çok etkiler. Kendi komisyonunu ayarlardan gir.
- **Karar (3 şart):**
  - ✓ Kontrol döneminde de kârda
  - ✓ Kâr faktörü 1,3 veya üstü
  - ✓ Kazanma oranı %50 veya üstü

  3/3 GÜÇLÜ, 2/3 ORTA, 0-1/3 ZAYIF.
- **Güncelleme:** Yahoo 5 ve 15 dakikalık veriyi sadece son 60 gün verdiği için sonuçlar **her cumartesi** yenilenir (`.github/workflows/scalper-test.yml`). Özet tablo `veri/SCALPER_SONUCLAR.md` dosyasındadır.

> ⚠️ Gün içi işlemde kısa geçmişle yapılan testler daha belirsizdir. Kontrol dönemi sonucuna ve "Karar" satırına mutlaka bak. Yatırım tavsiyesi değildir.

### Stratejiler ve geldikleri eski dosyalar
| # | Yeni ad | Kural | Eski dosya(lar) |
|---|---|---|---|
| 01 | RSI Karpuzlu | RSI(22) kendi EMA(66)'sını yukarı keser | 1. KARPUZLU-RSI, 1A |
| 02 | Dip Bulucu (Banker) | Fon trendi boğa/ayı çizgisini 25 altında keser (sarı mum) | 2. DIP FINDER, 2.A, 6. DIP FINDER MIX, 6A |
| 03 | Dip Bulucu-2 (VixFix) | Williams VixFix tavan yapar (kendi SAT'ı yok) | DİP BULUCU-2 |
| 04 | AlphaTrend | AlphaTrend AL/SAT | 3. ATD+ST+T3, 3A, ALPHATREND+TILSON, AT+M+T3, GERMENCIK-AT, USTA |
| 05 | SuperTrend | SuperTrend(10, 3) yön değişimi | USTA, NAZILLISUPERTREND |
| 06 | AlphaTrend + SuperTrend | İkisi birlikte yukarı dönünce | ODIE AT-DDT |
| 07 | Parabolic SAR | PSAR yön değişimi | 4. PARABOLIC SAR, 4A, NYSA TREND |
| 08 | MACD Dip Kesişimi | MACD sıfırın altında sinyali yukarı keser | 5. MACD TARAMA |
| 09 | ALMA Dönüşü | ALMA(14) yukarı döner | ALMA TARAMA, SOKEOVASI |
| 10 | T3 Tillson Dönüşü | T3(8) yukarı döner | ALPHATREND+TILSON, ARANLAR, AT+M+T3 |
| 11 | Bollinger Orta Bant | Fiyat 20'lik orta bandı yukarı keser | YORUKALIEFE |
| 12 | Bollinger20 x EMA50 | SMA20, EMA50'yi yukarı keser | BOLL ORTABAND+50EMA |
| 13 | EMA 5x13 (Umurlu) | EMA5, EMA13'ü keser | UMURLU 5-8-13 (+TARAMA), REG TREND |
| 14 | EMA 5x22 (Aydın) | EMA5, EMA22'yi keser | AYDIN-fibo v2, ATCA HO |
| 15 | WMA 9x15 (Efeler) | WMA9, WMA15'i keser | EFELER DDT, ARANLAR |
| 16 | SMMA 21x55 | SMMA21, SMMA55'i keser | EMA-SMMA 21 |
| 17 | Darvas Kutusu | Kutu tepesi kırılımı / dibi kırılımı | DARVAS AL SAT, Darvas-Bol |
| 18 | Fisher Dip | Fisher -1,5 altında yukarı döner | FISHER TARAMA |
| 19 | CCI Dip | CCI -100'ü yukarı keser | CCI TARAMA |
| 20 | TSI Dip | TSI -0,8 altına iner | TSI LINEER TARAMA |
| 21 | MACD Kesişimi | MACD kesişimi (Haftalık'ta test edilince eski "Haftalık MACD") | MUSLUCAV2, SOKEOVASI, NYSA TREND |
| 22 | Erik Kombo | 7 koşul birlikte (Ichimoku, EMA5xSMA10, MACD, RSI, MFI, HMA, kijun 26) | ERIK TARAMA |
| 23 | EMA Kombo | EMA5xEMA14 + EMA34 üstü + MACD + RSI>50 | KOMP-EMA TARAMA |
| 24 | Bollinger Kombo | Orta bant kırılımı + SMA200 üstü + MACD | BOLL-ORT TARAMA |
| 25 | ORTAK KARAR | Yukarıdakilerden en az N tanesi son birkaç barda AL verirse | — |

**Birleştirmede yapılan küçük uyarlamalar:**
- Eski tarama kodlarındaki çoklu hisse tarama tabloları, ücretsiz hesapta sınır yarattığı için çıkarıldı.
- Kombo stratejilerde (22, 23, 24) "her şey aynı mumda kesişsin" şartı neredeyse hiç sinyal üretmiyordu. Bu yüzden ana kesişim aranıyor, diğer koşulların ise o an "olumlu" olması yeterli sayılıyor.
- "Haftalık MACD" ve Erik'teki haftalık kijun için ayrı haftalık veri çekilmiyor. Strateji her zaman diliminde (Haftalık dahil) zaten ayrıca test ediliyor.
- MACD TARAMA'daki uyumsuzluk (divergence) kısmı ve sinyal üretmeyen yardımcı çizimler alınmadı: hareketli ortalama çizgileri, fibo, trend kanalları, OVAKÖY, trendstop+boll, ema14 haftalık-aylık.

> ⚠️ Sonuçlar geçmiş veriye dayanır ve geleceği garanti etmez. Yatırım tavsiyesi değildir.
