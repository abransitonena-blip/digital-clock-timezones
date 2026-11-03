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

def patio(p):                       # courtyard (rectángulo) absoluto
    _, (cw, ch) = huella(p["fp"])
    if p["rot"] % 180: cw, ch = ch, cw
    return (p["x"] - cw / 2, p["y"] - ch / 2, p["x"] + cw / 2, p["y"] + ch / 2)

def todos_pads(): return [q for p in D.P for q in pads(p)]

def contorno(n=24):                 # polígono del borde con muescas de esquina
    from shapely.geometry import box, Point
    b = box(-D.W / 2, -D.H / 2, D.W / 2, D.H / 2)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b = b.difference(Point(sx * D.ESQ_C, sy * D.ESQ_C).buffer(D.ESQ_R, n))
    return b
