"""LetreroLab AP-0.1 - placa de POTENCIA (va abajo; encima se atornilla la placa CABEZAL).

- Entrada 100-240 VCA -> fusible T2A -> varistor -> fuente conmutada encapsulada HLK-10M12 (12 V 10 W, aislada y
  certificada por el fabricante). Sin diodos en serie: la fuente alimenta directo el bus de 12 V (menos perdidas).
- 4 canales PWM con MOSFET IRLZ44N (tiras LED 12 V, RGB/RGBW, letreros de LED de 5 mm con resistencia).
- Relevador de 10 A con contacto seco (J4): enciende/apaga focos normales de 127/240 V (o lo que sea) desde la app.
- J5: 8 pines hacia la placa CABEZAL (12 V, GND, PWM1-4, AUX).
PCB 90 x 80 mm, una cara, THT, 4 barrenos M3. Zona de 127 V separada >= 5 mm de la zona de 12 V.

    python3 gen/make.py --manual      (dentro del contenedor de KiCad 9)
"""
import os, sys, json, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "fuente-os-127v", "gen"))
import comun  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, ".."))
KI = os.path.join(ROOT, "kicad")
PROJECT = LIB = "AP01_Potencia"
NS = uuid.UUID("5a1c0e77-3b2d-4c19-9e61-0d4f2a8b7c31")
ROOT_UUID = "6b2d1f88-4c3e-4d2a-8f72-1e5a3b9c8d42"
R, CP, D = "Device:R", "Device:C_Polarized", "Device:D"
T2, T3 = "Connector:Screw_Terminal_01x02", "Connector:Screw_Terminal_01x03"
RV = "R_Vertical_P5.08mm"

C = [
    ("J1", "ENTRADA CA", T2, "Clema_2P_P5.08mm", {"1": "L", "2": "N"}, (30.48, 30.48, 0),
     "Entrada 100-240 VCA (L = fase, N = neutro)"),
    ("F1", "T2A 250V", "Device:Fuse", "Fusible_TR5_P5.08mm", {"1": "L", "2": "LF"}, (45.72, 25.4, 90),
     "Fusible lento 2 A (TR5) para la fuente"),
    ("RV1", "07D471K", "Device:Varistor", "Varistor_D7mm_P5mm", {"1": "N", "2": "LF"}, (55.88, 35.56, 0),
     "Varistor contra picos de la red (471 = sirve para 127 y 240 V)"),
    ("PS1", "HLK-10M12", "Converter_ACDC:HLK-10M12", "HLK-10Mxx", {"1": "LF", "2": "N", "3": "GND", "4": "V12"},
     (81.28, 30.48, 0), "Fuente conmutada encapsulada 12 V 10 W (0.83 A), aislada; consumo en espera < 0.1 W"),
    ("C1", "100uF 25V", CP, "CP_Radial_D5.0mm_P2.54mm", {"1": "V12", "2": "GND"}, (124.46, 25.4, 0),
     "Filtro del bus de 12 V (105 C, larga vida)"),
    ("K1", "SRD-12VDC-SL-C", "Relay:SANYOU_SRD_Form_C", "Rele_SRD_FormC",
     {"1": "COM", "2": "RLY", "3": "NO", "4": None, "5": "V12"}, (40.64, 106.68, 0),
     "Relevador 12 V, contactos 10 A 250 VCA"),
    ("J4", "CONTACTO", T2, "Clema_2P_P5.08mm", {"1": "NO", "2": "COM"}, (20.32, 106.68, 0),
     "Contacto seco del relevador (COM / NA): interrumpe la fase de focos normales, max 10 A"),
    ("D3", "1N4148", D, "D_DO-35_Vertical_P5.08mm", {"1": "V12", "2": "RLY"}, (58.42, 106.68, 90),
     "Diodo de rueda libre de la bobina"),
    ("Q5", "2N7000", "Transistor_FET:2N7000", "TO-92_2N7000", {"1": "GND", "2": "G5", "3": "RLY"},
     (71.12, 106.68, 0), "Activa la bobina del relevador"),
    ("R9", "220", R, RV, {"1": "G5", "2": "AUX"}, (63.5, 121.92, 90), "Resistencia de compuerta del relevador"),
    ("R10", "10k", R, "R_Vertical_P2.54mm", {"1": "G5", "2": "GND"}, (76.2, 121.92, 0), "Relevador apagado si no hay cabezal"),
    ("J3", "SALIDAS", "Connector:Screw_Terminal_01x05", "Clema_5P_P5.08mm",
     {"1": "V12", "2": "CH1", "3": "CH2", "4": "CH3", "5": "CH4"}, (299.72, 101.6, 0),
     "Salidas: 1 = +12 V comun, 2-5 = negativo conmutado CH1..CH4 (max 2 A c/u, 0.8 A total con la fuente interna)"),
    ("J5", "CABEZAL", "Connector:Conn_01x08_Pin", "Pines_1x08_P2.54mm",
     {"1": "AUX", "2": "PWM1", "3": "PWM2", "4": "GND", "5": "GND", "6": "PWM3", "7": "PWM4", "8": "V12"},
     (152.4, 50.8, 0), "Conector hacia la placa CABEZAL (cable plano de 8 hilos)"),
]
for n in range(1, 5):
    x = 165.1 + (n - 1) * 30.48
    C += [
        ("R%d" % n, "220", R, RV, {"1": "G%d" % n, "2": "PWM%d" % n}, (x - 20.32, 101.6, 270),
         "Resistencia de compuerta canal %d" % n),
        ("R%d" % (n + 4), "10k", R, RV, {"1": "G%d" % n, "2": "GND"}, (x - 6.35, 116.84, 0),
         "Mantiene apagado el canal %d sin cabezal" % n),
        ("Q%d" % n, "IRLZ44N", "Transistor_FET:IRLZ44N", "TO-220_MOSFET",
         {"1": "G%d" % n, "2": "CH%d" % n, "3": "GND"}, (x, 101.6, 0), "MOSFET canal %d" % n),
    ]

NOTES = [
    (20.32, 15.24,
     "LETREROLAB AP-0.1 - POTENCIA.  PELIGRO: J1, F1, RV1, PS1 (lado CA), K1 (contactos) y J4 estan a voltaje de red.\n"
     "Montar SIEMPRE dentro del gabinete cerrado. La salida de PS1 (12 V) es aislada; todo lo demas es bajo voltaje."),
    (20.32, 139.7,
     "Fuente interna HLK-10M12: hasta 0.8 A en total (letreros de LED de 5 mm, tiras cortas, ~10 W).\n"
     "Para tiras largas usar la placa base 12 V con un eliminador externo de mas corriente.\n"
     "J4 es un contacto seco: la fase del foco pasa por COM -> NA. Cumple con la instalacion electrica local."),
]
TEXTS_SCH = [(20.32, 22.86, "Entrada de red y fuente conmutada"), (20.32, 93.98, "Relevador para focos normales"),
             (139.7, 86.36, "Canales de potencia")]

W, H = 90.0, 80.0
HOLES = [(3.5, 3.5), (W - 3.5, 3.5), (3.5, H - 3.5), (W - 3.5, H - 3.5)]
YQ = 60.0                                  # patas de los MOSFET
XG = (44.0, 54.8, 65.6, 76.4)              # compuertas Q1..Q4
YBUS = 52.54
POS = {
    "J1": (16.0, 7.0, 180), "F1": (16.0, 15.0, 0), "RV1": (10.92, 22.0, 0), "PS1": (28.0, 22.0, 0),
    "K1": (31.0, 60.0, 180), "J4": (5.6, 54.92, 270), "J5": (52.9, 44.0, 90), "J3": (44.0, 74.5, 0),
    "C1": (87.54, 50.0, 180), "Q5": (37.5, 48.5, 180), "D3": (37.0, 67.0, 90), "R9": (36.5, 44.0, 0),
    "R10": (34.96, 52.3, 0),
}
for i, xg in enumerate(XG):
    POS["Q%d" % (i + 1)] = (xg, YQ, 0)
    POS["R%d" % (i + 1)] = (xg, YQ - 4.92, 90)
    POS["R%d" % (i + 5)] = (xg, YQ + 3.5, 0)
XS = [x + 5.08 for x in XG]
XD = [x + 2.54 for x in XG]
XGND = 39.04                               # columna de GND a la izquierda (baja por debajo de PS1)
TRACKS = {  # todo a mano, del lado del cobre (B.Cu), sin puentes
    "L": [[(16.0, 7.0), (16.0, 15.0)]],
    "LF": [[(21.08, 15.0), (21.08, 22.0), (28.0, 22.0)], [(15.92, 23.3), (17.22, 22.0), (21.08, 22.0)]],
    "N": [[(10.92, 7.0), (10.92, 29.8), (28.0, 29.8)]],
    "COM": [[(31.0, 60.0), (5.6, 60.0)]],
    "NO": [[(16.85, 53.95), (15.88, 54.92), (5.6, 54.92)]],
    "V12": [[(70.68, 44.0), (70.5, 37.2)],
            [(70.5, 37.2), (88.4, 37.2), (88.4, 70.0), (82.5, 70.0), (82.5, 78.4), (29.05, 78.4), (29.05, 65.95)],
            [(44.0, 74.5), (44.0, 78.4)], [(37.0, 67.0), (37.0, 78.4)]],
    "GND": [[(70.5, 14.6), (68.6, 16.5), (XGND, 16.5), (XGND, YBUS), (85.0, YBUS), (85.0, 50.0)],
            [(60.52, 44.0), (60.52, YBUS)], [(63.06, 44.0), (63.06, YBUS)],
            [(37.5, 48.5), (XGND, 48.5)], [(37.5, 48.5), (37.5, 52.3)]] + [[(x, 63.5), (x, YBUS)] for x in XS],
    "AUX": [[(52.9, 44.0), (41.58, 44.0)]],
    "G5": [[(36.5, 44.0), (34.96, 45.54), (34.96, 52.3)]],
    "RLY": [[(32.42, 48.5), (32.42, 51.0), (29.05, 53.95)],
            [(29.05, 53.95), (29.6, 54.5), (34.0, 54.5), (37.0, 57.5), (37.0, 61.92)]],
    "PWM1": [[(55.44, 44.0), (55.44, 46.2), (XG[0], 46.2), (XG[0], 50.0)]],
    "PWM2": [[(57.98, 44.0), (57.98, 47.7), (XG[1], 47.7), (XG[1], 50.0)]],
    "PWM3": [[(65.6, 44.0), (XG[2], 50.0)]],
    "PWM4": [[(68.14, 44.0), (68.14, 47.0), (XG[3], 47.0), (XG[3], 50.0)]],
    "CH1": [[(XD[0], YQ), (XD[0], 70.0), (49.08, 72.54), (49.08, 74.5)]],
    "CH2": [[(XD[1], YQ), (XD[1], 66.0), (54.16, 69.18), (54.16, 74.5)]],
    "CH3": [[(XD[2], YQ), (XD[2], 67.2), (63.0, 67.2), (59.24, 70.96), (59.24, 74.5)]],
    "CH4": [[(XD[3], YQ), (XD[3], 69.5), (68.3, 69.5), (64.32, 73.48), (64.32, 74.5)]],
}
for i, xg in enumerate(XG):
    TRACKS["G%d" % (i + 1)] = [[(xg, YQ - 4.92), (xg, YQ + 3.5)]]
WIDTH = {"V12": 1.0, **{n: 1.5 for n in ("L", "N", "LF", "COM", "NO", "GND", "CH1", "CH2", "CH3", "CH4")}}
RED = ("L", "N", "LF", "COM", "NO")
TEXTS = [  # (texto, x, y, tamaño, ángulo, capa)
    ("LETREROLAB AP-0.1 POTENCIA", 60.0, 2.2, 1.0, 0, "F.SilkS"),
    ("AP-0.1 POTENCIA", 57.0, 7.5, 1.5, 0, "B.Cu"),
    ("N", 10.92, 11.0, 1.0, 0, "F.SilkS"), ("L", 16.0, 11.0, 1.0, 0, "F.SilkS"),
    ("RED 100-240 VCA", 13.5, 1.6, 0.8, 0, "F.SilkS"),
    ("PELIGRO 127 V", 13.0, 40.0, 1.2, 0, "F.SilkS"),
    ("NA", 9.4, 54.92, 0.8, 0, "F.SilkS"), ("COM", 9.6, 60.0, 0.8, 0, "F.SilkS"),
    ("FOCOS (contacto 10 A)", 8.0, 64.5, 0.7, 0, "F.SilkS"),
    ("+12", 44.0, 71.2, 0.8, 0, "F.SilkS"), ("CH1", 49.08, 71.2, 0.8, 0, "F.SilkS"),
    ("CH2", 54.16, 71.2, 0.8, 0, "F.SilkS"), ("CH3", 59.24, 71.2, 0.8, 0, "F.SilkS"),
    ("CH4", 64.32, 71.2, 0.8, 0, "F.SilkS"),
    ("A CABEZAL: 1 AUX 2-3 PWM 4-5 GND 6-7 PWM 8 +12V", 61.8, 40.6, 0.7, 0, "F.SilkS"),
]
REDCLR, LVCLR = 2.0, 5.0      # entre redes de 127 V / entre 127 V y bajo voltaje


def keepouts():
    """Zonas prohibidas para el ruteador alrededor de la red de 127 V (5 mm; 3 mm dentro del relevador)."""
    import math
    inK1 = lambda x, y: 12.0 < x < 33.5 and 51.5 < y < 68.5
    out = []
    for n in RED:
        for pl in TRACKS.get(n, []):
            for (x1, y1), (x2, y2) in zip(pl[:-1], pl[1:]):
                k = max(1, int(math.hypot(x2 - x1, y2 - y1) / 0.8))
                for i in range(k + 1):
                    x, y = x1 + (x2 - x1) * i / k, y1 + (y2 - y1) * i / k
                    out.append((x, y, 0.75 + (3.1 if inK1(x, y) else LVCLR + 0.1)))
    for ref, pads in (("J1", ((16.0, 7.0), (10.92, 7.0))), ("F1", ((16.0, 15.0), (21.08, 15.0))),
                      ("RV1", ((10.92, 22.0), (15.92, 23.3))), ("PS1", ((28.0, 22.0), (28.0, 29.8))),
                      ("J4", ((5.6, 54.92), (5.6, 60.0))), ("K1", ((16.85, 53.95),))):
        for x, y in pads:
            out.append((x, y, 1.5 + LVCLR + 0.1))
    out.append((31.0, 60.0, 1.5 + 3.1))       # COM del relevador (zona de la bobina)
    return out


def dru():
    """Reglas: 127 V contra 127 V >= 2 mm; 127 V contra bajo voltaje >= 5 mm (aislamiento reforzado);
    dentro del relevador se acepta su propia separacion bobina-contacto (aislamiento del fabricante)."""
    return ('(version 1)\n'
            '(rule "Pistas >= 0.8 mm"\n  (condition "A.Type == \'track\'")\n  (constraint track_width (min 0.8mm)))\n'
            '(rule "127 V contra 127 V"\n  (condition "A.NetClass == \'Red127V\' && B.NetClass == \'Red127V\'")\n'
            '  (constraint clearance (min %.1fmm)))\n'
            '(rule "127 V contra bajo voltaje (reforzado)"\n'
            '  (condition "A.NetClass == \'Red127V\' && B.NetClass != \'Red127V\'")\n'
            '  (constraint clearance (min %.1fmm)))\n'
            '(rule "Dentro del relevador y de la fuente (aislamiento del fabricante)"\n'
            '  (condition "(A.Parent == \'K1\' && B.Parent == \'K1\') || (A.Parent == \'PS1\' && B.Parent == \'PS1\')")\n'
            '  (constraint clearance (min 1.5mm)))\n'
            '(rule "Contacto COM junto a su propia bobina (aislamiento del relevador)"\n'
            '  (condition "(A.NetName == \'/COM\' && (B.NetName == \'/RLY\' || B.NetName == \'/V12\')) || '
            '(B.NetName == \'/COM\' && (A.NetName == \'/RLY\' || A.NetName == \'/V12\'))")\n'
            '  (constraint clearance (min 3.0mm)))\n'
            '(rule "Contacto NC del relevador (sin usar, junto a COM)"\n'
            '  (condition "(A.Parent == \'K1\' && A.Pad_Number == \'4\') || (B.Parent == \'K1\' && B.Pad_Number == \'4\')")\n'
            '  (constraint clearance (min 2.0mm)))\n' % (REDCLR, LVCLR))


def main():
    os.makedirs(KI, exist_ok=True)
    comps, pos, tracks, wires = list(C), dict(POS), None, []
    rr = os.path.join(HERE, "route_result.json")
    widths = {**{n: 0.8 for c in C for n in c[4].values() if n}, **WIDTH}
    if "--manual" in sys.argv:
        json.dump({"failed": [], "tracks": {"/" + k: v for k, v in TRACKS.items()}, "jumpers": []}, open(rr, "w"))
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
                         "LetreroLab AP-0.1 - Potencia: fuente 100-240 VCA a 12 V, 4 canales MOSFET y relevador",
                         ["PELIGRO: zona de red (J1, F1, RV1, PS1, K1 contactos, J4)",
                          "Bajo voltaje aislado: salida de PS1, J3, J5"], paper="A3",
                         flags=[("LF", 20.32, 50.8), ("N", 35.56, 50.8)] +
                         [(w[2], 137.16 + 15.24 * i, 63.5) for i, w in enumerate(wires) if w[1] in ("V12", "GND")],
                         company="PCB 90 x 80 mm, una cara, THT, 4 barrenos M3, transferencia de toner")
    b = comun.Board(W, H, LIB, KI, NS, comps, pos, holes=HOLES)
    if tracks:
        b.add_tracks(tracks, widths)
    b.texts(TEXTS)
    b.save(PROJECT)
    comun.make_project(KI, PROJECT, red_nets=RED, clr_red=REDCLR, clr=0.5, track=0.8)
    open(os.path.join(KI, PROJECT + ".kicad_dru"), "w").write(dru())
    print("ok", [w[0] for w in wires])


if __name__ == "__main__":
    main()
