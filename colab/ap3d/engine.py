"""Motor: foto(s) -> malla 3D (Hunyuan3D-2 / 2mv) -> textura -> Blender.

Uso de recursos:
  * Todos los modelos quedan cargados en la GPU a la vez (perfil MAXIMO /
    ALTO), asi no hay esperas entre una foto y la siguiente.
  * Los pesos se precargan en la RAM (cache de paginas de Linux) leyendo
    los archivos en paralelo: recargar un modelo tarda segundos.
  * El trabajo temporal va en /dev/shm (disco en RAM).
  * La GPU se protege con un candado; Blender (CPU + RAM) corre en
    paralelo con la siguiente generacion en la GPU.
  * Los resultados se guardan en una cache en RAM por hash de la foto y
    los ajustes: repetir la misma foto es instantaneo.
"""
import concurrent.futures as cf
import gc
import glob
import hashlib
import io
import json
import os
import re
import shutil
import sys
import subprocess
import threading
import time
import zipfile

import numpy as np
from PIL import Image, ImageOps

from . import config

HERE = os.path.dirname(os.path.abspath(__file__))
GPU_LOCK = threading.Lock()
VIEWS = ("front", "back", "left", "right")


# Seguridad: imagenes gigantes o falsas no pueden tumbar el servidor
Image.MAX_IMAGE_PIXELS = 64_000_000
MAX_SIDE = 2048


def safe_image(img):
    """Valida y normaliza una imagen subida (tamano, modo, formato)."""
    if not isinstance(img, Image.Image):
        raise ValueError("El archivo no es una imagen valida")
    w, h = img.size
    if w < 32 or h < 32:
        raise ValueError("La imagen es demasiado pequena (minimo 32 px)")
    if w * h > Image.MAX_IMAGE_PIXELS:
        raise ValueError("La imagen es demasiado grande")
    if max(w, h) > MAX_SIDE:
        img = img.copy()
        img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    return img


def cleanup_outputs(keep=80, min_free_gb=10):
    """Borra los resultados mas viejos si hay demasiados o falta disco."""
    try:
        ds = sorted(d for d in glob.glob(os.path.join(config.OUT_DIR, "*")) if os.path.isdir(d))
        free = shutil.disk_usage(config.OUT_DIR).free / 2**30
        while ds and (len(ds) > keep or free < min_free_gb):
            d = ds.pop(0)
            shutil.rmtree(d, ignore_errors=True)
            if os.path.exists(d + ".zip"):
                os.remove(d + ".zip")
            free = shutil.disk_usage(config.OUT_DIR).free / 2**30
    except Exception:
        pass


def quiet_logs():
    """Oculta avisos que no afectan al resultado (torch.range, pasos de
    difusion, INFO de hy3dgen) para que el registro muestre solo el avance."""
    import logging
    import warnings
    warnings.filterwarnings("ignore", message=".*torch.range.*")
    warnings.filterwarnings("ignore", category=FutureWarning)
    for name in ("hy3dgen", "hy3dgen.shapgen", "hy3dgen.shapegen", "hy3dgen.texgen"):
        logging.getLogger(name).setLevel(logging.WARNING)
    try:
        from diffusers.utils import logging as dlog
        dlog.set_verbosity_error()
    except Exception:
        pass
    try:
        from transformers.utils import logging as tlog
        tlog.set_verbosity_error()
    except Exception:
        pass


def _memoria_path():
    try:
        from .memoria import path
        return path()
    except Exception:
        return ""


DENSIDADES = {"humanoide": 985.0, "cuadrupedo": 1000.0, "cabeza": 1100.0, "objeto": 600.0}


def physics_data(mesh, height_m, tipo="humanoide"):
    """Datos fisicos del modelo a su tamano real (Y arriba):
    volumen, masa aproximada, centro de masa, base de apoyo, estabilidad
    (si se sostiene solo) y estimacion de impresion 3D a 15 cm en PLA."""
    import trimesh
    v = np.asarray(mesh.vertices, dtype=np.float64)
    ext = v.max(0) - v.min(0)
    k = float(height_m) / max(ext[1], 1e-9)          # escala a metros reales
    m = mesh.copy()
    m.apply_translation(-v.min(0))
    m.apply_scale(k)
    vv = np.asarray(m.vertices)
    dims = vv.max(0) - vv.min(0)
    if m.is_watertight:
        vol = float(abs(m.volume))
        com = np.asarray(m.center_mass, dtype=float)
    else:
        pitch = float(dims.max() / 96.0)
        vox = m.voxelized(pitch).fill()
        pts = vox.points
        vol = float(len(pts) * pitch ** 3)
        com = pts.mean(0) if len(pts) else vv.mean(0)
    area = float(m.area)
    dens = DENSIDADES.get(tipo, 800.0)
    masa = vol * dens
    # base de apoyo: puntos a menos de 1.5 % de la altura del suelo
    piso = vv[vv[:, 1] < 0.015 * dims[1]][:, [0, 2]]
    estable, margen, base_cm2 = None, None, 0.0
    try:
        from scipy.spatial import ConvexHull, Delaunay
        if len(piso) >= 4:
            hull = ConvexHull(piso)
            base_cm2 = float(hull.volume) * 1e4
            dl = Delaunay(piso[hull.vertices])
            c2 = com[[0, 2]]
            estable = bool(dl.find_simplex(c2) >= 0)
            hp = piso[hull.vertices]
            seg = np.roll(hp, -1, 0) - hp
            t = np.clip(((c2 - hp) * seg).sum(1) / np.maximum((seg ** 2).sum(1), 1e-12), 0, 1)
            dmin = float(np.min(np.linalg.norm(hp + seg * t[:, None] - c2, axis=1)))
            margen = round(dmin * 100 * (1 if estable else -1), 2)
    except Exception:
        pass
    # impresion: escalar a 15 cm de alto, PLA 1.24 g/cm3, ~20 % relleno
    s15 = 0.15 / max(dims[1], 1e-9)
    vol15_cm3 = vol * s15 ** 3 * 1e6
    area15_cm2 = area * s15 ** 2 * 1e4
    gramos = (area15_cm2 * 0.12 + max(vol15_cm3 - area15_cm2 * 0.12, 0) * 0.2) * 1.24
    horas = gramos / 11.0          # ~11 g/h en una impresora FDM comun
    # tensor de inercia aproximado (caja equivalente) para motores
    a_, b_, c_ = dims
    inercia = [masa / 12 * (b_ ** 2 + c_ ** 2), masa / 12 * (a_ ** 2 + c_ ** 2),
               masa / 12 * (a_ ** 2 + b_ ** 2)]
    return {
        "alto_m": round(float(dims[1]), 3), "ancho_m": round(float(dims[0]), 3),
        "fondo_m": round(float(dims[2]), 3), "volumen_l": round(vol * 1000, 2),
        "superficie_m2": round(area, 3), "densidad_kg_m3": dens, "masa_kg": round(masa, 2),
        "centro_masa_m": [round(float(x), 3) for x in com],
        "centro_masa_altura_pct": round(float(com[1] / max(dims[1], 1e-9)) * 100, 1),
        "base_apoyo_cm2": round(base_cm2, 1), "se_sostiene_solo": estable,
        "margen_estabilidad_cm": margen,
        "impresion_15cm": {"gramos_pla": round(gramos, 1), "horas": round(horas, 1),
                           "volumen_cm3": round(vol15_cm3, 1)},
        "inercia_kg_m2": [round(float(x), 4) for x in inercia],
    }


def render_preview(mesh, size=384, az=30.0):
    """Imagen de una malla sin GPU grafica: proyeccion ortografica con
    z-buffer de caras y luz por normales (para elegir variantes)."""
    v = np.asarray(mesh.vertices, dtype=np.float64)
    f = np.asarray(mesh.faces)
    a = np.radians(az)
    R = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    v = v @ R.T
    v -= v.mean(0)
    s = 0.9 * size / max(np.ptp(v[:, 0]), np.ptp(v[:, 1]), 1e-6)
    tri = v[f]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    luz = np.clip(n @ np.array([0.35, 0.5, 0.8]) / 1.0, 0, 1) * 0.75 + 0.2
    c = tri.mean(1)
    px = (c[:, 0] * s + size / 2).astype(int)
    py = (size / 2 - c[:, 1] * s).astype(int)
    ok = (px >= 0) & (px < size) & (py >= 0) & (py < size)
    order = np.argsort(c[:, 2])          # de atras hacia adelante
    img = np.full((size, size), 0.09)
    zb = np.full((size, size), -1e9)
    r = max(1, int(size / 220))
    for i in order[ok[order]]:
        x0, y0 = px[i], py[i]
        img[max(0, y0 - r):y0 + r + 1, max(0, x0 - r):x0 + r + 1] = luz[i]
    rgb = np.stack([img * 0.85, img * 0.88, img], -1)
    return Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))


class Engine:
    def __init__(self, prof=None, log=print):
        self.p = prof or config.detect()
        self.log = log
        self.rembg = None
        self.shape = None
        self.shape_mv = None
        self.shape_t = None
        self.shape_mv_t = None
        self.paint = None
        self.paint_kind = ""
        self.jobs = {"activos": 0, "en_cola": 0}
        self._preview = False
        # tiempos medidos (media movil) para estimar cuanto falta
        self.eta = {"forma": 8.0, "textura": 35.0, "blender": 60.0}
        self._eta_path = os.path.join(config.OUT_DIR, "tiempos.json")
        try:
            self.eta.update(json.load(open(self._eta_path)))
        except Exception:
            pass
        self.cache = {}
        self.ready = False
        self.blender_pool = cf.ThreadPoolExecutor(max_workers=3 * self.p["workers"])
        os.makedirs(config.OUT_DIR, exist_ok=True)

    def _ensure(self):
        """Si el codigo se actualizo con los modelos ya cargados, completa los
        atributos nuevos para no tener que reiniciar la sesion."""
        d = self.__dict__
        d.setdefault("shape_t", None)
        d.setdefault("shape_mv_t", None)
        d.setdefault("paint_kind", "")
        d.setdefault("jobs", {"activos": 0, "en_cola": 0})
        d.setdefault("_preview", False)
        d.setdefault("eta", {"forma": 8.0, "textura": 35.0, "blender": 60.0})
        d.setdefault("_eta_path", os.path.join(config.OUT_DIR, "tiempos.json"))
        d.setdefault("cache", {})
        d.setdefault("tripo", None)
        d.setdefault("t2i", None)
        if d.get("blender_pool") is None:
            d["blender_pool"] = cf.ThreadPoolExecutor(max_workers=3 * self.p["workers"])

    # ------------------------------------------------------------ carga
    def preload_weights(self, repos=("tencent/Hunyuan3D-2", "tencent/Hunyuan3D-2mv")):
        """Lee todos los archivos de pesos para dejarlos en la RAM."""
        from huggingface_hub import scan_cache_dir
        files = []
        try:
            for r in scan_cache_dir().repos:
                if r.repo_id in repos:
                    for rev in r.revisions:
                        files += [str(f.file_path) for f in rev.files]
        except Exception as e:
            self.log("No se pudo leer la cache de HF:", e)
            return 0

        def rd(path):
            n = 0
            with open(path, "rb", buffering=0) as f:
                while True:
                    b = f.read(64 << 20)
                    if not b:
                        return n
                    n += len(b)

        t = time.time()
        with cf.ThreadPoolExecutor(16) as ex:
            total = sum(ex.map(rd, files))
        self.log(f"Pesos precargados en RAM: {total / 2**30:.1f} GB en "
                 f"{time.time() - t:.0f}s")
        return total

    def _shape_pipe(self, repo, sub, turbo):
        from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
        pipe = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            repo, subfolder=sub, use_safetensors=True)
        if turbo:
            # FlashVDM: decodifica la malla ~10x mas rapido
            try:
                pipe.enable_flashvdm(mc_algo="mc")
            except TypeError:
                try:
                    pipe.enable_flashvdm()
                except Exception as e:
                    self.log("  FlashVDM no disponible:", e)
            except Exception as e:
                self.log("  FlashVDM no disponible:", e)
        return pipe

    def load(self, want_mv=True, want_paint=True, want_turbo=True, want_quality=None):
        quiet_logs()
        """Carga los modelos. Turbo (5 pasos + FlashVDM) es el modo por defecto:
        la forma sale en segundos. Con GPU grande tambien queda cargado el
        modelo normal (50 pasos) para el modo Calidad."""
        import torch
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        torch.backends.cudnn.benchmark = True
        from hy3dgen.rembg import BackgroundRemover
        if want_quality is None:
            want_quality = self.p["all_on_gpu"] or not want_turbo

        t = time.time()
        if self.rembg is None:
            self.rembg = BackgroundRemover()
        if want_turbo and self.shape_t is None:
            self.log("Cargando Hunyuan3D-2 Turbo (forma rapida)...")
            try:
                self.shape_t = self._shape_pipe("tencent/Hunyuan3D-2",
                                                "hunyuan3d-dit-v2-0-turbo", True)
            except Exception as e:
                self.log("  Turbo no disponible:", e)
                want_quality = True
        diferidos = []
        if want_quality and self.shape is None:
            if self.shape_t is not None:
                diferidos.append("forma")      # Turbo ya sirve: calidad en 2o plano
            else:
                self.log("Cargando Hunyuan3D-2 (forma, calidad)...")
                self.shape = self._shape_pipe("tencent/Hunyuan3D-2", "hunyuan3d-dit-v2-0", False)
        if want_mv and want_turbo and self.shape_mv_t is None:
            self.log("Cargando Hunyuan3D-2mv Turbo (varias vistas)...")
            try:
                self.shape_mv_t = self._shape_pipe("tencent/Hunyuan3D-2mv",
                                                   "hunyuan3d-dit-v2-mv-turbo", True)
            except Exception as e:
                self.log("  2mv Turbo no disponible:", e)
        if want_mv and (want_quality or self.shape_mv_t is None) and self.shape_mv is None:
            if self.shape_mv_t is not None:
                diferidos.append("mv")
            else:
                self.log("Cargando Hunyuan3D-2mv (varias vistas, calidad)...")
                try:
                    self.shape_mv = self._shape_pipe("tencent/Hunyuan3D-2mv",
                                                     "hunyuan3d-dit-v2-mv", False)
                except Exception as e:
                    self.log("  2mv no disponible, se usara solo 1 foto:", e)
        if want_paint and self.paint is None:
            from hy3dgen.texgen import Hunyuan3DPaintPipeline
            subs = (["hunyuan3d-paint-v2-0-turbo"] if want_turbo else []) + ["hunyuan3d-paint-v2-0"]
            for sub in subs:
                self.log(f"Cargando Hunyuan3D-Paint ({'turbo' if 'turbo' in sub else 'normal'})...")
                try:
                    try:
                        self.paint = Hunyuan3DPaintPipeline.from_pretrained(
                            "tencent/Hunyuan3D-2", subfolder=sub)
                    except TypeError:
                        if "turbo" in sub:
                            raise
                        self.paint = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2")
                    self.paint_kind = sub
                    break
                except Exception as e:
                    self.log("  no disponible:", e)
                    self.paint = None
            if self.paint is not None:
                self._set_texture_size(self.p["tex"])
                if self.p["offload"]:
                    self.paint.enable_model_cpu_offload()
            else:
                self.log("  Textura IA no disponible (color proyectado de la foto)")
        if not self.p["all_on_gpu"]:
            for p in (self.shape_mv, self.shape_mv_t, self.shape):
                if p is not None and p is not self.shape_t:
                    p.to("cpu")
        self.ready = True
        self.warmup()
        if diferidos:
            def _late():
                try:
                    if "forma" in diferidos:
                        self.shape = self._shape_pipe("tencent/Hunyuan3D-2", "hunyuan3d-dit-v2-0", False)
                    if "mv" in diferidos:
                        self.shape_mv = self._shape_pipe("tencent/Hunyuan3D-2mv",
                                                         "hunyuan3d-dit-v2-mv", False)
                    self.log("Modelos de calidad (50 pasos) listos en segundo plano")
                except Exception as e:
                    self.log("  modelos de calidad no cargados:", e)
            threading.Thread(target=_late, daemon=True).start()
            self.log("Turbo listo. Los modelos de 50 pasos se cargan en segundo plano.")
        self.log(f"Modelos listos en {time.time() - t:.0f}s")
        self.log_mem()

    def warmup(self):
        """Una pasada minima al cargar: compila los kernels de CUDA y elige
        los algoritmos de cuDNN, asi la primera foto ya va a toda velocidad."""
        import torch
        pipe = self.shape_t or self.shape
        if pipe is None or not torch.cuda.is_available():
            return
        t = time.time()
        try:
            from PIL import ImageDraw
            im = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            d.ellipse((176, 40, 336, 200), fill=(200, 170, 150, 255))
            d.rectangle((196, 190, 316, 470), fill=(60, 80, 160, 255))
            g = torch.Generator(device="cuda").manual_seed(0)
            with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16):
                pipe(image=im, num_inference_steps=2, octree_resolution=128,
                     num_chunks=self.p["chunks"], generator=g, output_type="trimesh")
            torch.cuda.synchronize()
            self.log(f"GPU calentada en {time.time() - t:.0f}s")
        except Exception as e:
            self.log("  calentamiento omitido:", e)

    def shape_variants(self, front, n=4, seed0=None, remove_bg=True, motor="hunyuan"):
        """Varias formas rapidas (Turbo, octree 256) con semillas distintas para
        elegir la buena antes de texturizar. Responde a la critica de que la IA
        da resultados distintos en cada intento: aqui los ves todos y eliges."""
        import random as _r
        self._ensure()
        if not self.ready:
            self.load()
        views = {"front": self.prep(front, remove_bg), "back": None, "left": None, "right": None}
        seeds = [int(seed0) + i * 7919 if seed0 is not None else _r.randint(0, 2**31 - 1)
                 for i in range(n)]
        out = []
        with GPU_LOCK:
            for sd in seeds:
                mesh, _ = self._shape(views, 5, 256, sd, 5.0, True, motor)
                try:
                    from hy3dgen.shapegen import FaceReducer, FloaterRemover
                    mesh = FloaterRemover()(mesh)
                    if len(mesh.faces) > 40000:
                        mesh = FaceReducer()(mesh, max_facenum=40000)
                except Exception:
                    pass
                out.append((sd, render_preview(mesh)))
        return out

    def text_to_image(self, prompt, seed=0):
        """Texto -> imagen de referencia. FLUX.1-schnell (2024, 4 pasos, licencia
        Apache 2.0, gran calidad); si no esta, HunyuanDiT. Se carga al usarlo."""
        import torch
        prompt = str(prompt).strip()[:400]
        full = (prompt + ", single character or object, full body, centered, front view, "
                "plain white background, soft studio light, 3D render style, high detail")
        if getattr(self, "t2i", None) is None:
            try:
                if os.environ.get("AP3D_T2I") == "hunyuan":
                    raise RuntimeError("FLUX sin acceso (falta token de Hugging Face)")
                from diffusers import FluxPipeline
                self.log("Cargando FLUX.1-schnell (texto a imagen)...")
                pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-schnell",
                                                    torch_dtype=torch.bfloat16)
                if self.p["vram_gb"] >= 60:
                    pipe.to("cuda")
                else:
                    pipe.enable_model_cpu_offload()
                self.t2i = ("flux", pipe)
            except Exception as e:
                self.log("  FLUX no disponible, se usa HunyuanDiT:", e)
                from hy3dgen.text2image import HunyuanDiTPipeline
                self.t2i = ("hunyuan", HunyuanDiTPipeline(
                    "Tencent-Hunyuan/HunyuanDiT-v1.1-Diffusers-Distilled"))
        kind, pipe = self.t2i
        if kind == "flux":
            g = torch.Generator("cpu").manual_seed(int(seed))
            with torch.inference_mode():
                return pipe(full, guidance_scale=0.0, num_inference_steps=4, height=1024,
                            width=1024, max_sequence_length=256, generator=g).images[0]
        return pipe(prompt + ", full body, centered, plain background", seed=int(seed))

    def load_triposg(self, root="/content/TripoSG"):
        """TripoSG (VAST / Tripo AI): forma de alta fidelidad desde 1 foto."""
        import torch
        if getattr(self, "tripo", None) is not None:
            return True
        try:
            if root not in sys.path:
                sys.path.insert(0, root)
                sys.path.insert(0, os.path.join(root, "scripts"))
            from triposg.pipelines.pipeline_triposg import TripoSGPipeline
            from briarmbg import BriaRMBG
            w = os.path.join(root, "pretrained_weights")
            self.tripo_rmbg = BriaRMBG.from_pretrained(os.path.join(w, "RMBG-1.4")).to("cuda").eval()
            self.tripo = TripoSGPipeline.from_pretrained(os.path.join(w, "TripoSG")).to(
                "cuda", torch.float16)
            self.log("TripoSG listo (motor de forma de Tripo AI)")
            return True
        except Exception as e:
            self.tripo = None
            self.log("TripoSG no disponible, se usa Hunyuan3D:", e)
            return False

    def shape_triposg(self, img, steps, seed, guidance):
        import tempfile
        import torch
        import trimesh
        from image_process import prepare_image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as fh:
            img.save(fh.name)
            path = fh.name
        try:
            pil = prepare_image(path, bg_color=np.array([1.0, 1.0, 1.0]), rmbg_net=self.tripo_rmbg)
        finally:
            os.remove(path)
        g = torch.Generator(device="cuda").manual_seed(int(seed))
        with torch.inference_mode():
            o = self.tripo(image=pil, generator=g, num_inference_steps=int(max(steps, 25)),
                           guidance_scale=float(guidance if guidance > 5 else 7.0)).samples[0]
        return trimesh.Trimesh(o[0].astype(np.float32), np.ascontiguousarray(o[1]))

    def _set_texture_size(self, size, render=None):
        if self.paint is None:
            return
        render = int(render or self.p["render"])
        try:
            from hy3dgen.texgen.differentiable_renderer.mesh_render import MeshRender
            self.paint.config.texture_size = size
            self.paint.config.render_size = render
            self.paint.render = MeshRender(default_resolution=render, texture_size=size)
            self._tex = (size, render)
        except Exception as e:
            self.log("No se pudo cambiar el tamano de textura:", e)

    def log_mem(self):
        try:
            import psutil
            import torch
            vm = psutil.virtual_memory()
            g = torch.cuda.memory_allocated() / 2**30 if torch.cuda.is_available() else 0
            self.log(f"RAM usada {vm.used / 2**30:.1f}/{vm.total / 2**30:.0f} GB · "
                     f"GPU {g:.1f}/{self.p['vram_gb']} GB")
        except Exception:
            pass

    # ------------------------------------------------------------ imagenes
    def prep(self, img, remove_bg=True):
        if img is None:
            return None
        if isinstance(img, str):
            img = Image.open(img)
        img = safe_image(img)
        img = ImageOps.exif_transpose(img)
        has_alpha = img.mode == "RGBA" and np.array(img)[..., 3].min() < 250
        if remove_bg and not has_alpha:
            img = self.rembg(img.convert("RGB"))
        img = img.convert("RGBA")
        # recortar al objeto y centrar en un cuadrado con margen
        a = np.array(img)[..., 3]
        ys, xs = np.nonzero(a > 10)
        if len(xs):
            x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
            img = img.crop((x0, y0, x1 + 1, y1 + 1))
        w, h = img.size
        s = int(max(w, h) * 1.18)
        sq = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        sq.paste(img, ((s - w) // 2, (s - h) // 2))
        return sq.resize((1024, 1024), Image.LANCZOS) if s > 1024 else sq

    def split_sheet(self, sheet, order="front,left,back,right"):
        """Divide una hoja de vistas en paneles separados por fondo."""
        if sheet is None:
            return {}
        rgba = self.rembg(ImageOps.exif_transpose(
            sheet if not isinstance(sheet, str) else Image.open(sheet)).convert("RGB"))
        a = np.array(rgba)[..., 3] > 10
        col = a.any(0)
        segs, inside, start = [], False, 0
        for i, v in enumerate(col):
            if v and not inside:
                inside, start = True, i
            elif not v and inside:
                inside = False
                segs.append((start, i))
        if inside:
            segs.append((start, len(col)))
        W = a.shape[1]
        segs = [s for s in segs if s[1] - s[0] > W * 0.04]
        if len(segs) < 2:   # sin huecos: partes iguales
            n = len(order.split(","))
            segs = [(int(i * W / n), int((i + 1) * W / n)) for i in range(n)]
        names = [o.strip() for o in order.split(",")]
        out = {}
        for name, (x0, x1) in zip(names, segs):
            out[name] = self.prep(rgba.crop((x0, 0, x1, rgba.size[1])), False)
        return out

    # ------------------------------------------------------------ forma
    def _repair(self, mesh, max_faces):
        from hy3dgen.shapegen import (DegenerateFaceRemover, FaceReducer,
                                      FloaterRemover)
        mesh = FloaterRemover()(mesh)
        mesh = DegenerateFaceRemover()(mesh)
        try:
            import pymeshlab
            ms = pymeshlab.MeshSet()
            ms.add_mesh(pymeshlab.Mesh(mesh.vertices, mesh.faces))
            ms.meshing_remove_duplicate_vertices()
            ms.meshing_repair_non_manifold_edges()
            ms.meshing_close_holes(maxholesize=2000)
            ms.meshing_re_orient_faces_coherently()
            m = ms.current_mesh()
            import trimesh
            mesh = trimesh.Trimesh(m.vertex_matrix(), m.face_matrix(), process=False)
        except Exception as e:
            self.log("  pymeshlab no disponible, se usa trimesh:", e)
            try:
                import trimesh
                mesh.merge_vertices()
                trimesh.repair.fix_normals(mesh)
                trimesh.repair.fill_holes(mesh)
            except Exception as e2:
                self.log("  reparacion omitida:", e2)
        if max_faces and len(mesh.faces) > max_faces:
            mesh = FaceReducer()(mesh, max_facenum=max_faces)
        return mesh

    def _shape(self, views, steps, octree, seed, guidance, turbo, motor):
        if motor == "triposg" and getattr(self, "tripo", None) is not None:
            try:
                mesh = self.shape_triposg(views["front"], steps, seed, guidance)
                # TripoSG sale en otra orientacion/escala: se alinea como Hunyuan
                return mesh, False
            except Exception as e:
                self.log("TripoSG fallo, se usa Hunyuan3D:", e)
        return self.shape_from(views, steps, octree, seed, guidance, turbo)

    def shape_from(self, views, steps, octree, seed, guidance, turbo=True):
        import torch
        multi = {k: v for k, v in views.items() if v is not None}
        want_mv = len(multi) > 1
        cands = ([self.shape_mv_t, self.shape_mv] if turbo else [self.shape_mv, self.shape_mv_t]) \
            if want_mv else []
        cands += [self.shape_t, self.shape] if turbo else [self.shape, self.shape_t]
        pipe = next(p for p in cands if p is not None)
        use_mv = pipe in (self.shape_mv, self.shape_mv_t)
        is_t = pipe in (self.shape_t, self.shape_mv_t)
        if is_t:
            steps = min(int(steps), 8) if int(steps) <= 10 else 5
        if not self.p["all_on_gpu"]:
            for other in (self.shape, self.shape_t, self.shape_mv, self.shape_mv_t):
                if other is not None and other is not pipe:
                    other.to("cpu")
            pipe.to("cuda")
            torch.cuda.empty_cache()
        img = multi if use_mv else views["front"]
        g = torch.Generator(device="cuda").manual_seed(int(seed))
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.float16):
            mesh = pipe(image=img, num_inference_steps=int(steps),
                        octree_resolution=int(octree), num_chunks=self.p["chunks"],
                        guidance_scale=float(guidance), generator=g,
                        output_type="trimesh")[0]
        return mesh, use_mv

    # ------------------------------------------------------------ textura
    def texture(self, mesh, views, tex_size, render=None):
        """render: resolucion interna del horneado. 1024 = textura rapida."""
        if self.paint is None:
            return mesh, False
        render = int(render or self.p["render"])
        if (tex_size, render) != getattr(self, "_tex", None):
            self._set_texture_size(tex_size, render)
        imgs = [views["front"]] + [views[k] for k in ("back", "left", "right") if views.get(k)]
        try:
            # Varias referencias (frente + espalda...) si la version lo admite
            out = self.paint(mesh, image=imgs if len(imgs) > 1 else imgs[0])
        except Exception as e:
            self.log("  textura con varias vistas no admitida, solo frente:", e)
            out = self.paint(mesh, image=imgs[0])
        return out, True

    # ------------------------------------------------------------ todo
    def key(self, views, opts):
        h = hashlib.sha1()
        for k in VIEWS:
            v = views.get(k)
            if v is not None:
                h.update(k.encode())
                h.update(v.tobytes()[:: 97])
        h.update(json.dumps(opts, sort_keys=True).encode())
        return h.hexdigest()[:12]

    def run(self, front, back=None, left=None, right=None, sheet=None,
            sheet_order="front,left,back,right", remove_bg=True,
            steps=None, octree=None, faces=None, tex=None, seed=1234,
            guidance=5.0, rig="humanoide", height=1.8, rotate=0.0,
            video="Caminar", video_res=None, samples=None, turntable=True,
            texture=True, relieve=0.8, turbo=True, progress=lambda f, m: None, on_partial=None,
            videos=False, on_stage=None, detalle=True, motor="hunyuan", tex_rapida=False):
        self._ensure()
        quiet_logs()
        if not self.ready:
            self.load()
        P = self.p
        steps = int(steps or P["steps"])
        octree = int(octree or P["octree"])
        faces = int(faces or P["faces"])
        tex = int(tex or P["tex"])
        video_res = int(video_res or P["video_res"])
        samples = int(samples or P["samples"])
        t0 = time.time()

        progress(0.02, "Quitando fondo")
        views = {"front": self.prep(front, remove_bg), "back": self.prep(back, remove_bg),
                 "left": self.prep(left, remove_bg), "right": self.prep(right, remove_bg)}
        if sheet is not None:
            for k, v in self.split_sheet(sheet, sheet_order).items():
                if views.get(k) is None:
                    views[k] = v
        if views["front"] is None:
            raise ValueError("Falta la foto de frente")
        opts = dict(steps=steps, octree=octree, faces=faces, tex=tex, seed=int(seed),
                    guidance=guidance, rig=rig, height=height, rotate=rotate,
                    video=video, video_res=video_res, samples=samples,
                    turntable=bool(turntable), texture=bool(texture), relieve=float(relieve),
                    turbo=bool(turbo), videos=bool(videos), detalle=bool(detalle), motor=motor,
                    tex_rapida=bool(tex_rapida))
        k = self.key(views, opts)
        if k in self.cache and os.path.isdir(self.cache[k]["dir"]):
            self.log("Resultado en cache:", k)
            return self.cache[k]

        cleanup_outputs()
        out = os.path.join(config.OUT_DIR, time.strftime("%Y%m%d_%H%M%S_") + k)
        os.makedirs(out, exist_ok=True)
        shutil.copy(os.path.join(HERE, "estudio.html"), out)
        stage = on_stage or (lambda name, d: None)
        work = os.path.join(P["work_dir"], k)
        os.makedirs(work, exist_ok=True)
        for n, v in views.items():
            if v is not None:
                v.save(os.path.join(work, f"vista_{n}.png"))

        E = self.eta
        # Reparto del 100 % segun lo que tardo cada fase la vez anterior
        tot = E["forma"] + (E["textura"] if texture else 0) + E["blender"] + 4
        f_shape = 0.04 + 0.90 * E["forma"] / tot
        f_tex = f_shape + 0.90 * (E["textura"] if texture else 0) / tot

        def tick(a, b, secs, msg, stop):
            """Avanza la barra suavemente dentro de una fase larga."""
            t1 = time.time()
            while not stop.is_set():
                x = min(0.95, (time.time() - t1) / max(secs, 1))
                progress(a + (b - a) * x, msg)
                stop.wait(0.5)

        def phase(a, b, secs, msg, fn):
            stop = threading.Event()
            th = threading.Thread(target=tick, args=(a, b, secs, msg, stop), daemon=True)
            th.start()
            try:
                return fn()
            finally:
                stop.set()
                th.join()

        self.jobs["en_cola"] += 1
        if GPU_LOCK.locked():
            progress(0.03, "En cola: la GPU termina otro modelo")
        with GPU_LOCK:
            self.jobs["en_cola"] -= 1
            self.jobs["activos"] += 1
            try:
                nv = sum(v is not None for v in views.values())
                ts = time.time()
                mesh, used_mv = phase(0.05, f_shape, E["forma"],
                                      "Generando la forma 3D" + (" (varias vistas)" if nv > 1 else "")
                                      + (" · Turbo" if turbo else ""),
                                      lambda: self._shape(views, steps, octree, seed,
                                                          guidance, turbo, motor))
                t_shape = time.time() - ts
                progress(f_shape, "Limpiando y cerrando agujeros")
                # 1) malla completa en alta resolucion (todo el detalle de la IA)
                # Primero se reduce (las mallas de 1 millon de caras tardaban
                # ~50 s en repararse) y despues se repara la malla ya ligera.
                info_alta = len(mesh.faces)
                if info_alta > 200000:
                    try:
                        from hy3dgen.shapegen import FaceReducer
                        mesh = FaceReducer()(mesh, max_facenum=200000)
                    except Exception as e:
                        self.log("  reduccion previa omitida:", e)
                mesh = self._repair(mesh, None)
                try:
                    mesh.export(os.path.join(out, "malla_alta.glb"))
                except Exception as e:
                    self.log("  malla alta omitida:", e)
                # 2) se reduce despues a las caras pedidas (para textura y esqueleto)
                progress(f_shape + 0.005, f"Reduciendo de {info_alta:,} a {faces:,} caras")
                if len(mesh.faces) > faces:
                    from hy3dgen.shapegen import FaceReducer
                    mesh = FaceReducer()(mesh, max_facenum=faces)
                mesh.export(os.path.join(work, "arcilla.glb"))
                shutil.copy(os.path.join(work, "arcilla.glb"), out)
                stage("malla", out)          # etapa 1: la malla ya se ve
                ts = time.time()
                if texture:
                    textured, ok_tex = phase(f_shape + 0.01, f_tex, E["textura"],
                                             "Pintando la textura con IA",
                                             lambda: self.texture(mesh, views, tex,
                                                                  1024 if tex_rapida else None))
                else:
                    textured, ok_tex = mesh, False
                t_tex = time.time() - ts
                textured.export(os.path.join(work, "modelo_texturizado.glb"))
                try:
                    # PLY con color en cada vertice: slicers multicolor (Bambu, Prusa)
                    cm = textured.copy()
                    cm.visual = cm.visual.to_color()
                    cm.export(os.path.join(out, "modelo_color_impresion.ply"))
                except Exception as e:
                    self.log("  PLY de color omitido:", e)
                shutil.copy(os.path.join(work, "modelo_texturizado.glb"), out)
                stage("textura", out)        # etapa 2: con color
                try:
                    import torch
                    torch.cuda.empty_cache()
                except Exception:
                    pass
            finally:
                self.jobs["activos"] -= 1
        E["forma"] = 0.5 * E["forma"] + 0.5 * t_shape
        if texture and ok_tex:
            E["textura"] = 0.5 * E["textura"] + 0.5 * t_tex

        # Blender fuera del candado (la GPU ya genera la siguiente foto).
        # Dos procesos a la vez: uno exporta archivos, el otro renderiza videos.
        tb = time.time()
        inp = os.path.join(work, "modelo_texturizado.glb")
        # Por defecto solo el modelo interactivo: sin videos ni render de Cycles
        stages = ["export", "video"] if videos else ["export"]
        self._preview = bool(videos)
        self._detalle = bool(detalle)
        vstate = {"f": 0.0, "msg": "", "done": "video" not in stages}
        estate = {"f": 0.0}

        def eprog(x, msg):
            estate["f"] = max(estate["f"], x)
            progress(f_tex + (0.97 - f_tex) * estate["f"], msg)

        def vprog(x, msg):
            vstate["f"] = max(vstate["f"], x)
            vstate["msg"] = msg

        # Lo que ya existe se copia antes: el estudio puede abrir el modelo
        # en cuanto termina la exportacion.
        shutil.copy(os.path.join(HERE, "estudio.html"), out)
        for f in ("arcilla.glb", "modelo_texturizado.glb") + tuple(
                f"vista_{n}.png" for n in VIEWS):
            src = os.path.join(work, f)
            if os.path.exists(src):
                shutil.copy(src, out)
        fe = self.blender_pool.submit(
            self.blender, inp, out, rig, height, rotate, video, video_res, samples,
            turntable, relieve, "export", eprog,
            lambda: (stage("esqueleto", out), on_partial and on_partial(out)))
        fv = None
        if "video" in stages:
            # Los videos NO frenan la entrega: siguen en segundo plano y se
            # agregan al ZIP cuando terminan.
            fv = self.blender_pool.submit(
                self.blender, inp, out, rig, height, rotate, video, video_res, samples,
                turntable, relieve, "video", vprog, None)
        # Segundo proceso de Blender a la vez: OBJ, STL, piezas, pesos y LOD
        fx = self.blender_pool.submit(
            self.blender, inp, out, rig, height, rotate, video, video_res, samples,
            turntable, relieve, "extra", None, None)
        blog = fe.result()
        try:
            blog += "\n\n" + fx.result()
        except Exception as e:
            self.log("Blender extra:", e)
        t_bl = time.time() - tb
        E["blender"] = 0.5 * E["blender"] + 0.5 * t_bl
        try:
            json.dump(E, open(self._eta_path, "w"))
        except Exception:
            pass

        info = {}
        ip = os.path.join(out, "rig_info.json")
        if os.path.exists(ip):
            info = json.load(open(ip))
        ipx = os.path.join(out, "rig_info_extra.json")
        if os.path.exists(ipx):
            ix = json.load(open(ipx))
            info.setdefault("archivos", {}).update(ix.get("archivos", {}))
            for k_ in ("lod_caras", "piezas", "quads_caras"):
                if k_ in ix:
                    info[k_] = ix[k_]
            info.setdefault("avisos", []).extend(
                a_ for a_ in ix.get("avisos", []) if a_ not in info.get("avisos", []))
            os.remove(ipx)
        try:
            tipo_ = (info.get("clasificacion") or {}).get("tipo", info.get("rig", "humanoide"))
            fis = physics_data(textured, height, tipo_)
            info["fisica"] = fis
            json.dump({"masa_kg": fis["masa_kg"], "centro_masa_m": fis["centro_masa_m"],
                       "inercia_kg_m2": fis["inercia_kg_m2"], "dimensiones_m":
                       [fis["ancho_m"], fis["alto_m"], fis["fondo_m"]], "notas":
                       "Y arriba, origen en el suelo bajo el modelo. Para Rigidbody de "
                       "Unity (mass, centerOfMass) o Unreal (Mass, COM offset)."},
                      open(os.path.join(out, "fisica.json"), "w"), indent=2)
        except Exception as e:
            self.log("  datos fisicos omitidos:", e)
        info.update(caras_alta=locals().get("info_alta"), multivista=used_mv, textura_ia=ok_tex, segundos_forma=round(t_shape, 1),
                    segundos_textura=round(t_tex, 1), segundos_blender=round(t_bl, 1),
                    segundos_total=round(time.time() - t0, 1), turbo=bool(turbo),
                    ajustes=opts, perfil=P["perfil"], gpu=P["gpu"])
        json.dump(info, open(ip, "w"), indent=2, ensure_ascii=False, default=str)
        open(os.path.join(out, "blender.log"), "w").write(blog)
        progress(0.98, "Empaquetando ZIP")
        zp = out + ".zip"
        self._zip(out, zp)
        progress(1.0, "Listo")
        res = dict(dir=out, zip=zp, info=info, key=k, video_future=fv, video_state=vstate)

        def finish_videos(fut):
            try:
                vlog = fut.result()
                ipv = os.path.join(out, "rig_info_video.json")
                inf = json.load(open(ip))
                if os.path.exists(ipv):
                    iv = json.load(open(ipv))
                    inf.setdefault("archivos", {}).update(iv.get("archivos", {}))
                    inf.setdefault("avisos", []).extend(
                        a_ for a_ in iv.get("avisos", []) if a_ not in inf.get("avisos", []))
                    inf["segundos_videos"] = iv.get("segundos")
                    os.remove(ipv)
                json.dump(inf, open(ip, "w"), indent=2, ensure_ascii=False, default=str)
                res["info"] = inf
                with open(os.path.join(out, "blender.log"), "a") as fh:
                    fh.write("\n\n" + vlog)
                self._zip(out, zp)
            except Exception as e:
                self.log("videos:", e)
            finally:
                vstate["done"] = True
                shutil.rmtree(work, ignore_errors=True)

        if fv is not None:
            fv.add_done_callback(finish_videos)
        else:
            shutil.rmtree(work, ignore_errors=True)
        self.cache[k] = res
        self.log_mem()
        return res

    @staticmethod
    def _zip(out, zp):
        tmp = zp + ".tmp"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as z:
            for f in sorted(os.listdir(out)):
                comp = zipfile.ZIP_STORED if f.endswith((".mp4", ".png", ".glb", ".blend")) \
                    else zipfile.ZIP_DEFLATED
                z.write(os.path.join(out, f), f, compress_type=comp)
        os.replace(tmp, zp)

    def rerig(self, d, rig, progress=lambda f, m: None):
        """Vuelve a poner esqueleto/animaciones a un modelo ya generado con el
        tipo que eligio el usuario (sin repetir la IA). Unos 30-60 s."""
        inp = os.path.join(d, "modelo_texturizado.glb")
        ip = os.path.join(d, "rig_info.json")
        info = json.load(open(ip)) if os.path.exists(ip) else {}
        a = info.get("ajustes", {})
        args = (inp, d, rig, a.get("height", 1.8), a.get("rotate", 0.0), a.get("video", "Caminar"),
                a.get("video_res", 720), a.get("samples", 16), False, a.get("relieve", 0.8))
        progress(0.1, f"Poniendo esqueleto de tipo {rig}")
        fe = self.blender_pool.submit(self.blender, *args, "export", None, None)
        fx = self.blender_pool.submit(self.blender, *args, "extra", None, None)
        log_ = fe.result() + "\n\n" + fx.result()
        new = json.load(open(ip)) if os.path.exists(ip) else {}
        ipx = os.path.join(d, "rig_info_extra.json")
        if os.path.exists(ipx):
            ix = json.load(open(ipx))
            new.setdefault("archivos", {}).update(ix.get("archivos", {}))
            for k_ in ("lod_caras", "piezas", "quads_caras"):
                if k_ in ix:
                    new[k_] = ix[k_]
            os.remove(ipx)
        for k_ in ("segundos_forma", "segundos_textura", "multivista", "textura_ia",
                   "ajustes", "caras_alta", "turbo", "perfil", "gpu"):
            if k_ in info:
                new[k_] = info[k_]
        new.setdefault("ajustes", {})["rig"] = rig
        new["corregido_por_usuario"] = rig
        json.dump(new, open(ip, "w"), indent=2, ensure_ascii=False, default=str)
        with open(os.path.join(d, "blender.log"), "a") as fh:
            fh.write("\n\n=== re-esqueleto ===\n" + log_)
        self._zip(d, d + ".zip")
        progress(1.0, "Listo")
        return new

    # Hitos del log de Blender -> avance (0..1) de cada proceso
    MILESTONES = {
        "export": [("malla", .05, "Blender: preparando la malla"),
                   ("esqueleto", .12, "Blender: ajustando el esqueleto"),
                   ("proxy de pesos", .18, "Blender: calculando pesos"),
                   ("pesos reparados", .35, "Blender: pesos listos"),
                   ("mapas de relieve", .40, "Blender: relieve"),
                   ("exportado modelo_animado", .55, "Exportando GLB animado"),
                   ("exportado modelo_web.glb", .60, "GLB ligero para web"),
                   ("exportado modelo_rig.fbx", .65, "Exportando FBX"),
                   ("exportado piezas", .72, "Piezas por hueso"),
                   ("exportado pesos", .78, "Mapa de pesos"),
                   ("exportado modelo_lod", .86, "Versiones ligeras (LOD)"),
                   ("exportado modelo.blend", 1.0, "Archivo de Blender")],
        "video": [("malla", .05, "Video: preparando escena"),
                  ("pesos reparados", .25, "Video: esqueleto listo"),
                  ("render animacion", .30, "Renderizando video de animacion"),
                  ("render giro 360", .70, "Renderizando giro 360"),
                  ("listo", 1.0, "Videos listos")],
    }

    def blender(self, inp, out, rig, height, rotate, video, video_res, samples, turntable,
                relieve=0.6, stage="all", on_progress=None, on_ready=None):
        cmd = [config.BLENDER, "-b", "--factory-startup", "-t", "0", "-P",
               os.path.join(HERE, "blender_rig.py"), "--", "--in", inp, "--out", out,
               "--rig", rig, "--height", str(height), "--rotate", str(rotate),
               "--video", video, "--video_res", str(video_res), "--samples", str(samples),
               "--turntable", "1" if turntable else "0", "--relieve", str(relieve),
               "--detalle", "1" if getattr(self, "_detalle", True) else "0",
               "--memoria", _memoria_path(),
               "--stage", stage, "--preview", "1" if stage != "export" or self._preview else "0"]
        ms = self.MILESTONES.get(stage, self.MILESTONES["export"])
        lines = []
        pr = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, bufsize=1)
        done = 0
        for line in pr.stdout:
            if "Append frame" in line or line.startswith("Fra:"):
                m = re.search(r"Append frame (\d+)", line)
                if m and on_progress and stage == "video":
                    on_progress(min(.95, .3 + int(m.group(1)) / 400), "Renderizando video")
                continue
            lines.append(line.rstrip())
            if on_ready and ("exportado modelo_web.glb" in line or "exportado modelo_rig.fbx" in line):
                on_ready()          # el estudio ya puede abrir el modelo
                on_ready = None
            if line.startswith("[rig") and on_progress:
                for i, (key, x, msg) in enumerate(ms):
                    if i >= done and key in line:
                        done = i + 1
                        on_progress(x, msg)
        pr.wait()
        logtxt = "\n".join(lines)
        if pr.returncode != 0:
            self.log(logtxt[-3000:])
        return logtxt


_ENGINE = None


def get_engine(log=print):
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = Engine(log=log)
    return _ENGINE
