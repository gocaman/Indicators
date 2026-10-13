# İndikatörler

## ⭐ HEPSİ BİR ARADA - BIST (tek indikatör)

Dosya: **`0. HEPSİ BİR ARADA - BIST.txt`**

Bu repodaki indikatörlerin AL/SAT kuralları tek bir indikatörde toplandı (24 strateji ve bunların ortak kararı).
Ücretsiz TradingView hesabında bile tek indikatör hakkıyla hepsini kullanabilirsin.

### Kurulum (telefon veya bilgisayar)
1. Dosyayı aç ve içeriğin tamamını kopyala.
2. TradingView'de **Pine Editor**'ü aç, yeni bir indikatör oluştur ve içindekileri silip kodu yapıştır.
3. **Kaydet** ve ardından **Grafiğe ekle**'ye bas.
   (Pine Editor telefon uygulamasında yoksa bu adımı bir kez bilgisayardan ya da telefon tarayıcısının masaüstü modundan yap. İndikatör hesabına kaydolur ve sonra telefon uygulamasında "Göstergeler → Benim komut dosyalarım" altında görünür.)

### Ne görürsün?
- **Sağ üstte performans tablosu:** 24 strateji açık olan grafikte geriye dönük test edilir ve en iyiden en kötüye sıralanır.
  | Sütun | Anlamı |
  |---|---|
  | Şimdi | Strateji şu an AL konumunda mı? |
  | İşlem | Test süresince yapılan işlem sayısı |
  | Kazanma | Kârla kapanan işlemlerin oranı |
  | Ort. | İşlem başına ortalama net getiri |
  | Toplam | Tüm işlemlerin birleşik getirisi |
  | Al-Tut | Hiç işlem yapmadan elde tutsaydın elde edeceğin getiri (karşılaştırma için) |
- **Grafikte AL / SAT etiketleri:** Varsayılan olarak tablodaki 1. stratejinin işlemleri gösterilir. SAT etiketinde o işlemin net getirisi yazar.

### BIST 100 için sıralamayı görmek
- **Genel endeks sıralaması:** Grafiği **XU100** yap ve tablo endeks üzerindeki sıralamayı gösterir.
- **Tek tek hisseler:** BIST 100 hisseleri arasında gezin (THYAO, ASELS, KCHOL…). Tablo her hissede o hisse için yeniden hesaplanır, çünkü bir hissede en iyi çalışan strateji başka bir hissede en iyisi olmayabilir.
- **Zaman dilimi:** Günlük, 4 saatlik veya haftalık grafikte sonuçlar farklıdır. Hangi zaman diliminde işlem yapıyorsan onu seç.

### Ayarlar (dişli simgesi)
| Ayar | Ne işe yarar |
|---|---|
| Gösterim | **En iyi strateji (otomatik)** / **Ortak karar** (birçok strateji aynı anda AL verince) / **Tek strateji seç** |
| Test başlangıç tarihi | Varsayılan 2020. Daha yakın bir tarih seçersen güncel piyasaya göre sıralar. |
| En fazla bekleme | SAT gelmese bile işlem bu kadar bar sonra kapatılır (varsayılan 40). |
| Komisyon + kayma | Her işlemden düşülür (varsayılan %0,2). |
| Sıralama ölçütü | Toplam getiri / Ortalama getiri / Kazanma oranı |
| Ortak karar | Son kaç barda, en az kaç stratejinin aynı yönde sinyal vermesi gerektiği |

### Alarm kurmak
TradingView'de **Alarm oluştur** ekranında koşul olarak bu indikatörü seç. Seçenekler:
- **ORTAK KARAR - AL / SAT**
- **Grafikteki strateji - AL / SAT**
- **Herhangi bir alert() fonksiyon çağrısı:** O an en iyi olan stratejinin AL/SAT'ını, stratejinin adıyla birlikte bildirir.

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
| 21 | Haftalık MACD | Haftalık MACD kesişimi (tamamlanmış mumla) | MUSLUCAV2, SOKEOVASI, NYSA TREND |
| 22 | Erik Kombo | 7 koşul birlikte (Ichimoku, EMA5xSMA10, MACD, RSI, MFI, HMA, haftalık kijun) | ERIK TARAMA |
| 23 | EMA Kombo | EMA5xEMA14 + EMA34 üstü + MACD + RSI>50 | KOMP-EMA TARAMA |
| 24 | Bollinger Kombo | Orta bant kırılımı + SMA200 üstü + MACD | BOLL-ORT TARAMA |
| 25 | ORTAK KARAR | Yukarıdakilerden en az N tanesi son birkaç barda AL verirse | — |

**Birleştirmede yapılan küçük uyarlamalar:**
- Eski tarama kodlarındaki çoklu hisse tarama tabloları, ücretsiz hesapta sınır yarattığı için çıkarıldı.
- Kombo stratejilerde (22, 23, 24) "her şey aynı mumda kesişsin" şartı neredeyse hiç sinyal üretmiyordu. Bu yüzden ana kesişim aranıyor, diğer koşulların ise o an "olumlu" olması yeterli sayılıyor.
- MACD TARAMA'daki uyumsuzluk (divergence) kısmı ve sinyal üretmeyen yardımcı çizimler alınmadı: hareketli ortalama çizgileri, fibo, trend kanalları, OVAKÖY, trendstop+boll, ema14 haftalık-aylık.

> ⚠️ Tablodaki sonuçlar geçmiş veriye dayanır ve geleceği garanti etmez. Yatırım tavsiyesi değildir.
