"""AP ELECTRIC · AP LIGHT AO4: 4 circuitos de alumbrado con atenuación 0-10 V (1-10 V) y salida de contactor.

Para qué: luminarias de red con driver atenuable (alumbrado público, estacionamientos, naves, oficinas, paneles LED):
- la salida 0-10 V de cada circuito atenúa los drivers (se ponen en paralelo hasta unos 10 mA en total);
- la salida de bobina de cada circuito (24 V DC, 0.5 A) manda el contactor de riel DIN certificado que corta la red
  de esos drivers: con nivel 0 % el circuito queda apagado de verdad, sin consumo en espera.
La red de 127/220 V nunca entra a esta placa: la conmuta el contactor, instalado por un electricista.

Circuito:
- U1 PCA9685 (I2C 0x44-0x47 según JP1/JP2): LED0-3 = 0-10 V, LED4-7 = bobinas. Al encender todo apagado.
- 0-10 V: PWM de 1.5 kHz y 3.3 V -> filtro RC de 2 etapas (10k / 1 uF, rizo menor a 2 mV) -> LM324 con ganancia 3
  (0 a 9.9 V) alimentado a 24 V -> seguidor PNP (MMBT5401) que ABSORBE la corriente que inyectan los drivers 1-10 V,
  y pull-up de 22k que da corriente a los drivers 0-10 V activos. Realimentación tomada en el conector (47 Ohm dentro
  del lazo) y compensación de 100 nF: simulado en ngspice, 4.95 V exactos con 0 a 10 mA y sin sobretiro con 100 m de
  cable. Mínimo: ~1 V con 1 mA, ~1.3 V con 10 mA (el mínimo de un driver 1-10 V es 1 V). Zener de 12 V contra picos.
- Bobinas: 74HCT125 a 5 V -> NCV8406A (lado bajo protegido, 65 V) + diodo SS14 por salida, LED por salida.
- Entrada 24 V por JST VH 2: fusible rápido de 3 A, diodo serie SS34 (polaridad) y supresor SMBJ26A.
- Un JST XH 4 por circuito: 1 = +24 V (bobina), 2 = bobina (-), 3 = 0-10 V, 4 = 0 V (común del 0-10 V).
- No aislado: el 0 V es el GND del CORE (la misma fuente de 24 V). Las entradas 0-10 V de los drivers son SELV.
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import placa  # noqa: E402
import conectores  # noqa: E402

PROJECT = "AP_AO4"
NS = uuid.UUID("c27d5e19-4a8b-4f3c-b1d6-0e9a8f7c6b52")
ROOT_UUID = "f04b3e7a-2c1d-4e59-a8b6-7d3c9e1f2a64"
R06, C06, C08, C12, R12 = ("Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric",
                           "Capacitor_SMD:C_0805_2012Metric", "Capacitor_SMD:C_1206_3216Metric",
                           "Resistor_SMD:R_1206_3216Metric")
QWIIC = "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal"
SJ = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"
SOIC14 = "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm"
SMA = "Diode_SMD:D_SMA"
R, C = "Device:R", "Device:C"
BUS = {"1": "GND", "2": "3V3", "3": "SDA", "4": "SCL", "MP": "GND"}

C_ = [
    ("J1", "QWIIC ENTRADA", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", QWIIC, dict(BUS),
     "Del programador o del módulo anterior"),
    ("J2", "QWIIC SALIDA", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", QWIIC, dict(BUS), "Al siguiente módulo"),
    ("U1", "PCA9685PW", "Driver_LED:PCA9685PW", "Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm",
     {"1": "AD0", "2": "AD1", "3": "3V3", "4": "GND", "5": "GND", "6": "PW1", "7": "PW2", "8": "PW3", "9": "PW4",
      "10": "PC1", "11": "PC2", "12": "PC3", "13": "PC4", "14": "GND", "15": None, "16": None, "17": None, "18": None,
      "19": None, "20": None, "21": None, "22": None, "23": "GND", "24": "GND", "25": "GND", "26": "SCL", "27": "SDA",
      "28": "3V3"}, "PWM de 12 bits por I2C (0x44-0x47): LED0-3 = 0-10 V, LED4-7 = bobinas"),
    ("C1", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U1"),
    ("C2", "10uF", C, C08, {"1": "3V3", "2": "GND"}, "Reserva del 3.3 V (amplitud del PWM = escala del 0-10 V)"),
    ("JP1", "+1", "Jumper:SolderJumper_2_Open", SJ, {"1": "3V3", "2": "AD0"}, "Dirección: cerrado suma 1"),
    ("JP2", "+2", "Jumper:SolderJumper_2_Open", SJ, {"1": "3V3", "2": "AD1"}, "Dirección: cerrado suma 2"),
    ("RA1", "10k", R, R06, {"1": "AD0", "2": "GND"}, "A0 en 0 si JP1 abierto"),
    ("RA2", "10k", R, R06, {"1": "AD1", "2": "GND"}, "A1 en 0 si JP2 abierto"),
    # --- 24 V ---
    ("J3", "24V", conectores.SYM[2], conectores.VH2, {"1": "VIN_RAW", "2": "GND"},
     "Alimentación: 1 = +24 V, 2 = 0 V (la misma fuente que el CORE)"),
    ("F1", "3A", "Device:Fuse", "Fuse:Fuse_1206_3216Metric", {"1": "VIN_RAW", "2": "VF"}, "Fusible rápido"),
    ("D1", "SS34", "Device:D_Schottky", SMA, {"1": "V24", "2": "VF"}, "Polaridad invertida (en serie)"),
    ("D2", "SMBJ26A", "Device:D_TVS", "Diode_SMD:D_SMB", {"1": "V24", "2": "GND"}, "Supresor de picos"),
    ("C3", "10uF 50V", C, C12, {"1": "V24", "2": "GND"}, "Entrada"),
    ("C4", "10uF 50V", C, C12, {"1": "V24", "2": "GND"}, "Entrada"),
    ("U4", "78L05G-AB3-R", "Regulator_Linear:L78L05_SOT89", "Package_TO_SOT_SMD:SOT-89-3",
     {"1": "V5", "2": "GND", "3": "V24"}, "5 V para el 74HCT125"),
    ("C5", "100nF", C, C06, {"1": "V24", "2": "GND"}, "Entrada del 78L05"),
    ("C6", "1uF 25V", C, C06, {"1": "V5", "2": "GND"}, "Salida del 78L05"),
    # --- amplificador 0-10 V ---
    ("U2", "LM324DT", "Amplifier_Operational:LM2902", SOIC14,
     {"1": "OA1", "2": "NI1", "3": "N21", "4": "V24", "5": "N22", "6": "NI2", "7": "OA2", "8": "OA3", "9": "NI3",
      "10": "N23", "11": "GND", "12": "N24", "13": "NI4", "14": "OA4"}, "4 amplificadores (ganancia 3) a 24 V"),
    ("C7", "100nF", C, C06, {"1": "V24", "2": "GND"}, "Desacoplo del LM324"),
    # --- bobinas ---
    ("U3", "74HCT125D", "74xx:74LS125", SOIC14,
     {"1": "GND", "2": "PC1", "3": "GK1", "4": "GND", "5": "PC2", "6": "GK2", "7": "GND",
      "8": "GK3", "9": "PC3", "10": "GND", "11": "GK4", "12": "PC4", "13": "GND", "14": "V5"},
     "Compuertas a 5 V (entradas TTL)"),
    ("C8", "100nF", C, C06, {"1": "V5", "2": "GND"}, "Desacoplo U3"),
    ("TP1", "24V", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "V24"}, "Prueba: 24 V"),
    ("TP2", "GND", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "GND"}, "Prueba: 0 V"),
    ("TP3", "5V", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "V5"}, "Prueba: 5 V"),
]
CX = [16.0, 33.0, 50.0, 67.0]                       # pata 1 del conector de cada circuito
for k, x0 in enumerate(CX, start=1):
    C_ += [
        # 0-10 V
        ("RFA%d" % k, "10k", R, R06, {"1": "PW%d" % k, "2": "N1%d" % k}, "Filtro 1 del circuito %d" % k),
        ("CFA%d" % k, "1uF", C, C06, {"1": "N1%d" % k, "2": "GND"}, "Filtro 1 del circuito %d" % k),
        ("RFB%d" % k, "10k", R, R06, {"1": "N1%d" % k, "2": "N2%d" % k}, "Filtro 2 del circuito %d" % k),
        ("CFB%d" % k, "1uF", C, C06, {"1": "N2%d" % k, "2": "GND"}, "Filtro 2 del circuito %d" % k),
        ("RG%d" % k, "10k", R, R06, {"1": "NI%d" % k, "2": "GND"}, "Ganancia 3: 10k a 0 V" ),
        ("RR%d" % k, "20k", R, R06, {"1": "AO%d" % k, "2": "NI%d" % k}, "Ganancia 3: 20k desde la salida"),
        ("CR%d" % k, "100nF", C, C06, {"1": "OA%d" % k, "2": "NI%d" % k},
         "Compensación: estable con hasta 1 uF de cable (simulado en ngspice)"),
        ("RB%d" % k, "1k", R, R06, {"1": "OA%d" % k, "2": "BQ%d" % k}, "Base del seguidor %d" % k),
        ("QB%d" % k, "MMBT5401", "Transistor_BJT:Q_PNP_BEC", "Package_TO_SOT_SMD:SOT-23",
         {"1": "BQ%d" % k, "2": "AI%d" % k, "3": "GND"},
         "Seguidor PNP: absorbe la corriente que inyectan los drivers 1-10 V (hasta 10 mA)"),
        ("RU%d" % k, "22k", R, R06, {"1": "V24", "2": "AI%d" % k},
         "Pull-up: da corriente a los drivers 0-10 V activos (0.6 mA a 10 V)"),
        ("RS%d" % k, "47", R, R06, {"1": "AI%d" % k, "2": "AO%d" % k}, "Salida 0-10 V %d (dentro del lazo)" % k),
        ("CB%d" % k, "100nF", C, C06, {"1": "AO%d" % k, "2": "GND"}, "Filtro de la salida %d" % k),
        ("DZ%d" % k, "MMSZ5242B 12V", "Device:D_Zener", "Diode_SMD:D_SOD-123", {"1": "AO%d" % k, "2": "GND"},
         "Picos y descargas en la salida 0-10 V %d" % k),
        # bobina
        ("RP%d" % k, "10k", R, R06, {"1": "PC%d" % k, "2": "GND"}, "Bobina %d apagada sin bus" % k),
        ("Q%d" % k, "NCV8406ASTT3G", "Transistor_FET:Q_NMOS_GDS", "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
         {"1": "GK%d" % k, "2": "BOB%d" % k, "3": "GND"}, "Bobina %d: lado bajo protegido" % k),
        ("D%d" % (k + 10), "SS14", "Device:D_Schottky", SMA, {"1": "V24", "2": "BOB%d" % k}, "Diodo de bobina %d" % k),
        ("RL%d" % k, "10k", R, R06, {"1": "V24", "2": "LA%d" % k}, "LED de la bobina %d" % k),
        ("DL%d" % k, "VERDE", "Device:LED", "LED_SMD:LED_0603_1608Metric", {"1": "BOB%d" % k, "2": "LA%d" % k},
         "Circuito %d con alimentación (contactor cerrado)" % k),
        ("J%d" % (k + 3), "CIRCUITO %d" % k, conectores.SYM[4], conectores.XH4,
         {"1": "V24", "2": "BOB%d" % k, "3": "AO%d" % k, "4": "GND"},
         "Circuito %d: 1 = +24 V bobina, 2 = bobina (-), 3 = 0-10 V, 4 = 0 V" % k),
    ]

W, H = 88.0, 56.0
RADIO_ESQUINA = 2.0
HOLES = [(3.5, 3.5), (84.5, 39.5), (84.5, 52.5)]
POS = {
    "J1": (14.0, 3.6, 180), "J2": (58.0, 3.6, 180),
    "U1": (36.0, 7.0, 90), "C1": (28.5, 6.0, 90), "C2": (25.5, 6.0, 90),
    "JP1": (66.0, 6.0, 0), "JP2": (66.0, 9.5, 0), "RA1": (71.0, 6.0, 0), "RA2": (71.0, 9.5, 0),
    "J3": (3.0, 50.4, 0), "F1": (5.0, 43.0, 90), "D1": (5.0, 36.0, 90), "D2": (5.5, 27.5, 90),
    "C3": (2.2, 19.5, 90), "C4": (5.4, 19.5, 90), "U4": (9.0, 14.5, 0), "C5": (9.6, 19.5, 90), "C6": (5.0, 14.0, 90),
    "U2": (45.0, 21.0, 90), "C7": (45.0, 15.0, 0),
    "U3": (70.0, 21.0, 90), "C8": (70.0, 15.0, 0),
    "TP1": (80.0, 14.0, 0), "TP2": (80.0, 18.0, 0), "TP3": (80.0, 22.0, 0),
}
GRID_X = {1: (15.0, 18.4, 21.8), 2: (15.0, 18.4, 21.8), 3: (27.0, 30.4, 33.8), 4: (27.0, 30.4, 33.8)}
GRID_Y = {1: (14.0, 16.0, 18.0, 20.0), 2: (23.5, 25.5, 27.5, 29.5), 3: (14.0, 16.0, 18.0, 20.0), 4: (23.5, 25.5, 27.5, 29.5)}
for k, x0 in enumerate(CX, start=1):
    gx, gy = GRID_X[k], GRID_Y[k]
    POS.update({
        "RFA%d" % k: (gx[0], gy[0], 0), "CFA%d" % k: (gx[1], gy[0], 0), "RFB%d" % k: (gx[2], gy[0], 0),
        "CFB%d" % k: (gx[0], gy[1], 0), "RG%d" % k: (gx[1], gy[1], 0), "RR%d" % k: (gx[2], gy[1], 0),
        "CR%d" % k: (gx[0], gy[2], 0), "RB%d" % k: (gx[1], gy[2], 0), "RU%d" % k: (gx[2], gy[2], 0),
        "QB%d" % k: (gx[1], gy[3] + 0.6, 0), "CB%d" % k: (x0 + 4.4, 45.0, 0),
        "RP%d" % k: (56.0 + 2.6 * k, 29.5, 90),
        "Q%d" % k: (x0 + 3.0, 38.0, 90), "D%d" % (k + 10): (x0 + 9.2, 38.0, 90),
        "RL%d" % k: (x0 + 12.4, 36.2, 90), "DL%d" % k: (x0 + 12.4, 40.0, 90),
        "RS%d" % k: (x0 + 1.2, 45.0, 0), "DZ%d" % k: (x0 + 8.8, 45.0, 0),
        "J%d" % (k + 3): (x0, 51.0, 0),
    })

NETCLASS = {"Potencia": (0.8, 0.25, ["VIN_RAW", "VF", "V24"]),
            "Media": (0.5, 0.2, ["BOB%d" % k for k in range(1, 5)])}
SILK = [
    ("+24 0V", 5.0, 46.0 - 1.0, 0.8, "F"),
    ("AP LIGHT AO4", 36.0, 33.0, 1.4, "F"),
    ("AP ELECTRIC  AP LIGHT AO4  4 circuitos 0-10 V + contactor", 44.0, 54.8, 1.0, "B"),
    ("1 +24  2 BOBINA  3 0-10V  4 0V. Red: solo por contactor", 44.0, 52.8, 0.8, "B"),
    ("Dirección: JP1 +1  JP2 +2  (0x44-0x47)", 66.0, 12.6, 0.8, "B"),
]
for k, x0 in enumerate(CX, start=1):
    SILK.append(("C%d" % k, x0 + 3.75, 47.6, 0.9, "F"))
FLAGS = [("VIN_RAW", 20.32, 20.32), ("GND", 35.56, 20.32), ("V24", 50.8, 20.32), ("3V3", 66.04, 20.32)]
NOTES = [(150.0, 15.0, "AP ELECTRIC · AP LIGHT AO4: PCA9685 (0x44-0x47) -> filtro RC -> LM324 x3 + PNP -> 0-10 V; LED4-7 ->\\n"
                       "74HCT125 -> NCV8406A (bobinas de contactor). La red NO entra a esta placa.")]
TITLE = "AP ELECTRIC · AP LIGHT AO4 - 4 circuitos de alumbrado 0-10 V + contactor"
SUBTITLES = ["Placa de 2 capas, 1 oz (JLCPCB)", "Drivers atenuables 0-10 V / 1-10 V y corte por contactor certificado"]
COMPANY = "PCB 88 x 56 mm, 2 capas"
COSTURA = 5.0
PAPER = "A3"
OCULTAR_REF = ("J1", "J2", "J3", "J4", "J5", "J6", "J7")

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
