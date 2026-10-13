#include "drivers.h"

static void MainLoop_Task(void)
{
    g_systemState.systemTickMs += 1U;

    if ((g_systemState.systemTickMs % 1000U) == 0U)
    {
        g_systemState.heartbeat += 1U;
    }
}

int main(void)
{
    Variables_Init();
    RS422_Init();
    CAN_Init();

    while (1)
    {
        MainLoop_Task();
    }

    return 0;
}
