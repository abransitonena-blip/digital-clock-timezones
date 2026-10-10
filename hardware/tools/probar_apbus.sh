#!/bin/bash
# Prueba en la PC del protocolo AP BUS del programa (apbus.h). Requiere g++.
set -e
cd "$(dirname "$0")/../ap1-prog/firmware/pruebas"
g++ -std=c++17 -Wall -Wextra -Werror -o /tmp/prueba_apbus prueba_apbus.cpp
/tmp/prueba_apbus
