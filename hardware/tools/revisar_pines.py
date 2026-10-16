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
if open(os.path.join(R, "firmware/APLink/ap_link.h")).read() != open(os.path.join(R, "firmware/APRack/ap_link.h")).read():
    errores.append("firmware/APRack/ap_link.h no es copia de firmware/APLink/ap_link.h")
for e in errores: print("  ERROR:", e)
print("Pines ESP32-C3: placas (7R Tour y AP Rack 16) y programas coinciden" if not errores else "Pines: %d errores" % len(errores))
sys.exit(1 if errores else 0)
