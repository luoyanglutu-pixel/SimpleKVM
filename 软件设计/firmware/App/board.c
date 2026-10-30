#include "app_config.h"
#include "board.h"
#include "ch32v00x.h"

static uint8_t selected_target = TARGET_NONE;

static void gpio_config(GPIO_TypeDef *port, uint16_t mask,
                        GPIOMode_TypeDef mode)
{
    GPIO_InitTypeDef cfg = {0};
    cfg.GPIO_Pin = mask;
    cfg.GPIO_Mode = mode;
    cfg.GPIO_Speed = GPIO_Speed_2MHz;
    GPIO_Init(port, &cfg);
}

void board_init_safe(void)
{
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA |
                          RCC_APB2Periph_GPIOC |
                          RCC_APB2Periph_GPIOD, ENABLE);
    /* Preload before changing direction. Never touch PD1 or PD7. */
    GPIOD->BSHR = BOARD_EN;
    GPIOC->BSHR = BOARD_LED_MASK | ((uint32_t)BOARD_SEL_MASK << 16);
    gpio_config(GPIOD, BOARD_EN, GPIO_Mode_Out_PP);
    gpio_config(GPIOC, BOARD_LED_MASK | BOARD_SEL_MASK, GPIO_Mode_Out_PP);
    gpio_config(GPIOD, BOARD_KEY_MASK, GPIO_Mode_IPU);
    gpio_config(GPIOA, GPIO_Pin_1 | GPIO_Pin_2, GPIO_Mode_AIN);
    gpio_config(GPIOC, GPIO_Pin_4 | GPIO_Pin_5, GPIO_Mode_AIN);
    gpio_config(GPIOD, GPIO_Pin_0, GPIO_Mode_AIN);
    selected_target = TARGET_NONE;
}

uint8_t board_key_mask(void)
{
    return (uint8_t)(((~GPIOD->INDR) & BOARD_KEY_MASK) >> 3);
}

void board_led_show(uint8_t target)
{
    uint16_t on = target < TARGET_COUNT ? (uint16_t)(1u << target) : 0u;
    GPIOC->BSHR = (BOARD_LED_MASK & (uint16_t)~on) | ((uint32_t)on << 16);
}

void board_mux_disable(void)
{
    GPIOD->BSHR = BOARD_EN;
    selected_target = TARGET_NONE;
}

bool board_mux_is_disabled(void)
{
    return (GPIOD->OUTDR & BOARD_EN) != 0u;
}

bool board_mux_select(uint8_t target)
{
    if (!board_mux_is_disabled() || target >= TARGET_COUNT) return false;
    uint16_t bits = (uint16_t)((uint16_t)target << 6);
    GPIOC->BSHR = bits | ((uint32_t)(BOARD_SEL_MASK & (uint16_t)~bits) << 16);
    selected_target = target;
    return true;
}

bool board_mux_enable(void)
{
    if (selected_target >= TARGET_COUNT || !board_mux_is_disabled() ||
        ((GPIOC->OUTDR & BOARD_SEL_MASK) >> 6) != selected_target)
        return false;
    GPIOD->BCR = BOARD_EN;
    return true;
}
