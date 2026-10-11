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
