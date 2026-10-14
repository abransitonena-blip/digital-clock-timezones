#!/usr/bin/env python3
"""Modelo financiero de AP Monitor 24 (7R Tour 24DC rev B + firmware + consola).

Sin dependencias externas (solo biblioteca estandar).

REGLA: ninguna entrada real esta llenada. El costo de piezas Extended, de
PCB y de ensamble es PD hasta cotizar (JLCPCB, LCSC, proveedor de caja/fuente,
agente aduanal). Por eso ENTRADAS_REALES es None en todo.

Uso:
  python3 modelo_ap_monitor.py --ejemplo            # corre con valores ILUSTRATIVOS
  python3 modelo_ap_monitor.py --json entradas.json # corre con tus cotizaciones
  python3 modelo_ap_monitor.py --plantilla          # imprime JSON vacio para llenar
  python3 modelo_ap_monitor.py                      # solo tabla de costo directo maximo

Todas las cantidades en MXN sin IVA, salvo las marcadas USD.
Marcas: [H] hipotesis, PD por determinar, [R] dato del repositorio.
"""
import json
import sys

LOTES = (5, 50, 200)  # primera tanda, lote 2, lote 3 (piloto de 5-10 kits dentro del lote 5 o 50)

# ----------------------------------------------------------------------------
# Entradas globales (por unidad o porcentaje). None = PD.
# ----------------------------------------------------------------------------
GLOBALES = {
    "tipo_cambio_mxn_usd": None,        # [H] rango 17-20; ref. FIX Banxico, ver MODELO.md
    "n_piezas_extended_unicas": 18,     # [R] contado del BOM 24DC (18 Extended, 4 Preferred, 25 Basic)
    "fuente_24v_mxn": None,             # PD cotizar; fuente certificada de terceros (riel DIN)
    "caja_din_mxn": None,               # PD cotizar; caja/carcasa DIN con mecanizado/etiquetado
    "etiqueta_mxn": None,               # PD cotizar; etiqueta de datos + advertencias
    "empaque_mxn": None,                # PD cotizar; caja, espuma, instructivo
    "flete_nacional_mxn_unidad": None,  # PD cotizar; paqueteria a cliente
    "garantia_pct_costo": None,         # [H] 3-10 % del costo directo como reserva
    "soporte_horas_unidad": None,       # [H] horas de soporte/puesta en marcha por kit
    "costo_hora_soporte_mxn": None,     # [H] costo interno o de tercero por hora
    "merma_placas_pct": None,           # [H] 0-20 % placas descartadas/retrabajo (rev B sin medir)
    "comision_canal_pct": None,         # [H] 0 venta directa; 10-25 % integrador/distribuidor
    "arancel_pct": None,                # PD agente aduanal (fraccion pendiente de confirmar)
    "iva_importacion_pct": 16.0,        # [V] tasa general, ver MODELO.md (acreditable; afecta flujo)
    "dta_y_agente_mxn_lote": None,      # PD honorarios agente aduanal + derechos por pedimento
    "precio_lista_mxn": None,           # [H] estudio: 5,000-7,000 (sin IVA); aqui un punto a probar
    "gastos_fijos_totales_mxn": None,   # PD suma NRE: certificaciones, abogado, contador, seguro, etc.
}

# Entradas por lote (USD salvo indicacion).
POR_LOTE = {
    "pcb_usd": None,            # PD fabricacion del PCB del lote (cotizacion JLCPCB)
    "piezas_usd": None,         # PD piezas del lote (Basic/Preferred/Extended, LCSC), total del lote
    "cargo_extended_usd": None, # PD cargo por pieza Extended unica x n_piezas_extended_unicas
    "ensamble_usd": None,       # PD ensamble SMT + stencil + ingenieria (cotizacion JLCPCB)
    "envio_usd": None,          # PD flete internacional del lote
    "mano_obra_final_mxn": None,# PD ensamble final/prueba/encajado por lote (propio o tercero)
}

# Ejemplo ILUSTRATIVO: numeros redondos, NO son cotizaciones ni estimaciones de mercado.
EJEMPLO_ILUSTRATIVO = {
    "globales": {
        "tipo_cambio_mxn_usd": 18.5, "n_piezas_extended_unicas": 18,
        "fuente_24v_mxn": 500, "caja_din_mxn": 300, "etiqueta_mxn": 20,
        "empaque_mxn": 50, "flete_nacional_mxn_unidad": 150,
        "garantia_pct_costo": 5, "soporte_horas_unidad": 2, "costo_hora_soporte_mxn": 300,
        "merma_placas_pct": 10, "comision_canal_pct": 0, "arancel_pct": 10,
        "iva_importacion_pct": 16.0, "dta_y_agente_mxn_lote": 3000,
        "precio_lista_mxn": 6000, "gastos_fijos_totales_mxn": 200000,
    },
    "lotes": {
        "5":   {"pcb_usd": 50,  "piezas_usd": 250,  "cargo_extended_usd": 50,  "ensamble_usd": 150,  "envio_usd": 40, "mano_obra_final_mxn": 1000},
        "50":  {"pcb_usd": 150, "piezas_usd": 1500, "cargo_extended_usd": 50,  "ensamble_usd": 300,  "envio_usd": 80, "mano_obra_final_mxn": 5000},
        "200": {"pcb_usd": 400, "piezas_usd": 5000, "cargo_extended_usd": 50,  "ensamble_usd": 600,  "envio_usd": 150, "mano_obra_final_mxn": 16000},
    },
}


def faltantes(g, l):
    f = [k for k in GLOBALES if g.get(k) is None]
    f += [k for k in POR_LOTE if l.get(k) is None]
    return f


def calcular(g, l, n, precio=None):
    """Devuelve dict con costos de un lote de n placas."""
    fx = g["tipo_cambio_mxn_usd"]
    merma = g["merma_placas_pct"] / 100.0
    # Valor en aduana (FOB + flete), en MXN
    valor_aduana = (l["pcb_usd"] + l["piezas_usd"] + l["cargo_extended_usd"]
                    + l["ensamble_usd"] + l["envio_usd"]) * fx
    arancel = valor_aduana * g["arancel_pct"] / 100.0
    base_iva = valor_aduana + arancel + g["dta_y_agente_mxn_lote"]
    iva_imp = base_iva * g["iva_importacion_pct"] / 100.0
    placas_lote = valor_aduana + arancel + g["dta_y_agente_mxn_lote"] + l["mano_obra_final_mxn"]
    # la merma encarece cada placa buena
    placa_unit = placas_lote / n / (1 - merma)
    otros = (g["fuente_24v_mxn"] + g["caja_din_mxn"] + g["etiqueta_mxn"]
             + g["empaque_mxn"] + g["flete_nacional_mxn_unidad"])
    directo = placa_unit + otros
    garantia = directo * g["garantia_pct_costo"] / 100.0
    soporte = g["soporte_horas_unidad"] * g["costo_hora_soporte_mxn"]
    cargado = directo + garantia + soporte
    c = g["comision_canal_pct"] / 100.0
    p = precio if precio is not None else g["precio_lista_mxn"]
    margen = (p * (1 - c) - cargado) / p if p else float("nan")
    contrib = p * (1 - c) - cargado
    equilibrio = g["gastos_fijos_totales_mxn"] / contrib if contrib > 0 else float("inf")
    # capital: salida de efectivo antes de cobrar (incluye IVA de importacion, recuperable)
    capital_sin_iva = placas_lote / (1 - merma) + otros * n
    capital_con_iva = capital_sin_iva + iva_imp
    return {
        "n": n, "placa_unit": placa_unit, "otros_unit": otros, "directo": directo,
        "garantia": garantia, "soporte": soporte, "cargado": cargado,
        "arancel_lote": arancel, "iva_import_lote": iva_imp,
        "margen_al_precio": margen, "equilibrio_unidades": equilibrio,
        "capital_sin_iva": capital_sin_iva, "capital_con_iva": capital_con_iva,
        "capital_con_iva_y_fijos": capital_con_iva + g["gastos_fijos_totales_mxn"],
        "precio": p,
    }


def precio_minimo(cargado, margen, comision_pct):
    d = 1 - margen - comision_pct / 100.0
    return cargado / d if d > 0 else float("inf")


def directo_maximo(precio, margen, comision_pct, garantia_pct, soporte_mxn):
    """Costo directo maximo que permite un precio y un margen (despejado)."""
    cargado_max = precio * (1 - margen - comision_pct / 100.0)
    return (cargado_max - soporte_mxn) / (1 + garantia_pct / 100.0)


def fm(x):
    return "inf" if x == float("inf") else f"{x:,.0f}"


def tabla_directo_maximo():
    print("\n== Costo directo maximo permitido (no necesita cotizacion) ==")
    print("Supuestos [H]: garantia 5 %, soporte 0 (sumelo luego). Precio sin IVA, MXN.")
    for com in (0, 15):
        print(f"\nComision de canal {com} %   (margen = (precio*(1-com) - costo cargado)/precio)")
        print("Precio   " + "".join(f"m={int(m*100)}%".rjust(10) for m in (0.30, 0.50, 2/3)))
        for p in (3750, 4560, 5000, 6000, 7000):
            print(f"{p:>6}   " + "".join(fm(directo_maximo(p, m, com, 5, 0)).rjust(10) for m in (0.30, 0.50, 2/3)))


def correr(cfg, etiqueta):
    g = cfg["globales"]
    print("=" * 78)
    print(etiqueta)
    print("=" * 78)
    resultados = {}
    for nlote in LOTES:
        l = cfg["lotes"].get(str(nlote), {})
        f = faltantes(g, l)
        if f:
            print(f"\nLote {nlote}: FALTAN entradas (PD): {', '.join(f)}")
            continue
        resultados[nlote] = calcular(g, l, nlote)
    if not resultados:
        return
    print("\n== Resultado por lote (MXN, sin IVA salvo indicacion) ==")
    enc = ["Concepto"] + [f"Lote {n}" for n in resultados]
    filas = [
        ("Placa por unidad (importada, con merma)", "placa_unit"),
        ("Fuente+caja+etiqueta+empaque+flete", "otros_unit"),
        ("COSTO DIRECTO unitario", "directo"),
        ("+ reserva garantia", "garantia"),
        ("+ soporte", "soporte"),
        ("COSTO CARGADO unitario", "cargado"),
        ("Arancel del lote", "arancel_lote"),
        ("IVA de importacion del lote (recuperable)", "iva_import_lote"),
        ("Capital del lote sin IVA", "capital_sin_iva"),
        ("Capital del lote con IVA importacion", "capital_con_iva"),
        ("Capital lote + gastos fijos (NRE)", "capital_con_iva_y_fijos"),
        ("Equilibrio (unidades, cubre gastos fijos)", "equilibrio_unidades"),
    ]
    print(enc[0].ljust(44) + "".join(e.rjust(14) for e in enc[1:]))
    for nombre, k in filas:
        print(nombre.ljust(44) + "".join(fm(r[k]).rjust(14) for r in resultados.values()))
    p = g["precio_lista_mxn"]
    print("Margen al precio de prueba {:,.0f}".format(p).ljust(44)
          + "".join(f"{r['margen_al_precio']*100:,.1f} %".rjust(14) for r in resultados.values()))
    print("\n== Precio minimo (sin IVA) para margen objetivo ==")
    print("Margen".ljust(10) + "".join(f"Lote {n}".rjust(14) for n in resultados))
    for m in (0.30, 0.50, 2/3):
        print(f"{m*100:.0f} %".ljust(10) + "".join(
            fm(precio_minimo(r['cargado'], m, g['comision_canal_pct'])).rjust(14) for r in resultados.values()))
    print("(66.7 % = regla 'precio >= 3 x costo' de ANALISIS_ECOSISTEMA.md §6, aplicada al costo cargado)")

    # Sensibilidad una a una (+-20 %) sobre el costo cargado del lote 50 (o el primero disponible)
    ref = 50 if 50 in resultados else next(iter(resultados))
    l0 = cfg["lotes"][str(ref)]
    base = resultados[ref]["cargado"]
    print(f"\n== Sensibilidad una a una, lote {ref}: costo cargado unitario (base {fm(base)}) ==")
    print("Variable".ljust(30) + "-20 %".rjust(10) + "base".rjust(10) + "+20 %".rjust(10) + "  rango".rjust(10))
    palancas = [(("g", k)) for k in ("tipo_cambio_mxn_usd", "fuente_24v_mxn", "caja_din_mxn", "arancel_pct",
                                      "merma_placas_pct", "garantia_pct_costo", "soporte_horas_unidad")]
    palancas += [(("l", k)) for k in ("pcb_usd", "piezas_usd", "cargo_extended_usd", "ensamble_usd", "envio_usd")]
    out = []
    for dom, k in palancas:
        vals = []
        for mult in (0.8, 1.0, 1.2):
            g2, l2 = dict(g), dict(l0)
            (g2 if dom == "g" else l2)[k] = (g if dom == "g" else l0)[k] * mult
            vals.append(calcular(g2, l2, ref)["cargado"])
        out.append((k, vals))
    out.sort(key=lambda t: -(t[1][2] - t[1][0]))
    for k, v in out:
        print(k.ljust(30) + "".join(fm(x).rjust(10) for x in v) + fm(v[2] - v[0]).rjust(10))

    print(f"\n== Cuadricula lote {ref}: costo cargado vs piezas (filas) y tipo de cambio (columnas) ==")
    fxs = [g["tipo_cambio_mxn_usd"] * m for m in (0.9, 1.0, 1.1)]
    print("piezas x".ljust(12) + "".join(f"FX {x:.2f}".rjust(12) for x in fxs))
    for mp in (0.7, 1.0, 1.5, 2.0):
        fila = []
        for x in fxs:
            g2, l2 = dict(g), dict(l0)
            g2["tipo_cambio_mxn_usd"] = x
            l2["piezas_usd"] = l0["piezas_usd"] * mp
            fila.append(calcular(g2, l2, ref)["cargado"])
        print(f"{mp:.1f}".ljust(12) + "".join(fm(v).rjust(12) for v in fila))

    print(f"\n== Margen del lote {ref} segun precio de lista (comision {g['comision_canal_pct']} %) ==")
    for pr in (5000, 6000, 7000):
        r = calcular(g, l0, ref, precio=pr)
        print(f"precio {pr:>5}: margen {r['margen_al_precio']*100:6.1f} %   equilibrio {fm(r['equilibrio_unidades'])} unidades")


def main(argv):
    if "--plantilla" in argv:
        print(json.dumps({"globales": GLOBALES, "lotes": {str(n): POR_LOTE for n in LOTES}}, indent=2, ensure_ascii=False))
        return
    tabla_directo_maximo()
    if "--ejemplo" in argv:
        correr(EJEMPLO_ILUSTRATIVO,
               "VALORES ILUSTRATIVOS - NO SON COTIZACIONES NI DATOS. Solo prueban que el modelo corre.")
    elif "--json" in argv:
        ruta = argv[argv.index("--json") + 1]
        with open(ruta, encoding="utf-8") as fh:
            cfg = json.load(fh)
        correr(cfg, f"Entradas de {ruta}")
    else:
        print("\nSin entradas: todo costo es PD. Use --plantilla para generar el JSON a llenar.")


if __name__ == "__main__":
    main(sys.argv[1:])
