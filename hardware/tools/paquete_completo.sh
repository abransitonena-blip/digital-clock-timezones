#!/bin/bash
# Junta TODO el proyecto LetreroLab AP-1 (KiCad editable, generadores, programa, gabinete, documentos y
# archivos para JLCPCB) en hardware/LetreroLab_proyecto_completo.zip, para trabajarlo en una PC.
# Antes: bash hardware/tools/pedido_jlcpcb.sh
#   bash hardware/tools/paquete_completo.sh
set -e
H=$(cd "$(dirname "$0")/.." && pwd)
NOM=LetreroLab_proyecto_completo
T=$(mktemp -d); D=$T/$NOM; mkdir -p "$D"
cd "$H"
# placas del ecosistema (las de 127 V antiguas no van: la red no entra a ninguna placa nueva)
for d in ap1-base ap1-prog ap1-ind ap1-pix ap1-plantilla ap1-dmx ap1-in ap1-out ap1-dist4 ap1-gabinete ap1-ensamble ap02 tools PEDIDO_JLCPCB \
         fuente-os-127v/gen controlador-flechas-36v/gen; do
  mkdir -p "$D/$(dirname "$d")"
  cp -r "$d" "$D/$(dirname "$d")/"
done
find "$D" \( -name __pycache__ -o -name "*-backups" \) -prune -exec rm -rf {} +
find "$D" \( -name "*.kicad_prl" -o -name "*.dsn" -o -name "*.ses" -o -name "*.log" -o -name "*.pyc" \) -delete
cp AP_ELECTRIC.md ECOSISTEMA.md PEDIDO_JLCPCB.md HOJA_DE_RUTA.md LetreroLab_AP1.md "$D/"
cp LEEME_PC.md "$D/LEEME_PRIMERO.md"
rm -f "$H/$NOM.zip"
(cd "$T" && zip -qr "$H/$NOM.zip" "$NOM")
rm -rf "$T"
echo "listo: $H/$NOM.zip ($(du -h "$H/$NOM.zip" | cut -f1))"
