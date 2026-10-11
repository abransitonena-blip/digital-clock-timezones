"""AP ELECTRIC · AP FOCO 127: el cabezal AP FOCO con su propia fuente de red (127 o 220 VCA).

Lado izquierdo (x 0-60): el AP FOCO tal cual (mismas piezas y rutas), con dos cambios:
- Cada canal lleva 0.2 Ohm (la resistencia Kelvin de 0.1 Ohm que mide el INA238 + otra de 0.1 Ohm en serie):
  el AL8860 entrega como máximo 500 mA por foco. Así los dos focos juntos (2 x 0.5 A x 20 V) caben siempre en la
  fuente de 21.6 W, aunque la resistencia de ID de un foco pida más.
- El PCA9685 va en 0x64 (A2 a 3.3 V; JP1 -> 0x65): el programa reconoce la versión de red y su tope de 500 mA.
Lado derecho (x 60-120): la entrada de red.
- Bornera KF128 (L, N) -> fusible de retardo 2 A 250 VCA -> varistor 10D471K -> fuente encapsulada Mean Well
  IRM-20-24 (85-264 VCA, 24 V 0.9 A, aislamiento entrada-salida 3 kVCA, certificada por el fabricante).
- Las patas de red de la fuente están en el borde derecho, a 45 mm de sus patas de 24 V.
- En la zona de red no hay relleno de cobre; entre la red y la baja tensión hay una ranura fresada y más de 8 mm
  de separación en la placa (aislamiento reforzado para 250 VCA). La red solo toca la bornera, el fusible, el
  varistor y las dos patas de entrada de la fuente.
Va dentro de una caja cerrada (la bornera de red no se toca con la caja puesta).

    bash ../tools/rutear.sh ap1-foco127 AP_FOCO127
"""
import importlib.util, os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import placa  # noqa: E402

_spec = importlib.util.spec_from_file_location("ap_foco", os.path.join(HERE, "..", "..", "ap1-foco", "gen", "make.py"))
F = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(F)

PROJECT = "AP_FOCO127"
NS = uuid.UUID("4d7a2c91-6e3b-4f58-a2d1-9c8e7b6a5f43")
ROOT_UUID = "7e9a1c3b-5d2f-4b6a-8c4e-0f1a2b3c4d5e"
R12 = "Resistor_SMD:R_1206_3216Metric"

QUITAR = {"J3"}                                   # la entrada de 12-24 V la da la fuente de la placa
C_ = []
for c in F.C_:
    ref, val, sym, fp, pins, func = c
    if ref in QUITAR:
        continue
    pins = dict(pins)
    if ref == "U1":                               # A2 (pata 3) a 3.3 V: 0x64
        pins["3"] = "3V3"
        func = "PWM del CTRL de los dos focos (0x64; JP1 -> 0x65: versión de red)"
    if ref in ("RSC1", "RSC2"):                   # la Kelvin termina en el punto medio; la segunda va en serie
        k = ref[-1]
        pins["4"] = "MID" + k
        func = "Mide la corriente (0.1 Ohm, Kelvin al INA238)"
    if ref == "F1":
        func = "Fusible de 3 A del lado de 24 V"
    C_.append((ref, val, sym, fp, pins, func))
for k in (1, 2):
    C_.append(("RSB%d" % k, "0R1", "Device:R", R12, {"1": "MID%d" % k, "2": "LEDA%d" % k},
               "Segunda resistencia de corriente: 0.1 V / 0.2 Ohm = 500 mA por foco"))
C_ += [
    # --- red ---
    ("J6", "KF128-5.08-2P", "Connector:Screw_Terminal_01x02",
     "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
     {"1": "L", "2": "N"}, "Entrada de red 127/220 VCA: 1 = L (fase), 2 = N (neutro)"),
    ("F2", "T2A 250VCA", "Device:Fuse", "LetreroLab:Fuse_2410_6125Metric", {"1": "L", "2": "LF"},
     "Fusible de retardo 2 A 250 VCA (protege la fuente y el cableado)"),
    ("RV1", "10D471K", "Device:Varistor", "Varistor:RV_Disc_D12mm_W5mm_P7.5mm", {"1": "LF", "2": "N"},
     "Varistor contra picos de la red (300 VCA)"),
    ("PS1", "IRM-20-24", "Converter_ACDC:IRM-20-24", "Converter_ACDC:Converter_ACDC_MeanWell_IRM-20-xx_THT",
     {"1": "LF", "2": "N", "3": "GND", "4": "VIN_RAW"},
     "Fuente encapsulada Mean Well 24 V 0.9 A, aislada y certificada (85-264 VCA)"),
]

W, H = 120.0, 56.0
RADIO_ESQUINA = 2.0
HOLES = list(F.HOLES) + [(116.5, 52.5)]
POS = {k: v for k, v in F.POS.items() if k not in QUITAR}
for k in (1, 2):
    POS["RSB%d" % k] = (17.6, 20.5 + (k - 1) * F.DY, 90)
POS.update({
    # IRM-20 girada 180: patas de red (1, 2) en x = 112, de 24 V (3, 4) en x = 67
    "PS1": (112.0, 27.0, 180),
    "J6": (101.0, 50.0, 0), "F2": (91.0, 51.0, 180), "RV1": (90.0, 40.0, 0),
})
NETCLASS = dict(F.NETCLASS)
NETCLASS["Red"] = (1.0, 1.5, ["L", "LF", "N"])   # la red va fija (PRE): 1.5 mm entre L y N, lejos de la baja tensión
NETCLASS["Media"] = (0.6, 0.2, list(F.NETCLASS["Media"][2]) + ["MID1", "MID2"])
PRE = list(F.PRE) + [
    # red, trazada a mano (todo en la zona x > 86, lejos de la baja tensión)
    ("L", 1.0, [(101.0, 50.0), (99.5, 51.0), (93.8, 51.0)]),
    ("LF", 1.0, [(88.2, 51.0), (88.2, 41.8), (90.0, 40.0)]),
    ("LF", 1.0, [(90.0, 40.0), (103.0, 27.0), (112.0, 27.0)]),
    ("N", 1.0, [(106.08, 50.0), (106.08, 44.0), (99.3, 44.0), (97.5, 42.2)]),
    ("N", 1.0, [(106.08, 44.0), (117.0, 33.0), (117.0, 8.2), (115.0, 6.2), (112.0, 6.2)]),
]
CELDAS = {"PS1": 2}
PREVIAS = list(F.PREVIAS)
# zona de red: sin relleno de cobre; ranura entre la red y la baja tensión
# aislamiento comprobado por el DRC: distancia en el aire y por la superficie (con las ranuras) entre la red y el resto
DRU = ('(rule "aislamiento_red" (condition "A.NetClass == \'Red\' && B.NetClass != \'Red\'") '
       '(constraint clearance (min 6.0mm)) (constraint creepage (min 6.4mm)))\n')
SIN_RELLENO = [[(80.0, 0.3), (119.7, 0.3), (119.7, 55.7), (80.0, 55.7)]]
RANURAS = [(80.0, 31.0, 82.0, 54.0)]
SILK = [s for s in F.SILK if s[0] not in ("+12-24V 0V", "AP FOCO")] + [
    ("L    N", 103.5, 44.4, 1.0, "F"),
    ("PELIGRO: RED 127/220 VCA", 90.5, 34.0, 1.0, "F"),
    ("AP FOCO 127", 36.0, 33.0, 1.2, "F"),
    ("AP ELECTRIC  AP FOCO 127  2 x 500 mA  fuente propia 127/220 VCA", 60.0, 54.8, 1.0, "B"),
    ("Zona de red: desconectar antes de abrir la caja", 100.0, 40.0, 0.9, "B"),
]
FLAGS = [f for f in F.FLAGS if f[0] not in ("VIN_RAW", "GND")] + [("LF", 360.68, 271.78), ("N", 375.92, 271.78)]
NOTES = [(150.0, 15.0, "AP ELECTRIC · AP FOCO 127: PCA9685 0x64 (CTRL), INA238 0x4C/0x4D, 2 x AL8860 a 500 mA.\n"
                       "Red: KF128 -> T2A -> 10D471K -> Mean Well IRM-20-24 (24 V 0.9 A, aislada 3 kVCA).")]
TITLE = "AP ELECTRIC · AP FOCO 127 - focos de corriente constante con fuente de red"
SUBTITLES = ["Placa de 2 capas, 1 oz (JLCPCB)", "127/220 VCA, 2 x 500 mA, 20 W"]
COMPANY = "PCB 120 x 56 mm, 2 capas"

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
