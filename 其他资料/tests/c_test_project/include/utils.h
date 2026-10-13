/**
 * @file utils.h
 * @brief 系统工具函数模块
 * @version 1.0
 * @date 2023-06-04
 */

#ifndef UTILS_H
#define UTILS_H

#include "system_monitor.h"

/**
 * @brief 获取当前时间戳
 * @return time_t 当前时间戳
 */
time_t get_current_timestamp(void);

/**
 * @brief 将时间戳转换为可读字符串
 * @param timestamp 时间戳
 * @param buffer 输出缓冲区
 * @param buffer_size 缓冲区大小
 * @return char* 转换后的字符串
 */
char* timestamp_to_string(time_t timestamp, char* buffer, size_t buffer_size);

/**
 * @brief 生成随机数
 * @param min 最小值
 * @param max 最大值
 * @return int 随机数
 */
int generate_random(int min, int max);

/**
 * @brief 安全字符串复制
 * @param dest 目标字符串
 * @param src 源字符串
 * @param dest_size 目标缓冲区大小
 * @return char* 目标字符串
 */
char* safe_strcpy(char* dest, const char* src, size_t dest_size);

/**
 * @brief 安全字符串连接
 * @param dest 目标字符串
 * @param src 源字符串
 * @param dest_size 目标缓冲区大小
 * @return char* 目标字符串
 */
char* safe_strcat(char* dest, const char* src, size_t dest_size);

/**
 * @brief 将系统状态转换为字符串
 * @param status 系统状态
 * @return const char* 状态字符串
 */
const char* status_to_string(SystemStatus status);

/**
 * @brief 检查指针是否为NULL
 * @param ptr 指针
 * @param ptr_name 指针名称
 * @param file 文件名
 * @param line 行号
 * @return bool 是否为NULL
 */
bool check_null_ptr(const void* ptr, const char* ptr_name, const char* file, int line);

/**
 * @brief 检查内存分配是否成功
 * @param ptr 指针
 * @param size 分配大小
 * @param file 文件名
 * @param line 行号
 * @return void* 分配的内存指针
 */
void* check_memory_alloc(void* ptr, size_t size, const char* file, int line);

#define CHECK_NULL(ptr) check_null_ptr((ptr), #ptr, __FILE__, __LINE__)
#define MALLOC_CHECK(size) check_memory_alloc(malloc(size), (size), __FILE__, __LINE__)

#endif /* UTILS_H */ 