# Simulación de la salida 0-10 V del AO4 (ngspice)

`salida_0_10V.cir` simula un canal:
- filtro;
- LM324 como modelo de comportamiento: ganancia 1e5, GBW 1 MHz, salida de 0 a 22.5 V;
- seguidor PNP (modelo del 2N3906, como el MMBT5401);
- pull-up de 22k;
- 47 Ω dentro del lazo y compensación de 100 nF.

La carga son drivers 1-10 V que **inyectan** de 0 a 10 mA, más la capacitancia del cable.

```
ngspice -b salida_0_10V.cir        (KiCad 9 trae ngspice)
```

| Carga de drivers | Consigna 50 % | Consigna 10 % (0.99 V ideal) |
|---|---|---|
| 0 mA | 4.950 V | 0.990 V |
| 1 mA | 4.950 V | 0.990 V |
| 5 mA | 4.950 V | 1.044 V |
| 10 mA | 4.950 V | 1.330 V |

- Con 10 nF de cable (unos 100 m) no hay sobretiro.
- Con 1 µF (caso extremo) hay un sobretiro breve sin carga.
- El mínimo con carga alta lo fija la caída base-emisor del PNP (~0.65 V) más 47 Ω × la corriente. Para drivers 1-10 V el mínimo de atenuación es 1 V, así que se aprovecha todo el rango.
