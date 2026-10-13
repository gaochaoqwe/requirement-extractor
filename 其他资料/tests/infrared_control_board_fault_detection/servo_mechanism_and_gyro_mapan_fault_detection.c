#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

typedef enum
{
    FAULT_NONE = 0,
    FAULT_POSITION_1 = 1
} FaultPosition;

typedef struct
{
    int16_t target_angle_deg;
    int16_t actual_angle_deg;
    uint16_t motor_current_ma;
    bool encoder_ok;
    bool limit_switch_ok;
    bool enabled;
} ServoMechanismStatus;

typedef struct
{
    int16_t spin_rpm;
    uint16_t supply_mv;
    bool gyro_comm_ok;
    bool mapan_locked;
} GyroMapanStatus;

static uint16_t abs_i16_to_u16(int16_t x)
{
    return (uint16_t)(x < 0 ? -x : x);
}

static bool is_in_range_u16(uint16_t value, uint16_t min_inclusive, uint16_t max_inclusive)
{
    return value >= min_inclusive && value <= max_inclusive;
}

FaultPosition servo_mechanism_fault_detect(const ServoMechanismStatus *status)
{
    if (status == NULL)
    {
        return FAULT_POSITION_1;
    }

    if (!status->enabled)
    {
        return FAULT_POSITION_1;
    }

    if (!status->encoder_ok)
    {
        return FAULT_POSITION_1;
    }

    if (!status->limit_switch_ok)
    {
        return FAULT_POSITION_1;
    }

    if (!is_in_range_u16(status->motor_current_ma, 0, 2000))
    {
        return FAULT_POSITION_1;
    }

    {
        int16_t err = (int16_t)(status->target_angle_deg - status->actual_angle_deg);
        if (abs_i16_to_u16(err) > 5)
        {
            return FAULT_POSITION_1;
        }
    }

    return FAULT_NONE;
}

FaultPosition gyro_mapan_fault_detect(const GyroMapanStatus *status)
{
    if (status == NULL)
    {
        return FAULT_POSITION_1;
    }

    if (!status->gyro_comm_ok)
    {
        return FAULT_POSITION_1;
    }

    if (!status->mapan_locked)
    {
        return FAULT_POSITION_1;
    }

    if (!is_in_range_u16(status->supply_mv, 4500, 5500))
    {
        return FAULT_POSITION_1;
    }

    if (!is_in_range_u16((uint16_t)status->spin_rpm, 0, 20000))
    {
        return FAULT_POSITION_1;
    }

    return FAULT_NONE;
}

int main(void)
{
    ServoMechanismStatus servo_ok = {
        .target_angle_deg = 10,
        .actual_angle_deg = 12,
        .motor_current_ma = 300,
        .encoder_ok = true,
        .limit_switch_ok = true,
        .enabled = true,
    };

    ServoMechanismStatus servo_fault = servo_ok;
    servo_fault.encoder_ok = false;

    GyroMapanStatus gyro_ok = {
        .spin_rpm = 6000,
        .supply_mv = 5000,
        .gyro_comm_ok = true,
        .mapan_locked = true,
    };

    GyroMapanStatus gyro_fault = gyro_ok;
    gyro_fault.mapan_locked = false;

    FaultPosition p1 = servo_mechanism_fault_detect(&servo_ok);
    FaultPosition p2 = servo_mechanism_fault_detect(&servo_fault);
    FaultPosition p3 = gyro_mapan_fault_detect(&gyro_ok);
    FaultPosition p4 = gyro_mapan_fault_detect(&gyro_fault);

    printf("servo_ok fault_position=%d\n", (int)p1);
    printf("servo_fault fault_position=%d\n", (int)p2);
    printf("gyro_ok fault_position=%d\n", (int)p3);
    printf("gyro_fault fault_position=%d\n", (int)p4);

    return 0;
}
