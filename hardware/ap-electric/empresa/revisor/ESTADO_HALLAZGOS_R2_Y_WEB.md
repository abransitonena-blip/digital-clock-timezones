# Estado de los hallazgos de la segunda revisión y de la revisión de la web

Actualizado el 15-oct-2026. Informes: [INFORME_REVISION_2.md](INFORME_REVISION_2.md) y [INFORME_REVISION_WEB.md](INFORME_REVISION_WEB.md). «Cerrado» = corregido y con prueba por software; nada se ha medido en una placa ni probado con Web Serial real.

## Firmware y pedido (R2)
| ID | Estado | Qué se hizo |
|---|---|---|
| R2-01 | Cerrado | Contadores I2C separados de lectura y de escritura |
| R2-02 | Cerrado | `PK ENT` y los registros 306-309 parten de la configuración vigente (con prueba) |
| R2-03 | Cerrado | La clave se genera con la fuente de ruido del convertidor analógico (`bootloader_random`) mezclada con `esp_random` y la MAC. Falta verificarlo en hardware |
| R2-04 | Cerrado | AP Studio pide y envía la clave del equipo; `AP_LOGICA.md` lo documenta |
| R2-05 | Cerrado (decisión) | La vigilancia Modbus es un latido de **escrituras** (documentado); las lecturas no cuentan |
| R2-06 | Cerrado | La consola tiene el botón «Empezar cuenta nueva» (`PK BORRAR`, solo USB) y explica el «—» |
| R2-07 | Cerrado | `FABRICA` solo por USB o por Modbus con permiso local; conserva la clave y las maniobras de los relés |
| R2-08 | Cerrado | La consola USB ejecuta solo líneas completas (buffer propio) |
| R2-09 a R2-14 | Abiertos (bajos) | Truncamientos de argumentos, escrituras Modbus múltiples no atómicas, `detectar7R`, estado inicial de entradas acopladas, clave en claro sin límite de intentos, `validar` de `nCanales` |

## Web y consola (W)
| ID | Estado | Qué se hizo |
|---|---|---|
| W-01 | Cerrado | Sin base de datos el formulario dice «NO SE ENVIÓ», no da folio, no guarda el contacto en el navegador y ofrece copiar el resumen (con prueba) |
| W-02 | Cerrado | El panel del equipo y la lista de interés toleran documentos malformados (con prueba) |
| W-03 | Parcial | El firmware envía `Access-Control-Allow-Origin: *` en `/api` (leer el estado). La consola desde `https://` sigue sin poder hablar con un equipo `http://`; el texto de ayuda lo dice. Sin probar en una placa |
| W-04 | Parcial | Los textos dicen lo que la red puede hacer con la clave. La clave sigue viajando por HTTP y es la del Wi-Fi: separarlas y limitar intentos queda para la rev C / API 3 |
| W-05 | Cerrado (textos) | La web y la consola ya no prometen el apagado por pérdida de comunicación salvo para canales Modbus con vigilancia activa |
| W-06 | Cerrado | Estados unificados: 7R Tour 24DC y AP Monitor 24 = Diseño; Home y 7R Tour CA = En pausa; consola y AP Studio = Prototipo (software en demostración) |
| W-07 | Cerrado | El límite de 30 V está en la ficha del 7R Tour 24DC y en la matriz; alumbrado de 127/220 V y motores se marcan «no en el piloto» |
| W-08 | Cerrado | Definición de OEE junto a los indicadores y botón para empezar cuenta nueva |
| W-09 | Cerrado | Botón deshabilitado al enviar, cantidad conservada, el límite de 20 avisa en lugar de borrar, folio de 6 caracteres, se muestran todas |
| W-10 | Parcial | Etiquetas corregidas (la lista de interés la puede leer quien abra la página). Falta decidir las reglas de la base y el botón «borrar mis datos» con el área legal |
| W-11 | Cerrado | `FABRICA` detalla qué borra, solo por USB y verifica la respuesta; las órdenes delicadas de «Avanzado» piden confirmación |
| W-12 | Abierto | CSP, separar el origen de la consola y lista de órdenes permitidas |
| W-13 | Cerrado en parte | El perfil Andon exige 4 entradas; `TEST` con «?» ya no se muestra como rechazo. Faltan botones PackML adicionales |
| W-14 | Cerrado en parte | Indicador «SIN DATOS», aviso de reinicio, tope de canales/entradas, decodificación en flujo. Falta correlación por orden |
| W-15 | Parcial | Contraste subido, botones de 44 px, barra superior desplazable en móvil. Falta medir con lectores de pantalla |
| W-16 | Cerrado | Textos imprecisos corregidos |
| W-17 | Abierto | Panel del equipo con búsqueda, filtros y notas |
| W-18 | Cerrado | Pruebas nuevas: sin base de datos, doble envío, datos malformados, límite de 20, cantidad, perfil en AP Home |
| W-19 | Documentado | La web avisa que los vínculos UDP no llevan clave ni firma |
