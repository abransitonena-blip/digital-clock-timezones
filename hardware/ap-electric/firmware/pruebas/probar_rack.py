#!/usr/bin/env python3
"""Revisa los JSON que genera prueba_rack.cpp: válidos y con la forma que usa la consola (api 2 con módulos)."""
import json, sys
def fallo(m):
    print("  falla:", m); sys.exit(1)
def revisa(ruta, total, rol):
    j = json.load(open(ruta))
    for k in ("v", "placa", "api", "cap", "rol", "pos", "total", "n", "ne", "mods", "id", "t", "enl"):
        if k not in j: fallo("%s: falta «%s»" % (ruta, k))
    if j["api"] != 2 or j["rol"] != rol: fallo("%s: api o rol" % ruta)
    for c in ("salidas", "entradas", "aplink", "modulos"):
        if c not in j["cap"]: fallo("cap " + c)
    if j["total"] != total: fallo("%s: total %s" % (ruta, j["total"]))
    for m in j["mods"]:
        for k in ("p", "id", "tp", "ns", "ne", "s", "e", "v", "f", "ok", "seg"):
            if k not in m: fallo("%s: módulo sin «%s»" % (ruta, k))
        if not (0 <= m["s"] <= 0xFFFF and 0 <= m["e"] <= 0xFF * 256 + 255): fallo("máscaras fuera de rango")
    return j
a = revisa("/tmp/json_rack_2mod.txt", 2, "cabeza")
if [m["p"] for m in a["mods"]] != [1, 2] or a["n"] != 32 or a["ne"] != 16: fallo("módulos del cabeza: %s" % a["mods"])
if a["mods"][0]["s"] != 5 or a["mods"][1]["s"] != 0x00F0 or a["mods"][1]["e"] != 0x42: fallo("estados de los módulos: %s" % a["mods"])
if a["mods"][1]["v"] != 24000 or a["mods"][0]["id"] == a["mods"][1]["id"]: fallo("tensión o id")
b = revisa("/tmp/json_rack_esclavo.txt", 2, "esclavo")
if len(b["mods"]) != 1 or b["pos"] != 2 or b["n"] != 16: fallo("JSON del esclavo")
c = revisa("/tmp/json_rack_3mod.txt", 3, "cabeza")
if len(c["mods"]) != 3 or c["n"] != 48 or c["ne"] != 24: fallo("3 módulos")
d = revisa("/tmp/json_rack_3tipos.txt", 3, "cabeza")
tipos = [m["tp"] for m in d["mods"]]
if tipos != [1, 2, 3]: fallo("tipos de módulo %s" % tipos)
if d["n"] != 16 or d["ne"] != 24: fallo("totales 3 tipos: n=%s ne=%s" % (d["n"], d["ne"]))
ai = d["mods"][2]
if ai["na"] != 8 or len(ai["a"]) != 8 or ai["a"][0] != 6200 or ai["a"][7] != 20000 or ai["am"] != 128: fallo("analógicas del AI8: %s" % ai)
if d["mods"][1]["e"] != 0x8001: fallo("entradas del IN16")
p = revisa("/tmp/json_rack_plc.txt", 3, "cabeza")
if "plc" not in p["cap"] or "plc" not in p: fallo("falta el estado del PLC")
for k in ("run", "n", "err", "ciclos", "m", "r", "t", "c"):
    if k not in p["plc"]: fallo("plc.%s" % k)
if len(p["plc"]["r"]) != 16 or len(p["plc"]["t"]) != 16 or len(p["plc"]["c"]) != 16: fallo("tamaños de r/t/c")
print("JSON de AP Rack: válido y con la forma esperada")
