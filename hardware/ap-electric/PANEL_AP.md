# Panel AP: la pantalla interactiva del PLC

> **Estado: CONCEPTO.** Es una página web que se abre en una tableta, computadora o celular; **no es una pantalla física**. Ninguna pantalla táctil con el sello AP está diseñada: no hay una pantalla verificada en el catálogo de piezas de JLCPCB, y no se inventó una.

`web/panel.html` (archivo único, sin nube) muestra y manda lo que hace el PLC de una cadena AP Rack:

| Elemento | Qué hace |
|---|---|
| **Botón de salida** | Alterna una salida Q (con confirmación opcional) |
| **Luz** | Muestra una entrada I, una salida Q, una marca M o un bit de sistema S (verde, rojo o ámbar) |
| **Valor** | Muestra A (analógica), R, T, C o V (tensión de un módulo), con unidad, barra y límites de alarma |
| **Consigna** | Escribe un registro R1-R16 con − / + o tecleando (para que el programa compare) |
| **Interruptor de marca** | Escribe una marca M1-M64 |
| **Tendencia** | Gráfica de un valor en el tiempo (los últimos ~5 minutos en la página) |
| **Módulos en la cadena** | Los módulos con su tipo, tensión y estado |
| **Alarmas** | Módulo sin respuesta, tensión fuera de 12-30 V, falla, error del PLC y el historial de cambios |
| **Estado del PLC** | RUN/STOP, instrucciones y ciclos |

Además, la sección **Programa PLC** carga el texto del programa en el equipo y lo pone en RUN o STOP (con confirmación).

## Cómo se usa

1. Abre `panel.html`. **Conectar** por USB (Chrome o Edge), por red (IP del módulo cabeza y la clave de la etiqueta) o **Demostración** (3 módulos simulados).
2. **Diseñar**: agrega elementos de la paleta, arrástralos en la cuadrícula de 12 × 8, cambia su tamaño con la esquina, edita sus propiedades, agrega páginas. El diseño se recuerda **en ese navegador** y se puede **exportar/importar** como texto (para llevarlo a otra tableta).
3. **Pantalla completa** (o `panel.html?kiosco=1`) deja solo la pantalla de operación.

## Lo que no es

- **No es una función de seguridad.** No sustituye paro de emergencia, guardas ni relés de seguridad. Un botón del panel no apaga la salida si se cierra la página (el apagado por pérdida de enlace es entre módulos, no con la tableta).
- Por red, la clave viaja **sin cifrar**: solo en una red de confianza. Desde una página `https://` el navegador no deja hablar con un equipo `http://` de tu red (usa USB o abre el archivo local).
- El diseño no se guarda en el equipo; si cambias de navegador, impórtalo.

## Probado

Pruebas en navegador (Playwright, `web/pruebas/prueba_panel.cjs`): demostración completa (botones, consigna, marca, PLC RUN/STOP, programa con error), diseñador (agregar, editar, arrastrar, borrar, exportar e importar, rechazar un diseño con tipo desconocido, que un texto con HTML no ejecute código, recordar el diseño), celular sin desborde, y la **prueba de contrato** frente al JSON real que genera el programa del módulo (`ap_rack.h`).

## Qué falta

- Una pantalla física con su placa (hay que verificar la pieza antes de diseñarla).
- Guardar el diseño en el cabeza para compartirlo entre tabletas.
- Escalera gráfica del programa (AP Studio) conectada a este PLC.
