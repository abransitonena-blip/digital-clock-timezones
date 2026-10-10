"""AP ELECTRIC · AP LIGHT PWM4: 4 canales de 12-24 V DC atenuables, de 6 A cada uno, aislados del bus (Qwiic).

Para qué: luminarias LED de 12-24 V (reflectores, luminarias de estacionamiento y bodegas, lámparas lineales, tiras
grandes, letras corpóreas), con atenuación de 0 a 100 %; también ventiladores y calefactores de 12-24 V (encendido y
velocidad). Varias PWM4 en el mismo bus: hasta 16 canales de potencia por CORE.

Circuito:
- Lado del bus (Qwiic, 3.3 V del CORE): U1 PCA9685 (16 PWM de 12 bits, I2C). Dirección 0x41 + JP1 (suma 2) + JP2
  (suma 16): 0x41, 0x43, 0x51 o 0x53 (no choca con el INA238 de la base en 0x40 ni con el AI4 en 0x49/0x4A).
  Al encender, todas sus salidas están apagadas.
- Aislamiento: franja de 3.5 mm sin cobre; cada canal cruza por un optoacoplador LTV-217. El 0 V de la fuente de
  potencia NO toca el 0 V del bus: la corriente fuerte nunca puede regresar por el cable Qwiic.
- Lado de potencia: entrada XT60 (hasta 20 A), supresor SMBJ26A; fuente de 12 V (LMR16006) para los drivers y 5 V
  (78L05) para los optos. U2/U3 UCC27524 mueven los MOSFET Q1-Q4 BSC028N06LS3 (60 V, 2.8 mOhm) con 12 V.
- Por canal: fusible mini de auto (hasta 7.5 A), MOSFET de lado bajo, diodo SS34 de rueda libre, LED "activo" y
  JST VH 2 (1 = +V con fusible, 2 = negativo conmutado).
- 4 capas: plano interno de 0 V de potencia (In1) y de +V (In2) solo en el lado de potencia.
- PWM a 500 Hz (los optos responden en unos 30 us): atenuación suave sin parpadeo visible.
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import placa  # noqa: E402
import conectores  # noqa: E402

PROJECT = "AP_PWM4"
NS = uuid.UUID("3f1c9a52-7b4e-4d18-9e2a-6c5d8b7f1a03")
ROOT_UUID = "a8d4e2f1-5c3b-4a97-8e61-2b7f9c0d4e15"
R06, C06, C08, C12, R12 = ("Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric",
                           "Capacitor_SMD:C_0805_2012Metric", "Capacitor_SMD:C_1206_3216Metric",
                           "Resistor_SMD:R_1206_3216Metric")
QWIIC = "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal"
SJ = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"
TDSON = "Package_TO_SOT_SMD:TDSON-8-1"
SMA = "Diode_SMD:D_SMA"
R, C = "Device:R", "Device:C"
BUS = {"1": "GND", "2": "3V3", "3": "SDA", "4": "SCL", "MP": "GND"}

C_ = [
    # --- lado del bus ---
    ("J6", "QWIIC ENTRADA", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", QWIIC, dict(BUS),
     "Del programador o del módulo anterior"),
    ("J7", "QWIIC SALIDA", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", QWIIC, dict(BUS), "Al siguiente módulo"),
    ("U1", "PCA9685PW", "Driver_LED:PCA9685PW", "Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm",
     {"1": "3V3", "2": "AD1", "3": "GND", "4": "GND", "5": "AD4", "6": "PW1", "7": "PW2", "8": "PW3", "9": "PW4",
      "10": None, "11": None, "12": None, "13": None, "14": "GND", "15": None, "16": None, "17": None, "18": None,
      "19": None, "20": None, "21": None, "22": None, "23": "GND", "24": "GND", "25": "GND", "26": "SCL", "27": "SDA",
      "28": "3V3"}, "PWM de 12 bits por I2C (0x41 / 0x43 / 0x51 / 0x53); salidas apagadas al encender"),
    ("C1", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U1"),
    ("C2", "10uF", C, C08, {"1": "3V3", "2": "GND"}, "Reserva del 3.3 V del bus"),
    ("JP1", "+2", "Jumper:SolderJumper_2_Open", SJ, {"1": "3V3", "2": "AD1"}, "Dirección: cerrado suma 2"),
    ("JP2", "+16", "Jumper:SolderJumper_2_Open", SJ, {"1": "3V3", "2": "AD4"}, "Dirección: cerrado suma 16"),
    ("RA1", "10k", R, R06, {"1": "AD1", "2": "GND"}, "A1 en 0 si JP1 abierto"),
    ("RA2", "10k", R, R06, {"1": "AD4", "2": "GND"}, "A4 en 0 si JP2 abierto"),
    # --- entrada de potencia ---
    ("J1", "ENTRADA 12-24V", conectores.SYM_XT60, conectores.XT60, {"1": "PGND", "2": "VIN"},
     "Fuente de las luminarias: XT60, hasta 20 A (+ y - como las marcas del conector)"),
    ("DTV", "SMBJ26A", "Device:D_TVS", "Diode_SMD:D_SMB", {"1": "VIN", "2": "PGND"}, "Supresor de picos"),
    ("CI1", "10uF 50V", C, C12, {"1": "VIN", "2": "PGND"}, "Desacoplo de la entrada"),
    ("CI2", "10uF 50V", C, C12, {"1": "VIN", "2": "PGND"}, "Desacoplo de la entrada"),
    # --- 12 V para los drivers ---
    ("U5", "LMR16006XDDC", "Regulator_Switching:LMR16006YQ", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "BST", "2": "PGND", "3": "FB", "4": "VIN", "5": "VIN", "6": "SW"}, "Buck 60 V a 12 V para los drivers"),
    ("L1", "47uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR4030S", {"1": "V12", "2": "SW"}, "Bobina del buck"),
    ("D9", "SS210", "Device:D_Schottky", SMA, {"1": "SW", "2": "PGND"}, "Rueda libre del buck"),
    ("C5", "100nF", C, C06, {"1": "BST", "2": "SW"}, "Bootstrap"),
    ("C6", "10uF 50V", C, C12, {"1": "VIN", "2": "PGND"}, "Entrada del buck"),
    ("C7", "22uF 25V", C, C12, {"1": "V12", "2": "PGND"}, "Salida 12 V"),
    ("RB1", "150k", R, R06, {"1": "V12", "2": "FB"}, "Divisor: 0.765 V x 16 = 12.2 V"),
    ("RB2", "10k", R, R06, {"1": "FB", "2": "PGND"}, "Divisor"),
    # --- 5 V para los optoacopladores ---
    ("U6", "78L05G-AB3-R", "Regulator_Linear:L78L05_SOT89", "Package_TO_SOT_SMD:SOT-89-3",
     {"1": "V5", "2": "PGND", "3": "VIN"}, "5 V para el lado de salida de los optos"),
    ("CV1", "100nF", C, C06, {"1": "VIN", "2": "PGND"}, "Entrada del 78L05"),
    ("CV2", "1uF 25V", C, C06, {"1": "V5", "2": "PGND"}, "Salida del 78L05"),
    # --- drivers de compuerta ---
    ("U2", "UCC27524D", "Driver_FET:UCC27524D", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "V12", "2": "IN1", "3": "PGND", "4": "IN2", "5": "GO2", "6": "V12", "7": "GO1", "8": "V12"}, "Driver 1-2"),
    ("U3", "UCC27524D", "Driver_FET:UCC27524D", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "V12", "2": "IN3", "3": "PGND", "4": "IN4", "5": "GO4", "6": "V12", "7": "GO3", "8": "V12"}, "Driver 3-4"),
    ("CU2", "1uF 25V", C, C06, {"1": "V12", "2": "PGND"}, "Desacoplo driver 1-2"),
    ("CU3", "1uF 25V", C, C06, {"1": "V12", "2": "PGND"}, "Desacoplo driver 3-4"),
    ("TP1", "VIN", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "VIN"}, "Prueba: entrada"),
    ("TP2", "12V", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "V12"}, "Prueba: 12 V"),
    ("TP3", "5V", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "V5"}, "Prueba: 5 V"),
    ("TP4", "0V", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "PGND"}, "Prueba: 0 V de potencia"),
]
FX = [25.0, 40.3, 55.6, 70.9]                         # x de la pata 1 de cada portafusible
for k, fx in enumerate(FX, start=1):
    C_ += [
        ("RO%d" % k, "330", R, R06, {"1": "PW%d" % k, "2": "LA%d" % k}, "LED del opto %d (unos 6 mA)" % k),
        ("OK%d" % k, "LTV-217-B", "Isolator:PC817", "Package_SO:SOP-4_4.4x2.6mm_P1.27mm",
         {"1": "LA%d" % k, "2": "GND", "3": "IN%d" % k, "4": "V5"}, "Canal %d aislado (seguidor de emisor)" % k),
        ("RE%d" % k, "2.2k", R, R06, {"1": "IN%d" % k, "2": "PGND"}, "Canal %d apagado sin señal" % k),
        ("F%d" % k, "MINI 7.5A", "Device:Fuse", "Fuse:Fuseholder_Blade_Mini_Keystone_3568", {"1": "VIN", "2": "OUT%d" % k},
         "Fusible del canal %d (mini de auto, 32 V, hasta 7.5 A)" % k),
        ("Q%d" % k, "BSC028N06LS3", "Transistor_FET:BSC028N06LS3", TDSON,
         {"1": "PGND", "2": "PGND", "3": "PGND", "4": "G%d" % k, "5": "CH%d" % k}, "MOSFET del canal %d (60 V, 2.8 mOhm)" % k),
        ("RG%d" % k, "4.7", R, R06, {"1": "GO%d" % k, "2": "G%d" % k}, "Compuerta del canal %d" % k),
        ("RP%d" % k, "10k", R, R06, {"1": "G%d" % k, "2": "PGND"}, "Canal %d apagado sin driver" % k),
        ("D%d" % k, "SS34", "Device:D_Schottky", SMA, {"1": "OUT%d" % k, "2": "CH%d" % k},
         "Rueda libre del canal %d (cables largos, ventiladores)" % k),
        ("RL%d" % k, "10k", R, "Resistor_SMD:R_0805_2012Metric", {"1": "OUT%d" % k, "2": "LD%d" % k}, "LED activo del canal %d" % k),
        ("DL%d" % k, "VERDE", "Device:LED", "LED_SMD:LED_0603_1608Metric", {"1": "CH%d" % k, "2": "LD%d" % k},
         "Canal %d encendido" % k),
        ("J%d" % (k + 1), "CANAL %d" % k, conectores.SYM[2], conectores.VH2, {"1": "OUT%d" % k, "2": "CH%d" % k},
         "Luminaria %d: 1 = +V (con fusible), 2 = negativo conmutado (JST VH)" % k),
    ]

W, H = 88.0, 56.0
RADIO_ESQUINA = 2.0
CAPAS = 4
HOLES = [(3.5, 3.5), (84.5, 39.5), (84.5, 52.5)]
YF, YT = 24.0, 50.4
XJ, YJ = 17.0, 44.0
POS = {
    "J6": (14.0, 3.6, 180), "J7": (58.0, 3.6, 180),
    "U1": (40.0, 6.2, 90), "C1": (32.5, 5.5, 90), "C2": (29.5, 5.5, 90),
    "JP1": (66.0, 6.0, 0), "JP2": (66.0, 9.5, 0), "RA1": (71.0, 6.0, 0), "RA2": (71.0, 9.5, 0),
    "J1": (XJ, YJ, 90), "DTV": (6.5, 52.5, 0), "CI1": (14.0, 52.5, 0), "CI2": (14.0, 50.0, 0),
    "U5": (11.0, 26.0, 0), "L1": (11.0, 21.0, 0), "C5": (7.8, 24.8, 90), "D9": (15.2, 22.0, 90),
    "C6": (15.2, 28.0, 90), "C7": (4.6, 27.4, 180), "RB1": (5.0, 29.5, 0), "RB2": (9.6, 29.4, 0),
    "U6": (3.5, 21.0, 0), "CV1": (6.6, 21.5, 90), "CV2": (3.5, 24.6, 0),
    "U2": (FX[0] + 6.0, 25.5, 0), "U3": (FX[2] + 6.0, 25.5, 0),
    "CU2": (FX[0] + 6.2, 29.6, 0), "CU3": (FX[2] + 6.2, 29.6, 0),
    "TP1": (FX[1] + 6.2, 23.0, 0), "TP2": (FX[1] + 6.2, 27.0, 0), "TP3": (FX[3] + 6.2, 23.0, 0), "TP4": (FX[3] + 6.2, 27.0, 0),
}
for k, fx in enumerate(FX, start=1):
    POS.update({
        "RO%d" % k: (fx + 2.6, 11.7, 90), "OK%d" % k: (fx + 6.0, 15.25, 270), "RE%d" % k: (fx + 2.8, 19.4, 90),
        "F%d" % k: (fx, YF, 270), "J%d" % (k + 1): (fx - 1.7, YT, 0),
        "Q%d" % k: (fx + 7.2, 41.0, 270), "D%d" % k: (fx + 2.5, 41.0, 270),
        "RG%d" % k: (fx + 3.6, 31.6, 0), "RP%d" % k: (fx + 7.4, 31.6, 0),
        "RL%d" % k: (fx + 4.0, 33.8, 0), "DL%d" % k: (fx + 7.7, 33.8, 180),
    })

CAMPO_POT = ["VIN", "PGND"] + ["%s%d" % (n, k) for n in ("OUT", "CH") for k in range(1, 5)]
CAMPO = ["V12", "V5", "SW", "BST", "FB"] + ["%s%d" % (n, k) for n in ("IN", "GO", "G", "LD") for k in range(1, 5)]
NETCLASS = {"CampoPot": (0.8, 0.3, CAMPO_POT), "Campo": (0.4, 0.2, CAMPO)}
CAMPO_AREA = [(0.3, 17.0), (87.7, 17.0), (87.7, 55.7), (0.3, 55.7)]
PLANOS = [("PGND", "In1", CAMPO_AREA), ("VIN", "In2", CAMPO_AREA)]
POWER_ZONES = []
PREVIAS = []
for k, fx in enumerate(FX, start=1):
    POWER_ZONES += [
        # + con fusible: de la pata 2 del portafusible al conector, con una lengüeta al cátodo del diodo
        ("OUT%d" % k, [(fx - 4.6, 32.4), (fx + 0.3, 32.4), (fx + 0.3, 36.6), (fx + 3.1, 36.6), (fx + 3.1, 40.9),
                       (fx + 0.3, 40.9), (fx + 0.3, 53.6), (fx - 4.6, 53.6)]),
        # negativo conmutado: drenador del MOSFET, ánodo del diodo y pata 2 del conector
        ("CH%d" % k, [(fx + 3.7, 39.6), (fx + 10.2, 39.6), (fx + 10.2, 53.6), (fx + 0.9, 53.6), (fx + 0.9, 41.6),
                      (fx + 3.7, 41.6)]),
    ]
    PREVIAS += [("PGND", fx + 6.6, 36.1), ("PGND", fx + 7.8, 36.1), ("PGND", fx + 9.0, 36.1),
                ("PGND", fx + 9.0, 37.3)]
# vías a los planos internos para las piezas SMD de la entrada (el ruteador no siempre las pone)
PRE = [("VIN", 0.6, [(12.53, 50.0), (10.7, 51.25), (12.53, 52.5)]), ("VIN", 0.6, [(4.35, 52.5), (4.35, 49.9)]),
       ("VIN", 0.6, [(15.2, 29.47), (15.2, 31.4)]), ("VIN", 0.4, [(6.6, 22.28), (6.6, 23.6)]),
       ("VIN", 0.4, [(1.55, 22.5), (1.55, 24.1)]),
       ("PGND", 0.3, [(9.86, 26.0), (9.0, 26.0), (8.4, 27.0)])]          # 0 V del LMR16006 a los planos
PREVIAS += [("VIN", 10.7, 51.25), ("VIN", 4.35, 49.9), ("VIN", 15.2, 31.4), ("VIN", 6.6, 23.6), ("PGND", 8.4, 27.0),
            ("VIN", 1.55, 24.1)]
for fx in FX:                                         # LED "activo": del cátodo al negativo conmutado, por fuera del 0 V
    PRE.append(("CH%d" % (FX.index(fx) + 1), 0.4, [(fx + 8.49, 33.8), (fx + 10.0, 33.8), (fx + 10.0, 40.2)]))
KEEPOUT_NETS = tuple("%s%d" % (n, k) for n in ("OUT", "CH") for k in range(1, 5))
ZONAS_FINALES = [("PGND", CAMPO_AREA), ("PGND", CAMPO_AREA, "B")]
SIN_COBRE = [[(0.3, 13.5), (87.7, 13.5), (87.7, 17.0), (0.3, 17.0)]]     # franja de aislamiento de 3.5 mm
DRU = """(rule "aislamiento"
  (condition "(A.NetClass == 'Campo' || A.NetClass == 'CampoPot') && B.NetClass != 'Campo' && B.NetClass != 'CampoPot' && !A.memberOfFootprint('OK*') && !B.memberOfFootprint('OK*') && !A.memberOfFootprint('J1') && !B.memberOfFootprint('J1')")
  (constraint clearance (min 2.5mm)))
"""
SILK = [
    ("ENTRADA 12-24V", 9.0, 46.6, 0.9, "F"), ("XT60 20A", 9.0, 48.2, 0.9, "F"),
    ("AP LIGHT PWM4", 50.0, 54.8, 1.0, "B"),
    ("AISLAMIENTO 3.5 mm", 44.0, 15.25, 0.8, "B"),
    ("12-24 V DC. 6 A por canal (fusible mini 7.5 A), 20 A en total", 44.0, 52.8, 0.8, "B"),
    ("Dirección 0x41: JP1 +2  JP2 +16", 66.0, 12.6, 0.8, "B"),
]
for k, fx in enumerate(FX, start=1):
    SILK += [("L%d+" % k, fx - 1.7, 45.0, 0.9, "F"), ("-", fx + 2.26, 45.0, 0.9, "F")]
FLAGS = [("GND", 20.32, 20.32), ("3V3", 35.56, 20.32), ("VIN", 50.8, 20.32), ("PGND", 66.04, 20.32), ("V12", 81.28, 20.32)]
NOTES = [(150.0, 15.0, "AP ELECTRIC · AP LIGHT PWM4: PCA9685 (0x41/0x43/0x51/0x53) -> optos LTV-217 -> UCC27524 ->\\n"
                       "BSC028N06LS3. Lado del bus (GND, 3V3) aislado del lado de potencia (PGND, VIN). PWM a 500 Hz.")]
TITLE = "AP ELECTRIC · AP LIGHT PWM4 - 4 canales de 6 A atenuables, aislados"
SUBTITLES = ["Placa de 4 capas, 2 oz exteriores (JLCPCB)", "Luminarias LED de 12-24 V, reflectores, ventiladores: 0-100 %"]
COMPANY = "PCB 88 x 56 mm, 4 capas"
COSTURA = 5.0
COSTURA_REDES = ("GND", "PGND")
PAPER = "A3"
OCULTAR_REF = ("J1", "J2", "J3", "J4", "J5", "J6", "J7")

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
