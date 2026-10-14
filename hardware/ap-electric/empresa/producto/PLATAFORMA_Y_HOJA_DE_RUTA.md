# AP Electric: plataforma «placa base», requisitos de la Rev C y hoja de ruta de 12 meses

> **Responsable:** ap-producto · **Fecha:** 14-oct-2026 · **Estado:** propuesta de escritorio para aprobación de Dirección.
> Nada de AP Electric está fabricado, medido ni certificado. Este documento **no cambia** ningún archivo de hardware, firmware ni web: propone y deja a cada dueño de área la decisión de implementarlo.
> Marcas: **[V]** fuente enlazada y fecha · **[CG]** conocimiento general sin verificar · **[H]** hipótesis por validar · **[R]** requisito o dato del repositorio · **[C]** cálculo · **[M]** medido (hoy ninguno) · `PD` por determinar.
> Los umbrales numéricos de aceptación de las secciones 2 y 4 son **requisitos propuestos** (decisión de diseño, no datos del mundo): se confirman o cambian con la medición de la primera tanda. No hay precios ni costos en este documento: siguen sin cotización real ni entrevistas.
> Fichas de producto: carpeta [`fichas/`](fichas/).

## 0. Resumen en diez líneas

1. «La placa base» es una **plataforma de cuatro capas**: hardware común (7R Tour hoy), firmware con capacidades `cap`, consola que se dibuja sola y **perfiles de aplicación** (datos, no placas).
2. Regla de crecimiento (**escalera de decisión**): perfil → firmware → módulo Modbus externo → accesorio → variante de placa → placa nueva. Se baja un escalón solo con evidencia medida o entrevistada.
3. Variante de placa justificada hoy por evidencia propia: **solo entradas NPN/PNP** (límite documentado). Memoria no volátil y Ethernet están **condicionados** a lo que se mida y se oiga en la primera tanda.
4. Más relés, más entradas, 4-20 mA y energía: **módulos por RS-485/Modbus**, no una placa base más grande. Esto exige que el 7R Tour pueda ser **maestro** y hoy su único RS-485 es **esclavo** (hallazgo 3).
5. La Rev C se decide con una **tabla de 14 mediciones** de la primera tanda y 5 preguntas de entrevista (sección 4). No se pide Rev C sin ellas.
6. Catálogo con 5 estados y criterio de paso medible (sección 5); 9 fichas de una página.
7. Hoja de ruta de 4 trimestres con 4 puertas internas (G1-G4) que alimentan las puertas de preventa A/B/C. Si G1 falla, no se gasta en Rev C.
8. Versiones: tres ejes independientes (`api`, `cap`/mapa Modbus, firmware) más letra de revisión de placa; el firmware decide por **capacidad**, no por revisión. Congelar `api` 3 y PackTags v1 antes de la puerta B.
9. OTA firmada: requisitos mínimos y una advertencia clave: **los fusibles (eFuse) de arranque seguro son irreversibles; no se queman en prototipos**.
10. «Sin nube» es la norma; nube opcional futura solo **saliente**, a un *broker* del cliente, con credenciales por equipo. Hallazgo urgente de seguridad: la `/api` por HTTP no tiene autenticación y acepta órdenes por GET (hallazgo 1).

---

## 1. La placa base como plataforma extensible

### 1.1 Las cuatro capas

```
 Capa 4  PERFILES DE APLICACIÓN   AP Monitor · AP Energía · AP Poka-Yoke · AP Agua · AP Frío · AP Agro · AP Lab
         (datos: cap requeridas + lista de órdenes + mapa E/S + plantilla de tablero + leyendas + pruebas de aceptación)
 Capa 3  CONSOLA / AP STUDIO      se dibuja con lo que la placa declara en `cap`; no conoce productos
 Capa 2  FIRMWARE AP Control      unidades con capacidad: salidas, entradas, packml, plc, modbus_esclavo, rs485, rtc,
                                  conteo_rapido, autoprueba  (+ futuras: modbus_maestro, bitacora, ota, mqtt, csv…)
 Capa 1  HARDWARE COMÚN           7R Tour: ESP32-C3, 7 relés, 8 entradas, RS-485 aislado, I2C (expansores, reloj), USB-C
         ──────────────────────────────────────────────────────────────────────────────────────────
         EXPANSIÓN Y PUENTES      módulos Modbus RTU (AP INPUT DI8, AP PRO DO8, AP PRO AI4, medidor de terceros) · AP GATE
```
Base documental: [`WEB_Y_PLACA.md`](../../WEB_Y_PLACA.md) (contrato `api`/`cap`), [`ARQUITECTURA.md`](../../ARQUITECTURA.md) (una placa, varios SKU), [`PACKML.md`](../../PACKML.md) (PackTags v1).

**Principio rector:** un producto nuevo es, en este orden de preferencia, (a) un *perfil* sobre la misma placa, (b) un perfil más un módulo de expansión, (c) una variante de la placa, (d) una placa nueva. Cada escalón cuesta más y arriesga más; se baja uno solo cuando el anterior **demostró** (medición o entrevistas) que no alcanza.

### 1.2 Escalera de decisión (qué se prueba antes de tocar el cobre)

| Escalón | Pregunta que debe contestarse «no alcanza» | Evidencia mínima para bajar |
|---|---|---|
| 1. Perfil | ¿Se resuelve con configuración (`PK ENT`, ciclo, causas, escalera AP Lógica, plantilla de tablero)? | Perfil probado en banco con la placa real |
| 2. Firmware | ¿Falta una función que el hardware ya permite? | Prueba automática en `firmware/pruebas/` y en banco |
| 3. Módulo Modbus externo | ¿Faltan E/S, analógicas o medición? | El módulo existe en diseño y el maestro está probado |
| 4. Accesorio externo | ¿Un adaptador pasivo/activo del cliente lo resuelve (p. ej. interfaz NPN→PNP, relé de interposición)? | Instalación probada en el piloto; el cliente lo acepta [H] |
| 5. Variante de placa | ¿Todos los anteriores fallan o cuestan más que rediseñar? | Medición propia **o** ≥ la proporción de entrevistas fijada en §4 |
| 6. Placa nueva | ¿Es otro problema físico (matriz de 64-256 puntos, CA, etc.)? | Puerta B superada en la línea de origen |

### 1.3 Perfil de aplicación: definición operativa

Un **perfil** es un paquete versionado de **datos** (no de código) que la consola sabe aplicar. Propuesta de contenido (formato por acordar con ap-web-software y ap-firmware; hoy ya existen «listas de órdenes como datos» y respaldo de configuración, ver `WEB_Y_PLACA.md`):

| Campo | Contenido |
|---|---|
| `perfil`, `version` | Nombre estable y versión del perfil (no confundir con la del firmware) |
| `requiere_cap` | Lista de `cap` que la placa debe declarar, p. ej. `["packml","entradas","conteo_rapido"]` |
| `requiere_hw` | Capacidades de hardware opcionales (p. ej. `entradas_bipolares`, `memoria_nv`), nunca la letra de revisión |
| `api_min` | Versión mínima del contrato de consola |
| `ordenes` | Lista de órdenes que se aplican (mismas que hoy: `PK ENT…`, `PK CICLO…`, `C…`, `MB…`, `GUARDAR`) |
| `mapa_es` | Etiquetas de cada entrada y salida y su función |
| `tablero` | Plantilla de tablero de AP Studio / consola (qué tarjetas y gráficas) |
| `leyendas` | Textos obligatorios («no es función de seguridad», «prototipo», etc.) |
| `aceptacion` | Lista de comprobaciones de puesta en marcha para ese perfil |
| `modulos` | Módulos de expansión soportados y su mapa |

Regla: **la consola rechaza aplicar** un perfil cuyo `requiere_cap`/`requiere_hw`/`api_min` no se cumpla, y dice cuál falta. Así AP Poka-Yoke no se puede activar en una placa sin bitácora no volátil, y nadie “cree” tener algo que la placa no tiene.

### 1.4 Perfiles y qué necesita cada uno [H salvo lo marcado]

| Perfil | Hardware | Firmware / `cap` nuevas | Web / consola | Estado hoy |
|---|---|---|---|---|
| **AP Monitor** | Base 24 V (rev B) [R] | `packml`, `entradas`, `conteo_rapido`, `rtc` (existen) [R] | Pestaña Producción (existe); falta historial por turno y causas [R] | Prototipo |
| **AP Energía** | Base + medidor Modbus de terceros (+ AP GATE si la base queda de esclava) | `modbus_maestro`, lectura de registros configurable, alarma de demanda | Tarjeta de demanda y factor de potencia | Concepto |
| **AP Poka-Yoke** | Base + AP INPUT; **memoria no volátil** | `bitacora` encadenada con *hash*, receta, `plc` | Tarjeta de secuencia y bitácora; exportación | Concepto |
| **AP Agua** | Base + AP PRO AI4 (4-20 mA) + contactor externo | `analogicas`, histéresis, alternancia de bombas | Tarjeta de nivel/presión | Concepto |
| **AP Frío** | Base + AI4 + sensor de temperatura (front-end `PD`) + memoria no volátil | `bitacora`, alarmas con retardo | Registro de temperatura exportable | Concepto |
| **AP Agro** | Base + AI4 + contactores | horario solar, riego por zonas | Tarjeta de zonas | Concepto |
| **AP Lab** | Base 24 V, sin cambios | Perfil de ejercicios, modo simulador | Guías en AP Studio | Concepto |

---

## 2. Cómo crece la plataforma: variantes, módulos y su justificación

### 2.1 Escalas usadas
- **Esfuerzo relativo** (no es tiempo ni costo): **S** = cambio pequeño de un solo dueño; **M** = cambia 2 áreas con pruebas; **L** = rediseño con nueva tanda y re-medición; **XL** = placa nueva o certificación asociada.
- **Riesgo:** Bajo / Medio / Alto, por probabilidad de romper algo ya diseñado o de abrir una obligación regulatoria.
- **Evidencia:** de dónde sale la justificación **y** qué dato la activa (disparador). Si no hay evidencia, se dice «ninguna: [H]».

### 2.2 Variantes de la placa base

| # | Variante | Placa | Firmware | Web / consola | Riesgo | Esfuerzo | Evidencia que la justifica | Disparador |
|---|---|---|---|---|---|---|---|---|
| V1 | **Entradas bipolares (NPN y PNP)** | Hoy: LTV-217-B (unipolar) + 1N4148W antiparalelo + común COMI [R: `gen/make.py` L209-213]. Opciones: (a) optoacoplador de entrada bidireccional en la misma huella SOP-4 (código por verificar [R: PUESTA_EN_MARCHA §1]); (b) puente de diodos delante del ópto (más piezas y más caída de tensión [CG]); (c) selección por puente (más bornes) | Cero si ambos polos se leen igual (la lógica es de nivel); si no, un parámetro de polaridad en `cfg` | Etiqueta de cableado NPN/PNP en el perfil; cap `entradas_bipolares` | Medio: toca las 8 entradas y el umbral (≈ 11 V encendida / ≈ 5 V apagada, 4.8 mA, máx. 30 V [R: DISENO_FINAL]) | **M** | Límite declarado en la ficha del piloto y en `ANALISIS_ECOSISTEMA.md` §8 (prioridad 1) [R]; ningún dato externo sobre la proporción de NPN en México (no encontrado) | ≥ 3 de las 10 máquinas descritas en entrevistas con sensor NPN **o** un cliente piloto que lo exija [H]; ver §4 |
| V2 | **Ethernet** (AP Base E) | El ESP32-C3 no tiene pines libres [R]. Exige otro módulo/MCU con SPI libre o Ethernet integrado: **cambia el cerebro**, no es un parche | Controlador de red, Modbus TCP, mismas reglas de origen «red» | Ninguna si el contrato es igual | Alto: rehacer firmware de comunicación, re-homologar radio si cambia | **L** | `ANALISIS_ECOSISTEMA.md` §8 (prioridad 6): «las plantas prefieren cable» [H, sin fuente]; guion de entrevista Q4 | Más del 50 % de las plantas entrevistadas rechazan Wi-Fi **y** no aceptan un puente RS-485↔Ethernet de terceros [H]. Hasta entonces: **AP GATE o puente de terceros** |
| V3 | **Memoria no volátil para bitácora** (FRAM I2C o flash SPI) | Un CI en el bus I2C ya existente, 1-2 pistas, alimentación 3.3 V; en FRAM no hay desgaste por ciclos [CG] | Bitácora con *hash* encadenado, instantánea de tiempos por estado (hoy no se guardan: empiezan en cero al encender [R: PACKML]), cap `bitacora` | Historial por turno, exportar CSV | Bajo: bus y pines ya existen | **M** | Hoy la bitácora y los tiempos por estado **se reinician al apagar** [R: PACKML «Lo que falta» 2]; IATF 16949 pide registros (8.5.2.1) para Poka-Yoke [V: AIAG, ver §Fuentes del estudio] | Número de apagones observados en el piloto de 30 días **y** necesidad de OEE por turno; o cliente de Poka-Yoke/Frío (obligatoria) |
| V4 | **Más relés / más entradas** | **No** en la base: se agregan con módulos (§2.3). Un relé extra implica bobina, ULN, expansor y aislamiento nuevos | Maestro Modbus | Tarjetas por módulo | Medio | **S** (módulo) / **L** (base mayor) | `ARQUITECTURA.md` §2: un cerebro, módulos de ampliación [R]; ninguna entrevista pidió más de 7/8 todavía (no hay entrevistas) | Un cliente real con > 7 salidas o > 8 entradas por máquina |
| V5 | **Medición de corriente/energía** | **No en la base.** Medidor Modbus de terceros primero. Si se hace propio: módulo con entradas de transformadores de corriente de baja tensión (sin conectar red) | `modbus_maestro`; cálculo de demanda | Tarjeta de demanda y factor de potencia | Alto en tensión (medir red = seguridad eléctrica y certificación); medio solo con corriente | **S** (terceros) / **XL** (propio con tensión) | `ESTUDIO_MERCADO_INDUSTRIAL.md` §9 oportunidad 2 (I=5, E=2) y 13 [R]; la tarifa GDMTH y el factor de potencia 0.97 pendientes de verificar en el DOF [R §12] | Entrevista con nave en GDMTH que quiera piloto **y** acepte medidor de terceros |
| V6 | **4-20 mA** | Módulo AP PRO AI4 ya en diseño [R]; no en la base | `analogicas`, escalado, filtro | Tarjeta de lectura | Bajo-medio: lazo alimentado, protección | **M** (módulo) | Oportunidades 8, 9, 10, 11 (agua, aire, frío, agro) usan AI4 [R: estudio §9] | Primer cliente de agua/aire/frío que firme piloto |
| V7 | **Segundo RS-485** o puente maestro | La base tiene 1 puerto aislado [R]. Un segundo puerto necesita otro transceptor aislado y pines que el C3 no tiene | `modbus_maestro` convive con `modbus_esclavo` en puertos distintos | Selector de rol | Medio | **L** | Hallazgo 3 (conflicto esclavo/maestro en un solo puerto) | Hasta que haya un cliente con SCADA **y** módulos en la misma máquina; antes: AP GATE hace de maestro |
| V8 | **Salida estática** (transistor/SSR) para conmutación frecuente o CC | Otra etapa de potencia, otro aislamiento | Salida con PWM lento / pulso | Tarjeta de salida | Medio | **L** | Ninguna: [H]. Depende de la vida de los relés, que no se ha medido | Fallo o desgaste de relés en piloto por conmutación frecuente |
| V9 | **Antena externa** (conector U.FL) | Cambio de módulo Wi-Fi o de la antena; implica homologación del radio | Ninguno | Ninguna | Medio-alto (radio) | **M** | Ninguna medida aún; el gabinete metálico atenúa Wi-Fi [CG] y **no está en el plan de medición** (hallazgo 6) | RSSI/pérdida de paquetes insuficientes en gabinete real |
| V10 | **SKU CA** (fuente de red en la placa) | Ya diseñado | Ninguno | Ninguna | Alto (seguridad eléctrica, NOM-001-SCFI-2018 [V: TÜV SÜD, `ANALISIS_ECOSISTEMA.md` §4]) | **XL** (certificación) | Congelado por regla 6 de `CONTEXTO_COMPARTIDO.md` | Solo después de la puerta C y pruebas con organismo acreditado |

### 2.3 Módulos de expansión por RS-485 / Modbus (estándar «AP-EXP»)

**Idea:** la base es **maestra** del bus y cada módulo es esclavo con un bloque común de identificación. Así sumar E/S, analógicas o un medidor es agregar una fila a un perfil, no rediseñar la placa.

| Elemento | Propuesta | Por qué |
|---|---|---|
| Rol de la base | Maestro (`modbus_maestro`) en su único puerto RS-485 cuando hay módulos; esclavo si lo lee un SCADA. **No ambos a la vez en un puerto** | Una sola línea semidúplex; ver hallazgo 3 y V7 |
| Identificación | Todo módulo AP responde la identificación estándar de Modbus (función 0x2B/0x0E [CG]; la especificación está en [modbus.org](https://modbus.org/modbus-specifications)) y un bloque de retención común: tipo, rev. de hardware, versión de firmware, mapa de registros (versión) y bitmap de capacidades | La base descubre y valida antes de usar; no depende de la letra de revisión |
| Dirección | Fijada por DIP o por configuración local; nunca por defecto igual en todos | Evita colisión y obliga a configurar |
| Estado seguro | Cada módulo con salidas lleva un temporizador de pérdida de comunicación (registro configurable) y apaga salidas de **proceso** al vencerse | Coherente con la regla de `PACKML.md` §5.5 y `ARQUITECTURA.md` §6 |
| Fallo | Módulo que no responde = falla **leve** en la base y evento en la bitácora; el OEE sigue calculándose | No detener la máquina por un módulo de lectura |
| Prueba | El maestro tiene pruebas automáticas como el esclavo (`tools/probar_apbus.sh`) | Regla 9 de `CONTEXTO_COMPARTIDO.md` |
| Licencia | Solo código propio o MIT/BSD/Apache/MPL/EPL [R: estudio §7.7] | Evitar GPL dentro del producto |

**Módulos candidatos (todos de la lista existente [R]):** AP INPUT (DI8), AP PRO DO8, AP PRO AI4, AP GATE (puente a otras redes), medidor de terceros. Ningún módulo nuevo se inventa en este documento.

### 2.4 Qué NO cambia al crecer (invariantes de la plataforma)
- Todo producto de AP **no es** función de seguridad.
- Salidas de proceso arrancan apagadas y se apagan al perder comunicación.
- Reanudar una máquina es **solo origen local**; por red solo Stop, Hold y Abort.
- Sin nube obligatoria; sin red de 127/220 V en el piloto.
- El firmware decide por **capacidad**; la consola, por `cap`.

---

## 3. Especificación de requisitos de la Rev C

> Rev C = primera mejora de hardware **tras** la primera tanda de la rev B (5 placas, 2-3 ensambladas [R: PUESTA_EN_MARCHA §2]). Se pide **solo si** G2 (§6) la aprueba. Cada requisito tiene: criterio de aceptación medible, qué se mide en la tanda 1 y la regla de decisión. Los números marcados «propuesto» son requisitos, no hechos.

### 3.1 Lista priorizada

Prioridad: **P0** condición para seguir (corrige fallas) · **P1** habilita la puerta B · **P2** mejora de valor, no bloquea · **P3** solo si el disparador se cumple · **No** se incluye.

| ID | Pri. | Requisito | Criterio de aceptación (medible) | Se decide con (tanda 1 / entrevistas) |
|---|---|---|---|---|
| C-00 | P0 | Corregir **todo defecto medido** en la tanda 1 (arranque de relés, aislamiento, alimentación, rutas largas INT/RS_DE/RS_RX, polarización de batería) | 0 relés con clic al energizar en 20 energizaciones; sin corto 24 V/5 V/3.3 V; RS-485 sin errores de trama en un tramo y tasa de baudios definidos (propuesto: el más largo que usará el piloto, a 115200 Bd y a 9600 Bd); DRC/ERC en 0 tras el cambio | Puesta en marcha etapas A-F de `PUESTA_EN_MARCHA.md` y riesgos 1-8 de `PLAN_VERIFICACION.md` §5 |
| C-01 | P1 | **Entradas bipolares NPN/PNP** (V1) | Con sensor NPN de contacto en colector abierto y con PNP, ambos activan la entrada: umbral de encendido ≥ el de la rev B o mejor (propuesto: igual banda ≈ 11 V encendida / ≈ 5 V apagada); corriente por entrada ≈ la rev B; polaridad invertida sin daño; conteo rápido ≥ 100 Hz sin pérdida con ambos tipos y rechazo de pulsos < 2 ms conservado | (a) prueba en banco con adaptador NPN provisional; (b) Q3 del guion: proporción de sensores NPN; (c) si algún cliente piloto lo exige |
| C-02 | P1 | **Identificación de revisión y número de serie** legible por firmware | `rev` y `serie` aparecen en `/api`, USB y registro Modbus; sobreviven a borrado de configuración y a OTA | Revisión de pines libres; cualquier I2C con área de serie (puede combinarse con C-03) |
| C-03 | P1/P2 | **Memoria no volátil para bitácora** (V3) | 100 ciclos de apagado en pleno conteo sin perder ningún evento confirmado ni romper la cadena de *hash*; tiempos por estado y contadores recuperados con error ≤ el intervalo de instantánea (propuesto: ≤ 1 min); escritura sin afectar el conteo rápido a ≥ 100 Hz | Apagones reales del piloto; cuántas veces el OEE se reinició en 72 h; entrevista: ¿piden OEE por turno? |
| C-04 | P1 | **Preparar OTA firmada** (ver §8): confirmar flash del módulo y esquema de dos particiones | Flash disponible ≥ 2 × tamaño de la imagen + datos (hoy 1.06 MB, 53 % del esquema actual [R: PLAN_VERIFICACION §1]; tamaño del flash del módulo `PD`); actualización de prueba y rollback pasan los 8 casos de §8.3 | Revisar la hoja del módulo ESP32-C3-WROOM-02 (pendiente de descargar [R: ARQUITECTURA §9]) |
| C-05 | P2 | **Reloj**: cristal con la carga correcta | Deriva medida en 14 días, extrapolada ≤ 60 s/mes (propuesto); con 3.3 V presente no entra corriente a la pila (riesgo 4) | Riesgo 1 de `PLAN_VERIFICACION.md` §5: medir contra hora de red |
| C-06 | P2 | **Protección de la entrada de 24 V** y de las entradas de sensor | Sin daño tras: inversión de 24 V, transitorio de arranque de una carga inductiva cercana (método y valor los fija ap-calidad-normas), 30 V en entradas | Fallas provocadas de `PLAN_VERIFICACION.md` §2.2 |
| C-07 | P2 | **Antena/gabinete** (V9 si falla) | RSSI mínimo y pérdida de paquetes aceptables dentro de un gabinete metálico cerrado con la puerta cerrada; valores umbral fijados con la tanda 1 | Medición **nueva** (hallazgo 6): añadir al plan de la tanda 1 |
| C-08 | P2 | **Mecánica y etiqueta**: caja DIN, bornes, serigrafía y etiqueta | Alta/baja de bornes sin herramienta especial; etiqueta con modelo, `rev`, `serie`, leyendas obligatorias («no es función de seguridad», «prototipo»); cabe en la caja elegida | Antes de la puerta B (ya listada en `ANALISIS_ECOSISTEMA.md` §8, prioridad 2) |
| C-09 | P3 | **Ethernet** (V2) | Variante con el MCU que se elija pasa las mismas etapas A-F; Modbus TCP responde con las mismas reglas de origen | Solo si se cumple el disparador de V2 |
| C-10 | P3 | **Segundo puerto RS-485 o puente** (V7) | Maestro y esclavo coexisten sin colisión en 24 h de corrida | Solo con cliente que lo necesite |
| C-11 | P3 | **Salida estática** (V8) | Vida eléctrica a la frecuencia de conmutación del cliente medida | Solo con falla de relés |
| — | No | Más relés o entradas en la base; medición de red; 4-20 mA en la base; SKU CA | — | Se resuelven con módulos o están congelados (§9) |

### 3.2 Criterios de salida de la Rev C (para pedir la tanda 2)
1. Todos los P0 y P1 cumplen su criterio **en banco con la placa nueva** (mínimo 2 unidades).
2. ERC/DRC/BOM/CPL sin errores con `bash hardware/tools/verificar_todo.sh` = «TODO BIEN» y revisión de `ap-revisor-adversarial` sin hallazgos críticos abiertos [R: ORGANIZACION regla 3].
3. El firmware soporta rev B **y** rev C (ver §7.3).
4. Cotización real de la tanda (compras) y aprobación de Dirección [R: ORGANIZACION].

---

## 4. Qué se mide en la primera tanda para decidir la Rev C

### 4.1 Tabla de decisión (14 mediciones)

| # | Medición | Cómo (referencia) | Qué decide | Umbral de acción [propuesto, ajustable] |
|---|---|---|---|---|
| M1 | Clics de relé al energizar (20 energizaciones) | Osciloscopio en bobinas [PLAN_VERIFICACION §2.1] | C-00 | Cualquier clic → corregir y no entregar a clientes [R: ANALISIS §9] |
| M2 | Corriente en reposo y con 7 relés | Etapa C pasos 7-9 | C-00, C-06 | Fuera de lo esperado `PD` → investigar antes de seguir |
| M3 | Corto o fuga entre redes y aislamiento funcional RS-485 | Etapa A | C-00 | Cualquier fallo de aislamiento → corregir [R: ANALISIS §9] |
| M4 | Umbrales de encendido/apagado de cada entrada con fuente variable | Banco §2.1 | C-01 | Fuera de la banda diseñada → ajustar resistencias |
| M5 | Entrada con sensor NPN mediante adaptador/relé de interposición | Banco (nuevo) | C-01 | Si funciona de forma estable, V1 baja a P2 y el adaptador es opción de piloto |
| M6 | Conteo rápido: pulsos perdidos a 100 Hz y a la frecuencia máxima que se pueda generar | Etapa D paso 12 | C-01, C-03 | Pérdida > 0 a 100 Hz → corregir antes de la puerta B |
| M7 | Deriva del reloj en ≥ 14 días contra hora de red | Riesgo 1 | C-05 | > 60 s/mes → cambiar cristal |
| M8 | Corriente hacia la pila con 3.3 V presente | Riesgo 4 | C-05, C-00 | Cualquier valor medible → corregir |
| M9 | Integridad RS-485 (tramas erróneas) en el tramo y baudios del piloto | Etapa E | C-00, C-10 | Errores → terminación/polarización/rutas largas |
| M10 | Arranque con y sin 24 V (pines IO2, IO8, IO9) | Riesgo 5 | C-00 | Fallo → corregir |
| M11 | Reinicios del vigilante en 72 h | Corrida de 72 h (puerta B) | C-00 | Reinicio no explicado → bloquea puerta B |
| M12 | Apagados y OEE perdido en 72 h y en el primer piloto | Corrida de 72 h + bitácora de eventos | C-03 | Más de 1 reinicio de OEE por turno hace de V3 condición de la puerta B [H] |
| M13 | Temperatura de bornes y relés con carga de 24 V | Etapa F | C-00 | `PD` por ensayo |
| M14 | **Nueva:** RSSI y pérdida de paquetes Wi-Fi dentro de un gabinete metálico cerrado (hallazgo 6) | Prueba con la placa en una caja/gabinete real | C-07, V2, V9 | Pérdida alta → antena externa, puente o Ethernet |

### 4.2 Preguntas de entrevista que alimentan la Rev C (del guion de `ANALISIS_ECOSISTEMA.md` §10)
| Pregunta | Dato | Decide |
|---|---|---|
| Q3 sensores (PNP, NPN, contacto seco, torre de luz) | Proporción NPN | C-01 |
| Q4 acceso a internet y Wi-Fi | Aceptación de Wi-Fi / necesidad de cable | C-09, V2 |
| Q7 certificados de la planta | Si exigen NOM/UL/CE para conectar | Puerta C, V10 |
| Q2 cómo registran hoy piezas y paros | Si piden turno/historial | C-03, AP Studio |
| Q1 cuántas máquinas y de qué tipo | Si piden > 7 salidas o > 8 entradas | V4 |

### 4.3 Reglas de decisión
- **Si M1, M3 o M10 fallan:** la Rev C es **correctiva** (solo C-00); se detiene todo lo demás hasta cerrar.
- **Si ≥ 3 de las 10 máquinas descritas tienen NPN** (o un piloto lo exige): C-01 pasa a **condición de la puerta B** [R: ANALISIS §9 «los clientes piden NPN en todas las máquinas»; el umbral 3/10 es [H]].
- **Si no hay evidencia de NPN ni de apagones:** Rev C solo con C-00 y C-02; se posponen V1 y V3 (no se rediseña por gusto).
- **Si menos de 3 de 10 entrevistas** pagan el rango de precio [R: ANALISIS §9]: no hay Rev C; se rediseña la oferta primero.

---

## 5. Catálogo ampliado y estados

### 5.1 Estados y criterio de paso

| Estado | Significa | Criterio para **entrar** | Criterio para **pasar al siguiente** |
|---|---|---|---|
| **Concepto** | Idea con dueño y problema escrito; sin esquema ni código | Problema y cliente en una ficha de 1 página; dueño asignado | Pasa a **Diseño** cuando: (1) ≥ 3 entrevistas confirman el dolor [H]; (2) las 6 preguntas de `ANALISIS_ECOSISTEMA.md` §3 con ≥ 5 «sí» y las «por saber» listadas; (3) perfil/hardware identificado por la escalera §1.2; (4) ap-revisor-adversarial no ve contradicción con reglas 2, 5, 6 |
| **Diseño** | Esquema/arquitectura/código existen; pruebas de software | Idem + decisión de Dirección | Pasa a **Prototipo** cuando: (1) pruebas automáticas y `verificar_todo.sh` = «TODO BIEN» si tocó código/placas/web; (2) revisión adversarial sin hallazgos críticos; (3) **hay al menos 2 unidades físicas** o, si es perfil, corre en una placa real en banco; (4) lista de qué falta medir |
| **Prototipo** | Existe físicamente y se prueba; sin certificación | Etapas A-D de `PUESTA_EN_MARCHA.md` superadas en 2 placas | Pasa a **Servicio** solo cuando se cumplen las **condiciones de la puerta C** de `ANALISIS_ECOSISTEMA.md` §7 y las certificaciones aplicables (ver §5.2). **Nunca** por antigüedad |
| **En pausa** | Dependencia externa o regla que lo impide | Se escribe la **condición de salida** y la fecha de revisión (cada trimestre) | Vuelve al estado anterior cuando la condición se cumple; si no se cumple en 2 revisiones seguidas se **descarta** (sección 9) |
| **Servicio** | Se entrega y se le da soporte | Condiciones de la puerta C; soporte y garantía escritos; evidencia en `PLAN_VERIFICACION.md` | Pasa a **En pausa** o se descarta si cae un criterio de parar (§6.5) |

Software (consola, AP Studio) y servicios (piloto, diseño a medida, capacitación) siguen el mismo esquema, pero «prototipo físico» se sustituye por «probado contra una placa real y con usuarios reales».

### 5.2 Catálogo propuesto (estado propuesto y por qué)

| Línea | Estado hoy en la web | Estado propuesto | Razón / condición |
|---|---|---|---|
| AP Monitor 24 (7R Tour 24DC rev B) | Prototipo | **Prototipo** (nada fabricado: ver nota) | Es el único candidato a piloto. *Nota:* «Prototipo» debe leerse como «diseño listo para pedir tanda 1»; no hay unidades físicas aún |
| 7R Tour CA | En pausa | **En pausa** | Pruebas de seguridad eléctrica con organismo acreditado [R: regla 6] |
| AP GATE | Diseño | **Diseño** (ficha) | Sin demanda comprobada; ruta de MQTT/OPC UA |
| AP PRO DO8 · DI8 · AI4 | Diseño | **Diseño** | Se vuelven necesarios con V4/V6 |
| AP UNO | Diseño | **En pausa** [H] | El 7R Tour cubre el caso; duplica soporte (decisión de Dirección) |
| AP Energía | Concepto | **Concepto** (ficha) | Requiere maestro Modbus y entrevista GDMTH |
| AP Poka-Yoke | no aparece | **Concepto** (ficha) | Requiere V3 |
| AP Agua · AP Frío · AP Agro | no aparecen | **Concepto** (fichas) | Requieren AI4 y piloto |
| AP Lab | «Capacitación» Concepto | **Concepto** (ficha) | Canal de bajo riesgo para validar |
| AP Test | no aparece | **Concepto** (ficha) | Es la única que pide placa nueva |
| AP Predict | no aparece | **Concepto, sin ficha** | Espera a corriente y temperatura de Energía/Frío |
| Línea Luz / AP LED | Diseño | **Fuera del plan industrial** | Mercado distinto [R: ANALISIS §4] |
| Home Plug · Home Switch | En pausa | **En pausa** | Certificación NOM-003 [R] |
| Consola AP Base · AP Studio | **Servicio** | **Prototipo** hasta probar con placa real | `WEB_Y_PLACA.md`: la consola «no se ha probado con una placa real»; ver hallazgo 2 |
| Piloto 30 días | Concepto | **Concepto** hasta la puerta B | Depende de placas probadas y contrato |
| Diseño a medida | Servicio | **Servicio** (sin precio) | Es un servicio de ingeniería caso por caso; no es producto |

---

## 6. Hoja de ruta de 12 meses

### 6.1 Supuestos
- Fecha de inicio: **14-oct-2026**. Los trimestres son **ventanas indicativas** sin compromiso con clientes; el avance lo marcan los **eventos** (placas en mano, pruebas superadas), no el calendario.
- Plazo de entrega de la tanda 1: `PD` (no hay cotización real). Si la tanda 1 llega tarde, **todo** lo que depende de G1 se corre sin saltar puertas.
- La puerta A (lista de interés) ya existe en la web; B y C no están abiertas [R: ANALISIS §7].

### 6.2 Plan por trimestre

| Trimestre | Objetivo | Entregables | Puerta de decisión al cierre |
|---|---|---|---|
| **T1 · 14-oct a 31-dic-2026** | Pedir y recibir la tanda 1; empezar a oír al mercado | Cotización real de las 5 placas (con y sin ensamble); revisión adversarial y aprobación de Dirección; entrevistas (mínimo 5, meta 10) y 3 conversaciones antes de fijar precio; mediciones M1-M14 en curso; política de versiones aprobada (§7); corrección de hallazgos 1 y 2 | **G1:** placas en mano y etapas A-D superadas en 2 placas |
| **T2 · ene-mar 2027** | Cerrar la tanda 1 y decidir la Rev C | Etapas E-F; corrida de 72 h en una máquina propia; M1-M14 completas en `PLAN_VERIFICACION.md`; decisión Rev C con §4; AP Studio con historial por turno y causas de paro; exportación CSV; caja DIN y etiqueta; contrato B2B corto revisado por abogado; congelar `api` 3 y PackTags v1 | **G2:** Rev C aprobada, aplazada o descartada. Si se cumplen las 4 condiciones de la puerta B → **abrir puerta B** |
| **T3 · abr-jun 2027** | Pilotos y, si G2 lo aprobó, Rev C | Kits piloto a costo (5-10 clientes) con instalación acompañada; diseño y verificación de Rev C por software (ERC/DRC/BOM) y pedido de la tanda 2 solo si cabe en presupuesto; OTA firmada en prototipos de laboratorio; AP GATE con MQTT/TLS (Sparkplug B) en prueba con un SCADA real; primer piloto de Energía si hay cliente GDMTH | **G3:** resultados de pilotos. Condición hacia la puerta C: ≥ 3 clientes que completaron el piloto |
| **T4 · jul-sep 2027** | Reunir lo que exige la puerta C y podar | Pre-escaneo de EMC y pruebas de seguridad eléctrica con organismo; precio validado con ventas reales del piloto; términos de devolución y entrega con abogado; importación y facturación con contador y agente aduanal; segunda línea (Energía o Gateway) en Prototipo; revisión de catálogo | **G4:** puerta C (go/no-go) y poda de líneas |

### 6.3 Coherencia con las puertas de preventa

| Puerta | Condiciones (de `ANALISIS_ECOSISTEMA.md` §7) | Dónde se verifican en la hoja de ruta |
|---|---|---|
| **A** lista de interés | Ninguna (ya existe) | Activa desde T1; se usa como canal de entrevistas |
| **B** kits piloto | 1) etapas A-D en 2 placas; 2) 72 h sin fallas no explicadas; 3) etiqueta y aviso; 4) contrato revisado | G1 (1), T2 (2-4) → abre en G2 |
| **C** preventa con pago | 1) B superada con ≥ 3 clientes; 2) precio validado; 3) EMC y seguridad eléctrica; 4) términos legales; 5) importación y facturación | G3 (1), T4 (2-5) → decide en G4 |

**Regla:** ninguna puerta se abre por calendario. Si una condición no se cumple, se publica el retraso y no se cobra.

### 6.4 Puertas internas G1-G4

| Puerta | Pasa si | Se detiene si |
|---|---|---|
| **G1** | Etapas A-D en 2 placas; M1, M3, M10 sin fallas | Falla de aislamiento o alimentación → corregir y volver a pedir (criterio de `ANALISIS_ECOSISTEMA.md` §9) |
| **G2** | Mediciones completas; decisión Rev C razonada con §4; 72 h sin fallas no explicadas | Más de un reinicio del vigilante no explicado; relés que cierran al energizar |
| **G3** | ≥ 3 clientes piloto con 30 días completos y retroalimentación escrita | < 3 pilotos completos en 2 intentos |
| **G4** | Pre-escaneo EMC y pruebas eléctricas hechas; precio validado con clientes; asesoría legal y aduanal obtenida | Cualquier condición de C sin cumplir → no se abre C |

### 6.5 Criterios de parar o cambiar de rumbo (consolidados)
Los de `ANALISIS_ECOSISTEMA.md` §9 más los de plataforma:
1. **Menos de 3 de 10** entrevistas pagarían el rango de precio de la hipótesis → rediseñar la oferta (más barata, solo conteo y andon) **antes** de gastar en Rev C.
2. **Fallos de aislamiento o de alimentación** en la tanda 1 → corregir antes de entregar nada.
3. **Rev C sin evidencia** (sin NPN, sin apagones, sin pedido de cable) → no se rediseña; se mejora software.
4. **Un competidor local publica un precio claramente menor** y el diferenciador (aplicación sin nube y soporte) no pesa → detener.
5. **Una línea candidata no llega a Diseño en 2 trimestres** consecutivos de su ventana → pasa a descartada (§9).
6. **Costo de soporte** de un piloto supera el valor aprendido (se mide en horas de ingeniería por piloto; umbral lo fija Dirección con finanzas) → limitar pilotos.
7. **Aviso de seguridad grave** (daño real o casi accidente atribuible al equipo) → retirar y notificar a clientes; revisión completa.

---

## 7. Política de versiones y compatibilidad

### 7.1 Ejes de versión (independientes)

| Eje | Dónde vive | Formato | Quién lo cambia | Regla |
|---|---|---|---|---|
| **`api`** (contrato consola ↔ placa) | JSON de `/api` y USB; hoy `api: 2` [R] | Entero MAYOR (cambia lo que rompe) + `api_menor` (aditivo; propuesto, nuevo en API 3) | ap-web-software con ap-firmware | MAYOR sube **solo** si se quita/renombra un campo u orden o cambia su significado. Añadir campos u órdenes opcionales **no** sube el MAYOR |
| **`cap`** (capacidades) | Lista en el JSON [R] | Cadenas estables | ap-firmware | Un nombre de `cap` **nunca se reutiliza ni cambia de significado**. Si cambia la semántica, nace uno nuevo (`packml2`) y el viejo se mantiene durante la ventana de deprecación |
| **Mapa Modbus** (PackTags) | Registro de entrada 100 = «versión del mapa (1)» [R: PACKML] | MAYOR en 100; MENOR propuesto en el registro 109 (libre en el mapa actual: 105-108 y 110-143 están ocupados) | ap-firmware | Direcciones **nunca se reasignan**; los nuevos registros van a rangos libres; los obsoletos quedan reservados |
| **Firmware** | Cadena de versión en arranque, `fw` en `/api` | MAYOR.MENOR.PARCHE (SemVer [V: semver.org, ver Fuentes]) + hash de *commit* | ap-firmware | MAYOR puede incluir cambio de `api`/mapa; MENOR agrega; PARCHE corrige |
| **Revisión de placa** | Serigrafía y etiqueta; `rev` y `serie` legibles por firmware (C-02) | Letra: A, B, C… | ap-hardware | La letra sube con **cualquier** cambio de cobre, lista de piezas o esquema que afecte la función |
| **Perfil** | Manifiesto del perfil | MAYOR.MENOR | ap-producto + ap-web-software | `requiere_cap`/`api_min` se validan al aplicar |

### 7.2 Reglas para no romper a los clientes
1. **Aditivo por defecto.** Un cliente que ignora campos desconocidos sigue funcionando; la consola y las integraciones **deben** ignorar campos que no conocen.
2. **Congelar antes del campo.** Antes de la puerta B se congelan `api` 3, PackTags v1 y el formato de respaldo; después, solo cambios aditivos.
3. **Ventana de deprecación.** Lo obsoleto se marca en la documentación y en `/api` (`dep: [...]`), se conserva al menos 2 versiones MENORES **y** un periodo en meses que fija Dirección con los pilotos (valor `PD`), y se retira en un MAYOR.
4. **Pruebas de contrato.** Guardar respuestas JSON de referencia por versión y correrlas contra el firmware (propuesta para `web/pruebas/` y `firmware/pruebas/`); un cambio que las rompa exige subir el MAYOR.
5. **La consola degrada con elegancia.** Si `api` de la placa > soportada, muestra solo lectura y avisa; si la placa no declara una `cap`, esa tarjeta no se dibuja [R: WEB_Y_PLACA].
6. **Configuración respaldada con cabecera.** El respaldo (lista de órdenes) lleva `# api`, `# fw`, `# rev`, `# perfil`; al restaurar, órdenes desconocidas se **saltan y se reportan**, nunca se aplican a ciegas.
7. **Los pilotos son clientes reales.** Cada kit se entrega con una versión congelada y una nota; se actualiza solo con acuerdo y por el procedimiento de §8.

### 7.3 Revisiones de placa y firmware
- El firmware decide por **capacidad de hardware** (`entradas_bipolares`, `memoria_nv`, `rtc`) declarada por la placa (p. ej. leída de la memoria de identificación, C-02), **no** por «si es la rev C».
- Cada versión de firmware soporta **las dos últimas revisiones** de placa (rev B y C durante la transición); retirar soporte de una revisión exige aviso a clientes con esa revisión.
- Un cambio de hardware que **cambia la semántica** de una entrada o salida (p. ej. polaridad) se declara como `cap` nueva y se documenta en el perfil, no se oculta.
- Tabla de compatibilidad viva: placa × firmware × `api` × consola × perfil (propuesta de archivo `COMPATIBILIDAD.md` en `producto/`, a crear cuando haya primera tanda; hoy sería vacía).

### 7.4 Quién valida
Antes de publicar un cambio de `api`, `cap` o mapa: ap-firmware + ap-web-software proponen, ap-producto registra la decisión, ap-revisor-adversarial revisa y Dirección aprueba [R: ORGANIZACION].

---

## 8. Actualización de firmware: OTA firmada, requisitos mínimos

> **Principio:** actualizar firmware cambia el comportamiento de una máquina. Debe ser una acción **local, autenticada, verificada y reversible**, nunca una consecuencia de que un servidor remoto lo ordene.

### 8.1 Requisitos mínimos (todos obligatorios antes de ofrecer actualización a clientes)

| # | Requisito | Detalle |
|---|---|---|
| O-1 | **Imagen firmada** | La placa solo ejecuta imágenes firmadas con la clave de AP. Con ESP32-C3, Secure Boot v2 existe y se recomienda en producción [V: [Espressif Security Overview](https://docs.espressif.com/projects/esp-idf/en/latest/esp32c3/security/security.html), consultado 14-oct-2026]. Verificar en la hoja del módulo exacto |
| O-2 | **Clave de firma fuera del repositorio** | Generada en un equipo con buena entropía, guardada fuera de línea o en un módulo de seguridad; una fuga compromete todo el esquema [V: misma fuente]. Plan de rotación: el chip admite varios resúmenes de clave [CG; verificar cuántos y la irreversibilidad] |
| O-3 | **Dos particiones y *rollback*** | La imagen nueva solo se marca válida tras una autoprueba; si no, vuelve a la anterior [V: misma fuente (OTA rollback)] |
| O-4 | **Anti-retroceso** | Número de versión de seguridad en eFuse para impedir instalar versiones viejas vulnerables [V: misma fuente]. **Es irreversible** |
| O-5 | **Autorización local** | La carga requiere acción local (USB con consola, o credencial de red **más** botón/interruptor físico); **nunca** por Modbus ni por un registro remoto, coherente con «reanudar es solo local» [R: PACKML §Reglas] |
| O-6 | **Estado seguro** | Solo se permite con la unidad en STOPPED o ABORTED; salidas de proceso apagadas durante y tras reiniciar; al volver, arranca en STOPPED [R: PACKML] |
| O-7 | **Configuración conservada** | La configuración y los contadores guardados se conservan; si cambia el formato, hay migración con respaldo previo (§7.2 punto 6) |
| O-8 | **Registro** | Cada actualización o intento fallido queda en la bitácora con versión anterior, nueva, resultado y origen |
| O-9 | **Canal sin nube** | Transferencia del archivo firmado por USB o por la red local; la verificación de firma la hace el equipo, **no** el canal. HTTPS es recomendable [V: misma fuente] pero no sustituye la firma |
| O-10 | **Procedencia del software** | Lista de componentes (SBOM) y revisión de licencias de cada versión [R: estudio §7.7] |

### 8.2 Advertencias específicas de ESP32
- **Los fusibles de arranque seguro y de cifrado de flash son irreversibles** [CG; confirmar en la guía de Espressif «Secure Boot v2» y «Flash Encryption» para el módulo exacto]. Regla propuesta: **no se queman en prototipos ni en kits piloto con firmware en cambio**; solo en el «lote de producción» con clave definitiva. Durante los pilotos se usa firma verificada por software y una protección de aplicación, y se documenta como tal.
- Verificar si deshabilitar depuración (JTAG) en producción deja intacta la consola USB [CG; hoja del chip].
- Tamaño de flash del módulo y esquema de particiones: hoy el programa ocupa 1.06 MB (53 % del espacio de aplicación definido) [R: PLAN_VERIFICACION §1]; hace falta confirmar que caben dos copias (C-04).

### 8.3 Pruebas de aceptación de OTA (8 casos)
1. Imagen válida se instala y arranca.
2. Imagen con firma de otra clave es rechazada.
3. Imagen corrupta (un byte cambiado) es rechazada.
4. Corte de energía a la mitad de la escritura: el equipo sigue arrancando la versión anterior.
5. Imagen nueva que no pasa autoprueba vuelve a la anterior sola.
6. Versión anterior a la de seguridad mínima es rechazada.
7. Intento por Modbus o por una orden de origen red: rechazado y registrado.
8. Con la unidad en EXECUTE: rechazado.

---

## 9. Mapa de integraciones

| Integración | Prioridad | Cómo se hace | Por qué esa prioridad | Riesgo / nota |
|---|---|---|---|---|
| **Modbus RTU** (esclavo) | **P0, existe** | Mapa PackTags v1 [R] | Es el idioma común de integradores y de AP GATE; no requiere nube | Escritura limitada y registro 305 de solo lectura [R]; fijar validación por registro |
| **CSV / exportación local** | **P1** | Desde AP Studio/consola: eventos, causas, turno; luego automatizable | Barata, la acepta TI sin discusión, es lo que usa quien hoy captura en papel [H]. Respalda la pregunta Q2 del guion | Los datos personales de operador (si se agregan) son dato personal: consultar a legal-marca |
| **Modbus TCP** | **P2** | Vía AP GATE o puente de terceros; el Wi-Fi de la base solo si se agrega lista de direcciones permitidas y escritura apagada por defecto | Los SCADA e integradores lo piden; pero el ESP32 con Wi-Fi expuesto es superficie de ataque | Modbus TCP clásico no tiene autenticación ni cifrado; existe «Modbus/TCP Security» con TLS en el puerto 802 [V: [modbus.org](https://modbus.org/modbus-specifications), consultado 14-oct-2026] pero la adopción en equipos pequeños es `PD`. Segmentar la red |
| **MQTT con Sparkplug B** | **P2 → P3** | En AP GATE, con TLS y escritura restringida; AP Base no habla MQTT en la tanda 1 | Sparkplug 3.0 se publicó en dic-2022 y se dice certificado como estándar ISO/IEC [V: [Eclipse/ARC](https://www.arcweb.com/node/131791) y [HiveMQ](https://www.hivemq.com/blog/whats-new-eclipse-sparkplug-30-specification-iiot-industry-40), consultados 14-oct-2026]; el número exacto «ISO/IEC 20237» **no se pudo confirmar** en esta búsqueda [CG] | No construir sin un SCADA real que lo pida (condición de etapa 3 del estudio §11) |
| **Home Assistant** | **P3** (por documentación) | Receta con su integración Modbus (RTU/TCP) [V: [home-assistant.io/integrations/modbus](https://home-assistant.io/integrations/modbus/), consultado 14-oct-2026]; descubrimiento por MQTT después | Útil para AP Lab, edificios, Agro y a quien ya lo usa; **no** requiere firmware nuevo | AP Home está en pausa; no comprometer soporte residencial. Sin promesas de compatibilidad |
| **OPC UA** | **P4** | Gateway Linux con open62541 (MPL-2.0) y el modelo OPC 30050 de PackML [R: estudio §7.4, §7.7] | Lo piden integradores de alto nivel, pero no la planta Tier 2/3 objetivo [H] | No portar al ESP32; se hace solo en gateway y con cliente que lo pague |
| **REST/JSON local** | **Existe** | `/api` | Base de la consola | Ver hallazgo 1: sin autenticación; no promoverla como integración hasta resolver |
| **EtherNet/IP · PROFINET** | **No (terceros)** | Pasarela comercial | Mercado de las grandes marcas; AP no compite aquí [R: ANALISIS §2.2] | — |
| **IO-Link** | **No** | — | No hay pila abierta madura para ESP32 [R: estudio §7.4] | — |
| **Correo/mensajería para andon** | **P3** | Solo desde un gateway/servidor del cliente, nunca desde el lazo de control [R: estudio §7.2] | Escalar avisos es valioso | Depende de V2 o de Wi-Fi con salida a internet |

---

## 10. Estrategia «sin nube» y opción futura de nube

### 10.1 Qué significa «sin nube» (compromiso de producto)
1. **Todo lo esencial funciona sin internet:** estado PackML, OEE, causas, andon, bitácora, consola, exportación CSV, Modbus.
2. **Los datos se quedan en la planta** salvo que el cliente decida otra cosa [R: PREVENTA].
3. **No hay conexión saliente por defecto:** el equipo no llama a ningún servidor de AP.
4. **Actualizaciones locales firmadas** (§8) en vez de “la nube actualiza”.
5. **Hora** por reloj con batería, consola o red local; SNTP solo si el cliente lo permite [R: PACKML].

### 10.2 Opción de nube futura (no antes de T4 y solo con cliente que la pida)
| Principio | Detalle |
|---|---|
| Opcional y apagada por defecto | Se activa por configuración local, con aviso |
| **Solo saliente** | El equipo inicia la conexión (MQTT con TLS) hacia un *broker* del **cliente** primero; un servicio de AP, solo después y con asesoría legal [R: ORGANIZACION regla 10] |
| Identidad por equipo | Credencial única por equipo (certificado o secreto), sin contraseña por defecto [R: estudio §7.6] |
| Lectura por defecto, escritura restringida | La nube nunca reanuda ni rearma una máquina [R: estudio §7.5]; órdenes de escritura limitadas a lista permitida y confirmación local |
| Privacidad | Qué dato sale, dónde se guarda y quién lo ve: lista de verificación para abogado (dato personal de operadores; no se ha verificado la ley aplicable aquí) |
| Costo y soporte | Una nube propia crea un costo recurrente y una obligación de soporte que hoy no existen: decisión de Dirección con finanzas |

### 10.3 IEC 62443 en términos prácticos
> AP **no declara** ningún nivel de seguridad (SL) ni cumplimiento de IEC 62443. Se usa como **lista de diseño**; certificar es otra decisión (costo y organismo `PD`).

La norma agrupa siete requisitos fundamentales; Parte 4-2 aplica a componentes y define niveles SL1-SL4 [V: [INCIBE-CERT](https://www.incibe.es/en/incibe-cert/blog/iec-62443-4-2-need-secure-components), consultado 14-oct-2026]. Lo que significa para AP (lista práctica, SL1-SL2):

| Requisito | Qué hace AP | Estado |
|---|---|---|
| Identificación y autenticación | Clave por equipo en la red de configuración (ya existe `claveAP()`, va en la etiqueta [R: APControl.ino L336]); falta autenticar la `/api` en red | Parcial |
| Control de uso | Orígenes local/red con permisos distintos [R] | Hecho en diseño |
| Integridad del sistema | OTA firmada (§8), CRC de configuración [R] | OTA pendiente |
| Confidencialidad de datos | TLS para MQTT/Modbus-TCP-Security; sin secretos en texto claro en respaldo | Pendiente |
| Flujo restringido de datos | Segmentación: equipo en red de campo; salida solo por gateway | Guía de instalación pendiente |
| Respuesta oportuna a eventos | Bitácora de cambios de configuración, de modo y de orígenes [R] | Parcial |
| Disponibilidad de recursos | Vigilante, estado seguro [R] | Hecho en diseño |

Nota de alcance: una fuente de segundo nivel (documento sobre SL2) sostiene que la autenticidad del software es exigencia propia de niveles superiores al SL1 [V débil: [ciso2ciso/62443 SL2](https://ciso2ciso.com/wp-content/uploads/2024/06/62443-SL2-as-a-Minimum-Baseline.pdf), consultado 14-oct-2026]; no se pudo verificar la redacción exacta de SR 3.4, así que la OTA firmada se adopta por **buena práctica**, no por obligación demostrada.

### 10.4 Riesgos de seguridad concretos y qué hacer
| Riesgo | Dónde | Mitigación propuesta | Dueño |
|---|---|---|---|
| `GET /api?c=ORDEN` sin autenticación y con efectos | `APControl.ino` L414 [R] | Autenticar (clave de equipo), mover órdenes a POST con cabecera, rechazar peticiones cruzadas de sitio; mantener Stop/Hold/Abort de red; revisar las órdenes de salida y de configuración | ap-firmware con ap-web-software |
| Contraseña Wi-Fi guardada en NVS y enviada por orden `WIFI STA red,clave` | `APControl.ino` L272-273 [R] | No devolverla en `/api`; borrar en «valores de fábrica» | ap-firmware |
| Vínculos UDP entre equipos (puerto 4210) sin autenticación [R: ARQUITECTURA §2] | Red local | Firma/ clave compartida o apagado por defecto | ap-firmware |
| Modbus sin autenticación | Bus RS-485 y TCP | Escritura limitada; segmentación; MBAP/TLS cuando exista | ap-firmware |
| Cadena de suministro del firmware | Bibliotecas | SBOM, licencias y revisión de actualizaciones | ap-firmware |
| Aviso de vulnerabilidades | Soporte | Dirección de contacto y proceso; si se vende en la UE, la Ley de Resiliencia Cibernética (CRA) exige notificar vulnerabilidades explotadas desde el 11-sep-2026 y el resto desde el 11-dic-2027 [V: [Jones Day](https://www.jonesday.com/en/insights/2026/07/eu-cyber-resilience-act-24hour-reporting-duties-start-september-11-2026), [PwC](https://www.pwc.ch/en/insights/regulation/eu-cyber-resilience-act.html), consultados 14-oct-2026]. **No aplica mientras no se exporte a la UE**: confirmar con abogado | ap-legal-marca |

---

## 11. Lo que NO se hará (y por qué)

| # | No se hará | Por qué | Cuándo se reconsideraría |
|---|---|---|---|
| 1 | Funciones de seguridad de máquina (paro de emergencia, guardas, cortinas, LOTO) | Regla 5; exige equipos certificados (ISO 13849-1, IEC 60204-1) | Nunca como producto de AP; solo leer el estado de un relé de seguridad |
| 2 | Competir como «un PLC más» | Mercado concentrado [V: GMI, `ANALISIS_ECOSISTEMA.md` §2.1]; guerra perdida | No |
| 3 | SKU CA y AP Home sin pruebas de seguridad eléctrica | Regla 6; riesgo legal y de incendio | Tras puerta C y organismo acreditado |
| 4 | Bus CAN propio (AP BUS/NODE) | Protocolo que nadie pidió; Modbus RTU/TCP cubren | Si un cliente pagado lo requiere |
| 5 | Nube propia obligatoria o cobro por suscripción como modelo base | Contradice el diferenciador (sin nube, pago único como hipótesis) | Opción de §10.2 con demanda real |
| 6 | Control remoto de procesos desde internet (reanudar, rearmar) | Seguridad y responsabilidad; regla de origen local | No |
| 7 | OTA “automática” desde un servidor de AP | Expone la planta; no hay infraestructura ni asesoría | Tras §10.2 y revisión legal |
| 8 | Portar OPC UA o PROFINET/EtherNet/IP al ESP32 | Sin pila madura abierta; esfuerzo alto [R: estudio §7.4] | Gateway Linux con cliente |
| 9 | Placa base más grande (más relés/entradas) | Los módulos Modbus escalan sin rehacer certificación ni la placa | Si un volumen de clientes justifica un segundo SKU |
| 10 | Medir tensión de red en la base | Seguridad eléctrica y certificación | Módulo aparte y certificado |
| 11 | Medición “certificada” de energía, calibración trazable (AP Frío) sin laboratorio | No hay trazabilidad propia | Con laboratorio de calibración |
| 12 | Retrofit de control, RFID de habilitación, bancos de baterías | Riesgo de seguridad y responsabilidad [R: ANALISIS §4] | Con socio y evaluación de riesgos |
| 13 | Línea AP LED/luz dentro del plan industrial | Otro mercado y otro proveedor [R] | Plan separado |
| 14 | Prometer sellos (CE, UL, NOM, IFT), fechas o precios antes de tiempo | Regla 2 | Cuando existan certificados y cotización |
| 15 | Usar código GPL dentro del firmware | Obligaciones al distribuir; evitar [R: estudio §7.7] | No |
| 16 | Quemar fusibles de seguridad en prototipos | Irreversible (§8.2) | Lote de producción |
| 17 | Rediseñar hardware sin medición o entrevistas | Regla de la escalera §1.2 | Con evidencia |
| 18 | Una API distinta por producto | Rompe el principio de plataforma | No |

---

## Hallazgos (ordenados por gravedad)

1. **Alta — `/api` sin autenticación y con órdenes por GET.** Dónde: `firmware/APControl/APControl.ino` línea 414: `web.on("/api", …{ if (web.hasArg("c")) ejecutar(web.arg("c")); … })`, sin clave. Por qué falla: cualquier equipo de la red (o una página abierta en un navegador de la red) puede enviar Stop, Hold o Abort y otras órdenes de origen «red» a una máquina; por ser GET, una página maliciosa puede dispararlas con una imagen o un enlace [CG, mecanismo; no probado en hardware]. Cómo comprobarlo: abrir `http://IP/api?c=PK%20HOLD` desde otro equipo. Corrección propuesta: §10.4 (autenticar, POST, cabecera, revisar qué órdenes de salida/configuración admite el origen red). Conviene resolverlo **antes de la puerta B**. No es mi área: propongo, no aplico.
2. **Media — Estados del catálogo sobrestimados.** `web/index.html` L882-885 marca «Servicio» a la Consola AP Base y AP Studio, pero `WEB_Y_PLACA.md` dice que la consola no se ha probado con una placa real. Propuesta: «Prototipo» hasta probarla (criterio §5.1).
3. **Media — Un solo RS-485 no puede ser esclavo y maestro a la vez.** Energía, expansión por módulos y poka-yoke con AP INPUT piden maestro; un SCADA pide esclavo. Decisión pendiente: AP GATE como maestro, o segundo puerto (V7). Afecta la narrativa de «módulos de expansión».
4. **Media — OTA y eFuse irreversibles.** Quemar Secure Boot en prototipos bloquea unidades de laboratorio; además falta confirmar el flash del módulo y que quepan dos imágenes (C-04, §8.2).
5. **Media — La bitácora y los tiempos por estado se reinician al apagar** (`PACKML.md` «Lo que falta» 2): una máquina con cortes pierde OEE por turno durante el piloto. Mitigación de firmware con instantáneas limitadas por desgaste; solución duradera: V3.
6. **Media — El plan de la tanda 1 no mide Wi-Fi dentro de un gabinete metálico.** Agregada M14.
7. **Baja — El código del optoacoplador bipolar no está identificado** (`PUESTA_EN_MARCHA.md` §1: «pendiente de verificar»). Debe resolverse antes de pedir una Rev C (C-01); no se inventa aquí.
8. **Baja — Número ISO de Sparkplug no verificado** en esta consulta; el estudio previo lo da como ISO/IEC 20237 [CG]. No citarlo como cifra hasta confirmarlo.

## Qué falta saber
- Resultados de la tanda 1 (todo el §4) y de al menos 5 entrevistas (proporción NPN, aceptación de Wi-Fi, apagones, turno).
- Flash real del módulo ESP32-C3-WROOM-02 y esquema de particiones (hoja original pendiente).
- Código verificado del optoacoplador bipolar SOP-4 y su efecto en el umbral.
- Cuántos resúmenes de clave y qué irreversibilidades tiene Secure Boot v2 en este chip (guía de Espressif).
- Si algún cliente necesita Ethernet, más de 7 salidas o 8 entradas, o Sparkplug.
- Texto oficial de IEC 62443-4-2 (SR 3.4 y siguientes) y de Modbus/TCP Security; número ISO de Sparkplug.
- Costo y plazo de las tandas, de EMC y de pruebas eléctricas: no hay cotizaciones (precio y margen quedan en `ap-finanzas`).
- Si el CRA de la UE o la ley mexicana de datos personales aplican a un cliente real (consulta a abogado).

## Siguiente paso recomendado
1. Dirección aprueba o ajusta la política de versiones (§7), el catálogo (§5) y la tabla M1-M14 (§4) como **documento de decisión de T1**.
2. ap-firmware y ap-web-software atienden el hallazgo 1 (autenticación de `/api`) y congelan `api` 3 y PackTags v1 como meta de T2.
3. ap-hardware identifica y verifica el optoacoplador bipolar y los pines libres para identificación (C-01, C-02), **sin pedir** Rev C todavía.
4. ap-compras cotiza la tanda 1 y ap-calidad-normas añade M14 al plan.
5. ap-ventas arranca las entrevistas con las preguntas Q1-Q4 y Q7 como prioridad.

## Fuentes (consultadas el 14-oct-2026)
- [Espressif: ESP32-C3 Security Overview (Secure Boot, OTA, anti-retroceso)](https://docs.espressif.com/projects/esp-idf/en/latest/esp32c3/security/security.html)
- [INCIBE-CERT: IEC 62443-4-2, componentes seguros](https://www.incibe.es/en/incibe-cert/blog/iec-62443-4-2-need-secure-components)
- [Documento sobre SL2 como línea base (fuente secundaria)](https://ciso2ciso.com/wp-content/uploads/2024/06/62443-SL2-as-a-Minimum-Baseline.pdf)
- [Rockwell: requisitos de integridad del sistema (ejemplo de OTA firmada SL1)](https://www.rockwellautomation.com/en-gb/docs/technical/logix5000/_online/1756-um900/controllogix-5590-controller-user-manual-ditamap/develop-secure-applications/requirements-for-system-integrity.html)
- [Eclipse: anuncio de Sparkplug 3.0 (vía ARC)](https://www.arcweb.com/node/131791) · [HiveMQ: novedades de Sparkplug 3.0](https://www.hivemq.com/blog/whats-new-eclipse-sparkplug-30-specification-iiot-industry-40)
- [Siemens: cumplimiento de IEC 61131-2 en módulos de entrada](https://support.industry.siemens.com/cs/attachments/109477921/109477921_Compliance_IEC_61131-2_DI_module_en.pdf) · [Beckhoff DK9222](https://download.beckhoff.com/download/document/application_notes/DK9222-0909-0008.pdf) · [Analog Devices: entradas industriales](https://www.analog.com/en/design-notes/industrial-digital-inputs-with-the-max22191.html)
- [Modbus Organization: especificaciones (incluye Modbus/TCP Security, puerto 802)](https://modbus.org/modbus-specifications)
- [Home Assistant: integración Modbus](https://home-assistant.io/integrations/modbus/)
- [Jones Day: obligaciones de reporte del CRA desde el 11-sep-2026](https://www.jonesday.com/en/insights/2026/07/eu-cyber-resilience-act-24hour-reporting-duties-start-september-11-2026) · [PwC Suiza: CRA](https://www.pwc.ch/en/insights/regulation/eu-cyber-resilience-act.html)
- [SemVer](https://semver.org/) [CG; no consultada en esta sesión]
- Repositorio: `ANALISIS_ECOSISTEMA.md`, `ESTUDIO_MERCADO_INDUSTRIAL.md`, `ARQUITECTURA.md`, `WEB_Y_PLACA.md`, `PACKML.md`, `PUESTA_EN_MARCHA.md`, `PLAN_VERIFICACION.md`, `PREVENTA_AP_MONITOR.md`, `7r-tour/gen/make.py`, `firmware/APControl/APControl.ino`, `web/index.html`.
