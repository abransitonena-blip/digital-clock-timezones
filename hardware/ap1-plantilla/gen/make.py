"""LetreroLab AP-1 PLANTILLA: el punto de partida para cualquier módulo nuevo del ecosistema AP-1.

Trae lo que TODO módulo debe tener, ya probado (ERC/DRC 0):
- Medida 88 x 56 mm, esquinas redondeadas, 3 agujeros M3 en (3.5, 3.5), (84.5, 39.5) y (84.5, 52.5).
- Zócalo J7 2x8 para el PROGRAMADOR en (47, 6), con las señales del conector LL (ver ECOSISTEMA.md).
- Zona sin cobre bajo la antena del programador (x 72.5-88, y 0-30.5).
- Entrada 12-24 V protegida (fusible, diodo contra polaridad invertida, supresor) y fuente de 12 V para el programador.
- Memoria de identidad M24C02 (I2C 0x50): el programa lee el modelo y se adapta.

Y para probar ideas antes de diseñar el módulo final:
- J8: conector macho 2x8 con LAS MISMAS SEÑALES que J7 (PWM 1-4, CTRL 1-2, AUX, I2C, ALERTA, 3.3 V, 12 V, GND).
- Área de prototipos de 12 x 10 agujeros metalizados a 2.54 mm (como una placa perforada).

Cómo hacer un módulo nuevo (detalle en ap1-plantilla/LEEME.md):
  1. Copia esta carpeta (p. ej. ap1-dali) y cambia PROJECT, NS y ROOT_UUID (uuid nuevos).
  2. Agrega tus piezas a C_ (referencia, valor, símbolo, huella, {pata: red}, función) y su posición a POS.
  3. Quita J8 y el área de prototipos si no los necesitas (SOLO_PLACA).
  4. bash ../tools/rutear.sh <carpeta> <PROYECTO>   ->   ERC/DRC
  5. python3 ../tools/salidas.py <carpeta> <PROYECTO>   ->   archivos para JLCPCB
  6. En el programa, agrega el modo del módulo: modelo "LL-XXX" en la memoria (orden MODELO LL-XXX).
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import placa  # noqa: E402

PROJECT = "AP1_Plantilla"
NS = uuid.UUID("9b3c6e21-7a4d-4f8b-a1c2-3d4e5f60718a")
ROOT_UUID = "e2f3a4b5-c6d7-4e8f-9a0b-1c2d3e4f5a6b"
R06, C06, C12 = "Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_1206_3216Metric"
MKDS3 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-%d-5.08_1x0%d_P5.08mm_Horizontal"
SMA = "Diode_SMD:D_SMA"
R, C = "Device:R", "Device:C"

# señales del conector LL (iguales en J7 y J8)
LL = {"1": "V12", "2": "V12", "3": "GND", "4": "GND", "5": "PWM1", "6": "PWM2", "7": "PWM3", "8": "PWM4",
      "9": "CC1", "10": "CC2", "11": "SDA", "12": "SCL", "13": "ALERT", "14": "AUX", "15": "3V3", "16": "GND"}

C_ = [
    # --- entrada 12-24 V protegida (igual que el módulo IND) ---
    ("J1", "ENTRADA 12-24V", "Connector:Screw_Terminal_01x02", MKDS3 % (2, 2), {"1": "VIN_RAW", "2": "GND"},
     "Entrada 12-24 V DC (+ / -), máx. 26 V"),
    ("F1", "3A", "Device:Fuse", "Fuse:Fuse_1206_3216Metric", {"1": "VIN_RAW", "2": "VF"}, "Fusible de la placa"),
    ("D1", "SS34", "Device:D_Schottky", SMA, {"1": "VIN", "2": "VF"}, "Polaridad invertida (en serie)"),
    ("D2", "SMBJ26A", "Device:D_TVS", "Diode_SMD:D_SMB", {"1": "VIN", "2": "GND"}, "Supresor de picos"),
    ("C1", "10uF 50V", C, C12, {"1": "VIN", "2": "GND"}, "Entrada"),
    ("C2", "10uF 50V", C, C12, {"1": "VIN", "2": "GND"}, "Entrada"),
    # --- fuente de 12 V para el programador (igual que la base) ---
    ("U2", "LMR16006XDDC", "Regulator_Switching:LMR16006YQ", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "BST", "2": "GND", "3": "FB", "4": "VIN", "5": "VIN", "6": "SW"}, "Buck 60 V a 12 V"),
    ("L1", "47uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR4030S", {"1": "V12", "2": "SW"}, "Bobina del buck"),
    ("D3", "SS210", "Device:D_Schottky", SMA, {"1": "SW", "2": "GND"}, "Rueda libre del buck"),
    ("C3", "100nF", C, C06, {"1": "BST", "2": "SW"}, "Bootstrap"),
    ("C4", "10uF 50V", C, C12, {"1": "VIN", "2": "GND"}, "Entrada del buck"),
    ("C5", "22uF 25V", C, C12, {"1": "V12", "2": "GND"}, "Salida 12 V"),
    ("RB1", "150k", R, R06, {"1": "V12", "2": "FB"}, "Divisor: 0.765 V x 16 = 12.2 V"),
    ("RB2", "10k", R, R06, {"1": "FB", "2": "GND"}, "Divisor"),
    # --- identidad y conectores ---
    ("U1", "M24C02-WMN6TP", "Memory_EEPROM:M24C02-WMN", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "GND", "2": "GND", "3": "GND", "4": "GND", "5": "SDA", "6": "SCL", "7": "GND", "8": "3V3"},
     "Identidad del módulo (I2C 0x50): modelo LL-XXX, serie y horas"),
    ("C6", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo EEPROM"),
    ("J7", "PROGRAMADOR", "Connector_Generic:Conn_02x08_Odd_Even",
     "Connector_PinSocket_2.54mm:PinSocket_2x08_P2.54mm_Vertical", dict(LL), "Zócalo del programador AP-1"),
    ("J8", "SEÑALES LL", "Connector_Generic:Conn_02x08_Odd_Even",
     "Connector_PinHeader_2.54mm:PinHeader_2x08_P2.54mm_Vertical", dict(LL),
     "Las mismas señales del programador para cablear prototipos (pata 1 = 12 V)"),
    ("TP1", "VIN", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "VIN"}, "Prueba: entrada"),
    ("TP2", "12V", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "V12"}, "Prueba: 12 V"),
    ("TP3", "3V3", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "3V3"}, "Prueba: 3.3 V"),
    ("TP4", "GND", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "GND"}, "Prueba: tierra"),
    # --- AQUÍ VAN LAS PIEZAS DEL MÓDULO NUEVO ---
]

W, H = 88.0, 56.0
RADIO_ESQUINA = 2.0
HOLES = [(3.5, 3.5), (84.5, 39.5), (84.5, 52.5)]
YT = 49.8
POS = {
    "J1": (3.6, YT, 0), "J7": (47.0, 6.0, 0), "J8": (60.0, 48.0, 90),
    "F1": (15.0, 43.2, 0), "D1": (21.5, 43.2, 0), "D2": (29.0, 43.2, 0), "C1": (35.0, 42.8, 90), "C2": (38.0, 42.8, 90),
    "U2": (11.0, 9.0, 0), "L1": (11.0, 4.0, 0), "C3": (7.8, 7.8, 90), "D3": (15.2, 5.0, 90), "C4": (15.2, 11.0, 90),
    "C5": (4.6, 10.4, 180), "RB1": (5.0, 12.5, 0), "RB2": (9.6, 12.4, 0),
    "U1": (57.0, 12.0, 0), "C6": (57.0, 16.4, 0),
    "TP1": (41.0, 41.0, 0), "TP2": (20.0, 6.0, 0), "TP3": (60.0, 20.0, 0), "TP4": (64.0, 20.0, 0),
}
SOLO_PLACA = [("PROTO1", "LetreroLab:Prototipo_2.54mm_12x10", 4.0, 15.2, 0)]   # área de prototipos (sin red)

NETCLASS = {"Media": (0.6, 0.2, ["VIN", "VIN_RAW", "VF", "V12", "SW"])}
PRE = [
    ("V12", 0.6, [(9.5, 2.6), (9.5, 1.1), (42.0, 1.1), (42.0, 6.0), (44.46, 6.0)]),   # como en la base
    ("V12", 0.6, [(44.46, 6.0), (47.0, 6.0)]),
    ("V12", 0.6, [(20.0, 6.0), (20.0, 1.1)]),                                        # TP2 al tronco
]
SIN_COBRE = [[(72.5, 0.3), (87.7, 0.3), (87.7, 30.5), (72.5, 30.5)]]     # bajo la antena del programador

SILK = [
    ("+", 3.6, 46.0, 1.2, "F"), ("-", 8.68, 46.0, 1.2, "F"),
    ("PROTOTIPOS 2.54 mm", 18.0, 27.0, 1.0, "B"),
    ("J8: 1-2 12V  3-4,16 GND  5-8 PWM1-4  9-10 CTRL1-2", 62.5, 40.6, 0.8, "F"),
    ("11 SDA  12 SCL  13 ALERTA  14 AUX  15 3V3", 62.5, 42.0, 0.8, "F"),
    ("LetreroLab AP-1 PLANTILLA  12-24V", 44.0, 54.8, 1.0, "B"),
]
FLAGS = [("VIN_RAW", 20.32, 20.32), ("GND", 35.56, 20.32), ("VIN", 50.8, 20.32), ("V12", 66.04, 20.32),
         ("3V3", 81.28, 20.32), ("VF", 96.52, 20.32)]
NOTES = [(150.0, 15.0, "LetreroLab AP-1 PLANTILLA: base para módulos nuevos. J7 = zócalo del programador; "
                       "J8 = las mismas señales para prototipos.\nI2C: M24C02 0x50. 3V3 lo da el programador por J7.")]
TITLE = "LetreroLab AP-1 PLANTILLA - base para módulos nuevos"
SUBTITLES = ["Placa de 2 capas (JLCPCB)", "Copiar esta carpeta para diseñar un módulo nuevo"]
COMPANY = "PCB 88 x 56 mm, 2 capas, 1 oz"
COSTURA = 5.0
PAPER = "A3"
OCULTAR_REF = ("PROTO1",)

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
