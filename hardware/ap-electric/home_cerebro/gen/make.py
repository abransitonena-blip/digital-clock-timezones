"""AP Electric · AP Home CEREBRO rev A (CONCEPTO): el cerebro chico de AP Home, SOLO baja tensión.

ESP32-C3-WROOM-02 (Wi-Fi/BLE), 3.3 V, botón, dos LED y pines de programación. Recibe 5 V de la placa AP Home POTENCIA por un cable de 4 hilos (JST XH) y le manda
el mando del relé; de vuelta lee el estado del apagador (salida aislada del optoacoplador). No toca la red de CA: se puede poner fuera de la caja metálica.

    bash ../../tools/rutear.sh ap-electric/home_cerebro AP_HOME_CEREBRO
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import placa  # noqa: E402
import conectores  # noqa: E402

PROJECT = "AP_HOME_CEREBRO"
NS = uuid.UUID("5e7a9c1b-3d5f-4b7a-a2c4-6e8b0d2f4a71")
ROOT_UUID = "8c0e2a4b-6d8f-4c1a-9b3d-5f7a1c3e5b92"
R06, R12, C06, C08, C12 = ("Resistor_SMD:R_0603_1608Metric", "Resistor_SMD:R_1206_3216Metric",
                           "Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_0805_2012Metric", "Capacitor_SMD:C_1206_3216Metric")
R, C = "Device:R", "Device:C"
KF2 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal"


C_ = [
    ('U2', 'AP63203WU', 'Regulator_Switching:AP63203WU', 'Package_TO_SOT_SMD:TSOT-23-6',
     {'1': '3V3', '2': 'V5', '3': 'V5', '4': 'GND', '5': 'SWP', '6': 'BSTP'},
     'Buck 3.3 V'),
    ('L1', '4.7uH', 'Device:L', 'Inductor_SMD:L_Changjiang_FNR4030S',
     {'1': 'SWP', '2': '3V3'},
     'Bobina 3.3 V'),
    ('C2', '100nF', 'Device:C', 'Capacitor_SMD:C_0603_1608Metric',
     {'1': 'BSTP', '2': 'SWP'},
     'Bootstrap'),
    ('C3', '10uF 25V', 'Device:C', 'Capacitor_SMD:C_1206_3216Metric',
     {'1': 'V5', '2': 'GND'},
     'Entrada del buck'),
    ('C4', '22uF', 'Device:C', 'Capacitor_SMD:C_0805_2012Metric',
     {'1': '3V3', '2': 'GND'},
     'Salida 3.3 V'),
    ('C5', '22uF', 'Device:C', 'Capacitor_SMD:C_0805_2012Metric',
     {'1': '3V3', '2': 'GND'},
     'Salida 3.3 V'),
    ('U1', 'ESP32-C3-WROOM-02', 'RF_Module:ESP32-C3-WROOM-02', 'LetreroLab:ESP32-C3-WROOM-02_JLC',
     {'1': '3V3', '2': 'EN', '3': 'RELE', '4': 'LV', '5': 'LR', '6': 'SWO', '7': 'IO8', '8': 'BOOT', '9': 'GND', '10': None, '11': None, '12': None, '13': 'USB_DN', '14': 'USB_DP', '15': None, '16': 'IO2', '17': None, '18': None, '19': 'GND'},
     'IO4 = relé, IO5/IO6 = LED, IO7 = entrada de apagador, IO9 = botón'),
    ('C6', '10uF', 'Device:C', 'Capacitor_SMD:C_0805_2012Metric',
     {'1': '3V3', '2': 'GND'},
     'Desacoplo del módulo'),
    ('C7', '100nF', 'Device:C', 'Capacitor_SMD:C_0603_1608Metric',
     {'1': '3V3', '2': 'GND'},
     'Desacoplo del módulo'),
    ('R2', '10k', 'Device:R', 'Resistor_SMD:R_0603_1608Metric',
     {'1': '3V3', '2': 'EN'},
     'Pull-up EN'),
    ('C8', '1uF', 'Device:C', 'Capacitor_SMD:C_0603_1608Metric',
     {'1': 'EN', '2': 'GND'},
     'Arranque retardado'),
    ('R3', '10k', 'Device:R', 'Resistor_SMD:R_0603_1608Metric',
     {'1': '3V3', '2': 'BOOT'},
     'Pull-up IO9'),
    ('R4', '10k', 'Device:R', 'Resistor_SMD:R_0603_1608Metric',
     {'1': '3V3', '2': 'IO2'},
     'IO2 en alto al arrancar'),
    ('R5', '10k', 'Device:R', 'Resistor_SMD:R_0603_1608Metric',
     {'1': '3V3', '2': 'IO8'},
     'IO8 en alto al arrancar'),
    ('R6', '100k', 'Device:R', 'Resistor_SMD:R_0603_1608Metric',
     {'1': '3V3', '2': 'SWO'},
     'Pull-up de la entrada de apagador'),
    ('SW1', 'BOTON', 'Switch:SW_Push', 'Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A',
     {'1': 'BOOT', '2': 'GND'},
     'Botón: corto = encender/apagar; 3 s = red de configuración; 10 s = fábrica'),
    ('R7', '1k', 'Device:R', 'Resistor_SMD:R_0603_1608Metric',
     {'1': 'LV', '2': 'LVA'},
     'LED verde'),
    ('D2', 'VERDE', 'Device:LED', 'LED_SMD:LED_0603_1608Metric',
     {'1': 'GND', '2': 'LVA'},
     'Encendido'),
    ('R8', '1k', 'Device:R', 'Resistor_SMD:R_0603_1608Metric',
     {'1': 'LR', '2': 'LRA'},
     'LED rojo'),
    ('D3', 'ROJO', 'Device:LED', 'LED_SMD:LED_0603_1608Metric',
     {'1': 'GND', '2': 'LRA'},
     'Falla'),
    ('J3', 'PROG', 'Connector_Generic:Conn_01x04', 'Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',
     {'1': 'VBUS', '2': 'USB_DN', '3': 'USB_DP', '4': 'GND'},
     'Programación por USB en fábrica, SIN red conectada'),
    ('D4', 'B5819W', 'Device:D_Schottky', 'Diode_SMD:D_SOD-123',
     {'1': 'V5', '2': 'VBUS'},
     '5 V del USB al programar'),
    ("J1", "A POTENCIA", conectores.SYM[4], conectores.XH4, {"1": "V5", "2": "GND", "3": "RELE", "4": "SWO"},
     "Cable de BAJA tensión a la placa de potencia (JST XH, 1 a 1): 1 = 5 V, 2 = 0 V, 3 = mando del relé (3.3 V), 4 = estado del apagador"),
]

W, H = 42.0, 56.0
RADIO_ESQUINA = 2.0
HOLES = [(3.5, 3.5), (38.5, 3.5)]
POS = {
    "J1": (11.0, 4.5, 0), "J3": (25.5, 3.5, 90),
    "U2": (6.0, 12.0, 0), "L1": (13.0, 12.0, 0), "C2": (9.5, 16.0, 0), "C3": (2.0, 12.0, 90), "C4": (18.5, 10.5, 0), "C5": (18.5, 14.5, 0),
    "D4": (26.0, 9.0, 0), "SW1": (36.0, 14.0, 0),
    "C6": (4.0, 20.0, 0), "C7": (7.5, 20.0, 0), "R2": (11.0, 20.0, 0), "C8": (14.5, 20.0, 0), "R3": (18.0, 20.0, 0), "R4": (21.5, 20.0, 0),
    "R5": (25.0, 20.0, 0), "R6": (28.5, 20.0, 0),
    "R7": (4.0, 23.0, 0), "D2": (8.0, 23.0, 0), "R8": (12.0, 23.0, 0), "D3": (16.0, 23.0, 0),
    "U1": (21.0, 36.0, 180),
}
NETCLASS = {"Media": (0.6, 0.25, ["V5", "VBUS"])}
PRE = []
SIN_COBRE = [[(8.0, 43.0), (41.7, 43.0), (41.7, 55.7), (8.0, 55.7)]]       # antena del ESP32
SILK = [
    ("AP HOME CEREBRO rev A", 21.0, 25.5, 0.8, "F"),
    ("A POTENCIA", 6.0, 8.0, 0.8, "F"),
    ("PROG sin red", 16.0, 8.0, 0.8, "F"),
    ("AP Home CEREBRO rev A - CONCEPTO - 5 V", 21.0, 52.0, 0.8, "B"),
]
FLAGS = [("3V3", 35.56, 20.32), ("V5", 50.8, 20.32), ("GND", 66.04, 20.32)]
NOTES = [(150.0, 15.0, "AP Electric · AP Home CEREBRO rev A (CONCEPTO): ESP32-C3-WROOM-02, AP63203 (5 V a 3.3 V), botón y LED.\n"
                       "Solo baja tensión: recibe 5 V y manda el relé de la placa de potencia por un cable de 4 hilos.")]
TITLE = "AP Electric · AP Home CEREBRO rev A - cerebro de baja tensión de AP Home (CONCEPTO)"
SUBTITLES = ["Placa de 2 capas (JLCPCB)", "Estado: concepto"]
COMPANY = "PCB 42 x 56 mm, 2 capas"

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
