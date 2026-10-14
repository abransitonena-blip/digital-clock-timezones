# Estudio de diseño de la rev C del 7R Tour (y qué cabe en una rev B1)

> **Estado:** estudio de gabinete (2026-10-14). No se fabricó ni se midió nada; no se tocó ningún archivo de diseño. Es una **propuesta con cálculos**, no un diseño cerrado. Ningún producto de AP es una función de seguridad.
> Autor del área: `ap-hardware` (modo estudio). Cálculos: [calc_entradas_rev_c.py](calc_entradas_rev_c.py) (`python3 -I calc_entradas_rev_c.py`).

## 0. Marcas y límites de las fuentes (leer antes de usar las cifras)

| Marca | Significado en este documento |
|---|---|
| `[R]` | Dato del repositorio (`make.py`, `jlcpcb.py`, `jlcpcb_catalogo.csv`, otros `.md`) |
| `[E*]` | Dato de una hoja de datos **citado en un extracto de buscador o de un distribuidor**. **No pude descargar los PDF completos**: el proxy de la sesión niega `jlcpcb.com`, `mouser.com`, `lcsc.com`, etc. (403/NXDOMAIN al intentar). Ningún `[E*]` está comprobado contra la hoja completa |
| `[C]` | Cálculo propio, reproducible (script o aritmética escrita) |
| `[CG]` | Conocimiento general sin verificar |
| `[H]` | Hipótesis por validar |
| `PD` | Por determinar |

Reglas que apliqué: no hay códigos LCSC inventados. Los que aparecen vienen del catálogo del repositorio `[R]` o de una página de distribuidor que el buscador devolvió, y llevan **«código LCSC por verificar»** (existencias, clase Basic/Extended y huella se revisan al pedir). Datos que faltan: se dicen en cada sección y se juntan en §10.

Lo que **no encontré** y condiciona todo: (1) la hoja completa del LTV-217 (solo extractos y el catálogo `[R]`: 70 V, 3 kV, 50 mA, VF 1.2 V, Vce(sat) 0.4 V a 2.4 mA/8 mA); (2) tr/tf del LTV-217; (3) la hoja del CA-IS3092W (umbral del receptor); (4) los dibujos mecánicos de la huella del LTV-354T frente al LTV-217.

---

## 1. Punto de partida: lo que hace hoy la entrada (rev B)

Esquema de una entrada (de `make.py`, refs `RAk, RB(k+2), LIk, RSk, DIk, OKk, RPk`):

```
IN ──RA 2.2k──RB 2.2k──┬── LI (LED verde, A→K) ──┬── IL ──┬─ OK pin1 (ánodo LED)
                       │                          │        └─ RS 2.2k ── COMI
                       └── DI 1N4148W (K en IB, A en COMI)      OK pin2 (cátodo) ── COMI
OK pin4 (colector) = Ek ──RP 10k── 3V3 ──► TCA9554 (0x21) ; Ek1/Ek2 también a IO0/IO20
OK pin3 (emisor) = GND
```

El sensor PNP da +24 V a IN y su 0 V va a COMI. **El LED del opto solo conduce IN→COMI**; la corriente inversa pasa por DI. Por eso un NPN no sirve. `[R]`

Hechos que el estudio usa (verificados leyendo `make.py`):

1. **Un solo común (COMI)** para las 8 entradas (J13 pin 3). Con entradas bipolares, el tipo de sensor lo decide *cómo se cablea COMI*: a 0 V para PNP, a +24 V para NPN. **Todas las entradas de una placa serían del mismo tipo** (no se puede mezclar PNP y NPN) mientras haya un solo COMI. `[C]` (confirmado con la lógica de cableado de PLC: https://industrialmonitordirect.com/blogs/knowledgebase/npn-vs-pnp-sensors-plc-input-wiring-guide , consultado 2026-10-14; esa fuente es un blog de un distribuidor, no un fabricante de PLC).
2. **No hay bornes de +24 V para sensores** en la placa: el +24 V del sensor viene de afuera.
3. **El ESP32-C3-WROOM-02 no tiene pines libres**: `make.py` usa IO0, IO1, IO2, IO3, IO4, IO5-IO7 (tres LED), IO8, IO9 (MODO), IO10, IO18-IO19 (USB) e IO20. Solo queda sin conectar el pad 12 (supongo IO21/U0TXD, `[H]`: la tabla de pines del módulo no se descargó). Expansores: U2 P7 = identificación, U3 completo (entradas), U4 completo, **U5 P7 libre**. Dirección I2C ocupadas: 0x20-0x23 y 0x51 (RTC). `[R]`
4. **Cobertura de umbrales actual (modelo propio).** La hoja de datos del producto dice «encendida > ≈ 11 V, apagada < ≈ 5 V, 4.8 mA». Mi modelo (script, `O0`) da: 4.71 mA a 24 V, **encendida garantizada desde 7.2 V** (con CTR mínimo) y **apagada garantizada solo hasta 5.26 V** (con CTR máximo de la banda). Es decir, el margen sobre «apagada < 5 V» es de **0.26 V**, muy apretado, y depende de supuestos `[H]` (VIL del TCA9554 = 0.3 VCC `[CG]`, banda CTR máxima 260 % `[CG]`). En 5 V la entrada toma 0.49 mA `[C]`, en el límite de los 0.5 mA que recuerdo para el tipo 1 de IEC 61131-2 `[CG]`. **Es un hallazgo para medir en la primera tanda, no una falla probada.**

### Supuestos del modelo (todos reproducibles en el script)
- IC necesaria para llevar la línea de 3.3 V (pull-up 10 kΩ) a VIL = 0.99 V: (3.3 − 0.99)/10 k = **0.231 mA** `[C]`.
- LED infrarrojo: 1.2 V a 5 mA `[R catálogo]`, idealidad 2 `[H]`. LED verde: 2.0 V a 2 mA `[H]`. 1N4148W: 0.72 V a 5 mA `[H]`.
- CTR mínimo garantizado: LTV-217: 50 % a IF = 5 mA, VCE = 5 V `[E*]` (https://jlcpcb.com/partdetail/LiteOn-LTV_217_BG/C115450 y extracto de la hoja Lite-On DS70-2009-0016). LTV-354T: 20 % a ±1 mA, VCE = 5 V `[E*]` (https://optoelectronics.liteon.com/upload/download/DS70-2001-004/LTV-354T%20series%20201610.pdf). CTR máximo de la banda: 260 % (217-B) y 300 % (354T, rev J: banda 100-300 %) `[CG]/[E*]`. **El CTR cae con IF bajo, con la temperatura y con la edad (`[CG]`): el modelo es optimista en el lado de «encendida».**

---

## 2. (a) Entradas bipolares: PNP, NPN y contacto seco de 24 V sin cambiar la placa

### 2.1 Cómo se cablea cada caso con una entrada bipolar (corriente en cualquier sentido entre IN y COMI)

| Fuente de señal | IN va a | COMI va a | Corriente por la entrada |
|---|---|---|---|
| Sensor PNP (de 3 hilos) | salida del sensor | 0 V de la fuente del sensor | IN → COMI |
| Sensor NPN (de 3 hilos) | salida del sensor | **+24 V** de la fuente del sensor | COMI → IN |
| Contacto seco con 24 V | un lado del contacto (el otro a +24 V) | 0 V | IN → COMI |
| Contacto seco con 24 V (variante) | un lado (el otro a 0 V) | +24 V | COMI → IN |
| Sensor de 2 hilos (CA/CC) | — | — | **No cubierto**: su fuga en reposo (hasta ≈ 1.5 mA `[CG]`) se lee como «encendido» (a 1.5 mA la entrada ya vio ≈ 8-10 V en todas las opciones) |

**Importante:** el contacto seco es «seco» respecto de la placa, pero necesita su propia fuente de 24 V; una corriente de 4-6 mA por entrada (§2.4) es suficiente para la corriente mínima de «mojado» típica de contactos (`[CG]`, PD).

### 2.2 Opciones evaluadas

Todas las cifras de umbral vienen del script (`ENTRADAS`). «Von garantizada» = tensión a la que aun la pieza de CTR mínimo ya lee «activa». «Voff garantizada» = tensión por debajo de la cual aun la pieza de CTR máximo lee «inactiva». Meta de diseño de la hoja de datos: Voff ≥ 5 V y Von ≤ 11 V (tipo 3) o ≤ 15 V (tipo 1) `[CG]`.

| Opción | I a 24 V | Von gar. | Voff gar. | I a 5 V | P a 24 V | Cumple 5 V / 11 V |
|---|---|---|---|---|---|---|
| **O0** rev B (hoy), solo PNP | 4.71 mA | 7.20 V | 5.26 V | 0.49 mA | 113 mW | sí / sí (margen 0.26 V) |
| **O1** puente + LTV-217 + LED serie, mismas R | 4.39 mA | 8.49 V | 6.50 V | 0.30 mA | 105 mW | sí / sí |
| **O1b** igual con R 3.9 k y RS 1.5 k | 4.95 mA | 8.95 V | 7.11 V | 0.36 mA | 119 mW | sí / sí |
| **O2** opto CA (LTV-354T), mismas R, sin LED serie | 5.18 mA | 8.45 V | **3.29 V** | 0.89 mA | 124 mW | **no** (Voff < 5 V) |
| **O2b** opto CA, R 4.7 k, RS 1.0 k | 4.85 mA | 11.84 V | 5.97 V | 0.88 mA | 117 mW | sí / ≈ (11.8 V, casi tipo 3) |
| **O2e** opto CA con LED serie antiparalelo, R 3.9 k, RS 1.0 k | 5.32 mA | 12.02 V | 7.07 V | 0.63 mA | 128 mW | sí / ≈ |
| **O2f** (B1 solo BOM): opto CA, LI→0 Ω, 2.2 k + 2.4 k, RS 1.0 k | 4.96 mA | 11.61 V | 5.87 V | 0.89 mA | 119 mW | sí / ≈ |
| **O3** dos LTV-217 antiparalelo, sin LED serie, R 4.7 k, RS 2.2 k | 4.85 mA | 5.55 V | **3.53 V** | 0.84 mA | 116 mW | **no** |
| **O3b** igual con RS 1.5 k | 4.85 mA | 6.62 V | **4.52 V** | 0.85 mA | 116 mW | **no** (justo) |
| **O5** rev B + pull-up externo 1 kΩ a +24 V (NPN, lógica invertida) | 3.85 mA (sensor apagado) | 8.16 V | 5.80 V | — | 92 mW | sí |

Leyenda de lo que cambia al pasar a bipolar: quitar el LED serie baja los umbrales unos 2 V (O2, O3), por eso hay que **subir el umbral con un RS menor** (más derivación). Con el puente (O1) se suman dos caídas de diodo y el umbral *sube* ≈ 1.3 V; funciona con las mismas R.

#### O1: puente rectificador + LTV-217 (se conserva el opto validado)
```
IN─RA─RB─┬── BAV99 #1 (pin3=nodo A) ──┐         ┌─ LED verde LI ─ OK(LED) ∥ RS ─┐
         │                             ├─ rail + ─┘                              ├─ rail −
COMI ────┴── BAV99 #2 (pin3=nodo B) ──┘                                         │
```
Un puente de 2 × BAV99 (SOT-23, cada uno con dos diodos en serie: pin1 = rail −, pin3 = punto medio a IN/COMI, pin2 = rail +) o 4 × 1N4148W (SOD-123) o un puente integrado MB10S (huella MBS, 4.7 × 3.8 mm `[R catálogo]`).
- Corriente y umbral: tabla (O1/O1b).
- Códigos del repositorio `[R catálogo]`: BAV99,215 **C2500 Basic** 0.012 USD; 1N4148W **C81598 Basic** 0.013 USD (ya en el BOM como DI); MB10S **C2488 Basic** 0.029 USD. Todos son Basic: **sin cargo de tipo extendido** `[R jlcpcb.py]`.
- Conserva el LED indicador en serie (se enciende en ambos sentidos) y la protección contra inversión (el LED nunca ve tensión inversa).
- Pérdidas: 2 caídas de diodo (≈ 1.4-1.5 V) `[H]`; la entrada pierde ≈ 1.4 V de margen en tensión mínima pero la tabla muestra que sigue cumpliendo.
- Costo relativo: +8 × (2 × 0.012 − 0.013) ≈ **+0.09 USD** de piezas por placa `[C, R]`; +1 pieza (2 BAV99 por 1 DI) por canal ⇒ **+8 piezas** a colocar. La **huella cambia** (DI SOD-123 → dos SOT-23): es **rev C** (no cabe sin reacomodar la columna de 5.9 mm).
- Riesgo: bajo en componentes (todos Basic y de uso común), medio en espacio.

#### O2: optoacoplador bipolar (LED antiparalelo interno) en la misma caja SOP-4
- **Familia de la misma caja:** Lite-On **LTV-354T** (entrada CA, «mini-flat» 4 pines, 3.75 kVrms, CTR mínimo 20 % a ±1 mA, rango −55/+100 °C) `[E*]` https://optoelectronics.liteon.com/upload/download/DS70-2001-004/LTV-354T%20series%20201610.pdf (la hoja Lite-On DS70-2001-004; solo vi portada y encabezados). Everlight **EL354** (misma función, 4-SOP, ±50 mA, 80 V, pin 4 = colector, pin 3 = emisor `[E*]`) https://www.mouser.com/datasheet/2/143/evers02575_1-2266814.pdf ; **no encontré página de LCSC del EL354**: «no encontrado».
- **Códigos LCSC por verificar:** LTV-354T de Lite-On **C119090** (Extended, SOP-4) https://jlcpcb.com/partdetail/LiteOn-LTV354T/C119090 ; LTV-354T de UMW **C2841485** (Extended, «SOP-4-2.54mm») https://jlcpcb.com/partdetail/3024121-LTV354T/C2841485 ; LTV-354T-A **C10802** https://www.lcsc.com/product-detail/C10802.html. Los listados difieren en VF (1.2 vs 1.4 V), tr/tf (4/3 µs vs 18/18 µs) y CTR máximo: **hay que leer la hoja Lite-On con la sufijo exacto**.
- **No es el LTV-814:** el LTV-814S del repositorio (`C108051`, Home) es **SMDIP-4 de 9.53 mm** `[R]`, otra huella; **no cabe** en OK1-8. Debe corregirse la nota de `PUESTA_EN_MARCHA.md` (dice «misma caja SOP-4 (pendiente)»). tr/tf del LTV-814: 4/3 µs típ., 18/18 µs máx. `[E*]` https://au.rs-online.com/web/p/optocoupler-ics/6912091 .
- **Compatibilidad de huella: pendiente `[H]`.** KiCad usa `SOP-4_4.4x2.6mm_P1.27mm` para el LTV-217; la página de LCSC describe al 217 como «SOP-4-175mil» y al 354T como «SOP-4-2.54mm». Probablemente son lo mismo (separación de 2.54 mm entre los pines 1-2 y 3-4), pero **hay que superponer los dibujos mecánicos** antes de prometer que es un cambio solo de BOM.
- **Efecto en el esquema:** el LED ya no puede ir en serie «unidireccional»: LI y DI deben salir. En B1 solo de BOM: LI → resistencia de 0 Ω 0603 (pierde el LED), DI sin montar, RA/RB = 2.2 k + 2.4 k, RS = 1.0 k (opción O2f). En rev C: LED indicador antiparalelo en serie (dos 0603, o uno bicolor) como O2e, o abandonar el indicador (el programa muestra el estado).
- **Indicador en el lado lógico, no sirve:** un LED de 1 mA en el colector sube la IC necesaria a ≈ 1.3 mA y, con CTR mínimo 20 %, exigiría IF ≥ 6.5 mA `[C]`. Descartado.
- Corriente/umbral: O2b, O2e, O2f (tabla). O2 con las R actuales **no cumple** el umbral de 5 V (Voff = 3.3 V); necesita RS ≈ 1.0 kΩ.
- Costo relativo: pieza Extended ⇒ cargo de tipo ≈ 3 USD por pedido `[R, comentario de jlcpcb.py]` (≈ +0.6 USD/placa con 5 placas) + precio de la pieza **PD** (el catálogo del repositorio no la trae). Se pierde el LTV-217 Basic (0.064 USD `[R]`).
- Riesgo: medio-bajo: sin cambio de PCB si la huella coincide; la dispersión de CTR (20 % a 300 %) hace amplio el umbral de conmutación; la fuga de sensores de 2 hilos sigue sin cubrirse.

#### O3: dos LTV-217 con LEDs antiparalelos y colectores en paralelo
Cada LED ve una polaridad; los colectores unidos (cualquiera que conduzca baja Ek). Código ya conocido (C115450, Basic). Necesita **otra huella SOP-4 por canal** (4.4 × 2.6 mm): rev C. Con 4.7 k/2.2 k no cumple el umbral de 5 V; con RS 1.5 k queda en 4.52 V (justo). Costo: +8 × 0.064 = **+0.51 USD** de piezas. Riesgo: alto de espacio, bajo eléctrico. **No recomendada** (O1 resuelve lo mismo con piezas más baratas).

#### O4: entrada de corriente constante
Puente + limitador de corriente (por ejemplo, un NPN pequeño como BC847 con una resistencia: I ≈ Vbe/R ≈ 0.6 V/220 Ω ≈ 2.7 mA `[C]`) + el opto y un zener de umbral. Ventajas: corriente igual de 11 a 30 V (consumo y EMC mejores, curva tipo 3 más limpia). Desventajas: 5-7 piezas por canal, el umbral lo fija la suma de un zener y las uniones (deriva con la temperatura), y la parte de disipación del limitador a 30 V. Integrados industriales de 8 entradas, p. ej. **MAX22190** (octal, 24 V, tipo 1/2/3 por resistencia, filtro programable por canal, detección de cable roto, 7-65 V de campo, TQFN 5 × 5 mm, SPI) https://www.mouser.com/maxim-max22190-input/ `[E*]`: son entradas **sumidero** (una polaridad) y necesitan 3-4 pines SPI que el C3 no tiene; **no resuelven NPN/PNP por sí solos**. **Descartada para la rev C**, se deja anotada para una futura placa con S3.

#### O5: lo que se puede hacer *hoy* con la rev B (sin cambiar la placa)
Para un sensor NPN con COMI a 0 V: una resistencia externa de 1.0 kΩ entre IN y +24 V. Con el NPN apagado la entrada ve 24 V a través de 1 kΩ + 4.4 k ⇒ 3.85 mA, se lee «activa»; con el NPN encendido IN cae a ≈ 0.2 V y se lee «inactiva». Es **lógica invertida**: el firmware necesita un indicador de inversión por entrada (`grep` de `firmware/APControl/*.h` no encuentra ninguno) `[R]`. El NPN sinke 24 V/1 kΩ = 24 mA `[C]` (típico de un sensor: 100-200 mA máx. `[CG]`); la resistencia disipa 15 mW. Sirve para validar NPN en la primera tanda con costo cero de hardware, pero **no es un producto** (cableado externo, riesgo de olvido).

### 2.3 Efecto sobre el conteo rápido a 500 Hz (E1/E2 → IO0/IO20)
Período 2.0 ms; semiperíodo (50 % de trabajo) **1.00 ms** `[C]`. Presupuesto:

| Elemento | Valor | Origen |
|---|---|---|
| tr/tf del opto con RL = 100 Ω, IC = 2 mA | LTV-354T: típ. 4/3 µs, máx. 18/18 µs (listados que se contradicen: Mouser 18/18 µs, TME 4 µs/18 µs, UMW 6/8 µs) | `[E*]` |
| Carga real: pull-up 10 kΩ, IC útil ≈ 0.33 mA, IF ≈ 4-5 mA | el transistor trabaja **saturado a fondo** (factor de exceso 7-36×) ⇒ aparece **tiempo de almacenamiento** en el apagado | `[C]` + `[H]` |
| Retardo estimado de apagado (almacenamiento) | **20-100 µs** | `[H]` (no hay dato; medir) |
| Subida del colector con RP = 10 kΩ y 20 pF | 0.2 µs | `[C]` |
| Distorsión de ancho de pulso supuesta | ≈ (t_apagado − t_encendido) ≤ 100 µs = **≤ 10 % del semiperíodo** | `[C/H]` |

Conclusión `[H]`: a 500 Hz el opto no es el límite, **pero la cifra de 20-100 µs hay que medirla** (§9). Para los canales rápidos 1-2:
- **No poner capacitor de filtro** de más de 1 nF en el colector: con CF en el colector la subida a VIH (0.7 VCC) vale t = −RP·(CF + 20 pF)·ln(0.3): **1 nF → 12 µs (1.2 %)**, **10 nF → 121 µs (12 %)**, **100 nF → 1.2 ms (120 %, deja de contar)** `[C]`.
- Filtro en el lado de entrada (C en paralelo con el LED, cargado por 4.4 k): 10 nF → τ = 44 µs; 100 nF → 0.44 ms; 220 nF → 0.97 ms `[C]`: 100 nF ya come el 44 % del semiperíodo. **Solo para canales lentos** y con condensador de ≥ 50 V.
- **Antirrebote por hardware no hace falta en los canales rápidos**: los sensores de estado sólido no rebotan y un contacto mecánico no llega a 500 Hz `[CG]`. Un contacto seco rebota 1-10 ms `[CG]`: eso se resuelve con el **antirrebote del programa** (hoy 30 ms por omisión, 5-2000 ms ajustable `[R]`). Para IO0/IO20 conviene añadir al programa un **tiempo muerto configurable de 0.1-0.5 ms** (menos de la mitad del semiperíodo mínimo) en la interrupción, en lugar de hardware.
- El histeresis del TCA9554 y del GPIO del C3 no está confirmada `[PD]` (hoja del TCA9554 no leída): por eso se evitan constantes de tiempo largas en los canales rápidos.

### 2.4 Consumo
8 entradas activas a 24 V: 8 × (105-128 mW) ≈ **0.84-1.0 W** `[C]`. Esa corriente (≈ 4-5 mA por canal, ≈ 40 mA en total) **sale de la fuente del sensor, no del J9** (la placa no alimenta sensores) `[R]`; el consumo de la placa (≈ 0.15 A, 3.6 W `[R]`) no cambia. A 30 V cada resistencia de 2.2 k disipa ≈ 81 mW de los 125 mW de un 0805 `[C, CG]`.

### 2.5 Mezclar PNP y NPN en la misma placa (hallazgo de diseño)
Con un solo COMI **no se pueden mezclar**. Para la rev C: **dos comunes** (COMA para I1-I4, COMB para I5-I8). Eso exige 10 polos de entrada en vez de 9: J13 pasaría a 4 polos (código **por verificar**; el KF128 de 4 polos no está en `CONOCIDOS`). Costo: un borne más y 1-2 pistas. Riesgo: bajo. **Recomendada para rev C.**

### 2.6 Qué dato falta
Hoja completa del LTV-217 (CTR por banda a IF bajo, tr/tf, VR del LED); hoja del LTV-354T con el sufijo comprado; dibujo mecánico de ambas huellas; VIL/VIH reales del TCA9554 y del GPIO IO0/IO20; fuga de los sensores PNP/NPN de la planta piloto.

---

## 3. (b) Memoria no volátil para la bitácora

Hoy: bitácora en RAM, se pierde al apagar (`ANALISIS_ECOSISTEMA.md`); el firmware ya usa `Preferences` (NVS en flash interna) para configuración `[R]`.

| Opción | Capacidad | Resistencia a escritura | Tiempo de escritura | Referencia (código LCSC por verificar salvo `[R]`) | Costo relativo |
|---|---|---|---|---|---|
| **FRAM I2C** Fujitsu/RAMXEED **MB85RC256V** | 32 KB | ≥ 10¹² ciclos por byte; retención 10 años a 85 °C; 2.7-5.5 V; Icc ≤ 200 µA a 1 MHz, espera 27 µA típ. `[E*]` https://www.mouser.com/datasheet/2/1113/MB85RC256V_DS501_00017_7v0_E-2329117.pdf | Sin espera de escritura (a velocidad del bus) | **no encontré página LCSC**; no está en `jlcpcb_catalogo.csv` `[R]` | PD (el catálogo no la trae) |
| **FRAM I2C** Infineon **FM24CL64B-GTR** | 8 KB | no verificado en esta sesión | — | **C9829** (página de LCSC devuelta por el buscador: «64Kbit 2.7V~3.65V 1MHz I2C SOIC-8-150mil») https://www.lcsc.com/product-detail/C9829.html | PD (clase Basic/Extended: no vista) |
| **EEPROM I2C** AT24C256C-SSHL-T | 32 KB | ~10⁶ ciclos `[CG]` | ≈ 5 ms por página `[CG]` | **C6482** Preferred, 0.391 USD `[R]` | media |
| **EEPROM I2C** M24C64-RMN6TP | 8 KB | ~10⁶ `[CG]` | ≈ 5 ms `[CG]` | **C79988** Preferred, 0.119 USD `[R]` | baja |
| **Flash NOR SPI** W25Q128JVSIQ | 16 MB | ~10⁵ borrados por sector `[CG]` | ms por sector | **C97521** Basic, 0.896 USD `[R]` | media; pide 4 pines SPI que no hay |
| **Flash interna** del módulo (LittleFS/NVS con nivelación) | PD (partición) | ~10⁵ por sector `[CG]` | ms | ya en la placa | **0** |

Cálculos `[C]` (cifras de entrada: 10¹² de la FRAM `[E*]`, 10⁶ de EEPROM `[CG]`):
- Registro de 16 B por evento ⇒ 32 KB = **2048 registros**.
- Si el puntero de cabeza se reescribe en cada registro: FRAM a 100 escrituras/s dura 10¹²/100 = 10¹⁰ s = **317 años**; a 500/s, **63 años**. EEPROM a 1 escritura/s: 10⁶ s = **11.6 días** ⇒ no sirve para contador ni puntero sin esquema de rotación.
- Escritura de un registro de 16 B + dirección (19 bytes × 9 relojes ≈ 171 pulsos) a 400 kHz ≈ **0.44 ms** `[C]` ⇒ ≈ 2290 registros/s como máximo teórico (FRAM, sin espera). En EEPROM: 5 ms ⇒ máx. 200/s.
- Flash interna: 256 registros por sector de 4 KB; a 1 registro cada 10 s, un sector se llena en 43 min; con 100 sectores (400 KB) la vida supera 10⁹ registros `[C]`: **suficiente**; el riesgo no es la capacidad ni el desgaste, es **perder el búfer de RAM sin vaciar** al cortar la alimentación.
- Respaldo ante corte: los capacitores de 24 V (C1+C2+C11 = 30 µF) sostienen ≈ 30 µF × (24 − 9 V)/0.1 A ≈ **4.5 ms** `[C, con 0.1 A supuesto]`; basta para un registro de FRAM (0.44 ms) pero **no** para borrar un sector de flash (ms a decenas de ms `[CG]`). La detección del corte necesita un pin: ninguno libre en el C3; usar **U5 P7** (expansor libre) a través de la interrupción compartida IO4: latencia estimada ≈ 1 ms `[H]`.
- Compatibilidad: FRAM y EEPROM I2C comparten pinout SOIC-8 de 24Cxx `[CG]`; **una huella SOIC-8 sirve para ambas** (dirección 0x52-0x57 para no chocar con el PCF8563 en 0x51 `[CG]`).

**Recomendación (b):** rev B1: **bitácora en flash interna con vaciado periódico** (solo firmware). Rev C: huella SOIC-8 compatible con FRAM/EEPROM + línea de aviso de corte (U5 P7) para guardar contadores sin pérdida. Elegir FRAM solo si el cliente exige contadores sin pérdida ante corte; para bitácora de eventos la EEPROM o la flash bastan.

---

## 4. (c) Opción Ethernet (variante, no el diseño base)

Datos: las rutas soportadas por ESP-IDF son **MAC interno (solo RMII)** o **módulo SPI externo** https://docs.espressif.com/projects/esp-idf/en/latest/api-reference/network/esp_eth.html `[E*]` (consultado 2026-10-14). Qué chip tiene EMAC no lo confirmó la búsqueda: por conocimiento general, ESP32 y ESP32-P4 sí; C3 y S3 no `[CG]`. Driver W5500 de Espressif: https://components.espressif.com/components/espressif/w5500 `[E*]`. Hay un caso comunitario de ESP32-C3 + W5500 (SPI a 25 MHz, MOSI/MISO/SCLK/CS/RST/INT) https://github.com/BOlaerts/ESPHome-W5500-Ethernet-on-ESP32-boards y un hilo con W5500 + C3 sin «Link Up» https://esp32.com/viewtopic.php?p=133756 (sin solución visible): riesgo de integración.

| Opción | Pines que necesita | Cabe en la placa actual | Costo/espacio | Veredicto |
|---|---|---|---|---|
| **E1: W5500 por SPI en el C3** | SCLK, MOSI, MISO, CS (+ INT y RST deseables) = 4-6. Libres: IO21 + los 3 de LED (IO5-7) **si** los LED pasan a un TCA9554 nuevo (0x24). Sin INT (modo por sondeo) `[E*]` | **No**: el espacio, el RJ45 con magnéticos y la antena no caben en 176 × 90 mm; el corte de LED y la alimentación obligan a rev C | W5500 ≈ **132 mA a 3.3 V** `[E*]` (https://api.dl.sipeed.com/fileList/MAIX/HDK/Spmod_EN/SP-Ethernet%20Datasheet%20V1.0.pdf ; también «típ. 128 mA» en un módulo) ⇒ +0.44 W ⇒ ≈ +21 mA a 24 V (η = 0.85 supuesta) `[C]` (+12 % del consumo) | Variante posible, pero **no sin rev C** |
| **E2: módulo Ethernet «listo» (W5500 + RJ45) por cable** | 4-6 pines + 3.3 V | Cabe como **placa hija** en un conector (no es la placa base) | Costo del módulo PD | Mejor para una variante con carcasa más grande |
| **E3: ESP32 clásico/P4 con PHY RMII** | ≈ 9 señales RMII + reloj de 50 MHz | **No** | Cambia módulo, huella, CPL y firmware; el P4 no trae radio (necesita compañero) `[CG]` | **Descartada** |
| **E4: ESP32-S3** (más pines, USB nativo) + W5500 SPI | SPI + INT + RST sobran | Requiere rev C (módulo mayor `[CG]`) | Resuelve de una vez Ethernet, ADC y puntero de corte | **Recomendado si Ethernet y medición se piden juntos** |
| **E5: gateway externo RS-485→Ethernet (Modbus TCP)** | ninguno (usa el RS-485 aislado ya existente) | **Sí, hoy** | Equipo comercial o del catálogo AP; PD | **Preferida para el piloto** |

**Recomendación (c):** no cambiar la placa base. Para el piloto: **gateway externo** (E5). Si el cliente exige Ethernet en el equipo, hacerlo como variante con **ESP32-S3 + W5500** en una rev C específica, no con el C3. Aviso: el W5500 y su RJ45 elevan el EMC de la placa (ver §6).

---

## 5. (d) Medición de corriente: por canal y por placa

### 5.1 Por placa (corriente de 24 V)
- **Viable**: shunt de 0.1 Ω en serie con V24 y un amplificador/ADC por I2C. Piezas conocidas del repositorio `[R]`: **INA238 (C2868250, Extended)**, shunt **0R1 1206 (C25334, Basic)** o 1 mΩ 2512 (C2924520, Extended). Sin pines nuevos (bus I2C; dirección 0x40-0x4F libre). Ver https://www.ti.com/product/INA181 para la alternativa analógica (+ ADC externo, y el INA181 admite modo común de −0.2 a 26 V `[E*]`, **insuficiente para 30 V**, por eso el INA238 de 85 V).
- Cálculo `[C]`: con 0.1 Ω y 0.35 A máx. ⇒ 35 mV (dentro de ±163.84 mV del INA238 `[CG]`), 0.1 × 0.35² = **12 mW**; LSB = 5 µV/0.1 Ω = **50 µA** `[CG]`.
- Qué da: consumo total, detección de bobina abierta o cortocircuito de bobina, corriente de arranque. No da carga por canal.
- Por qué es **rev C**: requiere partir la red V24 (aguas arriba/abajo del shunt) y, en el SKU CA, también la rama de D3; los pours y los capacitores de 24 V se tendrían que rehacer. No es cambio de BOM.

### 5.2 Por canal (corriente de la carga)
Hallazgo: **los 7 canales son contactos secos con común independiente**; el lado de carga *no tiene referencia a GND*, por lo que un shunt + amplificador con la referencia de la placa **no funciona** (modo común indefinido, hasta 30 V o 250 V CA). Hacen falta:
1. **Sensor de efecto Hall con aislamiento** en la trayectoria de cada canal. Familias con página de distribuidor: **ACS723/ACS724** (Allegro; SOIC-8, ±10 A: 200 mV/A con cero en 2.5 V a 5 V; aislamiento citado 2.4 kVrms, trayectoria ≈ 1.2 mΩ `[E*]`) https://www.pololu.com/product/4047/resources , https://www.digikey.com/en/products/detail/allegro-microsystems/ACS723LLCTR-40AB-T/4915381 ; **TMCS1108** (TI, SOIC-8, 50-400 mV/A, ancho de banda 80 kHz, ±1 % típ. / ±3 % máx., **solo aislamiento funcional de ±100 V de trabajo**) https://www.ti.com/product/TMCS1108 `[E*]`. Todos con **«código LCSC por verificar»**: ninguno está en el catálogo del repositorio.
2. Un ADC por I2C (el repositorio ya usa ADS1115 **C37593 Extended** `[R]`); dos ADS1115 cubren 7 canales; la tasa agregada de 860 S/s `[CG]` alcanza para valor medio/pico de CC pero **no para valor eficaz de 60 Hz por canal** (≈ 123 S/s por canal en 7 canales).
3. **Aislamiento incompatible con la regla de diseño actual:** la regla `aislamiento_red` exige 6.4 mm entre las redes de contactos (`Red`) y todo lo demás; un SOIC-8 tiene sus pines de entrada y de salida a menos de 6.4 mm (el ancho del cuerpo es ≈ 3.9 mm `[CG]`). Habría que crear una excepción para el paquete y **ensayar** el aislamiento. Para cargas de red de 127/220 V, el TMCS1108 (±100 V de trabajo) **no sirve**; para el ACS72x el valor de «tensión de trabajo» no lo pude comprobar. Como el SKU CA está en pausa y el piloto 24DC conmuta cargas de baja tensión, el caso viable sería un **SKU 24DC específico** (sensores montados solo ahí).
4. Alternativa sin cambiar la placa: **realimentación por las entradas** (contacto auxiliar del contactor o relé de estado de la carga a I1-I8) y **medición externa** (pinza amperimétrica con salida a un módulo Modbus aparte). Cero costo de hardware.

| Opción | Viable en la huella actual | Costo relativo | Riesgo |
|---|---|---|---|
| Shunt + INA238 en V24 (por placa) | No (rev C) | bajo (≈ 3 piezas; INA238 Extended) | bajo |
| 7 × Hall + 2 × ADS1115 (por canal) | **No**: aislamiento y espacio | alto (7 sensores + 2 ADC) | alto |
| Shunt + amplificador por canal | **No** (contactos flotantes) | — | — |
| Realimentación por entradas / pinza externa | **Sí** | cero | bajo |

**Recomendación (d):** B1: nada. Rev C: solo el INA238 por placa y la reserva de huella SOIC-8 + 2 pads de potencia para un Hall en el SKU 24DC, **solo después** de tener la hoja del ACS72x/TMCS1108 y de decidir con clientes si la corriente por canal es un requisito `[H]`.

---

## 6. (e) EMC y protección

Lógica de cada mejora, con lo que ya hay `[R]`: SMBJ33A + F1 3 A + SS34 en serie en 24 V; SM712 en A/B; USBLC6 en USB; diodos de bobina en el ULN2003A; aislamiento RS-485 de 5 kVrms.

| Mejora | Dónde y por qué | Pieza del repositorio / familia | Costo | Fase |
|---|---|---|---|---|
| **TVS en cada entrada** | La entrada conmuta ±30 V sin protección más allá de las R en serie y el diodo (el opto tiene 70 V `[R]`); el TVS recorta transitorios de cable largo. Bidireccional entre IN y COMI | SMAJ33CA **C19077549** Preferred 0.038 USD `[R]` (clamp ≈ 53 V `[R]`) o SMAJ36CA C19077551 | 8 × 0.038 = **0.30 USD** `[C]`; 8 piezas en la columna ajustada de 5.9 mm: **no cabe en B1**. Alternativa: **un** TVS por COMI y **un** TVS compartido por banco | C |
| **Descarga del común COMI** | COMI queda flotando respecto de GND; un condensador alto voltaje + resistor lleva ESD/burst a GND sin pasar por la capacidad del opto | 1 nF/2 kV 1206 **C9196** Basic 0.011 USD `[R]` + 1 MΩ | ≈ 0.03 USD | C (verificar contra la prueba de aislamiento) |
| **RS-485: malla y puesta a tierra** | La malla va a GNDB (aislada); sin ruta, el ruido de modo común carga el aislador. Resistor 1 MΩ ∥ 1 nF 2 kV de GNDB al agujero de montaje (PE opcional) | C9196 | ≈ 0.03 USD | C |
| **RS-485: polarización con terminación** | Con JP1 cerrado (120 Ω) y 680 Ω en A y B: V diferencial = 3.3 × 120/(680 + 120 + 680) = **0.27 V** `[C]`, margen de solo 67 mV sobre un umbral de 200 mV `[CG]` (hoja del CA-IS3092W no leída) | Cambiar 680 Ω → 470 Ω ⇒ 3.3 × 120/(470 + 120 + 470) = 0.37 V `[C]` | 0 | **B1 (valores)** |
| **Filtro de entrada de 24 V** | El buck LMR16006 y el AP63203 radian y conducen; una cuenta de ferrita en serie con V24 después del TVS + capacitor | GZ1608D601TF **C1002** Basic 0.010 USD (600 Ω a 100 MHz, 450 mΩ) `[R]`; para corriente alta ver su límite en la hoja (**PD**) | ≈ 0.01 USD | C (preensayar) |
| **Ferrita en A/B del RS-485** | Atenúa RF; en 115 200 Bd no afecta la señal `[CG]`; no sustituye al TVS | C1002 (2 piezas) | ≈ 0.02 USD | C |
| **Puesta a tierra de la carcasa/PE** | La placa va en carcasa de plástico, sin PE; las 4 perforaciones de montaje podrían unirse a GND por R/C (pad 0603 opcional) para ensayos de ESD | — | 0 | C |
| **Supresor de contacto** | **Un RC en paralelo con el contacto *fuga* corriente por la carga abierta**: con 100 nF X2: I = V·2π·f·C = 127 × 2π × 60 × 100 nF = **4.8 mA** (127 V) y **8.3 mA** (220 V) `[C]`; una lámpara LED puede encenderse tenue. Por eso el supresor va **en la carga** (varistor o RC del fabricante de la bobina), como ya dice la hoja de datos | — | — | no cambiar |

Lo que **no** conviene tocar sin ensayo: el diodo serie SS34 (cae ≈ 0.4 V `[CG]`) y el SMBJ33A (el voltaje de disparo 36.7-40.6 V `[R catálogo]` es mayor que los 30 V del rango de diseño, margen estrecho con transitorios de la fuente).

---

## 7. (f) Mejoras de fabricación (JLCPCB)

Fuentes: tooling holes, rieles y fiduciales son **obligatorios en pedidos con ensamble**; si no los pone el cliente, JLCPCB los agrega; los rieles de ≥ 5 mm; los fiduciales suelen ir en los rieles https://api.jlcpcb.com/help/article/How-to-add-edge-rails/fiducials-for-PCB-assembly-order , términos de ensamble https://jlcpcb.com/help/article/61-Terms-and-Conditions-of-JLCPCB-Assembly-Service (consultadas 2026-10-14; **la especificación de diámetro, apertura de máscara y llaveo de los fiduciales de JLCPCB no la encontré**; las cifras de 1-3 mm y 3 fiduciales son de guías de terceros, `[CG]`).

| Tema | Propuesta | Lógica / riesgo | Fase |
|---|---|---|---|
| **Puntos de prueba** | Hoy 11 (24 V, 5 V, 3.3 V, 2 × GND, SDA, SCL, TX, RX, DE, EN) `[R]`. **Añadir**: **E1 y E2** (colectores de las entradas rápidas, las que se miden en el ensayo de 500 Hz), **COMI**, **GNDB**, **VISO**, **V24 tras D1**, **IO9/MODO**, **VRTC** | Los de E1/E2/COMI son los que hacen falta para validar el §2.3; sin ellos se mide con una pinza soldada a la pista | B1 (si hay cobre libre y pasa el DRC) / C |
| **Orientación y polaridad** | Marcar pin 1 en todos los CI (U1-U11), ánodo/cátodo en D1, D2 (SMBJ33A es unidireccional), D6, D7, LED; marca «+» en J9 y C1-C2; flecha de giro del DIP «ON»; en las polarizadas se revisa la orientación en «Component Placement» (`DISENO_FINAL.md` §4) | Evita giros de CPL; ya se hace parcialmente | B1 (solo serigrafía) |
| **Orientación uniforme** | Colocar todas las piezas SMD con rotaciones 0°/90° homogéneas y todas en la cara superior (comprobar `POS` en `make.py`) `[H]` | Ensamble en una sola cara; menos error de CPL | C |
| **Fiduciales y rieles** | Fiduciales locales (2 en esquinas opuestas, al menos) a 5 mm del borde; dejar libre 5 mm en los lados largos para que JLCPCB coloque rieles sin invadir el cobre; el contorno de 176 × 90 mm tiene esquinas de R = 2.0 mm `[R]` | Si no se ponen, JLCPCB los añade (con cargo si hay que retirarlos) `[E*]` | C (o B1 con pocos cambios) |
| **Panelización** | Para 5 placas de piloto, panel de JLCPCB con rieles; para producción, panel de 2 en columna con unión «mouse-bite» (las ranuras de aislamiento de la zona de contactos no deben cortar las pestañas) `[H]` | V-cut no sirve con esquinas redondeadas ni con componentes a menos de ≈ 1 mm `[CG]` | C |
| **Componentes de patas (THT)** | 7 relés, 12 borneras KF128, DIP, IRM-20-24, varistor: hoy hay paquete `_solo_SMD` para soldar las de patas a mano `[R]` | Considerar etiquetas de serie y orden de soldadura en un procedimiento de ensamble (**PD**) | B1 (documento) |
| **Identificación** | Rev, fecha y espacio para número de serie/QR en serigrafía | Trazabilidad de la primera tanda | B1 |

---

## 8. (g) Cambios mínimos de bajo riesgo (rev B1) frente a los de la rev C

Criterio de B1: **mismo PCB** o cambios de **valores de BOM/serigrafía/firmware** que no modifican el ruteo ni los 6.4 mm de aislamiento de la red; se corre `verificar_todo.sh` y se repite el pedido.

### Rev B1 (propuesto)
| # | Cambio | Dónde | Riesgo que corrige | Condición |
|---|---|---|---|---|
| B1-1 | **Entradas bipolares solo con BOM (O2f):** OK1-8 → opto CA de la misma caja (LTV-354T o equivalente), LI → 0 Ω, **DI sin montar**, RA = 2.2 k, RB = 2.4 k, RS = 1.0 k | `make.py`/BOM de B1 | NPN y contacto seco de 24 V; ya no hace falta la mejora de la rev C para validar | **solo si** la huella coincide con el dibujo mecánico y tras medir O0 (§9). Se pierde el LED de entrada |
| B1-2 | Firmware: indicador de **inversión por entrada** y **tiempo muerto configurable 0.1-0.5 ms** en IO0/IO20 | `firmware/APControl` (`ap-firmware`) | Permite validar NPN con O5 y fija el conteo rápido | requiere pruebas |
| B1-3 | Bitácora en **flash interna** con vaciado periódico | firmware | La bitácora se pierde al apagar | límite de desgaste ya calculado (§3) |
| B1-4 | RS-485: polarización **680 Ω → 470 Ω** (R14 y R15 en `make.py`) | BOM | Margen de 67 mV con terminación | medir con 120 Ω |
| B1-5 | Serigrafía: marcas de polaridad, rev, diagrama de cableado de COMI, «NPN → COMI a +24 V» | `make.py` SILK | Errores de instalación | — |
| B1-6 | Puntos de prueba en E1, E2, COMI, GNDB (si el DRC lo permite) | `make.py` TPS | Medición del §2.3 | DRC y cobre libre |

### Rev C (espera a la primera tanda)
Puente o 2 comunes de entrada (COMA/COMB, J13 a 4 polos), TVS por entrada/banco, descarga de COMI, huella SOIC-8 FRAM/EEPROM + aviso de corte en U5 P7, INA238 + shunt en V24, partición de la red V24, filtros de ferrita, PE por montaje, fiduciales y panelización, módulo ESP32-S3 si se pide Ethernet o medición por canal, reserva de huella Hall solo para el SKU 24DC.

---

## 9. Recomendación y pruebas de la primera tanda

### Recomendación
1. **No rediseñar a ciegas.** Con las 5 placas rev B: medir las 8 entradas (curva I-V, umbral, tiempos) para obtener la dispersión real de CTR; es el dato que decide entre O1 (puente + LTV-217, Basic) y O2 (opto CA, Extended).
2. **Camino preferente para la rev C:** *bipolar* con **puente BAV99 + LTV-217** (O1 o O1b) si la dispersión es grande o si se quiere conservar el LED en serie; **opto CA** (O2e) si la huella coincide y el costo de la pieza Extended es aceptable. Ambas con **dos comunes (COMA/COMB)**.
3. **B1 inmediata (sin PCB):** B1-1 a B1-5, si la huella del LTV-354T coincide y la medición lo apoya; hoy el único camino para probar NPN sin pedir otra placa es O5 + firmware.
4. **Ethernet:** gateway externo en el piloto; variante propia con ESP32-S3 + W5500 si la demanda lo pide (no con el C3).
5. **Corriente:** solo por placa (INA238) en rev C; por canal queda fuera hasta confirmar aislamiento y requisito.
6. **Memoria:** flash interna ahora; huella SOIC-8 para FRAM/EEPROM en rev C.

### Pruebas que validan o descartan (primera tanda, 2-3 placas ensambladas)
| ID | Prueba | Criterio de pasa/no pasa | Decide |
|---|---|---|---|
| P1 | Curva I-V de cada entrada de 0 a 30 V con fuente regulada y amperímetro (8 canales × 3 placas) | Compararla con el modelo `[C]`: I(24 V) = 4.7 mA ± 15 %; umbral de lectura < 5 V = «inactiva» para todas | Si algún canal lee «activa» a < 5.5 V: O1b o RS menor; si el umbral > 11 V en alguno: revisar CTR |
| P2 | Barrido de umbral (voltaje al que Ek pasa a 0 y regresa) | Mediana y dispersión (para validar 7.2 V / 5.26 V del modelo) | O1 vs O2 |
| P3 | Generador de pulsos 24 V → entrada 1 y 2 a 100 Hz, 500 Hz, 1 kHz, 2 kHz (50 % de trabajo), osciloscopio en E1/E2 (TP nuevo o alambre) | t_encendido, t_apagado, distorsión de ancho < 10 % del semiperíodo a 500 Hz; **0 cuentas perdidas en 10⁶ pulsos** en IO0 e IO20 | Si falla: bajar la IF o RP a 4.7 kΩ; sin filtro de colector |
| P4 | Sensor PNP real, sensor NPN real con el esquema O5 y contacto seco de 24 V, cables de 1 m y 50 m | Lectura correcta; sin rebotes contados | Valida el §2.1; NPN con O5 en rev B |
| P5 | Sensor de 2 hilos con fuga ≈ 1.5 mA (resistor de 16 kΩ en paralelo con el sensor) | Registrar si lee «activa» (esperado: sí) | Confirmar que queda fuera del alcance |
| P6 | Consumo de la placa con 0-7 relés y Wi-Fi apagado/encendido; amperímetro en serie | Contrastar los 0.15 A de la hoja `[R]` | Decide INA238 y W5500 |
| P7 | 1000 ciclos de apagado/encendido con escritura de bitácora en flash interna; corte aleatorio durante la escritura | 0 registros corruptos; pérdida ≤ el período de vaciado | Descarta FRAM para la bitácora |
| P8 | Medición del tiempo de sostén de 24 V al cortar con carga (osciloscopio en V24 y 3V3) | ≥ 4 ms hasta que 3.3 V caiga | Decide el esquema de aviso de corte |
| P9 | Polarización RS-485 con terminación puesta: tensión diferencial en reposo | ≥ 0.3 V y sin errores de trama | Valida B1-4 |
| P10 | Prueba de aislamiento (500 V CC entre COMI/entradas y GND) con instrumento adecuado | Sin ruptura | Condición de cualquier TVS/condensador en COMI |
| P11 | `tools/revisar_pines.py` con el módulo ESP32-S3 propuesto y W5500 (sin placa) | Presupuesto de pines cubierto | Habilita la variante Ethernet |

---

## 10. Hallazgos, qué falta saber, siguiente paso y fuentes

**Hallazgos (por gravedad)**
1. **No se pueden mezclar PNP y NPN con un solo COMI**, ni siquiera con entradas bipolares (§2.1, §2.5). Requiere dos comunes en la rev C. `make.py`, J13 pin 3.
2. **LTV-814S no es de la misma huella** que OK1-8 (SMDIP-4 de 9.53 mm, `jlcpcb.py` línea C108051); `PUESTA_EN_MARCHA.md` §«Entradas» sugiere lo contrario. La familia de la misma caja es el LTV-354T/EL354 (huella por verificar).
3. **Margen de umbral en rev B: 0.26 V** sobre «apagada < 5 V» según el modelo (§1); y la hoja de datos dice «encendida > ≈ 11 V» cuando el modelo da 7.2 V. Medir (P1, P2).
4. **El C3 no tiene pines libres**: Ethernet, ADC y detección de corte exigen un módulo mayor (ESP32-S3) o más expansores. Solo quedan IO21 y U5 P7.
5. **Medición por canal no es viable con shunt** (contactos flotantes) y los Hall chocan con la regla de aislamiento de 6.4 mm (§5.2).
6. Con terminación puesta, la polarización del RS-485 da 0.27 V (margen de 67 mV) (§6).

**Qué falta saber:** hoja completa LTV-217 y LTV-354T (tr/tf, CTR a IF bajo, dibujo mecánico); hoja del CA-IS3092W (umbral del receptor); VIL/VIH reales del TCA9554 y de IO0/IO20; fuga de los sensores en la planta piloto; precio y clase LCSC de LTV-354T, FRAM e INA238 actuales; si el cliente exige corriente por canal; especificación de fiduciales de JLCPCB; tabla de pines del ESP32-C3-WROOM-02 (IO21 libre).

**Siguiente paso recomendado:** (1) imprimir y superponer los dibujos de LTV-217 y LTV-354T; (2) construir la prueba P1-P3 con la primera placa; (3) si P1-P3 pasan, aprobar B1-1…B1-5 y abrir la rev C con O1/O2e + COMA/COMB; (4) decidir Ethernet y corriente con las entrevistas de `ap-ventas-clientes`.

**Fuentes (consultadas 2026-10-14, extractos de buscador; hojas completas sin descargar)**
- LTV-217-B-G (C115450): https://jlcpcb.com/partdetail/LiteOn-LTV_217_BG/C115450 ; Arrow LTV-217-A-G: https://www.arrow.com/en/products/ltv-217-a-g/lite-on-technology.html ; Future: https://www.futureelectronics.com/p/3054477
- LTV-354T: https://optoelectronics.liteon.com/upload/download/DS70-2001-004/LTV-354T%20series%20201610.pdf ; https://jlcpcb.com/partdetail/LiteOn-LTV354T/C119090 ; https://jlcpcb.com/partdetail/3024121-LTV354T/C2841485 ; https://www.lcsc.com/product-detail/C10802.html
- LTV-814S: https://au.rs-online.com/web/p/optocoupler-ics/6912091 ; EL354: https://www.mouser.com/datasheet/2/143/evers02575_1-2266814.pdf
- FRAM: https://www.mouser.com/datasheet/2/1113/MB85RC256V_DS501_00017_7v0_E-2329117.pdf ; https://www.lcsc.com/product-detail/C9829.html
- Ethernet: https://docs.espressif.com/projects/esp-idf/en/latest/api-reference/network/esp_eth.html ; https://components.espressif.com/components/espressif/w5500 ; https://github.com/BOlaerts/ESPHome-W5500-Ethernet-on-ESP32-boards ; https://esp32.com/viewtopic.php?p=133756 ; Sipeed W5500: https://api.dl.sipeed.com/fileList/MAIX/HDK/Spmod_EN/SP-Ethernet%20Datasheet%20V1.0.pdf
- Corriente: https://www.ti.com/product/INA181 ; https://www.pololu.com/product/4047/resources ; https://www.digikey.com/en/products/detail/allegro-microsystems/ACS723LLCTR-40AB-T/4915381 ; https://www.ti.com/product/TMCS1108
- Entradas industriales: https://www.mouser.com/maxim-max22190-input/ ; cableado: https://industrialmonitordirect.com/blogs/knowledgebase/npn-vs-pnp-sensors-plc-input-wiring-guide
- JLCPCB: https://api.jlcpcb.com/help/article/How-to-add-edge-rails/fiducials-for-PCB-assembly-order ; https://jlcpcb.com/help/article/61-Terms-and-Conditions-of-JLCPCB-Assembly-Service
- Repositorio: `hardware/ap-electric/7r-tour/gen/make.py`, `hardware/tools/jlcpcb.py`, `hardware/tools/jlcpcb_catalogo.csv`, `empresa/compras/CADENA_SUMINISTRO_REV_B.md` (alternativas LTV-217-A-G C123195 y -C-G C123196).
