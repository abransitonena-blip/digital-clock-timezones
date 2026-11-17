#!/bin/bash
# AP Model 3D Foto - mantener activa la pagina desde tu Mac
#
# Que hace:
#   1. Impide que la Mac se duerma (caffeinate): la pestana de Colab/Kaggle
#      sigue conectada y la sesion no se corta por la Mac dormida.
#   2. Si le das la direccion de tu pagina, la visita cada minuto para que el
#      tunel no se quede inactivo y te avisa si deja de responder.
#
# Uso:
#   - Doble clic en este archivo (la 1a vez: clic derecho > Abrir), o en Terminal:
#       bash mantener_activo_mac.command https://tu-pagina.trycloudflare.com
#   - Para APAGAR: cierra esta ventana de Terminal o pulsa Ctrl+C.
#
# Importante: deja abierta la pestana de Colab/Kaggle en el navegador. Colab
# corta igual una sesion a las 24 h como maximo. Para una pagina siempre
# encendida sin tu Mac usa Modal (carpeta modal/ del repositorio).

URL="${1:-}"
if [ -z "$URL" ]; then
  read -r -p "Direccion de tu pagina (Enter para solo evitar que la Mac se duerma): " URL
fi

caffeinate -dimsu &
CAF=$!
trap 'kill $CAF 2>/dev/null; echo; echo "Apagado: la Mac ya puede dormir."; exit 0' INT TERM EXIT

echo "Activo desde $(date '+%H:%M'). La Mac no se dormira mientras esta ventana siga abierta."
echo "Para apagar: Ctrl+C o cierra la ventana."
fallas=0
while true; do
  if [ -n "$URL" ]; then
    code=$(curl -s -o /dev/null -m 20 -w "%{http_code}" "$URL/config")
    if [ "$code" = "200" ] || [ "$code" = "401" ] || [ "$code" = "403" ]; then
      [ $fallas -gt 0 ] && echo "$(date '+%H:%M') la pagina volvio a responder"
      fallas=0
    else
      fallas=$((fallas + 1))
      echo "$(date '+%H:%M') la pagina no responde (codigo $code)"
      if [ $fallas -eq 3 ]; then
        osascript -e 'display notification "La pagina dejo de responder: revisa la pestana de Colab/Kaggle" with title "AP Model 3D Foto"' 2>/dev/null
      fi
    fi
  fi
  sleep 60
done
