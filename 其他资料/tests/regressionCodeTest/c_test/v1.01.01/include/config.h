#ifndef CONFIG_H
#define CONFIG_H

#include "common.h"

typedef struct {
    u32 device_id;
    u32 baud_rate;
    u8 log_level;
    u8 strict_mode;
} app_config_t;

void config_set_default(app_config_t* cfg);
err_t config_validate(const app_config_t* cfg);

#endif
