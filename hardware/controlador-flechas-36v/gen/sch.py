"""Genera el esquema KiCad 9 (.kicad_sch) a partir de design.py.

Estilo: cada pin tiene un tramo corto de cable con etiqueta de red (o símbolo
de alimentación). Los bloques funcionales se enmarcan y se titulan.
"""
import os, sys, uuid, math, datetime
sys.path.insert(0, os.path.dirname(__file__))
from sexpr import parse, dump, Sym, find, find1
import design as DZ

KSYM = os.environ.get("KICAD_SYM", "/usr/share/kicad/symbols")
PROJECT = "ControladorFlechas"
ROOT_UUID = "6f1c1e2a-3b4d-4c5e-8f60-7a8b9c0d1e2f"
STUB = 2.54
NS = uuid.UUID("0b6a6d2e-5a0f-4f53-9d6e-3f1a2b4c5d6e")  # mismo espacio que pcbgen.py


def U():
    return str(uuid.uuid4())


def S(*a):
    return [Sym(a[0])] + list(a[1:])


_libcache = {}


def lib_symbol(lib_id):
    lib, name = lib_id.split(":")
    if lib not in _libcache:
        t = parse(open(os.path.join(KSYM, lib + ".kicad_sym")).read())
        _libcache[lib] = {s[1]: s for s in find(t, "symbol")}
    syms = _libcache[lib]
    s = syms[name]
    ext = find1(s, "extends")
    if ext:
        parent = syms[ext[1]]
        body = [x for x in parent if not (isinstance(x, list) and x and x[0] in ("property",))]
        props = [x for x in s if isinstance(x, list) and x and x[0] == "property"]
        out = [Sym("symbol"), lib_id]
        for x in body[2:]:
            if isinstance(x, list) and x and x[0] == "symbol":
                x = list(x)
                x[1] = x[1].replace(ext[1], name, 1)
            out.append(x)
        # insertar propiedades antes de los sub-símbolos
        idx = next(i for i, x in enumerate(out) if isinstance(x, list) and x and x[0] == "symbol")
        out = out[:idx] + props + out[idx:]
        return out
    out = list(s)
    out[1] = lib_id
    return out


def pins_of(libsym):
    pins = {}

    def walk(e):
        for x in e:
            if isinstance(x, list) and x:
                if x[0] == "pin":
                    at = find1(x, "at")
                    pins[find1(x, "number")[1]] = (float(at[1]), float(at[2]), float(at[3]), str(x[1]))
                else:
                    walk(x)
    walk(libsym)
    return pins


def rot(x, y, th):
    c, s = round(math.cos(math.radians(th))), round(math.sin(math.radians(th)))
    return x * c - y * s, x * s + y * c


def g(v):
    return round(v / 1.27) * 1.27


class Sheet:
    def __init__(self):
        self.items = []
        self.libs = {}
        self.pwr_n = 0
        self.flg_n = 0

    def use(self, lib_id):
        if lib_id not in self.libs:
            self.libs[lib_id] = lib_symbol(lib_id)
        return self.libs[lib_id]

    def symbol(self, lib_id, ref, val, x, y, th, fp="", dnp=False, props_extra=None, hide_ref=False, hide_val=False,
               in_bom=True, desc="", bom=True):
        ls = self.use(lib_id)
        pins = pins_of(ls)
        pp = [(x + rot(px, py, th)[0], y - rot(px, py, th)[1]) for (px, py, pa, pt) in pins.values()]
        fa = 0
        if len(pins) == 2 and abs(pp[0][1] - pp[1][1]) < 0.1:      # 2 pines, horizontal
            mx = min(p[0] for p in pp)
            rx, ry, vx, vy = mx + 2.0, y - 3.2, mx + 2.0, y + 4.4
            if lib_id == "Switch:SW_DIP_x01":
                ry, vy = y - 4.5, y + 5.5
        elif len(pins) <= 2:                                          # 2 pines, vertical
            rx, ry, vx, vy = x + 3.2, y - 1.0, x + 3.2, y + 1.6
        elif lib_id.startswith("Transistor_FET"):
            rx, ry, vx, vy = x + 6.0, y - 1.0, x + 6.0, y + 1.6
        elif lib_id.startswith("Regulator_Linear"):
            rx, ry, vx, vy = x - 4.0, y - 7.0, x + 1.0, y - 7.0
        else:
            mx = max(p[0] for p in pp)
            rx, ry, vx, vy = mx + 12.0, y - 1.0, mx + 12.0, y + 1.6
        if th in (90, 270):
            fa = (360 - th) % 360
        suid = str(uuid.uuid5(NS, ref)) if in_bom else U()
        e = [Sym("symbol"), S("lib_id", lib_id), S("at", x, y, th), S("unit", 1), S("exclude_from_sim", Sym("no")),
             S("in_bom", Sym("yes" if (in_bom and bom) else "no")), S("on_board", Sym("yes" if in_bom else "no")),
             S("dnp", Sym("yes" if dnp else "no")), S("uuid", suid)]

        def prop(k, v, px, py, hide=False, size=1.27):
            p = [Sym("property"), k, v, S("at", px, py, fa),
                 S("effects", S("font", S("size", size, size)), S("justify", Sym("left")))]
            if hide:
                p.insert(4, S("hide", Sym("yes")))
            return p
        e.append(prop("Reference", ref, rx, ry, hide_ref))
        e.append(prop("Value", val, vx, vy, hide_val))
        e.append(prop("Footprint", fp, x, y, True))
        e.append(prop("Datasheet", "~", x, y, True))
        e.append(prop("Description", desc, x, y, True))
        for k, v in (props_extra or {}).items():
            e.append(prop(k, v, x, y, True))
        for pn in pins:
            e.append(S("pin", pn, S("uuid", U())))
        e.append(S("instances", S("project", PROJECT, S("path", "/" + ROOT_UUID, S("reference", ref), S("unit", 1)))))
        self.items.append(e)
        # posiciones de pines en la hoja
        res = {}
        for pn, (px, py, pa, ptype) in pins.items():
            qx, qy = rot(px, py, th)
            sx, sy = x + qx, y - qy
            out_ang = (pa + 180 + th) % 360
            ux, uy = round(math.cos(math.radians(out_ang))), -round(math.sin(math.radians(out_ang)))
            res[pn] = (round(sx, 4), round(sy, 4), ux, uy)
        return res

    def wire(self, x1, y1, x2, y2):
        self.items.append(S("wire", S("pts", S("xy", x1, y1), S("xy", x2, y2)),
                            S("stroke", S("width", 0), S("type", Sym("default"))), S("uuid", U())))

    def label(self, name, x, y, ux, uy):
        ang = {(1, 0): 0, (0, -1): 90, (-1, 0): 180, (0, 1): 270}[(ux, uy)]
        just = "left" if ang in (0, 90) else "right"
        self.items.append(S("label", name, S("at", x, y, ang), S("fields_autoplaced", Sym("yes")),
                            S("effects", S("font", S("size", 1.27, 1.27)), S("justify", Sym(just), Sym("bottom"))),
                            S("uuid", U())))

    def power(self, net, x, y, ux, uy):
        lib_id = DZ.POWER[net]
        if net == "GND":
            th = {(0, 1): 0, (0, -1): 180, (-1, 0): 270, (1, 0): 90}[(ux, uy)]
        else:
            th = {(0, -1): 0, (0, 1): 180, (-1, 0): 90, (1, 0): 270}[(ux, uy)]
        self.pwr_n += 1
        self.symbol(lib_id, "#PWR%03d" % self.pwr_n, net, x, y, th, hide_ref=True, in_bom=False,
                    desc="Símbolo de alimentación")

    def flag(self, net, x, y):
        """PWR_FLAG conectado a la red 'net'."""
        self.flg_n += 1
        self.symbol("power:PWR_FLAG", "#FLG%02d" % self.flg_n, "PWR_FLAG", x, y, 0, hide_ref=True, in_bom=False,
                    desc="Bandera de alimentación para ERC")
        self.wire(x, y, x, y + 2.54)
        if net in DZ.POWER:
            self.power(net, x, y + 2.54, 0, 1) if net == "GND" else self.power_at(net, x, y + 2.54)
        else:
            self.label(net, x, y + 2.54, 1, 0)

    def power_at(self, net, x, y):
        # símbolo +V con el pin en (x, y) y el cuerpo hacia la derecha
        self.wire(x, y, x + 2.54, y)
        self.power(net, x + 2.54, y, 1, 0)

    def text(self, s, x, y, size=1.27, bold=False):
        f = S("font", S("size", size, size))
        if bold:
            f.append(S("bold", Sym("yes")))
        self.items.append(S("text", s, S("exclude_from_sim", Sym("no")), S("at", x, y, 0),
                            S("effects", f, S("justify", Sym("left"), Sym("top"))), S("uuid", U())))

    def rect(self, x1, y1, x2, y2):
        self.items.append(S("rectangle", S("start", x1, y1), S("end", x2, y2),
                            S("stroke", S("width", 0.3), S("type", Sym("dash"))), S("fill", S("type", Sym("none"))),
                            S("uuid", U())))

    def noconn(self, x, y):
        self.items.append(S("no_connect", S("at", x, y), S("uuid", U())))


BLOCK_SIZE = {"PWR": (180, 72), "REG": (185, 72), "OSC": (112, 88), "CNT": (270, 88), "OUT": (240, 85), "OPT": (140, 85)}

NOTES = [
    ("PWR", 0, 58, "Orden: J1 -> interruptor externo (J2) -> PTC -> diodo serie -> TVS/C1/C2.\n"
                   "Fuente externa CERTIFICADA y AISLADA de 36 VCC >= 0.5 A. Nunca 127 VCA en esta PCB."),
    ("REG", 0, 58, "Vout = 1.25 V x (1 + R3/R2) = 1.25 x (1 + 8.2k/1k) = 11.5 V\n"
                   "Pdis(U3) <= (36.25-11.5) V x 23 mA = 0.57 W (TO-220 sin disipador: +30 C)"),
    ("OSC", 5, 80, "T = 0.693 x C5 x (R5 + 2 x (R6 + RV1))\nRV1 = 0: 0.24 s   RV1 = 100k: 1.63 s"),
    ("CNT", 170, 62, "Q3 (pin 7) -> D7 -> RESET (pin 15): solo 3 pasos Q0-Q1-Q2.\n"
                     "POR: C8/R10 mantiene RESET ~0.6 s al encender (arranca en flecha 1).\n"
                     "PAUSA: SW1 lleva CLOCK INHIBIT (pin 13) a 12 V. REINICIO: SW2 fuerza RESET.\n"
                     "Salidas Q4-Q9 y CARRY sin conexión."),
    ("OUT", 30, 88, "I = 1.25 V / (68+68 ohm) + Iadj = 9.2 mA (8.8-9.8 mA en el peor caso), independiente de Vf y de la fuente.\n"
                   "Cada flecha: 9 LED verdes en serie, ánodo común a J3-1 (+36V), cátodo a F1-/F2-/F3-."),
    ("JMP", 0, 48, "Puentes de alambre desnudo en el lado de\ncomponentes (W1, W2...). Ambos extremos\nde cada puente pertenecen a la misma red.\nSe sueldan ANTES que los demás componentes."),
    ("OPT", 0, 55, "JP1-JP3 NO SE MONTAN hasta conocer: número de LED por rama, color,\n"
                   "Vf medida, polaridad, corriente deseada y división de ramas.\n"
                   "Las resistencias de cada rama van en el panel (no en esta PCB)."),
]


def main(outpath):
    sh = Sheet()
    for c in DZ.C:
        bx, by = DZ.BLOCKS[c["blk"]][1:3]
        x, y, th = c["pos"]
        x, y = g(bx + x + 10), g(by + y + 10)
        extra = {"Funcion": c["func"]}
        pins = sh.symbol(c["sym"], c["ref"], c["val"], x, y, th, fp=DZ.LIB + ":" + c["fp"], dnp=c["dnp"],
                         props_extra=extra, desc=c["func"], bom=not c["ref"].startswith("H"))
        for pn, (px, py, ux, uy) in pins.items():
            net = c["pins"].get(pn)
            if net is None:
                sh.noconn(px, py)
                continue
            st = STUB * 2 if (net in DZ.POWER and ux != 0) else STUB
            ex, ey = px + ux * st, py + uy * st
            sh.wire(px, py, ex, ey)
            if net in DZ.POWER and ux != 0:
                dy = 2.54 if net == "GND" else -2.54
                sh.wire(ex, ey, ex, ey + dy)
                sh.power(net, ex, ey + dy, 0, 1 if net == "GND" else -1)
            elif net in DZ.POWER:
                sh.power(net, ex, ey, ux, uy)
            else:
                sh.label(net, ex, ey, ux, uy)
    # banderas de alimentación
    for net, (b, fx, fy) in DZ.FLAGS.items():
        bx, by = DZ.BLOCKS[b][1:3]
        sh.flag(net, g(bx + fx + 10), g(by + fy + 10))
    extra = [n for n in DZ.PWR_FLAGS if n not in DZ.FLAGS]
    for i, net in enumerate(extra):
        bx, by = DZ.BLOCKS["JMP"][1:3]
        sh.flag(net, g(bx + 8 + i * 20), g(by + 32))
    for k, (title, bx, by, w, h) in DZ.BLOCKS.items():
        sh.rect(bx, by, bx + w, by + h)
        sh.text(title, bx + 2, by + 2, 2.0, bold=True)
    for k, dx, dy, s in NOTES:
        bx, by = DZ.BLOCKS[k][1:3]
        sh.text(s, bx + dx + 2, by + dy, 1.27)

    tb = S("title_block", S("title", "Controlador secuencial de flechas 36 V - Letrero Radox 246-402 modificado"),
           S("date", datetime.date.today().isoformat()), S("rev", "1.0"),
           S("company", "PCB una cara, THT, transferencia de toner"),
           S("comment", 1, "NE555P + CD4017BE + 2N7000 + LM317LZ (9 mA por flecha). Sin microcontrolador."),
           S("comment", 2, "Alimentacion: fuente externa aislada 36 VCC. SIN conexion a 127 VCA ni a la placa Radox."))
    doc = [Sym("kicad_sch"), S("version", Sym("20250114")), S("generator", "eeschema"), S("generator_version", "9.0"),
           S("uuid", ROOT_UUID), S("paper", "A3"), tb, [Sym("lib_symbols")] + list(sh.libs.values())]
    doc += sh.items
    doc.append(S("sheet_instances", S("path", "/", S("page", "1"))))
    doc.append(S("embedded_fonts", Sym("no")))
    open(outpath, "w").write(dump(doc) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
