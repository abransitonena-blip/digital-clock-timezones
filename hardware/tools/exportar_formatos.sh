#!/bin/bash
# Exporta los modelos 3D a otros formatos en ap-electric/formatos/: STEP de las placas (KiCad, contenedor kc en marcha) y 3MF/OBJ/FBX/.blend (Blender: pip install bpy==4.2.0 trimesh).
# Uso (desde hardware/):  bash tools/exportar_formatos.sh
set -e
cd "$(dirname "$0")/.."
mkdir -p ap-electric/formatos/step
for d in rack16:AP_RACK16 in16:AP_IN16 ai8:AP_AI8 led8:AP_LED8 rl4:AP_RL4 ao4:AP_RACKAO4; do
  dd=${d%%:*}; p=${d##*:}
  docker exec -w /work/hardware/ap-electric/$dd/kicad kc kicad-cli pcb export step --subst-models -f -o /work/hardware/ap-electric/formatos/step/$p.step $p.kicad_pcb | tail -1
done
${PYTHON:-python3} ap-electric/formatos/exportar_formatos.py     # PYTHON=ruta/al/python con bpy si el python del sistema no lo tiene
