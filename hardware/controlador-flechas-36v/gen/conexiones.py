"""Dibuja la imagen de conexiones externas sobre el render 3D superior (PIL en el anfitrión).

    python3 gen/conexiones.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FAB = os.path.join(HERE, "..", "fabricacion")
REN = os.path.join(FAB, "3d", "render_superior.png")
OUT = os.path.join(FAB, "conexiones_externas.png")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# calibración del render (px por mm y origen del borde de la placa)
BX0, BY0, SX, SY = 209, 174, 12.847, 12.84
OFFX, OFFY = 700, 330
W, H = 3200, 2150

RED, BLK, GRN, GRY, BLU, ORG = (200, 0, 0), (20, 20, 20), (0, 130, 40), (120, 120, 120), (0, 70, 170), (210, 110, 0)


def P(x, y):
    return (OFFX + BX0 + x * SX, OFFY + BY0 + y * SY)


def white_bg():
    """Pasa los renders (fondo transparente) a fondo blanco."""
    for n in ("render_superior.png", "render_inferior.png", "render_perspectiva.png"):
        p = os.path.join(FAB, "3d", n)
        im = Image.open(p)
        if im.mode == "RGBA":
            bg = Image.new("RGB", im.size, "white")
            bg.paste(im, mask=im.split()[3])
            bg.save(p, optimize=True)


def main():
    white_bg()
    im = Image.new("RGB", (W, H), "white")
    ren = Image.open(REN).convert("RGB")
    im.paste(ren, (OFFX, OFFY))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 30)
    fs = ImageFont.truetype(FONT, 25)
    fb = ImageFont.truetype(FONTB, 38)
    fbs = ImageFont.truetype(FONTB, 30)

    def wire(pts, color, width=7, dash=False):
        if dash:
            for a, b in zip(pts[:-1], pts[1:]):
                n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) / 22) + 1
                for k in range(0, n, 2):
                    t0, t1 = k / n, min(1, (k + 1) / n)
                    d.line([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0),
                            (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)], fill=color, width=width)
        else:
            d.line(pts, fill=color, width=width, joint="curve")
        x, y = pts[0]
        d.ellipse([x - 11, y - 11, x + 11, y + 11], outline=color, width=5)

    def box(x, y, lines, color, font=f, pad=14, fill=(255, 255, 255)):
        tw = max(d.textlength(t, font=font) for t in lines)
        th = len(lines) * (font.size + 8)
        d.rectangle([x, y, x + tw + 2 * pad, y + th + 2 * pad], outline=color, width=4, fill=fill)
        for i, t in enumerate(lines):
            d.text((x + pad, y + pad + i * (font.size + 8)), t, fill=color, font=font)
        return (x, y, x + tw + 2 * pad, y + th + 2 * pad)

    d.text((60, 40), "CONEXIONES EXTERNAS - Controlador de flechas 36 V (vista del lado de componentes)", fill=BLK, font=fb)
    box(60, 110, ["ADVERTENCIA: esta placa es de MUY BAJA TENSION (36 VCC). No conectar a 127 VCA ni a la",
                  "placa Radox original mientras esta siga conectada a la red. Si se requiere compartir una señal,",
                  "usar un optoacoplador y mantener aislamiento galvánico."], RED, font=fs, fill=(255, 240, 240))

    # ---- J3 FLECHAS (borde izquierdo) ----
    pins = [("+36V", 12.7, RED), ("F1-", 17.78, GRN), ("F2-", 22.86, GRN), ("F3-", 27.94, GRN)]
    ybase = 640
    for i, (nm, y, col) in enumerate(pins):
        x0, y0 = P(6.35, y)
        yy = ybase + i * 150
        wire([(x0, y0), (x0 - 170, y0), (560, yy)], col)
    box(40, 555, ["J3  FLECHAS (ánodo común)"], BLK, font=fbs)
    box(40, 610, ["+36V  ->  ÁNODOS de las 3 flechas", "(el + de las tres cadenas va unido aquí)"], RED)
    box(40, 750, ["F1-  ->  cátodo FLECHA 1", "(cerca de las flores, 9 LED verdes en serie)"], GRN)
    box(40, 900, ["F2-  ->  cátodo FLECHA 2", "(central, 9 LED verdes en serie)"], GRN)
    box(40, 1050, ["F3-  ->  cátodo FLECHA 3", "(cerca de la punta, 9 LED verdes en serie)"], GRN)
    box(40, 1210, ["Secuencia: F1 -> F2 -> F3 -> F1 ...", "Corriente fija 8.8-9.8 mA por flecha", "(LM317LZ), no requiere resistencia externa."], BLU, font=fs)

    # ---- J1/J2 entrada (borde derecho) ----
    x0, y0 = P(99.06, 25.4)          # J1 pin 2 = 36V+
    wire([(x0, y0), (x0 + 250, y0), (2560, 1030)], RED)
    x0, y0 = P(99.06, 30.48)         # J1 pin 1 = GND
    wire([(x0, y0), (x0 + 220, y0), (2560, 1160)], BLK)
    x0, y0 = P(99.06, 12.7)          # J2 pin 2 = VSW
    wire([(x0, y0), (x0 + 250, y0), (2560, 600)], ORG)
    x0, y0 = P(99.06, 17.78)         # J2 pin 1 = VIN
    wire([(x0, y0), (x0 + 220, y0), (2560, 700)], ORG)
    box(2560, 520, ["J2  INTERRUPTOR", "Interruptor ON/OFF de panel", "(balancín o palanca, >= 50 VCC 1 A).", "Si no se usa: puentear J2."], ORG)
    box(2560, 950, ["J1  ENTRADA 36 VCC", "36V+  <- positivo de la fuente", "GND   <- negativo de la fuente", "Fuente certificada y AISLADA,", "36 VCC >= 0.5 A (ej. Mean Well", "LRS-35-36). Verificar polaridad."], BLK)

    # ---- opcionales (borde inferior) ----
    for (x, col, lbl) in ((13.97, GRY, "+"), (19.05, GRY, "GND"), (26.67, GRY, "+"), (31.75, GRY, "GND"),
                          (86.36, GRY, "GND"), (91.44, GRY, "-")):
        x0, y0 = P(x, 73.66)
        wire([(x0, y0), (x0, 1830)], col, dash=True)
    box(520, 1830, ["J5 FLORES / J6 BAÑOS (opcionales, +36V fijos)", "NO CONECTAR hasta medir las series.", "Se habilitan soldando JP2 / JP3."], GRY, font=fs)
    box(1900, 1830, ["J4 CENTROS (opcional, parpadeo del 555)", "'-' = retorno conmutado por Q4; el + de las", "ramas se toma de J3 +36V. NO CONECTAR aún."], GRY, font=fs)

    # ---- controles ----
    x0, y0 = P(100.33, 59.69)
    d.line([(x0 + 60, y0), (2560, 1420)], fill=BLU, width=4)
    box(2560, 1380, ["RV1  VELOCIDAD", "0.24 s a 1.6 s por paso"], BLU, font=fs)
    x0, y0 = P(71.4, 69.9)
    d.line([(x0, y0 + 60), (1750, 2000)], fill=BLU, width=4)
    box(1500, 2000, ["SW2 REINICIO: vuelve a la flecha 1"], BLU, font=fs)
    im.save(OUT, optimize=True)
    print("imagen:", OUT)


if __name__ == "__main__":
    main()
