#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

typedef struct
{
    uint16_t supply_mv;
    uint16_t ir_tx_ma;
    uint16_t ir_rx_mv;
    uint16_t temperature_c;
    bool i2c_ok;
} IrBoardStatus;

typedef enum
{
    IR_FAULT_NONE = 0,
    IR_FAULT_POSITION_1 = 1
} IrFaultPosition;

typedef struct
{
    uint16_t signal_mv;
    uint16_t ambient_mv;
    bool self_test_ok;
    bool connected;
} IrDetectorStatus;

static bool is_in_range_u16(uint16_t value, uint16_t min_inclusive, uint16_t max_inclusive)
{
    return value >= min_inclusive && value <= max_inclusive;
}

IrFaultPosition ir_control_board_fault_detect(const IrBoardStatus *status)
{
    if (status == NULL)
    {
        return IR_FAULT_POSITION_1;
    }

    if (!status->i2c_ok)
    {
        return IR_FAULT_POSITION_1;
    }

    if (!is_in_range_u16(status->supply_mv, 4750, 5250))
    {
        return IR_FAULT_POSITION_1;
    }

    if (!is_in_range_u16(status->temperature_c, 0, 85))
    {
        return IR_FAULT_POSITION_1;
    }

    if (!is_in_range_u16(status->ir_tx_ma, 5, 200))
    {
        return IR_FAULT_POSITION_1;
    }

    if (!is_in_range_u16(status->ir_rx_mv, 50, 3300))
    {
        return IR_FAULT_POSITION_1;
    }

    return IR_FAULT_NONE;
}

IrFaultPosition ir_detector_fault_detect(const IrDetectorStatus *status)
{
    if (status == NULL)
    {
        return IR_FAULT_POSITION_1;
    }

    if (!status->connected)
    {
        return IR_FAULT_POSITION_1;
    }

    if (!status->self_test_ok)
    {
        return IR_FAULT_POSITION_1;
    }

    if (!is_in_range_u16(status->signal_mv, 100, 3200))
    {
        return IR_FAULT_POSITION_1;
    }

    if (!is_in_range_u16(status->ambient_mv, 0, 3300))
    {
        return IR_FAULT_POSITION_1;
    }

    if (status->signal_mv < status->ambient_mv)
    {
        return IR_FAULT_POSITION_1;
    }

    return IR_FAULT_NONE;
}

int main(void)
{
    IrBoardStatus ok = {
        .supply_mv = 5000,
        .ir_tx_ma = 60,
        .ir_rx_mv = 1200,
        .temperature_c = 25,
        .i2c_ok = true,
    };

    IrBoardStatus fault = ok;
    fault.i2c_ok = false;

    IrDetectorStatus det_ok = {
        .signal_mv = 1800,
        .ambient_mv = 200,
        .self_test_ok = true,
        .connected = true,
    };

    IrDetectorStatus det_fault = det_ok;
    det_fault.connected = false;

    IrFaultPosition p1 = ir_control_board_fault_detect(&ok);
    IrFaultPosition p2 = ir_control_board_fault_detect(&fault);

    IrFaultPosition p3 = ir_detector_fault_detect(&det_ok);
    IrFaultPosition p4 = ir_detector_fault_detect(&det_fault);

    printf("ok fault_position=%d\n", (int)p1);
    printf("fault fault_position=%d\n", (int)p2);

    printf("det_ok fault_position=%d\n", (int)p3);
    printf("det_fault fault_position=%d\n", (int)p4);

    return 0;
}
