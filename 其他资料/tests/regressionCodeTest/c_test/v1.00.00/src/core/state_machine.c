#include "state_machine.h"

void sm_init(app_sm_t* sm)
{
    if (sm == 0) {
        return;
    }
    sm->state = ST_BOOT;
    sm->error_count = 0u;
}

void sm_step(app_sm_t* sm, u8 event)
{
    if (sm == 0) {
        return;
    }

    switch (sm->state) {
        case ST_BOOT:
            sm->state = ST_IDLE;
            break;
        case ST_IDLE:
            if (event == 1u) {
                sm->state = ST_RUN;
            }
            break;
        case ST_RUN:
            if (event == 0u) {
                sm->state = ST_IDLE;
            }
            if (event == 255u) {
                sm->state = ST_ERROR;
                sm->error_count++;
            }
            break;
        case ST_ERROR:
        default:
            if (event == 2u) {
                sm->state = ST_IDLE;
            }
            break;
    }
}

app_state_t sm_get_state(const app_sm_t* sm)
{
    if (sm == 0) {
        return ST_ERROR;
    }
    return sm->state;
}
