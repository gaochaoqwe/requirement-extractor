#include "diag.h"
#include "crypto.h"

u32 diag_u32_saturating_add(u32 a, u32 b)
{
    u32 r = a + b;
    if (r < a) {
        return 0xFFFFFFFFu;
    }
    return r;
}

u32 diag_hash_tag(const char* tag)
{
    u32 acc = 0u;
    u32 i = 0u;

    if (tag == 0) {
        return 0u;
    }

    while (tag[i] != '\0') {
        acc = (acc * 131u) + (u32)(unsigned char)tag[i];
        i++;
    }

    return crypto_mix_u32(acc);
}
