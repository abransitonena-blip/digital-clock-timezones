#!/usr/bin/env python3
"""Revisa que los pines del ESP32-C3-WROOM-02 en la placa (netlist de gen/make.py) coincidan con los GPIO del programa (APControl.ino).
Tabla del módulo: símbolo RF_Module:ESP32-C3-WROOM-02 de KiCad 9. Uso:  python3 tools/revisar_pines.py"""
import re, sys, os
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ap-electric")
MODULO = {"1": "3V3", "2": "EN", "3": 4, "4": 5, "5": 6, "6": 7, "7": 8, "8": 9, "9": "GND", "10": 10, "11": 20, "12": 21, "13": 18, "14": 19,
          "15": 3, "16": 2, "17": 1, "18": 0, "19": "GND"}
mk = open(os.path.join(R, "7r-tour/gen/make.py"), encoding="utf-8").read()
m = re.search(r'\("U9", "ESP32-C3-WROOM-02".*?\{(".*?)\},\n', mk, re.S)
red_por_pin = eval("{" + m.group(1) + "}")
ino = open(os.path.join(R, "firmware/APControl/APControl.ino"), encoding="utf-8").read()
const = {}
for mm in re.finditer(r"const uint8_t ([^;]+);", ino):
    for a in re.finditer(r"(P7_\w+|PH_\w+|P_MODO)\s*=\s*(\d+)", mm.group(1)):
        const[a.group(1)] = int(a.group(2))
# red de la placa -> constante del programa
ESPERADO = {"INT": "P7_INT", "LRUN": "P7_LRUN", "LFAL": "P7_LFAL", "LCOM": "P7_LCOM", "SCL": "P7_SCL", "SDA": "P7_SDA", "RS_DE": "P7_DE",
            "RS_RX": "P7_RX", "RS_TX": "P7_TX", "E1": "P7_E1", "E2": "P7_E2", "BOOT": "P_MODO"}
errores = []
gpio_de_red = {}
for pin, red in red_por_pin.items():
    if red in ("3V3", "GND", "EN", None):
        continue
    gpio_de_red[red] = MODULO[pin]
for red, cte in ESPERADO.items():
    if red not in gpio_de_red: errores.append("la red %s no está en el módulo" % red); continue
    if cte not in const: errores.append("el programa no define %s" % cte); continue
    if gpio_de_red[red] != const[cte]:
        errores.append("%s: la placa la lleva a IO%s y el programa usa IO%s (%s)" % (red, gpio_de_red[red], const[cte], cte))
for red, g in gpio_de_red.items():
    if red not in ESPERADO and red not in ("USB_DN", "USB_DP"):
        errores.append("red %s (IO%s) sin constante del programa: agregarla a ESPERADO" % (red, g))
if gpio_de_red.get("USB_DN") != 18 or gpio_de_red.get("USB_DP") != 19:
    errores.append("USB debe ir a IO18/IO19")
if not (ino.count("CDCOnBoot=cdc") or "CDCOnBoot=cdc" in open(os.path.join(R, "../tools/compilar_esp32.sh"), encoding="utf-8").read()):
    errores.append("la consola USB necesita CDCOnBoot=cdc")
# ---- AP Rack 16: placa rack16/gen/make.py contra firmware/APRack/APRack.ino ----
rk = open(os.path.join(R, "rack16/gen/make.py"), encoding="utf-8").read()
m = re.search(r'\("U3", "ESP32-C3-WROOM-02".*?\{(".*?)\},\n', rk, re.S)
rojo = eval("{" + m.group(1) + "}")
rino = open(os.path.join(R, "firmware/APRack/APRack.ino"), encoding="utf-8").read()
bloque_s3 = re.search(r"#if CONFIG_IDF_TARGET_ESP32S3(.*?)\n#else", rino, re.S).group(1)       # pines del AP PLC C24 rev B (ESP32-S3)
rino = rino.replace(bloque_s3, "")                                                           # lo demás de las comprobaciones es del ESP32-C3
cr = {}
for mm in re.finditer(r"const uint8_t ([^;]+);", rino):
    for a in re.finditer(r"(P_\w+)\s*=\s*(\d+)", mm.group(1)):
        cr[a.group(1)] = int(a.group(2))
ESP_RACK = {"INT": "P_INT", "SENSE_I": "P_SENSE_I", "SENSE_O": "P_SENSE_O", "SCL": "P_SCL", "BOOT": "P_MODO", "RS_DE": "P_DE",
            "RS_RX": "P_RX", "SDA": "P_SDA", "RS_TX": "P_TX", "VSENSE": "P_VSENSE"}
g2 = {red: MODULO[pin] for pin, red in rojo.items() if red not in ("3V3", "GND", "EN", None)}
for red, cte in ESP_RACK.items():
    if red not in g2: errores.append("Rack: la red %s no está en el módulo" % red); continue
    if cte not in cr: errores.append("Rack: el programa no define %s" % cte); continue
    if g2[red] != cr[cte]: errores.append("Rack %s: la placa usa IO%s y el programa IO%s (%s)" % (red, g2[red], cr[cte], cte))
for red, g in g2.items():
    if red not in ESP_RACK and red not in ("USB_DN", "USB_DP"):
        errores.append("Rack: red %s (IO%s) sin constante del programa" % (red, g))
# direcciones I2C: pines A0-A2 de cada TCA9554 contra las constantes del programa
for ref, cte in (("U6", "TCA_S1"), ("U7", "TCA_S2"), ("U8", "TCA_ENT"), ("U9", "TCA_LED")):
    mt = re.search(r'tca\("%s", \("(\w+)", "(\w+)", "(\w+)"\)' % ref, rk)
    dirx = 0x20 + sum((1 << i) for i, v in enumerate(mt.groups()) if v == "3V3")
    mc = re.search(r"%s = (0x[0-9A-Fa-f]+)" % cte, rino)
    if int(mc.group(1), 16) != dirx: errores.append("Rack %s: la placa da 0x%02X y el programa %s" % (ref, dirx, mc.group(1)))
# ---- AP PLC C24: placa plc/gen/make.py contra el mismo programa (tipo 7) ----
pk = open(os.path.join(R, "plc/gen/make.py"), encoding="utf-8").read()
m = re.search(r'\("U3", "ESP32-C3-WROOM-02".*?\{(".*?)\},\n', pk, re.S)
pl = {red: MODULO[pin] for pin, red in eval("{" + m.group(1) + "}").items() if red not in ("3V3", "GND", "EN", None)}
ESP_PLC = {"INT": "P_INT", "SENSE_I": "P_SENSE_I", "SENSE_O": "P_SENSE_O", "SCL": "P_SCL", "BOOT": "P_MODO", "RS_DE": "P_DE", "RS_RX": "P_RX",
           "SDA": "P_SDA", "RS_TX": "P_TX", "ETH_CS": "P_ETH_CS", "ETH_SCK": "P_ETH_SCK", "ETH_MISO": "P_ETH_MISO", "ETH_MOSI": "P_ETH_MOSI"}
for red, cte in ESP_PLC.items():
    if red not in pl: errores.append("PLC: la red %s no está en el módulo" % red); continue
    if cte not in cr: errores.append("PLC: el programa no define %s" % cte); continue
    if pl[red] != cr[cte]: errores.append("PLC %s: la placa usa IO%s y el programa IO%s (%s)" % (red, pl[red], cr[cte], cte))
for red, g in pl.items():
    if red not in ESP_PLC and red not in ("USB_DN", "USB_DP"): errores.append("PLC: red %s (IO%s) sin constante del programa" % (red, g))
if "VSENSE" in pl: errores.append("PLC: IO0 es el CS del W5500; no puede medir la tensión de entrada")
for ref, cte in (("U6", "TCA_S1"), ("U7", "TCA_S2"), ("U8", "TCA_ENT"), ("U9", "TCA_LED"), ("U15", "TCA_ENT2")):
    mt = re.search(r'tca\("%s", \("(\w+)", "(\w+)", "(\w+)"\)' % ref, pk)
    dirx = 0x20 + sum((1 << i) for i, v in enumerate(mt.groups()) if v == "3V3")
    mc = re.search(r"%s = (0x[0-9A-Fa-f]+)" % cte, rino)
    if int(mc.group(1), 16) != dirx: errores.append("PLC %s: la placa da 0x%02X y el programa %s" % (ref, dirx, mc.group(1)))
# la placa del W5500 debe usar las mismas redes SPI que el ESP32 y el RJ45 los 4 hilos del par
for red in ("ETH_CS", "ETH_SCK", "ETH_MISO", "ETH_MOSI"):
    if '"%s"' % red not in pk.split('("U16"')[1].split('("Y1"')[0]: errores.append("PLC: el W5500 no usa la red %s" % red)
# ---- AP PLC C24 rev B: placa plcb/gen/make.py (ESP32-S3-WROOM-1) contra los pines del bloque ESP32-S3 del programa ----
S3 = {"1": "GND", "2": "3V3", "3": "EN", "4": 4, "5": 5, "6": 6, "7": 7, "8": 15, "9": 16, "10": 17, "11": 18, "12": 8, "13": 19, "14": 20, "15": 3, "16": 46, "17": 9, "18": 10,
      "19": 11, "20": 12, "21": 13, "22": 14, "23": 21, "24": 47, "25": 48, "26": 45, "27": 0, "28": 35, "29": 36, "30": 37, "31": 38, "32": 39, "33": 40, "34": 41, "35": 42,
      "36": "RXD0", "37": "TXD0", "38": 2, "39": 1, "40": "GND", "41": "GND"}
pb = open(os.path.join(R, "plcb/gen/make.py"), encoding="utf-8").read()
m = re.search(r'\("U3", "ESP32-S3-WROOM-1".*?\{(".*?)\},\n', pb, re.S)
rb = {red: S3[pin] for pin, red in eval("{" + m.group(1) + "}").items() if red not in ("3V3", "GND", "EN", None)}
c3 = {a.group(1): int(a.group(2)) for a in re.finditer(r"(P_\w+)\s*=\s*(\d+)", bloque_s3)}
ESP_B = {"SENSE_I": "P_SENSE_I", "SENSE_O": "P_SENSE_O", "SCL": "P_SCL", "SDA": "P_SDA", "BOOT": "P_MODO", "RS_DE": "P_DE", "RS_RX": "P_RX", "RS_TX": "P_TX",
         "VSENSE": "P_VSENSE", "ETH_CS": "P_ETH_CS", "ETH_SCK": "P_ETH_SCK", "ETH_MISO": "P_ETH_MISO", "ETH_MOSI": "P_ETH_MOSI", "ETH_INT": "P_ETH_INT", "ETH_RST": "P_ETH_RST",
         "MB_RX": "P_MB_RX", "MB_TX": "P_MB_TX", "MB_DE": "P_MB_DE"}
for red, cte in ESP_B.items():
    if red not in rb: errores.append("PLC rev B: la red %s no está en el módulo" % red); continue
    if cte not in c3: errores.append("PLC rev B: el programa no define %s" % cte); continue
    if rb[red] != c3[cte]: errores.append("PLC rev B %s: la placa usa IO%s y el programa IO%s (%s)" % (red, rb[red], c3[cte], cte))
for red, g in rb.items():
    if red not in ESP_B and red not in ("USB_DN", "USB_DP"): errores.append("PLC rev B: red %s (IO%s) sin constante del programa" % (red, g))
if rb.get("USB_DN") != 19 or rb.get("USB_DP") != 20: errores.append("PLC rev B: el USB debe ir a IO19/IO20")
bad = [g for g in rb.values() if g in (3, 45, 46) or (isinstance(g, int) and 26 <= g <= 37)]
if bad: errores.append("PLC rev B: usa pines de arranque o de memoria: %s" % bad)
# IN16 y AI8: mismo ESP32 que el Rack 16, y las direcciones I2C que usa el programa para reconocer el tipo de módulo
for carpeta, tipo in (("in16", "IN16"), ("ai8", "AI8"), ("led8", "LED8"), ("rl4", "RL4"), ("ao4", "AO4")):
    mk2 = open(os.path.join(R, carpeta, "gen/make.py"), encoding="utf-8").read()
    if "importlib" not in mk2 or "rack16" not in mk2: errores.append("%s: no hereda las piezas del Rack 16" % tipo)
if True:
    m1 = re.search(r'B\.tca\("U6", \("(\w+)", "(\w+)", "(\w+)"\)', open(os.path.join(R, "in16/gen/make.py"), encoding="utf-8").read())
    m2 = re.search(r'B\.tca\("U7", \("(\w+)", "(\w+)", "(\w+)"\)', open(os.path.join(R, "in16/gen/make.py"), encoding="utf-8").read())
    d1 = 0x20 + sum((1 << i) for i, v in enumerate(m1.groups()) if v == "3V3"); d2 = 0x20 + sum((1 << i) for i, v in enumerate(m2.groups()) if v == "3V3")
    for cte, dirx in (("TCA_E1", d1), ("TCA_E2", d2)):
        mc = re.search(r"%s = (0x[0-9A-Fa-f]+)" % cte, rino)
        if int(mc.group(1), 16) != dirx: errores.append("IN16 %s: la placa da 0x%02X y el programa %s" % (cte, dirx, mc.group(1)))
    ai = open(os.path.join(R, "ai8/gen/make.py"), encoding="utf-8").read()
    for ref, cte, dirx in (("U6", "ADS_A", 0x48), ("U7", "ADS_B", 0x49)):
        mc = re.search(r"%s = (0x[0-9A-Fa-f]+)" % cte, rino)
        if int(mc.group(1), 16) != dirx: errores.append("AI8 %s: el programa usa %s" % (cte, mc.group(1)))
    if '("U6", "C15", "GND"' not in ai or '("U7", "C16", "3V3"' not in ai: errores.append("AI8: ADDR de los ADS1115 distinto de 0x48 (GND) y 0x49 (3V3)")
if open(os.path.join(R, "firmware/APLink/ap_link.h")).read() != open(os.path.join(R, "firmware/APRack/ap_link.h")).read():
    errores.append("firmware/APRack/ap_link.h no es copia de firmware/APLink/ap_link.h")
lk = open(os.path.join(R, "led8/gen/make.py"), encoding="utf-8").read()
mc = re.search(r"PCA_LED = (0x[0-9A-Fa-f]+)", rino)
if not mc or int(mc.group(1), 16) != 0x40: errores.append("LED8: el programa usa PCA_LED distinto de 0x40")
mp = re.search(r'"U6", "PCA9685PW".*?\{(.*?)\},\s*"PWM', lk, re.S)
if not mp: errores.append("LED8: no se encontró el PCA9685 en la placa")
else:
    pines = dict((a2, b2) for a2, b2 in re.findall(r'"(\d+)": ("?\w+"?)', mp.group(1)))
    if any(pines.get(str(k)) != '"GND"' for k in (1, 2, 3, 4, 5, 24)): errores.append("LED8: A0-A5 del PCA9685 no están todos a 0 V (dirección 0x40)")
    if any(pines.get(str(6 + k)) != '"IN%d"' % (k + 1) for k in range(8)): errores.append("LED8: las salidas LED0-LED7 no van a las compuertas IN1-IN8")
rl = open(os.path.join(R, "rl4/gen/make.py"), encoding="utf-8").read()
if '"U7"' not in rl.split("_quitar =")[1].split("\n")[0]: errores.append("RL4: debe quitar el expansor U7 (0x21): el programa reconoce el RL4 porque 0x21 no contesta")
if "TCA_S2 = 0x21" not in rino or "!existe(TCA_S2) ? T_RL4" not in rino: errores.append("RL4: el programa no lo reconoce por la ausencia del 0x21")
if '"A1": "V24", "A2": "Q%d" % k' not in rl: errores.append("RL4: la bobina de cada relé debe ir entre V24 y la salida Qk")
if "NREL = 4" not in rl: errores.append("RL4: el programa dice 4 salidas y la placa no")
ao = open(os.path.join(R, "ao4/gen/make.py"), encoding="utf-8").read()
mc = re.search(r"PCA_AO = (0x[0-9A-Fa-f]+)", rino)
mp = re.search(r'"U6", "PCA9685PW".*?\{(.*?)\},\s*"PWM', ao, re.S)
if not mc or not mp: errores.append("AO4: no se encontró el PCA9685 en la placa o PCA_AO en el programa")
else:
    pines = dict((a2, b2) for a2, b2 in re.findall(r'"(\d+)": ("?\w+"?)', mp.group(1)))
    dirx = 0x40 + sum((1 << i) for i, k in enumerate((1, 2, 3, 4, 5)) if pines.get(str(k)) == '"3V3"') + (0x20 if pines.get("24") == '"3V3"' else 0)
    if int(mc.group(1), 16) != dirx: errores.append("AO4: la placa da la dirección 0x%02X y el programa PCA_AO = %s" % (dirx, mc.group(1)))
    if dirx == 0x40: errores.append("AO4: debe distinguirse del LED8 (0x40) por la dirección del PCA9685")
    if any(pines.get(str(6 + k)) != '"PW%d"' % (k + 1) for k in range(4)): errores.append("AO4: LED0-LED3 no van a PW1-PW4")
for e in errores: print("  ERROR:", e)
print("Pines ESP32-C3 y direcciones I2C: placas (7R Tour, AP Rack 16, AP PLC C24 rev A y rev B, IN16, AI8, LED8, RL4 y AO4) y programas coinciden" if not errores else "Pines: %d errores" % len(errores))
sys.exit(1 if errores else 0)
