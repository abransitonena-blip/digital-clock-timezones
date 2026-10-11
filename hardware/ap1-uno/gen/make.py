"""AP ELECTRIC · AP UNO: el módulo compacto todo en uno (BASE + CORE en una sola placa de 120 x 62 mm, 4 capas).

Junta en una placa lo que antes eran 3-4 módulos apilados o en cadena:
- POTENCIA (la misma de la BASE, mismas coordenadas, ya probada): entrada 12-24 V 20 A con fusible mini, polaridad
  sin pérdidas, supresor, medidor INA238 (V, A, W, kWh), 4 canales de 8 A atenuables, 2 focos de corriente constante
  (AL8860, 1 A), temperatura y corte por hardware ante sobrecorriente, sobrevoltaje y 85 °C.
- CEREBRO (el del CORE): ESP32-C3 con Wi-Fi, USB-C, botones MODO y RESET, LED de estado y de falla.
- 4 SALIDAS de 12-24 V para bobinas de contactor y relevadores (AO3400 + diodo por salida, fusible de 3 A común).
- 4 ENTRADAS de contacto seco (pulsadores, flotadores, sensores con salida a 0 V), con filtro y protección.
- PUERTO RS-485 (SP3485 + SM712, terminación y polarización por puente): DMX512 a reflectores y cabezales, o Modbus RTU
  a medidores, variadores y PLC.
- QWIIC para los cabezales y módulos: AP FOCO, PWM4, AO4, DO8, AP INPUT, AI4, DIST 4.
El programa reconoce la placa por dos patas del expansor de salidas (P5 a 0, P6 a 1) y la memoria "LL-UNO".

    bash ../tools/rutear.sh ap1-uno AP_UNO
"""
import importlib.util, os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import placa  # noqa: E402
import conectores  # noqa: E402

# la potencia es la de la BASE: se toma de su generador tal cual
_spec = importlib.util.spec_from_file_location("ap1_base", os.path.join(HERE, "..", "..", "ap1-base", "gen", "make.py"))
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)

PROJECT = "AP_UNO"
NS = uuid.UUID("6a2e9c71-3d4f-4b8e-a157-9c0d2e4f6b18")
ROOT_UUID = "e5f6a7b8-1c2d-4e3f-9a0b-c1d2e3f4a5b6"
R06, C06, C08, C12 = ("Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric",
                      "Capacitor_SMD:C_0805_2012Metric", "Capacitor_SMD:C_1206_3216Metric")
R, C = "Device:R", "Device:C"
SJ = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"
SJB = "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm"
TP = "TestPoint:TestPoint_Pad_D1.5mm"

QUITAR = {"J7", "Q5", "RAUX", "D4", "J6"}           # zócalo del programador y AUX de 12 V (pasa a las salidas)
ESP = {"1": "3V3", "2": "EN", "3": "PWM1", "4": "PWM2", "5": "PWM3", "6": "PWM4", "7": "SCL", "8": "BOOT",
       "9": "GND", "10": "CC2", "11": "ALERT", "12": "LEDV", "13": "USB_DN", "14": "USB_DP", "15": "RS_RX", "16": "SDA",
       "17": "RS_TX", "18": "CC1", "19": "GND"}

C_ = [c for c in B.C_ if c[0] not in QUITAR] + [
    # --- cerebro ---
    ("U10", "ESP32-C3-WROOM-02", "RF_Module:ESP32-C3-WROOM-02", "LetreroLab:ESP32-C3-WROOM-02_JLC", ESP,
     "Wi-Fi + BLE. IO4-7 = canales, IO0/IO10 = focos CC 1/2 (al revés que el CORE), IO20 = ALERTA, IO1/IO3 = RS-485, IO21 = LED"),
    ("C20", "10uF", C, C08, {"1": "3V3", "2": "GND"}, "Desacoplo del módulo"),
    ("C21", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo del módulo"),
    ("R20", "10k", R, R06, {"1": "3V3", "2": "EN"}, "Pull-up EN"),
    ("C22", "1uF", C, C06, {"1": "EN", "2": "GND"}, "Arranque retardado"),
    ("R21", "10k", R, R06, {"1": "3V3", "2": "BOOT"}, "Pull-up IO9"),
    ("SW1", "MODO / BOOT", "Switch:SW_Push", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", {"1": "BOOT", "2": "GND"},
     "MODO; mantenido al conectar el USB = modo programación"),
    ("SW2", "RESET", "Switch:SW_Push", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", {"1": "EN", "2": "GND"}, "Reinicio"),
    ("R22", "4.7k", R, R06, {"1": "3V3", "2": "SDA"}, "Pull-up I2C"),
    ("R23", "4.7k", R, R06, {"1": "3V3", "2": "SCL"}, "Pull-up I2C"),
    ("R24", "10k", R, R06, {"1": "3V3", "2": "ALERT"}, "Pull-up de la alerta (INA238 + TMP1075)"),
    ("R25", "1k", R, R06, {"1": "3V3", "2": "LRA"}, "LED de falla"),
    ("D12", "ROJO", "Device:LED", "LED_SMD:LED_0603_1608Metric", {"1": "ALERT", "2": "LRA"}, "FALLA (por hardware)"),
    ("R26", "1k", R, R06, {"1": "LEDV", "2": "LVA"}, "LED de estado"),
    ("D13", "VERDE", "Device:LED", "LED_SMD:LED_0603_1608Metric", {"1": "GND", "2": "LVA"}, "Estado"),
] + [("R%d" % (27 + k), "10k", R, R06, {"1": "PWM%d" % (k + 1), "2": "GND"}, "Canal %d apagado al arrancar" % (k + 1))
     for k in range(4)] + [
    # --- USB-C y 3.3 V ---
    ("J10", "USB-C", "Connector:USB_C_Receptacle_USB2.0_16P", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
     {"A1": "GND", "A4": "VBUS", "A5": "CC1U", "A6": "USB_DP", "A7": "USB_DN", "A8": None, "A9": "VBUS",
      "B1": "GND", "B4": "VBUS", "B5": "CC2U", "B6": "USB_DP", "B7": "USB_DN", "B8": None, "B9": "VBUS",
      "S1": "GND", "A12": "GND", "B12": "GND"}, "USB-C: programar y probar"),
    ("R31", "5.1k", R, R06, {"1": "CC1U", "2": "GND"}, "CC1"),
    ("R32", "5.1k", R, R06, {"1": "CC2U", "2": "GND"}, "CC2"),
    ("U11", "USBLC6-2SC6", "Power_Protection:USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "USB_DN", "2": "GND", "3": "USB_DP", "4": "USB_DP", "5": "VBUS", "6": "USB_DN"}, "ESD del USB"),
    ("D10", "B5819W", "Device:D_Schottky", "Diode_SMD:D_SOD-123", {"1": "VLOG", "2": "V12"}, "12 V de la potencia"),
    ("D11", "B5819W", "Device:D_Schottky", "Diode_SMD:D_SOD-123", {"1": "VLOG", "2": "VBUS"}, "5 V del USB"),
    ("U12", "AP63203WU", "Regulator_Switching:AP63203WU", "Package_TO_SOT_SMD:TSOT-23-6",
     {"1": "3V3", "2": "VLOG", "3": "VLOG", "4": "GND", "5": "SWP", "6": "BSTP"}, "Buck 3.3 V 2 A"),
    ("L4", "4.7uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR4030S", {"1": "SWP", "2": "3V3"}, "Bobina 3.3 V"),
    ("C23", "100nF", C, C06, {"1": "BSTP", "2": "SWP"}, "Bootstrap"),
    ("C24", "10uF 25V", C, C12, {"1": "VLOG", "2": "GND"}, "Entrada del buck de 3.3 V"),
    ("C25", "22uF", C, C08, {"1": "3V3", "2": "GND"}, "Salida 3.3 V"),
    ("C26", "22uF", C, C08, {"1": "3V3", "2": "GND"}, "Salida 3.3 V"),
    ("J11", "QWIIC", "Connector_Generic_MountingPin:Conn_01x04_MountingPin",
     "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
     {"1": "GND", "2": "3V3", "3": "SDA", "4": "SCL", "MP": "GND"}, "Cabezales y módulos (AP FOCO, PWM4, AO4, DO8...)"),
    # --- salidas (expansor 0x20: P0-P3 salidas, P5/P6 = identificación, P7 = DE del RS-485) ---
    ("U13", "TCA9554PWR", "Interface_Expansion:TCA9554PW", "Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
     {"1": "GND", "2": "GND", "3": "GND", "4": "DO1", "5": "DO2", "6": "DO3", "7": "DO4", "8": "GND",
      "9": None, "10": "ID5", "11": "ID6", "12": "RS_DE", "13": None, "14": "SCL", "15": "SDA", "16": "3V3"},
     "Expansor 0x20: salidas S1-S4, identificación del UNO y DE del RS-485"),
    ("C27", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U13"),
    ("R35", "10k", R, R06, {"1": "ID5", "2": "GND"}, "Identificación: P5 = 0"),
    ("R36", "10k", R, R06, {"1": "3V3", "2": "ID6"}, "Identificación: P6 = 1 (en un DO8 se lee 0)"),
    ("F3", "3A", "Device:Fuse", "Fuse:Fuse_1206_3216Metric", {"1": "VIN", "2": "VDO"}, "Fusible común de las 4 salidas"),
    ("J12", "SALIDAS 1-2", conectores.SYM[3], conectores.XH3, {"1": "VDO", "2": "SO1", "3": "SO2"},
     "1 = +V, 2 = salida 1, 3 = salida 2 (bobina entre +V y la salida)"),
    ("J13", "SALIDAS 3-4", conectores.SYM[3], conectores.XH3, {"1": "VDO", "2": "SO3", "3": "SO4"},
     "1 = +V, 2 = salida 3, 3 = salida 4"),
    # --- entradas (expansor 0x24) ---
    ("U14", "TCA9554PWR", "Interface_Expansion:TCA9554PW", "Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
     {"1": "GND", "2": "GND", "3": "3V3", "4": "DI1", "5": "DI2", "6": "DI3", "7": "DI4", "8": "GND",
      "9": "PFIJO", "10": "PFIJO", "11": "PFIJO", "12": "PFIJO", "13": None, "14": "SCL", "15": "SDA", "16": "3V3"},
     "Expansor 0x24: entradas E1-E4 (E5-E8 fijas, inactivas)"),
    ("C28", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U14"),
    ("R37", "10k", R, R06, {"1": "3V3", "2": "PFIJO"}, "P4-P7 en alto (inactivas)"),
    ("J14", "ENTRADAS 1-2", conectores.SYM[3], conectores.XH3, {"1": "IN1", "2": "IN2", "3": "GND"},
     "Contacto seco entre la entrada y 0 V"),
    ("J15", "ENTRADAS 3-4", conectores.SYM[3], conectores.XH3, {"1": "IN3", "2": "IN4", "3": "GND"},
     "Contacto seco entre la entrada y 0 V"),
    # --- RS-485: DMX512 o Modbus RTU ---
    ("U15", "SP3485EN", "Interface_UART:SP3485EN", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "RS_RX", "2": "RS_DE", "3": "RS_DE", "4": "RS_TX", "5": "GND", "6": "RSA", "7": "RSB", "8": "3V3"},
     "Transceptor RS-485 de 3.3 V (DE = /RE = P7 del expansor)"),
    ("C29", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U15"),
    ("R38", "10k", R, R06, {"1": "RS_DE", "2": "GND"}, "DE en bajo al arrancar"),
    ("D14", "SM712", "Diode:SM712_SOT23", "Package_TO_SOT_SMD:SOT-23", {"1": "RSA", "2": "RSB", "3": "GND"},
     "Protección de la línea RS-485"),
    ("R39", "120", R, "Resistor_SMD:R_1206_3216Metric", {"1": "RSA", "2": "TERM"}, "Terminación"),
    ("JP4", "120R", "Jumper:SolderJumper_2_Open", SJ, {"1": "TERM", "2": "RSB"}, "Cerrar en los extremos de la línea"),
    ("R40", "560", R, R06, {"1": "PA", "2": "RSA"}, "Polarización A"),
    ("R41", "560", R, R06, {"1": "RSB", "2": "PB"}, "Polarización B"),
    ("JP5", "POL A", "Jumper:SolderJumper_2_Bridged", SJB, {"1": "3V3", "2": "PA"}, "Polarización (cortar si ya hay)"),
    ("JP6", "POL B", "Jumper:SolderJumper_2_Bridged", SJB, {"1": "PB", "2": "GND"}, "Polarización (cortar si ya hay)"),
    ("J16", "RS-485", conectores.SYM[3], conectores.XH3, {"1": "GND", "2": "RSB", "3": "RSA"},
     "Como el XLR de DMX: 1 = 0 V, 2 = B (-), 3 = A (+)"),
    ("TP5", "3V3", "Connector:TestPoint", TP, {"1": "VLOG"}, "Prueba: entrada del 3.3 V"),
]
for k in range(1, 5):
    C_ += [
        ("Q%d" % (k + 5), "AO3400A", "Transistor_FET:AO3400A", "Package_TO_SOT_SMD:SOT-23",
         {"1": "DO%d" % k, "2": "GND", "3": "SO%d" % k}, "Salida %d (lado bajo, 30 V)" % k),
        ("RD%d" % k, "10k", R, R06, {"1": "DO%d" % k, "2": "GND"}, "Salida %d apagada al arrancar" % k),
        ("D%d" % (14 + k), "SS14", "Device:D_Schottky", "Diode_SMD:D_SMA", {"1": "VDO", "2": "SO%d" % k},
         "Diodo de bobina %d" % k),
        ("RU%d" % k, "4.7k", R, R06, {"1": "3V3", "2": "IN%d" % k}, "Entrada %d: pull-up" % k),
        ("RI%d" % k, "10k", R, R06, {"1": "IN%d" % k, "2": "DI%d" % k}, "Entrada %d: protección (24 V por error = 2 mA)" % k),
        ("CI%d" % k, "10nF", C, C06, {"1": "DI%d" % k, "2": "GND"}, "Entrada %d: filtro" % k),
    ]

W, H = 120.0, 62.0
RADIO_ESQUINA = 2.0
HOLES = [(3.5, 3.5), (84.5, 58.5), (116.5, 58.5)]
CAPAS = 4
POS = {k: v for k, v in B.POS.items() if k not in QUITAR}
POS["U9"] = (53.0, 10.4, 0)                       # memoria: un poco abajo, deja la fila superior a los conectores
POS["C14"] = (53.0, 15.6, 0)
XS = [45.5, 56.5, 67.5, 78.5]                      # fila superior: salidas 1-2, 3-4, entradas 1-2, 3-4
POS.update({
    "J12": (XS[0], 3.4, 0), "J13": (XS[1], 3.4, 0), "J14": (XS[2], 3.4, 0), "J15": (XS[3], 3.4, 0),
    # 3.3 V (donde estaba el zócalo del programador)
    "U12": (34.5, 10.5, 0), "C23": (34.5, 7.9, 0), "L4": (34.5, 15.2, 0), "C24": (38.2, 10.5, 90),
    "C25": (38.2, 18.8, 90), "C26": (38.2, 15.2, 90), "D10": (37.5, 5.2, 0), "TP5": (34.5, 19.4, 0),
    # salidas y entradas (zona derecha de la potencia)
    "F3": (66.0, 59.0, 0), "R35": (76.0, 11.5, 90), "R36": (77.6, 11.5, 90), "U13": (82.5, 13.2, 0), "C27": (82.5, 17.6, 0),
    "U14": (80.0, 42.8, 0), "C28": (85.8, 42.8, 90), "R37": (73.5, 42.8, 90),
    # ESP32 y su entorno
    "U10": (103.5, 19.2, 0),
    "C20": (91.0, 28.4, 0), "C21": (91.0, 30.5, 0), "R20": (94.4, 28.4, 0), "C22": (94.4, 30.2, 0),
    "R21": (97.8, 28.4, 0), "R22": (101.2, 28.4, 0), "R23": (101.2, 30.2, 0), "R24": (104.6, 28.4, 0),
    "R25": (108.0, 28.4, 0), "D12": (108.0, 30.2, 0), "R26": (111.4, 28.4, 0), "D13": (111.4, 30.2, 0),
    "R27": (114.8, 28.4, 0), "R28": (114.8, 30.2, 0), "R29": (114.8, 32.0, 0), "R30": (114.8, 33.8, 0),
    "SW1": (94.5, 36.0, 0), "SW2": (103.0, 36.0, 0), "D11": (108.6, 35.8, 90),
    "J10": (115.8, 42.5, 90), "U11": (107.8, 41.5, 90), "R31": (107.8, 45.6, 0), "R32": (107.8, 47.4, 0),
    # RS-485 (DMX512 / Modbus) y Qwiic
    "U15": (95.0, 43.5, 0), "C29": (100.8, 40.6, 0), "R38": (100.8, 42.4, 0), "D14": (101.2, 45.6, 0),
    "R39": (101.2, 49.4, 0), "JP4": (105.8, 49.6, 0),
    "R40": (88.2, 44.0, 90), "R41": (89.8, 44.0, 90), "JP5": (87.6, 48.4, 90), "JP6": (90.4, 48.4, 90),
    "J16": (91.5, 57.4, 0), "J11": (104.0, 58.3, 0),
})
for k in range(1, 5):
    x = 72.5 + 4.2 * (k - 1)
    POS.update({
        "Q%d" % (k + 5): (x, 20.8, 0), "RD%d" % k: (x, 24.2, 0),
        "D%d" % (14 + k): (x, 29.4, 90),
        "RU%d" % k: (x - 0.8, 35.0, 90), "RI%d" % k: (x + 0.8, 35.0, 90), "CI%d" % k: (x, 38.4, 0),
    })

NETCLASS = dict(B.NETCLASS)
NETCLASS["Media"] = (0.6, 0.2, B.NETCLASS["Media"][2] + ["VLOG", "VBUS", "3V3", "SWP", "VDO", "SO1", "SO2", "SO3", "SO4"])
POWER_ZONES = B.POWER_ZONES
KEEPOUT_NETS = B.KEEPOUT_NETS
VIAS = B.VIAS
# rutas de la BASE que llegaban al zócalo del programador: se quitan (el ruteador une el ESP32 con los drivers)
PRE = [p for p in B.PRE if not ((p[0] == "V12" and p[2][-1] == (44.46, 6.0)) or
                                 (p[0] == "CC2" and p[2][0] == (44.46, 16.16)) or
                                 (p[0] == "CC1" and p[2][0] == (47.0, 16.16)) or
                                 (p[0] in ("CC1", "CC2") and len(p) > 3))] + [
    # CTRL de los focos CC: los troncos de la BASE por el borde de arriba (B.Cu) siguen hasta el ESP32 (IO10 / IO0),
    # por fuera de la zona sin cobre de la antena
    # (en el UNO el foco 1 va a IO0 y el 2 a IO10: así los dos troncos no se cruzan)
    ("CC1", 0.3, [(7.6, 19.45), (7.6, 1.0), (88.6, 1.0), (88.6, 13.2), (113.9, 13.2)], "B"),
    ("CC2", 0.3, [(7.6, 31.95), (7.6, 25.0), (8.6, 24.0), (8.6, 1.8), (87.8, 1.8), (87.8, 24.4), (113.9, 24.4),
                  (113.9, 25.2)], "B"),
    ("CC1", 0.3, [(113.9, 13.2), (112.25, 13.2)]), ("CC2", 0.3, [(113.9, 25.2), (112.25, 25.2)]),
    # 3.3 V de la memoria (U9) por abajo hasta su capacitor, y A2 del expansor de entradas a su propia pata de 3.3 V
    ("3V3", 0.3, [(55.47, 8.5), (57.3, 7.9)]), ("3V3", 0.3, [(57.3, 7.9), (54.2, 11.0), (54.2, 13.6), (52.2, 14.6), (51.0, 15.6)], "B"),
    ("3V3", 0.3, [(51.0, 15.6), (52.22, 15.6)]),
    ("3V3", 0.3, [(77.14, 41.82), (78.4, 41.82), (79.7, 40.53), (82.86, 40.53)]),
    # 3.3 V: de la vía de la memoria a la pata 16 del expansor de salidas (une los dos grupos de 3.3 V)
    ("3V3", 0.4, [(57.3, 7.9), (80.6, 7.9)], "B"), ("3V3", 0.4, [(80.6, 7.9), (85.36, 7.9), (85.36, 10.92)]),
    # GND de la pata 8 del expansor de entradas
    ("GND", 0.4, [(77.14, 45.075), (75.9, 45.9)]),
    # foco 1: LEDA1 y VCC del AL8860 como en la BASE (el ruteador los cruzaba y dejaba sin VCC la pata 8)
    ("LEDA1", 0.4, [(2.89, 16.53), (2.84, 16.47), (1.55, 16.47)]),
    ("LEDA1", 0.6, [(1.55, 16.47), (1.55, 18.43), (4.5, 21.38)], "B"),
    ("LEDA1", 0.6, [(4.5, 21.38), (5.58, 21.38), (5.96, 21.0)]),
    ("LEDA1", 0.6, [(4.5, 21.38), (2.5, 23.38), (2.5, 50.5)], "B"),
    ("VCC", 0.4, [(6.65, 15.75), (7.17, 16.27), (7.17, 16.47), (7.11, 16.53)]),
    ("VCC", 0.6, [(6.65, 15.75), (6.2, 16.2), (6.2, 22.55)], "B"),
    # +V de las 4 salidas: de J3 (+V común, dentro del plano VIN) por la franja de abajo hasta el fusible F3
    ("VIN", 1.5, [(23.56, 50.4), (23.56, 59.0), (64.54, 59.0)]),
    # 12 V de la potencia al 3.3 V lógico (D10): el tronco de la BASE, que iba al zócalo, se corta en D10
    ("V12", 0.6, [(9.5, 2.6), (9.5, 1.1), (40.6, 1.1), (40.6, 5.2), (39.15, 5.2)]),
    # 3.3 V del INA238 (en la BASE llegaba del programador)
    ("3V3", 0.3, [(21.9, 22.2), (21.3, 22.2), (21.3, 20.4), (21.9, 19.8), (23.33, 19.8)]),
    # USB-C: los dos pares de VBUS se unen por abajo, detrás de la fila de patas
    ("VBUS", 0.6, [(111.75, 44.95), (110.6, 44.95)]), ("VBUS", 0.6, [(111.75, 40.05), (110.6, 40.05)]),
    ("VBUS", 0.6, [(110.6, 44.95), (110.6, 40.05)], "B"),
]
PREVIAS = [v for v in B.PREVIAS if v[1:] not in ((41.2, 12.35), (40.2, 16.2))] + [("VBUS", 110.6, 44.95), ("VBUS", 110.6, 40.05),
    ("CC1", 113.9, 13.2), ("CC2", 113.9, 25.2), ("3V3", 57.3, 7.9), ("3V3", 51.0, 15.6),
    ("3V3", 80.6, 7.9), ("GND", 75.9, 45.9), ("LEDA1", 1.55, 16.47), ("LEDA1", 4.5, 21.38), ("VCC", 6.65, 15.75),
    ("VCC", 6.2, 22.55)]
SIN_COBRE = [[(89.5, 0.3), (117.7, 0.3), (117.7, 12.4), (89.5, 12.4)]]     # bajo la antena del ESP32
RETORNO = B.RETORNO
SILK = [s for s in B.SILK if s[0] not in ("AUX", "LetreroLab AP-1 BASE", "LetreroLab AP-1 BASE universal  12-24V 20A")] + [
    ("+V S1 S2", XS[0] + 2.5, 8.6, 0.8, "F"), ("+V S3 S4", XS[1] + 2.5, 8.6, 0.8, "F"),
    ("E1 E2 0V", XS[2] + 2.5, 8.6, 0.8, "F"), ("E3 E4 0V", XS[3] + 2.5, 8.6, 0.8, "F"),
    ("0V B A", 94.0, 53.0, 0.8, "F"), ("RS-485 DMX", 94.0, 61.2, 0.8, "B"), ("QWIIC", 104.0, 53.6, 0.8, "F"),
    ("MODO", 94.5, 39.8, 0.8, "F"), ("RESET", 103.0, 39.8, 0.8, "F"),
    ("FALLA", 108.0, 31.8, 0.8, "B"), ("OK", 111.4, 31.8, 0.8, "B"),
    ("AP UNO", 76.0, 59.2, 1.6, "F"),
    ("AP ELECTRIC  AP UNO  12-24V 20A  todo en uno", 60.0, 60.0, 1.0, "B"),
    ("Salidas CC flotantes: no unir a tierra", 20.0, 2.0, 0.9, "B"),
]
FLAGS = B.FLAGS + [("VLOG", 142.24, 20.32), ("VDO", 157.48, 20.32)]
NOTES = [(150.0, 15.0, "AP ELECTRIC · AP UNO: BASE + CORE en una placa. I2C: INA238 0x40, TMP1075 0x48, M24C02 0x50,\n"
                       "salidas TCA9554 0x20 (S1-S4, P5=0 / P6=1 identificación, P7 = DE RS-485), entradas TCA9554 0x24 (E1-E4).\n"
                       "RS-485: TX IO1, RX IO3 (DMX512 o Modbus RTU).")]
TITLE = "AP ELECTRIC · AP UNO - módulo compacto todo en uno"
SUBTITLES = ["Placa de 4 capas, 2 oz exteriores (JLCPCB)", "4 x 8 A + 2 focos CC + 4 salidas + 4 entradas + RS-485 + Wi-Fi"]
COSTURA = 5.0
COMPANY = "PCB 120 x 56 mm, 4 capas"
PAPER = "A2"
MODELOS = {}
OCULTAR_REF = B.OCULTAR_REF + ("J12", "J13", "J14", "J15", "J16", "J11")

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
