#include "logger.h"

static log_level_t g_level = LOG_INFO;

void logger_init(log_level_t level)
{
    g_level = level;
}

void logger_set_level(log_level_t level)
{
    g_level = level;
}

void logger_log(log_level_t level, const char* tag, const char* msg)
{
    (void)tag;
    (void)msg;
    if (level > g_level) {
        return;
    }
}
