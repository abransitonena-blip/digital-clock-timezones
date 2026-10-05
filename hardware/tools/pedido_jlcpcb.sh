#!/bin/bash
# Junta en hardware/PEDIDO_JLCPCB/ los archivos que se suben a JLCPCB (placa + ensamble) de cada placa,
# y un ZIP con todo. Antes: python3 tools/salidas.py <carpeta> <PROYECTO> de cada placa (en el contenedor de KiCad).
#   bash hardware/tools/pedido_jlcpcb.sh
set -e
H=$(cd "$(dirname "$0")/.." && pwd)
OUT=$H/PEDIDO_JLCPCB
rm -rf "$OUT"; mkdir -p "$OUT"
for par in "ap1-base:AP1_Base:1_BASE" "ap1-prog:AP1_Programador:2_PROGRAMADOR" "ap1-ind:AP1_Industrial:3_MODULO_INDUSTRIAL" "ap1-pix:AP1_Pixel:4_MODULO_PIXELES" \
           "ap02:AP02:5_AP02_placa_unica" "ap1-plantilla:AP1_Plantilla:6_PLANTILLA_modulos_nuevos" \
           "ap1-dmx:AP1_DMX:7_MODULO_DMX" \
           "ap1-in:AP_Input:8_AP_INPUT" "ap1-out:AP_Output:9_AP_OUTPUT"; do
  IFS=: read -r dir proj nombre <<< "$par"
  src=$H/$dir/fabricacion/jlcpcb
  dst=$OUT/$nombre
  mkdir -p "$dst/ensamble_completo" "$dst/ensamble_economico_solo_SMD"
  cp "$src/${proj}_gerber_JLCPCB.zip" "$dst/1_${proj}_GERBER.zip"
  cp "$src/${proj}_BOM_JLCPCB.csv" "$dst/ensamble_completo/2_${proj}_BOM.csv"
  cp "$src/${proj}_CPL_JLCPCB.csv" "$dst/ensamble_completo/3_${proj}_CPL.csv"
  cp "$src/${proj}_BOM_JLCPCB_solo_SMD.csv" "$dst/ensamble_economico_solo_SMD/2_${proj}_BOM_solo_SMD.csv"
  cp "$src/${proj}_CPL_JLCPCB_solo_SMD.csv" "$dst/ensamble_economico_solo_SMD/3_${proj}_CPL_solo_SMD.csv"
  cp "$src/RESUMEN_JLCPCB.txt" "$dst/RESUMEN_costo_montaje.txt"
  cp "$H/$dir/fabricacion/3d/render_superior.png" "$dst/vista_superior.png"
done
cp "$H/PEDIDO_JLCPCB.md" "$OUT/LEEME_COMO_PEDIR.md"
(cd "$H" && rm -f PEDIDO_JLCPCB.zip && zip -qr PEDIDO_JLCPCB.zip PEDIDO_JLCPCB)
echo "listo: $OUT y $H/PEDIDO_JLCPCB.zip"
