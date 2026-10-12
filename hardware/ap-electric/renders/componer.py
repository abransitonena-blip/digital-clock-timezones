"""Imagen de la familia AP Electric (Home Plug, Home Switch, 7R Tour) con su identidad. python3 componer.py RENDERS IDENTIDAD SALIDA"""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

R, ID, SAL = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 2400, 2620
FT = "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf"
def f(t, b=True): return ImageFont.truetype(FT % ("-Bold" if b else ""), t)
NAR, GRA = (255, 107, 10), (29, 31, 36)

def recorte(n, ancho=None, alto=None):
    im = Image.open(f"{R}/hq_{n}.png").convert("RGBA")
    im.putalpha(im.split()[-1].point(lambda v: 0 if v < 90 else v))
    im = im.crop(im.split()[-1].getbbox())
    if ancho: im = im.resize((ancho, int(im.height * ancho / im.width)), Image.LANCZOS)
    if alto and im.height > alto: im = im.resize((int(im.width * alto / im.height), alto), Image.LANCZOS)
    return im

def sombra(im, desp=40, rad=40, alfa=90):
    a = im.split()[-1].point(lambda v: alfa if v > 10 else 0)
    s = Image.new("RGBA", im.size, (0, 0, 0, 0)); s.putalpha(a); s = s.filter(ImageFilter.GaussianBlur(rad))
    b = Image.new("RGBA", (im.width + 2 * rad, im.height + 2 * rad + desp), (0, 0, 0, 0))
    b.alpha_composite(s, (rad, rad + desp)); b.alpha_composite(im, (rad, rad)); return b

c = Image.new("RGBA", (W, H), (244, 244, 246, 255))
d = ImageDraw.Draw(c)
logo = Image.open(f"{ID}/logo_ap_electric_industrial_color.png").convert("RGBA")
logo = logo.resize((900, int(logo.height * 900 / logo.width)), Image.LANCZOS)
c.alpha_composite(logo, (110, 80))
d.text((W - 110, 110), "Dos placas · cuatro productos · un programa", font=f(44), fill=GRA, anchor="ra")
d.text((W - 110, 175), "Funciona sin internet · Modbus · lógica tipo PLC", font=f(34, False), fill=(90, 94, 104), anchor="ra")
d.text((W - 110, 225), "Prototipo de diseño: sin certificar, límites por determinar", font=f(28, False), fill=(192, 40, 31), anchor="ra")
r7 = sombra(recorte("7r", 1900), alfa=55)
c.alpha_composite(r7, ((W - r7.width) // 2, 300))
y = 300 + r7.height - 60
d.text((W // 2, y), "AP Electric Industrial 7R Tour", font=f(52), fill=GRA, anchor="mm")
d.text((W // 2, y + 60), "7 salidas por relé · 8 entradas de 24 V · RS-485 Modbus RTU aislado · mando manual por hardware", font=f(30, False), fill=(70, 74, 84), anchor="mm")
y += 120
for i, (n, t, s) in enumerate((("plug", "Home Plug", "enchufar y usar · lámparas de 127 V"), ("switch", "Home Switch", "instalación fija · conserva el apagador"))):
    im = sombra(recorte(n, alto=640), alfa=55)
    x = 300 + i * 1000
    c.alpha_composite(im, (x + (800 - im.width) // 2, y))
    d.text((x + 400, y + im.height + 10), t, font=f(46), fill=GRA, anchor="mm")
    d.text((x + 400, y + im.height + 62), s, font=f(28, False), fill=(70, 74, 84), anchor="mm")
c.convert("RGB").save(SAL, quality=92)
print("listo", c.size)
