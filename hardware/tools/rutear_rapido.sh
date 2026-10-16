#!/bin/bash
# Ruteo de una pasada (sirve cuando las pasadas de refinamiento de rutear.sh no mejoran): placa sin rutear -> Freerouting -> planos y serigrafía -> ERC/DRC.
# Uso (desde hardware/):  bash tools/rutear_rapido.sh ap-electric/in16 AP_IN16
set -e
cd "$(dirname "$0")/.."
DIR=$1; P=$2
FR=${FR:-/tmp/claude-0/fr/freerouting.jar}
JAVA=${JAVA:-$(ls /usr/lib/jvm/java-1.25*/bin/java 2>/dev/null | head -1)}
JAVA=${JAVA:-java}
K="docker exec -w /work/hardware/$DIR kc"
$K python3 gen/make.py > /dev/null 2>&1
(cd "$DIR/kicad" && "$JAVA" -Dgui.enabled=false -jar "$FR" -de $P.dsn -do $P.ses -mp 100 -mt 1 > "/tmp/fr_$P.log" 2>&1)
$K python3 gen/make.py --import 1 2>&1 | grep pasada
$K python3 gen/make.py --final 1 2>&1 | grep importado
rm -f $DIR/kicad/*.dsn $DIR/kicad/*.ses
$K bash -c "cd kicad && kicad-cli sch erc --severity-all -o /tmp/erc_$P.rpt $P.kicad_sch | grep -i violations; kicad-cli pcb drc --schematic-parity --severity-all -o /tmp/drc_$P.rpt $P.kicad_pcb | grep -i found; grep -A3 '^\[' /tmp/drc_$P.rpt | grep -v 'Rule:\|Local' | head -30; grep -A3 '^\[' /tmp/erc_$P.rpt | head -12"
