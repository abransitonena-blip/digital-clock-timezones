"""LetreroLab AP-0.1: notas y regla en los PDF 1:1 de cada placa, hoja A4 para planchar (2 potencia + 2 cabezal),
PNG a 1200 ppp y .zip de Gerber para JLCPCB/PCBWay.   python3 tools/ap01_impresion.py   (requiere PyMuPDF)"""
import os, json, zipfile
import pymupdf as fitz

HW = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MM = 72 / 25.4
W, H, M = 90.0, 80.0, 1.5
PLACAS = [("ap01-potencia", "AP01_Potencia", "POTENCIA", "AP-0.1 POTENCIA",
           "LetreroLab AP-0.1 POTENCIA (fuente 100-240 VCA, 4 MOSFET, relevador) - 90 x 80 mm - PELIGRO: zona de 127 V",
           {"0.8": "resistencias, 1N4148, C1, 2N7000", "1.0": "fusible, varistor, pines J5", "1.1": "MOSFET TO-220",
            "1.3": "clemas, fuente HLK, relevador", "3.2": "montaje M3"}),
          ("ap01-cabezal", "AP01_Cabezal", "CABEZAL", "AP-0.1 CABEZAL",
           "LetreroLab AP-0.1 CABEZAL (ATmega328P, Bluetooth, reloj, IR, LDR) - 90 x 80 mm - bajo voltaje",
           {"0.8": "zocalo DIP-28, resistencias, capacitores, resonador, LED", "1.0": "tiras de pines y zocalo BLE",
            "1.1": "regulador 7805", "3.2": "montaje M3"})]


def ruler(page, x0, y, length=100):
    page.draw_line((x0 * MM, y * MM), ((x0 + length) * MM, y * MM), width=0.6)
    for i in range(length + 1):
        h = 3.0 if i % 10 == 0 else (2.0 if i % 5 == 0 else 1.2)
        page.draw_line(((x0 + i) * MM, y * MM), ((x0 + i) * MM, (y - h) * MM), width=0.3)
        if i % 10 == 0:
            page.insert_text(((x0 + i) * MM - 3, (y + 3.5) * MM), str(i), fontsize=6)
    page.insert_text((x0 * MM, (y + 7) * MM), "Regla de calibracion: debe medir 100 mm exactos", fontsize=7)


def anotar(d, nombre, texto, pie, usos):
    pcb = os.path.join(HW, d, "fabricacion", "pcb")
    holes = json.load(open(os.path.join(pcb, "barrenos.json")))
    notas = {
        "1_cobre_para_planchado_1a1.pdf": ["COBRE (B.Cu) PARA TRANSFERENCIA DE TONER - ESCALA 1:1 - " + nombre,
                                           "Imprimir al 100 %%. Ya esta en espejo: el texto '%s' se lee AL REVES en el papel." % texto,
                                           "Toner contra el cobre. Puntos blancos = centro de cada barreno. Sin puentes."],
        "2_cobre_vista_desde_lado_soldadura_1a1.pdf": ["COBRE VISTO DESDE EL LADO DE SOLDADURA (revision) - " + nombre],
        "3_lado_componentes_1a1.pdf": ["LADO DE COMPONENTES (serigrafia) - ESCALA 1:1 - " + nombre],
        "4_plantilla_perforaciones_1a1.pdf": ["PLANTILLA DE PERFORACIONES - ESCALA 1:1 - " + nombre,
                                              "Circulo = diametro real de la broca (vista desde el lado de componentes)."],
        "5_ensamble_componentes_con_valores.pdf": ["GUIA DE ENSAMBLE: referencias y valores - " + nombre]}
    for f, lines in notas.items():
        p = os.path.join(pcb, f)
        doc = fitz.open(p)
        pg = doc[0]
        y = 14
        for i, t in enumerate(lines):
            pg.insert_text((15 * MM, y * MM), t, fontsize=10 if i == 0 else 8, fontname="hebo" if i == 0 else "helv")
            y += 6 if i == 0 else 4.5
        pg.insert_text((15 * MM, 202 * MM), pie, fontsize=7)
        ruler(pg, 20, 190)
        if f.startswith("4_"):
            pg.insert_text((200 * MM, 110 * MM), "Barrenos (diametro : cantidad)", fontsize=9, fontname="hebo")
            yy = 116
            for dd, n in holes.items():
                pg.insert_text((200 * MM, yy * MM), "%s mm : %d" % (dd, n), fontsize=8)
                pg.insert_text((205 * MM, (yy + 3.5) * MM), usos.get(dd, ""), fontsize=6.5)
                yy += 9
        doc.save(p + ".tmp", garbage=3, deflate=True)
        doc.close()
        os.replace(p + ".tmp", p)


def hoja():
    out = os.path.join(HW, "ap01-gabinete", "imprimir")
    os.makedirs(out, exist_ok=True)
    clip = fitz.Rect((100 - M) * MM, (100 - M) * MM, (100 + W + M) * MM, (100 + H + M) * MM)
    doc = fitz.open()
    pg = doc.new_page(width=210 * MM, height=297 * MM)
    t = ["LETREROLAB AP-0.1 - COBRE PARA PLANCHAR - ESCALA 1:1 (placas de 90 x 80 mm)",
         "Arriba: 2 placas de POTENCIA.  Abajo: 2 placas CABEZAL (una de repuesto de cada una).",
         "Imprimir en LASER al 100 % (sin 'Ajustar a la pagina') en papel couche. Verificar la regla de 100 mm.",
         "Ya estan en espejo: los textos de cobre se leen AL REVES en el papel. Sin puentes de cable."]
    y = 12
    for i, s in enumerate(t):
        pg.insert_text((12 * MM, y * MM), s, fontsize=10 if i == 0 else 7.5, fontname="hebo" if i == 0 else "helv")
        y += 6 if i == 0 else 4.2
    for r, (d, nombre, *_rest) in enumerate(PLACAS):
        src = fitz.open(os.path.join(HW, d, "fabricacion", "pcb", "1_cobre_para_planchado_1a1.pdf"))
        for c in range(2):
            x0, y0 = 12 + c * 95, 34 + r * 92
            pg.show_pdf_page(fitz.Rect(x0 * MM, y0 * MM, (x0 + W + 2 * M) * MM, (y0 + H + 2 * M) * MM), src, 0, clip=clip)
            pg.insert_text(((x0 + M) * MM, (y0 + H + 2 * M + 4) * MM), nombre.replace("AP01_", "") + " %d" % (c + 1),
                           fontsize=7)
        pix = src[0].get_pixmap(dpi=1200, clip=clip, colorspace=fitz.csGRAY)
        pix.set_dpi(1200, 1200)
        pix.save(os.path.join(out, nombre + "_cobre_1200ppp.png"))
    ruler(pg, 40, 225)
    doc.save(os.path.join(out, "AP01_cobre_planchar_A4.pdf"), garbage=3, deflate=True)


def zips():
    for d, nombre, *_r in PLACAS:
        g = os.path.join(HW, d, "fabricacion", "gerber")
        os.makedirs(os.path.join(HW, d, "fabricacion", "jlcpcb"), exist_ok=True)
        with zipfile.ZipFile(os.path.join(HW, d, "fabricacion", "jlcpcb", nombre + "_gerber_JLCPCB.zip"), "w",
                             zipfile.ZIP_DEFLATED) as z:
            for f in sorted(os.listdir(g)):
                if f.endswith((".gbr", ".drl")):
                    z.write(os.path.join(g, f), f)


if __name__ == "__main__":
    for d, nombre, _c, texto, pie, usos in PLACAS:
        anotar(d, nombre.replace("AP01_", "AP-0.1 ").upper(), texto, pie, usos)
    hoja()
    zips()
    print("ok")
