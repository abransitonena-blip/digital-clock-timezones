"""Convierte ../app/index.html en src/pagina.h para que el cubo sirva su propia página por Wi-Fi."""
import os
aqui = os.path.dirname(os.path.abspath(__file__))
html = open(os.path.join(aqui, "..", "app", "index.html"), encoding="utf-8").read()
assert ")PAGINA\"" not in html
open(os.path.join(aqui, "src", "pagina.h"), "w", encoding="utf-8").write(
    "// Generado por gen_pagina.py desde app/index.html. No editar a mano.\n#pragma once\n#include <pgmspace.h>\n"
    f"static const char PAGINA_HTML[] PROGMEM = R\"PAGINA({html})PAGINA\";\n")
print("pagina.h:", len(html.encode()), "bytes")
