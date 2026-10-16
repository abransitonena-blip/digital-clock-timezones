#!/usr/bin/env python3
"""Regenera la tabla de LEEME.md a partir de catalogo.json (python3 accesorios.py primero)."""
import json, os, re
H = os.path.dirname(os.path.abspath(__file__))
c = json.load(open(os.path.join(H, "catalogo.json")))
rows = "\n".join("| %s | `%s` | %s | %s | %s × %s × %s | %s |" % (p["sku"], p["archivo"], p["funcion"], p["material"], *p["dimensiones_mm"], p["nota"]) for p in c["imprimibles"])
ref = "\n".join("| %s | `%s` | %s |" % (r["sku"], r["archivo"], r["funcion"]) for r in c["referencias"])
t = open(os.path.join(H, "LEEME.md"), encoding="utf-8").read()
t = re.sub(r"(\| SKU \| Archivo \| Función \| Material sugerido \| Medidas \(mm\) \| Nota \|\n\|---\|---\|---\|---\|---\|---\|\n).*?(\n\n## Modelos)", lambda m: m.group(1) + rows + m.group(2), t, flags=re.S)
t = re.sub(r"(\| SKU \| Archivo \| Qué es \|\n\|---\|---\|---\|\n).*?(\n\n## Lo que falta)", lambda m: m.group(1) + ref + m.group(2), t, flags=re.S)
t = re.sub(r"\d+ piezas imprimibles", "%d piezas imprimibles" % len(c["imprimibles"]), t)
open(os.path.join(H, "LEEME.md"), "w", encoding="utf-8").write(t)
print("LEEME.md:", len(c["imprimibles"]), "piezas")
