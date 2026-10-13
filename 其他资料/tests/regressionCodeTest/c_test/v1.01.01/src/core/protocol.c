#include "protocol.h"
#include "crypto.h"

static u8 compute_frame_cs(const u8* data, u32 len)
{
    return crypto_crc8(data, len, 0x5Au);
}

int protocol_is_supported(u8 msg_type)
{
    return (msg_type == MSG_PING || msg_type == MSG_SET_OUTPUT || msg_type == MSG_READ_SENSOR);
}

err_t protocol_encode(const proto_msg_t* msg, u8* out, u32 out_cap, u32* out_len)
{
    u32 i;
    u8 cs;

    if (msg == 0 || out == 0 || out_len == 0) {
        return ERR_INVALID_ARG;
    }
    if (!protocol_is_supported(msg->msg_type)) {
        return ERR_UNSUPPORTED;
    }
    if (msg->payload_len > PROTO_MAX_PAYLOAD) {
        return ERR_INVALID_ARG;
    }

    if (out_cap < (u32)(msg->payload_len + PROTO_MIN_FRAME)) {
        return ERR_OVERFLOW;
    }

    out[0] = 0xAAu;
    out[1] = msg->msg_type;
    out[2] = msg->payload_len;

    for (i = 0u; i < msg->payload_len; i++) {
        out[3u + i] = msg->payload[i];
    }

    cs = compute_frame_cs(out, 3u + msg->payload_len);
    out[3u + msg->payload_len] = cs;

    *out_len = (u32)(msg->payload_len + PROTO_MIN_FRAME);
    return ERR_OK;
}

err_t protocol_decode(const u8* in, u32 in_len, proto_msg_t* out_msg)
{
    u8 msg_type;
    u8 payload_len;
    u8 cs;
    u8 expected;
    u32 i;

    if (in == 0 || out_msg == 0) {
        return ERR_INVALID_ARG;
    }
    if (in_len < PROTO_MIN_FRAME) {
        return ERR_PARSE;
    }
    if (in[0] != 0xAAu) {
        return ERR_PARSE;
    }

    msg_type = in[1];
    payload_len = in[2];

    if (!protocol_is_supported(msg_type)) {
        return ERR_UNSUPPORTED;
    }
    if (payload_len > PROTO_MAX_PAYLOAD) {
        return ERR_PARSE;
    }
    if (in_len != (u32)(payload_len + PROTO_MIN_FRAME)) {
        return ERR_PARSE;
    }

    cs = in[3u + payload_len];
    expected = compute_frame_cs(in, 3u + payload_len);
    if (cs != expected) {
        return ERR_PARSE;
    }

    out_msg->msg_type = msg_type;
    out_msg->payload_len = payload_len;
    for (i = 0u; i < payload_len; i++) {
        out_msg->payload[i] = in[3u + i];
    }

    return ERR_OK;
}
