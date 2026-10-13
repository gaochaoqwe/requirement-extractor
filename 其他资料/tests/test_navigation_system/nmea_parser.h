/**
 * @file nmea_parser.h
 * @brief NMEA协议解析接口
 */

#ifndef NMEA_PARSER_H
#define NMEA_PARSER_H

#include "gps_receiver.h"

/**
 * @brief 初始化NMEA解析器
 * @return 0表示成功，非0表示失败
 */
int nmea_parser_init(void);

/**
 * @brief 清理NMEA解析器
 */
void nmea_parser_cleanup(void);

/**
 * @brief 解析NMEA语句
 * @param sentence NMEA语句字符串
 * @param data 输出的GPS数据
 * @return 0表示成功，非0表示失败
 */
int parse_nmea_sentence(const char *sentence, GPSData *data);

/**
 * @brief 从串口读取NMEA数据
 * @param buffer 缓冲区
 * @param size 缓冲区大小
 * @return 0表示成功，非0表示失败
 */
int read_nmea_from_serial(char *buffer, int size);

/**
 * @brief 提取GPS坐标
 * @param nmea_field NMEA字段
 * @return 转换后的坐标值
 */
double extract_gps_coordinates(const char *nmea_field, char direction);

#endif // NMEA_PARSER_H

