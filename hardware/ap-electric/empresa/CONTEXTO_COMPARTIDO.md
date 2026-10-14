# Contexto compartido del grupo AP Electric

Lo lee **cada agente** antes de trabajar. Es la fuente de verdad de las reglas y del mapa del repositorio.

## Reglas que no se rompen
1. **Idioma:** español. Claro y sin relleno.
2. **Estado real:** nada se ha fabricado, medido ni certificado. Jamás escribir «listo para vender», «certificado», «seguro» ni sellos (CE, UL, NOM, IFT) como logros. Hay un solo producto candidato para piloto: **AP Monitor 24 = 7R Tour 24DC rev B + firmware PackML/OEE + consola**.
3. **Marcas de origen:** `[V]` dato con fuente enlazada y fecha · `[CG]` conocimiento general sin verificar · `[H]` hipótesis por validar · `[R]` requisito o dato del repositorio · `[E]` hoja del componente · `[C]` cálculo · `[M]` medido (hoy ninguno) · `PD` por determinar.
4. **No inventar:** ni cifras, ni precios, ni capacidades nominales, ni códigos LCSC, ni normas, ni nombres de empresas. Si no hay fuente, se escribe «no encontrado» y se marca `[H]` o `PD`. Toda cifra externa lleva URL y fecha de consulta.
5. **Seguridad funcional:** ningún producto de AP es una función de seguridad (paro de emergencia, guardas, cortinas). Nunca proponer lo contrario.
6. **Red eléctrica:** nada de red de 127/220 V en el piloto; el SKU CA y AP Home están en pausa hasta tener pruebas de seguridad eléctrica con un organismo acreditado.
7. **Sin modelo ni autor de IA** en archivos del repositorio (ni comentarios, ni textos).
8. **Alcance de escritura:** cada agente escribe **solo** en su carpeta (`hardware/ap-electric/empresa/<area>/`) salvo que su encargo diga otra cosa. **No** modificar `kicad/`, `gen/`, `firmware/`, `fabricacion/` ni `web/` si no es el dueño del área y sin correr las pruebas. **No** hacer commit ni push: lo hace el coordinador.
9. **Verificar antes de decir «listo»:** `bash hardware/tools/verificar_todo.sh` debe dar «TODO BIEN» si se tocó código, placas o web.
10. **Asesoría:** lo legal, fiscal, aduanal y de certificación son **listas de verificación para consultar a un profesional**, no asesoría.

## Mapa del repositorio (rama `claude/led-sequential-controller-kicad-eb86y7`)
- `hardware/ap-electric/` documentos de la familia: `ARQUITECTURA.md`, `ANALISIS_ECOSISTEMA.md`, `ESTUDIO_MERCADO_INDUSTRIAL.md`, `DISENO_FINAL.md`, `PLAN_VERIFICACION.md`, `PUESTA_EN_MARCHA.md`, `PACKML.md`, `WEB_Y_PLACA.md`, `PREVENTA_AP_MONITOR.md`, `HOJA_DATOS_*.md`.
- `hardware/ap-electric/7r-tour/` placa industrial (KiCad en `kicad/`, generador `gen/make.py`, fabricación en `fabricacion/`). `home/` placa de hogar.
- `hardware/ap-electric/firmware/APControl/` firmware común; pruebas en `firmware/pruebas/`.
- `hardware/ap-electric/web/` página de la empresa (`index.html`), `consola.html`, pruebas en `web/pruebas/`.
- `hardware/ap-studio/` aplicación de la serie AP-1.
- `hardware/tools/` herramientas: `verificar_todo.sh`, `probar_apbus.sh`, `probar_web.sh`, `revisar_pedido.py`, `revisar_pines.py`, `ruta_auto.py`, `placa.py`, `jlcpcb.py`.
- Página publicada (privada): https://claude.ai/artifact/K6mTPerSpevi3ydEjX3Cus

## Cómo reportar
Cada informe termina con: **Hallazgos** (ordenados por gravedad) · **Qué falta saber** · **Siguiente paso recomendado** · **Fuentes**. Los hallazgos de diseño llevan: dónde está, por qué falla, cómo reproducirlo o comprobarlo y la corrección propuesta (sin aplicarla si no es tu área).
