#!/bin/bash
# Compila el firmware del LetreroLab AP-0.2 (ESP32-C3) sin el IDE de Arduino.
# Solo descarga de github.com (arduino-cli, núcleo ESP32 3.1.1 y su compilador RISC-V).
#   bash hardware/tools/compilar_esp32.sh            -> deja los .bin en hardware/ap02/firmware/binarios
#   PUERTO=/dev/ttyACM0 bash hardware/tools/compilar_esp32.sh   -> además lo graba por USB-C
set -e
DIR=${ESP_DIR:-$HOME/.letrerolab-esp32}
REPO=$(cd "$(dirname "$0")/../.." && pwd)
SKETCH=$REPO/hardware/ap02/firmware/LetreroLabAP02
OUT=$REPO/hardware/ap02/firmware/binarios
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
pl['toolsDependencies'] = [t for t in pl['toolsDependencies'] if t['name'] in ('esp32-arduino-libs', 'esp-rv32', 'esptool_py')]
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
FQBN=esp32:esp32:esp32c3:CDCOnBoot=cdc,PartitionScheme=min_spiffs
./arduino-cli --config-file cli.yaml compile -b $FQBN --warnings all \
  --build-property runtime.tools.ctags.path="$DIR/ctags" --output-dir "$DIR/out" "$SKETCH"
mkdir -p "$OUT"
cp "$DIR/out/LetreroLabAP02.ino.merged.bin" "$OUT/LetreroLabAP02_completo_0x0.bin"
cp "$DIR/out/LetreroLabAP02.ino.bin" "$OUT/LetreroLabAP02_actualizacion_OTA.bin"
echo "Binarios en $OUT"
if [ -n "$PUERTO" ]; then
  ./arduino-cli --config-file cli.yaml upload -b $FQBN -p "$PUERTO" --input-dir "$DIR/out" "$SKETCH"
fi
