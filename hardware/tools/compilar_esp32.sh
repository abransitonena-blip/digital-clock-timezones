#!/bin/bash
# Compila el firmware del LetreroLab AP-0.2 o del programador AP-1 (ESP32-C3) sin el IDE de Arduino.
# Solo descarga de github.com (arduino-cli, núcleo ESP32 3.1.1 y su compilador RISC-V).
#   bash hardware/tools/compilar_esp32.sh            -> deja los .bin en hardware/ap02/firmware/binarios
#   PUERTO=/dev/ttyACM0 bash hardware/tools/compilar_esp32.sh   -> además lo graba por USB-C
set -e
DIR=${ESP_DIR:-$HOME/.letrerolab-esp32}
REPO=$(cd "$(dirname "$0")/../.." && pwd)
# Programa: ap02 (por omisión) o ap1:   bash hardware/tools/compilar_esp32.sh ap1
case "${1:-ap02}" in
  apcontrol) SKETCH=$REPO/hardware/ap-electric/firmware/APControl; OUT=$REPO/hardware/ap-electric/firmware/binarios; NOMBRE=APControl ;;
  aprack) SKETCH=$REPO/hardware/ap-electric/firmware/APRack; OUT=$REPO/hardware/ap-electric/firmware/binarios; NOMBRE=APRack ;;
  # AP PLC C24 rev B (ESP32-S3-WROOM-1 N8): el mismo programa APRack compilado para el ESP32-S3; baja además el compilador Xtensa
  aprack_s3) SKETCH=$REPO/hardware/ap-electric/firmware/APRack; OUT=$REPO/hardware/ap-electric/firmware/binarios; NOMBRE=APRack; CHIP=s3; SALIDA=APPLC_C24B ;;
  ap1) SKETCH=$REPO/hardware/ap1-prog/firmware/LetreroLabAP1; OUT=$REPO/hardware/ap1-prog/firmware/binarios; NOMBRE=LetreroLabAP1 ;;
  *)   SKETCH=$REPO/hardware/ap02/firmware/LetreroLabAP02; OUT=$REPO/hardware/ap02/firmware/binarios; NOMBRE=LetreroLabAP02 ;;
esac
CHIP=${CHIP:-c3}; export CHIP
[ "$CHIP" = s3 ] && DIR=${ESP_DIR_S3:-$HOME/.letrerolab-esp32-s3}
mkdir -p "$DIR" && cd "$DIR"
if [ ! -x arduino-cli ]; then
  curl -sSfL -o acli.tgz https://github.com/arduino/arduino-cli/releases/download/v1.1.1/arduino-cli_1.1.1_Linux_64bit.tar.gz
  tar xzf acli.tgz arduino-cli
fi
if [ ! -f package_esp32local_index.json ]; then
  # índice reducido: solo lo necesario para el ESP32-C3 (todo alojado en github.com)
  curl -sSfL -o idx.json https://github.com/espressif/arduino-esp32/releases/download/3.1.1/package_esp32_index.json
  python3 - <<'EOF'
import json
d = json.load(open('idx.json')); p = d['packages'][0]
pl = [x for x in p['platforms'] if x['version'] == '3.1.1'][0]
pl['toolsDependencies'] = [t for t in pl['toolsDependencies'] if t['name'] in (('esp32-arduino-libs', 'esp-x32', 'esptool_py') if __import__('os').environ.get('CHIP') == 's3' else ('esp32-arduino-libs', 'esp-rv32', 'esptool_py'))]
p['platforms'] = [pl]
v = {(t['name'], t['version']) for t in pl['toolsDependencies']}
p['tools'] = [t for t in p['tools'] if (t['name'], t['version']) in v]
json.dump(d, open('package_esp32local_index.json', 'w'))
EOF
fi
cat > cli.yaml <<EOF
board_manager:
  additional_urls: [file://$DIR/package_esp32local_index.json]
directories: {data: $DIR/data, downloads: $DIR/dl, user: $DIR/user}
EOF
# arduino-cli genera prototipos con ctags (se baja de downloads.arduino.cc); el programa ya los declara, así que basta uno vacío
mkdir -p ctags && printf '#!/bin/sh\nexit 0\n' > ctags/ctags && chmod +x ctags/ctags
./arduino-cli --config-file cli.yaml core update-index >/dev/null 2>&1 || true
./arduino-cli --config-file cli.yaml core list | grep -q "esp32:esp32" || ./arduino-cli --config-file cli.yaml core install esp32:esp32@3.1.1
if [ "$CHIP" = s3 ]; then FQBN=esp32:esp32:esp32s3:CDCOnBoot=cdc,FlashSize=8M,PartitionScheme=default_8MB; else FQBN=esp32:esp32:esp32c3:CDCOnBoot=cdc,PartitionScheme=min_spiffs; fi
./arduino-cli --config-file cli.yaml compile -b $FQBN --warnings all \
  --build-property runtime.tools.ctags.path="$DIR/ctags" --output-dir "$DIR/out" "$SKETCH"
mkdir -p "$OUT"
SALIDA=${SALIDA:-$NOMBRE}
cp "$DIR/out/$NOMBRE.ino.merged.bin" "$OUT/${SALIDA}_completo_0x0.bin"
cp "$DIR/out/$NOMBRE.ino.bin" "$OUT/${SALIDA}_actualizacion_OTA.bin"
echo "Binarios en $OUT"
if [ -n "$PUERTO" ]; then
  ./arduino-cli --config-file cli.yaml upload -b $FQBN -p "$PUERTO" --input-dir "$DIR/out" "$SKETCH"
fi
