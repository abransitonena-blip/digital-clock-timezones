/* Nodo AP · arranque mínimo del CH32V003 (QingKe V2A, RV32EC), sin SDK.
 * Tabla de vectores en 0x0: la entrada 0 es la instrucción de arranque; las demás son direcciones
 * absolutas de rutinas (mtvec en modo 3). Solo se usa la interrupción 32 (USART1). */
    .section .init, "ax"
    .global _start
    .option norvc
_start:
    j reset
    .rept 31
    .word irq_sin_uso
    .endr
    .word USART1_IRQHandler                 /* 32: USART1 */
    .rept 6
    .word irq_sin_uso
    .endr
    .option rvc

    .text
reset:
    .option push
    .option norelax
    la gp, __global_pointer$
    .option pop
    la sp, _fin_pila
    li a0, 0x1880                           /* MPP = máquina; interrupciones apagadas hasta main */
    csrw mstatus, a0
    la a0, _start
    ori a0, a0, 3                           /* vectores con direcciones absolutas */
    csrw mtvec, a0
    la a0, _datos_flash                     /* copiar .data de flash a RAM */
    la a1, _datos_ini
    la a2, _datos_fin
1:  bgeu a1, a2, 2f
    lw a3, 0(a0)
    sw a3, 0(a1)
    addi a0, a0, 4
    addi a1, a1, 4
    j 1b
2:  la a1, _bss_ini                         /* poner .bss en cero */
    la a2, _bss_fin
3:  bgeu a1, a2, 4f
    sw zero, 0(a1)
    addi a1, a1, 4
    j 3b
4:  call main
5:  j 5b

irq_sin_uso:
    mret
