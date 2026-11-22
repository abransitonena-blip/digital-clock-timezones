/* Nodo AP · capa de hardware para el CH32V003F4P6 (TSSOP-20), sin SDK.
 * Pines:  PD6 = RX DMX (RO del transceptor RS-485) · PD2/PA1/PC3/PC4 = PWM R/G/B/W (TIM1 CH1–CH4)
 *         PC1 = LED de estado · PC2 = botón a GND · PD1 = SWIO (programación con WCH-LinkE)
 * Reloj: HSI 24 MHz × PLL 2 = 48 MHz.  PWM: 48 MHz / 12 / 1024 = 3.9 kHz, 10 bit. */
#include "ch32v003_reg.h"
#include "nodo.h"

#define F_CPU 48000000u
#define CONFIG_DIR 0x08003FC0u                 /* última página de 64 B de la flash de 16 KB */

static Nodo nodo;
static volatile uint8_t trama_pend;           /* la interrupción cerró una trama válida */
static volatile uint32_t ms;

/* ---------- Tiempo (SysTick libre a HCLK) ---------- */
static uint32_t st_prev, st_acum;
static uint32_t ahora_ms(void) {
    uint32_t c = SYSTICK_CNT, d = c - st_prev; st_prev = c;
    st_acum += d;
    while (st_acum >= F_CPU / 1000) { st_acum -= F_CPU / 1000; ms++; }
    return ms;
}

/* ---------- Reloj, pines y periféricos ---------- */
static void reloj_48mhz(void) {
    FLASH_ACTLR = 1;                                         /* 1 ciclo de espera a 48 MHz */
    RCC_CFGR0 = 0;                                           /* HPRE /1, PLL desde HSI ×2 */
    RCC_CTLR |= RCC_HSION | RCC_PLLON;
    while (!(RCC_CTLR & RCC_PLLRDY)) {}
    RCC_CFGR0 = (RCC_CFGR0 & ~3u) | RCC_SW_PLL;
    while ((RCC_CFGR0 & RCC_SWS_MSK) != RCC_SWS_PLL) {}
}

static void cfg_pin(uint32_t puerto, int pin, uint32_t modo) {
    uint32_t r = GPIO_CFGLR(puerto);
    r &= ~(0xFu << (4 * pin)); r |= modo << (4 * pin);
    GPIO_CFGLR(puerto) = r;
}

static void pines(void) {
    RCC_APB2PCENR |= APB2_AFIO | APB2_IOPA | APB2_IOPC | APB2_IOPD | APB2_TIM1 | APB2_USART1;
    cfg_pin(GPIOD, 6, GPIO_IN_FLOTANTE);                     /* RX DMX */
    cfg_pin(GPIOD, 2, GPIO_AF_PP); cfg_pin(GPIOA, 1, GPIO_AF_PP);
    cfg_pin(GPIOC, 3, GPIO_AF_PP); cfg_pin(GPIOC, 4, GPIO_AF_PP);
    cfg_pin(GPIOC, 1, GPIO_OUT_PP);                          /* LED */
    cfg_pin(GPIOC, 2, GPIO_IN_PULL); GPIO_BSHR(GPIOC) = 1u << 2;   /* botón con pull-up */
}

static void pwm(void) {
    TIM1_PSC = 11; TIM1_ATRLR = PWM_MAX;
    TIM1_CHCTLR1 = 0x6868;                                   /* CH1/CH2: PWM modo 1 con precarga */
    TIM1_CHCTLR2 = 0x6868;                                   /* CH3/CH4 */
    TIM1_CH1CVR = TIM1_CH2CVR = TIM1_CH3CVR = TIM1_CH4CVR = 0;
    TIM1_CCER = 0x1111;                                      /* salidas CH1..CH4 activas en alto */
    TIM1_BDTR = 1u << 15;                                    /* MOE: TIM1 es avanzado, hay que habilitar salidas */
    TIM1_SWEVGR = 1;                                         /* cargar registros */
    TIM1_CTLR1 = (1u << 7) | 1u;                             /* ARPE + CEN */
}

static void uart_dmx(void) {
    USART1_BRR = F_CPU / 250000u;                            /* 192: 250 kbaud exactos */
    USART1_CTLR2 = 2u << 12;                                 /* 2 bits de parada (al recibir basta 1) */
    USART1_CTLR1 = USART_UE | USART_RE | USART_RXNEIE;
    PFIC_IENR(USART1_IRQn / 32) = 1u << (USART1_IRQn % 32);
}

static void salidas(const uint16_t *v) {
    TIM1_CH1CVR = v[0]; TIM1_CH2CVR = v[1]; TIM1_CH3CVR = v[2]; TIM1_CH4CVR = v[3];
}

/* ---------- Interrupción del UART: ruptura = error de trama con dato 0 ---------- */
__attribute__((interrupt)) void USART1_IRQHandler(void) {
    uint32_t s = USART1_STATR;
    uint8_t b = (uint8_t)USART1_DATAR;                       /* leer DATAR limpia RXNE/FE/ORE */
    if (s & USART_FE) {                                      /* ruptura: cambio de búfer O(1) aquí mismo, */
        if (b == 0 && dmx_ruptura(&nodo.dmx)) trama_pend = 1;    /* así no se pierde el código de inicio siguiente */
        return;
    }
    if (s & USART_RXNE) dmx_byte(&nodo.dmx, b);
}

/* ---------- Flash: configuración en la última página ---------- */
static void flash_guardar(const Config *c) {
    uint32_t pal[16];
    uint8_t b[CONFIG_BYTES]; config_a_bytes(c, b);
    for (int i = 0; i < 16; i++) pal[i] = 0xFFFFFFFFu;
    pal[0] = b[0] | (b[1] << 8) | (b[2] << 16) | ((uint32_t)b[3] << 24);
    pal[1] = b[4] | (b[5] << 8) | (b[6] << 16) | ((uint32_t)b[7] << 24);
    volatile uint32_t *p = (volatile uint32_t *)CONFIG_DIR;
    FLASH_KEYR = FLASH_KEY1; FLASH_KEYR = FLASH_KEY2;
    FLASH_MODEKEYR = FLASH_KEY1; FLASH_MODEKEYR = FLASH_KEY2;
    FLASH_CTLR = FLASH_PAGE_ER; FLASH_ADDR = CONFIG_DIR; FLASH_CTLR = FLASH_PAGE_ER | FLASH_STRT;
    while (FLASH_STATR & FLASH_BSY) {}
    FLASH_CTLR = FLASH_PAGE_PG; FLASH_CTLR = FLASH_PAGE_PG | FLASH_BUF_RST; FLASH_ADDR = CONFIG_DIR;
    while (FLASH_STATR & FLASH_BSY) {}
    for (int i = 0; i < 16; i++) {
        p[i] = pal[i];
        FLASH_CTLR = FLASH_PAGE_PG | FLASH_BUF_LOAD;
        while (FLASH_STATR & FLASH_BSY) {}
    }
    FLASH_CTLR = FLASH_PAGE_PG | FLASH_STRT;
    while (FLASH_STATR & FLASH_BSY) {}
    FLASH_CTLR = FLASH_LOCK;
}

static void flash_leer(Config *c) {
    const volatile uint8_t *p = (const volatile uint8_t *)CONFIG_DIR;
    uint8_t b[CONFIG_BYTES];
    for (int i = 0; i < CONFIG_BYTES; i++) b[i] = p[i];
    config_de_bytes(c, b);                                   /* si está borrada o dañada: valores por defecto */
}

/* ---------- Principal ---------- */
int main(void) {
    reloj_48mhz();
    SYSTICK_CTLR = 5;                                        /* contador libre a HCLK */
    pines(); pwm();
    Config c; flash_leer(&c);
    nodo_iniciar(&nodo, &c);
    uart_dmx();
    __asm__ volatile("csrs mstatus, %0" :: "r"(0x8));       /* habilitar interrupciones */

    uint8_t boton_ant = 1; uint32_t boton_t = 0;
    for (;;) {
        uint32_t t = ahora_ms();
        if (trama_pend) {                                    /* procesar la trama recién cerrada mientras */
            trama_pend = 0;                                  /* la interrupción llena el otro búfer */
            __asm__ volatile("" ::: "memory");
            nodo_procesar(&nodo, t);
            salidas(nodo.salida);
        }
        if (nodo.guardar) { nodo.guardar = 0; flash_guardar(&nodo.cfg); }
        uint8_t b = (GPIO_INDR(GPIOC) >> 2) & 1;             /* 0 = presionado */
        if (b != boton_ant && t - boton_t > 30) {            /* antirrebote de 30 ms */
            boton_t = t; boton_ant = b;
            if (!b) nodo_boton(&nodo, t);
        }
        if (nodo_led(&nodo, t)) GPIO_BSHR(GPIOC) = 1u << 1; else GPIO_BSHR(GPIOC) = 1u << (1 + 16);
    }
}
