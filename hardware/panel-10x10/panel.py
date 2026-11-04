"""Une la placa A (flechas, 50 x 60 mm) y la placa B (fuente de 3 salidas, 50 x 50 mm) en una sola
fenólica de 10 x 10 cm, a escala 1:1, para planchar las dos de una vez y luego cortarlas.

    python3 hardware/panel-10x10/panel.py      (en el anfitrión, requiere PyMuPDF)
"""
import os
import pymupdf as fitz

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.join(HERE, "..")
MM = 72 / 25.4
OX, OY = 40.0, 48.0          # esquina superior izquierda de la fenólica de 10 x 10 en la hoja (mm)
BOARDS = [  # (carpeta, ancho, alto, posición x dentro del panel)
    ("flechas-127v", 50.0, 60.0, 0.0),
    ("fuente3-127v", 50.0, 50.0, 50.0),
]
SHEETS = {
    "1_cobre_para_planchado_1a1.pdf": [
        "PANEL 10 x 10 cm - COBRE PARA TRANSFERENCIA DE TONER - ESCALA 1:1",
        "Imprimir al 100 % (sin 'Ajustar a la pagina') en impresora LASER sobre papel couche. Medir la regla de 100 mm.",
        "Izquierda: placa A (flechas, 50 x 60 mm). Derecha: placa B (fuente de 3 salidas, 50 x 50 mm).",
        "Los textos del cobre deben verse AL REVES en el papel. Despues de atacar, cortar por la linea central.",
    ],
    "3_lado_componentes_1a1.pdf": [
        "PANEL 10 x 10 cm - LADO DE COMPONENTES (serigrafia) - ESCALA 1:1",
        "Opcional: planchar sobre el lado sin cobre, alineado con los barrenos.",
    ],
    "4_plantilla_perforaciones_1a1.pdf": [
        "PANEL 10 x 10 cm - PLANTILLA DE PERFORACIONES - ESCALA 1:1 (vista lado de componentes)",
        "Circulo = diametro de broca: 0.8 mm (resistencias 1/4 W, CI, SCR), 1.0 mm (1 W, poliester, 2W10), 1.3 mm (clemas y cables).",
    ],
}


def ruler(page, x0, y, length=100):
    page.draw_line((x0 * MM, y * MM), ((x0 + length) * MM, y * MM), width=0.6)
    for i in range(length + 1):
        h = 3.0 if i % 10 == 0 else (2.0 if i % 5 == 0 else 1.2)
        page.draw_line(((x0 + i) * MM, y * MM), ((x0 + i) * MM, (y - h) * MM), width=0.3)
        if i % 10 == 0:
            page.insert_text(((x0 + i) * MM - 3, (y + 3.5) * MM), str(i), fontsize=6, fontname="helv")
    page.insert_text((x0 * MM, (y + 7) * MM), "Regla de calibracion: 100 mm exactos", fontsize=7, fontname="helv")


def main():
    out = fitz.open()
    for name, lines in SHEETS.items():
        page = out.new_page(width=297 * MM, height=210 * MM)
        for folder, w, h, px in BOARDS:
            src = fitz.open(os.path.join(HW, folder, "fabricacion", "pcb", name))
            clip = fitz.Rect(99.0 * MM, 99.0 * MM, (101.0 + w) * MM, (101.0 + h) * MM)
            dst = fitz.Rect((OX + px - 1.0) * MM, (OY - 1.0) * MM, (OX + px + w + 1.0) * MM, (OY + h + 1.0) * MM)
            page.show_pdf_page(dst, src, 0, clip=clip)
        # contorno de la fenólica de 10 x 10 y línea de corte
        page.draw_rect(fitz.Rect(OX * MM, OY * MM, (OX + 100) * MM, (OY + 100) * MM), width=0.3, dashes="[2 2] 0")
        page.draw_line(((OX + 50) * MM, (OY - 3) * MM), ((OX + 50) * MM, (OY + 103) * MM), width=0.3, dashes="[1 2] 0")
        page.insert_text(((OX + 101) * MM, (OY + 50) * MM), "corte", fontsize=7, fontname="helv", rotate=90)
        y = 14
        for i, t in enumerate(lines):
            page.insert_text((15 * MM, y * MM), t, fontsize=10 if i == 0 else 8, fontname="hebo" if i == 0 else "helv")
            y += 6 if i == 0 else 4.5
        page.insert_text(((OX + 2) * MM, (OY + 64) * MM), "A: flechas (100 / 010 / 001)", fontsize=7, fontname="helv")
        page.insert_text(((OX + 52) * MM, (OY + 54) * MM), "B: fuente 3 salidas fijas", fontsize=7, fontname="helv")
        ruler(page, 160, 175)
        page.insert_text((15 * MM, 202 * MM), "Letrero Radox 246-402 modificado - placas A + B - 127 VCA NO AISLADAS: PELIGRO",
                         fontsize=7, fontname="helv")
        # cada tipo de hoja en su propio PDF
        single = fitz.open()
        single.insert_pdf(out, from_page=len(out) - 1, to_page=len(out) - 1)
        single.save(os.path.join(HERE, "panel_" + name), garbage=3, deflate=True)
    print("panel listo")


if __name__ == "__main__":
    main()
