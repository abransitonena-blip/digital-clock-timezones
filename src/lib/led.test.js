import { test } from 'node:test'
import assert from 'node:assert/strict'
import { cotizar, COSTOS_EJEMPLO, e96, rbParaVoltaje, vDeRb, elegirTarjeta, elegirCartucho, caidaCable, awgMinimo, consumo, planificar, resumenLote, vMinApp, PERFILES } from './led.js'

test('E96', () => {
  assert.equal(e96(29400), 29400); assert.equal(e96(1927.9), 1910); assert.equal(e96(2099), 2100); assert.equal(e96(5600), 5620)
  assert.ok(Number.isNaN(e96(0)))
})
test('R_B de los perfiles coincide con el firmware', () => {
  for (const p of PERFILES) assert.ok(Math.abs(vDeRb(p.rb) - p.vmax) < 0.06, p.nombre)
})
test('R_B a la medida', () => {
  const r = rbParaVoltaje(13); assert.equal(r.rb, 1910); assert.ok(Math.abs(r.vreal - 13) < 0.15)
  assert.equal(rbParaVoltaje(30), null); assert.equal(rbParaVoltaje(2), null)
})
test('tarjetas para los pedidos de ejemplo', () => {
  assert.equal(elegirTarjeta(12, 5).nombre, '12V 5A')
  assert.equal(elegirTarjeta(12, 1).nombre, '12V 1A')
  assert.equal(elegirTarjeta(15, 1).nombre, '15V 1A')
  assert.equal(elegirTarjeta(12, 1.5).nombre, '12V 2A')
  const p = elegirTarjeta(19, 2); assert.equal(p.personal, true); assert.equal(p.rid, 220000)
  assert.equal(elegirTarjeta(12, 6), null)
})
test('cartucho y rango de la app', () => {
  assert.equal(elegirCartucho(12).id, 'S'); assert.equal(elegirCartucho(15).id, 'S'); assert.equal(elegirCartucho(30).id, 'M')
  assert.equal(elegirCartucho(60).id, 'L'); assert.equal(elegirCartucho(70), null)
  assert.ok(Math.abs(vMinApp(12) - 10.62) < 0.01)
})
test('cable', () => {
  const c = caidaCable(5, 2, 18); assert.ok(Math.abs(c.v - 0.42) < 1e-9)
  assert.equal(awgMinimo(5, 2, 12), 16); assert.equal(awgMinimo(1, 2, 12), 24)
})
test('consumo de la tira del usuario: 7 filas de 2835 a 12 V', () => {
  const tira = { v: 12, wm: 4.8, tramoMax: 5 }
  const c = consumo(tira, 7 * 1, 1); assert.ok(Math.abs(c.a - 2.8) < 1e-9); assert.equal(c.cubos, 1); assert.equal(c.inyecciones, 1)
  const g = consumo({ v: 5, wm: 18, tramoMax: 2 }, 10, 1); assert.equal(g.cubos, 8); assert.equal(g.inyecciones, 4)
})
test('planificar y lote', () => {
  const a = planificar({ v: 12, a: 5, cantidad: 20 }); assert.equal(a.cartucho.id, 'L'); assert.equal(a.cubos, 20); assert.deepEqual(a.errores, []); assert.ok(a.avisos[0].includes('89 %'))
  const b = planificar({ v: 12, a: 8 }); assert.equal(b.cubosPorLetrero, 2); assert.equal(b.tarjeta.nombre, '12V 5A')
  const c = planificar({ v: 24, a: 2 }); assert.equal(c.cartucho.id, 'L'); assert.ok(c.errores.some(e => e.includes('28–36 V')))
  assert.ok(planificar({ v: 24, a: 3 }).errores.some(e => e.includes('75 W')))
  const r = resumenLote([{ v: 12, a: 5, cantidad: 20 }, { v: 12, a: 1, cantidad: 3 }, { v: 15, a: 1, cantidad: 2 }])
  assert.equal(r.total, 25); assert.equal(r.cubos.L, 20); assert.equal(r.cubos.S, 5)
  assert.equal(r.tarjetas['12V 5A (R_B 2100 Ω, R_ID 33k)'], 20)
})

test('cotización', () => {
  const c = { ...COSTOS_EJEMPLO }
  const q = cotizar([{ v: 12, a: 5, cantidad: 2 }, { v: 12, a: 1, cantidad: 1 }, { v: 40, a: 1, cantidad: 3 }], c, { margen: 0.5, iva: 0.16 })
  const L = c.L + c.placa + c.caja100 + c.tarjeta + c.accesorios + c.manoObra
  const S = c.S + c.placa + c.caja80 + c.tarjeta + c.accesorios + c.manoObra
  assert.equal(q.detalle[0].costoCubo, L); assert.equal(q.detalle[1].costoCubo, S); assert.equal(q.detalle[2].costo, 0)   // 40 V: inválido, no suma
  assert.equal(q.costo, 2 * L + S); assert.ok(Math.abs(q.total - (2 * L + S) * 1.5 * 1.16) < 1e-9); assert.ok(Math.abs(q.ganancia - (2 * L + S) * 0.5) < 1e-9)
})
