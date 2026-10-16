#!/bin/bash
# Todas las comprobaciones por software de la familia AP Electric, en una sola orden.
# No sustituye ensayos físicos (ver ap-electric/PLAN_VERIFICACION.md). Requiere g++, Python 3, Node y Playwright.
set -e
cd "$(dirname "$0")/.."
echo "== Pruebas del programa (núcleo, PackML, Modbus, PLC, JSON del equipo) =="; bash tools/probar_apbus.sh
echo "== Pines del ESP32-C3: placa contra programa =="; python3 tools/revisar_pines.py
echo "== Pedido a JLCPCB: 7R Tour 24DC y CA, AP Home =="
python3 tools/revisar_pedido.py ap-electric/7r-tour AP_7R_TOUR 24DC | grep -E "RESULTADO|ERROR"
python3 tools/revisar_pedido.py ap-electric/7r-tour AP_7R_TOUR CA | grep -E "RESULTADO|ERROR"
python3 tools/revisar_pedido.py ap-electric/home AP_HOME | grep -E "RESULTADO|ERROR"
[ -d ap-electric/rack16/fabricacion/jlcpcb ] && python3 tools/revisar_pedido.py ap-electric/rack16 AP_RACK16 | grep -E "RESULTADO|ERROR"
echo "== Complementos 3D (sólidos y medidas) =="; (cd ap-electric/accesorios && python3 validar.py)
echo "== Consola y web en navegador =="; bash tools/probar_web.sh
echo "TODO BIEN (por software)"
