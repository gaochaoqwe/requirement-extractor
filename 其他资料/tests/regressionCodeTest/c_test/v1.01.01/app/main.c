#include "config.h"
#include "logger.h"
#include "metrics.h"
#include "protocol.h"
#include "sensor.h"
#include "actuator.h"
#include "state_machine.h"

static proto_metrics_t g_metrics;

static void app_handle_msg(const proto_msg_t* msg)
{
    if (msg == 0) {
        return;
    }

    if (!protocol_is_supported(msg->msg_type)) {
        logger_log(LOG_WARN, "app", "unsupported msg");
        return;
    }

    if (msg->msg_type == MSG_SET_OUTPUT) {
        int v = 0;
        if (msg->payload_len >= 1u) {
            v = (int)msg->payload[0];
        }
        (void)actuator_set_output(v);
    }
}

int main(void)
{
    app_config_t cfg;
    app_sm_t sm;

    config_set_default(&cfg);
    (void)config_validate(&cfg);

    logger_init((log_level_t)cfg.log_level);
    metrics_reset(&g_metrics);

    sensor_init();
    actuator_init();
    sm_init(&sm);

    for (;;) {
        proto_msg_t msg;
        msg.msg_type = MSG_PING;
        msg.payload_len = 0;

        app_handle_msg(&msg);
        sm_step(&sm, 1);
    }

    return 0;
}
