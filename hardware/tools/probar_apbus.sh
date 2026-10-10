#!/bin/bash
# Pruebas en la PC del protocolo AP BUS (apbus.h) y del maestro Modbus RTU (modbus.h) y de AP LIGHT (luz.h). Requiere g++.
set -e
cd "$(dirname "$0")/../ap1-prog/firmware/pruebas"
g++ -std=c++17 -Wall -Wextra -Werror -o /tmp/prueba_apbus prueba_apbus.cpp
/tmp/prueba_apbus
g++ -std=c++17 -Wall -Wextra -Werror -o /tmp/prueba_modbus prueba_modbus.cpp
/tmp/prueba_modbus
g++ -std=c++17 -Wall -Wextra -Werror -o /tmp/prueba_luz prueba_luz.cpp
/tmp/prueba_luz
