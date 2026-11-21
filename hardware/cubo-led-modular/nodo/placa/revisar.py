"""Revisa la colocación: patios que se enciman, partes fuera del borde, redes con un solo pin."""
import itertools, collections
from shapely.geometry import box, Point
import diseno as D, geom as G
ok = True
borde = G.contorno()
cy = {p["ref"]: box(*G.patio(p)) for p in D.P}
for a, b in itertools.combinations(D.P, 2):
    i = cy[a["ref"]].intersection(cy[b["ref"]]).area
    if i > 0.05 and not ({a["ref"], b["ref"]} & {"U3"} and min(a["fp"], b["fp"]) == "TP"):
        print(f"ENCIME {a['ref']}–{b['ref']}  {i:.2f} mm²"); ok = False
for p in D.P:
    if not p["fp"].startswith("BORNE") and p["fp"] != "SUPERMINI" and not borde.buffer(-0.3).contains(cy[p["ref"]]): print("FUERA/BORDE", p["ref"]); ok = False
    for h in D.BARRENOS:
        if cy[p["ref"]].distance(Point(h)) < 3.3: print("BARRENO", p["ref"]); ok = False
import fab
pads = G.todos_pads()
for q in pads: q["g"] = fab.pad_geo(q)
for a, b in itertools.combinations(pads, 2):
    if a["net"] != b["net"] and a["g"].distance(b["g"]) < 0.19 and (a["drill"] or b["drill"] or True):
        print(f"PADS {a['ref']}.{a['pin']}–{b['ref']}.{b['pin']} a {a['g'].distance(b['g']):.2f} mm"); ok = False
nets = collections.defaultdict(list)
for q in G.todos_pads(): nets[q["net"]].append(q["ref"] + "." + q["pin"])
for n, l in sorted(nets.items()):
    if len(l) < 2 and not n.startswith("NC"): print("RED DE 1 PIN", n, l); ok = False
print("redes:", len([n for n in nets if not n.startswith("NC")]), "pads:", sum(map(len, nets.values())), "OK" if ok else "")
