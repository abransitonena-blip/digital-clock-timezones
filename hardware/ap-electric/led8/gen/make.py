"""AP Electric Industrial · AP Rack LED8 rev A (CONCEPTO): módulo de 8 salidas con brillo (PWM) para tiras y luminarias LED de 12-30 V en la cadena AP LINK.

Es la placa AP Rack 16 con 8 de sus 16 salidas: las mismas etapas NCV8406A (65 V, protegidas) y 74HCT125, pero en lugar de dos expansores TCA9554 las compuertas las
maneja un PCA9685 (I2C 0x40, 12 bits, 1 kHz) y cada salida lleva su brillo. Conserva las 8 entradas de 12-30 V del Rack 16 (botones y fines de carrera), el
panel de LED, la alimentación 12-30 V CC, el ESP32-C3 y el enlace AP LINK (ENTRA/SIGUE). Se anuncia en la cadena como tipo 4 (8 salidas con PWM, 8 entradas).

    bash ../../tools/rutear_rapido.sh ap-electric/led8 AP_LED8
"""
import os, sys, uuid, importlib.util, re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import placa  # noqa: E402
_spec = importlib.util.spec_from_file_location("rack16_make", os.path.join(HERE, "..", "..", "rack16", "gen", "make.py"))
B = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(B)

PROJECT = "AP_LED8"
NS = uuid.UUID("5e9a2c47-1d6b-4a83-b0f5-7c3e9d1a4b28")
ROOT_UUID = "6d2f4a8c-0b3e-4c5d-9e71-3a5c7e9b1d42"
NSAL = 8
_quitar = {"U6", "U7", "C15", "C16", "U12", "U13", "C21", "C22", "J10", "J11", "J12", "J13"}
for _p in ("Q", "DQ", "RD", "RL", "DL"):
    _quitar |= {"%s%d" % (_p, k) for k in range(NSAL + 1, 17)}
C_ = [c for c in B.C_ if c[0] not in _quitar]
C_.append(("U6", "PCA9685PW", "Driver_LED:PCA9685PW", "Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm",
           {"1": "GND", "2": "GND", "3": "GND", "4": "GND", "5": "GND", "6": "IN1", "7": "IN2", "8": "IN3", "9": "IN4",
            "10": "IN5", "11": "IN6", "12": "IN7", "13": "IN8", "14": "GND", "15": None, "16": None, "17": None, "18": None,
            "19": None, "20": None, "21": None, "22": None, "23": "GND", "24": "GND", "25": "GND", "26": "SCL", "27": "SDA", "28": "3V3"},
           "PWM de 12 bits por I2C 0x40 (A0-A5 a 0 V), 1 kHz; salidas 9-16 sin usar; OE a 0 V: las salidas arrancan apagadas y las mantienen así los pull-down RD"))
C_.append(("C15", "100nF", B.C, B.C06, {"1": "3V3", "2": "GND"}, "Desacoplo U6"))
C_.append(("C16", "10uF", B.C, B.C08, {"1": "3V3", "2": "GND"}, "Reserva de U6"))
_refs = [c[0] for c in C_]
assert len(_refs) == len(set(_refs)), "referencias repetidas: %s" % sorted({r for r in _refs if _refs.count(r) > 1})
W, H = B.W, B.H
RADIO_ESQUINA = B.RADIO_ESQUINA
HOLES = B.HOLES
PX = B.PX
X0 = B.X0
POS = {k: v for k, v in B.POS.items() if k in {c[0] for c in C_}}
POS.update({"U6": (66.0, 52.5, 90), "C15": (75.0, 52.5, 90), "C16": (79.0, 52.5, 90)})
NETCLASS = B.NETCLASS
NETCLASS = {"Potencia": NETCLASS["Potencia"], "Media": (0.8, 0.2, ["V24", "V5"] + ["Q%d" % k for k in range(1, NSAL + 1)]), "Bus": NETCLASS["Bus"]}
PRE = []
SIN_COBRE = B.SIN_COBRE
SILK = [
    ("AP ELECTRIC INDUSTRIAL  AP RACK LED8  rev A", 110.0, 36.0, 1.3, "F"),
    ("+V  0V", 66.0, 1.6, 0.8, "F"),
    ("I1 I2 I3 I4 I5 I6 I7 I8 COM", 6.0, 2.0, 0.8, "F"),
    ("L1 L2  L3 L4  L5 L6  L7 L8  PWM 1 kHz", 36.0, 12.0, 0.8, "F"),
    ("ENTRA", 146.0, 90.5, 0.8, "F"), ("SIGUE", 160.0, 90.5, 0.8, "F"),
    ("MODULO 8 4 2 1", 148.0, 63.5, 0.8, "F"), ("RUN FALLA COM CABEZA", 158.0, 73.2, 0.8, "F"),
    ("AP ELECTRIC AP RACK LED8 rev A - CONCEPTO. 12-30 V CC. Carga entre +V y la salida. SENSE/A/B: solo AP LINK, no AP BUS.", 88.0, 98.5, 0.8, "B"),
]
FLAGS = B.FLAGS
NOTES = [(115.0, 15.0, "AP Electric Industrial · AP Rack LED8 rev A (CONCEPTO): PCA9685 (0x40) -> 2 x 74HCT125 -> 8 x NCV8406A (8 salidas con PWM),\n"
                       "8 entradas de 12-30 V LTV-217 (TCA9554 0x22, 0x23 LED), SP3485 + 2 x JST XH4 (AP LINK), ESP32-C3. Sin red de CA.")]
TITLE = "AP Electric Industrial · AP Rack LED8 rev A - 8 salidas con brillo, 8 entradas, AP LINK (CONCEPTO)"
SUBTITLES = B.SUBTITLES
COMPANY = B.COMPANY
COSTURA = B.COSTURA
PAPER = "A3"
OCULTAR_REF = tuple("J%d" % k for k in range(1, 14)) + tuple(["JL1", "JL2"] + ["RL%d" % k for k in range(1, 9)] + ["RD%d" % k for k in range(1, 9)])

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
