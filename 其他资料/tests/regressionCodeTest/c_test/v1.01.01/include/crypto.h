#ifndef CRYPTO_H
#define CRYPTO_H

#include "common.h"

u8 crypto_crc8(const u8* data, u32 len, u8 seed);
u32 crypto_mix_u32(u32 x);

#endif
