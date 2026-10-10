"""AP ELECTRIC · AP GATE: pasarela de campo con Wi-Fi, AP BUS (24 V + CAN) y RS-485 / Modbus RTU, con ESP32-C3.

Para qué: hablar con los equipos industriales que ya hay en la obra, por el bus RS-485 con Modbus RTU:
- medidores de energía (kWh, V, A, factor de potencia) de riel DIN;
- variadores de frecuencia de bombas y ventiladores (marcha, paro, frecuencia);
- PLC, controladores de temperatura y sensores con salida Modbus.
Sus lecturas salen en la app y en Home Assistant y pueden disparar acciones; también es un AP NODE completo (maestro o
nodo remoto del AP BUS) con sus módulos locales por Qwiic.

Circuito (igual que el AP NODE, más el puerto RS-485):
- J1 / J2: AP BUS (JST XH 4: +24 V, CAN_H, CAN_L, 0 V), unidos en la placa.
- Entrada: fusible rápido de 3 A, SS34 en serie, SMBJ26A. LMR16006 -> 5 V; AP63203 -> 3.3 V; USB-C para el taller.
- U4 TJA1051T/3: CAN (IO4 TX, IO5 RX). Terminación 120 Ohm con JP3.
- U6 SP3485 (3.3 V): RS-485 semidúplex. DI = IO6 (TX de UART1), RO = IO7 (RX), DE y /RE juntos en IO1 (el receptor se
  apaga mientras transmite). D7 SM712: descargas y picos en A/B (-7 V / +12 V, el rango de RS-485).
- Terminación 120 Ohm con JP4 (solo en los extremos del cable RS-485).
- Polarización: 560 Ohm de A a 3.3 V y de B a 0 V, con JP5/JP6 cerrados de fábrica (la pasarela es el maestro y
  polariza la línea en reposo). Si otro equipo ya polariza, se cortan.
- J4: JST XH 3: 1 = A (+), 2 = B (-), 3 = 0 V (común). Nota: en la norma Modbus, A/B se llaman D0/D1 al revés en
  algunos equipos; si no responde, se invierten A y B (no daña nada).
- No aislado: el 0 V de RS-485 es el 0 V del bus. Para líneas largas entre edificios, un repetidor RS-485 aislado.
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import placa  # noqa: E402
import conectores  # noqa: E402

PROJECT = "AP_Gate"
NS = uuid.UUID("ba6e7f3d-8244-49b2-8a49-8f870cff80ae")
ROOT_UUID = "661b0b49-119f-4e4a-9780-84d8303d147d"
R06, C06, C08, C12 = ("Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric",
                      "Capacitor_SMD:C_0805_2012Metric", "Capacitor_SMD:C_1206_3216Metric")
SMA = "Diode_SMD:D_SMA"
R, C = "Device:R", "Device:C"
BUS = {"1": "BUS24", "2": "CANH", "3": "CANL", "4": "GND"}
ESP = {"1": "3V3", "2": "EN", "3": "CAN_TX", "4": "CAN_RX", "5": "RS_TX", "6": "RS_RX", "7": "SCL", "8": "BOOT",
       "9": "GND", "10": "LEDB", "11": None, "12": "LEDV", "13": "USB_DN", "14": "USB_DP", "15": None, "16": "SDA",
       "17": "RS_DE", "18": None, "19": "GND"}

C_ = [
    # --- AP BUS ---
    ("J1", "AP BUS ENTRA", conectores.SYM[4], conectores.XH4, dict(BUS), "AP BUS desde el CORE o el nodo anterior"),
    ("J2", "AP BUS SIGUE", conectores.SYM[4], conectores.XH4, dict(BUS), "AP BUS al siguiente nodo (pasa de largo)"),
    ("F1", "3A", "Device:Fuse", "Fuse:Fuse_1206_3216Metric", {"1": "BUS24", "2": "VF"}, "Fusible rápido del nodo"),
    ("D1", "SS34", "Device:D_Schottky", SMA, {"1": "V24", "2": "VF"}, "Polaridad invertida (en serie)"),
    ("D2", "SMBJ26A", "Device:D_TVS", "Diode_SMD:D_SMB", {"1": "V24", "2": "GND"}, "Supresor de picos"),
    ("C2", "10uF 50V", C, C12, {"1": "V24", "2": "GND"}, "Entrada"),
    # --- 5 V ---
    ("U2", "LMR16006XDDC", "Regulator_Switching:LMR16006YQ", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "BST", "2": "GND", "3": "FB", "4": "V24", "5": "V24", "6": "SW"}, "Buck 60 V a 5 V"),
    ("L1", "47uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR4030S", {"1": "V5", "2": "SW"}, "Bobina del buck"),
    ("D4", "SS210", "Device:D_Schottky", SMA, {"1": "SW", "2": "GND"}, "Rueda libre del buck"),
    ("C5", "100nF", C, C06, {"1": "BST", "2": "SW"}, "Bootstrap"),
    ("C6", "10uF 50V", C, C12, {"1": "V24", "2": "GND"}, "Entrada del buck"),
    ("C7", "22uF 25V", C, C12, {"1": "V5", "2": "GND"}, "Salida 5 V"),
    ("RB1", "56k", R, R06, {"1": "V5", "2": "FB"}, "Divisor: 0.765 V x 6.6 = 5.05 V"),
    ("RB2", "10k", R, R06, {"1": "FB", "2": "GND"}, "Divisor"),
    ("D3", "B5819W", "Device:D_Schottky", "Diode_SMD:D_SOD-123", {"1": "V5", "2": "VBUS"}, "5 V del USB (taller)"),
    # --- 3.3 V ---
    ("U5", "AP63203WU", "Regulator_Switching:AP63203WU", "Package_TO_SOT_SMD:TSOT-23-6",
     {"1": "3V3", "2": "V5", "3": "V5", "4": "GND", "5": "SWP", "6": "BSTP"}, "Buck 3.3 V 2 A (síncrono)"),
    ("L2", "4.7uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR4030S", {"1": "SWP", "2": "3V3"}, "Bobina 3.3 V"),
    ("C8", "100nF", C, C06, {"1": "BSTP", "2": "SWP"}, "Bootstrap"),
    ("C9", "10uF 25V", C, C12, {"1": "V5", "2": "GND"}, "Entrada del buck de 3.3 V"),
    ("C10", "22uF", C, C08, {"1": "3V3", "2": "GND"}, "Salida 3.3 V"),
    ("C11", "22uF", C, C08, {"1": "3V3", "2": "GND"}, "Salida 3.3 V"),
    # --- CAN ---
    ("U4", "TJA1051T/3", "Interface_CAN_LIN:TJA1051T-3", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "CAN_TX", "2": "GND", "3": "V5", "4": "CAN_RX", "5": "3V3", "6": "CANL", "7": "CANH", "8": "GND"},
     "Transceptor CAN (VIO 3.3 V); S a 0 V = modo normal"),
    ("C12", "100nF", C, C06, {"1": "V5", "2": "GND"}, "Desacoplo VCC del transceptor"),
    ("C13", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo VIO del transceptor"),
    ("RT", "120", R, "Resistor_SMD:R_1206_3216Metric", {"1": "CANH", "2": "TERM"}, "Terminación del bus"),
    ("JP3", "120R", "Jumper:SolderJumper_2_Open", "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
     {"1": "TERM", "2": "CANL"}, "Cerrar solo en los dos extremos del cable"),
    # --- ESP32-C3 ---
    ("U1", "ESP32-C3-WROOM-02", "RF_Module:ESP32-C3-WROOM-02", "LetreroLab:ESP32-C3-WROOM-02_JLC", ESP,
     "Wi-Fi + BLE + CAN (TWAI). IO4 = CAN TX, IO5 = CAN RX"),
    ("C1", "10uF", C, C08, {"1": "3V3", "2": "GND"}, "Desacoplo del módulo"),
    ("C3", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo del módulo"),
    ("R1", "10k", R, R06, {"1": "3V3", "2": "EN"}, "Pull-up EN"),
    ("C4", "1uF", C, C06, {"1": "EN", "2": "GND"}, "Arranque retardado"),
    ("R2", "10k", R, R06, {"1": "3V3", "2": "BOOT"}, "Pull-up IO9 (arranque normal)"),
    ("SW1", "MODO / BOOT", "Switch:SW_Push", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", {"1": "BOOT", "2": "GND"},
     "MODO; mantenido al conectar el USB = modo programación"),
    ("SW2", "RESET", "Switch:SW_Push", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", {"1": "EN", "2": "GND"}, "Reinicio"),
    ("R5", "4.7k", R, R06, {"1": "3V3", "2": "SDA"}, "Pull-up I2C (IO2 en alto al arrancar)"),
    ("R6", "4.7k", R, R06, {"1": "3V3", "2": "SCL"}, "Pull-up I2C (IO8 en alto al arrancar)"),
    ("R9", "1k", R, R06, {"1": "LEDV", "2": "LEDVA"}, "LED de estado"),
    ("D5", "VERDE", "Device:LED", "LED_SMD:LED_0603_1608Metric", {"1": "GND", "2": "LEDVA"}, "Estado (IO21)"),
    ("R10", "1k", R, R06, {"1": "LEDB", "2": "LEDBA"}, "LED del bus"),
    ("D6", "VERDE", "Device:LED", "LED_SMD:LED_0603_1608Metric", {"1": "GND", "2": "LEDBA"}, "Bus CAN (IO10)"),
    # --- USB-C ---
    ("J5", "USB-C", "Connector:USB_C_Receptacle_USB2.0_16P", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
     {"A1": "GND", "A4": "VBUS", "A5": "CC1U", "A6": "USB_DP", "A7": "USB_DN", "A8": None, "A9": "VBUS",
      "B1": "GND", "B4": "VBUS", "B5": "CC2U", "B6": "USB_DP", "B7": "USB_DN", "B8": None, "B9": "VBUS",
      "S1": "GND", "A12": "GND", "B12": "GND"}, "USB-C: programar y probar"),
    ("R3", "5.1k", R, R06, {"1": "CC1U", "2": "GND"}, "CC1 (dispositivo)"),
    ("R4", "5.1k", R, R06, {"1": "CC2U", "2": "GND"}, "CC2"),
    ("U3", "USBLC6-2SC6", "Power_Protection:USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "USB_DN", "2": "GND", "3": "USB_DP", "4": "USB_DP", "5": "VBUS", "6": "USB_DN"}, "ESD del USB"),
    # --- módulos locales ---
    ("J3", "QWIIC", "Connector_Generic_MountingPin:Conn_01x04_MountingPin",
     "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
     {"1": "GND", "2": "3V3", "3": "SDA", "4": "SCL", "MP": "GND"}, "Módulos locales: DO8, AP INPUT, AI4, DIST 4"),
    # --- RS-485 / Modbus RTU ---
    ("U6", "SP3485EN", "Interface_UART:SP3485EN", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "RS_RX", "2": "RS_DE", "3": "RS_DE", "4": "RS_TX", "5": "GND", "6": "RSA", "7": "RSB", "8": "3V3"},
     "Transceptor RS-485 de 3.3 V, semidúplex (DE = /RE = IO1)"),
    ("C14", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo del transceptor RS-485"),
    ("RDE", "10k", R, R06, {"1": "RS_DE", "2": "GND"}, "DE en bajo al arrancar: la pasarela no ocupa la línea"),
    ("D7", "SM712", "Diode:SM712_SOT23", "Package_TO_SOT_SMD:SOT-23", {"1": "RSA", "2": "RSB", "3": "GND"},
     "Protección de la línea RS-485 (-7 V / +12 V)"),
    ("RT2", "120", R, "Resistor_SMD:R_1206_3216Metric", {"1": "RSA", "2": "TERM2"}, "Terminación RS-485"),
    ("JP4", "120R", "Jumper:SolderJumper_2_Open", "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
     {"1": "TERM2", "2": "RSB"}, "Cerrar solo en los extremos del cable RS-485"),
    ("RPA", "560", R, R06, {"1": "PA", "2": "RSA"}, "Polarización: A hacia 3.3 V"),
    ("RPB", "560", R, R06, {"1": "RSB", "2": "PB"}, "Polarización: B hacia 0 V"),
    ("JP5", "POL A", "Jumper:SolderJumper_2_Bridged", "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm",
     {"1": "3V3", "2": "PA"}, "Polarización activa de fábrica; cortar si otro equipo ya polariza"),
    ("JP6", "POL B", "Jumper:SolderJumper_2_Bridged", "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm",
     {"1": "PB", "2": "GND"}, "Polarización activa de fábrica; cortar si otro equipo ya polariza"),
    ("J4", "RS-485", conectores.SYM[3], conectores.XH3, {"1": "RSA", "2": "RSB", "3": "GND"},
     "RS-485 / Modbus RTU: 1 = A (+), 2 = B (-), 3 = 0 V (común)"),
    ("TP1", "24V", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "V24"}, "Prueba: 24 V del nodo"),
    ("TP2", "5V", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "V5"}, "Prueba: 5 V"),
    ("TP3", "3V3", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "3V3"}, "Prueba: 3.3 V"),
    ("TP4", "GND", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "GND"}, "Prueba: tierra"),
]

W, H = 88.0, 56.0
RADIO_ESQUINA = 2.0
HOLES = [(3.5, 3.5), (84.5, 39.5), (84.5, 52.5)]        # como la base: soporte DIN de 88 x 56
POS = {
    # bus y entrada (abajo a la izquierda)
    "J1": (4.0, 50.4, 0), "J2": (18.0, 50.4, 0),
    "F1": (5.0, 42.0, 0), "D1": (12.0, 42.0, 0), "D2": (21.0, 42.0, 0), "C2": (27.0, 42.0, 90),
    # 5 V
    "U2": (11.0, 31.0, 0), "L1": (11.0, 26.0, 0), "C5": (7.8, 29.8, 90), "D4": (15.6, 27.0, 90),
    "C6": (15.6, 33.6, 90), "C7": (4.6, 32.4, 180), "RB1": (5.0, 35.0, 0), "RB2": (9.6, 35.0, 0),
    # USB (arriba a la izquierda)
    "J5": (14.5, 4.2, 180), "U3": (14.5, 12.4, 0), "R3": (18.6, 11.6, 90), "R4": (10.4, 11.6, 90),
    "D3": (14.5, 17.0, 0),
    # 3.3 V
    "U5": (26.0, 25.0, 0), "L2": (31.0, 25.2, 0), "C8": (26.0, 22.3, 0), "C9": (22.0, 25.0, 90),
    "C10": (31.0, 29.6, 0), "C11": (31.0, 32.2, 0),
    # CAN
    "U4": (40.0, 42.0, 0), "C12": (35.0, 38.0, 0), "C13": (45.0, 38.0, 0),
    "RT": (35.0, 50.4, 0), "JP3": (40.5, 50.4, 0),
    # ESP32 (antena arriba a la derecha)
    "U1": (68.0, 19.2, 0), "C1": (50.0, 13.0, 0), "C3": (50.0, 15.0, 0), "R1": (50.0, 18.0, 0),
    "C4": (50.0, 20.0, 0), "R2": (50.0, 23.0, 0),
    "SW1": (60.0, 33.5, 0), "SW2": (70.0, 33.5, 0),
    "R5": (40.0, 9.5, 0), "R6": (40.0, 11.3, 0),
    "R9": (78.0, 30.5, 0), "D5": (78.0, 32.3, 0), "R10": (78.0, 34.6, 0), "D6": (78.0, 36.4, 0),
    # módulos locales
    "J3": (30.0, 3.6, 180),
    "TP1": (40.0, 20.0, 0), "TP2": (44.0, 20.0, 0), "TP3": (40.0, 24.0, 0), "TP4": (44.0, 24.0, 0),
    # RS-485 (abajo a la derecha)
    "J4": (57.0, 50.4, 0), "U6": (60.0, 42.0, 0), "C14": (54.0, 42.0, 90), "RDE": (54.0, 46.2, 0),
    "D7": (68.0, 44.0, 0), "RT2": (71.0, 48.4, 0), "JP4": (71.0, 51.6, 0),
    "RPA": (66.0, 39.6, 0), "RPB": (70.0, 39.6, 0), "JP5": (77.0, 43.0, 0), "JP6": (77.0, 46.5, 0),
}

NETCLASS = {"Potencia": (2.0, 0.3, ["BUS24"]),
            "Media": (0.6, 0.2, ["VF", "V24", "V5", "SW", "VBUS", "3V3", "SWP"]),
            "CAN": (0.4, 0.2, ["CANH", "CANL", "RSA", "RSB"])}
SIN_COBRE = [[(53.5, 0.3), (82.5, 0.3), (82.5, 12.3), (53.5, 12.3)]]    # bajo la antena del ESP32
SILK = [
    ("+24 H L 0V", 7.8, 46.2, 0.8, "F"), ("+24 H L 0V", 21.8, 46.2, 0.8, "F"),
    ("ENTRA", 7.8, 55.0, 0.8, "F"), ("SIGUE", 21.8, 55.0, 0.8, "F"),
    ("120R: solo extremos", 38.0, 53.6, 0.8, "F"),
    ("MODO", 60.0, 37.6, 0.8, "F"), ("RESET", 70.0, 37.6, 0.8, "F"),
    ("OK", 81.0, 32.3, 0.8, "F"), ("BUS", 81.4, 36.4, 0.8, "F"),
    ("AP GATE", 47.5, 52.6, 1.4, "F"),
    ("A+ B- 0V", 59.5, 46.6, 0.8, "F"), ("RS-485", 59.5, 55.0, 0.8, "F"),
    ("120R", 75.6, 51.6, 0.8, "F"), ("POL", 80.6, 44.7, 0.8, "F"),
    ("AP ELECTRIC  AP GATE  AP BUS + RS-485 Modbus", 44.0, 54.8, 1.0, "B"),
    ("Bus: 1 +24V  2 CAN_H  3 CAN_L  4 0V  (pasa de largo, max 3 A)", 44.0, 52.8, 0.8, "B"),
]
FLAGS = [("BUS24", 20.32, 20.32), ("GND", 35.56, 20.32), ("V24", 50.8, 20.32), ("V5", 66.04, 20.32),
         ("3V3", 81.28, 20.32), ("VBUS", 96.52, 20.32)]
NOTES = [(150.0, 15.0, "AP ELECTRIC · AP GATE: ESP32-C3 + TJA1051T/3 + SP3485. CAN TX = IO4, CAN RX = IO5, RS-485 TX = IO6,\n"
                       "RX = IO7, DE = IO1, SDA/SCL = IO2/IO8, MODO = IO9, LED = IO21, LED bus = IO10, USB = IO18/IO19.")]
TITLE = "AP ELECTRIC · AP GATE - pasarela Wi-Fi, AP BUS y RS-485 Modbus RTU"
SUBTITLES = ["Placa de 2 capas, 1 oz (JLCPCB)", "ESP32-C3, CAN, RS-485 protegido, 5 V y 3.3 V desde el bus, Qwiic local"]
COMPANY = "PCB 88 x 56 mm, 2 capas"
COSTURA = 5.0
PAPER = "A3"
OCULTAR_REF = ("J1", "J2", "J4")

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
