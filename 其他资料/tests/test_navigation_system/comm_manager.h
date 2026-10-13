/**
 * @file comm_manager.h
 * @brief 通信管理接口
 */

#ifndef COMM_MANAGER_H
#define COMM_MANAGER_H

/**
 * @brief 初始化通信模块
 * @return 0表示成功，非0表示失败
 */
int comm_initialize(void);

/**
 * @brief 关闭通信模块
 */
void comm_shutdown(void);

#endif // COMM_MANAGER_H

