"""AP Electric · AP Home POTENCIA rev A (CONCEPTO): la parte de 127 V CA de AP Home, separada del cerebro.

Va en la caja de registro / junto a la luminaria. Lleva SOLO la red: relé Omron G2RL-1A-E-HA 5 V, fuente Mean Well IRM-03-5 (5 V, aislada) con fusible T2A y
varistor, y la entrada de apagador de red con LTV-814S. La baja tensión sale por un cable corto de 4 hilos (JST XH): 5 V, 0 V, mando del relé y estado del apagador.
El cerebro (ESP32-C3, Wi-Fi) es otra placa chica, AP Home CEREBRO, que puede ir fuera de la caja metálica para tener señal.
Mismo circuito y mismo trazado de red que AP Home rev A (aislamiento: 6.0 mm en el aire y 6.4 mm por la superficie entre red y baja tensión).

    bash ../../tools/rutear.sh ap-electric/home_potencia AP_HOME_POTENCIA
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import placa  # noqa: E402
import conectores  # noqa: E402

PROJECT = "AP_HOME_POTENCIA"
NS = uuid.UUID("9a3c5e7f-2b4d-4c6a-8e1f-3d5b7a9c1e32")
ROOT_UUID = "1d3f5b7a-9c2e-4a4b-b6d8-0f2c4e6a8b50"
R06, R12, C06, C08, C12 = ("Resistor_SMD:R_0603_1608Metric", "Resistor_SMD:R_1206_3216Metric",
                           "Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_0805_2012Metric", "Capacitor_SMD:C_1206_3216Metric")
R, C = "Device:R", "Device:C"
KF2 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal"


C_ = [
    ('J1', 'KF128-5.08-2P', 'Connector:Screw_Terminal_01x02', 'TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal',
     {'1': 'L', '2': 'N'},
     'Red 127 VCA: 1 = L (fase), 2 = N (neutro)'),
    ('J2', 'KF128-5.08-2P', 'Connector:Screw_Terminal_01x02', 'TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal',
     {'1': 'LS', '2': 'SW'},
     '1 = LS (fase a la lámpara), 2 = SW (fase que regresa del apagador; solo Home Switch)'),
    ('K1', 'G2RL-1A-E-HA DC5', 'Relay:Relay_SPST-NO', 'Relay_THT:Relay_SPST_Omron_G2RL-1A-E',
     {'A1': 'V5', 'A2': 'BOB', '13': 'L', '14': 'LS'},
     'Omron G2RL-1A-E-HA 5 V (16 A 250 VCA resistivo, hoja del fabricante)'),
    ('F1', 'T2A 250VCA', 'Device:Fuse', 'LetreroLab:Fuse_2410_6125Metric',
     {'1': 'L', '2': 'LF'},
     'Fusible de retardo de la fuente y de la entrada (la carga la protege el interruptor de la instalación)'),
    ('RV1', '10D471K', 'Device:Varistor', 'Varistor:RV_Disc_D12mm_W5mm_P7.5mm',
     {'1': 'LF', '2': 'N'},
     'Varistor contra picos'),
    ('PS1', 'IRM-03-5', 'Converter_ACDC:IRM-03-5', 'Converter_ACDC:Converter_ACDC_MeanWell_IRM-03-xx_THT',
     {'1': 'LF', '3': 'N', '5': None, '14': 'GND', '16': 'V5'},
     'Mean Well 5 V 600 mA, aislada y certificada'),
    ('RW1', '100k', 'Device:R', 'Resistor_SMD:R_1206_3216Metric',
     {'1': 'SW', '2': 'SWA'},
     'Entrada de apagador (1 de 2): ~0.64 mA a 127 VCA, 41 mW'),
    ('RW2', '100k', 'Device:R', 'Resistor_SMD:R_1206_3216Metric',
     {'1': 'SWA', '2': 'SWB'},
     'Entrada de apagador (2 de 2)'),
    ('OK1', 'LTV-814S', 'Isolator:EL814', 'Package_DIP:SMDIP-4_W9.53mm',
     {'1': 'N', '2': 'SWB', '3': 'GND', '4': 'SWO'},
     'Optoacoplador de entrada CA (LED antiparalelos), 5 kVrms'),
    ('C1', '22uF 25V', 'Device:C', 'Capacitor_SMD:C_1206_3216Metric',
     {'1': 'V5', '2': 'GND'},
     'Salida de la fuente'),
    ('Q1', 'AO3400A', 'Transistor_FET:AO3400A', 'Package_TO_SOT_SMD:SOT-23',
     {'1': 'RELE', '2': 'GND', '3': 'BOB'},
     'Bobina del relé (lado bajo)'),
    ('R1', '10k', 'Device:R', 'Resistor_SMD:R_0603_1608Metric',
     {'1': 'RELE', '2': 'GND'},
     'Relé apagado al arrancar'),
    ('D1', 'SS14', 'Device:D_Schottky', 'Diode_SMD:D_SMA',
     {'1': 'V5', '2': 'BOB'},
     'Diodo de la bobina'),
    ("J4", "A CEREBRO", conectores.SYM[4], conectores.XH4, {"1": "V5", "2": "GND", "3": "RELE", "4": "SWO"},
     "Cable de BAJA tensión al cerebro (JST XH, 1 a 1): 1 = 5 V, 2 = 0 V, 3 = mando del relé (3.3 V), 4 = estado del apagador (salida del optoacoplador, aislada)"),
]

W, H = 55.0, 68.0
RADIO_ESQUINA = 2.0
HOLES = [(51.5, 3.5), (51.5, 64.5)]
POS = {
    "J1": (11.08, 6.0, 180), "J2": (36.0, 6.0, 180),
    "K1": (49.5, 40.0, 180), "F1": (9.0, 16.0, 180), "RV1": (5.0, 21.0, 0), "PS1": (4.5, 30.0, 0),
    "RW1": (28.0, 14.3, 270), "RW2": (28.0, 19.8, 270), "OK1": (35.0, 29.0, 270),
    "Q1": (43.0, 46.0, 0), "R1": (46.5, 46.0, 90), "D1": (51.0, 46.3, 90),
    "C1": (28.5, 50.0, 0), "J4": (31.0, 58.0, 0),
}
RED = ["L", "N", "LF", "LS", "SW"]
NETCLASS = {"Red": (2.0, 0.6, RED), "RedR": (0.6, 0.6, ["SWA", "SWB"]), "Media": (0.6, 0.25, ["V5", "BOB", "VBUS"])}
PRE = [
    ("LS", 2.5, [(36.0, 6.0), (36.0, 11.0), (40.0, 15.0), (49.5, 15.0)]),
    ("L", 2.5, [(11.08, 6.0), (11.08, 11.1), (37.2, 11.1), (37.2, 20.0), (49.5, 20.0)], "B"),
    ("L", 1.0, [(11.08, 6.0), (11.8, 8.0), (11.8, 16.0)]),
    ("LF", 1.0, [(6.2, 16.0), (5.0, 17.5), (5.0, 21.0), (5.0, 28.5), (4.5, 30.0)]),
    ("N", 1.0, [(6.0, 6.0), (6.0, 12.0), (9.0, 15.0), (9.0, 24.24), (38.5, 24.24)], "B"),
    ("N", 1.0, [(12.5, 24.24), (12.5, 23.2)], "B"),
    ("N", 1.0, [(9.0, 24.24), (9.0, 33.0), (6.92, 35.08), (4.5, 35.08)], "B"),
    ("N", 0.6, [(38.5, 24.24), (36.27, 24.24)]),
    ("SW", 0.6, [(30.92, 6.0), (28.0, 9.0), (28.0, 12.83)]),
    ("SWA", 0.6, [(28.0, 15.78), (28.0, 18.33)]),
    ("SWB", 0.6, [(28.0, 21.28), (31.0, 24.24), (33.73, 24.24)]),
]
PREVIAS = [("N", 38.5, 24.24)]
DRU = ('(rule "aislamiento_red" (condition "(A.NetClass == \'Red\' || A.NetClass == \'RedR\') && B.NetClass != \'Red\' && B.NetClass != \'RedR\' && B.NetName != \'unconnected-*\'") '
       '(constraint clearance (min 6.4mm)) (constraint creepage (min 6.4mm)))\n'
       '(rule "entre_redes" (condition "A.NetClass == \'Red\' && B.NetClass == \'Red\' && A.NetName != B.NetName") '
       '(constraint clearance (min 2.0mm)) (constraint creepage (min 2.4mm)))\n')
SIN_RELLENO = [[(0.3, 0.3), (54.7, 0.3), (54.7, 28.5), (12.0, 28.5), (12.0, 42.5), (0.3, 42.5)]]
SILK = [
    ("L   N", 8.5, 12.8, 1.0, "F"), ("SW  LS", 33.5, 13.6, 1.0, "F"),
    ("PELIGRO 127 VCA", 18.0, 26.5, 0.9, "F"),
    ("AP HOME POTENCIA rev A", 17.0, 46.5, 0.9, "F"),
    ("A CEREBRO", 36.0, 63.5, 0.8, "F"),
    ("AP Electric AP Home POTENCIA rev A - CONCEPTO. SW = entrada de red, no contacto seco.", 27.5, 2.0, 0.8, "B"),
]
FLAGS = [("LF", 50.8, 20.32), ("N", 66.04, 20.32)]
NOTES = [(150.0, 15.0, "AP Electric · AP Home POTENCIA rev A (CONCEPTO): G2RL-1A-E-HA 5 V, IRM-03-5 + T2A + 10D471K,\n"
                       "entrada de apagador de red con LTV-814S. Sin cerebro: va a AP Home CEREBRO por un cable de baja tensión.")]
TITLE = "AP Electric · AP Home POTENCIA rev A - 1 canal de 127 VCA, sin cerebro (CONCEPTO)"
SUBTITLES = ["Placa de 2 capas, 2 oz (JLCPCB)", "Estado: concepto. Límites del producto por determinar por ensayo"]
COMPANY = "PCB 55 x 68 mm, 2 capas, 2 oz"

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
