#include "config.h"
#include "logger.h"
#include "protocol.h"
#include "sensor.h"
#include "actuator.h"
#include "state_machine.h"

static void app_handle_msg(const proto_msg_t* msg)
{
    (void)msg;
}

int main(void)
{
    app_config_t cfg;
    app_sm_t sm;

    config_set_default(&cfg);
    (void)config_validate(&cfg);

    logger_init((log_level_t)cfg.log_level);

    sensor_init();
    actuator_init();
    sm_init(&sm);

    for (;;) {
        proto_msg_t msg;
        msg.msg_type = 1;
        msg.payload_len = 0;
        app_handle_msg(&msg);
        sm_step(&sm, 1);
    }

    return 0;
}
