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
             "piezas.glb", "arcilla.glb", "rig_info.json"]
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
    if "vertices_sin_peso_reparados" in info:
        lines.append(f"Pesos: 100 % de la malla sigue al esqueleto "
                     f"({info['vertices_sin_peso_reparados']} vertices reparados)")
    lines.append("Abre **visor.html** del ZIP para ver el modelo animado en el navegador o en AR.")
    for w in info.get("avisos", []):
        lines.append(f"⚠️ {w}")
    return "\n\n".join(lines)


def generate(front, back, left, right, sheet, sheet_order, remove_bg, steps, octree,
             faces, tex, seed, rand_seed, guidance, rig, height, rotate, video,
             video_res, samples, turntable, texture, progress=gr.Progress()):
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
                      steps, octree, faces, int(tex), seed, guidance, rig, height,
                      rotate, video, video_res, samples, turntable, texture,
                      progress=lambda f, m: progress(f, desc=m))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise gr.Error(f"Fallo: {e}")
    d = res["dir"]
    info = res["info"]
    p = lambda f: (os.path.join(d, f) if os.path.exists(os.path.join(d, f))
                   and os.path.getsize(os.path.join(d, f)) > 2000 else None)
    vid = None
    for f in os.listdir(d):
        if f.startswith("video_") and "giro360" not in f and p(f):
            vid = os.path.join(d, f)
    return (p("modelo_animado.glb") or p("modelo_texturizado.glb"),
            p("modelo_texturizado.glb"), p("arcilla.glb"), p("piezas.glb"),
            vid, p("video_giro360.mp4"), [res["zip"]] + _files(d),
            _summary(info) + (f"\n\n🎬 **[Abrir visor animado (botones por animación, AR)]"
                              f"(/gradio_api/file={os.path.join(d, 'visor.html')})**"
                              if p("visor.html") is not None or os.path.exists(os.path.join(d, "visor.html")) else ""),
            int(seed))


def batch(files, rig, video, progress=gr.Progress()):
    if not files:
        raise gr.Error("Sube varias fotos")
    eng = get_engine()
    zips, log = [], []
    for i, f in enumerate(files):
        progress(i / len(files), desc=f"Foto {i + 1}/{len(files)}")
        path = f if isinstance(f, str) else f.name
        try:
            r = eng.run(path, rig=rig, video=video)
            zips.append(r["zip"])
            log.append(f"✅ {os.path.basename(path)} → {os.path.basename(r['zip'])}")
        except Exception as e:
            log.append(f"❌ {os.path.basename(path)}: {e}")
    return zips, "\n\n".join(log)


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


def build_ui():
    eng = get_engine()
    P = eng.p
    css = """
    .gradio-container {max-width: 1400px !important}
    #gen {background: linear-gradient(90deg,#5b5bf0,#7c4dff); color: white; font-size: 18px}
    """
    with gr.Blocks(title="AP Model 3D Foto", theme=gr.themes.Soft(primary_hue="indigo"),
                   css=css) as demo:
        gr.Markdown(f"# AP Model 3D Foto\nFoto → modelo 3D texturizado, esqueleto "
                    f"compatible con Mixamo, animaciones, piezas y exportacion a "
                    f"Blender / FBX / GLB / OBJ / STL / video.\n\n`{config.describe(P)}`")
        with gr.Tab("Estudio"):
            with gr.Row():
                with gr.Column(scale=4):
                    front = gr.Image(label="Frente (obligatoria)", type="pil",
                                     image_mode="RGBA", height=300)
                    with gr.Accordion("Mas vistas: espalda / perfiles / hoja de vistas "
                                      "(mejor forma y espalda pintada)", open=False):
                        with gr.Row():
                            back = gr.Image(label="Espalda", type="pil", image_mode="RGBA", height=160)
                            left = gr.Image(label="Perfil izq.", type="pil", image_mode="RGBA", height=160)
                            right = gr.Image(label="Perfil der.", type="pil", image_mode="RGBA", height=160)
                        sheet = gr.Image(label="Hoja de vistas (una imagen con todas)",
                                         type="pil", height=160)
                        sheet_order = gr.Dropdown(
                            ["front,left,back,right", "front,right,back,left",
                             "front,back", "front,left,back", "left,front,right,back"],
                            value="front,left,back,right",
                            label="Orden de la hoja (de izquierda a derecha)")
                    ex = sorted(glob.glob(os.path.join(EXAMPLES_DIR, "*.png")))[:12]
                    if ex:
                        gr.Examples(ex, inputs=[front], label="Ejemplos")
                    with gr.Accordion("Calidad", open=False):
                        preset = gr.Radio(list(PRESETS), value="Maxima" if P["vram_gb"] >= 38
                                          else ("Alta" if P["vram_gb"] >= 20 else "Rapido"),
                                          label="Preajuste")
                        with gr.Row():
                            steps = gr.Slider(10, 100, P["steps"], step=1, label="Pasos")
                            octree = gr.Slider(192, 640, P["octree"], step=32,
                                               label="Resolucion de forma (octree)")
                        with gr.Row():
                            faces = gr.Slider(10000, 400000, P["faces"], step=5000,
                                              label="Caras maximas")
                            tex = gr.Dropdown(["1024", "2048", "4096"], value=str(P["tex"]),
                                              label="Textura (px)")
                        with gr.Row():
                            seed = gr.Number(1234, label="Semilla", precision=0)
                            rand_seed = gr.Checkbox(False, label="Semilla aleatoria")
                            guidance = gr.Slider(1, 15, 5.0, step=0.5, label="Fidelidad a la foto")
                        with gr.Row():
                            remove_bg = gr.Checkbox(True, label="Quitar fondo")
                            texture = gr.Checkbox(True, label="Textura con IA")
                    with gr.Accordion("Esqueleto, animacion y video", open=False):
                        rig = gr.Radio(["humanoide", "cuadrupedo", "ninguno"],
                                       value="humanoide", label="Esqueleto")
                        with gr.Row():
                            height = gr.Slider(0.2, 5, 1.8, step=0.05, label="Altura real (m)")
                            rotate = gr.Slider(-180, 180, 0, step=90,
                                               label="Girar si mira hacia atras (grados)")
                        with gr.Row():
                            video = gr.Dropdown(ANIMS, value="Caminar", label="Animacion del video")
                            video_res = gr.Dropdown([480, 720, 1080, 1440], value=P["video_res"],
                                                    label="Resolucion del video")
                            samples = gr.Slider(4, 256, P["samples"], step=4, label="Calidad de render")
                        turntable = gr.Checkbox(True, label="Video giro 360")
                    btn = gr.Button("Generar 3D con IA + Esqueleto", elem_id="gen", size="lg")
                with gr.Column(scale=6):
                    status = gr.Markdown("Sube una foto y pulsa **Generar**.")
                    with gr.Tabs():
                        with gr.Tab("Animado"):
                            m_anim = gr.Model3D(label="Esqueleto + animaciones", height=520,
                                                clear_color=(0.07, 0.08, 0.1, 1))
                        with gr.Tab("Textura"):
                            m_tex = gr.Model3D(label="Texturizado", height=520,
                                               clear_color=(0.07, 0.08, 0.1, 1))
                        with gr.Tab("Arcilla"):
                            m_clay = gr.Model3D(label="Solo forma", height=520,
                                                clear_color=(0.07, 0.08, 0.1, 1))
                        with gr.Tab("Piezas"):
                            m_parts = gr.Model3D(label="Una pieza por hueso", height=520,
                                                 clear_color=(0.07, 0.08, 0.1, 1))
                    with gr.Row():
                        v_anim = gr.Video(label="Animacion", height=300)
                        v_360 = gr.Video(label="Giro 360", height=300)
                    out_files = gr.File(label="Descargas (ZIP con todo + archivos sueltos)",
                                        file_count="multiple")

            def apply_preset(name):
                s, o, f, t = PRESETS[name]
                return s, o, f, str(t)

            preset.change(apply_preset, preset, [steps, octree, faces, tex])
            btn.click(generate,
                      [front, back, left, right, sheet, sheet_order, remove_bg, steps, octree,
                       faces, tex, seed, rand_seed, guidance, rig, height, rotate, video,
                       video_res, samples, turntable, texture],
                      [m_anim, m_tex, m_clay, m_parts, v_anim, v_360, out_files, status, seed],
                      concurrency_limit=P["workers"], concurrency_id="gen")

        with gr.Tab("Lote (varias fotos)"):
            gr.Markdown("Procesa muchas fotos seguidas. Mientras Blender anima una, "
                        "la GPU ya genera la siguiente.")
            b_files = gr.File(file_count="multiple", file_types=["image"], label="Fotos")
            with gr.Row():
                b_rig = gr.Radio(["humanoide", "cuadrupedo", "ninguno"], value="humanoide",
                                 label="Esqueleto")
                b_video = gr.Dropdown(ANIMS, value="Caminar", label="Animacion")
            b_btn = gr.Button("Procesar lote", variant="primary")
            b_log = gr.Markdown()
            b_out = gr.File(file_count="multiple", label="ZIPs")
            b_btn.click(batch, [b_files, b_rig, b_video], [b_out, b_log],
                        concurrency_id="gen")

        with gr.Tab("Historial"):
            h_btn = gr.Button("Actualizar")
            h_out = gr.File(file_count="multiple", label="Resultados anteriores (esta sesion)")
            h_btn.click(history, None, h_out)

        with gr.Tab("Recursos"):
            r_btn = gr.Button("Ver uso de RAM / GPU")
            r_out = gr.Markdown()
            r_btn.click(resources, None, r_out)
            gr.Markdown(
                "**Consejos**\n\n"
                "- Personas: pose en T o A, cuerpo completo, fondo liso, buena luz.\n"
                "- Sube espalda y perfiles para que la forma y la espalda salgan bien.\n"
                "- `modelo_estatico.obj` sirve para subirlo a mixamo.com si quieres "
                "sus animaciones; `modelo_rig.fbx` ya trae huesos con nombres de Mixamo.\n"
                "- El STL esta en milimetros para impresion 3D.")
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
