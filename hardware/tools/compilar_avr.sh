#!/bin/sh
# Compila un sketch .ino para ATmega328P (16 MHz) sin el IDE: usa avr-gcc y el núcleo Arduino de Debian/Ubuntu.
#   sudo apt install gcc-avr avr-libc arduino-core-avr
#   sh hardware/tools/compilar_avr.sh ruta/al/Sketch.ino      -> Sketch.hex y tamaño de memoria
set -e
INO=$(readlink -f "$1"); NAME=$(basename "$INO" .ino); OUT=${2:-/tmp/avrbuild_$NAME}
A=/usr/share/arduino/hardware/arduino/avr
mkdir -p "$OUT"
F="-mmcu=atmega328p -DF_CPU=16000000L -DARDUINO=10806 -DARDUINO_AVR_NANO -DARDUINO_ARCH_AVR -Os -w -ffunction-sections -fdata-sections"
INC="-I$A/cores/arduino -I$A/variants/standard -I$A/libraries/SoftwareSerial/src -I$A/libraries/EEPROM/src -I$A/libraries/Wire/src -I$A/libraries/Wire/src/utility"
{ echo '#include <Arduino.h>'; echo "#line 1 \"$INO\""; cat "$INO"; } > "$OUT/$NAME.cpp"
OBJS=""
LIBC=""; LIBCPP=""
grep -q "SoftwareSerial.h" "$INO" && LIBCPP="$LIBCPP $A/libraries/SoftwareSerial/src/*.cpp"
grep -q "Wire.h" "$INO" && { LIBC="$LIBC $A/libraries/Wire/src/utility/*.c"; LIBCPP="$LIBCPP $A/libraries/Wire/src/*.cpp"; }
rm -f "$OUT"/*.o
for f in $A/cores/arduino/*.c $LIBC; do
  o="$OUT/$(basename $f).o"; avr-gcc $F $INC -c "$f" -o "$o"; OBJS="$OBJS $o"; done
for f in $A/cores/arduino/*.cpp $LIBCPP "$OUT/$NAME.cpp"; do
  o="$OUT/$(basename $f).o"; avr-g++ $F -fno-exceptions -fno-threadsafe-statics -std=gnu++11 $INC -c "$f" -o "$o"; OBJS="$OBJS $o"; done
for f in $A/cores/arduino/*.S; do o="$OUT/$(basename $f).o"; avr-gcc $F -x assembler-with-cpp $INC -c "$f" -o "$o"; OBJS="$OBJS $o"; done
avr-gcc -mmcu=atmega328p -Os -Wl,--gc-sections $OBJS -o "$OUT/$NAME.elf" -lm
avr-objcopy -O ihex -R .eeprom "$OUT/$NAME.elf" "$OUT/$NAME.hex"
avr-size -C --mcu=atmega328p "$OUT/$NAME.elf" | grep -E "Program|Data"
echo "HEX: $OUT/$NAME.hex"
