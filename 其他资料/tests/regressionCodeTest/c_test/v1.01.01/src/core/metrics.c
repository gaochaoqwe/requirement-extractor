#include "metrics.h"

void metrics_reset(proto_metrics_t* m)
{
    if (m == 0) {
        return;
    }
    m->encoded_ok = 0u;
    m->decoded_ok = 0u;
    m->parse_fail = 0u;
}

void metrics_on_encode_ok(proto_metrics_t* m)
{
    if (m == 0) {
        return;
    }
    m->encoded_ok++;
}

void metrics_on_decode_ok(proto_metrics_t* m)
{
    if (m == 0) {
        return;
    }
    m->decoded_ok++;
}

void metrics_on_parse_fail(proto_metrics_t* m)
{
    if (m == 0) {
        return;
    }
    m->parse_fail++;
}
