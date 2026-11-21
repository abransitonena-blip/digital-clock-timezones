# Cubo AP · Placa de control v1 (68 × 64 mm, 2 capas)

Es la placa que va dentro del cubo, encima del cartucho de potencia. Recibe 12–36 V del cartucho y entrega a la tira LED:
- un voltaje fijado por la tarjeta y ajustable desde la app (5–24 V, hasta 5 A);
- 4 canales PWM (R, G, B, W) de ánodo común;
- una salida de datos WS2812.

Mide V, A, °C y el voltaje de entrada, y se controla por Bluetooth con el firmware de `../firmware`.

| Vista | Archivo |
|---|---|
| Cómo se verá fabricada (arriba / abajo) | `vista_placa_arriba.png`, `vista_placa_abajo.png` |
| Cobre de cada capa | `vista_cobre_arriba.png`, `vista_cobre_abajo.png` |
| Colocación de componentes | `vista_colocacion.png` |
| Esquema (7 hojas A3) | `esquema_placa_control.pdf` |

## Fabricar
1. Sube `cubo_ap_control_gerbers.zip` a JLCPCB (o similar) con estas opciones: 2 capas, 1.6 mm, **cobre de 2 oz recomendado** (sirve 1 oz), acabado HASL sin plomo y máscara verde.
   - Contenido: F_Cu, B_Cu, F_Mask, B_Mask, F_Paste, F_Silkscreen, Edge_Cuts, PTH.drl y NPTH.drl. Unidades en mm; el origen es la esquina inferior izquierda.
2. Para el ensamble, usa `bom.csv` y `cpl.csv`:
   - Llena la columna LCSC con piezas en existencia que cumplan la descripción.
   - En la vista previa de JLC revisa la rotación de cada pieza; las convenciones cambian según la librería.
3. Las piezas de inserción (J1, J2, J3 y las tiras para el SuperMini) son más baratas de soldar a mano.

Reglas usadas, todas dentro de lo estándar:
- pista mínima 0.2 mm;
- separación 0.2 mm entre pistas y 0.3 mm de los planos a otras redes;
- vía de 0.6/0.3 mm;
- cobre a ≥0.4 mm del borde.

## Cómo se diseñó (todo regenerable)
```
python3.11 revisar.py   # colocación: encimes, bordes, barrenos, pads a <0.2 mm, redes de un pin
python3.11 fab.py       # enrutado A* en 2 capas + zonas de potencia + planos GND + DRC + conectividad
python3.11 gerber.py    # Gerber, Excellon, serigrafía, BOM, CPL y zip
python3.11 vista.py     # vistas (SVG) -> PNG:  node svg2png.cjs archivo.svg archivo.png 1400
python3.11 esquema.py && node html2pdf.cjs esquema.html esquema_placa_control.pdf
```
- `diseno.py` es la **única fuente de verdad**: componentes, valores, conexiones, posiciones, zonas de potencia y anchos de pista. El esquema, la placa y la BOM salen de ahí, así que no pueden contradecirse.
- **Resultado actual:**
  - 83 componentes, 51 redes, 207 pistas (827 mm) y 159 vías.
  - **DRC: 0 errores. Redes abiertas: 0.**
  - Los Gerber se volvieron a leer con pygerber, una herramienta independiente: las medidas son 68 × 64 mm y las capas coinciden con las vistas.
- **Potencia:** los caminos de corriente alta son zonas de cobre anchas en la capa superior:
  - entrada → fusible → MOSFET de polaridad → reductor;
  - nodo SW → inductor → capacitores → shunt → V+;
  - cada canal: MOSFET → bornera.

  La capa inferior es casi toda plano de GND.

## Bloques
1. **Entrada.**
   - Fusible de 6.3 A.
   - P-MOSFET contra inversión de polaridad, con zener de compuerta.
   - TVS de 40 V.
   - 100 µF + 3 × 10 µF.
2. **Reductor TPS54560** (60 V, 5 A, 400 kHz).
   - Vout = 0.8 × (1 + 29.4k / R_B). R_B viene en la tarjeta (conector J3: FB · GND · ID).
   - El DAC MCP4725 baja el voltaje a través de BAT54 + 47k.
   - Shunt de 5 mΩ + INA226.
3. **5 V auxiliar** con LMR14006 para los drivers, el buffer WS2812 y el SuperMini. D6 evita alimentar al USB de la PC.
4. **ESP32-C3 SuperMini** en tira hembra (enchufable). La antena sobresale 1 mm del borde, sin cobre debajo, y queda bajo la ventana delgada de la tapa.
5. **Canales:** 2 drivers UCC27524 (conmutan en ~20 ns, así los MOSFET no se calientan a 19 kHz) y 4 N-MOSFET DFN 3.3 × 3.3. El 74AHCT1G125 sube los datos a 5 V.

## Antes de mandar a fabricar: revisar (honesto)
**No se ha fabricado ni probado.** No pude bajar las hojas de datos (la red de este entorno las bloquea), así que estos datos salen de memoria y **hay que confirmarlos contra el datasheet de la pieza exacta que compres**:
- **Orden de pines del SuperMini.** Con el USB hacia atrás y vista desde arriba:
  - izquierda: 5V, GND, 3V3, IO4, IO3, IO2, IO1, IO0;
  - derecha: IO5, IO6, IO7, IO8, IO9, IO10, IO20, IO21.

  Hay clones con otro orden.
- **Pinout y huella de cada integrado:**
  - TPS54560 (HSOP-8 PowerPAD): 1 BOOT, 2 VIN, 3 EN, 4 RT, 5 FB, 6 COMP, 7 GND, 8 SW.
  - LMR14006 (SOT-23-6): 1 CB, 2 GND, 3 FB, 4 SHDN, 5 VIN, 6 SW.
  - INA226 (VSSOP-10), MCP4725 (SOT-23-6), UCC27524 (SOIC-8) y 74AHCT1G125 (SOT-23-5): su orden de pines está en `esquema_placa_control.pdf`.
- **Huellas genéricas:** MOSFET DFN 3.3 × 3.3 (S-S-S-G + pad de drenador), inductor de 12.5 mm, electrolíticos de 6.3 y 8 mm, borneras de 5.08 mm.
- **Compensación del TPS54560** (62k / 10 nF / 68 pF): calculada a mano para cruce ≈ 15 kHz a 12 V. Confírmala con la herramienta de TI (WEBENCH o la calculadora del datasheet).
- **INA226:** el sentido no es Kelvin puro; se conecta a las zonas junto al shunt. Calibra la corriente con un amperímetro (offset y ganancia en firmware).

## Primera prueba sugerida
1. **Sin SuperMini ni tarjeta**, alimenta 24 V con límite de corriente de 100 mA. Mide:
   - 5 V en TP2;
   - ~0 V en TP4: sin tarjeta la salida se cae a ~0.8 V, y con el EN apagado queda en 0.
2. Coloca la tarjeta de 12 V. Pon EN en alto con un puente de 3.3 V a la pata IO4 y mide 12.0 V en TP4.
3. Coloca el SuperMini con el firmware y prueba con una carga resistiva antes de conectar la tira.
4. Sube la corriente poco a poco y vigila la temperatura de L1, D2 y RS.
