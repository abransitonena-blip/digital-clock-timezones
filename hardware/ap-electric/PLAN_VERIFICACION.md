# AP Electric: plan de verificación

Lo que se comprueba por software **no sustituye** a los ensayos eléctricos: un DRC aprobado o un render no hacen un producto «listo para vender».

## 1. Ya comprobado por software (estado: hecho)

| Qué | Cómo | Resultado |
|---|---|---|
| Esquema 7R Tour y AP Home | ERC de KiCad 9 | 0 errores |
| Placa AP Home | DRC con reglas propias: red-baja tensión ≥ 6.4 mm en el aire y por la superficie; ≥ 2.0 / 2.4 mm entre redes de red | 0 violaciones, 0 sin conectar, paridad 0, reglas de JLCPCB 0 |
| Placa 7R Tour rev B | Igual; además el bus RS-485 aislado ≥ 1.5 mm de la lógica (aislamiento funcional, no de seguridad) | 0 violaciones, 0 sin conectar, paridad 0, reglas de JLCPCB 0 |
| BOM | Todas las piezas con código LCSC (relés, fuentes, aisladores verificados por búsqueda en lcsc.com / jlcpcb.com) | Ver `fabricacion/jlcpcb` |
| Programa | Compila para ESP32-C3 (arduino-cli 3.1.1) | 1.06 MB, 53 % |
| Unidad PackML | `tools/probar_apbus.sh` (`prueba_packml.cpp`) | Ciclo de estados, comandos inválidos, reglas de reanudación remota, fallas, tiempos por estado, OEE, microparos y mapa Modbus PackTags. Falta probarla en una máquina real |
| Lógica | `tools/probar_apbus.sh` | Arranque seguro, antirrebote, pulsador / interruptor / conmutador, minutero, Modbus (lectura, escritura, excepciones, difusión, CRC), vigilancia de comunicación, PLC, retroalimentación de bobinas, mantenimiento, límite de escrituras |

## 2. Banco de prototipo (con equipo de laboratorio básico)

1. **Funcional sin carga.**
   - Arranque con todas las salidas apagadas: osciloscopio en las bobinas durante el encendido; ningún pulso.
   - Botones, LEDs, entradas: umbrales de encendido y apagado con fuente variable (meta IEC 61131-2 tipo 1/3).
   - DIP manual con el ESP32 en reset.
2. **Fallas provocadas.**
   - Desconectar 24 V con relés activos.
   - Detener el programa (vigilante): medir el tiempo hasta que las salidas abren.
   - Cortar la comunicación Modbus.
   - Quitar un expansor I2C.
   - Invertir la polaridad de 24 V y de las entradas.
3. **Consumo**: en espera y con todos los canales.
4. **Irrupción de lámparas LED de 127 V reales** (varias marcas del mercado mexicano):
   - medir pico y duración por lámpara y por grupo;
   - ciclos de maniobra con cada combinación;
   - fijar el número de lámparas o los W admisibles por canal, o la necesidad de contactor.
5. **Calentamiento**:
   - 7 canales a la corriente meta durante 4 h en la carcasa cerrada;
   - termopares en relés, bornes y pistas;
   - curva de reducción por temperatura ambiente.
6. **Vida eléctrica** de muestra con carga de alumbrado representativa.

## 3. Laboratorio acreditado (antes de vender)

- Rigidez dieléctrica red-SELV, red-RS-485, entradas-lógica, canal-canal.
- Resistencia de aislamiento; corriente de fuga (Home).
- Calentamiento normativo; sobrecarga y cortocircuito con la protección declarada. El SCCR solo si se evalúa.
- Inflamabilidad de la carcasa (hilo incandescente).
- Prueba del dedo de prueba en bornes y receptáculo.
- Para la clavija y el receptáculo del Home Plug: fuerzas de inserción.
- EMC: emisiones conducidas y radiadas, inmunidad (ESD, transitorios rápidos, sobretensiones, caídas de tensión).
- Radio: homologación (NOM-208-SCFI-2016 / IFT-008-2015, autoridad CRT) o uso de un módulo con homologación vigente.
- IP e IK si se van a declarar.
- Evaluación de conformidad NOM-003-SCFI-2014 por SKU con un organismo acreditado; normas de producto a definir con él:
  - IEC 60669-2-1 para los Home;
  - IEC 61010-2-201 para el 7R Tour.

## 4. Pendientes concretos

1. Hojas originales (PDF) de las piezas críticas. Desde este entorno no se pudieron descargar: se usaron datos de páginas de fabricante y distribuidor vistos por búsqueda.
2. Significado de «7R» y registro de marca.
3. Proveedor de la clavija y el receptáculo certificados del Home Plug.
4. Límites de producto por canal (sección 2.4 y 2.5).
5. Reemplazo del G2RL por un relé con valor de irrupción publicado (G5RL-1A-E-HR) si las mediciones lo piden. Requiere su dibujo de montaje.

## 5. Riesgos conocidos de la rev B del 7R Tour (revisar en la primera tanda)

Revisión de escritorio del diseño, hecha por el equipo de diseño; **no sustituye medir**. «[CG]» = conocimiento general por confirmar con la hoja del fabricante.

| # | Riesgo | Por qué | Qué hacer |
|---|---|---|---|
| 1 | El reloj puede adelantar o atrasar unos minutos por mes | El cristal elegido (32.768 kHz, 12.5 pF, C32346) puede no coincidir con la capacitancia de carga que pide el PCF8563 (7 pF típica [CG]) | Confirmar en la hoja del PCF8563; medir la deriva comparando contra la hora de la red durante varios días; si pesa, cambiar el cristal en la rev C. Mientras tanto la hora se reajusta por Modbus o consola |
| 2 | Tres pistas largas (INT, RS_DE, RS_RX, ≈ 100 mm) trazadas por una herramienta propia | El ruteador automático no las unió | Revisarlas en KiCad antes de pedir; con osciloscopio, verlas en TP (DE, RX) a 9600-115200 Bd: deben verse limpias |
| 3 | Las entradas son PNP | Diseño de la rev B | No conectar sensores NPN; planear la rev C |
| 4 | Batería del reloj | Conector de 2 polos con un OR de diodos Schottky (BAT54C); una pila no recargable no debe recibir corriente | Medir que, con 3.3 V presentes, no entra corriente a la pila; polaridad marcada en la serigrafía |
| 5 | Pines de arranque del ESP32-C3 | IO2, IO8 e IO9 son de arranque; llevan I2C y el botón de modo | La prueba automática `tools/revisar_pines.py` confirma que la placa y el programa coinciden; en banco, comprobar que arranca con y sin 24 V |
| 6 | Salidas del expansor al encender | Antes de que el programa las configure las patas del TCA9554 son entradas | Hay una resistencia de 10 kΩ a 0 V por canal; comprobar con el osciloscopio que ningún relé hace clic al energizar |
| 7 | Cobre de 2 oz | No se confirmó que JLCPCB lo ofrezca también con ensamble | Verlo en la cotización antes de pagar |
| 8 | Capacidad de contactos y calentamiento | Todos los límites por canal están en PD | Ensayos de la sección 3 antes de declarar cualquier valor |

