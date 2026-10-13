#!/bin/bash
# Pruebas en navegador de la consola AP Base y de la web de la empresa. Requiere Node y Playwright (npm i -g playwright).
set -e
cd "$(dirname "$0")/../ap-electric/web/pruebas"
NODE_PATH="$(npm root -g)" node prueba_web.cjs
