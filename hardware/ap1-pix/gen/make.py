"""LetreroLab AP-1 PIX: módulo de pixeles del ecosistema AP-1 (tiras y letreros direccionables WS2812/SK6812/WS2815).

Misma medida (88 x 56 mm), mismo zócalo 2x8, mismos agujeros y misma memoria que la BASE: el mismo PROGRAMADOR se
enclava encima y cabe en el mismo gabinete. El programa lo reconoce por su memoria ("LL-PIX").

- Entrada 5-24 V DC hasta 15 A: fusible mini de auto (ATM), protección de polaridad con MOSFET de nivel lógico
  (funciona desde 5 V), supresor SMBJ26A y medidor INA238 con shunt de 1 mOhm: el programa limita el brillo para no
  pasar de la corriente configurada (como el "ABL" de WLED, pero medido de verdad).
- 4 salidas de pixeles con conector JST VH de 3 patas (+V con fusible propio de 3 A, DATOS, GND).
- Datos: PWM 1-4 del programador -> buffer 74HCT125 alimentado a 5 V -> 100 Ohm -> conector. Señal de 5 V limpia aunque
  la tira sea de 12 o 24 V y el cable mida varios metros.
- Fuente de 5 V (LMR16006) para el buffer; el programador toma la entrada directa (acepta 5-26 V).

    bash ../tools/rutear.sh ap1-pix AP1_Pixel
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import placa  # noqa: E402
import conectores  # noqa: E402

PROJECT = "AP1_Pixel"
NS = uuid.UUID("5d8e2a14-3c6f-4b7a-9d0e-1f2a3b4c5d6f")
ROOT_UUID = "d1e2f3a4-b5c6-4d7e-8f90-a1b2c3d4e5f6"
R06, C06, C12 = "Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_1206_3216Metric"
TDSON = "Package_TO_SOT_SMD:TDSON-8-1"
SMA = "Diode_SMD:D_SMA"
R, C, CP = "Device:R", "Device:C", "Device:C_Polarized"

C_ = [
    # --- entrada, protección y medición ---
    ("J1", "ENTRADA 5-24V", conectores.SYM[4], conectores.VH4, {"1": "VIN_RAW", "2": "VIN_RAW", "3": "GNDIN", "4": "GNDIN"},
     "Entrada 5-24 V DC (+ / -), hasta 15 A"),
    ("F1", "MINI 15A", "Device:Fuse", "Fuse:Fuseholder_Blade_Mini_Keystone_3568", {"1": "VIN_RAW", "2": "VF"},
     "Fusible mini de auto (ATM): 15 A máximo; se cambia sin soldar"),
    ("RS1", "1mR 2512 2W", "Device:R_Shunt", "LetreroLab:R_2512_Kelvin_NetTie",
     {"1": "VIN", "2": "ISN", "3": "ISP", "4": "VF"}, "Shunt de 1 mOhm con sensado Kelvin (igual que la base)"),
    ("U1", "INA238", "Sensor_Energy:INA238", "Package_SO:VSSOP-10_3x3mm_P0.5mm",
     {"1": "GND", "2": "GND", "3": "ALERT", "4": "SDA", "5": "SCL", "6": "3V3", "7": "GND", "8": "ISN", "9": "ISN",
      "10": "ISP"}, "Medidor V/A/W (I2C 0x40): limita el brillo por corriente medida"),
    ("C4", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo INA238"),
    ("QR1", "BSC028N06LS3", "Transistor_FET:BSC028N06LS3", TDSON,
     {"1": "GND", "2": "GND", "3": "GND", "4": "GREV", "5": "GNDIN"},
     "Polaridad invertida en el negativo: MOSFET de nivel lógico, conduce bien desde 5 V"),
    ("RG0", "10k", R, R06, {"1": "VF", "2": "GREV"}, "Compuerta de la protección"),
    ("DZ1", "MMSZ5242B 12V", "Device:D_Zener", "Diode_SMD:D_SOD-123", {"1": "GREV", "2": "GND"},
     "Limita la compuerta a 12 V"),
    ("D1", "SMBJ26A", "Device:D_TVS", "Diode_SMD:D_SMB", {"1": "VIN", "2": "GND"}, "Supresor de picos"),
    ("C1", "330uF 50V", CP, "Capacitor_SMD:CP_Elec_10x10.5", {"1": "VIN", "2": "GND"},
     "Reserva para los picos de corriente de los pixeles"),
    ("C2", "10uF 50V", C, C12, {"1": "VIN", "2": "GND"}, "Desacoplo cerámico de +V"),
    ("C3", "10uF 50V", C, C12, {"1": "VIN", "2": "GND"}, "Desacoplo cerámico de +V"),
    # --- fuente de 5 V para el buffer ---
    ("U2", "LMR16006XDDC", "Regulator_Switching:LMR16006YQ", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "BST", "2": "GND", "3": "FB", "4": "VIN", "5": "VIN", "6": "SW"},
     "Buck 60 V a 5 V; con entrada de 5 V pasa casi directo (el buffer aguanta 4.5-5.5 V)"),
    ("L1", "47uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR4030S", {"1": "V5", "2": "SW"}, "Bobina del buck"),
    ("D7", "SS210", "Device:D_Schottky", SMA, {"1": "SW", "2": "GND"}, "Rueda libre del buck"),
    ("C5", "100nF", C, C06, {"1": "BST", "2": "SW"}, "Bootstrap"),
    ("C6", "10uF 50V", C, C12, {"1": "VIN", "2": "GND"}, "Entrada del buck"),
    ("C7", "22uF 25V", C, C12, {"1": "V5", "2": "GND"}, "Salida 5 V"),
    ("RB1", "56k", R, R06, {"1": "V5", "2": "FB"}, "Divisor: 0.765 V x 6.6 = 5.05 V"),
    ("RB2", "10k", R, R06, {"1": "FB", "2": "GND"}, "Divisor"),
    # --- buffer de datos ---
    ("U3", "74HCT125D", "74xx:74LS125", "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
     {"1": "GND", "2": "PWM1", "3": "DB1", "4": "GND", "5": "PWM2", "6": "DB2", "7": "GND",
      "8": "DB3", "9": "PWM3", "10": "GND", "11": "DB4", "12": "PWM4", "13": "GND", "14": "V5"},
     "Buffer 3.3 V -> 5 V (entradas TTL) para los datos de los pixeles"),
    ("C8", "100nF", C, C06, {"1": "V5", "2": "GND"}, "Desacoplo del buffer"),
    # --- identidad y conector del programador ---
    ("U4", "M24C02-WMN6TP", "Memory_EEPROM:M24C02-WMN", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "GND", "2": "GND", "3": "GND", "4": "GND", "5": "SDA", "6": "SCL", "7": "GND", "8": "3V3"},
     "Identidad del módulo: \"LL-PIX\", serie, horas y número de LED por salida (I2C 0x50)"),
    ("C10", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo EEPROM"),
    ("J7", "PROGRAMADOR", "Connector_Generic:Conn_02x08_Odd_Even",
     "Connector_PinSocket_2.54mm:PinSocket_2x08_P2.54mm_Vertical",
     {"1": "VIN", "2": "VIN", "3": "GND", "4": "GND", "5": "PWM1", "6": "PWM2", "7": "PWM3", "8": "PWM4",
      "9": None, "10": None, "11": "SDA", "12": "SCL", "13": "ALERT", "14": None, "15": "3V3", "16": "GND"},
     "Zócalo del programador AP-1: aquí las patas 1-2 llevan la entrada directa (5-24 V)"),
    ("TP1", "VIN", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "VIN"}, "Prueba: entrada medida"),
    ("TP2", "5V", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "V5"}, "Prueba: 5 V del buffer"),
    ("TP3", "GND", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "GND"}, "Prueba: tierra"),
]
SAL_X = (20.0, 35.5, 51.0, 66.5)              # pata 1 (+V) del borne de cada salida
for k, x in enumerate(SAL_X, start=1):
    C_ += [
        ("J%d" % (k + 1), "PIXELES %d" % k, conectores.SYM[3], conectores.VH3,
         {"1": "VO%d" % k, "2": "DAT%d" % k, "3": "GND"}, "Salida de pixeles %d: +V (con fusible), DATOS, GND" % k),
        ("FO%d" % k, "3A", "Device:Fuse", "Fuse:Fuse_1206_3216Metric", {"1": "VIN", "2": "VO%d" % k},
         "Fusible de la salida %d (3 A); para tiras largas inyectar +V aparte" % k),
        ("RD%d" % k, "100", R, R06, {"1": "DB%d" % k, "2": "DAT%d" % k}, "Resistencia en serie de los datos %d" % k),
    ]

W, H = 88.0, 56.0
RADIO_ESQUINA = 2.0
HOLES = [(3.5, 3.5), (84.5, 39.5), (84.5, 52.5)]     # iguales que la base
YT = 49.8
POS = {
    "J1": (2.6, 50.4, 0), "J7": (47.0, 6.0, 0),
    "F1": (3.5, 28.0, 0), "RS1": (20.7, 29.7, 180), "U1": (17.5, 23.2, 0), "C4": (17.5, 20.4, 0),
    "QR1": (8.7, 39.5, 270), "RG0": (13.0, 35.0, 270), "DZ1": (9.5, 34.6, 0),
    "C1": (29.5, 14.5, 90), "D1": (34.6, 25.0, 90), "C2": (39.5, 40.3, 270), "C3": (56.0, 40.3, 270),
    # fuente de 5 V: misma ubicación que la de 12 V de la base
    "U2": (11.0, 9.0, 0), "L1": (11.0, 4.0, 0), "C5": (7.8, 7.8, 90), "D7": (15.2, 5.0, 90), "C6": (15.2, 11.0, 90),
    "C7": (4.6, 10.4, 180), "RB1": (5.0, 12.5, 0), "RB2": (9.6, 12.4, 0),
    "U3": (56.0, 24.0, 0), "C8": (60.5, 18.5, 0),
    "RD1": (61.8, 22.0, 0), "RD2": (61.8, 23.8, 0), "RD3": (61.8, 25.6, 0), "RD4": (61.8, 27.4, 0),
    "U4": (57.0, 11.5, 0), "C10": (57.0, 15.8, 0),
    "TP1": (40.0, 31.0, 0), "TP2": (2.6, 16.0, 0), "TP3": (44.0, 31.0, 0),
}
for k, x in enumerate(SAL_X, start=1):
    POS["J%d" % (k + 1)] = (x, 50.4, 0)
    POS["FO%d" % k] = (x, 40.9, 270)          # entrada (VIN) arriba, salida (VOk) abajo

NETCLASS = {
    "Potencia": (2.0, 0.3, ["VIN", "VIN_RAW", "VF", "GNDIN", "VO1", "VO2", "VO3", "VO4"]),
    "Media": (0.6, 0.2, ["V5", "SW"]),
}
POWER_ZONES = [
    ("VIN_RAW", [(0.6, 25.5), (5.6, 25.5), (5.6, 45.6), (8.3, 45.6), (8.3, 52.2), (0.6, 52.2)]),   # J1 patas 1-2
    ("VF", [(11.6, 26.4), (18.6, 26.4), (18.6, 32.6), (11.6, 32.6)]),
    ("VIN", [(22.9, 18.0), (36.0, 18.0), (36.0, 33.4), (72.0, 33.4), (72.0, 39.6), (13.4, 39.6), (13.4, 33.4),
             (22.9, 33.4)]),
    ("GNDIN", [(6.6, 42.2), (10.8, 42.2), (10.8, 44.0), (16.4, 44.0), (16.4, 52.2), (8.9, 52.2), (8.9, 45.0),
               (6.6, 45.0)]),                                                                       # J1 patas 3-4
] + [("VO%d" % k, [(x - 1.4, 42.6), (x + 1.4, 42.6), (x + 1.4, 52.2), (x - 1.4, 52.2)]) for k, x in enumerate(SAL_X, 1)]
KEEPOUT_NETS = ("VIN", "VIN_RAW", "VF", "GNDIN", "VO1", "VO2", "VO3", "VO4")
PRE = [
    ("VIN", 0.6, [(36.0, 30.0), (40.5, 30.0), (40.5, 3.4), (44.46, 3.4), (44.46, 6.0)]),   # entrada al programador
    ("VIN", 0.5, [(22.9, 20.0), (17.2, 14.0), (13.2, 12.4), (12.1, 11.3), (12.1, 9.0)]),  # entrada del buck
    ("VIN", 0.6, [(44.46, 6.0), (47.0, 6.0)]),                                              # patas 1 y 2 del zócalo
    ("VF", 0.5, [(13.0, 32.3), (13.0, 34.18)]),                                             # compuerta de la protección
]
SIN_COBRE = [[(72.5, 0.3), (87.7, 0.3), (87.7, 30.5), (72.5, 30.5)]]     # bajo la antena del programador

SILK = [
    ("+ +  - -", 8.5, 45.0, 0.9, "F"),
    ("LetreroLab AP-1 PIX  5-24V", 44.0, 54.8, 1.0, "B"),
    ("Tiras largas: inyectar +V desde la fuente", 30.0, 2.0, 0.8, "B"),
]
for k, x in enumerate(SAL_X, start=1):
    SILK += [("+V", x, 45.0, 0.9, "F"), ("D%d" % k, x + 3.96, 45.0, 0.9, "F"), ("-", x + 7.92, 45.0, 1.2, "F")]
FLAGS = [("VIN_RAW", 20.32, 20.32), ("GND", 35.56, 20.32), ("VIN", 50.8, 20.32), ("GNDIN", 66.04, 20.32),
         ("V5", 81.28, 20.32), ("3V3", 96.52, 20.32), ("VF", 111.76, 20.32)]
NOTES = [(150.0, 15.0, "LetreroLab AP-1 PIX: 4 salidas de pixeles (+V con fusible, DATOS a 5 V, GND).\n"
                       "I2C: INA238 0x40, M24C02 0x50 (modelo LL-PIX). 3V3 lo da el programador por J7.")]
TITLE = "LetreroLab AP-1 PIX - módulo de pixeles direccionables"
SUBTITLES = ["Placa de 2 capas para ensamble en fábrica (JLCPCB)", "5-24 V DC, 4 salidas WS2812/SK6812/WS2815"]
COMPANY = "PCB 88 x 56 mm, 2 capas, cobre 2 oz"
COSTURA = 5.0
PAPER = "A2"
OCULTAR_REF = ("J1", "J2", "J3", "J4", "J5")

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
