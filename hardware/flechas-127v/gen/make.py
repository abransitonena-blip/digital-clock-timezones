"""Secuenciador de 3 flechas (3 x 9 LED verdes) alimentado directo de 127 VCA (tipo Radox, NO aislado).

NE555 (reloj) + CD4017 (1 -> 2 -> 3) + 3 SCR MCR100-6. Dos fuentes capacitivas con puente 2W10:
  - lógica: 474J -> 2W10 -> zener 12 V + 220 uF
  - flechas: 224J -> 2W10 -> ánodo común de las 3 flechas (~8 mA por flecha, sin filtrar: el SCR
    se apaga en cada cruce por cero y el 4017 elige la siguiente flecha)
PCB de 50 x 50 mm, una cara; se rutea con el ruteador de una cara del proyecto de 36 V.

    python3 gen/make.py          (dentro del contenedor de KiCad 9)
"""
import os, sys, json, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "fuente-os-127v", "gen"))
import comun  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, ".."))
KI = os.path.join(ROOT, "kicad")
PROJECT = LIB = "Flechas127"
NS = uuid.UUID("7e2a9c1b-4d3f-4b6a-8e5c-1a2b3c4d5e6f")
ROOT_UUID = "3c5e7a9b-2d4f-4e6a-9c8b-0a1b2c3d4e5f"

R, CP, CD, D, DZ = "Device:R", "Device:C_Polarized", "Device:C", "Device:D", "Device:D_Zener"
SCR = "Triac_Thyristor:BT169D"
T2, T4 = "Connector:Screw_Terminal_01x02", "Connector:Screw_Terminal_01x04"
RV, RH, R1W = "R_Vertical_P5.08mm", "R_Axial_P10.16mm", "R_1W_Vertical_P7.62mm"

C = [
    # ---- entrada y fuentes capacitivas ----
    ("J1", "127 VCA", T2, "Clema_2P_P5.08mm", {"1": "N", "2": "L"}, (20.32, 45.72, 180),
     "Entrada 127 VCA (pin 1 = N neutro, pin 2 = L fase; se pueden intercambiar). Del mismo cable que la placa Radox"),
    ("R3", "1M 1/2W", R, RV, {"1": "L", "2": "N"}, (20.32, 66.04, 0),
     "Descarga los capacitores al desenchufar (entre L y N)"),
    ("C1", "474J 400V", CD, "C_Poliester_P10-15mm", {"1": "L", "2": "X1"}, (40.64, 38.1, 90),
     "Poliester 0.47 uF 400 V (paso 10 o 15 mm): fuente de la logica, ~19 mA"),
    ("R1", "220R 1W fusible", R, R1W, {"1": "X1", "2": "ACL"}, (58.42, 38.1, 90),
     "Resistencia fusible de la fuente logica (limita el pico al enchufar)"),
    ("BR1", "2W10", "Device:D_Bridge_+-AA", "Puente_2W10", {"1": "V12", "2": "GND", "3": "ACL", "4": "N"},
     (83.82, 45.72, 0), "Puente 2W10 de la fuente logica"),
    ("DZ1", "1N4742A 12V 1W", DZ, "D_DO-41_P10.16mm", {"1": "V12", "2": "GND"}, (116.84, 43.18, 270),
     "Zener 12 V: fija el voltaje de la logica y absorbe la corriente sobrante"),
    ("C3", "220uF 25V", CP, "CP_Radial_D8.0mm_P3.81mm", {"1": "V12", "2": "GND"}, (134.62, 43.18, 0),
     "Filtro de 12 V"),
    ("C2", "224J 400V", CD, "C_Poliester_P10-15mm", {"1": "L", "2": "X2"}, (40.64, 60.96, 90),
     "Poliester 0.22 uF 400 V (paso 10 o 15 mm): corriente de las flechas, ~8 mA"),
    ("R2", "220R 1W fusible", R, R1W, {"1": "X2", "2": "ACF"}, (58.42, 60.96, 90),
     "Resistencia fusible de la fuente de flechas"),
    ("BR2", "2W10", "Device:D_Bridge_+-AA", "Puente_2W10", {"1": "VF", "2": "GND", "3": "N", "4": "ACF"},
     (83.82, 68.58, 0), "Puente 2W10 de las flechas (+ = anodo comun, sin filtrar)"),
    # ---- reloj NE555 ----
    ("U1", "NE555P", "Timer:NE555P", "DIP-8_W7.62mm",
     {"1": "GND", "2": "TIM", "3": "CLK", "4": "V12", "5": None, "6": "TIM", "7": None, "8": "V12"},
     (40.64, 99.06, 0), "Reloj (astable con la salida): T = 1.4 x R6 x C5 = 0.66 s por flecha"),
    ("R6", "47k", R, RV, {"1": "CLK", "2": "TIM"}, (17.78, 104.14, 90),
     "Salida -> capacitor de tiempo (velocidad: 33k = 0.46 s, 47k = 0.66 s, 68k = 0.95 s, 100k = 1.4 s)"),
    ("C5", "10uF 25V", CP, "CP_Radial_D5.0mm_P2.54mm", {"1": "TIM", "2": "GND"}, (27.94, 116.84, 0),
     "Capacitor de tiempo del 555"),
    # ---- contador CD4017 ----
    ("U2", "CD4017BE", "4xxx:4017", "DIP-16_W7.62mm",
     {"16": "V12", "8": "GND", "13": "RST", "14": "CLK", "15": "RST", "3": "Q0", "2": "Q1", "4": "Q2", "7": "RST",
      "1": None, "5": None, "6": None, "9": None, "10": None, "11": None, "12": None},
     (86.36, 104.14, 0), "Contador: Q0-Q2 = flechas 1-3, Q3 -> RESET (3 pasos). INH (13) va a RESET: siempre en bajo salvo el pulso de reset"),
]
# Canales (de abajo hacia arriba en la PCB): Q1 -> flecha 2, Q0 -> flecha 1, Q2 -> flecha 3
for n, q, x in ((1, "Q0", 124.46), (2, "Q1", 149.86), (3, "Q2", 175.26)):
    C += [
        ("R%d" % (7 + n), "4.7k", R, RV, {"1": q, "2": "G%d" % n}, (x - 10.16, 88.9, 90),
         "Resistencia de compuerta del SCR %d (2.4 mA)" % n),
        ("SCR%d" % n, "MCR100-6", SCR, "TO-92_SCR", {"1": "GND", "2": "G%d" % n, "3": "F%dN" % n}, (x, 96.52, 0),
         "SCR de la flecha %d (0.8 A 400 V; tambien PCR606J). Patas: K G A" % n),
    ]
C.append(("J2", "FLECHAS", T4, "Cables_4P_P5.08mm", {"1": "VF", "2": "F3N", "3": "F1N", "4": "F2N"},
          (218.44, 96.52, 0),
          "Cables a las flechas: 1 = + comun (anodos), 2 = F3-, 3 = F1-, 4 = F2- (catodos). "
          "Rotulado en la placa como +, F3, F1, F2"))

NOTES = [
    (20.32, 20.32,
     "SECUENCIADOR DE 3 FLECHAS (9 LED VERDES c/u) - 127 VCA - NO AISLADO (mismo principio que la placa Radox)\n"
     "PELIGRO: TODO el circuito (placa, LED, 555, 4017) queda a potencial de red. Desenchufar antes de tocar."),
    (20.32, 135.89,
     "Logica: I = 240 x 0.47uF x (180 - 13) = 19 mA; consumo 555 + 4017 + compuerta ~9 mA; el zener absorbe el resto (< 0.25 W).\n"
     "Flechas: I = 240 x 0.22uF x (180 - 27) = 8.1 mA por flecha (9 LED verdes x 3.0 V = 27 V). Siempre hay una flecha encendida.\n"
     "Linea de flechas SIN capacitor de filtro: el SCR se apaga en cada cruce por cero (120 veces/s) y el 4017 decide cual vuelve a encender.\n"
     "Velocidad: T = 1.4 x R6 x 10uF (R6 de la salida pin 3 a pines 2-6):  33k -> 0.46 s   47k -> 0.66 s   68k -> 0.95 s   100k -> 1.4 s"),
]
TEXTS_SCH = [(38.1, 30.48, "Fuentes capacitivas"), (15.24, 83.82, "Reloj NE555"),
             (78.74, 83.82, "Contador CD4017"), (114.3, 83.82, "SCR de las flechas y salida")]

# ---------------------------------------------------------------- PCB
W, H = 50.0, 60.0
POS = {
    "J1": (5.8, 5.2, 270),
    "C1": (14.2, 4.8, 0), "C2": (14.2, 12.4, 0),
    "R1": (34.0, 4.8, 270), "R2": (34.0, 16.5, 270),
    "BR1": (40.3, 4.8, 0), "BR2": (45.88, 21.5, 180),
    "R3": (5.8, 15.2, 270),
    "DZ1": (19.2, 19.62, 0),
    "C3": (10.5, 25.5, 0),
    "U1": (11.62, 40.0, 180),
    "R6": (3.0, 50.5, 0),
    "C5": (11.5, 50.5, 0),
    "U2": (26.5, 56.0, 180),
    # resistencias de compuerta acostadas (el bus de GND pasa entre sus patas) y SCR en columna
    "R10": (31.5, 36.36, 0), "SCR3": (41.5, 38.9, 90),
    "R8": (31.5, 45.06, 0), "SCR1": (41.5, 47.6, 90),
    "R9": (31.5, 53.76, 0), "SCR2": (41.5, 56.3, 90),
    "J2": (45.88, 30.0, 0),
}
# Parte de 127 V trazada a mano (topología sin cruces; V12 y GND pasan por debajo de C2 y entre las patas de R1/R2)
PRE = {
    "N": [[(5.8, 5.2), (5.8, 1.6), (48.4, 1.6), (48.4, 16.42), (45.88, 16.42)], [(45.38, 1.6), (45.38, 4.8)],
          [(5.8, 5.2), (1.6, 5.2), (1.6, 20.28), (5.8, 20.28)]],
    "L": [[(5.8, 10.28), (12.3, 10.28), (14.2, 12.4), (14.2, 4.8)], [(5.8, 10.28), (5.8, 15.2)]],
    "X1": [[(24.2, 4.8), (29.2, 4.8), (34.0, 4.8)]],
    "X2": [[(24.2, 12.4), (29.2, 12.4), (31.3, 14.5), (34.0, 16.5)]],
    "ACL": [[(34.0, 12.42), (37.8, 12.42), (40.3, 9.88)]],
    "ACF": [[(34.0, 24.12), (40.8, 24.12), (40.8, 21.5)]],
    "V12": [[(40.3, 4.8), (36.5, 8.6), (19.2, 8.6), (19.2, 19.62)]],
    "GND": [[(45.38, 9.88), (42.7, 12.56), (40.8, 14.46), (40.8, 16.42), (37.6, 19.62), (29.36, 19.62)]],
    "VF": [[(45.88, 21.5), (45.88, 30.0)]],
}
WIDTH = {n: 1.2 for n in ("L", "N", "X1", "X2", "ACL", "ACF", "VF")}
TEXTS = [  # (texto, x, y, tamaño, ángulo, capa)
    ("N", 9.9, 5.2, 1.2, 0, "F.SilkS"), ("L", 9.9, 10.3, 1.2, 0, "F.SilkS"),
    ("127VCA", 5.8, 1.3, 0.8, 0, "F.SilkS"),
    ("+", 49.0, 30.0, 1.4, 0, "F.SilkS"), ("F3", 49.0, 35.08, 1.0, 90, "F.SilkS"),
    ("F1", 49.0, 40.16, 1.0, 90, "F.SilkS"), ("F2", 49.0, 45.24, 1.0, 90, "F.SilkS"),
    ("FLECHAS", 45.9, 48.8, 0.9, 0, "F.SilkS"),
    ("W1 W2: CABLE FORRADO", 36.0, 58.4, 0.9, 0, "F.SilkS"),
    ("PELIGRO 127V - NO TOCAR ENCHUFADA", 31.0, 27.3, 0.8, 0, "F.SilkS"),
    ("R6 velocidad: 47k=0.66s", 12.5, 58.6, 0.7, 0, "F.SilkS"),
    ("FLECHAS 127V v1", 13.0, 58.5, 1.2, 0, "B.Cu"),
]
RED = ("L", "N", "X1", "X2", "ACL", "ACF")


def main():
    os.makedirs(KI, exist_ok=True)
    comps, pos, tracks, wires = list(C), dict(POS), None, []
    rr = os.path.join(HERE, "route_result.json")
    widths = {**{n: 0.8 for c in C for n in c[4].values() if n}, **WIDTH}
    if "--noroute" not in sys.argv and "--from-result" not in sys.argv:
        comun.make_footprints(KI, LIB, sorted({c[3] for c in C}))
        b = comun.Board(W, H, LIB, KI, NS, C, POS)
        failed, tr, jumps = b.route(widths, clearance=0.6, iters=int(os.environ.get("ITERS", "40")), pre=PRE,
                                    jumpers=tuple(float(v) for v in os.environ.get("JUMPS", "").split(",") if v),
                                    jcost=float(os.environ.get("JCOST", "40")))
        print("FALLIDAS:", failed, "PUENTES:", jumps)
        json.dump({"failed": failed, "tracks": tr, "jumpers": jumps}, open(rr, "w"))
    if "--noroute" not in sys.argv:
        d = json.load(open(rr))
        comun.make_footprints(KI, LIB, sorted({c[3] for c in C}))
        b = comun.Board(W, H, LIB, KI, NS, C, POS)
        tracks, netsplit, wires = comun.split_jumper_nets(b.pads_geom(), d["tracks"],
                                                          [(n, tuple(a), tuple(c)) for n, a, c in d["jumpers"]], widths)
        comps = []
        for ref, val, sym, fp, pins, sp, func in C:
            comps.append((ref, val, sym, fp, {p: netsplit.get("%s.%s" % (ref, p), n) for p, n in pins.items()},
                          sp, func))
        for i, (wref, na, nb, pa, pb) in enumerate(wires):
            L = round(abs(pb[0] - pa[0]) + abs(pb[1] - pa[1]), 2)
            comps.append((wref, "PUENTE", "Jumper:Jumper_2_Bridged", "Puente_Alambre_P%.2fmm" % L,
                          {"1": na, "2": nb}, (40.64 + 30.48 * i, 127.0, 0),
                          "Puente de alambre (lado componentes) que une %s con %s" % (na, nb)))
            rot = {(1, 0): 0, (-1, 0): 180, (0, 1): 270, (0, -1): 90}[
                (int(round((pb[0] - pa[0]) / L)), int(round((pb[1] - pa[1]) / L)))]
            pos[wref] = (pa[0], pa[1], rot)
            widths[nb] = widths.get(na, 0.8)
        names = sorted({c[3] for c in comps if not c[3].startswith("Puente_")})
        comun.make_footprints(KI, LIB, names)
        for wref, na, nb, pa, pb in wires:
            L = abs(pb[0] - pa[0]) + abs(pb[1] - pa[1])
            fpn = "Puente_Alambre_P%.2fmm" % L
            open(os.path.join(KI, LIB + ".pretty", fpn + ".kicad_mod"), "w").write(
                comun.dump(comun.fplib.build_jumper(L, fpn)) + "\n")
    else:
        comun.make_footprints(KI, LIB, sorted({c[3] for c in C}))
    comun.make_schematic(KI, PROJECT, LIB, ROOT_UUID, NS, comps, NOTES, TEXTS_SCH,
                         "Secuenciador de 3 flechas 127 VCA (NE555 + CD4017 + SCR)",
                         ["NO AISLADO: todo el circuito queda a potencial de red (igual que la placa Radox)",
                          "Flechas: 9 LED verdes c/u, ~8 mA con 224J; paso 0.66 s (R6 = 47k)"], paper="A3",
                         flags=[("V12", 147.32, 30.48), ("GND", 162.56, 30.48)] +
                         [(w[2], 177.8 + 15.24 * i, 30.48) for i, w in enumerate(wires) if w[1] in ("V12", "GND")],
                         company="PCB 50 x 60 mm, una cara, THT, transferencia de toner, 2 puentes de alambre")
    b = comun.Board(W, H, LIB, KI, NS, comps, pos)
    if tracks:
        b.add_tracks(tracks, widths)
    b.texts(TEXTS)
    b.save(PROJECT)
    comun.make_project(KI, PROJECT, red_nets=RED, clr_red=1.2, clr=0.6, track=0.8)
    print("ok", [w[0] for w in wires])


if __name__ == "__main__":
    main()
