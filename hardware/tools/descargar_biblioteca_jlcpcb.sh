#!/bin/bash
# Descarga e instala la biblioteca JLCPCB-KiCad-Library (CDFER, licencia MIT) para KiCad 9:
# ~1500 piezas Basic/Preferred de JLCPCB con símbolo, huella, modelo 3D y su código LCSC ya puesto.
# Con ella, todo lo que se agregue a una placa sale en la BOM con código LCSC y sin cargo de montaje por tipo.
#
#   bash hardware/tools/descargar_biblioteca_jlcpcb.sh            -> instala en ~/.local/share/kicad/9.0/3rdparty
#   DESTINO=/otra/carpeta bash hardware/tools/descargar_biblioteca_jlcpcb.sh
#
# Además rehace hardware/tools/jlcpcb_catalogo.csv (lo usa tools/salidas.py para llenar la columna LCSC).
# No se guarda en el repositorio (pesa ~140 MB con los modelos 3D).
set -e
VERSION=${VERSION:-2025.07.18}
DESTINO=${DESTINO:-$HOME/.local/share/kicad/9.0/3rdparty/jlcpcb}
AQUI=$(cd "$(dirname "$0")" && pwd)
TMP=$(mktemp -d)
curl -sSfL -o "$TMP/jlc.zip" \
  "https://github.com/CDFER/JLCPCB-Kicad-Library/releases/download/$VERSION/JLCPCB-KiCad-Library-$VERSION.zip"
mkdir -p "$DESTINO"
unzip -qo "$TMP/jlc.zip" -d "$DESTINO"
rm -rf "$TMP"
python3 "$AQUI/jlcpcb.py" construir "$DESTINO/symbols"

cat <<EOF

Biblioteca instalada en: $DESTINO
En KiCad 9 (una sola vez):
  Preferencias > Administrar bibliotecas de símbolos > Global > "+" :
      nombre PCM_JLCPCB-<grupo>   ruta $DESTINO/symbols/JLCPCB-<grupo>.kicad_sym   (o use "Agregar existente" y elija todos)
  Preferencias > Administrar bibliotecas de huellas > Global > "+" :
      nombre PCM_JLCPCB           ruta $DESTINO/footprints/JLCPCB.pretty
  Preferencias > Configurar rutas: agregue  KICAD9_3RD_PARTY = $(dirname "$DESTINO")
O más fácil: Administrador de complementos (PCM) > buscar "JLCPCB" > Instalar (es el mismo paquete).

Para elegir piezas Extended (circuitos de potencia, ESP32, etc.) y pegar su código LCSC desde KiCad:
  Administrador de complementos > "JLCPCB Tools" (Bouni/kicad-jlcpcb-tools).
EOF
