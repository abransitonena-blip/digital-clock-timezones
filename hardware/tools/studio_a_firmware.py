"""Empaca la app AP Studio (ap-studio/index.html) comprimida dentro del programa: ap1-prog/firmware/LetreroLabAP1/studio.h
El equipo la sirve en http://<equipo>/studio (misma dirección que la API: el navegador no bloquea nada).
    python3 hardware/tools/studio_a_firmware.py"""
import gzip, os
H = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(H, "..", "ap-studio", "index.html")
dst = os.path.join(H, "..", "ap1-prog", "firmware", "LetreroLabAP1", "studio.h")
z = gzip.compress(open(src, "rb").read(), 9, mtime=0)
lin = [", ".join("0x%02x" % b for b in z[i:i + 20]) for i in range(0, len(z), 20)]
open(dst, "w").write("// Generado por tools/studio_a_firmware.py desde ap-studio/index.html: no editar a mano.\n#pragma once\n"
                     "const uint8_t STUDIO_GZ[] PROGMEM = {\n  " + ",\n  ".join(lin) + "\n};\nconst size_t STUDIO_LEN = %d;\n" % len(z))
print("studio.h: %d bytes comprimidos" % len(z))
