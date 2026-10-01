#!/bin/bash
# Ruteo completo de la AP-0.2: genera placa -> Freerouting en 3 pasadas -> rellena planos -> ERC/DRC.
# Uso (desde hardware/ap02):  bash gen/rutear.sh
# Requiere: contenedor "kc" con KiCad 9 (/work = repositorio) y Java 21+ con freerouting.jar (FR=ruta del .jar).
set -e
cd "$(dirname "$0")/.."
FR=${FR:-/tmp/claude-0/fr/freerouting.jar}
JAVA=${JAVA:-$(ls /usr/lib/jvm/java-1.25*/bin/java 2>/dev/null | head -1)}
JAVA=${JAVA:-java}
K="docker exec -w /work/hardware/ap02 kc"
fr() { (cd kicad && "$JAVA" -Dgui.enabled=false -jar "$FR" -de "$1" -do "$2" -mp 100 -mt 1 > "/tmp/fr_$2.log" 2>&1); }
$K python3 gen/make.py > /dev/null 2>&1                      # placa, esquema y AP02.dsn
fr AP02.dsn AP02.ses
$K python3 gen/make.py --import 1 2>&1 | grep pasada
fr AP02_2.dsn AP02_2.ses
$K python3 gen/make.py --import 2 2>&1 | grep pasada
fr AP02_3.dsn AP02_3.ses
$K python3 gen/make.py --final 3 2>&1 | grep importado
$K bash -c "cd kicad && kicad-cli sch erc --severity-all -o /tmp/erc.rpt AP02.kicad_sch | grep -i violations; \
  kicad-cli pcb drc --schematic-parity --severity-all -o /tmp/drc.rpt AP02.kicad_pcb | grep -i found; \
  grep -A3 '^\[' /tmp/drc.rpt | head -40"
