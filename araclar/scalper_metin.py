"""pine_uret.py --scalper için swing metnini gün içi (scalper) metnine çevirir."""


def _degistir(metin, eski, yeni):
    assert eski in metin, f"scalper_metin: bulunamadı: {eski[:70]}"
    return metin.replace(eski, yeni)


def uyarla(m):
    m = _degistir(m, '''//  OTOMATİK EN İYİ STRATEJİ - BIST
//  Hangi hisseyi açarsan aç, bu repodaki 24 strateji + aralarındaki 276 ikili kombin,
//  4 zaman diliminde (1S / 4S / Günlük / Haftalık) o hissenin geçmişinde test edilir.''', '''//  OTOMATİK SCALPER - BIST  (gün içi işlem)
//  24 strateji + gün içine özel 7 strateji (VWAP, ilk mum kırılımı, RSI(2), Stokastik RSI,
//  EMA 9x21+VWAP, hızlı SuperTrend, Bollinger sıkışma) ve aralarındaki 465 ikili kombin,
//  5 dakika / 15 dakika / 1 saat grafikte test edilir. Gece taşıma yok: pozisyon gün sonunda kapanır.''')
    m = _degistir(m, 'indicator("OTOMATİK EN İYİ STRATEJİ - BIST", shorttitle = "OTO-BIST"',
                  'indicator("OTOMATİK SCALPER - BIST", shorttitle = "OTO-SCALP"')
    m = _degistir(m, '"BIST 100 için hazır test sonuçlarını kullan (hızlı)", group = G1, tooltip = "Açıkken listedeki hisselerde test yapılmaz, GitHub\'da her ay hesaplanan',
                  '"BIST 100 için hazır test sonuçlarını kullan (hızlı)", group = G1, tooltip = "Açıkken listedeki hisselerde test yapılmaz, GitHub\'da her hafta hesaplanan')
    m = _degistir(m, 'testBas = input.time(timestamp("01 Jan 2020 00:00 +0300")', 'testBas = input.time(timestamp("01 Jan 2024 00:00 +0300")')
    m = _degistir(m, 'minIslem = input.int(6, ', 'minIslem = input.int(10, ')
    m = _degistir(m, 'maxBar = input.int(40, "Bir işlemde en fazla bekleme (bar)", minval = 1, maxval = 500, group = G1, tooltip = "Strateji SAT vermese bile bu kadar bar sonra işlem kapatılır.")',
                  'maxBar = input.int(30, "Bir işlemde en fazla bekleme (bar)", minval = 1, maxval = 500, group = G1, tooltip = "Strateji SAT vermese bile bu kadar bar sonra işlem kapatılır. Gün sonunda her durumda kapanır.")')
    m = _degistir(m, 'komisyon = input.float(0.2, ', 'komisyon = input.float(0.15, ')
    m = _degistir(m, 'sadece 25 tek strateji test edilir', 'sadece 32 tek strateji test edilir')
    m = _degistir(m, '''tf60 = input.bool(false, "1 Saat", group = G2, inline = "tf", tooltip = "1 saatlik test işlemciyi en çok yoran testtir. İndikatör yavaşlarsa kapalı tut.")
tf240 = input.bool(true, "4 Saat", group = G2, inline = "tf")
tfD = input.bool(true, "Günlük", group = G2, inline = "tf")
tfW = input.bool(true, "Haftalık", group = G2, inline = "tf")''', '''tf5 = input.bool(true, "5 Dakika", group = G2, inline = "tf", tooltip = "Listede olmayan hissede canlı test bu zaman dilimlerinde yapılır. Yavaşlarsa 5 Dakika'yı kapat.")
tf15 = input.bool(true, "15 Dakika", group = G2, inline = "tf")
tf60 = input.bool(true, "1 Saat", group = G2, inline = "tf")''')
    # gece taşıma yok
    m = _degistir(m, '''    cik = poz and (sat or bar_index - girisBar >= maxBar)
    gir = al and not poz''', '''    cik = poz and (sat or bar_index - girisBar >= maxBar or session.islastbar)
    gir = al and not poz and not session.islastbar''')
    # not kutusu ve karar
    m = _degistir(m, "            k1 = topG > alTut\n", "            k1 = hazir ? yil > 0 : topG > 0\n")
    m = _degistir(m, "            k3 = yil > 0\n", "            k3 = hazir ? alTut >= 1.3 : yil > 0\n")
    m = _degistir(m, '''str.tostring(n) + " işlem • %" + str.tostring(kazOran, "0") + " kazanç • Toplam " + f_yuzde(topG) + " (Al-Tut " + f_yuzde(alTut) + ")"''',
                  '''str.tostring(n) + " işlem • %" + str.tostring(kazOran, "0") + " kazanç • Toplam " + f_yuzde(topG) + (hazir ? " • KF " + str.tostring(alTut, "0.00") + " • günde " + str.tostring(array.get(hYillik, hI), "0.0") + " işlem" : "")''')
    m = _degistir(m, '''"/3) • Son 1 yıl " + f_yuzde(yil)''', '''"/3)" + (hazir ? " • Kontrol " : " • Son 30 gün ") + f_yuzde(yil)''')
    # swing'deki "nasıl seçildi" metni (hazır sonuç) baştan sona scalper metniyle değiştirilir
    bas = m.index('"NASIL SEÇİLDİ: BIST 100 hisseleri her ay')
    son = m.index("f_yuzde(array.get(hYillik, hI))", bas) + len("f_yuzde(array.get(hYillik, hI))")
    m = m[:bas] + '''"NASIL SEÇİLDİ: BIST 100 hisseleri her hafta GitHub'da test edilir\\n(son: " + HAZIR_TARIH + "). 31 strateji + 465 kombin 5dk/15dk/1S'te\\n" + array.get(hBas, hI) + "'den beri denendi. Sadece dönemin ilk %70'ine bakılarak\\nseçildi (günde en az 0,5 işlem); en iyi 10 aday için 11 stop/hedef ayarı\\ndenendi. Son %30 KONTROL dönemi: seçimde hiç kullanılmadı."''' + m[son:]
    m = _degistir(m, '''"NASIL SEÇİLDİ: 24 strateji + 276 ikili kombin, seçili zaman\\ndilimlerinde "''', '''"NASIL SEÇİLDİ: 31 strateji + 465 ikili kombin, seçili zaman\\ndilimlerinde "''')
    m = _degistir(m, '''" bar sonra) çıkılır. Her işlemden %" + str.tostring(komisyon) + " komisyon düşülür."''',
                  '''" bar sonra) çıkılır. Gün sonunda pozisyon kapatılır,\\ngece taşınmaz. Her işlemden %" + str.tostring(komisyon) + " komisyon+kayma düşülür."''')
    m = _degistir(m, '''"NASIL KARAR VERİLİR (3 şart):\\n" + (k1 ? "✓" : "✗") + " Toplam getiri Al-Tut'tan yüksek\\n" + (k2 ? "✓" : "✗") + " Kazanma oranı %50 veya üstü\\n" + (k3 ? "✓" : "✗") + " Son 1 yılda da kârda\\n''',
                  '''"NASIL KARAR VERİLİR (3 şart):\\n" + (k1 ? "✓" : "✗") + (hazir ? " Kontrol döneminde de kârda" : " Toplam kârda") + "\\n" + (k2 ? "✓" : "✗") + " Kazanma oranı %50 veya üstü\\n" + (k3 ? "✓" : "✗") + (hazir ? " Kâr faktörü 1,3 veya üstü" : " Son 30 günde de kârda") + "\\n''')
    m = _degistir(m, 'plot(na, "OTO-BIST", display = display.none)', 'plot(na, "OTO-SCALP", display = display.none)')
    return m
