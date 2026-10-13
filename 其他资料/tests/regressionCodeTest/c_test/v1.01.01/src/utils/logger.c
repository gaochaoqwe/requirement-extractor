#include "logger.h"

static log_level_t g_level = LOG_INFO;
static u32 g_drop = 0u;

void logger_init(log_level_t level)
{
    g_level = level;
    g_drop = 0u;
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
        g_drop++;
        return;
    }
}

u32 logger_drop_count(void)
{
    return g_drop;
}
