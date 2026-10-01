# Placa B: fuente capacitiva de 3 salidas para letreros fijos, 127 VCA

Placa de **50 × 50 mm**, una cara y **sin puentes**. Es **no aislada**, con el mismo principio que Radox.

Cada salida es independiente y lleva capacitor de poliéster, resistencia fusible de 220 Ω 1 W y puente 2W10. La resistencia R10 de 1 MΩ, entre L y N, descarga los capacitores al desenchufar.

> **PELIGRO:** con la placa enchufada, todo (placa, cables y LED) queda a voltaje de red. Desenchufa antes de tocar y monta la placa dentro de la caja.

## Elegir el capacitor de cada salida

La corriente es `I = 240 × C × (180 V − Vtira)`. La tira no debe pasar de unos **100 V**.

| Tira | Ejemplos | Capacitor | Corriente |
|---|---|---|---|
| hasta 30 V | 9–10 verdes o blancos, 15 ámbar | **224J 400V** | ≈ 8 mA |
| 40–60 V | 27 ámbar (54 V), 20 blancos (60 V) | **334J 400V** | ≈ 9–10 mA |
| 60–100 V | 27 blancos (81 V), 45 ámbar (90 V) | **474J 400V** | ≈ 9–11 mA |

- Una salida sirve también para **las flechas** de la placa A: el ánodo común va al **+** de la salida.
- Sin electrolítico a la salida: si una tira se abre, no hay nada que reviente.

## Conexiones

- **J1 (clema):** 127 VCA, N y L. Van en paralelo con el mismo cordón.
- **Salidas (pads para soldar cable):** **S1+/S1−, S2+/S2−, S3+/S3−**.
  - El **+** va al ánodo del primer LED de la tira.
  - El **−** va al cátodo del último LED.

## Materiales (3 salidas)

| Cant | Pieza |
|---|---|
| 3 | Capacitor de poliéster 400 V (224J, 334J o 474J según la tabla; paso 10 o 15 mm) |
| 3 | Resistencia 220 Ω 1 W fusible (flameproof) |
| 3 | Puente 2W10 (el **+** del cuerpo va al pad cuadrado) |
| 1 | Resistencia 1 MΩ ½ W |
| 1 | Clema de 2 polos 5.08 mm |

Si solo usas 2 salidas, no montes las piezas de la tercera.

## Archivos (`fabricacion/`)

- `pcb/1_cobre_para_planchado_1a1.pdf`
- Lado de componentes, plantilla de perforaciones y guía de ensamble.
- Esquema, BOM, Gerber y reportes: ERC y DRC sin errores, y el esquema coincide con la placa.

También está el panel de 10×10 junto con la placa A, en `../panel-10x10/`.
