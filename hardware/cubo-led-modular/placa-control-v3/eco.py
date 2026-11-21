"""Cambio de ingeniería sobre una placa ya ruteada: conserva el ruteo guardado y rehace solo lo afectado.
Quita pistas y vias de redes que ya no existen o que chocan con pads cuyo cableado cambió, y vuelve a conectar.
Uso: python3.11 eco.py  (después: reparar.py si queda algo abierto)"""
import json, shapely
import fab
P = fab.Placa()                                         # pads, zonas y pistas fijas del diseño actual
redes = {q["net"] for q in P.pads}
fijo = [[c for c in capa] for capa in P.cobre]          # lo que pone el diseño
viejo = fab.cargar_cobre()
ru = json.load(open("ruteo.json"))
quitadas = set()
pads_l = [[(q["net"], q["g"]) for q in P.pads if l == 0 or q["drill"]] for l in (0, 1)]
for l in (0, 1):
    for n, g, t in viejo[l]:
        if t not in ("pista", "via"): continue
        if n not in redes or any(m != n and g.distance(pg) < fab.CLR - 0.005 for m, pg in pads_l[l]):
            quitadas.add(n); continue
        fijo[l].append((n, g, t))
P.cobre = fijo
P.vias = [tuple(v) for v in ru["vias"] if v[2] in redes and not any(
    m != v[2] and shapely.geometry.Point(v[0], v[1]).buffer(fab.VIA_D / 2).distance(pg) < fab.CLR for m, pg in pads_l[0] + pads_l[1])]
vset = {(round(x, 3), round(y, 3)) for x, y, _ in P.vias}
P.cobre = [[c for c in capa if c[2] != "via" or (round(c[1].centroid.x, 3), round(c[1].centroid.y, 3)) in vset] for capa in P.cobre]
P.pistas = [p for p in ru["pistas"] if p["red"] in redes and p["red"] not in quitadas or p.get("fija")]
P.repintar()
print("redes con cobre quitado:", sorted(quitadas))
abiertas = [n for n in sorted(redes - {"GND"}) if not n.startswith("NC") and len(P.islas(n)) > 1]
print("a reconectar:", abiertas)
for n in abiertas: print("  ", n, "ok" if P.conectar_red(n) else "FALLA")
json.dump(dict(pistas=P.pistas, vias=P.vias), open("ruteo.json", "w"), indent=0); fab.guardar_cobre(P.cobre)
