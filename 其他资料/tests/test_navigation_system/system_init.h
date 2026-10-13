/**
 * @file system_init.h
 * @brief 系统初始化接口定义
 */

#ifndef SYSTEM_INIT_H
#define SYSTEM_INIT_H

/**
 * @brief 系统初始化
 * @return 0表示成功，非0表示失败
 */
int system_initialize(void);

/**
 * @brief 系统清理
 */
void system_cleanup(void);

/**
 * @brief 获取系统状态
 * @return 1表示就绪，0表示未就绪
 */
int get_system_status(void);

#endif // SYSTEM_INIT_H

