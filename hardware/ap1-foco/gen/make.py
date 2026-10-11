"""AP ELECTRIC · AP FOCO: cabezal de 2 focos de corriente constante que se adapta al foco que le conectas.

Para qué: focos y LED de potencia (dicroicos LED, reflectores de COB, downlights, módulos de letrero, lupas) sin
resistencias ni drivers sueltos. Cada foco dice cuánta corriente quiere con una resistencia en su conector (el mismo
principio que "LEDset" / "Rset" de la industria) y el cabezal la aplica sola; sin resistencia, usa la corriente que
elijas en la app. El cabezal mide la corriente real de cada foco y avisa si se abre o se desconecta.

Circuito por canal (el mismo de la BASE, ya probado):
- AL8860 (buck de corriente constante, 40 V, hasta 1 A) con resistencia de 0.1 Ohm: 1 A al 100 %.
- Atenuación por la pata CTRL con el PWM del PCA9685 (1 kHz), con resistencia de 2.2k a 0 V: apagado sin bus.
- INA238 sobre la resistencia de corriente: mide la corriente del foco (±1.6 A, resolución de 50 uA). Su entrada VBUS
  (independiente, 0-85 V) lee la resistencia de identificación del foco: 10k a 3.3 V y la Rset del foco a 0 V.
- Conector JST XH 4 por foco: 1 = LED +, 2 = LED -, 3 = ID (Rset), 4 = 0 V. Las salidas LED son flotantes.
Entrada: 12-24 V DC por JST VH 2, fusible de 3 A, diodo serie SS34, supresor SMBJ26A (limita a 42 V).
I2C: PCA9685 0x60 (JP1 -> 0x61), INA238 0x4C / 0x4D (JP2/JP3 -> 0x4E / 0x4F): dos cabezales por sistema.
La alimentación es DC de una fuente certificada: la misma placa sirve en instalaciones de 127 V, 220 V o 480 V
(se cambia la fuente, no el cabezal). La red no entra a esta placa.
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import placa  # noqa: E402
import conectores  # noqa: E402

PROJECT = "AP_FOCO"
NS = uuid.UUID("8b3d6f2a-9e41-4c7d-b5a8-1f2e3d4c5b6a")
ROOT_UUID = "2c4e6a8b-0d1f-4a3c-8e5b-7d9f1a3c5e7b"
R06, C06, C08, C12, R12 = ("Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric",
                           "Capacitor_SMD:C_0805_2012Metric", "Capacitor_SMD:C_1206_3216Metric",
                           "Resistor_SMD:R_1206_3216Metric")
QWIIC = "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal"
SJ = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"
SJ3 = "Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm"
SMA = "Diode_SMD:D_SMA"
R, C = "Device:R", "Device:C"
BUS = {"1": "GND", "2": "3V3", "3": "SDA", "4": "SCL", "MP": "GND"}

C_ = [
    ("J1", "QWIIC ENTRADA", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", QWIIC, dict(BUS),
     "Del CORE o del módulo anterior"),
    ("J2", "QWIIC SALIDA", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", QWIIC, dict(BUS), "Al siguiente módulo"),
    ("U1", "PCA9685PW", "Driver_LED:PCA9685PW", "Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm",
     {"1": "AD0", "2": "GND", "3": "GND", "4": "GND", "5": "GND", "6": "CT1", "7": "CT2", "8": None, "9": None,
      "10": None, "11": None, "12": None, "13": None, "14": "GND", "15": None, "16": None, "17": None, "18": None,
      "19": None, "20": None, "21": None, "22": None, "23": "GND", "24": "3V3", "25": "GND", "26": "SCL", "27": "SDA",
      "28": "3V3"}, "PWM del CTRL de los dos focos (0x60; JP1 -> 0x61)"),
    ("C1", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U1"),
    ("C2", "10uF", C, C08, {"1": "3V3", "2": "GND"}, "Reserva del 3.3 V"),
    ("JP1", "+1", "Jumper:SolderJumper_2_Open", SJ, {"1": "3V3", "2": "AD0"}, "Segundo cabezal: cerrar"),
    ("RA1", "10k", R, R06, {"1": "AD0", "2": "GND"}, "A0 en 0 si JP1 abierto"),
    # --- entrada ---
    ("J3", "12-24V", conectores.SYM[2], conectores.VH2, {"1": "VIN_RAW", "2": "GND"},
     "Alimentación de los focos: 1 = +12-24 V, 2 = 0 V (fuente certificada)"),
    ("F1", "3A", "Device:Fuse", "Fuse:Fuse_1206_3216Metric", {"1": "VIN_RAW", "2": "VF"}, "Fusible rápido"),
    ("D1", "SS34", "Device:D_Schottky", SMA, {"1": "VCC", "2": "VF"}, "Polaridad invertida (en serie)"),
    ("D2", "SMBJ26A", "Device:D_TVS", "Diode_SMD:D_SMB", {"1": "VCC", "2": "GND"},
     "Supresor: limita a 42 V, lo máximo que aguantan los AL8860"),
    ("C3", "10uF 50V", C, C12, {"1": "VCC", "2": "GND"}, "Entrada"),
    ("TP1", "VCC", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "VCC"}, "Prueba: entrada"),
    ("TP2", "GND", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "GND"}, "Prueba: 0 V"),
]
for k in (1, 2):
    u, l, d, rs, c, rc = ("U%d" % (k + 3), "L%d" % k, "D%d" % (k + 2), "RSC%d" % k, "C%d" % (k + 10), "RC%d" % k)
    C_ += [
        (u, "AL8860MP", "Driver_LED:AL8860MP", "Package_SO:MSOP-8-1EP_3x3mm_P0.65mm_EP1.5x1.8mm",
         {"1": "LEDA%d" % k, "2": "GND", "3": "GND", "4": "CT%d" % k, "5": "SWC%d" % k, "6": "SWC%d" % k, "7": None,
          "8": "VCC", "9": "GND"}, "Driver de corriente constante %d (40 V, 1 A)" % k),
        (rs, "0R1", "Device:R_Shunt", "LetreroLab:R_1206_Kelvin_NetTie",
         {"1": "VCC", "2": "SP%d" % k, "3": "SN%d" % k, "4": "LEDA%d" % k},
         "Corriente máxima: 0.1 V / 0.1 Ohm = 1 A; sensado Kelvin hacia el INA238"),
        (l, "47uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR6045S", {"1": "LEDK%d" % k, "2": "SWC%d" % k},
         "Bobina %d (Isat > 1.5 A)" % k),
        (d, "SS34", "Device:D_Schottky", SMA, {"1": "VCC", "2": "SWC%d" % k}, "Rueda libre %d" % k),
        (c, "4.7uF 50V", C, C12, {"1": "VCC", "2": "GND"}, "Entrada del canal %d" % k),
        (rc, "2.2k", R, R06, {"1": "CT%d" % k, "2": "GND"}, "Apagado sin bus (CTRL < 0.2 V)"),
        ("U%d" % (k + 1), "INA238", "Sensor_Energy:INA238", "Package_SO:VSSOP-10_3x3mm_P0.5mm",
         {"1": "SCL", "2": "IA%d" % k, "3": None, "4": "SDA", "5": "SCL", "6": "3V3", "7": "GND", "8": "ID%d" % k,
          "9": "SN%d" % k, "10": "SP%d" % k}, "Corriente del foco %d y su resistencia de identificación" % k),
        ("C%d" % (k + 12), "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo del INA238 %d" % k),
        ("JP%d" % (k + 1), "DIR", "Jumper:SolderJumper_3_Bridged12", SJ3,
         {"1": "GND" if k == 1 else "3V3", "2": "IA%d" % k, "3": "SDA" if k == 1 else "SCL"},
         "Dirección del INA238 %d: 0x4%s (cortar 1-2 y unir 2-3: 0x4%s)" % (k, "C" if k == 1 else "D", "E" if k == 1 else "F")),
        ("RID%d" % k, "10k 1%", R, R06, {"1": "3V3", "2": "ID%d" % k}, "Lectura de la Rset del foco %d" % k),
        ("CID%d" % k, "100nF", C, C06, {"1": "ID%d" % k, "2": "GND"}, "Filtro de la identificación %d" % k),
        ("J%d" % (k + 3), "FOCO %d" % k, conectores.SYM[4], conectores.XH4,
         {"1": "LEDA%d" % k, "2": "LEDK%d" % k, "3": "ID%d" % k, "4": "GND"},
         "Foco %d: 1 = LED +, 2 = LED -, 3 = ID (Rset a 0 V), 4 = 0 V" % k),
    ]

W, H = 60.0, 56.0
RADIO_ESQUINA = 2.0
HOLES = [(3.5, 3.5), (56.5, 3.5), (56.5, 38.5)]
DY = 12.5                                         # el canal 2 está 12.5 mm abajo, igual que en la BASE
POS = {
    "J1": (22.0, 3.6, 180), "J2": (44.0, 3.6, 180),
    "U1": (36.0, 12.0, 90), "C1": (29.0, 9.5, 90), "C2": (29.0, 13.5, 90), "JP1": (46.0, 9.5, 0), "RA1": (46.0, 13.0, 0),
    "J3": (42.0, 50.4, 0), "F1": (50.0, 44.0, 90), "D1": (50.0, 36.0, 90), "D2": (55.0, 47.0, 90), "C3": (45.0, 36.0, 90),
    "TP1": (52.0, 29.0, 0), "TP2": (52.0, 25.0, 0),
}
for k in (1, 2):
    dy = (k - 1) * DY
    POS.update({
        "U%d" % (k + 3): (5.0, 17.5 + dy, 0), "L%d" % k: (12.8, 17.6 + dy, 0), "D%d" % (k + 2): (12.3, 23.0 + dy, 0),
        "RSC%d" % k: (4.5, 21.0 + dy, 0), "C%d" % (k + 10): (4.5, 24.0 + dy, 0), "RC%d" % k: (4.5, 26.4 + dy, 0),
        "U%d" % (k + 1): (24.0, 20.5 + dy, 0), "C%d" % (k + 12): (24.0, 24.2 + dy, 0),
        "JP%d" % (k + 1): (29.6, 20.5 + dy, 90), "RID%d" % k: (19.6, 25.0 + dy, 90), "CID%d" % k: (21.4, 25.0 + dy, 90),
        "J%d" % (k + 3): (8.0 + (k - 1) * 18.0, 51.0, 0),
    })

NETCLASS = {"Potencia": (0.8, 0.25, ["VIN_RAW", "VF"]),           # VCC en Media como en la BASE: entra a la pata 8 del AL8860
            "Media": (0.6, 0.2, ["VCC", "SWC1", "SWC2", "LEDA1", "LEDK1", "LEDA2", "LEDK2"])}   # 0.6 mm: 2 A (2 focos)
# conmutación y CTRL de los AL8860: las mismas rutas de la BASE (canal 2 = canal 1 + 12.5 mm)
PRE = []
PREVIAS = []
for k in (1, 2):
    dy = (k - 1) * DY
    PRE += [
        ("SWC%d" % k, 0.6, [(x, y + dy) for x, y in [(7.11, 18.47), (7.11, 17.88), (8.06, 17.88), (8.69, 17.25),
                                                     (8.69, 15.16), (9.63, 14.22), (11.67, 14.22), (15.05, 17.60),
                                                     (14.30, 18.35), (14.30, 23.00)]]),
        ("CT%d" % k, 0.3, [(1.3, 19.45 + dy), (1.3, 18.47 + dy), (2.89, 18.47 + dy)]),
        ("CT%d" % k, 0.3, [(1.3, 19.45 + dy), (1.3, 26.4 + dy), (3.675, 26.4 + dy)]),
    ]
    # CTRL: el router lo lleva al PCA9685 desde el final de esta pista (sin vía fija)
SILK = [
    ("AP FOCO", 36.0, 30.0, 1.6, "F"),
    ("+12-24V 0V", 52.0, 45.8, 0.8, "F"),
    ("+ - ID 0V", 11.75, 46.6, 0.8, "F"), ("+ - ID 0V", 29.75, 46.6, 0.8, "F"),
    ("FOCO 1", 11.75, 55.0, 0.8, "F"), ("FOCO 2", 29.75, 55.0, 0.8, "F"),
    ("AP ELECTRIC  AP FOCO  2 x 1 A corriente constante", 36.0, 54.8, 1.0, "B"),
    ("Salidas LED flotantes: no unir a tierra. ID: Rset a 0 V", 36.0, 52.8, 0.8, "B"),
    ("JP1: 0x61   JP2/JP3 2-3: 0x4E / 0x4F", 36.0, 50.8, 0.8, "B"),
]
FLAGS = [("VIN_RAW", 20.32, 20.32), ("GND", 35.56, 20.32), ("VCC", 50.8, 20.32), ("3V3", 66.04, 20.32)]
NOTES = [(150.0, 15.0, "AP ELECTRIC · AP FOCO: PCA9685 0x60 (CTRL), INA238 0x4C/0x4D (corriente + ID), 2 x AL8860.\n"
                       "Rset del foco: I [mA] = 5000 / R [kOhm] (5 k = 1 A, 10 k = 500 mA, 14.3 k = 350 mA).")]
TITLE = "AP ELECTRIC · AP FOCO - 2 focos de corriente constante adaptable"
SUBTITLES = ["Placa de 2 capas, 1 oz (JLCPCB)", "La corriente la fija la resistencia del foco o la app"]
COMPANY = "PCB 60 x 56 mm, 2 capas"
COSTURA = 5.0
PAPER = "A3"
OCULTAR_REF = ("J1", "J2", "J3", "J4", "J5")

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
