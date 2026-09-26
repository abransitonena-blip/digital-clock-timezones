# Fuente capacitiva para la palabra "OS" (20 LED amarillos), 127 VCA

Placa de **50 × 50 mm**, una cara y con componentes de patas (THT), hecha para transferencia de tóner. Es el mismo principio que la placa Radox: **no aislada**.

> **PELIGRO:** con la placa enchufada, todo el circuito (placa, cables y LED) queda a voltaje de red. Desenchufa, espera 10 s y
> solo entonces toca. Monta la placa dentro de la caja del letrero, sin partes metálicas accesibles.

## Circuito

```
L ─ R1 220Ω 1W ─┬─ C1 334J 400V ─┬─ AC1 ┐
                │   (R2 1M ‖ C1)  │      ├─ puente 4×1N4007 ─► J2 + / −  →  20 LED amarillos en serie
                RV1 07D201K       │      │
N ──────────────┴─────────────────┴──────┘
```

## Cálculo

Fórmula de corriente: `I = 4·f·C·(Vpico − Vtira)`.

| Caso | Corriente |
|---|---|
| Nominal: 127 V (pico 180 V), tira de 40 V | **11.1 mA** |
| Red a 115 V, Vf alto (44 V) | 9.3 mA |
| Red a 140 V, Vf bajo (38 V) | 12.7 mA |

Otros capacitores posibles:

| C1 | Corriente |
|---|---|
| 224J | 7.4 mA (más tenue) |
| 474J | 15.8 mA (más brillante) |
| 224J + 104 en paralelo | 10.8 mA |

## Materiales

| Ref | Valor | Nota |
|---|---|---|
| R1 | 220 Ω 1 W **fusible** (flameproof) | Limita el pico al enchufar y actúa como fusible |
| RV1 | Varistor 07D201K | Opcional, recomendado |
| C1 | **334J 400 V** poliéster (paso 15 mm) | Fija la corriente |
| R2 | 1 MΩ ½ W | Descarga C1 |
| D1–D4 | 1N4007 | Puente rectificador |
| J1, J2 | Clema 2 polos 5.08 mm | Entrada 127 V y salida a los LED |

## Archivos (`fabricacion/`)

- `pcb/1_cobre_para_planchado_1a1.pdf`: se imprime al 100 %. El texto del cobre sale al revés en el papel, y así debe ser.
- `pcb/3_lado_componentes_1a1.pdf`, `pcb/4_plantilla_perforaciones_1a1.pdf`, `pcb/5_ensamble_componentes_con_valores.pdf`
- `esquema/FuenteOS_esquema.pdf`, `bom/BOM_KiCad.csv`, `gerber/`, `3d/`, `reportes/`: ERC y DRC sin errores, con paridad esquema-PCB.

## Armado y prueba

1. Mide la regla de 100 mm del PDF impreso antes de planchar.
2. Perfora con broca de 1.0 mm (0.8 mm para R2, 1.3 mm para las clemas). Suelda primero los diodos, respetando la **franja = K**.
3. Conecta J1 al **mismo cable de 127 V** que la placa Radox, en paralelo. No lo tomes del + o del − de la placa Radox.
4. Conecta J2 a la tira de la palabra OS: el + va al ánodo del primer LED y el − al cátodo del último.
5. Enchufa con las manos fuera. Si no enciende, desenchufa y revisa que ningún LED esté al revés.
