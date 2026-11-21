"""Cubo AP · placa de control 68 × 64 mm, 2 capas. Única fuente de verdad: componentes, valores, conexiones y posición.
Coordenadas en mm con origen en el centro del cubo; +x hacia la salida LED (derecha), +y hacia atrás (ventila)."""
import math

W, H = 68.0, 64.0
ESQ_R = 5.8                                   # muesca para los postes de esquina del cubo (centro ±32.5)
ESQ_C = 32.5
BARRENOS = [(sx * 30.5, sy * 24.0) for sx in (-1, 1) for sy in (-1, 1)]   # M3, sobre postes del cubo
ANTENA = (-9.5, -32.0, 9.5, -31.4)           # la antena del SuperMini sobresale 1 mm del borde: sin cobre debajo

# (ref, huella, valor, MPN / nota, x, y, rot, {pin: red})
P = []
def c(ref, fp, val, mpn, x, y, rot, nets): P.append(dict(ref=ref, fp=fp, val=val, mpn=mpn, x=x, y=y, rot=rot, nets=nets))

# ---------------- Entrada (cartucho 12–36 V) ----------------
c("J1", "BORNE2", "Entrada 12–36 V", "Bornera enchufable 5.08 mm 2 polos 15 A (sobresale del borde)", -29.5, 10.0, 0, {"1": "VIN_RAW", "2": "GND"})
c("F1", "2410", "6.3 A rápido", "Fusible SMD 2410 6.3 A 63 V", -19.5, 11.5, 0, {"1": "VIN_RAW", "2": "VIN_F"})
c("Q1", "SO8-PMOS", "P-MOSFET −60 V", "P-MOSFET SO-8 −60 V ≥ 8 A Rds ≤ 25 mΩ (inversión de polaridad)", -16.5, 19.0, 180,
  {"1": "VIN", "2": "VIN", "3": "VIN", "4": "QG", "5": "VIN_F", "6": "VIN_F", "7": "VIN_F", "8": "VIN_F"})
c("DZ1", "SOD123", "12 V", "Zener 12 V 500 mW SOD-123 (protege Vgs)", -24.0, 24.6, 0, {"1": "VIN", "2": "QG"})
c("R1", "0603", "100k", "", -24.0, 27.0, 0, {"1": "QG", "2": "GND"})
c("D1", "SMB", "SMBJ40A", "TVS 40 V unidireccional SMB", -22.5, 17.5, 90, {"1": "VIN", "2": "GND"})
c("C1", "ELEC8", "100 µF 50 V", "Electrolítico SMD 8×10 low-ESR", -18.5, 3.0, 0, {"1": "VIN", "2": "GND"})

# ---------------- Reductor principal TPS54560 (5 A, Vref 0.8 V, 400 kHz) ----------------
c("U1", "HSOP8", "TPS54560DDA", "TI TPS54560DDAR (60 V 5 A)", -5.0, 22.0, 270,
  {"1": "BOOT", "2": "VIN", "3": "EN", "4": "RT", "5": "FB", "6": "COMP", "7": "GND", "8": "SW", "9": "GND"})
c("C2", "1210", "10 µF 50 V X7R", "", -11.0, 25.5, 90, {"1": "VIN", "2": "GND"})
c("C3", "1210", "10 µF 50 V X7R", "", -14.5, 25.5, 90, {"1": "VIN", "2": "GND"})
c("C4", "1210", "10 µF 50 V X7R", "", -11.0, 20.5, 270, {"1": "VIN", "2": "GND"})
c("C5", "0603", "100 nF 50 V", "", -9.3, 16.6, 0, {"1": "VIN", "2": "GND"})
c("C6", "0603", "100 nF", "BOOT", -5.0, 26.0, 0, {"1": "BOOT", "2": "SW"})
c("R2", "0603", "243k 1%", "RT → 400 kHz", -9.3, 14.6, 0, {"1": "RT", "2": "GND"})
c("R3", "0603", "10k", "EN abajo: apagado al arrancar", -9.3, 12.6, 0, {"1": "EN", "2": "GND"})
c("R4", "0603", "4.7k", "GPIO4 → EN", -9.3, 10.6, 0, {"1": "IO4", "2": "EN"})
c("R5", "0603", "62k", "Compensación Rc", 2.0, 16.6, 0, {"1": "COMP", "2": "CC"})
c("C7", "0603", "10 nF", "Compensación Cc", 2.0, 14.6, 0, {"1": "CC", "2": "GND"})
c("C8", "0603", "68 pF", "Compensación Cp", 2.0, 18.6, 0, {"1": "COMP", "2": "GND"})
c("R6", "0603", "29.4k 1%", "Divisor superior (inferior en la tarjeta)", 2.0, 20.6, 0, {"1": "VBUCK", "2": "FB"})
c("C9", "0603", "100 pF", "Filtro FB", 2.0, 12.6, 0, {"1": "FB", "2": "GND"})
c("L1", "IND1265", "10 µH ≥ 9 A", "Inductor blindado 12.5×12.5 mm, Isat ≥ 9 A, DCR ≤ 15 mΩ", 11.8, 23.2, 0, {"1": "SW", "2": "VBUCK"})
c("D2", "SMC", "B560C", "Schottky 60 V 5 A SMC", 1.8, 26.0, 90, {"1": "SW", "2": "GND"})
c("C10", "1210", "22 µF 35 V X7R", "", 20.1, 27.6, 90, {"1": "VBUCK", "2": "GND"})
c("C11", "1210", "22 µF 35 V X7R", "", 23.5, 27.6, 90, {"1": "VBUCK", "2": "GND"})
c("C12", "ELEC6", "100 µF 35 V", "Polímero / low-ESR 6.3×7.7", 12.2, 12.8, 180, {"1": "VBUCK", "2": "GND"})
c("RS", "2512", "5 mΩ 1% 3 W", "Shunt de corriente", 21.8, 21.0, 270, {"1": "VBUCK", "2": "VOUT"})
c("D3", "SMB", "SMBJ26A", "TVS salida 26 V", 22.0, 14.6, 180, {"1": "VOUT", "2": "GND"})

# ---------------- Tarjeta de configuración y ajuste por DAC ----------------
c("J3", "HDR1x3", "Tarjeta", "Tira hembra 2.54 mm 3 pines: 1 FB · 2 GND · 3 ID", -3.8, 11.5, 90, {"1": "FB", "2": "GND", "3": "ID"})
c("U5", "SOT23-6", "MCP4725A0", "DAC 12 bit I2C (0x60)", -1.0, 4.5, 0,
  {"1": "DAC", "2": "GND", "3": "3V3", "4": "SDA", "5": "SCL", "6": "GND"})
c("C14", "0603", "100 nF", "", -1.0, 1.4, 0, {"1": "3V3", "2": "GND"})
c("D5", "SOT23", "BAT54", "Schottky: el DAC solo puede bajar el voltaje", -1.0, 8.4, 0, {"1": "DAC", "2": "NC_D5", "3": "DAC_D"})
c("R8", "0603", "47k 1%", "Inyección al FB", 2.4, 10.6, 0, {"1": "DAC_D", "2": "FB"})
c("R11", "0603", "47k", "Pull-up de ID", -5.6, 8.6, 90, {"1": "3V3", "2": "ID"})
c("C15", "0603", "100 nF", "", -3.6, 8.6, 90, {"1": "ID", "2": "GND"})

# ---------------- Medición: INA226 ----------------
c("U4", "VSSOP10", "INA226", "TI INA226AIDGSR (0x40)", 6.5, 4.5, 90,
  {"1": "GND", "2": "GND", "3": "EN", "4": "SDA", "5": "SCL", "6": "3V3", "7": "GND", "8": "VOUT", "9": "VOUT", "10": "VBUCK"})
c("C13", "0603", "100 nF", "", 6.5, 0.6, 0, {"1": "3V3", "2": "GND"})
c("R9", "0603", "4.7k", "Pull-up SDA", -5.0, 1.4, 0, {"1": "3V3", "2": "SDA"})
c("R10", "0603", "4.7k", "Pull-up SCL", -5.0, -0.6, 0, {"1": "3V3", "2": "SCL"})

# ---------------- 5 V auxiliar (LMR14006) ----------------
c("U2", "SOT23-6", "LMR14006", "TI LMR14006YDDCR 40 V 0.6 A", -17.5, -5.0, 0,
  {"1": "CB", "2": "GND", "3": "FB5", "4": "SHDN", "5": "VIN", "6": "SW5"})
c("C16", "1206", "2.2 µF 50 V", "", -21.8, -5.0, 90, {"1": "VIN", "2": "GND"})
c("R17", "0603", "100k", "SHDN → VIN", -17.5, -8.6, 0, {"1": "VIN", "2": "SHDN"})
c("C17", "0603", "100 nF", "CB", -14.4, -2.4, 0, {"1": "CB", "2": "SW5"})
c("D4", "SMA", "B160", "Schottky 60 V 1 A SMA", -17.5, -12.0, 0, {"1": "SW5", "2": "GND"})
c("L2", "IND4020", "15 µH", "Inductor 4×4 mm Isat ≥ 1 A", -12.0, -6.0, 0, {"1": "SW5", "2": "5V"})
c("R18", "0603", "56k 1%", "FB 5 V", -23.0, -8.4, 0, {"1": "5V", "2": "FB5"})
c("R19", "0603", "10k 1%", "", -23.0, -10.4, 0, {"1": "FB5", "2": "GND"})
c("C18", "1206", "22 µF 10 V", "", -12.0, -10.3, 0, {"1": "5V", "2": "GND"})

# ---------------- Medición de entrada, temperatura, botón, LED ----------------
c("R12", "0603", "100k 1%", "Vin ÷ 11", -26.0, -1.0, 90, {"1": "VIN", "2": "VIN_S"})
c("R13", "0603", "10k 1%", "", -26.0, -4.6, 90, {"1": "VIN_S", "2": "GND"})
c("C19", "0603", "100 nF", "", -28.0, -4.6, 90, {"1": "VIN_S", "2": "GND"})
c("TH1", "0603", "NTC 10k B3950", "Junto al inductor", 6.4, 14.5, 0, {"1": "NTC", "2": "GND"})
c("R14", "0603", "10k 1%", "", 6.4, 12.5, 0, {"1": "3V3", "2": "NTC"})
c("SW1", "TACT6", "Botón", "Pulsador SMD 6×6", -20.5, -26.0, 0, {"1": "IO2", "2": "GND", "x1": "NC_S1", "x2": "NC_S2"})
c("R15", "0603", "10k", "Pull-up botón", -16.5, -21.0, 0, {"1": "3V3", "2": "IO2"})
c("LED1", "0805", "Verde", "LED de estado (tubo de luz de la tapa)", 13.6, -17.0, 0, {"1": "LED_A", "2": "GND"})
c("R16", "0603", "330", "", 13.6, -19.0, 0, {"1": "IO20", "2": "LED_A"})

# ---------------- ESP32-C3 SuperMini (enchufable) ----------------
U3 = {"5V": "5V_MOD", "GND": "GND", "3V3": "3V3", "IO4": "IO4", "IO3": "NTC", "IO2": "IO2", "IO1": "VIN_S", "IO0": "ID",
      "IO5": "IO5", "IO6": "IO6", "IO7": "IO7", "IO8": "SDA", "IO9": "SCL", "IO10": "IO10", "IO20": "IO20", "IO21": "IO21"}
c("U3", "SUPERMINI", "ESP32-C3 SuperMini", "Módulo ESP32-C3 SuperMini sobre tira de pines (USB hacia atrás)", 0.0, -21.5, 0, U3)

c("D6", "SMA", "B140", "Schottky: evita retroalimentar el USB de la PC", -11.5, -15.5, 90, {"1": "5V_MOD", "2": "5V"})

# ---------------- Canales PWM: 2 × UCC27524 + 4 MOSFET ----------------
for ref, ia, ib, ga, gb in (("U6", "IO21", "IO5", "GR", "GG"), ("U7", "IO6", "IO7", "GB", "GW")):
    x, y, r = {"U6": (14.2, 3.4, 0), "U7": (14.2, -7.2, 0)}[ref]
    c(ref, "SOIC8", "UCC27524", "TI UCC27524DR doble driver 5 A", x, y, r,
      {"1": "5V", "2": ia, "3": "GND", "4": ib, "5": gb + "_D", "6": "5V", "7": ga + "_D", "8": "5V"})
c("C20", "0805", "1 µF", "", 14.2, 8.2, 0, {"1": "5V", "2": "GND"})
c("C21", "0805", "1 µF", "", 14.2, -12.2, 0, {"1": "5V", "2": "GND"})
CANAL = [("R", 10.16, "GR"), ("G", 5.08, "GG"), ("B", 0.0, "GB"), ("W", -5.08, "GW")]
for i, (n, yj, g) in enumerate(CANAL):
    y = yj
    c(f"Q{2+i}", "DFN3x3", "N-MOSFET 40 V", "N-MOSFET 40 V Rds ≤ 12 mΩ @ 4.5 V, DFN 3.3×3.3", 22.6, y, 270,
      {"1": "GND", "2": "GND", "3": "GND", "4": g, "D": "CH_" + n})
    c(f"R{20+i}", "0603", "10", "Compuerta", 18.6, y + 1.0, 0, {"1": g + "_D", "2": g})
    c(f"R{24+i}", "0603", "100k", "Pull-down compuerta", 18.6, y - 1.0, 0, {"1": g, "2": "GND"})

# ---------------- Salida direccionable ----------------
c("U8", "SOT23-5", "74AHCT1G125", "Buffer 3.3 → 5 V para WS2812", 16.0, -24.5, 0, {"1": "GND", "2": "IO10", "3": "GND", "4": "DAT_B", "5": "5V"})
c("C22", "0603", "100 nF", "", 12.6, -24.5, 90, {"1": "5V", "2": "GND"})
c("R28", "0603", "33", "Serie datos", 19.5, -24.5, 0, {"1": "DAT_B", "2": "DATA"})

# ---------------- Salida LED ----------------
c("J2", "BORNE7", "Salida LED", "Bornera enchufable 5.08 mm 7 polos: V+ R G B W DAT GND", 29.5, 0.0, 0,
  {"1": "VOUT", "2": "CH_R", "3": "CH_G", "4": "CH_B", "5": "CH_W", "6": "DATA", "7": "GND"})

# ---------------- Puntos de prueba ----------------
for i, (n, x, y) in enumerate((("VIN", -12.5, 1.6), ("5V", -8.0, -5.0), ("3V3", -11.5, -20.6), ("VOUT", 26.0, 20.2), ("GND", -26.0, -15.0))):
    c(f"TP{i+1}", "TP", n, "Punto de prueba", x, y, 0, {"1": n})

# ---------------- Zonas de cobre de potencia (capa superior), se recortan con 0.3 mm a otras redes --------------
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
ZONAS = {
  "VIN_RAW": box(-30.8, 10.1, -21.3, 13.84),
  "VIN_F":   box(-19.0, 10.1, -14.0, 17.1),
  "VIN":     Polygon([(-17.6, 20.8), (-9.2, 20.8), (-9.2, 22.25), (-6.95, 22.25), (-6.95, 23.0), (-9.2, 23.0), (-9.2, 25.0), (-17.6, 25.0)]),
  "SW":      Polygon([(-3.1, 23.55), (-0.5, 23.55), (-0.5, 21.3), (8.7, 21.3), (8.7, 25.8), (-0.5, 25.8), (-0.5, 24.25), (-3.1, 24.25)]),
  "VBUCK":   Polygon([(12.6, 11.9), (16.5, 11.9), (16.5, 20.6), (18.6, 20.6), (18.6, 22.9), (25.2, 22.9), (25.2, 26.8), (14.9, 26.8), (14.9, 20.0), (12.6, 20.0)]),
  "VOUT":    unary_union([box(20.1, 16.6, 23.6, 19.0), box(23.0, 13.45, 31.0, 17.2), box(25.0, 17.2, 27.0, 21.2)]),
}
for _n, _yq in (("R", 10.16), ("G", 5.08), ("B", 0.0), ("W", -5.08)):
    ZONAS["CH_" + _n] = box(21.9, _yq - 1.2, 31.0, _yq + 1.2)
# clase de pista por red (ancho mm); el resto usa 0.25 mm
ANCHO = {"VIN": 0.5, "5V": 0.5, "5V_MOD": 0.5, "3V3": 0.4, "SW5": 0.6, "GR_D": 0.4, "GG_D": 0.4, "GB_D": 0.4, "GW_D": 0.4,
         "GR": 0.4, "GG": 0.4, "GB": 0.4, "GW": 0.4, "VBUCK": 0.6, "VOUT": 0.4, "QG": 0.3}
