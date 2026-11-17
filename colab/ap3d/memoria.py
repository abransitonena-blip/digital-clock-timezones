"""Memoria del proyecto: guarda lo que el usuario aprueba o corrige y lo usa
para no repetir errores.

* Cada resultado puede recibir 👍/👎 en: tipo detectado, forma, textura y
  esqueleto/animacion (con comentario opcional).
* Las correcciones de tipo (persona/animal/cabeza/objeto) se guardan con las
  medidas de la malla. Blender las lee y, si llega un modelo con medidas
  parecidas, usa el tipo que el usuario eligio (vecino mas cercano).
* Las estadisticas (que motor/preajuste sale mejor) se muestran en el panel.
Se guarda en Google Drive si esta montado; si no, en la carpeta de salidas.
"""
import json
import os
import threading
import time

from . import config

_LOCK = threading.Lock()
FEATS = ("ancho", "largo", "base", "piernas", "patas", "brazos", "cuello")


def path():
    drive = "/content/drive/MyDrive"
    if os.path.isdir(drive):
        return os.path.join(drive, "ap3d_aprendizaje.json")
    os.makedirs(config.OUT_DIR, exist_ok=True)
    return os.path.join(config.OUT_DIR, "aprendizaje.json")


def load():
    try:
        with open(path()) as f:
            return json.load(f)
    except Exception:
        return {"votos": [], "tipos": []}


def save(m):
    p = path()
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(m, f, indent=1, ensure_ascii=False)
    os.replace(tmp, p)


def features(clas):
    return [float(clas.get(k, 0)) for k in FEATS]


def vote(d, info, pregunta, ok, comentario=""):
    """Guarda un voto 👍/👎 de un resultado."""
    a = info.get("ajustes", {})
    with _LOCK:
        m = load()
        m["votos"].append({
            "t": time.strftime("%Y-%m-%d %H:%M"), "modelo": os.path.basename(d),
            "pregunta": pregunta, "ok": bool(ok), "comentario": comentario[:300],
            "motor": a.get("motor", "hunyuan"), "preset_pasos": a.get("steps"),
            "caras": a.get("faces"), "tipo": (info.get("clasificacion") or {}).get("tipo",
                                                                                  info.get("rig")),
        })
        save(m)


def teach_type(info, tipo_correcto):
    """Corrige el tipo de un modelo: queda como ejemplo para los siguientes."""
    clas = info.get("clasificacion")
    if not clas:
        return False
    with _LOCK:
        m = load()
        m["tipos"].append({"f": features(clas), "tipo": tipo_correcto,
                           "antes": clas.get("tipo"), "t": time.strftime("%Y-%m-%d %H:%M")})
        save(m)
    return True


def stats_md():
    m = load()
    v = m.get("votos", [])
    if not v and not m.get("tipos"):
        return ("Aún no hay votos. Después de cada modelo responde **¿Salió bien?** "
                "y el proyecto irá aprendiendo.")
    lines = [f"**{len(v)} votos · {len(m.get('tipos', []))} correcciones de tipo aprendidas**"]
    for q in ("tipo", "forma", "textura", "esqueleto"):
        qs = [x for x in v if x["pregunta"] == q]
        if qs:
            ok = sum(x["ok"] for x in qs)
            lines.append(f"- {q.capitalize()}: {ok}/{len(qs)} bien ({100 * ok // len(qs)} %)")
    # que motor sale mejor en forma
    for motor in ("hunyuan", "triposg"):
        qs = [x for x in v if x["pregunta"] == "forma" and x.get("motor") == motor]
        if len(qs) >= 2:
            ok = sum(x["ok"] for x in qs)
            lines.append(f"- Forma con {motor}: {100 * ok // len(qs)} % bien ({len(qs)} votos)")
    malos = [x for x in v if not x["ok"] and x.get("comentario")][-5:]
    if malos:
        lines.append("\n**Últimos problemas que anotaste:**")
        lines += [f"- {x['pregunta']}: {x['comentario']}" for x in malos]
    return "\n".join(lines)


def recommend(d, motor, tex_rapida, detalle):
    """Ajustes para reintentar segun los votos: devuelve (cambios, explicacion)."""
    m = load()
    v = m.get("votos", [])
    mine = [x for x in v if x.get("modelo") == os.path.basename(d or "")]
    malo = {q: any(not x["ok"] for x in mine if x["pregunta"] == q)
            for q in ("forma", "textura", "esqueleto")}
    cambios, why = {}, []
    if malo["forma"] or not mine:
        cambios["nueva_semilla"] = True
        why.append("otra semilla para la forma")
        # motor que mejor sale en tus votos (minimo 3 votos de cada uno)
        rate = {}
        for mo in ("hunyuan", "triposg"):
            qs = [x for x in v if x["pregunta"] == "forma" and x.get("motor") == mo]
            if len(qs) >= 3:
                rate[mo] = sum(x["ok"] for x in qs) / len(qs)
        actual = "triposg" if str(motor).startswith("Tripo") else "hunyuan"
        otro = "hunyuan" if actual == "triposg" else "triposg"
        if otro in rate and rate[otro] > rate.get(actual, 0) + 0.15:
            cambios["motor"] = otro
            why.append(f"motor {otro} (te sale mejor: {int(rate[otro] * 100)} % bien)")
    if malo["textura"] and tex_rapida:
        cambios["tex_rapida"] = False
        why.append("textura completa (sin «rápida»)")
    if malo["esqueleto"] and detalle:
        # con dedos/ojos falla mas en mallas simples: probar el basico
        cambios["detalle"] = False
        why.append("esqueleto simple (23 huesos)")
    return cambios, ", ".join(why) or "otra semilla"
