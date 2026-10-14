# 8. Software: licencias de las dependencias del repositorio

> **ADVERTENCIA:** inventario y lista de verificación para revisión de un abogado mexicano. **No es asesoría legal.** Las licencias de terceros listadas como `[CG]` salen de conocimiento general, **no se pudieron verificar** en los repositorios oficiales (red restringida) y deben comprobarse en cada paquete. No hay `node_modules`, `package-lock.json` ni `LICENSE` en el repositorio, así que las versiones exactas y los textos de licencia no se pudieron leer aquí.

## 1. Licencia del propio repositorio
- **No existe** archivo `LICENSE`/`COPYING` en la raíz (`ls` el 14-oct-2026) `[R]`. Sin licencia, el código queda con **todos los derechos reservados** por defecto, para quien sea titular `[CG]` por confirmar con abogado.
- `package.json`: `name: digital-clock-timezones`, `version 1.0.0`, **sin campo `license`** `[R]`.
- Los encabezados de `hardware/ap-electric/firmware/APControl/*.h` y `APControl.ino` (leídos hoy) son **comentarios técnicos**: **sin titular, año ni licencia** `[R]`. Archivos: `ap_control.h`, `autoprueba.h`, `logica.h`, `modbus_esclavo.h`, `reloj.h`, `unidad_packml.h`, `APControl.ino` (el encabezado de `unidad_packml.h` no se leyó entero).
- Titularidad: el repositorio tiene autores humanos y herramientas de ayuda; **quién es titular de los derechos** (autor, empleador, la futura sociedad) y cómo se cede a la empresa: **por confirmar con abogado**. Mientras no haya sociedad, los derechos son de la persona autora.

## 2. Aplicación web de reloj (raíz: `package.json`, `src/`) `[R]` para nombres/rangos, `[CG]` para licencias

| Paquete | Rango | Tipo | Licencia habitual `[CG]` | Nota |
|---|---|---|---|---|
| react | ^18.2.0 | dependencia | MIT | verificar |
| react-dom | ^18.2.0 | dependencia | MIT | verificar |
| date-fns | ^2.30.0 | dependencia | MIT | verificar |
| zustand | ^4.4.0 | dependencia | MIT | verificar |
| vite | ^5.0.0 | desarrollo | MIT | no se distribuye en el build |
| @vitejs/plugin-react | ^4.2.0 | desarrollo | MIT | no se distribuye |

Importaciones reales en `src/`: `react`, `react-dom/client`, `zustand` (no se vio `date-fns` importado en el grep, verificar si se usa) `[R]`.
Riesgos: licencias MIT exigen conservar el aviso de copyright y la licencia en las distribuciones; **las dependencias transitivas** (cientos, vía npm) no están listadas: ejecutar un inventario (`npm ls --all` y herramienta de licencias) antes de entregar. Este proyecto de reloj **no forma parte** del producto AP Monitor; confirmar si se publica.

## 3. Firmware `APControl` y binarios `[R]` / `[CG]`

| Elemento | Origen | Licencia habitual `[CG]` | Riesgo |
|---|---|---|---|
| `ap_control.h`, `logica.h`, `modbus_esclavo.h`, `reloj.h`, `autoprueba.h`, `unidad_packml.h` | Código propio, sin dependencias (`<stdint.h>`, `<string.h>`, `<stdio.h>`, etc., biblioteca estándar) `[R]` | Sin declarar | Declarar titular y licencia (propietaria o abierta) |
| `APControl.ino` usa `WiFi.h`, `WebServer.h`, `WiFiUdp.h`, `Preferences.h`, `Wire.h`, `time.h` `[R]` | Núcleo **arduino-esp32** (el script `hardware/tools/compilar_esp32.sh` descarga el núcleo 3.1.1 y arduino-cli 1.1.1) `[R]` | **Núcleo: LGPL-2.1**; marco ESP-IDF subyacente: **Apache-2.0**; bibliotecas del núcleo con sus propias licencias `[CG]` | **Distribuir binarios** (`firmware/binarios/*.bin`, 4.2 MB completo y 1.0 MB OTA `[R]`) obliga, con LGPL, a dar aviso y permitir que el usuario relinkee/sustituya la parte LGPL; suele cumplirse publicando los objetos o el código fuente. Por confirmar con abogado qué obligaciones aplican al enviar equipos a clientes |
| Compilador y herramientas (RISC-V GCC, arduino-cli) | Descargados de github.com | GPL/LGPL (herramientas, no su salida) `[CG]` | Normalmente la salida del compilador no hereda GPL; la biblioteca de tiempo de ejecución puede tener excepciones. Abogado |
| Binarios (`.bin`) | Compilados de lo anterior | Mezcla | Nota: **los binarios no se verificaron en esta ronda**; no se sabe qué módulos contienen |
| Protocolos (Modbus, PackML) | `modbus_esclavo.h`, `unidad_packml.h` implementan sus propios mapas | «Modbus» es nombre de un protocolo/organización; PackML es una guía técnica de ISA/OMAC `[CG]` | Implementar un protocolo abierto suele ser libre, pero **usar el nombre/logo para declarar conformidad no lo es**: ver `05_etiquetado_y_declaraciones.md` |
| Mapa de registros | Propio | — | Si se publica, decidir licencia de documentación |

## 4. Páginas web y consola (`hardware/ap-electric/web`, `hardware/ap-studio`) `[R]`

- `web/index.html` carga tipografías de **Google Fonts**: Saira Condensed, IBM Plex Sans, IBM Plex Mono (`fonts.googleapis.com`) `[R]`. Esas fuentes suelen estar bajo **SIL Open Font License 1.1** `[CG]` (verificar). Riesgo de privacidad: el navegador del visitante contacta a Google (ver `02_aviso_privacidad.md`). Alternativa: alojar las fuentes localmente cumpliendo la licencia.
- La página usa `window.claude.use("user"|"db")` (plataforma donde está publicada) `[R]`: es un servicio de terceros con **términos de la plataforma**; confirmar condiciones, propiedad de los datos y qué ocurre si se cambia de alojamiento.
- `web/consola.html`, `ap-studio/index.html`: sin scripts externos con `src=` en el grep; sin bibliotecas JS externas detectadas `[R]` (revisión no exhaustiva).

## 5. Herramientas Python y hardware `[R]` / `[CG]`

| Elemento | Licencia | Riesgo |
|---|---|---|
| `numpy` (importada en `hardware/tools/`) | BSD-3 `[CG]` | Bajo; solo herramienta |
| `pymupdf` (importada como `fitz`) | **AGPL-3.0** o licencia comercial de Artifex `[CG]` | Alto *si* se distribuyera o se ofreciera como servicio; hoy es herramienta interna de generación. Revisar uso |
| `pcbnew` (KiCad) | GPL-3.0 `[CG]` | Herramienta de generación; la salida (planos, Gerbers) es del autor, salvo bibliotecas |
| Bibliotecas **oficiales de KiCad** | Normalmente **CC-BY-SA 4.0 con excepción** para uso en diseños `[CG]` | Revisar si se redistribuyen símbolos/huellas dentro del repositorio |
| **JLCPCB-KiCad-Library** (CDFER) | **MIT** según el encabezado del script `descargar_biblioteca_jlcpcb.sh` (versión 2025.07.18) `[R]` | No se guarda en el repositorio (~140 MB); `jlcpcb_catalogo.csv` **sí** se genera de ella: conservar el aviso de la licencia MIT `[CG]` |
| `hardware/tools/huellas/LetreroLab.pretty` (huellas propias o copiadas) | **Origen y licencia no encontrados** en los archivos `[R]` | Verificar si son propias; el nombre «LetreroLab» parece de un proyecto previo: confirmar titular |
| Logotipos (`identidad/`) | Generados por `generar.py` con matplotlib y fuente **DejaVu Sans** `[R]` | DejaVu usa licencia libre tipo Bitstream Vera `[CG]`; los logotipos son obra del autor: considerar registro de derecho de autor y de marca (`01_...`) |
| Piezas y huellas de fabricantes (módulo ESP32-C3-WROOM-02, etc.) | Modelos 3D/huellas de terceros | Verificar si se incluyen modelos 3D con licencias; no se redistribuyan sin permiso |

## 6. Marcas de terceros mencionadas en el repositorio
Wi-Fi (Wi-Fi Alliance), Modbus, ESP32 (Espressif), Arduino, KiCad, JLCPCB/LCSC, PackML (OMAC/ISA), IBM Plex: nombrar descriptivamente, sin logos, sin sugerir aval `[CG]` por confirmar con abogado.

## 7. Lista de verificación
- [ ] Decidir titular y licencia del código (propietaria cerrada, fuente disponible, o abierta) y añadir `LICENSE` y encabezado a cada archivo.
- [ ] Hacer inventario automático de dependencias npm con licencias y versiones resueltas (`package-lock.json`).
- [ ] Documentar la licencia y versión del núcleo arduino-esp32 usado para los `.bin` y preparar un **aviso de licencias de terceros** (NOTICE) que acompañe el firmware.
- [ ] Definir si se publica el código fuente del firmware; si sí, cuidar el cumplimiento LGPL/Apache y la licencia propia.
- [ ] Confirmar el origen y licencia de `LetreroLab.pretty` y de cualquier modelo 3D.
- [ ] Revisar `pymupdf` (AGPL) si alguna herramienta se entrega a clientes.
- [ ] Alojar las fuentes localmente o aceptar la transferencia a Google en el aviso.
- [ ] Contrato de cesión de derechos de cada autor a la sociedad (ver `07_...`).
- [ ] Política de contribuciones si colaboran terceros.

## Hallazgos
1. Sin `LICENSE` ni titular declarado: derechos de autor sin definir (media-alta antes de entregar firmware a clientes).
2. Los `.bin` incluyen el núcleo arduino-esp32 (LGPL-2.1 `[CG]`): obligaciones de aviso/relink al distribuir.
3. `LetreroLab.pretty` y `pymupdf` son los puntos de licencia más inciertos.
4. Fuentes de Google cargadas desde la página afectan a privacidad.

## Qué falta saber
Versiones exactas resueltas de npm, contenido de los binarios, origen de `LetreroLab.pretty`, y la decisión de licencia/titular.

## Siguiente paso recomendado
Instalar dependencias en un entorno aparte y generar un reporte de licencias; con eso el abogado redacta NOTICE y decide la licencia del firmware.

## Fuentes
- Revisión del repositorio el 14-oct-2026: `package.json`, `src/`, `hardware/ap-electric/firmware/APControl/*`, `hardware/tools/compilar_esp32.sh`, `hardware/tools/descargar_biblioteca_jlcpcb.sh`, `hardware/ap-electric/web/index.html`, `identidad/generar.py` `[R]`.
- Licencias de terceros: `[CG]`, sin URL verificada en esta ronda. A comprobar en: https://spdx.org/licenses/ y en cada repositorio de paquete.
