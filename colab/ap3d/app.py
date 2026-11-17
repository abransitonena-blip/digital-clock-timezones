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
    order = ["modelo_animado.glb", "modelo_web.glb", "modelo_rig.fbx", "modelo.blend", "modelo_texturizado.glb",
             "modelo_estatico.obj", "modelo_estatico.mtl", "modelo_impresion3d.stl",
             "piezas.glb", "pesos.glb", "arcilla.glb", "rig_info.json"]
    fs = [os.path.join(d, f) for f in order if os.path.exists(os.path.join(d, f))]
    fs += [f for f in sorted(glob.glob(os.path.join(d, "*")))
           if f not in fs and not f.endswith((".log",))]
    return fs


def _summary(info):
    a = info.get("ajustes", {})
    lines = [
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
    if info.get("lod_caras"):
        lines.append("LOD ligeros: " + ", ".join(
            f"{k} ({v:,} caras)" for k, v in info["lod_caras"].items()))
    if info.get("mapas_relieve"):
        lines.append("Relieve: mapa de normales creado desde la textura")
    if "vertices_sin_peso_reparados" in info:
        lines.append(f"Pesos: 100 % de la malla sigue al esqueleto "
                     f"({info['vertices_sin_peso_reparados']} vertices reparados)")
    for w in info.get("avisos", []):
        lines.append(f"⚠️ {w}")
    return "\n\n".join(lines)


RIGS = {"Auto": "auto", "Humano": "humanoide", "Criatura": "cuadrupedo", "Sin esqueleto": "ninguno"}


def viewer_html(d=None, height=600, view=None, wire=False, etapa=None, msg=None):
    """Estudio 3D (three.js) en un iframe servido desde la carpeta del resultado."""
    if not d or not os.path.exists(os.path.join(d, "estudio.html")):
        return (f"<div style='height:{height}px;display:flex;align-items:center;"
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
    """show_progress_on solo si esta version de Gradio lo admite."""
    import inspect
    ok = "show_progress_on" in inspect.signature(gr.Button.click).parameters
    return {"show_progress_on": [comp]} if ok else {}


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
               detalle=True, progress=gr.Progress()):
    """Etapa 1: lanza el trabajo y devuelve la malla en cuanto existe."""
    if front is None and sheet is None:
        raise gr.Error("Sube al menos la foto de frente (o una hoja de vistas).")
    if rand_seed:
        seed = random.randint(0, 2**31 - 1)
    eng = get_engine()
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
                                detalle=bool(detalle))
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
    return (jid, viewer_html(d, view="clay", wire=True, etapa="Etapa 1/3 · Malla"),
            gr.update(selected="malla"),
            f"**Etapa 1/3 · Malla lista** ({time.time() - st['t0']:.0f} s). Pintando la textura…",
            int(seed))


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
            "Poniendo esqueleto y animaciones…")


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
            f"✅ **Modelo listo en {time.time() - st['t0']:.0f} s**\n\n" + _summary(info),
            monitor_html())


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


def my_models():
    """Galeria de modelos guardados (vista previa o foto de frente)."""
    items = []
    for d in sorted(glob.glob(os.path.join(config.OUT_DIR, "*")), reverse=True):
        if not os.path.isdir(d):
            continue
        img = next((os.path.join(d, f) for f in ("vista_previa.png", "vista_front.png")
                    if os.path.exists(os.path.join(d, f))), None)
        if img:
            items.append((img, os.path.basename(d)[:15].replace("_", " ")))
    return items[:60]


def open_model(evt: gr.SelectData):
    dirs = [d for d in sorted(glob.glob(os.path.join(config.OUT_DIR, "*")), reverse=True)
            if os.path.isdir(d) and any(os.path.exists(os.path.join(d, f)) for f in
                                        ("vista_previa.png", "vista_front.png"))]
    d = dirs[evt.index]
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
            ([zp] if os.path.exists(zp) else []) + _files(d), _summary(info), monitor_html())


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
    with gr.Blocks(title="AP Model 3D Foto", theme=theme, css=CSS,
                   js="()=>{document.body.classList.add('dark')}") as demo:
        with gr.Row(elem_id="hdr"):
            gr.Markdown(f"# AP Model 3D Foto\n{config.describe(P)}")
        with gr.Row(equal_height=False):
            # ------------------------------------------------ panel izquierdo
            with gr.Column(scale=3, min_width=320, elem_id="side"):
                with gr.Tabs():
                    with gr.Tab("Generar"):
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
                            detalle = gr.Checkbox(True, label="Esqueleto detallado",
                                                  info="Dedos de manos y pies, ojos y mandíbula "
                                                       "(66 huesos en vez de 23)")
                        with gr.Accordion("Altura real", open=True):
                            height = gr.Slider(0.2, 5, 1.7, step=0.01, label="metros")
                        with gr.Accordion("Mapas de relieve", open=False):
                            relieve_on = gr.Checkbox(True, label="Relieve realista desde la textura")
                            relieve = gr.Slider(0.1, 2.5, 0.8, step=0.1, label="Intensidad")
                        with gr.Accordion("Calidad", open=False):
                            preset = gr.Radio(list(PRESETS), value=best, label="Preajuste",
                                              info="Detallado: Turbo con malla 512 y 150 000 caras (recomendado). "
                                                   "Turbo: el mas rapido (60 000 caras; la textura tarda menos "
                                                   "con menos caras). Maxima: 50 pasos, el mas lento")
                            tex = gr.Dropdown(["1024", "2048", "4096"], value=str(PRESETS[best][3]),
                                              label="Textura (px)")
                            with gr.Row():
                                remove_bg = gr.Checkbox(True, label="Quitar fondo")
                                texture = gr.Checkbox(True, label="Textura con IA")
                        with gr.Accordion("Videos (opcional, más lento)", open=False):
                            make_videos = gr.Checkbox(False, label="Generar videos MP4",
                                                      info="No hace falta: el modelo interactivo ya trae todas las animaciones")
                            video = gr.Dropdown(ANIMS, value="Caminar", label="Animación del video")
                            turntable = gr.Checkbox(True, label="Video giro 360")
                        btn = gr.Button("Generar 3D con IA + Esqueleto", elem_id="gen", size="lg")
                        ex = sorted(glob.glob(os.path.join(EXAMPLES_DIR, "*.png")))[:8]
                        if ex:
                            gr.Examples(ex, inputs=[front], label="Ejemplos")
                    with gr.Tab("Mis Modelos"):
                        g_btn = gr.Button("Actualizar", size="sm")
                        gal = gr.Gallery(label="Toca uno para abrirlo en el estudio",
                                         columns=2, height=520, allow_preview=False)
                        h_out = gr.File(file_count="multiple", label="ZIPs guardados")
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
                status = gr.Markdown("Sube una foto y pulsa **Generar**. Veras primero la "
                                     "malla, luego la textura y al final el modelo animado.",
                                     min_height=70)
                with gr.Tabs() as tabs:
                    with gr.Tab("1 · Malla", id="malla"):
                        m_clay = gr.HTML(viewer_html(msg="Aquí aparecerá la malla"))
                    with gr.Tab("2 · Textura", id="textura"):
                        m_tex = gr.HTML(viewer_html(msg="Aquí aparecerá el modelo con textura"))
                    with gr.Tab("3 · Estudio animado", id="estudio"):
                        view = gr.HTML(viewer_html())
                out_files = gr.File(label="Descargas (ZIP con todo + archivos sueltos)",
                                    file_count="multiple")
                with gr.Accordion("Videos (solo si activaste «Generar videos»)", open=False):
                    with gr.Row():
                        v_anim = gr.Video(label="Animación", height=280)
                        v_360 = gr.Video(label="Giro 360", height=280)
                with gr.Accordion("Monitor de GPU / RAM", open=True):
                    mon = gr.HTML(monitor_html(), elem_id="mon")
                    mon_btn = gr.Button("Actualizar monitor", size="sm")
        job = gr.State("")

        def apply_preset(name):
            s, o, f, t = PRESETS[name]
            return s, o, f, str(t)

        preset.change(apply_preset, preset, [steps, octree, faces, tex])
        final_outs = [view, tabs, m_clay, m_tex, v_anim, v_360, out_files, status, mon]
        (btn.click(step_malla,
                   [front, back, left, right, sheet, sheet_order, remove_bg, steps, octree,
                    faces, tex, seed, rand_seed, guidance, rig, height, rotate, video,
                    video_res, samples, turntable, texture, relieve_on, relieve, make_videos,
                    detalle],
                   [job, m_clay, tabs, status, seed], concurrency_id="gen",
                   concurrency_limit=P["workers"], **_spo(status))
            .success(step_textura, job, [m_tex, tabs, status], concurrency_id="gen",
                     **_spo(status))
            .success(step_final, job, final_outs, concurrency_id="gen",
                     **_spo(status)))
        mon_btn.click(monitor_html, None, mon)
        g_btn.click(lambda: (my_models(), history()), None, [gal, h_out])
        gal.select(open_model, None, final_outs)
        b_btn.click(batch, [b_files, b_rig, b_video], [b_out, b_log], concurrency_id="gen")
        r_btn.click(resources, None, r_out)
        demo.load(lambda: (my_models(), history()), None, [gal, h_out])
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
