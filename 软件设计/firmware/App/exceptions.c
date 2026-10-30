#include "app_config.h"
#include "board.h"
#include "debug_state.h"

static void exception_stop(void) __attribute__((noreturn));
static void exception_stop(void)
{
    board_mux_disable();
    board_led_show(TARGET_NONE);
    g_debug.last_fault = KVM_FAULT_EXCEPTION;
    __asm volatile("csrr %0, mcause" : "=r"(g_debug.raw_mcause));
    /* No ISR feeding: RELEASE resets via IWDG if it has been started. */
    for (;;) __asm volatile("nop");
}
void NMI_Handler(void) __attribute__((interrupt("WCH-Interrupt-fast")));
void HardFault_Handler(void) __attribute__((interrupt("WCH-Interrupt-fast")));
void NMI_Handler(void) { exception_stop(); }
void HardFault_Handler(void) { exception_stop(); }
