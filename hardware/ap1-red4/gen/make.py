"""AP ELECTRIC · AP RED 4: 4 relevadores para cargas de red de 127/220 VCA (focos, contactos, bombas chicas).

- 4 relevadores Songle SRD-24VDC-SL-C (10 A 250 VCA resistivos), bobina de 24 V con MOSFET AO3400A, diodo y LED.
- Contacto seco por canal en su propia bornera KF128 (COM, NA): la fase de cada carga pasa por su relevador.
- Mando por Qwiic con el mismo expansor TCA9554 del DO8: el programa lo ve como salidas S9-S12 (0x21) sin cambios.
  Dirección: 0x21 de fábrica; JP1 (A0) y JP2 (A1) la cambian a 0x20, 0x22 o 0x23 (el rango de los DO8).
- Alimentación de las bobinas: 24 V DC por JST VH 2 (por ejemplo del J3 +V del AP UNO), fusible y diodo serie.
- Aislamiento: la red solo está a la derecha de x = 30 (patas COM, NA, NC de los relevadores y borneras). Allí no
  hay relleno de cobre. Cada pata COM queda entre dos ranuras fresadas que la separan de las patas de la bobina
  (más de 7 mm por la superficie). El relevador da aislamiento básico (1500 VCA bobina-contacto): la placa va dentro
  de una caja cerrada y la instala un electricista, con un interruptor termomagnético para las cargas.

    bash ../tools/rutear.sh ap1-red4 AP_RED4
    python3 ../tools/unir_puntas.py kicad/AP_RED4.kicad_pcb 2.5   (une las puntas que el ruteador deja a décimas de un tramo fijo;
    en la versión entregada además se unió a mano la pata 3 de Q2 con su tramo de bobina, 2 mm en línea recta)
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import placa  # noqa: E402
import conectores  # noqa: E402

PROJECT = "AP_RED4"
NS = uuid.UUID("c3e5a7b9-2d4f-4618-9a0c-1e3f5a7b9d2c")
ROOT_UUID = "9f1b3d5e-7a2c-4e6b-8d0f-2a4c6e8b0d1f"
R06, C06, C08, C12 = ("Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric",
                      "Capacitor_SMD:C_0805_2012Metric", "Capacitor_SMD:C_1206_3216Metric")
QWIIC = "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal"
SJ3 = "Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm"
R, C = "Device:R", "Device:C"
BUS = {"1": "GND", "2": "3V3", "3": "SDA", "4": "SCL", "MP": "GND"}
KF = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal"
YK = [11.0, 28.0, 45.0, 62.0]                     # eje de cada relevador (pata COM)
XR = 34.0                                         # x de la pata COM

C_ = [
    ("J1", "QWIIC ENTRADA", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", QWIIC, dict(BUS),
     "Del CORE / AP UNO o del módulo anterior"),
    ("J2", "QWIIC SALIDA", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", QWIIC, dict(BUS), "Al siguiente módulo"),
    ("U1", "TCA9554PWR", "Interface_Expansion:TCA9554PW", "Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
     {"1": "A0", "2": "A1", "3": "GND", "4": "DO1", "5": "DO2", "6": "DO3", "7": "DO4", "8": "GND",
      "9": None, "10": None, "11": None, "12": None, "13": None, "14": "SCL", "15": "SDA", "16": "3V3"},
     "Expansor I2C (el del DO8): P0-P3 = relevadores 1-4"),
    ("C1", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U1"),
    ("JP1", "A0", "Jumper:SolderJumper_3_Bridged12", SJ3, {"1": "3V3", "2": "A0", "3": "GND"},
     "A0 = 1 de fábrica (0x21); cortar 1-2 y unir 2-3: A0 = 0"),
    ("JP2", "A1", "Jumper:SolderJumper_3_Bridged12", SJ3, {"1": "GND", "2": "A1", "3": "3V3"},
     "A1 = 0 de fábrica; cortar 1-2 y unir 2-3: A1 = 1 (0x22 / 0x23)"),
    ("J3", "24V", conectores.SYM[2], conectores.VH2, {"1": "VIN_RAW", "2": "GND"},
     "Bobinas: 1 = +24 V, 2 = 0 V (por ejemplo del J3 +V del AP UNO)"),
    ("F1", "3A", "Device:Fuse", "Fuse:Fuse_1206_3216Metric", {"1": "VIN_RAW", "2": "VF"}, "Fusible del 24 V"),
    ("D1", "SS34", "Device:D_Schottky", "Diode_SMD:D_SMA", {"1": "V24", "2": "VF"}, "Polaridad invertida"),
    ("C2", "10uF 50V", C, C12, {"1": "V24", "2": "GND"}, "Reserva de las bobinas"),
]
for k in range(1, 5):
    C_ += [
        ("Q%d" % k, "AO3400A", "Transistor_FET:AO3400A", "Package_TO_SOT_SMD:SOT-23",
         {"1": "DO%d" % k, "2": "GND", "3": "BOB%d" % k}, "Bobina del relevador %d (lado bajo)" % k),
        ("RD%d" % k, "10k", R, R06, {"1": "DO%d" % k, "2": "GND"}, "Relevador %d apagado al arrancar" % k),
        ("D%d" % (k + 1), "SS14", "Device:D_Schottky", "Diode_SMD:D_SMA", {"1": "V24", "2": "BOB%d" % k},
         "Diodo de la bobina %d" % k),
        ("RL%d" % k, "10k", R, R06, {"1": "V24", "2": "LA%d" % k}, "LED del relevador %d (2 mA)" % k),
        ("LD%d" % k, "VERDE", "Device:LED", "LED_SMD:LED_0603_1608Metric", {"1": "BOB%d" % k, "2": "LA%d" % k},
         "Relevador %d encendido" % k),
        ("K%d" % k, "SRD-24VDC-SL-C", "Relay:SANYOU_SRD_Form_C", "Relay_THT:Relay_SPDT_SANYOU_SRD_Series_Form_C",
         {"1": "COM%d" % k, "2": "BOB%d" % k, "3": "NA%d" % k, "4": None, "5": "V24"},
         "Relevador %d: 10 A 250 VCA (1 = COM, 3 = NA, 4 = NC sin usar)" % k),
        ("J%d" % (k + 3), "KF128-5.08-2P", "Connector:Screw_Terminal_01x02", KF,
         {"1": "NA%d" % k, "2": "COM%d" % k}, "Carga %d: COM = fase de entrada, NA = fase a la carga" % k),
    ]

W, H = 84.0, 73.0
RADIO_ESQUINA = 2.0
HOLES = [(3.5, 3.5), (3.5, 58.0), (80.5, 3.5), (80.5, 69.5)]
POS = {
    "J1": (3.6, 22.0, 90), "J2": (3.6, 32.0, 90),
    "U1": (10.0, 45.0, 0), "C1": (10.0, 40.0, 0), "JP1": (5.5, 52.0, 90), "JP2": (8.5, 52.0, 90),
    "J3": (5.0, 66.4, 0), "F1": (13.5, 63.0, 90), "D1": (13.5, 54.5, 90), "C2": (9.8, 57.5, 90),
}
for k, y in enumerate(YK, start=1):
    POS.update({
        "K%d" % k: (XR, y, 0),
        "Q%d" % k: (23.0, y + 6.0, 0), "RD%d" % k: (23.0, y + 2.2, 0),
        "D%d" % (k + 1): (24.5, y - 5.0, 180),            # cátodo (V24) hacia el relevador
        "RL%d" % k: (17.5, y - 2.0, 90), "LD%d" % k: (17.5, y + 2.0, 90),
        "J%d" % (k + 3): (70.0, y + 2.58, 90),            # tornillos arriba, el cable entra por el borde derecho
    })
NETCLASS = {"Red": (2.5, 0.5, ["COM%d" % k for k in range(1, 5)] + ["NA%d" % k for k in range(1, 5)]),
            "Media": (0.6, 0.2, ["VIN_RAW", "VF", "V24"] + ["BOB%d" % k for k in range(1, 5)])}
NETCLASS["Red"] = (2.5, 1.5, NETCLASS["Red"][2])
# la red va fija, trazada a mano en las dos caras (2.5 mm en cada una, 2 oz: 10 A), toda a la derecha de x = 30.
# Las patas NC (sin usar) también están a voltaje de red: el DRC las cuenta del lado de la red.
PRE = []
for y in YK:
    k = YK.index(y) + 1
    for capa in ("F", "B"):
        PRE += [("COM%d" % k, 2.5, [(XR, y), (60.0, y), (62.5, y - 2.5), (70.0, y - 2.5)], capa),
                ("NA%d" % k, 2.5, [(XR + 14.15, y + 6.05), (60.0, y + 6.05), (63.5, y + 2.58), (70.0, y + 2.58)], capa)]
    # bobina: de sus patas (x + 1.95, y -+6) hacia la baja tensión, por fuera de las ranuras
    # (el área sin relleno también es zona prohibida para el ruteador: los tramos salen hasta x < 27)
    PRE += [("V24", 0.6, [(XR + 1.95, y - 5.95), (27.45, y - 5.95), (26.5, y - 5.0)]),
            ("BOB%d" % k, 0.6, [(XR + 1.95, y + 6.05), (26.0, y + 6.05)])]
# aislamiento comprobado por el DRC: distancia en el aire y por la superficie (con las ranuras) entre la red y el resto
DRU = ('(rule "aislamiento_red" (condition "A.NetClass == \'Red\' && B.NetClass != \'Red\' && B.NetName != \'unconnected-*\'") '
       '(constraint clearance (min 3.0mm)) (constraint creepage (min 5.0mm)))\n')
# 24 V de las bobinas: un bus fijo por abajo (x = 26, sobre los cátodos de los diodos) que une las 4 bobinas con vías y baja al diodo de entrada D1
PRE += [("V24", 0.8, [(26.0, YK[0] - 5.95), (26.0, YK[-1] - 5.95), (15.5, YK[-1] - 5.95)], "B"),
        ("V24", 0.8, [(15.5, YK[-1] - 5.95), (13.5, YK[-1] - 5.5)])]
PREVIAS = [("V24", 26.0, y - 5.95) for y in YK] + [("V24", 15.5, YK[-1] - 5.95)]
SIN_RELLENO = [[(27.0, 0.3), (83.7, 0.3), (83.7, 72.7), (27.0, 72.7)]]
# ranuras a los lados de cada pata COM: la separan de las patas de la bobina (x + 1.95, y +-6)
RANURAS = []
for y in YK:
    RANURAS += [(XR - 2.5, y - 3.6, XR + 9.0, y - 2.6), (XR - 2.5, y + 2.6, XR + 9.0, y + 3.6)]
SILK = [
    ("AP RED 4", 10.0, 36.5, 1.2, "F"),
    ("PELIGRO: 127/220 VCA", 56.0, 71.2, 1.0, "F"),
    ("24V  0V", 7.5, 61.6, 0.8, "F"),
] + [("COM", 64.0, y - 2.5, 0.8, "F") for y in YK] + [("NA", 64.0, y + 2.58, 0.8, "F") for y in YK] + [("%d" % k, 52.0, y, 1.2, "F") for k, y in enumerate(YK, 1)] + [
    ("AP ELECTRIC  AP RED 4  4 x 10 A 250 VCA  bobinas 24 V  I2C 0x21", 42.0, 71.0, 1.0, "B"),
    ("Desconectar la red antes de abrir la caja. Interruptor termomagnetico por carga.", 42.0, 1.6, 0.8, "B"),
]
FLAGS = [("VIN_RAW", 20.32, 20.32), ("GND", 35.56, 20.32), ("V24", 50.8, 20.32), ("3V3", 66.04, 20.32)]
NOTES = [(150.0, 15.0, "AP ELECTRIC · AP RED 4: TCA9554 0x21 (0x20-0x23), 4 x SRD-24VDC-SL-C 10 A 250 VCA.\n"
                       "Red a la derecha de x = 30 mm, sin relleno; ranuras junto a cada pata COM.")]
TITLE = "AP ELECTRIC · AP RED 4 - 4 relevadores de 10 A para cargas de red"
SUBTITLES = ["Placa de 2 capas, 2 oz (JLCPCB)", "127/220 VCA, mando I2C como el DO8"]
COMPANY = "PCB 84 x 73 mm, 2 capas, 2 oz"

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
