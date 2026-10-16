"""AP Electric Industrial · AP Rack RL4 rev A (CONCEPTO): módulo de 4 relés con contacto seco para la cadena AP LINK.

Es la placa AP Rack 16 con 4 de sus salidas protegidas (NCV8406A) manejando la bobina de un relé Omron G2RL-1A-E DC24 cada una (diodo de bobina SS14 y LED de
bobina como en el Rack 16) y un bloque de 2 polos por relé (común y normalmente abierto). Se alimenta con 24 V CC (la bobina es de 24 V: 21.6 a 26.4 V). Conserva las
8 entradas de 12-30 V, el panel de LED y el enlace AP LINK. Se anuncia en la cadena como tipo 5 (4 salidas, 8 entradas).

NO está diseñada ni validada para tensión de red: los contactos del relé tienen la clasificación de la hoja del fabricante, pero la placa no cumple distancias de
aislamiento de red. Úsala solo con cargas de hasta 30 V (igual que el piloto del 7R Tour).

    bash ../../tools/rutear_rapido.sh ap-electric/rl4 AP_RL4
"""
import os, sys, uuid, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import placa  # noqa: E402
_spec = importlib.util.spec_from_file_location("rack16_make", os.path.join(HERE, "..", "..", "rack16", "gen", "make.py"))
B = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(B)

PROJECT = "AP_RL4"
NS = uuid.UUID("a3c81e56-92d4-4b07-8e1f-5d0b7c2a9e63")
ROOT_UUID = "c4e6a8b0-1d3f-4e5a-9c7b-2f4d6a8c0e51"
NREL = 4
KF2 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal"
_quitar = {"U7", "C16", "U11", "U12", "U13", "C20", "C21", "C22"} | {"J%d" % k for k in range(6, 14)}
for _p in ("Q", "DQ", "RD", "RL", "DL"):
    _quitar |= {"%s%d" % (_p, k) for k in range(NREL + 1, 17)}
C_ = [c for c in B.C_ if c[0] not in _quitar]
# U6 (TCA9554 0x20): solo P0-P3 se usan (compuertas 1-4)
C_ = [B.tca("U6", ("GND", "GND", "GND"), ["IN1", "IN2", "IN3", "IN4", None, None, None, None], "0x20: P0-P3 = compuertas de las salidas 1-4 (los relés)") if c[0] == "U6" else c for c in C_]
for k in range(1, NREL + 1):
    C_ += [
        ("K%d" % k, "G2RL-1A-E DC24", "Relay:Relay_SPST-NO", "Relay_THT:Relay_SPST_Omron_G2RL-1A-E",
         {"A1": "V24", "A2": "Q%d" % k, "13": "C%d" % k, "14": "N%d" % k},
         "Relé %d: Omron G2RL-1A-E 24 V (contacto 16 A 250 VCA resistivo según la hoja; aquí solo hasta 30 V)" % k),
        ("J%d" % (5 + k), "KF128-5.08-2P", "Connector:Screw_Terminal_01x02", KF2, {"1": "C%d" % k, "2": "N%d" % k},
         "Relé %d: 1 = común, 2 = normalmente abierto (contacto seco)" % k),
    ]
_refs = [c[0] for c in C_]
assert len(_refs) == len(set(_refs)), "referencias repetidas: %s" % sorted({r for r in _refs if _refs.count(r) > 1})
W, H = B.W, B.H
RADIO_ESQUINA = B.RADIO_ESQUINA
HOLES = B.HOLES
PX = B.PX
X0 = B.X0
XC = [40.0 + 17.0 * k for k in range(NREL)]          # eje de cada relé
YB = 44.0                                             # patas de la bobina; contactos 13 en y = 24, 14 en y = 19
POS = {k: v for k, v in B.POS.items() if k in {c[0] for c in C_}}
for k, xc in enumerate(XC, start=1):
    POS["K%d" % k] = (xc + 3.75, YB, 180); POS["J%d" % (5 + k)] = (xc + 2.54, 7.0, 180)
# etapas de las bobinas: bloque en la parte superior derecha, libre
XQ = [124.0 + 11.0 * k for k in range(NREL)]
for k, xc in enumerate(XQ, start=1):
    POS.update({"Q%d" % k: (xc, 31.5, 90), "DQ%d" % k: (xc - 1.9, 21.5, 270), "RD%d" % k: (xc, 39.0, 90),
                "RL%d" % k: (xc + 2.3, 20.5, 90), "DL%d" % k: (xc + 2.3, 24.0, 90)})
POS["U10"] = (114.0, 47.0, 90); POS["C19"] = (120.5, 47.0, 90)
NETCLASS = {"Potencia": B.NETCLASS["Potencia"], "Media": (0.8, 0.2, ["V24", "V5"] + ["Q%d" % k for k in range(1, NREL + 1)]), "Bus": B.NETCLASS["Bus"],
            "Contacto": (2.0, 0.3, ["C%d" % k for k in range(1, NREL + 1)] + ["N%d" % k for k in range(1, NREL + 1)])}
PRE = []
for k, xc in enumerate(XC, start=1):
    for capa in ("F", "B"):
        PRE += [
            ("N%d" % k, 2.0, [(xc - 3.75, 19.0), (xc + 3.75, 19.0)], capa),
            ("N%d" % k, 2.0, [(xc - 3.75, 19.0), (xc - 3.75, 10.5), (xc - 2.54, 9.0), (xc - 2.54, 7.0)], capa),
            ("C%d" % k, 2.0, [(xc - 3.75, 24.0), (xc + 8.4, 24.0), (xc + 8.4, 10.5), (xc + 5.0, 7.0), (xc + 2.54, 7.0)], capa),
        ]
SIN_RELLENO = [[(34.0, 0.3), (112.0, 0.3), (112.0, 31.0), (34.0, 31.0)]]
SIN_COBRE = B.SIN_COBRE
SILK = [
    ("AP ELECTRIC INDUSTRIAL  AP RACK RL4  rev A", 60.0, 36.5, 1.3, "F"),
    *[("RELE %d" % k, xc, 30.0, 1.0, "F") for k, xc in enumerate(XC, 1)],
    *[("NA%d   C%d" % (k, k), xc, 14.5, 0.9, "F") for k, xc in enumerate(XC, 1)],
    ("SOLO HASTA 30 V - NO RED", 60.0, 27.5, 1.0, "F"),
    ("+24V  0V", 66.0, 1.6, 0.8, "F"),
    ("I1 I2 I3 I4 I5 I6 I7 I8 COM", 6.0, 2.0, 0.8, "F"),
    ("ENTRA", 146.0, 90.5, 0.8, "F"), ("SIGUE", 160.0, 90.5, 0.8, "F"),
    ("MODULO 8 4 2 1", 148.0, 63.5, 0.8, "F"), ("RUN FALLA COM CABEZA", 158.0, 73.2, 0.8, "F"),
    ("AP ELECTRIC AP RACK RL4 rev A - CONCEPTO. 24 V CC (21.6-26.4 V). Contactos solo hasta 30 V, sin distancias de red. SENSE/A/B: solo AP LINK.", 88.0, 98.5, 0.8, "B"),
]
FLAGS = B.FLAGS
NOTES = [(115.0, 15.0, "AP Electric Industrial · AP Rack RL4 rev A (CONCEPTO): TCA9554 (0x20) -> 74HCT125 -> 4 x NCV8406A -> 4 x relé G2RL-1A-E DC24,\n"
                       "8 entradas de 12-30 V LTV-217 (TCA9554 0x22, 0x23 LED), SP3485 + 2 x JST XH4 (AP LINK), ESP32-C3. Alimentación 24 V. Sin red de CA.")]
TITLE = "AP Electric Industrial · AP Rack RL4 rev A - 4 relés de contacto seco, 8 entradas, AP LINK (CONCEPTO)"
SUBTITLES = B.SUBTITLES
COMPANY = B.COMPANY
COSTURA = B.COSTURA
PAPER = "A3"
OCULTAR_REF = tuple("J%d" % k for k in range(1, 10)) + tuple(["JL1", "JL2"] + ["RL%d" % k for k in range(1, 5)] + ["RD%d" % k for k in range(1, 5)])

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
