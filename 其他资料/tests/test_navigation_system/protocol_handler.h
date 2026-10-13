/**
 * @file protocol_handler.h
 * @brief 通信协议处理接口
 */

#ifndef PROTOCOL_HANDLER_H
#define PROTOCOL_HANDLER_H

/**
 * @brief 初始化协议处理器
 * @return 0表示成功，非0表示失败
 */
int protocol_handler_init(void);

/**
 * @brief 清理协议处理器
 */
void protocol_handler_cleanup(void);

#endif // PROTOCOL_HANDLER_H

