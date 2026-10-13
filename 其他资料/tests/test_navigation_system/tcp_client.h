/**
 * @file tcp_client.h
 * @brief TCP客户端接口
 */

#ifndef TCP_CLIENT_H
#define TCP_CLIENT_H

/**
 * @brief 连接到服务器
 * @param host 服务器地址
 * @param port 服务器端口
 * @return 0表示成功，非0表示失败
 */
int tcp_connect(const char *host, int port);

/**
 * @brief 断开连接
 */
void tcp_disconnect(void);

/**
 * @brief 发送数据
 * @param data 数据指针
 * @param size 数据大小
 * @return 发送的字节数，-1表示失败
 */
int tcp_send(const void *data, int size);

/**
 * @brief 接收数据
 * @param buffer 接收缓冲区
 * @param size 缓冲区大小
 * @return 接收的字节数，-1表示失败
 */
int tcp_receive(void *buffer, int size);

#endif // TCP_CLIENT_H

