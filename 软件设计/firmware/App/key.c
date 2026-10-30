#include "app_config.h"
#include "key.h"

void key_init(KeyContext *key)
{
    key->candidate_since = 0;
    key->last_sample = 0;
    key->candidate = 0;
    key->armed = false;
    key->sampled = false;
}

uint8_t key_poll(KeyContext *key, uint8_t mask, uint32_t now)
{
    uint32_t gap = now - key->last_sample;
    mask &= 0x0fu;
    if (key->sampled && gap == 0u) return TARGET_NONE;

    if (!key->sampled || gap > KEY_SAMPLE_GAP_MAX_MS) {
        key->candidate = mask;
        key->candidate_since = now;
        if (!key->sampled || mask != 0u) key->armed = false;
        key->sampled = true;
    }
    key->last_sample = now;

    /* Even a brief observed overlap cancels this press sequence. */
    if ((mask & (uint8_t)(mask - 1u)) != 0u) key->armed = false;
    if (mask != key->candidate) {
        key->candidate = mask;
        key->candidate_since = now;
    }
    if ((uint32_t)(now - key->candidate_since) < KEY_DEBOUNCE_MS)
        return TARGET_NONE;
    if (mask == 0u) {
        key->armed = true;
        return TARGET_NONE;
    }
    if (!key->armed || (mask & (uint8_t)(mask - 1u)) != 0u)
        return TARGET_NONE;

    key->armed = false;
    for (uint8_t target = 0; target < TARGET_COUNT; ++target)
        if (mask == (uint8_t)(1u << target)) return target;
    return TARGET_NONE;
}
