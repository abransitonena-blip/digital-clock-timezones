"""Fuente capacitiva (tipo Radox, NO aislada) para la palabra "OS" (O = 13 + S = 14 = 27 LED ámbar/amarillos
en serie) a 127 VCA, con puente rectificador redondo 2W10. PCB de 50 x 50 mm, una cara, pistas a mano.

    python3 gen/make.py          (dentro del contenedor de KiCad 9)
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import comun  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, ".."))
KI = os.path.join(ROOT, "kicad")
PROJECT = LIB = "FuenteOS"
NS = uuid.UUID("5d1f3c7a-2e4b-4a6c-9b8d-0f1e2d3c4b5a")
ROOT_UUID = "9a2b7c4d-1e3f-4a5b-8c6d-7e8f9a0b1c2d"

C = [
    ("J1", "127 VCA", "Connector:Screw_Terminal_01x02", "Clema_2P_P5.08mm", {"1": "L", "2": "N"}, (35.56, 71.12, 180),
     "Entrada de red 127 VCA (pin 1 = L fase, pin 2 = N neutro). Del mismo cable que la placa Radox"),
    ("C1", "334J 400V", "Device:C", "C_Poliester_P10-15mm", {"1": "L", "2": "X"}, (63.5, 60.96, 90),
     "Poliester 0.33 uF 400 V (paso 10 o 15 mm): fija la corriente (~10 mA con 27 LED ambar). "
     "Si los LED son blanco calido usar 474J"),
    ("R2", "1M 1/2W", "Device:R", "R_Axial_P10.16mm", {"1": "L", "2": "X"}, (63.5, 78.74, 90),
     "Descarga C1 al desenchufar (tau = 1M x 0.33uF = 0.33 s)"),
    ("R1", "220R 1W fusible", "Device:R", "R_1W_Vertical_P7.62mm", {"1": "X", "2": "AC"}, (93.98, 60.96, 90),
     "Resistencia fusible (flameproof): limita el pico al enchufar (180 V / 220 = 0.8 A) y actua como fusible"),
    ("BR1", "2W10", "Device:D_Bridge_+-AA", "Puente_2W10", {"1": "OS+", "2": "OS-", "3": "N", "4": "AC"},
     (132.08, 71.12, 0), "Puente rectificador redondo 2W10 (1000 V 2 A). Tambien W10M/W06M"),
    ("J2", "SALIDA OS", "Connector:Screw_Terminal_01x02", "Clema_2P_P5.08mm", {"1": "OS-", "2": "OS+"},
     (170.18, 71.12, 0), "Salida a O+S (27 LED en serie): pin 2 = + (anodo del primer LED), pin 1 = - (catodo del ultimo)"),
]

NOTES = [
    (20.32, 22.86,
     "FUENTE CAPACITIVA NO AISLADA - PALABRA 'OS' (O 13 + S 14 = 27 LED EN SERIE) - 127 VCA 60 Hz\n"
     "PELIGRO: TODO el circuito (placa, cables y LED) queda a potencial de red. No tocar con la placa enchufada.\n"
     "Montar dentro de la caja del letrero, LED detras del acrilico, sin partes metalicas accesibles."),
    (20.32, 101.6,
     "CALCULO (I = 4 f C (Vpico - Vtira)),  Vpico = 127 x 1.414 = 180 V:\n"
     "  LED ambar/amarillo (2.0 V): Vtira = 27 x 2.0 = 54 V -> C1 = 334J:  I = 240 x 0.33e-6 x (180 - 54) = 10.0 mA\n"
     "      red 115 V y Vf 2.2 V: 240 x 0.33e-6 x (162 - 59) = 8.1 mA     red 140 V y Vf 1.9 V: 240 x 0.33e-6 x (198 - 51) = 11.6 mA\n"
     "  LED blanco calido (3.0 V): Vtira = 27 x 3.0 = 81 V -> C1 = 474J:  I = 240 x 0.47e-6 x (180 - 81) = 11.2 mA\n"
     "  (LED 5 mm: maximo 20 mA)   R1: (15 mA rms)^2 x 220 = 0.05 W   C1: ~0 W (reactiva)\n"
     "Sin electrolitico a la salida (igual que Radox): si la tira se abre no hay nada que reviente."),
]
TEXTS_SCH = [(40.64, 48.26, "Entrada y limitacion de corriente"), (119.38, 48.26, "Puente 2W10 y salida")]

POS = {  # (x, y, rot) del pad 1, mm desde la esquina superior izquierda
    "J1": (6.0, 11.0, 270),
    "C1": (14.0, 5.0, 0),
    "R2": (14.0, 11.0, 0),
    "R1": (34.0, 5.0, 270),
    "BR1": (30.0, 22.0, 0),
    "J2": (45.0, 6.0, 180),
}
HOLES = [(3.5, 3.5), (3.5, 46.5), (46.5, 46.5)]
W = H = 50.0
WIDTH = {n: 1.2 for n in ("L", "N", "X", "AC", "OS+", "OS-")}
TRACKS = {
    "L": [[(6.0, 11.0), (14.0, 11.0), (14.0, 5.0)]],
    "X": [[(24.0, 5.0), (29.0, 5.0), (34.0, 5.0)], [(24.16, 11.0), (24.0, 5.0)]],
    "AC": [[(34.0, 12.62), (35.08, 13.7), (35.08, 22.0)]],
    "N": [[(6.0, 16.08), (6.0, 27.08), (30.0, 27.08)]],
    "OS+": [[(30.0, 22.0), (30.0, 8.8), (39.92, 8.8), (39.92, 6.0)]],
    "OS-": [[(35.08, 27.08), (45.0, 27.08), (45.0, 6.0)]],
}
TEXTS = [  # (texto, x, y, tamaño, ángulo, capa)
    ("L", 9.8, 8.6, 1.2, 0, "F.SilkS"),
    ("N", 9.8, 16.1, 1.2, 0, "F.SilkS"),
    ("127 VCA", 6.8, 21.2, 1.0, 0, "F.SilkS"),
    ("+", 39.92, 12.6, 1.6, 0, "F.SilkS"),
    ("-", 45.0, 12.6, 1.6, 0, "F.SilkS"),
    ("SALIDA OS", 42.4, 14.6, 0.9, 0, "F.SilkS"),
    ("PELIGRO 127V", 17.0, 33.0, 1.3, 0, "F.SilkS"),
    ("NO TOCAR ENCHUFADA", 17.0, 35.2, 1.0, 0, "F.SilkS"),
    ("OS: 27 LED  C1=334J (ambar)", 25.0, 40.0, 1.0, 0, "F.SilkS"),
    ("474J si son blanco calido", 25.0, 42.0, 1.0, 0, "F.SilkS"),
    ("FUENTE OS 127V v2", 25.0, 32.0, 1.4, 0, "B.Cu"),
]


def main():
    os.makedirs(KI, exist_ok=True)
    comun.make_footprints(KI, LIB, sorted({c[3] for c in C}))
    comun.make_schematic(KI, PROJECT, LIB, ROOT_UUID, NS, C, NOTES, TEXTS_SCH,
                         "Fuente capacitiva 127 VCA para la palabra OS (27 LED)",
                         ["NO AISLADA: todo el circuito queda a potencial de red (igual que la placa Radox)",
                          "C1 = 334J -> 10 mA con LED ambar (474J si son blanco calido)"])
    b = comun.Board(W, H, LIB, KI, NS, C, POS, HOLES)
    b.add_tracks(TRACKS, WIDTH)
    b.ref_pos({"R1": (31.4, 8.3, 90), "BR1": (32.5, 18.6, 0)})
    b.texts(TEXTS)
    b.save(PROJECT)
    comun.make_project(KI, PROJECT, red_nets=WIDTH.keys(), clr_red=1.5, clr=1.5, track=1.2)
    print("ok")


if __name__ == "__main__":
    main()
