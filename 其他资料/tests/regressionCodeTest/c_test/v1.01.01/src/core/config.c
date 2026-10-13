#include "config.h"

void config_set_default(app_config_t* cfg)
{
    if (cfg == 0) {
        return;
    }
    cfg->device_id = 1000u;
    cfg->baud_rate = 115200u;
    cfg->log_level = 2u;
    cfg->strict_mode = 1u;
}

err_t config_validate(const app_config_t* cfg)
{
    if (cfg == 0) {
        return ERR_INVALID_ARG;
    }

    if (cfg->baud_rate < 1200u || cfg->baud_rate > 2000000u) {
        return ERR_INVALID_ARG;
    }

    if (cfg->log_level > 3u) {
        return ERR_INVALID_ARG;
    }

    if (cfg->strict_mode > 1u) {
        return ERR_INVALID_ARG;
    }

    return ERR_OK;
}
