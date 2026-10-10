# AP ELECTRIC · AP PRO DO8: 8 salidas de 24 V DC protegidas

> Parte de la línea **AP PRO** del ecosistema [AP ELECTRIC](../AP_ELECTRIC.md). Se conecta al programador (AP CORE) por **Qwiic**, sola o en cadena con AP INPUT, AI4 y DIST 4. **Reemplaza al AP OUTPUT** (ULN2003, 7 × 300 mA, sin protección contra cortos).

![render](fabricacion/3d/render_perspectiva.png)

**Para qué sirve:** mandar cargas de 24 V DC desde horarios, entradas, umbrales analógicos, la app o Home Assistant:
- bobinas de **contactores** y relevadores de interfaz de riel DIN, para bombas, motores y luces de red;
- **electroválvulas** de 24 V DC, por ejemplo de riego;
- sirenas, balizas, lámparas piloto y ventiladores de 24 V.

> La red de 127/220 V **no entra a esta placa**. Bombas, motores y luces de red se encienden con un contactor o relevador de estado sólido de riel DIN certificado, instalado por un electricista. Esta placa solo mueve su bobina de 24 V DC.

## Conectores (AP CONNECT, sin borneras)

| Conector | Tipo | Qué se conecta |
|---|---|---|
| **J4** 24V | JST VH 2 patas: 1 = +24 V, 2 = 0 V | Fuente de 24 V DC. **La misma fuente que alimenta la base**: el 0 V es la tierra del programador |
| **J5-J12** (Q1-Q8 en la serigrafía; en el programa S1-S8) | JST XH 2 patas por salida: 1 = +24 V, 2 = salida | Cada carga va **entre las dos patas**: un cable de 2 hilos por bobina o válvula |
| J1 / J2 | Qwiic | Bus I2C del programador / al siguiente módulo |
| J3 | Macho 1×4 de 2.54 mm | Mismo bus por cable dupont |

**Cableado de una carga:** pata 1 (+24 V) → bobina o válvula → pata 2 (salida). Cada salida trae su diodo de bobina (SS14), así que no hace falta poner diodos en las cargas.

## Por qué es "superior" (electrónica de potencia)

| | AP OUTPUT (antes) | **AP PRO DO8** |
|---|---|---|
| Salidas | 7 | **8** |
| Interruptor | ULN2003 (Darlington, 1.1 V de caída) | **NCV8406A**: MOSFET de 65 V con protección propia (pocos cientos de mΩ) |
| Corriente por salida | 300 mA | **1.5 A** continua |
| Total | 0.7 A | **8 A** (fusible mini de 10 A) |
| Cortocircuito en una salida | Daña el ULN2003 | **Limita la corriente y se apaga por temperatura**: las demás siguen funcionando |
| Polaridad invertida | Sin protección | El supresor SMBJ26A conduce y **el fusible se abre** |
| Picos de la fuente | Sin protección | **SMBJ26A** a la entrada |
| Mando de compuerta | 3.3 V | **5 V** (buffer 74HCT125): el MOSFET conduce completo |

- **Arranque seguro:** al encender, el TCA9554 tiene todas sus patas como entradas y las resistencias RD (10k) mantienen apagadas las compuertas. Ninguna salida se activa hasta que el programa lo pide.
- **Cobre de 2 oz** y pistas anchas: 3 mm en el tronco de +24 V y 0.8 mm por salida.

## Límites

| | |
|---|---|
| Tensión de las cargas | 12-24 V DC (máximo 26 V por el supresor de entrada) |
| Corriente por salida | **1.5 A** continua |
| Corriente total | **8 A** al mismo tiempo |
| Fusible general | Mini de auto de **10 A** (F1). Usa 5 A si tus cargas suman menos |

- Una bobina de contactor de 24 V DC de 3 W consume 125 mA. Una válvula de riego de 24 V DC suele consumir 150-300 mA. Un ventilador de 24 V de 120 mm consume 0.1-0.3 A.
- **Lámparas incandescentes y cargas con arranque fuerte:** la protección del NCV8406A puede apagarlas en el arranque. Para ellas usa un relevador de interfaz.

## Cómo funciona

- **Expansor I2C TCA9554, dirección 0x20-0x23:**
  - JP1 cerrado suma 1 y JP2 suma 2. Así caben **4 módulos: S1-S32**. El módulo 0x20 tiene S1-S8, el 0x21 S9-S16, y así.
  - Necesita el programa **1.8 o posterior** (8 salidas por módulo). Con el 1.7 solo se usan S1-S7 de cada módulo.
- **LED verde por salida:** encendido = salida activa.
- **Órdenes:**
  - `SA n 1` enciende la salida n, `SA n 0` la apaga y `SA n 2` la alterna;
  - en los **horarios**, acciones 5 (encender salida), 6 (apagar salida) y 7 (alternar salida), con la salida como valor;
  - las **entradas** de AP INPUT y los **umbrales** de AI4 pueden mandar cualquier salida.
- **App:** tarjeta "Entradas y salidas". **Home Assistant:** un interruptor por salida, con su nombre (`ET S1 Bomba`).
- **Se puede conectar en marcha:** el programa busca módulos cada 5 s.
- **Si el programador se reinicia o pierde la conexión**, las salidas se quedan como estaban hasta que el programa vuelva a escribirlas. Si una válvula o bomba **no debe quedarse encendida**, ponle un límite de tiempo propio, como un flotador o un temporizador del contactor.

## Pedir en JLCPCB

- 2 capas, **2 oz**, 88 × 56 mm. Archivos en `fabricacion/jlcpcb/` (y en `PEDIDO_JLCPCB/9_AP_PRO_DO8`).
- Todas las piezas traen código LCSC (TCA9554PWR C477924, NCV8406ASTT3G C459816, 78L05 C71136).
- Los conectores, J3 y el portafusibles se sueldan a mano en el pedido económico (o van en "ensamble completo").
- **Montaje en riel DIN:** soporte imprimible `ap1-gabinete/din/soporte_din_88x56.stl`.

## Pruebas antes de instalar

1. Conecta solo el cable Qwiic y 24 V. La consola debe decir `AP PRO DO8: 01` (o `AP OUTPUT: 01` con el programa 1.7).
2. `SA 1 1`: el LED de S1 enciende, y entre las patas 1 y 2 de J5 se miden unos 24 V.
3. Con una bobina de contactor real en S1: enciende y apaga 20 veces; el NCV8406A debe quedar tibio.
4. **Prueba de corto** (con fuente de laboratorio limitada a 10 A): pon un cable entre las patas 1 y 2 de S8 y `SA 8 1`. El LED enciende, la salida se protege y **S1 sigue funcionando**. Quita el corto y `SA 8 0`.
5. Desconecta el Qwiic con S1 encendida y vuelve a conectarlo: S1 debe seguir como el programa la tiene.
