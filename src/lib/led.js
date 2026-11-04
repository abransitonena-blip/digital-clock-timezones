// Cálculos de tiras LED y del Cubo AP. Funciones puras (sin React) para poder probarlas con `node --test`.
// Los consumos de tiras son valores típicos del mercado: verifica siempre la ficha del fabricante.

export const VREF = 0.8, RT = 29400, RINJ = 47000          // red de realimentación de la placa de control
export const I_MAX_CUBO = 5                                   // A por cubo (reductor TPS54560)

// Perfiles de tarjeta del firmware (mismo orden y valores que firmware/src/nucleo.cpp)
export const PERFILES = [
  { nombre: '5V 3A', rid: 10000, vmax: 4.98, imax: 3, rb: 5620 },
  { nombre: '12V 1A', rid: 15000, vmax: 12.0, imax: 1, rb: 2100 },
  { nombre: '12V 2A', rid: 22000, vmax: 12.0, imax: 2, rb: 2100 },
  { nombre: '12V 5A', rid: 33000, vmax: 12.0, imax: 5, rb: 2100 },
  { nombre: '15V 1A', rid: 47000, vmax: 15.05, imax: 1, rb: 1650 },
  { nombre: '15V 3A', rid: 68000, vmax: 15.05, imax: 3, rb: 1650 },
  { nombre: '24V 2A', rid: 100000, vmax: 24.32, imax: 2, rb: 1000 },
  { nombre: '24V 3A', rid: 150000, vmax: 24.32, imax: 3, rb: 1000 },
]
export const PERSONAL = { nombre: 'PERSONAL', rid: 220000 }

// Cartuchos de potencia (AC 127 V -> DC). Clase de potencia; el modelo exacto se elige al comprar.
export const CARTUCHOS = [
  { id: 'S', w: 25, vsal: 24, cubo: '80 mm (ASA/PETG)' },
  { id: 'M', w: 40, vsal: 24, cubo: '80 mm (ASA/PETG)' },
  { id: 'L', w: 75, vsal: 24, cubo: '100 mm de aluminio (disipa ~8 W)' },
]

const E96 = [100, 102, 105, 107, 110, 113, 115, 118, 121, 124, 127, 130, 133, 137, 140, 143, 147, 150, 154, 158, 162, 165, 169, 174, 178, 182, 187, 191, 196, 200, 205, 210, 215, 221, 226, 232, 237, 243, 249, 255, 261, 267, 274, 280, 287, 294, 301, 309, 316, 324, 332, 340, 348, 357, 365, 374, 383, 392, 402, 412, 422, 432, 442, 453, 464, 475, 487, 499, 511, 523, 536, 549, 562, 576, 590, 604, 619, 634, 649, 665, 681, 698, 715, 732, 750, 768, 787, 806, 825, 845, 866, 887, 909, 931, 953, 976]

/** Valor E96 (1 %) más cercano a r ohm. */
export function e96(r) {
  if (!(r > 0)) return NaN
  const dec = Math.pow(10, Math.floor(Math.log10(r)) - 2)
  let mejor = Infinity, val = NaN
  for (const m of [...E96, 1000]) {
    const v = m * dec
    const err = Math.abs(Math.log(v / r))
    if (err < mejor) { mejor = err; val = v }
  }
  return Math.round(val * 1000) / 1000
}
/** Voltaje de salida para una R_B dada. */
export const vDeRb = rb => VREF * (1 + RT / rb)
/** R_B ideal y E96 para un voltaje máximo (3–24.4 V). */
export function rbParaVoltaje(v) {
  if (!(v >= 3 && v <= 24.4)) return null
  const ideal = RT / (v / VREF - 1)
  const rb = e96(ideal)
  return { ideal, rb, vreal: vDeRb(rb) }
}
/** Rango que la app puede ajustar (solo hacia abajo) dado el máximo. */
export const vMinApp = vmax => vmax - (3.3 - 0.3 - VREF) * RT / RINJ

/** Elige la tarjeta: perfil estándar si existe (mismo voltaje ±3 % y corriente suficiente), si no PERSONAL. */
export function elegirTarjeta(v, i) {
  const candidatos = PERFILES.filter(p => Math.abs(p.vmax - v) / v <= 0.03 && p.imax >= i).sort((a, b) => a.imax - b.imax)
  if (candidatos.length) return { ...candidatos[0], personal: false }
  const rb = rbParaVoltaje(v)
  if (!rb || i > I_MAX_CUBO) return null
  return { ...PERSONAL, vmax: +rb.vreal.toFixed(2), imax: i, rb: rb.rb, personal: true }
}

/** Elige cartucho para una potencia de salida (W) con eficiencia y margen. */
export function elegirCartucho(wSalida, { eficiencia = 0.9, margen = 1.1 } = {}) {
  const necesario = (wSalida / eficiencia) * margen
  return CARTUCHOS.find(c => c.w >= necesario) || null
}

/** Resistencia por metro de UN conductor de cobre (Ω/m) a 20 °C. */
export const AWG = { 24: 0.0842, 22: 0.0530, 20: 0.0333, 18: 0.0210, 16: 0.0132, 14: 0.00828, 12: 0.00521 }

/** Caída en el cable (ida y vuelta). */
export function caidaCable(corriente, metros, awg) {
  const r = AWG[awg]
  if (r == null) throw new Error('AWG no soportado')
  const v = corriente * r * 2 * metros
  return { v, w: corriente * v }
}
/** Calibre mínimo para que la caída del cable sea ≤ pct del voltaje. */
export function awgMinimo(corriente, metros, voltaje, pct = 0.03) {
  const ordenados = Object.keys(AWG).map(Number).sort((a, b) => b - a)   // del más delgado al más grueso
  for (const g of ordenados) if (caidaCable(corriente, metros, g).v <= voltaje * pct) return g
  return null
}

/**
 * Consumo de una instalación.
 * tira: { v, wm (W/m al 100 %), tramoMax (m sin reinyectar) }; metros; uso 0–1 (blanco 100 % = 1; efectos ≈ 0.4–0.6).
 */
export function consumo(tira, metros, uso = 1) {
  const w = tira.wm * metros * uso
  const a = w / tira.v
  const inyecciones = Math.max(0, Math.ceil(metros / tira.tramoMax) - 1)
  const cubos = Math.max(1, Math.ceil(a / I_MAX_CUBO))
  return { w, a, inyecciones, cubos, aPorCubo: a / cubos, wPorCubo: w / cubos }
}

/** Plan completo para un pedido: tarjeta, cartucho y cable por cubo. */
export function planificar({ v, a, cantidad = 1, metrosCable = 2 }) {
  const cubosPorLetrero = Math.max(1, Math.ceil(a / I_MAX_CUBO))
  const aCubo = a / cubosPorLetrero
  const tarjeta = elegirTarjeta(v, aCubo)
  const cartucho = elegirCartucho(v * aCubo)
  const awg = awgMinimo(aCubo, metrosCable, v)
  const errores = []
  if (!tarjeta) errores.push(v > 24.4 || v < 3 ? 'Voltaje fuera de 3–24.4 V' : 'Corriente fuera de rango')
  if (!cartucho) errores.push('La potencia por cubo supera el cartucho L (75 W): divide la carga')
  if (cartucho && v > cartucho.vsal - 1.2) errores.push('El cartucho de 24 V no alcanza: usa uno de 28–36 V para salidas mayores a 22.8 V')
  const avisos = []
  const carga = cartucho ? (v * aCubo / 0.9) / cartucho.w : 0
  if (carga > 0.85) avisos.push(`Cartucho ${cartucho.id} al ${Math.round(carga * 100)} %: asegura ventilación o baja a 11–11.5 V`)
  if (!awg) avisos.push('Cable muy largo: acerca el cubo a la tira o reinyecta')
  return {
    avisos, carga,
    cubosPorLetrero, cubos: cubosPorLetrero * cantidad, aCubo, wCubo: v * aCubo, tarjeta, cartucho, awg, errores,
    vMin: tarjeta && tarjeta.vmax ? vMinApp(tarjeta.vmax) : null,
  }
}

/** Resume un lote de pedidos (lista de compra). */
export function resumenLote(pedidos) {
  const cubos = {}, tarjetas = {}
  let w = 0, total = 0
  for (const p of pedidos) {
    const pl = planificar(p)
    if (pl.errores.length) continue
    total += pl.cubos; w += pl.wCubo * pl.cubos
    const k = pl.cartucho.id; cubos[k] = (cubos[k] || 0) + pl.cubos
    const t = pl.tarjeta.personal ? `PERSONAL ${pl.tarjeta.vmax} V (R_B ${pl.tarjeta.rb} Ω, R_ID 220k)` : `${pl.tarjeta.nombre} (R_B ${pl.tarjeta.rb} Ω, R_ID ${pl.tarjeta.rid / 1000}k)`
    tarjetas[t] = (tarjetas[t] || 0) + pl.cubos
  }
  return { cubos, tarjetas, total, w }
}
