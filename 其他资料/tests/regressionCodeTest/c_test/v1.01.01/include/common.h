#ifndef COMMON_H
#define COMMON_H

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

typedef enum {
    ERR_OK = 0,
    ERR_INVALID_ARG = 1,
    ERR_OVERFLOW = 2,
    ERR_UNDERFLOW = 3,
    ERR_PARSE = 4,
    ERR_UNSUPPORTED = 5
} err_t;

#endif
