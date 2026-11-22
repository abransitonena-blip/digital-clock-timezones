"""Nodo AP · decodificador DMX512 → 4 canales PWM (RGBW) con el CH32V003 soldado. 50 × 38 mm, 2 capas.
Recibe DMX por cable (del Cubo AP, de una consola o de otro nodo) y maneja una tira de ánodo común de 12–24 V,
hasta 3 A por canal y 5 A en total. Coordenadas en mm, origen al centro de la placa, +x hacia la salida LED."""
from shapely.geometry import box

W, H = 50.0, 38.0
ESQ_R, ESQ_C = 0.0, 0.0                       # sin muescas de esquina
BARRENOS = [(-21.5, -15.5), (14.5, -16.5)]   # M3 (arriba va el cobre ancho de V+)
ANTENA = None

P = []
def c(ref, fp, val, mpn, x, y, rot, nets): P.append(dict(ref=ref, fp=fp, val=val, mpn=mpn, x=x, y=y, rot=rot, nets=nets))

# ---------------- Entrada y 5 V ----------------
c("J1", "BORNE2", "Entrada 12–24 V", "Bornera 5.08 mm 2 polos", -21.0, 10.5, 0, {"1": "VIN_RAW", "2": "GND"})
c("F1", "2410", "8 A", "Fusible SMD 2410 8 A rápido ≥ 32 V (carga máx. 5 A = 63 % del nominal, con margen por temperatura)", -12.5, 14.3, 0, {"1": "VIN_RAW", "2": "VIN"})
c("D1", "SMA", "B140", "Schottky 40 V 1 A: protege la lógica de la polaridad invertida", -12.5, 10.4, 180, {"1": "VIN_D", "2": "VIN"})
c("R30", "1206", "150", "Resistencia serie 1206 0.25 W: se lleva parte del calor del 78L05 (a 24 V, 20 mA: 0.06 W)", -7.5, 6.4, 0,
  {"1": "VIN_D", "2": "VIN_R"})
c("C1", "0805", "1 µF 50 V", "X7R", -8.6, 10.4, 90, {"1": "VIN_R", "2": "GND"})
c("U3", "SOT89", "78L05", "Regulador 5 V 100 mA SOT-89 (1 OUT · 2 GND · 3 IN), Vin máx. 30 V", -4.6, 11.0, 0,
  {"1": "5V", "2": "GND", "3": "VIN_R"})
c("C2", "0805", "10 µF", "X5R 10 V", -0.6, 11.4, 90, {"1": "5V", "2": "GND"})

# ---------------- Microcontrolador CH32V003F4P6 (a 5 V) ----------------
U1 = {"3": "DMX_RX", "5": "PWM_G", "7": "GND", "9": "5V", "11": "LED", "12": "BOTON", "13": "PWM_B", "14": "PWM_W",
      "18": "SWIO", "19": "PWM_R"}
c("U1", "TSSOP20", "CH32V003F4P6", "WCH CH32V003F4P6 (RISC-V 48 MHz, 16 KB flash, 2 KB RAM) TSSOP-20", 1.5, 1.0, 0, U1)
c("C3", "0603", "100 nF", "", -3.6, 0.0, 90, {"1": "5V", "2": "GND"})

# ---------------- DMX512: RS-485 de 5 V, solo recepción ----------------
c("U2", "SOIC8", "MAX485", "Transceptor RS-485 5 V (MAX485/SP485/THVD1450), fijo en recepción", -11.0, -1.0, 0,
  {"1": "DMX_RX", "2": "GND", "3": "GND", "4": "GND", "5": "GND", "6": "DMX_A", "7": "DMX_B", "8": "5V"})
c("C4", "0603", "100 nF", "", -11.0, 3.4, 0, {"1": "5V", "2": "GND"})
c("D2", "SOT23", "SM712", "TVS para RS-485 (−7/+12 V)", -15.5, -6.0, 0, {"1": "DMX_A", "2": "DMX_B", "3": "GND"})
c("R5", "0603", "120", "Terminación DMX", -11.0, -6.4, 0, {"1": "DMX_A", "2": "TERM"})
c("JP1", "HDR1x2", "TERM", "Puente: solo en el último equipo de la línea", -6.5, -6.8, 90, {"1": "TERM", "2": "DMX_B"})
c("J3", "BORNE35_3", "DMX entra", "Bornera 3.5 mm: GND · D− · D+ (XLR 1-2-3)", -21.5, -1.5, 0, {"1": "GND", "2": "DMX_B", "3": "DMX_A"})
c("J4", "BORNE35_3", "DMX sale", "Bornera 3.5 mm en paralelo para encadenar nodos", -12.0, -13.0, 90, {"1": "GND", "2": "DMX_B", "3": "DMX_A"})

# ---------------- Salidas: 4 MOSFET de nivel lógico ----------------
J2Y = 0.0
c("J2", "BORNE5", "Salida LED", "Bornera 5.08 mm 5 polos: V+ R G B W (ánodo común)", 21.5, J2Y, 0,
  {"1": "VIN", "2": "CH_R", "3": "CH_G", "4": "CH_B", "5": "CH_W"})
for i, (n, pwm) in enumerate((("R", "PWM_R"), ("G", "PWM_G"), ("B", "PWM_B"), ("W", "PWM_W"))):
    y = J2Y + 5.08 - 5.08 * i
    c(f"Q{i+1}", "DFN3x3", "N-MOSFET 30 V", "N-MOSFET 30 V Rds ≤ 10 mΩ @ Vgs 4.5 V, DFN 3.3×3.3 (pad de drenaje grande: disipa al cobre)", 15.4, y, 270,
      {"1": "GND", "2": "GND", "3": "GND", "4": "G" + n, "D": "CH_" + n})
    c(f"R{i+1}", "0603", "100", "Compuerta", 11.4, y + 0.9, 0, {"1": pwm, "2": "G" + n})
    c(f"R{i+11}", "0603", "100k", "Pull-down: apagado al arrancar", 11.4, y - 0.9, 0, {"1": "G" + n, "2": "GND"})

# ---------------- Interfaz: botón, LED, programación ----------------
c("SW1", "TACT6", "APRENDER", "Pulsador 6 × 6 mm: aprende la dirección DMX", 1.0, -11.0, 0, {"1": "BOTON", "2": "GND", "x1": "BOTON", "x2": "GND"})
c("LED1", "0805", "Verde", "Estado: fijo = recibe · destello = sin señal · rápido = aprendiendo", 7.2, -8.5, 90, {"1": "LED_A", "2": "GND"})
c("R6", "0603", "1k", "", 7.2, -4.6, 90, {"1": "LED", "2": "LED_A"})
c("J5", "HDR1x3", "SWIO", "Programación WCH-LinkE: 1 5V · 2 SWIO · 3 GND", 7.0, 7.0, 0, {"1": "5V", "2": "SWIO", "3": "GND"})

# ---------------- Cobre de potencia (capa superior) ----------------
ZONAS = {"VIN": box(-11.0, 15.6, 23.0, 18.4).union(box(20.0, 9.0, 23.0, 18.4))}   # 2.8 mm: hasta 6 A
for i, n in enumerate("RGBW"):
    y = J2Y + 5.08 - 5.08 * i
    ZONAS["CH_" + n] = box(15.8, y - 1.0, 21.0, y + 1.0)
ANCHO = {"VIN": 0.8, "VIN_RAW": 1.0, "VIN_D": 0.4, "VIN_R": 0.4, "5V": 0.4, "CH_R": 1.2, "CH_G": 1.2, "CH_B": 1.2, "CH_W": 1.2}
PISTAS, VIAS, VEDA = [], [], []
LEYENDAS = [("V+", 18.9, 10.16, 0.9), ("R", 18.9, 6.3, 0.9), ("G", 18.9, 1.2, 0.9), ("B", 18.9, -3.9, 0.9), ("W", 18.9, -9.0, 0.9),
            ("12-24V", -21.0, 17.2, 0.9), ("DMX", -21.5, -8.1, 0.9), ("GND D- D+", -12.0, -9.0, 0.7),
            ("NODO AP", 2.5, 13.6, 1.2), ("5V SWIO GND", 7.0, 11.4, 0.6)]
