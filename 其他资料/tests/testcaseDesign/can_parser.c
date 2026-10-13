#include <stdint.h>
#include <stddef.h>

typedef struct
{
    uint32_t id;
    uint8_t dlc;
    uint8_t data[8];
    uint8_t crc;
} CAN_Frame;

typedef enum
{
    CAN_PARSE_OK = 0,
    CAN_PARSE_ERR_NULL = 1,
    CAN_PARSE_ERR_LEN = 2,
    CAN_PARSE_ERR_CRC = 3,
    CAN_PARSE_ERR_UNSUPPORTED = 4
} CAN_ParseResult;

static uint8_t CAN_CalcCrc8(const CAN_Frame *frame)
{
    uint8_t crc = 0U;
    uint8_t i = 0U;
    uint8_t j = 0U;

    if (frame == NULL)
    {
        return 0U;
    }

    crc ^= (uint8_t)(frame->id & 0xFFU);
    crc ^= (uint8_t)((frame->id >> 8U) & 0xFFU);
    crc ^= (uint8_t)((frame->id >> 16U) & 0xFFU);
    crc ^= (uint8_t)((frame->id >> 24U) & 0xFFU);
    crc ^= frame->dlc;

    for (i = 0U; i < frame->dlc; ++i)
    {
        crc ^= frame->data[i];
        for (j = 0U; j < 8U; ++j)
        {
            if ((crc & 0x80U) != 0U)
            {
                crc = (uint8_t)((crc << 1U) ^ 0x1DU);
            }
            else
            {
                crc <<= 1U;
            }
        }
    }

    return crc;
}

static CAN_ParseResult CAN_ValidateFrame(const CAN_Frame *frame)
{
    uint8_t crc = 0U;

    if (frame == NULL)
    {
        return CAN_PARSE_ERR_NULL;
    }

    if (frame->dlc > 8U)
    {
        return CAN_PARSE_ERR_LEN;
    }

    crc = CAN_CalcCrc8(frame);
    if (crc != frame->crc)
    {
        return CAN_PARSE_ERR_CRC;
    }

    return CAN_PARSE_OK;
}

static void CAN_HandleHeartbeat(const CAN_Frame *frame)
{
    (void)frame;
}

static void CAN_HandleSensorData(const CAN_Frame *frame)
{
    (void)frame;
}

static CAN_ParseResult CAN_Dispatch(const CAN_Frame *frame)
{
    if (frame == NULL)
    {
        return CAN_PARSE_ERR_NULL;
    }

    switch (frame->id)
    {
        case 0x100U:
            if (frame->dlc != 1U)
            {
                return CAN_PARSE_ERR_LEN;
            }
            CAN_HandleHeartbeat(frame);
            return CAN_PARSE_OK;

        case 0x200U:
            if (frame->dlc != 4U)
            {
                return CAN_PARSE_ERR_LEN;
            }
            CAN_HandleSensorData(frame);
            return CAN_PARSE_OK;

        default:
            return CAN_PARSE_ERR_UNSUPPORTED;
    }
}

CAN_ParseResult CAN_ParseAndProcess(const CAN_Frame *frame)
{
    CAN_ParseResult r = CAN_PARSE_OK;

    r = CAN_ValidateFrame(frame);
    if (r != CAN_PARSE_OK)
    {
        return r;
    }

    return CAN_Dispatch(frame);
}

#ifdef CAN_PARSER_SELFTEST
int main(void)
{
    CAN_Frame f;

    f.id = 0x100U;
    f.dlc = 1U;
    f.data[0] = 0x55U;
    f.crc = CAN_CalcCrc8(&f);

    (void)CAN_ParseAndProcess(&f);

    f.dlc = 9U;
    (void)CAN_ParseAndProcess(&f);

    f.id = 0x200U;
    f.dlc = 4U;
    f.data[0] = 1U;
    f.data[1] = 2U;
    f.data[2] = 3U;
    f.data[3] = 4U;
    f.crc = (uint8_t)(CAN_CalcCrc8(&f) ^ 0xFFU);

    (void)CAN_ParseAndProcess(&f);

    return 0;
}
#endif
