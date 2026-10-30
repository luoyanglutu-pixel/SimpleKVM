#ifndef KVM_HEALTH_H
#define KVM_HEALTH_H
#include <stdbool.h>
#include <stdint.h>
typedef struct { uint32_t last_fed_tick; } HealthContext;
void health_init(HealthContext *health, uint32_t now);
bool health_should_feed(HealthContext *health, uint32_t now,
                        bool scan_completed, bool switch_healthy);
bool watchdog_start(void);
void watchdog_feed(void);
#endif
