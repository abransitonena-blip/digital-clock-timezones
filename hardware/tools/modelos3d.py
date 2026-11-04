"""Descarga los modelos 3D (STEP) de KiCad 9 que usan las huellas de un proyecto: python3 tools/modelos3d.py <carpeta_kicad>"""
import os, re, sys, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "fuente-os-127v", "gen"))
URL = "https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/9.0.0/%s.3dshapes/%s.step"
SRC = {}
for line in open(os.path.join(os.path.dirname(__file__), "..", "fuente-os-127v", "gen", "comun.py")).read().split("\n"):
    for m in re.finditer(r'"([A-Za-z_]+(?:\.[0-9A-Za-z]+)?[A-Za-z0-9_,.\-]*)/([^"]+)"\)', line):
        SRC[m.group(2)] = m.group(1)
SRC.update({"PinSocket_1x15_P2.54mm_Vertical": "Connector_PinSocket_2.54mm"})
ki = sys.argv[1]
d3 = os.path.join(ki, "3d")
os.makedirs(d3, exist_ok=True)
need = set()
for f in os.listdir(next(os.path.join(ki, x) for x in os.listdir(ki) if x.endswith(".pretty"))):
    s = open(os.path.join(ki, [x for x in os.listdir(ki) if x.endswith(".pretty")][0], f)).read()
    need |= set(re.findall(r'\$\{KIPRJMOD\}/3d/([^"]+)\.step', s))
for m in sorted(need):
    out = os.path.join(d3, m + ".step")
    if os.path.exists(out) and os.path.getsize(out) > 5000:
        continue
    lib = SRC.get(m)
    if not lib:
        print("sin origen:", m); continue
    r = subprocess.run(["curl", "-sS", "-f", "-o", out, URL % (lib, m)], capture_output=True)
    print(("ok  " if r.returncode == 0 else "FALLA ") + m)
    if r.returncode:
        os.path.exists(out) and os.remove(out)
