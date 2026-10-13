#ifndef SENSOR_H
#define SENSOR_H

#include "common.h"

typedef struct {
    int value;
    u8 valid;
} sensor_reading_t;

void sensor_init(void);
err_t sensor_read(sensor_reading_t* out);

#endif
