"""AP ELECTRIC · AP INPUT: módulo de 8 entradas de 12-24 V DC aisladas para el programador AP-1 (AP CORE).

Para qué: pulsadores, interruptores, sensores de presencia PNP/contacto, flotadores, finales de carrera,
contactos auxiliares de contactores y alarmas. El programa reacciona a cada entrada (encender luces, escenas,
salidas de AP OUTPUT) y las publica en la app y en Home Assistant.

Circuito por entrada (lado de campo, aislado):
  In -> 4.7k (1206) -> LED del LTV-217 -> COM, con 1k en paralelo al LED.
  - Enciende desde unos 6 V (el 1k se lleva los primeros 1.1 mA): el ruido no la activa.
  - A 24 V: 4.9 mA en total, 3.8 mA por el LED. A 12 V: 1.2 mA por el LED (CTR >= 130 %).
  - Conectada al revés: el 1k deja al LED en 4.2 V inversos (aguanta 6 V).
Lado lógico: colector con 10k a 3.3 V y LED indicador (2.2k) -> TCA9554 (I2C 0x24-0x27; A2 = 1).
Aislamiento: franja de 3.5 mm sin cobre entre el campo (In, COM) y el programador; optoacopladores LTV-217 (3 kV o más).
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import placa  # noqa: E402

PROJECT = "AP_Input"
NS = uuid.UUID("7286ead3-dd88-4189-ac48-9236c8a80839")
ROOT_UUID = "73c0f81f-b2ef-43f0-90c6-7d91ce77f8c0"
R06, C06, R12 = "Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric", "Resistor_SMD:R_1206_3216Metric"
MKDS3 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-%d-5.08_1x0%d_P5.08mm_Horizontal"
QWIIC = "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal"
SJ = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"
R, C = "Device:R", "Device:C"
BUS = {"1": "GND", "2": "3V3", "3": "SDA", "4": "SCL", "MP": "GND"}

C_ = [
    ("J1", "QWIIC ENTRADA", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", QWIIC, dict(BUS),
     "Del programador (o del módulo anterior)"),
    ("J2", "QWIIC SALIDA", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", QWIIC, dict(BUS),
     "Al siguiente módulo"),
    ("J3", "I2C", "Connector:Conn_01x04_Pin", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
     {"1": "GND", "2": "3V3", "3": "SDA", "4": "SCL"}, "Bus por cable dupont (mismo orden que Qwiic)"),
    ("U1", "TCA9554PWR", "Interface_Expansion:TCA9554PW", "Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
     {"1": "A0", "2": "A1", "3": "3V3", "4": "IN1", "5": "IN2", "6": "IN3", "7": "IN4", "8": "GND",
      "9": "IN5", "10": "IN6", "11": "IN7", "12": "IN8", "13": None, "14": "SCL", "15": "SDA", "16": "3V3"},
     "Expansor I2C 0x24-0x27 (A2 = 1: rango de entradas)"),
    ("C1", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U1"),
    ("JP1", "A0", "Jumper:SolderJumper_2_Open", SJ, {"1": "3V3", "2": "A0"}, "Dirección: cerrado suma 1"),
    ("JP2", "A1", "Jumper:SolderJumper_2_Open", SJ, {"1": "3V3", "2": "A1"}, "Dirección: cerrado suma 2"),
    ("RA1", "10k", R, R06, {"1": "A0", "2": "GND"}, "A0 en 0 si JP1 abierto"),
    ("RA2", "10k", R, R06, {"1": "A1", "2": "GND"}, "A1 en 0 si JP2 abierto"),
    ("J4", "I1-I3", "Connector:Screw_Terminal_01x03", MKDS3 % (3, 3), {"1": "I1", "2": "I2", "3": "I3"}, "Entradas 1-3"),
    ("J5", "I4-I6", "Connector:Screw_Terminal_01x03", MKDS3 % (3, 3), {"1": "I4", "2": "I5", "3": "I6"}, "Entradas 4-6"),
    ("J6", "I7-I8", "Connector:Screw_Terminal_01x02", MKDS3 % (2, 2), {"1": "I7", "2": "I8"}, "Entradas 7-8"),
    ("J7", "COM", "Connector:Screw_Terminal_01x02", MKDS3 % (2, 2), {"1": "COM", "2": "COM"},
     "Común de las entradas: el 0 V de la fuente de los sensores"),
    ("TP1", "3V3", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "3V3"}, "Prueba: 3.3 V"),
    ("TP2", "GND", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "GND"}, "Prueba: tierra"),
]
OX = [6.0, 13.5, 21.0, 28.5, 36.0, 43.5, 51.0, 58.5]       # x de cada canal (optoacoplador y su columna)
for k, x in enumerate(OX, start=1):
    C_ += [
        ("RI%d" % k, "4.7k", R, R12, {"1": "I%d" % k, "2": "IA%d" % k}, "Entrada %d: 4.9 mA a 24 V" % k),
        ("RP%d" % k, "1k", R, R06, {"1": "IA%d" % k, "2": "COM"}, "Umbral de 6 V y protección inversa, entrada %d" % k),
        ("OK%d" % k, "LTV-217-B", "Isolator:PC817", "Package_SO:SOP-4_4.4x2.6mm_P1.27mm",
         {"1": "IA%d" % k, "2": "COM", "3": "GND", "4": "IN%d" % k}, "Optoacoplador entrada %d" % k),
        ("RU%d" % k, "10k", R, R06, {"1": "3V3", "2": "IN%d" % k}, "Pull-up entrada %d" % k),
        ("RL%d" % k, "2.2k", R, R06, {"1": "3V3", "2": "LA%d" % k}, "LED entrada %d" % k),
        ("DL%d" % k, "VERDE", "Device:LED", "LED_SMD:LED_0603_1608Metric", {"1": "IN%d" % k, "2": "LA%d" % k},
         "Entrada %d activa" % k),
    ]

W, H = 72.0, 56.0
RADIO_ESQUINA = 2.0
HOLES = [(3.5, 3.5), (68.5, 3.5), (68.5, 38.5)]
YT = 49.8
POS = {
    "J1": (14.0, 3.6, 180), "J2": (58.0, 3.6, 180), "J3": (30.0, 3.5, 90),
    "U1": (46.0, 11.0, 0), "C1": (46.0, 15.6, 0),
    "JP1": (21.0, 9.0, 0), "JP2": (21.0, 12.5, 0), "RA1": (26.0, 9.0, 0), "RA2": (26.0, 12.5, 0),
    "J4": (4.0, YT, 0), "J5": (21.0, YT, 0), "J6": (38.0, YT, 0), "J7": (50.0, YT, 0),
    "TP1": (63.0, 12.0, 0), "TP2": (63.0, 16.0, 0),
}
for k, x in enumerate(OX, start=1):
    POS.update({"OK%d" % k: (x, 29.25, 90), "RI%d" % k: (x - 1.3, 36.0, 90), "RP%d" % k: (x + 1.9, 36.5, 90),
                "RU%d" % k: (x - 1.2, 22.8, 90), "RL%d" % k: (x + 1.2, 22.8, 90), "DL%d" % k: (x + 1.2, 19.2, 90)})

CAMPO = ["COM"] + ["I%d" % k for k in range(1, 9)] + ["IA%d" % k for k in range(1, 9)]
NETCLASS = {"Campo": (0.3, 0.2, CAMPO)}
ZONA_CAMPO = [(0.3, 31.0), (71.7, 31.0), (71.7, 55.7), (0.3, 55.7)]
ZONAS_FINALES = [("COM", ZONA_CAMPO), ("COM", ZONA_CAMPO, "B")]
SIN_COBRE = [[(0.3, 27.5), (71.7, 27.5), (71.7, 31.0), (0.3, 31.0)]]     # franja de aislamiento de 3.5 mm
DRU = """(rule "aislamiento"
  (condition "A.NetClass == 'Campo' && B.NetClass != 'Campo' && !A.memberOfFootprint('OK*') && !B.memberOfFootprint('OK*')")
  (constraint clearance (min 2.5mm)))
"""
SILK = [
    ("I1", 4.0, 45.6, 0.9, "F"), ("I2", 9.08, 45.6, 0.9, "F"), ("I3", 14.16, 45.6, 0.9, "F"),
    ("I4", 21.0, 45.6, 0.9, "F"), ("I5", 26.08, 45.6, 0.9, "F"), ("I6", 31.16, 45.6, 0.9, "F"),
    ("I7", 38.0, 45.6, 0.9, "F"), ("I8", 43.08, 45.6, 0.9, "F"), ("COM", 50.0, 45.6, 0.9, "F"), ("COM", 55.08, 45.6, 0.9, "F"),
    ("AISLADO 12-24V", 63.0, 34.0, 0.9, "F"),
    ("ENTRA", 14.0, 7.6, 0.8, "F"), ("SIGUE", 58.0, 7.6, 0.8, "F"),
    ("AP ELECTRIC  AP INPUT  8 x 12-24V", 36.0, 54.8, 1.0, "B"),
    ("Dirección: JP1 +1  JP2 +2  (0x24-0x27)", 36.0, 16.0, 0.8, "B"),
    ("AISLAMIENTO 3.5 mm", 36.0, 29.25, 0.8, "B"),
]
FLAGS = [("GND", 20.32, 20.32), ("3V3", 35.56, 20.32), ("COM", 50.8, 20.32)]
NOTES = [(150.0, 15.0, "AP ELECTRIC · AP INPUT: 8 entradas 12-24 V aisladas (LTV-217) + TCA9554 (I2C 0x24-0x27).\n"
                       "Entrada activa = pata en bajo en el TCA9554 (el programa la invierte).")]
TITLE = "AP ELECTRIC · AP INPUT - 8 entradas de 12-24 V aisladas"
SUBTITLES = ["Placa de 2 capas (JLCPCB)", "Pulsadores, sensores, flotadores, contactos auxiliares"]
COMPANY = "PCB 72 x 56 mm (4 módulos DIN), 2 capas, 1 oz"
COSTURA = 5.0
COSTURA_REDES = ("GND", "COM")
PAPER = "A3"
OCULTAR_REF = ("J1", "J2", "J4", "J5", "J6", "J7")

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
