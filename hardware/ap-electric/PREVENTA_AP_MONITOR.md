# AP Monitor 24: ficha del programa piloto

> **Prototipo de ingeniería en validación.** Todavía no hay placas fabricadas ni medidas. Sin certificación. **No es una función de seguridad.** Sin fecha ni precio comprometidos. Esta ficha explica qué se ofrece y qué no, para que cualquiera decida con la información completa. Análisis completo: [ANALISIS_ECOSISTEMA.md](ANALISIS_ECOSISTEMA.md).

## Qué es
Una caja de riel DIN de 24 V CC que se conecta a una máquina que hoy no entrega datos y le agrega:
- **Estado de la máquina** con el modelo PackML (detenida, lista, en producción, retenida, abortada).
- **Conteo** de piezas buenas y defectuosas, desde un sensor o un botón.
- **Causa de paro**, microparos y llamado de andon.
- **OEE** (disponibilidad × desempeño × calidad) y hora de cada evento.
- Tablero local en **AP Studio** (pestaña Producción) y lectura por **Modbus RTU** (RS-485 aislado) o Wi-Fi. **Sin nube.**

## Qué lleva el hardware (diseño, sin medir)
- 7 salidas de relé (torre de luz, andon, habilitación de proceso).
- 8 entradas de 24 V **PNP**.
- RS-485 aislado, Wi-Fi, reloj con batería externa, puntos de prueba.
- Alimentación: 24 V CC de una **fuente certificada de terceros** (no incluida).

## Qué NO es
- No es un dispositivo de seguridad: no sustituye paro de emergencia, guardas ni relé de seguridad.
- No está certificado (NOM, UL, CE) ni tiene el radio homologado.
- No funciona con sensores **NPN** directos en esta revisión.
- No tiene Ethernet.
- No tiene mediciones de EMC, temperatura, vida de relés ni capacidad de contactos (por determinar por ensayo).

## Cómo participar
1. **Hoy:** registrar interés en la página (no se cobra nada y no hay compromiso).
2. **Cuando haya placas probadas:** kits piloto a costo para 5 a 10 clientes, con instalación acompañada, aviso de prototipo y contrato corto.
3. **Después del piloto:** preventa con pago, solo con fecha, garantía y devolución por escrito.

## Qué le pedimos a un piloto
- Una máquina real y una persona de mantenimiento o producción para acompañar 30 días.
- Decirnos qué sensores tiene (PNP, NPN, contacto seco, torre de luz).
- Retroalimentación honesta: qué falta, qué sobra, cuánto pagaría.

## Preguntas frecuentes
**¿Puedo pagar ya?** No. Hasta que exista una unidad funcional y términos revisados, no se cobra.
**¿Cuánto costará?** No hay precio publicado. La referencia que se prueba es de $5,000 a $7,000 MXN por máquina, pago único; se confirma con clientes y con el costo real.
**¿Sirve con mi sensor NPN?** No directo. Es la primera mejora prevista de la siguiente revisión.
**¿Se conecta a la nube?** No es necesaria. Los datos quedan en la planta.
**¿Puedo usarlo para proteger al operador?** No. Para eso hay equipos de seguridad certificados.
