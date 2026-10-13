#include "drivers.h"

RS422_Config g_rs422Config;
CAN_Config g_canConfig;
SystemState g_systemState;

static void Delay_Short(void)
{
    volatile uint32_t i = 0;
    for (i = 0; i < 10000U; ++i)
    {
        __asm__ volatile ("" : : : "memory");
    }
}

void Variables_Init(void)
{
    g_rs422Config.baudrate = 115200U;
    g_rs422Config.databits = 8U;
    g_rs422Config.stopbits = 1U;
    g_rs422Config.parity = 0U;

    g_canConfig.bitrate = 500000U;
    g_canConfig.mode = 0U;
    g_canConfig.samplePoint = 75U;

    g_systemState.systemTickMs = 0U;
    g_systemState.heartbeat = 0U;
    g_systemState.isRs422Ready = 0U;
    g_systemState.isCanReady = 0U;
}

void RS422_Init(void)
{
    Delay_Short();
    g_systemState.isRs422Ready = 1U;
}

void CAN_Init(void)
{
    Delay_Short();
    g_systemState.isCanReady = 1U;
}
