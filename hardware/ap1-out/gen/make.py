"""AP ELECTRIC · AP PRO DO8: 8 salidas de 24 V DC protegidas para el programador AP-1 (AP CORE).

Reemplaza al AP OUTPUT (ULN2003, 7 salidas de 300 mA, sin protección contra cortos).

Para qué: bobinas de contactores y relevadores de interfaz, electroválvulas de 24 V DC, sirenas, balizas, lámparas
piloto, ventiladores de 24 V. Las cargas de red (bombas, motores, luces de 127/220 V) se mandan SIEMPRE con un
contactor o relevador de riel DIN certificado: la red NO entra a esta placa.

Circuito:
- Bus: I2C por Qwiic (J1 entra, J2 sigue al siguiente módulo) o por J3 (2.54 mm). 3.3 V y GND del programador.
- U1 TCA9554 (I2C 0x20-0x23, según JP1/JP2): al encender todas sus patas son entradas y RDn (10k) las mantiene en
  bajo: ninguna salida se activa hasta que el programa lo pide.
- U4/U5 74HCT125 a 5 V (entradas TTL: aceptan los 3.3 V del TCA9554) mueven la compuerta de cada salida con 5 V.
- U3 78L05: 5 V desde los 24 V (entrada hasta 30 V; el buffer y las compuertas consumen pocos mA).
- Q1-Q8 NCV8406A (onsemi): MOSFET de lado bajo de 65 V con protección propia contra cortocircuito, sobrecorriente
  (límite interno de unos 7 A), sobretemperatura (se apaga y se recupera solo), sobrevoltaje (enclavamiento) y ESD.
- D11-D18 SS14: diodo de bobina por salida, hacia +24 V.
- Entrada: fusible mini de auto (Keystone 3568, hasta 10 A) y supresor SMBJ26A. Si se conecta al revés, el supresor
  conduce y el fusible se abre.
- LED verde por salida: encendido = salida activa.
- No aislado: el 0 V de los 24 V es el GND del programador. Usar la misma fuente que alimenta la base.
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import placa  # noqa: E402
import conectores  # noqa: E402

PROJECT = "AP_DO8"
NS = uuid.UUID("e0546af7-a8d8-4959-bd5a-7c745928433b")
ROOT_UUID = "334cccb0-f9aa-4df4-b0e6-372ca1d028ab"
R06, C06, C12, R12 = ("Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric",
                      "Capacitor_SMD:C_1206_3216Metric", "Resistor_SMD:R_1206_3216Metric")
QWIIC = "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal"
SJ = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"
SOIC14 = "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm"
R, C = "Device:R", "Device:C"
BUS = {"1": "GND", "2": "3V3", "3": "SDA", "4": "SCL", "MP": "GND"}

C_ = [
    # --- bus I2C ---
    ("J1", "QWIIC ENTRADA", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", QWIIC, dict(BUS),
     "Del programador (o del módulo anterior)"),
    ("J2", "QWIIC SALIDA", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", QWIIC, dict(BUS),
     "Al siguiente módulo"),
    ("J3", "I2C", "Connector:Conn_01x04_Pin", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
     {"1": "GND", "2": "3V3", "3": "SDA", "4": "SCL"}, "Bus por cable dupont (mismo orden que Qwiic)"),
    ("U1", "TCA9554PWR", "Interface_Expansion:TCA9554PW", "Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
     {"1": "A0", "2": "A1", "3": "GND", "4": "IN1", "5": "IN2", "6": "IN3", "7": "IN4", "8": "GND",
      "9": "IN5", "10": "IN6", "11": "IN7", "12": "IN8", "13": None, "14": "SCL", "15": "SDA", "16": "3V3"},
     "Expansor I2C 0x20-0x23 (A2 = 0: rango de salidas)"),
    ("C1", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U1"),
    ("JP1", "A0", "Jumper:SolderJumper_2_Open", SJ, {"1": "3V3", "2": "A0"}, "Dirección: cerrado suma 1"),
    ("JP2", "A1", "Jumper:SolderJumper_2_Open", SJ, {"1": "3V3", "2": "A1"}, "Dirección: cerrado suma 2"),
    ("RA1", "10k", R, R06, {"1": "A0", "2": "GND"}, "A0 en 0 si JP1 abierto"),
    ("RA2", "10k", R, R06, {"1": "A1", "2": "GND"}, "A1 en 0 si JP2 abierto"),
    # --- 5 V y buffer de compuertas ---
    ("U3", "78L05G-AB3-R", "Regulator_Linear:L78L05_SOT89", "Package_TO_SOT_SMD:SOT-89-3",
     {"1": "V5", "2": "GND", "3": "V24"}, "5 V para el buffer y las compuertas (entrada hasta 30 V)"),
    ("C3", "100nF", C, C06, {"1": "V24", "2": "GND"}, "Entrada del 78L05"),
    ("C4", "1uF 25V", C, C06, {"1": "V5", "2": "GND"}, "Salida del 78L05"),
    ("U4", "74HCT125D", "74xx:74LS125", SOIC14,
     {"1": "GND", "2": "IN1", "3": "G1", "4": "GND", "5": "IN2", "6": "G2", "7": "GND",
      "8": "G3", "9": "IN3", "10": "GND", "11": "G4", "12": "IN4", "13": "GND", "14": "V5"},
     "Compuertas 1-4 a 5 V (entradas TTL)"),
    ("U5", "74HCT125D", "74xx:74LS125", SOIC14,
     {"1": "GND", "2": "IN5", "3": "G5", "4": "GND", "5": "IN6", "6": "G6", "7": "GND",
      "8": "G7", "9": "IN7", "10": "GND", "11": "G8", "12": "IN8", "13": "GND", "14": "V5"},
     "Compuertas 5-8 a 5 V (entradas TTL)"),
    ("C5", "100nF", C, C06, {"1": "V5", "2": "GND"}, "Desacoplo U4"),
    ("C6", "100nF", C, C06, {"1": "V5", "2": "GND"}, "Desacoplo U5"),
    # --- entrada de 24 V ---
    ("J4", "24V", conectores.SYM[2], conectores.VH2, {"1": "VIN_RAW", "2": "GND"},
     "Alimentación de las cargas: 1 = +24 V, 2 = 0 V (la misma fuente que la base). JST VH, hasta 10 A"),
    ("F1", "MINI 10A", "Device:Fuse", "Fuse:Fuseholder_Blade_Mini_Keystone_3568", {"1": "VIN_RAW", "2": "V24"},
     "Fusible mini de auto (ATM), hasta 10 A; se cambia sin soldar"),
    ("D2", "SMBJ26A", "Device:D_TVS", "Diode_SMD:D_SMB", {"1": "V24", "2": "GND"},
     "Supresor de picos; al revés conduce y abre el fusible"),
    ("C2", "10uF 50V", C, C12, {"1": "V24", "2": "GND"}, "Entrada"),
    ("C7", "10uF 50V", C, C12, {"1": "V24", "2": "GND"}, "Entrada"),
    ("TP1", "24V", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "V24"}, "Prueba: 24 V"),
    ("TP2", "GND", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "GND"}, "Prueba: tierra"),
    ("TP3", "5V", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "V5"}, "Prueba: 5 V"),
]
CX = [13.5 + 8.6 * k for k in range(8)]                 # pata 1 del conector de cada salida
for k, x in enumerate(CX, start=1):
    C_ += [
        ("J%d" % (k + 4), "Q%d" % k, conectores.SYM[2], conectores.XH2, {"1": "V24", "2": "Q%d" % k},
         "Salida %d: 1 = +24 V, 2 = salida (la carga va entre las dos). JST XH, hasta 1.5 A" % k),
        ("Q%d" % k, "NCV8406ASTT3G", "Transistor_FET:Q_NMOS_GDS", "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
         {"1": "G%d" % k, "2": "Q%d" % k, "3": "GND"},
         "Salida %d: MOSFET protegido 65 V (corto, sobrecorriente, temperatura)" % k),
        ("D%d" % (k + 10), "SS14", "Device:D_Schottky", "Diode_SMD:D_SMA", {"1": "V24", "2": "Q%d" % k},
         "Diodo de bobina de la salida %d" % k),
        ("RD%d" % k, "10k", R, R06, {"1": "IN%d" % k, "2": "GND"}, "Salida %d apagada al arrancar" % k),
        ("RL%d" % k, "10k", R, R06, {"1": "V24", "2": "LA%d" % k}, "LED de la salida %d (2 mA)" % k),
        ("DL%d" % k, "VERDE", "Device:LED", "LED_SMD:LED_0603_1608Metric", {"1": "Q%d" % k, "2": "LA%d" % k},
         "Salida %d activa" % k),
    ]

W, H = 88.0, 56.0
RADIO_ESQUINA = 2.0
HOLES = [(3.5, 3.5), (84.5, 39.5), (84.5, 52.5)]        # como la base: soporte DIN de 88 x 56
FX, FY = 8.0, 30.0                                      # portafusible: pata 1 (entrada) arriba, pata 2 (+24 V) abajo
YTR = 44.5                                              # tronco de +24 V sobre los conectores
POS = {
    "J1": (14.0, 3.6, 180), "J2": (58.0, 3.6, 180), "J3": (30.0, 3.5, 90),
    "U1": (42.0, 12.0, 0), "C1": (42.0, 16.6, 0),
    "JP1": (12.0, 10.0, 0), "JP2": (12.0, 13.5, 0), "RA1": (17.0, 10.0, 0), "RA2": (17.0, 13.5, 0),
    "U3": (70.0, 13.0, 0), "C3": (70.0, 17.8, 0), "C4": (74.8, 13.0, 90),
    "U4": (28.0, 17.0, 90), "U5": (56.0, 17.0, 90), "C5": (22.0, 17.0, 90), "C6": (62.0, 17.0, 90),
    "J4": (3.0, 50.4, 0), "F1": (FX, FY, 270), "D2": (5.5, 17.0, 90), "C2": (1.9, 17.0, 90), "C7": (1.9, 23.0, 90),
    "TP1": (84.0, 20.0, 0), "TP2": (84.0, 24.0, 0), "TP3": (84.0, 28.0, 0),
}
for k, x in enumerate(CX, start=1):
    POS.update({
        "J%d" % (k + 4): (x, 51.0, 0),
        "Q%d" % k: (x + 1.25, 29.8, 90),
        "D%d" % (k + 10): (x - 0.5, 38.3, 90),
        "RD%d" % k: (x + 1.25, 23.0, 90),
        "RL%d" % k: (x + 3.4, 36.2, 90), "DL%d" % k: (x + 3.4, 40.0, 90),
    })

# V24 va en "Media" para el ruteador: el tronco y las derivaciones de potencia ya van trazados (PRE) a 3 y 1 mm
NETCLASS = {"Potencia": (1.5, 0.3, ["VIN_RAW"]),
            "Media": (0.8, 0.2, ["V24"] + ["Q%d" % k for k in range(1, 9)])}
PRE = [
    # entrada: de J1 por el borde izquierdo a la pata 1 del portafusible
    ("VIN_RAW", 1.5, [(3.0, 50.4), (3.0, 45.0), (1.4, 43.4), (1.4, FY), (FX - 3.4, FY), (FX, FY)]),   # las 2 patas de la entrada
    # tronco de +24 V (3 mm, 2 oz): de la pata 2 del portafusible a lo largo de los 8 conectores. KiCad solo une pistas
    # por sus extremos: el tronco se parte en cada derivación
    ("V24", 3.0, [(FX - 3.4, FY + 9.92), (FX, FY + 9.92), (FX, YTR)] + [p for x in CX for p in ((x - 0.5, YTR), (x, YTR))]),
] + [("V24", 1.0, [(x, YTR), (x, 51.0)]) for x in CX] \
  + [("V24", 1.0, [(x - 0.5, 40.3), (x - 0.5, YTR)]) for x in CX]   # pata 1 del conector y cátodo del diodo

SILK = [
    ("+24 0V", 5.0, 45.6, 0.8, "F"),
    *[("Q%d" % (k + 1), x + 1.25, 47.4, 0.9, "F") for k, x in enumerate(CX)],
    ("AP PRO DO8", 44.0, 25.6, 1.4, "F"),
    ("ENTRA", 14.0, 7.6, 0.8, "F"), ("SIGUE", 58.0, 7.6, 0.8, "F"), ("5V", 84.0, 30.6, 0.8, "F"),
    ("AP ELECTRIC  AP PRO DO8  8 x 24V 1.5A protegidas", 44.0, 54.8, 1.0, "B"),
    ("Carga entre las 2 patas de Qn. Red: solo con contactor", 44.0, 52.8, 0.8, "B"),
    ("Dirección: JP1 +1  JP2 +2  (0x20-0x23)", 44.0, 8.0, 0.8, "B"),
]
FLAGS = [("VIN_RAW", 20.32, 20.32), ("GND", 35.56, 20.32), ("V24", 50.8, 20.32), ("3V3", 66.04, 20.32)]
NOTES = [(150.0, 15.0, "AP ELECTRIC · AP PRO DO8: TCA9554 (I2C 0x20-0x23) + 74HCT125 (5 V) + 8 x NCV8406A protegidos.\n"
                       "3V3 y GND llegan por Qwiic desde el programador. La red NO entra a esta placa.")]
TITLE = "AP ELECTRIC · AP PRO DO8 - 8 salidas de 24 V DC protegidas"
SUBTITLES = ["Placa de 2 capas, 2 oz (JLCPCB)", "Bobinas de contactor, relevadores, electroválvulas: 1.5 A por salida"]
COMPANY = "PCB 88 x 56 mm, 2 capas, 2 oz"
COSTURA = 5.0
PAPER = "A3"
OCULTAR_REF = ("J1", "J2", "J4") + tuple("J%d" % k for k in range(5, 13))

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
