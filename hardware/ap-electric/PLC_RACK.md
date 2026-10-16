# PLC en una cadena AP Rack (AP LÓGICA multi-módulo)

> **Estado: CONCEPTO, probado en simulación en la PC** (`firmware/pruebas/prueba_plc_rack.cpp`, 29 comprobaciones sobre la cadena simulada de AP LINK) y compilado para el ESP32-C3. No se ha probado en placas.

El **cabeza** de la cadena (módulo 1) corre el mismo motor que AP Control y AP UNO ([AP_LOGICA.md](../AP_LOGICA.md)), pero con las entradas y salidas de **todos** los módulos como si fueran un solo equipo. Cada ciclo (10 ms) lee las entradas de la cadena, ejecuta el programa y manda las salidas por AP LINK.

## Áreas de memoria

| Área | En una cadena AP Rack |
|---|---|
| **I1…** | Entradas digitales de todos los módulos, seguidas en orden de cadena (AP Rack 16: 8; AP Rack IN16: 16) |
| **Q1…** | Salidas de todos los módulos, seguidas (AP Rack 16: 16). La salida 1 del módulo 2 es Q17 si el módulo 1 es un Rack 16 |
| **A1…** | Entradas analógicas de los módulos AI8, en V o mA (solo para comparar: `LD A3 > 4.5`) |
| **R1-R16** | Consignas que **escribe el panel** (`PLC R n valor`); el programa las compara. No se recuerdan al apagar |
| **M1-M64** | Marcas internas; el panel las puede escribir (`PLC M n 0|1`). M65-M128 y los contadores siguen siendo del programa |
| **T, C** | Temporizadores y contadores del motor (16 y 16) |
| **S2** pulso de 1 s · **S3** siempre 1 · **S5** hay falla · **S6** falta algún módulo · **S7** hay más de un módulo · **S11-S26** el módulo n está presente |

## Reglas que importan

- **El programa es dueño de las salidas que nombra** con `OUT`, `SET` o `RST` mientras está en RUN. La consola y el panel **no** pueden cambiarlas (la orden se rechaza); las demás siguen siendo manuales. «Apagar todas» respeta lo que maneja el programa.
- **STOP** apaga las salidas que era del programa; **BORRAR** olvida el programa.
- Si un módulo **deja de contestar** (≈ 1 s), sus entradas valen 0, sus analógicas «no tienen lectura» (la comparación es falsa) y **S6 = 1**. El módulo mismo lleva sus salidas a su estado seguro en 1 s.
- Si el cabeza deja de serlo, el programa **no corre** (y los demás módulos pasan a estado seguro en 1 s).
- Un programa con errores **no sustituye** al que corre: se rechaza y queda el mensaje (`renglon 3: …`).
- El programa y su modo (RUN/STOP) se **recuerdan** al reiniciar el cabeza.

## Órdenes y red

| Orden | Qué hace |
|---|---|
| `PLC TXT LD I9|OUT Q1|…` | Carga un programa (renglones separados por `|`) |
| `PLC RUN` · `PLC STOP` · `PLC BORRAR` | Modo y borrado |
| `PLC M n 0|1` · `PLC R n valor` | Escribir una marca o una consigna (lo usa el [Panel AP](PANEL_AP.md)) |
| `POST /plc?k=CLAVE` · `GET /plc` | Cargar y leer el texto por red (la clave de la etiqueta) |

El estado (`plc.run`, `plc.n`, `plc.err`, marcas, consignas, temporizadores y contadores) va en el JSON de `/api`.

## Qué falta

- Probar con placas y con cargas reales (ver el [plan de verificación](PLAN_VERIFICACION.md)).
- Que AP Studio edite este programa con escalera (hoy se carga como texto desde el Panel AP o por la orden).
- Persistir las consignas R (hoy se pierden al reiniciar).
- Esto **no es una función de seguridad**: un PLC de este tipo no sustituye paros de emergencia ni relés de seguridad.
