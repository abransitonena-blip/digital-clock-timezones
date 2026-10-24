"""Hoja de diagnóstico para un canal que no da voltaje: lado del cobre visto como queda en la placa
(espejo de cobre_planchar.svg), con puntos de prueba numerados. Escribe diagnostico.html."""
import os, runpy
here = os.path.dirname(os.path.abspath(__file__))
g = runpy.run_path(os.path.join(here, "generar.py"))
W, H, pads, traces, TW, DRILL, CU_TEXT = (g[k] for k in ("W", "H", "pads", "traces", "TW", "DRILL", "CU_TEXT"))
X = lambda x: W - x                      # visto desde el cobre
P = {(p[0], p[1]): (p[2], p[3]) for p in pads}
CU, OR = "#b8733c", "#e8590c"
# punto: (número, pieza, pin, burbuja dx, dy) — dx/dy en la vista del cobre, canal 1
PUNTOS = [(1, "WL", "", -3.2, -2.6), (8, "WN", "", 0, -2.9),
          (2, "C", "L", -2.8, 2.6), (3, "C", "B", 0, 3.2), (4, "RS", "B", -0.2, 3.2), (5, "RS", "A", 0, -3.1),
          (9, "BR", "+", -3.3, 0.5), (6, "BR", "~1", -3.3, 0), (7, "BR", "~2", -3.3, 0), (10, "BR", "-", -3.3, 0),
          (11, "J", "+", 3.0, -1.2), (12, "J", "-", -3.0, 2.8)]
def svg():
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="128mm" height="128mm" viewBox="-1 -1 {W+2} {H+2}" font-family="Arial,Helvetica,sans-serif">',
         f'<rect x="0" y="0" width="{W}" height="{H}" rx="1" fill="#f3efe6" stroke="#555" stroke-width="0.3"/>']
    for n, pts in traces:
        d = "M" + " L".join(f"{X(x):.2f} {y:.2f}" for x, y in pts)
        o.append(f'<path d="{d}" fill="none" stroke="{CU}" stroke-width="{TW}" stroke-linecap="round" stroke-linejoin="round"/>')
    for p in pads:
        r, pn, x, y, n, f, w, h = p
        if r.startswith("MH"):
            o.append(f'<circle cx="{X(x)}" cy="{y}" r="{w/2}" fill="none" stroke="{CU}" stroke-width="0.4"/>'); continue
        if f == "r": o.append(f'<rect x="{X(x)-w/2:.2f}" y="{y-h/2:.2f}" width="{w}" height="{h}" rx="{min(w,h)/2}" fill="{CU}"/>')
        else: o.append(f'<circle cx="{X(x)}" cy="{y}" r="{w/2}" fill="{CU}"/>')
        o.append(f'<circle cx="{X(x)}" cy="{y}" r="{DRILL/2}" fill="#fff"/>')
    for (x, y, h, t) in CU_TEXT:
        o.append(f'<text x="{X(x)}" y="{y}" text-anchor="middle" font-weight="700" font-size="{h}" fill="{CU}">{t}</text>')
    hechos = set()
    for s, f, k in (("1", lambda y: y, 1), ("2", lambda y: H - y, -1)):
        for num, ref, pin, dx, dy in PUNTOS:
            key = ref if ref in ("WL", "WN") else ref + s
            if (key, pin) in hechos: continue
            hechos.add((key, pin))
            x, y = P[(key, pin)]
            if ref in ("WL", "WN"): px, py = X(x), y
            else: px, py = X(x), y
            bx, by = px + dx, py + (dy * k if ref not in ("WL", "WN") else dy)
            o.append(f'<circle cx="{px}" cy="{py}" r="1.85" fill="none" stroke="{OR}" stroke-width="0.45"/>')
            o.append(f'<path d="M{px} {py} L{bx:.2f} {by:.2f}" stroke="{OR}" stroke-width="0.3"/>')
            o.append(f'<circle cx="{bx:.2f}" cy="{by:.2f}" r="1.45" fill="{OR}"/>')
            o.append(f'<text x="{bx:.2f}" y="{by+0.62:.2f}" text-anchor="middle" font-size="1.75" font-weight="700" fill="#fff">{num}</text>')
    o.append(f'<text x="25" y="49.2" text-anchor="middle" font-size="1.3" fill="#555">Visto desde el lado del cobre (el texto se lee derecho)</text>')
    o.append('</svg>'); return "\n".join(o)

FILAS = [
 ("1 → 2", "Continuidad", "Pita", "Pista L rota o soldadura fría en el X2"),
 ("2 ↔ 3", "Ω (escala 2 MΩ)", "≈ 1 MΩ", "0 Ω: X2 en corto. OL: R de 1 MΩ abierta o mal soldada"),
 ("3 → 4", "Continuidad", "Pita", "Pista corta X2–R 150 Ω rota"),
 ("4 ↔ 5", "Ω (escala 200 Ω)", "≈ 150 Ω", "OL: R de 150 Ω quemada o soldadura fría (lo más común)"),
 ("5 → 6", "Continuidad", "Pita", "Pista hacia el puente rota, o pata ~ del puente sin soldar"),
 ("7 → 8", "Continuidad", "Pita", "Pista N rota hasta ese puente"),
 ("6 → 9 y 7 → 9", "Diodo: roja en ~, negra en +", "0.4 – 0.7", "OL en uno: puente abierto. 0.00: puente en corto"),
 ("10 → 6 y 10 → 7", "Diodo: roja en −, negra en ~", "0.4 – 0.7", "Igual que arriba; al revés debe marcar OL"),
 ("9 → 11", "Continuidad", "Pita", "Pista + a la salida rota"),
 ("10 → 12", "Continuidad", "Pita", "Pista − a la salida rota"),
 ("11 ↔ 12", "Continuidad", "NO pita", "Si pita: corto en la salida o puente de soldadura"),
]
filas = "".join(f"<tr><td class=n>{a}</td><td>{b}</td><td class=c>{c}</td><td class=v></td><td class=v></td><td>{d}</td></tr>" for a, b, c, d in FILAS)
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size: letter; margin: 11mm 12mm; }}
body {{ font-family: Arial, Helvetica, sans-serif; font-size: 9.6pt; color: #111; margin: 0; }}
h1 {{ font-size: 17pt; margin: 0 0 1mm; }} h2 {{ font-size: 11.5pt; margin: 4mm 0 1.5mm; border-bottom: 1.5px solid #111; }}
.sub {{ color: #444; margin-bottom: 2mm; }}
.alerta {{ border: 2px solid {OR}; border-radius: 3mm; padding: 2mm 3mm; background: #fff4ec; }}
.fig {{ text-align: center; margin: 2mm 0 0; }}
table {{ border-collapse: collapse; width: 100%; font-size: 8.8pt; }}
th, td {{ border: 1px solid #999; padding: 1.1mm 1.5mm; vertical-align: top; }} th {{ background: #eee; text-align: left; }}
td.n {{ font-weight: 700; white-space: nowrap; color: {OR}; }} td.c {{ font-weight: 700; white-space: nowrap; }} td.v {{ width: 13mm; }}
ul {{ margin: 1mm 0; padding-left: 5mm; }} li {{ margin: 0.6mm 0; }}
.pb {{ page-break-before: always; }}
</style></head><body>
<h1>Diagnóstico · canal que no da voltaje</h1>
<div class="sub">Fuente capacitiva AP · 2 canales · 5 × 5 cm. Compara el canal malo con el bueno: deben marcar lo mismo en cada punto.</div>
<div class="alerta"><b>Sin corriente.</b> Desenchufa, espera 1 minuto y mide voltaje DC entre + y − de cada salida.
No toques la placa hasta que marque menos de 5 V. Todas las mediciones de la tabla son con la placa <b>desconectada</b>.</div>
<div class="fig">{svg()}</div>
<p style="margin:1mm 0 0">Los números son iguales en los dos canales. Canal 1 = lado de la marca <b>S1</b>; canal 2 = lado de <b>S2</b>.
1 (L) y 8 (N) son la entrada común.</p>
<h2 class="pb">Mediciones (anota lo que marca)</h2>
<table><tr><th>Puntos</th><th>Multímetro en</th><th>Debe marcar</th><th>Canal 1</th><th>Canal 2</th><th>Si no marca eso</th></tr>{filas}</table>
<h2>Por qué el voltaje "va bajando"</h2>
<p>Si al medir la salida el voltaje empieza alto y baja solo hasta cero, al electrolítico <b>no le está llegando corriente</b>:
lo que ves es su carga descargándose por el multímetro y la resistencia de 220 kΩ. El problema está antes del puente
(puntos 1 a 8), casi siempre una <b>soldadura fría</b> o la R de 150 Ω abierta. Si a veces da y a veces no, es soldadura fría segura.</p>
<h2>Arreglo rápido</h2>
<ul>
<li>Recalienta con soldadura nueva todas las uniones de ese canal: 2 del X2, 2 de la R 150 Ω, 2 de la R 1 MΩ y 4 del puente.
Cada una debe quedar brillante, en forma de volcancito, mojando el pad y la pata.</li>
<li>Una pista rota (fisura fina, se ve a contraluz) se arregla soldando encima un pedazo de alambre o una pata de resistencia sobrante.</li>
<li>Si una pieza mide mal también fuera de la placa, cámbiala por una igual.</li>
</ul>
<h2>Prueba con corriente (después de arreglar)</h2>
<ul>
<li>Conecta primero los LEDs, luego enchufa. Nunca conectes LEDs con la placa energizada.</li>
<li>Multímetro en voltaje DC, escala 200 V o más, entre + y − de la salida, sin tocar nada más.</li>
<li>Sin LEDs: 170 – 180 V. Con LEDs: la suma de sus voltajes (20 rojos × 2 V ≈ 40 V). Debe quedarse <b>fijo</b>, no bajar.</li>
<li>Si marca negativo (−40 V), los cables de esa salida están al revés: intercambia rojo y negro.</li>
</ul>
</body></html>"""
open(os.path.join(here, "diagnostico.html"), "w").write(html)
print("diagnostico.html escrito")
