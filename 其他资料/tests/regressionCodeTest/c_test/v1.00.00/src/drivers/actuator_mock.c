#include "actuator.h"

static int g_last = 0;

void actuator_init(void)
{
    g_last = 0;
}

err_t actuator_set_output(int value)
{
    g_last = value;
    if (g_last > 1000) {
        return ERR_OVERFLOW;
    }
    if (g_last < -1000) {
        return ERR_UNDERFLOW;
    }
    return ERR_OK;
}
