"""AP Electric Industrial · AP Rack 16 rev A (CONCEPTO): 16 salidas de estado sólido protegidas, 8 entradas, enlace AP LINK en cadena.

Una placa de CC (12-30 V) para tablero. Sin red de CA: las cargas de red se mandan con contactor o relevador de riel DIN certificado.

Bloques:
- Entrada 12-30 V CC por JST VH (hasta 10 A por pata), fusible mini de auto (Keystone 3568), supresor SMBJ33A. Sin diodo en serie: con la
  polaridad invertida el supresor conduce y el fusible se abre. Rango de diseño 12-30 V; el 24 V nominal es un punto del rango, no el único.
- 5 V (LMR16006, 60 V) y 3.3 V (AP63203), igual que el 7R Tour.
- 16 salidas de lado bajo: NCV8406A (onsemi, 65 V, protección propia contra cortocircuito, sobrecorriente, temperatura y sobrevoltaje) con
  diodo de bobina SS14 hacia +V y LED por salida. La carga va entre +V y la salida: bornera KF128 de 3 polos = salida, +V, salida (2 salidas por bloque).
  Compuertas a 5 V con 74HCT125 (entradas TTL: aceptan 3.3 V del expansor); pull-down de 10 k en cada entrada del buffer: salidas apagadas al arrancar.
- Expansores TCA9554 I2C: 0x20 = salidas 1-8, 0x21 = salidas 9-16, 0x22 = entradas 1-8 (con interrupción), 0x23 = LED (posición en la cadena, RUN, FALLA, COM, CABEZA).
- 8 entradas de 12-30 V optoaisladas (LTV-217), mismo circuito que el 7R Tour con resistencias de 3.3 k; común propio COMI.
- AP LINK: dos conectores JST XH de 4 patas (ENTRA y SIGUE, A/B/GND unidos; SENSE aparte) y un SP3485 sin aislar. Pata 1 = SENSE, 2 = B (D-), 3 = A (D+), 4 = GND.
  SENSE_OUT: 1 kΩ en serie y 10 kΩ a 0 V; SENSE_IN: 10 kΩ en serie y 100 kΩ a 3.3 V (el cabeza de una cadena no tiene cable: lee 1).
- Medición de la tensión de entrada por divisor 100 k / 10 k a un ADC del ESP32-C3.
- USB-C para programar y probar. Los 4 LED de posición (1, 2, 4, 8) muestran en binario la posición del módulo en la cadena.

    bash ../../tools/rutear.sh ap-electric/rack16 AP_RACK16
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import placa  # noqa: E402
import conectores  # noqa: E402

PROJECT = "AP_RACK16"
NS = uuid.UUID("5d3c1e7a-9b4f-4c2d-8a6e-3f1b5d7c9e42")
ROOT_UUID = "8e2a4c6d-0f1b-4d3e-9a5c-7b9d1f3e5a64"
R06, R08, R12 = "Resistor_SMD:R_0603_1608Metric", "Resistor_SMD:R_0805_2012Metric", "Resistor_SMD:R_1206_3216Metric"
C06, C08, C12 = "Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_0805_2012Metric", "Capacitor_SMD:C_1206_3216Metric"
R, C = "Device:R", "Device:C"
LED06 = "LED_SMD:LED_0603_1608Metric"
SMA, SMB = "Diode_SMD:D_SMA", "Diode_SMD:D_SMB"
TSSOP = "Package_SO:TSSOP-16_4.4x5mm_P0.65mm"
SOIC14 = "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm"
SOIC8 = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
BTN = "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A"
KF3 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal"
SJO = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"
TP = "TestPoint:TestPoint_Pad_D1.5mm"
NSAL, NENT = 16, 8


def tca(ref, a, pines, func, int_net=None):
    """TCA9554: a = (A0, A1, A2) en '3V3'/'GND'; pines = 8 redes P0-P7."""
    p = {"1": a[0], "2": a[1], "3": a[2], "8": "GND", "13": int_net, "14": "SCL", "15": "SDA", "16": "3V3"}
    for num, red in zip(("4", "5", "6", "7", "9", "10", "11", "12"), pines):
        p[num] = red
    return (ref, "TCA9554PWR", "Interface_Expansion:TCA9554PW", TSSOP, p, func)


C_ = [
    # --- entrada de potencia ---
    ("J1", "VIN 12-30V", conectores.SYM[2], conectores.VH2, {"1": "VIN_RAW", "2": "GND"},
     "Alimentación 12-30 V CC: 1 = +, 2 = 0 V. JST VH, hasta 10 A por pata"),
    ("F1", "MINI 3A", "Device:Fuse", "Fuse:Fuseholder_Blade_Mini_Keystone_3568", {"1": "VIN_RAW", "2": "V24"},
     "Fusible mini de auto (ATM) de 3 A en esta revisión: el +V de la placa va en pistas de 0.8 mm (sin medir); se cambia sin soldar"),
    ("D1", "SMBJ33A", "Device:D_TVS", SMB, {"1": "V24", "2": "GND"}, "Supresor de picos; con la polaridad invertida conduce y abre el fusible"),
    ("C1", "10uF 50V", C, C12, {"1": "V24", "2": "GND"}, "Reserva de entrada"),
    ("C2", "10uF 50V", C, C12, {"1": "V24", "2": "GND"}, "Reserva de entrada"),
    # --- 5 V ---
    ("U1", "LMR16006XDDC", "Regulator_Switching:LMR16006YQ", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "BST", "2": "GND", "3": "FB", "4": "V24", "5": "V24", "6": "SW"}, "Buck 60 V a 5 V"),
    ("L1", "47uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR4030S", {"1": "V5", "2": "SW"}, "Bobina del buck de 5 V"),
    ("D2", "SS210", "Device:D_Schottky", SMA, {"1": "SW", "2": "GND"}, "Rueda libre del buck"),
    ("C3", "100nF", C, C06, {"1": "BST", "2": "SW"}, "Bootstrap"),
    ("C4", "10uF 50V", C, C12, {"1": "V24", "2": "GND"}, "Entrada del buck"),
    ("C5", "22uF 25V", C, C12, {"1": "V5", "2": "GND"}, "Salida 5 V"),
    ("RB1", "56k", R, R06, {"1": "V5", "2": "FB"}, "Divisor: 0.765 V x 6.6 = 5.05 V"),
    ("RB2", "10k", R, R06, {"1": "FB", "2": "GND"}, "Divisor"),
    ("D3", "B5819W", "Device:D_Schottky", "Diode_SMD:D_SOD-123", {"1": "V5", "2": "VBUS"}, "5 V del USB (programar sin 12-30 V)"),
    # --- 3.3 V ---
    ("U2", "AP63203WU", "Regulator_Switching:AP63203WU", "Package_TO_SOT_SMD:TSOT-23-6",
     {"1": "3V3", "2": "V5", "3": "V5", "4": "GND", "5": "SWP", "6": "BSTP"}, "Buck 3.3 V (síncrono)"),
    ("L2", "4.7uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR4030S", {"1": "SWP", "2": "3V3"}, "Bobina 3.3 V"),
    ("C6", "100nF", C, C06, {"1": "BSTP", "2": "SWP"}, "Bootstrap"),
    ("C7", "10uF 50V", C, C12, {"1": "V5", "2": "GND"}, "Entrada del buck de 3.3 V"),
    ("C8", "22uF", C, C08, {"1": "3V3", "2": "GND"}, "Salida 3.3 V"),
    ("C9", "22uF", C, C08, {"1": "3V3", "2": "GND"}, "Salida 3.3 V"),
    # --- cerebro ---
    ("U3", "ESP32-C3-WROOM-02", "RF_Module:ESP32-C3-WROOM-02", "LetreroLab:ESP32-C3-WROOM-02_JLC",
     {"1": "3V3", "2": "EN", "3": "INT", "4": "SENSE_I", "5": "SENSE_O", "6": None, "7": "SCL", "8": "BOOT",
      "9": "GND", "10": "RS_DE", "11": None, "12": None, "13": "USB_DN", "14": "USB_DP", "15": "RS_RX",
      "16": "SDA", "17": "RS_TX", "18": "VSENSE", "19": "GND"},
     "IO0 = tensión de entrada, IO1/IO3/IO10 = RS-485, IO2/IO8 = I2C, IO4 = interrupción de entradas, IO5 = SENSE_IN, IO6 = SENSE_OUT"),
    ("C10", "10uF", C, C08, {"1": "3V3", "2": "GND"}, "Desacoplo del módulo"),
    ("C11", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo del módulo"),
    ("R1", "10k", R, R06, {"1": "3V3", "2": "EN"}, "Pull-up EN"),
    ("C12", "1uF", C, C06, {"1": "EN", "2": "GND"}, "Arranque retardado"),
    ("R2", "10k", R, R06, {"1": "3V3", "2": "BOOT"}, "Pull-up IO9"),
    ("SW1", "MODO", "Switch:SW_Push", BTN, {"1": "BOOT", "2": "GND"}, "MODO; mantenido al conectar el USB = programar"),
    ("SW2", "RESET", "Switch:SW_Push", BTN, {"1": "EN", "2": "GND"}, "Reinicio"),
    ("R3", "4.7k", R, R06, {"1": "3V3", "2": "SDA"}, "Pull-up I2C"),
    ("R4", "4.7k", R, R06, {"1": "3V3", "2": "SCL"}, "Pull-up I2C"),
    ("R5", "10k", R, R06, {"1": "3V3", "2": "INT"}, "Pull-up de la interrupción de entradas"),
    ("R6", "100k", R, R06, {"1": "V24", "2": "VSENSE"}, "Divisor de la tensión de entrada: 30 V -> 2.7 V"),
    ("R7", "10k", R, R06, {"1": "VSENSE", "2": "GND"}, "Divisor de la tensión de entrada"),
    ("C13", "100nF", C, C06, {"1": "VSENSE", "2": "GND"}, "Filtro del ADC"),
    # --- USB-C ---
    ("J2", "USB-C", "Connector:USB_C_Receptacle_USB2.0_16P", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
     {"A1": "GND", "A4": "VBUS", "A5": "CC1U", "A6": "USB_DP", "A7": "USB_DN", "A8": None, "A9": "VBUS",
      "B1": "GND", "B4": "VBUS", "B5": "CC2U", "B6": "USB_DP", "B7": "USB_DN", "B8": None, "B9": "VBUS",
      "S1": "GND", "A12": "GND", "B12": "GND"}, "USB-C: programar y probar"),
    ("R8", "5.1k", R, R06, {"1": "CC1U", "2": "GND"}, "CC1"),
    ("R9", "5.1k", R, R06, {"1": "CC2U", "2": "GND"}, "CC2"),
    ("U4", "USBLC6-2SC6", "Power_Protection:USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "USB_DN", "2": "GND", "3": "USB_DP", "4": "USB_DP", "5": "VBUS", "6": "USB_DN"}, "ESD del USB"),
    # --- AP LINK ---
    ("JL1", "AP LINK ENTRA", conectores.SYM[4], conectores.XH4, {"1": "SENSE_IC", "2": "RSB", "3": "RSA", "4": "GND"},
     "ENTRA (viene del módulo anterior o del cabeza): 1 = SENSE, 2 = B (D-), 3 = A (D+), 4 = 0 V. NO conectar un cable de AP BUS"),
    ("JL2", "AP LINK SIGUE", conectores.SYM[4], conectores.XH4, {"1": "SENSE_OC", "2": "RSB", "3": "RSA", "4": "GND"},
     "SIGUE (va al módulo siguiente): mismas patas; A, B y 0 V unidos con ENTRA. Cable 1 a 1. NO conectar un cable de AP BUS"),
    ("U5", "SP3485EN", "Interface_UART:SP3485EN", SOIC8,
     {"1": "RS_RX", "2": "RS_DE", "3": "RS_DE", "4": "RS_TX", "5": "GND", "6": "RSA", "7": "RSB", "8": "3V3"},
     "Transceptor RS-485 a 3.3 V (sin aislar: el cable lleva 0 V común)"),
    ("C14", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo del SP3485"),
    ("R10", "10k", R, R06, {"1": "RS_DE", "2": "GND"}, "Recibir al arrancar"),
    ("D4", "SM712", "Diode:SM712_SOT23", "Package_TO_SOT_SMD:SOT-23", {"1": "RSA", "2": "RSB", "3": "GND"}, "Protección de la línea"),
    ("R11", "120", R, R12, {"1": "RSA", "2": "TERM"}, "Terminación"),
    ("JP1", "120R", "Jumper:SolderJumper_2_Open", SJO, {"1": "TERM", "2": "RSB"}, "Cerrar solo en el ÚLTIMO módulo de la cadena"),
    ("R12", "680", R, R06, {"1": "PA", "2": "RSA"}, "Polarización A"),
    ("R13", "680", R, R06, {"1": "RSB", "2": "PB"}, "Polarización B"),
    ("JP2", "POL A", "Jumper:SolderJumper_2_Open", SJO, {"1": "3V3", "2": "PA"}, "Cerrar solo en el PRIMER módulo (cabeza)"),
    ("JP3", "POL B", "Jumper:SolderJumper_2_Open", SJO, {"1": "PB", "2": "GND"}, "Cerrar solo en el PRIMER módulo (cabeza)"),
    ("R14", "10k", R, R06, {"1": "SENSE_IC", "2": "SENSE_I"}, "SENSE_IN: serie de 10 k (si entra un cable equivocado limita la corriente)"),
    ("R15", "100k", R, R06, {"1": "3V3", "2": "SENSE_I"}, "SENSE_IN: sin cable vale 1 (el cabeza de la cadena)"),
    ("R16", "1k", R, R06, {"1": "SENSE_O", "2": "SENSE_OC"}, "SENSE_OUT: serie de 1 k"),
    ("R17", "10k", R, R06, {"1": "SENSE_OC", "2": "GND"}, "SENSE_OUT vale 0 sin programa o sin energía: el siguiente módulo queda en espera"),
    # --- expansores ---
    tca("U6", ("GND", "GND", "GND"), ["IN%d" % k for k in range(1, 9)], "0x20: P0-P7 = compuertas de las salidas 1-8"),
    ("C15", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U6"),
    tca("U7", ("3V3", "GND", "GND"), ["IN%d" % k for k in range(9, 17)], "0x21: P0-P7 = compuertas de las salidas 9-16"),
    ("C16", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U7"),
    tca("U8", ("GND", "3V3", "GND"), ["E%d" % k for k in range(1, 9)], "0x22: P0-P7 = entradas 1-8 (0 = activa)", int_net="INT"),
    ("C17", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U8"),
    tca("U9", ("3V3", "3V3", "GND"), ["LP1", "LP2", "LP4", "LP8", "LRUN", "LFAL", "LCOM", "LHEAD"],
        "0x23: P0-P3 = LED de posición (1, 2, 4, 8), P4 RUN, P5 FALLA, P6 COM, P7 CABEZA"),
    ("C18", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U9"),
]
# --- compuertas: 4 x 74HCT125, 4 salidas cada una ---
for i in range(4):
    u = "U%d" % (10 + i)
    base = 4 * i
    p = {"14": "V5", "1": "GND", "4": "GND", "10": "GND", "13": "GND", "7": "GND"}
    p.update({"2": "IN%d" % (base + 1), "3": "G%d" % (base + 1), "5": "IN%d" % (base + 2), "6": "G%d" % (base + 2),
              "9": "IN%d" % (base + 3), "8": "G%d" % (base + 3), "12": "IN%d" % (base + 4), "11": "G%d" % (base + 4)})
    C_ += [(u, "74HCT125D", "74xx:74LS125", SOIC14, p, "Compuertas %d-%d a 5 V (entradas TTL)" % (base + 1, base + 4)),
           ("C%d" % (19 + i), "100nF", C, C06, {"1": "V5", "2": "GND"}, "Desacoplo %s" % u)]
# --- LED del panel (de TCA 0x23) ---
LEDS = [("LP1", "VERDE", "posición 1"), ("LP2", "VERDE", "posición 2"), ("LP4", "VERDE", "posición 4"), ("LP8", "VERDE", "posición 8"),
        ("LRUN", "VERDE", "RUN"), ("LFAL", "ROJO", "FALLA"), ("LCOM", "AMARILLO", "COM (tramas del enlace)"), ("LHEAD", "VERDE", "CABEZA")]
for k, (red, color, txt) in enumerate(LEDS, start=1):
    C_ += [("RP%d" % k, "1k", R, R06, {"1": red, "2": red + "A"}, "LED %s" % txt),
           ("DP%d" % k, color, "Device:LED", LED06, {"1": "GND", "2": red + "A"}, "LED %s" % txt)]
# --- entradas ---
for k in range(1, NENT + 1):
    C_ += [
        ("RA%d" % k, "3.3k", R, R08, {"1": "IN%dX" % k, "2": "IA%d" % k}, "Entrada %d (1 de 2)" % k),
        ("RC%d" % k, "3.3k", R, R08, {"1": "IA%d" % k, "2": "IB%d" % k}, "Entrada %d (2 de 2)" % k),
        ("LI%d" % k, "VERDE", "Device:LED", LED06, {"1": "IL%d" % k, "2": "IB%d" % k}, "Entrada %d activa" % k),
        ("RS%d" % k, "2.2k", R, R06, {"1": "IL%d" % k, "2": "COMI"}, "Umbral: apagada por debajo de ~5 V"),
        ("DI%d" % k, "1N4148W", "Device:D", "Diode_SMD:D_SOD-123", {"1": "IB%d" % k, "2": "COMI"}, "Entrada %d: polaridad invertida" % k),
        ("OK%d" % k, "LTV-217-B", "Isolator:PC817", "Package_SO:SOP-4_4.4x2.6mm_P1.27mm",
         {"1": "IL%d" % k, "2": "COMI", "3": "GND", "4": "E%d" % k}, "Optoacoplador de la entrada %d" % k),
        ("RQ%d" % k, "10k", R, R06, {"1": "3V3", "2": "E%d" % k}, "Pull-up de la entrada %d" % k),
    ]
# las entradas llegan por 3 borneras de 3 polos
C_ += [("J3", "KF128-5.08-3P", "Connector:Screw_Terminal_01x03", KF3, {"1": "IN1X", "2": "IN2X", "3": "IN3X"}, "Entradas 1-3"),
       ("J4", "KF128-5.08-3P", "Connector:Screw_Terminal_01x03", KF3, {"1": "IN4X", "2": "IN5X", "3": "IN6X"}, "Entradas 4-6"),
       ("J5", "KF128-5.08-3P", "Connector:Screw_Terminal_01x03", KF3, {"1": "IN7X", "2": "IN8X", "3": "COMI"},
        "Entradas 7-8 y común de entradas (0 V del sensor)")]
# --- salidas ---
for k in range(1, NSAL + 1):
    C_ += [
        ("Q%d" % k, "NCV8406ASTT3G", "Transistor_FET:Q_NMOS_GDS", "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
         {"1": "G%d" % k, "2": "Q%d" % k, "3": "GND"}, "Salida %d: MOSFET protegido 65 V (corto, sobrecorriente, temperatura)" % k),
        ("DQ%d" % k, "SS14", "Device:D_Schottky", SMA, {"1": "V24", "2": "Q%d" % k}, "Diodo de bobina de la salida %d" % k),
        ("RD%d" % k, "10k", R, R06, {"1": "IN%d" % k, "2": "GND"}, "Salida %d apagada al arrancar" % k),
        ("RL%d" % k, "15k", R, R06, {"1": "V24", "2": "LA%d" % k}, "LED de la salida %d (2 mA a 30 V)" % k),
        ("DL%d" % k, "VERDE", "Device:LED", LED06, {"1": "Q%d" % k, "2": "LA%d" % k}, "Salida %d activa" % k),
    ]
for b in range(1, 9):
    C_.append(("J%d" % (5 + b), "KF128-5.08-3P", "Connector:Screw_Terminal_01x03", KF3,
               {"1": "Q%d" % (2 * b - 1), "2": "V24", "3": "Q%d" % (2 * b)},
               "Salidas %d y %d: 1 = salida %d, 2 = +V, 3 = salida %d. La carga va entre +V y la salida" % (2 * b - 1, 2 * b, 2 * b - 1, 2 * b)))
TPS = [("TP1", "V24", "+V"), ("TP2", "V5", "5V"), ("TP3", "3V3", "3V3"), ("TP4", "GND", "GND"), ("TP5", "SDA", "SDA"),
       ("TP6", "SCL", "SCL"), ("TP7", "RSA", "A"), ("TP8", "RSB", "B"), ("TP9", "SENSE_I", "SI"), ("TP10", "SENSE_O", "SO")]
for ref, red, txt in TPS:
    C_.append((ref, "TP " + txt, "Connector:TestPoint", TP, {"1": red}, "Punto de prueba %s" % txt))

W, H = 176.0, 100.0
RADIO_ESQUINA = 2.0
HOLES = [(3.5, 3.5), (172.5, 3.5), (3.5, 96.5), (172.5, 96.5)]
PX = 17.2                                                # separación de los bloques de salida
X0 = 36.0                                                # pata 1 del primer bloque
YT = 6.4                                                 # patas de las bornas de salida (arriba)
YTR = 15.0                                               # tronco de +V debajo de las bornas
XOUT = {}                                                # centro de la celda de cada salida
for b in range(8):
    XOUT[2 * b + 1] = X0 + PX * b + 0.1
    XOUT[2 * b + 2] = X0 + PX * b + 8.7
POS = {
    # entrada de potencia (esquina superior izquierda)
    "J1": (11.0, 9.0, 0), "F1": (17.0, 16.6, 0), "D1": (10.0, 26.0, 0), "C1": (15.0, 26.0, 90), "C2": (18.5, 26.0, 90),
    # 5 V y 3.3 V
    "U1": (62.0, 76.0, 0), "L1": (70.0, 76.0, 0), "D2": (62.0, 82.0, 0), "C3": (66.5, 72.0, 0), "C4": (57.0, 80.0, 90),
    "C5": (77.0, 76.0, 90), "RB1": (68.0, 81.5, 0), "RB2": (72.5, 81.5, 0), "D3": (80.0, 82.0, 90),
    "U2": (92.0, 76.0, 0), "L2": (100.0, 76.0, 0), "C6": (96.5, 72.0, 0), "C7": (86.5, 80.0, 90),
    "C8": (106.5, 76.0, 90), "C9": (109.5, 76.0, 90),
    # cerebro
    "U3": (156.0, 78.0, 270), "C10": (147.0, 68.0, 90), "C11": (147.0, 72.0, 90), "R1": (144.0, 76.4, 90), "C12": (147.0, 76.0, 90),
    "R2": (144.0, 81.0, 90), "SW1": (141.5, 66.0, 0), "SW2": (141.5, 72.0, 0),
    "R3": (118.0, 70.0, 90), "R4": (120.5, 70.0, 90), "R5": (123.0, 70.0, 90), "R6": (126.0, 70.0, 90), "R7": (128.5, 70.0, 90), "C13": (131.0, 70.0, 90),
    "J2": (104.0, 94.5, 0), "R8": (112.0, 90.0, 90), "R9": (112.0, 86.0, 90), "U4": (131.0, 82.0, 0),
    # AP LINK
    "JL1": (64.0, 95.0, 0), "JL2": (80.0, 95.0, 0),
    "U5": (74.0, 62.0, 90), "C14": (80.0, 62.0, 90), "R10": (68.0, 58.5, 90), "D4": (86.0, 62.0, 0),
    "R11": (92.0, 62.0, 0), "JP1": (97.5, 62.0, 0), "R12": (101.0, 62.0, 0), "R13": (104.5, 62.0, 0),
    "JP2": (108.5, 62.0, 0), "JP3": (112.5, 62.0, 0),
    "R14": (60.0, 88.0, 0), "R15": (64.0, 88.0, 0), "R16": (84.0, 88.0, 0), "R17": (88.0, 88.0, 0),
    # expansores
    "U6": (40.0, 54.0, 0), "C15": (45.0, 54.0, 90), "U7": (90.0, 54.0, 0), "C16": (95.0, 54.0, 90),
    "U8": (62.0, 66.0, 0), "C17": (67.0, 66.0, 90), "U9": (123.0, 62.0, 0), "C18": (128.0, 62.0, 90),
}
for k in range(1, 5):
    POS["U%d" % (9 + k)] = (X0 + PX * (2 * (k - 1)) + 12.0, 46.0, 90)
    POS["C%d" % (18 + k)] = (X0 + PX * (2 * (k - 1)) + 18.5, 46.0, 90)
for k in range(1, 9):
    POS["RP%d" % k] = (115.0 + 3.6 * (k - 1), 90.0, 90)
    POS["DP%d" % k] = (115.0 + 3.6 * (k - 1), 86.0, 90)
for k in range(1, 9):
    xi = 5.0 + 5.9 * (k - 1)
    POS.update({"RQ%d" % k: (xi + 1.0, 60.5, 90), "OK%d" % k: (xi + 1.0, 66.5, 90), "LI%d" % k: (xi, 72.5, 90),
                "RS%d" % k: (xi + 2.7, 72.5, 90), "RC%d" % k: (xi, 77.5, 90), "DI%d" % k: (xi + 2.7, 77.0, 90),
                "RA%d" % k: (xi + 0.6, 82.5, 0)})
POS.update({"J3": (10.6, 94.0, 0), "J4": (27.2, 94.0, 0), "J5": (44.4, 94.0, 0)})
for k in range(1, NSAL + 1):
    xc = XOUT[k]
    POS.update({"Q%d" % k: (xc, 31.5, 90), "DQ%d" % k: (xc - 1.9, 21.5, 270), "RD%d" % k: (xc, 39.0, 90),
                "RL%d" % k: (xc + 2.3, 20.5, 90), "DL%d" % k: (xc + 2.3, 24.0, 90)})
for b in range(1, 9):
    POS["J%d" % (5 + b)] = (X0 + PX * (b - 1), YT, 180)
_tpx = [124.0, 129.0, 134.0, 139.0, 144.0, 149.0, 132.0, 137.0, 142.0, 147.0]
for i, (ref, red, txt) in enumerate(TPS):
    POS[ref] = (_tpx[i], 98.0 if i < 6 else 52.0, 0)

NETCLASS = {"Potencia": (1.5, 0.3, ["VIN_RAW"]),
            "Media": (0.8, 0.2, ["V24", "V5"] + ["Q%d" % k for k in range(1, NSAL + 1)]),
            "Bus": (0.25, 0.2, ["RSA", "RSB"])}
PRE = []
SIN_COBRE = [[(163.0, 56.0), (175.7, 56.0), (175.7, 99.7), (163.0, 99.7)]]       # antena del ESP32
SILK = [
    ("AP ELECTRIC INDUSTRIAL  AP RACK 16  rev A", 72.0, 52.0, 1.3, "F"),
    ("+V  0V", 66.0, 1.6, 0.8, "F"),
    ("I1 I2 I3 I4 I5 I6 I7 I8 COM", 6.0, 2.0, 0.8, "F"),
    ("ENTRA", 146.0, 90.5, 0.8, "F"), ("SIGUE", 160.0, 90.5, 0.8, "F"),
    ("MODULO 8 4 2 1", 148.0, 63.5, 0.8, "F"), ("RUN FALLA COM CABEZA", 158.0, 73.2, 0.8, "F"),
    ("AP ELECTRIC AP RACK 16 rev A - CONCEPTO. 12-30 V CC. Carga entre +V y la salida. Red solo con contactor. SENSE/A/B: solo AP LINK, no AP BUS.", 88.0, 98.5, 0.8, "B"),
]
FLAGS = [("GND", 96.52, 20.32), ("VIN_RAW", 20.32, 20.32), ("V24", 35.56, 20.32), ("V5", 50.8, 20.32), ("3V3", 66.04, 20.32), ("COMI", 81.28, 20.32)]
NOTES = [(150.0, 15.0, "AP Electric Industrial · AP Rack 16 rev A (CONCEPTO): 16 x NCV8406A, 4 x 74HCT125, 4 x TCA9554 (0x20-0x23),\n"
                       "8 entradas de 12-30 V LTV-217, SP3485 + 2 x JST XH4 (AP LINK, cadena con SENSE), ESP32-C3. Sin red de CA.")]
TITLE = "AP Electric Industrial · AP Rack 16 rev A - 16 salidas protegidas, 8 entradas, AP LINK (CONCEPTO)"
SUBTITLES = ["Placa de 2 capas, 2 oz (JLCPCB)", "Estado: concepto. Límites del producto por determinar por ensayo"]
COMPANY = "PCB 176 x 100 mm, 2 capas, 2 oz"
COSTURA = 5.0
PAPER = "A3"
OCULTAR_REF = tuple("J%d" % k for k in range(1, 14)) + tuple(["JL1", "JL2"] + ["RL%d" % k for k in range(1, 17)] + ["RD%d" % k for k in range(1, 17)])

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
