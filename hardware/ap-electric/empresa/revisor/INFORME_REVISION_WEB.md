# Revisión adversarial de la web y la consola (14-oct-2026)

Revisor: `ap-revisor-adversarial` (resumen guardado por la dirección; el agente no pudo escribir el archivo). Alcance: `web/index.html`, `web/consola.html`, `web/pruebas/prueba_web.cjs`, contrastados con el firmware y los documentos. Pruebas con Playwright, base de datos simulada, puerto serie falso y servidores HTTP falsos. No pudo revisar: reglas reales de la base de datos, sandbox de la plataforma, Web Serial con placa real. **Sin hallazgos de XSS** (todo entra con `textContent`).

| ID | Grav. | Resumen | Estado |
|---|---|---|---|
| W-01 | alto | Fuera de Claude (o antes de cargar la base) el formulario dice «Listo» y «el equipo te escribe», pero la solicitud solo queda en el navegador | ver ESTADO_HALLAZGOS_WEB.md |
| W-02 | alto | Un documento mal formado en `solicitudes` o `interes` deja vacío el panel del equipo | idem |
| W-03 | alto | La consola «por red» falla por CORS y el firmware no sirve la consola | idem |
| W-04 | alto | Por red, con la clave, se aceptan muchas más órdenes que Stop/Hold/Abort; la clave viaja en la URL por HTTP y es también la clave Wi-Fi | idem |
| W-05 | alto | «Se apaga al perder la comunicación» solo vale para canales mandados por Modbus con vigilancia ≠ 0 | idem |
| W-06 | alto | «Servicio» y «Prototipo» contradicen las definiciones del repositorio (nada existe físicamente) | idem |
| W-07 | alto | La matriz y las fichas contradicen el límite de 30 V del piloto | idem |
| W-08 | medio | H-21: falta la definición de disponibilidad junto al OEE; tras un reinicio el OEE queda en «—» sin explicación ni botón | idem |
| W-09 | medio | Doble envío, límite de 20 que borra en silencio, cantidad que se reinicia, folio de poca entropía | idem |
| W-10 | medio | La nota de interés es legible por todos aunque diga «solo el equipo»; el contacto queda en `localStorage` | idem |
| W-11 | medio | `FABRICA`, `TEST RELES SI` y `CLAVE NUEVA` sin protección en «Avanzado»; aviso de reinicio aunque la orden falle | idem |
| W-12 | medio | Con el puerto USB concedido, una página maliciosa o un XSS del mismo origen manda cualquier orden local | idem |
| W-13 | medio | El perfil Andon se ofrece en AP Home y no funciona; `TEST` con fallas se muestra como «rechazada»; faltan órdenes PackML | idem |
| W-14 | medio | Robustez del puerto: sin indicador de datos viejos, respuestas tardías, JSON sin tope | idem |
| W-15 | medio | Contraste, desbordamiento a 375 px, foco y botones de 40 px | idem |
| W-16 | bajo | Afirmaciones imprecisas («0 cuentas», «nadie toca cables de red», «fuente certificada», «500 pulsos/s») | idem |
| W-17 | bajo | Panel del equipo sin búsqueda, filtros ni notas | idem |
| W-18 | bajo | Las pruebas cubren solo el camino feliz | idem |
| W-19 | bajo | Los vínculos UDP entre equipos no tienen clave ni firma | idem |
