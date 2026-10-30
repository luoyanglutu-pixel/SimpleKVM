/* Freestanding byte routines: no allocator, printf or C runtime startup. */
#include <stddef.h>
void *memset(void *dst, int value, size_t count)
{
    unsigned char *p = dst;
    while (count-- != 0u) *p++ = (unsigned char)value;
    return dst;
}
void *memcpy(void *dst, const void *src, size_t count)
{
    unsigned char *d = dst;
    const unsigned char *s = src;
    while (count-- != 0u) *d++ = *s++;
    return dst;
}
