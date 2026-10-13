#ifndef STATE_MACHINE_H
#define STATE_MACHINE_H

#include "common.h"

typedef enum {
    ST_BOOT = 0,
    ST_IDLE = 1,
    ST_RUN = 2,
    ST_ERROR = 3
} app_state_t;

typedef struct {
    app_state_t state;
    u32 error_count;
} app_sm_t;

void sm_init(app_sm_t* sm);
void sm_step(app_sm_t* sm, u8 event);
app_state_t sm_get_state(const app_sm_t* sm);

#endif
