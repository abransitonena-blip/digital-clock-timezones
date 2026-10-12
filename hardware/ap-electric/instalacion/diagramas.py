"""Diagramas de instalación de AP Home y del 7R Tour (SVG + PNG). python3 diagramas.py SALIDA_DIR"""
import os, sys
import cairosvg

F = "font-family:DejaVu Sans,sans-serif"
L, N, PE, CTRL, GRIS = "#C0281F", "#1f5fbf", "#2e9e44", "#E07000", "#555"


class D:
    def __init__(s, w, h, titulo):
        s.w, s.h, s.e = w, h, []
        s.e.append('<rect width="100%%" height="100%%" fill="#fff"/><text x="20" y="34" style="%s;font-size:22px;font-weight:bold">%s</text>' % (F, titulo))
    def caja(s, x, y, w, h, txt, sub="", color="#1D1F24", fondo="#f4f4f6"):
        s.e.append('<rect x="%d" y="%d" width="%d" height="%d" rx="8" fill="%s" stroke="%s" stroke-width="2"/>' % (x, y, w, h, fondo, color))
        s.e.append('<text x="%d" y="%d" text-anchor="middle" style="%s;font-size:15px;font-weight:bold" fill="%s">%s</text>' % (x + w / 2, y + 22, F, color, txt))
        if sub:
            for i, t in enumerate(sub.split("|")):
                s.e.append('<text x="%d" y="%d" text-anchor="middle" style="%s;font-size:12px" fill="%s">%s</text>' % (x + w / 2, y + 40 + 15 * i, F, GRIS, t))
    def borne(s, x, y, txt, lado="arriba"):
        s.e.append('<circle cx="%d" cy="%d" r="6" fill="#fff" stroke="#000" stroke-width="2"/>' % (x, y))
        dy = -12 if lado == "arriba" else 22
        s.e.append('<text x="%d" y="%d" text-anchor="middle" style="%s;font-size:12px;font-weight:bold">%s</text>' % (x, y + dy, F, txt))
    def cable(s, pts, color, ancho=3, guion=False):
        d = "M" + " L".join("%d %d" % p for p in pts)
        s.e.append('<path d="%s" fill="none" stroke="%s" stroke-width="%d" %s stroke-linejoin="round"/>' % (d, color, ancho, 'stroke-dasharray="8 5"' if guion else ""))
    def texto(s, x, y, t, tam=13, color="#000", neg=False):
        s.e.append('<text x="%d" y="%d" style="%s;font-size:%dpx;%s" fill="%s">%s</text>' % (x, y, F, tam, "font-weight:bold" if neg else "", color, t))
    def lampara(s, x, y, txt="Lámpara"):
        s.e.append('<circle cx="%d" cy="%d" r="20" fill="#fff8d6" stroke="#000" stroke-width="2"/><path d="M%d %d l28 28 M%d %d l-28 28" stroke="#000" stroke-width="2"/>' % (x, y, x - 14, y - 14, x + 14, y - 14))
        s.texto(x - 30, y + 40, txt, 12)
    def apagador(s, x, y, txt):
        s.e.append('<circle cx="%d" cy="%d" r="4"/><circle cx="%d" cy="%d" r="4"/><path d="M%d %d L%d %d" stroke="#000" stroke-width="3"/>' % (x, y, x + 40, y, x, y, x + 36, y - 16))
        s.texto(x - 6, y + 22, txt, 12)
    def leyenda(s, x, y):
        for i, (c, t) in enumerate(((L, "Fase (L)"), (N, "Neutro (N)"), (PE, "Tierra (PE)"), (CTRL, "Mando / baja tensión"))):
            s.cable([(x, y + 22 * i), (x + 40, y + 22 * i)], c); s.texto(x + 50, y + 5 + 22 * i, t, 12)
    def svg(s):
        return '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">%s</svg>' % (s.w, s.h, s.w, s.h, "".join(s.e))


def plug():
    d = D(900, 420, "Home Plug: enchufar y usar (sin tocar conductores)")
    d.caja(60, 120, 180, 160, "Contacto de pared", "127 V~ con tierra|(NEMA 5-15R)")
    d.caja(360, 110, 200, 180, "AP Home Plug", "clavija atrás|receptáculo al frente|botón y LED", "#E07000", "#fff4ea")
    d.caja(680, 120, 160, 160, "Lámpara", "con su clavija|y su apagador|(debe quedar en ON)")
    d.cable([(240, 200), (360, 200)], "#000", 6); d.texto(262, 192, "se enchufa", 12)
    d.cable([(560, 200), (680, 200)], "#000", 6); d.texto(585, 192, "se enchufa", 12)
    d.texto(60, 330, "Si el apagador propio de la lámpara está abierto, el Home Plug no puede encenderla.", 14, L, True)
    d.texto(60, 356, "Solo lámparas de encendido/apagado no regulables. Carga máxima: ver etiqueta (por determinar).", 13)
    d.texto(60, 380, "Funciona sin internet: el botón enciende y apaga; la app y la red son opcionales.", 13)
    return d


def switch_simple():
    d = D(980, 520, "Home Switch con apagador sencillo (instalación fija, circuito desenergizado)")
    d.caja(40, 70, 170, 120, "Tablero", "interruptor|termomagnético|del circuito")
    d.caja(420, 250, 240, 150, "AP Home Switch", "L   N   SW   LS", "#E07000", "#fff4ea")
    for x, t in ((450, "L"), (500, "N"), (590, "SW"), (640, "LS")):
        d.borne(x, 250, t)
    d.cable([(210, 110), (330, 110), (330, 210), (450, 210), (450, 244)], L)
    d.cable([(210, 150), (300, 150), (300, 470), (790, 470), (790, 330)], N)
    d.cable([(500, 244), (500, 230), (300, 230)], N)
    d.apagador(250, 330, "Apagador de pared")
    d.cable([(330, 110), (330, 140), (250, 140), (250, 330)], L)
    d.cable([(290, 330), (360, 330), (360, 200), (590, 200), (590, 244)], L)
    d.texto(372, 192, "fase del apagador → SW (entrada de red)", 12, L)
    d.cable([(640, 244), (640, 180), (790, 180), (790, 270)], L)
    d.lampara(790, 300)
    d.leyenda(40, 420)
    d.texto(330, 510, "Modo de la entrada: INTERRUPTOR (la luz sigue a la palanca). SW nunca se usa como contacto seco.", 13, "#000", True)
    return d


def switch_escalera():
    d = D(1120, 560, "Home Switch con apagadores de escalera (3 vías)")
    d.caja(40, 70, 170, 120, "Tablero", "interruptor|termomagnético")
    d.caja(560, 280, 240, 150, "AP Home Switch", "L   N   SW   LS", "#E07000", "#fff4ea")
    for x, t in ((590, "L"), (640, "N"), (730, "SW"), (780, "LS")):
        d.borne(x, 280, t)
    d.cable([(210, 110), (470, 110), (470, 240), (590, 240), (590, 274)], L)
    d.cable([(210, 150), (250, 150), (250, 520), (940, 520), (940, 370)], N)
    d.cable([(640, 274), (640, 260), (250, 260)], N)
    # apagadores de 3 vías: común del 1 desde L, viajeros, común del 2 a SW
    d.cable([(470, 110), (300, 110), (300, 330)], L)
    # apagador 1: común a la izquierda; apagador 2: común a la derecha (espejo)
    d.e.append('<circle cx="300" cy="330" r="5"/><circle cx="340" cy="310" r="5"/><circle cx="340" cy="350" r="5"/><path d="M300 330 L338 312" stroke="#000" stroke-width="3"/>')
    d.e.append('<circle cx="470" cy="330" r="5"/><circle cx="430" cy="310" r="5"/><circle cx="430" cy="350" r="5"/><path d="M470 330 L432 312" stroke="#000" stroke-width="3"/>')
    d.texto(270, 380, "Apagador 1 (3 vías)", 12); d.texto(410, 380, "Apagador 2 (3 vías)", 12)
    d.e.append('<path d="M%d 310 L%d 310 M%d 350 L%d 350" stroke="%s" stroke-width="3"/>' % (340, 430, 340, 430, L))
    d.texto(352, 302, "viajeros", 11, L)
    d.cable([(470, 330), (520, 330), (520, 220), (730, 220), (730, 274)], L)
    d.texto(540, 212, "salida común del apagador 2 → SW", 12, L)
    d.cable([(780, 274), (780, 200), (940, 200), (940, 310)], L)
    d.lampara(940, 340)
    d.leyenda(40, 430)
    d.texto(300, 470, "Modo de la entrada: CONMUTADOR. Cada cambio de cualquiera de los dos apagadores alterna la luz.", 13, "#000", True)
    d.texto(300, 492, "Los viajeros siguen entre los apagadores; no van al equipo ni a ningún pin del microcontrolador.", 13)
    d.texto(300, 514, "Antes, la salida común del apagador 2 iba a la lámpara; ahora va a SW y la lámpara a LS.", 13)
    return d


def r7():
    d = D(1200, 690, "7R Tour 24DC: conexión típica (tablero)")
    d.caja(40, 70, 180, 90, "Tablero", "circuito de las cargas|127 / 220 V~")
    d.cable([(130, 70), (130, 50), (1150, 50)], N); d.texto(1120, 44, "N", 12, N, True)
    d.caja(410, 270, 440, 160, "AP Electric Industrial 7R Tour", "arriba: C / NA de cada canal (7)|abajo: +24 V 0 V · I1-I8 COM · A B 0V aislado", "#E07000", "#fff4ea")
    # salidas
    d.cable([(220, 115), (250, 115), (250, 100), (290, 100)], L); d.caja(290, 80, 110, 40, "Int. canal 1", "")
    d.cable([(250, 115), (250, 170), (290, 170)], L); d.caja(290, 150, 110, 40, "Int. canal 2", "")
    d.cable([(400, 100), (450, 100), (450, 264)], L); d.borne(450, 270, "C1")
    d.cable([(400, 170), (540, 170), (540, 264)], L); d.borne(540, 270, "C2")
    d.borne(480, 270, "NA1"); d.cable([(480, 264), (480, 215), (660, 215)], L)
    d.lampara(690, 215, ""); d.texto(650, 262, "Alumbrado (límite: PD)", 12)
    d.cable([(710, 215), (800, 215), (800, 50)], N)
    d.borne(570, 270, "NA2"); d.cable([(570, 264), (570, 245), (930, 245), (930, 180)], L)
    d.caja(880, 90, 230, 90, "Contactor externo", "bobina A1-A2 (CA)|contactos AC-3 / AC-1")
    d.cable([(1060, 90), (1060, 50)], N)
    d.texto(880, 205, "motor, bomba, calefacción: siempre por contactor", 12)
    # 24 V, entrada y RS-485
    d.caja(40, 480, 190, 90, "Fuente 24 V CC", "certificada, SELV")
    d.cable([(230, 505), (450, 505), (450, 436)], CTRL); d.borne(450, 430, "+24", "abajo"); d.texto(240, 498, "+24 V", 12, CTRL)
    d.cable([(230, 545), (480, 545), (480, 436)], "#000"); d.borne(480, 430, "0V", "abajo"); d.texto(240, 560, "0 V", 12)
    d.cable([(300, 505), (300, 620), (320, 620)], CTRL); d.apagador(320, 620, "sensor o botón 24 V")
    d.cable([(360, 620), (540, 620), (540, 436)], CTRL); d.borne(540, 430, "I1", "abajo")
    d.cable([(400, 545), (400, 650), (680, 650), (680, 436)], "#000"); d.borne(680, 430, "COM", "abajo")
    for x, t in ((740, "A"), (770, "B"), (800, "0Va")):
        d.borne(x, 430, t, "abajo")
    d.cable([(740, 436), (740, 640)], "#7a3fbf", 2); d.cable([(770, 436), (770, 640)], "#7a3fbf", 2)
    d.texto(785, 640, "par trenzado al maestro Modbus / PLC", 12, "#7a3fbf")
    d.leyenda(900, 300)
    d.texto(870, 480, "Cada canal tiene su propio común.", 13, "#000", True)
    d.texto(870, 502, "Protección externa obligatoria", 13, "#000", True)
    d.texto(870, 524, "por circuito de carga.", 13, "#000", True)
    d.texto(870, 552, "Terminación de 120 Ω solo en los", 12)
    d.texto(870, 570, "extremos de la línea RS-485.", 12)
    return d


if __name__ == "__main__":
    sal = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(sal, exist_ok=True)
    for n, f in (("home_plug", plug), ("home_switch_sencillo", switch_simple), ("home_switch_escalera", switch_escalera), ("7r_tour_24dc", r7)):
        p = os.path.join(sal, "instalacion_%s.svg" % n)
        open(p, "w").write(f().svg())
        cairosvg.svg2png(url=p, write_to=p.replace(".svg", ".png"))
    print("diagramas listos")
