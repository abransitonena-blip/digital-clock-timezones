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
for e in errores: print("  ERROR:", e)
print("Pines ESP32-C3: placa y programa coinciden" if not errores else "Pines: %d errores" % len(errores))
sys.exit(1 if errores else 0)
