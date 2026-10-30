#include "app_config.h"
#include "timebase.h"
#include "ch32v00x.h"

volatile uint32_t g_ms;

void TIM2_IRQHandler(void) __attribute__((interrupt("WCH-Interrupt-fast")));
void TIM2_IRQHandler(void)
{
    if (TIM_GetITStatus(TIM2, TIM_IT_Update) != RESET) {
        TIM_ClearITPendingBit(TIM2, TIM_IT_Update);
        ++g_ms;
    }
}

bool timebase_init(void)
{
    RCC_ClocksTypeDef clocks;
    SystemCoreClockUpdate();
    RCC_GetClocksFreq(&clocks);
    if (SystemCoreClock != KVM_SYSCLK_HZ ||
        clocks.HCLK_Frequency != KVM_SYSCLK_HZ ||
        clocks.PCLK1_Frequency != KVM_SYSCLK_HZ)
        return false;

    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM2, ENABLE);
    TIM_Cmd(TIM2, DISABLE);
    TIM_TimeBaseInitTypeDef cfg = {0};
    cfg.TIM_Prescaler = 23;
    cfg.TIM_Period = 999;
    cfg.TIM_ClockDivision = TIM_CKD_DIV1;
    cfg.TIM_CounterMode = TIM_CounterMode_Up;
    TIM_TimeBaseInit(TIM2, &cfg);
    TIM_GenerateEvent(TIM2, TIM_EventSource_Update);
    TIM_SetCounter(TIM2, 0);
    TIM_ClearITPendingBit(TIM2, TIM_IT_Update);
    NVIC_ClearPendingIRQ(TIM2_IRQn);
    g_ms = 0;
    NVIC_EnableIRQ(TIM2_IRQn);
    TIM_ITConfig(TIM2, TIM_IT_Update, ENABLE);
    TIM_Cmd(TIM2, ENABLE);
    return true;
}

uint32_t timebase_now(void)
{
    /* Aligned 32-bit access on RV32; ISR is the only writer. */
    return g_ms;
}
