"""LetreroLab AP-1 DMX: módulo DMX512 del ecosistema AP-1 (hecho a partir de ap1-plantilla).

El programador manda un universo DMX512 (512 canales, 250 kbit/s, unos 30 cuadros por segundo) por RS-485:
- reflectores RGB/RGBW, barras de LED, cabezas móviles y decodificadores DMX para tiras;
- atenuadores DMX de 1 canal.
Cada equipo DMX se maneja como un "pixel": los mismos 10 modos, colores, horarios, app y Home Assistant.

Circuito:
- Entrada 12-24 V protegida y fuente de 12 V para el programador (igual que la plantilla).
- U3 SP3485 (3.3 V): DI = PWM1 (TX de UART1), RO = PWM2 (por 1k), DE = PWM3; /RE a GND, así el receptor regresa el eco
  de lo que se manda y el programa reconoce solo el módulo la primera vez.
- D4 SM712: protección contra descargas y picos en A/B (-7 V / +12 V, el rango de RS-485).
- R2 120 ohm + JP1 (puente de soldadura, abierto): terminación, solo si el módulo queda al final de la línea.
- J2 borne de 3 polos con el orden del XLR de DMX: 1 GND (malla), 2 DATOS- (B), 3 DATOS+ (A).
- D5 LED verde: parpadea mientras se transmite (AUX).
- Memoria M24C02: modelo "LL-DMX", dirección DMX, canales por equipo y cantidad de equipos.

Seguridad: la línea DMX es de baja tensión (SELV). No va aislada: comparte GND con la fuente de 12-24 V, como la mayoría
de los controladores DMX sencillos. Si los equipos DMX tienen su propia fuente lejos, usar un divisor/repetidor DMX aislado.
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import placa  # noqa: E402

PROJECT = "AP1_DMX"
NS = uuid.UUID("d9101cc6-dde9-4f33-bb0d-f1c999bc2753")
ROOT_UUID = "62f188a7-63eb-44f5-8bc7-e7ef4c7c7873"
R06, C06, C12 = "Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_1206_3216Metric"
MKDS3 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-%d-5.08_1x0%d_P5.08mm_Horizontal"
SMA = "Diode_SMD:D_SMA"
R, C = "Device:R", "Device:C"

# señales del conector LL (J7)
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
     "Connector_PinSocket_2.54mm:PinSocket_2x08_P2.54mm_Vertical",
     dict(LL, **{"8": None, "9": None, "10": None, "13": None}), "Zócalo del programador AP-1 (PWM4, CTRL 1-2 y ALERTA sin usar)"),
    ("TP1", "VIN", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "VIN"}, "Prueba: entrada"),
    ("TP2", "12V", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "V12"}, "Prueba: 12 V"),
    ("TP3", "3V3", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "3V3"}, "Prueba: 3.3 V"),
    ("TP4", "GND", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "GND"}, "Prueba: tierra"),
    # --- DMX512 ---
    ("U3", "SP3485EN", "Interface_UART:SP3485EN", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "RO", "2": "GND", "3": "PWM3", "4": "PWM1", "5": "GND", "6": "DMXA", "7": "DMXB", "8": "3V3"},
     "Transceptor RS-485 de 3.3 V (DE = PWM3; /RE fijo: eco para reconocer el módulo)"),
    ("C7", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo del transceptor"),
    ("R1", "1k", R, R06, {"1": "RO", "2": "PWM2"}, "Eco a PWM2: limita la corriente si el programador aún tiene la pata como salida"),
    ("D4", "SM712", "Diode:SM712_SOT23", "Package_TO_SOT_SMD:SOT-23", {"1": "DMXA", "2": "DMXB", "3": "GND"},
     "Protección de la línea (-7 V / +12 V)"),
    ("R2", "120", R, "Resistor_SMD:R_1206_3216Metric", {"1": "DMXA", "2": "TERM"}, "Terminación de la línea DMX"),
    ("JP1", "TERMINACION", "Jumper:SolderJumper_2_Open", "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
     {"1": "TERM", "2": "DMXB"}, "Cerrar con soldadura solo si este módulo queda al final de la línea"),
    ("J2", "DMX", "Connector:Screw_Terminal_01x03", MKDS3 % (3, 3), {"1": "GND", "2": "DMXB", "3": "DMXA"},
     "Salida DMX: 1 GND/malla, 2 DATOS- (B), 3 DATOS+ (A), como las patas del XLR"),
    ("R3", "1k", R, R06, {"1": "AUX", "2": "LEDA"}, "LED de actividad"),
    ("D5", "VERDE", "Device:LED", "LED_SMD:LED_0603_1608Metric", {"1": "GND", "2": "LEDA"}, "Parpadea mientras se transmite DMX"),
]

W, H = 88.0, 56.0
RADIO_ESQUINA = 2.0
HOLES = [(3.5, 3.5), (84.5, 39.5), (84.5, 52.5)]
YT = 49.8
POS = {
    "J1": (3.6, YT, 0), "J7": (47.0, 6.0, 0),
    "F1": (15.0, 43.2, 0), "D1": (21.5, 43.2, 0), "D2": (29.0, 43.2, 0), "C1": (35.0, 42.8, 90), "C2": (38.0, 42.8, 90),
    "U2": (11.0, 9.0, 0), "L1": (11.0, 4.0, 0), "C3": (7.8, 7.8, 90), "D3": (15.2, 5.0, 90), "C4": (15.2, 11.0, 90),
    "C5": (4.6, 10.4, 180), "RB1": (5.0, 12.5, 0), "RB2": (9.6, 12.4, 0),
    "U1": (57.0, 12.0, 0), "C6": (57.0, 16.4, 0),
    "TP1": (41.0, 41.0, 0), "TP2": (20.0, 6.0, 0), "TP3": (60.0, 20.0, 0), "TP4": (64.0, 20.0, 0),
    "J2": (60.0, YT, 0), "U3": (62.0, 36.0, 0), "C7": (62.0, 31.4, 0), "R1": (56.0, 33.0, 90),
    "D4": (70.0, 40.5, 0), "R2": (54.0, 41.0, 0), "JP1": (54.0, 44.2, 0),
    "R3": (76.0, 43.0, 0), "D5": (76.0, 46.0, 0),
}
SOLO_PLACA = []

NETCLASS = {"Media": (0.6, 0.2, ["VIN", "VIN_RAW", "VF", "V12", "SW"])}
PRE = [
    ("V12", 0.6, [(9.5, 2.6), (9.5, 1.1), (42.0, 1.1), (42.0, 6.0), (44.46, 6.0)]),   # como en la base
    ("V12", 0.6, [(44.46, 6.0), (47.0, 6.0)]),
    ("V12", 0.6, [(20.0, 6.0), (20.0, 1.1)]),                                        # TP2 al tronco
]
SIN_COBRE = [[(72.5, 0.3), (87.7, 0.3), (87.7, 30.5), (72.5, 30.5)]]     # bajo la antena del programador

SILK = [
    ("+", 3.6, 46.0, 1.2, "F"), ("-", 8.68, 46.0, 1.2, "F"),
    ("GND", 60.0, 45.6, 1.0, "F"), ("D-", 65.08, 45.6, 1.0, "F"), ("D+", 70.16, 45.6, 1.0, "F"),
    ("1 GND   2 D-   3 D+", 65.0, 41.8, 0.8, "B"),
    ("DMX", 76.0, 49.2, 1.0, "F"), ("120R", 54.0, 46.4, 0.8, "F"),
    ("LetreroLab AP-1 DMX512  12-24V", 44.0, 54.8, 1.0, "B"),
    ("JP1 cerrado = terminación 120 ohm (fin de línea)", 44.0, 52.8, 0.8, "B"),
]
FLAGS = [("VIN_RAW", 20.32, 20.32), ("GND", 35.56, 20.32), ("VIN", 50.8, 20.32), ("V12", 66.04, 20.32),
         ("3V3", 81.28, 20.32), ("VF", 96.52, 20.32)]
NOTES = [(150.0, 15.0, "LetreroLab AP-1 DMX512: el programador manda DMX por UART1 (PWM1) a 250 kbit/s.\n"
                       "/RE a GND: el eco por RO (PWM2) sirve para reconocer el módulo. Línea DMX SELV, no aislada.")]
TITLE = "LetreroLab AP-1 DMX512 - módulo para equipos DMX"
SUBTITLES = ["Placa de 2 capas (JLCPCB)", "Reflectores RGB/RGBW, barras y atenuadores DMX"]
COMPANY = "PCB 88 x 56 mm, 2 capas, 1 oz"
COSTURA = 5.0
PAPER = "A3"
OCULTAR_REF = ("J2",)

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
