"""Análisis térmico del Cubo AP (placa v3 + cartucho) y del Nodo AP.

Modelo físico (estado estable):
  1. Pérdidas de cada pieza según el perfil (Vout, Imax) y el voltaje del cartucho, dependientes de la temperatura
     (Rds(on) sube 0.4 %/K, la fuga del Schottky sube ×10 cada 37.5 K, el Vf baja 1.5 mV/K) → se itera hasta converger.
  2. Placa como lámina 2D (celdas de 0.5 mm): conducción en el plano por el cobre (2 capas de 35 µm, 70 % de llenado)
     y el FR4; cada celda pierde calor por convección al aire interior y por radiación a las paredes.
     Opcional: almohadilla térmica (gap pad) bajo la zona de potencia hacia una costilla del cuerpo de aluminio.
  3. Caja: nodos aire interior y pared; pared → ambiente por convección natural + radiación (+ sol si se pide).
     El cartucho AC-DC mete su pérdida al aire (plástico) o directo a la pared (aluminio, atornillado con pasta).
  4. Temperatura de unión: T_placa local + P·ψ (ψJB de la hoja de datos de cada encapsulado).
  5. Vida de capacitores: electrolítico L = L0·2^((Tr−T)/10); híbrido de polímero igual pero desde 125 °C;
     polímero sólido L = L0·10^((Tr−T)/20).
Todo es estimación de primer orden (±15 K): se valida con termopar y cámara térmica en el prototipo.
Uso: python3.11 termico.py  → informe_termico.md + figuras PNG en esta carpeta."""
import os, math, importlib.util
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SIGMA = 5.67e-8

def cargar(ruta):
    spec = importlib.util.spec_from_file_location("d", ruta); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return {p["ref"]: p for p in m.P}, m.W, m.H

# ---------------------------------------------------------------- cajas
CAJAS = {
    # area_ext: caras expuestas (m²) · area_int: interior · k_pared, e_pared (m) · aletas: multiplicador de área efectiva
    "plastico": dict(nombre="Cubo ASA (plástico) sellado", area_ext=5 * 0.080**2, area_int=5 * 0.072**2, k=0.17, e=0.004,
                     aletas=1.0, eps=0.9, pad=False, cart_a_pared=0.05),
    "aluminio": dict(nombre="Cubo de aluminio con aletas + costilla y gap pad bajo la potencia", area_ext=5 * 0.080**2,
                     area_int=5 * 0.072**2, k=150.0, e=0.003, aletas=1.55, eps=0.85, pad=True, cart_a_pared=1.2),   # 16 aletas 12 mm (cubo.py): área ×1.67, eficiencia ≈ 0.93
    "nodo_al": dict(nombre="Nodo en perfil de aluminio 70×50×25 mm con gap pad bajo los MOSFET",
                    area_ext=2 * (0.070 * 0.050 + 0.070 * 0.025 + 0.050 * 0.025), area_int=2 * (0.066 * 0.046 + 0.066 * 0.021 + 0.046 * 0.021),
                    k=150.0, e=0.002, aletas=1.0, eps=0.8, pad=True, cart_a_pared=0.0),
    "nodo": dict(nombre="Caja del Nodo AP (ABS/ASA 58×46×23 mm)", area_ext=2 * (0.058 * 0.046 + 0.058 * 0.023 + 0.046 * 0.023),
                 area_int=2 * (0.052 * 0.040 + 0.052 * 0.019 + 0.040 * 0.019), k=0.17, e=0.003, aletas=1.0, eps=0.9, pad=False,
                 cart_a_pared=0.0),
}
H_PAD = 900.0          # W/m²K, vías térmicas (30 % del área) + FR4 + gap pad 3 W/mK de 1 mm comprimido
K_SHEET = 385 * 35e-6 * 2 * 0.70 + 0.3 * 1.6e-3      # W/K por cuadro: cobre de 2 capas + FR4

def h_nat(dt, l=0.07):
    """Convección natural laminar en placa vertical: h = 1.42·(ΔT/L)^0.25 (W/m²K)."""
    return max(2.0, 1.42 * (max(abs(dt), 0.5) / l) ** 0.25)

def h_rad(t1, t2, eps):
    a, b = t1 + 273.15, t2 + 273.15
    return eps * SIGMA * (a * a + b * b) * (a + b)

# ---------------------------------------------------------------- pérdidas
def perdidas_cubo(vout, iout, vin, T):
    """T: dict de temperaturas de unión/pieza (°C) de la iteración anterior. Devuelve {ref: W} y datos."""
    d = vout / vin
    fsw = 400e3
    rds_u1 = 0.092 * (1 + 0.004 * (T["U1"] - 25))
    p_u1 = iout**2 * rds_u1 * d + vin**2 * fsw * iout * 0.25e-9 + vin * 3e-9 * fsw + vin * 146e-6   # cond + conm + Qg + Iq
    vf = max(0.30, 0.42 + 0.03 * iout - 0.0015 * (T["D2"] - 25))
    ir = 0.5e-3 * (vin / 60) * 10 ** ((T["D2"] - 25) / 37.5)                                          # fuga B560C
    p_d2 = vf * iout * (1 - d) + vin * ir * d + 0.5 * 300e-12 * vin**2 * fsw
    ripple = (vin - vout) * d / (10e-6 * fsw)
    irms_l = math.sqrt(iout**2 + ripple**2 / 12)
    p_l1 = irms_l**2 * 0.015 * (1 + 0.0039 * (T["L1"] - 25)) + 0.04 * (ripple / 1.0) ** 2.1 * (fsw / 400e3) ** 1.4
    p_rs = iout**2 * 0.005
    p_q = iout**2 * 0.012 * (1 + 0.004 * (T["Q2"] - 25))          # peor caso: toda la corriente por un canal
    p_j2 = iout**2 * 0.0025 * 2                                      # 2 contactos de bornera (ida y vuelta)
    # 5 V lógica: ESP32 0.33 W (Wi-Fi promedio), drivers, buffer, INA226 → 0.75 W; LMR14006 ≈ 80 %
    p5 = 0.75
    p_u2 = p5 * (1 / 0.80 - 1) * 0.75; p_d4 = p5 * (1 / 0.80 - 1) * 0.25
    p_u11 = (5.0 - 3.3) * 0.10
    p_u3 = 0.33
    pin = vout * iout + p_u1 + p_d2 + p_l1 + p_rs + p_q + p_j2 + p5 / 0.80
    iin = pin / vin
    p_q1 = iin**2 * 0.025 * (1 + 0.004 * (T["Q1"] - 25))
    p_f1 = iin**2 * 0.012
    p_j1 = iin**2 * 0.0025 * 2
    P = {"U1": p_u1, "D2": p_d2, "L1": p_l1, "RS": p_rs, "Q2": p_q, "J2": p_j2, "U2": p_u2, "D4": p_d4, "U11": p_u11,
         "U3": p_u3, "Q1": p_q1, "F1": p_f1, "J1": p_j1}
    return P, dict(d=d, ripple=ripple, iin=iin, pin=pin + p_q1 + p_f1 + p_j1)

def perdidas_nodo(vin, i_canal, n_canales, T, r_serie=150.0, rds=0.010, r_fus=0.008):
    """Nodo rev. B: MOSFET DFN de 10 mΩ, fusible de 8 A, 150 Ω en serie con el 78L05. Rev. A: rds=0.026 (AO3400A), r_fus=0.015, r_serie=0."""
    i_log = 0.020
    p_q = i_canal**2 * rds * 1.2 * (1 + 0.004 * (T["Q1"] - 25))
    it = i_canal * n_canales + i_log
    v_u3 = vin - 0.4 - i_log * r_serie
    P = {"U3": (v_u3 - 5.0) * i_log, "F1": it**2 * r_fus, "J1": it**2 * 0.005, "J2": it**2 * 0.005, "D1": 0.4 * i_log,
         "U1": 5.0 * 0.006, "U2": 5.0 * 0.001}
    for k in range(n_canales): P[f"Q{k+1}"] = p_q
    if r_serie: P["R30"] = i_log**2 * r_serie
    return P, dict(it=it, v_u3=v_u3)

# tamaño de la fuente de calor (mm) y ψ unión→placa (K/W)
HUELLA = {"U1": (5.0, 4.0, 24.3), "D2": (7.0, 6.0, 15.0), "L1": (12.5, 12.5, 42.0), "RS": (6.3, 3.2, 20.0), "Q2": (3.3, 3.3, 3.0),
          "J2": (6.0, 40.0, 0.0), "U2": (3.0, 3.0, 50.0), "D4": (5.0, 2.6, 25.0), "U11": (3.0, 3.0, 60.0), "U3": (5.0, 5.0, 9.0),
          "Q1": (5.0, 4.0, 15.0), "F1": (6.0, 2.5, 0.0), "J1": (6.0, 10.0, 0.0),
          "U3n": (4.5, 2.5, 45.0), "Qn": (3.3, 3.3, 5.0), "QnA": (2.9, 2.4, 70.0), "D1": (4.3, 2.6, 30.0), "U1n": (6.5, 4.4, 40.0), "U2n": (5.0, 4.0, 40.0),
          "R30": (3.2, 1.6, 0.0)}

# ---------------------------------------------------------------- mapa térmico de la placa
class Placa:
    def __init__(self, W, H, caja, zona_pad=None, dx=0.5e-3):
        self.W, self.H, self.dx, self.caja = W, H, dx, caja
        self.nx, self.ny = int(round(W * 1e-3 / dx)), int(round(H * 1e-3 / dx))
        self.zona_pad = zona_pad
        x = (np.arange(self.nx) + 0.5) * dx * 1e3 - W / 2
        y = (np.arange(self.ny) + 0.5) * dx * 1e3 - H / 2
        self.X, self.Y = np.meshgrid(x, y)

    def resolver(self, fuentes, p_cart, t_amb, sol=0.0, t_guess=60.0):
        """fuentes: lista (x, y, w, h, P) en mm/W. Devuelve campo T (ny, nx), T_aire, T_pared."""
        c, n = self.caja, self.nx * self.ny
        A = self.dx**2
        q = np.zeros(self.ny * self.nx)
        for (x0, y0, w, h, p) in fuentes:
            m = (np.abs(self.X - x0) <= w / 2) & (np.abs(self.Y - y0) <= h / 2)
            if not m.any():
                m = np.zeros_like(m); m[np.unravel_index(np.argmin((self.X - x0)**2 + (self.Y - y0)**2), m.shape)] = True
            q[m.ravel()] += p / m.sum()
        pad = np.zeros(n, bool)
        if c["pad"] and self.zona_pad is not None:
            x1, y1, x2, y2 = self.zona_pad
            pad = ((self.X >= x1) & (self.X <= x2) & (self.Y >= y1) & (self.Y <= y2)).ravel()
        if not hasattr(self, "lap"):
            idx = np.arange(n).reshape(self.ny, self.nx)
            r, cc = [], []
            for a, b in ((idx[:, :-1], idx[:, 1:]), (idx[:-1, :], idx[1:, :])):
                r.append(a.ravel()); cc.append(b.ravel())
            a, b = np.concatenate(r), np.concatenate(cc)
            Lp = sp.coo_matrix((np.full(len(a), -K_SHEET), (a, b)), shape=(n, n))
            Lp = Lp + Lp.T
            self.lap = (Lp - sp.diags(np.asarray(Lp.sum(axis=1)).ravel())).tocsr()
        gp = np.where(pad, H_PAD * A, 0.0)
        frac = min(1, c["cart_a_pared"] / (c["cart_a_pared"] + 0.1))
        t_air, t_wall, T = t_guess, t_guess - 5, None
        for _ in range(4):                                   # radiación y convección no lineales: se itera
            t_board = t_guess if T is None else float(T.mean())
            g_conv = 2 * 0.8 * h_nat(t_board - t_air, 0.06) * A     # placa horizontal: ~80 % de una vertical
            g_w = 2 * h_rad(t_board, t_wall, 0.9) * A + gp     # radiación de las dos caras + gap pad
            g_aw = h_nat(t_air - t_wall) * c["area_int"]
            hr_ext = h_rad(t_wall, t_amb, c["eps"])
            # aletas: multiplican el área de convección; la radiación sale por la envolvente (las aletas se ven entre sí)
            g_wall = 1 / (c["e"] / (c["k"] * c["area_int"]) + 1 / ((h_nat(t_wall - t_amb, 0.08) * c["aletas"] + hr_ext) * c["area_ext"]))
            K = self.lap + sp.diags(g_conv + g_w)
            ca = sp.csr_matrix(np.full((n, 1), -g_conv)); cw = sp.csr_matrix(-g_w.reshape(n, 1))
            filas_a = sp.csr_matrix(np.concatenate([np.full(n, -g_conv), [n * g_conv + g_aw, -g_aw]]).reshape(1, -1))
            filas_w = sp.csr_matrix(np.concatenate([-g_w, [-g_aw, g_w.sum() + g_aw + g_wall]]).reshape(1, -1))
            M = sp.vstack([sp.hstack([K, ca, cw]), filas_a, filas_w]).tocsc()
            b = np.concatenate([q, [p_cart * (1 - frac), p_cart * frac + sol + g_wall * t_amb]])
            v = spl.spsolve(M, b)
            T, t_air, t_wall = v[:n].reshape(self.ny, self.nx), v[n], v[n + 1]
        return T, t_air, t_wall

    def en(self, T, x, y, w=1.0, h=1.0):
        m = (np.abs(self.X - x) <= max(w, 1) / 2) & (np.abs(self.Y - y) <= max(h, 1) / 2)
        return float(T[m].max()) if m.any() else float("nan")

# ---------------------------------------------------------------- cubo
PZ, W3, H3 = cargar(os.path.join(RAIZ, "placa-control-v3", "diseno.py"))
ZONA_PAD = (-14.0, 13.0, 27.0, 31.0)          # bajo U1, D2, L1, RS, Q1 (cara inferior de la placa)
CAPS = {"C1": "electrolitico", "C12": "polimero", "C2": "mlcc", "C10": "mlcc", "C18": "mlcc", "C31": "mlcc"}

PERFILES = [("5V 3A", 4.98, 3.0, 24.0), ("12V 1A", 12.0, 1.0, 24.0), ("12V 2A", 12.0, 2.0, 24.0), ("12V 5A", 12.0, 5.0, 24.0),
            ("15V 3A", 15.05, 3.0, 24.0), ("24V 2A", 24.3, 2.0, 36.0), ("24V 3A", 24.3, 3.0, 36.0)]

def cartucho(p_salida):
    """Pérdida del módulo AC-DC (tipo IRM/LRS): eficiencia 86–90 % según carga."""
    eta = 0.82 + 0.07 * min(1.0, p_salida / 40) if p_salida > 3 else 0.70
    return p_salida * (1 / eta - 1)

def simular_cubo(perfil, caja, t_amb, carga=1.0, sol=0.0, placa=None):
    nombre, vout, imax, vin = perfil
    iout = imax * carga
    placa = placa or Placa(W3, H3, CAJAS[caja], ZONA_PAD)
    T = {k: t_amb + 30 for k in ("U1", "D2", "L1", "Q1", "Q2")}
    res = None
    for it in range(30):
        P, info = perdidas_cubo(vout, iout, vin, T)
        fuentes = []
        for ref, p in P.items():
            c = PZ[ref]; w, h, _ = HUELLA[ref]
            if c["rot"] % 180: w, h = h, w
            fuentes.append((c["x"], c["y"], w, h, p))
        p_cart = cartucho(info["pin"])
        Tf, ta, tw = placa.resolver(fuentes, p_cart, t_amb, sol)
        nuevo = {}
        for ref in T:
            c = PZ[ref]; w, h, psi = HUELLA[ref]
            nuevo[ref] = placa.en(Tf, c["x"], c["y"], w, h) + P[ref] * psi
        if max(abs(nuevo[k] - T[k]) for k in T) < 0.05: T = nuevo; break
        if max(nuevo.values()) > 250: T = nuevo; break           # fuga térmica
        T = nuevo
    res = dict(P=P, info=info, p_cart=p_cart, T=Tf, t_air=ta, t_wall=tw, Tj=T, placa=placa)
    res["Tj"].update({ref: placa.en(Tf, PZ[ref]["x"], PZ[ref]["y"], *HUELLA[ref][:2]) + P[ref] * HUELLA[ref][2]
                      for ref in ("U2", "U11", "U3", "RS")})
    res["caps"] = {ref: placa.en(Tf, PZ[ref]["x"], PZ[ref]["y"], 3, 3) for ref in CAPS}
    return res

def vida(tipo, t):
    if tipo == "electrolitico": return 2000 * 2 ** ((105 - t) / 10)       # 105 °C 2000 h (SMD 8×10 común)
    if tipo == "hibrido": return 4000 * 2 ** ((125 - t) / 10)             # 125 °C 4000 h (híbrido de polímero)
    if tipo == "polimero": return 2000 * 10 ** ((105 - t) / 20)           # polímero sólido 105 °C 2000 h
    return float("inf")

LIM = dict(U1=125.0, D2=125.0, L1=125.0, Q1=125.0, Q2=125.0, U3=85.0, aire=60.0)

def cumple(r):
    tj = r["Tj"]
    return (tj["U1"] <= LIM["U1"] and tj["D2"] <= LIM["D2"] and tj["L1"] <= LIM["L1"] and tj["U3"] <= LIM["U3"]
            and r["t_air"] <= LIM["aire"] and max(tj.values()) < 200)

def carga_max(perfil, caja, t_amb, placa):  # placa de 1 mm para que sea rápido
    lo, hi = 0.0, 1.0
    r = simular_cubo(perfil, caja, t_amb, 1.0, placa=placa)
    if cumple(r): return 1.0
    for _ in range(6):
        m = (lo + hi) / 2
        if cumple(simular_cubo(perfil, caja, t_amb, m, placa=placa)): lo = m
        else: hi = m
    return lo

def fmt(t):
    return "> 150 °C" if t > 150 else f"{t:.0f} °C"

def mapa_png(r, titulo, ruta, W, H, partes):
    fig, ax = plt.subplots(figsize=(6.4, 5.6), dpi=130)
    im = ax.imshow(r["T"], origin="lower", extent=(-W / 2, W / 2, -H / 2, H / 2), cmap="inferno")
    cb = fig.colorbar(im, ax=ax, shrink=0.85); cb.set_label("°C")
    for ref in partes:
        c = partes[ref]
        ax.text(c["x"], c["y"], ref, color="w", fontsize=7, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.15", fc=(0, 0, 0, 0.45), ec="none"))
    ax.set_title(titulo, fontsize=9); ax.set_xlabel("mm"); ax.set_ylabel("mm")
    fig.tight_layout(); fig.savefig(ruta); plt.close(fig)

# ---------------------------------------------------------------- nodo
PN, WN, HN = cargar(os.path.join(RAIZ, "nodo", "placa", "diseno.py"))

def simular_nodo(vin, i_canal, n_can, t_amb, caja="nodo", rev="B"):
    placa = Placa(WN, HN, CAJAS[caja], (12.0, -13.0, 19.0, 13.0))
    T = {"Q1": t_amb + 20}
    qk = "Qn" if rev == "B" else "QnA"
    args = {} if rev == "B" else dict(r_serie=0.0, rds=0.026, r_fus=0.015)
    for _ in range(20):
        P, info = perdidas_nodo(vin, i_canal, n_can, T, **args)
        fuentes = []
        for ref, p in P.items():
            c = PN[ref] if ref in PN else dict(x=-7.5, y=6.4, rot=0)
            key = {"U3": "U3n", "U1": "U1n", "U2": "U2n", "D1": "D1", "R30": "R30"}.get(ref, qk if ref.startswith("Q") else ref)
            w, h, _ = HUELLA[key]
            if c["rot"] % 180: w, h = h, w
            fuentes.append((c["x"], c["y"], w, h, p))
        Tf, ta, tw = placa.resolver(fuentes, 0.0, t_amb, t_guess=t_amb + 15)
        tq = placa.en(Tf, PN["Q1"]["x"], PN["Q1"]["y"], 2.4, 2.9) + P["Q1"] * HUELLA[qk][2]
        if abs(tq - T["Q1"]) < 0.05: break
        T["Q1"] = tq
    tj = {"Q": T["Q1"], "U3": placa.en(Tf, PN["U3"]["x"], PN["U3"]["y"], 4.5, 2.5) + P["U3"] * HUELLA["U3n"][2]}
    caps = {ref: placa.en(Tf, PN[ref]["x"], PN[ref]["y"], 2, 2) for ref in ("C1", "C2")}
    return dict(P=P, info=info, T=Tf, t_air=ta, t_wall=tw, Tj=tj, caps=caps, placa=placa)

# ---------------------------------------------------------------- informe
def main():
    L = []
    w = L.append
    w("# Informe térmico · Cubo AP (placa v3) y Nodo AP\n")
    w("Generado por `analisis/termico.py`. **Estimación de primer orden (±15 K), sin prototipo medido.** "
      "Se valida con termopares en U1, D2, L1, C1, C12 y aire interior, y con cámara térmica, a 25 °C y en cámara a 45 °C.\n")
    w("## 1. Modelo\n")
    w("- **Pérdidas por pieza**, recalculadas con la temperatura: TPS54560 (conducción con Rds(on) de 92 mΩ +0.4 %/K, "
      "conmutación Vin²·fsw·I·0.25 ns/V, carga de compuerta, Iq), Schottky B560C (Vf·I·(1−D) + **fuga en inversa** Vin·Ir(T)·D, "
      "Ir ×10 cada 37.5 K + carga de la capacitancia), inductor (I²·DCR con +0.39 %/K + núcleo), shunt, MOSFET de canal "
      "(peor caso: toda la corriente en un canal), borneras, fusible, MOSFET de polaridad, buck de 5 V y LDO de 3.3 V, ESP32-C3.")
    w(f"- **Placa** como lámina 2D de celdas de 0.5 mm: conductancia en el plano {K_SHEET*1e3:.1f} mW/K por cuadro "
      "(2 capas de 35 µm al 70 % + FR4). Cada cara: convección natural al aire interior y radiación a la pared (ε 0.9).")
    w(f"- **Convección natural** laminar h = 1.42·(ΔT/L)^¼ en cada superficie (3–6 W/m²K), radiación con h = εσ(T₁²+T₂²)(T₁+T₂). "
      "Caja: aire interior → pared, conducción por la pared, pared → ambiente. Aluminio: 16 aletas de 12 mm con canal de 7.2 mm (cubo.py, CUBO_CUERPO=aluminio): área de convección ×1.55, la radiación sale por la envolvente; gap pad bajo la zona de potencia "
      f"({H_PAD:.0f} W/m²K con vías térmicas); cartucho atornillado a la pared con pasta.")
    w("- **Cartucho AC-DC**: eficiencia 82–89 % según carga (típica de módulos IRM/LRS); su pérdida es la mayor fuente de calor.")
    w("- **Límites usados**: uniones ≤ 125 °C (margen de 25 K al máximo de 150 °C y de ~50 K al disparo térmico del TPS54560), "
      "ESP32-C3 ≤ 85 °C, aire interior ≤ 60 °C (los módulos AC-DC entregan el 100 % hasta 50–60 °C de aire).\n")

    # --- pérdidas por perfil
    w("## 2. Pérdidas en la placa por perfil (carga completa, 25 °C)\n")
    w("| Perfil | Cartucho | Ciclo D | U1 | D2 | L1 | Canal | Resto | **Placa** | **Cartucho** | **Total en el cubo** |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    placa_pl = Placa(W3, H3, CAJAS["plastico"], ZONA_PAD); placa_al = Placa(W3, H3, CAJAS["aluminio"], ZONA_PAD)
    rap_pl = Placa(W3, H3, CAJAS["plastico"], ZONA_PAD, 1e-3); rap_al = Placa(W3, H3, CAJAS["aluminio"], ZONA_PAD, 1e-3)
    filas = []
    for pf in PERFILES:
        r = simular_cubo(pf, "aluminio", 25.0, placa=placa_al)
        P = r["P"]; tot = sum(P.values())
        resto = tot - P["U1"] - P["D2"] - P["L1"] - P["Q2"]
        filas.append((pf[0], P, r))
        w(f"| {pf[0]} | {pf[3]:.0f} V | {r['info']['d']:.2f} | {P['U1']:.2f} | {P['D2']:.2f} | {P['L1']:.2f} | {P['Q2']:.2f} | "
          f"{resto:.2f} | **{tot:.1f} W** | **{r['p_cart']:.1f} W** | **{tot + r['p_cart']:.1f} W** |")
    w("\nLa pérdida del Schottky domina cuando el ciclo es bajo (5 V desde 24 V: conduce el 79 % del tiempo). "
      "El cartucho pierde más que toda la placa en los perfiles grandes.\n")

    fig, ax = plt.subplots(figsize=(7.5, 3.6), dpi=130)
    nombres = [f[0] for f in filas]; base = np.zeros(len(filas))
    for k, col, lab in (("U1", "#e8590c", "TPS54560"), ("D2", "#f08c00", "Schottky D2"), ("L1", "#fab005", "Inductor L1"),
                        ("Q2", "#82c91e", "MOSFET canal")):
        v = np.array([f[1][k] for f in filas]); ax.bar(nombres, v, bottom=base, color=col, label=lab); base += v
    v = np.array([sum(f[1].values()) for f in filas]) - base; ax.bar(nombres, v, bottom=base, color="#adb5bd", label="Resto placa"); base += v
    v = np.array([f[2]["p_cart"] for f in filas]); ax.bar(nombres, v, bottom=base, color="#495057", label="Cartucho AC-DC")
    ax.set_ylabel("W de calor dentro del cubo"); ax.legend(fontsize=7, ncol=3); ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(AQUI, "perdidas_perfiles.png")); plt.close(fig)
    w("![Pérdidas](perdidas_perfiles.png)\n")

    # --- comparación de cajas en el peor perfil
    peor = PERFILES[3]
    w(f"## 3. Peor caso: perfil {peor[0]} a 40 °C de ambiente\n")
    w("| Caja | Aire interior | Pared | U1 (unión) | D2 (unión) | L1 | ESP32-C3 | C1 | C12 | ¿Cumple? |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    res = {}
    for caja, pl in (("plastico", placa_pl), ("aluminio", placa_al)):
        r = simular_cubo(peor, caja, 40.0, placa=pl); res[caja] = r
        tj = r["Tj"]
        fuga = max(tj.values()) > 200
        u1txt = '> 150 °C (fuga térmica)' if fuga else fmt(tj['U1'])
        w(f"| {CAJAS[caja]['nombre']} | {fmt(r['t_air'])} | {fmt(r['t_wall'])} | {u1txt} | "
          f"{fmt(tj['D2'])} | {fmt(tj['L1'])} | {fmt(tj['U3'])} | {fmt(r['caps']['C1'])} | {fmt(r['caps']['C12'])} | "
          f"{'sí' if cumple(r) else '**no**'} |")
        mapa_png(r, f"Placa v3 · {peor[0]} · 40 °C · {CAJAS[caja]['nombre']}", os.path.join(AQUI, f"mapa_v3_{caja}.png"), W3, H3,
                 {k: PZ[k] for k in ("U1", "D2", "L1", "RS", "Q1", "C1", "C12", "U3", "U2", "J2", "J1")})
    w("\n![Mapa plástico](mapa_v3_plastico.png) ![Mapa aluminio](mapa_v3_aluminio.png)\n")
    w("**Conclusión:** en el cubo de plástico sellado el aire interior es la resistencia que manda (el calor tiene que pasar "
      "placa → aire → pared con coeficientes de 3–5 W/m²K). Con 60 W de salida no es viable: el aire pasa de 60 °C, el cartucho "
      "sale de su curva y la fuga del Schottky D2 crece con la temperatura hasta desbocarse (fuga térmica). El cuerpo de aluminio con aletas, costilla y gap pad saca el calor por conducción: da el 100 % hasta ≈ 25–30 °C "
      "en los perfiles de 60–72 W y a 40 °C recorta a ≈ 56 %. El límite es la unión del TPS54560 (≈ 1.9 W de pérdida a 12 V 5 A): "
      "la v4 con reductor síncrono lo resuelve. Los perfiles de hasta 45 W van al 100 % hasta 40 °C.\n")

    # --- derating
    w("## 4. Curva de carga máxima contra temperatura ambiente\n")
    ambs = [25, 30, 35, 40, 45, 50, 55]
    fig, ax = plt.subplots(figsize=(7.5, 3.8), dpi=130)
    tabla = {}
    for pf, col in ((PERFILES[3], "#e8590c"), (PERFILES[6], "#1971c2"), (PERFILES[0], "#2f9e44"), (PERFILES[4], "#9c36b5"),
                    (PERFILES[2], "#0c8599")):
        for caja, pl, est in (("plastico", rap_pl, "--"), ("aluminio", rap_al, "-")):
            ys = [100 * carga_max(pf, caja, a, pl) for a in ambs]
            tabla[(pf[0], caja)] = ys
            ax.plot(ambs, ys, est, color=col, label=f"{pf[0]} · {'plástico' if caja == 'plastico' else 'aluminio'}")
    ax.set_xlabel("Temperatura ambiente (°C)"); ax.set_ylabel("Carga máxima continua (%)"); ax.set_ylim(0, 105)
    ax.grid(alpha=0.3); ax.legend(fontsize=6.5, ncol=2)
    fig.tight_layout(); fig.savefig(os.path.join(AQUI, "derating.png")); plt.close(fig)
    w("| Perfil · caja | " + " | ".join(f"{a} °C" for a in ambs) + " |")
    w("|---|" + "---|" * len(ambs))
    for (n, caja), ys in tabla.items():
        w(f"| {n} · {'plástico' if caja == 'plastico' else 'aluminio'} | " + " | ".join(f"{y:.0f} %" for y in ys) + " |")
    w("\n![Derating](derating.png)\n")
    pl_w = {a: max(tabla[(pf[0], "plastico")][ambs.index(a)] / 100 * pf[1] * pf[2] for pf in PERFILES if (pf[0], "plastico") in tabla)
            for a in (25, 30, 40)}
    w(f"**Cubo de plástico:** saca como máximo ≈ {pl_w[25]:.0f} W de salida a 25 °C, ≈ {pl_w[30]:.0f} W a 30 °C y ≈ {pl_w[40]:.0f} W a 40 °C. "
      "Sirve para interiores con 12 V 1 A o 5 V hasta 2 A; para lo demás, cuerpo de aluminio.\n")
    w("El firmware ya tiene **recorte térmico de 70 a 90 °C** medido en la placa (TH1 junto a L1): baja el brillo de forma lineal "
      "y apaga a 90 °C. Esta curva es la que se publica en la hoja de datos.\n")

    # --- sol
    r_sol = simular_cubo(peor, "aluminio", 40.0, sol=0.5 * 1000 * 0.080**2 * 1.5, placa=placa_al)
    w("## 5. Sol directo\n")
    w(f"Con sol de 1000 W/m² sobre la tapa y una cara (absortancia 0.5, gris claro) entran ≈ {0.5*1000*0.08**2*1.5:.1f} W más. "
      f"En aluminio, {peor[0]} a 40 °C: aire {r_sol['t_air']:.0f} °C, U1 {r_sol['Tj']['U1']:.0f} °C, ESP32 {r_sol['Tj']['U3']:.0f} °C "
      f"({'cumple' if cumple(r_sol) else 'no cumple: el recorte térmico baja el brillo'}). "
      "Recomendación: acabado claro (anodizado natural o pintura blanca); un acabado negro casi duplica la carga solar.\n")

    # --- capacitores
    w("## 6. Capacitores y calor\n")
    ra = res["aluminio"]
    w("Regla aplicada: **ningún electrolítico junto a una fuente de calor**. Los cerámicos X7R de entrada y salida del reductor "
      "**deben** quedarse pegados a U1/D2/L1: el lazo de alta corriente conmutada tiene que ser lo más corto posible "
      "(si se alejan, sube la inductancia del lazo, los picos de voltaje en SW y la emisión electromagnética). "
      "Los X7R no se secan: aguantan 125 °C y no tienen desgaste por temperatura, solo pierden algo de capacitancia (±15 %).\n")
    w("| Pieza | Tipo | Temperatura (aluminio, 40 °C, " + peor[0] + ") | Vida estimada | Acción |")
    w("|---|---|---|---|---|")
    t1, t12 = ra["caps"]["C1"], ra["caps"]["C12"]
    w(f"| C1 entrada 100 µF 50 V | electrolítico 105 °C 2000 h | {t1:.0f} °C | {vida('electrolitico', t1)/8760:.1f} años continuos | "
      f"**cambiar a híbrido de polímero 125 °C 4000 h** → {vida('hibrido', t1)/8760:.0f} años |")
    w(f"| C12 salida 100 µF 35 V | polímero sólido | {t12:.0f} °C | {min(vida('polimero', t12)/8760, 99):.0f} años | "
      "**movido a 2.5 mm de L1** (estaba a 0.2 mm del cuerpo del inductor) |")
    for ref in ("C2", "C10", "C18", "C31"):
        w(f"| {ref} | cerámico X7R | {ra['caps'][ref]:.0f} °C | sin desgaste térmico | se queda junto a su regulador (lazo corto) |")
    w("")

    # --- nodo
    w("## 7. Nodo AP\n")
    w("Rev. A = diseño anterior (AO3400A SOT-23 de 26 mΩ, fusible 6.3 A, 78L05 directo). "
      "Rev. B = esta revisión (MOSFET DFN 3.3×3.3 de ≤ 10 mΩ, fusible 8 A, 150 Ω en serie con el 78L05).\n")
    w("| Caso (40 °C) | Caja | Pérdida | Aire interior | MOSFET (unión) | 78L05 (unión) | C1 | C2 | ¿Cumple? |")
    w("|---|---|---|---|---|---|---|---|---|")
    casos = [("Rev. A · 24 V · 2 × 3 A", 24, 3.0, 2, "nodo", "A"), ("Rev. B · 24 V · 2 × 3 A", 24, 3.0, 2, "nodo", "B"),
             ("Rev. B · 24 V · 4 × 1.25 A", 24, 1.25, 4, "nodo", "B"), ("Rev. B · 12 V · 4 × 1.25 A", 12, 1.25, 4, "nodo", "B"),
             ("Rev. B · 24 V · 2 × 3 A", 24, 3.0, 2, "nodo_al", "B"), ("Rev. B · 24 V · 4 × 1.25 A", 24, 1.25, 4, "nodo_al", "B")]
    rn = None
    for nom, v, i, nc, caja, rev in casos:
        r = simular_nodo(v, i, nc, 40.0, caja, rev)
        ok = r["Tj"]["Q"] <= 125 and r["Tj"]["U3"] <= 125 and r["t_air"] <= 70
        w(f"| {nom} | {'plástico' if caja == 'nodo' else 'aluminio'} | {sum(r['P'].values()):.2f} W | {r['t_air']:.0f} °C | "
          f"{r['Tj']['Q']:.0f} °C | {r['Tj']['U3']:.0f} °C | {r['caps']['C1']:.0f} °C | {r['caps']['C2']:.0f} °C | {'sí' if ok else '**no**'} |")
        if rev == "B" and caja == "nodo" and i == 3.0: rn = r
    mapa_png(rn, "Nodo AP rev. B · 24 V · 2 canales × 3 A · 40 °C · caja de plástico", os.path.join(AQUI, "mapa_nodo.png"), WN, HN,
             {k: PN[k] for k in ("U3", "Q1", "Q2", "Q3", "Q4", "F1", "C1", "C2", "U1", "J2")})
    w("\n![Mapa nodo](mapa_nodo.png)\n")
    w("El nodo no tiene reductor: su calor viene de los MOSFET, el fusible, las borneras y el regulador lineal. "
      "En la rev. A, con 6 A el fusible de 6.3 A trabajaba al 95 % de su nominal (los fusibles se usan a ≤ 75 % y menos con calor) "
      "y los AO3400A en SOT-23 pasaban de 140 °C. La rev. B usa MOSFET DFN de ≤ 10 mΩ con pad de drenaje al cobre, fusible de 8 A "
      "y límite de **5 A en total** (3 A por canal). La resistencia de 150 Ω reparte el calor del 78L05 y deja funcionar el nodo desde "
      "12 V (el 78L05 necesita ≥ 6.7 V en su entrada). C1 y C2 son cerámicos X7R que deben ir pegados al regulador para su estabilidad; "
      "no tienen desgaste por temperatura.\n")

    # --- cambios
    w("## 8. Cambios de diseño que salen del análisis\n")
    w("1. **Cuerpo de aluminio** (fundición o maquinado, aletas en las 4 caras laterales, anodizado claro) para los perfiles de más de 25 W; "
      "el de plástico queda para interiores hasta ≈ 15 W (12 V 1 A, 5 V 2 A). La antena ya es externa (U.FL), así que el metal no estorba la radio.")
    w("2. **Costilla interna + gap pad** (3 W/m·K, 1 mm, aislante) bajo la zona U1–D2–L1–RS–Q1, con **vías térmicas** "
      "en esa zona de la placa. La placa queda flotante eléctricamente: el gap pad aísla.")
    w("3. **Cartucho atornillado a la pared** de aluminio con pasta o pad térmico; no flotando en el aire.")
    w("4. **C1 → híbrido de polímero 125 °C** (misma huella 8×10), **C12 → 2.5 mm de L1** (antes 0.2 mm) (aplicado en la placa v3); la placa ya lleva **4 vías térmicas bajo el PowerPAD de U1 y 4 bajo el ánodo de D2** hacia el plano inferior.")
    w("5. **Nodo rev. B:** MOSFET DFN 3.3×3.3 de ≤ 10 mΩ, fusible de 8 A, 150 Ω en serie antes del 78L05 y límite de 5 A total (aplicado y reruteado).")
    w("6. **Hoja de datos:** curva de carga contra temperatura ambiente; rango de operación −20 a +50 °C; acabado claro en exteriores.")
    w("7. **Siguiente revisión de la placa (v4):** cambiar el reductor asíncrono (TPS54560 + Schottky) por uno **síncrono** de 60 V 5 A "
      "(p. ej. LM76005): desaparece D2 y su fuga, y la pérdida a 12 V 5 A baja de ≈ 3.2 W a ≈ 1.5 W. Mientras tanto, D2 puede ser un "
      "rectificador de baja fuga (trinchera o SBR) de 60 V 5 A en SMC.")
    w("8. **Nodo AP:** caja de perfil de aluminio con gap pad bajo los MOSFET para instalaciones de 5 A continuos o a más de 35 °C.")
    open(os.path.join(AQUI, "informe_termico.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))

if __name__ == "__main__":
    main()
