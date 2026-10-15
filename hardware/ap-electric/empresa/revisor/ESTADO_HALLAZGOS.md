# Estado de los hallazgos de la revisión adversarial (rev B)

Actualizado el 14-oct-2026 por la dirección. Informe original: [INFORME_REVISION_REV_B.md](INFORME_REVISION_REV_B.md). **Cerrado** = corregido y con prueba o comprobación por software; no significa medido en una placa.

| ID | Estado | Qué se hizo / qué falta | Dueño |
|---|---|---|---|
| H-01 | Cerrado en el diseño; verificar la ficha al pedir | Todas las posiciones de 10 µF del riel usan ahora la misma fila «10uF 50V» (C13585, que el catálogo del repositorio describe como CL31A106KBHNNNE de 50 V): ya no hay un mismo código con dos voltajes. Falta ver la ficha en lcsc.com | compras |
| H-02 | Cerrado en software; falta ver la vista previa | El CPL usa ahora las mismas coordenadas que los Gerber (las de KiCad) y `revisar_pedido.py` lo comprueba. Las rotaciones se revisan a mano en «Component Placement» (lista de piezas de riesgo en PUESTA_EN_MARCHA.md) | compras / hardware |
| H-03 | **Abierto (sin costo)** | Confirmar con la hoja del CA-IS3092W los pines 7, 12 y 13. Si A/B resultaran invertidas basta cruzar los cables; el pin 7 en GND es hipótesis | hardware |
| H-04 | Cerrado | De fábrica, las entradas de una placa de varios canales quedan desacopladas; AP Home conserva pulsador. Con prueba | firmware |
| H-05 | Cerrado (con otra decisión) | La vigilancia es un **latido de escrituras**, documentado: las lecturas no cuentan (así un HMI que solo lee no oculta la muerte del maestro que manda). De fábrica está en 0 (sin vigilancia). Con prueba | firmware |
| H-06 | Cerrado | Tras un reinicio, el desempeño y el OEE no son calculables hasta `PK BORRAR` o un arranque limpio. Con prueba | firmware |
| H-07 | Cerrado | Clave aleatoria de 8 dígitos guardada en la memoria; orden `CLAVE` por USB. Falta el procedimiento de etiquetado en producción | firmware |
| H-08 | Documentado | La red INT no la maneja ningún expansor: el programa sondea. Se corrige en la rev C (unir las salidas INT o quitar la red) | hardware |
| H-09 | Cerrado | Se generan `AP_7R_TOUR_24DC_*_solo_SMD.csv`; la guía los cita | hardware |
| H-10 | Cerrado | «Aislamiento funcional; 5 kVrms es del chip» en la hoja de datos y en el diseño final | calidad |
| H-11 | Cerrado | El límite de 30 V del piloto está en la hoja de datos y en el diseño final | calidad |
| H-12 | Abierto (medir) | Umbral de entradas por medir (prueba P1); se ajusta con RA/RB sin cambiar la placa | calidad |
| H-13 | Abierto (medir / verificar) | Fusible F1, bobina a 30 V y retorno por el TVS; limitar el piloto a 22-26 V hasta medir | hardware / calidad |
| H-14 | Documentado | Con solo USB, V24 sube a ≈ 4 V y las bobinas se leen «energizadas»; la guía lo dice. La solución de hardware es de la rev C | hardware |
| H-15 | Cerrado | El rótulo de cada canal dice «NA… C…» en el orden en que están los pines | hardware |
| H-16 | Abierto (bajo) | Marcar el «+» junto al pin 1 del conector de batería en la próxima serigrafía | hardware |
| H-17 | Abierto | Cotizar con 2 oz y mirar el DFM en pantalla | compras |
| H-18 | Cerrado | «Valores de fábrica» borra toda la configuración y conserva solo la clave; el registro 200 = 0x5AA5 exige el permiso local (excepción 04 si no). Con prueba | firmware |
| H-19 | Cerrado (reabierto y corregido en la 2.ª revisión) | Contadores separados de lectura y de escritura: una lectura sana ya no borra una falla de escritura ni al revés | firmware |
| H-20 | Documentado | La entrada de conteo rápido ignora pulsos separados menos de 2 ms: solo sensores sin rebote | firmware |
| H-21 | Cerrado | La consola muestra la definición propia de disponibilidad, desempeño y calidad junto al OEE | web |
| H-22 | Documentado | Los estados PackML no abren relés por sí mismos; falta vigilancia por hardware de los relés (rev C) | hardware / producto |
| H-23 | Cerrado | `validar` corrige `nEntradas` y el arranque exige que coincida con la placa | firmware |
| H-24 | Cerrado | Dirección + cantidad mayores de 65536 responden excepción 02. Con prueba | firmware |
| H-25 | Pendiente (bajo) | Validar rangos de `A k valor` y de la hora más allá de 2038 | firmware |
| H-26 | Cerrado | La consola USB no bloquea más de 20 ms por una línea sin salto | firmware |
| H-27 | Cerrado | CLKOUT del reloj apagado al ajustar la hora | firmware |
