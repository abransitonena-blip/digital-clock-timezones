#!/bin/bash
# Pruebas en la PC del protocolo AP BUS (apbus.h), del maestro Modbus RTU (modbus.h), de AP LIGHT (luz.h)
# y del programa tipo PLC AP LÓGICA (logica.h). Requiere g++.
set -e
cd "$(dirname "$0")/../ap1-prog/firmware/pruebas"
g++ -std=c++17 -Wall -Wextra -Werror -o /tmp/prueba_apbus prueba_apbus.cpp
/tmp/prueba_apbus
g++ -std=c++17 -Wall -Wextra -Werror -o /tmp/prueba_modbus prueba_modbus.cpp
/tmp/prueba_modbus
g++ -std=c++17 -Wall -Wextra -Werror -o /tmp/prueba_luz prueba_luz.cpp
/tmp/prueba_luz
g++ -std=c++17 -Wall -Wextra -Werror -o /tmp/prueba_logica prueba_logica.cpp
/tmp/prueba_logica
node ../../../ap-studio/pruebas/prueba_logica.cjs      # el mismo motor en AP Studio (JS)
cd ../../../ap-electric/firmware/pruebas
g++ -std=c++17 -Wall -Wextra -Werror -o /tmp/prueba_control prueba_control.cpp
/tmp/prueba_control
g++ -std=c++17 -Wall -Wextra -Werror -o /tmp/prueba_packml prueba_packml.cpp
/tmp/prueba_packml
# JSON del equipo (API 2): se extrae del programa real y se valida
python3 - <<'PY'
import re
src = open("../APControl/APControl.ino", encoding="utf-8").read()
i = src.index("const char* NOMBRE_FALLA[]"); j = src.index("\n}\n", src.index("String estadoJSON() {")) + 3
open("/tmp/estado_json.inc", "w", encoding="utf-8").write(src[i:j])
PY
g++ -std=c++17 -Wall -Wextra -Werror -o /tmp/prueba_json prueba_json.cpp
/tmp/prueba_json
python3 probar_json.py
cmp ../APControl/logica.h ../../../ap1-prog/firmware/LetreroLabAP1/logica.h && echo "logica.h: la copia de AP Control es la misma"
