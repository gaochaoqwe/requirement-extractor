#include "sensor.h"
#include "crypto.h"

static int g_value = 0;

void sensor_init(void)
{
    g_value = 10;
}

err_t sensor_read(sensor_reading_t* out)
{
    u32 mixed;

    if (out == 0) {
        return ERR_INVALID_ARG;
    }

    mixed = crypto_mix_u32((u32)g_value);
    out->value = (int)(mixed & 0x7Fu);
    out->valid = 1u;

    g_value++;
    return ERR_OK;
}
