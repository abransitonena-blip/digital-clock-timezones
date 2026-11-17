"""Interfaz web (Gradio) del estudio: dentro del notebook o como pagina
publica con contrasena a traves de un tunel de Cloudflare."""
import glob
import json
import os
import random
import re
import secrets
import subprocess
import threading
import time

import gradio as gr

from . import config
from .engine import get_engine

ANIMS = ["Caminar", "Correr", "Saludar", "Saltar", "Bailar", "Reposo", "Manos", "Hablar"]
PRESETS = {
    # nombre: (pasos, octree, caras, textura). 10 pasos o menos = modelo Turbo
    "Turbo": (5, 384, 60000, 2048),
    "Detallado": (8, 512, 150000, 2048),
    "Rapido": (25, 256, 40000, 2048),
    "Alta": (40, 384, 80000, 2048),
    "Maxima": (50, 512, 150000, 4096),
}
EXAMPLES_DIR = "/content/Hunyuan3D-2/assets/example_images"


def _files(d):
    order = ["modelo_animado.glb", "modelo_roblox.fbx", "modelo_quads.glb", "modelo_quads.fbx", "modelo_web.glb", "modelo_rig.fbx", "modelo.blend", "modelo_texturizado.glb",
             "modelo_estatico.obj", "modelo_estatico.mtl", "modelo_impresion3d.stl",
             "modelo_color_impresion.ply",
             "piezas.glb", "pesos.glb", "arcilla.glb", "rig_info.json"]
    fs = [os.path.join(d, f) for f in order if os.path.exists(os.path.join(d, f))]
    fs += [f for f in sorted(glob.glob(os.path.join(d, "*")))
           if f not in fs and not f.endswith((".log",))]
    return fs


def _summary(info):
    a = info.get("ajustes", {})
    lines = [
        (f"Malla de la IA: **{info['caras_alta']:,} caras** → reducida a " if info.get("caras_alta") else "") +
        f"**{info.get('caras', '?'):,} caras** · textura {a.get('tex')} px · "
        f"esqueleto {info.get('rig')} ({info.get('huesos', 0)} huesos, pesos por "
        f"{info.get('pesos', '-')}) · {info.get('segundos_total', '?')} s",
        f"Forma: {'multivista' if info.get('multivista') else '1 foto'} "
        f"({info.get('segundos_forma')} s) · Textura IA: "
        f"{'si' if info.get('textura_ia') else 'no'} ({info.get('segundos_textura')} s) · "
        f"Render: {info.get('render', '-')}",
        f"⏱ Tiempos: forma {info.get('segundos_forma', '?')} s"
        f"{' (Turbo)' if info.get('turbo') else ''} · textura {info.get('segundos_textura', '?')} s · "
        f"Blender {info.get('segundos_blender', '?')} s · "
        f"{('videos ' + str(info.get('segundos_videos')) + ' s (en segundo plano) · ') if info.get('segundos_videos') else ''}"
        f"**total {info.get('segundos_total', '?')} s**",
    ]
    if info.get("animaciones"):
        lines.append("Animaciones: " + ", ".join(info["animaciones"]))
    c = info.get("clasificacion")
    if c:
        tipos = {"humanoide": "persona", "cuadrupedo": "animal de 4 patas",
                 "cabeza": "cabeza / busto", "vehiculo": "vehículo", "mueble": "mueble",
                 "objeto": "objeto"}
        rasgos = [k for k in ("piernas", "brazos", "cuello", "patas", "ruedas") if c.get(k)]
        lines.append(f"Detectado como **{tipos.get(c.get('tipo'), c.get('tipo'))}**"
                     + (f" (vio: {', '.join(rasgos)})" if rasgos else ""))
    uv = info.get("uv")
    if uv:
        lines.append(f"UV ({uv['nota']}): textura aprovechada {uv['cobertura_pct']} % · "
                     f"triángulos estirados {uv['estirados_pct']} % · invertidos {uv['invertidos_pct']} %")
    if info.get("quads_caras"):
        lines.append(f"Malla en cuadrados limpia: **{info['quads_caras']:,} caras** con color y relieve "
                     "horneados de la original (`modelo_quads.glb`, pestaña *Cuadros*)")
    fz = info.get("fisica")
    if fz:
        lines.append(f"Física: {fz['masa_kg']} kg · centro de masa al {fz['centro_masa_altura_pct']} % · "
                     f"{'se sostiene solo' if fz.get('se_sostiene_solo') else 'necesita base'} · "
                     f"imprimir a 15 cm: {fz['impresion_15cm']['gramos_pla']} g PLA "
                     f"(`fisica.json` para Unity/Unreal)")
    if info.get("lod_caras"):
        lines.append("LOD ligeros: " + ", ".join(
            f"{k} ({v:,} caras)" for k, v in info["lod_caras"].items()))
    if info.get("mapas_rugosidad"):
        lines.append("PBR: rugosidad estimada y metal = 0 (no brilla como metal en Unity/Unreal)")
    if info.get("mapas_relieve"):
        lines.append("Relieve: mapa de normales creado desde la textura")
    if info.get("vertices_tela"):
        lines.append(f"Física de telas: {info['vertices_tela']:,} vértices de túnica/capa/mangas "
                     "liberados de las piernas y brazos para que no se rasguen")
    if info.get("huesos_tela"):
        lines.append(f"Huesos de tela: {info['huesos_tela']} (la túnica/capa se balancea con inercia)")
    if info.get("pesos_rellenados"):
        lines.append(f"Pesos por calor parcial: {info['pesos_rellenados']:,} puntos difíciles "
                     "(tiras, garras) tomaron el peso de sus vecinos")
    if info.get("pesos_intento", 1) > 1:
        lines.append(f"Pesos por calor logrados en el intento {info['pesos_intento']} (proxy más cerrado)")
    if "vertices_sin_peso_reparados" in info:
        lines.append(f"Pesos: 100 % de la malla sigue al esqueleto "
                     f"({info['vertices_sin_peso_reparados']} vertices reparados)")
    for w in info.get("avisos", []):
        lines.append(f"⚠️ {w}")
    return "\n\n".join(lines)


RIGS = {"Auto": "auto", "Humano": "humanoide", "Criatura": "cuadrupedo",
        "Cabeza / busto": "cabeza", "Vehículo": "vehiculo", "Mueble": "mueble", "Objeto": "objeto",
        "Sin esqueleto": "ninguno"}


def viewer_html(d=None, height=600, view=None, wire=False, etapa=None, msg=None):
    """Estudio 3D (three.js) en un iframe servido desde la carpeta del resultado."""
    if not d or not os.path.exists(os.path.join(d, "estudio.html")):
        return (f"<div class='vph' style='height:{height}px;display:flex;align-items:center;"
                "justify-content:center;flex-direction:column;gap:10px;background:#121318;"
                "border-radius:14px;color:#9a9daa;font-family:system-ui'>"
                "<div style='font-size:46px'>🧍</div><div>" + (msg or "Sube una foto y pulsa "
                "<b style='color:#e8e9ee'>Generar 3D con IA + Esqueleto</b>") + "</div></div>")
    from urllib.parse import quote
    q = f"t={int(time.time() * 1000)}"
    if view:
        q += f"&v={view}"
    if wire:
        q += "&wire=1"
    if etapa:
        q += "&etapa=" + quote(etapa)
    src = f"/gradio_api/file={os.path.join(d, 'estudio.html')}?{q}"
    return (f"<iframe src='{src}' style='width:100%;height:{height}px;border:0;"
            "border-radius:14px;background:#121318' allow='fullscreen; xr-spatial-tracking'"
            " allowfullscreen></iframe>"
            f"<div style='text-align:right;margin-top:4px'><a href='{src}' target='_blank' "
            "style='color:#8b8bff;font-size:13px'>Abrir en pantalla completa ↗</a></div>")


# ------------------------------------------------------------ generar por etapas
# Mismo formato que la app oficial de Hunyuan3D: funciones simples encadenadas
# (malla -> textura -> esqueleto). Cada una devuelve su resultado y la pagina
# lo muestra al terminar esa etapa. Sin transmision en vivo ni temporizadores.
JOBS = {}


def _wait(st, name, progress):
    """Espera a que el trabajo llegue a la etapa `name` mostrando el avance."""
    while name not in st["names"] and not st["done"]:
        progress(min(0.99, st["f"]), desc=f"{st['m']} · {time.time() - st['t0']:.0f} s")
        time.sleep(0.5)
    if st["err"]:
        raise gr.Error(f"Fallo: {st['err']}")


def _spo(comp):
    """La barra de Gradio se oculta: el avance se ve en el monitor de arriba."""
    return {"show_progress": "hidden"}


def _done_html():
    # Un solo visor 3D vivo a la vez: el celular no se queda sin memoria
    return viewer_html(msg="Etapa terminada. Todo está en «3 · Estudio animado»: los botones "
                           "Arcilla y Polígonos muestran la malla")


def _exists(d, f):
    p = os.path.join(d, f)
    return p if os.path.exists(p) and os.path.getsize(p) > 500 else None


def step_malla(front, back, left, right, sheet, sheet_order, remove_bg, steps, octree,
               faces, tex, seed, rand_seed, guidance, rig, height, rotate, video,
               video_res, samples, turntable, texture, relieve_on, relieve, make_videos,
               detalle=True, motor="Hunyuan3D (rápido)", prompt="", tex_rapida=False,
               activo="Auto", altura_prop=0.40, roblox="Roblox 12k", progress=gr.Progress()):
    """Etapa 1: lanza el trabajo y devuelve la malla en cuanto existe."""
    if rand_seed:
        seed = random.randint(0, 2**31 - 1)
    eng = get_engine()
    if front is None and sheet is None:
        if not (prompt or "").strip():
            raise gr.Error("Sube una foto o escribe una descripción.")
        progress(0.01, desc="Creando la imagen desde el texto…")
        try:
            front = eng.text_to_image(prompt, seed)
        except Exception as e:
            raise gr.Error(f"No se pudo crear la imagen desde el texto: {e}")
    if front is None:
        front = eng.split_sheet(sheet, sheet_order).get("front")
    jid = secrets.token_hex(6)
    st = {"f": 0.0, "m": "Preparando", "res": None, "err": None, "done": False,
          "names": [], "dir": None, "t0": time.time()}
    JOBS[jid] = st
    for old in list(JOBS)[:-20]:
        JOBS.pop(old, None)

    def prog(fr, m):
        st["f"] = max(st["f"], float(fr))
        st["m"] = m

    def on_stage(name, d):
        st["dir"] = d
        st["names"].append(name)

    def work():
        try:
            st["res"] = eng.run(front, back, left, right, sheet, sheet_order, remove_bg,
                                steps, octree, faces, int(tex), seed, guidance,
                                RIGS.get(rig, rig), height, rotate, video, video_res,
                                samples, turntable, texture,
                                relieve=float(relieve) if relieve_on else 0.0,
                                turbo=int(steps) <= 10, progress=prog,
                                videos=bool(make_videos), on_stage=on_stage,
                                detalle=bool(detalle),
                                motor="triposg" if str(motor).startswith("Tripo") else "hunyuan",
                                tex_rapida=bool(tex_rapida),
                                asset_type={"Personaje": "character", "Prop rígido": "prop_rigid",
                                            "Prop articulado": "prop_articulated"}.get(activo, "auto"),
                                altura_prop=float(altura_prop),
                                roblox_tris={"No": 0, "Roblox 12k": 12000, "Roblox 15k": 15000,
                                             "High 40k": 40000}.get(roblox, 12000))
            st["dir"] = st["res"]["dir"]
        except Exception as e:
            import traceback
            st["err"] = f"{type(e).__name__}: {e}"
            st["trace"] = traceback.format_exc()
            print(st["trace"])
        finally:
            st["done"] = True

    threading.Thread(target=work, daemon=True).start()
    _wait(st, "malla", progress)
    d = st["dir"]
    return (front, jid, viewer_html(d, view="hi" if _exists(d, "malla_alta.glb") else "clay", wire=True,
                             etapa="Etapa 1/3 · Malla en alta resolución"),
            gr.update(selected="malla"),
            f"**Etapa 1/3 · Malla lista** ({time.time() - st['t0']:.0f} s). Pintando la textura…",
            int(seed), tablero_html(2, activo=True))


def step_textura(jid, progress=gr.Progress()):
    """Etapa 2: devuelve el modelo con textura."""
    st = JOBS.get(jid)
    if st is None:
        raise gr.Error("Trabajo no encontrado; vuelve a generar.")
    _wait(st, "textura", progress)
    d = st["dir"]
    return (viewer_html(d, view="tex", etapa="Etapa 2/3 · Textura"),
            gr.update(selected="textura"),
            f"**Etapa 2/3 · Textura lista** ({time.time() - st['t0']:.0f} s). "
            "Poniendo esqueleto y animaciones…", tablero_html(3, activo=True))


def step_final(jid, progress=gr.Progress()):
    """Etapa 3: esqueleto, animaciones y archivos."""
    st = JOBS.get(jid)
    if st is None:
        raise gr.Error("Trabajo no encontrado; vuelve a generar.")
    _wait(st, "__fin__", progress)
    r = st["res"]
    d, info = r["dir"], r["info"]
    vid = next((os.path.join(d, f) for f in sorted(os.listdir(d))
                if f.startswith("video_") and "giro360" not in f and _exists(d, f)), None)
    zp = d + ".zip"
    files = ([zp] if os.path.exists(zp) else []) + _files(d)
    return (viewer_html(d), gr.update(selected="estudio"),
            _done_html(), _done_html(),
            vid, _exists(d, "video_giro360.mp4"), files,
            f"✅ **Modelo listo en {time.time() - st['t0']:.0f} s** · datos y resumen debajo del visor",
            monitor_html(), d, _review_md(info), _tipo_actual(info), tablero_html(7), datos_html(info),
            _summary(info))


# ------------------------------------------------------------ tablero (tarjetas)
_IC = {  # iconos de linea, estilo de la hoja de diseno
    "foto": "<rect x='6' y='14' width='36' height='24' rx='4'/><circle cx='24' cy='26' r='7'/><path d='M17 14l3-5h8l3 5'/>",
    "forma": "<path d='M24 6l16 9v18l-16 9-16-9V15z'/><path d='M8 15l16 9 16-9M24 24v18'/>",
    "textura": "<path d='M10 38l18-18 6 6-18 18H10z'/><path d='M28 20l5-5a3 3 0 014 4l-5 5'/><circle cx='13' cy='12' r='3'/>",
    "esqueleto": "<circle cx='24' cy='9' r='4'/><path d='M24 13v14M14 18h20M24 27l-7 13M24 27l7 13'/><circle cx='14' cy='18' r='2'/><circle cx='34' cy='18' r='2'/>",
    "poses": "<circle cx='28' cy='8' r='4'/><path d='M27 13l-6 12 8 5-3 11M21 25l-9 2M27 15l9 6'/>",
    "fisica": "<path d='M24 6v8M10 18h28M14 18l-6 12h12zM34 18l-6 12h12z'/><path d='M18 42h12M24 14v28'/>",
    "exportar": "<path d='M24 6v20M16 18l8 8 8-8'/><rect x='8' y='30' width='14' height='12' rx='2'/><rect x='26' y='30' width='14' height='12' rx='2'/>",
}
_ETAPAS = [("foto", "Foto"), ("forma", "Forma 3D"), ("textura", "Textura"),
           ("esqueleto", "Esqueleto"), ("poses", "Animaciones"), ("fisica", "Física"),
           ("exportar", "Exportar")]


def tablero_html(hecho=0, info=None, activo=None, solo_datos=False):
    """Tarjetas del proceso (azul = hecho, borde brillante = en curso) y
    los datos del modelo: fisica, esqueleto, malla, impresion."""
    info = info or {}
    cards = []
    for i, (k, lab) in enumerate(_ETAPAS):
        st = "ok" if i < hecho else ("run" if i == hecho and activo else "")
        cards.append(f"<div class='tc {st}'><svg viewBox='0 0 48 48'>{_IC[k]}</svg>"
                     f"<span>{lab}</span></div>")
    datos = ""
    f = info.get("fisica")
    if f:
        est = f.get("se_sostiene_solo")
        est_txt = ("✅ se sostiene solo" if est else "⚠️ se cae: necesita base o soporte") \
            if est is not None else "—"
        imp = f.get("impresion_15cm", {})
        datos += (
            "<div class='td'><b>Física (a tamaño real)</b>"
            f"<div class='kv'><span>Medidas</span><b>{f['ancho_m']} × {f['alto_m']} × {f['fondo_m']} m</b></div>"
            f"<div class='kv'><span>Volumen</span><b>{f['volumen_l']} L</b></div>"
            f"<div class='kv'><span>Masa aprox.</span><b>{f['masa_kg']} kg</b></div>"
            f"<div class='kv'><span>Centro de masa</span><b>{f['centro_masa_altura_pct']} % de la altura</b></div>"
            f"<div class='kv'><span>Base de apoyo</span><b>{f['base_apoyo_cm2']} cm²</b></div>"
            f"<div class='kv'><span>Equilibrio</span><b>{est_txt}</b></div>"
            "</div><div class='td'><b>Impresión 3D a 15 cm (PLA, 20 %)</b>"
            f"<div class='kv'><span>Filamento</span><b>{imp.get('gramos_pla')} g</b></div>"
            f"<div class='kv'><span>Tiempo aprox.</span><b>{imp.get('horas')} h</b></div>"
            f"<div class='kv'><span>Volumen</span><b>{imp.get('volumen_cm3')} cm³</b></div></div>")
    qa = info.get("qa")
    if qa:
        dm = qa.get("dimensions_m") or [0, 0, 0]
        ws = qa.get("warnings") or []
        isl = info.get("islas_malla") or {}
        datos += ("<div class='td'><b>Control de calidad</b>"
                  f"<div class='kv'><span>Estado</span><b>{'✅ aprobado' if qa.get('passed', not ws) else '❌ no aprobado'}"
                  f"{'' if not ws else ' · ' + str(len(ws)) + ' alertas'}</b></div>"
                  f"<div class='kv'><span>Tipo de activo</span><b>{info.get('tipo_activo', '—')}</b></div>"
                  f"<div class='kv'><span>Medidas (m)</span><b>{dm[0]} × {dm[1]} × {dm[2]}</b></div>"
                  f"<div class='kv'><span>Triángulos</span><b>{qa.get('triangles', 0):,}</b></div>"
                  f"<div class='kv'><span>Vértices</span><b>{qa.get('vertices', 0):,}</b></div>"
                  f"<div class='kv'><span>Roblox</span><b>{qa.get('roblox_triangles') or '—'}"
                  f"{' ✅ listo' if qa.get('roblox_ready') else ''}</b></div>"
                  f"<div class='kv'><span>Islas</span><b>{isl.get('islas', '—')} → {qa.get('islands')} "
                  f"(ancladas {isl.get('ancladas', 0)}, puentes {isl.get('puentes', 0)}, "
                  f"quitadas {isl.get('eliminadas', 0)})</b></div>"
                  f"<div class='kv'><span>Bordes no manifold</span><b>{qa.get('non_manifold_edges')}</b></div>"
                  f"<div class='kv'><span>Esqueleto</span><b>{'sí' if qa.get('has_rig') else 'no'}</b></div>"
                  f"<div class='kv'><span>Texturas empaquetadas</span><b>{'sí' if qa.get('textures_packed') else 'no'}</b></div>"
                  + "".join(f"<div class='kv'><span class='warnq'>⚠️ {w}</span></div>" for w in ws)
                  + "</div>")
    if info.get("huesos"):
        c = (info.get("clasificacion") or {}).get("tipo", info.get("rig"))
        datos += ("<div class='td'><b>Modelo</b>"
                  f"<div class='kv'><span>Tipo</span><b>{TIPOS_UI.get(c, c)}</b></div>"
                  f"<div class='kv'><span>Huesos</span><b>{info.get('huesos')}</b></div>"
                  f"<div class='kv'><span>Caras</span><b>{info.get('caras', 0):,}</b></div>"
                  f"<div class='kv'><span>Cuadros</span><b>{info.get('quads_caras') or '—'}</b></div>"
                  f"<div class='kv'><span>UV</span><b>{(info.get('uv') or {}).get('nota', '—')}</b></div>"
                  f"<div class='kv'><span>Total</span><b>{info.get('segundos_total', '—')} s</b></div></div>")
    if solo_datos:
        return f"<div class='tab'><div class='tds'>{datos}</div></div>" if datos else ""
    return "<div class='tab'><div class='tcs'>" + "".join(cards) + "</div></div>"


def datos_html(info):
    return tablero_html(7, info, solo_datos=True)


# ------------------------------------------------------------ aprender del usuario
TIPOS_UI = {"humanoide": "Persona", "cuadrupedo": "Animal de 4 patas",
            "cabeza": "Cabeza / busto", "vehiculo": "Vehículo", "mueble": "Mueble",
            "objeto": "Objeto", "ninguno": "Prop rígido (sin esqueleto)"}
UI_TIPOS = {v: k for k, v in TIPOS_UI.items()}


def _tipo_actual(info):
    t = "ninguno" if info.get("rig") == "ninguno" else (info.get("clasificacion") or {}).get("tipo", info.get("rig"))
    return TIPOS_UI.get(t, "Persona")


def _review_md(info):
    t = _tipo_actual(info)
    extra = " (aprendido de tus correcciones)" if (info.get("clasificacion") or {}).get(
        "aprendido_de") else ""
    return (f"### ¿Salió bien?\nEl modelo se detectó como **{t}**{extra}. Vota cada parte: "
            "con 👎 el proyecto lo anota y evita repetir el error.")


def _info_of(d):
    try:
        return json.load(open(os.path.join(d, "rig_info.json")))
    except Exception:
        return {}


def do_vote(d, pregunta, ok, comentario):
    if not d:
        raise gr.Error("Primero genera o abre un modelo.")
    from . import memoria
    memoria.vote(d, _info_of(d), pregunta, ok, comentario or "")
    consejo = ""
    if not ok:
        consejo = {
            "forma": "Prueba con otra **semilla** (Avanzado › Aleatoria), el motor **TripoSG** o "
                     "subir la **espalda y perfiles** en «Más vistas».",
            "textura": "Prueba sin «Textura rápida», o con una foto con mejor luz y fondo liso.",
            "esqueleto": "Si el tipo está mal, corrígelo arriba. Si no, prueba quitando "
                         "«Esqueleto detallado» o subiendo la foto en pose T/A.",
            "tipo": "Elige el tipo correcto y pulsa **Corregir esqueleto**.",
        }.get(pregunta, "")
    return (f"Anotado: {pregunta} {'👍' if ok else '👎'}. " + consejo, memoria.stats_md())


def fix_type(d, tipo_ui, progress=gr.Progress()):
    """El usuario corrige el tipo: se aprende y se rehace el esqueleto."""
    if not d:
        raise gr.Error("Primero genera o abre un modelo.")
    from . import memoria
    rig = UI_TIPOS.get(tipo_ui, "humanoide")
    info = _info_of(d)
    if memoria.teach_type(info, rig):
        aviso = f"Aprendido: modelos parecidos serán **{tipo_ui}**. "
    else:
        aviso = ""
    memoria.vote(d, info, "tipo", rig == (info.get("clasificacion") or {}).get("tipo"),
                 f"correcto: {tipo_ui}")
    new = get_engine().rerig(d, rig, progress=lambda f, m: progress(f, desc=m))
    zp = d + ".zip"
    return (viewer_html(d), gr.update(selected="estudio"),
            ([zp] if os.path.exists(zp) else []) + _files(d),
            aviso + "Esqueleto rehecho.\n\n" + _summary(new), memoria.stats_md())


def rig_edit(carpeta: str, cambios: str) -> str:
    """API del editor de esqueleto del visor: recibe la carpeta del modelo y
    un JSON {mover, extra, reiniciar}; lo acumula en huesos_editados.json y
    rehace esqueleto y pesos en Blender (30-60 s)."""
    d = os.path.realpath(carpeta)
    base = os.path.realpath(config.OUT_DIR)
    if not d.startswith(base + os.sep) or not os.path.isdir(d):
        raise gr.Error("Carpeta no valida")
    ed = json.loads(cambios)
    if not isinstance(ed, dict):
        raise gr.Error("Datos no validos")
    p = os.path.join(d, "huesos_editados.json")
    prev = {"mover": {}, "extra": []}
    if os.path.exists(p) and not ed.get("reiniciar"):
        prev = json.load(open(p))
    prev["mover"].update({str(k): [float(x) for x in v][:3] for k, v in (ed.get("mover") or {}).items()})
    quitar = set(ed.get("borrar") or [])
    prev["extra"] = [e for e in prev["extra"] if e.get("nombre") not in quitar]
    for e in (ed.get("extra") or [])[:40]:
        prev["extra"].append({"nombre": str(e["nombre"])[:20], "padre": str(e.get("padre", "")),
                              "head": [float(x) for x in e["head"]][:3],
                              "tail": [float(x) for x in e["tail"]][:3],
                              "orden": int(e.get("orden", 0))})
    json.dump(prev, open(p, "w"), indent=1)
    info = _info_of(d)
    rig = info.get("rig") or (info.get("clasificacion") or {}).get("tipo") or "humanoide"
    new = get_engine().rerig(d, rig, huesos=p)
    e = new.get("edicion_huesos", {})
    return json.dumps({"ok": True, "huesos": new.get("huesos"), "movidos": e.get("movidos", 0),
                       "extra": e.get("extra", 0), "avisos": new.get("avisos", [])})


def batch(files, rig, video, progress=gr.Progress()):
    if not files:
        raise gr.Error("Sube varias fotos")
    eng = get_engine()
    zips, log = [], []
    for i, f in enumerate(files):
        progress(i / len(files), desc=f"Foto {i + 1}/{len(files)}")
        path = f if isinstance(f, str) else f.name
        try:
            r = eng.run(path, rig=RIGS.get(rig, rig), video=video)
            zips.append(r["zip"])
            log.append(f"✅ {os.path.basename(path)} → {os.path.basename(r['zip'])}")
        except Exception as e:
            log.append(f"❌ {os.path.basename(path)}: {e}")
    return zips, "\n\n".join(log)


FILTROS = {"Todos": None, "Personas": "humanoide", "Vehículos": "vehiculo",
           "Animales": "cuadrupedo", "Cabezas": "cabeza", "Muebles": "mueble",
           "Objetos": "objeto"}


def _model_dirs(filtro="Todos"):
    want = FILTROS.get(filtro)
    out = []
    for d in sorted(glob.glob(os.path.join(config.OUT_DIR, "*")), reverse=True):
        if not os.path.isdir(d):
            continue
        img = next((os.path.join(d, f) for f in ("miniatura.png", "vista_previa.png", "vista_front.png")
                    if os.path.exists(os.path.join(d, f))), None)
        if not img:
            continue
        try:
            inf = json.load(open(os.path.join(d, "rig_info.json")))
        except Exception:
            inf = {}
        tipo = (inf.get("clasificacion") or {}).get("tipo", inf.get("rig"))
        if want and tipo != want:
            continue
        out.append((d, img, tipo, inf))
    return out[:60]


def my_models(filtro="Todos"):
    """Galeria de modelos guardados, con su tipo y numero de huesos."""
    return [(img, f"{TIPOS_UI.get(t, t or '?')} · {inf.get('huesos', 0)} huesos · "
                  f"{os.path.basename(d)[9:15]}")
            for d, img, t, inf in _model_dirs(filtro)]


def kpis_html():
    """Tarjetas de resumen (estilo dashboard): modelos, tiempo medio,
    aprobacion de tus votos y GPU."""
    ds = _model_dirs()
    tiempos = [inf.get("segundos_total") for _, _, _, inf in ds if inf.get("segundos_total")]
    medio = f"{sum(tiempos) / len(tiempos):.0f} s" if tiempos else "—"
    try:
        from . import memoria
        v = memoria.load().get("votos", [])
        ok = f"{100 * sum(x['ok'] for x in v) // len(v)} %" if v else "—"
    except Exception:
        ok = "—"
    try:
        import torch
        fr, tot = torch.cuda.mem_get_info()
        gpu = f"{100 * (tot - fr) // tot} %"
    except Exception:
        gpu = "—"
    ic = {"m": "<path d='M6 18l18-10 18 10-18 10z'/><path d='M6 26l18 10 18-10M6 34l18 10 18-10'/>",
          "t": "<circle cx='24' cy='24' r='17'/><path d='M24 14v11l7 5'/>",
          "v": "<path d='M14 22v18h-6V22zM14 38l6 2h14l6-14-4-4H28l2-10-4-2-12 12'/>",
          "g": "<rect x='12' y='12' width='24' height='24' rx='3'/><rect x='19' y='19' width='10' height='10'/>"
               "<path d='M18 6v6M30 6v6M18 36v6M30 36v6M6 18h6M6 30h6M36 18h6M36 30h6'/>"}
    cards = [("m", "Modelos", str(len(ds))), ("t", "Tiempo medio", medio),
             ("v", "Te gustaron", ok), ("g", "Memoria GPU", gpu)]
    return ("<div class='kpis'>" + "".join(
        f"<div class='kpi'><svg viewBox='0 0 48 48'>{ic[k]}</svg><span>{lab}</span><b>{val}</b></div>"
        for k, lab, val in cards) + "</div>")


def open_model(filtro, evt: gr.SelectData):
    d = _model_dirs(filtro)[evt.index][0]
    if not os.path.exists(os.path.join(d, "estudio.html")):
        import shutil
        shutil.copy(os.path.join(os.path.dirname(__file__), "estudio.html"), d)
    info = {}
    try:
        info = json.load(open(os.path.join(d, "rig_info.json")))
    except Exception:
        pass
    vid = next((os.path.join(d, f) for f in sorted(os.listdir(d))
                if f.startswith("video_") and "giro360" not in f and _exists(d, f)), None)
    zp = d + ".zip"
    return (viewer_html(d), gr.update(selected="estudio"),
            _done_html(), _done_html(), vid, _exists(d, "video_giro360.mp4"),
            ([zp] if os.path.exists(zp) else []) + _files(d), "📂 Modelo abierto · datos debajo del visor",
            monitor_html(), d, _review_md(info), _tipo_actual(info), tablero_html(7), datos_html(info),
            _summary(info))


def history():
    zs = sorted(glob.glob(os.path.join(config.OUT_DIR, "*.zip")), reverse=True)
    return zs[:50]


def resources():
    try:
        import psutil
        import torch
        vm = psutil.virtual_memory()
        g = torch.cuda.mem_get_info() if torch.cuda.is_available() else (0, 0)
        e = get_engine()
        return (f"{config.describe(e.p)}\n\nRAM: {vm.used / 2**30:.1f} / "
                f"{vm.total / 2**30:.0f} GB ({vm.percent}%) · GPU usada: "
                f"{(g[1] - g[0]) / 2**30:.1f} / {g[1] / 2**30:.0f} GB · "
                f"resultados en cache: {len(e.cache)}")
    except Exception as ex:
        return str(ex)


_HIST = {"t": [], "gpu": [], "vram": [], "ram": [], "cpu": [], "temp": []}


def _sample():
    import psutil
    g = v = tp = pw = 0.0
    try:
        o = subprocess.run("nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,"
                           "temperature.gpu,power.draw --format=csv,noheader,nounits",
                           shell=True, capture_output=True, text=True, timeout=3).stdout
        a = [float(x) for x in o.strip().split("\n")[0].split(",")]
        g, v, tp, pw = a[0], 100 * a[1] / max(a[2], 1), a[3], a[4]
        vram_txt = f"{a[1] / 1024:.1f}/{a[2] / 1024:.0f} GB"
    except Exception:
        vram_txt = "sin GPU"
    vm = psutil.virtual_memory()
    vals = dict(gpu=g, vram=v, ram=vm.percent, cpu=psutil.cpu_percent(), temp=tp)
    for k_, x in vals.items():
        _HIST[k_].append(x)
        del _HIST[k_][:-90]
    return vals, vram_txt, vm, pw


# ------------------------------------------------------------ monitor en vivo
_MON = {"hilo": None}
LIVE_JS = r"""
<script>
(function(){
 const LIM={gpu:97,vram:92,ram:90,cpu:95,temp:83};
 const FC={Cola:'#e5484d',Fondo:'#8a90a8',Forma:'#4d7dff',Limpieza:'#9b7bff',Textura:'#e0a030',Blender:'#1f9d6b',ZIP:'#4fb3d9',Carga:'#e5484d'};
 function sp(h,c,max){if(!h||h.length<2)return '';const W=300,H=40;
   return `<polyline fill="none" stroke="${c}" stroke-width="1.6" points="${h.map((v,i)=>`${(W*i/(h.length-1)).toFixed(1)},${(H-H*Math.min(v,max)/max).toFixed(1)}`).join(' ')}"/>`}
 async function tick(){const el=document.getElementById('livebox');if(!el)return;
  let d;try{d=await (await fetch('gradio_api/file=__PATH__?t='+Date.now())).json()}catch(e){return}
  const ch=[['GPU',d.gpu,'%','gpu'],['VRAM',d.vram,'%','vram'],['Temp',d.temp,'°C','temp'],['CPU',d.cpu,'%','cpu'],['RAM',d.ram,'%','ram']];
  const alert=ch.filter(c=>c[1]>=LIM[c[3]]).map(c=>c[0]);if(d.cola>0)alert.push(d.cola+' en cola');
  let h=`<div class="lv-top"><span class="${alert.length?'lv-bad':'lv-ok'}">${alert.length?'⚠ '+alert.join(', '):'● Todo normal'}</span><span class="lv-sub">${d.vram_txt} · ${Math.round(d.pw)} W</span></div>`;
  h+='<div class="lv-chips">'+ch.map(c=>`<span class="lv-chip ${c[1]>=LIM[c[3]]?'bad':''}"><i>${c[0]}</i><b>${Math.round(c[1])}${c[2]}</b></span>`).join('')+'</div>';
  h+=`<svg class="lv-spark" viewBox="0 0 300 40" preserveAspectRatio="none">${sp(d.h_gpu,'#4d7dff',100)}${sp(d.h_temp,'#e0a030',100)}${sp(d.h_vram,'#9b7bff',100)}</svg>`;
  const s=d.status;const fases=s.activo?s.fases:s.ultimo;
  if(s.activo){const p=Math.round(s.pct*100);h+=`<div class="lv-job"><div class="lv-row"><span>${s.msg}</span><b>${p}% · ${Math.round(s.seg)} s</b></div><div class="lv-bar"><div style="width:${p}%"></div></div></div>`}
  if(fases&&fases.length){const tot=fases.reduce((a,f)=>a+Math.max(f[2]-f[1],0.01),0);
   h+=`<div class="lv-row lv-sub"><span>${s.activo?'Tiempo por fase (en curso)':'Último modelo: tiempo por fase'}</span><b>${Math.round(tot)} s</b></div><div class="lv-stack">`+
     fases.map(f=>{const dur=f[2]-f[1],w=100*Math.max(dur,0.01)/tot,lento=d.normal[f[0]]&&dur>2.2*d.normal[f[0]]&&dur>20;
       return `<div title="${f[0]} ${dur.toFixed(1)} s" class="${lento?'slow':''}" style="width:${w}%;background:${FC[f[0]]||'#666'}">${w>9?f[0]+' '+Math.round(dur)+'s':''}</div>`}).join('')+'</div>';
   const lentos=fases.filter(f=>d.normal[f[0]]&&(f[2]-f[1])>2.2*d.normal[f[0]]&&(f[2]-f[1])>20);
   if(lentos.length)h+=`<div class="lv-bad lv-why">⚠ Lento: ${lentos.map(f=>`${f[0]} ${Math.round(f[2]-f[1])} s (normal ~${Math.round(d.normal[f[0]])} s)`).join(' · ')}${d.gpu>90?' — GPU al tope':''}${d.cola>0?' — hay trabajos en cola':''}</div>`}
  el.innerHTML=h}
 setInterval(tick,1500);setTimeout(tick,300);
})();
</script>"""


def start_monitor():
    """Hilo que cada segundo escribe el estado (GPU, temperatura, fase actual
    y tiempos por fase) en un JSON que la pagina lee directamente."""
    if _MON["hilo"] is not None:
        return
    from . import engine as _eng
    path = os.path.join(config.OUT_DIR, "_monitor.json")

    def loop():
        while True:
            try:
                vals, vram_txt, vm, pw = _sample()
                st = _eng.STATUS
                e = get_engine()
                n = {"Forma": e.eta.get("forma", 8), "Textura": e.eta.get("textura", 35),
                     "Blender": e.eta.get("blender", 40), "Limpieza": 8, "Fondo": 2, "ZIP": 3}
                d = dict(vals, vram_txt=vram_txt, pw=pw, h_gpu=_HIST["gpu"][-60:],
                         h_temp=_HIST["temp"][-60:], h_vram=_HIST["vram"][-60:],
                         cola=getattr(e, "jobs", {}).get("en_cola", 0), normal=n,
                         status={"activo": st["activo"], "msg": st["msg"], "pct": st["pct"],
                                 "seg": (time.time() - st["t0"]) if st["t0"] else 0,
                                 "fases": st["fases"], "ultimo": st["ultimo"]})
                tmp = path + ".tmp"
                with open(tmp, "w") as fh:
                    json.dump(d, fh)
                os.replace(tmp, path)
            except Exception:
                pass
            time.sleep(1.0)

    _MON["hilo"] = threading.Thread(target=loop, daemon=True)
    _MON["hilo"].start()


def monitor_html():
    """Grafica en vivo (90 s). Rojo cuando algo pasa del limite o hay cola."""
    try:
        vals, vram_txt, vm, pw = _sample()
    except Exception as e:
        return f"<div style='color:#9a9daa'>Monitor no disponible: {e}</div>"
    eng = get_engine()
    jobs = getattr(eng, "jobs", {"activos": 0, "en_cola": 0})
    LIM = dict(gpu=97, vram=92, ram=90, cpu=95, temp=83)
    series = [("GPU", "gpu", "#5b5bf0", "%"), ("VRAM", "vram", "#9b7bff", "%"),
              ("RAM", "ram", "#1f9d6b", "%"), ("CPU", "cpu", "#e0a030", "%"),
              ("Temp", "temp", "#4fb3d9", "°C")]
    W, H = 600, 90
    paths, chips = [], []
    alert = []
    for name, k_, col, u in series:
        h = _HIST[k_]
        over = h and h[-1] >= LIM[k_]
        c = "#e5484d" if over else col
        if over:
            alert.append(name)
        if len(h) > 1:
            pts = " ".join(f"{W * i / 89:.1f},{H - H * min(x, 100) / 100:.1f}"
                           for i, x in enumerate(h[-90:]))
            paths.append(f"<polyline points='{pts}' fill='none' stroke='{c}' "
                         f"stroke-width='{2.5 if over else 1.6}'/>")
        chips.append(f"<span style='padding:3px 9px;border-radius:12px;background:"
                     f"{'#e5484d33' if over else '#2a2d36'};color:{c};border:1px solid "
                     f"{c if over else '#2a2d36'}'>{name} <b>{h[-1]:.0f}{u}</b></span>")
    cola = jobs.get("en_cola", 0)
    if cola > 0:
        alert.append(f"{cola} en cola")
    chips.append(f"<span style='padding:3px 9px;border-radius:12px;background:"
                 f"{'#e5484d33' if cola else '#2a2d36'};color:{'#e5484d' if cola else '#e8e9ee'}'>"
                 f"Trabajos <b>{jobs.get('activos', 0)}</b> · cola <b>{cola}</b></span>")
    lim_line = f"<line x1='0' x2='{W}' y1='{H * 0.1}' y2='{H * 0.1}' stroke='#e5484d55' stroke-dasharray='4 4'/>"
    head = ("<b style='color:#e5484d'>⚠ Saturado: " + ", ".join(alert) + "</b>") if alert \
        else "<span style='color:#1f9d6b'>● Todo normal</span>"
    return (f"<div style='background:#20222b;border:1px solid {'#e5484d' if alert else '#2a2d36'};"
            f"border-radius:12px;padding:8px 12px;font:13px system-ui;color:#e8e9ee'>"
            f"<div style='display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px'>{head}"
            f"<span style='color:#9a9daa'>VRAM {vram_txt} · RAM {vm.used / 2**30:.0f}/"
            f"{vm.total / 2**30:.0f} GB · {pw:.0f} W</span></div>"
            f"<svg viewBox='0 0 {W} {H}' preserveAspectRatio='none' style='width:100%;height:70px;"
            f"margin:6px 0'>{lim_line}{''.join(paths)}</svg>"
            f"<div style='display:flex;gap:6px;flex-wrap:wrap'>{''.join(chips)}</div></div>")


CSS = """
body, .gradio-container {background:#17181d !important}
.gradio-container {max-width:1500px !important; color:#e8e9ee}
#hdr h1 {font-size:22px; margin:0}
#hdr p {color:#9a9daa; margin:2px 0 0}
#side {background:#1b1d24; border:1px solid #2a2d36; border-radius:16px; padding:10px}
#stage {background:#1b1d24; border:1px solid #2a2d36; border-radius:16px; padding:10px}
#side .block, #stage .block {background:#20222b !important; border-color:#2a2d36 !important}
#gen {background:linear-gradient(90deg,#5b5bf0,#7c4dff) !important; color:#fff !important;
      font-size:17px !important; border-radius:12px !important; box-shadow:0 0 24px #5b5bf055}
#rigsel .wrap {gap:6px} #rigsel label {border-radius:20px !important}
footer {display:none !important}
#livebox {background:#151824; border:1px solid #2a2f45; border-radius:14px; padding:8px 12px;
          color:#c9cee0; font-size:12px; margin-bottom:6px}
.lv-top,.lv-row {display:flex; justify-content:space-between; gap:8px; align-items:center}
.lv-ok {color:#1f9d6b} .lv-bad {color:#e5484d; font-weight:600} .lv-sub {color:#8a90a8}
.lv-chips {display:grid; grid-template-columns:repeat(5,1fr); gap:6px; margin:6px 0}
.lv-chip {background:#1d2130; border:1px solid #2a2f45; border-radius:10px; padding:4px 6px; text-align:center}
.lv-chip i {display:block; font-style:normal; color:#8a90a8; font-size:10px}
.lv-chip b {color:#8fb0ff; font-size:15px} .lv-chip.bad {border-color:#e5484d} .lv-chip.bad b {color:#e5484d}
.lv-spark {width:100%; height:34px; display:block}
.lv-job {margin:6px 0} .lv-bar {height:8px; background:#0f1118; border-radius:5px; overflow:hidden; margin-top:3px}
.lv-bar div {height:100%; background:linear-gradient(90deg,#3d6bff,#9b7bff); transition:width .6s}
.lv-stack {display:flex; height:18px; border-radius:6px; overflow:hidden; margin-top:3px}
.lv-stack div {color:#fff; font-size:10px; line-height:18px; text-align:center; white-space:nowrap; overflow:hidden}
.lv-stack div.slow {outline:2px solid #e5484d; outline-offset:-2px}
.lv-why {margin-top:4px}
.tab .tcs {display:grid; grid-template-columns:repeat(7,1fr); gap:6px}
.tc {border:1px solid #2a2f45; border-radius:10px; padding:6px 2px; text-align:center;
     color:#5d6380; background:#151824; font-size:11px}
.tc svg {width:28px; height:28px; display:block; margin:0 auto 3px; fill:none;
         stroke:currentColor; stroke-width:2.2; stroke-linecap:round; stroke-linejoin:round}
.tc.ok {color:#4d7dff; border-color:#2b4da8; box-shadow:0 0 12px #3d6bff33}
.tc.run {color:#9db6ff; border-color:#6d8dff; animation:tcp 1.2s ease-in-out infinite}
@keyframes tcp {50% {box-shadow:0 0 16px #6d8dffaa}}
.tds {display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:8px; margin-top:8px}
.td {border:1px solid #2a2f45; border-radius:12px; padding:8px 10px; background:#151824;
     color:#c9cee0; font-size:13px}
.td > b {color:#8fb0ff; font-size:12px; text-transform:uppercase; letter-spacing:.04em}
.warnq {color:#e0a030 !important}
.kv {display:flex; justify-content:space-between; gap:8px; border-bottom:1px dashed #252a3d;
     padding:3px 0} .kv:last-child {border:0} .kv span {color:#8a90a8}
.kpis {display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:6px}
.kpi {border:1px solid #2a2f45; border-radius:14px; padding:10px; background:#151824; color:#8a90a8;
      font-size:12px} .kpi svg {width:22px; height:22px; fill:none; stroke:#4d7dff; stroke-width:2.6;
      stroke-linecap:round; stroke-linejoin:round; display:block; margin-bottom:4px}
.kpi b {display:block; color:#4d7dff; font-size:24px; margin-top:2px}
#filtros label {border-radius:20px !important; padding:4px 10px !important}
@media (max-width:820px) {.tab .tcs {grid-template-columns:repeat(4,1fr)} .tc {font-size:10px}}
.hdr {display:flex; justify-content:space-between; align-items:center; width:100%}
.hdr .ttl {font-size:26px; font-weight:700; color:#e8e9ee}
.hdr .chip {text-align:right; color:#9a9daa; font-size:12px; line-height:1.3}
.hdr .dot {display:inline-block; width:9px; height:9px; border-radius:50%; background:#3d6bff;
           box-shadow:0 0 10px #3d6bff; margin-right:6px}
@media (max-width: 820px) {
  .gradio-container {padding:6px !important}
  #main {flex-direction:column !important}
  #stage {order:-1; padding:4px !important}          /* el visor primero, como una app */
  #side {padding:6px !important}
  #gen {position:sticky; bottom:10px; z-index:30}      /* Generar siempre a mano */
  #stage iframe, #stage .vph {height:56vh !important; min-height:340px}
  #review button {padding:6px 2px !important; font-size:12px !important}
  .hdr .ttl {font-size:21px}
}
#review {border:1px solid #3b3d8f !important; border-radius:14px; padding:6px;
         background:linear-gradient(180deg,#20223a,#1b1d24) !important}
#votes button {min-width:0 !important}
"""


def build_ui():
    eng = get_engine()
    P = eng.p
    theme = gr.themes.Base(primary_hue="indigo", neutral_hue="slate",
                           font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"]).set(
        body_background_fill="#17181d", body_background_fill_dark="#17181d",
        block_background_fill="#20222b", block_background_fill_dark="#20222b",
        block_border_color="#2a2d36", block_border_color_dark="#2a2d36",
        body_text_color="#e8e9ee", body_text_color_dark="#e8e9ee",
        block_label_text_color="#9a9daa", block_title_text_color="#e8e9ee",
        input_background_fill="#17181d", input_background_fill_dark="#17181d",
        button_secondary_background_fill="#2c2f3a", button_secondary_text_color="#e8e9ee",
        button_secondary_background_fill_dark="#2c2f3a", button_secondary_text_color_dark="#e8e9ee",
        checkbox_label_background_fill="#2a2d36", checkbox_label_background_fill_dark="#2a2d36",
        checkbox_label_text_color="#e8e9ee", checkbox_label_text_color_dark="#e8e9ee")
    best = "Detallado" if P["vram_gb"] >= 38 else "Turbo"
    os.makedirs(config.OUT_DIR, exist_ok=True)
    start_monitor()
    live_js = LIVE_JS.replace("__PATH__", os.path.join(config.OUT_DIR, "_monitor.json"))
    with gr.Blocks(title="AP Model 3D Foto", theme=theme, css=CSS, head=live_js,
                   js="()=>{document.body.classList.add('dark')}") as demo:
        with gr.Row(elem_id="hdr"):
            gr.HTML(f"<div class='hdr'><div class='ttl'>AP Model 3D Foto</div>"
                    f"<div class='chip'><span class='dot'></span>{P['gpu'].replace('NVIDIA ', '')[:18]}"
                    f"<br><small>{P['perfil'].capitalize()}</small></div></div>")
        gr.HTML("<div id='livebox'>Conectando con el monitor…</div>")
        with gr.Row(equal_height=False, elem_id="main"):
            # ------------------------------------------------ panel izquierdo
            with gr.Column(scale=3, min_width=320, elem_id="side"):
                with gr.Tabs():
                    with gr.Tab("Generar"):
                        prompt = gr.Textbox(label="O descríbelo con texto (como Tripo)",
                                            placeholder="Ej.: a medieval knight with silver armor",
                                            info="Si no subes foto, FLUX crea la imagen desde el texto "
                                                 "y luego el 3D. Funciona mejor en inglés.",
                                            lines=2, max_lines=4)
                        front = gr.Image(label="Foto de frente", type="pil",
                                         image_mode="RGBA", height=230)
                        with gr.Accordion("Más vistas (espalda, perfiles, hoja)", open=False):
                            with gr.Row():
                                back = gr.Image(label="Espalda", type="pil", image_mode="RGBA", height=120)
                                left = gr.Image(label="Perfil izq.", type="pil", image_mode="RGBA", height=120)
                                right = gr.Image(label="Perfil der.", type="pil", image_mode="RGBA", height=120)
                            sheet = gr.Image(label="Hoja de vistas", type="pil", height=120)
                            sheet_order = gr.Dropdown(
                                ["front,left,back,right", "front,right,back,left",
                                 "front,back", "front,left,back", "left,front,right,back"],
                                value="front,left,back,right", label="Orden de la hoja")
                        with gr.Accordion("Esqueleto (Rig)", open=True):
                            rig = gr.Radio(list(RIGS), value="Auto", show_label=False,
                                           elem_id="rigsel")
                            gr.Markdown("<small>Auto detecta persona, animal de 4 patas, "
                                        "cabeza/busto (mueve boca, ojos y cabeza) u objeto "
                                        "(flota, gira, rebota, baila).</small>")
                            activo = gr.Radio(["Auto", "Personaje", "Prop rígido", "Prop articulado"],
                                              value="Auto", label="Tipo de activo",
                                              info="Prop rígido: sin esqueleto (cajas, relojes, "
                                                   "estatuas). Prop articulado: partes rígidas que se "
                                                   "mueven (ruedas, puertas). Personaje: rig Mixamo.")
                            altura_prop = gr.Slider(0.05, 3.0, 0.40, step=0.01,
                                                    label="Altura real del prop (m)")
                            detalle = gr.Checkbox(True, label="Esqueleto detallado",
                                                  info="Dedos de manos y pies, ojos y mandíbula "
                                                       "(66 huesos en vez de 23)")
                        with gr.Accordion("Altura real", open=True):
                            height = gr.Slider(0.2, 5, 1.7, step=0.01, label="metros")
                        with gr.Accordion("Mapas de relieve", open=False):
                            relieve_on = gr.Checkbox(True, label="Relieve realista desde la textura")
                            relieve = gr.Slider(0.1, 2.5, 0.8, step=0.1, label="Intensidad")
                        with gr.Accordion("Calidad", open=False):
                            motor = gr.Radio(["Hunyuan3D (rápido)", "TripoSG (más detalle)"],
                                             value="Hunyuan3D (rápido)", label="Motor de forma",
                                             info="TripoSG es el modelo abierto de Tripo AI")
                            preset = gr.Radio(list(PRESETS), value=best, label="Preajuste",
                                              info="Detallado: Turbo con malla 512 y 150 000 caras (recomendado). "
                                                   "Turbo: el mas rapido (60 000 caras; la textura tarda menos "
                                                   "con menos caras). Maxima: 50 pasos, el mas lento")
                            tex = gr.Dropdown(["1024", "2048", "4096"], value=str(PRESETS[best][3]),
                                              label="Textura (px)")
                            roblox = gr.Radio(["No", "Roblox 12k", "Roblox 15k", "High 40k"],
                                              value="Roblox 12k", label="Exportación para Roblox Studio",
                                              info="FBX reducido (triángulos máx.), escala real "
                                                   "aplicada, texturas embebidas")
                            tex_rapida = gr.Checkbox(False, label="Textura rápida",
                                                     info="Hornea a 1024 en vez de 2048: tarda "
                                                          "menos y los colores salen algo menos nítidos")
                            with gr.Row():
                                remove_bg = gr.Checkbox(True, label="Quitar fondo")
                                texture = gr.Checkbox(True, label="Textura con IA")
                        with gr.Accordion("Videos (opcional, más lento)", open=False):
                            make_videos = gr.Checkbox(False, label="Generar videos MP4",
                                                      info="No hace falta: el modelo interactivo ya trae todas las animaciones")
                            video = gr.Dropdown(ANIMS, value="Caminar", label="Animación del video")
                            turntable = gr.Checkbox(True, label="Video giro 360")
                        with gr.Accordion("🎲 Ver 4 variantes de forma antes (10-20 s)", open=False):
                            gr.Markdown("<small>La IA da formas distintas con cada semilla. "
                                        "Mira 4 y toca la que te guste: se usará esa.</small>")
                            var_btn = gr.Button("Generar 4 variantes", size="sm")
                            var_gal = gr.Gallery(columns=2, height=360, allow_preview=False,
                                                 show_label=False)
                            var_msg = gr.Markdown("")
                        btn = gr.Button("Generar 3D con IA + Esqueleto", elem_id="gen", size="lg")
                        ex = sorted(glob.glob(os.path.join(EXAMPLES_DIR, "*.png")))[:8]
                        if ex:
                            gr.Examples(ex, inputs=[front], label="Ejemplos")
                    with gr.Tab("Mis Modelos"):
                        kpis = gr.HTML(kpis_html())
                        filtro = gr.Radio(list(FILTROS), value="Todos", show_label=False,
                                          elem_id="filtros")
                        g_btn = gr.Button("Actualizar", size="sm")
                        gal = gr.Gallery(label="Toca uno para abrirlo en el estudio",
                                         columns=2, height=520, allow_preview=False)
                        h_out = gr.File(file_count="multiple", label="ZIPs guardados")
                    with gr.Tab("Escena"):
                        gr.Markdown("**Crea un cuarto completo.** Un objeto por línea, con su "
                                    "altura en metros después de «|». Se genera cada uno (texto → "
                                    "3D con esqueleto) y se acomodan: los grandes contra las "
                                    "paredes, los chicos al centro. Mejor en inglés.")
                        esc_txt = gr.Textbox(lines=6, label="Objetos",
                                             value="wooden wardrobe with two doors | 1.9\n"
                                                   "modern grey sofa | 0.85\n"
                                                   "small round coffee table | 0.45\n"
                                                   "floor lamp | 1.6\n"
                                                   "cat | 0.3")
                        with gr.Row():
                            esc_w = gr.Slider(3, 10, 5, step=0.5, label="Ancho del cuarto (m)")
                            esc_d = gr.Slider(3, 10, 4, step=0.5, label="Fondo (m)")
                        esc_btn = gr.Button("Crear escena", variant="primary")
                        esc_msg = gr.Markdown("")
                    with gr.Tab("Avanzado"):
                        with gr.Row():
                            steps = gr.Slider(3, 100, PRESETS[best][0], step=1,
                                              label="Pasos (≤10 = Turbo)")
                            octree = gr.Slider(192, 640, PRESETS[best][1], step=32, label="Octree")
                        faces = gr.Slider(10000, 400000, PRESETS[best][2], step=5000,
                                          label="Caras máximas")
                        with gr.Row():
                            seed = gr.Number(1234, label="Semilla", precision=0)
                            rand_seed = gr.Checkbox(False, label="Aleatoria")
                        guidance = gr.Slider(1, 15, 5.0, step=0.5, label="Fidelidad a la foto")
                        rotate = gr.Slider(-180, 180, 0, step=90, label="Girar si mira atrás (°)")
                        with gr.Row():
                            video_res = gr.Dropdown([480, 720, 1080, 1440], value=P["video_res"],
                                                    label="Resolución video")
                            samples = gr.Slider(4, 256, P["samples"], step=4, label="Calidad render")
                        with gr.Accordion("Lote (varias fotos)", open=False):
                            b_files = gr.File(file_count="multiple", file_types=["image"], label="Fotos")
                            b_rig = gr.Radio(list(RIGS), value="Auto", label="Esqueleto")
                            b_video = gr.Dropdown(ANIMS, value="Caminar", label="Animación")
                            b_btn = gr.Button("Procesar lote")
                            b_log = gr.Markdown()
                            b_out = gr.File(file_count="multiple", label="ZIPs")
                        r_btn = gr.Button("Ver uso de RAM / GPU", size="sm")
                        r_out = gr.Markdown()
            # ------------------------------------------------ escenario
            with gr.Column(scale=7, elem_id="stage"):
                tablero = gr.HTML(tablero_html(0))
                status = gr.Markdown("Sube una foto y pulsa **Generar**. Veras primero la "
                                     "malla, luego la textura y al final el modelo animado.",
                                     min_height=40)
                with gr.Tabs() as tabs:
                    with gr.Tab("1 · Malla", id="malla"):
                        m_clay = gr.HTML(viewer_html(msg="Aquí aparecerá la malla"))
                    with gr.Tab("2 · Textura", id="textura"):
                        m_tex = gr.HTML(viewer_html(msg="Aquí aparecerá el modelo con textura"))
                    with gr.Tab("3 · Estudio animado", id="estudio"):
                        view = gr.HTML(viewer_html())
                with gr.Group(elem_id="review"):
                    review = gr.Markdown("### ¿Salió bien?\nCuando termine un modelo, vota "
                                         "aquí. El proyecto aprende de tus respuestas.")
                    with gr.Row():
                        tipo_fix = gr.Dropdown(list(TIPOS_UI.values()), value="Persona",
                                               label="Tipo de modelo", scale=3)
                        fix_btn = gr.Button("Corregir esqueleto", variant="primary", scale=2)
                    comentario = gr.Textbox(label="Comentario (opcional): ¿qué salió mal?",
                                            lines=1, max_lines=3)
                    votes = []
                    with gr.Row(elem_id="votes"):
                        for q, lab in (("forma", "Forma"), ("textura", "Textura"),
                                       ("esqueleto", "Esqueleto")):
                            votes.append((q, True, gr.Button(f"👍 {lab}", size="sm")))
                            votes.append((q, False, gr.Button(f"👎 {lab}", size="sm")))
                    with gr.Row():
                        retry_btn = gr.Button("🔁 Reintentar con lo aprendido", variant="secondary")
                        best_btn = gr.Button("⭐ Usar mis mejores ajustes", variant="secondary")
                    review_out = gr.Markdown("")
                datos = gr.HTML("")
                with gr.Accordion("Resumen técnico completo", open=False):
                    resumen = gr.Markdown("")
                out_files = gr.File(label="Descargas (ZIP con todo + archivos sueltos)",
                                    file_count="multiple")
                with gr.Accordion("Lo que el proyecto ha aprendido", open=False):
                    learn_md = gr.Markdown("")
                with gr.Accordion("Videos (solo si activaste «Generar videos»)", open=False):
                    with gr.Row():
                        v_anim = gr.Video(label="Animación", height=280)
                        v_360 = gr.Video(label="Giro 360", height=280)
                with gr.Accordion("Monitor de GPU / RAM (detalle)", open=False):
                    mon = gr.HTML(monitor_html(), elem_id="mon")
                    mon_btn = gr.Button("Actualizar monitor", size="sm")
        job = gr.State("")
        cur_dir = gr.State("")

        def apply_preset(name):
            s, o, f, t = PRESETS[name]
            return s, o, f, str(t)

        preset.change(apply_preset, preset, [steps, octree, faces, tex])
        preset.change(lambda n: n == "Turbo", preset, tex_rapida)
        final_outs = [view, tabs, m_clay, m_tex, v_anim, v_360, out_files, status, mon,
                      cur_dir, review, tipo_fix, tablero, datos, resumen]
        gen_inputs = [front, back, left, right, sheet, sheet_order, remove_bg, steps, octree,
                      faces, tex, seed, rand_seed, guidance, rig, height, rotate, video,
                      video_res, samples, turntable, texture, relieve_on, relieve, make_videos,
                      detalle, motor, prompt, tex_rapida, activo, altura_prop, roblox]

        def chain(ev):
            return (ev.then(step_malla, gen_inputs, [front, job, m_clay, tabs, status, seed, tablero],
                            concurrency_id="gen", concurrency_limit=P["workers"], **_spo(status))
                    .success(step_textura, job, [m_tex, tabs, status, tablero], concurrency_id="gen",
                             **_spo(status))
                    .success(step_final, job, final_outs, concurrency_id="gen", **_spo(status)))

        chain(btn.click(lambda: None, None, None))

        def apply_learned(d, mo, tr, de, sd):
            from . import memoria
            cambios, why = memoria.recommend(d, mo, tr, de)
            if cambios.get("nueva_semilla"):
                sd = random.randint(0, 2**31 - 1)
            if "motor" in cambios:
                mo = "TripoSG (más detalle)" if cambios["motor"] == "triposg" else "Hunyuan3D (rápido)"
            tr = cambios.get("tex_rapida", tr)
            de = cambios.get("detalle", de)
            return mo, tr, de, sd, f"🔁 Reintentando con: **{why}**…"

        def apply_best(mo, tr, de, st, oc, fa):
            from . import memoria
            aj, txt = memoria.best_settings()
            if not aj:
                return mo, tr, de, st, oc, fa, "⭐ " + txt
            mo = "TripoSG (más detalle)" if aj.get("motor") == "triposg" else "Hunyuan3D (rápido)"
            return (mo, bool(aj.get("tex_rapida")), aj.get("detalle", True) is not False,
                    aj.get("steps") or st, aj.get("octree") or oc, aj.get("faces") or fa,
                    "⭐ Aplicados. " + txt)

        best_btn.click(apply_best, [motor, tex_rapida, detalle, steps, octree, faces],
                       [motor, tex_rapida, detalle, steps, octree, faces, review_out])
        chain(retry_btn.click(apply_learned, [cur_dir, motor, tex_rapida, detalle, seed],
                              [motor, tex_rapida, detalle, seed, review_out]))
        mon_btn.click(monitor_html, None, mon)

        def do_scene(txt, w_, d_, progress=gr.Progress()):
            try:
                out, inf = get_engine().build_scene(txt, w_, d_,
                                                    progress=lambda f, m: progress(f, desc=m))
            except Exception as e:
                raise gr.Error(str(e))
            zp = out + ".zip"
            msg = (f"✅ Escena de {inf['cuarto_m'][0]} × {inf['cuarto_m'][1]} m con "
                   f"{len(inf['colocados'])} objetos" +
                   (f" · no cupieron: {', '.join(inf['no_cupieron'])}" if inf["no_cupieron"] else "") +
                   ". Archivos: `escena.glb` (con animaciones) y `escena.blend`.")
            return (viewer_html(out, view="tex"), gr.update(selected="estudio"),
                    [zp] + _files(out), msg, msg)

        esc_btn.click(do_scene, [esc_txt, esc_w, esc_d], [view, tabs, out_files, status, esc_msg],
                      concurrency_id="gen")
        var_seeds = gr.State([])

        def do_variants(img, mo, sd, prompt_, progress=gr.Progress()):
            eng = get_engine()
            if img is None:
                if not (prompt_ or "").strip():
                    raise gr.Error("Sube una foto o escribe una descripción.")
                img = eng.text_to_image(prompt_, int(sd))
            progress(0.1, desc="Creando 4 formas…")
            res = eng.shape_variants(img, 4, None,
                                     motor="triposg" if str(mo).startswith("Tripo") else "hunyuan")
            return ([(im, f"Semilla {s_}") for s_, im in res], [s_ for s_, _ in res],
                    "Toca la que te guste y luego pulsa **Generar**.")

        def pick_variant(seeds, evt: gr.SelectData):
            sd = seeds[evt.index]
            return sd, False, f"✅ Elegida la variante {evt.index + 1} (semilla {sd}). Pulsa **Generar**."

        var_btn.click(do_variants, [front, motor, seed, prompt], [var_gal, var_seeds, var_msg],
                      concurrency_id="gen")
        var_gal.select(pick_variant, var_seeds, [seed, rand_seed, var_msg])
        for q, ok, b in votes:
            b.click(lambda d, c, q=q, ok=ok: do_vote(d, q, ok, c), [cur_dir, comentario],
                    [review_out, learn_md])
        fix_btn.click(fix_type, [cur_dir, tipo_fix], [view, tabs, out_files, status, learn_md],
                      concurrency_id="gen")
        g_btn.click(lambda f_: (my_models(f_), history(), kpis_html()), filtro, [gal, h_out, kpis])
        filtro.change(my_models, filtro, gal)
        gal.select(open_model, filtro, final_outs)
        b_btn.click(batch, [b_files, b_rig, b_video], [b_out, b_log], concurrency_id="gen")
        r_btn.click(resources, None, r_out)
        def _on_load():
            from . import memoria
            return my_models(), history(), memoria.stats_md(), kpis_html()
        demo.load(_on_load, None, [gal, h_out, learn_md, kpis])
        gr.api(rig_edit, api_name="rig_edit")
    demo.queue(default_concurrency_limit=P["workers"], max_size=20)
    return demo



# ------------------------------------------------------------ lanzar
_SERVERS = {}


def _free_port(port):
    """Cierra lo que esta celda lanzo antes y busca un puerto libre."""
    import socket
    for k in ("inline", "web"):
        d = _SERVERS.pop(k, None)
        if d is not None:
            try:
                d.close()
            except Exception:
                pass
    t = _SERVERS.pop("tunnel", None)
    if t is not None:
        t.terminate()
    for p in range(port, port + 40):
        with socket.socket() as s:
            try:
                s.bind(("0.0.0.0", p))
                return p
            except OSError:
                continue
    return port


def launch_inline(port=7860):
    port = _free_port(port)
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=port, inline=True, share=False,
                prevent_thread_lock=True, show_error=True, height=1100,
                allowed_paths=[config.OUT_DIR, EXAMPLES_DIR])
    _SERVERS["inline"] = demo
    return demo


def _cloudflared():
    exe = "/content/cloudflared"
    if not os.path.exists(exe):
        subprocess.run(["wget", "-q", "-O", exe,
                        "https://github.com/cloudflare/cloudflared/releases/latest/download/"
                        "cloudflared-linux-amd64"], check=True)
        os.chmod(exe, 0o755)
    return exe


def launch_web(password="", user="ap", port=7861):
    if not password:
        password = secrets.token_urlsafe(9)
    port = _free_port(port)
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=port, share=False, auth=(user, password),
                auth_message="AP Model 3D Foto", prevent_thread_lock=True, show_error=True,
                allowed_paths=[config.OUT_DIR, EXAMPLES_DIR], max_file_size="25mb")
    _SERVERS["web"] = demo
    url = None
    try:
        exe = _cloudflared()
        proc = subprocess.Popen([exe, "tunnel", "--no-autoupdate", "--url",
                                 f"http://127.0.0.1:{port}"],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        t = time.time()
        while time.time() - t < 60:
            line = proc.stdout.readline()
            m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line or "")
            if m:
                url = m.group(0)
                break
        threading.Thread(target=lambda: [None for _ in proc.stdout], daemon=True).start()
        _SERVERS["tunnel"] = proc
    except Exception as e:
        print("Cloudflare no disponible:", e)
    if url is None:
        print("Usando el enlace publico de Gradio como respaldo...")
        demo.close()
        demo = build_ui()
        demo.launch(share=True, auth=(user, password), prevent_thread_lock=True,
                    allowed_paths=[config.OUT_DIR, EXAMPLES_DIR])
        url = demo.share_url
        _SERVERS["web"] = demo
    return url, user, password
