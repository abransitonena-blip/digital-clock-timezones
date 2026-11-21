/* Nodo AP · núcleo portable. Ver nodo.h. */
#include "nodo.h"

/* ---------- DMX ---------- */
void dmx_iniciar(Dmx *d) {
    d->act = 0; d->n = 0; d->lista = d->buf[1]; d->lista_n = 0; d->tramas = 0;
    d->buf[1][0] = 0xFF;                       /* nada válido todavía */
}

int dmx_ruptura(Dmx *d) {
    int ok = 0;
    uint8_t *b = d->buf[d->act];
    if (d->n >= 2 && b[0] == 0) {              /* código de inicio 0 (niveles) y al menos un canal */
        d->lista = b; d->lista_n = (uint16_t)(d->n - 1);
        d->act ^= 1; d->tramas++; ok = 1;
    }
    d->n = 0;
    return ok;
}

void dmx_byte(Dmx *d, uint8_t v) {
    if (d->n <= DMX_SLOTS) d->buf[d->act][d->n++] = v;
}

/* ---------- Configuración ---------- */
uint8_t crc8(const uint8_t *p, int n) {        /* CRC-8/ATM, polinomio 0x07 */
    uint8_t c = 0;
    for (int i = 0; i < n; i++) {
        c ^= p[i];
        for (int k = 0; k < 8; k++) c = (uint8_t)((c & 0x80) ? (c << 1) ^ 0x07 : (c << 1));
    }
    return c;
}

void config_defecto(Config *c) { c->direccion = 1; c->canales = 3; c->curva = 1; }

void config_a_bytes(const Config *c, uint8_t o[CONFIG_BYTES]) {
    o[0] = 'A'; o[1] = 'P';
    o[2] = (uint8_t)(c->direccion & 0xFF); o[3] = (uint8_t)(c->direccion >> 8);
    o[4] = c->canales; o[5] = c->curva; o[6] = 0;
    o[7] = crc8(o, 7);
}

int config_de_bytes(Config *c, const uint8_t in[CONFIG_BYTES]) {
    config_defecto(c);
    if (in[0] != 'A' || in[1] != 'P' || crc8(in, 7) != in[7]) return 0;
    uint16_t dir = (uint16_t)(in[2] | (in[3] << 8));
    if (dir < 1 || dir > DMX_SLOTS || in[4] < 1 || in[4] > NODO_CANALES || in[5] > 1) return 0;
    c->direccion = dir; c->canales = in[4]; c->curva = in[5];
    return 1;
}

/* ---------- Aprendizaje ---------- */
void aprender_iniciar(Aprender *a) { a->candidato = 0; a->iguales = 0; }

uint16_t aprender_trama(Aprender *a, const uint8_t *ch, uint16_t n) {
    uint16_t cand = 0;
    for (uint16_t i = 0; i < n; i++) {
        if (ch[i] >= 200) { if (cand) { cand = 0; break; } cand = (uint16_t)(i + 1); }
        else if (ch[i] >= 50) { cand = 0; break; }          /* ruido o escena encendida: no es una señal de aprendizaje */
    }
    if (!cand) { a->iguales = 0; a->candidato = 0; return 0; }
    if (cand == a->candidato) { if (++a->iguales >= 3) return cand; }
    else { a->candidato = cand; a->iguales = 1; }
    return 0;
}

/* ---------- Salidas ---------- */
/* Tabla gamma 2.2 de 33 puntos (v = 0, 8, 16 … 248, 255) interpolada: 66 bytes en vez de 512. */
static const uint16_t GAMMA33[33] = {
    0, 1, 2, 6, 11, 17, 26, 36, 49, 63, 80, 98, 119, 142, 167, 195, 225,
    257, 291, 328, 367, 408, 452, 499, 548, 599, 653, 710, 769, 831, 895, 962, 1023
};

uint16_t curva_gamma(uint8_t v) {
    if (v == 0) return 0;
    if (v == 255) return PWM_MAX;
    uint16_t i = v >> 3, f = v & 7;
    uint32_t a = GAMMA33[i], b = GAMMA33[i + 1];
    uint32_t r = (a * (8 - f) + b * f) >> 3;
    if (r == 0) r = 1;                                       /* valor > 0 nunca queda apagado */
    return (uint16_t)(r > PWM_MAX ? PWM_MAX : r);
}

static uint16_t lineal(uint8_t v) { return (uint16_t)(((uint32_t)v * PWM_MAX + 127) / 255); }

void nodo_salidas(const Config *c, const uint8_t *ch, uint16_t n, uint16_t out[NODO_CANALES]) {
    for (int k = 0; k < NODO_CANALES; k++) {
        uint16_t slot = (uint16_t)(c->direccion - 1 + k);    /* índice base 0 */
        uint8_t v = (k < c->canales && slot < n) ? ch[slot] : 0;
        out[k] = c->curva ? curva_gamma(v) : lineal(v);
    }
}

/* ---------- LED ---------- */
int led_patron(int e, uint32_t t) {
    switch (e) {
        case LED_RECIBIENDO:  return 1;
        case LED_APRENDIENDO: return (t / 100) & 1;                  /* 5 Hz */
        case LED_APRENDIDO:   return (t % 300) < 150 && (t % 1200) < 900; /* 3 destellos */
        default:              return (t % 1000) < 100;               /* destello corto cada segundo */
    }
}

/* ---------- Máquina principal ---------- */
void nodo_iniciar(Nodo *n, const Config *c) {
    dmx_iniciar(&n->dmx); n->cfg = *c; aprender_iniciar(&n->apr);
    n->aprendiendo = 0; n->ult_trama_ms = 0; n->aprendido_ms = 0; n->guardar = 0;
    for (int k = 0; k < NODO_CANALES; k++) n->salida[k] = 0;
    n->dmx.tramas = 0;
}

void nodo_boton(Nodo *n, uint32_t t) {
    (void)t;
    n->aprendiendo = !n->aprendiendo;
    aprender_iniciar(&n->apr);
}

void nodo_ruptura(Nodo *n, uint32_t t) {
    if (dmx_ruptura(&n->dmx)) nodo_procesar(n, t);
}

void nodo_procesar(Nodo *n, uint32_t t) {
    n->ult_trama_ms = t;
    const uint8_t *ch = n->dmx.lista + 1;
    if (n->aprendiendo) {
        uint16_t d = aprender_trama(&n->apr, ch, n->dmx.lista_n);
        if (d) { n->cfg.direccion = d; n->aprendiendo = 0; n->aprendido_ms = t ? t : 1; n->guardar = 1; }
        return;                                              /* mientras aprende, las salidas no cambian */
    }
    nodo_salidas(&n->cfg, ch, n->dmx.lista_n, n->salida);    /* sin señal: se mantiene el último valor */
}

int nodo_led(const Nodo *n, uint32_t t) {
    if (n->aprendiendo) return led_patron(LED_APRENDIENDO, t);
    if (n->aprendido_ms && t - n->aprendido_ms < 1200) return led_patron(LED_APRENDIDO, t - n->aprendido_ms);
    if (n->dmx.tramas && t - n->ult_trama_ms < SIN_SENAL_MS) return led_patron(LED_RECIBIENDO, t);
    return led_patron(LED_SIN_SENAL, t);
}
