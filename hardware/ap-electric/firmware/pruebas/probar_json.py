#!/usr/bin/env python3
"""Revisa los JSON que genera prueba_json.cpp: válidos y con la forma que usa la consola (api 2)."""
import json, sys
def fallo(m):
    print("  falla:", m); sys.exit(1)
def revisa(ruta, n, ne, rs485):
    j = json.load(open(ruta))
    for k in ("v", "placa", "n", "ne", "s", "e", "b", "fz", "f", "fn", "man", "arr", "carga", "mb", "pk", "api", "cap", "cfg", "plc", "id", "t"):
        if k not in j: fallo("%s: falta «%s»" % (ruta, k))
    if j["api"] != 2: fallo("api")
    if j["n"] != n or j["ne"] != ne: fallo("%s: n/ne = %s/%s" % (ruta, j["n"], j["ne"]))
    for k in ("man", "arr", "carga"):
        if len(j[k]) != n: fallo("%s: longitud de %s" % (ruta, k))
    c = j["cfg"]
    if len(c["pul"]) != n or len(c["acc"]) != n or len(c["ent"]) != ne or any(len(e) != 3 for e in c["ent"]) or len(c["mon"]) != 4: fallo("%s: cfg incompleta" % ruta)
    for k in ("dir", "bps", "par", "vig", "ok", "mal"):
        if k not in j["mb"]: fallo("mb.%s" % k)
    for k in ("e", "m", "r", "n", "d", "disp", "des", "cal", "oee", "mp", "rem", "h", "hv"):
        if k not in j["pk"]: fallo("pk.%s" % k)
    for base in ("salidas", "entradas", "packml", "plc", "modbus_esclavo"):
        if base not in j["cap"]: fallo("cap " + base)
    for extra in ("rs485", "rtc", "conteo_rapido", "autoprueba"):
        if (extra in j["cap"]) != rs485: fallo("%s: cap %s inesperada o ausente" % (ruta, extra))
    if not isinstance(j["fn"], list): fallo("fn")
    return j
a = revisa("/tmp/json_7r.txt", 7, 8, True)
b = revisa("/tmp/json_7r_falla.txt", 7, 8, True)
if b["s"] != 5 or b["e"] != 3 or b["b"] != 5: fallo("estado de salidas/entradas")
if not b["f"] or "bobina sin tensión" not in b["fn"] or "comunicación perdida" not in b["fn"]: fallo("nombres de falla: %s" % b["fn"])
if b["pk"]["e"] not in (3, 4, 6, 15): fallo("estado PackML %s" % b["pk"]["e"])
c = revisa("/tmp/json_home.txt", 1, 1, False)
if c["placa"] != "AP Home": fallo("placa Home")
print("JSON del equipo: válido y con la forma esperada")
