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

## Límites

- Sigue siendo la pieza grande: la fuente IRM-03-5 (38 mm de largo) y el relé G2RL mandan el tamaño. Para que quepa en una chalupa hay que cambiar la fuente y el relé por otros más chicos (ej. otro relé de 5 V de menos altura y una fuente de 2 W), con su propia verificación de aislamiento; **no está hecho**.
- Aislamiento: el cable al cerebro lleva solo baja tensión (la fuente es aislada), pero hay que tender el cable de baja tensión separado de la red dentro de la caja.
- Sin función de seguridad ni protección contra falla a tierra.

Regenerar: `bash ../../tools/rutear.sh ap-electric/home_potencia AP_HOME_POTENCIA` (desde `hardware/`).
