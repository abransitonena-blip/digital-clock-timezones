/* CH32V003: 16 KB de flash (la última página de 64 B guarda la configuración) y 2 KB de RAM. */
ENTRY(_start)
MEMORY {
  FLASH (rx)  : ORIGIN = 0x00000000, LENGTH = 16K - 64
  RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 2K
}
SECTIONS {
  .text : { KEEP(*(.init)) *(.text*) *(.rodata*) *(.srodata*) . = ALIGN(4); } > FLASH
  .data : {
    _datos_ini = .;
    __global_pointer$ = . + 0x800;
    *(.data*) *(.sdata*) . = ALIGN(4);
    _datos_fin = .;
  } > RAM AT > FLASH
  _datos_flash = LOADADDR(.data);
  .bss (NOLOAD) : { _bss_ini = .; *(.sbss*) *(.bss*) *(COMMON) . = ALIGN(4); _bss_fin = .; } > RAM
  _fin_pila = ORIGIN(RAM) + LENGTH(RAM);
  ASSERT(_fin_pila - _bss_fin >= 384, "queda poca RAM para la pila")
}
