"""Acabados y formatos de imagen de la caja AP Rack (colores, texturas y tamaños) con Blender.

  blender -b -P blender/render_acabados.py -- --salida blender/renders/acabados
  python blender/render_acabados.py --solo carbono --muestras 96          (con el módulo bpy)

Genera, para la caja con la placa dentro y la tapa levantada:
  un render por acabado (color + textura: PETG mate, grafito texturizado, blanco satinado, azul industrial, fibra de carbono, aluminio cepillado, humo translúcido)
  los formatos de imagen para web y redes con el acabado de siempre: cuadrado (1080x1080), vertical (1080x1350), banner (1920x640) y portada (1920x1080)
Opciones: --solo TEXTO  --muestras N  --placa AP_RACK16|AP_RL4|AP_LED8|AP_RACKAO4  --rehacer si
Textura = relieve procedural (no es una imagen): las capas de impresión, el tejido del carbono y el cepillado son aproximaciones visuales.
"""
import math, os, sys
import bpy
from mathutils import Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import render_blender as R  # noqa: E402

RAIZ = R.RAIZ

# nombre: (color caja, color tapa, rugosidad, metal, textura, descripción)
ACABADOS = {
    "petg_naranja": ((0.16, 0.18, 0.22), (0.91, 0.36, 0.02), 0.45, 0.0, "capas", "PETG grafito con tapa naranja AP, con capas de impresión sutiles"),
    "grafito_texturizado": ((0.10, 0.105, 0.12), (0.06, 0.065, 0.075), 0.75, 0.0, "grano", "Grafito mate con grano fino (como una superficie texturizada de la cama de impresión)"),
    "blanco_satinado": ((0.88, 0.89, 0.9), (0.91, 0.36, 0.02), 0.30, 0.0, "liso", "Blanco satinado con tapa naranja"),
    "azul_industrial": ((0.05, 0.16, 0.38), (0.78, 0.8, 0.82), 0.38, 0.0, "capas", "Azul industrial con tapa gris claro"),
    "fibra_carbono": ((0.02, 0.02, 0.025), (0.03, 0.03, 0.035), 0.22, 0.1, "carbono", "Efecto fibra de carbono (tejido) en caja y tapa"),
    "aluminio_cepillado": ((0.62, 0.64, 0.67), (0.55, 0.57, 0.6), 0.34, 1.0, "cepillado", "Efecto aluminio cepillado"),
    "humo_translucido": ((0.12, 0.13, 0.15), (0.35, 0.38, 0.42), 0.18, 0.0, "traslucido", "Caja grafito con tapa de plástico ahumado translúcido (deja ver los LED)"),
}
FORMATOS = {"portada": (1920, 1080), "cuadrado": (1080, 1080), "vertical": (1080, 1350), "banner": (1920, 640)}


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    o = {"salida": os.path.join(AQUI, "renders", "acabados"), "solo": "", "muestras": "64", "placa": "AP_RACK16", "rehacer": "no"}
    for i in range(0, len(a) - 1, 2):
        k = a[i].lstrip("-")
        if k in o:
            o[k] = a[i + 1]
    o["muestras"] = int(o["muestras"])
    return o


def lin(c):
    """Los colores de ACABADOS están escritos como sRGB (0-1, como en la web); Blender trabaja en lineal."""
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def material_acabado(nombre, rgb, rug, metal, textura, translucido=False):
    rgb = lin(rgb)
    m = bpy.data.materials.new(nombre); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    p = N["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rug; p.inputs["Metallic"].default_value = metal
    if translucido:
        p.inputs["Alpha"].default_value = 0.55
        try:
            p.inputs["Transmission Weight"].default_value = 0.6
        except KeyError:
            pass
        m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
    coord = N.new("ShaderNodeTexCoord"); mapa = N.new("ShaderNodeMapping")
    L.new(coord.outputs["Object"], mapa.inputs["Vector"])
    bump = N.new("ShaderNodeBump"); bump.inputs["Distance"].default_value = 0.0004
    if textura == "capas":                    # líneas horizontales de capa de impresión (0.2 mm)
        w = N.new("ShaderNodeTexWave"); w.wave_type = "BANDS"; w.bands_direction = "Z"; w.inputs["Scale"].default_value = 1.0 / 0.0002 / 6.2832
        w.inputs["Distortion"].default_value = 0.15; w.inputs["Detail"].default_value = 0.0
        L.new(mapa.outputs["Vector"], w.inputs["Vector"]); L.new(w.outputs["Fac"], bump.inputs["Height"]); bump.inputs["Strength"].default_value = 0.25
    elif textura == "grano":
        n = N.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 9000; n.inputs["Detail"].default_value = 3
        L.new(mapa.outputs["Vector"], n.inputs["Vector"]); L.new(n.outputs["Fac"], bump.inputs["Height"]); bump.inputs["Strength"].default_value = 0.9
    elif textura == "cepillado":
        mapa.inputs["Scale"].default_value = (1.0, 220.0, 1.0)
        n = N.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 900; n.inputs["Detail"].default_value = 4
        L.new(mapa.outputs["Vector"], n.inputs["Vector"]); L.new(n.outputs["Fac"], bump.inputs["Height"]); bump.inputs["Strength"].default_value = 0.35
    elif textura == "carbono":                # tejido 2x2: dos ondas cruzadas con cuadros
        c = N.new("ShaderNodeTexChecker"); c.inputs["Scale"].default_value = 520
        w1 = N.new("ShaderNodeTexWave"); w1.wave_type = "BANDS"; w1.bands_direction = "X"; w1.inputs["Scale"].default_value = 2600
        w2 = N.new("ShaderNodeTexWave"); w2.wave_type = "BANDS"; w2.bands_direction = "Y"; w2.inputs["Scale"].default_value = 2600
        mix = N.new("ShaderNodeMix"); mix.data_type = "FLOAT"
        L.new(mapa.outputs["Vector"], c.inputs["Vector"]); L.new(mapa.outputs["Vector"], w1.inputs["Vector"]); L.new(mapa.outputs["Vector"], w2.inputs["Vector"])
        L.new(c.outputs["Fac"], mix.inputs[0]); L.new(w1.outputs["Fac"], mix.inputs[2]); L.new(w2.outputs["Fac"], mix.inputs[3])
        L.new(mix.outputs[0], bump.inputs["Height"]); bump.inputs["Strength"].default_value = 0.8
    if textura in ("capas", "grano", "cepillado", "carbono"):
        L.new(bump.outputs["Normal"], p.inputs["Normal"])
    return m


def asignar(o, m):
    o.data.materials.clear(); o.data.materials.append(m)


def montar(placa, acabado, res, muestras, pieza_extra=False):
    sc = R.limpiar("%dx%d" % res, muestras, "CYCLES")
    cc, ct, rug, metal, tex, _ = ACABADOS[acabado]
    caja = R.importar_stl(os.path.join(RAIZ, "accesorios", "stl", "caja_rack.stl")); R.pintar(caja, "caja")
    tapa = R.importar_stl(os.path.join(RAIZ, "accesorios", "stl", "tapa_caja_rack.stl")); R.pintar(tapa, "tapa")
    asignar(caja, material_acabado("caja_" + acabado, cc, rug, metal, tex))
    asignar(tapa, material_acabado("tapa_" + acabado, ct, rug, metal, tex if tex != "capas" else "capas", translucido=(tex == "traslucido")))
    bpy.context.view_layer.update()
    mnc, mxc = R.caja_limites([caja]); cx, cy = (mnc.x + mxc.x) / 2, (mnc.y + mxc.y) / 2
    objs = R.importar_glb(os.path.join(RAIZ, "web", "modelos3d", placa + ".glb"))
    mn, mx = R.caja_limites([x for x in objs if x.type == "MESH"])
    d = Vector((cx - (mn.x + mx.x) / 2, cy - (mn.y + mx.y) / 2, 0.0090 - mn.z))
    for x in objs:
        if x.parent is None:
            x.location += d
    tapa.location.z += (mxc.z - mnc.z) + 0.030
    bpy.context.view_layer.update()
    return [caja, tapa] + [x for x in objs if x.type == "MESH"]


def render(placa, acabado, nombre, res, muestras, salida, vertical_dist=1.0, azim=-32, elev=30):
    objs = montar(placa, acabado, res, muestras)
    ratio = res[0] / res[1]
    dist = 4.6 * max(1.0, (1.6 / ratio) ** 0.5) * vertical_dist
    R.escena(objs, os.path.join(salida, nombre + ".jpg"), dist=dist, azim=azim, elev=elev)


if __name__ == "__main__":
    o = args(); os.makedirs(o["salida"], exist_ok=True); hechos = 0
    for ac in ACABADOS:
        n = "acabado_%s" % ac
        if o["solo"] and o["solo"] not in n or (o["rehacer"] != "si" and os.path.exists(os.path.join(o["salida"], n + ".jpg"))):
            continue
        render(o["placa"], ac, n, (1600, 1000), o["muestras"], o["salida"]); hechos += 1
    for f, res in FORMATOS.items():
        n = "formato_%s" % f
        if o["solo"] and o["solo"] not in n or (o["rehacer"] != "si" and os.path.exists(os.path.join(o["salida"], n + ".jpg"))):
            continue
        render(o["placa"], "petg_naranja", n, res, o["muestras"], o["salida"], vertical_dist=(1.75 if f == "banner" else 1.0)); hechos += 1
    print("listo: %d renders en %s" % (hechos, o["salida"]))
