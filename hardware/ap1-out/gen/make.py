"""AP ELECTRIC · AP OUTPUT: módulo de 7 salidas de 24 V DC para el programador AP-1 (AP CORE).

Para qué: bobinas de contactores y relevadores de interfaz, electroválvulas de 24 V DC, sirenas, balizas y
lámparas piloto. Las cargas de red (bombas, motores, luces de 127/220 V) se mandan SIEMPRE con un contactor o
relevador de riel DIN certificado: la red NO entra a esta placa.

Circuito:
- Bus: I2C por Qwiic (J1 entra, J2 sigue al siguiente módulo) o por el conector J3 de 2.54 mm.
  3.3 V y GND vienen del programador.
- U1 TCA9554 (I2C 0x20-0x23, según JP1/JP2). Al encender, todas sus patas son entradas: ninguna salida se activa
  hasta que el programa lo pide.
- U2 ULN2003: 7 salidas a GND (la carga va entre +24 V y la salida), 50 V, con diodos para bobinas (COM a +24 V).
  Límite: 300 mA por salida y 700 mA en total (calor del ULN2003).
- P7 del TCA9554: LED RUN (parpadea mientras el programa está al mando).
- Entrada 24 V protegida: fusible 3 A, diodo en serie, supresor SMBJ26A.
- LED por salida (verde): encendido = salida activa.
- No aislado: el 0 V de los 24 V es el GND del programador. Usar la misma fuente que alimenta la base.
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import placa  # noqa: E402

PROJECT = "AP_Output"
NS = uuid.UUID("e0546af7-a8d8-4959-bd5a-7c745928433b")
ROOT_UUID = "334cccb0-f9aa-4df4-b0e6-372ca1d028ab"
R06, C06, C12 = "Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_1206_3216Metric"
MKDS3 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-%d-5.08_1x0%d_P5.08mm_Horizontal"
QWIIC = "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal"
SJ = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"
R, C = "Device:R", "Device:C"
BUS = {"1": "GND", "2": "3V3", "3": "SDA", "4": "SCL", "MP": "GND"}

C_ = [
    # --- bus I2C ---
    ("J1", "QWIIC ENTRADA", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", QWIIC, dict(BUS),
     "Del programador (o del módulo anterior)"),
    ("J2", "QWIIC SALIDA", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", QWIIC, dict(BUS),
     "Al siguiente módulo"),
    ("J3", "I2C", "Connector:Conn_01x04_Pin", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
     {"1": "GND", "2": "3V3", "3": "SDA", "4": "SCL"}, "Bus por cable dupont (mismo orden que Qwiic)"),
    ("U1", "TCA9554PWR", "Interface_Expansion:TCA9554PW", "Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
     {"1": "A0", "2": "A1", "3": "GND", "4": "IN1", "5": "IN2", "6": "IN3", "7": "IN4", "8": "GND",
      "9": "IN5", "10": "IN6", "11": "IN7", "12": "RUNK", "13": None, "14": "SCL", "15": "SDA", "16": "3V3"},
     "Expansor I2C 0x20-0x23 (A2 = 0: rango de salidas)"),
    ("C1", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U1"),
    ("JP1", "A0", "Jumper:SolderJumper_2_Open", SJ, {"1": "3V3", "2": "A0"}, "Dirección: cerrado suma 1"),
    ("JP2", "A1", "Jumper:SolderJumper_2_Open", SJ, {"1": "3V3", "2": "A1"}, "Dirección: cerrado suma 2"),
    ("RA1", "10k", R, R06, {"1": "A0", "2": "GND"}, "A0 en 0 si JP1 abierto"),
    ("RA2", "10k", R, R06, {"1": "A1", "2": "GND"}, "A1 en 0 si JP2 abierto"),
    ("R8", "1k", R, R06, {"1": "3V3", "2": "RUNA"}, "LED RUN"),
    ("D10", "VERDE", "Device:LED", "LED_SMD:LED_0603_1608Metric", {"1": "RUNK", "2": "RUNA"},
     "RUN: lo enciende el programa (P7 en bajo)"),
    # --- entrada de 24 V ---
    ("J4", "24V", "Connector:Screw_Terminal_01x02", MKDS3 % (2, 2), {"1": "VIN_RAW", "2": "GND"},
     "Alimentación de las cargas: +24 V y 0 V (la misma fuente que la base)"),
    ("F1", "3A", "Device:Fuse", "Fuse:Fuse_1206_3216Metric", {"1": "VIN_RAW", "2": "VF"}, "Fusible"),
    ("D1", "SS34", "Device:D_Schottky", "Diode_SMD:D_SMA", {"1": "V24", "2": "VF"}, "Polaridad invertida"),
    ("D2", "SMBJ26A", "Device:D_TVS", "Diode_SMD:D_SMB", {"1": "V24", "2": "GND"}, "Supresor de picos"),
    ("C2", "10uF 50V", C, C12, {"1": "V24", "2": "GND"}, "Entrada"),
    # --- salidas ---
    ("U2", "ULN2003ADR", "Transistor_Array:ULN2003", "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
     {"1": "IN1", "2": "IN2", "3": "IN3", "4": "IN4", "5": "IN5", "6": "IN6", "7": "IN7", "8": "GND", "9": "V24",
      "16": "Q1", "15": "Q2", "14": "Q3", "13": "Q4", "12": "Q5", "11": "Q6", "10": "Q7"},
     "7 salidas a GND, 50 V, 300 mA c/u (700 mA en total); diodos de bobina a +24 V"),
    ("J5", "Q1-Q3", "Connector:Screw_Terminal_01x03", MKDS3 % (3, 3), {"1": "Q1", "2": "Q2", "3": "Q3"}, "Salidas 1-3"),
    ("J6", "Q4-Q6", "Connector:Screw_Terminal_01x03", MKDS3 % (3, 3), {"1": "Q4", "2": "Q5", "3": "Q6"}, "Salidas 4-6"),
    ("J7", "Q7 +24 +24", "Connector:Screw_Terminal_01x03", MKDS3 % (3, 3), {"1": "Q7", "2": "V24", "3": "V24"},
     "Salida 7 y +24 V para las cargas"),
    ("TP1", "24V", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "V24"}, "Prueba: 24 V"),
    ("TP2", "GND", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "GND"}, "Prueba: tierra"),
]
QX = [16.0, 21.08, 26.16, 33.0, 38.08, 43.16, 50.0]     # x de cada borne Q1..Q7
for k in range(1, 8):
    C_ += [("RL%d" % k, "10k", R, R06, {"1": "V24", "2": "LA%d" % k}, "LED de la salida %d (2 mA)" % k),
           ("DL%d" % k, "VERDE", "Device:LED", "LED_SMD:LED_0603_1608Metric", {"1": "Q%d" % k, "2": "LA%d" % k},
            "Salida %d activa" % k)]

W, H = 72.0, 56.0
RADIO_ESQUINA = 2.0
HOLES = [(3.5, 3.5), (68.5, 3.5), (68.5, 38.5)]
YT = 49.8
POS = {
    "J1": (14.0, 3.6, 180), "J2": (58.0, 3.6, 180), "J3": (30.0, 3.5, 90),
    "U1": (24.0, 16.0, 0), "C1": (24.0, 21.0, 0),
    "JP1": (13.0, 11.0, 0), "JP2": (13.0, 14.5, 0), "RA1": (13.0, 18.0, 0), "RA2": (13.0, 20.5, 0),
    "R8": (60.0, 14.0, 0), "D10": (60.0, 17.0, 0),
    "J4": (3.6, YT, 0), "F1": (5.0, 38.0, 90), "D1": (5.0, 29.5, 90), "D2": (10.0, 29.0, 90), "C2": (10.0, 37.4, 90),
    "U2": (42.0, 20.0, 0),
    "J5": (16.0, YT, 0), "J6": (33.0, YT, 0), "J7": (50.0, YT, 0),
    "TP1": (64.0, 24.0, 0), "TP2": (64.0, 28.0, 0),
}
for k, x in enumerate(QX, start=1):
    POS["DL%d" % k] = (x, 39.6, 90)
    POS["RL%d" % k] = (x, 35.6, 90)

NETCLASS = {"Media": (0.6, 0.2, ["VIN_RAW", "VF", "V24"] + ["Q%d" % k for k in range(1, 8)])}
SILK = [
    ("+24", 3.6, 45.6, 0.9, "F"), ("0V", 8.68, 45.6, 0.9, "F"),
    ("Q1", 16.0, 45.6, 0.9, "F"), ("Q2", 21.08, 45.6, 0.9, "F"), ("Q3", 26.16, 45.6, 0.9, "F"),
    ("Q4", 33.0, 45.6, 0.9, "F"), ("Q5", 38.08, 45.6, 0.9, "F"), ("Q6", 43.16, 45.6, 0.9, "F"),
    ("Q7", 50.0, 45.6, 0.9, "F"), ("+24", 55.08, 45.6, 0.9, "F"), ("+24", 60.16, 45.6, 0.9, "F"),
    ("AP OUTPUT", 34.0, 28.0, 1.5, "F"),
    ("RUN", 64.0, 17.0, 0.9, "F"), ("ENTRA", 14.0, 7.6, 0.8, "F"), ("SIGUE", 58.0, 7.6, 0.8, "F"),
    ("AP ELECTRIC  AP OUTPUT  7 x 24V 300mA", 36.0, 54.8, 1.0, "B"),
    ("Carga entre +24 y Qn. Red: solo con contactor", 36.0, 52.8, 0.8, "B"),
    ("Dirección: JP1 +1  JP2 +2  (0x20-0x23)", 36.0, 31.0, 0.8, "B"),
]
FLAGS = [("VIN_RAW", 20.32, 20.32), ("GND", 35.56, 20.32), ("V24", 50.8, 20.32), ("3V3", 66.04, 20.32),
         ("VF", 81.28, 20.32)]
NOTES = [(150.0, 15.0, "AP ELECTRIC · AP OUTPUT: TCA9554 (I2C 0x20-0x23) + ULN2003, 7 salidas de 24 V DC.\n"
                       "3V3 y GND llegan por Qwiic desde el programador. La red NO entra a esta placa.")]
TITLE = "AP ELECTRIC · AP OUTPUT - 7 salidas de 24 V DC"
SUBTITLES = ["Placa de 2 capas (JLCPCB)", "Bobinas de contactor, relevadores de interfaz, electroválvulas 24 V DC"]
COMPANY = "PCB 72 x 56 mm (4 módulos DIN), 2 capas, 1 oz"
COSTURA = 5.0
PAPER = "A3"
OCULTAR_REF = ("J1", "J2", "J4", "J5", "J6", "J7")

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
