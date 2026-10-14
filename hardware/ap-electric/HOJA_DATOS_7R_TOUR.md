# AP Electric Industrial · 7R Tour: hoja de datos preliminar

> **Estado: CONCEPTO / prototipo de diseño.**
> - El diseño pasa la revisión eléctrica (ERC) y la de reglas de la placa (DRC); el programa compila y pasa sus pruebas en la PC.
> - No se ha fabricado, medido ni certificado. **No es una hoja de datos comercial**: muchas cifras son metas o cálculos.
>
> Origen de cada valor:
> - **[R]** requisito propuesto
> - **[C]** cálculo
> - **[E]** especificación del componente (hoja del fabricante o del distribuidor)
> - **[M]** medido (hoy ninguno)
> - **[A]** límite aprobado del producto (hoy ninguno)
> - **PD** = por determinar

| | |
|---|---|
| Modelos (SKU) | **7R Tour 24DC** (24 V CC externos) · **7R Tour CA** (fuente de red integrada). La misma placa rev B: el CA monta J8, F2, RV1, PS1, D3 y C3 |
| Función | Controlador de 7 salidas por relé para alumbrado y para mando de contactores; 8 entradas de 24 V; lógica tipo PLC; Modbus RTU esclavo aislado |
| Nombre | «7R» = siete canales de relé: **supuesto pendiente de confirmar** |
| Revisión | Placa **rev B** (conteo rápido en IO0/IO20, reloj PCF8563 con batería externa, 11 puntos de prueba) · programa AP Control con PackML/OEE · ver [DISENO_FINAL.md](DISENO_FINAL.md) |

## Cargas

| Carga | Estado |
|---|---|
| Lámparas incandescentes y halógenas, focos LED de 127/220 V no regulables | Previstas; límite por canal **PD** (meta 10 A resistivos [R]) |
| Luminarias LED con driver, balastros electrónicos | **PD**: la irrupción de drivers LED puede pasar de 10 veces la nominal. Se fijará el número de luminarias por canal tras medir. Si no alcanza: contactor externo |
| Bobinas de contactores y relés de CA | Previstas (mando); potencia de bobina admisible **PD** |
| Motores, bombas, compresores, resistencias grandes | **Solo mediante contactor externo** elegido por categoría de utilización (AC-3, AC-1…) |
| Cargas en CC de más de 30 V | **Excluidas** (el contacto de CA no queda autorizado para CC) |
| 208/400/480 V, trifásico | **Excluidas** en este SKU (otro SKU, otro aislamiento) o contactor externo |
| Regulación de brillo | **No** |
| Funciones de seguridad (paro de emergencia, enclavamientos de protección de personas) | **No**: no es un equipo de seguridad |

## Alimentación

| | Valor | Origen |
|---|---|---|
| 7R Tour 24DC | 24 V CC SELV de una fuente certificada; rango de diseño 19.2-30 V | [R] |
| Consumo | ≈ 0.15 A a 24 V (3.6 W) con los 7 relés activos y Wi-Fi apagado; ≈ 0.2 A con picos de Wi-Fi | [C] PD [M] |
| Protección interna | Fusible rápido de 3 A (F1); diodo serie contra polaridad invertida (SS34); supresor SMBJ33A | [E] |
| 7R Tour CA | Mean Well IRM-20-24 en la placa: 85-264 V CA de entrada y 24 V 0.9 A de salida, según la hoja del fabricante | [E] |
| 7R Tour CA: rango del producto | **PD** | [R] |
| 7R Tour CA: protección de la fuente | Fusible de retardo T2A 250 V CA y varistor 10D471K | [E] |
| Aislamiento entre red y 24 V (placa) | ≥ 6.4 mm en el aire y por la superficie, comprobado por el DRC | [C] |
| Aislamiento entre red y 24 V (fuente) | El de la IRM-20-24 | [E] |
| Clase de aislamiento del producto | PD | |

## Entradas (8, de 24 V CC)

| | Valor | Origen |
|---|---|---|
| Tipo | Optoaisladas (LTV-217-B) | [E] |
| Común | Propio, COMI: el sensor da +24 V a la entrada y su 0 V va a COMI | [R] |
| Encendida | Meta > 11 V. El cálculo de escritorio da ≈ 7 V de encendido garantizado (corriente mínima del optoacoplador, LED indicador y 2 × 2.2 kΩ) | [C] **PD [M]** |
| Apagada | Meta < 5 V, **sin garantía**: con el mismo cálculo el optoacoplador puede leer «activa» cerca de 5 V (importa con sensores de 2 hilos con fuga). Se mide en la primera tanda; el umbral se ajusta cambiando RA y RB en la lista de piezas, sin cambiar la placa | [C] **PD [M]** |
| Corriente a 24 V | ≈ 4.8 mA | [C] |
| Meta | IEC 61131-2 tipo 1/3; PD [M] | [R] |
| Polaridad invertida | Diodo en antiparalelo | [R] |
| Tensión máxima | 30 V | [R] |
| Antirrebote | 30 ms por omisión, ajustable de 5 a 2000 ms (programa) | |
| Indicación | LED en serie: se enciende con la corriente real de la entrada | |

## Salidas (7)

| | Valor | Origen |
|---|---|---|
| Tipo | Contacto seco NA (SPST-NO), **común independiente por canal** | |
| Relé | Omron G2RL-1A-E DC24, monoestable: sin bobina, abre | [E] |
| Capacidad del relé | 16 A 250 V CA resistivo | [E] |
| Vida eléctrica del relé | 30 000 maniobras a 16 A 250 V CA resistivo | [E] |
| Distancia bobina-contacto del relé | 8 mm | [E] |
| **Corriente por canal (producto)** | **PD**; meta 10 A resistivo a ≤ 250 V CA [R]. Pistas de 2.0 mm en las dos caras, 2 oz | |
| **Corriente total simultánea** | **PD** (calentamiento del conjunto con los 7 canales) | |
| Irrupción admisible / maniobras con LED | **PD** | |
| Tensión máxima de contactos (producto) | **PD**; meta 250 V CA, monofásico [R] | |
| Distancia entre canales en la placa | ≥ 2.0 mm en el aire y ≥ 2.4 mm por la superficie (DRC). Entre las dos patas de una bornera de 5.08 mm: 2.48 mm, el contacto abierto | [C] |
| Supresión | Diodo de las bobinas en el ULN2003A. Para cargas inductivas de CA, supresor RC o varistor en la carga según el fabricante de la bobina (no incluido) | |
| Indicación | LED en paralelo con cada bobina: tensión real en la bobina | |
| Retroalimentación | Divisor por bobina al programa: avisa «bobina sin tensión» y «forzado manual». **No detecta un contacto soldado** | |

## Mando manual

| | |
|---|---|
| Botones de canal (frente) | Por programa: alternan el canal; dependen del microcontrolador |
| DIP 1-7 (bajo la tapa) | **Por hardware**: une el lado bajo de la bobina a 0 V y enciende el relé aunque el microcontrolador esté detenido. Requiere los 24 V. No es un bypass del contacto |
| DIP 8 | Wi-Fi apagado (lo respeta el programa) |

## Comunicaciones

| | Valor | Origen |
|---|---|---|
| Transceptor RS-485 | Chipanalog CA-IS3092W, aislamiento de 5 kVrms con fuente aislada integrada | [E] |
| Protección del bus | SM712 | [E] |
| Terminación | 120 Ω por puente | |
| Polarización | Por puente (680 Ω) | |
| Protocolo | Modbus RTU esclavo; 9600-115200 Bd, 8N2 / 8E1 / 8O1; mapa de registros en `firmware/APControl/modbus_esclavo.h` | |
| Vigilancia del maestro | 0-3600 s | |
| Wi-Fi | ESP32-C3-WROOM-02, **apagado de fábrica**; red de configuración solo a pedido (MODO 3 s), clave propia de cada equipo | |
| Vínculos entre equipos | UDP en la red local (sin nube) | |
| Homologación de radio en México | **PD** | |

## Comportamiento

| Situación | Qué hace |
|---|---|
| Arranque | Escribe 0 al expansor antes de configurarlo: ningún relé se mueve. Luego aplica la política de cada canal: APAGADO (fábrica), ÚLTIMO o ENCENDIDO. Un canal de **proceso** solo admite APAGADO |
| Corte de 24 V o de red | Todos los relés abren (monoestables). Al volver, se aplica la política de arranque |
| Programa trabado | Vigilante de 8 s: reinicia y aplica la política de arranque. **Mientras dura el bloqueo, el expansor mantiene las salidas como estaban** (hasta 8 s) |
| Falla de los 3.3 V con 24 V presentes | Las entradas del ULN2003A quedan sin excitación y los relés abren [C]; PD [M] |
| Pérdida de comunicación Modbus | Los canales que mandaba el maestro pasan a su acción configurada (apagar, por omisión). Al volver la comunicación no se reenciende nada |
| Sobretemperatura | **No hay sensor**: no se detecta. Ventilación y reducción de capacidad PD |
| Fallas que informa | Configuración inválida, bobina sin tensión, sin 24 V, comunicación perdida, mantenimiento de relés (80 % de la vida), reinicio por vigilante, expansor I2C |
| Fallas que requieren intervención | Bobina sin tensión persistente, falla de expansor, contacto pegado (no detectado: revisión física) |

## Ambiente, mecánica e instalación

| | Valor | Origen |
|---|---|---|
| Temperatura de operación | **PD**. Los componentes críticos admiten −40 a +85 °C (relé) según su hoja | [E] |
| Humedad | **PD**, sin condensación | |
| Altitud | **PD**; las distancias se calcularon sin corrección por altitud | |
| IP / IK | **No declarados** (solo por ensayo) | |
| Placa | 176 × 90 mm, 2 capas, 2 oz | |
| Carcasa de riel DIN (concepto) | ≈ 181 × 95 × 55 mm, ≈ 10 módulos | [C] |
| Bornes | KEFA KF128 de 5.08 mm; sección de conductor y par de apriete según el fabricante del borne (**PD**) | |
| Puesta a tierra | Sin partes conductoras accesibles en la carcasa de plástico; la tierra de las cargas no pasa por el equipo | |
| Protección externa obligatoria | Interruptor termomagnético o fusible por circuito de carga, ≤ el límite del canal (**PD**), coordinado con el cable | |
| Capacidad de cortocircuito del conjunto (SCCR) | **No evaluada**. El valor de un fusible no es el SCCR del producto | |

## Ensayos y certificaciones

Ninguno realizado. Ver `PLAN_VERIFICACION.md`. Normas por estudiar con un organismo:
- IEC 61010-2-201 (equipo de control) e IEC 61131-2;
- coordinación de aislamiento IEC 60664-1;
- NOM-003-SCFI-2014 y NMX aplicables para el SKU CA;
- radio: NOM-208-SCFI-2016 / IFT-008-2015 (autoridad actual: CRT).
