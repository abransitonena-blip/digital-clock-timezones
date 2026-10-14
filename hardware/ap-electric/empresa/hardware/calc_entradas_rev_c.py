#!/usr/bin/env python3
"""Cálculo reproducible de las opciones de entrada bipolar (estudio rev C del 7R Tour).
Uso:  python3 calc_entradas_rev_c.py
Modelos de diodo/LED: [H] (exponencial con idealidad supuesta); CTR mínimo/máximo: [E]/[CG] (ver ESTUDIO_REV_C.md).
No es una medición. Cambie las constantes de ENTRADAS para probar otros valores."""
import math

VT = 0.02585
def vf_ir(i, v5=1.2, n=2.0):            # LED infrarrojo del opto: 1.2 V a 5 mA [E catálogo LTV-217] ; n supuesto [H]
    return v5 + n * VT * math.log(max(i, 1e-9) / 5e-3)
def vf_verde(i):                          # LED indicador verde 0603: ~2.0 V a 2 mA [H]
    return 2.0 + 0.08 * math.log(max(i, 1e-9) / 2e-3)
def vf_d(i):                              # 1N4148W: ~0.72 V a 5 mA [H]; catálogo: 1 V a 50 mA
    return 0.72 + 0.045 * math.log(max(i, 1e-9) / 5e-3)

PULLUP, VCC = 10e3, 3.3
VIL = 0.3 * VCC                           # TCA9554: VIL = 0.3 VCC [CG]
IC_NEC = (VCC - VIL) / PULLUP             # corriente de colector para llevar la línea a VIL
CTR = {"217-B": (0.50, 2.60), "354T": (0.20, 3.00)}   # (mínimo garantizado, máximo de la banda) ; mín [E], máx [CG]/[E rev J]

def corr_entrada(vin, rser, rs, n_diodos=0, led_ind=False):
    """Devuelve (I_entrada, I_led_opto) para la tensión vin (>0), bisección sobre I_entrada."""
    def v_req(i):
        # i = i_rs + i_f ;  V_IL = vf_ir(i_f) = rs * i_rs
        lo, hi = 0.0, i
        for _ in range(60):
            m = (lo + hi) / 2                       # i_f
            v_il = vf_ir(m)
            if (i - m) * rs > v_il: lo = m          # sobra corriente por RS => más para el LED
            else: hi = m
        i_f = (lo + hi) / 2
        v = i * rser + vf_ir(i_f) + n_diodos * vf_d(i) + (vf_verde(i) if led_ind else 0.0)
        return v, i_f
    lo, hi = 0.0, 0.1
    for _ in range(60):
        m = (lo + hi) / 2
        v, _f = v_req(m)
        if v < vin: lo = m
        else: hi = m
    i = (lo + hi) / 2
    return i, v_req(i)[1]

def umbral(rser, rs, ctr, n_diodos, led_ind):
    """Tensión de entrada a la que IC = IC_NEC (el nivel pasa a 0)."""
    lo, hi = 0.0, 40.0
    for _ in range(50):
        m = (lo + hi) / 2
        _i, i_f = corr_entrada(m, rser, rs, n_diodos, led_ind)
        if ctr * i_f >= IC_NEC: hi = m
        else: lo = m
    return (lo + hi) / 2

ENTRADAS = [
    # nombre, rser, rs, n_diodos (puente = 2), led indicador en serie, opto
    ("O0 rev B: LTV-217 + LED serie + RS (hoy)",            4.4e3, 2.2e3, 0, True,  "217-B"),
    ("O1 puente + LTV-217 + LED serie, mismas R",           4.4e3, 2.2e3, 2, True,  "217-B"),
    ("O1b puente + LTV-217, LED serie, R 3.9k / RS 1.5k",   3.9e3, 1.5e3, 2, True,  "217-B"),
    ("O2 opto CA LTV-354T, LED en lado lógico, mismas R",   4.4e3, 2.2e3, 0, False, "354T"),
    ("O2b opto CA, R 4.7k / RS 1.0k",                       4.7e3, 1.0e3, 0, False, "354T"),
    ("O2c opto CA, R 4.7k / RS 0.82k",                      4.7e3, 0.82e3, 0, False, "354T"),
    ("O2d opto CA, R 3.3k / RS 1.0k + LED serie bicolor/antiparalelo (Vf~2V)", 3.3e3, 1.0e3, 0, True, "354T"),
]

if __name__ == "__main__":
    print("IC necesaria para llevar la linea de 3.3 V (pull-up 10k) a VIL=%.2f V: %.3f mA" % (VIL, IC_NEC * 1e3))
    print("%-62s %6s %6s | %8s %8s | %8s %8s | %7s %7s" % ("opcion", "Iin12", "Iin24", "Von_gar", "Voff_gar", "Von_tip", "", "Iin30", "P24mW"))
    for nom, rser, rs, nd, led, op in ENTRADAS:
        cmin, cmax = CTR[op]
        i12, _ = corr_entrada(12, rser, rs, nd, led); i24, if24 = corr_entrada(24, rser, rs, nd, led)
        i30, _ = corr_entrada(30, rser, rs, nd, led)
        von_gar = umbral(rser, rs, cmin, nd, led)       # aun la pieza de CTR mínimo ya lee "activa"
        voff_gar = umbral(rser, rs, cmax, nd, led)      # por debajo de esto ninguna pieza lee "activa" (CTR máximo)
        print("%-62s %6.2f %6.2f | %8.2f %8.2f | %8.2f %8s | %7.2f %7.0f" % (
            nom, i12 * 1e3, i24 * 1e3, von_gar, voff_gar, umbral(rser, rs, math.sqrt(cmin * cmax), nd, led), "", i30 * 1e3, 24 * i24 * 1e3))
    # corriente de entrada justo en 5 V y en 15 V (IEC 61131-2 tipo 1: apagada <=5 V ; encendida >=15 V con >=2 mA)
    print()
    for nom, rser, rs, nd, led, op in ENTRADAS:
        i5, _ = corr_entrada(5, rser, rs, nd, led); i15, _ = corr_entrada(15, rser, rs, nd, led); i11, _ = corr_entrada(11, rser, rs, nd, led)
        print("%-62s I(5V)=%.2f mA  I(11V)=%.2f mA  I(15V)=%.2f mA" % (nom, i5 * 1e3, i11 * 1e3, i15 * 1e3))
    # tiempos a 500 Hz
    print()
    f = 500.0; semi = 1 / f / 2
    print("500 Hz: periodo %.1f ms, semiperiodo (50 %% de trabajo) %.2f ms" % (2e3 / f / 1e0 / 2 * 2 / 2 * 1, semi * 1e3))
    for c, nom in [(0, "sin C"), (1e-9, "1 nF"), (10e-9, "10 nF"), (100e-9, "100 nF")]:
        # C en el colector: sube por el pull-up hasta VIH=0.7*VCC ; baja rapido por el transistor
        t_sube = -PULLUP * (c + 20e-12) * math.log(1 - 0.7)
        print("  C colector %-7s: tiempo de subida a VIH = %7.1f us  (%.1f %% del semiperiodo)" % (nom, t_sube * 1e6, 100 * t_sube / semi))
    # filtro en el lado de entrada: C en paralelo con RS (carga por rser)
    for c, nom in [(10e-9, "10 nF"), (100e-9, "100 nF"), (220e-9, "220 nF")]:
        tau = 4.4e3 * c
        print("  C de entrada %-7s (R serie 4.4k): tau=%.2f ms ; retardo a ~63 %% = tau" % (nom, tau * 1e3))
    # potencia de las resistencias a 30 V
    i30, _ = corr_entrada(30, 4.4e3, 2.2e3, 0, True)
    print("Potencia por resistencia de 2.2k (2 en serie) a 30 V en rev B: %.0f mW (0805: 125 mW [CG])" % ((i30 ** 2) * 2.2e3 * 1e3))
