"""Ubicación de componentes en la PCB (mm, origen = esquina superior izquierda).

(x, y, rotación) de la huella = posición del pad 1. Rotación en grados (antihorario).
Coordenadas en múltiplos de 0.3175 mm para que los pads caigan en la rejilla del ruteador.

Topología (una sola cara, sin cruces):
  * +36 V: bus por el borde superior e izquierdo (llega a J3 y a los puentes JP1-JP3).
  * GND:   bus por el borde derecho e inferior + bus vertical x=47.6 que pasa por debajo
           de las resistencias de compuerta (puentes naturales entre la lógica y las salidas).
  * +12 V: bus vertical x=73.66 desde el LM317T hacia la lógica.
"""
W, H = 105.0, 80.0

POS = {}


def put(ref, x, y, r=0):
    POS[ref] = (x, y, r)


# ---- entrada (borde derecho) y banda superior ----
put("J2", 99.06, 12.7, 270)      # 1 VSW (arriba), 2 VIN
put("J1", 99.06, 25.4, 270)      # 1 VIN (36V+), 2 GND
put("F1", 92.075, 12.7, 180)     # VSW 86.995, VF 81.915
put("D1", 68.58, 12.7, 0)        # K(+36V) 68.58, A(VF) 78.74
put("D2", 64.77, 5.08, 270)      # K 5.08 (+36V), A 17.78 (GND)
put("C1", 58.1, 5.08, 270)       # + 5.08, - 8.89
put("C2", 52.07, 5.08, 270)      # +36V 5.08, GND 10.16
put("R1", 42.545, 3.81, 270)    # +36V 3.81, LED1A 8.89
put("LED1", 47.625, 11.43, 90)   # K 11.43, A 8.89
put("U3", 71.12, 20.32, 0)       # ADJ 71.12, OUT 73.66, IN 76.2
put("R2", 73.66, 24.765, 180)    # +12V 73.66, ADJ12 68.58
put("R3", 64.77, 26.035, 90)     # ADJ12 26.035, GND 20.955

# ---- filas de salida (flechas) ----
ROWS = [(1, 19.05, "U4", "R22", "R23", "Q1", "R17", "R16", "R13", "LED3"),
        (2, 33.02, "U5", "R24", "R25", "Q2", "R19", "R18", "R14", "LED4"),
        (3, 46.99, "U6", "R26", "R27", "Q3", "R21", "R20", "R15", "LED5")]
BUS_X = 47.625
for n, y0, u, ra, rb, q, rp, rg, ri, led in ROWS:
    put(u, 22.86, y0, 180)                 # IN 17.78, OUT 20.32, ADJ 22.86
    put(ra, 19.05, y0 - 4.445, 90)         # InA abajo, InB arriba
    put(rb, 24.13, y0 - 9.525, 270)        # InB arriba, DRN abajo
    put(q, 33.02, y0, 180)                 # S 33.02, G 30.48, D 27.94
    put(rp, 30.48, y0 - 4.445, 90)         # G abajo, GND arriba
    put(rg, 53.34, y0 - 3.81, 180)         # Qk 53.34, Gn 43.18 (puente sobre el bus GND)
    put(ri, 53.34, y0 + 0.9525, 270)       # Qk, LEDA abajo
    put(led, BUS_X, y0 + 6.0325, 0)        # K sobre el bus, A a la derecha
put("J3", 6.35, 27.94, 90)                 # 1 F3N 27.94, 2 F2N, 3 F1N, 4 +36V 12.7

# ---- CENTROS y salidas fijas (abajo a la izquierda) ----
put("R28", 77.47, 60.96, 0)              # CLK 53.34, G4 43.18 (puente sobre el bus GND)
put("Q4", 83.82, 64.77, 0)               # S 44.45, G 41.91, D 39.37
put("R29", 90.17, 60.325, 0)               # G4 41.91, GND 46.99
put("J4", 91.44, 73.66, 180)               # 1 CENT_D 44.45, 2 V_CENT 39.37
put("J6", 31.75, 73.66, 180)               # 1 GND 31.75, 2 V_BANO 26.67
put("J5", 19.05, 73.66, 180)               # 1 GND 19.05, 2 V_FLOR 13.97
put("JP3", 15.24, 66.04, 0)                # +36V 16.51, V_BANO 24.13
put("JP2", 8.255, 62.23, 270)              # +36V 62.23, V_FLOR 69.85

# ---- lógica ----
put("U2", 58.42, 33.02, 0)                 # izq: 1..8 (y 30.48..48.26); der x 66.04: 16..9
put("C7", 61.595, 26.67, 90)                # +12V 26.67, GND 21.59
put("U1", 87.63, 40.64, 0)                 # izq 1 GND,2 TRIG,3 OUT,4 RST; der 8 VCC,7 DIS,6 THR,5 CV
put("R7", 80.01, 35.56, 180)               # CLK555 80.01, CLK 69.85 (puente sobre el bus +12V)
put("C4", 96.52, 36.83, 180)               # +12V 87.63, GND 82.55
put("C3", 88.9, 23.495, 270)              # + 27.305, - 31.115
put("R5", 100.33, 38.1, 270)                # +12V, DIS
put("R6", 100.33, 46.99, 270)               # DIS, RB
put("RV1", 100.33, 57.15, 90)              # RB 58.42, TIM 55.88, TIM 53.34
put("C5", 91.7575, 65.405, 0)                 # TIM, GND
put("C6", 95.25, 52.07, 180)              # CV 87.63, GND 82.55
put("R8", 81.28, 32.0675, 0)               # CLK555, LED6A
put("LED6", 90.4875, 33.3375, 90)              # K 64.77, A 62.23
put("R9", 69.5325, 50.8, 0)              # INH, GND
put("D7", 60.6425, 61.595, 90)               # K RST (52.07), A Q3 (62.23)
put("D5", 63.5, 57.785, 0)               # K RST, A POR
put("R11", 57.15, 61.595, 270)              # RST, GND
put("C8", 73.66, 62.23, 180)               # + 62.23, - 64.77 (POR)
put("R10", 64.77, 66.675, 270)              # POR, GND
put("SW2", 73.66, 66.675, 270)                # 1 +12V, 2 SWR  (botón REINICIO)
put("R30", 73.66, 54.61, 0)               # SWR, RST

for i, (x, y) in enumerate([(4.0, 4.0), (101.0, 4.0), (4.0, 76.0), (101.0, 76.0)]):
    put("H%d" % (i + 1), x, y, 0)

KEEPOUTS = [(4.0, 4.0, 3.6), (101.0, 4.0, 3.6), (4.0, 76.0, 3.6), (101.0, 76.0, 3.6)]

# Buses pre-ruteados
PRE = {
    "+36V": [[(68.58, 12.7), (68.58, 2.54), (9.525, 2.54), (9.525, 8.89), (2.54, 8.89), (2.54, 60.325)],
             ],
    "GND": [[(99.06, 30.48), (103.18, 30.48), (103.18, 70.485), (95.885, 70.485), (95.885, 77.47),
             (19.05, 77.47)],
            [(BUS_X, 11.43), (BUS_X, 77.47)]],

}

# Conexiones fijas (pre-ruteadas) entre pads: (red, [ "REF.pad" | (x, y), ... ])
CHAINS = []
QK = {1: "Q0", 2: "Q1", 3: "Q2"}
for n, y0, u, ra, rb, q, rp, rg, ri, led in ROWS:
    CHAINS += [("I%dA" % n, [u + ".2", ra + ".1"]),
               ("I%dB" % n, [ra + ".2", rb + ".1"]),
               ("DRN%d" % n, [rb + ".2", u + ".1", q + ".3"]),
               ("G%d" % n, [rg + ".2", rp + ".1", q + ".2"]),
               ("GND", [q + ".1", ("BUS", 0)]),
               (QK[n], [ri + ".1", rg + ".1"]),
               ("LED%dA" % (n + 2), [ri + ".2", led + ".2"])]

CHAINS += [("+36V", [(2.54, 60.325), ("VX", 15.24), "JP3.1"]),
           ("+12V", ["U3.2", ("VX", 73.66), "SW2.1"]),
           ("RST", ["U2.15", (63.5, 35.56), "D5.1"]),
           ("Q3", ["U2.7", (60.96, 48.26), "D7.2"])]

REF_POS = {}
TEXTS = []
LINES = []
ORDER = None
FIRST = ["+36V", "+12V"]
LAST = ["GND"]
