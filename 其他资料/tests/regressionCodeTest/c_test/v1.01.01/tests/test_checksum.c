#include "checksum.h"

int test_checksum_xor8_basic(void)
{
    u8 data[4];
    data[0] = 1u;
    data[1] = 2u;
    data[2] = 3u;
    data[3] = 4u;

    return (checksum_xor8(data, 4u) != 0u);
}
