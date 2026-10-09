"""Base de datos: capacitor X2 según color y cantidad de LED, para 3 niveles de brillo.
Red 127 V / 60 Hz. I = 4·f·C·(Vpico − 1.4 − Vcarga). LED de 5 mm y 3 mm."""
import math, csv, json, itertools

VAC, HZ, ALTA = 127, 60, 1.10
E12 = [0.1, 0.12, 0.15, 0.18, 0.22, 0.27, 0.33, 0.39, 0.47, 0.56, 0.68, 0.82, 1.0, 1.2, 1.5]
# Hoja de datos típica de LED de 5 mm a 20 mA (varía por marca)
LED = [  # color, nm, Vf mín, típ, máx, mcd, nota
    ("Rojo",              "620–630",  1.8, 2.0, 2.3, "1 500–8 000",   "alto brillo a 20 mA ≈ 2.0–2.3 V"),
    ("Naranja",           "600–610",  1.8, 2.0, 2.3, "2 000–8 000",   ""),
    ("Amarillo",          "585–595",  1.8, 2.1, 2.4, "2 000–8 000",   ""),
    ("Verde limón (GaP)", "565–575",  2.0, 2.2, 2.6, "100–1 000",     "verde claro, poco brillo"),
    ("Verde esmeralda",   "515–530",  2.9, 3.1, 3.4, "8 000–20 000",  "verde intenso (InGaN)"),
    ("Azul",              "460–470",  2.9, 3.1, 3.4, "3 000–8 000",   ""),
    ("Blanco frío",       "6000–7000 K", 2.9, 3.1, 3.4, "10 000–25 000", ""),
    ("Blanco cálido",     "2700–3500 K", 2.9, 3.1, 3.4, "8 000–18 000",  ""),
    ("Rosa",              "chip azul + fósforo", 2.9, 3.1, 3.4, "3 000–8 000", ""),
    ("Violeta / UV",      "395–405",  3.0, 3.3, 3.7, "500–2 000",     "no mirar de frente"),
]
NS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 18, 20, 25, 30, 35, 40]
Z = [(12,"1N5349B"),(15,"1N5352B"),(18,"1N5355B"),(20,"1N5357B"),(22,"1N5358B"),(24,"1N5359B"),(27,"1N5361B"),
     (30,"1N5363B"),(36,"1N5365B"),(39,"1N5366B"),(43,"1N5367B"),(47,"1N5368B"),(51,"1N5369B"),(56,"1N5370B"),
     (62,"1N5372B"),(68,"1N5373B"),(75,"1N5374B"),(82,"1N5375B"),(91,"1N5377B"),(100,"1N5378B"),(110,"1N5379B"),
     (120,"1N5380B"),(130,"1N5381B"),(150,"1N5383B")]
EXTRA_V3 = 3.8   # LED testigo + 100 Ω de la versión 3
NIVELES = [("bajo", 10), ("medio", 15), ("alto", 20)]

def I(c, vac, vo): return max(0.0, 4*HZ*c*1e-6*(vac*math.sqrt(2) - 1.4 - vo))*1000
def code(u):
    pf = round(u*1e6); e = 0
    while pf >= 100: pf /= 10; e += 1
    return f"{round(pf)}{e}"
def nombre(cs): return " + ".join(code(c) for c in cs)
def elegir(vo, meta, opciones):
    tope = meta*1.2   # con la red alta no pasa de +20 % de la meta (24 mA en alto; LED aguanta 30)
    ok = [cs for cs in opciones if I(sum(cs), VAC*ALTA, vo) <= tope]
    return min(ok, key=lambda cs: (abs(I(sum(cs), VAC, vo) - meta), len(cs))) if ok else None

SOLOS = [(c,) for c in E12]
PARES = SOLOS + [p for p in itertools.combinations_with_replacement(E12, 2) if sum(p) <= 1.6]

rows = []
for color, nm, vmin, vf, vmax, mcd, nota in LED:
    for n in NS:
        vo = n*vf + EXTRA_V3
        z = next((z for z in Z if z[0] >= 1.15*(n*vmax + 4.2)), None)
        if vo > 125 or z is None: continue
        r = dict(color=color, vf=vf, n=n, v_total=round(n*vf, 1))
        for niv, meta in NIVELES:
            cs = elegir(vo, meta, SOLOS)
            r[f"cap_{niv}"] = code(cs[0]); r[f"uf_{niv}"] = cs[0]
            r[f"ma_{niv}"] = round(I(cs[0], VAC, vo), 1)
        cs = elegir(vo, 20, SOLOS)
        r["ma_alto_red_alta"] = round(I(cs[0], VAC*ALTA, vo), 1)
        r["ma_alto_v1v2"] = round(I(cs[0], VAC, n*vf), 1)
        pr = elegir(vo, 20, PARES)
        r["exacto_20mA"] = nombre(pr); r["ma_exacto"] = round(I(sum(pr), VAC, vo), 1)
        r["zener_v3"] = f"{z[1]} ({z[0]} V)"
        r["watts_led"] = round(n*vf*r["ma_alto"]/1000, 2)
        rows.append(r)
for i, r in enumerate(rows, 1): r["id"] = i
campos = ["id"] + [k for k in rows[0] if k != "id"]
with open("base_datos_capacitores_led.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=campos); w.writeheader(); w.writerows(rows)
VS = [5, 10, 15, 20, 30, 40, 50, 60, 75, 90, 105, 120]
json.dump(dict(rows=rows, leds=LED, ns=NS, vs=VS,
               inversa=[[code(c), c] + [round(I(c, VAC, v), 1) for v in VS] for c in E12]),
          open("datos.json", "w"), ensure_ascii=False)
print(len(rows), "filas")
