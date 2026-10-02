"""LetreroLab AP-1 IND: módulo industrial del ecosistema AP-1 (luminarias de nave, paneles, reflectores y focos de red).

Misma medida (88 x 56 mm), mismo zócalo 2x8, mismos agujeros y misma memoria de identidad que la BASE: el mismo
PROGRAMADOR se enclava encima y cabe en el mismo gabinete. El programa reconoce el módulo por su memoria ("LL-IND").

- 4 salidas 0-10 V AISLADAS para drivers con entrada de atenuación 0-10 V o 1-10 V (campanas de nave, paneles,
  reflectores). PWM -> optoacoplador LTV-217 (3 kV) -> filtro -> LM358 alimentado por un convertidor aislado
  B1212S-1WR3 (1.5 kV). El amplificador da y absorbe corriente: sirve para drivers que la piden y para los que la entregan.
- 2 salidas para la BOBINA de un contactor o relevador de estado sólido de riel DIN (12 o 24 V, como la fuente; 0.5 A).
  Ese contactor (fuera de la placa, instalado por un electricista) enciende y apaga la luz de 127/240 V.
  La red NO entra a esta placa.
- Entrada 12-24 V DC (máx. 26 V): fusible, diodo contra polaridad invertida, supresor SMBJ26A y fuente de 12 V
  (LMR16006) para el programador y el convertidor aislado.
- Franja sin cobre de 3 mm entre el lado de la fuente y el lado aislado (regla de DRC de 2.5 mm).

    bash ../tools/rutear.sh ap1-ind AP1_Industrial
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import placa  # noqa: E402

PROJECT = "AP1_Industrial"
NS = uuid.UUID("7a2e4c11-5b3d-4f6a-8c9e-2d1f0a3b4c5d")
ROOT_UUID = "c4d5e6f7-a8b9-4c0d-9e1f-2a3b4c5d6e7f"
R06, C06, C12 = "Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_1206_3216Metric"
MKDS3 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-%d-5.08_1x0%d_P5.08mm_Horizontal"
PT15 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-%d-3.5-H_1x0%d_P3.50mm_Horizontal"
SMA = "Diode_SMD:D_SMA"
SOIC8 = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
R, C = "Device:R", "Device:C"

C_ = [
    # --- entrada y fuente de 12 V ---
    ("J1", "ENTRADA 12-24V", "Connector:Screw_Terminal_01x02", MKDS3 % (2, 2), {"1": "VIN_RAW", "2": "GND"},
     "Entrada 12-24 V DC (+ / -), máx. 26 V"),
    ("F1", "2A", "Device:Fuse", "Fuse:Fuse_1206_3216Metric", {"1": "VIN_RAW", "2": "VF"}, "Fusible de la placa"),
    ("D1", "SS34", "Device:D_Schottky", SMA, {"1": "VIN", "2": "VF"}, "Polaridad invertida (en serie)"),
    ("D2", "SMBJ26A", "Device:D_TVS", "Diode_SMD:D_SMB", {"1": "VIN", "2": "GND"},
     "Supresor de picos (igual que la base)"),
    ("C1", "10uF 50V", C, C12, {"1": "VIN", "2": "GND"}, "Entrada"),
    ("C2", "10uF 50V", C, C12, {"1": "VIN", "2": "GND"}, "Entrada"),
    ("U1", "LMR16006XDDC", "Regulator_Switching:LMR16006YQ", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "BST", "2": "GND", "3": "FB", "4": "VIN", "5": "VIN", "6": "SW"}, "Buck 60 V a 12 V (como la base)"),
    ("L1", "47uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR4030S", {"1": "V12", "2": "SW"}, "Bobina del buck"),
    ("D3", "SS210", "Device:D_Schottky", SMA, {"1": "SW", "2": "GND"}, "Rueda libre del buck"),
    ("C3", "100nF", C, C06, {"1": "BST", "2": "SW"}, "Bootstrap"),
    ("C4", "10uF 50V", C, C12, {"1": "VIN", "2": "GND"}, "Entrada del buck"),
    ("C5", "22uF 25V", C, C12, {"1": "V12", "2": "GND"}, "Salida 12 V"),
    ("RB1", "150k", R, R06, {"1": "V12", "2": "FB"}, "Divisor: 0.765 V x 16 = 12.2 V"),
    ("RB2", "10k", R, R06, {"1": "FB", "2": "GND"}, "Divisor"),
    # --- contactores (bobina a +V de la entrada) ---
    ("J2", "CONTACTORES", "Connector:Screw_Terminal_01x04", PT15 % (4, 4),
     {"1": "VIN", "2": "K1", "3": "VIN", "4": "K2"}, "Bobina del contactor 1 y 2 (+V y salida conmutada), 0.5 A c/u"),
    ("Q1", "AO3400A", "Transistor_FET:AO3400A", "Package_TO_SOT_SMD:SOT-23", {"1": "AUX", "2": "GND", "3": "K1"},
     "Contactor 1 (sigue al encendido de la luz)"),
    ("Q2", "AO3400A", "Transistor_FET:AO3400A", "Package_TO_SOT_SMD:SOT-23", {"1": "CC1", "2": "GND", "3": "K2"},
     "Contactor 2 (manual u horario)"),
    ("RK1", "10k", R, R06, {"1": "AUX", "2": "GND"}, "Contactor 1 apagado sin programador"),
    ("RK2", "10k", R, R06, {"1": "CC1", "2": "GND"}, "Contactor 2 apagado sin programador"),
    ("D4", "SS34", "Device:D_Schottky", SMA, {"1": "VIN", "2": "K1"}, "Rueda libre de la bobina 1"),
    ("D5", "SS34", "Device:D_Schottky", SMA, {"1": "VIN", "2": "K2"}, "Rueda libre de la bobina 2"),
    # --- lado aislado: convertidor, amplificadores y bornes 0-10 V ---
    ("U2", "B1212S-1WR3", "Converter_DCDC:MEE1S0303SC", "Converter_DCDC:Converter_DCDC_Murata_MEE1SxxxxSC_THT",
     {"1": "GND", "2": "V12", "3": "ISOGND", "4": "ISO12"}, "Convertidor aislado 12 V -> 12 V, 1 W, 1.5 kV (SIP-4)"),
    ("C6", "10uF 25V", C, C12, {"1": "V12", "2": "GND"}, "Entrada del convertidor aislado"),
    ("C7", "10uF 25V", C, C12, {"1": "ISO12", "2": "ISOGND"}, "Salida aislada"),
    ("U3", "LM358DR2G", "Amplifier_Operational:LM2904", SOIC8,
     {"1": "OUT1", "2": "OUT1", "3": "FL1", "4": "ISOGND", "5": "FL2", "6": "OUT2", "7": "OUT2", "8": "ISO12"},
     "Seguidores de los canales 1 y 2 (dan y absorben corriente)"),
    ("U4", "LM358DR2G", "Amplifier_Operational:LM2904", SOIC8,
     {"1": "OUT3", "2": "OUT3", "3": "FL3", "4": "ISOGND", "5": "FL4", "6": "OUT4", "7": "OUT4", "8": "ISO12"},
     "Seguidores de los canales 3 y 4"),
    ("C8", "100nF", C, C06, {"1": "ISO12", "2": "ISOGND"}, "Desacoplo U3"),
    ("C9", "100nF", C, C06, {"1": "ISO12", "2": "ISOGND"}, "Desacoplo U4"),
    ("J3", "0-10V", "Connector:Screw_Terminal_01x08", PT15 % (8, 8),
     {"1": "DIM1", "2": "ISOGND", "3": "DIM2", "4": "ISOGND", "5": "DIM3", "6": "ISOGND", "7": "DIM4", "8": "ISOGND"},
     "Atenuación 0-10 V: DIM+ y DIM- de cada canal (aislados de la fuente)"),
    # --- identidad, conector del programador, pruebas ---
    ("U5", "M24C02-WMN6TP", "Memory_EEPROM:M24C02-WMN", SOIC8,
     {"1": "GND", "2": "GND", "3": "GND", "4": "GND", "5": "SDA", "6": "SCL", "7": "GND", "8": "3V3"},
     "Identidad del módulo: \"LL-IND\", serie y horas (I2C 0x50)"),
    ("C10", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo EEPROM"),
    ("J7", "PROGRAMADOR", "Connector_Generic:Conn_02x08_Odd_Even",
     "Connector_PinSocket_2.54mm:PinSocket_2x08_P2.54mm_Vertical",
     {"1": "V12", "2": "V12", "3": "GND", "4": "GND", "5": "PWM1", "6": "PWM2", "7": "PWM3", "8": "PWM4",
      "9": "CC1", "10": None, "11": "SDA", "12": "SCL", "13": None, "14": "AUX", "15": "3V3", "16": "GND"},
     "Zócalo del programador AP-1 (mismas señales que la base)"),
    ("TP1", "VIN", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "VIN"}, "Prueba: entrada"),
    ("TP2", "12V", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "V12"}, "Prueba: 12 V"),
    ("TP3", "GND", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "GND"}, "Prueba: tierra"),
    ("TP4", "ISO12", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "ISO12"}, "Prueba: 12 V aislados"),
]
OPTO_X = (3.0, 7.8, 32.2, 37.2)                  # x de cada canal (optoacoplador y su columna de piezas)
for k, x in enumerate(OPTO_X, start=1):
    C_ += [
        ("RL%d" % k, "330", R, R06, {"1": "PWM%d" % k, "2": "LA%d" % k}, "LED del optoacoplador %d (6 mA)" % k),
        ("OK%d" % k, "LTV-217-B", "Isolator:PC817", "Package_SO:SOP-4_4.4x2.6mm_P1.27mm",
         {"1": "LA%d" % k, "2": "GND", "3": "EM%d" % k, "4": "ISO12"}, "Optoacoplador canal %d (3 kV)" % k),
        ("RE%d" % k, "4.7k", R, R06, {"1": "EM%d" % k, "2": "ISOGND"}, "Carga del optoacoplador %d" % k),
        ("RF%d" % k, "10k", R, R06, {"1": "EM%d" % k, "2": "FL%d" % k}, "Filtro canal %d" % k),
        ("RD%d" % k, "47k", R, R06, {"1": "FL%d" % k, "2": "ISOGND"}, "Escala canal %d: 12 V x 47/57 = 9.9 V" % k),
        ("CF%d" % k, "1uF 25V", C, C06, {"1": "FL%d" % k, "2": "ISOGND"}, "Filtro canal %d (2 kHz -> 10 ms)" % k),
        ("RA%d" % k, "100", R, R06, {"1": "OUT%d" % k, "2": "DIM%d" % k}, "Protección de la salida %d" % k),
        ("DZ%d" % k, "MMSZ5242B 12V", "Device:D_Zener", "Diode_SMD:D_SOD-123", {"1": "DIM%d" % k, "2": "ISOGND"},
         "Limita la salida %d a 12 V (cables largos, conexión equivocada)" % k),
    ]

W, H = 88.0, 56.0
RADIO_ESQUINA = 2.0
HOLES = [(3.5, 3.5), (84.5, 39.5), (84.5, 52.5)]     # iguales que la base
YT = 49.8
POS = {
    "J3": (3.0, YT, 0), "J1": (48.0, YT, 0), "J2": (62.0, YT, 0), "J7": (47.0, 6.0, 0),
    # fuente de 12 V: misma ubicación que en la base
    "U1": (11.0, 9.0, 0), "L1": (11.0, 4.0, 0), "C3": (7.8, 7.8, 90), "D3": (15.2, 5.0, 90), "C4": (15.2, 11.0, 90),
    "C5": (4.6, 10.4, 180), "RB1": (5.0, 12.5, 0), "RB2": (9.6, 12.4, 0),
    # entrada (detrás de J1, bajo el programador: piezas bajas)
    "F1": (47.6, 41.9, 0), "D1": (53.6, 41.3, 0), "D2": (49.2, 36.6, 0), "C1": (55.4, 36.8, 90), "C2": (58.0, 36.8, 90),
    # contactores
    "Q1": (63.0, 42.0, 0), "Q2": (69.0, 42.0, 0), "RK1": (63.0, 38.8, 0), "RK2": (69.0, 38.8, 0),
    "D4": (63.5, 34.8, 0), "D5": (70.5, 34.8, 0),
    # convertidor aislado: cruza la franja de aislamiento (patas 1-2 fuente, 3-4 aislado)
    "U2": (20.0, 24.9, 0), "C6": (27.0, 24.6, 90), "C7": (20.0, 37.4, 90),
    "U3": (14.1, 38.0, 0), "U4": (26.0, 38.0, 0), "C8": (14.1, 42.7, 0), "C9": (26.0, 42.7, 0),
    "U5": (57.0, 12.0, 0), "C10": (57.0, 16.4, 0),
    "TP1": (46.0, 33.0, 0), "TP2": (2.5, 16.0, 0), "TP3": (60.0, 31.0, 0), "TP4": (20.0, 42.6, 0),
}
for k, x in enumerate(OPTO_X, start=1):
    POS.update({"RL%d" % k: (x, 23.6, 90), "OK%d" % k: (x, 30.3, 270),
                "RE%d" % k: (x - 1.0, 36.2, 90), "RF%d" % k: (x + 1.0, 36.2, 90),
                "RD%d" % k: (x - 1.0, 39.4, 90), "CF%d" % k: (x + 1.0, 39.4, 90),
                "RA%d" % k: (x - 1.2, 43.4, 90), "DZ%d" % k: (x + 0.9, 43.4, 90)})

AISLADO = ["ISO12", "ISOGND"] + ["%s%d" % (n, k) for n in ("EM", "FL", "OUT", "DIM") for k in range(1, 5)]
NETCLASS = {
    "Media": (0.6, 0.2, ["VIN", "VIN_RAW", "VF", "V12", "SW", "K1", "K2"]),
    "Aislado": (0.25, 0.2, AISLADO),
}
# lado aislado (con el hueco donde están las patas 3-4 del convertidor) relleno con su propia tierra
ZONA_ISO = [(0.3, 32.2), (18.0, 32.2), (18.0, 28.4), (22.0, 28.4), (22.0, 32.2), (41.5, 32.2), (41.5, 55.7),
            (0.3, 55.7)]
ZONAS_FINALES = [("ISOGND", ZONA_ISO), ("ISOGND", ZONA_ISO, "B")]   # se rutea como pista y al final se rellena
# franja de aislamiento de 3 mm: sin pistas, vías ni relleno en las dos capas
SIN_COBRE = [
    [(72.5, 0.3), (87.7, 0.3), (87.7, 30.5), (72.5, 30.5)],               # bajo la antena del programador
    [(0.3, 28.4), (18.0, 28.4), (18.0, 32.2), (0.3, 32.2)],
    [(22.0, 28.4), (44.5, 28.4), (44.5, 32.2), (22.0, 32.2)],
    [(41.5, 32.2), (44.5, 32.2), (44.5, 55.7), (41.5, 55.7)],
]
SIN_RELLENO = [[(17.0, 25.6), (23.0, 25.6), (23.0, 28.4), (17.0, 28.4)]]  # la tierra de la fuente no se acerca al hueco
DRU = """(rule "aislamiento"
  (condition "A.NetClass == 'Aislado' && B.NetClass != 'Aislado' && !A.memberOfFootprint('U2') && !B.memberOfFootprint('U2')")
  (constraint clearance (min 2.5mm)))
"""
PRE = [
    ("V12", 0.6, [(9.5, 2.6), (9.5, 1.1), (42.0, 1.1), (42.0, 6.0), (44.46, 6.0)]),   # como en la base
    ("V12", 0.6, [(44.46, 6.0), (47.0, 6.0)]),                                          # patas 1 y 2 del zócalo
    # convertidor aislado: la entrada sale por arriba de la pata 2 y la tierra aislada por abajo de la pata 3,
    # para que entre las dos pistas queden más de 2.5 mm (regla "aislamiento")
    ("V12", 0.6, [(20.0, 26.9), (23.0, 26.9), (27.0, 26.08)]),
    ("ISOGND", 0.3, [(20.6, 30.5), (21.6, 31.5), (21.6, 34.6)]),
]

SILK = [
    ("1+", 3.0, 45.6, 0.9, "F"), ("1-", 6.5, 45.6, 0.9, "F"), ("2+", 10.0, 45.6, 0.9, "F"), ("2-", 13.5, 45.6, 0.9, "F"),
    ("3+", 17.0, 45.6, 0.9, "F"), ("3-", 20.5, 45.6, 0.9, "F"), ("4+", 24.0, 45.6, 0.9, "F"), ("4-", 27.5, 45.6, 0.9, "F"),
    ("0-10V AISLADO", 33.0, 46.2, 0.9, "F"),
    ("+", 48.0, 46.0, 1.2, "F"), ("-", 53.08, 46.0, 1.2, "F"),
    ("+V", 62.0, 45.6, 0.9, "F"), ("K1", 65.5, 45.6, 0.9, "F"), ("+V", 69.0, 45.6, 0.9, "F"), ("K2", 72.5, 45.6, 0.9, "F"),
    ("LetreroLab AP-1 IND  12-24V", 44.0, 54.8, 1.0, "B"),
    ("AISLAMIENTO 3 mm", 20.0, 30.3, 0.8, "B"),
    ("Contactor: bobina 12/24 V. La red NO entra a esta placa", 44.0, 2.0, 0.8, "B"),
]
FLAGS = [("VIN_RAW", 20.32, 20.32), ("GND", 35.56, 20.32), ("VIN", 50.8, 20.32), ("V12", 66.04, 20.32),
         ("3V3", 81.28, 20.32), ("VF", 96.52, 20.32)]
NOTES = [(150.0, 15.0, "LetreroLab AP-1 IND: 4 salidas 0-10 V aisladas (LTV-217 + B1212S + LM358) y 2 bobinas de "
                       "contactor.\nI2C: M24C02 0x50 (modelo LL-IND). 3V3 lo da el programador por J7. "
                       "PWM de 2 kHz para los optoacopladores.")]
TITLE = "LetreroLab AP-1 IND - módulo industrial 0-10 V + contactores"
SUBTITLES = ["Placa de 2 capas para ensamble en fábrica (JLCPCB)", "12-24 V DC, 4 x 0-10 V aislados + 2 contactores"]
COMPANY = "PCB 88 x 56 mm, 2 capas, 1 oz"
COSTURA = 4.0                                      # vías de costura cada 4 mm en las dos tierras
COSTURA_REDES = ("GND", "ISOGND")
PAPER = "A2"
OCULTAR_REF = ("J3", "J2")

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
