"""AP Electric Industrial · AP Rack AI8 rev A (CONCEPTO): módulo de 8 entradas analógicas (0-10 V o 4-20 mA) para la cadena AP LINK.

Misma alimentación (12-30 V CC), ESP32-C3, USB-C, panel de LED y enlace AP LINK que el AP Rack 16. Cambia el frente: dos ADS1115 (16 bits, I2C 0x48 y 0x49)
con 4 canales cada uno y el circuito de la placa AP PRO AI4 por canal:
- Borne de 3 polos: 1 = +V de los sensores (después del fusible), 2 = señal, 3 = 0 V.
- 0-10 V: divisor 22k / 10k (10 V -> 3.125 V al ADC) y filtro 1k + 100 nF.
- 4-20 mA: puente JPn cerrado = shunt de 150 Ω a 0 V (20 mA -> 3.0 V). Con el puente cerrado NO conectar una fuente de voltaje.
  Con el puente hay que avisarle al programa del módulo (orden AM) para que informe mA y no V.
- El lazo de 4-20 mA se alimenta con la misma entrada del módulo (12-30 V): un transmisor a 2 hilos pide unos 12 V más los 3 V del shunt; con menos de ~15 V puede no llegar.
El módulo se anuncia en la cadena como tipo 3 (0 salidas, 0 entradas digitales, 8 analógicas). No aislado.

    bash ../../tools/rutear.sh ap-electric/ai8 AP_AI8
"""
import os, sys, uuid, re, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import placa  # noqa: E402
_spec = importlib.util.spec_from_file_location("rack16_make", os.path.join(HERE, "..", "..", "rack16", "gen", "make.py"))
B = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(B)

PROJECT = "AP_AI8"
NS = uuid.UUID("7c1d9e35-4b8a-4e62-8f17-2a6c4e8b0d93")
ROOT_UUID = "9b1d3f5a-7c2e-4b4d-8a6f-0e2c4a6b8d10"
SJ = B.SJO
_quitar = re.compile(r"^(J(3|4|5|6|7|8|9|1[0-3])|U(6|7|8|1[0-3])|C(15|16|17|19|20|21|22)|Q\d+|DQ\d+|RD\d+|RL\d+|DL\d+|RA\d+|RC\d+|LI\d+|RS\d+|DI\d+|OK\d+|RQ\d+|TP9|TP10)$")
C_ = [c for c in B.C_ if not _quitar.match(c[0])]
C_ += [("TP9", "TP SI", "Connector:TestPoint", B.TP, {"1": "SENSE_I"}, "Punto de prueba SI"), ("TP10", "TP SO", "Connector:TestPoint", B.TP, {"1": "SENSE_O"}, "Punto de prueba SO")]
ADS = "Package_SO:TSSOP-10_3x3mm_P0.5mm"
for ref, cref, dirn, an, cod in (("U6", "C15", "GND", range(1, 5), "0x48"), ("U7", "C16", "3V3", range(5, 9), "0x49")):
    C_.append((ref, "ADS1115IDGSR", "Analog_ADC:ADS1115IDGS", ADS,
               {"1": dirn, "2": None, "3": "GND", "4": "AN%d" % an[0], "5": "AN%d" % an[1], "6": "AN%d" % an[2], "7": "AN%d" % an[3], "8": "3V3", "9": "SDA", "10": "SCL"},
               "ADC de 16 bits, I2C %s (ADDR a %s)" % (cod, "0 V" if dirn == "GND" else "3.3 V")))
    C_.append((cref, "100nF", B.C, B.C06, {"1": "3V3", "2": "GND"}, "Desacoplo %s" % ref))
NAN = 8
for k in range(1, NAN + 1):
    C_ += [
        ("RT%d" % k, "22k", B.R, B.R06, {"1": "IN%d" % k, "2": "ND%d" % k}, "Divisor canal %d (10 V -> 3.125 V)" % k),
        ("RB%d" % k, "10k", B.R, B.R06, {"1": "ND%d" % k, "2": "GND"}, "Divisor canal %d" % k),
        ("RF%d" % k, "1k", B.R, B.R06, {"1": "ND%d" % k, "2": "AN%d" % k}, "Filtro y protección canal %d" % k),
        ("CF%d" % k, "100nF", B.C, B.C06, {"1": "AN%d" % k, "2": "GND"}, "Filtro canal %d (0.1 ms)" % k),
        ("RM%d" % k, "150", B.R, B.R08, {"1": "IN%d" % k, "2": "MA%d" % k}, "Shunt 4-20 mA canal %d (20 mA -> 3.0 V)" % k),
        ("JM%d" % k, "4-20mA", "Jumper:SolderJumper_2_Open", SJ, {"1": "MA%d" % k, "2": "GND"}, "Canal %d en 4-20 mA (cerrar). Abierto = 0-10 V" % k),
        ("J%d" % (5 + k), "KF128-5.08-3P", "Connector:Screw_Terminal_01x03", B.KF3, {"1": "V24", "2": "IN%d" % k, "3": "GND"},
         "Canal %d: 1 = +V del sensor, 2 = señal, 3 = 0 V" % k),
    ]
W, H = B.W, B.H
RADIO_ESQUINA = B.RADIO_ESQUINA
HOLES = B.HOLES
PX = 17.2
X0 = 36.0
POS = {k: v for k, v in B.POS.items() if k in {c[0] for c in C_}}
POS.update({"U6": (60.0, 54.0, 0), "C15": (65.0, 54.0, 90), "U7": (100.0, 54.0, 0), "C16": (105.0, 54.0, 90)})
POS["TP9"] = (112.0, 40.0, 0); POS["TP10"] = (117.0, 40.0, 0)
for k in range(1, NAN + 1):
    x0 = X0 + PX * (k - 1)
    POS["J%d" % (5 + k)] = (x0, 6.0, 180)
    POS.update({"RT%d" % k: (x0 + 2.0, 21.0, 90), "RB%d" % k: (x0 + 5.0, 21.0, 90), "RF%d" % k: (x0 + 8.0, 21.0, 90),
                "CF%d" % k: (x0 + 11.0, 21.0, 90), "RM%d" % k: (x0 + 2.0, 29.0, 90), "JM%d" % k: (x0 + 7.0, 30.0, 90)})
NETCLASS = {"Potencia": (1.5, 0.3, ["VIN_RAW"]), "Media": (0.8, 0.2, ["V24", "V5"]), "Bus": (0.25, 0.2, ["RSA", "RSB"])}
PRE = []
SIN_COBRE = B.SIN_COBRE
SILK = [
    ("AP ELECTRIC INDUSTRIAL  AP RACK AI8  rev A", 70.0, 42.5, 1.3, "F"),
    ("+V  0V", 66.0, 1.6, 0.8, "F"),
    *[("AI%d" % k, X0 + PX * (k - 1) + 5.1, 16.5, 0.9, "F") for k in range(1, NAN + 1)],
    ("mA: cerrar JMn", 70.0, 34.5, 0.8, "F"),
    ("ENTRA", 146.0, 90.5, 0.8, "F"), ("SIGUE", 160.0, 90.5, 0.8, "F"),
    ("MODULO 8 4 2 1", 148.0, 63.5, 0.8, "F"), ("RUN FALLA COM CABEZA", 158.0, 73.2, 0.8, "F"),
    ("AP ELECTRIC AP RACK AI8 rev A - CONCEPTO. 0-10 V / 4-20 mA. Puente cerrado: NO conectar voltaje. SENSE/A/B: solo AP LINK.", 88.0, 98.5, 0.8, "B"),
]
FLAGS = B.FLAGS
NOTES = [(150.0, 15.0, "AP Electric Industrial · AP Rack AI8 rev A (CONCEPTO): 2 x ADS1115 (I2C 0x48, 0x49), 8 entradas 0-10 V (22k/10k) o 4-20 mA (150 ohm con JMn),\n"
                       "SP3485 + 2 x JST XH4 (AP LINK), ESP32-C3. No aislado.")]
TITLE = "AP Electric Industrial · AP Rack AI8 rev A - 8 entradas analógicas, AP LINK (CONCEPTO)"
SUBTITLES = B.SUBTITLES
COMPANY = B.COMPANY
COSTURA = B.COSTURA
PAPER = "A3"
OCULTAR_REF = tuple("J%d" % k for k in range(1, 14)) + ("JL1", "JL2")

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
