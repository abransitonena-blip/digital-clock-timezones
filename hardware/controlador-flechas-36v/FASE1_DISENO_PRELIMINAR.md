# Controlador secuencial de flechas verdes (36 VCC) para letrero Radox 246-402 modificado

**Fase 1: Diseño preliminar para validación**
Estado: **EN ESPERA DE VALIDACIÓN**. Todavía no hay pistas, Gerber ni proyecto KiCad; se generarán cuando se aprueben el esquema y los cálculos.

---

## 0. Criterios de seguridad adoptados

1. La nueva PCB **no** tiene conexión a 127 VCA. Toda la placa es de muy baja tensión de seguridad (MBTS/SELV), alimentada por una fuente externa **certificada y aislada** de 36 VCC.
2. No se copia la fuente capacitiva de la Radox ni se reutiliza ningún componente de ella.
3. **Ningún conductor** de la placa Radox (común, salidas, LED) se conecta a esta PCB mientras la Radox siga conectada a 127 VCA. Los LED que controla la Radox están referidos a la red. Aunque parezcan "de bajo voltaje", deben tratarse como si estuvieran conectados directamente a la red.
4. Si en el futuro hace falta una señal entre las dos placas, se usará un optoacoplador (por ejemplo, PC817 o 4N35), manteniendo la separación de aislamiento reforzado en las dos PCB y en el cableado.
5. Las salidas opcionales FLORES, BAÑOS y CENTROS quedan **deshabilitadas por diseño** (puentes sin montar) hasta tener las mediciones de la sección 6.

---

## 1. Diagrama por bloques

```
                         ZONA DE POTENCIA 36 V                         |            ZONA LÓGICA 12 V
                                                                       |
 Fuente aislada   J1                                                   |
 36 VCC ≥0.5 A ──[36V+]──F1 PTC 0.25A──D1 1N4007──┬── BUS +36V_P ──────┼──► J2 → módulo LM2596(HV) IN+
 (certificada)    [GND]──────────────┐             │                   |    J3 ◄── módulo OUT+ 12 V
                                     │   D2 TVS  C1 100µ/63V  C2 100n  |          │
                                     │    P6KE47A   │          │       |    DZ1 15V · C3 100µ/25V · LED 12V
                                     ├─────────┴────┴──────────┴───────┼──────────┤
                                     │                                 |   ┌──────┴──────┐   ┌─────────────┐
                                     │  +36V_P ──► J4 (+36V común)     |   │ U1 NE555P   │──►│ U2 CD4017BE │
                                     │             F1− F2− F3−         |   │ astable     │CLK│ Q0 Q1 Q2    │
                                     │              │   │   │          |   │ 0.24–1.6 s  │   │ Q3→RESET    │
                                     │         [Regulador de corriente │   └──────┬──────┘   │ + POR       │
                                     │          por flecha, opción A/B]|          │          └──┬──┬──┬────┘
                                     │              │   │   │          |          │ OUT        Q0 Q1 Q2
                                     │            Q1  Q2  Q3 2N7000 ◄──┼──────────┼────────────┴──┴──┘
                                     │            (compuerta 1k/100k)  |          │  (indicadores 1 mA)
                                     │                                 |          ▼
                                     │  +36V_P ──► J5 CENTROS ◄── Q4 ◄─┼──── pulso 555 (opcional)
                                     │  +36V_P ─JP2(no montado)─► J6 FLORES   (opcional)
                                     │  +36V_P ─JP3(no montado)─► J7 BAÑOS    (opcional)
                                     └── GND (punto estrella en J1) ───┘
```

Separación física: la mitad izquierda de la PCB (J1, F1, D1, D2, C1, C2, MOSFET, resistencias o reguladores de las flechas, J4 a J7) es la zona de 36 V. La mitad derecha (U1, U2, temporización, POR, indicadores) es la zona de 12 V. Las compuertas de los MOSFET son las únicas señales que cruzan la frontera, y lo hacen a través de resistencias de 1 kΩ.

---

## 2. Esquema eléctrico propuesto (lista de conexiones)

### 2.1 Entrada y protección (zona 36 V)

| Ref | Valor | Conexión |
|---|---|---|
| J1 | Clema 2 P, 5.08 mm | pin 1 = **36V+**, pin 2 = **GND** |
| F1 | PTC RXEF025 (0.25 A hold / 0.50 A trip, 72 V) | J1-1 → nodo `V_F` |
| D1 | 1N4007 | ánodo `V_F` → cátodo `+36V_P` (bloquea la inversión de polaridad) |
| D2 | TVS P6KE47A (unidireccional) | cátodo `+36V_P`, ánodo GND. Va **después** de D1, así que nunca conduce con la polaridad invertida |
| C1 | 100 µF / 63 V electrolítico, 105 °C | `+36V_P` / GND |
| C2 | 100 nF / 100 V cerámico X7R | `+36V_P` / GND, junto a C1 |
| R1 + LED1 | 33 kΩ ¼ W + LED verde 3 mm "36V" | `+36V_P` → R1 → LED1 → GND (≈1 mA) |

### 2.2 Módulo reductor (externo, cableado a la PCB)

| Ref | Conexión |
|---|---|
| J2 | Clema 2 P "A LM2596 IN": pin 1 = `+36V_P` → IN+ del módulo, pin 2 = GND → IN− |
| J3 | Clema 2 P "DE LM2596 OUT": pin 1 = OUT+ (12 V) → `+12V`, pin 2 = OUT− → GND |

El LM2596 no es aislado: IN− y OUT− son el mismo nodo. Eso es aceptable porque toda la placa es SELV.

### 2.3 Riel de 12 V (zona lógica)

| Ref | Valor | Conexión |
|---|---|---|
| C3 | 100 µF / 25 V electrolítico | `+12V` / GND |
| DZ1 | 1N4744A (15 V, 1 W) | cátodo `+12V`, ánodo GND. Protección de sacrificio si el módulo se desajusta por encima de 15 V |
| R2 + LED2 | 10 kΩ + LED rojo 3 mm "12V" | ≈1 mA |

### 2.4 Oscilador NE555P (U1, DIP-8)

| Pin U1 | Conexión |
|---|---|
| 1 GND | GND |
| 2 TRIG + 6 THRES | unidos; nodo `TIM`, a C5 (+) |
| 3 OUT | `CLK_555` → R5 1 kΩ → U2-14; → R21 1 kΩ → compuerta Q4; → R11 10 kΩ → LED6 "CENTROS" → GND |
| 4 RESET | `+12V` |
| 5 CONT | C6 10 nF → GND |
| 7 DISCH | nodo `DIS`: R3 4.7 kΩ a `+12V`; R4 15 kΩ + RV1 100 kΩ (reóstato) a `TIM` |
| 8 VCC | `+12V`; C4 100 nF a GND pegado al pin 8 |
| — | C5 10 µF / 25 V electrolítico: `TIM` (+) → GND (−) |

### 2.5 Contador CD4017BE (U2, DIP-16)

| Pin U2 | Señal | Conexión |
|---|---|---|
| 3 | Q0 | `G1_L` → R12 1 kΩ → compuerta Q1 (flecha 1); → R8 10 kΩ → LED3 "F1" → GND |
| 2 | Q1 | `G2_L` → R13 1 kΩ → compuerta Q2 (flecha 2); → R9 10 kΩ → LED4 "F2" → GND |
| 4 | Q2 | `G3_L` → R14 1 kΩ → compuerta Q3 (flecha 3); → R10 10 kΩ → LED5 "F3" → GND |
| 7 | Q3 | → D4 1N4148 (ánodo en Q3, cátodo en RESET) |
| 15 | RESET | nodo `RST`: R7 47 kΩ a GND; cátodos de D3 y D4 |
| 14 | CLOCK | desde R5 (salida del 555) |
| 13 | CLOCK INHIBIT | GND |
| 16 | VDD | `+12V`; C7 100 nF a GND pegado al pin 16 |
| 8 | VSS | GND |
| 1, 5, 6, 9, 10, 11 | Q5, Q6, Q7, Q8, Q4, Q9 | sin conexión (son salidas; se dejan abiertas) |
| 12 | CARRY OUT | sin conexión |

Pines del CD4017: Q0 = 3, Q1 = 2, Q2 = 4, Q3 = 7, Q4 = 10, Q5 = 1, Q6 = 5, Q7 = 6, Q8 = 9, Q9 = 11. Todos quedan abiertos salvo Q0–Q3.

### 2.6 Reset de encendido (POR) y reset por Q3 (OR con diodos)

| Ref | Valor | Conexión |
|---|---|---|
| C8 | 2.2 µF / 25 V electrolítico | (+) a `+12V`, (−) al nodo `POR` |
| R6 | 100 kΩ | `POR` → GND |
| D3 | 1N4148 | ánodo en `POR`, cátodo en `RST` |
| D5 | 1N4148 | ánodo en GND, cátodo en `POR` (descarga rápida de C8 al apagar; limita `POR` a −0.7 V) |
| D4 | 1N4148 | ánodo en U2-Q3 (pin 7), cátodo en `RST` |
| R7 | 47 kΩ | `RST` → GND |

### 2.7 Etapas de salida de las flechas (zona 36 V)

Por flecha *n* (n = 1, 2, 3):

```
 J4-1 (+36V común) ──► ánodo de la cadena de 9 LED verdes ──► cátodo ──► J4-(n+1) "Fn−"
                                                                           │
                                                          [ Limitador de corriente, opción A o B ]
                                                                           │
                                                                     Drenaje de Qn (2N7000)
                            Gn_L ── R 1 kΩ ── compuerta Qn ── R 100 kΩ ── fuente de Qn = GND
```

| Ref | F1 | F2 | F3 |
|---|---|---|---|
| MOSFET | Q1 | Q2 | Q3 |
| Resistencia de compuerta | R12 1 kΩ | R13 1 kΩ | R14 1 kΩ |
| Pull-down de compuerta | R15 100 kΩ | R16 100 kΩ | R17 100 kΩ |
| Limitador (opción A) | R18 (valor por medición, ½ W) | R19 | R20 |
| Limitador (opción B) | U3 LM317LZ + R18 | U4 + R19 | U5 + R20 |

**Opción A (solo resistencia):** Fn− → R18 → drenaje de Q1.
**Opción B (fuente de corriente constante del lado bajo):** Fn− → IN de U3 (LM317LZ); OUT de U3 → R18 → nodo ADJ de U3 → drenaje de Q1. R18 = 68 Ω + 68 Ω (1 %) en serie, o 140 Ω 1 % (E96).

J4 = clema de 4 P: **+36V**, **F1−**, **F2−**, **F3−** (las tres flechas comparten el ánodo).

### 2.8 Salidas opcionales (sin montar, no conectar)

| Salida | Circuito | Estado |
|---|---|---|
| **CENTROS** | J5 (2 P): pin 1 = `+36V_P` vía JP1 (puente no montado); pin 2 = drenaje de Q4 (2N7000). Compuerta: R21 1 kΩ desde la salida del 555 y R22 100 kΩ a GND | Parpadea con el pulso del 555. Las resistencias de cada rama van **en el panel**, una por rama; su valor no se define aquí |
| **FLORES** | J6 (2 P): pin 1 = `+36V_P` vía JP2 (no montado); pin 2 = GND | Salida fija; las resistencias van en el panel |
| **BAÑOS** | J7 (2 P): pin 1 = `+36V_P` vía JP3 (no montado); pin 2 = GND | Salida fija; las resistencias van en el panel |

Mientras JP1–JP3 no estén montados, las clemas J5–J7 quedan sin tensión. Esto evita energizar series desconocidas por accidente.

Otros elementos: H1–H4, perforaciones de montaje M3 (3.2 mm) en las esquinas.

---

## 3. Cálculos

### 3.1 Hipótesis de tensión

| Parámetro | Mín. | Nom. | Máx. | Nota |
|---|---|---|---|---|
| Fuente de 36 V (tolerancia de ajuste y regulación) | 35.0 V | 36.0 V | 37.0 V | ±3 % (a confirmar con el modelo de fuente) |
| Caída en D1 (1N4007 a ~35 mA) | 0.70 V | 0.75 V | 0.85 V | |
| Caída en F1 (PTC, ~1–3 Ω) | ≈0.05 V | | ≈0.1 V | despreciable |
| **Bus +36V_P** | **34.1 V** | **35.2 V** | **36.25 V** | |
| VDS(on) de 2N7000 a 10 mA (RDS(on) ≤ 5 Ω a VGS = 10 V) | | 0.02 V | 0.05 V | despreciable |
| Cadena de 9 LED: 9 × 2.8 / 3.0 / 3.2 V | 25.2 V | 27.0 V | 28.8 V | Vf del enunciado; normalmente especificado a 20 mA |

### 3.2 Opción A: resistencia fija (cálculo solicitado)

I = (V_bus − V_cadena − VDS) / R

**a) Con la resistencia sugerida de 1 kΩ, bus nominal de 35.2 V:**

| Vf por LED | V cadena | V en R | I | ¿Dentro de 8–10 mA? |
|---|---|---|---|---|
| 2.8 V (mín.) | 25.2 V | 10.0 V | **10.0 mA** | en el límite |
| 3.0 V (típ.) | 27.0 V | 8.2 V | **8.2 mA** | sí |
| 3.2 V (máx.) | 28.8 V | 6.4 V | **6.4 mA** | **NO** |

**b) Resistencia ideal para 9 mA, por cada Vf:**

| Vf | R ideal | E24 más cercana | I resultante (bus nominal) |
|---|---|---|---|
| 2.8 V | 1111 Ω | 1.1 kΩ | 9.1 mA |
| 3.0 V | 911 Ω | 910 Ω | 9.0 mA |
| 3.2 V | 711 Ω | 750 Ω | 8.5 mA |

**c) Hallazgo importante:** para cumplir 8–10 mA en todo el rango de Vf haría falta R ≥ 1000 Ω (por Vf mín.) y a la vez R ≤ 800 Ω (por Vf máx.). **Es imposible con una sola resistencia fija.** El margen de tensión en R (6.4–10 V) es comparable a la dispersión de la cadena (3.6 V). Además:
- Cada voltio de variación de la fuente cambia la corriente ≈1.1 mA (con R ≈ 910 Ω).
- La Vf de un LED verde InGaN baja unos 3 mV/°C, o ≈27 mV/°C por cadena. Con un calentamiento de 30 °C, la corriente sube ≈0.9 mA.

Con la opción A, la resistencia solo puede elegirse **después de medir** cada cadena real: R = (V_bus medido − V_cadena medida a 9 mA) / 9 mA. Aun así, la corriente se saldrá de 8–10 mA si la fuente varía más de ±0.5 V.

**d) Potencia de la resistencia en el peor caso** (bus máx. de 36.25 V, Vf mín., encendido continuo sin considerar el ciclo de 1/3):

| R | V en R | I | P | Potencia nominal elegida | Margen |
|---|---|---|---|---|---|
| 1.1 kΩ | 11.05 V | 10.0 mA | 0.111 W | ½ W | 350 % |
| 1.0 kΩ | 11.05 V | 11.0 mA | 0.122 W | ½ W | 310 % |
| 910 Ω | 11.05 V | 12.1 mA | 0.134 W | ½ W | 270 % |
| 750 Ω | 11.05 V | 14.7 mA | 0.163 W | ½ W | 207 % |

Todas cumplen con holgura el margen de potencia de ≥100 % que se pidió. Se usa ½ W de película metálica.

### 3.3 Opción B: LM317LZ como fuente de corriente (recomendada)

I = V_REF / R + I_ADJ, con V_REF = 1.20–1.30 V e I_ADJ = 50 µA típ. / 100 µA máx.

| R18–R20 | I mín. | I máx. | ¿Cumple 8–10 mA? |
|---|---|---|---|
| 140 Ω 1 % (E96) | 1.20 / 141.4 + 0.05 = **8.54 mA** | 1.30 / 138.6 + 0.10 = **9.48 mA** | **sí**, para cualquier Vf, fuente y temperatura |
| 68 Ω + 68 Ω 1 % (136 Ω) | 8.78 mA | 9.76 mA | sí |
| 150 Ω 5 % | 7.6 mA | 9.1 mA | no |

- **Margen de regulación:** V_bus mín. 34.1 − cadena máx. 28.8 − VDS 0.05 = 5.25 V disponibles. El LM317L necesita V_REF + 3 V (condición garantizada de la hoja de datos) = 4.25 V. **Sobra 1.0 V** incluso en el peor caso.
- **Disipación del LM317L** (bus máx., Vf mín.): (36.25 − 25.2 − 1.25 − 0.05) V × 9.5 mA = **93 mW**. El TO-92 admite unos 625 mW, así que el aumento de temperatura es de unos 17 °C.
- **Potencia en R18:** 1.3² / 136 = 12 mW. Una resistencia de ¼ W da un margen >1900 %.
- **Tensión de entrada a salida del LM317L:** ≤ 11 V al conducir, muy por debajo del máximo de 40 V.

### 3.4 Oscilador NE555

T = 0.693 · C5 · (R3 + 2·(R4 + RV1)), con C5 = 10 µF, R3 = 4.7 kΩ, R4 = 15 kΩ y RV1 = 0–100 kΩ.

| RV1 | T (C nominal) | T (C −20 %) | T (C +20 %) | Ciclo de trabajo |
|---|---|---|---|---|
| 0 Ω | **0.24 s** | 0.19 s | 0.29 s | 57 % |
| 100 kΩ | **1.63 s** | 1.30 s | 1.95 s | 51 % |

El rango de 0.3 a 1.2 s por paso queda cubierto aunque C5 tenga una tolerancia de ±20 %. El CD4017 avanza en cada flanco de subida, así que **un periodo = un paso**. La secuencia completa (3 flechas) dura entre 0.72 y 4.9 s.

Nivel de reloj: VOH del NE555 a 12 V ≈ 10.3–10.8 V, por encima del VIH del CD4017B a 12 V (≈8.4 V). La entrada CLOCK del CD4017B tiene disparador Schmitt.

### 3.5 Reset de encendido y Q3 → RESET

- **POR:** C8 · R6 = 2.2 µF × 100 kΩ = 0.22 s. RESET se mantiene por encima de VDD/2 durante ≈0.13 s (considerando la caída de D3).
- **Primer flanco de subida contado del 555:** 1.1·(R3 + R4)·C5 + 0.693·R4·C5 ≥ 0.22 + 0.10 = **0.32 s** con RV1 = 0. El flanco inicial ocurre durante el reset y se ignora. Por lo tanto, el contador siempre empieza en Q0 (flecha 1).
- Sin POR, el contador Johnson de 5 etapas puede arrancar en un estado inválido, donde podría haber **más de una salida decodificada activa a la vez** durante algunos pulsos de reloj. Esto justifica incluir el POR.
- **Reset por Q3:** cuando Q3 sube, D4 lleva RESET a ≈11.3 V (> VIH). El contador pasa a Q0 y Q3 baja. El pulso dura cientos de nanosegundos (autolimitado) y R7 lo alarga ≈1 µs. Es la configuración clásica y confiable. Q3 no maneja ninguna carga, así que nunca se enciende una flecha "4".
- **Aislamiento entre ambos resets:** D3 y D4 forman una compuerta OR. Q3 no tiene que cargar C8 y el POR no carga a Q3.

### 3.6 Exclusividad de las salidas

- El contador Johnson del CD4017 cambia **un solo biestable por pulso de reloj**, y cada salida decodifica dos biestables adyacentes. En los 10 estados válidos hay **exactamente una salida alta** y no se producen glitches de decodificación.
- En la transición Qn → Qn+1 puede haber un solapamiento o hueco de decenas de nanosegundos, debido a los retardos de los buffers. Es invisible y no tiene efecto eléctrico, porque cada flecha tiene su propio limitador.
- Los estados inválidos solo pueden aparecer al energizar o ante un brown-out. El POR los elimina al arrancar. Además, el CD4017B tiene lógica de autocorrección que vuelve a la secuencia válida en pocos pulsos.

### 3.7 Compuerta de los MOSFET

- VOH del CD4017 con carga de 1 mA (indicador) + 0.12 mA (pull-down) ≈ 11.0–11.8 V. Esa es la VGS aplicada.
- VGS(th) del 2N7000 = 0.8–3.0 V. RDS(on) ≤ 5 Ω especificado a VGS = 10 V. **Hay VGS de sobra.**
- VGS máx. = ±20 V. En el peor caso, con DZ1 conduciendo, la compuerta ve ≈15–16 V. Cumple.
- R 1 kΩ en la compuerta: amortigua y limita la corriente hacia el CD4017 si el MOSFET falla en corto D-G. R 100 kΩ de pull-down: mantiene el MOSFET apagado sin lógica o sin el CI en su zócalo.

### 3.8 Tensión VDS máxima (margen ≥ 50 %)

| Condición | VDS máx. | Límite del 2N7000 / BS170 | Margen |
|---|---|---|---|
| Apagado, flecha desconectada o bus máx. | 36.25 V | 60 V | **66 %** |
| Apagado, fuente ajustada al extremo (+10 %, 39.6 V) | 38.9 V | 60 V | 54 % |
| Transitorio de sobretensión (TVS en ruptura, ≤49 V) con la cadena conectada | ≤ 49 − 9 × ~2.3 V ≈ 28 V | 60 V | La propia cadena de LED impide que el drenaje alcance el bus |

La corriente de 10 mA frente a los 200 mA continuos del 2N7000 (500 mA en el BS170) da un margen de 20×.

> **Pinout:** 2N7000 = S-G-D; BS170 = D-G-S (visto desde la cara plana). La serigrafía se hará para 2N7000. Un BS170 se monta **girado 180°**, y así se indicará en la placa.

### 3.9 Una flecha desconectada

La lógica (U1, U2) no depende del drenaje. Si falta una cadena, ese drenaje queda flotante (VDS ≤ bus). La secuencia de las otras dos flechas sigue igual; la flecha faltante solo produce un paso "a oscuras". Con la opción B, el LM317L de esa rama no conduce. **No hay afectación.**

### 3.10 Disipación de todos los componentes

| Ref | Condición del peor caso | P | Nominal | Margen |
|---|---|---|---|---|
| R18–R20 (A) | 11.05 V, 14.7 mA | 0.163 W | 0.5 W | 207 % |
| R18–R20 (B) | 1.3 V, 9.8 mA | 0.013 W | 0.25 W | >1800 % |
| U3–U5 LM317LZ (B) | 9.75 V × 9.5 mA | 0.093 W | ~0.625 W | 570 % |
| Q1–Q4 2N7000 | (10 mA)² × 5 Ω | 0.0005 W | 0.4 W | enorme |
| D1 1N4007 | 0.85 V × 40 mA | 0.034 W | ~1 W (1 A) | enorme |
| F1 PTC | (40 mA)² × 3 Ω | 0.005 W | — | — |
| R1 (LED 36V) | (36.25 − 2)² / 33 k | 0.036 W | 0.25 W | 590 % |
| R2, R8–R11 (10 kΩ) | (12 − 1.8)² / 10 k | 0.010 W | 0.25 W | enorme |
| R3 (4.7 kΩ, descarga) | 12² / 4.7 k (en fase baja) | 0.031 W | 0.25 W | 700 % |
| U1 NE555P | 12 V × 15 mA máx. | 0.18 W | ~1 W (DIP-8) | 450 % |
| U2 CD4017BE | < 1 mW | — | — | — |
| DZ1 | 12 V: solo fuga (< 5 µA) | ~0 | 1 W | — |

### 3.11 Corrientes esperadas

| Rama | Típica | Máxima |
|---|---|---|
| Flecha encendida (solo una a la vez), opción B | 9.0 mA | 9.8 mA |
| Flecha encendida, opción A (según R elegida) | 9 mA | 14.7 mA |
| LED1 (indicador de 36 V) | 1.0 mA | 1.05 mA |
| Carga del riel de 12 V: NE555 (7 típ. / 15 máx.) + descarga R3 (2.6) + indicadores (3 × 1) + pull-downs (0.25) + CD4017 (< 0.1) | 12 mA | 21 mA |
| Entrada del LM2596 desde 36 V (eficiencia ≈65 % a carga ligera + IQ) | 12 mA | 20 mA |
| **Total de la fuente de 36 V sin salidas opcionales** | **≈ 22 mA (0.8 W)** | **≈ 35 mA (1.3 W)** (opción A: ≈ 40 mA) |
| Salidas opcionales CENTROS/FLORES/BAÑOS | **desconocida** | limitada por F1 a 0.25 A |

Con la fuente de 500 mA, la reserva es >10× sin las salidas opcionales.

### 3.12 Tensiones esperadas (tabla de pruebas)

| Punto de prueba | Valor esperado |
|---|---|
| J1-1 a GND | 35.0–37.0 V |
| `+36V_P` (cátodo de D1) | J1 − 0.75 V ≈ 35.2 V |
| J1 con la polaridad invertida | `+36V_P` ≈ 0 V (D1 bloquea) |
| J3-1 `+12V` | 12.0 V ± 0.2 V (ajustado en el trimpot del módulo **antes** de conectarlo) |
| U1-8 / U2-16 | 12.0 V |
| U1-5 (CONT) | 8.0 V (2/3 VCC) |
| U1-2/6 (`TIM`) | diente de sierra de 4.0 a 8.0 V |
| U1-3 (OUT) | cuadrada de 0 V a ≈10.5 V |
| U2-3/2/4 (Q0/Q1/Q2) | 0 V o ≈11–12 V; solo una en alto a la vez |
| U2-7 (Q3) | ≈0 V (pulsos de < 1 µs, no medibles con multímetro) |
| U2-15 (RESET) | 0 V en marcha; ≈11 V durante ≈0.13 s al encender |
| Compuerta de Qn encendido / apagado | ≈11 V / 0 V |
| Drenaje de Qn encendido | ≈0.05 V |
| Fn− con la flecha encendida, opción B | V_bus − V_cadena ≈ 6–11 V (según Vf); el LM317L absorbe el excedente |
| Fn− con la flecha encendida, opción A | ≈ 0.05 V + I·R ≈ 6.4–11 V |
| Fn− con la flecha apagada | entre ≈15 V y el bus (tensión de fuga de la cadena) |
| Cadena de 9 LED encendida | 25–29 V (medir y anotar) |

---

## 4. Lista de componentes (preliminar, opción B)

| Ref | Cant. | Valor / parte | Encapsulado (TH) | Función |
|---|---|---|---|---|
| J1 | 1 | Clema 2 P 5.08 mm | TerminalBlock 5.08 mm | Entrada 36V+ / GND |
| J2 | 1 | Clema 2 P 5.08 mm | TerminalBlock 5.08 mm | Hacia la entrada del LM2596 |
| J3 | 1 | Clema 2 P 5.08 mm | TerminalBlock 5.08 mm | Desde la salida de 12 V del LM2596 |
| J4 | 1 | Clema 4 P 5.08 mm | TerminalBlock 5.08 mm | +36V, F1−, F2−, F3− |
| J5, J6, J7 | 3 | Clema 2 P 5.08 mm | TerminalBlock 5.08 mm | CENTROS, FLORES, BAÑOS (opcionales) |
| JP1–JP3 | 3 | Puente de alambre **NO MONTAR** | Paso de 7.62 mm | Habilitación de las salidas opcionales |
| F1 | 1 | PTC RXEF025 (o MF-R025) | Radial, 5.1 mm | Fusible rearmable de 0.25 A hold |
| D1 | 1 | 1N4007 | DO-41, 10.16 mm | Protección contra inversión de polaridad |
| D2 | 1 | P6KE47A | DO-15, 12.7 mm | TVS (VRWM 40.2 V) |
| DZ1 | 1 | 1N4744A 15 V 1 W | DO-41 | Sobretensión en 12 V |
| D3, D4, D5 | 3 | 1N4148 | DO-35, 7.62 mm | OR de reset y POR |
| C1 | 1 | 100 µF / 63 V, 105 °C | Radial D8 P3.5 | Volumen de entrada |
| C2 | 1 | 100 nF / 100 V X7R | Disco P5.08 | Desacoplo de 36 V |
| C3 | 1 | 100 µF / 25 V | Radial D6.3 P2.5 | Volumen de 12 V |
| C4, C7 | 2 | 100 nF / 50 V | Disco P5.08 | Desacoplo de U1 y U2 |
| C5 | 1 | 10 µF / 25 V (baja fuga) | Radial D5 P2 | Temporización del 555 |
| C6 | 1 | 10 nF / 50 V | Disco P5.08 | CONT del 555 |
| C8 | 1 | 2.2 µF / 25 V | Radial D5 P2 | Reset de encendido |
| U1 | 1 | NE555P + zócalo DIP-8 | DIP-8 | Oscilador |
| U2 | 1 | CD4017BE + zócalo DIP-16 | DIP-16 | Contador y secuencia |
| U3, U4, U5 | 3 | LM317LZ | TO-92 | Corriente constante de 9 mA por flecha (opción B) |
| Q1–Q4 | 4 | 2N7000 (alt. BS170, girado) | TO-92 | Interruptores de F1, F2, F3 y CENTROS |
| R1 | 1 | 33 kΩ ¼ W | Axial P10.16 | LED 36V |
| R2, R8, R9, R10, R11 | 5 | 10 kΩ ¼ W | Axial P10.16 | Indicadores |
| R3 | 1 | 4.7 kΩ ¼ W | Axial | RA del 555 |
| R4 | 1 | 15 kΩ ¼ W | Axial | RB fija del 555 |
| RV1 | 1 | 100 kΩ lineal, trimpot multivuelta 3296W o de una vuelta | TH | Ajuste de velocidad |
| R5 | 1 | 1 kΩ ¼ W | Axial | Serie del reloj |
| R6 | 1 | 100 kΩ ¼ W | Axial | POR |
| R7 | 1 | 47 kΩ ¼ W | Axial | Pull-down de RESET |
| R12, R13, R14, R21 | 4 | 1 kΩ ¼ W | Axial | Compuertas |
| R15, R16, R17, R22 | 4 | 100 kΩ ¼ W | Axial | Pull-downs de compuerta |
| R18, R19, R20 | 3 (6) | 140 Ω 1 % ¼ W (o 2 × 68 Ω 1 %) | Axial | Programación de corriente (opción B) |
| LED1 | 1 | Verde 3 mm | LED 3 mm | 36V presente |
| LED2 | 1 | Rojo 3 mm | LED 3 mm | 12V presente |
| LED3–LED6 | 4 | Amarillo/rojo 3 mm | LED 3 mm | F1, F2, F3, CENTROS (prueba de la lógica) |
| H1–H4 | 4 | Perforación de 3.2 mm | — | Montaje M3 |
| Externo | 1 | Módulo LM2596**HV** (4.5–60 V) ajustado a 12 V | — | Reductor 36 → 12 V |
| Externo | 1 | Fuente de 36 VCC ≥ 0.5 A, certificada y aislada (p. ej. Mean Well LRS-35-36) | — | Alimentación |

Con la **opción A** se quitan U3–U5 y R18–R20 pasan a ser de ½ W, con el valor que resulte de la medición (1 kΩ inicial para la prueba).

---

## 5. Riesgos y datos faltantes

### 5.1 Riesgos técnicos detectados

1. **La corriente de 8–10 mA no se puede garantizar con una resistencia fija** (sección 3.2c). Por eso propongo la opción B (LM317LZ).
2. **LM2596 estándar a 36 V:** su tensión máxima de operación es de 40 V (45 V absoluta). Con la fuente a 37 V, el margen es solo de 8 %, y el TVS (ruptura de 44.7–49.4 V) **no puede protegerlo**. Recomiendo el módulo **LM2596HV** (hasta 60 V). También hay que revisar que el capacitor de entrada del módulo sea de ≥ 50 V: algunos módulos baratos traen de 35 V.
3. **Aislamiento con la Radox:** si las flechas verdes están montadas en la misma placa o panel que los LED de la Radox (que están a potencial de red), un contacto accidental pondría la red en todo el circuito de 36 V, incluido el módulo y la fuente. Se requiere separación física con aislamiento reforzado (se sugieren ≥ 6 mm de distancia en superficie y en aire, o una barrera aislante) entre el cableado verde y el de la Radox.
4. **Fantasma en las flechas apagadas:** los LED verdes InGaN pueden brillar débilmente con µA de fuga. La IDSS del 2N7000 es de 1 µA máx., normalmente nA. Si se observa, se agrega una resistencia de drenaje. Se verificará en la prueba.
5. El **NE555 bipolar** genera picos de corriente en cada conmutación. Se mitiga con C4 junto al pin 8 y con C3.
6. **CENTROS** parpadea sincronizado con los pasos de la flecha (mismo 555). Si se desea otra frecuencia, haría falta un segundo 555.
7. Si el módulo LM2596 se desajusta a más de 15 V, DZ1 conduce y se sacrifica (falla en corto) hasta que actúa F1. Por eso se debe **ajustar el módulo a 12.0 V sin conectarlo a la PCB**.

### 5.2 Mediciones faltantes para CENTROS, FLORES y BAÑOS (no se inventan valores)

Para cada serie que se quiera pasar a esta placa hace falta:
1. Número de LED por rama y número de ramas en paralelo.
2. Color de cada rama.
3. Vf medida por LED a la corriente deseada (con una fuente de laboratorio limitada a 5–10 mA, **con la Radox desconectada de la red**).
4. Polaridad y cuál conductor es el común (¿ánodo o cátodo común?).
5. Corriente deseada por rama.
6. División exacta de las ramas: con 36 V solo caben ≈ 13–14 LED rojos (Vf ≈ 2 V) o ≈ 9–10 LED azules o verdes (Vf ≈ 3 V) por rama. Por ejemplo, los 75 LED rojos de BAÑOS tendrían que **recablearse** en ≥ 6 ramas, cada una con su propia resistencia **en el panel**.

Nota: el conteo original (BAÑOS, flecha roja, dos figuras azules) no incluye "flores" ni "centros". Hay que confirmar a qué LED se refieren.

### 5.3 Preguntas que necesito que valides antes de trazar la PCB

1. **Limitación de corriente de las flechas:** ¿opción B (LM317LZ, garantiza 8.5–9.8 mA) u opción A (resistencia de ½ W elegida tras medir)?
2. **Módulo reductor:** ¿puedes conseguir el **LM2596HV** (hasta 60 V)? Si solo tienes el LM2596 estándar (40 V), ¿aceptas el riesgo o prefieres otro módulo?
3. **Fuente de 36 V:** ¿qué modelo exacto es? ¿Tiene ajuste de tensión (Vadj)? ¿Cuál es su tolerancia?
4. **Montaje de las flechas verdes:** ¿están en la misma placa o panel que los LED de la Radox? ¿A qué distancia de sus pistas o cables?
5. **Cableado de las flechas:** ¿aceptas ánodo común (+36V compartido, clema de 4 hilos: +36V, F1−, F2−, F3−)?
6. **CENTROS sincronizado** con los pasos: ¿está bien?
7. **FLORES y CENTROS:** ¿a qué LED físicos corresponden?
8. **Clemas de 5.08 mm** y trimpot en la PCB (no potenciómetro de panel): ¿correcto?

---

## 6. Plan de las siguientes fases (después de la validación)

1. Proyecto KiCad 9: esquema `.kicad_sch` con ERC sin errores.
2. PCB de una cara `.kicad_pcb` de ≈ 75 × 55 mm, sin vías, con pistas de 0.8 mm (señal) y 1.2–1.5 mm (potencia), separación ≥ 0.6 mm, pads de 2.4–2.8 mm y DRC sin errores.
3. Salidas de fabricación: Gerber, Excellon, PDF del cobre espejado 1:1, PDF de componentes, plantilla de perforaciones, render 3D y diagrama de conexiones externas.
4. Procedimiento de montaje y de pruebas por etapas (incluida la prueba de la lógica sin LED).
