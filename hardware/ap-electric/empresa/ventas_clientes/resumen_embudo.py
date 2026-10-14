#!/usr/bin/env python3
"""Resume el embudo de solicitudes y prospectos de AP Monitor 24.

Uso:
    python3 resumen_embudo.py seguimiento_plantilla.csv
    python3 resumen_embudo.py archivo.csv --hoy 2026-10-14 --dias-vencido 7

Sin dependencias (solo biblioteca estandar). Lee el CSV definido en
03_SEGUIMIENTO.md. No modifica el archivo. No inventa datos: si el CSV esta
vacio o faltan campos, lo dice.
"""
import argparse
import csv
import sys
from collections import Counter
from datetime import date, datetime

# Estados que usa la pagina (web/index.html), en orden de embudo.
ESTADOS = [
    "Recibida",
    "En revisión",
    "Respondida",
    "Piloto o muestra confirmados",
    "En lista de espera",
    "Cerrada",
    "No viable",
]
ESTADOS_ABIERTOS = {"Recibida", "En revisión", "Respondida",
                    "Piloto o muestra confirmados", "En lista de espera"}
SEMAFOROS = ["verde", "amarillo", "rojo", "sin_dato"]
COLUMNAS = [
    "id", "fecha_alta", "origen", "tipo_registro", "folio", "empresa",
    "contacto", "cargo", "correo_o_telefono", "perfil", "ciudad_estado",
    "tipo_solicitud", "estado", "etapa_descubrimiento", "semaforo",
    "maquinas_sin_datos", "sensores", "bloqueador_principal",
    "disposicion_pago", "rango_pago_mencionado_mxn", "fecha_ultimo_contacto",
    "proximo_paso", "fecha_proximo_paso", "responsable",
    "consentimiento_datos", "notas",
]


def fecha(texto):
    texto = (texto or "").strip()
    if not texto:
        return None
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        return None


def barra(n, total, ancho=20):
    if total <= 0:
        return ""
    return "#" * round(ancho * n / total)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("csv", help="ruta del CSV de seguimiento")
    ap.add_argument("--hoy", help="fecha de referencia AAAA-MM-DD (por omision, hoy)")
    ap.add_argument("--dias-vencido", type=int, default=7,
                    help="dias sin contacto para marcar seguimiento vencido (7)")
    args = ap.parse_args()

    hoy = fecha(args.hoy) if args.hoy else date.today()
    if hoy is None:
        sys.exit("--hoy debe ser AAAA-MM-DD")

    try:
        with open(args.csv, newline="", encoding="utf-8-sig") as f:
            lector = csv.DictReader(f)
            faltan = [c for c in COLUMNAS if c not in (lector.fieldnames or [])]
            filas = list(lector)
    except OSError as e:
        sys.exit("No se pudo leer el archivo: %s" % e)

    if faltan:
        print("AVISO: faltan columnas: " + ", ".join(faltan))
    n = len(filas)
    print("Resumen del embudo al %s  (archivo: %s)" % (hoy, args.csv))
    print("Registros: %d" % n)
    if n == 0:
        print("No hay registros. Sin entrevistas no hay cifras (ver 06_METRICAS_Y_REGLAS.md).")
        return
    if any("FICT" in (r.get("id") or "") or "FICTICI" in (r.get("empresa") or "")
           for r in filas):
        print("*** CONTIENE DATOS FICTICIOS: no son evidencia real. ***")

    def g(r, k):
        return (r.get(k) or "").strip()

    # Estados
    estados = Counter(g(r, "estado") for r in filas)
    invalidos = [(g(r, "id"), e) for r in filas
                 for e in [g(r, "estado")] if e not in ESTADOS]
    print("\nEmbudo por estado")
    for e in ESTADOS:
        print("  %-30s %3d  %s" % (e, estados.get(e, 0), barra(estados.get(e, 0), n)))
    if invalidos:
        print("  AVISO: estados no reconocidos: " +
              "; ".join("%s=%r" % x for x in invalidos))

    # Origen y tipo
    print("\nPor origen: " + ", ".join("%s %d" % (k or "(vacio)", v)
          for k, v in Counter(g(r, "origen") for r in filas).most_common()))
    print("Por perfil: " + ", ".join("%s %d" % (k or "(vacio)", v)
          for k, v in sorted(Counter(g(r, "perfil") for r in filas).items())))

    # Descubrimiento
    etapas = Counter(g(r, "etapa_descubrimiento") for r in filas)
    print("Etapa de descubrimiento: " + ", ".join("%s %d" % (k or "(vacio)", v)
          for k, v in etapas.most_common()))
    hechas = [r for r in filas if g(r, "etapa_descubrimiento") in ("llamada_hecha", "visita_hecha")]
    print("Conversaciones hechas (llamada o visita): %d de 10 meta" % len(hechas))

    # Semaforo
    sem = Counter(g(r, "semaforo") or "sin_dato" for r in filas)
    print("\nSemaforo (sobre todos los registros)")
    for s in SEMAFOROS:
        print("  %-9s %3d" % (s, sem.get(s, 0)))
    sem_h = Counter(g(r, "semaforo") or "sin_dato" for r in hechas)
    print("Semaforo (solo conversaciones hechas): " +
          ", ".join("%s %d" % (s, sem_h.get(s, 0)) for s in SEMAFOROS))

    # Disposicion a pagar (solo conversaciones hechas)
    dp = Counter(g(r, "disposicion_pago") or "sin_dato" for r in hechas)
    si = dp.get("si", 0)
    print("\nDisposicion a pagar (conversaciones hechas): " +
          ", ".join("%s %d" % (k, v) for k, v in dp.most_common()))
    print("  'si' = menciona rango propio y rubro; ver definicion en 06_METRICAS_Y_REGLAS.md")
    if len(hechas) >= 10:
        regla = "PARAR/REVISAR: menos de 3 de 10" if si < 3 else "CONTINUAR (regla minima cumplida)"
        print("  %d de %d dispuestos -> %s" % (si, len(hechas), regla))
    else:
        print("  Solo %d conversaciones hechas: la regla de 3 de 10 aun no se puede evaluar." % len(hechas))

    # Bloqueadores y sensores
    blo = Counter(g(r, "bloqueador_principal") or "(vacio)" for r in filas)
    print("\nBloqueadores: " + ", ".join("%s %d" % (k, v) for k, v in blo.most_common()))
    sen = Counter(g(r, "sensores") or "(vacio)" for r in filas)
    print("Sensores: " + ", ".join("%s %d" % (k, v) for k, v in sen.most_common()))
    npn = sum(1 for r in filas if "npn" in g(r, "sensores").lower()
              or g(r, "bloqueador_principal").lower() == "npn")
    print("Registros con NPN como sensor o bloqueo: %d" % npn)

    # Seguimiento vencido
    print("\nSeguimientos vencidos (abiertos, ultimo contacto hace mas de %d dias o proximo paso con fecha pasada)"
          % args.dias_vencido)
    venc = 0
    for r in filas:
        if g(r, "estado") not in ESTADOS_ABIERTOS:
            continue
        uc, pp = fecha(g(r, "fecha_ultimo_contacto")), fecha(g(r, "fecha_proximo_paso"))
        motivos = []
        if uc is None:
            motivos.append("sin fecha de contacto")
        elif (hoy - uc).days > args.dias_vencido:
            motivos.append("%d dias sin contacto" % (hoy - uc).days)
        if pp is not None and pp < hoy:
            motivos.append("proximo paso vencido (%s)" % pp)
        if motivos:
            venc += 1
            print("  %s %s [%s]: %s" % (g(r, "id"), g(r, "empresa"), g(r, "estado"),
                                      "; ".join(motivos)))
    if venc == 0:
        print("  ninguno")

    # Calidad del dato
    sin_cons = [g(r, "id") for r in filas if g(r, "consentimiento_datos").lower() != "si"]
    if sin_cons:
        print("\nAVISO: sin consentimiento de datos registrado (no usar su contacto): " +
              ", ".join(sin_cons))
    print("\nNota: los conteos son del archivo; no son estimaciones de mercado.")


if __name__ == "__main__":
    main()
