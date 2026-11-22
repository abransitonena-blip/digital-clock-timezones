# Nodo AP · decodificador DMX512 → RGBW con CH32V003

Es el nivel más barato de la familia AP. Un **CH32V003** (RISC‑V de WCH, de unos 0.10–0.20 USD) va soldado directo en la placa. Recibe **DMX512 por cable** y maneja **4 canales PWM** (R, G, B y W) para una tira de ánodo común de 12–24 V.

Sirve para luminarias que se repiten: muchos nodos en una sola línea DMX, alimentada por una consola, por una interfaz Art‑Net → DMX o por otro equipo.

## Placa (`placa/`)
- **Tamaño:** 50 × 38 mm, 2 capas.
- **Ruteo:** propio, igual que el de las placas del cubo, con DRC sin errores, 0 redes abiertas y 53 vías (rev. B).
- **Entrada:** J1 recibe 12–24 V. El fusible F1 es de 8 A, así la carga máxima de 5 A queda al 63 % de su nominal, con margen para la temperatura. La corriente de las tiras va por cobre de 2.8 mm hasta V+ de J2.
- **Lógica a 5 V:** un 78L05 (SOT‑89, acepta hasta 30 V) alimenta el CH32V003 (que trabaja de 2.8 a 5.5 V) y el MAX485. D1 protege la lógica si la polaridad está invertida. R30 (150 Ω, 1206) va en serie antes del 78L05 y se lleva parte de su calor; aun así el regulador tiene ≥ 6.7 V de entrada desde 12 V.
- **DMX:**
  - transceptor RS‑485 de 5 V fijo en recepción, con SM712 contra descargas;
  - dos borneras en paralelo (J3 entra, J4 sale) para encadenar nodos;
  - terminación de 120 Ω con el puente JP1, que se pone solo en el último nodo.
  - En las borneras: 1 GND · 2 D− · 3 D+, igual que los pines 1, 2 y 3 del XLR.
- **Salidas:** 4 × N‑MOSFET de nivel lógico en DFN 3.3 × 3.3 (≤ 10 mΩ a 4.5 V), manejados directo por TIM1. El pad de drenaje grande pasa el calor al cobre. Hasta 3 A por canal y 5 A en total.
- **Térmico (rev. B):** según `../analisis/informe_termico.md`, a 40 °C con 2 × 3 A en caja de plástico los MOSFET llegan a ≈ 88 °C (antes ≈ 147 °C con los AO3400A). En perfil de aluminio con gap pad, a ≈ 56 °C. Los capacitores no quedan junto a piezas calientes.
- **Interfaz:** botón APRENDER, LED de estado y header SWIO para el WCH‑LinkE.
- **Huellas:** la TSSOP‑20 y la SOT‑89 se leen de la librería oficial de KiCad (`huellas_kicad/`).
- **Archivos:** Gerber en `nodo_ap_gerbers.zip`, BOM y CPL, esquema en `esquema_nodo_ap.pdf` y vistas.

## Firmware (`firmware/`)
Escrito sin SDK: arranque, vector de interrupciones, linker y registros propios (`ch32v003_reg.h`). Las direcciones de registros se cotejaron con el manual de WCH y con `ch32v003hw.h` de ch32v003fun (MIT).

- **DMX:**
  - el UART recibe a 250 kbaud por interrupción;
  - la ruptura se detecta como error de trama con dato 0;
  - hay doble búfer: el cambio de búfer ocurre en la interrupción, así que no se pierde el código de inicio de la trama siguiente;
  - se ignoran los códigos de inicio distintos de 0 (RDM, texto).
- **Salidas:** PWM de 3.9 kHz y 10 bit con curva gamma 2.2 interpolada, con error menor al 1 %. Se puede elegir lineal.
- **Dirección:**
  1. Se pulsa APRENDER.
  2. En la consola se pone **un** canal en ≥ 200 y el resto en < 50.
  3. Con 3 tramas iguales, ese canal queda como dirección y se guarda en la última página de flash (64 B, con firma y CRC‑8).
- **Sin señal:** mantiene el último valor y el LED da un destello por segundo.
- **Tamaño:** 2.8 KB de 16 KB de flash y 1.1 KB de 2 KB de RAM.
- **Compilar:** `firmware/compilar.sh` corre las 60 pruebas del núcleo en la PC y compila `nodo.bin` con `gcc-riscv64-unknown-elf` (`-march=rv32ec_zicsr -mabi=ilp32e`).
- **Grabar:** con WCH‑LinkE por SWIO, por ejemplo `minichlink -w nodo.bin flash -b`.

## Pendiente / verificar antes de fabricar
- **Nada de esto se ha probado en hardware.** El firmware compila y el núcleo pasa sus pruebas, pero la capa de registros no se ha corrido en un chip real.
- **Pinouts:**
  - el del CH32V003 se verificó contra el símbolo oficial de KiCad;
  - PD2 = T1CH1 y PC4 = T1CH4 se confirmaron con los ejemplos de ch32v003fun;
  - PA1 = T1CH2 y PC3 = T1CH3 (mapeo por defecto) hay que confirmarlos en la hoja de datos;
  - hay que verificar también el del 78L05 en SOT‑89 (1 OUT · 2 GND · 3 IN) y el del MOSFET DFN elegido (1‑3 S · 4 G · pad D).
- **Cubo como maestro:** el Cubo AP **v3** con el puente JP4 cerrado transmite DMX. Con `DMX SALIDA ESPEJO` los nodos (en las direcciones 1, 5, 9…) copian el color del cubo; con `DMX SALIDA PUENTE`, el universo de Art‑Net/sACN. El v2 solo recibe. También sirve cualquier consola o interfaz Art‑Net → DMX.
