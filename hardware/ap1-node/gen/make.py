"""AP ELECTRIC · AP NODE: nodo remoto del AP BUS (24 V DC + CAN) con ESP32-C3.

Para qué: llevar entradas y salidas lejos del tablero principal (otra planta, la bomba, la azotea) con UN solo cable
de 4 hilos: +24 V, CAN_H, CAN_L y 0 V. El nodo reparte la alimentación a sus módulos locales (AP PRO DO8, AP INPUT,
AI4) por Qwiic y habla con el CORE por CAN a 250 kbit/s. El mismo cable sigue al siguiente nodo.

Circuito:
- J1 (ENTRA) y J2 (SIGUE): JST XH de 4 patas, 1 = +24 V, 2 = CAN_H, 3 = CAN_L, 4 = 0 V, unidos en la placa (el bus
  pasa de largo: hasta 3 A por el conector XH).
- Entrada del nodo: fusible rápido de 3 A (1206), diodo SS34 en serie (polaridad invertida) y supresor SMBJ26A.
- U2 LMR16006 (60 V): 5 V para el transceptor CAN. El USB-C también alimenta los 5 V por D3 (B5819W) para programar
  en el taller sin bus.
- U5 AP63203: 3.3 V (2 A) desde los 5 V para el ESP32 y los módulos Qwiic.
- U4 TJA1051T/3 (NXP): transceptor CAN de alta velocidad, VCC 5 V y VIO 3.3 V (lógica directa al ESP32), modo
  silencioso desactivado (S a 0 V). Su TXD tiene pull-up interno: el bus queda en recesivo mientras el ESP32 arranca.
- Terminación: 120 Ohm entre CAN_H y CAN_L al cerrar JP3. Solo en los DOS extremos del cable.
- U1 ESP32-C3-WROOM-02: controlador CAN interno (TWAI) en IO4 (TX) e IO5 (RX); I2C en IO2/IO8 con pull-up de 4.7k
  (también fijan el arranque); IO9 = MODO/BOOT; IO21 = LED de estado; IO10 = LED del bus; IO6/IO7 al conector EXT.
- Antena del módulo en el borde superior derecho, sin cobre debajo.
- No aislado: el 0 V del bus es el GND del nodo, igual que en el resto del ecosistema (una sola fuente de 24 V).
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import placa  # noqa: E402
import conectores  # noqa: E402

PROJECT = "AP_Node"
NS = uuid.UUID("975733d8-1a77-46d8-ab60-e81fdf3fce69")
ROOT_UUID = "12d9638d-82fd-4acc-8197-da80187649df"
R06, C06, C08, C12 = ("Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric",
                      "Capacitor_SMD:C_0805_2012Metric", "Capacitor_SMD:C_1206_3216Metric")
SMA = "Diode_SMD:D_SMA"
R, C = "Device:R", "Device:C"
BUS = {"1": "BUS24", "2": "CANH", "3": "CANL", "4": "GND"}
ESP = {"1": "3V3", "2": "EN", "3": "CAN_TX", "4": "CAN_RX", "5": "EXT1", "6": "EXT2", "7": "SCL", "8": "BOOT",
       "9": "GND", "10": "LEDB", "11": None, "12": "LEDV", "13": "USB_DN", "14": "USB_DP", "15": None, "16": "SDA",
       "17": None, "18": None, "19": "GND"}

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
    ("J4", "EXT", "Connector:Conn_01x04_Pin", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
     {"1": "3V3", "2": "EXT1", "3": "EXT2", "4": "GND"}, "IO6 / IO7 libres (sensor 1-wire, botón, etc.)"),
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
    "J3": (30.0, 3.6, 180), "J4": (44.0, 3.5, 90),
    "TP1": (52.0, 44.0, 0), "TP2": (56.0, 44.0, 0), "TP3": (60.0, 44.0, 0), "TP4": (64.0, 44.0, 0),
}

NETCLASS = {"Potencia": (2.0, 0.3, ["BUS24"]),
            "Media": (0.6, 0.2, ["VF", "V24", "V5", "SW", "VBUS", "3V3", "SWP"]),
            "CAN": (0.4, 0.2, ["CANH", "CANL"])}
SIN_COBRE = [[(53.5, 0.3), (82.5, 0.3), (82.5, 12.3), (53.5, 12.3)]]    # bajo la antena del ESP32
SILK = [
    ("+24 H L 0V", 7.8, 46.2, 0.8, "F"), ("+24 H L 0V", 21.8, 46.2, 0.8, "F"),
    ("ENTRA", 7.8, 55.0, 0.8, "F"), ("SIGUE", 21.8, 55.0, 0.8, "F"),
    ("120R: solo extremos", 38.0, 53.6, 0.8, "F"),
    ("MODO", 60.0, 37.6, 0.8, "F"), ("RESET", 70.0, 37.6, 0.8, "F"),
    ("OK", 81.0, 32.3, 0.8, "F"), ("BUS", 81.4, 36.4, 0.8, "F"),
    ("AP NODE", 66.0, 49.0, 1.4, "F"),
    ("AP ELECTRIC  AP NODE  AP BUS 24V + CAN", 44.0, 54.8, 1.0, "B"),
    ("Bus: 1 +24V  2 CAN_H  3 CAN_L  4 0V  (pasa de largo, max 3 A)", 44.0, 52.8, 0.8, "B"),
]
FLAGS = [("BUS24", 20.32, 20.32), ("GND", 35.56, 20.32), ("V24", 50.8, 20.32), ("V5", 66.04, 20.32),
         ("3V3", 81.28, 20.32), ("VBUS", 96.52, 20.32)]
NOTES = [(150.0, 15.0, "AP ELECTRIC · AP NODE: ESP32-C3 + TJA1051T/3. CAN TX = IO4, CAN RX = IO5, SDA/SCL = IO2/IO8,\n"
                       "MODO = IO9, LED = IO21, LED bus = IO10, EXT = IO6/IO7, USB = IO18/IO19. AP BUS: 24 V + CAN 250 kbit/s.")]
TITLE = "AP ELECTRIC · AP NODE - nodo remoto del AP BUS (24 V + CAN)"
SUBTITLES = ["Placa de 2 capas, 1 oz (JLCPCB)", "ESP32-C3, transceptor CAN, 5 V y 3.3 V desde el bus, Qwiic local"]
COMPANY = "PCB 88 x 56 mm, 2 capas"
COSTURA = 5.0
PAPER = "A3"
OCULTAR_REF = ("J1", "J2")

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
