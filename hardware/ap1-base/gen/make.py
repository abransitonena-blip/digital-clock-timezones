"""LetreroLab AP-1 BASE universal: placa de potencia para focos, tiras y letreros (4 capas, ensamble en fábrica).

Sobre ella se enclava el PROGRAMADOR AP-1 (conector 2x8 + tornillo). La base no tiene microcontrolador: es la misma
para todos los modelos; lo que cambia por modelo es la placa de LEDs/focos y la configuración guardada en su memoria.

- Entrada 12-24 V DC hasta 20 A: fusible mini de auto (ATM), protección de polaridad sin pérdidas (MOSFET de 1.6 mOhm),
  TVS, medidor INA238 con shunt Kelvin de 1 mOhm (V, A, W, kWh y alerta por sobrecorriente).
- 4 canales de 8 A (MOSFET BSC028N06LS3 + driver UCC27524) para tiras, letreros y RGBW.
- 2 canales de CORRIENTE CONSTANTE (AL8860, 1 A, hasta 40 V): focos y LED de potencia sin resistencias; atenuables.
- Salida AUX de 12 V / 0.3 A para relevador o contactor externo (focos de 127/240 V fuera de la placa) o ventilador.
- Fuente conmutada de 60 V a 12 V (LMR16006 + diodo Schottky) para drivers, AUX y programador.
- Temperatura (TMP1075) junto a los MOSFET y memoria de identidad AT24CS02 (número de serie único de fábrica).

    bash ../tools/rutear.sh ap1-base     (placa, Freerouting en 3 pasadas, planos, ERC/DRC)
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import placa  # noqa: E402

PROJECT = "AP1_Base"
NS = uuid.UUID("3f1c9a52-6d7e-4b8a-9e0f-1a2b3c4d5e61")
ROOT_UUID = "b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e"
R06, C06, C12 = "Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_1206_3216Metric"
R12 = "Resistor_SMD:R_1206_3216Metric"
TDSON = "Package_TO_SOT_SMD:TDSON-8-1"
MKDS3 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-%d-5.08_1x0%d_P5.08mm_Horizontal"
PT15 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-%d-3.5-H_1x0%d_P3.50mm_Horizontal"
R, C, CP = "Device:R", "Device:C", "Device:C_Polarized"
FET = "Transistor_FET:BSC028N06LS3"
SMA = "Diode_SMD:D_SMA"

C_ = [
    # --- entrada, protección y medición ---
    ("J1", "ENTRADA 12-24V", "Connector:Screw_Terminal_01x02", MKDS3 % (2, 2), {"1": "VIN_RAW", "2": "GNDIN"},
     "Entrada 12-24 V DC (+ / -), hasta 20 A"),
    ("F1", "MINI 20A", "Device:Fuse", "Fuse:Fuseholder_Blade_Mini_Keystone_3568", {"1": "VIN_RAW", "2": "VF"},
     "Fusible mini de auto (ATM): 20 A tiras, 5-10 A letreros; se cambia sin soldar"),
    ("RS1", "1mR 2512 Kelvin", "Device:R_Shunt", "Resistor_SMD:R_Shunt_Vishay_WSK2512_6332Metric_T1.19mm",
     {"1": "VIN", "2": "ISN", "3": "ISP", "4": "VF"}, "Shunt de 1 mOhm con sensado Kelvin"),
    ("U1", "INA238", "Sensor_Energy:INA238", "Package_SO:VSSOP-10_3x3mm_P0.5mm",
     {"1": "GND", "2": "GND", "3": "ALERT", "4": "SDA", "5": "SCL", "6": "3V3", "7": "GND", "8": "ISN", "9": "ISN",
      "10": "ISP"}, "Medidor V/A/W hasta 85 V (I2C 0x40); alerta por sobrecorriente y sobrevoltaje"),
    ("C4", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo INA238"),
    ("QR1", "BSC016N06NS", "Transistor_FET:BSC028N06LS3", TDSON,
     {"1": "GND", "2": "GND", "3": "GND", "4": "GREV", "5": "GNDIN"},
     "Polaridad invertida sin pérdidas en el negativo: 60 V, 1.6 mOhm (0.6 W a 20 A)"),
    ("RG0", "10k", R, R06, {"1": "VF", "2": "GREV"}, "Compuerta de la protección"),
    ("DZ1", "MMSZ5242B 12V", "Device:D_Zener", "Diode_SMD:D_SOD-123", {"1": "GREV", "2": "GND"},
     "Limita la compuerta a 12 V"),
    ("D1", "SMBJ33A", "Device:D_TVS", "Diode_SMD:D_SMB", {"1": "VIN", "2": "GND"}, "Supresor de picos"),
    ("C1", "330uF 50V", CP, "Capacitor_SMD:CP_Elec_10x10.5", {"1": "VIN", "2": "GND"},
     "Filtro de entrada (105 C, bajo ESR, larga vida)"),
    ("C3", "10uF 50V", C, C12, {"1": "VIN", "2": "GND"}, "Desacoplo cerámico de +V junto a J3"),
    ("C13", "10uF 50V", C, C12, {"1": "VIN", "2": "GND"}, "Desacoplo cerámico de +V junto a J3"),
    ("J3", "+V SALIDA", "Connector:Screw_Terminal_01x02", MKDS3 % (2, 2), {"1": "VIN", "2": "VIN"},
     "+12/24 V común de tiras y letreros (2 polos)"),
    ("TP1", "VIN", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "VIN"}, "Prueba: entrada medida"),
    # --- fuente conmutada 12 V ---
    ("U2", "LMR16006XDDC", "Regulator_Switching:LMR16006YQ", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "BST2", "2": "GND", "3": "FB2", "4": "VIN", "5": "VIN", "6": "SW2"},
     "Buck 60 V / 0.6 A a 12 V (no síncrono: lleva diodo D7)"),
    ("L1", "47uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR4030S", {"1": "V12", "2": "SW2"}, "Bobina del buck"),
    ("D7", "SS210", "Device:D_Schottky", SMA, {"1": "SW2", "2": "GND"}, "Diodo de rueda libre del buck (100 V, 2 A)"),
    ("C5", "100nF", C, C06, {"1": "BST2", "2": "SW2"}, "Bootstrap"),
    ("C6", "10uF 50V", C, C12, {"1": "VIN", "2": "GND"}, "Entrada del buck"),
    ("C7", "22uF 25V", C, C12, {"1": "V12", "2": "GND"}, "Salida 12 V"),
    ("RF1", "150k", R, R06, {"1": "V12", "2": "FB2"}, "Divisor: 0.765 V x 16 = 12.2 V"),
    ("RF2", "10k", R, R06, {"1": "FB2", "2": "GND"}, "Divisor"),
    ("TP2", "12V", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "V12"}, "Prueba: 12 V"),
    # --- corriente constante (focos) ---
    ("F2", "3A", "Device:Fuse", "Fuse:Fuse_1206_3216Metric", {"1": "VCC", "2": "VIN"},
     "Fusible propio de los canales de corriente constante"),
    ("J5", "FOCOS CC", "Connector:Screw_Terminal_01x04", PT15 % (4, 4),
     {"1": "LEDA1", "2": "LEDK1", "3": "LEDA2", "4": "LEDK2"},
     "Salidas de corriente constante: + y - de cada foco (flotantes: no unir a tierra)"),
]
for k, (u, l, d, rs, c, rc) in enumerate((("U6", "L2", "D2", "RSC1", "C11", "RC1"),
                                          ("U7", "L3", "D3", "RSC2", "C12", "RC2")), start=1):
    C_ += [
        (u, "AL8860MP", "Driver_LED:AL8860MP", "Package_SO:MSOP-8-1EP_3x3mm_P0.65mm_EP1.5x1.8mm",
         {"1": "LEDA%d" % k, "2": "GND", "3": "GND", "4": "CC%d" % k, "5": "SWC%d" % k, "6": "SWC%d" % k, "7": None,
          "8": "VCC", "9": "GND"}, "Driver de corriente constante %d (40 V, 1.5 A máx.)" % k),
        (rs, "0R1", R, R12, {"1": "VCC", "2": "LEDA%d" % k},
         "Fija la corriente: 0.1 V / R (0.1 = 1 A, 0.15 = 0.67 A, 0.33 = 0.3 A)"),
        (l, "47uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR6045S", {"1": "LEDK%d" % k, "2": "SWC%d" % k},
         "Bobina CC %d (Isat > 1.5 A)" % k),
        (d, "SS34", "Device:D_Schottky", SMA, {"1": "VCC", "2": "SWC%d" % k}, "Rueda libre CC %d" % k),
        (c, "4.7uF 50V", C, C12, {"1": "VCC", "2": "GND"}, "Entrada CC %d" % k),
        (rc, "2.2k", R, R06, {"1": "CC%d" % k, "2": "GND"}, "Apagado sin programador (CTRL < 0.2 V)"),
    ]
C_ += [
    # --- 4 canales de potencia ---
    ("U3", "UCC27524D", "Driver_FET:UCC27524D", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": None, "2": "PWM1", "3": "GND", "4": "PWM2", "5": "GO2", "6": "V12", "7": "GO1", "8": None}, "Driver 1-2"),
    ("U4", "UCC27524D", "Driver_FET:UCC27524D", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": None, "2": "PWM3", "3": "GND", "4": "PWM4", "5": "GO4", "6": "V12", "7": "GO3", "8": None}, "Driver 3-4"),
    ("C8", "1uF 25V", C, C06, {"1": "V12", "2": "GND"}, "Desacoplo driver 1-2"),
    ("C9", "1uF 25V", C, C06, {"1": "V12", "2": "GND"}, "Desacoplo driver 3-4"),
    ("J4", "CANALES", "Connector:Screw_Terminal_01x04", MKDS3 % (4, 4),
     {"1": "CH1", "2": "CH2", "3": "CH3", "4": "CH4"}, "Negativo conmutado de cada canal (8 A c/u)"),
]
for n in range(1, 5):
    C_ += [
        ("Q%d" % n, "BSC028N06LS3", FET, TDSON, {"1": "GND", "2": "GND", "3": "GND", "4": "G%d" % n, "5": "CH%d" % n},
         "MOSFET canal %d (60 V, 2.8 mOhm)" % n),
        ("RG%d" % n, "4.7", R, R06, {"1": "GO%d" % n, "2": "G%d" % n}, "Compuerta canal %d" % n),
        ("RP%d" % n, "10k", R, R06, {"1": "G%d" % n, "2": "GND"}, "Canal %d apagado sin driver" % n),
    ]
C_ += [
    # --- AUX, sensores, identidad, conector del programador ---
    ("Q5", "AO3400A", "Transistor_FET:AO3400A", "Package_TO_SOT_SMD:SOT-23", {"1": "AUX", "2": "GND", "3": "AUXD"},
     "Salida AUX (lado bajo)"),
    ("RAUX", "10k", R, R06, {"1": "AUX", "2": "GND"}, "AUX apagada sin programador (vence el pull-up débil del ESP al arrancar)"),
    ("D4", "SS34", "Device:D_Schottky", SMA, {"1": "V12", "2": "AUXD"}, "Rueda libre de la bobina externa"),
    ("J6", "AUX 12V", "Connector:Screw_Terminal_01x02", PT15 % (2, 2), {"1": "V12", "2": "AUXD"},
     "AUX: +12 V y salida conmutada, máx. 0.3 A (relevador/contactor/ventilador)"),
    ("U8", "TMP1075D", "Sensor_Temperature:TMP1075D", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "SDA", "2": "SCL", "3": "ALERT", "4": "GND", "5": "GND", "6": "GND", "7": "GND", "8": "3V3"},
     "Temperatura junto a los MOSFET (I2C 0x48)"),
    ("C15", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo TMP1075"),
    ("U9", "AT24CS02", "Memory_EEPROM:AT24CS02-STUM", "Package_TO_SOT_SMD:SOT-23-5",
     {"1": "SCL", "2": "GND", "3": "SDA", "4": "3V3", "5": "GND"},
     "Identidad de la base: modelo, calibración y número de serie único (I2C 0x50/0x58)"),
    ("C14", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo EEPROM"),
    ("J7", "PROGRAMADOR", "Connector_Generic:Conn_02x08_Odd_Even",
     "Connector_PinSocket_2.54mm:PinSocket_2x08_P2.54mm_Vertical",
     {"1": "V12", "2": "V12", "3": "GND", "4": "GND", "5": "PWM1", "6": "PWM2", "7": "PWM3", "8": "PWM4",
      "9": "CC1", "10": "CC2", "11": "SDA", "12": "SCL", "13": "ALERT", "14": "AUX", "15": "3V3", "16": "GND"},
     "Zócalo del programador AP-1"),
    ("TP3", "3V3", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "3V3"}, "Prueba: 3.3 V"),
    ("TP4", "GND", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "GND"}, "Prueba: tierra"),
]

W, H = 88.0, 56.0
RADIO_ESQUINA = 2.0
HOLES = [(3.5, 3.5), (84.5, 39.5), (84.5, 52.5)]     # (84.5, 39.5): tornillo del programador
YT = 49.8
QX = (46.1, 53.1, 60.1, 67.1)
POS = {
    "J5": (3.0, YT, 0), "J3": (20.0, YT, 0), "J1": (32.0, YT, 0), "J4": (44.5, YT, 0), "J6": (67.0, YT, 0),
    "J7": (47.0, 6.0, 0),
    "F1": (30.6, 38.0, 90), "RS1": (24.1, 28.6, 0), "U1": (24.1, 23.2, 180), "C4": (24.1, 19.8, 0),
    "C1": (24.0, 13.0, 0), "C3": (24.0, 33.8, 0), "C13": (24.0, 36.6, 0), "D1": (23.6, 41.0, 0),
    "U2": (11.0, 9.0, 0), "L1": (11.0, 4.0, 0), "C5": (7.8, 7.8, 90), "D7": (15.2, 5.0, 90), "C6": (15.2, 11.0, 90),
    "C7": (4.6, 10.4, 180), "RF1": (5.0, 12.5, 0), "RF2": (9.6, 12.4, 0),
    "U6": (5.0, 17.5, 0), "L2": (12.8, 17.6, 0), "D2": (12.3, 23.0, 0), "RSC1": (4.5, 21.0, 0),
    "C11": (4.5, 24.0, 0), "RC1": (4.5, 26.4, 0),
    "U7": (5.0, 30.0, 0), "L3": (12.8, 30.1, 0), "D3": (12.3, 35.5, 0), "RSC2": (4.5, 33.5, 0),
    "C12": (4.5, 36.5, 0), "RC2": (4.5, 38.9, 0), "F2": (15.6, 40.5, 0),
    "QR1": (39.0, 37.8, 270), "RG0": (39.0, 30.6, 0), "DZ1": (39.5, 27.9, 0),
    "U3": (53.0, 25.5, 0), "U4": (63.6, 25.5, 0), "C8": (57.6, 25.5, 90), "C9": (68.3, 25.5, 90),
    "U8": (58.3, 19.5, 0), "C15": (58.3, 15.0, 0), "U9": (53.0, 12.0, 0), "C14": (53.0, 15.2, 0),
    "Q5": (72.2, 36.0, 0), "RAUX": (71.5, 40.5, 90), "D4": (76.0, 40.0, 90),
    "TP1": (18.2, 33.0, 0), "TP2": (1.9, 12.8, 0), "TP3": (45.0, 28.0, 0), "TP4": (47.8, 28.0, 0),
}
for n, x in enumerate(QX, start=1):
    POS["Q%d" % n] = (x, 37.8, 270)
    POS["RG%d" % n] = (x - 1.6, 30.7, 0)
    POS["RP%d" % n] = (x + 1.6, 30.7, 0)

NETCLASS = {
    "Potencia": (2.0, 0.3, ["VIN", "VIN_RAW", "VF", "GNDIN", "CH1", "CH2", "CH3", "CH4"]),
    "Media": (0.6, 0.2, ["V12", "SW2", "VCC", "SWC1", "SWC2", "LEDA1", "LEDK1", "LEDA2", "LEDK2", "AUXD"]),
}

POWER_ZONES = [
    ("VIN_RAW", [(29.0, 36.6), (35.3, 36.6), (35.3, 52.2), (29.0, 52.2)]),
    ("VF", [(25.7, 26.3), (35.7, 26.3), (35.7, 30.9), (25.7, 30.9)]),
    ("VIN", [(16.9, 11.5), (22.3, 11.5), (22.3, 14.5), (20.4, 14.5), (20.4, 26.3), (25.2, 26.3), (25.2, 31.4),
             (28.3, 31.4), (28.3, 52.2), (16.9, 52.2)]),
    ("GNDIN", [(35.9, 36.4), (41.9, 36.4), (41.9, 41.6), (39.4, 41.6), (39.4, 52.2), (35.9, 52.2)]),
    ("GND", [(37.75, 32.0), (41.7, 32.0), (41.7, 35.3), (37.75, 35.3)]),            # fuentes de QR1
    ("CH1", [(43.9, 36.4), (48.3, 36.4), (48.3, 42.5), (46.2, 44.6), (46.2, 52.2), (42.6, 52.2), (42.6, 42.0),
             (43.9, 41.0)]),
    ("CH2", [(50.9, 36.4), (55.3, 36.4), (55.3, 42.4), (51.4, 46.3), (51.4, 52.2), (46.8, 52.2), (46.8, 45.0),
             (49.4, 42.4), (50.9, 42.4)]),
    ("CH3", [(57.9, 36.4), (62.3, 36.4), (62.3, 42.4), (56.5, 48.2), (56.5, 52.2), (52.0, 52.2), (52.0, 47.0),
             (56.6, 42.4), (57.9, 42.4)]),
    ("CH4", [(64.9, 36.4), (69.3, 36.4), (69.3, 42.4), (61.6, 50.1), (61.6, 52.2), (57.1, 52.2), (57.1, 49.0),
             (63.7, 42.4), (64.9, 42.4)]),
] + [("GND", [(x - 1.1, 32.2), (x + 2.6, 32.2), (x + 2.6, 35.3), (x - 1.1, 35.3)]) for x in QX]
KEEPOUT_NETS = ("VIN", "VIN_RAW", "VF", "GNDIN", "CH1", "CH2", "CH3", "CH4")
VIAS = ([(x, y) for x in (38.4, 39.4, 40.4, 41.2) for y in (32.7, 33.6)]
        + [(x + dx, y) for x in QX for dx in (-0.5, 0.7, 1.9) for y in (32.9, 34.0)]
        + [(26.9, 33.8), (26.9, 36.6), (27.4, 41.0)])
PRE = [
    # sensado Kelvin del shunt hacia el INA238 (fuera de los planos de entrada)
    ("ISP", 0.3, [(27.53, 27.33), (26.9, 25.7), (21.0, 25.7), (21.0, 24.6), (21.9, 24.2)]),
    ("ISN", 0.3, [(20.67, 29.87), (19.2, 29.87)]), ("ISN", 0.3, [(19.2, 29.87), (19.2, 23.45)], "B"),
    ("ISN", 0.3, [(19.2, 23.45), (21.9, 23.45)]), ("ISN", 0.3, [(21.9, 23.2), (21.9, 23.7)]),
    ("VF", 0.6, [(35.4, 30.6), (38.225, 30.6)]),                       # compuerta de la protección
    ("VIN", 0.5, [(17.2, 12.4), (13.2, 12.4), (12.1, 11.3), (12.1, 9.0)]),   # entrada del buck
    ("GND", 0.6, [(25.4, 33.8), (26.9, 33.8)]), ("GND", 0.6, [(25.4, 36.6), (26.9, 36.6)]),
    ("GND", 0.8, [(25.75, 41.0), (27.4, 41.0)]),
    # CTRL de los canales de corriente constante: cruzan la placa por abajo, junto al borde superior
    ("CC2", 0.3, [(44.46, 16.16), (40.2, 16.2)]),
    ("CC1", 0.3, [(47.0, 16.16), (45.73, 14.9), (45.73, 12.35), (41.2, 12.35)]),
    ("CC1", 0.3, [(41.2, 12.35), (41.2, 1.0), (7.6, 1.0), (7.6, 19.45)], "B"),
    ("CC2", 0.3, [(40.2, 16.2), (40.2, 1.8), (8.6, 1.8), (8.6, 29.0)], "B"),
    # bajo cada AL8860 (entre el chip y su resistencia de corriente): la pata SET queda libre hacia arriba
    ("CC1", 0.3, [(7.6, 19.45), (1.3, 19.45), (1.3, 18.47), (2.89, 18.47)]),
    ("CC1", 0.3, [(1.3, 19.45), (1.3, 26.4), (3.675, 26.4)]),
    ("CC2", 0.3, [(8.6, 29.0), (8.6, 32.15), (1.3, 32.15), (1.3, 30.97), (2.89, 30.97)]),
    ("CC2", 0.3, [(1.3, 32.15), (1.3, 38.9), (3.675, 38.9)]),
    # tronco de 12 V del buck al zócalo por el borde superior (lejos del nodo de conmutación)
    ("V12", 0.6, [(9.5, 2.6), (9.5, 1.1), (42.0, 1.1), (42.0, 6.0), (44.46, 6.0)]),
]
PREVIAS = [("ISN", 19.2, 29.87), ("ISN", 19.2, 23.45), ("CC1", 41.2, 12.35), ("CC1", 7.6, 19.45),
           ("CC2", 40.2, 16.2), ("CC2", 8.6, 29.0)]
SIN_COBRE = [[(72.5, 0.3), (87.7, 0.3), (87.7, 30.5), (72.5, 30.5)]]     # bajo la antena del programador
RETORNO = [[(35.5, 29.6), (71.0, 29.6), (71.0, 44.5), (35.5, 44.5)]]   # regreso de los 4 canales hacia QR1

SILK = [
    ("LetreroLab AP-1 BASE", 70.0, 45.0, 1.2, "B"),
    ("+V", 20.0, 46.0, 1.0, "F"), ("+V", 25.08, 46.0, 1.0, "F"),
    ("+", 32.0, 46.0, 1.2, "F"), ("-", 37.08, 46.0, 1.2, "F"),
    ("CH1", 44.5, 46.0, 1.0, "F"), ("CH2", 49.58, 46.0, 1.0, "F"),
    ("CH3", 54.66, 46.0, 1.0, "F"), ("CH4", 59.74, 46.0, 1.0, "F"),
    ("1+", 3.0, 45.6, 0.9, "F"), ("1-", 6.5, 45.6, 0.9, "F"), ("2+", 10.0, 45.6, 0.9, "F"), ("2-", 13.5, 45.6, 0.9, "F"),
    ("FOCOS CC 1A", 8.3, 42.6, 0.9, "F"),
    ("12V", 67.0, 45.6, 0.9, "F"), ("AUX", 70.5, 45.6, 0.9, "F"),
    ("LetreroLab AP-1 BASE universal  12-24V 20A", 44.0, 54.8, 1.0, "B"),
    ("Salidas CC flotantes: no unir a tierra", 20.0, 2.0, 0.9, "B"),
]
FLAGS = [("VIN_RAW", 20.32, 20.32), ("GND", 35.56, 20.32), ("VIN", 50.8, 20.32), ("GNDIN", 66.04, 20.32),
         ("V12", 81.28, 20.32), ("3V3", 96.52, 20.32), ("VF", 111.76, 20.32), ("VCC", 127.0, 20.32)]
NOTES = [(150.0, 15.0, "LetreroLab AP-1 BASE universal: 12-24 V / 20 A, 4 canales de 8 A, 2 canales de corriente "
                       "constante (1 A), AUX 12 V.\nI2C: INA238 0x40, TMP1075 0x48, AT24CS02 0x50 (+0x58 serie). "
                       "3V3 lo da el programador por J7.")]
TITLE = "LetreroLab AP-1 - base universal de potencia"
SUBTITLES = ["Placa de 4 capas (In1/In2 = GND) para ensamble en fábrica (JLCPCB)", "12-24 V DC, 4 x 8 A + 2 x 1 A CC + AUX"]
CAPAS = 4                                 # F.Cu señales+potencia, In1 GND, In2 GND, B.Cu potencia+GND
COSTURA = 5.0                             # vías GND cada 5 mm: une F.Cu/B.Cu con los planos internos
COMPANY = "PCB 88 x 56 mm, 4 capas JLC04161H-7628, externas 2 oz, internas 1 oz"
PAPER = "A2"
MODELOS = {"WSK2512": "R_2512_6332Metric.step"}
OCULTAR_REF = ("J5", "J6")

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
