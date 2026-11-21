/* Registros del CH32V003 que usa el nodo (solo los necesarios).
 * Direcciones y bits según el manual de referencia de WCH, cotejados con ch32v003hw.h de ch32v003fun (MIT). */
#ifndef CH32V003_REG_H
#define CH32V003_REG_H
#include <stdint.h>
#define R32(a) (*(volatile uint32_t *)(a))
#define R16(a) (*(volatile uint16_t *)(a))

/* RCC (AHB + 0x1000) */
#define RCC_CTLR      R32(0x40021000)
#define RCC_CFGR0     R32(0x40021004)
#define RCC_APB2PCENR R32(0x40021018)
#define RCC_HSION   (1u << 0)
#define RCC_PLLON   (1u << 24)
#define RCC_PLLRDY  (1u << 25)
#define RCC_SW_PLL  0x2u
#define RCC_SWS_MSK 0xCu
#define RCC_SWS_PLL 0x8u
#define APB2_AFIO   (1u << 0)
#define APB2_IOPA   (1u << 2)
#define APB2_IOPC   (1u << 4)
#define APB2_IOPD   (1u << 5)
#define APB2_TIM1   (1u << 11)
#define APB2_USART1 (1u << 14)

/* FLASH (AHB + 0x2000) */
#define FLASH_ACTLR    R32(0x40022000)
#define FLASH_KEYR     R32(0x40022004)
#define FLASH_STATR    R32(0x4002200C)
#define FLASH_CTLR     R32(0x40022010)
#define FLASH_ADDR     R32(0x40022014)
#define FLASH_MODEKEYR R32(0x40022024)
#define FLASH_KEY1 0x45670123u
#define FLASH_KEY2 0xCDEF89ABu
#define FLASH_BSY      (1u << 0)
#define FLASH_STRT     (1u << 6)
#define FLASH_LOCK     (1u << 7)
#define FLASH_PAGE_PG  (1u << 16)          /* programación rápida de página de 64 B */
#define FLASH_PAGE_ER  (1u << 17)          /* borrado rápido de página de 64 B */
#define FLASH_BUF_LOAD (1u << 18)
#define FLASH_BUF_RST  (1u << 19)

/* GPIO (APB2 + 0x0800 / 0x1000 / 0x1400): CFGLR, INDR, OUTDR, BSHR */
#define GPIOA 0x40010800u
#define GPIOC 0x40011000u
#define GPIOD 0x40011400u
#define GPIO_CFGLR(p) R32((p) + 0x00)
#define GPIO_INDR(p)  R32((p) + 0x08)
#define GPIO_OUTDR(p) R32((p) + 0x0C)
#define GPIO_BSHR(p)  R32((p) + 0x10)
#define GPIO_IN_FLOTANTE 0x4u
#define GPIO_IN_PULL     0x8u              /* pull-up si OUTDR = 1 */
#define GPIO_OUT_PP      0x3u              /* salida push-pull 30 MHz */
#define GPIO_AF_PP       0xBu              /* función alterna push-pull 30 MHz */

/* TIM1 (APB2 + 0x2C00) */
#define TIM1 0x40012C00u
#define TIM1_CTLR1   R16(TIM1 + 0x00)
#define TIM1_SWEVGR  R16(TIM1 + 0x14)
#define TIM1_CHCTLR1 R16(TIM1 + 0x18)
#define TIM1_CHCTLR2 R16(TIM1 + 0x1C)
#define TIM1_CCER    R16(TIM1 + 0x20)
#define TIM1_PSC     R16(TIM1 + 0x28)
#define TIM1_ATRLR   R16(TIM1 + 0x2C)
#define TIM1_CH1CVR  R32(TIM1 + 0x34)
#define TIM1_CH2CVR  R32(TIM1 + 0x38)
#define TIM1_CH3CVR  R32(TIM1 + 0x3C)
#define TIM1_CH4CVR  R32(TIM1 + 0x40)
#define TIM1_BDTR    R16(TIM1 + 0x44)

/* USART1 (APB2 + 0x3800) */
#define USART1_STATR R32(0x40013800)
#define USART1_DATAR R32(0x40013804)
#define USART1_BRR   R32(0x40013808)
#define USART1_CTLR1 R32(0x4001380C)
#define USART1_CTLR2 R32(0x40013810)
#define USART_FE   (1u << 1)
#define USART_ORE  (1u << 3)
#define USART_RXNE (1u << 5)
#define USART_RE     (1u << 2)
#define USART_RXNEIE (1u << 5)
#define USART_UE     (1u << 13)

/* Núcleo: PFIC y SysTick */
#define PFIC_IENR(i)  R32(0xE000E100u + 4u * (i))
#define SYSTICK_CTLR  R32(0xE000F000)
#define SYSTICK_CNT   R32(0xE000F008)
#define USART1_IRQn 32
#endif
