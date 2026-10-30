#ifndef KVM_TIMEBASE_H
#define KVM_TIMEBASE_H
#include <stdbool.h>
#include <stdint.h>
extern volatile uint32_t g_ms;
bool timebase_init(void);
uint32_t timebase_now(void);
#endif
