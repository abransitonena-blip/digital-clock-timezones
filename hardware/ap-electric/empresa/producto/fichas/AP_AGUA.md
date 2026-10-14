# Ficha: AP Agua

> **Estado propuesto: Concepto.** Responsable: ap-producto · 14-oct-2026. Marcas: [R] · [H] · PD.

**Qué es [H].** Tablero de bombeo y cisterna: nivel, presión, alternancia de bombas, alarmas y bitácora; la potencia va por contactor externo [R: estudio §9 oportunidad 8].

**Para quién [H].** Condominios, organismos operadores y pequeñas plantas con cisterna.

**Problema.** Controles de bombeo hechos a medida o sin registro. Sin datos de mercado propios (no encontrados).

**Hardware / firmware / web.** Base + AP PRO AI4 (4-20 mA) + contactores del cliente. Firmware con `analogicas`, histéresis y alternancia. Tarjeta de nivel y presión.

**Evidencia.** Escritorio: I=4, E=3, R=5, Rg=3 [R: estudio §9]. Campo: ninguna.

**Lo que NO es.** No maneja motores directamente (los contactores van fuera); no es protección de motor ni seguridad.

**Riesgos.** Cargas inductivas (contactor), intemperie, fallo de sensor sin respaldo, responsabilidad por inundación o falta de agua.

**Siguiente puerta.** Piloto con un cliente y AI4 probado. **Criterio de parar:** requiere condiciones de campo (IP, exterior) que el diseño no cubre.

**Qué falta.** AI4 fabricado y medido, protocolo de pruebas, selección de sensores.
