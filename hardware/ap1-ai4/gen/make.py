"""AP ELECTRIC · AP PRO AI4: 4 entradas analógicas (0-10 V o 4-20 mA) para el programador AP-1 (AP CORE).

Para qué: sensores industriales y de edificio con salida analógica:
- nivel de cisternas (transmisor 4-20 mA), presión de bombeo, temperatura (transmisor 4-20 mA o 0-10 V),
- luz (fotómetro 0-10 V), humedad, potenciómetros de mando (0-10 V), salidas analógicas de otros equipos.

Circuito por canal:
- Conector JST XH de 3 patas: 1 = +24 V (para alimentar el sensor, con el fusible de la placa), 2 = señal, 3 = 0 V.
- 0-10 V: divisor 22k / 10k (10 V -> 3.125 V) y 1k + 100 nF de filtro hacia el ADC.
  Con 24 V por error, el nodo queda en 7.5 V y entran 3.9 mA por el diodo de protección del ADC (aguanta 10 mA).
- 4-20 mA: puente JPm cerrado = resistencia de 150 ohm a 0 V (20 mA -> 3.0 V en la entrada, 0.94 V en el ADC).
  ¡Con el puente cerrado NO conectar una fuente de voltaje! (24 V en 150 ohm = 3.8 W).
- ADC: ADS1115 (16 bits, I2C, 3.3 V del programador). Dirección 0x49 (JP5 cerrado de fábrica); para un segundo
  módulo, cortar JP5 y cerrar JP6 -> 0x4A. (0x48 lo usa el sensor de temperatura de la BASE.)
- No aislado: el 0 V de la fuente de los sensores es el GND del programador (usar la misma fuente de 24 V).
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import placa  # noqa: E402
import conectores  # noqa: E402

PROJECT = "AP_AI4"
NS = uuid.UUID("6adab52a-9aeb-41cb-804a-1b0020c7d2d6")
ROOT_UUID = "1cd80ccf-ef68-4aeb-8337-bd7024046395"
R06, C06, C12, R08 = ("Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric",
                      "Capacitor_SMD:C_1206_3216Metric", "Resistor_SMD:R_0805_2012Metric")
QWIIC = "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal"
SJ = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"
SJB = "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm"
R, C = "Device:R", "Device:C"
BUS = {"1": "GND", "2": "3V3", "3": "SDA", "4": "SCL", "MP": "GND"}

C_ = [
    ("J1", "QWIIC ENTRADA", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", QWIIC, dict(BUS),
     "Del programador (o del módulo anterior)"),
    ("J2", "QWIIC SALIDA", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", QWIIC, dict(BUS), "Al siguiente módulo"),
    ("U1", "ADS1115IDGSR", "Analog_ADC:ADS1115IDGS", "Package_SO:TSSOP-10_3x3mm_P0.5mm",
     {"1": "ADDR", "2": None, "3": "GND", "4": "AN1", "5": "AN2", "6": "AN3", "7": "AN4", "8": "3V3", "9": "SDA",
      "10": "SCL"}, "ADC de 16 bits, I2C 0x49 (0x4A con JP6)"),
    ("C1", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U1"),
    ("JP5", "0x49", "Jumper:SolderJumper_2_Bridged", SJB, {"1": "3V3", "2": "ADDR"},
     "Dirección 0x49 (cerrado de fábrica; cortar para usar JP6)"),
    ("JP6", "0x4A", "Jumper:SolderJumper_2_Open", SJ, {"1": "SDA", "2": "ADDR"}, "Dirección 0x4A (segundo módulo)"),
    ("J7", "24V", conectores.SYM[2], conectores.VH2, {"1": "VIN_RAW", "2": "GND"},
     "Alimentación de los sensores: 1 = +24 V, 2 = 0 V (la misma fuente que la base). JST VH"),
    ("F1", "3A", "Device:Fuse", "Fuse:Fuse_1206_3216Metric", {"1": "VIN_RAW", "2": "VF"}, "Fusible de los sensores"),
    ("D1", "SS34", "Device:D_Schottky", "Diode_SMD:D_SMA", {"1": "V24", "2": "VF"}, "Polaridad invertida"),
    ("D2", "SMBJ26A", "Device:D_TVS", "Diode_SMD:D_SMB", {"1": "V24", "2": "GND"}, "Supresor de picos"),
    ("C2", "10uF 50V", C, C12, {"1": "V24", "2": "GND"}, "Entrada"),
    ("TP1", "3V3", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "3V3"}, "Prueba: 3.3 V"),
    ("TP2", "GND", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "GND"}, "Prueba: tierra"),
]
CX = [6.0, 22.0, 38.0, 54.0]                     # pata 1 del conector de cada canal
for k, x in enumerate(CX, start=1):
    C_ += [
        ("J%d" % (k + 2 if k < 3 else k + 5), "AI%d" % k, conectores.SYM[3], conectores.XH3,
         {"1": "V24", "2": "IN%d" % k, "3": "GND"}, "Canal %d: 1 = +24 V, 2 = señal, 3 = 0 V (JST XH)" % k),
        ("RT%d" % k, "22k", R, R06, {"1": "IN%d" % k, "2": "ND%d" % k}, "Divisor canal %d (10 V -> 3.125 V)" % k),
        ("RB%d" % k, "10k", R, R06, {"1": "ND%d" % k, "2": "GND"}, "Divisor canal %d" % k),
        ("RS%d" % k, "1k", R, R06, {"1": "ND%d" % k, "2": "AN%d" % k}, "Filtro y protección canal %d" % k),
        ("CF%d" % k, "100nF", C, C06, {"1": "AN%d" % k, "2": "GND"}, "Filtro canal %d (0.1 ms)" % k),
        ("RM%d" % k, "150", R, R08, {"1": "IN%d" % k, "2": "MA%d" % k}, "Shunt 4-20 mA canal %d (20 mA -> 3.0 V)" % k),
        ("JP%d" % k, "4-20mA", "Jumper:SolderJumper_2_Open", SJ, {"1": "MA%d" % k, "2": "GND"},
         "Canal %d en 4-20 mA (cerrar). Abierto = 0-10 V" % k),
    ]

W, H = 72.0, 56.0
RADIO_ESQUINA = 2.0
HOLES = [(3.5, 3.5), (68.5, 3.5), (68.5, 38.5)]
POS = {
    "J1": (14.0, 3.6, 180), "J2": (58.0, 3.6, 180),
    "U1": (36.0, 14.0, 0), "C1": (36.0, 18.6, 0), "JP5": (28.0, 9.5, 0), "JP6": (28.0, 13.0, 0),
    "J7": (60.6, 23.0, 270), "F1": (52.0, 23.5, 90), "D1": (52.0, 30.0, 90), "D2": (46.0, 23.5, 90),
    "C2": (46.0, 30.5, 90), "TP1": (20.0, 10.0, 0), "TP2": (44.0, 9.0, 0),
}
for k, x in enumerate(CX, start=1):
    ref = "J%d" % (k + 2 if k < 3 else k + 5)
    POS.update({
        ref: (x, 51.0, 0),
        "RT%d" % k: (x + 2.5, 42.0, 90), "RB%d" % k: (x + 5.0, 42.0, 90), "RS%d" % k: (x + 5.0, 37.0, 90),
        "CF%d" % k: (x + 7.5, 37.0, 90), "RM%d" % k: (x, 40.0, 90), "JP%d" % k: (x, 35.6, 90),
    })

NETCLASS = {"Media": (0.6, 0.2, ["VIN_RAW", "VF", "V24"])}
SILK = [
    ("AP PRO AI4", 36.0, 26.0, 1.5, "F"),
    ("ENTRA", 14.0, 7.6, 0.8, "F"), ("SIGUE", 58.0, 7.6, 0.8, "F"), ("+24 0V", 65.0, 30.0, 0.8, "F"),
    *[("AI%d" % (k + 1), x + 2.5, 46.6, 0.9, "F") for k, x in enumerate(CX)],
    *[("mA", x, 32.8, 0.8, "F") for x in CX],
    ("1 +24V  2 señal  3 0V", 36.0, 55.0, 0.8, "B"),
    ("AP ELECTRIC  AP PRO AI4  0-10V / 4-20mA", 36.0, 52.8, 0.9, "B"),
    ("4-20 mA: cerrar JPn. Cerrado: NO conectar voltaje", 36.0, 31.0, 0.8, "B"),
    ("I2C 0x49 (JP5) / 0x4A (cortar JP5, cerrar JP6)", 36.0, 21.0, 0.8, "B"),
]
FLAGS = [("VIN_RAW", 20.32, 20.32), ("GND", 35.56, 20.32), ("V24", 50.8, 20.32), ("3V3", 66.04, 20.32),
         ("VF", 81.28, 20.32)]
NOTES = [(150.0, 15.0, "AP ELECTRIC · AP PRO AI4: ADS1115 (I2C 0x49/0x4A) + 4 entradas 0-10 V (22k/10k) o 4-20 mA\\n"
                       "(150 ohm con JPn). +24 V para sensores de lazo con fusible de 3 A. No aislado.")]
TITLE = "AP ELECTRIC · AP PRO AI4 - 4 entradas analógicas"
SUBTITLES = ["Placa de 2 capas (JLCPCB)", "0-10 V o 4-20 mA por canal, ADS1115 de 16 bits"]
COMPANY = "PCB 72 x 56 mm (4 módulos DIN), 2 capas, 1 oz"
COSTURA = 5.0
PAPER = "A3"
OCULTAR_REF = ("J1", "J2", "J3", "J4", "J8", "J9")

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
