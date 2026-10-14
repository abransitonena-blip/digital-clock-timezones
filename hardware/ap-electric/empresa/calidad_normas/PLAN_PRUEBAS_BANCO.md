# Plan de pruebas de banco de la primera tanda (7R Tour 24DC rev B)

Fecha: 2026-10-14 · Dueño: ap-calidad-normas (plan) y ap-hardware (ejecución) · Mejora `PUESTA_EN_MARCHA.md` §4 sin reemplazarlo: conserva sus etapas A-F y añade la etapa S (arranque y fallas) y la H (fuera de la primera tanda). Hoja de captura: `HOJA_CAPTURA_BANCO.csv` (una fila por prueba y por placa; copiar y llenar `placa_n`, `firmware`, `fecha`, `operador`, `medido`, `resultado`, `foto_o_captura`).

**Origen de los criterios:** los que vienen de HOJA_DATOS o PUESTA_EN_MARCHA llevan [R] o [C]; los marcados [H] son criterios de aceptación propuestos por calidad y se discuten con ap-hardware antes de usarlos; [CG] es conocimiento general que se debe confirmar en la norma o en la hoja. Ninguna medición de este plan existe todavía.

## Reglas de ejecución
1. **Sin red de 127/220 V** en ninguna prueba de este plan (CONTEXTO regla 6). B-H1 y B-H2 quedan fuera de la primera tanda.
2. Fuente de laboratorio con **limitación de corriente**, ajustada en cada paso (ver columna condición). Para polaridad invertida: 100 mA.
3. Probar primero en la placa de sacrificio (de las 2-3 ensambladas, designar **una** para las pruebas destructivas S3, S6 y S8). Las otras no reciben pruebas destructivas.
4. Parar al primer fallo y anotar. No seguir a la etapa siguiente con una falla abierta.
5. Registrar para cada placa: versión del firmware, ambiente (°C), lote de la fuente y del cable, fotos. Calibración: anotar el número de serie y la última calibración del multímetro y del osciloscopio (si no hay calibración, el valor es indicativo y se marca).
6. Con la placa 24DC verificar que **no están montados** J8, F2, RV1, PS1, D3 y C3 (B-A1).
7. Repetir los ensayos críticos de arranque (B-S1) en **todas** las placas ensambladas; son la prueba de aceptación de cada placa.

## Instrumentos mínimos
| Instrumento | Para qué | Notas |
|---|---|---|
| Fuente de laboratorio 0-30 V con limitación (y una fuente de 24 V riel DIN) | etapa C, S, polaridad | El PLAN supone fuente certificada para uso normal |
| Multímetro de 4½ dígitos preferible | resistencias, tensiones, µA de la pila | Anotar incertidumbre del manual del fabricante |
| Osciloscopio de 4 canales, ≥ 100 MHz, sondas 10:1 y una diferencial | arranque, caída de 24 V, RS-485 | Para arranque se necesitan 7 bobinas: 2 capturas de 4 y 3 canales o 7 LED + 1 captura |
| Generador de funciones 0-24 V a 1 kHz | conteo rápido | Salida con colector abierto o amplificada a 24 V |
| Adaptador USB-RS-485, PC con mbpoll o pymodbus | Modbus | Registrar versión del software |
| Termopares tipo K (≥ 6) y registrador | temperatura | Cámara térmica opcional |
| Lámparas de 24 V (7) | carga de ensayo | Medir su corriente antes |
| Cronómetro / PC con NTP | reloj, tiempos | |

## Etapas, valores esperados y tolerancias
Las tolerancias [H] no son requisitos del producto: son criterios para decidir si seguir probando.

| ID | Etapa | Prueba | Instrumento | Valor esperado | Tolerancia / criterio | Unidad |
|---|---|---|---|---|---|---|
| B-A1 | A | Inspección visual: puentes en U1,U2-U5,U6,U11,U9; polaridad de diodos/LED/relés/J15; confirmar 24DC sin J8,F2,RV1,PS1,D3,C3 | lupa o microscopio, fotos | 0 defectos | 0 defectos; cualquier defecto detiene | cuenta |
| B-A2a | A | Resistencia 24V a 0V | multímetro | > 1000 | > 1 kΩ (corte si menor) | ohm |
| B-A2b | A | Resistencia 5V a 0V | multímetro | > 1000 | > 1 kΩ | ohm |
| B-A2c | A | Resistencia 3.3V a 0V | multímetro | > 1000 | > 1 kΩ | ohm |
| B-A3 | A | Continuidad entre contactos de salida J1-J7 y 0V/USB | multímetro | abierto (OL) | sin continuidad | ohm |
| B-B1a | B | V5 en TP2 solo con USB | multímetro | 5.0 | ± 5 % | V |
| B-B1b | B | V3.3 en TP3 solo con USB | multímetro | 3.3 | ± 3 % | V |
| B-B1c | B | Tensión en TP1 (24 V) solo con USB (retroalimentación) | multímetro | ≈ 0 | < 0.5 V | V |
| B-B2 | B | Puerto serie y línea de arranque con versión | PC, consola | aparece puerto y línea de arranque | aparece en < 10 s | s |
| B-B3 | B | TEST sin 24 V: expansores y reloj | consola | expansores de lógica y reloj OK; retroalimentación avisa sin 24 V | según PUESTA_EN_MARCHA 6 | texto |
| B-C1a | C | Corriente en reposo al subir de 0 a 24 V (sin cargas, 7 relés apagados) | fuente de laboratorio con limitación 200 mA; multímetro | decenas de mA | < 100 mA a 24 V | mA |
| B-C1b | C | V24 en TP1 (después del diodo) a 24.0 V de fuente | multímetro | ≈ 23.5 (caída de SS34) | ± 1 V; registrar caída real | V |
| B-C1c | C | V5 en TP2 con 24 V | multímetro | 5.0 | ± 5 % | V |
| B-C2 | C | TEST: expansores 0x20-0x23 contestan, identificación 7R Tour, sin bobinas con tensión | consola | 4 de 4 | 4 de 4 | cuenta |
| B-C3 | C | TEST RELES SI (sin cargas): cada relé hace clic y su bobina se detecta | consola, oído, osciloscopio | 7 de 7 | 7 de 7 | cuenta |
| B-C3b | C | Tensión en bobina energizada (por canal) | multímetro | ≈ 22-23 | ≥ 21.6 V (90 % de 24 V) [H] | V |
| B-C4 | C | DIP 1-7 fuerza el relé con ESP32 en reset; programa ve «forzado»; con todos los DIP apagados ningún clic | consola, ESP32 en reset (EN a 0 V) | 7 de 7 + 0 clics | 7 de 7 | cuenta |
| B-D1a | D | Umbral de encendido de la entrada n (subir tensión hasta que el LED y la consola cambien) | fuente variable, multímetro | ≈ 11 (diseño [C]) | se registra; aceptable 8-14 V [H]; debe estar ≥ 5 V | V |
| B-D1b | D | Umbral de apagado de la entrada n (bajando) | fuente variable | ≈ 5 (diseño [C]) | < 5 V no debe estar activa; registrar histéresis | V |
| B-D1c | D | Entrada a 5 V no enciende y a 15 V sí (meta tipo 1/3) | fuente variable | apaga / enciende | 8 de 8 entradas | cuenta |
| B-D1d | D | Corriente de entrada a 24 V | multímetro en serie | 4.8 | ± 20 % [H] | mA |
| B-D1e | D | Entrada a 30 V sin daño; luego repetición de umbral | fuente variable limitada 20 mA | sin daño; umbrales sin cambio | ± 0.5 V del valor previo | V |
| B-D2a | D | Conteo rápido 100 Hz, entrada 1 (IO0) y 2 (IO20), 10 000 pulsos | generador de funciones 0-24 V, consola | 10 000 | 0 pérdidas | pulsos |
| B-D2b | D | Conteo rápido 500 Hz, 50 000 pulsos | generador | 50 000 | pérdida ≤ 0.1 % [H]; registrar | pulsos |
| B-D2c | D | Conteo con contacto de relé y con pulsador (rebote) | pulsador, osciloscopio | 1 cuenta por acción | 100 acciones, 0 dobles | cuenta |
| B-D3 | D | Hora conservada 1 min sin USB ni 24 V con batería | reloj de referencia | error ≤ 2 s | ≤ 2 s | s |
| B-D4 | D | Sin batería: pierde hora y TEST avisa; el resto funciona | consola | aviso y operación normal | sí | texto |
| B-D5 | D | Deriva del reloj en 7 días (leer hora del equipo cada 24 h vs. hora de red/NTP de la PC) | PC con NTP; consola | /deriva/ ≤ 1 min/mes | ≤ 23 ppm equivalente [H]; registrar ppm calculadas | ppm |
| B-D6 | D | Corriente hacia la pila con 3.3 V presente | multímetro µA en serie con la pila | 0 | < 1 µA [H]; cualquier valor positivo notable es falla | µA |
| B-E1a | E | Leer registros de entrada 100, 101 y 153 por Modbus | adaptador USB-RS-485, mbpoll | lectura sin error | 0 errores en 1000 lecturas | errores |
| B-E1b | E | Escribir reg. 300 = 1 (Reset) sin permiso local | mbpoll | excepción 04 | excepción 04 | código |
| B-E1c | E | Barrido 9600/19200/38400/57600/115200 Bd × 8N2/8E1/8O1 | mbpoll | todas contestan | 15 de 15, 1000 tramas sin error por combinación | errores |
| B-E2 | E | Pasos de PACKML.md: estados, paros, microparos, OEE | consola, entradas simuladas | según PACKML.md | según PACKML.md | texto |
| B-E3a | E | Nivel diferencial del bus en reposo con polarización | osciloscopio diferencial (o 2 canales A-B) | ≥ 200 mV diferencial | ≥ 200 mV [CG: umbral de receptor RS-485] | mV |
| B-E3b | E | Forma de onda en TP (DE) y TP (RX) a 115200 Bd | osciloscopio 4 canales | limpia, sin rebotes ni bordes dobles | sin cruces falsos; sobreimpulso < 20 % [H] | % |
| B-E3c | E | Tramas sin error en 10 000 con 10 m de cable y 7 relés conmutando cada 1 s y una lámpara de 24 V | mbpoll, osciloscopio | 0 errores CRC | ≤ 1 error en 10 000 [H]; si falla, parar | errores |
| B-E3d | E | Ruido de modo común: inyectar con generador 1 Vpp 1 MHz en 0 V aislado del bus y ver CRC | generador | sin errores | registrar nivel de falla | V |
| B-E4 | E | Wi-Fi: sin SSID tras encender; SSID tras MODO 3 s; con DIP 8 activo no aparece | teléfono/analizador Wi-Fi | no / sí / no | 3 de 3 | cuenta |
| B-E5 | E | Vínculo UDP entre dos equipos y paquete malformado | 2 placas, PC | vínculo ok; malformado ignorado | sin reinicio ni salida espuria | texto |
| B-F1 | F | Lámpara de 24 V por canal: encender/apagar 100 veces | lámpara 24 V, multímetro | 100/100 | 100/100 | cuenta |
| B-F2a | F | Consumo en reposo y Wi-Fi apagado | multímetro/fuente | registrar | < 100 mA [H] | mA |
| B-F2b | F | Consumo con 7 relés activos, Wi-Fi apagado | fuente | ≈ 150 | 105-195 mA (± 30 %) [H] | mA |
| B-F2c | F | Consumo con 7 relés y pico de Wi-Fi | osciloscopio con pinza o resistor shunt | ≈ 200 | registrar pico y duración; ≤ 3 A (F1) | mA |
| B-F3 | F | Temperatura con 7 relés activos 4 h en carcasa cerrada (relés, bornes, U1, U7, U9, pistas) a Tamb registrada | termopares tipo K ×6+, registrador; cámara térmica opcional | registrar ΔT | ninguna pieza > 85 °C absolutos (límite del relé [E]); ΔT estable < 1 K/30 min | °C |
| B-S1 | S | ARRANQUE: nadie hace clic al energizar. 20 energizaciones: 10 con escalón (interruptor de la fuente) y 10 con rampa lenta (1 V/s); con y sin USB; en las 7 bobinas (nodo bajo, canal 1-4 simultáneos + 5-7) | osciloscopio ≥ 4 canales, una captura por serie + LED de bobina + oído | 0 pulsos en las 7 bobinas | nodo bajo de cada bobina nunca < 20 V [H] (bobina < 4 V); 0 clics; LED apagados | V |
| B-S2a | S | CAÍDA de 24 V brusca con 7 relés activos: tiempo hasta que abren todos y rebote | osciloscopio en V24 y en un contacto (con lámpara de 24 V + resistor de pull-up de prueba) | todos abren; ninguno vuelve a cerrar | 7 de 7 abren; sin re-cierre durante la caída | ms |
| B-S2b | S | CAÍDA lenta de 24 V (rampa 24 → 0 V en 30 s) | fuente programable u osciloscopio | registrar tensión de apertura de cada relé y tensión a la que el microcontrolador reinicia (brown-out) | ningún relé cerrado con reinicio del ESP32 a mitad; sin chasquidos al volver | V |
| B-S2c | S | Retorno de 24 V según política (APAGADO, ÚLTIMO, ENCENDIDO) en cada tipo de canal | consola, 3 corridas | política aplicada; canal de proceso siempre APAGADO | sin excepción | cuenta |
| B-S3a | S | POLARIDAD INVERTIDA de 24 V: -24 V, fuente limitada a 100 mA | fuente con limitación, multímetro, cámara térmica | corriente ≈ 0 | ≤ límite de la fuente, TP1 ≈ 0 V, sin calentamiento; luego funciona con polaridad correcta (TEST 4/4) | mA |
| B-S3b | S | POLARIDAD INVERTIDA en entradas (COMI/IN a -24 V, limitada 20 mA) | fuente limitada | LED apagado; sin daño | umbrales sin cambio tras la prueba (B-D1a ± 0.5 V) | V |
| B-S4a | S | USB conectado sin 24 V: relés, retroalimentación y V24 (secuencia de 4: USB→24V, 24V→USB, quitar USB con 24V, quitar 24V con USB) | multímetro, osciloscopio en bobinas | 0 clics; TP1 ≈ 0 con solo USB; sin reinicios al agregar 24 V | 0 clics en 20 secuencias; sin reinicio del ESP32 salvo el esperado | cuenta |
| B-S4b | S | Con USB y 24 V presentes, el 5 V de la placa no retroalimenta al USB de la PC | multímetro en VBUS | VBUS ≈ 5.0 | dentro de 4.75-5.25 V (rango USB) [CG] | V |
| B-S5 | S | Programa trabado: tiempo hasta que las salidas abren / se reinicia | consola con orden de bloqueo de prueba si existe; osciloscopio | reinicio en 8 s; salidas mantenidas hasta 8 s | 8 s ± 1 s | s |
| B-S6 | S | Falla de 3.3 V con 24 V presentes (sacar 3.3 V con resistencia de carga) | resistor de carga, osciloscopio | relés abren | 7 de 7 abren | cuenta |
| B-S7 | S | Corte de comunicación Modbus con vigilancia = 10 s | mbpoll, cronómetro | canal apaga a los 10 s | 10 s ± 1 s; no se reenciende al volver | s |
| B-S8 | S | Quitar un expansor I2C (desoldar o puentear) y ver falla informada y salidas | consola | falla informada «expansor I2C»; sin salida espuria | falla informada en ≤ 5 s [H] | s |
| B-S9 | S | Barrido de tensión de alimentación 17, 19.2, 24, 30, 32 V con 7 relés activos y Wi-Fi | fuente variable, multímetro | funciona 19.2-30 V | TEST 4/4 y sin reinicios 19.2-30 V; a 17 V y 32 V solo registrar | V |
| B-H1 | H | FUERA de la primera tanda: irrupción de lámparas LED reales (127 V) con transformador de aislamiento, persona competente | pinza de corriente rápida / shunt, osciloscopio aislado | registrar pico y duración | según PLAN_VERIFICACION 2.4 | A / ms |
| B-H2 | H | FUERA de la primera tanda: vida eléctrica de muestra | banco de maniobras | registrar fallas | PD | maniobras |

## Notas por prueba crítica
- **B-S1 (arranque):** conectar el osciloscopio al nodo bajo de la bobina (salida del ULN2003A) de cada canal, referencia 0 V. En reposo debe estar a ≈ 24 V (sin corriente de bobina). Un descenso sostenido indica excitación. Capturar con disparo por flanco descendente por debajo de 20 V, modo único, y repetir 20 veces; guardar las capturas en `evidencia/B-S1_<placa>_<n>.png` (carpeta por crear por quien ejecute). Además de las 20 energizaciones, hacer 5 con el botón MODO pulsado y 5 con la entrada 1 a 24 V al encender.
- **B-S2 (caída de 24 V):** usar un interruptor de sobremesa para el corte brusco. Medir el tiempo entre el flanco de caída de 24 V y la apertura de cada contacto (lámpara de 24 V con resistencia de monitoreo en serie sobre contacto o tensión a través del contacto). El PLAN dice que los relés abren, pero el valor de tiempo es PD.
- **B-S3 (polaridad):** antes de energizar en inversa, revisar el esquema para saber si SMBJ33A queda antes o después del SS34. Si queda antes, el fusible F1 de 3 A actuará: por eso la limitación de 100 mA y el uso de la placa de sacrificio.
- **B-S4 (USB y 24 V):** 4 secuencias × 5 repeticiones; en cada una capturar bobinas, TP1, TP2 y TP3. Registrar si el ESP32 reinicia.
- **B-E3 (RS-485):** registrar longitud del cable, tipo (par trenzado), terminaciones y la posición de los puentes de polarización.
- **B-F3 (temperatura):** Tamb entre 20 y 30 °C registrada. Con 24 V CC no se puede probar el calentamiento a 10 A de forma representativa (el contacto es de CA y 24 V CC con 10 A no es la condición declarada ni la meta de calor del producto): el calentamiento del contacto con corriente se hace en L-01 o con persona competente fuera de la primera tanda, y con la corriente DC que fije la hoja original del relé (PD). Aquí se mide el calor de bobinas, regulador y ULN2003A.

## Qué reportar al final de la tanda
Una tabla placa × prueba con PASA/FALLA/NA, las capturas, y la lista de hallazgos con la propuesta de cambio para rev C. Se actualiza `MATRIZ_REQUISITOS_EVIDENCIA.csv` (columna `estado`) y `FMEA_AP_MONITOR_24.csv` (columna D) solo con base en datos medidos.

## Propuestas de cambio a PLAN_VERIFICACION.md (no aplicadas)
1. Añadir a la sección 2.1 las pruebas B-S1 (20 energizaciones, 7 bobinas, con y sin USB y MODO) y B-S4 (USB con y sin 24 V).
2. Añadir a 2.2 las pruebas B-S2b (caída lenta), B-S5 (tiempo del vigilante) y B-S6 (3.3 V).
3. Reconciliar 2.4 «irrupción de lámparas de 127 V» con CONTEXTO regla 6: marcarla «fuera de la primera tanda; solo persona competente con transformador de aislamiento y protección».
4. En la sección 3 dividir en «3a Pre-cumplimiento» (pre-escaneo EMC, ESD y ráfagas) y «3b Acreditado», y enlazar a PLAN_ENSAYOS_LABORATORIO.md.
5. Cambiar «Radio: homologación (NOM-208 / IFT-008-2015, autoridad CRT) o uso de un módulo con homologación vigente» por «el certificado del módulo no se transfiere automáticamente; consultar a la CRT o a un laboratorio; ver L-12».
6. Corregir «IEC 61010-2-201» como referencia: citar la edición 2024 y IEC 61131-2:2017 solo para funcionalidad y EMC (la seguridad se movió a la serie 61010; ver fuentes).
7. Añadir a la sección 5 riesgos: contactos con tensión de usuario en el 24DC (RG-02), vigilante de 8 s (RG-18), arranque con USB (FM-02), cambios de BOM (RG-16).
8. Añadir columnas «ensayo», «fecha» y «quién» a las tablas de riesgos de la sección 5.
