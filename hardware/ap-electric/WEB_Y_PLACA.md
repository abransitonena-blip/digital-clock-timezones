# La web de AP Electric y la placa base: cómo se hablan

> **Estado: concepto con prototipo de software.** La consola y la web funcionan en demostración y con pruebas automáticas en un navegador; **no se han probado con una placa real**. La API HTTP y la consola USB ya existen en el firmware (sin probar en hardware).

## Idea
La web de la empresa explica y vende lo que hay; la **consola** controla y configura la placa. La consola **no conoce productos**: le pregunta a la placa qué sabe hacer y dibuja solo eso. Así un modelo nuevo no obliga a rehacer la página.

## Tres caminos de conexión
| Camino | Cómo | Origen para el equipo | Cuándo sirve |
|---|---|---|---|
| **USB** | Web Serial (Chrome o Edge) a 115200 baudios, una orden por línea; la placa contesta con una línea JSON | **local**: puede reanudar la máquina, dar el permiso remoto (`PK REMOTO 1`) y correr `TEST` | Puesta en marcha, taller, desde la web pública (https) |
| **Red local** | `GET /api?c=ORDEN` a la IP de la placa | **red**: solo Stop, Hold y Abort; no da permisos | Cuando la consola se abre desde la propia placa (`http://IP/`) o desde un archivo local. Un sitio `https://` **no puede** llamar a un `http://` de la red (regla del navegador) |
| **Demostración** | Simulador dentro de la página | — | Conocer el panel sin equipo |

Una conexión **remota por internet** (nube, MQTT) no existe y no es necesaria. Si se agrega, será opcional, con TLS, credenciales por equipo y escritura restringida (ver `ESTUDIO_MERCADO_INDUSTRIAL.md`, §7.6).

## Contrato placa ↔ consola (API 2)
La respuesta JSON de `/api` y de la línea USB trae, además del estado:
- `api`: versión del contrato (2).
- `cap`: lista de capacidades, por ejemplo `salidas`, `entradas`, `packml`, `plc`, `modbus_esclavo`, `rs485`, `rtc`, `conteo_rapido`, `autoprueba`.
- `cfg`: configuración editable (pulso y acción de comunicación por canal, modo/canal/antirrebote por entrada, entradas del monitor, ciclo nominal) y `mb.par` (paridad).
La consola muestra una sección **solo si** la capacidad existe. **Para sumar un modelo:** el firmware declara sus `cap` y reutiliza las órdenes existentes (`C`, `A`, `T`, `P`, `X`, `E`, `MB`, `PK …`, `GUARDAR`); si trae una función nueva, se agrega una tarjeta a la consola con su capacidad.

## Qué se puede hacer desde la consola
Alternar salidas; ver bobinas, forzado manual y maniobras; ver entradas; configurar canales (carga, arranque, pulso, acción al perder Modbus) y entradas; estado PackML, OEE, piezas, causa de paro y órdenes; Modbus; poner la hora; autoprueba y prueba de relés (solo USB, con confirmación de que no hay cargas); guardar o restaurar a fábrica; **perfiles de aplicación** (listas de órdenes como datos); respaldo de configuración como lista de órdenes.

## Reglas de seguridad que la consola no puede saltarse
- Por red solo se aceptan Stop, Hold y Abort; reanudar es local (USB, botón o `PK REMOTO 1` por USB).
- Un canal de **proceso** arranca apagado y se apaga al perder la comunicación; el equipo lo impone aunque la consola pida otra cosa.
- `TEST RELES` pide confirmación y exige que la unidad esté detenida.
- No es una función de seguridad.

## Web de la empresa (`web/index.html`)
- **La placa**: qué es, qué hace, cómo funciona, qué se espera y qué no es.
- **Catálogo vivo**: una lista de datos (`CATALOGO`) con estado real de cada fila (prototipo, diseño, concepto, en pausa, servicio). Agregar una fila la muestra y la hace solicitable.
- **Solicitudes**: cotización, piloto, muestra, diseño a medida, soporte, interés o proveedor. Genera un **folio**, muestra una confirmación y el estado (Recibida, En revisión, Respondida, Piloto o muestra confirmados, En lista de espera, Cerrada, No viable). **Una solicitud no es una compra**: no cobra, no promete precio ni fecha.
- **Panel del equipo**: quien puede editar la página ve las solicitudes y cambia su estado.
- **Proveedores y marca**: el panel de trabajo que ya existía.

### Datos y reglas (en la página publicada)
| Ruta | Quién lee | Quién escribe | Contenido |
|---|---|---|---|
| `solicitudes/{usuario}` | Equipo y el propio usuario | El propio usuario | Sus últimas 20 solicitudes (con contacto) |
| `confirmaciones/{usuario}` | Equipo y el propio usuario | **Solo el equipo** | Estado y nota de cada folio: la confirmación no la puede fabricar el solicitante |
| `proveedores`, `nombres` | Todos | Equipo | Panel de proveedores y marca |
| `interes/{usuario}` | Todos | El propio usuario | Lista de interés anterior |
Sin base de datos (página fuera de Claude) las solicitudes se guardan solo en el navegador y se puede copiar el resumen.

## Pendiente y siguiente
- Probar la consola USB con una placa real (el protocolo línea a línea y los tiempos de `TEST`).
- Mover la web a un sitio propio con base de datos y correo reales, y un contrato para la política de datos (ver asesoría legal; el contacto de los solicitantes es dato personal).
- API 3 con bitácora, historial por turno y firmas de actualización (OTA firmada).
- Perfiles de aplicación como archivos compartibles.
