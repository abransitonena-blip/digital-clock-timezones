#!/bin/bash
# Modelos 3D de cada placa en formatos para ver y compartir (además del STEP y los PNG de salidas.py):
#   GLB (glTF binario): se abre en el navegador, en Windows (Visor 3D), en Blender, en el celular y en realidad aumentada
#   (para CAD y gabinetes: el STEP de fabricacion/3d; para una maqueta impresa: kicad-cli pcb export stl)
# Uso (desde hardware/, con el contenedor "kc" de KiCad 9):  bash tools/renders.sh
set -e
cd "$(dirname "$0")/.."
for par in ap1-base:AP1_Base ap1-prog:AP1_Programador ap1-ind:AP1_Industrial ap1-pix:AP1_Pixel ap1-plantilla:AP1_Plantilla \
           ap1-dmx:AP1_DMX ap1-in:AP_Input ap1-out:AP_DO8 ap1-dist4:AP_Dist4 ap1-ai4:AP_AI4 ap1-node:AP_Node ap1-gate:AP_Gate ap1-pwm4:AP_PWM4 ap1-ao4:AP_AO4; do
  IFS=: read -r d p <<< "$par"
  docker exec -w /work/hardware/$d/kicad kc bash -c "
    kicad-cli pcb export glb --subst-models --include-silkscreen --include-soldermask -o ../fabricacion/3d/$p.glb $p.kicad_pcb >/dev/null 2>&1"
  echo "$d: $(du -h $d/fabricacion/3d/$p.glb | cut -f1) GLB"
done
