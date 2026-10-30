#ifndef KVM_SWITCH_CTRL_H
#define KVM_SWITCH_CTRL_H
#include <stdbool.h>
#include <stdint.h>

enum SwitchState { SWITCH_GAP = 0, SWITCH_SETTLE = 1,
                   SWITCH_ACTIVE = 2, SWITCH_FAULT = 3 };
typedef struct {
    uint32_t since;
    uint32_t gap_ticks;
    uint32_t connections;
    uint8_t state;
    uint8_t active;
    uint8_t pending;
    uint8_t fault;
} SwitchContext;

void switch_init(SwitchContext *sw, uint32_t now);
bool switch_request(SwitchContext *sw, uint8_t target, uint32_t now);
void switch_poll(SwitchContext *sw, uint32_t now);
bool switch_is_healthy(const SwitchContext *sw);
void switch_fault(SwitchContext *sw, uint8_t fault);
#endif
