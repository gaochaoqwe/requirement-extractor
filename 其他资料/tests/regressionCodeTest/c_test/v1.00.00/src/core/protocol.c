#include "protocol.h"
#include "checksum.h"

err_t protocol_encode(const proto_msg_t* msg, u8* out, u32 out_cap, u32* out_len)
{
    u8 cs;
    u32 i;

    if (msg == 0 || out == 0 || out_len == 0) {
        return ERR_INVALID_ARG;
    }
    if (msg->payload_len > PROTO_MAX_PAYLOAD) {
        return ERR_INVALID_ARG;
    }
    if (out_cap < (u32)(msg->payload_len + 3u)) {
        return ERR_OVERFLOW;
    }

    out[0] = msg->msg_type;
    out[1] = msg->payload_len;

    for (i = 0u; i < msg->payload_len; i++) {
        out[2u + i] = msg->payload[i];
    }

    cs = checksum_xor8(out, 2u + msg->payload_len);
    out[2u + msg->payload_len] = cs;

    *out_len = 3u + msg->payload_len;
    return ERR_OK;
}

err_t protocol_decode(const u8* in, u32 in_len, proto_msg_t* out_msg)
{
    u8 payload_len;
    u8 cs;
    u8 expected;
    u32 i;

    if (in == 0 || out_msg == 0) {
        return ERR_INVALID_ARG;
    }
    if (in_len < 3u) {
        return ERR_PARSE;
    }

    payload_len = in[1];
    if (payload_len > PROTO_MAX_PAYLOAD) {
        return ERR_PARSE;
    }
    if (in_len != (u32)(payload_len + 3u)) {
        return ERR_PARSE;
    }

    cs = in[2u + payload_len];
    expected = checksum_xor8(in, 2u + payload_len);
    if (cs != expected) {
        return ERR_PARSE;
    }

    out_msg->msg_type = in[0];
    out_msg->payload_len = payload_len;
    for (i = 0u; i < payload_len; i++) {
        out_msg->payload[i] = in[2u + i];
    }

    return ERR_OK;
}
