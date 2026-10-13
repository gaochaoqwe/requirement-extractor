#include "protocol.h"

static int bytes_equal(const u8* a, const u8* b, u32 n)
{
    u32 i;
    for (i = 0u; i < n; i++) {
        if (a[i] != b[i]) {
            return 0;
        }
    }
    return 1;
}

int test_protocol_roundtrip(void)
{
    proto_msg_t msg;
    u8 buf[80];
    u32 out_len = 0u;
    proto_msg_t decoded;
    u8 i;

    msg.msg_type = MSG_SET_OUTPUT;
    msg.payload_len = 3u;
    for (i = 0u; i < msg.payload_len; i++) {
        msg.payload[i] = (u8)(20u + i);
    }

    if (protocol_encode(&msg, buf, (u32)sizeof(buf), &out_len) != ERR_OK) {
        return 0;
    }

    if (protocol_decode(buf, out_len, &decoded) != ERR_OK) {
        return 0;
    }

    if (decoded.msg_type != msg.msg_type) {
        return 0;
    }
    if (decoded.payload_len != msg.payload_len) {
        return 0;
    }

    if (!bytes_equal(decoded.payload, msg.payload, msg.payload_len)) {
        return 0;
    }

    return 1;
}

int test_protocol_reject_bad_header(void)
{
    u8 frame[4];
    proto_msg_t out;

    frame[0] = 0xABu;
    frame[1] = MSG_PING;
    frame[2] = 0u;
    frame[3] = 0u;

    return (protocol_decode(frame, 4u, &out) != ERR_OK);
}
