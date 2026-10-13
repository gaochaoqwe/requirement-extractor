#include "crypto.h"

int test_crypto_crc8_stability(void)
{
    u8 data[3];
    u8 a;
    u8 b;

    data[0] = 1u;
    data[1] = 2u;
    data[2] = 3u;

    a = crypto_crc8(data, 3u, 0x5Au);
    b = crypto_crc8(data, 3u, 0x5Au);

    return (a == b);
}
