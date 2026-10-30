#include "app_config.h"
#include "board.h"
#include "debug_state.h"
#include "health.h"
#include "key.h"
#include "switch_ctrl.h"
#include "timebase.h"
#include "ch32v00x.h"

volatile DebugState g_debug;
static KeyContext keys;
static SwitchContext channel;
static HealthContext health;

static void publish(uint8_t raw, uint32_t now)
{
    g_debug.ms = now;
    g_debug.connections = channel.connections;
    g_debug.state = channel.state;
    g_debug.active = channel.active;
    g_debug.pending = channel.pending;
    g_debug.raw_keys = raw;
    g_debug.key_armed = (uint8_t)keys.armed;
    g_debug.last_fault = channel.fault;
}

int main(void)
{
    board_init_safe();
    g_debug.version = KVM_VERSION_CODE;
    g_debug.reset_flags = RCC->RSTSCKR;
    RCC_ClearFlag();
    SystemCoreClockUpdate();
    g_debug.sysclk_hz = SystemCoreClock;
    g_debug.watchdog = KVM_WATCHDOG;
    g_debug.bringup = KVM_BRINGUP;

    key_init(&keys);
    switch_init(&channel, 0);
    health_init(&health, 0);
    bool clock_ok = timebase_init();
    bool watchdog_ok = watchdog_start();
    if (!clock_ok) switch_fault(&channel, KVM_FAULT_CLOCK);
    else if (!watchdog_ok) switch_fault(&channel, KVM_FAULT_WATCHDOG_INIT);

    uint32_t last_tick = timebase_now();
    /* GAP starts after peripheral initialization, never before it. */
    channel.since = last_tick;
    health_init(&health, last_tick);
    publish(0, last_tick);
    for (;;) {
        uint32_t now = timebase_now();
        if (now == last_tick) continue;
        last_tick = now;
        uint8_t raw = board_key_mask();
        uint8_t event = key_poll(&keys, raw, now);
#if KVM_BRINGUP
        /* Diagnostic image: buttons/LEDs only. EN# NEVER goes low. */
        if (event != TARGET_NONE && channel.fault == KVM_FAULT_NONE)
            board_led_show(event);
        board_mux_disable();
#else
        if (event != TARGET_NONE) (void)switch_request(&channel, event, now);
        switch_poll(&channel, now);
#endif
        publish(raw, now);
        if (health_should_feed(&health, now, true, switch_is_healthy(&channel)))
            watchdog_feed();
    }
}
