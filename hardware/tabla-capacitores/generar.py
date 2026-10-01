"""Base de datos: capacitor X2 (fuente capacitiva) según tipo y cantidad de LED.
Red 127 V / 60 Hz. Fórmula: I = 4·f·C·(Vpico − 1.4 − Vcarga)."""
import math, csv, json

VAC, HZ, ALTA = 127, 60, 1.10
CAPS = [0.1, 0.15, 0.22, 0.27, 0.33, 0.39, 0.47, 0.56, 0.68, 0.82, 1.0, 1.2]
LED = [  # (color, Vf típico, Vf máximo, nota)
    ("Rojo", 2.0, 2.4, ""), ("Naranja", 2.0, 2.4, ""), ("Amarillo", 2.1, 2.4, ""),
    ("Verde limón (GaP)", 2.2, 2.6, "verde claro, poco brillo"),
    ("Verde brillante", 3.1, 3.4, "verde intenso"), ("Azul", 3.1, 3.4, ""),
    ("Blanco", 3.1, 3.4, "blanco frío o cálido"), ("Rosa", 3.1, 3.4, ""),
    ("Violeta / UV", 3.3, 3.7, ""),
]
NS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 18, 20, 25, 30, 35, 40]
Z = [(12,"1N5349B"),(15,"1N5352B"),(18,"1N5355B"),(20,"1N5357B"),(22,"1N5358B"),(24,"1N5359B"),(27,"1N5361B"),
     (30,"1N5363B"),(36,"1N5365B"),(39,"1N5366B"),(43,"1N5367B"),(47,"1N5368B"),(51,"1N5369B"),(56,"1N5370B"),
     (62,"1N5372B"),(68,"1N5373B"),(75,"1N5374B"),(82,"1N5375B"),(91,"1N5377B"),(100,"1N5378B"),(110,"1N5379B"),
     (120,"1N5380B"),(130,"1N5381B"),(150,"1N5383B")]
EXTRA = 3.8          # LED testigo + resistencia de 100 Ω (versión 3)
NORMAL, VIDA = 21.5, 16.0   # mA máximos con la red alta (+10 %)

def I(c, vac, vo): return max(0.0, 4*HZ*c*1e-6*(vac*math.sqrt(2) - 1.4 - vo))*1000
def code(u):
    pf = round(u*1e6); e = 0
    while pf >= 100: pf /= 10; e += 1
    return f"{round(pf)}{e}J"
def pick(vo, lim):
    ok = [c for c in CAPS if I(c, VAC*ALTA, vo) <= lim]
    return ok[-1] if ok else None

rows = []
rid = 1
for color, vf, vfm, nota in LED:
    for n in NS:
        vo = n*vf + EXTRA
        z = next((z for z in Z if z[0] >= 1.15*(n*vfm + 4.2)), None)
        if vo > 125 or z is None: continue
        cn, cv = pick(vo, NORMAL), pick(vo, VIDA)
        rows.append(dict(id=rid, color=color, vf=vf, n=n, v_total=round(n*vf, 1),
            cap_normal=code(cn), uf_normal=cn, ma_normal=round(I(cn, VAC, vo), 1), ma_alta=round(I(cn, VAC*ALTA, vo), 1),
            cap_vida=code(cv), ma_vida=round(I(cv, VAC, vo), 1), zener=f"{z[1]} ({z[0]} V)",
            watts=round(n*vf*I(cn, VAC, vo)/1000, 2), nota=nota))
        rid += 1

with open("tabla_capacitores.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
import os
json.dump(dict(rows=rows, leds=LED, ns=NS, caps=[(code(c), c) for c in CAPS],
               inversa=[[code(c), c] + [round(I(c, VAC, v), 1) for v in (10, 25, 50, 75, 100)] for c in CAPS]),
          open("datos.json", "w"), ensure_ascii=False)
print(len(rows), "filas")
