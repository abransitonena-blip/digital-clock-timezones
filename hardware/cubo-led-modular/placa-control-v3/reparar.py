"""Reparación incremental: parte del ruteo guardado (cobre.json + ruteo.json) y conecta las redes abiertas
arrancando y rehaciendo los vecinos que estorban. Un cambio solo se acepta si baja el número de redes abiertas.
Uso: python3.11 reparar.py [intentos]"""
import sys, json, copy, random, time
import fab, geom as G

def cargar():
    P = fab.Placa()
    ru = json.load(open("ruteo.json"))
    P.cobre = [[c for c in capa if c[2] != "plano"] for capa in fab.cargar_cobre()]
    P.vias = [tuple(v) for v in ru["vias"]]; P.pistas = ru["pistas"]
    P.repintar(); return P

def abiertas(P):
    redes = sorted({q["net"] for q in P.pads if not q["net"].startswith("NC")} - {"GND"})
    return [n for n in redes if len(P.islas(n)) > 1]

def estado(P): return (copy.deepcopy(P.cobre), list(P.vias), copy.deepcopy(P.pistas))
def volver(P, e): P.cobre, P.vias, P.pistas = copy.deepcopy(e[0]), list(e[1]), copy.deepcopy(e[2]); P.repintar()

if __name__ == "__main__":
    random.seed(1); t0 = time.time()
    P = cargar(); ab = abiertas(P); print("abiertas al inicio:", ab)
    for it in range(int(sys.argv[1]) if len(sys.argv) > 1 else 40):
        if not ab: break
        n = ab[it % len(ab)]; e = estado(P)
        if P.conectar_red(n):
            nuevo = abiertas(P)
            if len(nuevo) < len(ab): ab = nuevo; print(f"  {it}: {n} directo → {len(ab)} abiertas"); continue
            volver(P, e)
        if not hasattr(P, "ult_par"): continue
        cand = [m for m in P.estorbos(n) if m not in ("GND",)]
        random.shuffle(cand); quitar = cand[:random.choice((1, 2, 3, 4))]
        for m in quitar: P.arrancar(m)
        orden = [n] + quitar
        for m in orden: P.conectar_red(m)
        for m in orden:
            if len(P.islas(m)) > 1: P.conectar_red(m)
        nuevo = abiertas(P)
        if len(nuevo) < len(ab): ab = nuevo; print(f"  {it}: {n} (quité {', '.join(quitar)}) → {len(ab)} abiertas  {time.time()-t0:.0f}s")
        else: volver(P, e)
        sys.stdout.flush()
    P.planos()
    if len(P.islas("GND")) > 1:
        for l in (0, 1): P.cobre[l] = [c for c in P.cobre[l] if c[2] != "plano"]
        P.repintar(); P.planos(); P.conectar_red("GND")
        for l in (0, 1): P.cobre[l] = [c for c in P.cobre[l] if c[2] != "plano"]
        P.repintar(); P.planos()
    err, ab2 = P.drc()
    json.dump(dict(pistas=P.pistas, vias=P.vias), open("ruteo.json", "w"), indent=0)
    fab.guardar_cobre(P.cobre)
    print("vias:", len(P.vias), " pistas:", len(P.pistas))
    print("DRC:", len(err), "errores"); [print("  ", x) for x in err[:20]]
    print("Abiertas:", len(ab2)); [print("  ", a) for a in ab2]
