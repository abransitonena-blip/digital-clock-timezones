"""AP Electric Industrial · AP Rack IN16 rev A (CONCEPTO): módulo de 16 entradas de 12-30 V optoaisladas para la cadena AP LINK.

Es la placa AP Rack 16 sin las salidas: misma alimentación (12-30 V CC), mismo ESP32-C3, USB-C, panel de LED y enlace AP LINK
(ENTRA/SIGUE). Cambia el frente: 16 entradas LTV-217 con el circuito del 7R Tour (resistencias de 3.3 k), común propio COMI, dos TCA9554 (0x24 y 0x25,
con una sola interrupción compartida) y borneras de 3 polos: IN, IN, IN. El módulo se anuncia en la cadena como tipo 2 (16 entradas, 0 salidas).

    bash ../../tools/rutear.sh ap-electric/in16 AP_IN16
"""
import os, sys, uuid, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import placa  # noqa: E402
_spec = importlib.util.spec_from_file_location("rack16_make", os.path.join(HERE, "..", "..", "rack16", "gen", "make.py"))
B = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(B)

PROJECT = "AP_IN16"
NS = uuid.UUID("2b7e4d19-6a3c-4f58-9e01-8c5d7a3b1f64")
ROOT_UUID = "4a6c8e0b-2d4f-4a1c-9b3e-5d7f9a1c3e86"
import re
_quitar = re.compile(r"^(J(6|7|8|9|1[0-3])|U(6|7|8|1[0-3])|C(15|16|17|19|20|21|22)|Q\d+|DQ\d+|RD\d+|RL\d+|DL\d+|RA\d+|RC\d+|LI\d+|RS\d+|DI\d+|OK\d+|RQ\d+|J3|J4|J5)$")
C_ = [c for c in B.C_ if not _quitar.match(c[0])]
C_ = [c for c in C_ if not (c[0] == "TP10" or c[0] == "TP9")] + [c for c in B.C_ if c[0] in ("TP9", "TP10")]
NENT = 16
C_.append(B.tca("U6", ("GND", "GND", "3V3"), ["E%d" % k for k in range(1, 9)], "0x24: P0-P7 = entradas 1-8 (0 = activa)", int_net="INT"))
C_.append(("C15", "100nF", B.C, B.C06, {"1": "3V3", "2": "GND"}, "Desacoplo U6"))
C_.append(B.tca("U7", ("3V3", "GND", "3V3"), ["E%d" % k for k in range(9, 17)], "0x25: P0-P7 = entradas 9-16 (0 = activa)", int_net="INT"))
C_.append(("C16", "100nF", B.C, B.C06, {"1": "3V3", "2": "GND"}, "Desacoplo U7"))
for k in range(1, NENT + 1):
    C_ += [
        ("RA%d" % k, "3.3k", B.R, B.R08, {"1": "IN%dX" % k, "2": "IA%d" % k}, "Entrada %d (1 de 2)" % k),
        ("RC%d" % k, "3.3k", B.R, B.R08, {"1": "IA%d" % k, "2": "IB%d" % k}, "Entrada %d (2 de 2)" % k),
        ("LI%d" % k, "VERDE", "Device:LED", B.LED06, {"1": "IL%d" % k, "2": "IB%d" % k}, "Entrada %d activa" % k),
        ("RS%d" % k, "2.2k", B.R, B.R06, {"1": "IL%d" % k, "2": "COMI"}, "Umbral: apagada por debajo de ~5 V"),
        ("DI%d" % k, "1N4148W", "Device:D", "Diode_SMD:D_SOD-123", {"1": "IB%d" % k, "2": "COMI"}, "Entrada %d: polaridad invertida" % k),
        ("OK%d" % k, "LTV-217-B", "Isolator:PC817", "Package_SO:SOP-4_4.4x2.6mm_P1.27mm",
         {"1": "IL%d" % k, "2": "COMI", "3": "GND", "4": "E%d" % k}, "Optoacoplador de la entrada %d" % k),
        ("RQ%d" % k, "10k", B.R, B.R06, {"1": "3V3", "2": "E%d" % k}, "Pull-up de la entrada %d" % k),
    ]
_pines = ["IN%dX" % k for k in range(1, 17)] + ["COMI", "COMI"]
for b in range(6):
    C_.append(("J%d" % (3 + b), "KF128-5.08-3P", "Connector:Screw_Terminal_01x03", B.KF3, {"1": _pines[3 * b], "2": _pines[3 * b + 1], "3": _pines[3 * b + 2]},
               "Entradas %s: la 1ª pata de cada trío es la entrada impar de la serie; COMI = 0 V del sensor" % "-".join(p.replace("X", "").replace("IN", "") for p in _pines[3 * b:3 * b + 3])))

W, H = B.W, B.H
RADIO_ESQUINA = B.RADIO_ESQUINA
HOLES = B.HOLES
PX = 17.2
X0 = 36.0
POS = {k: v for k, v in B.POS.items() if k in {c[0] for c in C_}}
POS.update({"U6": (46.0, 50.0, 0), "C15": (51.0, 50.0, 90), "U7": (86.0, 50.0, 0), "C16": (91.0, 50.0, 90)})
for k in range(1, NENT + 1):
    xi = 38.0 + 6.1 * (k - 1)
    POS.update({"RQ%d" % k: (xi + 1.0, 40.0, 90), "OK%d" % k: (xi + 1.0, 34.0, 90), "LI%d" % k: (xi, 28.0, 90),
                "RS%d" % k: (xi + 2.7, 28.0, 90), "DI%d" % k: (xi + 2.7, 23.5, 90), "RC%d" % k: (xi, 23.0, 90), "RA%d" % k: (xi + 0.6, 18.0, 0)})
for b in range(6):
    POS["J%d" % (3 + b)] = (X0 + PX * b, 6.0, 180)
POS["TP9"] = (112.0, 52.0, 0); POS["TP10"] = (117.0, 52.0, 0)
for k in range(1, 9):                                    # el panel de LED queda donde estaba; las resistencias de 1 k encima
    pass
NETCLASS = {"Potencia": (1.5, 0.3, ["VIN_RAW"]), "Media": (0.8, 0.2, ["V24", "V5"]), "Bus": (0.25, 0.2, ["RSA", "RSB"])}
PRE = []
SIN_COBRE = B.SIN_COBRE
SILK = [
    ("AP ELECTRIC INDUSTRIAL  AP RACK IN16  rev A", 70.0, 56.5, 1.3, "F"),
    ("+V  0V", 66.0, 1.6, 0.8, "F"),
    ("ENTRA", 146.0, 90.5, 0.8, "F"), ("SIGUE", 160.0, 90.5, 0.8, "F"),
    ("MODULO 8 4 2 1", 148.0, 63.5, 0.8, "F"), ("RUN FALLA COM CABEZA", 158.0, 73.2, 0.8, "F"),
    ("AP ELECTRIC AP RACK IN16 rev A - CONCEPTO. 16 entradas 12-30 V. SENSE/A/B: solo AP LINK, no AP BUS.", 88.0, 98.5, 0.8, "B"),
]
FLAGS = B.FLAGS
NOTES = [(150.0, 15.0, "AP Electric Industrial · AP Rack IN16 rev A (CONCEPTO): 16 x LTV-217 (12-30 V), 2 x TCA9554 (0x24, 0x25),\n"
                       "SP3485 + 2 x JST XH4 (AP LINK), ESP32-C3. Mismo programa que AP Rack 16 (se reconoce por sus expansores).")]
TITLE = "AP Electric Industrial · AP Rack IN16 rev A - 16 entradas de 12-30 V, AP LINK (CONCEPTO)"
SUBTITLES = B.SUBTITLES
COMPANY = B.COMPANY
COSTURA = B.COSTURA
PAPER = "A3"
OCULTAR_REF = tuple("J%d" % k for k in range(1, 9)) + ("JL1", "JL2")

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
