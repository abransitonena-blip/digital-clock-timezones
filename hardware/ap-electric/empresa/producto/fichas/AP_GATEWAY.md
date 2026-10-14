# Ficha: AP Gateway (AP GATE y AP NODE)

> **Estado propuesto: Diseño.** Sin demanda comprobada. Responsable: ap-producto · 14-oct-2026. Marcas: [R] · [V] · [H] · PD.

**Qué es.** Maestro Modbus RTU que lleva datos a MQTT (Sparkplug B) y, después, a OPC UA en un gateway Linux; es la ruta de datos de las demás líneas [R: estudio §7.4, §9 oportunidad 3].

**Para quién [H].** Integradores y mantenimiento que ya tienen SCADA o broker MQTT.

**Problema.** Los gateways de terceros son caros y de configuración pesada (Moxa MGate €518, Teltonika TRB246 €176 [V, `ANALISIS_ECOSISTEMA.md` §2.2]).

**Hardware / firmware / web.** AP GATE (diseño existente) con Ethernet y Modbus TCP por resolver [R: estudio §8]. Sparkplug 3.0 y open62541 (MPL-2.0) son opciones de licencia permisiva [R: estudio §7.7]. Resuelve el conflicto esclavo/maestro de la base (hallazgo 3).

**Evidencia.** Escritorio: I=4, E=2, R=5, Rg=2. Campo: ninguna. El número ISO de Sparkplug no se confirmó [CG].

**Lo que NO es.** No es nube ni control remoto; las escrituras se restringen y el reanudar sigue siendo local.

**Riesgos.** Superficie de ataque de red (ver §10.4 de la plataforma); mantenimiento de integraciones de terceros.

**Siguiente puerta.** Un SCADA real que lo pida (condición de la etapa 3 del estudio). **Criterio de parar:** sin cliente con SCADA en 2 trimestres, se difiere.

**Qué falta.** Ethernet, Modbus TCP, MQTT con TLS, pruebas con SCADA real, dueño de la política de seguridad.
