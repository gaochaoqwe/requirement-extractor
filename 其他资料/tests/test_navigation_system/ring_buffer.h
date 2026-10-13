/**
 * @file ring_buffer.h
 * @brief 环形缓冲区接口
 */

#ifndef RING_BUFFER_H
#define RING_BUFFER_H

#include "gps_receiver.h"

/**
 * @brief 初始化环形缓冲区
 * @param capacity 缓冲区容量
 * @return 0表示成功，非0表示失败
 */
int rb_init(int capacity);

/**
 * @brief 清理环形缓冲区
 */
void rb_cleanup(void);

/**
 * @brief 写入数据到环形缓冲区
 * @param data GPS数据
 * @return 0表示成功，非0表示失败
 */
int rb_write(const GPSData *data);

/**
 * @brief 从环形缓冲区读取数据
 * @param data 输出的GPS数据
 * @return 0表示成功，非0表示失败
 */
int rb_read(GPSData *data);

/**
 * @brief 获取缓冲区大小
 * @return 当前缓冲区中的数据数量
 */
int rb_size(void);

/**
 * @brief 判断缓冲区是否为空
 * @return 1表示空，0表示非空
 */
int rb_empty(void);

/**
 * @brief 判断缓冲区是否满
 * @return 1表示满，0表示未满
 */
int rb_full(void);

#endif // RING_BUFFER_H

