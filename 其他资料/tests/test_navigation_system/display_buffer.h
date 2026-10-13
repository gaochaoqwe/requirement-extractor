/**
 * @file display_buffer.h
 * @brief 显示缓冲区管理接口
 */

#ifndef DISPLAY_BUFFER_H
#define DISPLAY_BUFFER_H

/**
 * @brief 初始化显示缓冲区
 * @return 0表示成功，非0表示失败
 */
int display_buffer_init(void);

/**
 * @brief 清理显示缓冲区
 */
void display_buffer_cleanup(void);

/**
 * @brief 更新显示缓冲区
 * @return 0表示成功，非0表示失败
 */
int update_display_buffer(void);

#endif // DISPLAY_BUFFER_H

