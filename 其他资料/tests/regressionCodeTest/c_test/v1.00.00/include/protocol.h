#ifndef PROTOCOL_H
#define PROTOCOL_H

#include "common.h"

#define PROTO_MAX_PAYLOAD 64

typedef struct {
    u8 msg_type;
    u8 payload_len;
    u8 payload[PROTO_MAX_PAYLOAD];
} proto_msg_t;

err_t protocol_encode(const proto_msg_t* msg, u8* out, u32 out_cap, u32* out_len);
err_t protocol_decode(const u8* in, u32 in_len, proto_msg_t* out_msg);

#endif
