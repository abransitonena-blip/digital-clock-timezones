"""AP Electric · AP Home rev A (CONCEPTO): una placa para dos SKU de alumbrado de 127 V CA.

- Home Plug: va dentro de una caja con clavija y receptáculo encerrados (NEMA 5-15, tierra pasante que no toca la
  placa). El usuario solo enchufa. Los bornes de la placa se unen a la clavija y al receptáculo dentro de la caja.
  La entrada SW no se usa (sin cable).
- Home Switch: instalación fija con fase, neutro y entrada de apagador (SW), en una caja de registro o junto a la
  luminaria; la instala una persona competente con el circuito desenergizado.

Bloques:
- Relé Omron G2RL-1A-E-HA DC5 (16 A 250 VCA resistivo según la hoja). Límite del producto: POR DETERMINAR
  (meta 6 A de alumbrado a 127 V; la irrupción de lámparas LED se medirá).
- Fuente encapsulada Mean Well IRM-03-5 (85-305 VCA, 5 V 600 mA, aislada y certificada por su fabricante) con
  fusible de retardo T2A y varistor 10D471K. No hay fuente capacitiva.
- Entrada de apagador SW = ENTRADA DE RED (fase que regresa del apagador): 2 x 100k 1206 en serie + LTV-814S (entrada CA,
  5 kVrms) a N. No es contacto seco: no se conecta nada de baja tensión a SW.
- ESP32-C3-WROOM-02; botón (IO9) y LED verde / rojo; AP63203 de 5 V a 3.3 V; pines de programación (USB D+/D-).
- Aislamiento: red arriba y a la izquierda (sin relleno); DRC: 6.0 mm en el aire y 6.4 mm por la superficie entre la red
  y la baja tensión; 2.0 / 2.4 mm entre redes de red distintas.

    bash ../../tools/rutear.sh ap-electric/home AP_HOME
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import placa  # noqa: E402

PROJECT = "AP_HOME"
NS = uuid.UUID("4b2d6f8a-1c3e-4a5b-9d7f-0e2a4c6b8d13")
ROOT_UUID = "6e8a0c2b-4d6f-4e1a-8b3c-5d7f9a1b3c24"
R06, R12, C06, C08, C12 = ("Resistor_SMD:R_0603_1608Metric", "Resistor_SMD:R_1206_3216Metric",
                           "Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_0805_2012Metric", "Capacitor_SMD:C_1206_3216Metric")
R, C = "Device:R", "Device:C"
KF2 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal"

C_ = [
    # --- red ---
    ("J1", "KF128-5.08-2P", "Connector:Screw_Terminal_01x02", KF2, {"1": "L", "2": "N"},
     "Red 127 VCA: 1 = L (fase), 2 = N (neutro)"),
    ("J2", "KF128-5.08-2P", "Connector:Screw_Terminal_01x02", KF2, {"1": "LS", "2": "SW"},
     "1 = LS (fase a la lámpara), 2 = SW (fase que regresa del apagador; solo Home Switch)"),
    ("K1", "G2RL-1A-E-HA DC5", "Relay:Relay_SPST-NO", "Relay_THT:Relay_SPST_Omron_G2RL-1A-E",
     {"A1": "V5", "A2": "BOB", "13": "L", "14": "LS"}, "Omron G2RL-1A-E-HA 5 V (16 A 250 VCA resistivo, hoja del fabricante)"),
    ("F1", "T2A 250VCA", "Device:Fuse", "LetreroLab:Fuse_2410_6125Metric", {"1": "L", "2": "LF"},
     "Fusible de retardo de la fuente y de la entrada (la carga la protege el interruptor de la instalación)"),
    ("RV1", "10D471K", "Device:Varistor", "Varistor:RV_Disc_D12mm_W5mm_P7.5mm", {"1": "LF", "2": "N"},
     "Varistor contra picos"),
    ("PS1", "IRM-03-5", "Converter_ACDC:IRM-03-5", "Converter_ACDC:Converter_ACDC_MeanWell_IRM-03-xx_THT",
     {"1": "LF", "3": "N", "5": None, "14": "GND", "16": "V5"}, "Mean Well 5 V 600 mA, aislada y certificada"),
    ("RW1", "100k", R, R12, {"1": "SW", "2": "SWA"}, "Entrada de apagador (1 de 2): ~0.64 mA a 127 VCA, 41 mW"),
    ("RW2", "100k", R, R12, {"1": "SWA", "2": "SWB"}, "Entrada de apagador (2 de 2)"),
    ("OK1", "LTV-814S", "Isolator:EL814", "Package_DIP:SMDIP-4_W9.53mm",
     {"1": "N", "2": "SWB", "3": "GND", "4": "SWO"}, "Optoacoplador de entrada CA (LED antiparalelos), 5 kVrms"),
    # --- 5 V y bobina ---
    ("C1", "22uF 25V", C, C12, {"1": "V5", "2": "GND"}, "Salida de la fuente"),
    ("Q1", "AO3400A", "Transistor_FET:AO3400A", "Package_TO_SOT_SMD:SOT-23", {"1": "RELE", "2": "GND", "3": "BOB"},
     "Bobina del relé (lado bajo)"),
    ("R1", "10k", R, R06, {"1": "RELE", "2": "GND"}, "Relé apagado al arrancar"),
    ("D1", "SS14", "Device:D_Schottky", "Diode_SMD:D_SMA", {"1": "V5", "2": "BOB"}, "Diodo de la bobina"),
    # --- 3.3 V ---
    ("U2", "AP63203WU", "Regulator_Switching:AP63203WU", "Package_TO_SOT_SMD:TSOT-23-6",
     {"1": "3V3", "2": "V5", "3": "V5", "4": "GND", "5": "SWP", "6": "BSTP"}, "Buck 3.3 V"),
    ("L1", "4.7uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR4030S", {"1": "SWP", "2": "3V3"}, "Bobina 3.3 V"),
    ("C2", "100nF", C, C06, {"1": "BSTP", "2": "SWP"}, "Bootstrap"),
    ("C3", "10uF 25V", C, C12, {"1": "V5", "2": "GND"}, "Entrada del buck"),
    ("C4", "22uF", C, C08, {"1": "3V3", "2": "GND"}, "Salida 3.3 V"),
    ("C5", "22uF", C, C08, {"1": "3V3", "2": "GND"}, "Salida 3.3 V"),
    # --- cerebro ---
    ("U1", "ESP32-C3-WROOM-02", "RF_Module:ESP32-C3-WROOM-02", "LetreroLab:ESP32-C3-WROOM-02_JLC",
     {"1": "3V3", "2": "EN", "3": "RELE", "4": "LV", "5": "LR", "6": "SWO", "7": "IO8", "8": "BOOT",
      "9": "GND", "10": None, "11": None, "12": None, "13": "USB_DN", "14": "USB_DP", "15": None,
      "16": "IO2", "17": None, "18": None, "19": "GND"},
     "IO4 = relé, IO5/IO6 = LED, IO7 = entrada de apagador, IO9 = botón"),
    ("C6", "10uF", C, C08, {"1": "3V3", "2": "GND"}, "Desacoplo del módulo"),
    ("C7", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo del módulo"),
    ("R2", "10k", R, R06, {"1": "3V3", "2": "EN"}, "Pull-up EN"),
    ("C8", "1uF", C, C06, {"1": "EN", "2": "GND"}, "Arranque retardado"),
    ("R3", "10k", R, R06, {"1": "3V3", "2": "BOOT"}, "Pull-up IO9"),
    ("R4", "10k", R, R06, {"1": "3V3", "2": "IO2"}, "IO2 en alto al arrancar"),
    ("R5", "10k", R, R06, {"1": "3V3", "2": "IO8"}, "IO8 en alto al arrancar"),
    ("R6", "100k", R, R06, {"1": "3V3", "2": "SWO"}, "Pull-up de la entrada de apagador"),
    ("SW1", "BOTON", "Switch:SW_Push", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", {"1": "BOOT", "2": "GND"},
     "Botón: corto = encender/apagar; 3 s = red de configuración; 10 s = fábrica"),
    ("R7", "1k", R, R06, {"1": "LV", "2": "LVA"}, "LED verde"),
    ("D2", "VERDE", "Device:LED", "LED_SMD:LED_0603_1608Metric", {"1": "GND", "2": "LVA"}, "Encendido"),
    ("R8", "1k", R, R06, {"1": "LR", "2": "LRA"}, "LED rojo"),
    ("D3", "ROJO", "Device:LED", "LED_SMD:LED_0603_1608Metric", {"1": "GND", "2": "LRA"}, "Falla"),
    ("J3", "PROG", "Connector_Generic:Conn_01x04", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
     {"1": "VBUS", "2": "USB_DN", "3": "USB_DP", "4": "GND"}, "Programación por USB en fábrica, SIN red conectada"),
    ("D4", "B5819W", "Device:D_Schottky", "Diode_SMD:D_SOD-123", {"1": "V5", "2": "VBUS"}, "5 V del USB al programar"),
]

W, H = 55.0, 80.0
RADIO_ESQUINA = 2.0
HOLES = [(51.5, 3.5), (3.6, 76.2)]
POS = {
    "J1": (11.08, 6.0, 180), "J2": (36.0, 6.0, 180),
    "K1": (49.5, 40.0, 180), "F1": (9.0, 16.0, 180), "RV1": (5.0, 21.0, 0), "PS1": (4.5, 30.0, 0),
    "RW1": (28.0, 14.3, 270), "RW2": (28.0, 19.8, 270), "OK1": (35.0, 29.0, 270),
    "R6": (36.3, 38.6, 90), "SW1": (30.0, 40.0, 0),
    "R7": (27.5, 45.5, 0), "D2": (31.0, 45.5, 0), "R8": (34.5, 45.5, 0), "D3": (38.0, 45.5, 0),
    "Q1": (43.0, 46.0, 0), "R1": (46.5, 46.0, 90), "D1": (51.0, 46.3, 90),
    "C1": (28.5, 50.0, 0), "C6": (33.0, 50.0, 0), "C7": (36.5, 50.0, 0),
    "R2": (41.0, 51.0, 0), "C8": (44.5, 51.0, 0), "R3": (48.0, 51.0, 0), "R4": (51.5, 51.0, 0), "R5": (30.5, 52.6, 0),
    "U1": (40.5, 61.0, 180),
    "U2": (6.0, 69.0, 0), "L1": (12.5, 69.0, 0), "C2": (9.5, 73.3, 0), "C3": (2.0, 69.0, 90),
    "C4": (18.0, 67.5, 0), "C5": (18.0, 71.5, 0),
    "J3": (23.0, 67.0, 0), "D4": (17.5, 75.5, 0),
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
SIN_COBRE = [[(31.0, 68.0), (54.7, 68.0), (54.7, 79.7), (31.0, 79.7)]]       # antena del ESP32
SILK = [
    ("L   N", 8.5, 12.8, 1.0, "F"), ("SW  LS", 33.5, 13.6, 1.0, "F"),
    ("PELIGRO 127 VCA", 18.0, 26.5, 0.9, "F"),
    ("AP HOME rev A", 20.0, 46.0, 1.0, "F"),
    ("PROG: solo sin red", 17.0, 64.8, 0.8, "F"),
    ("AP Electric AP Home rev A - CONCEPTO. SW = entrada de red, no contacto seco.", 27.5, 2.0, 0.8, "B"),
]
FLAGS = [("3V3", 35.56, 20.32), ("LF", 50.8, 20.32), ("N", 66.04, 20.32)]
NOTES = [(150.0, 15.0, "AP Electric · AP Home rev A (CONCEPTO): G2RL-1A-E-HA 5 V, IRM-03-5 + T2A + 10D471K,\n"
                       "entrada de apagador de red con LTV-814S, ESP32-C3. Un PCB para Home Plug y Home Switch.")]
TITLE = "AP Electric · AP Home rev A - 1 canal de 127 VCA para Home Plug y Home Switch (CONCEPTO)"
SUBTITLES = ["Placa de 2 capas, 2 oz (JLCPCB)", "Estado: concepto. Límites del producto por determinar por ensayo"]
COMPANY = "PCB 55 x 80 mm, 2 capas, 2 oz"

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
