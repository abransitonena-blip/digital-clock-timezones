"""SVG de colocación y de capas. Uso: python3.11 vista.py colocacion|top|bottom|completa  -> vista_*.svg"""
import sys, json, os, html
import diseno as D, geom as G
S = 12  # px por mm
def X(x): return (x + D.W / 2 + 2) * S
def Y(y): return (D.H / 2 + 2 - y) * S
def svg_ini(): return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{(D.W+4)*S}" height="{(D.H+4)*S}" viewBox="0 0 {(D.W+4)*S} {(D.H+4)*S}" font-family="DejaVu Sans,Arial">']
def poly(g, color, op=1.0, extra=""):
    out = []
    geoms = getattr(g, "geoms", [g])
    for p in geoms:
        if p.is_empty: continue
        d = ""
        for ring in [p.exterior, *p.interiors]:
            d += "M" + " L".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in ring.coords) + "Z"
        out.append(f'<path d="{d}" fill="{color}" fill-opacity="{op}" fill-rule="evenodd" {extra}/>')
    return "".join(out)
def pad_svg(q, color):
    if q["f"] == "c": s = f'<circle cx="{X(q["x"]):.1f}" cy="{Y(q["y"]):.1f}" r="{q["w"]/2*S:.1f}" fill="{color}"/>'
    else: s = f'<rect x="{X(q["x"]-q["w"]/2):.1f}" y="{Y(q["y"]+q["h"]/2):.1f}" width="{q["w"]*S:.1f}" height="{q["h"]*S:.1f}" fill="{color}"/>'
    if q["drill"]: s += f'<circle cx="{X(q["x"]):.1f}" cy="{Y(q["y"]):.1f}" r="{q["drill"]/2*S:.1f}" fill="#111"/>'
    return s
def colocacion():
    o = svg_ini(); o.append(f'<rect width="100%" height="100%" fill="#fff"/>')
    o.append(poly(G.contorno(), "#1d5c3a"))
    if D.ANTENA: x0, y0, x1, y1 = D.ANTENA; o.append(f'<rect x="{X(x0)}" y="{Y(y1)}" width="{(x1-x0)*S}" height="{(y1-y0)*S}" fill="#f5d76e" opacity=".5"/>')
    for h in D.BARRENOS: o.append(f'<circle cx="{X(h[0])}" cy="{Y(h[1])}" r="{1.6*S}" fill="#fff"/><circle cx="{X(h[0])}" cy="{Y(h[1])}" r="{3.3*S}" fill="none" stroke="#fff" stroke-dasharray="4 3"/>')
    for p in D.P:
        x0, y0, x1, y1 = G.patio(p)
        o.append(f'<rect x="{X(x0)}" y="{Y(y1)}" width="{(x1-x0)*S}" height="{(y1-y0)*S}" fill="none" stroke="#e8e8e8" stroke-width="1"/>')
        for q in G.pads(p): o.append(pad_svg(q, "#d9a441"))
        o.append(f'<text x="{X(p["x"])}" y="{Y(p["y"])+4}" font-size="{11 if len(p["ref"])<4 else 9}" fill="#fff" text-anchor="middle" font-weight="bold">{p["ref"]}</text>')
    o.append("</svg>"); return "\n".join(o)

def capas(cobre, vias, titulo="", solo=None):
    """Vista de cobre: capa superior en rojo/cobre, inferior en azul, vias y serigrafía de referencias."""
    o = svg_ini(); o.append('<rect width="100%" height="100%" fill="#0e1a14"/>')
    o.append(poly(G.contorno(), "#163d2a"))
    colores = {0: "#d9822b", 1: "#3b82c4"}
    for l in ((1, 0) if solo is None else (solo,)):
        for n, g, t in cobre[l]:
            op = 0.55 if t == "plano" else (0.85 if l == 1 else 0.95)
            col = colores[l] if n != "GND" or t != "plano" else ("#7a4a1c" if l == 0 else "#1f4a73")
            o.append(poly(g, col, op))
    for x, y, n in vias:
        o.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{0.3*S:.1f}" fill="#ccc"/><circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{0.15*S:.1f}" fill="#111"/>')
    for p in D.P:
        for q in G.pads(p):
            if q["drill"]: o.append(f'<circle cx="{X(q["x"]):.1f}" cy="{Y(q["y"]):.1f}" r="{q["drill"]/2*S:.1f}" fill="#111"/>')
        o.append(f'<text x="{X(p["x"])}" y="{Y(p["y"])+4}" font-size="10" fill="#fff" fill-opacity=".85" text-anchor="middle">{p["ref"]}</text>')
    for h in D.BARRENOS: o.append(f'<circle cx="{X(h[0])}" cy="{Y(h[1])}" r="{1.6*S}" fill="#0e1a14"/>')
    if titulo: o.append(f'<text x="10" y="18" font-size="14" fill="#fff">{titulo}</text>')
    o.append("</svg>"); return "\n".join(o)

def realista(cobre, vias, silk, capa=0):
    """Cómo se verá la placa fabricada: máscara verde, cobre bajo la máscara, pads dorados, serigrafía blanca."""
    import fab
    from shapely.ops import unary_union
    o = svg_ini(); o.append('<rect width="100%" height="100%" fill="#f2f2ee"/>')
    o.append(poly(G.contorno(), "#0b5d36"))
    cu = unary_union([g for n, g, t in cobre[capa]])
    o.append(poly(cu, "#12804b", 1.0))
    pads = G.todos_pads()
    abiertos = unary_union([fab.pad_geo(q) for q in pads if capa == 0 or q["drill"]])
    o.append(poly(abiertos, "#d8b25a"))
    if capa == 0: o.append(poly(silk, "#ffffff"))
    for x, y, n in vias: o.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{0.15*S:.1f}" fill="#1a1a1a"/>')
    for q in pads:
        if q["drill"]: o.append(f'<circle cx="{X(q["x"]):.1f}" cy="{Y(q["y"]):.1f}" r="{q["drill"]/2*S:.1f}" fill="#1a1a1a"/>')
    for h in D.BARRENOS: o.append(f'<circle cx="{X(h[0])}" cy="{Y(h[1])}" r="{1.6*S}" fill="#f2f2ee"/>')
    o.append("</svg>")
    s = "\n".join(o)
    if capa == 1:   # vista desde abajo: espejo horizontal
        s = s.replace('font-family="DejaVu Sans,Arial">', f'font-family="DejaVu Sans,Arial"><g transform="translate({(D.W+4)*S},0) scale(-1,1)">', 1).replace("</svg>", "</g></svg>")
    return s

def generar_todo():
    import fab, json, shapely
    cobre = fab.cargar_cobre(); r = json.load(open("ruteo.json"))
    silk = shapely.from_wkb(open("serigrafia.wkb.hex").read())
    salidas = {"vista_colocacion.svg": colocacion(), "vista_placa_arriba.svg": realista(cobre, r["vias"], silk, 0),
               "vista_placa_abajo.svg": realista(cobre, r["vias"], silk, 1),
               "vista_cobre_arriba.svg": capas(cobre, r["vias"], "Capa superior (vista desde arriba)", 0),
               "vista_cobre_abajo.svg": capas(cobre, r["vias"], "Capa inferior: plano de GND (vista desde arriba, a través de la placa)", 1)}
    for k, v in salidas.items(): open(k, "w").write(v)
    return list(salidas)

if __name__ == "__main__":
    print(generar_todo())
