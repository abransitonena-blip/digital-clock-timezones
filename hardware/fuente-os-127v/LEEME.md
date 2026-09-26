# Fuente capacitiva para la palabra "OS" (O 13 + S 14 = 27 LED ámbar/amarillos), 127 VCA

Placa de **50 × 50 mm**, una cara y con componentes de patas (THT), hecha para transferencia de tóner. Es el mismo principio que la placa Radox: **no aislada**.

> **PELIGRO:** con la placa enchufada, todo el circuito (placa, cables y LED) queda a voltaje de red. Desenchufa, espera 10 s y
> solo entonces toca. Monta la placa dentro de la caja del letrero, sin partes metálicas accesibles.

## Circuito

```
L ─┬─ C1 334J 400V ─ R1 220Ω 1W fusible ─ ~ 2W10 ─► + ── 27 LED en serie ── − ◄─ 2W10
   └─ R2 1M ─┘                                  N ── ~ 2W10
```

## Cálculo

Fórmula de corriente: `I = 4·f·C·(Vpico − Vtira)`.

**LED ámbar o amarillo (2 V):** la tira suma 27 × 2 = 54 V, así que va C1 = **334J**.

| Caso | Corriente |
|---|---|
| Nominal (127 V) | 240 × 0.33 µF × 126 = **10 mA** |
| Red baja y Vf alto | 8.1 mA |
| Red alta y Vf bajo | 11.6 mA |

**LED blanco cálido (3 V):** la tira suma 81 V, así que va C1 = **474J**, con unos 11 mA.

## Materiales

| Ref | Valor | Nota |
|---|---|---|
| C1 | **334J 400 V** poliéster | El footprint acepta paso 10 o 15 mm. 474J si los LED son blanco cálido |
| R1 | 220 Ω 1 W **fusible** (flameproof) | Limita el pico al enchufar y actúa como fusible |
| R2 | 1 MΩ ½ W | Descarga C1 |
| BR1 | **2W10** (o W10M/W06M) | El + del cuerpo va al pad cuadrado |
| J1, J2 | Clema 2 polos 5.08 mm | Entrada 127 V y salida a los LED |

## Archivos (`fabricacion/`)

- `pcb/1_cobre_para_planchado_1a1.pdf`: se imprime al 100 %. El texto del cobre sale al revés en el papel, y así debe ser.
- `pcb/3_lado_componentes_1a1.pdf`, `pcb/4_plantilla_perforaciones_1a1.pdf`, `pcb/5_ensamble_componentes_con_valores.pdf`
- `esquema/FuenteOS_esquema.pdf`, `bom/BOM_KiCad.csv`, `gerber/`, `3d/`, `reportes/`: ERC y DRC sin errores, con paridad esquema-PCB.

## Armado y prueba

1. Mide la regla de 100 mm del PDF impreso antes de planchar.
2. Perfora con broca de 1.0 mm (0.8 mm para R2, 1.3 mm para las clemas). Orienta el 2W10 con su **+** en el pad cuadrado.
3. Conecta J1 al **mismo cable de 127 V** que la placa Radox, en paralelo. No lo tomes del + o del − de la placa Radox.
4. Conecta J2 a la tira O + S: el + va al ánodo del primer LED y el − al cátodo del último.
5. Enchufa con las manos fuera. Si no enciende, desenchufa y revisa que ningún LED esté al revés.
