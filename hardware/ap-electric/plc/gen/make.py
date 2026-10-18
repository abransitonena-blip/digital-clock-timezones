"""AP Electric Industrial · AP PLC C24 rev A (CONCEPTO): PLC compacto con 12 entradas, 12 salidas protegidas, Ethernet y AP LINK.

Una sola placa de CC (12-30 V) pensada como los PLC compactos de tablero (cuerpo único con bornas arriba y abajo): CPU, entradas, salidas, Ethernet y
el enlace AP LINK para sumarle los módulos AP Rack (IN16, AI8, LED8, RL4, AO4, Rack16). Sin red de CA: las cargas de red se mandan con contactor o relevador de riel DIN.

Parte de AP Rack 16 (misma potencia, salidas NCV8406A, entradas LTV-217 y AP LINK) y agrega:
- Ethernet 10/100: W5500 (SPI) + RJ45 con magnéticos HR911105A, cristal de 25 MHz. El ESP32-C3 no tiene MAC Ethernet.
- 12 salidas (6 borneras de 3 polos) y 12 entradas (4 borneras de entradas + 1 de comunes).
- Botón RUN/STOP leído por un quinto TCA9554 (0x24) y 4 LED de usuario que el programa del PLC puede mover.
- LED de energía y de enlace Ethernet por hardware (el de enlace lo maneja el W5500).
Cambios por falta de pines del ESP32-C3-WROOM-02: el SPI del W5500 usa IO7 (SCK), IO20 (MISO), IO21 (MOSI) e IO0 (CS), así que se quita la medición de la
tensión de entrada que tenía AP Rack 16; el W5500 no usa INT (el programa consulta) y su reset es un RC. No hay reloj con pila en esta revisión (la hora sale de NTP por Ethernet).

    bash ../../tools/rutear.sh ap-electric/plc AP_PLC_C24
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import placa  # noqa: E402
import conectores  # noqa: E402

PROJECT = "AP_PLC_C24"
NS = uuid.UUID("3b7e9a1c-52d4-4f68-a0c3-6d8e1f4b7a25")
ROOT_UUID = "6a1c3e5b-7d9f-4b2a-8c4e-0f2a4c6e8b19"
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
NSAL, NENT = 12, 12


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
     {"1": "3V3", "2": "V5", "3": "V5", "4": "GND", "5": "SWP", "6": "BSTP"}, "Buck 3.3 V (síncrono, 2 A): ESP32 y W5500"),
    ("L2", "4.7uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR4030S", {"1": "SWP", "2": "3V3"}, "Bobina 3.3 V"),
    ("C6", "100nF", C, C06, {"1": "BSTP", "2": "SWP"}, "Bootstrap"),
    ("C7", "10uF 50V", C, C12, {"1": "V5", "2": "GND"}, "Entrada del buck de 3.3 V"),
    ("C8", "22uF", C, C08, {"1": "3V3", "2": "GND"}, "Salida 3.3 V"),
    ("C9", "22uF", C, C08, {"1": "3V3", "2": "GND"}, "Salida 3.3 V"),
    # --- cerebro ---
    ("U3", "ESP32-C3-WROOM-02", "RF_Module:ESP32-C3-WROOM-02", "LetreroLab:ESP32-C3-WROOM-02_JLC",
     {"1": "3V3", "2": "EN", "3": "INT", "4": "SENSE_I", "5": "SENSE_O", "6": "ETH_SCK", "7": "SCL", "8": "BOOT",
      "9": "GND", "10": "RS_DE", "11": "ETH_MISO", "12": "ETH_MOSI", "13": "USB_DN", "14": "USB_DP", "15": "RS_RX",
      "16": "SDA", "17": "RS_TX", "18": "ETH_CS", "19": "GND"},
     "IO0 = CS del W5500, IO7/IO20/IO21 = SCK/MISO/MOSI del W5500, IO1/IO3/IO10 = RS-485, IO2/IO8 = I2C, IO4 = interrupción de entradas, IO5 = SENSE_IN, IO6 = SENSE_OUT"),
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
     "ENTRA (queda libre en el PLC, que es la cabeza): 1 = SENSE, 2 = B (D-), 3 = A (D+), 4 = 0 V. NO conectar un cable de AP BUS"),
    ("JL2", "AP LINK SIGUE", conectores.SYM[4], conectores.XH4, {"1": "SENSE_OC", "2": "RSB", "3": "RSA", "4": "GND"},
     "SIGUE (va al primer módulo AP Rack): mismas patas; A, B y 0 V unidos con ENTRA. Cable 1 a 1. NO conectar un cable de AP BUS"),
    ("U5", "SP3485EN", "Interface_UART:SP3485EN", SOIC8,
     {"1": "RS_RX", "2": "RS_DE", "3": "RS_DE", "4": "RS_TX", "5": "GND", "6": "RSA", "7": "RSB", "8": "3V3"},
     "Transceptor RS-485 a 3.3 V (sin aislar: el cable lleva 0 V común)"),
    ("C14", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo del SP3485"),
    ("R10", "10k", R, R06, {"1": "RS_DE", "2": "GND"}, "Recibir al arrancar"),
    ("D4", "SM712", "Diode:SM712_SOT23", "Package_TO_SOT_SMD:SOT-23", {"1": "RSA", "2": "RSB", "3": "GND"}, "Protección de la línea"),
    ("R11", "120", R, R12, {"1": "RSA", "2": "TERM"}, "Terminación"),
    ("JP1", "120R", "Jumper:SolderJumper_2_Open", SJO, {"1": "TERM", "2": "RSB"}, "Cerrar solo en el ÚLTIMO módulo de la cadena (el PLC solo si va solo)"),
    ("R12", "680", R, R06, {"1": "PA", "2": "RSA"}, "Polarización A"),
    ("R13", "680", R, R06, {"1": "RSB", "2": "PB"}, "Polarización B"),
    ("JP2", "POL A", "Jumper:SolderJumper_2_Open", SJO, {"1": "3V3", "2": "PA"}, "Cerrar en el PLC (cabeza de la cadena)"),
    ("JP3", "POL B", "Jumper:SolderJumper_2_Open", SJO, {"1": "PB", "2": "GND"}, "Cerrar en el PLC (cabeza de la cadena)"),
    ("R14", "10k", R, R06, {"1": "SENSE_IC", "2": "SENSE_I"}, "SENSE_IN: serie de 10 k (si entra un cable equivocado limita la corriente)"),
    ("R15", "100k", R, R06, {"1": "3V3", "2": "SENSE_I"}, "SENSE_IN: sin cable vale 1 (el cabeza de la cadena)"),
    ("R16", "1k", R, R06, {"1": "SENSE_O", "2": "SENSE_OC"}, "SENSE_OUT: serie de 1 k"),
    ("R17", "10k", R, R06, {"1": "SENSE_OC", "2": "GND"}, "SENSE_OUT vale 0 sin programa o sin energía: el siguiente módulo queda en espera"),
    # --- expansores ---
    tca("U6", ("GND", "GND", "GND"), ["IN%d" % k for k in range(1, 9)], "0x20: P0-P7 = compuertas de las salidas 1-8"),
    ("C15", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U6"),
    tca("U7", ("3V3", "GND", "GND"), ["IN%d" % k for k in range(9, 13)] + ["UN"] * 4,
        "0x21: P0-P3 = compuertas de las salidas 9-12; P4-P7 sin uso (con pull-up)"),
    ("C16", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U7"),
    tca("U8", ("GND", "3V3", "GND"), ["E%d" % k for k in range(1, 9)], "0x22: P0-P7 = entradas 1-8 (0 = activa)", int_net="INT"),
    ("C17", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U8"),
    tca("U9", ("3V3", "3V3", "GND"), ["LRUN", "LFAL", "LCOM", "LNET", "LU1", "LU2", "LU3", "LU4"],
        "0x23: P0 RUN, P1 FALLA, P2 COM (AP LINK), P3 NET (Ethernet), P4-P7 = LED de usuario del programa del PLC"),
    ("C18", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U9"),
    tca("U15", ("GND", "GND", "3V3"), ["E9", "E10", "E11", "E12", "BRS", "UN", "UN", "UN"],
        "0x24: P0-P3 = entradas 9-12 (0 = activa), P4 = botón RUN/STOP (0 = pulsado), P5-P7 sin uso (con pull-up)", int_net="INT"),
    ("C22", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U15"),
    ("R27", "10k", R, R06, {"1": "3V3", "2": "BRS"}, "Pull-up del botón RUN/STOP"),
    ("R28", "10k", R, R06, {"1": "3V3", "2": "UN"}, "Pull-up de los pines sin uso de los TCA9554"),
    ("SW3", "RUN/STOP", "Switch:SW_Push", BTN, {"1": "BRS", "2": "GND"}, "Botón RUN/STOP: cada pulsación alterna RUN y STOP (el programa guarda el estado)"),
    ("C34", "100nF", C, C06, {"1": "BRS", "2": "GND"}, "Antirrebote del botón RUN/STOP"),
    # --- Ethernet: W5500 + RJ45 con magnéticos ---
    ("U16", "W5500", "Interface_Ethernet:W5500", "Package_QFP:LQFP-48_7x7mm_P0.5mm",
     {"1": "ETH_TXN", "2": "ETH_TXP", "3": "GND", "4": "3V3", "5": "ETH_RXN", "6": "ETH_RXP", "7": None, "8": "3V3", "9": "GND",
      "10": "EXRES", "11": "3V3", "12": None, "13": None, "14": "GND", "15": "3V3", "16": "GND", "17": "3V3", "18": None, "19": "GND",
      "20": "TOCAP", "21": "3V3", "22": "V1P2", "23": "GND", "24": None, "25": "LINKLED", "26": None, "27": None, "28": "3V3",
      "29": "GND", "30": "XI", "31": "XO", "32": "ETH_CS", "33": "ETH_SCK", "34": "ETH_MISO", "35": "ETH_MOSI", "36": None,
      "37": "ETH_RST", "38": "GND", "39": "GND", "40": "GND", "41": "GND", "42": "GND", "43": "3V3", "44": "3V3", "45": "3V3",
      "46": None, "47": None, "48": "GND"},
     "Ethernet 10/100 por SPI. PMODE = 111 (negociación automática). Pines reservados a 0 V y DNC sin conectar, como en la referencia del fabricante [CG]"),
    ("Y1", "25MHz", "Device:Crystal_GND24", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", {"1": "XI", "2": "GND", "3": "XO", "4": "GND"}, "Cristal de 25 MHz, 18 pF de carga"),
    ("C24", "18pF", C, C06, {"1": "XI", "2": "GND"}, "Carga del cristal"),
    ("C25", "18pF", C, C06, {"1": "XO", "2": "GND"}, "Carga del cristal"),
    ("R19", "12k", R, R06, {"1": "EXRES", "2": "EXMID"}, "EXRES1 del W5500: 12 kΩ + 390 Ω en serie = 12.39 kΩ (la referencia pide 12.4 kΩ 1 %; sin código LCSC de 0603 con existencias confirmado). Otro valor deja el chip sin responder"),
    ("R30", "390", R, R06, {"1": "EXMID", "2": "GND"}, "EXRES1 del W5500: segunda parte de 12.39 kΩ"),
    ("C23", "4.7uF", C, C08, {"1": "TOCAP", "2": "GND"}, "TOCAP del W5500"),
    ("C26", "10nF", C, C06, {"1": "V1P2", "2": "GND"}, "1V2O del W5500"),
    ("C27", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo analógico W5500"),
    ("C28", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo analógico W5500"),
    ("C29", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo digital W5500"),
    ("C30", "10uF", C, C08, {"1": "3V3", "2": "GND"}, "Reserva del W5500"),
    ("R18", "10k", R, R06, {"1": "3V3", "2": "ETH_CS"}, "CS del W5500 inactivo al arrancar (IO0 flota durante el arranque)"),
    ("R24", "10k", R, R06, {"1": "3V3", "2": "ETH_RST"}, "Reset del W5500: pull-up y RC"),
    ("C33", "100nF", C, C06, {"1": "ETH_RST", "2": "GND"}, "Reset del W5500: retardo al energizar"),
    ("J14", "HR911105A", "Connector:RJ45_Hanrun_HR911105A_Horizontal", "Connector_RJ:RJ45_Hanrun_HR911105A_Horizontal",
     {"1": "ETH_TXP", "2": "ETH_TXN", "3": "ETH_RXP", "4": "ETH_CT", "5": "ETH_CT", "6": "ETH_RXN", "7": None, "8": None,
      "9": None, "10": None, "11": None, "12": None, "SH": "GND"}, "RJ45 con magnéticos y LED: Ethernet"),
    ("R20", "49.9", R, R06, {"1": "ETH_TXP", "2": "ETH_TERM"}, "Terminación del par de transmisión [CG: confirmar con el esquema de referencia de WIZnet]"),
    ("R21", "49.9", R, R06, {"1": "ETH_TXN", "2": "ETH_TERM"}, "Terminación del par de transmisión"),
    ("R22", "49.9", R, R06, {"1": "ETH_RXP", "2": "ETH_TERM"}, "Terminación del par de recepción"),
    ("R23", "49.9", R, R06, {"1": "ETH_RXN", "2": "ETH_TERM"}, "Terminación del par de recepción"),
    ("C31", "10nF", C, C06, {"1": "ETH_TERM", "2": "GND"}, "Terminación de las líneas Ethernet"),
    ("C32", "100nF", C, C06, {"1": "ETH_CT", "2": "GND"}, "Tomas centrales de los magnéticos"),
    ("R29", "0", R, R06, {"1": "3V3", "2": "ETH_CT"}, "Alimenta las tomas centrales desde 3.3 V"),
    # LED de energía y de enlace Ethernet (hardware)
    ("RPW", "1k", R, R06, {"1": "3V3", "2": "PWA"}, "LED de energía"),
    ("DPW", "VERDE", "Device:LED", LED06, {"1": "GND", "2": "PWA"}, "LED de energía (3.3 V)"),
    ("RLK", "1k", R, R06, {"1": "3V3", "2": "LKA"}, "LED de enlace Ethernet"),
    ("DLK", "VERDE", "Device:LED", LED06, {"1": "LINKLED", "2": "LKA"}, "LED de enlace Ethernet (lo baja el W5500)"),
]
# --- compuertas: 3 x 74HCT125, 4 salidas cada una ---
for i in range(3):
    u = "U%d" % (10 + i)
    base = 4 * i
    p = {"14": "V5", "1": "GND", "4": "GND", "10": "GND", "13": "GND", "7": "GND"}
    p.update({"2": "IN%d" % (base + 1), "3": "G%d" % (base + 1), "5": "IN%d" % (base + 2), "6": "G%d" % (base + 2),
              "9": "IN%d" % (base + 3), "8": "G%d" % (base + 3), "12": "IN%d" % (base + 4), "11": "G%d" % (base + 4)})
    C_ += [(u, "74HCT125D", "74xx:74LS125", SOIC14, p, "Compuertas %d-%d a 5 V (entradas TTL)" % (base + 1, base + 4)),
           ("C%d" % (19 + i), "100nF", C, C06, {"1": "V5", "2": "GND"}, "Desacoplo %s" % u)]
# --- LED del panel (de TCA 0x23) ---
LEDS = [("LRUN", "VERDE", "RUN"), ("LFAL", "ROJO", "FALLA"), ("LCOM", "AMARILLO", "COM (tramas del enlace)"), ("LNET", "VERDE", "NET (Ethernet)"),
        ("LU1", "VERDE", "usuario 1"), ("LU2", "VERDE", "usuario 2"), ("LU3", "AMARILLO", "usuario 3"), ("LU4", "AMARILLO", "usuario 4")]
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
# las entradas llegan por 4 borneras de 3 polos y una de comunes
for b in range(4):
    C_.append(("J%d" % (3 + b), "KF128-5.08-3P", "Connector:Screw_Terminal_01x03", KF3,
               {"1": "IN%dX" % (3 * b + 1), "2": "IN%dX" % (3 * b + 2), "3": "IN%dX" % (3 * b + 3)}, "Entradas %d-%d" % (3 * b + 1, 3 * b + 3)))
C_.append(("J7", "KF128-5.08-3P", "Connector:Screw_Terminal_01x03", KF3, {"1": "COMI", "2": "COMI", "3": "COMI"},
           "Común de entradas (0 V del sensor), 3 patas unidas"))
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
for b in range(1, 7):
    C_.append(("J%d" % (7 + b), "KF128-5.08-3P", "Connector:Screw_Terminal_01x03", KF3,
               {"1": "Q%d" % (2 * b - 1), "2": "V24", "3": "Q%d" % (2 * b)},
               "Salidas %d y %d: 1 = salida %d, 2 = +V, 3 = salida %d. La carga va entre +V y la salida" % (2 * b - 1, 2 * b, 2 * b - 1, 2 * b)))
TPS = [("TP1", "V24", "+V"), ("TP2", "V5", "5V"), ("TP3", "3V3", "3V3"), ("TP4", "GND", "GND"), ("TP5", "SDA", "SDA"),
       ("TP6", "SCL", "SCL"), ("TP7", "RSA", "A"), ("TP8", "RSB", "B"), ("TP9", "SENSE_I", "SI"), ("TP10", "SENSE_O", "SO")]
for ref, red, txt in TPS:
    C_.append((ref, "TP " + txt, "Connector:TestPoint", TP, {"1": red}, "Punto de prueba %s" % txt))

W, H = 200.0, 100.0
RADIO_ESQUINA = 2.0
HOLES = [(3.5, 3.5), (196.5, 3.5), (3.5, 96.5), (196.5, 96.5)]
PX = 17.2                                                # separación de los bloques de salida
X0 = 36.0                                                # pata 1 del primer bloque
YT = 6.4                                                 # patas de las bornas de salida (arriba)
XOUT = {}                                                # centro de la celda de cada salida
for b in range(6):
    XOUT[2 * b + 1] = X0 + PX * b + 0.1
    XOUT[2 * b + 2] = X0 + PX * b + 8.7
POS = {
    # entrada de potencia (esquina superior izquierda)
    "J1": (11.0, 9.0, 0), "F1": (17.0, 16.6, 0), "D1": (10.0, 26.0, 0), "C1": (15.0, 26.0, 90), "C2": (18.5, 26.0, 90),
    # 5 V y 3.3 V
    "U1": (90.0, 78.0, 0), "L1": (98.0, 78.0, 0), "D2": (90.0, 84.0, 0), "C3": (94.5, 74.0, 0), "C4": (85.0, 82.0, 90),
    "C5": (105.0, 78.0, 90), "RB1": (96.0, 83.5, 0), "RB2": (100.5, 83.5, 0), "D3": (108.0, 84.0, 90),
    "U2": (118.0, 78.0, 0), "L2": (126.0, 78.0, 0), "C6": (122.5, 74.0, 0), "C7": (112.5, 82.0, 90),
    "C8": (132.5, 78.0, 90), "C9": (135.5, 78.0, 90),
    # cerebro
    "U3": (180.0, 78.0, 270), "C10": (171.0, 68.0, 90), "C11": (171.0, 72.0, 90), "R1": (168.0, 76.4, 90), "C12": (171.0, 76.0, 90),
    "R2": (168.0, 81.0, 90), "SW1": (165.5, 66.0, 0), "SW2": (165.5, 72.0, 0),
    "R3": (140.0, 70.0, 90), "R4": (142.5, 70.0, 90), "R5": (145.0, 70.0, 90),
    "J2": (132.0, 94.5, 0), "R8": (140.0, 90.0, 90), "R9": (140.0, 86.0, 90), "U4": (147.0, 84.0, 0),
    "SW3": (153.0, 93.0, 0), "C34": (161.5, 93.0, 0), "R27": (160.5, 87.0, 0), "R28": (155.0, 87.0, 0),
    # AP LINK
    "JL1": (100.0, 95.0, 0), "JL2": (115.0, 95.0, 0),
    "U5": (112.0, 62.0, 90), "C14": (118.0, 62.0, 90), "R10": (106.5, 58.5, 90), "D4": (124.0, 62.0, 0),
    "R11": (130.0, 62.0, 0), "JP1": (135.5, 62.0, 0), "R12": (139.0, 58.0, 0), "R13": (142.5, 58.0, 0),
    "JP2": (146.5, 62.0, 0), "JP3": (150.5, 62.0, 0),
    "R14": (96.0, 88.5, 0), "R15": (100.0, 88.5, 0), "R16": (120.0, 88.5, 0), "R17": (124.0, 88.5, 0),
    # expansores
    "U6": (40.0, 54.0, 0), "C15": (45.0, 54.0, 90), "U7": (90.0, 54.0, 0), "C16": (95.0, 54.0, 90),
    "U8": (84.0, 66.0, 0), "C17": (89.0, 66.0, 90), "U15": (98.0, 66.0, 0), "C22": (103.0, 66.0, 90),
    "U9": (108.0, 54.0, 0), "C18": (113.0, 54.0, 90),
    # Ethernet
    "U16": (165.0, 28.0, 180), "Y1": (150.0, 30.0, 0), "C24": (146.5, 34.0, 0), "C25": (153.5, 34.0, 0),
    "R19": (160.0, 38.5, 0), "R30": (160.0, 41.5, 0), "C23": (165.0, 38.5, 0), "C26": (169.5, 38.5, 0),
    "C27": (172.5, 20.0, 90), "C28": (172.5, 24.0, 90), "C29": (172.5, 33.0, 90), "C30": (157.5, 20.0, 90),
    "R18": (150.0, 24.0, 90), "R24": (153.0, 24.0, 90), "C33": (156.0, 24.0, 90),
    "J14": (183.2, 22.0, 90),
    "R20": (176.5, 38.0, 0), "R21": (176.5, 41.0, 0), "R22": (176.5, 44.0, 0), "R23": (176.5, 47.0, 0),
    "C31": (181.5, 42.5, 90), "C32": (184.5, 42.5, 90), "R29": (187.5, 42.5, 90),
    "RPW": (143.0, 44.0, 0), "DPW": (147.0, 44.0, 0), "RLK": (143.0, 47.0, 0), "DLK": (147.0, 47.0, 0),
}
for k in range(1, 4):
    POS["U%d" % (9 + k)] = (X0 + PX * (2 * (k - 1)) + 12.0, 46.0, 90)
    POS["C%d" % (18 + k)] = (X0 + PX * (2 * (k - 1)) + 18.5, 46.0, 90)
for k in range(1, NENT + 1):
    xi = 5.0 + 5.9 * (k - 1)
    POS.update({"RQ%d" % k: (xi + 1.0, 60.5, 90), "OK%d" % k: (xi + 1.0, 66.5, 90), "LI%d" % k: (xi, 72.5, 90),
                "RS%d" % k: (xi + 2.7, 72.5, 90), "RC%d" % k: (xi, 77.5, 90), "DI%d" % k: (xi + 2.7, 77.0, 90),
                "RA%d" % k: (xi + 0.6, 82.5, 0)})
for i in range(5):
    POS["J%d" % (3 + i)] = (10.6 + 16.8 * i, 94.0, 0)
for k in range(1, NSAL + 1):
    xc = XOUT[k]
    POS.update({"Q%d" % k: (xc, 31.5, 90), "DQ%d" % k: (xc - 1.9, 21.5, 270), "RD%d" % k: (xc, 39.0, 90),
                "RL%d" % k: (xc + 2.3, 20.5, 90), "DL%d" % k: (xc + 2.3, 24.0, 90)})
for b in range(1, 7):
    POS["J%d" % (7 + b)] = (X0 + PX * (b - 1), YT, 180)
# LED del panel: fila de 8 a la derecha de las compuertas
for k in range(1, 9):
    POS["RP%d" % k] = (135.0 + 3.6 * (k - 1), 54.0, 90)
    POS["DP%d" % k] = (135.0 + 3.6 * (k - 1), 50.0, 90)
_tp = [(142.0, 98.0), (147.0, 98.0), (152.0, 98.0), (157.0, 98.0), (162.0, 98.0), (167.0, 98.0), (127.0, 47.5), (131.0, 47.5), (127.0, 44.0), (131.0, 44.0)]
for i, (ref, red, txt) in enumerate(TPS):
    POS[ref] = (_tp[i][0], _tp[i][1], 0)

NETCLASS = {"Potencia": (1.5, 0.3, ["VIN_RAW"]),
            "Media": (0.8, 0.2, ["V24", "V5"] + ["Q%d" % k for k in range(1, NSAL + 1)]),
            "Bus": (0.25, 0.2, ["RSA", "RSB"])}
PRE = []
SIN_COBRE = [[(187.0, 56.0), (199.7, 56.0), (199.7, 99.7), (187.0, 99.7)]]       # antena del ESP32
SILK = [
    ("AP ELECTRIC INDUSTRIAL  AP PLC C24  rev A", 72.0, 49.0, 1.3, "F"),
    ("+V  0V", 66.0, 1.6, 0.8, "F"),
    ("I1-I12 COM", 6.0, 2.0, 0.8, "F"),
    ("ENTRA", 100.0, 90.5, 0.8, "F"), ("SIGUE", 115.0, 90.5, 0.8, "F"),
    ("RUN/STOP", 153.0, 90.0, 0.8, "F"), ("RUN FALLA COM NET U1-U4", 135.0, 47.0, 0.8, "F"),
    ("ETHERNET", 186.0, 48.0, 0.8, "F"),
    ("AP ELECTRIC AP PLC C24 rev A - CONCEPTO. 12-30 V CC. Carga entre +V y la salida. Red solo con contactor. SENSE/A/B: solo AP LINK, no AP BUS.", 88.0, 98.5, 0.8, "B"),
]
FLAGS = [("GND", 96.52, 20.32), ("VIN_RAW", 20.32, 20.32), ("V24", 35.56, 20.32), ("V5", 50.8, 20.32), ("3V3", 66.04, 20.32), ("COMI", 81.28, 20.32)]
NOTES = [(150.0, 15.0, "AP Electric Industrial · AP PLC C24 rev A (CONCEPTO): 12 x NCV8406A, 3 x 74HCT125, 5 x TCA9554 (0x20-0x24),\n"
                       "12 entradas de 12-30 V LTV-217, W5500 + RJ45 (Ethernet), SP3485 + 2 x JST XH4 (AP LINK), ESP32-C3. Sin red de CA.")]
TITLE = "AP Electric Industrial · AP PLC C24 rev A - 12 entradas, 12 salidas protegidas, Ethernet y AP LINK (CONCEPTO)"
SUBTITLES = ["Placa de 2 capas, 2 oz (JLCPCB)", "Estado: concepto. Límites del producto por determinar por ensayo"]
COMPANY = "PCB 200 x 100 mm, 2 capas, 2 oz"
COSTURA = 5.0
PAPER = "A3"
OCULTAR_REF = tuple("J%d" % k for k in range(1, 15)) + tuple(["JL1", "JL2"] + ["RL%d" % k for k in range(1, 13)] + ["RD%d" % k for k in range(1, 13)])

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
