# Electrónica de potencia en AP ELECTRIC: cómo se protege cada placa

Guía de diseño para las placas actuales y para las siguientes. **Regla fija:** la red de 127/220 V nunca entra a una placa. Todo es 12-24 V DC desde una fuente certificada. Las cargas de red van por contactor o relevador de estado sólido (SSR) de riel DIN certificado.

## 1. Las 5 capas de protección de una entrada de 24 V

| Capa | Qué protege | Cómo lo hacemos hoy | Mejora (siguiente versión) |
|---|---|---|---|
| 1. Fusible | Incendio del cableado | Fusible mini de auto (BASE, PIX, DIST 4, DO8) o 1206 rápido (AI4, NODE) | — (siempre va) |
| 2. Polaridad invertida | Placa conectada al revés | Diodo Schottky en serie (NODE, DMX), MOSFET en el negativo (BASE, PIX), o supresor + fusible (DO8) | **Diodo ideal LM74700-Q1**: controla un MOSFET con 20 mV de caída, aguanta −65 V y corta la corriente inversa en menos de 0.75 µs |
| 3. Picos y transitorios | Desconexión de bobinas y motores, descargas | Supresor **SMBJ26A** (600 W) en todas | SMBJ33A si la fuente es de 28 V o más |
| 4. Corto y sobrecorriente | Una carga en corto tumba todo | Medidor INA238 + programa (BASE, PIX); protección propia por salida (DO8) | **eFuse TPS2660** (60 V, 2 A, límite ajustable con ±5 %, polaridad invertida integrada) por rama |
| 5. Temperatura | Calentamiento lento | TMP1075 en la BASE; apagado térmico del NCV8406A | Mismo esquema en DIST 4 |

## 2. Salidas: de "transistor solo" a "interruptor inteligente"

| Generación | Pieza | Caída / resistencia | Corto en la salida | Placa |
|---|---|---|---|---|
| 1 | ULN2003 (Darlington) | ~1.1 V | Se daña | AP OUTPUT (retirada) |
| 2 | MOSFET de nivel lógico + driver | 2-3 mΩ | La protege el programa (lento) | BASE (8 A por canal, PWM) |
| **3** | **NCV8406A** (onsemi, interruptor de lado bajo protegido) | **210 mΩ máx.** | **Límite interno (~7 A) y apagado térmico con reinicio automático** | **AP PRO DO8** |
| 4 (futuro) | Interruptor de lado alto con diagnóstico (familia VN/BTS) | 10-100 mΩ | Límite + **aviso de falla por pata** | AP PRO DO8-HS |

**Cálculo de una salida del DO8 a 1.5 A:**
- P = I² × R = 1.5² × 0.21 = **0.47 W** en el SOT-223.
- Con el cobre de 2 oz, sube unos 30-40 °C sobre el ambiente.
- Por eso el límite de la placa es de 1.5 A por salida y 8 A en total, aunque la pieza aguante más.

**Lado bajo y lado alto:**
- **Lado bajo** (DO8): el interruptor está entre la carga y el 0 V. La carga queda siempre con +24 V en una pata. Es más simple y barato.
- **Lado alto:** el interruptor está entre el +24 V y la carga. La carga queda sin tensión al apagar. Lo pide la norma en algunas máquinas, y es mejor si el cable de la carga puede tocar el chasis.

## 3. Cargas inductivas (bobinas, válvulas, motores)

- **Al apagar** una bobina, su energía produce un pico de tensión.
  - En el DO8, el diodo SS14 de cada salida lo devuelve al +24 V.
  - El NCV8406A además tiene su propio enclavamiento.
- **Con diodo**, el contactor tarda un poco más en soltar (decenas de ms). Si hace falta soltar rápido, la opción es un diodo + zener (siguiente versión).
- **Motores DC:** la corriente de arranque es de 5 a 10 veces la nominal. Para ellos se usa un relevador de interfaz o un variador, nunca la salida directa.

## 4. Reducción por temperatura (derating)

Regla del proyecto: **usar como máximo el 60-70 %** de lo que dice la hoja de datos, porque el tablero puede estar a 40-50 °C.

| Pieza | Hoja de datos | Uso en AP ELECTRIC |
|---|---|---|
| JST VH (por pata) | 10 A | 8 A |
| JST XH (por pata) | 3 A | 1.5-2 A en salidas, 3 A en el bus |
| XT60 | 30 A continuos | 20 A |
| NCV8406A | 7 A (límite interno) | 1.5 A |
| Pista de 3 mm en 2 oz | ~10 A con 10 °C de aumento (IPC-2221) | 8 A |

## 5. Cobre y pistas

- **2 oz** en las placas de potencia (BASE, PIX, DIST 4, DO8): la mitad de resistencia y de calentamiento.
- **Planos** (zonas de cobre) en vez de pistas para las corrientes grandes, con varias vías en paralelo entre capas (cada vía de 0.3 mm ≈ 1 A).
- **Retorno de corriente:** el 0 V de potencia y el de la lógica se unen en un solo punto, cerca de la entrada.

## 6. Medir y actuar por hardware, no solo por programa

- El programa reacciona en milisegundos. Un corto necesita microsegundos.
- **Hoy:**
  - BASE: el INA238 tiene una alerta por hardware que enciende el LED de FALLA aunque el programa esté colgado;
  - DO8: cada NCV8406A se protege solo.
- **Siguiente:** eFuse por rama en DIST 4 (corta en microsegundos y avisa al CORE por una pata).

## 7. Piezas candidatas (por verificar antes de usarlas)

Según la regla del proyecto, una pieza entra a una placa solo con su código LCSC y su huella verificados.

| Pieza | Para qué | Estado |
|---|---|---|
| LM74700QDBVTQ1 (LCSC C2653623) | Diodo ideal en la entrada | Código visto; falta revisar la huella SOT-23-6 |
| TPS2660x (HTSSOP-16 / VQFN-24) | eFuse por rama en DIST 4 | Falta código LCSC y huella |
| Conector RJ45 para AP BUS PRO | Bus con cable de red armado | Candidatos sin huella verificada |
| M12 de 5 polos codificación A | AP BUS a prueba de agua | Por buscar |

## Fuentes

- onsemi NCV8406A: <https://www.onsemi.com/products/discrete-power-modules/protected-mosfets/ncv8406a> · LCSC C459816
- TI LM74700-Q1: <https://www.ti.com/product/LM74700-Q1> · LCSC C2653623
- TI TPS2660 (eFuse industrial de 60 V con protección de polaridad): <https://www.ti.com/product/TPS2660>
