"""Placa base LetreroLab 12 V: potencia de 3 canales + zócalo para Arduino Nano + zócalo para Bluetooth HC-05.

Bajo voltaje AISLADO (eliminador/fuente switching de 12 V regulada): se puede tocar sin peligro.
  - Entrada 12 V con fusible rearmable (PTC) y diodo contra polaridad invertida (hace saltar el PTC).
  - 3 canales con MOSFET IRLZ44N (nivel lógico, 5 V): luz fija, parpadeo, secuencia 1-2-3, desvanecido,
    o una tira RGB de 12 V (ánodo común) para cambio de color.
  - El Arduino Nano (enchufable) se alimenta por VIN con los 12 V; su 5 V alimenta al HC-05.
  - HC-05: TXD -> D2, RXD <- D3 por divisor 1k / 2.2k (3.3 V).  Botón MODO en D7.
PCB 50 x 60 mm, una cara; puentes (si hacen falta) con cable forrado del lado del cobre.

    python3 gen/make.py          (dentro del contenedor de KiCad 9)
"""
import os, sys, json, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "fuente-os-127v", "gen"))
import comun  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, ".."))
KI = os.path.join(ROOT, "kicad")
PROJECT = LIB = "Base12V"
NS = uuid.UUID("1c3e5a7b-9d1f-4b3d-8f5a-7c9e1b3d5f7a")
ROOT_UUID = "2d4f6b8c-0e2a-4c4e-9a6c-8e0a2c4e6a8c"
R, CP, CD, D = "Device:R", "Device:C_Polarized", "Device:C", "Device:D"
T2, T4 = "Connector:Screw_Terminal_01x02", "Connector:Screw_Terminal_01x04"
RV = "R_Vertical_P5.08mm"

NANO_PINS = {str(i): None for i in range(1, 31)}
NANO_PINS.update({"29": "GND", "30": "V12", "27": "V5", "24": "BTTX", "21": "BTRXL", "19": "BOTON",
                  "12": "D9", "13": "D10", "14": "D11"})
C = [
    ("J1", "ENTRADA 12V", T2, "Clema_2P_P5.08mm", {"1": "VINR", "2": "GND"}, (30.48, 40.64, 0),
     "Entrada 12 V DC de eliminador/fuente switching REGULADA (pin 1 = +, pin 2 = -)"),
    ("F1", "PTC 2.5A", "Device:Polyfuse", "PTC_Radial_P5.08mm", {"1": "V12", "2": "VINR"}, (53.34, 33.02, 90),
     "Fusible rearmable 2.5 A (MF-R250 o similar, 30 V)"),
    ("D1", "1N4007", D, "D_DO-41_Vertical_P5.08mm", {"1": "V12", "2": "GND"}, (55.88, 50.8, 90),
     "Proteccion: si se invierte la polaridad conduce y hace saltar el PTC"),
    ("C1", "220uF 25V", CP, "CP_Radial_D8.0mm_P3.81mm", {"1": "V12", "2": "GND"}, (68.58, 50.8, 0),
     "Filtro de entrada"),
    ("A1", "Arduino Nano", "MCU_Module:Arduino_Nano_v3.x", "Arduino_Nano_Zocalo", NANO_PINS, (129.54, 76.2, 0),
     "Arduino Nano (clon CH340) en 2 tiras hembra de 15 pines: es el 'cerebro' enchufable; VIN = 12 V"),
    ("J3", "HC-05", "Connector:Conn_01x06_Socket", "Zocalo_1x06_P2.54mm",
     {"1": None, "2": "V5", "3": "GND", "4": "BTTX", "5": "BTRX", "6": None}, (175.26, 60.96, 0),
     "Zocalo para modulo Bluetooth HC-05/HC-06 (EN, VCC, GND, TXD, RXD, STATE): se enchufa directo. Opcional"),
    ("R7", "1k", R, RV, {"1": "BTRX", "2": "BTRXL"}, (154.94, 55.88, 90),
     "Limita la corriente hacia RXD (3.3 V) del HC-05 desde A2 (5 V)"),
    ("J4", "MODO", "Connector:Conn_01x02_Pin", "Cables_2P_P5.08mm", {"1": "BOTON", "2": "GND"}, (175.26, 86.36, 0),
     "Boton MODO (pulsador normalmente abierto) entre A0 y GND; pull-up interno del Nano"),
    ("J2", "SALIDAS", T4, "Clema_4P_P5.08mm", {"1": "V12", "2": "CH1", "3": "CH2", "4": "CH3"}, (309.88, 101.6, 0),
     "Salidas: 1 = +12 V comun, 2/3/4 = negativo conmutado de los canales 1/2/3 (max 2 A c/u)"),
]
for n, d in ((1, "D9"), (2, "D10"), (3, "D11")):
    x = 170.18 + (n - 1) * 45.72
    C += [
        ("R%d" % n, "220", R, RV, {"1": "G%d" % n, "2": d}, (x - 20.32, 121.92, 270),
         "Resistencia de compuerta canal %d" % n),
        ("R%d" % (n + 3), "10k", R, RV, {"1": "G%d" % n, "2": "GND"}, (x - 6.35, 137.16, 0),
         "Mantiene apagado el canal %d si no hay Nano" % n),
        ("Q%d" % n, "IRLZ44N", "Transistor_FET:IRLZ44N", "TO-220_MOSFET", {"1": "G%d" % n, "2": "CH%d" % n,
                                                                                  "3": "GND"},
         (x, 121.92, 0), "MOSFET canal %d (nivel logico, 47 A / 55 V; aqui hasta 2 A sin disipador)" % n),
    ]

NOTES = [
    (20.32, 20.32,
     "PLACA BASE LETREROLAB 12 V - 3 CANALES + ARDUINO NANO + BLUETOOTH (OPCIONAL)\n"
     "Bajo voltaje aislado: usar SIEMPRE un eliminador/fuente switching de 12 V regulada (nunca 127 V en esta placa)."),
    (20.32, 140.97,
     "Cada canal: +12 V comun (J2-1) -> tira -> J2-2/3/4. Tira LED 12 V directa, o LED de 5 mm en grupos con resistencia:\n"
     "  verde/blanco/azul (3 V): 3 LED + 220 ohm = 13 mA     ambar/amarillo/rojo (2 V): 5 LED + 100 ohm = 16 mA\n"
     "Tira RGB 12 V (anodo comun): + a J2-1, R/G/B a CH1/CH2/CH3: cambio de color por PWM (D9/D10/D11).\n"
     "Bluetooth: HC-05 TXD -> A5, RXD <- 1k <- A2 (SoftwareSerial, 9600). Boton MODO en A0.\n"
     "Consumo: eliminador de 12 V 1 A basta para LED de 5 mm; 2-3 A para tiras."),
]
TEXTS_SCH = [(25.4, 30.48, "Entrada 12 V"), (101.6, 30.48, "Cerebro enchufable (Arduino Nano) y Bluetooth"),
             (160.02, 101.6, "Canales de potencia")]

W, H = 50.0, 60.0
YT, YB = 12.5, 27.74            # filas del Nano (arriba: VIN..D13, abajo: D1..D12)
YQ = 43.45                      # patas de los MOSFET
YRG, YRP, YBUS = YQ - 4.92, YQ + 3.5, 35.99   # R de compuerta (pad 1), R a GND, bus de GND
YL = (29.9, 31.25, 32.6)        # carriles D9, D10, D11
XG = (4.0, 14.8, 25.6)          # compuerta de Q1, Q2, Q3
POS = {
    "J3": (12.52, 5.0, 90), "R7": (25.22, 8.75, 0), "J4": (35.38, 5.5, 90),
    "A1": (7.44, YB, 90),
    "J2": (2.5, 54.5, 0), "J1": (40.92, 54.5, 0),
    "F1": (30.76, 54.5, 0), "C1": (36.0, 44.5, 0), "D1": (45.0, 46.0, 90),
}
for i, xg in enumerate(XG):
    POS["Q%d" % (i + 1)] = (xg, YQ, 0)
    POS["R%d" % (i + 1)] = (xg, YRG, 90)
    POS["R%d" % (i + 4)] = (xg, YRP, 0)
YR2 = YRG - 5.08
TRACKS = {  # todo a mano, del lado del cobre (B.Cu), sin puentes
    "V12": [[(30.76, 54.5), (30.76, 58.4), (1.6, 58.4), (1.6, 8.0), (7.44, 8.0), (7.44, YT)],
            [(30.76, 54.5), (33.6, 51.66), (33.6, 47.2), (43.8, 47.2), (45.0, 46.0)],
            [(36.0, 44.5), (36.0, 47.2)]],
    "VINR": [[(35.84, 54.5), (40.92, 54.5)]],
    "GND": [[(17.6, 5.0), (17.6, 1.6), (9.98, 1.6), (9.98, YT)],
            [(17.6, 1.6), (48.4, 1.6), (48.4, 52.0), (46.0, 54.4), (46.0, 54.5)],
            [(40.46, 5.5), (40.46, 1.6)],
            [(9.08, YRP), (9.08, YBUS), (48.4, YBUS)],
            [(19.88, YRP), (19.88, YBUS)], [(30.68, YRP), (30.68, YBUS)],
            [(39.81, 44.5), (39.81, YBUS)], [(45.0, 40.92), (45.0, YBUS)]],
    "G1": [[(4.0, YRG), (4.0, YRP)]], "G2": [[(14.8, YRG), (14.8, YRP)]], "G3": [[(25.6, YRG), (25.6, YRP)]],
    "D9": [[(4.0, YR2), (4.0, YL[0]), (35.38, YL[0]), (35.38, YB)]],
    "D10": [[(14.8, YR2), (14.8, YL[1]), (37.92, YL[1]), (37.92, YB)]],
    "D11": [[(25.6, YR2), (25.6, YL[2]), (40.46, YL[2]), (40.46, YB)]],
    "CH1": [[(6.54, YQ), (6.54, 49.3), (7.58, 50.34), (7.58, 54.5)]],
    "CH2": [[(17.34, YQ), (17.34, 48.8), (12.66, 53.48), (12.66, 54.5)]],
    "CH3": [[(28.14, YQ), (28.14, 49.7), (21.4, 49.7), (17.74, 53.36), (17.74, 54.5)]],
    "V5": [[(15.06, 5.0), (15.06, YT)]],
    "BTTX": [[(20.14, 5.0), (20.14, 7.0), (22.68, 9.54), (22.68, YT)]],
    "BTRX": [[(22.68, 5.0), (22.68, 6.6), (24.83, 8.75), (25.22, 8.75)]],
    "BTRXL": [[(30.3, 8.75), (30.3, YT)]],
    "BOTON": [[(35.38, 5.5), (35.38, YT)]],
}
WIDTH = {"V12": 1.0, **{n: 1.5 for n in ("VINR", "GND", "CH1", "CH2", "CH3")}}
RED = ()
TEXTS = [  # (texto, x, y, tamaño, ángulo, capa)
    ("+12", 2.5, 51.2, 0.8, 0, "F.SilkS"), ("CH1", 7.58, 51.2, 0.8, 0, "F.SilkS"),
    ("CH2", 12.66, 51.2, 0.8, 0, "F.SilkS"), ("CH3", 17.74, 51.2, 0.8, 0, "F.SilkS"),
    ("+12V", 40.92, 51.4, 0.8, 0, "F.SilkS"), ("GND", 46.0, 51.4, 0.8, 0, "F.SilkS"),
    ("HC-05", 6.2, 4.6, 0.8, 0, "F.SilkS"), ("EN", 12.52, 2.3, 0.8, 0, "F.SilkS"), ("STATE", 25.22, 2.3, 0.8, 0, "F.SilkS"), ("MODO", 37.9, 8.8, 0.8, 0, "F.SilkS"),
    ("LETREROLAB BASE 12V v1", 25.0, 23.5, 1.0, 0, "F.SilkS"),
    ("LETREROLAB 12V", 25.0, 19.0, 1.6, 0, "B.Cu"),
]
def main():
    os.makedirs(KI, exist_ok=True)
    comps, pos, tracks, wires = list(C), dict(POS), None, []
    rr = os.path.join(HERE, "route_result.json")
    widths = {**{n: 0.8 for c in C for n in c[4].values() if n}, **WIDTH}
    if "--manual" in sys.argv:
        json.dump({"failed": [], "tracks": {"/" + k: v for k, v in TRACKS.items()}, "jumpers": []}, open(rr, "w"))
    elif "--noroute" not in sys.argv and "--from-result" not in sys.argv:
        comun.make_footprints(KI, LIB, sorted({c[3] for c in C}))
        b = comun.Board(W, H, LIB, KI, NS, C, POS)
        failed, tr, jumps = b.route(widths, clearance=float(os.environ.get("CLR", "0.55")), iters=int(os.environ.get("ITERS", "40")), pre=PRE,
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
            comps.append((wref, "PUENTE", "Jumper:Jumper_2_Bridged", "Puente_Abajo_P%.2fmm" % L,
                          {"1": na, "2": nb}, (40.64 + 30.48 * i, 127.0, 0),
                          "Puente de cable forrado del lado del cobre (sin agujero) que une %s con %s" % (na, nb)))
            rot = {(1, 0): 0, (-1, 0): 180, (0, 1): 270, (0, -1): 90}[
                (int(round((pb[0] - pa[0]) / L)), int(round((pb[1] - pa[1]) / L)))]
            pos[wref] = (pa[0], pa[1], rot)
            widths[nb] = widths.get(na, 0.8)
        names = sorted({c[3] for c in comps if not c[3].startswith("Puente_")})
        comun.make_footprints(KI, LIB, names)
        for wref, na, nb, pa, pb in wires:
            L = abs(pb[0] - pa[0]) + abs(pb[1] - pa[1])
            fpn = "Puente_Abajo_P%.2fmm" % L
            open(os.path.join(KI, LIB + ".pretty", fpn + ".kicad_mod"), "w").write(
                comun.dump(comun.build_jumper_bottom(L, fpn)) + "\n")
    else:
        comun.make_footprints(KI, LIB, sorted({c[3] for c in C}))
    comun.make_schematic(KI, PROJECT, LIB, ROOT_UUID, NS, comps, NOTES, TEXTS_SCH,
                         "Placa base LetreroLab 12 V: 3 canales MOSFET + Arduino Nano + Bluetooth",
                         ["Bajo voltaje aislado: eliminador/fuente switching de 12 V regulada",
                          "Canales: tira 12 V, LED 5 mm con resistencia o tira RGB anodo comun"], paper="A3",
                         flags=[("V12", 45.72, 71.12), ("GND", 60.96, 71.12)] +
                         [(w[2], 106.68 + 15.24 * i, 22.86) for i, w in enumerate(wires) if w[1] in ("V12", "GND")],
                         company="PCB 50 x 60 mm, una cara, THT, transferencia de toner")
    b = comun.Board(W, H, LIB, KI, NS, comps, pos)
    if tracks:
        b.add_tracks(tracks, widths)
    b.texts(TEXTS)
    b.save(PROJECT)
    comun.make_project(KI, PROJECT, red_nets=RED, clr_red=0.6, clr=0.5, track=0.8)
    print("ok", [w[0] for w in wires])


if __name__ == "__main__":
    main()
