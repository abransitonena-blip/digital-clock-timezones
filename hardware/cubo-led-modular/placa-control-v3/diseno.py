"""Cubo AP · placa de control v3: ESP32-C3 SOLDADO DIRECTO (chip QFN32, sin módulo) + DMX512 por cable + 5 canales. 68 × 64 mm, 2 capas.
Mismo mapa de GPIO que la v2: corre el mismo firmware (CUBO_PLACA=2). Circuito del chip según la guía de diseño de hardware
de Espressif (ESP32-C3, esquema de referencia y lista de verificación): cristal 40 MHz ±10 ppm, inductor serie de 24 nH en XTAL_P,
LC en VDD3P3, CLC de acople RF, RC en CHIP_EN. Única fuente de verdad: componentes, valores, conexiones y posición.
Coordenadas en mm con origen en el centro del cubo; +x hacia la salida LED (derecha), +y hacia atrás (ventila)."""
import math

W, H = 68.0, 64.0
ESQ_R = 5.8                                   # muesca para los postes de esquina del cubo (centro ±32.5)
ESQ_C = 32.5
BARRENOS = [(sx * 30.5, sy * 24.0) for sx in (-1, 1) for sy in (-1, 1)]   # M3, sobre postes del cubo
ANTENA = None                                 # v3: antena externa por U.FL (cable a través de la pared del cubo)

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
c("D3", "SOD123", "SMF26A", "TVS salida 26 V 200 W, SOD-123FL", 19.8, 15.55, 180, {"1": "VOUT", "2": "GND"})

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
c("LED1", "0805", "Verde", "LED de estado (tubo de luz de la tapa)", 13.6, -17.0, 0, {"1": "LED_A", "2": "GND"})
c("R16", "0603", "330", "", 13.6, -19.0, 0, {"1": "IO20", "2": "LED_A"})

# ---------------- ESP32-C3FH4 soldado (QFN32 5×5, 4 MB de flash dentro del encapsulado) ----------------
# Rotación 90°: abajo pines 1–8 (RF, VDD3P3, GPIO0–3, EN); derecha 9–16 (GPIO4–10); arriba 17–24 (VDD_CPU, VDD_SPI, SPI interno = NC);
# izquierda 25–32 (USB D−/D+, GPIO20/21, XTAL, VDDA). Pines 19–24: flash interna, no se conectan.
UX, UY = 0.0, -18.5
U3 = {"1": "LNA", "2": "3V3_RF", "3": "3V3_RF", "4": "ID", "5": "VIN_S", "6": "DMX_RX", "7": "CHIP_EN", "8": "NTC",
      "9": "IO4", "10": "IO5", "11": "3V3", "12": "IO6", "13": "IO7", "14": "SDA", "15": "SCL", "16": "IO10",
      "17": "3V3", "18": "VDD_SPI", "25": "USB_DM", "26": "USB_DP", "27": "IO20", "28": "IO21", "29": "XTAL_N", "30": "XTAL_P",
      "31": "3V3", "32": "3V3", "33": "GND"}
c("U3", "QFN32", "ESP32-C3FH4", "Espressif ESP32-C3FH4 (RISC-V 160 MHz, Wi-Fi 4 + BLE 5, 4 MB flash interna) QFN32 5×5", UX, UY, 90, U3)
# VDD3P3 (pines 2-3): 2.0 nH + desacoplo (ref. Espressif: L1 2.0 nH, 10 µF + 0.1 µF del lado de 3V3, 1 µF del lado del chip)
c("L3", "0402", "2.0 nH", "Inductor RF 0402 2.0 nH ≥ 500 mA", -1.0, -22.65, 90, {"1": "3V3", "2": "3V3_RF"})
c("C35", "0402", "1 µF", "X5R 10 V", -1.0, -24.6, 270, {"1": "3V3", "2": "GND"})
c("C34", "0603", "10 µF", "X5R 10 V (riel de RF: picos de TX)", 0.9, -26.0, 90, {"1": "3V3", "2": "GND"})
c("C36", "0402", "0.1 µF", "", -1.0, -26.6, 270, {"1": "3V3", "2": "GND"})
# VDDA (31-32): 1 µF + 10 nF
c("C43", "0402", "10 nF", "", -3.6, -21.8, 270, {"1": "3V3", "2": "GND"})
c("C42", "0402", "1 µF", "", -4.6, -21.8, 270, {"1": "3V3", "2": "GND"})
# VDD3P3_RTC (11) y VDD3P3_CPU (17): 0.1 µF; VDD_SPI (18, alimenta la flash interna): 1 µF
c("C44", "0402", "0.1 µF", "VDD3P3_RTC", 6.6, -22.2, 0, {"1": "3V3", "2": "GND"})
c("C45", "0402", "0.1 µF", "VDD3P3_CPU", 2.3, -14.3, 90, {"1": "3V3", "2": "GND"})
c("C47", "0402", "1 µF", "VDD_SPI (flash interna)", 0.9, -14.3, 90, {"1": "VDD_SPI", "2": "GND"})
# CHIP_EN: RC 10k / 1 µF (arranque después de que se estabilice 3V3)
c("R32", "0402", "10k", "CHIP_EN pull-up", 4.4, -23.4, 0, {"1": "3V3", "2": "CHIP_EN"})
c("C48", "0402", "1 µF", "CHIP_EN retardo", 4.4, -24.4, 0, {"1": "CHIP_EN", "2": "GND"})
# Cristal 40 MHz ±10 ppm (CL 10 pF): C = 2·(CL − Cparásita) ≈ 12 pF; ajustar con prueba de tono (offset ≤ ±10 ppm)
c("Y1", "XTAL3225", "40 MHz", "Cristal 3225 40 MHz ±10 ppm CL 10 pF", -7.5, -19.6, 0, {"1": "XTAL_PX", "2": "GND", "3": "XTAL_N", "4": "GND"})
c("L5", "0402", "24 nH", "Serie en XTAL_P (atenúa armónicos del cristal); ajustar tras prueba", -4.4, -19.5, 0, {"1": "XTAL_PX", "2": "XTAL_P"})
c("C49", "0402", "12 pF", "Carga del cristal (XTAL_P) C0G", -8.6, -22.2, 270, {"1": "XTAL_PX", "2": "GND"})
c("C50", "0402", "12 pF", "Carga del cristal (XTAL_N) C0G", -6.4, -16.9, 90, {"1": "XTAL_N", "2": "GND"})
# RF: CLC junto al chip (valores por sintonizar con analizador de redes) → 50 Ω → U.FL → antena externa
c("C40", "0402", "DNP", "Acople RF: C en paralelo, valor por sintonizar (sin poblar al inicio)", -3.51, -24.4, 180, {"1": "LNA", "2": "GND"})
c("L4", "0402", "0 Ω", "Acople RF: elemento serie (0 Ω al inicio, luego L/C sintonizado)", -3.0, -25.8, 270, {"1": "LNA", "2": "ANT"})
c("C41", "0402", "DNP", "Acople RF: C en paralelo, valor por sintonizar", -3.51, -27.2, 180, {"1": "ANT", "2": "GND"})
c("J6", "UFL", "U.FL", "Hirose U.FL-R-SMT-1 → pigtail a antena 2.4 GHz externa (prensaestopa/SMA en la pared)", -3.0, -29.4, 270, {"1": "ANT", "2": "GND"})
# Regulador 3.3 V (antes lo traía el módulo)
c("U11", "SOT23-5", "AP2112K-3.3", "Diodes AP2112K-3.3TRG1 LDO 600 mA", 7.0, -26.8, 0, {"1": "5V", "2": "GND", "3": "5V", "4": "NC_U11", "5": "3V3"})
c("C30", "0603", "1 µF", "Entrada LDO", 4.2, -26.8, 90, {"1": "5V", "2": "GND"})
c("C31", "0805", "10 µF", "Salida LDO", 10.2, -26.8, 90, {"1": "3V3", "2": "GND"})
# Programación: USB del propio C3 (USB-Serial-JTAG) en 6 pads para puntas pogo; IO9 a GND al reset = modo descarga
c("J5", "PROG6", "PROG", "Pads de programación: 5V · D− · D+ · GND · EN · IO9 (adaptador pogo a USB)", 10.0, -30.0, 0,
  {"1": "5V_USB", "2": "USB_DM", "3": "USB_DP", "4": "GND", "5": "CHIP_EN", "6": "SCL"})
c("D6", "SMA", "B140", "Schottky: evita retroalimentar el USB de la PC", -11.5, -14.5, 90, {"1": "5V_USB", "2": "5V"})

# ---------------- Canales PWM: 2 × UCC27524 + 4 MOSFET ----------------
for ref, ia, ib, ga, gb in (("U6", "IO21", "IO5", "GR", "GG"), ("U7", "IO6", "IO7", "GB", "GW")):
    x, y, r = {"U6": (14.2, 3.4, 0), "U7": (14.2, -7.2, 0)}[ref]
    c(ref, "SOIC8", "UCC27524", "TI UCC27524DR doble driver 5 A", x, y, r,
      {"1": "5V", "2": ia, "3": "GND", "4": ib, "5": gb + "_D", "6": "5V", "7": ga + "_D", "8": "5V"})
c("C20", "0805", "1 µF", "", 14.2, 8.2, 0, {"1": "5V", "2": "GND"})
c("C21", "0805", "1 µF", "", 14.2, -12.2, 0, {"1": "5V", "2": "GND"})
CANAL = [("R", 12.7, "GR"), ("G", 7.62, "GG"), ("B", 2.54, "GB"), ("W", -2.54, "GW"), ("C", -7.62, "GC")]
for i, (n, yj, g) in enumerate(CANAL):
    y = yj
    c(f"Q{2+i}", "DFN3x3", "N-MOSFET 40 V", "N-MOSFET 40 V Rds ≤ 12 mΩ @ 4.5 V, DFN 3.3×3.3", 22.6, y, 270,
      {"1": "GND", "2": "GND", "3": "GND", "4": g, "D": "CH_" + n})
    c(f"R{20+i}", "0603", "10", "Compuerta", 18.6, y + 1.0, 0, {"1": g + "_D", "2": g})
    c(f"R{40+i}", "0603", "100k", "Pull-down compuerta", 18.6, y - 1.0, 0, {"1": g, "2": "GND"})
# 5.º canal (blanco frío): driver sencillo; su entrada comparte IO10 con los datos WS2812 (el firmware nunca usa ambos)
c("U10", "SOT23-5", "UCC27517", "TI UCC27517DBVR driver sencillo 4 A", 17.8, -13.2, 0, {"1": "5V", "2": "GND", "3": "IO10", "4": "GND", "5": "GC_D"})
c("C24", "0805", "1 µF", "", 21.4, -15.6, 0, {"1": "5V", "2": "GND"})

# ---------------- DMX512 por cable (RS-485, solo recepción) ----------------
c("U9", "SOIC8", "RS-485 3.3 V", "Transceptor RS-485 3.3 V con fail-safe, pinout xx485 (p. ej. THVD1410, SN65HVD72)", -19.5, -21.0, 0,
  {"1": "DMX_RX", "2": "GND", "3": "GND", "4": "DMX_DI", "5": "GND", "6": "DMX_A", "7": "DMX_B", "8": "3V3"})
c("C23", "0603", "100 nF", "", -21.4, -15.8, 0, {"1": "3V3", "2": "GND"})
c("R30", "0603", "10k", "DI fijo (solo recepción)", -17.6, -15.8, 0, {"1": "3V3", "2": "DMX_DI"})
c("D7", "SOT23", "SM712", "TVS para RS-485 (−7/+12 V)", -24.5, -22.0, 0, {"1": "DMX_A", "2": "DMX_B", "3": "GND"})
c("R31", "0603", "120", "Terminación DMX", -14.2, -21.2, 0, {"1": "DMX_A", "2": "TERM"})
c("JP3", "HDR1x2", "TERM", "Puente: colocar solo en el último equipo de la línea", -13.0, -23.8, 90, {"1": "TERM", "2": "DMX_B"})
c("J4", "BORNE35_3", "DMX", "Bornera 3.5 mm 3 polos: GND · D− · D+ (pines 1-2-3 del XLR)", -16.0, -28.6, 90,
  {"1": "GND", "2": "DMX_B", "3": "DMX_A"})

# ---------------- Salida direccionable ----------------
c("U8", "SOT23-5", "74AHCT1G125", "Buffer 3.3 → 5 V para WS2812", 16.0, -24.5, 0, {"1": "GND", "2": "IO10", "3": "GND", "4": "DAT_B", "5": "5V"})
c("C22", "0603", "100 nF", "", 12.6, -24.5, 90, {"1": "5V", "2": "GND"})
c("R28", "0603", "33", "Serie datos", 19.5, -24.5, 0, {"1": "DAT_B", "2": "DATA"})

# ---------------- Salida LED ----------------
c("J2", "BORNE8", "Salida LED", "Bornera enchufable 5.08 mm 8 polos: V+ R G B WW CW DAT GND", 29.5, 0.0, 0,
  {"1": "VOUT", "2": "CH_R", "3": "CH_G", "4": "CH_B", "5": "CH_W", "6": "CH_C", "7": "DATA", "8": "GND"})

# ---------------- Puntos de prueba ----------------
for i, (n, x, y) in enumerate((("VIN", -12.5, 1.6), ("5V", -8.0, -5.0), ("3V3", 6.5, -12.0), ("GND", -26.0, -15.0))):
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
  "VOUT":    unary_union([box(20.1, 14.9, 23.6, 19.0), box(23.0, 16.3, 31.0, 19.3)]),
}
for _n, _yq, _g in CANAL:
    ZONAS["CH_" + _n] = box(21.9, _yq - 1.2, 31.0, _yq + 1.2)
# clase de pista por red (ancho mm); el resto usa 0.25 mm
ANCHO = {"VIN": 0.5, "5V": 0.5, "5V_MOD": 0.5, "3V3": 0.4, "SW5": 0.6, "GR_D": 0.4, "GG_D": 0.4, "GB_D": 0.4, "GW_D": 0.4,
         "GR": 0.4, "GG": 0.4, "GB": 0.4, "GW": 0.4, "GC": 0.4, "GC_D": 0.4, "VBUCK": 0.6, "VOUT": 0.4, "QG": 0.3}

# ---------------- Zona del chip: pistas fijas (RF, cristal, desacoplo) ----------------
def pf(red, w, *pts, plana=False): PISTAS.append(dict(red=red, w=w, pts=list(pts), plana=plana))
PISTAS = []
pf("LNA", 0.3, (-1.75, -21.0), (-1.75, -22.6), (-3.0, -23.85), (-3.0, -25.29))
pf("ANT", 0.8, (-3.0, -26.31), (-3.0, -28.35), plana=True)
pf("3V3_RF", 0.25, (-1.25, -21.1), (-1.25, -21.65), (-0.75, -21.65), (-0.75, -21.1))
pf("3V3_RF", 0.25, (-1.0, -21.65), (-1.0, -22.14))
pf("3V3", 0.3, (-1.0, -23.16), (-1.0, -24.09))
pf("3V3", 0.25, (-2.7, -19.75), (-3.3, -19.75), (-3.3, -21.29))     # VDDA 31
pf("3V3", 0.25, (-2.7, -20.25), (-3.3, -20.25))                      # VDDA 32
pf("3V3", 0.25, (-3.3, -21.0), (-4.6, -21.0), (-4.6, -21.29))
pf("XTAL_N", 0.2, (-2.7, -18.75), (-6.2, -18.75))
pf("XTAL_N", 0.2, (-6.4, -18.4), (-6.4, -17.41))
pf("XTAL_P", 0.2, (-2.7, -19.25), (-3.4, -19.25), (-3.65, -19.5), (-3.89, -19.5))
pf("XTAL_PX", 0.2, (-4.91, -19.5), (-5.3, -19.5), (-5.3, -21.5), (-8.6, -21.5), (-8.6, -20.6))
pf("VDD_SPI", 0.25, (1.25, -15.8), (1.25, -15.3), (0.9, -14.95), (0.9, -14.81))
pf("3V3", 0.25, (1.75, -15.8), (1.75, -15.3), (2.3, -14.95), (2.3, -14.81))
from shapely.geometry import box as _box
ZONA_FINA = _box(UX - 3.7, UY - 3.7, UX + 3.7, UY + 3.7)
W_FINO = 0.15
VEDA = [((1,), _box(-9.6, -23.4, -5.0, -16.4)),                       # bajo el cristal: plano de GND inferior sin cortes
        ((1,), _box(-5.6, -31.8, -1.4, -22.6)),                       # bajo la red RF y el U.FL
        ((0,), _box(-9.5, -21.2, -5.5, -17.8))]
CLR_PLANO_RED = {"LNA": 0.2, "ANT": 0.2}
pf("3V3", 0.25, (-4.1, -21.0), (-4.1, -20.4))                        # VDDA sale por una via (queda encerrada entre cristal y RF)
VIAS = [(-4.1, -20.4, "3V3")]

# Abanico (fan-out) fijo de los pines de señal: separa las salidas a ≥ 0.8 mm antes de que entre el ruteador
WF = 0.15
for k in range(8):                                                  # derecha: pines 9–16
    y = UY - 1.75 + 0.5 * k; y2 = UY + (y - UY) * 1.6
    pf(U3[str(9 + k)], WF, (UX + 2.7, y), (UX + 3.3, y), (UX + 4.5, y2), (UX + 5.3, y2))
for k, x in enumerate((-0.25, 0.25, 0.75, 1.25, 1.75)):             # abajo: pines 4–8
    x2 = 1.5 + (x - 0.75) * 1.6
    pf(U3[str(4 + k)], WF, (x, UY - 2.7), (x, UY - 3.3), (x2, UY - 4.5))
for k in range(4):                                                  # izquierda: pines 25–28 suben en carriles de 0.6 mm
    y = UY + 1.75 - 0.5 * k; xc = UX - 3.3 - 0.6 * k
    pf(U3[str(25 + k)], WF, (UX - 2.7, y), (xc, y), (xc, UY + 3.3))
