"""LetreroLab AP-0.1 - placa CABEZAL (va arriba de la placa de POTENCIA, con separadores M3 de 25 mm).

Chip propio ATmega328P (DIP-28 en zócalo, 16 MHz) -> no depende de tarjetas Arduino ni ESP32.
- 4 salidas PWM + AUX hacia la placa de potencia (cable plano de 8 hilos, J1).
- Bluetooth: zócalo para módulo BLE HM-10 / JDY-23 / AT-09 (app web) o HC-05 (app de terminal).
- Reloj DS3231 (módulo enchufable) para horarios; LDR para encender de noche; receptor IR para control remoto.
- Botón MODO en la placa y conector para un botón externo; LED de estado.
- Conector de programación (adaptador USB-serie de 6 pines, tipo FTDI/CH340) con auto-reset.
- Regulador 7805: toma los 12 V de la placa de potencia.
PCB 90 x 80 mm, una cara, THT, 4 barrenos M3 alineados con la placa de potencia.

    python3 gen/make.py            (rutea; dentro del contenedor de KiCad 9)
"""
import os, sys, json, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "fuente-os-127v", "gen"))
import comun  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, ".."))
KI = os.path.join(ROOT, "kicad")
PROJECT = LIB = "AP01_Cabezal"
NS = uuid.UUID("7c3e2a99-5d4f-4e3b-a083-2f6b4c0d9e53")
ROOT_UUID = "8d4f3baa-6e50-4f4c-b194-3a7c5d1eaf64"
R, CP, CD = "Device:R", "Device:C_Polarized", "Device:C"
RV, RS = "R_Vertical_P5.08mm", "R_Vertical_P2.54mm"

U1 = {str(i): None for i in range(1, 29)}
U1.update({"1": "RST", "2": "RXD", "3": "TXD", "7": "V5", "8": "GND", "9": "X1", "10": "X2",
           "12": "PWM4", "15": "PWM3", "16": "PWM2", "17": "PWM1", "18": "AUX", "20": "V5", "22": "GND",
           "23": "LDR", "24": "MODO", "25": "IR", "26": "LED", "27": "SDA", "28": "SCL"})
C = [
    ("U1", "ATmega328P-PU", "MCU_Microchip_ATmega:ATmega328P-P", "DIP-28_W7.62mm", U1, (101.6, 76.2, 0),
     "Microcontrolador en zocalo DIP-28 (con bootloader de Arduino UNO)"),
    ("Y1", "16MHz", "Device:Resonator", "Resonador_3P_P2.54mm", {"1": "X2", "2": "GND", "3": "X1"}, (63.5, 101.6, 0),
     "Resonador ceramico 16 MHz de 3 patas (ya trae sus capacitores)"),
    ("C8", "100nF", CD, "C_Disc_P2.54mm", {"1": "GND", "2": "V5"}, (76.2, 50.8, 0), "Desacoplo VCC"),
    ("R1", "10k", R, RS, {"1": "RST", "2": "V5"}, (127.0, 50.8, 0), "Pull-up del reset"),
    ("C10", "100nF", CD, "C_Disc_P5.08mm", {"1": "RST", "2": "DTR"}, (137.16, 50.8, 0),
     "Auto-reset al programar (DTR del adaptador USB-serie)"),
    ("U2", "LM7805", "Regulator_Linear:L7805", "TO-220_7805", {"1": "V12", "2": "GND", "3": "V5"}, (35.56, 38.1, 0),
     "Regulador 12 V -> 5 V (consumo del cabezal ~40 mA)"),
    ("C1", "100nF", CD, "C_Disc_P2.54mm", {"1": "V12", "2": "GND"}, (25.4, 50.8, 0), "Entrada del 7805"),
    ("C2", "10uF 25V", CP, "CP_Radial_D5.0mm_P2.54mm", {"1": "V5", "2": "GND"}, (45.72, 50.8, 0), "Salida del 7805"),
    ("J1", "A POTENCIA", "Connector:Conn_01x08_Pin", "Pines_1x08_P2.54mm",
     {"1": "AUX", "2": "PWM1", "3": "PWM2", "4": "GND", "5": "GND", "6": "PWM3", "7": "PWM4", "8": "V12"},
     (25.4, 76.2, 0), "Cable plano de 8 hilos a J5 de la placa de potencia (pin 1 con pin 1)"),
    ("J3", "BLE", "Connector:Conn_01x06_Socket", "Zocalo_1x06_P2.54mm",
     {"1": None, "2": "BTRX", "3": "BTTX", "4": "GND", "5": "V5", "6": None}, (175.26, 60.96, 0),
     "Modulo Bluetooth BLE HM-10 / AT-09 / JDY-23 (STATE RXD TXD GND VCC EN). Para programar: quitarlo y usar el adaptador"),
    ("R2", "1k", R, RV, {"1": "TXD", "2": "BTRX"}, (162.56, 76.2, 0), "Divisor 5 V -> 3.3 V hacia RXD del modulo"),
    ("R3", "2k", R, RV, {"1": "BTRX", "2": "GND"}, (172.72, 76.2, 0), "Divisor 5 V -> 3.3 V hacia RXD del modulo"),
    ("R7", "1k", R, RV, {"1": "RXD", "2": "BTTX"}, (182.88, 76.2, 0), "Proteccion de la linea TXD del modulo"),
    ("J2", "DTR", "Connector:Conn_01x02_Pin", "Pines_1x02_P2.54mm", {"1": "DTR", "2": "GND"}, (152.4, 35.56, 0),
     "Pin DTR del adaptador USB-serie (programar: GND, TX y RX van a los pines del modulo BLE)"),
    ("J6", "RELOJ", "Connector:Conn_01x04_Pin", "Pines_1x04_P2.54mm",
     {"1": "SCL_C", "2": "SDA_C", "3": "V5", "4": "GND"}, (190.5, 86.36, 0),
     "Modulo reloj DS3231 (SCL SDA VCC GND) con pila, con cable Dupont"),
    ("R5", "220", R, RV, {"1": "SCL", "2": "SCL_C"}, (152.4, 86.36, 0), "Proteccion I2C"),
    ("R6", "220", R, RV, {"1": "SDA", "2": "SDA_C"}, (152.4, 101.6, 0), "Proteccion I2C"),
    ("J7", "IR", "Connector:Conn_01x03_Pin", "Pines_1x03_P2.54mm", {"1": "IR_C", "2": "GND", "3": "V5"},
     (190.5, 104.14, 0), "Receptor IR VS1838B / TSOP38238 (OUT GND VCC), con cable al frente"),
    ("R8", "220", R, RV, {"1": "IR", "2": "IR_C"}, (152.4, 116.84, 0), "Proteccion de la entrada IR"),
    ("J4", "MODO", "Connector:Conn_01x02_Pin", "Pines_1x02_P2.54mm", {"1": "MODO_C", "2": "GND"}, (190.5, 119.38, 0),
     "Boton MODO (pulsador normalmente abierto)"),
    ("R9", "220", R, RV, {"1": "MODO", "2": "MODO_C"}, (152.4, 132.08, 0), "Proteccion de la entrada del boton"),
    ("J8", "LUZ", "Connector:Conn_01x02_Pin", "Pines_1x02_P2.54mm", {"1": "LDR_C", "2": "GND"}, (190.5, 134.62, 0),
     "Fotoresistencia LDR (GL5528) entre A0 y GND: encender solo de noche"),
    ("R10", "1k", R, RV, {"1": "LDR", "2": "LDR_C"}, (152.4, 147.32, 0), "Proteccion de la entrada del LDR"),
    ("D1", "LED", "Device:LED", "LED_D3.0mm", {"1": "GND", "2": "LEDA"}, (99.06, 132.08, 0),
     "LED de estado (late lento = encendido, rapido = en pausa)"),
    ("R4", "1k", R, RV, {"1": "LED", "2": "LEDA"}, (83.82, 132.08, 0), "Limita la corriente del LED (~3 mA, ahorro)"),
]

NOTES = [
    (20.32, 15.24,
     "LETREROLAB AP-0.1 - CABEZAL: chip propio ATmega328P (16 MHz, bootloader de Arduino Uno/Nano).\n"
     "Pines: PWM1=D11 PWM2=D10 PWM3=D9 PWM4=D6 AUX=D12 | BLE en Serial D0/D1 (9600) | RTC SDA=A4 SCL=A5 |\n"
     "IR=A2 | MODO=A1 | LED=A3 | LDR=A0 (pull-up interno) | programacion por D0/D1 + DTR (quitar el modulo BLE)."),
]
TEXTS_SCH = [(20.32, 27.94, "Alimentacion 5 V"), (88.9, 27.94, "Microcontrolador"), (147.32, 27.94, "Modulos")]

W, H = 90.0, 80.0
HOLES = [(3.5, 3.5), (W - 3.5, 3.5), (3.5, H - 3.5), (W - 3.5, H - 3.5)]
X1, YT = 58.0, 34.0                      # pin 1 del ATmega (arriba a la derecha) y fila de arriba
YB, YC = YT + 7.62, YT + 3.81            # fila de abajo, centro (carril de 5 V por dentro del zocalo)
XV, XH, XG = 65.0, 72.0, 82.5            # columna de 5 V, conectores, columna de GND
POS = {
    "U1": (X1, YT, 270), "U2": (8.0, 12.0, 0), "C1": (8.0, 15.5, 0), "C2": (13.08, 20.0, 180),
    "Y1": (32.6, 28.0, 0), "C8": (40.22, 28.0, 0),
    "J1": (37.68, 50.0, 270),
    "R2": (62.46, 11.5, 0), "R7": (62.46, 15.5, 0), "R3": (76.0, 12.54, 0), "J3": (XH, 10.0, 0),
    "C10": (62.46, 27.0, 0), "R1": (62.46, 31.0, 0), "J2": (XH, 27.0, 0),
    "R5": (62.46, 43.0, 0), "R6": (62.46, 46.4, 0), "J6": (XH, 44.0, 0),
    "R4": (62.46, 55.5, 0), "D1": (78.54, 55.5, 180),
    "R8": (62.46, 59.0, 0), "J7": (XH, 59.0, 0),
    "R9": (62.46, 67.8, 0), "J4": (XH, 67.8, 0),
    "R10": (62.46, 74.0, 0), "J8": (XH, 74.0, 0),
}
P = lambda k: (X1 - (k - 1) * 2.54, YT) if k <= 14 else (X1 - 33.02 + (k - 15) * 2.54, YB)
TRACKS = {  # todo a mano (B.Cu), sin puentes
    "GND": [[(10.54, 12.0), (10.54, 23.0), (40.22, 23.0), P(8)], [(35.14, 28.0), (35.14, 23.0)],
            [(10.54, 12.0), (10.54, 5.0), (XG, 5.0), (XG, 12.54)],
            [(81.08, 12.54), (XG, 12.54), (XG, 78.4), (27.52, 78.4), (27.52, 50.0)],
            [P(22), (42.76, 78.4)], [(30.06, 50.0), (30.06, 78.4)],
            [(XH, 17.62), (XG, 17.62)], [(XH, 29.54), (XG, 29.54)], [(XH, 51.62), (XG, 51.62)],
            [(78.54, 55.5), (XG, 55.5)], [(XH, 61.54), (XG, 61.54)], [(XH, 70.34), (XG, 70.34)],
            [(XH, 76.54), (XG, 76.54)]],
    "V5": [[(13.08, 12.0), (13.08, 20.0)], [(13.08, 18.0), (42.76, 18.0), P(7)],
           [P(7), (42.76, YC), (XV, YC)], [P(20), (37.68, YC), (42.76, YC)],
           [(XV, 20.16), (XV, 64.08)], [(XH, 20.16), (XV, 20.16)], [(XH, 49.08), (XV, 49.08)],
           [(XH, 64.08), (XV, 64.08)]],
    "V12": [[(19.9, 50.0), (19.9, 54.0), (3.9, 54.0), (3.9, 12.0), (8.0, 12.0), (8.0, 15.5)]],
    "PWM4": [[P(12), (30.06, 30.9), (22.44, 30.9), (22.44, 50.0)]],
    "PWM3": [[P(15), (24.98, 50.0)]],
    "PWM2": [[P(16), (27.52, 43.5), (32.6, 48.58), (32.6, 50.0)]],
    "PWM1": [[P(17), (30.06, 43.5), (35.14, 48.58), (35.14, 50.0)]],
    "AUX": [[P(18), (32.6, 43.5), (37.68, 48.58), (37.68, 50.0)]],
    "X1": [[P(9), (37.68, 28.0)]],
    "X2": [[P(10), (35.14, 32.7), (32.6, 30.16), (32.6, 28.0)]],
    "TXD": [[P(3), (52.92, 11.5), (62.46, 11.5)]],
    "RXD": [[P(2), (55.46, 15.5), (62.46, 15.5)]],
    "BTRX": [[(67.54, 11.5), (XH, 12.54)], [(XH, 12.54), (76.0, 12.54)]],
    "BTTX": [[(67.54, 15.5), (XH, 15.08)]],
    "RST": [[P(1), (58.0, 31.0), (62.46, 31.0), (62.46, 27.0)]],
    "DTR": [[(67.54, 27.0), (XH, 27.0)]],
    "SCL": [[P(28), (58.0, 43.0), (62.46, 43.0)]], "SCL_C": [[(67.54, 43.0), (XH, 44.0)]],
    "SDA": [[P(27), (55.46, 46.4), (62.46, 46.4)]], "SDA_C": [[(67.54, 46.4), (XH, 46.54)]],
    "LED": [[P(26), (52.92, 55.5), (62.46, 55.5)]], "LEDA": [[(67.54, 55.5), (76.0, 55.5)]],
    "IR": [[P(25), (50.38, 59.0), (62.46, 59.0)]], "IR_C": [[(67.54, 59.0), (XH, 59.0)]],
    "MODO": [[P(24), (47.84, 67.8), (62.46, 67.8)]], "MODO_C": [[(67.54, 67.8), (XH, 67.8)]],
    "LDR": [[P(23), (45.3, 74.0), (62.46, 74.0)]], "LDR_C": [[(67.54, 74.0), (XH, 74.0)]],
}
JUMPERS = []
WIDTH = {"V12": 1.0, "V5": 0.8, "GND": 1.0}
RED = ()
TEXTS = [  # (texto, x, y, tamaño, ángulo, capa)
    ("LETREROLAB AP-0.1 CABEZAL", 15.0, 64.0, 1.0, 0, "F.SilkS"),
    ("AP-0.1 CABEZAL", 15.0, 71.5, 1.5, 0, "B.Cu"),
    ("A POTENCIA: 1 AUX ... 8 +12V", 28.8, 57.0, 0.8, 0, "F.SilkS"),
    ("BLE: 1 STATE 2 RXD 3 TXD 4 GND 5 VCC 6 EN", 62.0, 2.4, 0.7, 0, "F.SilkS"),
    ("DTR", 76.5, 27.0, 0.7, 0, "F.SilkS"), ("GND", 76.5, 29.54, 0.7, 0, "F.SilkS"),
    ("SCL", 76.5, 44.0, 0.7, 0, "F.SilkS"), ("SDA", 76.5, 46.54, 0.7, 0, "F.SilkS"),
    ("5V", 76.5, 49.08, 0.7, 0, "F.SilkS"), ("GND", 76.5, 51.62, 0.7, 0, "F.SilkS"),
    ("IR", 76.5, 59.0, 0.7, 0, "F.SilkS"), ("GND", 76.5, 61.54, 0.7, 0, "F.SilkS"),
    ("5V", 76.5, 64.08, 0.7, 0, "F.SilkS"),
    ("MODO", 77.0, 67.8, 0.7, 0, "F.SilkS"), ("GND", 76.5, 70.34, 0.7, 0, "F.SilkS"),
    ("LUZ", 76.5, 74.0, 0.7, 0, "F.SilkS"), ("GND", 76.5, 76.54, 0.7, 0, "F.SilkS"),
    ("RELOJ", 72.0, 41.2, 0.7, 0, "F.SilkS"),
]


def keepouts():
    return []


def dru():
    return ('(version 1)\n(rule "Pistas >= 0.8 mm"\n  (condition "A.Type == \'track\'")\n'
            '  (constraint track_width (min 0.8mm)))\n')


def main():
    os.makedirs(KI, exist_ok=True)
    comps, pos, tracks, wires = list(C), dict(POS), None, []
    rr = os.path.join(HERE, "route_result.json")
    widths = {**{n: 0.8 for c in C for n in c[4].values() if n}, **WIDTH}
    if "--manual" in sys.argv:
        json.dump({"failed": [], "tracks": {"/" + k: v for k, v in TRACKS.items()}, "jumpers": JUMPERS}, open(rr, "w"))
    elif "--noroute" not in sys.argv and "--from-result" not in sys.argv:
        comun.make_footprints(KI, LIB, sorted({c[3] for c in C}))
        b = comun.Board(W, H, LIB, KI, NS, C, POS, holes=HOLES)
        failed, tr, jumps = b.route(widths, clearance=float(os.environ.get("CLR", "0.55")),
                                    iters=int(os.environ.get("ITERS", "40")), pre=TRACKS, keepouts=keepouts(),
                                    jumpers=tuple(float(v) for v in os.environ.get("JUMPS", "").split(",") if v),
                                    jcost=float(os.environ.get("JCOST", "40")))
        print("FALLIDAS:", failed, "PUENTES:", jumps)
        json.dump({"failed": failed, "tracks": tr, "jumpers": jumps}, open(rr, "w"))
    if "--noroute" not in sys.argv:
        d = json.load(open(rr))
        comun.make_footprints(KI, LIB, sorted({c[3] for c in C}))
        b = comun.Board(W, H, LIB, KI, NS, C, POS, holes=HOLES)
        tracks, netsplit, wires = comun.split_jumper_nets(b.pads_geom(), d["tracks"],
                                                          [(n, tuple(a), tuple(c)) for n, a, c in d["jumpers"]], widths)
        comps = []
        for ref, val, sym, fp, pins, sp, func in C:
            comps.append((ref, val, sym, fp, {p: netsplit.get("%s.%s" % (ref, p), n) for p, n in pins.items()},
                          sp, func))
        for i, (wref, na, nb, pa, pb) in enumerate(wires):
            L = round(abs(pb[0] - pa[0]) + abs(pb[1] - pa[1]), 2)
            comps.append((wref, "PUENTE", "Jumper:Jumper_2_Open", "Puente_Abajo_P%.2fmm" % L,
                          {"1": na, "2": nb}, (40.64 + 30.48 * i, 132.08, 0),
                          "Puente de cable forrado del lado del cobre (sin agujero) que une %s con %s" % (na, nb)))
            rot = {(1, 0): 0, (-1, 0): 180, (0, 1): 270, (0, -1): 90}[
                (int(round((pb[0] - pa[0]) / L)), int(round((pb[1] - pa[1]) / L)))]
            pos[wref] = (pa[0], pa[1], rot)
            widths[nb] = widths.get(na, 0.8)
        comun.make_footprints(KI, LIB, sorted({c[3] for c in comps if not c[3].startswith("Puente_")}))
        for wref, na, nb, pa, pb in wires:
            L = abs(pb[0] - pa[0]) + abs(pb[1] - pa[1])
            fpn = "Puente_Abajo_P%.2fmm" % L
            open(os.path.join(KI, LIB + ".pretty", fpn + ".kicad_mod"), "w").write(
                comun.dump(comun.build_jumper_bottom(L, fpn)) + "\n")
    else:
        comun.make_footprints(KI, LIB, sorted({c[3] for c in C}))
    comun.make_schematic(KI, PROJECT, LIB, ROOT_UUID, NS, comps, NOTES, TEXTS_SCH,
                         "LetreroLab AP-0.1 - Cabezal: ATmega328P, Bluetooth, reloj, IR, LDR",
                         ["Bajo voltaje: se alimenta con 12 V de la placa de potencia",
                          "Chip propio programable con adaptador USB-serie"], paper="A3",
                         flags=[("V12", 20.32, 63.5), ("GND", 35.56, 63.5)] +
                         [(w[2], 137.16 + 15.24 * i, 63.5) for i, w in enumerate(wires) if w[1] in ("V12", "GND")],
                         company="PCB 90 x 80 mm, una cara, THT, 4 barrenos M3 (apila sobre la potencia)")
    b = comun.Board(W, H, LIB, KI, NS, comps, pos, holes=HOLES)
    if tracks:
        b.add_tracks(tracks, widths)
    b.texts(TEXTS)
    b.save(PROJECT)
    comun.make_project(KI, PROJECT, red_nets=RED, clr_red=0.5, clr=0.5, track=0.8)
    open(os.path.join(KI, PROJECT + ".kicad_dru"), "w").write(dru())
    print("ok", [w[0] for w in wires])


if __name__ == "__main__":
    main()
