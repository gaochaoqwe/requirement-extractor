/**
 * @file nmea_parser.c
 * @brief NMEA协议解析实现
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include "nmea_parser.h"
#include "logger.h"

/**
 * @brief 初始化NMEA解析器
 */
int nmea_parser_init(void) {
    log_message(LOG_DEBUG, "NMEA parser initialized");
    return 0;
}

/**
 * @brief 清理NMEA解析器
 */
void nmea_parser_cleanup(void) {
    log_message(LOG_DEBUG, "NMEA parser cleaned up");
}

/**
 * @brief 解析NMEA语句
 */
int parse_nmea_sentence(const char *sentence, GPSData *data) {
    char buffer[256];
    char *token;
    char *fields[20];
    int field_count = 0;
    
    if (sentence == NULL || data == NULL) {
        return -1;
    }
    
    // 复制到缓冲区进行处理
    strncpy(buffer, sentence, sizeof(buffer) - 1);  // 问题：可能截断数据
    buffer[sizeof(buffer) - 1] = '\0';
    
    // 验证NMEA格式（以$开头）
    if (buffer[0] != '$') {
        log_message(LOG_WARNING, "Invalid NMEA sentence (missing $)");
        return -2;
    }
    
    // 分割字段
    token = strtok(buffer, ",");
    while (token != NULL && field_count < 20) {
        fields[field_count++] = token;
        token = strtok(NULL, ",");
    }
    
    // 解析GPGGA（定位信息）
    if (strncmp(fields[0], "$GPGGA", 6) == 0) {
        if (field_count < 15) {
            log_message(LOG_WARNING, "GPGGA: insufficient fields");
            return -3;
        }
        
        // 提取时间（字段1）
        // 提取纬度（字段2和3）
        if (strlen(fields[2]) > 0) {
            data->latitude = extract_gps_coordinates(fields[2], fields[3][0]);
        }
        
        // 提取经度（字段4和5）
        if (strlen(fields[4]) > 0) {
            data->longitude = extract_gps_coordinates(fields[4], fields[5][0]);
        }
        
        // 提取定位质量（字段6）
        int quality = atoi(fields[6]);
        data->valid = (quality > 0);
        
        // 提取卫星数量（字段7）
        data->satellite_count = atoi(fields[7]);
        
        // 提取海拔（字段9）
        data->altitude = atof(fields[9]);
        
        data->timestamp = time(NULL);
        
        log_message(LOG_DEBUG, "GPGGA parsed: lat=%.6f, lon=%.6f, quality=%d", 
                   data->latitude, data->longitude, quality);
        return 0;
    }
    
    // 解析GPRMC（推荐最小定位信息）
    if (strncmp(fields[0], "$GPRMC", 6) == 0) {
        if (field_count < 12) {
            log_message(LOG_WARNING, "GPRMC: insufficient fields");
            return -4;
        }
        
        // 提取状态（字段2）
        data->valid = (fields[2][0] == 'A');  // A=有效, V=无效
        
        // 提取纬度（字段3和4）
        if (strlen(fields[3]) > 0) {
            data->latitude = extract_gps_coordinates(fields[3], fields[4][0]);
        }
        
        // 提取经度（字段5和6）
        if (strlen(fields[5]) > 0) {
            data->longitude = extract_gps_coordinates(fields[5], fields[6][0]);
        }
        
        // 提取速度（字段7，单位：节）
        float speed_knots = atof(fields[7]);
        data->speed = speed_knots * 1.852;  // 转换为km/h
        
        // 提取方向（字段8）
        data->direction = atof(fields[8]);
        
        data->timestamp = time(NULL);
        
        log_message(LOG_DEBUG, "GPRMC parsed: speed=%.2f km/h, direction=%.1f", 
                   data->speed, data->direction);
        return 0;
    }
    
    // 不支持的NMEA类型
    log_message(LOG_DEBUG, "Unsupported NMEA sentence type: %s", fields[0]);
    return -5;
}

/**
 * @brief 提取GPS坐标
 */
double extract_gps_coordinates(const char *nmea_field, char direction) {
    double value;
    int degrees;
    double minutes;
    
    // NMEA格式：ddmm.mmmm (纬度) 或 dddmm.mmmm (经度)
    value = atof(nmea_field);
    
    // 提取度数
    if (strlen(nmea_field) > 7) {  // 经度（3位度数）
        degrees = (int)(value / 100);
    } else {  // 纬度（2位度数）
        degrees = (int)(value / 100);
    }
    
    // 提取分钟
    minutes = value - (degrees * 100);
    
    // 转换为十进制度数
    double decimal_degrees = degrees + (minutes / 60.0);
    
    // 应用方向（N/S/E/W）
    if (direction == 'S' || direction == 'W') {
        decimal_degrees = -decimal_degrees;
    }
    
    return decimal_degrees;
}

/**
 * @brief 从串口读取NMEA数据（模拟）
 */
int read_nmea_from_serial(char *buffer, int size) {
    // 模拟数据（实际应从串口读取）
    static int counter = 0;
    counter++;
    
    // 模拟GPGGA语句
    if (counter % 2 == 0) {
        snprintf(buffer, size, "$GPGGA,123519,3959.123,N,11623.456,W,1,08,0.9,545.4,M,46.9,M,,*47");
    } else {
        // 模拟GPRMC语句
        snprintf(buffer, size, "$GPRMC,123519,A,3959.123,N,11623.456,W,000.5,054.7,191194,020.3,E*68");
    }
    
    return 0;
}

