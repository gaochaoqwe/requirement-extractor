#ifndef DRIVERS_H
#define DRIVERS_H

#include <stdint.h>

typedef struct
{
    uint32_t baudrate;
    uint8_t databits;
    uint8_t stopbits;
    uint8_t parity;
} RS422_Config;

typedef struct
{
    uint32_t bitrate;
    uint8_t mode;
    uint8_t samplePoint;
} CAN_Config;

typedef struct
{
    uint32_t systemTickMs;
    uint32_t heartbeat;
    uint8_t isRs422Ready;
    uint8_t isCanReady;
} SystemState;

extern RS422_Config g_rs422Config;
extern CAN_Config g_canConfig;
extern SystemState g_systemState;

void Variables_Init(void);
void RS422_Init(void);
void CAN_Init(void);

#endif
