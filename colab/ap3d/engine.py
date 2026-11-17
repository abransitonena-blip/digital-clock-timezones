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
import hashlib
import io
import json
import os
import shutil
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


class Engine:
    def __init__(self, prof=None, log=print):
        self.p = prof or config.detect()
        self.log = log
        self.rembg = None
        self.shape = None
        self.shape_mv = None
        self.paint = None
        self.cache = {}
        self.ready = False
        self.blender_pool = cf.ThreadPoolExecutor(max_workers=self.p["workers"])
        os.makedirs(config.OUT_DIR, exist_ok=True)

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

    def load(self, want_mv=True, want_paint=True):
        import torch
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        torch.backends.cudnn.benchmark = True
        from hy3dgen.rembg import BackgroundRemover
        from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

        t = time.time()
        if self.rembg is None:
            self.rembg = BackgroundRemover()
        if self.shape is None:
            self.log("Cargando Hunyuan3D-2 (forma, 1 foto)...")
            self.shape = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
                "tencent/Hunyuan3D-2", subfolder="hunyuan3d-dit-v2-0",
                use_safetensors=True)
        if want_mv and self.shape_mv is None:
            self.log("Cargando Hunyuan3D-2mv (forma, varias vistas)...")
            try:
                self.shape_mv = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
                    "tencent/Hunyuan3D-2mv", subfolder="hunyuan3d-dit-v2-mv",
                    use_safetensors=True)
            except Exception as e:
                self.log("  2mv no disponible, se usara solo 1 foto:", e)
        if want_paint and self.paint is None:
            self.log("Cargando Hunyuan3D-Paint (textura)...")
            try:
                from hy3dgen.texgen import Hunyuan3DPaintPipeline
                self.paint = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2")
                self._set_texture_size(self.p["tex"])
                if self.p["offload"]:
                    self.paint.enable_model_cpu_offload()
            except Exception as e:
                self.log("  Textura IA no disponible (se exporta con color "
                         "proyectado de la foto):", e)
                self.paint = None
        if not self.p["all_on_gpu"] and self.shape_mv is not None:
            # GPU chica: el modelo multivista espera en la RAM
            self.shape_mv.to("cpu")
        self.ready = True
        self.log(f"Modelos listos en {time.time() - t:.0f}s")
        self.log_mem()

    def _set_texture_size(self, size):
        if self.paint is None:
            return
        try:
            from hy3dgen.texgen.differentiable_renderer.mesh_render import MeshRender
            self.paint.config.texture_size = size
            self.paint.config.render_size = self.p["render"]
            self.paint.render = MeshRender(default_resolution=self.p["render"],
                                           texture_size=size)
            self._tex = size
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
        if len(mesh.faces) > max_faces:
            mesh = FaceReducer()(mesh, max_facenum=max_faces)
        return mesh

    def shape_from(self, views, steps, octree, seed, guidance):
        import torch
        multi = {k: v for k, v in views.items() if v is not None}
        use_mv = self.shape_mv is not None and len(multi) > 1
        pipe = self.shape_mv if use_mv else self.shape
        if not self.p["all_on_gpu"]:
            other = self.shape if use_mv else self.shape_mv
            if other is not None:
                other.to("cpu")
            pipe.to("cuda")
            torch.cuda.empty_cache()
        img = multi if use_mv else views["front"]
        g = torch.Generator(device="cuda").manual_seed(int(seed))
        with torch.inference_mode():
            mesh = pipe(image=img, num_inference_steps=int(steps),
                        octree_resolution=int(octree), num_chunks=self.p["chunks"],
                        guidance_scale=float(guidance), generator=g,
                        output_type="trimesh")[0]
        return mesh, use_mv

    # ------------------------------------------------------------ textura
    def texture(self, mesh, views, tex_size):
        if self.paint is None:
            return mesh, False
        if tex_size != getattr(self, "_tex", None):
            self._set_texture_size(tex_size)
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
            texture=True, progress=lambda f, m: None):
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
                    turntable=bool(turntable), texture=bool(texture))
        k = self.key(views, opts)
        if k in self.cache and os.path.isdir(self.cache[k]["dir"]):
            self.log("Resultado en cache:", k)
            return self.cache[k]

        work = os.path.join(P["work_dir"], k)
        os.makedirs(work, exist_ok=True)
        for n, v in views.items():
            if v is not None:
                v.save(os.path.join(work, f"vista_{n}.png"))

        with GPU_LOCK:
            progress(0.08, "Generando la forma 3D con IA" +
                     (" (varias vistas)" if sum(v is not None for v in views.values()) > 1 else ""))
            ts = time.time()
            mesh, used_mv = self.shape_from(views, steps, octree, seed, guidance)
            t_shape = time.time() - ts
            progress(0.40, "Limpiando y cerrando agujeros")
            mesh = self._repair(mesh, faces)
            mesh.export(os.path.join(work, "arcilla.glb"))
            progress(0.48, "Pintando la textura con IA (frente y espalda)")
            ts = time.time()
            textured, ok_tex = self.texture(mesh, views, tex) if texture else (mesh, False)
            t_tex = time.time() - ts
            textured.export(os.path.join(work, "modelo_texturizado.glb"))
            try:
                import torch
                torch.cuda.empty_cache()
            except Exception:
                pass

        # Blender fuera del candado: la GPU queda libre para la siguiente foto
        progress(0.70, "Blender: esqueleto, pesos, animaciones y video")
        out = os.path.join(config.OUT_DIR, time.strftime("%Y%m%d_%H%M%S_") + k)
        os.makedirs(out, exist_ok=True)
        fut = self.blender_pool.submit(
            self.blender, os.path.join(work, "modelo_texturizado.glb"), out,
            rig, height, rotate, video, video_res, samples, turntable)
        blog = fut.result()

        for f in ("arcilla.glb", "modelo_texturizado.glb") + tuple(
                f"vista_{n}.png" for n in VIEWS):
            src = os.path.join(work, f)
            if os.path.exists(src):
                shutil.copy(src, out)
        info = {}
        ip = os.path.join(out, "rig_info.json")
        if os.path.exists(ip):
            info = json.load(open(ip))
        info.update(multivista=used_mv, textura_ia=ok_tex, segundos_forma=round(t_shape, 1),
                    segundos_textura=round(t_tex, 1), segundos_total=round(time.time() - t0, 1),
                    ajustes=opts, perfil=P["perfil"], gpu=P["gpu"])
        json.dump(info, open(ip, "w"), indent=2, ensure_ascii=False, default=str)
        open(os.path.join(out, "blender.log"), "w").write(blog)
        progress(0.97, "Empaquetando ZIP")
        zp = out + ".zip"
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(os.listdir(out)):
                z.write(os.path.join(out, f), f)
        shutil.rmtree(work, ignore_errors=True)
        res = dict(dir=out, zip=zp, info=info, key=k)
        self.cache[k] = res
        self.log_mem()
        return res

    def blender(self, inp, out, rig, height, rotate, video, video_res, samples, turntable):
        cmd = [config.BLENDER, "-b", "--factory-startup", "-t", "0", "-P",
               os.path.join(HERE, "blender_rig.py"), "--", "--in", inp, "--out", out,
               "--rig", rig, "--height", str(height), "--rotate", str(rotate),
               "--video", video, "--video_res", str(video_res), "--samples", str(samples),
               "--turntable", "1" if turntable else "0"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        logtxt = "\n".join(l for l in (r.stdout + "\n" + r.stderr).splitlines()
                           if "Append frame" not in l and not l.startswith("Fra:"))
        if r.returncode != 0:
            self.log(logtxt[-3000:])
        return logtxt


_ENGINE = None


def get_engine(log=print):
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = Engine(log=log)
    return _ENGINE
