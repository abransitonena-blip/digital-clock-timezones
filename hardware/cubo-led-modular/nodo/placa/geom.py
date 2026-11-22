import math
from huellas import huella
import diseno as D

def rot(x, y, a):
    r = math.radians(a); return x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r)

def pads(p):
    lst, _ = huella(p["fp"]); out = []
    for pin, dx, dy, w, h, f, dr in lst:
        x, y = rot(dx, dy, p["rot"])
        if p["rot"] % 180: w, h = h, w
        out.append(dict(ref=p["ref"], pin=pin, net=p["nets"].get(pin, f"NC_{p['ref']}_{pin}"),
                        x=p["x"] + x, y=p["y"] + y, w=w, h=h, f=f, drill=dr))
    return out

def patio(p):                       # courtyard (rectángulo) absoluto; acepta (ancho, alto) centrado o (x0, y0, x1, y1)
    _, cy = huella(p["fp"])
    if len(cy) == 2: cy = (-cy[0] / 2, -cy[1] / 2, cy[0] / 2, cy[1] / 2)
    esq = [rot(x, y, p["rot"]) for x in (cy[0], cy[2]) for y in (cy[1], cy[3])]
    xs, ys = [p["x"] + a for a, b in esq], [p["y"] + b for a, b in esq]
    return (round(min(xs), 4), round(min(ys), 4), round(max(xs), 4), round(max(ys), 4))

def todos_pads(): return [q for p in D.P for q in pads(p)]

def contorno(n=24):                 # polígono del borde con muescas de esquina
    from shapely.geometry import box, Point
    b = box(-D.W / 2, -D.H / 2, D.W / 2, D.H / 2)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b = b.difference(Point(sx * D.ESQ_C, sy * D.ESQ_C).buffer(D.ESQ_R, n))
    return b
