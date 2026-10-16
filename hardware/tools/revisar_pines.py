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
# IN16 y AI8: mismo ESP32 que el Rack 16, y las direcciones I2C que usa el programa para reconocer el tipo de módulo
for carpeta, tipo in (("in16", "IN16"), ("ai8", "AI8"), ("led8", "LED8"), ("rl4", "RL4")):
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
for e in errores: print("  ERROR:", e)
print("Pines ESP32-C3 y direcciones I2C: placas (7R Tour, AP Rack 16, IN16, AI8, LED8 y RL4) y programas coinciden" if not errores else "Pines: %d errores" % len(errores))
sys.exit(1 if errores else 0)
