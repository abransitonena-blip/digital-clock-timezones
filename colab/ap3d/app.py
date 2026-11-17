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

ANIMS = ["Caminar", "Correr", "Saludar", "Saltar", "Bailar", "Reposo"]
PRESETS = {
    # nombre: (pasos, octree, caras, textura)
    "Rapido": (25, 256, 40000, 2048),
    "Alta": (40, 384, 80000, 2048),
    "Maxima": (50, 512, 150000, 4096),
}
EXAMPLES_DIR = "/content/Hunyuan3D-2/assets/example_images"


def _files(d):
    order = ["modelo_animado.glb", "modelo_rig.fbx", "modelo.blend", "modelo_texturizado.glb",
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


def viewer_html(d=None, height=640):
    """Estudio 3D (three.js) en un iframe servido desde la carpeta del resultado."""
    if not d or not os.path.exists(os.path.join(d, "estudio.html")):
        return (f"<div style='height:{height}px;display:flex;align-items:center;"
                "justify-content:center;flex-direction:column;gap:10px;background:#121318;"
                "border-radius:14px;color:#9a9daa;font-family:system-ui'>"
                "<div style='font-size:46px'>🧍</div><div>Sube una foto y pulsa "
                "<b style='color:#e8e9ee'>Generar 3D con IA + Esqueleto</b></div></div>")
    src = f"/gradio_api/file={os.path.join(d, 'estudio.html')}?t={int(time.time())}"
    return (f"<iframe src='{src}' style='width:100%;height:{height}px;border:0;"
            "border-radius:14px;background:#121318' allow='fullscreen; xr-spatial-tracking'"
            " allowfullscreen></iframe>"
            f"<div style='text-align:right;margin-top:4px'><a href='{src}' target='_blank' "
            "style='color:#8b8bff;font-size:13px'>Abrir en pantalla completa ↗</a></div>")


def _outputs(d, info, seed):
    p = lambda f: (os.path.join(d, f) if os.path.exists(os.path.join(d, f))
                   and os.path.getsize(os.path.join(d, f)) > 2000 else None)
    vid = None
    for f in sorted(os.listdir(d)):
        if f.startswith("video_") and "giro360" not in f and p(f):
            vid = os.path.join(d, f)
    zp = d + ".zip"
    files = ([zp] if os.path.exists(zp) else []) + _files(d)
    return (viewer_html(d), vid, p("video_giro360.mp4"), files, _summary(info), seed)


def generate(front, back, left, right, sheet, sheet_order, remove_bg, steps, octree,
             faces, tex, seed, rand_seed, guidance, rig, height, rotate, video,
             video_res, samples, turntable, texture, relieve_on, relieve,
             progress=gr.Progress()):
    if front is None and sheet is None:
        raise gr.Error("Sube al menos la foto de frente (o una hoja de vistas).")
    if rand_seed:
        seed = random.randint(0, 2**31 - 1)
    eng = get_engine()
    if front is None:          # solo hoja de vistas
        parts = eng.split_sheet(sheet, sheet_order)
        front = parts.get("front")
    try:
        res = eng.run(front, back, left, right, sheet, sheet_order, remove_bg,
                      steps, octree, faces, int(tex), seed, guidance, RIGS.get(rig, rig),
                      height, rotate, video, video_res, samples, turntable, texture,
                      relieve=float(relieve) if relieve_on else 0.0,
                      progress=lambda f, m: progress(f, desc=m))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise gr.Error(f"Fallo: {e}")
    return _outputs(res["dir"], res["info"], int(seed))


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
    return _outputs(d, info, info.get("ajustes", {}).get("seed", 1234))


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
    best = "Maxima" if P["vram_gb"] >= 38 else ("Alta" if P["vram_gb"] >= 20 else "Rapido")
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
                        with gr.Accordion("Altura real", open=True):
                            height = gr.Slider(0.2, 5, 1.7, step=0.01, label="metros")
                        with gr.Accordion("Mapas de relieve", open=False):
                            relieve_on = gr.Checkbox(True, label="Relieve realista desde la textura")
                            relieve = gr.Slider(0.1, 2.0, 0.6, step=0.1, label="Intensidad")
                        with gr.Accordion("Calidad", open=False):
                            preset = gr.Radio(list(PRESETS), value=best, label="Preajuste")
                            tex = gr.Dropdown(["1024", "2048", "4096"], value=str(P["tex"]),
                                              label="Textura (px)")
                            with gr.Row():
                                remove_bg = gr.Checkbox(True, label="Quitar fondo")
                                texture = gr.Checkbox(True, label="Textura con IA")
                        with gr.Accordion("Animación y video", open=False):
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
                            steps = gr.Slider(10, 100, P["steps"], step=1, label="Pasos")
                            octree = gr.Slider(192, 640, P["octree"], step=32, label="Octree")
                        faces = gr.Slider(10000, 400000, P["faces"], step=5000, label="Caras máximas")
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
                view = gr.HTML(viewer_html())
                status = gr.Markdown("")
                with gr.Accordion("Videos", open=False):
                    with gr.Row():
                        v_anim = gr.Video(label="Animación", height=280)
                        v_360 = gr.Video(label="Giro 360", height=280)
                out_files = gr.File(label="Descargas (ZIP con todo + archivos sueltos)",
                                    file_count="multiple")

        def apply_preset(name):
            s, o, f, t = PRESETS[name]
            return s, o, f, str(t)

        outs = [view, v_anim, v_360, out_files, status, seed]
        preset.change(apply_preset, preset, [steps, octree, faces, tex])
        btn.click(generate,
                  [front, back, left, right, sheet, sheet_order, remove_bg, steps, octree,
                   faces, tex, seed, rand_seed, guidance, rig, height, rotate, video,
                   video_res, samples, turntable, texture, relieve_on, relieve],
                  outs, concurrency_limit=P["workers"], concurrency_id="gen")
        g_btn.click(lambda: (my_models(), history()), None, [gal, h_out])
        gal.select(open_model, None, outs)
        b_btn.click(batch, [b_files, b_rig, b_video], [b_out, b_log], concurrency_id="gen")
        r_btn.click(resources, None, r_out)
        demo.load(lambda: (my_models(), history()), None, [gal, h_out])
    demo.queue(default_concurrency_limit=P["workers"], max_size=64)
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
                allowed_paths=[config.OUT_DIR, EXAMPLES_DIR], max_file_size="200mb")
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
