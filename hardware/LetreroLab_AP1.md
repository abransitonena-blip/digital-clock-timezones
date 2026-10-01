# LetreroLab AP-1: base universal + programador que se enclava

![Conjunto AP-1](ap1-ensamble/render_ensamble.png)

El sistema tiene tres partes:

| Parte | Qué es | ¿Cambia por modelo? |
|---|---|---|
| **Base universal** (`ap1-base/`) | Placa de potencia: entrada protegida y medida, 4 canales de 8 A, 2 canales de **corriente constante** para focos, salida AUX, sensores y la memoria de la base | **No**: es la misma para todos |
| **Programador** (`ap1-prog/`) | El cerebro: ESP32-C3 con Wi-Fi, USB-C, botones, IR, LEDs y conector Qwiic. **Se enclava encima** de la base | No |
| **Placa de LEDs o focos** | La que lleva la luz: letrero BAÑOS, flechas, lámpara, tira… | **Sí**, una por modelo. Se conecta a las clemas de la base |

**Por qué conviene así:**
- **Se fabrica una sola base para todo.** Mientras más piezas iguales, más barato y mejor probado sale cada lote.
- **El modelo vive en la memoria de la base**, no en la placa:
  - nombre del modelo;
  - consumo normal de cada salida;
  - horas de uso;
  - un **número de serie único grabado de fábrica** (AT24CS02), que no se puede borrar y sirve para las **garantías**.
- **Servicio en campo rápido:** si algo falla, se cambia solo el programador (un tornillo) o solo la base.
- **Más seguro:** la red de 127/240 V **no entra a ninguna placa**. Los focos normales se manejan con un relevador o contactor externo desde la salida AUX, como se pidió desde el principio.

## Medidas

| | Base | Programador | Conjunto |
|---|---|---|---|
| Tamaño | 88 × 56 mm, esquinas redondeadas | 52 × 42 mm | 88 × 56 mm de planta |
| Capas / cobre | 2 capas, **2 oz** | 2 capas, 1 oz | |
| Piezas | 65 (todo SMD, salvo clemas, portafusible y zócalo) | 41 | |

Frente a la AP-0.2 (90 × 70 mm, 6300 mm²), la base ocupa **4928 mm² (22 % menos)** y además trae los 2 canales de corriente constante, la memoria de identidad y la salida AUX.

## Cómo se enclavan

- **Base:** zócalo hembra 2×8 de 2.54 mm (J7) y agujero M3 en (84.5, 39.5).
- **Programador:** conector macho 2×8 **por debajo** (J1) y agujero M3 en la misma posición.
- **Montaje:** separador de **11 mm** (zócalo de 8.5 mm + plástico del conector de 2.5 mm) con **tornillo de nylon**. Queda junto a la antena y uno de metal la desafinaría.
- **No se puede poner al revés:** girado 180°, el programador se sale de la base y el agujero no coincide.
- **Antena:** la base tiene una **zona sin cobre** (x 72.5–88, y 0–30.5) justo debajo de la antena del ESP32-C3, en las dos capas.
- **Altura:** bajo el programador solo hay piezas bajas (≤ 4.5 mm). El portafusible y el capacitor alto quedan fuera, y las clemas quedan libres al frente.
- **Verificación:** las 16 patas del conector macho coinciden en posición y en señal con las 16 del zócalo.

Señales del conector (iguales en las dos placas):

| Pata | Señal | Pata | Señal |
|---|---|---|---|
| 1, 2 | +12 V de la base | 3, 4, 16 | GND |
| 5, 6, 7, 8 | PWM canales 1-4 | 9, 10 | CTRL focos CC 1 y 2 |
| 11, 12 | SDA, SCL (I2C) | 13 | ALERTA (protecciones) |
| 14 | AUX | 15 | 3.3 V del programador a los sensores de la base |

## Base universal

![Base](ap1-base/fabricacion/3d/render_superior.png)

**Entrada (J1, 12–24 V, hasta 20 A):**
- **Fusible mini de auto (ATM)**: se cambia sin soldar; se consigue en cualquier refaccionaria.
- Protección de polaridad invertida sin pérdidas: un MOSFET de 1.6 mΩ (0.6 W a 20 A).
- TVS contra picos.
- **Medidor INA238** de 85 V con shunt Kelvin de 1 mΩ: V, A, W y kWh, y alerta por sobrecorriente.

**Salidas, todas en el borde de abajo para cablear por un solo lado de la caja:**

| Clema | Salida |
|---|---|
| **J3** `+V +V` | Positivo común de tiras y letreros |
| **J4** `CH1…CH4` | Negativo conmutado de cada canal, **8 A** c/u (MOSFET 2.8 mΩ + driver), PWM de 19.5 kHz desfasado |
| **J5** `1+ 1- 2+ 2-` | **Focos de corriente constante**, 1 A cada uno; LEDs de hasta unos 2 V menos que la entrada (ver nota) |
| **J6** `12V AUX` | 12 V y salida conmutada, máx. **0.3 A**: bobina de relevador o contactor, o ventilador |

**Corriente constante (AL8860):**
- La corriente la fija una resistencia: `I = 0.1 V / R`. Con 0.1 Ω (la de serie) son **1 A**; con 0.15 Ω, 0.67 A; con 0.33 Ω, 0.3 A.
- El voltaje de los LEDs debe ser **menor que la entrada menos ~2 V**. Con 24 V caben unos 6 LEDs blancos de potencia en serie; con 12 V, unos 3.
- **Las salidas CC son flotantes:** cada foco va **solo** entre su `+` y su `-`. No se unen a tierra ni a otras salidas; la serigrafía lo advierte.
- Llevan su **propio fusible** (F2, 3 A) y se atenúan desde la app.

**Otras partes de la base:**
- **Fuente conmutada a bordo:** LMR16006 de 60 V a 12 V, con su diodo de rueda libre. Alimenta drivers, AUX y programador.
- **Sensores:** temperatura TMP1075 junto a los MOSFET. La memoria AT24CS02 guarda modelo, consumo normal, horas de uso y número de serie.
- **Diseño del cobre:**
  - Planos de potencia de 7–11 mm.
  - Una **franja de retorno** en la capa inferior donde no se permiten pistas, para que la corriente de los 4 canales regrese sin rodeos.
  - Áreas prohibidas al rutear sobre todos los planos de potencia.
- **Arranque seguro:** sin programador, todas las salidas quedan apagadas por resistencias: gates a GND, CTRL a 2.2 k, AUX a 10 k.

## Programador

![Programador](ap1-prog/fabricacion/3d/render_superior.png)

- **ESP32-C3-WROOM-02:** Wi-Fi y Bluetooth LE certificados.
- **USB-C** con protección ESD. Sirve para programar y también para probar el programador solo, sin base.
- **Fuente conmutada AP63203** a 3.3 V, alimentada desde los 12 V de la base o desde el USB (diodos en OR).
- **Botones MODO/BOOT y RESET.**
- **LED verde OK**, que maneja el programa.
- **LED rojo FALLA por hardware:** sigue a la línea ALERTA aunque el programa esté detenido.
- **Receptor IR** a bordo. El conector **J4** (3V3, GND, IR, MODO) sirve para poner un ojo IR y un botón en la tapa de la caja.
- **Conector Qwiic** (JST-SH de 4 patas, I2C). Se conecta sin soldar:
  - pantalla **OLED SSD1306** de 0.96";
  - sensor de luz **BH1750**;
  - reloj **DS3231**.
- **Pull-down de 10 k en los 4 PWM:** al conectar, el ESP32-C3 puede dejar esas patas con pull-up débil unos 0.3 s, lo que encendería los canales de 8 A.
- **IO21 al LED verde:** IO21 transmite el registro de arranque, así que solo hace parpadear el LED. En una salida de luz haría parpadear un foco.

## Programa (`ap1-prog/firmware/LetreroLabAP1`)

Es el mismo programa de la AP-0.2 (app web, horarios, toda la casa, MQTT, OTA, protecciones), con lo nuevo:

- **Diagnóstico de salidas** (pestaña *Salidas* u orden `DIAG`):
  - Prueba cada salida **por turno** con el medidor de precisión de la base.
  - Primero al **5 %**: si a 100 % pasaría del límite, la marca como **corto** sin llegar a encenderla fuerte.
  - Luego al 100 % y mide su corriente.
  - Califica cada salida: **OK**, **sin carga** (cable suelto o LED abierto), **corto**, **baja** (tramo fundido) o **alta**.
- **Aprender** (`APRENDER`):
  - Con la instalación funcionando bien, guarda en la base el consumo normal de cada salida.
  - Desde entonces, en modo fijo o color, el equipo **avisa solo** si el consumo se aleja más de 25 % de lo esperado, sin apagar nada para medir.
- **Focos CC** (`O a b`), **AUX** manual o **ventilador automático** (`Y 1`, enciende a 45 °C).
- **Datos de la base:** modelo (`MODELO texto`), número de serie y horas de uso, en la app y en la pantalla OLED.
- **Pantalla OLED** opcional: IP, V/A/W, temperatura, kWh de hoy, modo, falla o aviso, resumen de salidas y serie de la base.

| Control | Salidas |
|---|---|
| ![](ap1-prog/firmware/capturas/1_control.png) | ![](ap1-prog/firmware/capturas/2_salidas.png) |

**Compilación y grabación:**
- **Estado:** compila sin advertencias (1.35 MB, 68 % de la flash). La app se probó en navegador contra un simulador.
- **Compilar:** `bash hardware/tools/compilar_esp32.sh ap1`. Los binarios quedan en `ap1-prog/firmware/binarios/`.
- **Grabar:** el archivo `_completo_0x0.bin` va por USB-C en la dirección 0x0; el `_actualizacion_OTA.bin` va por Wi-Fi.

## Pedir a JLCPCB

Son **dos pedidos** (o uno con dos diseños). Cada carpeta `fabricacion/jlcpcb/` trae el Gerber (ZIP), la BOM y el CPL:

1. **Base** (`ap1-base`): 2 capas, **cobre exterior 2 oz**, ensamble del lado superior.
2. **Programador** (`ap1-prog`): 2 capas, 1 oz, ensamble del lado superior. El **conector macho 2×8 va abajo**: pídelo con ensamble THT o suéldalo tú.
3. En la revisión de cada BOM, confirma los códigos LCSC. Las piezas nuevas van sin código y se eligen ahí mismo:
   - INA238, AL8860, TMP1075, AT24CS02;
   - shunt 1 mΩ de 4 terminales;
   - portafusible Keystone 3568;
   - zócalo 2×8.
4. En la vista previa del ensamble, revisa el **giro** de los integrados, MOSFET, diodos y USB-C.

**Primera tanda sugerida:** 5 bases y 5 programadores. Pruebas antes de pedir más:
- temperatura a 20 A durante 1 h;
- corte de la protección con carga electrónica;
- diagnóstico con salidas abiertas, en corto (con fuente limitada) y con un tramo desconectado;
- focos CC a 1 A durante 72 h;
- Wi-Fi con el programador montado dentro de la caja.

## Cómo se diseñó y se revisa

- **Una librería, una carpeta por placa:** las placas salen de `tools/placa.py`, la librería común de generación. Cada placa es un archivo de datos: `ap1-base/gen/make.py` y `ap1-prog/gen/make.py`.
- **Comandos:**
  - `bash tools/rutear.sh ap1-base AP1_Base` → genera la placa, rutea con Freerouting en 3 pasadas, rellena los planos y corre ERC/DRC.
  - `python3 tools/salidas.py ap1-base AP1_Base` → archivos de fábrica, PDF, STEP y renders.
  - `python3 tools/modelos_locales.py ap1-base AP1_Base` → copia los modelos 3D dentro del proyecto.
  - `python3 ap1-ensamble/ensamble.py` → modelo 3D del conjunto (base + programador a 11 mm). Sirve para diseñar la caja.
- **Revisión:** las dos placas dan **ERC 0, DRC 0 (incluidas advertencias), 0 sin conectar y 0 diferencias** entre esquema y placa.

## Pendientes y advertencias honestas

- **Nada de esto se ha fabricado ni probado todavía.** El orden de pruebas está arriba.
- **Ruteo automático:** las señales las trazó Freerouting. Las rutas críticas son fijas (sensado Kelvin, 12 V, CTRL de los focos, planos). Antes de un lote grande conviene una revisión visual en KiCad.
- **Diagnóstico de los focos CC:** el medidor está a la entrada, así que para los focos ve la potencia de entrada, no la corriente del LED. Sirve para comparar contra lo aprendido (abierto, bajo, alto), no como medición absoluta en amperes del foco.
- **PWM del AL8860:** se usa a 1 kHz. Hay que confirmar en las primeras placas que la atenuación es pareja; si no, se baja la frecuencia en `CC_HZ`.
- **Modelos 3D faltantes:** USB-C y conector Qwiic (no están en la librería de KiCad) y el shunt (se muestra con el cuerpo de una 2512). Solo afecta las imágenes.
- **AUX:** la salida es de 0.3 A. Un contactor grande necesita su propio relevador intermedio.
