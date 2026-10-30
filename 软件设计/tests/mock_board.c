#include "app_config.h"
#include "board.h"
#include "health.h"
#include "key.h"
#include "switch_ctrl.h"

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT __attribute__((visibility("default")))
#endif

typedef struct { uint32_t time; uint8_t kind; uint8_t value; } Event;
static Event events[512];
static uint32_t event_count, violations, timestamp, feeds;
static uint8_t disabled, selected, led, injected_failure;
static KeyContext keys;
static SwitchContext sw;
static HealthContext health;

static void log_event(uint8_t kind, uint8_t value)
{
    if (event_count < 512) {
        events[event_count].time = timestamp;
        events[event_count].kind = kind;
        events[event_count].value = value;
        ++event_count;
    } else ++violations;
}
void board_init_safe(void) { disabled = 1; selected = TARGET_NONE; led = TARGET_NONE; }
uint8_t board_key_mask(void) { return 0; }
void board_led_show(uint8_t target) { led = target; log_event(2, target); }
void board_mux_disable(void)
{
    disabled = 1;
    selected = TARGET_NONE;
    log_event(1, 1);
}
bool board_mux_is_disabled(void) { return disabled != 0; }
bool board_mux_select(uint8_t target)
{
    if (!disabled || target >= TARGET_COUNT) { ++violations; return false; }
    if (injected_failure == 1) return false;
    selected = target;
    log_event(3, target);
    return true;
}
bool board_mux_enable(void)
{
    if (!disabled || selected >= TARGET_COUNT) { ++violations; return false; }
    if (injected_failure == 2) return false;
    disabled = 0;
    log_event(4, selected);
    return true;
}

EXPORT void test_reset(uint32_t now)
{
    event_count = violations = feeds = 0;
    timestamp = now;
    injected_failure = 0;
    board_init_safe();
    key_init(&keys);
    switch_init(&sw, now);
    health_init(&health, now);
}
EXPORT uint32_t test_tick(uint32_t now, uint32_t mask)
{
    timestamp = now;
    uint8_t event = key_poll(&keys, (uint8_t)mask, now);
    if (event != TARGET_NONE) (void)switch_request(&sw, event, now);
    switch_poll(&sw, now);
    if (health_should_feed(&health, now, true, switch_is_healthy(&sw))) ++feeds;
    return event;
}
EXPORT uint32_t test_request(uint32_t now, uint32_t target)
{
    timestamp = now;
    return switch_request(&sw, (uint8_t)target, now);
}
EXPORT void test_poll(uint32_t now)
{
    timestamp = now;
    switch_poll(&sw, now);
}
EXPORT void test_corrupt(uint32_t state, uint32_t pending, uint32_t active)
{
    sw.state = (uint8_t)state;
    sw.pending = (uint8_t)pending;
    sw.active = (uint8_t)active;
}
EXPORT void test_inject_failure(uint32_t mode) { injected_failure = (uint8_t)mode; }
EXPORT void test_clear_events(void) { event_count = 0; }
EXPORT uint32_t test_get(uint32_t field)
{
    switch (field) {
    case 0: return sw.state;
    case 1: return sw.active;
    case 2: return sw.pending;
    case 3: return sw.fault;
    case 4: return sw.connections;
    case 5: return keys.armed;
    case 6: return disabled;
    case 7: return selected;
    case 8: return led;
    case 9: return event_count;
    case 10: return violations;
    case 11: return feeds;
    default: return UINT32_MAX;
    }
}
EXPORT uint32_t test_event(uint32_t index, uint32_t field)
{
    if (index >= event_count) return UINT32_MAX;
    if (field == 0) return events[index].time;
    if (field == 1) return events[index].kind;
    return events[index].value;
}
EXPORT uint32_t test_health(uint32_t now, uint32_t scanned, uint32_t healthy)
{
    return health_should_feed(&health, now, scanned != 0, healthy != 0);
}
