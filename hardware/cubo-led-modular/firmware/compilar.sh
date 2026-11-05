#!/bin/bash
# Compila el firmware del Cubo AP con arduino-cli (sin IDE). Todo se descarga de github.com:
# arduino-cli 1.1.1, núcleo ESP32 3.1.1 (solo herramientas del C3) y librerías con versión fija.
#   bash compilar.sh                         -> binarios en ./binarios (placa v2 y v1)
#   PUERTO=/dev/ttyACM0 bash compilar.sh     -> además graba por USB-C
set -e
AQUI=$(cd "$(dirname "$0")" && pwd)
D=${ESP_DIR:-$HOME/.cuboap-esp32}
mkdir -p "$D" && cd "$D"
[ -x arduino-cli ] || { curl -sSfL -o acli.tgz https://github.com/arduino/arduino-cli/releases/download/v1.1.1/arduino-cli_1.1.1_Linux_64bit.tar.gz; tar xzf acli.tgz arduino-cli; }
if [ ! -f package_esp32local_index.json ]; then
  curl -sSfL -o idx.json https://github.com/espressif/arduino-esp32/releases/download/3.1.1/package_esp32_index.json
  python3 - <<'PY'
import json
d = json.load(open('idx.json')); p = d['packages'][0]
pl = [x for x in p['platforms'] if x['version'] == '3.1.1'][0]
pl['toolsDependencies'] = [t for t in pl['toolsDependencies'] if t['name'] in ('esp32-arduino-libs', 'esp-rv32', 'esptool_py')]
p['platforms'] = [pl]; v = {(t['name'], t['version']) for t in pl['toolsDependencies']}
p['tools'] = [t for t in p['tools'] if (t['name'], t['version']) in v]
json.dump(d, open('package_esp32local_index.json', 'w'))
PY
fi
printf 'board_manager:\n  additional_urls: [file://%s/package_esp32local_index.json]\ndirectories: {data: %s/data, downloads: %s/dl, user: %s/user}\n' "$D" "$D" "$D" "$D" > cli.yaml
mkdir -p ctags && printf '#!/bin/sh\nexit 0\n' > ctags/ctags && chmod +x ctags/ctags
./arduino-cli --config-file cli.yaml core list | grep -q "esp32:esp32" || ./arduino-cli --config-file cli.yaml core install esp32:esp32@3.1.1
mkdir -p user/libraries && cd user/libraries
[ -d NimBLE-Arduino ] || git clone -q --depth 1 -b 2.5.2 https://github.com/h2zero/NimBLE-Arduino.git
[ -d Adafruit_NeoPixel ] || git clone -q --depth 1 -b 1.12.3 https://github.com/adafruit/Adafruit_NeoPixel.git
[ -d Espalexa ] || git clone -q --depth 1 -b v2.7.0 https://github.com/Aircoookie/Espalexa.git
cd "$D"
python3 "$AQUI/gen_pagina.py"
rm -rf CuboAP && mkdir CuboAP && cp "$AQUI"/src/*.cpp "$AQUI"/src/*.h CuboAP/ && echo '// programa en main.cpp y nucleo.cpp' > CuboAP/CuboAP.ino
FQBN=esp32:esp32:esp32c3:CDCOnBoot=cdc,PartitionScheme=min_spiffs
mkdir -p "$AQUI/binarios"
for P in 2 1; do
  ./arduino-cli --config-file cli.yaml compile -b $FQBN --build-property runtime.tools.ctags.path="$D/ctags" \
    --build-property "compiler.cpp.extra_flags=-DCUBO_PLACA=$P" --output-dir "$D/out$P" CuboAP
  cp "out$P/CuboAP.ino.merged.bin" "$AQUI/binarios/CuboAP_placa_v${P}_completo_0x0.bin"
  cp "out$P/CuboAP.ino.bin" "$AQUI/binarios/CuboAP_placa_v${P}_OTA.bin"
done
echo "Binarios en $AQUI/binarios"
[ -z "$PUERTO" ] || ./arduino-cli --config-file cli.yaml upload -b $FQBN -p "$PUERTO" --input-dir out${PLACA:-2} CuboAP
