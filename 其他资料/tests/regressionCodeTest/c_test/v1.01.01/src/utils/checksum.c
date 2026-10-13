#include "checksum.h"

u8 checksum_xor8(const u8* data, u32 len)
{
    u32 i;
    u8 acc = 0u;

    if (data == 0 || len == 0u) {
        return 0u;
    }

    for (i = 0u; i < len; i++) {
        acc = (u8)(acc ^ data[i]);
        acc = (u8)((acc << 1) | (acc >> 7));
    }

    return acc;
}
