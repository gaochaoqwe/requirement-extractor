#ifndef METRICS_H
#define METRICS_H

#include "common.h"

typedef struct {
    u32 encoded_ok;
    u32 decoded_ok;
    u32 parse_fail;
} proto_metrics_t;

void metrics_reset(proto_metrics_t* m);
void metrics_on_encode_ok(proto_metrics_t* m);
void metrics_on_decode_ok(proto_metrics_t* m);
void metrics_on_parse_fail(proto_metrics_t* m);

#endif
