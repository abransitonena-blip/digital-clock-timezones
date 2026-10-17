"""AP Electric Industrial · AP Rack AO4 rev A (CONCEPTO): módulo de 4 salidas analógicas 0-10 V para la cadena AP LINK.

Es la placa AP Rack 16 sin salidas de potencia: el mismo circuito 0-10 V de la placa AP LIGHT AO4 (un canal del PCA9685 a 1.5 kHz -> filtro RC de 2 etapas ->
LM324 con ganancia 3 -> seguidor PNP que absorbe la corriente de un driver 1-10 V, pull-up de 22 k y zener de 12 V), pero alimentado desde el +V de 12-30 V del
Rack (el LM324 y el pull-up cuelgan del +V: con 12 V la salida llega a ~10 V sin margen, se recomienda 15 V o más). Conserva las 8 entradas de 12-30 V, el panel de
LED y el enlace AP LINK. Se anuncia en la cadena como tipo 6 (4 salidas con nivel 0-255, 8 entradas).

    bash ../../tools/rutear_rapido.sh ap-electric/ao4 AP_RACKAO4
"""
import os, sys, uuid, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import placa  # noqa: E402
_spec = importlib.util.spec_from_file_location("rack16_make", os.path.join(HERE, "..", "..", "rack16", "gen", "make.py"))
B = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(B)

PROJECT = "AP_RACKAO4"
NS = uuid.UUID("d8f2a4c6-3b17-4e95-a0d2-6c4e8a1b3f75")
ROOT_UUID = "e1a3c5d7-4f26-4b08-9d3a-5f7b9c1e2a60"
NCH = 4
KF2 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal"
_quitar = {"U6", "U7", "C15", "C16", "U10", "U11", "U12", "U13", "C19", "C20", "C21", "C22"} | {"J%d" % k for k in range(6, 14)}
for _p in ("Q", "DQ", "RD", "RL", "DL"):
    _quitar |= {"%s%d" % (_p, k) for k in range(1, 17)}
C_ = [c for c in B.C_ if c[0] not in _quitar]
C_.append(("U6", "PCA9685PW", "Driver_LED:PCA9685PW", "Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm",
           {"1": "3V3", "2": "GND", "3": "GND", "4": "GND", "5": "GND", "6": "PW1", "7": "PW2", "8": "PW3", "9": "PW4",
            "10": None, "11": None, "12": None, "13": None, "14": "GND", "15": None, "16": None, "17": None, "18": None,
            "19": None, "20": None, "21": None, "22": None, "23": "GND", "24": "GND", "25": "GND", "26": "SCL", "27": "SDA", "28": "3V3"},
           "PWM de 12 bits por I2C 0x41 (A0 a 3.3 V, A1-A5 a 0 V), 1.5 kHz; LED0-3 = niveles 0-10 V; salidas apagadas al encender"))
C_.append(("C15", "100nF", B.C, B.C06, {"1": "3V3", "2": "GND"}, "Desacoplo U6"))
C_.append(("C16", "10uF", B.C, B.C08, {"1": "3V3", "2": "GND"}, "Reserva del 3.3 V (la amplitud del PWM es la escala del 0-10 V)"))
C_.append(("U10", "LM324DT", "Amplifier_Operational:LM2902", B.SOIC14,
           {"1": "OA1", "2": "NI1", "3": "N21", "4": "V24", "5": "N22", "6": "NI2", "7": "OA2", "8": "OA3", "9": "NI3",
            "10": "N23", "11": "GND", "12": "N24", "13": "NI4", "14": "OA4"}, "4 amplificadores (ganancia 3) desde el +V"))
C_.append(("C19", "100nF", B.C, B.C06, {"1": "V24", "2": "GND"}, "Desacoplo del LM324"))
for k in range(1, NCH + 1):
    C_ += [
        ("RFA%d" % k, "10k", B.R, B.R06, {"1": "PW%d" % k, "2": "N1%d" % k}, "Filtro 1 del canal %d" % k),
        ("CFA%d" % k, "1uF", B.C, B.C06, {"1": "N1%d" % k, "2": "GND"}, "Filtro 1 del canal %d" % k),
        ("RFB%d" % k, "10k", B.R, B.R06, {"1": "N1%d" % k, "2": "N2%d" % k}, "Filtro 2 del canal %d" % k),
        ("CFB%d" % k, "1uF", B.C, B.C06, {"1": "N2%d" % k, "2": "GND"}, "Filtro 2 del canal %d" % k),
        ("RG%d" % k, "10k", B.R, B.R06, {"1": "NI%d" % k, "2": "GND"}, "Ganancia 3: 10k a 0 V"),
        ("RR%d" % k, "20k", B.R, B.R06, {"1": "AO%d" % k, "2": "NI%d" % k}, "Ganancia 3: 20k desde la salida"),
        ("CR%d" % k, "100nF", B.C, B.C06, {"1": "OA%d" % k, "2": "NI%d" % k}, "Compensación (simulada en la placa AP LIGHT AO4)"),
        ("RX%d" % k, "1k", B.R, B.R06, {"1": "OA%d" % k, "2": "BQ%d" % k}, "Base del seguidor %d" % k),
        ("QB%d" % k, "MMBT5401", "Transistor_BJT:Q_PNP_BEC", "Package_TO_SOT_SMD:SOT-23", {"1": "BQ%d" % k, "2": "AI%d" % k, "3": "GND"},
         "Seguidor PNP: absorbe la corriente que inyectan los drivers 1-10 V (hasta 10 mA)"),
        ("RU%d" % k, "22k", B.R, B.R06, {"1": "V24", "2": "AI%d" % k}, "Pull-up para drivers 0-10 V activos"),
        ("RO%d" % k, "47", B.R, B.R06, {"1": "AI%d" % k, "2": "AO%d" % k}, "Salida 0-10 V %d (dentro del lazo)" % k),
        ("CB%d" % k, "100nF", B.C, B.C06, {"1": "AO%d" % k, "2": "GND"}, "Filtro de la salida %d" % k),
        ("DZ%d" % k, "MMSZ5242B 12V", "Device:D_Zener", "Diode_SMD:D_SOD-123", {"1": "AO%d" % k, "2": "GND"}, "Picos y descargas en la salida %d" % k),
        ("J%d" % (5 + k), "KF128-5.08-2P", "Connector:Screw_Terminal_01x02", KF2, {"1": "AO%d" % k, "2": "GND"}, "Salida %d: 1 = 0-10 V, 2 = 0 V" % k),
    ]
_refs = [c[0] for c in C_]
assert len(_refs) == len(set(_refs)), "referencias repetidas: %s" % sorted({r for r in _refs if _refs.count(r) > 1})
W, H = B.W, B.H
RADIO_ESQUINA = B.RADIO_ESQUINA
HOLES = B.HOLES
PX = B.PX
X0 = B.X0
POS = {k: v for k, v in B.POS.items() if k in {c[0] for c in C_}}
POS.update({"U6": (68.0, 51.0, 90), "C15": (77.0, 51.0, 90), "C16": (81.0, 51.0, 90), "U10": (76.0, 38.5, 90), "C19": (83.5, 38.5, 90)})
for k in range(1, NCH + 1):
    x0 = 40.0 + 22.0 * (k - 1)
    POS["J%d" % (5 + k)] = (x0, 6.0, 180)
    for j, ref in enumerate(("RFA", "CFA", "RFB", "CFB")): POS["%s%d" % (ref, k)] = (x0 + 3.0 * j, 17.0, 90)
    for j, ref in enumerate(("RG", "RR", "CR", "RX")): POS["%s%d" % (ref, k)] = (x0 + 3.0 * j, 22.0, 90)
    for j, ref in enumerate(("RU", "RO", "CB")): POS["%s%d" % (ref, k)] = (x0 + 3.0 * j, 27.0, 90)
    POS["DZ%d" % k] = (x0 + 10.0, 27.0, 90); POS["QB%d" % k] = (x0 + 12.5, 21.0, 0)
NETCLASS = {"Potencia": B.NETCLASS["Potencia"], "Media": (0.6, 0.2, ["V24", "V5"]), "Bus": B.NETCLASS["Bus"]}
PRE = []
SIN_COBRE = B.SIN_COBRE
SILK = [
    ("AP ELECTRIC INDUSTRIAL  AP RACK AO4  rev A", 110.0, 14.0, 1.3, "F"),
    *[("0-10V %d" % k, 40.0 + 22.0 * (k - 1) + 5.0, 12.0, 0.8, "F") for k in range(1, NCH + 1)],
    ("+V  0V", 66.0, 1.6, 0.8, "F"),
    ("I1 I2 I3 I4 I5 I6 I7 I8 COM", 6.0, 2.0, 0.8, "F"),
    ("ENTRA", 146.0, 90.5, 0.8, "F"), ("SIGUE", 160.0, 90.5, 0.8, "F"),
    ("MODULO 8 4 2 1", 148.0, 63.5, 0.8, "F"), ("RUN FALLA COM CABEZA", 158.0, 73.2, 0.8, "F"),
    ("AP ELECTRIC AP RACK AO4 rev A - CONCEPTO. 12-30 V CC (15 V o mas para llegar a 10 V). Salidas no aisladas. SENSE/A/B: solo AP LINK.", 88.0, 98.5, 0.8, "B"),
]
FLAGS = [f for f in B.FLAGS if f[0] != "COMI"] if False else B.FLAGS
NOTES = [(115.0, 15.0, "AP Electric Industrial · AP Rack AO4 rev A (CONCEPTO): PCA9685 (0x41) -> filtro RC -> LM324 x4 + PNP -> 4 salidas 0-10 V,\n"
                       "8 entradas de 12-30 V LTV-217 (TCA9554 0x22, 0x23 LED), SP3485 + 2 x JST XH4 (AP LINK), ESP32-C3. No aislado.")]
TITLE = "AP Electric Industrial · AP Rack AO4 rev A - 4 salidas 0-10 V, 8 entradas, AP LINK (CONCEPTO)"
SUBTITLES = B.SUBTITLES
COMPANY = B.COMPANY
COSTURA = B.COSTURA
PAPER = "A3"
OCULTAR_REF = tuple("J%d" % k for k in range(1, 10)) + ("JL1", "JL2")

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
