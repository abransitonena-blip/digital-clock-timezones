"""AP ELECTRIC · AP SIGN DIST 4: distribución DC protegida de 4 ramas para letreros (12-24 V DC).

Para qué: repartir la fuente de los LED de un letrero (letras corpóreas, cajas de luz, neón LED) en 4 ramas, cada
una con su fusible, y saber desde la app cuál rama falla.

- Entrada 12-24 V DC (máximo 26 V), hasta 10 A en total (tronco de 2.5 mm en 2 oz). Portafusibles mini de auto (Keystone 3568) por rama:
  fusible de hasta 7.5 A por rama. Los portafusibles mini son de 32 V: solo baja tensión.
- LED verde por rama: hay voltaje en la salida. LED rojo por rama: fusible abierto (se enciende cuando el fusible
  se abre y la carga sigue conectada).
- Aviso al CORE por el bus (Qwiic): optoacoplador por rama y uno de "fuente presente" -> TCA9554 (I2C 0x24-0x27,
  el mismo rango que AP INPUT: E1-E4 = ramas con voltaje, E5 = fuente presente).
- La fuente de las cargas (VIN, 0V) queda AISLADA del bus de control: franja de 3.5 mm sin cobre y optoacopladores.
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import placa  # noqa: E402
import conectores  # noqa: E402

PROJECT = "AP_Dist4"
NS = uuid.UUID("61d5e27d-4e2f-4644-8f42-21416861ad6d")
ROOT_UUID = "837d2a4a-1b19-4f86-ae14-24aad2f3368c"
R06, C06, R12 = "Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric", "Resistor_SMD:R_1206_3216Metric"
QWIIC = "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal"
SJ = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"
R, C = "Device:R", "Device:C"
BUS = {"1": "GND", "2": "3V3", "3": "SDA", "4": "SCL", "MP": "GND"}

C_ = [
    ("J6", "QWIIC ENTRADA", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", QWIIC, dict(BUS),
     "Del programador o del módulo anterior"),
    ("J7", "QWIIC SALIDA", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", QWIIC, dict(BUS), "Al siguiente módulo"),
    ("U1", "TCA9554PWR", "Interface_Expansion:TCA9554PW", "Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
     {"1": "A0", "2": "A1", "3": "3V3", "4": "SEN1", "5": "SEN2", "6": "SEN3", "7": "SEN4", "8": "GND",
      "9": "SENV", "10": "PFIJO", "11": "PFIJO", "12": "PFIJO", "13": None, "14": "SCL", "15": "SDA", "16": "3V3"},
     "Expansor I2C 0x24-0x27: P0-P3 ramas, P4 fuente; P5-P7 fijas (inactivas)"),
    ("C1", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U1"),
    ("RF", "10k", R, R06, {"1": "3V3", "2": "PFIJO"}, "P5-P7 en alto (sin uso: se leen inactivas)"),
    ("JP1", "A0", "Jumper:SolderJumper_2_Open", SJ, {"1": "3V3", "2": "A0"}, "Dirección: cerrado suma 1"),
    ("JP2", "A1", "Jumper:SolderJumper_2_Open", SJ, {"1": "3V3", "2": "A1"}, "Dirección: cerrado suma 2"),
    ("RA1", "10k", R, R06, {"1": "A0", "2": "GND"}, "A0 en 0 si JP1 abierto"),
    ("RA2", "10k", R, R06, {"1": "A1", "2": "GND"}, "A1 en 0 si JP2 abierto"),
    ("J1", "ENTRADA 12-24V", conectores.SYM_XT60, conectores.XT60, {"1": "LGND", "2": "VIN"},
     "Fuente de los LED: XT60, + y - como las marcas del conector (hasta 10 A)"),
    # fuente presente
    ("RIV", "4.7k", R, R12, {"1": "VIN", "2": "IAV"}, "Aviso de fuente presente"),
    ("RPV", "1k", R, R06, {"1": "IAV", "2": "LGND"}, "Umbral de unos 6 V"),
    ("OKV", "LTV-217-B", "Isolator:PC817", "Package_SO:SOP-4_4.4x2.6mm_P1.27mm",
     {"1": "IAV", "2": "LGND", "3": "GND", "4": "SENV"}, "Fuente presente (aislado)"),
    ("RUV", "10k", R, R06, {"1": "3V3", "2": "SENV"}, "Pull-up"),
]
FX = [25.2, 41.2, 57.2, 73.2]                     # x de la pata 1 de cada portafusible
for k, fx in enumerate(FX, start=1):
    ox = fx + 6.0
    C_ += [
        ("F%d" % k, "MINI 5A", "Device:Fuse", "Fuse:Fuseholder_Blade_Mini_Keystone_3568", {"1": "VIN", "2": "OUT%d" % k},
         "Fusible de la rama %d (mini de auto, 32 V, hasta 7.5 A)" % k),
        ("J%d" % (k + 1), "RAMA %d" % k, conectores.SYM[2], conectores.VH2,
         {"1": "OUT%d" % k, "2": "LGND"}, "Salida de la rama %d: + y 0 V" % k),
        ("RR%d" % k, "4.7k", R, R12, {"1": "VIN", "2": "RA%d" % k}, "LED rojo de la rama %d" % k),
        ("DR%d" % k, "ROJO", "Device:LED", "LED_SMD:LED_0603_1608Metric", {"1": "OUT%d" % k, "2": "RA%d" % k},
         "Fusible %d abierto" % k),
        ("RG%d" % k, "4.7k", R, R12, {"1": "OUT%d" % k, "2": "GA%d" % k}, "LED verde de la rama %d" % k),
        ("DG%d" % k, "VERDE", "Device:LED", "LED_SMD:LED_0603_1608Metric", {"1": "LGND", "2": "GA%d" % k},
         "Rama %d con voltaje" % k),
        ("RI%d" % k, "4.7k", R, R12, {"1": "OUT%d" % k, "2": "IA%d" % k}, "Aviso de la rama %d" % k),
        ("RP%d" % k, "1k", R, R06, {"1": "IA%d" % k, "2": "LGND"}, "Umbral de unos 6 V"),
        ("OK%d" % k, "LTV-217-B", "Isolator:PC817", "Package_SO:SOP-4_4.4x2.6mm_P1.27mm",
         {"1": "IA%d" % k, "2": "LGND", "3": "GND", "4": "SEN%d" % k}, "Rama %d con voltaje (aislado)" % k),
        ("RU%d" % k, "10k", R, R06, {"1": "3V3", "2": "SEN%d" % k}, "Pull-up"),
    ]

W, H = 88.0, 56.0
RADIO_ESQUINA = 2.0
HOLES = [(3.5, 3.5), (84.5, 39.5), (84.5, 52.5)]
YT = 50.4                                         # fila de los conectores VH de las ramas
XJ, YJ = 17.0, 44.0                               # XT60 de entrada: pata 1; el enchufe sale por la izquierda
YF = 24.0                                          # fila de las patas de entrada de los portafusibles
POS = {
    "J6": (14.0, 3.6, 180), "J7": (58.0, 3.6, 180),
    "U1": (36.0, 6.5, 0), "C1": (36.0, 11.0, 0), "RF": (44.0, 4.0, 90),
    "JP1": (66.0, 6.0, 0), "JP2": (66.0, 9.5, 0), "RA1": (71.0, 6.0, 0), "RA2": (71.0, 9.5, 0),
    "J1": (XJ, YJ, 90),
    "OKV": (10.0, 15.25, 90), "RIV": (8.5, 20.9, 0), "RPV": (13.0, 20.9, 0), "RUV": (10.0, 8.8, 90),
}
for k, fx in enumerate(FX, start=1):
    ox = fx + 6.0
    POS.update({
        "F%d" % k: (fx, YF, 270), "J%d" % (k + 1): (fx - 1.7, YT, 0),
        "RR%d" % k: (fx + 4.5, 30.0, 90), "DR%d" % k: (fx + 4.5, 34.6, 90),
        "RG%d" % k: (fx + 7.5, 30.0, 90), "DG%d" % k: (fx + 7.5, 34.6, 90),
        "OK%d" % k: (ox, 15.25, 90), "RI%d" % k: (ox - 1.5, 20.9, 0), "RP%d" % k: (ox + 2.6, 20.9, 0),
        "RU%d" % k: (ox, 8.8, 90),
    })

POT = ["VIN", "LGND"] + ["OUT%d" % k for k in range(1, 5)]
CAMPO = ["IAV"] + ["%s%d" % (n, k) for n in ("IA", "RA", "GA") for k in range(1, 5)]
NETCLASS = {"CampoPot": (0.6, 0.3, POT), "Campo": (0.3, 0.2, CAMPO)}
# tronco de +V (2.5 mm): de J1 sube por la izquierda y corre por las patas de entrada de los 4 portafusibles;
# cada rama baja de la pata de salida del fusible al + de su borne
# XT60: pata 1 = "-" (abajo, y 44) y pata 2 = "+" (arriba, y 36.8), como las marcas del conector
PRE = [("VIN", 2.5, [(XJ, YJ - 7.2), (XJ, YF), (FX[-1], YF)]),
       ("VIN", 0.6, [(7.04, 20.9), (7.04, YF), (XJ, YF)])]       # aviso de fuente presente
for k, fx in enumerate(FX, start=1):
    PRE.append(("OUT%d" % k, 2.5, [(fx, YF + 9.92), (fx, 41.0), (fx - 1.7, 43.0), (fx - 1.7, YT)]))
ZONA_CAMPO = [(0.3, 17.0), (87.7, 17.0), (87.7, 55.7), (0.3, 55.7)]
ZONAS_FINALES = [("LGND", ZONA_CAMPO), ("LGND", ZONA_CAMPO, "B")]
SIN_COBRE = [[(0.3, 13.5), (87.7, 13.5), (87.7, 17.0), (0.3, 17.0)]]     # franja de aislamiento de 3.5 mm
DRU = """(rule "aislamiento"
  (condition "(A.NetClass == 'Campo' || A.NetClass == 'CampoPot') && B.NetClass != 'Campo' && B.NetClass != 'CampoPot' && !A.memberOfFootprint('OK*') && !B.memberOfFootprint('OK*') && !A.memberOfFootprint('J1') && !B.memberOfFootprint('J1')")
  (constraint clearance (min 2.5mm)))
"""
SILK = [
    ("ENTRADA 12-24V", 9.0, 50.6, 0.9, "F"), ("XT60", 9.0, 52.2, 0.9, "F"),
    ("AP SIGN DIST 4", 50.0, 54.8, 1.0, "B"),
    ("AISLAMIENTO 3.5 mm", 44.0, 15.25, 0.8, "B"),
    ("Solo 12-24 V DC. Fusibles mini de auto, máx. 7.5 A por rama, 10 A en total", 44.0, 52.8, 0.8, "B"),
    ("Dirección: JP1 +1  JP2 +2  (0x24-0x27)", 66.0, 12.6, 0.8, "B"),
]
for k, fx in enumerate(FX, start=1):
    SILK += [("R%d+" % k, fx - 1.7, 45.0, 0.9, "F"), ("0V", fx + 2.26, 45.0, 0.9, "F"),
             ("V", fx + 7.5, 37.4, 0.8, "F"), ("F", fx + 4.5, 37.4, 0.8, "F")]
FLAGS = [("GND", 20.32, 20.32), ("3V3", 35.56, 20.32), ("VIN", 50.8, 20.32), ("LGND", 66.04, 20.32)]
NOTES = [(150.0, 15.0, "AP ELECTRIC · AP SIGN DIST 4: 4 ramas de 12-24 V DC con fusible mini, LED verde (voltaje) y rojo\\n"
                       "(fusible abierto). Aviso aislado al bus: TCA9554 0x24-0x27, E1-E4 ramas, E5 fuente.")]
TITLE = "AP ELECTRIC · AP SIGN DIST 4 - distribución DC protegida"
SUBTITLES = ["Placa de 2 capas, 2 oz (JLCPCB)", "Letras corpóreas, cajas de luz, neón LED: 4 ramas con diagnóstico"]
COMPANY = "PCB 88 x 56 mm, 2 capas, 2 oz"
COSTURA = 5.0
COSTURA_REDES = ("GND", "LGND")
PAPER = "A3"
OCULTAR_REF = ("J1", "J2", "J3", "J4", "J5", "J6", "J7")

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
