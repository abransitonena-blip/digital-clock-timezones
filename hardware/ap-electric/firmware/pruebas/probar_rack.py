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
print("JSON de AP Rack: válido y con la forma esperada")
