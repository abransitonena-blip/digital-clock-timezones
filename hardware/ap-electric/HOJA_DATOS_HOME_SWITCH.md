# AP Electric · Home Switch: hoja de datos preliminar

> **Estado: CONCEPTO.** La misma placa AP Home rev A que el Home Plug (otro SKU: otra caja, bornes y entrada de apagador habilitada). Origen de cada valor: [R] · [C] · [E] · [M] (ninguno) · [A] (ninguno) · **PD**.

| | |
|---|---|
| Función | Controla un circuito de alumbrado de 127 V CA conservando el apagador de pared |
| Instalación | **Fija**, por una persona competente, con el circuito desenergizado. No es «enchufar y usar» |
| Requiere | Fase y **neutro** en la caja. Va en una caja de registro o junto a la luminaria; la placa mide 55 × 80 mm y **no cabe en la chalupa del apagador** |

## Bornes

| Borne | Conexión |
|---|---|
| **L** | Fase de la instalación |
| **N** | Neutro |
| **LS** | Fase a la lámpara (pasa por el relé) |
| **SW** | Fase que regresa del apagador |

**SW es entrada de red, no contacto seco.** Unos 0.64 mA a 127 V [C], por 2 × 100 kΩ y el optoacoplador LTV-814S (5 kVrms [E]). Por eso:
- no se conecta ahí nada de baja tensión;
- no se ofrece un SKU con contacto seco en el mismo borne.

## Apagadores compatibles

| Arreglo | Modo | Qué hace |
|---|---|---|
| Apagador sencillo (de palanca) | INTERRUPTOR | La luz sigue a la palanca; además se puede mandar desde el botón o la red |
| Botón de timbre (retorno) | PULSADOR | Cada toque alterna |
| **Escalera** (dos apagadores de 3 vías) | CONMUTADOR | Los dos apagadores conservan su función: su salida común va a SW y cada cambio de cualquiera alterna la luz (ver `INSTALACION.md`). Los viajeros no van a ningún pin del microcontrolador |
| Sin neutro en la caja del apagador | **No soportado** | Sería otro SKU con evaluación de fugas, parpadeo y compatibilidad LED |

## Eléctrico

Mismos valores que el [Home Plug](HOJA_DATOS_HOME_PLUG.md):
- alimentación de 127 V CA 60 Hz [R];
- fuente IRM-03-5 [E];
- relé G2RL-1A-E-HA [E];
- carga máxima **PD** (meta 6 A de alumbrado [R]);
- protección de la carga por el interruptor del circuito (obligatoria).

| Entrada SW | Valor | Origen |
|---|---|---|
| Umbral | PD | |
| Retardo de detección | ≤ 25 ms + antirrebote de 30 ms | [C] |

## Comportamiento y certificación

| | |
|---|---|
| Comportamiento | Igual que el Home Plug. El apagador manda una orden: si el equipo está en falla o sin energía, el apagador **no** enciende la luz. Un bypass físico no se ofrece |
| Certificación | Ninguna. Por estudiar: IEC 60669-2-1 (interruptores electrónicos, ≤ 250 V CA, ≤ 16 A; sin «full off-state» sin interruptor mecánico), NOM-003-SCFI-2014 y NMX, y homologación de radio |
