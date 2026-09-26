"""Placa B - fuente capacitiva de 3 salidas para letreros LED fijos a 127 VCA (NO aislada, principio Radox).

Cada salida es independiente: capacitor de poliéster (se elige según la tira) + resistencia fusible 220 ohm
1 W + puente 2W10. Sin electrolítico a la salida (si una tira se abre no hay nada que reviente).
Una resistencia de 1M entre L y N descarga los capacitores al desenchufar.
PCB 50 x 50 mm, una cara; puentes (si hacen falta) con cable forrado del lado del cobre.

    python3 gen/make.py          (dentro del contenedor de KiCad 9)
"""
import os, sys, json, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "fuente-os-127v", "gen"))
import comun  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, ".."))
KI = os.path.join(ROOT, "kicad")
PROJECT = LIB = "Fuente3"
NS = uuid.UUID("9b2d4f6a-8c0e-4a2c-8e4a-6c8e0a2c4e6a")
ROOT_UUID = "5e7a9c1e-3f5b-4d7f-9b1d-3f5b7d9f1b3d"
R, CD = "Device:R", "Device:C"
T2 = "Connector:Screw_Terminal_01x02"

T1 = "Connector:Screw_Terminal_01x01"
C = [
    ("J1", "127 VCA", T2, "Clema_2P_P5.08mm", {"1": "N", "2": "L"}, (20.32, 45.72, 180),
     "Entrada 127 VCA (pin 1 = N, pin 2 = L; se pueden intercambiar). Del mismo cable que las otras placas"),
    ("R10", "1M 1/2W", R, "R_Vertical_P5.08mm", {"1": "L", "2": "N"}, (20.32, 66.04, 0),
     "Descarga los capacitores al desenchufar (entre L y N)"),
]
VALS = {1: "224J 400V", 2: "334J 400V", 3: "474J 400V"}
for n in (1, 2, 3):
    y = 30.48 + (n - 1) * 25.4
    C += [
        ("C%d" % n, VALS[n], CD, "C_Poliester_P10-15mm", {"1": "L", "2": "X%d" % n}, (45.72, y, 90),
         "Capacitor de la salida %d: fija la corriente (ver tabla). Poliester 400 V, paso 10 o 15 mm" % n),
        ("R%d" % n, "220R 1W fusible", R, "R_1W_Vertical_P7.62mm", {"1": "X%d" % n, "2": "AC%d" % n}, (68.58, y, 90),
         "Resistencia fusible de la salida %d (limita el pico al enchufar)" % n),
        ("BR%d" % n, "2W10", "Device:D_Bridge_+-AA", "Puente_2W10",
         {"1": "S%d+" % n, "2": "S%d-" % n, "3": "AC%d" % n, "4": "N"}, (96.52, y, 0),
         "Puente 2W10 de la salida %d" % n),
        ("J%d" % (2 * n), "S%d +" % n, T1, "Cables_1P_P5.08mm", {"1": "S%d+" % n}, (124.46, y - 2.54, 0),
         "Salida %d +: anodo del primer LED de la tira" % n),
        ("J%d" % (2 * n + 1), "S%d -" % n, T1, "Cables_1P_P5.08mm", {"1": "S%d-" % n}, (124.46, y + 5.08, 0),
         "Salida %d -: catodo del ultimo LED de la tira" % n),
    ]

NOTES = [
    (20.32, 17.78,
     "PLACA B - FUENTE CAPACITIVA DE 3 SALIDAS PARA LETREROS FIJOS - 127 VCA - NO AISLADA (principio Radox)\n"
     "PELIGRO: TODO el circuito (placa, cables y LED) queda a potencial de red. No tocar con la placa enchufada."),
    (20.32, 106.68,
     "ELEGIR EL CAPACITOR DE CADA SALIDA:  I = 240 x C x (180 V - Vtira)   (Vtira = suma de los LED, max ~100 V)\n"
     "  Tira hasta 30 V (p. ej. 9-10 verdes/blancos o 15 ambar):  224J -> 8 mA\n"
     "  Tira 40-60 V (p. ej. 27 ambar = 54 V, 20 blancos = 60 V): 334J -> 9-10 mA\n"
     "  Tira 60-100 V (p. ej. 27 blancos = 81 V, 45 ambar = 90 V): 474J -> 9-11 mA\n"
     "Una salida sin filtro sirve tambien para alimentar las flechas del secuenciador (anodo comun al +).\n"
     "Sin electrolitico a la salida: si la tira se abre, no hay nada que reviente."),
]
TEXTS_SCH = [(38.1, 25.4, "Salidas 1 a 3 (iguales; solo cambia el capacitor)")]

W = H = 50.0
Y0 = {1: 1.6, 2: 16.6, 3: 31.6}          # borde superior de cada fila (paso 15 mm)
POS = {"J1": (5.8, 5.2, 270), "R10": (5.8, 15.2, 270)}
TRACKS = {
    "N": [[(5.8, 5.2), (5.8, 1.4), (48.4, 1.4), (48.4, Y0[3] + 3.0)], [(5.8, 5.2), (1.6, 5.2), (1.6, 20.28), (5.8, 20.28)]],
    "L": [[(5.8, 10.28), (13.5, 10.28)], [(13.5, Y0[1] + 3.0), (13.5, Y0[3] + 3.0)], [(5.8, 10.28), (5.8, 15.2)]],
}
for n, y0 in Y0.items():
    POS["C%d" % n] = (13.5, y0 + 3.0, 0)
    POS["R%d" % n] = (33.0, y0 + 3.0, 270)
    POS["BR%d" % n] = (38.5, y0 + 3.0, 0)
    POS["J%d" % (2 * n)] = (20.0, y0 + 8.2, 0)          # S+
    POS["J%d" % (2 * n + 1)] = (43.58, y0 + 12.6, 0)    # S-
    TRACKS["N"].append([(48.4, y0 + 3.0), (43.58, y0 + 3.0)])
    TRACKS["X%d" % n] = [[(23.5, y0 + 3.0), (28.5, y0 + 3.0), (33.0, y0 + 3.0)]]
    TRACKS["AC%d" % n] = [[(33.0, y0 + 10.62), (35.5, y0 + 10.62), (38.5, y0 + 8.08)]]
    # el + cruza la fila por entre las patas de R (bajo su cuerpo) hasta su pad, a la izquierda
    TRACKS["S%d+" % n] = [[(38.5, y0 + 3.0), (35.6, y0 + 5.9), (35.6, y0 + 6.6), (21.0, y0 + 6.6), (20.0, y0 + 8.2)]]
    TRACKS["S%d-" % n] = [[(43.58, y0 + 8.08), (43.58, y0 + 12.6)]]
WIDTH = {n: 1.2 for n in TRACKS}
RED = tuple(sorted(TRACKS))
TEXTS = [
    ("N", 9.9, 5.2, 1.2, 0, "F.SilkS"), ("L", 9.9, 10.3, 1.2, 0, "F.SilkS"),
    ("127VCA", 5.8, 13.8, 0.8, 0, "F.SilkS"),
]
for n, y0 in Y0.items():
    TEXTS += [("S%d+" % n, 16.4, y0 + 8.2, 1.0, 0, "F.SilkS"), ("S%d-" % n, 47.0, y0 + 12.6, 0.9, 90, "F.SilkS")]
TEXTS += [("PELIGRO 127V - NO TOCAR ENCHUFADA", 25.0, 46.6, 0.8, 0, "F.SilkS"),
          ("B: FUENTE 3 SALIDAS", 25.0, 48.4, 0.8, 0, "F.SilkS"),
          ("FUENTE 3 SALIDAS v1", 27.0, 48.0, 1.0, 0, "B.Cu")]


def main():
    os.makedirs(KI, exist_ok=True)
    comun.make_footprints(KI, LIB, sorted({c[3] for c in C}))
    comun.make_schematic(KI, PROJECT, LIB, ROOT_UUID, NS, C, NOTES, TEXTS_SCH,
                         "Placa B: fuente capacitiva de 3 salidas para letreros fijos 127 VCA",
                         ["NO AISLADA: todo el circuito queda a potencial de red (igual que la placa Radox)",
                          "Capacitor de cada salida segun la tira: 224J / 334J / 474J"], paper="A4",
                         company="PCB 50 x 50 mm, una cara, THT, transferencia de toner, sin puentes")
    b = comun.Board(W, H, LIB, KI, NS, C, POS)
    b.add_tracks(TRACKS, WIDTH)
    b.texts(TEXTS)
    b.save(PROJECT)
    comun.make_project(KI, PROJECT, red_nets=RED, clr_red=1.2, clr=1.2, track=1.2)
    print("ok")


if __name__ == "__main__":
    main()
