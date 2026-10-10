# Actuadores de potencia: qué pone el electricista para que AP ELECTRIC mande cargas grandes

**Regla del ecosistema:** las placas AP ELECTRIC solo manejan baja tensión de seguridad (12-24 V DC). Toda carga de red (127/220/440 V) se conecta con un **aparato certificado de riel DIN**:
- contactor;
- relevador de interfaz;
- relevador de estado sólido (SSR);
- arrancador;
- variador.

Lo instala un electricista en el centro de carga o en el tablero, según la NOM-001-SEDE. La placa solo mueve la **bobina o la entrada de control** de ese aparato.

```
  AP ELECTRIC (24 V DC)            Tablero de potencia (electricista)
  DO8 / AO4 / BASE AUX  ──bobina 24 V DC──►  Contactor ──► bomba, luminarias, motor, resistencias
  AP GATE (RS-485)      ──Modbus──────────►  Variador de frecuencia ──► motor
  AP GATE (RS-485)      ◄─Modbus───────────  Medidor de energía de riel DIN
```

## 1. Qué aparato va con cada carga

| Carga | Aparato recomendado | Categoría de uso | Cómo dimensionarlo |
|---|---|---|---|
| **Luminarias LED con driver de red** (naves, alumbrado público, oficinas) | Contactor modular **para iluminación** o con capacidad declarada para LED | AC-5b / la tabla de lámparas del fabricante | Los drivers piden un **pico de arranque** de decenas de amperes por menos de 1 ms. Cuenta los **drivers por contactor** según la tabla del fabricante, no solo los amperes |
| **Luminarias de descarga** (sodio, aditivos metálicos) | Contactor AC-5a | AC-5a | Corriente de arranque y del capacitor de compensación |
| **Focos incandescentes o halógenos** | Contactor AC-5b | AC-5b | El filamento frío pide unas 10 veces su corriente |
| **Resistencias** (calentadores, hornos, deshielo) | Contactor AC-1 o **SSR con cruce por cero** y disipador | AC-1 | SSR: al 50 % de su corriente sin disipador; con disipador, unos 1-1.5 W de calor por ampere |
| **Motores trifásicos** (bombas, ventiladores, compresores) | Contactor AC-3 + **guardamotor** o relevador térmico | AC-3 | Por la potencia del motor (kW) a su voltaje. El guardamotor se ajusta a la corriente de placa |
| **Motores con velocidad variable** | **Variador de frecuencia** con RS-485 | — | El variador se maneja por **Modbus** desde la AP GATE: marcha, paro, frecuencia, lectura de corriente y fallas |
| **Bombas sumergibles con arrancador propio** | Relevador de interfaz al contacto de "marcha" del arrancador | — | Contacto seco; no se toca la potencia del arrancador |
| **Contactos (tomas) y aparatos** | Contactor AC-1 o relevador de interfaz | AC-1 | Corriente del circuito, con su interruptor termomagnético |
| **Válvulas de 24 V AC** (riego) | Relevador de interfaz con bobina de 24 V DC | — | El contacto conmuta los 24 V AC del transformador de riego |
| **Cargas de 12-24 V DC** | **Directo:** DO8 (1.5 A), PWM4 (6 A, atenuable), BASE (8 A) | — | Sin contactor |

## 2. La bobina: siempre de 24 V DC

- Elige contactores y relevadores con **bobina de 24 V DC** (bornes A1 y A2).
- Una bobina modular consume de 1 a 5 W (40-200 mA): cualquier salida del **DO8** (1.5 A) o del **AO4** (0.5 A) la mueve.
- **Cableado:**
  - pata 1 del conector (+24 V) → A1;
  - pata 2 (salida) → A2.
  - El diodo de la bobina ya viene en la placa.
- Si el contactor que ya existe tiene **bobina de 127/220 V AC**, no la conectes a la placa: pon un **relevador de interfaz** con bobina de 24 V DC, y su contacto manda la bobina de red.
- **SSR:** entrada de 3-32 V DC. Su + va al +24 V y su − a la salida del DO8. Solo para cargas resistivas, o del tipo que diga el fabricante: los SSR con cruce por cero no sirven para motores ni transformadores.

## 3. Protección del lado de red (la pone el electricista)

| Protección | Dónde |
|---|---|
| Interruptor termomagnético | Uno por circuito, según el calibre del cable |
| Interruptor diferencial (30 mA) | Contactos, exteriores, zonas húmedas, bombas sumergibles |
| Supresor de picos (SPD) de riel DIN | Alumbrado exterior y alumbrado público (rayos), entrada del tablero |
| Guardamotor o relevador térmico | Cada motor |
| Botón de paro de emergencia | Máquinas: corta la bobina **por cable**, no por programa |

## 4. Tablero: separación de control y potencia

- **Riel superior:** fuente de 24 V certificada, CORE, módulos AP ELECTRIC (soportes DIN impresos).
- **Rieles inferiores:** interruptores, contactores, relevadores, variadores.
- **Canaletas separadas** para los cables de 24 V y los de red. Si se cruzan, que sea en ángulo recto.
- **Etiquetas iguales** en el programa (`ET S3 Bomba 1`), en el contactor y en el plano.
- Fuente de 24 V **con su propio interruptor**, para poder trabajar en el control sin cortar todo, y al revés.

## 5. Familias de ejemplo (verifica el modelo y su hoja de datos con tu proveedor)

| Tipo | Familias conocidas |
|---|---|
| Contactores modulares (riel DIN, 1-4 polos, 16-63 A) | Schneider Acti9 iCT, ABB ESB, Hager ESC, Finder serie 22, Siemens 5TT |
| Relevadores de interfaz (bobina 24 V DC, contacto 6-16 A) | Finder series 38 y 39, Phoenix Contact PLC-RSC, Weidmüller TERMSERIES |
| Contactores industriales AC-3 | Schneider TeSys, ABB AF, Siemens SIRIUS, LS Metasol, WEG CWM |
| SSR de riel DIN | Carlo Gavazzi RGS/RM, Crydom, Fotek (verifica que sea original) |
| Variadores con Modbus RTU | WEG CFW, Schneider Altivar, ABB ACS, Siemens SINAMICS V20, Delta |
| Medidores de energía con Modbus RTU | Eastron SDM120/SDM230/SDM630, Schneider iEM, Carlo Gavazzi EM |

## 6. Cuál módulo AP ELECTRIC va con cada aparato

| Para mandar… | Módulo | Cómo |
|---|---|---|
| Hasta 8 contactores o relevadores (encendido y apagado) | **AP PRO DO8** | Una salida por bobina |
| Circuitos de alumbrado atenuables de red | **AP LIGHT AO4** | 0-10 V a los drivers + bobina del contactor que les da la red |
| Luminarias LED de 24 V DC | **AP LIGHT PWM4** | Directo, atenuable, 6 A por canal |
| Variador, medidor, PLC | **AP GATE** | Modbus RTU por RS-485 |
| Algo en otro tablero | **AP NODE** + DO8 | Por el AP BUS (24 V + CAN), hasta 250 m |
