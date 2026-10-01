#!/bin/bash
# Ruteo completo de una placa LetreroLab hecha con tools/placa.py:
#   placa sin rutear -> Freerouting en 3 pasadas (1 hilo: reproducible) -> planos y serigrafía -> ERC/DRC
# Uso (desde hardware/):  bash tools/rutear.sh ap1-base AP1_Base
# Requiere el contenedor "kc" con KiCad 9 (/work = repositorio) y Java 21+ con freerouting.jar (FR=ruta).
set -e
cd "$(dirname "$0")/.."
DIR=$1; P=$2
FR=${FR:-/tmp/claude-0/fr/freerouting.jar}
JAVA=${JAVA:-$(ls /usr/lib/jvm/java-1.25*/bin/java 2>/dev/null | head -1)}
JAVA=${JAVA:-java}
K="docker exec -w /work/hardware/$DIR kc"
fr() { (cd "$DIR/kicad" && "$JAVA" -Dgui.enabled=false -jar "$FR" -de "$1" -do "$2" -mp 100 -mt 1 > "/tmp/fr_$2.log" 2>&1); }
$K python3 gen/make.py > /dev/null 2>&1
fr $P.dsn $P.ses
$K python3 gen/make.py --import 1 2>&1 | grep pasada
fr ${P}_2.dsn ${P}_2.ses
$K python3 gen/make.py --import 2 2>&1 | grep pasada
fr ${P}_3.dsn ${P}_3.ses
$K python3 gen/make.py --final 3 2>&1 | grep importado
rm -f $DIR/kicad/*.dsn $DIR/kicad/*.ses
$K bash -c "cd kicad && kicad-cli sch erc --severity-all -o /tmp/erc.rpt $P.kicad_sch | grep -i violations; \
  kicad-cli pcb drc --schematic-parity --severity-all -o /tmp/drc.rpt $P.kicad_pcb | grep -i found; \
  grep -A3 '^\[' /tmp/drc.rpt | grep -v 'Rule:\|Local' | head -40; grep -A3 '^\[' /tmp/erc.rpt | head -20"
