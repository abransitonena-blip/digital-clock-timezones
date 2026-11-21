#!/bin/sh
# Compila el firmware del nodo para el CH32V003 (gcc-riscv64-unknown-elf) y corre las pruebas del núcleo en la PC.
# Graba con WCH-LinkE por SWIO:  minichlink -w nodo.bin flash -b   (o WCH-LinkUtility)
set -e
cd "$(dirname "$0")"
cc -std=c11 -Wall -Wextra -Werror -o /tmp/test_nodo_$$ test_nodo.c nodo.c -lm && /tmp/test_nodo_$$ && rm -f /tmp/test_nodo_$$
P=riscv64-unknown-elf
$P-gcc -march=rv32ec_zicsr -mabi=ilp32e -Os -ffunction-sections -fdata-sections -fno-builtin \
  -Wall -Wextra -Werror -nostartfiles -nostdlib -static -T enlace.ld -Wl,--gc-sections -Wl,-Map=nodo.map \
  arranque.S hal_ch32v003.c nodo.c -lgcc -o nodo.elf
$P-objcopy -O binary nodo.elf nodo.bin
$P-size nodo.elf
