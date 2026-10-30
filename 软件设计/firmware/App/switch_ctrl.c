#include "app_config.h"
#include "board.h"
#include "switch_ctrl.h"

void switch_fault(SwitchContext *sw, uint8_t fault)
{
    board_mux_disable();
    board_led_show(TARGET_NONE);
    sw->active = TARGET_NONE;
    sw->state = SWITCH_FAULT;
    if (sw->fault == KVM_FAULT_NONE)
        sw->fault = fault == KVM_FAULT_NONE ? KVM_FAULT_STATE : fault;
}

bool switch_is_healthy(const SwitchContext *sw)
{
    if (sw->fault != KVM_FAULT_NONE || sw->pending >= TARGET_COUNT)
        return false;
    switch (sw->state) {
    case SWITCH_GAP:
        return sw->active == TARGET_NONE &&
               (sw->gap_ticks == BOOT_GAP_TICKS ||
                sw->gap_ticks == SWITCH_GAP_TICKS);
    case SWITCH_SETTLE:
        return sw->active == TARGET_NONE;
    case SWITCH_ACTIVE:
        return sw->active < TARGET_COUNT && sw->active == sw->pending;
    default:
        return false;
    }
}

void switch_init(SwitchContext *sw, uint32_t now)
{
    board_mux_disable();
    board_led_show(TARGET_NONE);
    sw->since = now;
    sw->gap_ticks = BOOT_GAP_TICKS;
    sw->connections = 0;
    sw->state = SWITCH_GAP;
    sw->active = TARGET_NONE;
    sw->pending = DEFAULT_TARGET;
    sw->fault = KVM_FAULT_NONE;
}

bool switch_request(SwitchContext *sw, uint8_t target, uint32_t now)
{
    if (!switch_is_healthy(sw)) {
        switch_fault(sw, KVM_FAULT_STATE);
        return false;
    }
    if (target >= TARGET_COUNT) {
        switch_fault(sw, KVM_FAULT_TARGET);
        return false;
    }
    if (sw->state == SWITCH_ACTIVE && target == sw->active) return true;

    board_mux_disable();
    board_led_show(TARGET_NONE);
    sw->active = TARGET_NONE;
    sw->pending = target;
    sw->state = SWITCH_GAP;
    sw->since = now;
    sw->gap_ticks = SWITCH_GAP_TICKS;
    return true;
}

void switch_poll(SwitchContext *sw, uint32_t now)
{
    if (!switch_is_healthy(sw)) {
        switch_fault(sw, KVM_FAULT_STATE);
        return;
    }
    if (sw->state == SWITCH_GAP) {
        if ((uint32_t)(now - sw->since) >= sw->gap_ticks) {
            if (!board_mux_select(sw->pending)) {
                switch_fault(sw, KVM_FAULT_IO);
                return;
            }
            sw->state = SWITCH_SETTLE;
            sw->since = now;
        }
    } else if (sw->state == SWITCH_SETTLE) {
        if ((uint32_t)(now - sw->since) >= MUX_SETTLE_TICKS) {
            if (!board_mux_enable()) {
                switch_fault(sw, KVM_FAULT_IO);
                return;
            }
            sw->active = sw->pending;
            sw->state = SWITCH_ACTIVE;
            ++sw->connections;
            board_led_show(sw->active);
        }
    }
}
