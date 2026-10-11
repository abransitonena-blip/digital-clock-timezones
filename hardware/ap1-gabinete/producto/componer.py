"""Imagen del producto terminado: familia en el riel DIN, cada equipo con sus datos y AP Studio programando.
    python3 componer.py RENDERS_DIR CAPTURA_APP SALIDA.png"""
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

R, APP, SAL = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 2400, 3560
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf"
def f(t, b=True): return ImageFont.truetype(F % ("-Bold" if b else ""), t)
NAR = (255, 107, 10)

def fondo():
    g = Image.new("RGB", (1, H))
    for y in range(H):
        t = y / H
        g.putpixel((0, y), (int(14 + 18 * t), int(16 + 18 * t), int(22 + 22 * t)))
    return g.resize((W, H))

def sombra(im, desp=(0, 40), rad=40, alfa=150):
    a = im.split()[-1].point(lambda v: alfa if v > 10 else 0)
    s = Image.new("RGBA", im.size, (0, 0, 0, 0)); s.putalpha(a)
    s = s.filter(ImageFilter.GaussianBlur(rad))
    base = Image.new("RGBA", (im.width + 2 * rad, im.height + 2 * rad + desp[1]), (0, 0, 0, 0))
    base.alpha_composite(s, (rad + desp[0], rad + desp[1])); base.alpha_composite(im, (rad, rad))
    return base

def recorte(n, ancho):
    im = Image.open(f"{R}/hq_{n}.png").convert("RGBA")
    im.putalpha(im.split()[-1].point(lambda v: 0 if v < 24 else v))     # sin el velo casi transparente del render
    im = im.crop(im.split()[-1].getbbox())
    return im.resize((ancho, int(im.height * ancho / im.width)), Image.LANCZOS)

def logo(d, x, y, s):
    d.rounded_rectangle((x, y, x + s, y + s), radius=s * 0.22, fill=NAR)
    ft = f(int(s * 0.5)); w = d.textlength("AP", font=ft)
    d.text((x + (s - w) / 2, y + s * 0.2), "AP", font=ft, fill="white")

c = fondo().convert("RGBA")
d = ImageDraw.Draw(c)
# encabezado
logo(d, 120, 110, 120)
d.text((270, 112), "AP ELECTRIC", font=f(76), fill="white")
d.text((272, 200), "Serie DIN · automatización, alumbrado y potencia", font=f(36, False), fill=(170, 176, 190))
d.text((W - 120, 130), "Programable como un PLC", font=f(40), fill=NAR, anchor="ra")
d.text((W - 120, 190), "Escalera · lista de instrucciones · en línea", font=f(30, False), fill=(170, 176, 190), anchor="ra")
# familia en el riel
fam = sombra(recorte("familia", 2160), (0, 60), 60, 110)
c.alpha_composite(fam, ((W - fam.width) // 2, 250))
y0 = 250 + fam.height - 40
# tarjetas
P = [("uno", "AP UNO", "El cerebro todo en uno", ["PLC de 10 ms con escalera e IL", "4 canales 8 A · 2 focos 1 A", "4 salidas · 4 entradas", "RS-485: DMX512 o Modbus RTU", "Wi-Fi · Home Assistant · OTA"]),
     ("red4", "AP RED 4", "Salidas de potencia de red", ["4 relevadores de 10 A · 250 V~", "Bornes de tornillo 5.08 mm", "Ranuras de aislamiento 5 mm", "Q9-Q12 en el programa", "Se conecta por AP LINK"]),
     ("foco127", "AP FOCO 127", "Focos LED directo a la red", ["Fuente Mean Well certificada", "2 × 500 mA, corriente medida", "Se adapta a cada foco (ID)", "127 / 220 V~ con fusible y varistor", "L33-L36 en el programa"])]
cw, gap = 700, 50
x = (W - 3 * cw - 2 * gap) // 2
for n, nom, sub, items in P:
    d.rounded_rectangle((x, y0, x + cw, y0 + 1060), radius=36, fill=(30, 33, 42), outline=(52, 56, 68), width=2)
    im = recorte(n, cw - 60)
    if im.height > 520:
        im = im.resize((int(im.width * 520 / im.height), 520), Image.LANCZOS)
    c.alpha_composite(im, (x + (cw - im.width) // 2, y0 + 30 + (520 - im.height) // 2))
    d.text((x + 50, y0 + 590), nom, font=f(54), fill="white")
    d.text((x + 50, y0 + 665), sub, font=f(30, False), fill=NAR)
    for k, t in enumerate(items):
        yy = y0 + 740 + k * 58
        d.ellipse((x + 52, yy + 12, x + 66, yy + 26), fill=NAR)
        d.text((x + 86, yy), t, font=f(29, False), fill=(214, 218, 228))
    x += cw + gap
# AP Studio
y1 = y0 + 1120
app = Image.open(APP).convert("RGBA")
app = app.crop((0, 0, app.width, int(app.width * 1.25)))
app = app.resize((560, int(app.height * 560 / app.width)), Image.LANCZOS)
m = Image.new("L", app.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, app.width - 1, app.height - 1), radius=44, fill=255)
app.putalpha(m)
marco = Image.new("RGBA", (app.width + 28, app.height + 28), (0, 0, 0, 0))
ImageDraw.Draw(marco).rounded_rectangle((0, 0, marco.width - 1, marco.height - 1), radius=56, fill=(8, 8, 10))
marco.alpha_composite(app, (14, 14))
marco = sombra(marco, (0, 30), 40, 160)
c.alpha_composite(marco, (W - marco.width - 90, y1 - 40))
d.text((140, y1 + 40), "AP Studio", font=f(64), fill="white")
d.text((140, y1 + 125), "La app del equipo, en el celular o la PC", font=f(34, False), fill=NAR)
lineas = ["Programa en escalera (Ladder) o lista de instrucciones,", "como en un PLC industrial (IEC 61131-3):",
          "contactos, flancos, comparaciones analógicas,", "SET / RST, TON / TOF / TP, CTU / CTD.", "",
          "Ve el programa en línea: lo que conduce, en verde.", "RUN / STOP, plantillas listas, marcas y contadores",
          "que se recuerdan, bitácora de eventos y vigilante.", "", "Funciona sin internet: el equipo la sirve en Wi-Fi."]
for k, t in enumerate(lineas):
    d.text((140, y1 + 220 + k * 52), t, font=f(33, False), fill=(214, 218, 228))
d.text((W // 2, H - 70), "AP ELECTRIC · diseño propio · placas, programa y carcasa", font=f(28, False), fill=(120, 126, 140), anchor="mm")
c.convert("RGB").save(SAL, quality=92)
print("listo", SAL)
