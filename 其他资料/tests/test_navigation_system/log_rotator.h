/**
 * @file log_rotator.h
 * @brief 日志轮转接口
 */

#ifndef LOG_ROTATOR_H
#define LOG_ROTATOR_H

#define MAX_LOG_SIZE (10 * 1024 * 1024)  // 10MB
#define MAX_LOG_FILES 5

/**
 * @brief 检查并执行日志轮转
 * @return 0表示成功，非0表示失败
 */
int check_and_rotate_log(void);

#endif // LOG_ROTATOR_H

