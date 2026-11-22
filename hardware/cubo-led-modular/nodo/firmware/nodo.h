/* Nodo AP · núcleo portable (sin hardware): recepción DMX512, aprendizaje de dirección, curva y salidas.
 * Se prueba en la PC (test_nodo.c) y se compila igual para el CH32V003 (hal_ch32v003.c). */
#ifndef NODO_H
#define NODO_H
#include <stdint.h>

#define DMX_SLOTS 512
#define PWM_MAX 1023u                 /* resolución de salida: 10 bit */
#define NODO_CANALES 4                /* R G B W */

/* ---------- Receptor DMX512 (byte a byte, con aviso de ruptura) ---------- */
typedef struct {
    uint8_t  buf[2][DMX_SLOTS + 1];   /* doble búfer: [0] = código de inicio, [1..512] = canales */
    uint8_t  act;                     /* búfer que se está llenando */
    uint16_t n;                       /* bytes recibidos en la trama actual */
    const uint8_t *lista;             /* última trama completa (apunta al otro búfer: cambio O(1) en la ruptura) */
    uint16_t lista_n;                 /* canales válidos en lista (sin el código de inicio) */
    uint32_t tramas;                  /* tramas válidas recibidas */
} Dmx;

void dmx_iniciar(Dmx *d);
/* Ruptura (BREAK) detectada: cierra la trama anterior. Devuelve 1 si quedó una trama válida en `lista`. */
int  dmx_ruptura(Dmx *d);
/* Un byte recibido después de la ruptura. */
void dmx_byte(Dmx *d, uint8_t b);

/* ---------- Configuración guardada ---------- */
typedef struct {
    uint16_t direccion;               /* 1..512 */
    uint8_t  canales;                 /* 1..4: MONO, (CCT=2), RGB=3, RGBW=4 */
    uint8_t  curva;                   /* 1 = corrección gamma 2.2; 0 = lineal */
} Config;

#define CONFIG_BYTES 8
void config_defecto(Config *c);
void config_a_bytes(const Config *c, uint8_t out[CONFIG_BYTES]);   /* con firma y CRC-8 */
int  config_de_bytes(Config *c, const uint8_t in[CONFIG_BYTES]);   /* 1 = válida; si no, deja valores por defecto */
uint8_t crc8(const uint8_t *p, int n);

/* ---------- Aprendizaje de dirección ----------
 * Se activa con el botón. La consola o el cubo pone UN canal en ≥ 200 y el resto en < 50:
 * ese canal pasa a ser la dirección. Hacen falta 3 tramas seguidas iguales para aceptar. */
typedef struct { uint16_t candidato; uint8_t iguales; } Aprender;
void aprender_iniciar(Aprender *a);
/* Devuelve la dirección aprendida (1..512) o 0 si todavía no. */
uint16_t aprender_trama(Aprender *a, const uint8_t *canales, uint16_t n);

/* ---------- Salidas ---------- */
uint16_t curva_gamma(uint8_t v);      /* 0..255 → 0..1023 con gamma 2.2 */
/* Calcula las salidas a partir de una trama (canales[0] = canal 1). Canales fuera de la trama = 0. */
void nodo_salidas(const Config *c, const uint8_t *canales, uint16_t n, uint16_t out[NODO_CANALES]);

/* ---------- LED de estado ---------- */
enum { LED_SIN_SENAL, LED_RECIBIENDO, LED_APRENDIENDO, LED_APRENDIDO };
/* t_ms = tiempo libre; devuelve 1 = encendido. */
int led_patron(int estado, uint32_t t_ms);

/* ---------- Máquina principal (portable) ---------- */
typedef struct {
    Dmx dmx;
    Config cfg;
    Aprender apr;
    uint8_t aprendiendo;
    uint32_t ult_trama_ms;
    uint32_t aprendido_ms;
    uint16_t salida[NODO_CANALES];
    uint8_t guardar;                  /* 1 = la HAL debe escribir cfg en flash */
} Nodo;

#define SIN_SENAL_MS 1000u
void nodo_iniciar(Nodo *n, const Config *c);
void nodo_boton(Nodo *n, uint32_t t_ms);              /* pulsación corta: entra/sale de aprendizaje */
void nodo_ruptura(Nodo *n, uint32_t t_ms);            /* BREAK: cierra la trama y la procesa (pruebas) */
void nodo_procesar(Nodo *n, uint32_t t_ms);           /* procesa dmx.lista (en el equipo: tras dmx_ruptura en la interrupción) */
int  nodo_led(const Nodo *n, uint32_t t_ms);
#endif
