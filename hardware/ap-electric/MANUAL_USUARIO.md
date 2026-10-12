# AP Electric: manual breve del usuario (AP Control 1.0)

## Sin internet, desde el primer encendido

- No se necesita cuenta, teléfono, nube ni Wi-Fi.
- **Home Plug / Home Switch:** el botón enciende y apaga.
- **7R Tour:**
  - cada botón del frente alterna su canal;
  - el LED de cada canal indica si su bobina tiene tensión.
- Al llegar la energía todo queda **apagado**, salvo los canales de alumbrado que configures como «último estado» o «encendido».

| LED | Significado |
|---|---|
| Verde (Home) / RUN (7R) | Encendido / funcionando (fijo con el programa PLC en RUN) |
| Rojo / FALLA | Destella: hay una falla (ver abajo) |
| COM (7R) | Actividad del Modbus |

## Fallas que indica

| Falla | Qué revisar |
|---|---|
| Sin 24 V | Fuente de 24 V del 7R Tour |
| Bobina sin tensión | Relé o excitador del canal: requiere servicio |
| Comunicación perdida | Cable RS-485, maestro Modbus. Los canales que mandaba se apagaron |
| Mantenimiento | Un relé pasó el 80 % de su vida de maniobras: programar su cambio |
| Reinicio por vigilante | El programa se reinició solo: si se repite, servicio |
| Expansor I2C | Falla interna del 7R Tour: servicio |
| Configuración inválida | Se usaron valores seguros: revisar y GUARDAR |

## Red local (opcional)

1. MODO 3 s: abre la red **APElectric-XXXXXX** con la clave de la etiqueta. Se cierra sola a los 15 min.
2. Entra a `http://192.168.4.1`: canales, entradas y fallas.
3. `WIFI STA red,clave` conecta el equipo a la red de la casa o la planta (opcional).
4. Con dos equipos en la misma red, `VINC i mac entrada canal modo` hace que una entrada de un equipo mande un canal de otro, sin nube.

## Órdenes (consola USB, página o `/api?c=`)

| Orden | Qué hace |
|---|---|
| `C k 0/1/2` | Apaga / enciende / alterna el canal k |
| `A k 0/1/2` | Arranque del canal: apagado / último / encendido |
| `T k 0/1` | Carga: alumbrado / **proceso**. Proceso = siempre arranca apagado y se apaga al perder la comunicación |
| `P k s` | Apagado automático a los s segundos (minutero de escalera) |
| `E k modo canal ms` | Entrada k: 0 pulsador, 1 interruptor, 2 conmutador de escalera, 3 desacoplada |
| `MB dir baud par vig` | Modbus |
| `GUARDAR` · `FABRICA` | Guardar la configuración · valores de fábrica |
| `PLC RUN` · `PLC STOP` · `PLC BORRAR` | Programa tipo PLC (se sube con POST /plc; lenguaje en `../AP_LOGICA.md`) |
| `PK RESET` … `PK ABORT` · `PK BUENA` · `PK MODO n` | Unidad PackML: estado de la máquina, piezas y modo (ver [PACKML.md](PACKML.md)). Por la web solo parar, retener y abortar |
| `WIFI OFF` | Apaga el Wi-Fi |

Los cambios valen al momento y se guardan con `GUARDAR`, para que la memoria no se desgaste.

## Modbus RTU (7R Tour)

Mapa completo en `firmware/APControl/modbus_esclavo.h`.

| Tipo | Contenido |
|---|---|
| Bobinas 0-6 | Canales |
| Entradas discretas 0-7 | Entradas |
| Entradas discretas 16-22 | Bobina energizada |
| Registros de entrada | Versión, fallas, salidas, maniobras |
| Registros de retención | Configuración (vigilancia, arranque, carga, pulsos, entradas) |
| Registros 100-156 y 300-305 | Estado PackML, tiempos por estado, piezas y OEE (ver [PACKML.md](PACKML.md)) |
| Registro 200 | 0xA55A guarda |
