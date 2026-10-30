#ifndef KVM_KEY_H
#define KVM_KEY_H
#include <stdbool.h>
#include <stdint.h>

typedef struct {
    uint32_t candidate_since;
    uint32_t last_sample;
    uint8_t candidate;
    bool armed;
    bool sampled;
} KeyContext;

void key_init(KeyContext *key);
uint8_t key_poll(KeyContext *key, uint8_t mask, uint32_t now);
#endif
