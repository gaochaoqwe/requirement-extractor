#ifndef LOGGER_H
#define LOGGER_H

#include "common.h"

typedef enum {
    LOG_ERROR = 0,
    LOG_WARN = 1,
    LOG_INFO = 2,
    LOG_DEBUG = 3
} log_level_t;

void logger_init(log_level_t level);
void logger_set_level(log_level_t level);
void logger_log(log_level_t level, const char* tag, const char* msg);

#endif
