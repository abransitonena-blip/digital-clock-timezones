"""LetreroLab AP-0.2 - controlador Wi-Fi de potencia, 1 sola placa de 2 capas, armada en fábrica (JLCPCB).

- ESP32-C3-WROOM-02 (Wi-Fi + Bluetooth LE, certificado), programación por USB-C nativo (sin chip USB-serie).
- Entrada 12-24 V DC hasta 20 A: fusible ATO, protección contra polaridad invertida sin pérdidas (2 MOSFET de 60 V
  en paralelo, ideal-diode en el negativo), TVS SMBJ33A, capacitores de 470 uF.
- 4 canales de potencia: MOSFET BSC028N06LS3 (60 V, 2.8 mOhm) con driver UCC27524 a 12 V -> 8 A por canal
  (20 A en total), PWM rápido y frío.
- Fuentes: buck LMR16006 de 60 V (12 V para drivers, relevador y lógica) y buck AP63203 (3.3 V desde esos 12 V).
- Medición y protección (rev B): INA238 + shunt Kelvin de 1 mOhm (V, A, W, kWh, alerta de sobrecorriente) y TMP1075
  junto a los MOSFET; ambas alertas a IO20. Puntos de prueba para la prueba en fábrica.
- Relevador de 10 A con contacto seco para focos de 127/240 V (separación >= 5 mm).
- Expansión: I2C (reloj/sensores), receptor IR, LDR y botón externo.

    bash gen/rutear.sh             (todo el flujo: placa, Freerouting en 3 pasadas, planos, ERC/DRC)
"""
import os, sys, json, uuid, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "fuente-os-127v", "gen"))
import comun  # noqa: E402
import pcbnew  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, ".."))
KI = os.path.join(ROOT, "kicad")
PROJECT = "AP02"
NS = uuid.UUID("9e5f4c11-7a6b-4d8e-b2a5-4c8e6f1a2b75")
ROOT_UUID = "a06f5d22-8b7c-4e9f-c3b6-5d9f7a2b3c86"
FPL = "/usr/share/kicad/footprints"
R06, C06, C08, C12 = ("Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric",
                      "Capacitor_SMD:C_0805_2012Metric", "Capacitor_SMD:C_1206_3216Metric")
TDSON = "Package_TO_SOT_SMD:TDSON-8-1"
MKDS3 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-%d-5.08_1x0%d_P5.08mm_Horizontal"
R, C, CP = "Device:R", "Device:C", "Device:C_Polarized"

ESP = {"1": "3V3", "2": "EN", "3": "PWM1", "4": "PWM2", "5": "PWM3", "6": "PWM4", "7": "SCL", "8": "BOOT",
       "9": "GND", "10": "LED", "11": "ALERT", "12": "TXD", "13": "USB_DN", "14": "USB_DP", "15": "IR", "16": "SDA",
       "17": "RLYG", "18": "LDR", "19": "GND"}
C_ = [
    # --- entrada de potencia ---
    ("J1", "ENTRADA 12-24V", "Connector:Screw_Terminal_01x02", MKDS3 % (2, 2), {"1": "VIN_RAW", "2": "GNDIN"},
     "Entrada 12-24 V DC (+ / -), hasta 20 A"),
    ("F1", "ATO 20A", "Device:Fuse", "Fuse:Fuseholder_Blade_ATO_Littelfuse_Pudenz_2_Pin", {"1": "VIN_RAW", "2": "VFUS"},
     "Fusible de navaja ATO (20 A para tiras, 5 A para letreros)"),
    ("RS1", "1mR 2512 Kelvin", "Device:R_Shunt", "Resistor_SMD:R_Shunt_Vishay_WSK2512_6332Metric_T1.19mm",
     {"1": "VIN", "2": "ISN", "3": "ISP", "4": "VFUS"}, "Shunt de 1 mOhm (4 terminales) para medir la corriente total"),
    ("U7", "INA238", "Sensor_Energy:INA238", "Package_SO:VSSOP-10_3x3mm_P0.5mm",
     {"1": "GND", "2": "GND", "3": "ALERT", "4": "SDA", "5": "SCL", "6": "3V3", "7": "GND", "8": "ISN", "9": "ISN",
      "10": "ISP"}, "Medidor de corriente, voltaje y potencia hasta 85 V (I2C 0x40); alerta por sobrecorriente"),
    ("C17", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo INA238"),
    ("QR1", "BSC028N06LS3", "Transistor_FET:BSC028N06LS3", TDSON, {"1": "GND", "2": "GND", "3": "GND", "4": "GREV",
                                                                    "5": "GNDIN"},
     "Proteccion de polaridad invertida (ideal diode en el negativo)"),
    ("QR2", "BSC028N06LS3", "Transistor_FET:BSC028N06LS3", TDSON, {"1": "GND", "2": "GND", "3": "GND", "4": "GREV",
                                                                    "5": "GNDIN"},
     "Segundo MOSFET en paralelo (20 A)"),
    ("RG0", "10k", R, R06, {"1": "VFUS", "2": "GREV"}, "Compuerta de la proteccion"),
    ("DZ1", "MMSZ5242B 12V", "Device:D_Zener", "Diode_SMD:D_SOD-123", {"1": "GREV", "2": "GND"},
     "Limita la compuerta a 12 V con 24 V de entrada"),
    ("D1", "SMBJ33A", "Device:D_TVS", "Diode_SMD:D_SMB", {"1": "VFUS", "2": "GND"},
     "Supresor de picos (despues del fusible: una falla sostenida abre el fusible)"),
    ("C1", "330uF 50V", CP, "Capacitor_SMD:CP_Elec_10x10.5", {"1": "VFUS", "2": "GND"},
     "Filtro de entrada (50 V, 105 C, bajo ESR, larga vida)"),
    ("C2", "330uF 50V", CP, "Capacitor_SMD:CP_Elec_10x10.5", {"1": "VFUS", "2": "GND"},
     "Filtro de entrada (50 V, 105 C, bajo ESR, larga vida)"),
    ("C3", "4.7uF 50V", C, C12, {"1": "VIN", "2": "GND"}, "Desacoplo de la salida +V junto a J3 (lazo corto con las tiras)"),
    ("J3", "+V SALIDA", "Connector:Screw_Terminal_01x02", MKDS3 % (2, 2), {"1": "VIN", "2": "VIN"},
     "+12/24 V comun de las tiras (2 polos para repartir corriente)"),
    ("J4", "CANALES", "Connector:Screw_Terminal_01x04", MKDS3 % (4, 4),
     {"1": "CH1", "2": "CH2", "3": "CH3", "4": "CH4"}, "Negativo conmutado de cada canal (hasta 8 A c/u)"),
    # --- fuente 3.3 V ---
    ("D2", "SS34", "Device:D_Schottky", "Diode_SMD:D_SMA", {"1": "VLOG", "2": "V12G"},
     "Alimenta la logica desde los 12 V internos"),
    ("D3", "SS34", "Device:D_Schottky", "Diode_SMD:D_SMA", {"1": "VLOG", "2": "VBUS"},
     "Alimenta la logica desde USB (programar sin fuente externa)"),
    ("U1", "AP63203WU", "Regulator_Switching:AP63203WU", "Package_TO_SOT_SMD:TSOT-23-6",
     {"1": "3V3", "2": "VLOG", "3": "VLOG", "4": "GND", "5": "SW1", "6": "BST1"}, "Buck 3.3 V 2 A (entrada 5-12 V: USB o 12 V internos)"),
    ("L1", "4.7uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR4030S", {"1": "SW1", "2": "3V3"}, "Bobina buck 3.3 V"),
    ("C4", "100nF", C, C06, {"1": "BST1", "2": "SW1"}, "Bootstrap"),
    ("C5", "10uF 50V", C, C12, {"1": "VLOG", "2": "GND"}, "Entrada buck 3.3 V"),
    ("C6", "22uF", C, C08, {"1": "3V3", "2": "GND"}, "Salida 3.3 V"),
    ("C7", "22uF", C, C08, {"1": "3V3", "2": "GND"}, "Salida 3.3 V"),
    # --- fuente 12 V para drivers y relevador ---
    ("U2", "LMR16006XDDC", "Regulator_Switching:LMR16006YQ", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "BST2", "2": "GND", "3": "FB2", "4": "VFUS", "5": "VFUS", "6": "SW2"},
     "Buck 12 V de 60 V / 0.6 A, 700 kHz (drivers, relevador y logica): aguanta picos de la entrada"),
    ("L2", "47uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR4030S", {"1": "SW2", "2": "V12G"}, "Bobina buck 12 V"),
    ("C8", "100nF", C, C06, {"1": "BST2", "2": "SW2"}, "Bootstrap"),
    ("C9", "10uF 50V", C, C12, {"1": "VFUS", "2": "GND"}, "Entrada buck 12 V"),
    ("C10", "22uF 25V", C, C12, {"1": "V12G", "2": "GND"}, "Salida 12 V"),
    ("RF1", "150k", R, R06, {"1": "V12G", "2": "FB2"}, "Divisor: 0.765 V x 16 = 12.2 V"),
    ("RF2", "10k", R, R06, {"1": "FB2", "2": "GND"}, "Divisor de 12 V"),
    # --- canales ---
    ("U3", "UCC27524D", "Driver_FET:UCC27524D", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": None, "2": "PWM1", "3": "GND", "4": "PWM2", "5": "GO2", "6": "V12G", "7": "GO1", "8": None},
     "Driver doble canales 1 y 2"),
    ("U4", "UCC27524D", "Driver_FET:UCC27524D", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": None, "2": "PWM3", "3": "GND", "4": "PWM4", "5": "GO4", "6": "V12G", "7": "GO3", "8": None},
     "Driver doble canales 3 y 4"),
    ("U8", "TMP1075D", "Sensor_Temperature:TMP1075D", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "SDA", "2": "SCL", "3": "ALERT", "4": "GND", "5": "GND", "6": "GND", "7": "GND", "8": "3V3"},
     "Temperatura junto a drivers y MOSFET (I2C 0x48); alerta a 85 C"),
    ("C18", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo TMP1075"),
    ("R15", "10k", R, R06, {"1": "3V3", "2": "ALERT"}, "Pull-up de la alerta (IO20)"),
    ("C11", "1uF 25V", C, C06, {"1": "V12G", "2": "GND"}, "Desacoplo driver 1"),
    ("C12", "1uF 25V", C, C06, {"1": "V12G", "2": "GND"}, "Desacoplo driver 2"),
]
for n in range(1, 5):
    C_ += [
        ("Q%d" % n, "BSC028N06LS3", "Transistor_FET:BSC028N06LS3", TDSON,
         {"1": "GND", "2": "GND", "3": "GND", "4": "G%d" % n, "5": "CH%d" % n}, "MOSFET canal %d (60 V, 8 A)" % n),
        ("RG%d" % n, "4.7", R, R06, {"1": "GO%d" % n, "2": "G%d" % n}, "Resistencia de compuerta canal %d" % n),
        ("RP%d" % n, "10k", R, R06, {"1": "G%d" % n, "2": "GND"}, "Canal %d apagado sin driver" % n),
    ]
C_ += [
    # --- relevador ---
    ("K1", "SRD-12VDC-SL-C", "Relay:SANYOU_SRD_Form_C", "Relay_THT:Relay_SPDT_SANYOU_SRD_Series_Form_C",
     {"1": "COM", "2": "RLYD", "3": "NO", "4": "NC_K1", "5": "V12G"}, "Relevador 10 A 250 VCA"),
    ("Q5", "AO3400A", "Transistor_FET:AO3400A", "Package_TO_SOT_SMD:SOT-23", {"1": "RLYG", "2": "GND", "3": "RLYD"},
     "Activa la bobina del relevador"),
    ("D4", "1N4148W", "Device:D", "Diode_SMD:D_SOD-123", {"1": "V12G", "2": "RLYD"}, "Rueda libre de la bobina"),
    ("R5", "100k", R, R06, {"1": "RLYG", "2": "GND"}, "Relevador apagado al arrancar"),
    ("J5", "FOCOS", "Connector:Screw_Terminal_01x02",
     "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
     {"1": "COM", "2": "NO"}, "Contacto seco del relevador (COM / NA), max 10 A 250 VCA"),
    # --- ESP32-C3 ---
    ("U5", "ESP32-C3-WROOM-02", "RF_Module:ESP32-C3-WROOM-02", "RF_Module:ESP32-C3-WROOM-02", ESP,
     "Wi-Fi + Bluetooth LE (modulo certificado)"),
    ("C13", "10uF", C, C08, {"1": "3V3", "2": "GND"}, "Desacoplo del modulo"),
    ("C14", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo del modulo"),
    ("R6", "10k", R, R06, {"1": "3V3", "2": "EN"}, "Pull-up EN"),
    ("C15", "1uF", C, C06, {"1": "EN", "2": "GND"}, "Retardo de arranque"),
    ("SW1", "MODO / BOOT", "Switch:SW_Push", "Button_Switch_SMD:SW_SPST_TL3342", {"1": "BOOT", "2": "GND"},
     "Boton MODO (mantener al conectar USB = modo programacion)"),
    ("SW2", "RESET", "Switch:SW_Push", "Button_Switch_SMD:SW_SPST_TL3342", {"1": "EN", "2": "GND"}, "Reinicio"),
    ("R7", "10k", R, R06, {"1": "3V3", "2": "BOOT"}, "Pull-up IO9"),
    ("R8", "4.7k", R, R06, {"1": "3V3", "2": "SDA"}, "Pull-up I2C (IO2 debe estar en alto al arrancar)"),
    ("R9", "4.7k", R, R06, {"1": "3V3", "2": "SCL"}, "Pull-up I2C (IO8 debe estar en alto al arrancar)"),
    ("R10", "10k", R, R06, {"1": "3V3", "2": "IR"}, "Pull-up del receptor IR"),
    ("R11", "10k", R, R06, {"1": "3V3", "2": "LDR"}, "LDR a GND con pull-up de 10 k"),
    ("C16", "100nF", C, C06, {"1": "LDR", "2": "GND"}, "Filtro del LDR"),
    ("R12", "1k", R, R06, {"1": "LED", "2": "LEDA"}, "LED de estado"),
    ("D5", "LED", "Device:LED", "LED_SMD:LED_0603_1608Metric", {"1": "GND", "2": "LEDA"}, "LED de estado"),
    # --- USB-C ---
    ("J2", "USB-C", "Connector:USB_C_Receptacle_USB2.0_16P", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
     {"A1": "GND", "A4": "VBUS", "A5": "CC1", "A6": "USB_DP", "A7": "USB_DN", "A8": None, "A9": "VBUS",
      "B1": "GND", "B4": "VBUS", "B5": "CC2", "B6": "USB_DP", "B7": "USB_DN", "B8": None, "B9": "VBUS",
      "S1": "GND", "A12": "GND", "B12": "GND"}, "USB-C: programar y probar (5 V)"),
    ("R13", "5.1k", R, R06, {"1": "CC1", "2": "GND"}, "CC1 (dispositivo USB-C)"),
    ("R14", "5.1k", R, R06, {"1": "CC2", "2": "GND"}, "CC2"),
    ("U6", "USBLC6-2SC6", "Power_Protection:USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "USB_DN", "2": "GND", "3": "USB_DP", "4": "USB_DP", "5": "VBUS", "6": "USB_DN"}, "Proteccion ESD USB"),
    # --- puntos de prueba (prueba de fabrica con agujas) ---
    ("TP1", "VIN", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "VIN"}, "Prueba: entrada"),
    ("TP2", "12V", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "V12G"}, "Prueba: 12 V"),
    ("TP3", "3V3", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "3V3"}, "Prueba: 3.3 V"),
    ("TP4", "GND", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "GND"}, "Prueba: tierra"),
    ("TP5", "TXD", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "TXD"}, "Prueba: registro serie IO21"),
    ("TP6", "EN", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "EN"}, "Prueba: reinicio"),
    # --- expansión ---
    ("J6", "EXPANSION", "Connector:Conn_01x07_Pin", "Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical",
     {"1": "3V3", "2": "GND", "3": "SDA", "4": "SCL", "5": "IR", "6": "LDR", "7": "BOOT"},
     "3V3 GND SDA SCL IR LDR MODO: reloj/sensores I2C, receptor IR, LDR, boton externo"),
]

W, H = 90.0, 70.0
HOLES = [(3.5, 3.5), (86.5, 3.5), (62.5, 66.0)]
YT = 63.5
QX = (33.5, 40.5, 47.5, 54.5)             # MOSFET de canal (rot 270: drenaje hacia J4)
POS = {
    "J3": (5.0, YT, 0), "J1": (17.5, YT, 0), "J4": (36.0, YT, 0), "J5": (77.0, YT, 0),
    "F1": (17.5, 50.0, 90), "RS1": (10.9, 40.8, 0), "U7": (6.0, 36.3, 180), "C17": (4.0, 33.5, 0),
    "U8": (44.0, 37.0, 90), "C18": (44.0, 32.0, 0), "R15": (44.0, 30.3, 0),
    "TP1": (5.5, 47.5, 0), "TP2": (38.5, 26.0, 0), "TP3": (54.0, 23.5, 0), "TP4": (54.0, 26.3, 0),
    "TP5": (56.6, 23.5, 0), "TP6": (56.6, 26.3, 0),
    "QR1": (26.0, 53.0, 0), "QR2": (26.0, 46.0, 0), "RG0": (23.6, 41.6, 0), "DZ1": (28.0, 40.4, 0),
    "U3": (37.0, 37.0, 0), "U4": (51.0, 37.0, 0), "C11": (37.0, 32.5, 0), "C12": (51.0, 32.5, 0),
    "C1": (10.0, 27.0, 180), "C2": (10.0, 12.8, 180), "D1": (20.5, 32.6, 0), "C3": (6.5, 51.0, 0),
    "U2": (24.0, 22.0, 0), "L2": (30.0, 22.0, 0), "C8": (24.0, 25.5, 0), "C9": (19.5, 22.0, 90),
    "C10": (34.5, 22.0, 90), "RF1": (24.0, 18.5, 0), "RF2": (28.5, 18.5, 0),
    "U1": (24.0, 10.0, 0), "L1": (30.0, 10.0, 0), "C4": (24.0, 13.5, 0), "C5": (19.5, 10.0, 90),
    "C6": (34.5, 10.0, 90), "C7": (37.5, 10.0, 90), "D2": (44.0, 18.0, 90), "D3": (48.0, 18.0, 90),
    "U5": (68.0, 19.5, 0),
    "C13": (51.5, 8.0, 0), "C14": (51.5, 10.5, 0), "R6": (51.5, 13.0, 0), "C15": (51.5, 15.5, 0),
    "R7": (51.5, 18.0, 0), "R9": (51.5, 20.5, 0),
    "R8": (83.5, 14.0, 90), "R10": (83.5, 17.0, 90), "R11": (83.5, 20.0, 90), "C16": (83.5, 23.0, 90),
    "SW1": (59.0, 31.0, 0), "SW2": (68.0, 31.0, 0), "R12": (57.0, 36.5, 0), "D5": (61.0, 36.5, 0),
    "J2": (85.0, 32.5, 90), "R13": (78.0, 37.5, 0), "R14": (74.5, 37.5, 0), "U6": (76.0, 32.5, 90),
    "J6": (87.0, 9.2, 0),
    "K1": (68.0, 47.0, 0), "Q5": (59.5, 47.0, 0), "D4": (59.5, 52.0, 90), "R5": (59.5, 43.5, 0),
}
for n, x in enumerate(QX, start=1):
    POS["Q%d" % n] = (x, 50.0, 270)
    POS["RG%d" % n] = (x - 1.6, 42.9, 0)
    POS["RP%d" % n] = (x + 1.6, 42.9, 0)

NETCLASS = {  # nombre: (ancho de pista, separacion, redes)
    "Potencia": (2.0, 0.3, ["VIN", "VIN_RAW", "GNDIN", "CH1", "CH2", "CH3", "CH4"]),
    "Media": (0.6, 0.2, ["VFUS", "V12G", "VLOG", "3V3", "VBUS", "RLYD", "SW1", "SW2", "GND"]),
    "Red127V": (2.5, 2.0, ["COM", "NO"]),
    "RelNC": (0.5, 2.0, ["NC_K1"]),
}


def fp_id(f):
    lib, name = f.split(":")
    return lib, name


def build_board():
    b = pcbnew.BOARD()
    b.GetDesignSettings().SetCopperLayerCount(2)
    nets = {}
    for c in C_:
        for n in c[4].values():
            if n and n not in nets:
                nets[n] = pcbnew.NETINFO_ITEM(b, "/" + n)
                b.Add(nets[n])
    mm = pcbnew.FromMM
    P = lambda x, y: pcbnew.VECTOR2I(mm(100 + x), mm(100 + y))
    pts = [(0, 0), (W, 0), (W, H), (0, H)]
    for a, c in zip(pts, pts[1:] + pts[:1]):
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(P(*a)); s.SetEnd(P(*c)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
        b.Add(s)
    fps = {}
    for ref, val, sym, f, pins, func in C_:
        lib, name = fp_id(f)
        fp = pcbnew.FootprintLoad(os.path.join(FPL, lib + ".pretty"), name)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref); fp.SetValue(val)
        x, y, r = POS[ref]
        fp.SetPosition(P(x, y)); fp.SetOrientationDegrees(r)
        fp.SetPath(pcbnew.KIID_PATH("/" + str(uuid.uuid5(NS, ref))))
        fp.Value().SetVisible(False)
        b.Add(fp)
        for pad in fp.Pads():
            num = pad.GetNumber()
            if not num:
                continue
            n = pins.get(num)
            if n:
                pad.SetNet(nets[n])
            else:
                nm = comun.pin_names(sym).get(num, "")
                nm = "" if nm in ("", "~") else nm.replace("/", "{slash}") + "-"
                ni = pcbnew.NETINFO_ITEM(b, "unconnected-(%s-%sPad%s)" % (ref, nm, num))
                b.Add(ni); pad.SetNet(ni)
        if ref.startswith("TP"):
            fp.SetExcludedFromBOM(False)    # igual que el simbolo (el filtro de JLCPCB los quita)
            fp.Reference().SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.7), pcbnew.FromMM(0.7)))
            fp.Reference().SetTextThickness(pcbnew.FromMM(0.12))
        fps[ref] = fp
    for i, (x, y) in enumerate(HOLES):
        fp = pcbnew.FootprintLoad(os.path.join(FPL, "MountingHole.pretty"), "MountingHole_3.2mm_M3")
        fp.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_3.2mm_M3"))
        fp.SetReference("H%d" % (i + 1)); fp.SetPosition(P(x, y)); fp.SetBoardOnly(True)
        fp.SetExcludedFromBOM(True); fp.SetExcludedFromPosFiles(True); fp.Reference().SetVisible(False)
        b.Add(fp)
    # clases de red
    ds = b.GetDesignSettings()
    ns = ds.m_NetSettings
    for cname, (w, clr, members) in NETCLASS.items():
        nc = pcbnew.NETCLASS(cname)
        nc.SetTrackWidth(mm(w)); nc.SetClearance(mm(clr)); nc.SetViaDiameter(mm(0.8 if w >= 1 else 0.6))
        nc.SetViaDrill(mm(0.4 if w >= 1 else 0.3))
        ns.SetNetclass(cname, nc)
        for m in members:
            ns.SetNetclassPatternAssignment("/" + m, cname)
    dflt = ns.GetDefaultNetclass()
    dflt.SetTrackWidth(mm(0.25)); dflt.SetClearance(mm(0.2)); dflt.SetViaDiameter(mm(0.6)); dflt.SetViaDrill(mm(0.3))
    ds.m_MinThroughDrill = mm(0.2)
    return b, fps, nets


def add_zone(b, net, layer, pts, prio=0, clearance=0.3, solid=True):
    mm = pcbnew.FromMM
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(b.FindNet("/" + net))
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(mm(100 + x), mm(100 + y))
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(mm(clearance))
    z.SetMinThickness(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if solid else pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIsFilled(False)
    b.Add(z)
    return z


QX_ = (33.5, 40.5, 47.5, 54.5)
POWER_ZONES = [  # (red, capa, poligono) en F.Cu; prioridad alta
    ("VIN_RAW", [(12.6, 48.0), (19.9, 48.0), (19.9, 56.5), (20.1, 56.5), (20.1, 66.0), (12.6, 66.0)]),   # 7.3 mm
    ("VFUS", [(12.2, 6.0), (15.35, 6.0), (15.35, 30.8), (19.8, 30.8), (19.8, 35.2), (20.6, 35.2), (20.6, 43.2),
              (12.2, 43.2)]),                       # fusible -> shunt, y columna de los capacitores de entrada
    ("VIN", [(1.0, 38.6), (9.6, 38.6), (9.6, 43.2), (12.0, 43.2), (12.0, 66.0), (1.0, 66.0)]),   # shunt -> J3, 11 mm
    ("GNDIN", [(24.9, 43.5), (30.2, 43.5), (30.2, 66.0), (20.6, 66.0), (20.6, 57.3), (24.9, 57.3)]),
    ("CH1", [(31.3, 48.8), (35.8, 48.8), (35.8, 55.0), (37.5, 57.0), (37.5, 66.0), (34.5, 66.0), (34.5, 57.0), (31.3, 54.0)]),
    ("CH2", [(38.3, 48.8), (42.7, 48.8), (42.7, 66.0), (39.5, 66.0), (39.5, 57.0), (38.3, 55.5)]),
    ("CH3", [(45.3, 48.8), (49.7, 48.8), (49.7, 55.0), (47.8, 57.0), (47.8, 66.0), (44.6, 66.0), (44.6, 57.0), (45.3, 55.5)]),
    ("CH4", [(52.3, 48.8), (56.7, 48.8), (56.7, 55.0), (52.9, 59.0), (52.9, 66.0), (49.6, 66.0), (49.6, 59.0), (52.3, 55.5)]),
    ("GND", [(20.4, 43.6), (23.5, 43.6), (23.5, 47.3), (20.4, 47.3)]),          # fuentes de QR2
    ("GND", [(20.4, 50.6), (23.5, 50.6), (23.5, 54.3), (20.4, 54.3)]),          # fuentes de QR1
] + [("GND", [(x - 1.1, 44.4), (x + 2.6, 44.4), (x + 2.6, 47.5), (x - 1.1, 47.5)]) for x in QX_]
VIAS = ([(2.3, 35.8), (5.7, 33.5), (9.5, 37.2), (7.975, 52.6)] + [(20.9, y) for y in (44.2, 45.4, 46.6, 51.2, 52.4, 53.6)] + [(21.95, y) for y in (44.2, 45.4, 46.6, 51.2, 52.4, 53.6)]
        + [(x + dx, y) for x in QX_ for dx in (-0.5, 0.7, 1.9) for y in (45.1, 46.2)])


PRE = [  # pistas fijas: contactos del relevador (127 V) y bobina (que se aleje del COM)
    ("COM", 2.5, [(68.0, 47.0), (76.9, 47.0), (76.9, 61.0), (77.0, 63.5)]),
    ("NO", 2.5, [(82.15, 53.05), (82.08, 63.5)]),
    ("3V3", 0.6, [(59.25, 13.5), (53.3, 13.5), (53.3, 9.3), (50.72, 9.3), (50.72, 10.5)]),
    ("V12G", 0.8, [(69.95, 41.05), (69.95, 38.3), (63.5, 38.3)]),   # bobina: su pata esta a < 5 mm del COM
    ("RLYD", 0.8, [(69.95, 53.05), (69.95, 56.0), (60.9, 56.0), (60.9, 47.6), (60.44, 47.0)]),
    ("RLYD", 0.8, [(60.9, 50.35), (59.5, 50.35)]),
    # INA238 (patas de 0.3 mm a 0.5 mm de paso) y sensado Kelvin del shunt (fuera de los planos de entrada)
    ("3V3", 0.3, [(3.8, 35.3), (3.225, 34.7), (3.225, 33.5)]),
    ("GND", 0.3, [(3.8, 35.8), (2.3, 35.8)]), ("GND", 0.4, [(4.775, 33.5), (5.7, 33.5)]),
    ("GND", 0.3, [(8.2, 37.3), (8.2, 36.8)]), ("GND", 0.3, [(8.2, 37.05), (9.5, 37.2)]),
    ("ISN", 0.3, [(3.8, 36.3), (3.8, 36.8)]), ("ISN", 0.3, [(3.8, 36.55), (2.6, 36.55), (1.5, 37.65)]),
    ("ISN", 0.3, [(1.5, 37.65), (1.5, 43.2), (7.47, 43.2)], "B"), ("ISN", 0.3, [(7.47, 43.2), (7.47, 42.07)]),
    ("ISP", 0.3, [(14.33, 39.53), (13.6, 38.3), (11.6, 38.3)]), ("ISP", 0.3, [(11.6, 38.3), (2.9, 38.3)], "B"),
    ("ISP", 0.3, [(2.9, 38.3), (3.8, 37.3)]),
    ("GND", 0.6, [(7.975, 51.0), (7.975, 52.6)]),           # tierra de C3 dentro del plano VIN
    ("VFUS", 0.6, [(20.0, 41.6), (22.775, 41.6)]),                                     # compuerta proteccion
    ("VFUS", 0.4, [(19.5, 23.47), (21.5, 24.4), (26.4, 24.4), (26.4, 22.0), (25.14, 22.0)]),  # pata VIN del buck
    ("VFUS", 0.8, [(14.0, 23.6), (19.5, 23.6), (19.5, 23.47)]), ("VFUS", 0.4, [(25.14, 22.0), (25.14, 22.95)]),   # buck 12 V
]
PREVIAS = [("V12G", 63.5, 38.3), ("ISN", 1.5, 37.65), ("ISN", 7.47, 43.2), ("ISP", 11.6, 38.3), ("ISP", 2.9, 38.3)]
KEEPOUT_NETS = ("VIN", "VIN_RAW", "VFUS")        # el ruteador no pasa pistas sobre estos planos


def add_power(b):
    mm = pcbnew.FromMM
    for item in PRE:
        net, w, pts = item[:3]
        lay = pcbnew.B_Cu if len(item) > 3 and item[3] == "B" else pcbnew.F_Cu
        for a, c in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(mm(100 + a[0]), mm(100 + a[1])))
            t.SetEnd(pcbnew.VECTOR2I(mm(100 + c[0]), mm(100 + c[1])))
            t.SetWidth(mm(w)); t.SetLayer(lay); t.SetNet(b.FindNet("/" + net)); t.SetLocked(True)
            b.Add(t)
    for net, pts in POWER_ZONES:
        add_zone(b, net, pcbnew.F_Cu, pts, prio=10, clearance=0.3, solid=True)
    mm = pcbnew.FromMM
    for x, y in VIAS:
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(mm(100 + x), mm(100 + y)))
        v.SetWidth(mm(0.8)); v.SetDrill(mm(0.4)); v.SetNet(b.FindNet("/GND"))
        v.SetIsFree(True)
        b.Add(v)
    for net, x, y in PREVIAS:
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(mm(100 + x), mm(100 + y)))
        v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(b.FindNet("/" + net)); v.SetLocked(True)
        b.Add(v)
    for net, pts in POWER_ZONES:                 # solo para rutear: se quitan antes del relleno final
        if net not in KEEPOUT_NETS:
            continue
        ps = pcbnew.SHAPE_POLY_SET(); ps.NewOutline()
        for x, y in pts:
            ps.Append(mm(100 + x), mm(100 + y))
        ps.Deflate(mm(0.8), pcbnew.CORNER_STRATEGY_CHAMFER_ALL_CORNERS, mm(0.01))
        k = pcbnew.ZONE(b)
        k.SetIsRuleArea(True); k.SetLayer(pcbnew.F_Cu)
        o, ol = ps.Outline(0), k.Outline()            # se copian los puntos (SetOutline libera el poligono dos veces)
        ol.NewOutline()
        for i in range(o.PointCount()):
            ol.Append(o.CPoint(i).x, o.CPoint(i).y)
        k.SetDoNotAllowTracks(True); k.SetDoNotAllowVias(True); k.SetDoNotAllowCopperPour(False)
        k.SetDoNotAllowPads(False); k.SetDoNotAllowFootprints(False); k.SetZoneName("ruteo_" + net)
        b.Add(k)


def write_project():
    mm_rules = {"min_clearance": 0.2, "min_track_width": 0.15, "min_copper_edge_clearance": 0.3,
                "min_through_hole_diameter": 0.2, "min_hole_to_hole": 0.25, "min_hole_clearance": 0.2,
                "min_via_diameter": 0.45, "min_via_annular_width": 0.1, "min_connection": 0.0,
                "min_silk_clearance": 0.0, "min_text_height": 0.6, "min_text_thickness": 0.1,
                "allow_blind_buried_vias": False, "allow_microvias": False}
    pro = json.load(open("/usr/share/kicad/template/kicad.kicad_pro"))
    ds = pro.setdefault("board", {}).setdefault("design_settings", {})
    ds.setdefault("rules", {}).update(mm_rules)
    ds.setdefault("rule_severities", {}).update({
        "silk_over_copper": "ignore", "silk_overlap": "ignore", "silk_edge_clearance": "ignore",
        "lib_footprint_mismatch": "ignore", "lib_footprint_issues": "ignore", "text_height": "ignore",
        "text_thickness": "ignore", "footprint_type_mismatch": "ignore", "isolated_copper": "ignore",
        "starved_thermal": "ignore"})
    ds["track_widths"] = [0.0, 0.25, 0.6, 1.0, 2.0]
    ds["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3},
                            {"diameter": 0.8, "drill": 0.4}]
    base = {"bus_width": 12, "clearance": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
            "diff_pair_width": 0.2, "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
            "name": "Default", "pcb_color": "rgba(0, 0, 0, 0.000)", "priority": 2147483647,
            "schematic_color": "rgba(0, 0, 0, 0.000)", "track_width": 0.25, "via_diameter": 0.6,
            "via_drill": 0.3, "wire_width": 6}
    classes, pats = [base], []
    for i, (cname, (w, clr, members)) in enumerate(NETCLASS.items()):
        c = dict(base)
        c.update({"name": cname, "clearance": clr, "track_width": w, "priority": i,
                  "via_diameter": 0.8 if w >= 1 else 0.6, "via_drill": 0.4 if w >= 1 else 0.3})
        classes.append(c)
        pats += [{"netclass": cname, "pattern": "/" + m} for m in members]
    pro["net_settings"] = {"classes": classes, "meta": {"version": 4}, "netclass_patterns": pats}
    pro.setdefault("meta", {})["filename"] = PROJECT + ".kicad_pro"
    json.dump(pro, open(os.path.join(KI, PROJECT + ".kicad_pro"), "w"), indent=2)
    open(os.path.join(KI, PROJECT + ".kicad_dru"), "w").write(
        '(version 1)\n'
        '(rule "127 V contra bajo voltaje (reforzado)"\n'
        "  (condition \"A.NetClass == 'Red127V' && B.NetClass != 'Red127V'\")\n"
        '  (constraint clearance (min 5.0mm)))\n'
        '(rule "Dentro del relevador (aislamiento del fabricante)"\n'
        "  (condition \"A.intersectsCourtyard('K1') && B.intersectsCourtyard('K1') && "
        "(A.NetClass == 'Red127V' || B.NetClass == 'Red127V')\")\n"
        '  (constraint clearance (min 1.5mm)))\n'
        '(rule "Contacto NC sin usar"\n'
        "  (condition \"(A.Parent == 'K1' && A.Pad_Number == '4') || (B.Parent == 'K1' && B.Pad_Number == '4')\")\n"
        '  (constraint clearance (min 2.0mm)))\n')


def schematic():
    comps = []
    for i, (ref, val, sym, f, pins, func) in enumerate(C_):
        pins = {k: (None if v == "NC_K1" else v) for k, v in pins.items()}
        x, y = 30.48 + (i % 9) * 43.18, 40.64 + (i // 9) * 38.1
        comps.append((ref, val, sym, f, pins, (round(x / 2.54) * 2.54, round(y / 2.54) * 2.54, 0), func))
    flags = [("VIN_RAW", 20.32, 20.32), ("GND", 35.56, 20.32), ("VBUS", 50.8, 20.32), ("VLOG", 66.04, 20.32),
             ("V12G", 81.28, 20.32), ("3V3", 96.52, 20.32), ("VIN", 111.76, 20.32), ("GNDIN", 127.0, 20.32),
             ("VFUS", 142.24, 20.32)]
    notes = [(150.0, 15.0, "LetreroLab AP-0.2: entrada 12-24 V / 20 A, 4 canales de 8 A, ESP32-C3 Wi-Fi, relevador 10 A.\n"
                           "PWM1-4 = IO4-IO7, relevador = IO1, LED = IO10, IR = IO3, LDR = IO0, SDA/SCL = IO2/IO8, MODO = IO9,\n"
                           "ALERTA (INA238 0x40 + TMP1075 0x48) = IO20, TXD de prueba = IO21. Shunt 1 mOhm Kelvin.")]
    comun.make_schematic(KI, PROJECT, PROJECT, ROOT_UUID, NS, comps, notes, [],
                         "LetreroLab AP-0.2 - controlador Wi-Fi de potencia",
                         ["Placa de 2 capas para ensamble en fabrica (JLCPCB)", "12-24 V DC, 4 x 8 A, ESP32-C3"],
                         paper="A2", flags=flags, company="PCB 90 x 70 mm, 2 capas, cobre 2 oz recomendado")


SILK = [  # (texto, x, y, alto mm, capa)
    ("LetreroLab AP-0.2 rev B", 38.5, 3.2, 1.5, "F"),
    ("12-24V 20A, mide y protege", 38.0, 5.6, 1.0, "F"),
    ("+V", 5.0, 60.6, 1.0, "F"), ("+V", 10.08, 60.6, 1.0, "F"),
    ("+", 17.5, 60.6, 1.2, "F"), ("-", 22.58, 60.6, 1.2, "F"),
    ("CH1", 36.0, 60.6, 1.0, "F"), ("CH2", 41.08, 60.6, 1.0, "F"),
    ("CH3", 46.16, 60.6, 1.0, "F"), ("CH4", 51.24, 60.6, 1.0, "F"),
    ("COM", 77.0, 60.6, 1.0, "F"), ("NO", 82.08, 60.6, 1.0, "F"),
    ("127-240V~ 10A", 79.5, 58.0, 1.0, "B"),
    ("8 A max por canal - 20 A total", 45.0, 30.0, 1.0, "B"),
    ("LetreroLab AP-0.2  ESP32-C3  Wi-Fi", 45.0, 66.5, 1.4, "B"),
    ("Cobre 2 oz  -  no conectar 127V a J1/J3/J4", 45.0, 4.0, 1.0, "B"),
]


def finish(b):
    """Modelos 3D locales (kicad/3d) y textos de serigrafia."""
    mm = pcbnew.FromMM
    d3 = os.path.join(KI, "3d")
    for fp in b.GetFootprints():
        ms = list(fp.Models())
        for m in ms:
            if "WSK2512" in m.m_Filename:                # la libreria no trae este modelo: se usa el cuerpo 2512
                m.m_Filename = "R_2512_6332Metric.step"
            f = os.path.basename(m.m_Filename)
            if os.path.exists(os.path.join(d3, f)):
                m.m_Filename = "${KIPRJMOD}/3d/" + f
        fp.Models().clear()
        for m in ms:
            fp.Add3DModel(m)
    for txt, x, y, h, side in SILK:
        t = pcbnew.PCB_TEXT(b)
        t.SetText(txt); t.SetPosition(pcbnew.VECTOR2I(mm(100 + x), mm(100 + y)))
        t.SetTextSize(pcbnew.VECTOR2I(mm(h), mm(h))); t.SetTextThickness(mm(h * 0.15))
        t.SetLayer(pcbnew.F_SilkS if side == "F" else pcbnew.B_SilkS)
        if side == "B":
            t.SetMirrored(True)
        b.Add(t)


def main():
    os.makedirs(KI, exist_ok=True)
    write_project()
    schematic()
    b, fps, nets = build_board()
    path = os.path.join(KI, PROJECT + ".kicad_pcb")
    dsn, ses = os.path.join(KI, PROJECT + ".dsn"), os.path.join(KI, PROJECT + ".ses")
    sufijo = lambda k: "" if k == 1 else "_%d" % k          # pasada 1: AP02.ses, pasada k: AP02_k.ses
    if "--import" in sys.argv:
        # pasada k importada; se exporta otra vez para que el ruteador termine lo pendiente
        k = int(sys.argv[sys.argv.index("--import") + 1]) if len(sys.argv) > sys.argv.index("--import") + 1 else 1
        b = pcbnew.LoadBoard(path)
        pcbnew.ImportSpecctraSES(b, ses.replace(".ses", sufijo(k) + ".ses"))
        b.Save(path)
        b = pcbnew.LoadBoard(path)
        nc = b.GetDesignSettings().m_NetSettings.GetNetClassByName("Red127V")
        nc.SetClearance(pcbnew.FromMM(5.0))
        pcbnew.ExportSpecctraDSN(b, dsn.replace(".dsn", sufijo(k + 1) + ".dsn"))
        print("pasada %d importada; dsn %d" % (k, k + 1), path)
        return
    if "--final" in sys.argv:
        k = int(sys.argv[sys.argv.index("--final") + 1])
        b = pcbnew.LoadBoard(path)
        pcbnew.ImportSpecctraSES(b, ses.replace(".ses", sufijo(k) + ".ses"))
        # el contacto NC del relevador solo tenia red para el ruteador (separacion); en el esquema va sin conectar
        for pad in b.FindFootprintByReference("K1").Pads():
            if pad.GetNumber() == "4":
                ni = pcbnew.NETINFO_ITEM(b, "unconnected-(K1-Pad4)")
                b.Add(ni)
                pad.SetNet(ni)
        for z in list(b.Zones()):                # las areas prohibidas eran solo para el ruteador
            if z.GetIsRuleArea() and z.GetZoneName().startswith("ruteo_"):
                b.Remove(z)
        # planos de GND en ambas capas (prioridad baja) y relleno
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            add_zone(b, "GND", layer, [(0.3, 0.3), (W - 0.3, 0.3), (W - 0.3, H - 0.3), (0.3, H - 0.3)], prio=0,
                     clearance=0.3, solid=False)
        finish(b)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        b.Save(path)
        print("importado y rellenado", path)
        return
    b.Save(path)
    b = pcbnew.LoadBoard(path)
    add_power(b)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(path)
    # para el ruteador: la red de 127 V se aleja 5 mm de todo
    nc = b.GetDesignSettings().m_NetSettings.GetNetClassByName("Red127V")
    nc.SetClearance(pcbnew.FromMM(5.0))
    pcbnew.ExportSpecctraDSN(b, dsn)
    print("placa", path, "dsn", dsn)





if __name__ == "__main__":
    main()
