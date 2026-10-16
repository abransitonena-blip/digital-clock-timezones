"""Pone colores a los GLB que exporta KiCad (las piezas salen sin material y se ven grises).
Asigna un material por tipo de huella según el nombre de la malla. Uso: python3 tools/colorear_glb.py archivo.glb [...]
Es solo apariencia para el visor: no cambia la geometría."""
import json, struct, sys

# (fragmento del nombre, color RGB 0-1, metálico, rugosidad)
REGLAS = [
    ("TerminalBlock", (0.10, 0.55, 0.26), 0.0, 0.6),
    ("JST", (0.92, 0.90, 0.82), 0.0, 0.7),
    ("USB_C", (0.78, 0.80, 0.84), 0.9, 0.35),
    ("ESP32", (0.55, 0.57, 0.60), 0.8, 0.4),
    ("Fuse", (0.85, 0.65, 0.12), 0.1, 0.6),
    ("TestPoint", (0.85, 0.68, 0.25), 0.9, 0.3),
    ("Relay", (0.12, 0.16, 0.26), 0.0, 0.5),
    ("SW_", (0.30, 0.31, 0.33), 0.6, 0.4),
    ("LED", (0.55, 0.95, 0.60), 0.0, 0.3),
    ("SOIC", (0.07, 0.07, 0.08), 0.1, 0.6), ("TSSOP", (0.07, 0.07, 0.08), 0.1, 0.6), ("SOT", (0.07, 0.07, 0.08), 0.1, 0.6),
    ("SOP", (0.07, 0.07, 0.08), 0.1, 0.6), ("TSOT", (0.07, 0.07, 0.08), 0.1, 0.6),
    ("D_SM", (0.10, 0.10, 0.11), 0.1, 0.6), ("D_SOD", (0.10, 0.10, 0.11), 0.1, 0.6),
    ("L_", (0.18, 0.18, 0.20), 0.3, 0.5),
    ("R_", (0.06, 0.06, 0.07), 0.1, 0.7),
    ("C_", (0.62, 0.48, 0.28), 0.0, 0.7),
    ("MountingHole", (0.8, 0.8, 0.8), 0.9, 0.3),
]
DEFECTO = (0.5, 0.5, 0.52, 0.2, 0.6)


def procesar(ruta):
    b = open(ruta, "rb").read()
    magic, ver, tam = struct.unpack("<4sII", b[:12])
    ljson, tjson = struct.unpack("<I4s", b[12:20])
    j = json.loads(b[20:20 + ljson])
    resto = b[20 + ljson:]
    mats = list(j.get("materials", []))
    idx = {}

    def mat(nombre, rgb, met, rug):
        if nombre not in idx:
            idx[nombre] = len(mats)
            mats.append({"name": nombre, "pbrMetallicRoughness": {"baseColorFactor": [rgb[0], rgb[1], rgb[2], 1.0], "metallicFactor": met, "roughnessFactor": rug}, "doubleSided": True})
        return idx[nombre]
    n = 0
    for m in j.get("meshes", []):
        nom = m.get("name", "")
        elegido = None
        for frag, rgb, met, rug in REGLAS:
            if frag in nom:
                elegido = mat(frag, rgb, met, rug); break
        if elegido is None:
            elegido = mat("otros", DEFECTO[:3], DEFECTO[3], DEFECTO[4])
        for p in m.get("primitives", []):
            if "material" not in p:
                p["material"] = elegido; n += 1
    j["materials"] = mats
    nuevo = json.dumps(j, separators=(",", ":")).encode()
    nuevo += b" " * ((4 - len(nuevo) % 4) % 4)
    cuerpo = struct.pack("<I4s", len(nuevo), tjson) + nuevo + resto
    open(ruta, "wb").write(struct.pack("<4sII", magic, ver, 12 + len(cuerpo)) + cuerpo)
    return n, len(mats)


if __name__ == "__main__":
    for r in sys.argv[1:]:
        print("%s: %d primitivas con material, %d materiales" % (r, *procesar(r)))
