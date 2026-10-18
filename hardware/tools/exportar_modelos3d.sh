#!/bin/bash
# Exporta las placas AP Rack a GLB (con colores) para el visor 3D de la web y para abrir en cualquier visor de glTF.
# Requiere el contenedor de KiCad (kc) en marcha. Uso (desde hardware/):  bash tools/exportar_modelos3d.sh
set -e
cd "$(dirname "$0")/.."
D=ap-electric/web/modelos3d; mkdir -p $D
for d in rack16:AP_RACK16 in16:AP_IN16 ai8:AP_AI8 led8:AP_LED8 rl4:AP_RL4 ao4:AP_RACKAO4 plc:AP_PLC_C24; do
  dd=${d%%:*}; p=${d##*:}
  docker exec -w /work/hardware/ap-electric/$dd/kicad kc kicad-cli pcb export glb -f -o /work/hardware/$D/$p.glb $p.kicad_pcb | tail -1
done
python3 tools/colorear_glb.py $D/AP_RACK16.glb $D/AP_IN16.glb $D/AP_AI8.glb $D/AP_LED8.glb $D/AP_RL4.glb $D/AP_RACKAO4.glb $D/AP_PLC_C24.glb
