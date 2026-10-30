#ifndef KVM_DEBUG_STATE_H
#define KVM_DEBUG_STATE_H
#include <stdint.h>
typedef struct {
    uint32_t version;
    uint32_t sysclk_hz;
    uint32_t ms;
    uint32_t connections;
    uint32_t reset_flags;
    uint32_t raw_mcause;
    uint8_t state;
    uint8_t active;
    uint8_t pending;
    uint8_t raw_keys;
    uint8_t key_armed;
    uint8_t last_fault;
    uint8_t watchdog;
    uint8_t bringup;
} DebugState;
extern volatile DebugState g_debug;
#endif
