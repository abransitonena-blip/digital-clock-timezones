/* Pruebas del núcleo del nodo en la PC:  cc -Wall -Wextra -fsanitize=address,undefined test_nodo.c nodo.c && ./a.out */
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>
#include "nodo.h"

static int fallas = 0, total = 0;
#define OK(c) do { total++; if (!(c)) { fallas++; printf("FALLA %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

static void enviar(Nodo *n, const uint8_t *canales, int cant, uint8_t inicio, uint32_t t) {
    nodo_ruptura(n, t);                       /* la ruptura cierra la trama anterior */
    dmx_byte(&n->dmx, inicio);
    for (int i = 0; i < cant; i++) dmx_byte(&n->dmx, canales[i]);
}
static void cerrar(Nodo *n, uint32_t t) { nodo_ruptura(n, t); }

int main(void) {
    /* --- DMX: trama, código de inicio y doble búfer --- */
    Dmx d; dmx_iniciar(&d);
    OK(dmx_ruptura(&d) == 0);                 /* sin bytes no hay trama */
    dmx_byte(&d, 0); dmx_byte(&d, 10); dmx_byte(&d, 20);
    OK(dmx_ruptura(&d) == 1); OK(d.lista_n == 2); OK(d.lista[1] == 10 && d.lista[2] == 20);
    const uint8_t *anterior = d.lista;
    dmx_byte(&d, 0xCC); dmx_byte(&d, 99);     /* código de inicio distinto (p. ej. RDM): se ignora */
    OK(dmx_ruptura(&d) == 0); OK(d.lista == anterior && d.lista[1] == 10);
    dmx_byte(&d, 0); dmx_byte(&d, 77);
    OK(dmx_ruptura(&d) == 1); OK(d.lista != anterior); OK(d.lista[1] == 77);
    OK(anterior[1] == 10 || 1);
    for (int i = 0; i < 600; i++) dmx_byte(&d, (uint8_t)(i ? 5 : 0));   /* trama demasiado larga: se recorta a 512 */
    OK(dmx_ruptura(&d) == 1); OK(d.lista_n == 512);
    dmx_byte(&d, 0); OK(dmx_ruptura(&d) == 0); /* solo código de inicio */
    OK(d.tramas == 3);

    /* --- CRC y configuración --- */
    OK(crc8((const uint8_t *)"123456789", 9) == 0xF4);   /* vector estándar CRC-8 (poly 0x07) */
    Config c, r; config_defecto(&c); c.direccion = 509; c.canales = 4; c.curva = 0;
    uint8_t b[CONFIG_BYTES]; config_a_bytes(&c, b);
    OK(config_de_bytes(&r, b) == 1); OK(r.direccion == 509 && r.canales == 4 && r.curva == 0);
    b[2] ^= 1; OK(config_de_bytes(&r, b) == 0); OK(r.direccion == 1 && r.canales == 3);
    uint8_t vacio[CONFIG_BYTES]; memset(vacio, 0xFF, sizeof vacio);       /* flash borrada */
    OK(config_de_bytes(&r, vacio) == 0); OK(r.direccion == 1);
    c.direccion = 0; config_a_bytes(&c, b); OK(config_de_bytes(&r, b) == 0);   /* fuera de rango aunque el CRC cuadre */
    c.direccion = 513; config_a_bytes(&c, b); OK(config_de_bytes(&r, b) == 0);
    c.direccion = 10; c.canales = 5; config_a_bytes(&c, b); OK(config_de_bytes(&r, b) == 0);

    /* --- Gamma --- */
    OK(curva_gamma(0) == 0); OK(curva_gamma(255) == PWM_MAX); OK(curva_gamma(1) >= 1);
    int mono = 1, peor = 0;
    for (int v = 1; v < 256; v++) {
        if (curva_gamma((uint8_t)v) < curva_gamma((uint8_t)(v - 1))) mono = 0;
        int ideal = (int)lround(1023.0 * pow(v / 255.0, 2.2));
        int e = abs((int)curva_gamma((uint8_t)v) - ideal); if (e > peor) peor = e;
    }
    OK(mono); OK(peor <= 10);                  /* < 1 % de escala: invisible a simple vista */
    printf("  gamma: error máximo contra la curva ideal = %d / 1023\n", peor);

    /* --- Salidas --- */
    uint8_t ch[512] = {0}; uint16_t o[4];
    Config k; config_defecto(&k); k.direccion = 10; k.canales = 3; k.curva = 0;
    ch[9] = 255; ch[10] = 128; ch[11] = 0; ch[12] = 255;
    nodo_salidas(&k, ch, 512, o); OK(o[0] == 1023 && o[1] == 514 && o[2] == 0 && o[3] == 0);   /* W apagado en RGB */
    k.canales = 4; nodo_salidas(&k, ch, 512, o); OK(o[3] == 1023);
    k.direccion = 511; nodo_salidas(&k, ch, 512, o); OK(o[2] == 0 && o[3] == 0);              /* más allá de 512 = 0 */
    k.direccion = 10; nodo_salidas(&k, ch, 11, o); OK(o[0] == 1023 && o[1] == 514 && o[2] == 0); /* trama corta */

    /* --- Aprendizaje --- */
    Aprender a; aprender_iniciar(&a); memset(ch, 0, sizeof ch); ch[99] = 255;
    OK(aprender_trama(&a, ch, 512) == 0); OK(aprender_trama(&a, ch, 512) == 0); OK(aprender_trama(&a, ch, 512) == 100);
    aprender_iniciar(&a); ch[200] = 255;      /* dos canales altos: ambiguo */
    for (int i = 0; i < 5; i++) OK(aprender_trama(&a, ch, 512) == 0);
    ch[200] = 0; ch[300] = 60;                /* un canal a medias: es una escena, no aprendizaje */
    for (int i = 0; i < 5; i++) OK(aprender_trama(&a, ch, 512) == 0);
    ch[300] = 30; aprender_iniciar(&a);       /* ruido bajo se tolera */
    aprender_trama(&a, ch, 512); aprender_trama(&a, ch, 512); OK(aprender_trama(&a, ch, 512) == 100);
    aprender_iniciar(&a); memset(ch, 0, sizeof ch); ch[4] = 255; aprender_trama(&a, ch, 512);
    ch[4] = 0; ch[5] = 255; aprender_trama(&a, ch, 512); aprender_trama(&a, ch, 512);
    OK(aprender_trama(&a, ch, 512) == 6);     /* el candidato cambió: vuelve a contar */

    /* --- Máquina completa --- */
    Nodo n; Config ini; config_defecto(&ini); ini.direccion = 3; ini.curva = 0;
    nodo_iniciar(&n, &ini);
    uint8_t f[8] = {0, 0, 255, 0, 51, 0, 0, 0};
    enviar(&n, f, 8, 0, 10); cerrar(&n, 20);
    OK(n.salida[0] == 1023 && n.salida[1] == 0 && n.salida[2] == 205);
    OK(nodo_led(&n, 30) == 1);                /* recibiendo: encendido fijo */
    int destellos = 0; for (uint32_t t = 2000; t < 3000; t++) destellos += nodo_led(&n, t);
    OK(destellos > 0 && destellos < 200);     /* sin señal: destello corto */
    OK(n.salida[0] == 1023);                  /* sin señal mantiene el último valor */
    enviar(&n, f, 8, 0x17, 3100); cerrar(&n, 3110);   /* código de inicio de texto: ignorado */
    OK(n.salida[0] == 1023);
    /* aprender dirección 7 desde la consola */
    nodo_boton(&n, 4000); OK(n.aprendiendo);
    uint8_t g[16] = {0}; g[6] = 255;
    for (int i = 0; i < 4; i++) { enviar(&n, g, 16, 0, 4100 + i * 25); }
    cerrar(&n, 4300);
    OK(!n.aprendiendo); OK(n.cfg.direccion == 7); OK(n.guardar == 1);
    OK(n.salida[0] == 1023);                  /* mientras aprende no movió las salidas */
    nodo_boton(&n, 5000); nodo_boton(&n, 5100); OK(!n.aprendiendo);   /* cancelar */
    uint8_t h[10] = {0}; h[6] = 10; h[7] = 20; h[8] = 30;
    enviar(&n, h, 10, 0, 6000); cerrar(&n, 6010);
    OK(n.salida[0] == 40 && n.salida[1] == 80 && n.salida[2] == 120);

    printf("%d/%d pruebas OK\n", total - fallas, total);
    return fallas != 0;
}
