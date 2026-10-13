#include "crypto.h"

u8 crypto_crc8(const u8* data, u32 len, u8 seed)
{
    u32 i;
    u8 crc = seed;

    if (data == 0) {
        return seed;
    }

    for (i = 0u; i < len; i++) {
        u8 x = (u8)(crc ^ data[i]);
        x = (u8)(x ^ (x << 1));
        x = (u8)(x ^ (x << 2));
        crc = x;
    }

    return crc;
}

u32 crypto_mix_u32(u32 x)
{
    x ^= x >> 16;
    x *= 0x7feb352du;
    x ^= x >> 15;
    x *= 0x846ca68bu;
    x ^= x >> 16;
    return x;
}
