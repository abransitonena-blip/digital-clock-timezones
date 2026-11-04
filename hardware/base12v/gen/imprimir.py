"""Hoja A4 para imprimir en láser: 4 copias 1:1 del cobre (ya en espejo para planchar) + PNG a 1200 ppp,
y el .zip de Gerber para mandar a fabricar (JLCPCB/PCBWay).

Se ejecuta en el equipo anfitrión (requiere PyMuPDF), después de outputs.py y pdf_post.py:
    python3 gen/imprimir.py
"""
import os
import pymupdf as fitz

HERE = os.path.dirname(os.path.abspath(__file__))
FAB = os.path.join(HERE, "..", "fabricacion")
SRC = os.path.join(FAB, "pcb", "1_cobre_para_planchado_1a1.pdf")
OUT = os.path.join(FAB, "imprimir")
MM = 72 / 25.4
W, H, M = 60.0, 72.0, 1.5                       # placa y margen alrededor del contorno


def main():
    os.makedirs(OUT, exist_ok=True)
    src = fitz.open(SRC)
    clip = fitz.Rect((100 - M) * MM, (100 - M) * MM, (100 + W + M) * MM, (100 + H + M) * MM)
    doc = fitz.open()
    page = doc.new_page(width=210 * MM, height=297 * MM)
    t = ["PLACA BASE LETREROLAB 12 V - COBRE PARA PLANCHAR - 4 COPIAS ESCALA 1:1 (60 x 72 mm, v1.1)",
         "Imprimir en LASER al 100 % (sin 'Ajustar a la pagina'), en papel couche o de revista. Verificar la regla de 100 mm.",
         "Ya esta en espejo: 'LETREROLAB 12V' se lee AL REVES en el papel. Toner contra el cobre, plancha 3-5 min.",
         "Puntos blancos = centro de cada barreno. Sin puentes. Recortar por la linea del contorno."]
    y = 14
    for i, s in enumerate(t):
        page.insert_text((15 * MM, y * MM), s, fontsize=10 if i == 0 else 7.5, fontname="hebo" if i == 0 else "helv")
        y += 6 if i == 0 else 4.2
    for k in range(4):
        x0, y0 = 25 + (k % 2) * 85, 38 + (k // 2) * 92
        page.show_pdf_page(fitz.Rect(x0 * MM, y0 * MM, (x0 + W + 2 * M) * MM, (y0 + H + 2 * M) * MM), src, 0, clip=clip)
        page.insert_text(((x0 + M) * MM, (y0 + H + 2 * M + 4) * MM), "Copia %d" % (k + 1), fontsize=7, fontname="helv")
    x0, yr = 40, 270
    page.draw_line((x0 * MM, yr * MM), ((x0 + 100) * MM, yr * MM), width=0.6)
    for i in range(101):
        h = 3.0 if i % 10 == 0 else (2.0 if i % 5 == 0 else 1.2)
        page.draw_line(((x0 + i) * MM, yr * MM), ((x0 + i) * MM, (yr - h) * MM), width=0.3)
        if i % 10 == 0:
            page.insert_text(((x0 + i) * MM - 3, (yr + 3.5) * MM), str(i), fontsize=6, fontname="helv")
    page.insert_text((x0 * MM, (yr + 8) * MM), "Regla de calibracion: debe medir 100 mm exactos", fontsize=7,
                     fontname="helv")
    pdf = os.path.join(OUT, "Base12V_cobre_4copias_A4.pdf")
    doc.save(pdf, garbage=3, deflate=True)
    pix = src[0].get_pixmap(dpi=1200, clip=clip, colorspace=fitz.csGRAY)
    pix.set_dpi(1200, 1200)
    pix.save(os.path.join(OUT, "Base12V_cobre_1200ppp.png"))
    import zipfile                                           # paquete Gerber para fabricar en JLCPCB / PCBWay
    os.makedirs(os.path.join(FAB, "jlcpcb"), exist_ok=True)
    gz = os.path.join(FAB, "jlcpcb", "Base12V_v1.1_gerber_JLCPCB.zip")
    with zipfile.ZipFile(gz, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(os.path.join(FAB, "gerber"))):
            if f.endswith((".gbr", ".drl")):
                z.write(os.path.join(FAB, "gerber", f), f)
    print("ok", pdf, gz)


if __name__ == "__main__":
    main()
