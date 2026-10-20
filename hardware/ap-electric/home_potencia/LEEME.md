# AP Home POTENCIA rev A (CONCEPTO)

La parte de **127 V CA** de AP Home, sin el cerebro. Va en la caja de registro o junto a la luminaria. Es el mismo circuito y el mismo trazado de red que AP Home rev A (relé Omron G2RL-1A-E-HA de 5 V, fuente Mean Well IRM-03-5 aislada con fusible T2A y varistor 10D471K, entrada de apagador de red con LTV-814S), con 6.0 mm en el aire y 6.4 mm por la superficie entre la red y la baja tensión.

> **Estado: CONCEPTO.** ERC 0, DRC 0 (con las reglas de aislamiento de red), sin pistas sin unir, paridad 0, reglas de fabricación 0 y pedido «sin errores». **Nada fabricado ni medido; sin certificación; el límite de carga sigue por determinar.** Instalación por una persona competente con el circuito desenergizado.

| | |
|---|---|
| Tamaño | **55 × 68 mm** (la original de una pieza medía 55 × 80) |
| Piezas | 12 tipos, 14 piezas; pedido completo ~21 USD de cargo por 7 tipos Extended; económico ~6 USD con 6 piezas de patas a mano |
| Bornes de red | L, N, LS (fase a la lámpara) y SW (fase que regresa del apagador; entrada de **red**, no contacto seco) |
| Cable al cerebro | JST XH de 4 hilos: 5 V · 0 V · RELE · SWO (ver [home_cerebro](../home_cerebro/LEEME.md)) |
| Sin cerebro | el relé queda apagado (pull-down de 10 kΩ) y el apagador sigue sin energía de control |

## ¿Se puede achicar más? Lo que se buscó (octubre 2026)

- **Fuente:** la Hi-Link HLK-PM01 (5 V, 3 W) es C209903 en LCSC (otra página la lista como C917667: confirmar), de **34 × 24 mm** de huella; la Mean Well IRM-02-5 (5 V, 2 W, 400 mA) mide unos **33.7 × 22.2 mm** y no encontré un código LCSC. La IRM-03-5 de ahora ocupa unos 38 mm de largo. Es decir: el cambio ahorra **solo unos 4 mm**, y la IRM-02-5 (400 mA) deja menos margen para el relé y el ESP32 que la de 600 mA. No lo aplico.
- **Relé:** no encontré con código LCSC un relé de 5 V, SPST y 10 A más chico que el Omron G2RL (los de la familia Hongfa HF115F que aparecen son de 2 polos y 8 A, de 29 × 12.7 mm; el Hongfa HF33F de 20.5 × 10.2 × 15.3 mm no mostró código LCSC).
- **Conclusión:** con piezas aisladas y verificadas, la parte de red no baja mucho de 55 × 68 mm. Achicarla de verdad exige otra solución de alimentación (por ejemplo un módulo de fuente más delgado o montado de canto) y su evaluación de seguridad, que no está hecha. **No se debe quitar el aislamiento para ganar tamaño** (nada de fuente capacitiva).

## Límites

- Sigue siendo la pieza grande: la fuente IRM-03-5 (38 mm de largo) y el relé G2RL mandan el tamaño. Para que quepa en una chalupa hay que cambiar la fuente y el relé por otros más chicos (ej. otro relé de 5 V de menos altura y una fuente de 2 W), con su propia verificación de aislamiento; **no está hecho**.
- Aislamiento: el cable al cerebro lleva solo baja tensión (la fuente es aislada), pero hay que tender el cable de baja tensión separado de la red dentro de la caja.
- Sin función de seguridad ni protección contra falla a tierra.

Regenerar: `bash ../../tools/rutear.sh ap-electric/home_potencia AP_HOME_POTENCIA` (desde `hardware/`).
