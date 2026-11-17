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
            # ajustes completos: para aprender que combinacion te sale mejor
            "ajustes": {k: a.get(k) for k in ("steps", "octree", "faces", "tex", "guidance",
                                              "tex_rapida", "detalle", "motor", "relieve")},
            "segundos": info.get("segundos_total"),
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
    _, mejor = best_settings()
    lines.append("\n" + mejor)
    bt = by_type_md()
    if bt:
        lines.append(bt)
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


def _key(aj):
    return json.dumps({k: aj.get(k) for k in ("steps", "octree", "faces", "tex_rapida",
                                              "detalle", "motor", "guidance")}, sort_keys=True)


def best_settings(min_votos=3):
    """La combinacion de ajustes con mas 👍 (forma+textura+esqueleto), con
    suavizado bayesiano para no premiar 1 solo voto. Devuelve (ajustes, texto)."""
    v = [x for x in load().get("votos", []) if x.get("ajustes")]
    grupos = {}
    for x in v:
        g = grupos.setdefault(_key(x["ajustes"]), {"ok": 0, "n": 0, "aj": x["ajustes"], "t": []})
        g["n"] += 1
        g["ok"] += int(x["ok"])
        if x.get("segundos"):
            g["t"].append(x["segundos"])
    cand = [g for g in grupos.values() if g["n"] >= min_votos]
    if not cand:
        return None, f"Aún faltan votos: necesito {min_votos} con los mismos ajustes."
    # (aciertos + 1) / (votos + 2): estimacion que no se fia de pocos votos
    best = max(cand, key=lambda g: ((g["ok"] + 1) / (g["n"] + 2), -sum(g["t"] or [0])))
    p = 100 * best["ok"] // best["n"]
    aj = best["aj"]
    t = f" · ~{sum(best['t']) / len(best['t']):.0f} s" if best["t"] else ""
    return aj, (f"Tus mejores ajustes: {p} % bien en {best['n']} votos{t} "
                f"(pasos {aj.get('steps')}, caras {aj.get('faces')}, motor {aj.get('motor')}, "
                f"textura {'rápida' if aj.get('tex_rapida') else 'completa'}, "
                f"esqueleto {'detallado' if aj.get('detalle', True) else 'simple'})")


def by_type_md():
    """Aprobacion del esqueleto por tipo de modelo (donde falla mas)."""
    v = [x for x in load().get("votos", []) if x["pregunta"] in ("esqueleto", "tipo")]
    tipos = {}
    for x in v:
        t = tipos.setdefault(x.get("tipo") or "?", [0, 0])
        t[0] += int(x["ok"])
        t[1] += 1
    if not tipos:
        return ""
    return "\n**Esqueleto por tipo:** " + " · ".join(
        f"{k} {100 * a // n} % ({n})" for k, (a, n) in sorted(tipos.items(), key=lambda z: -z[1][1]))
