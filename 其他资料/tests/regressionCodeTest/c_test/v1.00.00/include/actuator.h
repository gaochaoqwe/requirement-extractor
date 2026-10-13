#ifndef ACTUATOR_H
#define ACTUATOR_H

#include "common.h"

void actuator_init(void);
err_t actuator_set_output(int value);

#endif
