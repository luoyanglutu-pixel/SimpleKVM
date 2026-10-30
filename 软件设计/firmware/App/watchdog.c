#include "app_config.h"
#include "health.h"
#include "ch32v00x.h"

bool watchdog_start(void)
{
#if KVM_WATCHDOG
    /* LSI nominal 128kHz: 64 * (1999+1) / 128000 = 1s.
       Actual LSI and reset timeout MUST be checked on the sample. */
    uint32_t timeout = UINT32_C(1000000);
    RCC_LSICmd(ENABLE);
    while (RCC_GetFlagStatus(RCC_FLAG_LSIRDY) == RESET) {
        if (--timeout == 0u) return false;
    }
    IWDG_WriteAccessCmd(IWDG_WriteAccess_Enable);
    IWDG_SetPrescaler(IWDG_Prescaler_64);
    IWDG_SetReload(1999);
    timeout = UINT32_C(1000000);
    while (IWDG_GetFlagStatus(IWDG_FLAG_PVU | IWDG_FLAG_RVU) != RESET) {
        if (--timeout == 0u) return false;
    }
    IWDG_ReloadCounter();
    /* LSI is already ready; avoids the SDK's unbounded LSI wait. */
    IWDG->CTLR = UINT16_C(0xcccc);
#endif
    return true;
}

void watchdog_feed(void)
{
#if KVM_WATCHDOG
    IWDG_ReloadCounter();
#endif
}
