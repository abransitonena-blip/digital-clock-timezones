# Ficha: AP Energía

> **Estado propuesto: Concepto.** Sin hardware propio. Responsable: ap-producto · 14-oct-2026. Marcas: [R] · [V] · [H] · PD.

**Qué es [H].** Perfil que lee un medidor Modbus de terceros y muestra demanda y factor de potencia, con alarma por salida cuando la demanda se acerque a un límite que fije el cliente; opciones posteriores: aire comprimido y solar [R: estudio §9 oportunidades 2, 9, 12].

**Para quién [H].** Naves industriales en tarifa de demanda (GDMTH) donde el costo evitable está en el recibo de CFE [R: estudio §9].

**Problema.** Evitar penalizaciones o picos de demanda. Los datos de tarifa y del factor de potencia exigido en 2026 **no se verificaron** (pendiente en el DOF) [R: estudio §12].

**Hardware / firmware / web.** Base + medidor de terceros (modelo `PD`, sin elegir). Requiere `modbus_maestro` (hoy la base es esclava; **conflicto de un solo RS-485**, hallazgo 3) o AP GATE como maestro. Tarjeta de demanda en la consola. **No** se mide tensión de red en la base.

**Evidencia.** Escritorio: I=5, E=2, R=5, Rg=2 [R: estudio §9]. Campo: ninguna.

**Lo que NO es.** No es medición certificada para facturación ni sustituye al medidor de la compañía eléctrica.

**Riesgos.** Dependencia de un medidor de terceros y su mapa de registros; certificación si algún día se mide tensión; la tarifa vigente cambia.

**Siguiente puerta.** Entrevista con una nave en GDMTH dispuesta a un piloto con medidor de terceros. **Criterio de parar:** nadie con ese perfil acepta piloto en 2 trimestres.

**Qué falta.** Elección de medidor, mapa de registros, validación del cálculo con la factura real, `modbus_maestro` probado.
