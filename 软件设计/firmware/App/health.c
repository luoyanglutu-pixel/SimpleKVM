#include "health.h"
void health_init(HealthContext *health, uint32_t now)
{
    health->last_fed_tick = now;
}
bool health_should_feed(HealthContext *health, uint32_t now,
                        bool scan_completed, bool switch_healthy)
{
    if (now == health->last_fed_tick || !scan_completed || !switch_healthy)
        return false;
    health->last_fed_tick = now;
    return true;
}
