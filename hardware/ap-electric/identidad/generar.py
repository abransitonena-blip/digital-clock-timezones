"""AP Electric · identidad: isotipo, logotipos, marca del modelo 7R Tour y etiquetas de producto.

Todo es vector real: las letras se convierten a trazos (DejaVu Sans, licencia libre de Bitstream Vera / DejaVu), sin
depender de fuentes instaladas. Salidas: SVG, PNG (cairosvg) y PDF (cairosvg).

    python3 generar.py SALIDA_DIR

Las etiquetas NO llevan sellos de certificación (NOM, CE, UL ni otros) y dicen PROTOTIPO: los valores que faltan van
como "por determinar" hasta que haya ensayos.
"""
import os, sys
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
import cairosvg

NAR, GRA, GRI, AMA = "#FF6B0A", "#1D1F24", "#6E737D", "#FFD100"
NEG = FontProperties(family="DejaVu Sans", weight="bold")
NOR = FontProperties(family="DejaVu Sans", weight="normal")
NEGC = FontProperties(family="DejaVu Sans", weight="bold", stretch="condensed")


def trazo(texto, x, y, alto, color, prop=NEG, espacio=0.0, ancla="izq", maximo=None):
    """Texto como <path>: x, y = línea base (coordenadas SVG), alto = altura de mayúscula; maximo = ancho máximo."""
    if maximo:
        _, a = trazo(texto, 0, 0, alto, color, prop, espacio)
        if a > maximo:
            f = maximo / a
            alto, espacio = alto * f, espacio * f
    esc = alto / 0.729                                  # DejaVu: mayúscula ~ 0.729 del tamaño
    partes, cx = [], 0.0
    for ch in texto:
        if ch == " ":
            cx += 0.30 + espacio / esc
            continue
        tp = TextPath((0, 0), ch, size=1, prop=prop)
        partes.append((cx, tp))
        cx += tp.get_extents().width + tp.get_extents().x0 + 0.06 + espacio / esc
    ancho = (cx - espacio / esc) * esc
    dx = {"izq": 0, "centro": -ancho / 2, "der": -ancho}[ancla]
    d = []
    for ox, tp in partes:
        for verts, cod in tp.iter_segments(curves=True):
            pass
        verts, codes = tp.vertices, tp.codes
        i = 0
        while i < len(verts):
            c = codes[i]
            px = lambda v: "%.2f %.2f" % (x + dx + (ox + v[0]) * esc, y - v[1] * esc)
            if c == 1: d.append("M" + px(verts[i])); i += 1
            elif c == 2: d.append("L" + px(verts[i])); i += 1
            elif c == 3: d.append("Q" + px(verts[i]) + " " + px(verts[i + 1])); i += 2
            elif c == 4: d.append("C" + px(verts[i]) + " " + px(verts[i + 1]) + " " + px(verts[i + 2])); i += 3
            elif c == 79: d.append("Z"); i += 1
            else: i += 1
    return '<path fill="%s" fill-rule="nonzero" d="%s"/>' % (color, " ".join(d)), ancho


def isotipo(x, y, s, fondo=NAR, letra="#FFFFFF"):
    """Cuadro redondeado con 'AP' sobre un riel (perfil de riel DIN): el sello de la marca."""
    r = s * 0.22
    g = ['<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="%.2f" fill="%s"/>' % (x, y, s, s, r, fondo)]
    t, _ = trazo("AP", x + s / 2, y + s * 0.64, s * 0.40, letra, ancla="centro", espacio=s * 0.01)
    g.append(t)
    # riel: barra con dos pestañas (perfil sombrero de 35 mm, simplificado)
    g.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="%.2f" fill="%s"/>' % (x + s * 0.17, y + s * 0.74, s * 0.66, s * 0.055, s * 0.02, letra))
    for fx in (0.17, 0.77):
        g.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s"/>' % (x + s * fx, y + s * 0.74, s * 0.06, s * 0.10, letra))
    return "\n".join(g)


def svg(w, h, cuerpo, fondo=None, unidades=""):
    bg = '<rect width="100%%" height="100%%" fill="%s"/>' % fondo if fondo else ""
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%s%s" height="%s%s" viewBox="0 0 %s %s">\n%s\n%s\n</svg>\n'
            % (w, unidades, h, unidades, w, h, bg, cuerpo))


def logo(variante, industrial=False):
    """variante: color / negro / blanco (para fondo oscuro)."""
    tinta = {"color": GRA, "negro": "#000000", "blanco": "#FFFFFF"}[variante]
    acento = {"color": NAR, "negro": "#000000", "blanco": "#FFFFFF"}[variante]
    iso_f = {"color": NAR, "negro": "#000000", "blanco": "#FFFFFF"}[variante]
    iso_l = {"color": "#FFFFFF", "negro": "#FFFFFF", "blanco": "#000000" if False else GRA}[variante]
    if variante == "blanco":
        iso_l = GRA
    g = [isotipo(0, 0, 120, iso_f, iso_l)]
    t, a = trazo("AP ELECTRIC", 150, 78 if not industrial else 70, 46, tinta, espacio=5)
    g.append(t)
    w = 150 + a
    if industrial:
        t2, a2 = trazo("INDUSTRIAL", 152, 108, 18, acento, espacio=11.5)
        g.append(t2); w = max(w, 152 + a2)
    return svg(int(w + 6), 120, "\n".join(g))


def marca_modelo():
    g = ['<rect x="2" y="2" width="128" height="76" rx="10" fill="none" stroke="%s" stroke-width="5"/>' % NAR]
    t, _ = trazo("7R", 66, 61, 46, NAR, ancla="centro", espacio=2); g.append(t)
    t, a = trazo("TOUR", 150, 61, 46, GRA, espacio=6); g.append(t)
    t2, a2 = trazo("AP ELECTRIC INDUSTRIAL", 150, 78 + 18, 12, GRI, espacio=3.5); g.append(t2)
    return svg(int(150 + max(a, a2) + 6), 100, "\n".join(g))


def triangulo_w012(x, y, s):
    """Advertencia de electricidad (forma del símbolo ISO 7010 W012: triángulo amarillo con borde negro y rayo)."""
    h = s * 0.866
    tri = "M%.2f %.2f L%.2f %.2f L%.2f %.2f Z" % (x + s / 2, y, x + s, y + h, x, y + h)
    k = s / 10
    rayo = ("M%.2f %.2f L%.2f %.2f L%.2f %.2f L%.2f %.2f L%.2f %.2f L%.2f %.2f Z" %
            (x + 5.6 * k, y + 2.6 * k, x + 3.6 * k, y + 5.8 * k, x + 5.0 * k, y + 5.8 * k, x + 4.2 * k, y + 8.0 * k,
             x + 6.6 * k, y + 4.6 * k, x + 5.2 * k, y + 4.6 * k))
    return ('<path d="%s" fill="%s" stroke="#000" stroke-width="%.2f" stroke-linejoin="round"/><path d="%s" fill="#000"/>'
            % (tri, AMA, s * 0.06, rayo))


def etiqueta(modelo, sub, lineas, aviso, ancho=110, alto=44):
    """Etiqueta en mm. lineas = [(texto, negrita)]."""
    g = ['<rect x="0.4" y="0.4" width="%.1f" height="%.1f" rx="2" fill="#FFF" stroke="#000" stroke-width="0.5"/>' % (ancho - 0.8, alto - 0.8)]
    g.append(isotipo(3, 3, 9))
    t, _ = trazo("AP ELECTRIC", 14.5, 7.4, 2.6, GRA, espacio=0.35); g.append(t)
    t, _ = trazo(sub, 14.5, 11.3, 1.5, NAR if "INDUSTRIAL" in sub else GRI, espacio=0.45); g.append(t)
    t, _ = trazo(modelo, ancho - 3, 9.0, 3.6, GRA, ancla="der", espacio=0.2, maximo=ancho - 50); g.append(t)
    y = 17.0
    for i, (txt, neg) in enumerate(lineas):
        lim = ancho - 6 if y < alto - 15 else ancho - 22          # junto al triángulo, renglón más corto
        t, _ = trazo(txt, 3, y, 1.5, "#000", NEG if neg else NOR, maximo=lim); g.append(t); y += 2.9
    g.append('<rect x="3" y="%.1f" width="%.1f" height="5.2" rx="0.8" fill="#C0281F"/>' % (alto - 8.2, ancho - 19))
    t, _ = trazo(aviso, 3 + (ancho - 19) / 2, alto - 4.6, 1.9, "#FFF", ancla="centro", espacio=0.2); g.append(t)
    g.append(triangulo_w012(ancho - 14.5, alto - 13.2, 11.5))
    return svg(ancho, alto, "\n".join(g), unidades="mm")


ETIQUETAS = {
    "etiqueta_7r_tour_24dc": ("7R TOUR 24DC", "INDUSTRIAL", [
        ("Controlador de 7 salidas por relé (contacto NA), 8 entradas 24 V CC, Modbus RTU aislado", True),
        ("Alimentación: 24 V CC SELV de fuente certificada · consumo: por determinar", False),
        ("Salidas: tensión y corriente por canal POR DETERMINAR (ver hoja de datos). CA únicamente.", False),
        ("Protección externa obligatoria por circuito de carga · no es un equipo de seguridad", False),
        ("Rev A · N.º de serie: ____________ · Fabricante: AP Electric (razón social por registrar)", False)],
        "PROTOTIPO · NO CERTIFICADO · NO VENDER"),
    "etiqueta_7r_tour_ca": ("7R TOUR CA", "INDUSTRIAL", [
        ("Controlador de 7 salidas por relé (contacto NA), 8 entradas 24 V CC, Modbus RTU aislado", True),
        ("Alimentación: red de CA monofásica, 50/60 Hz · rango y consumo: por determinar", False),
        ("Salidas: tensión y corriente por canal POR DETERMINAR (ver hoja de datos). CA únicamente.", False),
        ("Desconecte la red antes de abrir · instalación por persona competente", False),
        ("Rev A · N.º de serie: ____________ · Fabricante: AP Electric (razón social por registrar)", False)],
        "PROTOTIPO · NO CERTIFICADO · NO VENDER"),
    "etiqueta_home_plug": ("HOME PLUG", "HOGAR", [
        ("Controlador de 1 salida para lámparas de 127 V CA ~ 60 Hz (encender y apagar)", True),
        ("Carga máxima: POR DETERMINAR · solo lámparas no regulables · no motores ni calefactores", False),
        ("Si el apagador propio de la lámpara está abierto, este equipo no puede encenderla.", False),
        ("Funciona sin internet: botón, LED y programación local · uso en interiores secos", False),
        ("Rev A · N.º de serie: ____________ · Fabricante: AP Electric (razón social por registrar)", False)],
        "PROTOTIPO · NO CERTIFICADO · NO VENDER"),
    "etiqueta_home_switch": ("HOME SWITCH", "HOGAR", [
        ("Controlador de 1 salida para alumbrado de 127 V CA ~ 60 Hz · requiere neutro", True),
        ("L = fase · N = neutro · LS = fase a la lámpara · SW = fase que regresa del apagador", False),
        ("SW es ENTRADA DE RED, no contacto seco · carga máxima: POR DETERMINAR", False),
        ("Instalación fija por persona competente, con el circuito desenergizado", False),
        ("Rev A · N.º de serie: ____________ · Fabricante: AP Electric (razón social por registrar)", False)],
        "PROTOTIPO · NO CERTIFICADO · NO VENDER"),
}


def escribir(sal, nombre, contenido):
    p = os.path.join(sal, nombre + ".svg")
    open(p, "w").write(contenido)
    cairosvg.svg2png(url=p, write_to=os.path.join(sal, nombre + ".png"), output_width=1600 if "etiqueta" in nombre else 1200)
    cairosvg.svg2pdf(url=p, write_to=os.path.join(sal, nombre + ".pdf"))


if __name__ == "__main__":
    sal = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(sal, exist_ok=True)
    escribir(sal, "isotipo_color", svg(120, 120, isotipo(0, 0, 120)))
    escribir(sal, "isotipo_negro", svg(120, 120, isotipo(0, 0, 120, "#000000", "#FFFFFF")))
    escribir(sal, "isotipo_blanco", svg(120, 120, isotipo(0, 0, 120, "#FFFFFF", GRA)))
    for v in ("color", "negro", "blanco"):
        escribir(sal, "logo_ap_electric_" + v, logo(v))
        escribir(sal, "logo_ap_electric_industrial_" + v, logo(v, True))
    escribir(sal, "marca_7r_tour", marca_modelo())
    for n, (m, s, l, a) in ETIQUETAS.items():
        escribir(sal, n, etiqueta(m, s, l, a))
    print("identidad lista en", sal)
