"""Genera los documentos PÚBLICOS (hojas de datos, manual de usuario, póliza de garantía) en HTML → PDF tamaño carta,
y src/datos/fichas.json para la página Soporte del sitio. Fuente única: datos.py (+ la curva de carga del informe térmico).
Uso: python3.11 hacer_publicos.py && NODE_PATH=$(npm root -g) node pdf.cjs"""
import os, re, json, html
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import datos as D

AQUI = os.path.dirname(os.path.abspath(__file__))
SITIO = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
e = html.escape

# ---------------------------------------------------------------- curva de carga (del informe térmico)
def curva():
    md = open(os.path.join(AQUI, "..", "analisis", "informe_termico.md")).read()
    filas = {}
    for m in re.finditer(r"^\| ([^|]+?) \|((?: \d+ % \|)+)\s*$", md, re.M):
        filas[m.group(1).strip()] = [int(x) for x in re.findall(r"(\d+) %", m.group(2))]
    ts = D.CURVA_CUBO["temperaturas"]
    fig, ax = plt.subplots(figsize=(6.2, 2.9), dpi=150)
    for (et, clave), col in zip(D.CURVA_CUBO["aluminio"].items(), ("#0b7d55", "#1971c2")):
        ax.plot(ts, filas[clave], "-o", ms=3, color=col, label=f"Aluminio · {et}")
    pl = {k: v for k, v in filas.items() if k.endswith("plástico")}
    perf = {"12V 5A": 60, "24V 3A": 72.9, "5V 3A": 14.9, "15V 3A": 45.2, "12V 2A": 24}
    wmax = [max(perf[k.split(" · ")[0]] * v[i] / 100 for k, v in pl.items()) for i in range(len(ts))]
    ax2 = ax.twinx()
    ax2.plot(ts, wmax, "--s", ms=3, color="#a86b12", label="ASA · potencia máxima (W, eje derecho)")
    ax.set_xlabel("Temperatura ambiente (°C)"); ax.set_ylabel("Carga continua (%)"); ax2.set_ylabel("W (cuerpo ASA)")
    ax.set_ylim(0, 105); ax2.set_ylim(0, 25); ax.grid(alpha=.3)
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=7, loc="lower left")
    fig.tight_layout(); fig.savefig(os.path.join(AQUI, "curva_carga.png")); plt.close(fig)
    return filas, wmax

# ---------------------------------------------------------------- piezas HTML
CSS = """
@page { size: Letter; margin: 14mm 15mm 16mm; }
* { box-sizing: border-box; }
body { font: 10pt/1.45 'DejaVu Sans', system-ui, sans-serif; color: #18201c; margin: 0; }
h1 { font-size: 22pt; margin: 0; letter-spacing: -.01em; } h2 { font-size: 12.5pt; margin: 14px 0 6px; color: #0b7d55; border-bottom: 1.5px solid #0b7d55; padding-bottom: 2px; }
h3 { font-size: 10.5pt; margin: 10px 0 4px; }
.cab { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 3px solid #0b7d55; padding-bottom: 8px; margin-bottom: 10px; }
.marca { display: flex; gap: 8px; align-items: center; } .marca i { background: #0b7d55; color: #fff; font-style: normal; font-weight: 800; border-radius: 6px; padding: 4px 7px; }
.meta { text-align: right; font-size: 8.5pt; color: #5a6862; } .pre { color: #a86b12; font-weight: 700; }
.sub { color: #5a6862; font-size: 11pt; margin-top: 2px; }
table { width: 100%; border-collapse: collapse; margin: 4px 0 6px; font-size: 9.3pt; page-break-inside: avoid; }
td, th { border-bottom: 1px solid #dfe6e2; padding: 4px 6px; text-align: left; vertical-align: top; }
th { background: #eef4f1; font-size: 8.5pt; text-transform: uppercase; letter-spacing: .04em; color: #43514a; }
td:first-child { width: 38%; color: #43514a; }
.dos { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.caja { border: 1px solid #dfe6e2; border-radius: 8px; padding: 8px 10px; background: #f7faf8; page-break-inside: avoid; }
.alerta { border-left: 4px solid #c0392b; background: #fdf1ef; padding: 7px 10px; margin: 6px 0; page-break-inside: avoid; }
.nota { border-left: 4px solid #a86b12; background: #fbf5ea; padding: 7px 10px; margin: 6px 0; font-size: 9pt; page-break-inside: avoid; }
ol, ul { margin: 4px 0 6px 18px; padding: 0; } li { margin: 2px 0; }
.pie { position: fixed; bottom: -10mm; left: 0; right: 0; font-size: 7.5pt; color: #8a968f; text-align: center; }
img.fig { width: 100%; max-width: 165mm; display: block; margin: 4px auto; }
.salto { page-break-before: always; }
.firma { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 16px; } .firma div { border-top: 1px solid #18201c; padding-top: 3px; font-size: 8.5pt; text-align: center; }
.campo { border-bottom: 1px solid #9aa6a0; display: inline-block; min-width: 55mm; }
"""

def doc(titulo, codigo, cuerpo, sub=""):
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{e(titulo)}</title><style>{CSS}</style></head><body>
<div class="cab"><div><div class="marca"><i>AP</i><h1>{e(titulo)}</h1></div><div class="sub">{e(sub)}</div></div>
<div class="meta">{e(codigo)} · v{e(D.VERSION)}<br>{e(D.FECHA)}<br><span class="pre">PRELIMINAR</span></div></div>
{cuerpo}
<div class="pie">AP · {e(codigo)} · v{e(D.VERSION)} · Los datos pueden cambiar sin aviso mientras el producto esté en desarrollo.</div>
</body></html>"""

def tabla(filas, cab=None):
    t = "<table>"
    if cab: t += "<tr>" + "".join(f"<th>{e(c)}</th>" for c in cab) + "</tr>"
    for f in filas: t += "<tr>" + "".join(f"<td>{e(str(c))}</td>" for c in f) + "</tr>"
    return t + "</table>"

def svg_cubo():
    return """<svg viewBox="0 0 380 190" width="100%" style="max-width:150mm" font-family="DejaVu Sans" font-size="9">
<g transform="translate(70,0)">
<rect x="0" y="22" width="110" height="110" rx="10" fill="#eef4f1" stroke="#18201c"/><text x="55" y="81" text-anchor="middle" font-weight="700">Vista superior</text>
<rect x="35" y="6" width="40" height="16" rx="4" fill="#fff" stroke="#18201c"/><rect x="35" y="132" width="40" height="16" rx="4" fill="#fff" stroke="#18201c"/>
<text x="80" y="17">oreja M4</text><text x="80" y="143">oreja M4</text>
<circle cx="0" cy="77" r="7" fill="#fff" stroke="#18201c"/><text x="-10" y="80" text-anchor="end">Alimentación</text>
<circle cx="110" cy="77" r="7" fill="#fff" stroke="#18201c"/><text x="120" y="80">Tira LED</text>
<line x1="0" y1="165" x2="110" y2="165" stroke="#5a6862"/><line x1="0" y1="160" x2="0" y2="170" stroke="#5a6862"/><line x1="110" y1="160" x2="110" y2="170" stroke="#5a6862"/>
<text x="55" y="180" text-anchor="middle" fill="#5a6862">80 mm</text></g>
<g transform="translate(225,0)">
<rect x="0" y="32" width="110" height="100" rx="8" fill="#eef4f1" stroke="#18201c"/><rect x="0" y="32" width="110" height="18" rx="6" fill="#dfe6e2" stroke="#18201c"/>
<text x="55" y="45" text-anchor="middle">tapa</text><text x="55" y="90" text-anchor="middle" font-weight="700">Vista lateral</text>
<circle cx="55" cy="112" r="6" fill="#fff" stroke="#18201c"/><text x="55" y="150" text-anchor="middle">ventila (atrás)</text>
<line x1="122" y1="32" x2="122" y2="132" stroke="#5a6862"/><text x="127" y="86" fill="#5a6862">80</text></g></svg>"""

def hoja(P, extra=""):
    c = f"<p>{e(P['resumen'])}</p>"
    c += "<h2>Versiones</h2>" + tabla(P["versiones"], ["Versión", "Uso"])
    izq, der = P["secciones"][: (len(P["secciones"]) + 1) // 2], P["secciones"][(len(P["secciones"]) + 1) // 2:]
    for t, f in P["secciones"]:
        c += f"<h2>{e(t)}</h2>" + tabla(f)
    c += extra
    c += "<h2>Notas</h2><ul>" + "".join(f"<li>{e(n)}</li>" for n in P["notas"]) + "</ul>"
    return c

# ---------------------------------------------------------------- manual de usuario
FALLAS = [["1 destello", "Sin tarjeta de configuración o mal insertada", "Apaga, inserta la tarjeta hasta el fondo y enciende."],
          ["2 destellos", "La tarjeta no coincide con el voltaje medido", "Verifica que la tarjeta sea la de tu tira; si persiste, servicio."],
          ["3 destellos", "Sobrecorriente", "La tira pide más de lo que permite la tarjeta: baja el brillo, acorta la tira o usa una tarjeta mayor."],
          ["4 destellos", "Temperatura alta: se apagó para protegerse", "Revisa ventilación y sol directo; vuelve solo al enfriarse."],
          ["5 destellos", "Voltaje de entrada insuficiente", "Revisa la alimentación y que el cartucho sea el indicado para tu tarjeta."],
          ["6 destellos", "Corto en la salida", "Desconecta la tira y revisa cables y conectores; el cubo reintenta solo."]]

PROBLEMAS = [["No aparece en la app", "Usa Chrome o Edge en Android, Windows o macOS con Bluetooth activo; acércate a menos de 10 m. iPhone y iPad no tienen Bluetooth web: la primera configuración del Wi-Fi se hace desde Android o una computadora; después se usa la página por Wi-Fi o Matter."],
             ["Pide un PIN", "Es el número de 6 dígitos de la etiqueta del cubo."],
             ["La tira enciende con colores cambiados", "Elige el tipo de tira correcto en la app o intercambia los cables de color en la bornera."],
             ["Brilla menos de lo esperado", "Revisa el estado térmico en la app: con calor el cubo baja el brillo para protegerse. Revisa también el voltaje de salida."],
             ["Parpadea en video", "Normal en tiras direccionables con brillo bajo; las analógicas usan 19 kHz y no parpadean."],
             ["No toma el Wi-Fi", "Solo redes de 2.4 GHz; escribe el nombre sin espacios. Acerca el router o reorienta la antena."],
             ["DMX: la luz no responde", "Revisa dirección y universo, la polaridad D+/D− y que solo el último equipo tenga terminación."],
             ["Nodo AP: el LED destella una vez por segundo", "No recibe DMX: revisa el cable, la polaridad y que el maestro esté transmitiendo."]]

def manual(filas_curva):
    E = D.EMPRESA
    c = """<div class="alerta"><b>Seguridad.</b> El cubo con cartucho se conecta a 100–240 V~. La instalación de ese lado debe hacerla personal
calificado, con la alimentación desconectada y con un interruptor o protección en el circuito. No abras el cubo energizado. No lo uses con
el empaque dañado o las tapas flojas si está a la intemperie. Usa cable adecuado a la corriente de tu tira.</div>
<h2>1. Contenido</h2><ul><li>Cubo AP con cartucho de alimentación y tarjeta de configuración instalados (o Nodo AP).</li>
<li>Etiqueta con el nombre del equipo y el PIN de Bluetooth de 6 dígitos. <b>Consérvala.</b></li><li>Este manual y la póliza de garantía.</li></ul>
<h2>2. Conoce tu Cubo AP</h2>""" + svg_cubo() + """
<ul><li><b>Tarjeta de configuración:</b> fija el voltaje y la corriente máximos para tu tira. La app puede bajar el voltaje, nunca subirlo.
Pide la tarjeta que corresponda a tu tira (5, 12, 15 o 24 V).</li>
<li><b>LED de estado</b> (tubo de luz de la tapa): latido corto = en espera · encendido con un parpadeo cada 2 s = luz encendida y conectado ·
fijo = luz encendida sin app · destellos en serie = aviso (tabla de la sección 8).</li></ul>
<h2>3. Instalación</h2><ol>
<li>Fija el cubo con 2 tornillos M4 por las orejas. Deja los prensaestopas hacia abajo o hacia los lados, nunca hacia arriba en exteriores.</li>
<li>Pasa el cable de alimentación por el prensaestopas izquierdo y el de la tira por el derecho. Usa cable redondo de 4–8 mm para que selle.</li>
<li><b>Alimentación:</b> con cartucho, fase y neutro a la bornera del cartucho (y tierra si aplica). Sin cartucho, 12–36 V⎓ a la bornera de entrada
(+ y −), al menos 1.2 V arriba del voltaje de tu tira.</li>
<li><b>Tira analógica</b> (ánodo común): V+ al común de la tira y R, G, B, WW, CW a cada color. <b>Tira direccionable:</b> V+, DAT y GND.</li>
<li><b>DMX por cable</b> (opcional): GND · D− · D+ (pines 1 · 2 · 3 del XLR).</li>
<li>Aprieta los prensaestopas, revisa que el empaque esté en su ranura y cierra la tapa apretando los 4 tornillos en cruz y parejo.</li></ol>
<div class="nota">Calibre mínimo de cable para la tira: hasta 2 A, 0.75 mm² (18 AWG) · hasta 5 A, 1.5 mm² (16 AWG) · tramos de más de 5 m, un calibre mayor.
Una tira de 12 V larga pierde voltaje al final: aliméntala por ambos extremos.</div>
<h2>4. Primer encendido y app</h2><ol>
<li>Energiza: el LED da un latido cada 2 s.</li>
<li>Abre la app AP (sitio web, sección <i>Cubo AP</i>) en Chrome o Edge y pulsa <b>Conectar Bluetooth</b>; elige tu cubo y escribe el PIN de la etiqueta.</li>
<li>Pulsa el círculo de encendido. Elige el <b>tipo de tira</b> en la pestaña <i>Tira y voltaje</i>.</li>
<li>Con <b>Demo</b> puedes probar la app sin cubo.</li></ol>
<h2>5. Funciones</h2>
<table><tr><th>Función</th><th>Cómo</th></tr>
<tr><td>Brillo, color y blanco</td><td>Pestaña <i>Luz</i>. En tiras CCT, temperatura de 2700 a 6500 K.</td></tr>
<tr><td>Efectos</td><td>Fijo, Respira, Arcoíris, Fuego y Cometa.</td></tr>
<tr><td>Escenas</td><td>Guarda hasta 8 combinaciones de color, brillo y efecto, y recupéralas con un toque.</td></tr>
<tr><td>Horario diario</td><td>Hora de encendido y apagado. Con Wi-Fi el cubo toma la hora de internet.</td></tr>
<tr><td>Voltaje de salida</td><td>Bájalo un poco (p. ej. 11.5 V en tiras de 12 V): la tira se calienta menos y dura más.</td></tr>
<tr><td>Wi-Fi</td><td>Pestaña <i>Red y hogar</i>: red de 2.4 GHz y contraseña. Luego hay una página de control en la red local.</td></tr>
<tr><td>Grupos</td><td>Mismo nombre y clave de grupo en varios cubos; con «Aplicar a todo el grupo» se mueven juntos.</td></tr>
<tr><td>Hogar inteligente</td><td>Versión estándar: WLED, Home Assistant y Alexa. Versión Matter: pulsa <b>Código</b> y en Apple Home, Google Home o Alexa elige
«Agregar accesorio» → «Más opciones» y escribe el código (mismo Wi-Fi).</td></tr>
<tr><td>Actualizaciones</td><td>Por Wi-Fi desde la app (versión estándar) o por USB con el instalador del sitio. Durante la actualización la salida se apaga.</td></tr></table>
<h2>6. DMX e iluminación profesional</h2><ul>
<li><b>Recibir:</b> pestaña <i>DMX</i>: Art-Net o sACN (universo y dirección) por Wi-Fi, o DMX512 por cable (dirección).</li>
<li><b>Transmitir a Nodos AP</b> (cubos con salida DMX): <i>Espejo</i> hace que todos los nodos copien el color del cubo; <i>Puente</i> reenvía al cable lo que llega por Art-Net/sACN.</li>
<li>Línea DMX: cable de par trenzado, de equipo a equipo (sin derivaciones en estrella), terminación de 120 Ω solo en el último.</li></ul>
<h2>7. Nodo AP</h2><ol>
<li>Conecta 12–24 V a la bornera de entrada, la tira RGBW (V+ R G B W) a la de salida y la línea DMX a la bornera DMX de entrada; la de salida sigue al siguiente nodo.</li>
<li><b>Asignar dirección:</b> pulsa APRENDER (el LED destella rápido). En la consola, sube <b>un solo</b> canal a más del 80 % y deja los demás abajo del 15 %.
El nodo toma ese canal como su dirección y usa ese y los 3 siguientes (R, G, B, W). Con un Cubo AP en modo Espejo usa las direcciones 1, 5, 9, 13…</li>
<li>LED: fijo = recibe · un destello por segundo = sin señal (mantiene la última luz) · rápido = aprendiendo.</li>
<li>Puente TERM: ponlo solo en el último nodo de la línea.</li></ol>
<h2>8. Avisos del LED (Cubo AP)</h2>""" + tabla(FALLAS, ["LED", "Significa", "Qué hacer"]) + """
<p>Desde la app, <b>Reiniciar</b> borra el aviso. Por sobrecorriente o corto el cubo reintenta solo 3 veces, cada 5 s.</p>
<h2>9. Calor y carga máxima</h2><p>El cubo saca su calor por las paredes. Con más temperatura ambiente, menos carga continua:</p>
<img class="fig" src="curva_carga.png"><ul>
<li>Cuerpo ASA (plástico): hasta ≈ 15 W continuos a 30 °C. Para más, cuerpo de aluminio.</li>
<li>Cuerpo de aluminio: 100 % hasta 35 °C; menos arriba de eso, según la curva.</li>
<li>Si se excede, el cubo baja el brillo solo y lo recupera al enfriarse: no es falla.</li>
<li>No lo encierres en cajas sin ventilación ni lo cubras. Al sol, prefiere el acabado claro.</li></ul>
<h2>10. Solución de problemas</h2>""" + tabla(PROBLEMAS, ["Síntoma", "Qué revisar"]) + f"""
<h2>11. Mantenimiento</h2><ul><li>Limpia con paño húmedo; sin solventes ni hidrolavadora a presión directa.</li>
<li>Cada año en exteriores: revisa que los prensaestopas y la tapa sigan apretados y el empaque sin grietas.</li>
<li>Por dentro no hay piezas que el usuario deba reparar. Abrirlo o modificarlo anula la garantía.</li></ul>
<h2>12. Fin de vida</h2><p>No lo tires a la basura: llévalo a un centro de acopio de residuos electrónicos.</p>
<h2>13. Soporte</h2><p>{e(E['razon'])} · {e(E['telefono'])} · {e(E['correo'])} · {e(E['web'])}</p>"""
    return c

# ---------------------------------------------------------------- póliza de garantía
def garantia():
    E = D.EMPRESA
    return f"""<div class="nota">Borrador para revisión legal. Antes de entregarla al público hay que llenar los datos del responsable y verificarla
contra la Ley Federal de Protección al Consumidor (LFPC, arts. 77–79) y la NOM-024-SCFI-2013.</div>
<h2>Producto</h2><table><tr><td>Producto</td><td>☐ Cubo AP &nbsp;&nbsp; ☐ Nodo AP</td></tr>
<tr><td>Modelo / versión</td><td><span class="campo"></span></td></tr><tr><td>Número de serie</td><td><span class="campo"></span></td></tr>
<tr><td>Fecha de compra o entrega</td><td><span class="campo"></span></td></tr><tr><td>Distribuidor</td><td><span class="campo"></span></td></tr></table>
<h2>Cobertura</h2><p><b>{e(E['razon'])}</b> garantiza este producto por <b>12 (doce) meses</b> a partir de la fecha de compra o entrega, contra
cualquier defecto de fabricación y de funcionamiento, en todas sus piezas, componentes y mano de obra, incluido el cartucho de alimentación y la
tarjeta de configuración entregados con el producto.</p>
<h2>Cómo hacerla efectiva</h2><ol>
<li>Presenta el producto y esta póliza sellada, o el comprobante de compra (factura o ticket), en el domicilio de abajo o con el distribuidor.</li>
<li>El producto se repara o, si no es posible, se cambia por uno igual o equivalente. Si tampoco es posible, se devuelve lo pagado.</li>
<li>El tiempo de reparación no será mayor de <b>30 días naturales</b> desde que se recibe el producto. Ese tiempo no cuenta dentro del plazo de garantía.</li>
<li>Los gastos de transportación del producto que deriven del cumplimiento de esta garantía corren a cargo de {e(E['razon'])} dentro de su red de servicio.</li>
<li>Las refacciones y partes pueden adquirirse en el mismo domicilio.</li></ol>
<h2>Esta garantía no es válida cuando</h2><ol>
<li>El producto se usó en condiciones distintas a las normales (por ejemplo, alimentación fuera del rango indicado en la hoja de datos, o carga mayor a la de la tarjeta).</li>
<li>El producto no se operó de acuerdo con el manual de uso que lo acompaña.</li>
<li>El producto fue alterado o reparado por personas no autorizadas por {e(E['razon'])}.</li></ol>
<h2>Responsable</h2><table><tr><td>Razón social</td><td>{e(E['razon'])}</td></tr><tr><td>Domicilio</td><td>{e(E['domicilio'])}</td></tr>
<tr><td>RFC</td><td>{e(E['rfc'])}</td></tr><tr><td>Teléfono</td><td>{e(E['telefono'])}</td></tr><tr><td>Correo</td><td>{e(E['correo'])}</td></tr></table>
<div class="firma"><div>Sello y firma del distribuidor</div><div>Fecha</div></div>
<div class="nota" style="margin-top:14px">En caso de extravío de esta póliza, el consumidor puede hacerla efectiva con su comprobante de compra.</div>"""

# ---------------------------------------------------------------- todo
def main():
    filas, wmax = curva()
    ex = ("<h2>Perfiles de tarjeta</h2>" + tabla(D.CUBO["perfiles"], ["Tarjeta", "Voltaje máx.", "Corriente máx.", "Potencia", "Uso"]) +
          "<h2>Curva de carga contra temperatura ambiente</h2><img class='fig' src='curva_carga.png'>"
          "<p style='font-size:9pt'>Carga continua máxima sin que actúe el recorte térmico, en aire quieto y sin sol. "
          "Arriba de la curva el cubo baja el brillo solo para protegerse.</p><h2>Dimensiones y conexiones</h2>" + svg_cubo())
    paginas = {
        "hd_cubo_ap": doc("Cubo AP · Hoja de datos", D.CUBO["codigo"], hoja(D.CUBO, ex), D.CUBO["subtitulo"]),
        "hd_nodo_ap": doc("Nodo AP · Hoja de datos", D.NODO["codigo"], hoja(D.NODO), D.NODO["subtitulo"]),
        "manual_usuario_ap": doc("Manual de usuario", "MU-AP", manual(filas), "Cubo AP y Nodo AP: instalación, uso y cuidados"),
        "garantia_ap": doc("Póliza de garantía", "PG-AP", garantia(), "Cubo AP y Nodo AP"),
    }
    for n, h in paginas.items(): open(os.path.join(AQUI, n + ".html"), "w").write(h)
    fichas = {"fecha": D.FECHA, "version": D.VERSION, "cubo": D.CUBO, "nodo": D.NODO,
              "curva": {"temperaturas": D.CURVA_CUBO["temperaturas"], "aluminio": {k: filas[v] for k, v in D.CURVA_CUBO["aluminio"].items()},
                        "plastico_w": [round(x, 1) for x in wmax]},
              "fallas": FALLAS, "problemas": PROBLEMAS,
              "documentos": [["hd_cubo_ap.pdf", "Hoja de datos · Cubo AP"], ["hd_nodo_ap.pdf", "Hoja de datos · Nodo AP"],
                             ["manual_usuario_ap.pdf", "Manual de usuario"], ["garantia_ap.pdf", "Póliza de garantía (borrador)"]]}
    json.dump(fichas, open(os.path.join(SITIO, "src", "datos", "fichas.json"), "w"), ensure_ascii=False, indent=1)
    print("listo:", ", ".join(paginas))

if __name__ == "__main__":
    main()
