#include "sensor.h"

static int g_value = 0;

void sensor_init(void)
{
    g_value = 10;
}

err_t sensor_read(sensor_reading_t* out)
{
    if (out == 0) {
        return ERR_INVALID_ARG;
    }

    out->value = g_value;
    out->valid = 1u;
    g_value++;
    return ERR_OK;
}
