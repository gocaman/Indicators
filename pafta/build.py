#!/usr/bin/env python3
"""pafta.svg üretir. Kullanım: python3 build.py  (metin/yerleşim değişikliklerini bu dosyada yap)."""
from PIL import ImageFont
from xml.sax.saxutils import escape
import math

W, H = 1200, 1697
BORDO, MAVI, GRI, KOYU = "#7a0c1c", "#5b7fa6", "#555555", "#1d1d1d"
FR = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FB = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT = "Liberation Sans, Helvetica, Arial, sans-serif"
out = []

def wrap(text, size, maxw, bold=False):
    f = ImageFont.truetype(FB if bold else FR, size)
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if f.getlength(t) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def text(x, y, s, size=13, fill=KOYU, bold=False, anchor="start", maxw=None, lh=None, ident=None, extra=""):
    lines = wrap(s, size, maxw, bold) if maxw else [s]
    lh = lh or round(size * 1.38)
    sp = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else lh}">{escape(l)}</tspan>' for i, l in enumerate(lines))
    idn = f' id="{ident}"' if ident else ""
    out.append(f'<text{idn} x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{"700" if bold else "400"}" {extra}>{sp}</text>')
    return y + lh * (len(lines) - 1)

def pill(x, y, label, w=None, h=26):
    f = ImageFont.truetype(FB, 14)
    w = w or int(f.getlength(label)) + 34
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h//2}" fill="{BORDO}"/>')
    out.append(f'<text x="{x+17}" y="{y+h-8}" font-size="14" font-weight="700" fill="#fff" letter-spacing="0.6">{escape(label)}</text>')

def img(href, x, y, w, h, extra=""):
    out.append(f'<image href="assets/{href}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet" {extra}/>')

def arrow(x1, y1, x2, y2, width, color, head=None):
    head = head or width * 2.6
    a = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * 0.8 * math.cos(a), y2 - head * 0.8 * math.sin(a)
    px, py = -math.sin(a), math.cos(a)
    out.append(f'<line x1="{x1}" y1="{y1}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{color}" stroke-width="{width}"/>')
    pts = f"{x2},{y2} {bx+px*head/2:.1f},{by+py*head/2:.1f} {bx-px*head/2:.1f},{by-py*head/2:.1f}"
    out.append(f'<polygon points="{pts}" fill="{color}"/>')

def layer(name, open_=True):
    out.append(f'<g id="{name}" inkscape:groupmode="layer" inkscape:label="{name}">' if open_ else '</g>')

# ------------------------------------------------------------------ başlangıç
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">')
out.append('<title>Kentsel Bağlantılar Paftası</title>')
out.append('<defs><clipPath id="harita-kes"><polygon points="350,0 1374,0 1374,2610 750,2610 750,1190 0,1190 0,270 350,270"/></clipPath></defs>')
layer("zemin"); out.append(f'<rect width="{W}" height="{H}" fill="#fff"/>'); layer("zemin", False)

# ------------------------------------------------------------------ başlık
layer("baslik")
out.append(f'<rect x="0" y="34" width="22" height="76" fill="{BORDO}"/>')
text(40, 92, "KENTSEL BAĞLANTILAR PAFTASI", 44, KOYU, True, ident="baslik-metni", extra='letter-spacing="0.5"')
text(40, 128, "Konyaaltı / Gürsu Mahallesi – Antalya", 21, BORDO)
text(1160, 66, "AKDENİZ ÜNİVERSİTESİ · MİMARLIK FAKÜLTESİ", 13, GRI, True, "end")
text(1160, 85, "Peyzaj Mimarlığı Bölümü – Proje V Dersi", 13, GRI, False, "end")
out.append(f'<line x1="40" y1="150" x2="1160" y2="150" stroke="{BORDO}" stroke-width="2"/>')
layer("baslik", False)

# ------------------------------------------------------------------ sol sütun
LX, LW = 40, 520
layer("sol-bilgi")
pill(LX, 172, "KONUM")
text(LX, 224, "Proje alanı Antalya ili Konyaaltı ilçesi Gürsu Mahallesi'nde yer almaktadır. Alan, Konyaaltı sahil bandına ve kent merkezine yakın konumuyla önemli rekreasyon, turizm ve konut alanlarıyla ilişkili bir bölgede bulunmaktadır. Ana ulaşım akslarına ve toplu taşıma güzergâhlarına yakınlığı sayesinde kentsel erişilebilirliği yüksek bir konumdadır.", 13.5, KOYU, maxw=LW, lh=19)
pill(LX, 352, "NÜFUS")
img("nufus.png", LX, 390, 420, 140)
pill(LX, 552, "SOSYO-EKONOMİK DURUM")
img("sosyo.png", LX, 592, 200, 148)
text(LX + 225, 614, "Gürsu Mahallesi, turizm ve hizmet sektörüne yakınlığı sayesinde orta ve üst gelir grubunun yoğun olduğu, yaşam kalitesi yüksek bir yerleşim alanıdır.", 13.5, KOYU, maxw=LW - 225, lh=19)
layer("sol-bilgi", False)

layer("analiz-diskleri")
pill(LX, 762, "ALAN ANALİZ ŞEMALARI")
cells = [
 ("Ulaşım Analizi", "disk-ulasim.png", "Alan, çevresindeki ana ve tali ulaşım akslarıyla yaya bağlantıları açısından değerlendirilmiş, erişilebilirlik düzeyi incelenmiştir. Mevcut ulaşım ağının alan kullanımına etkisi ve bağlantı sürekliliği analiz edilmiştir."),
 ("Yeşil Alan Analizi", "disk-yesil.png", "Alan ve yakın çevresindeki aktif ve pasif yeşil alanların dağılımı değerlendirilmiştir. Yeşil alan sürekliliği ve kullanıcı erişimi incelenerek ekolojik ve rekreatif potansiyel belirlenmiştir."),
 ("Dolu-Boş Analizi", "disk-dolubos.png", "Yapılaşmış alanlar ile açık ve boş alanların mekânsal dağılımı incelenmiştir. Alanın yoğunluk dengesi ve açık alan kullanım potansiyeli değerlendirilmiştir."),
 ("Gürültü Analizi", "disk-gurultu.png", "Alan çevresindeki ulaşım akslarından ve yoğun alanlardan kaynaklanan gürültü etkileri analiz edilmiştir. Gürültü seviyesinin kullanıcı konforu ve mekânsal kullanım üzerindeki etkileri değerlendirilmiştir."),
]
for i, (t, f, c) in enumerate(cells):
    cx, cy = LX + (i % 2) * 270, 812 + (i // 2) * 263
    text(cx, cy, t, 15, BORDO, True)
    img(f, cx, cy + 8, 250, 150)
    text(cx, cy + 176, c, 12, KOYU, maxw=250, lh=16)
layer("analiz-diskleri", False)

layer("pozitif-negatif")
py = 1352
pill(LX, py, "POZİTİF YÖNLER", 190)
pill(LX + 270, py, "NEGATİF YÖNLER", 190)
poz = ["Konyaaltı sahiline ve kıyı rekreasyon alanlarına yakın konumu sayesinde yüksek yaşam kalitesi ve sosyal kullanım potansiyeli sunması",
       "Turizm, konut ve ticaret fonksiyonlarının bir arada bulunmasıyla canlı ve çok işlevli bir kentsel yapı oluşturması",
       "Ana ulaşım akslarına ve toplu taşıma olanaklarına yakınlığı sayesinde erişilebilirliğinin güçlü olması",
       "Gelişmekte olan konut alanları ve sosyal donatıların artışıyla yaşam standartlarının yükselmesi",
       "İklim, doğal çevre ve peyzaj potansiyeli açısından açık alan ve rekreasyon kullanımlarına elverişli olması"]
neg = ["Turizm ve ikinci konut kullanımı nedeniyle yaz aylarında nüfus yoğunluğunun artması ve kullanım baskısı oluşması",
       "Artan yapılaşma ve nüfus yoğunluğu nedeniyle mevcut açık ve yeşil alanlar üzerinde baskı oluşması",
       "Mevsimsel nüfus artışına bağlı olarak trafik yoğunluğunun ve otopark sorunlarının yaşanması",
       "Hızlı kentleşme sürecinin bazı bölgelerde mekânsal gelişimde düzensizliğe yol açabilmesi",
       "Kıyı kullanımının yoğunluğu nedeniyle çevresel sürdürülebilirlik ve kıyı ekosistemi üzerinde baskı oluşma riski"]
for col, items, mark, color in ((LX, poz, "+", "#2f6b3a"), (LX + 270, neg, "–", BORDO)):
    y = py + 52
    for it in items:
        out.append(f'<text x="{col}" y="{y}" font-size="14" font-weight="700" fill="{color}">{mark}</text>')
        y = text(col + 16, y, it, 11.5, KOYU, maxw=234, lh=14.5) + 21
layer("pozitif-negatif", False)

# ------------------------------------------------------------------ harita
RX, RY, S = 600, 172, 560 / 1374
layer("arka-plan-cad")
out.append(f'<g transform="translate({RX},{RY}) scale({S:.5f})"><image href="assets/harita-cad.png" x="0" y="0" width="1374" height="2610" clip-path="url(#harita-kes)"/></g>')
out.append(f'<rect x="{RX+1220*S:.1f}" y="{RY}" width="{154*S:.1f}" height="{46*S:.1f}" fill="#fff"/>')
layer("arka-plan-cad", False)

layer("harita-oklar-yazilar")
out.append(f'<g transform="translate({RX},{RY}) scale({S:.5f})" font-weight="700">')
arrow(930, 1325, 1235, 1075, 7, "#b8892a", 34)
for lbl, ty in (("KAZANCI BEDİH", 1030), ("GÜZEL SANATLAR L.", 1074)):
    out.append(f'<text x="1355" y="{ty}" font-size="36" fill="#b8892a" text-anchor="end" stroke="#fff" stroke-width="9" paint-order="stroke">{lbl}</text>')
arrow(1085, 1470, 1290, 1470, 22, MAVI, 60)
out.append(f'<text x="1355" y="1545" text-anchor="end" font-size="36" fill="#b8892a" stroke="#fff" stroke-width="9" paint-order="stroke">MİMAR SİNAN BULVARI</text>')
arrow(850, 2020, 1260, 1850, 16, MAVI, 50)
out.append(f'<text x="880" y="2085" font-size="36" fill="#b8892a" stroke="#fff" stroke-width="9" paint-order="stroke">MEVLANA BULVARI</text>')
out.append(f'<text x="930" y="1245" font-size="34" fill="{BORDO}" text-anchor="middle" stroke="#fff" stroke-width="9" paint-order="stroke">PROJE ALANI</text>')
out.append('</g>')
# kuzey oku
out.append(f'<g id="kuzey-oku" transform="translate(1128,215)"><circle r="22" fill="#fff" stroke="{KOYU}" stroke-width="1.2"/><polygon points="0,-17 7,10 0,5 -7,10" fill="{KOYU}"/><text y="-27" font-size="13" font-weight="700" text-anchor="middle">K</text></g>')
layer("harita-oklar-yazilar", False)

# ------------------------------------------------------------------ boşluktaki bölge (harita çentiği)
layer("gunes-ve-rota")
img("gunes.png", 610, 664, 285, 215)
pill(610, 905, "GEZİ ROTASI")
img("foto.png", 610, 945, 285, 180)
layer("gunes-ve-rota", False)

# ------------------------------------------------------------------ alt sağ
layer("lejant-uzaklik")
img("lejant.png", 600, 1280, 270, 233)
pill(880, 1272, "ULAŞIM UZAKLIKLARI")
rows = [("Şehirlerarası Otobüs Terminali", "11,7 km"), ("Havalimanı", "29,3 km"), ("Alışveriş Merkezi", "4,8 km"), ("Hastane", "1,6 km")]
for i, (a, b) in enumerate(rows):
    y = 1330 + i * 46
    text(880, y, a, 12.5, KOYU)
    text(880, y + 24, b, 22, BORDO, True)
    out.append(f'<line x1="880" y1="{y+33}" x2="1160" y2="{y+33}" stroke="#ddd"/>')
layer("lejant-uzaklik", False)

# ------------------------------------------------------------------ alt bant
text(40, 1665, "Prof. Dr. Tahsin YILMAZ", 11, GRI)
text(1160, 1665, "Konyaaltı / Gürsu · Antalya", 11, GRI, False, "end")
out.append('</svg>')
open("pafta.svg", "w", encoding="utf-8").write("\n".join(out))
print("pafta.svg yazıldı")
