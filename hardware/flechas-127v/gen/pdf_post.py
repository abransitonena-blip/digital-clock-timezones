"""Flechas: añade encabezado, instrucciones y regla de calibración de 100 mm a los PDF 1:1.

Se ejecuta en el equipo anfitrión (requiere PyMuPDF):  python3 gen/pdf_post.py
"""
import os, json
import pymupdf as fitz

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "fabricacion", "pcb")
MM = 72 / 25.4

NOTAS = {
    "1_cobre_para_planchado_1a1.pdf": [
        "COBRE (B.Cu) PARA TRANSFERENCIA DE TONER - ESCALA 1:1",
        "Imprimir al 100 % (desactivar 'Ajustar a la pagina'). Verificar la regla de 100 mm antes de planchar.",
        "La imagen YA esta en la orientacion correcta para planchar: el texto 'FLECHAS 127V v1' debe verse AL REVES",
        "en el papel. Coloque el lado del toner contra el cobre. Los puntos blancos marcan el centro de cada barreno.",
    ],
    "2_cobre_vista_desde_lado_soldadura_1a1.pdf": [
        "COBRE VISTO DESDE EL LADO DE SOLDADURA (solo para revision) - ESCALA 1:1",
        "Asi se vera la placa ya atacada, mirando el cobre. NO usar para planchar.",
    ],
    "3_lado_componentes_1a1.pdf": [
        "LADO DE COMPONENTES (serigrafia) SIN ESPEJO - ESCALA 1:1",
        "Opcional: planchar sobre el lado sin cobre para marcar la posicion y polaridad de los componentes,",
        "alineando con los barrenos ya perforados.",
    ],
    "4_plantilla_perforaciones_1a1.pdf": [
        "PLANTILLA DE PERFORACIONES - ESCALA 1:1 (vista desde el lado de componentes)",
        "Circulo = diametro real de la broca. Pegar sobre el lado de componentes o usar como referencia.",
    ],
    "5_ensamble_componentes_con_valores.pdf": [
        "GUIA DE ENSAMBLE: referencias y valores (vista lado de componentes)",
    ],
}


def ruler(page, x0_mm, y_mm, length=100):
    x0 = x0_mm * MM
    y = y_mm * MM
    page.draw_line((x0, y), (x0 + length * MM, y), width=0.6)
    for i in range(0, length + 1):
        h = 3.0 if i % 10 == 0 else (2.0 if i % 5 == 0 else 1.2)
        page.draw_line((x0 + i * MM, y), (x0 + i * MM, y - h * MM), width=0.3)
        if i % 10 == 0:
            page.insert_text((x0 + i * MM - 3, y + 3.5 * MM), str(i), fontsize=6, fontname="helv")
    page.insert_text((x0, y + 7 * MM), "Regla de calibracion: 100 mm exactos (medir con regla o vernier)",
                     fontsize=7, fontname="helv")


def main():
    holes = json.load(open(os.path.join(PCB, "barrenos.json")))
    for name, lines in NOTAS.items():
        path = os.path.join(PCB, name)
        doc = fitz.open(path)
        page = doc[0]
        y = 14 * MM
        for i, t in enumerate(lines):
            page.insert_text((15 * MM, y), t, fontsize=10 if i == 0 else 8, fontname="hebo" if i == 0 else "helv")
            y += (6 if i == 0 else 4.5) * MM
        page.insert_text((15 * MM, 200 * MM), "Secuenciador de 3 flechas 127 VCA (NE555 + CD4017 + SCR) - placa 50 x 60 mm - v1.0 - NO AISLADA: PELIGRO 127 V",
                         fontsize=7, fontname="helv")
        ruler(page, 20, 170)
        if name.startswith("4_"):
            yy = 170
            page.insert_text((160 * MM, 165 * MM), "Barrenos (diametro : cantidad)", fontsize=9, fontname="hebo")
            usos = {"0.8": "resistencias 1/4W, CI, SCR, C5, C3, puentes W", "1.0": "R1/R2 1W, C1/C2, 2W10, zener",
                    "1.3": "clemas de 5.08 mm", "3.2": "montaje M3"}
            yy = 171
            for d, n in holes.items():
                page.insert_text((160 * MM, yy * MM), "%s mm : %d   (%s)" % (d, n, usos.get(d, "")), fontsize=8,
                                 fontname="helv")
                yy += 5
        doc.save(path + ".tmp", garbage=3, deflate=True)
        doc.close()
        os.replace(path + ".tmp", path)
    print("PDF anotados")


if __name__ == "__main__":
    main()
