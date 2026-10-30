#ifndef KVM_BOARD_H
#define KVM_BOARD_H
#include <stdbool.h>
#include <stdint.h>

/* Exact CH32V003F4P6/TSSOP20 map from the 2026-10-21-2 netlist. */
#define BOARD_LED_MASK UINT16_C(0x000f)   /* PC0..3, active low */
#define BOARD_SEL0 UINT16_C(0x0040)       /* PC6, package pin 16 */
#define BOARD_SEL1 UINT16_C(0x0080)       /* PC7, package pin 17 */
#define BOARD_SEL_MASK (BOARD_SEL0 | BOARD_SEL1)
#define BOARD_EN UINT16_C(0x0004)         /* PD2, high disconnect */
#define BOARD_KEY_MASK UINT16_C(0x0078)  /* PD3..6, active low */

void board_init_safe(void);
uint8_t board_key_mask(void);
void board_led_show(uint8_t target);
void board_mux_disable(void);
bool board_mux_select(uint8_t target);
bool board_mux_enable(void);
bool board_mux_is_disabled(void);
#endif
