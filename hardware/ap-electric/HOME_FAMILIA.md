# AP Home: mejoras al manejo de apagadores y familia separada por uso

> **Estado: CONCEPTO.** No cambia ninguna placa. Lo nuevo es programa (probado en simulación en la PC) y piezas 3D de prototipo (sin imprimir). Los límites eléctricos siguen **por determinar** (ver las hojas de datos).

## Un SKU por uso (cada uno con su caja, bornes y hoja)

| SKU | Para qué | Estado |
|---|---|---|
| [Home Plug](HOJA_DATOS_HOME_PLUG.md) | Enchufar una lámpara; clavija y receptáculo encerrados | Concepto (en pausa) |
| [Home Switch](HOJA_DATOS_HOME_SWITCH.md) | Un circuito de alumbrado con fase y neutro en caja de registro, conservando el apagador | Concepto (en pausa) |
| Home Switch con varios pulsadores | Varios circuitos: **un módulo Home Switch por circuito**, y una tapa de pared con 2 o 3 pulsadores que los manda (por la red local, con los *vínculos* que ya existen) | Solo la tapa 3D; los módulos por circuito ya existen |
| 2G / empotrable en la chalupa | Dos relés en una placa, o una placa que quepa en la caja del apagador | **No existe**: la placa mide 55 × 80 mm y no cabe en la chalupa; exigiría otra placa de red y su evaluación de seguridad |

No se ofrece un Home Switch sin neutro ni un atenuador de red: sin evaluación de fugas y parpadeo con lámparas LED no son seguros de prometer.

## Home en dos piezas: cerebro chico + potencia (nuevo)

Para que Home sea **fácil y no se vea monstruoso**, la placa de una pieza se separa en dos, unidas por un cable de baja tensión de 4 hilos (JST XH):

| Pieza | Qué lleva | Tamaño | Estado |
|---|---|---|---|
| [AP Home CEREBRO](home_cerebro/LEEME.md) | ESP32-C3 (Wi-Fi/BLE), 3.3 V, botón, LED. **Solo baja tensión**: puede ir fuera de la caja metálica | 42 × 56 mm | ERC 0 · DRC 0 · pedido sin errores |
| [AP Home POTENCIA](home_potencia/LEEME.md) | Los 127 V: relé, fuente aislada, fusible, varistor, entrada de apagador | 55 × 68 mm | ERC 0 · DRC 0 · pedido sin errores |

La placa de una pieza (55 × 80 mm) se queda como referencia. **Aviso honesto:** la suma de las dos placas es mayor que la original; lo que se gana es que el cerebro (lo que se ve) va aparte y la parte de red baja de 80 a 68 mm. Para una pieza que de verdad quepa en la chalupa hace falta otra fuente y otro relé más chicos (no hecho). Industrial (AP Rack, AP PLC) **no cambia**.

## Qué se mejoró en el programa

Modo de entrada nuevo **4 = pulsador con gestos** (disponible en la consola y por la orden `E k 4 canal antirrebote doble largo`):

| Gesto | Qué hace |
|---|---|
| Un toque | Alterna el canal, sin esperar (no hay retardo para distinguirlo del doble) |
| Doble toque (< 400 ms entre toques) | Deshace el primer toque y hace la acción configurada |
| Toque largo (800 ms) | Deshace el toque inicial y hace la acción configurada |

Acciones: 0 nada · 1 encender el canal · 2 apagarlo · 3 **apagar todo el alumbrado** · 4 encender todo el alumbrado. «Todo» solo toca canales de **alumbrado**, nunca los de proceso. Con las acciones en 0, el modo se comporta como un pulsador normal. Fuera del modo 4 las acciones se borran y la validación las corrige.

Probado en `firmware/pruebas/prueba_control.cpp` (simulador de entradas con tiempos): toque, doble toque en dos canales, toque largo, toques separados más de 400 ms que no cuentan como doble, canal de proceso excluido de «todo», y validación de valores fuera de rango.

## Piezas 3D nuevas (en [accesorios/](accesorios/LEEME.md))

- `placa_pulsadores_1/2/3`: tapa de pared de chalupa sencilla con 1, 2 o 3 pulsadores de 16 mm y una ventana de luz junto a cada uno.
- `soporte_home_registro`: base con postes en los agujeros de la placa AP Home para fijarla dentro de una caja de registro.

Medidas de la chalupa (82.55 mm entre tornillos) y de los pulsadores: de conocimiento general, **por confirmar con las piezas compradas**. La tapa no es una tapa certificada para instalaciones de red: aquí solo lleva pulsadores de **baja tensión**.

## Qué falta

- Medir el comportamiento con lámparas LED reales (corriente de irrupción, parpadeo) y el límite de carga.
- Imprimir y probar las tapas con la chalupa y los pulsadores reales.
- Decidir con clientes si hace falta una placa de 2 circuitos o empotrable antes de diseñarla.
