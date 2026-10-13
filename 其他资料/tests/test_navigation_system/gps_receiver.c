/**
 * @file gps_receiver.c
 * @brief GPS数据接收实现
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "gps_receiver.h"
#include "nmea_parser.h"
#include "data_filter.h"
#include "ring_buffer.h"
#include "logger.h"

// GPS接收器状态
static int gps_running = 0;
static GPSData last_valid_position;

/**
 * @brief 启动GPS接收器
 */
int gps_receiver_start(void) {
    log_message(LOG_INFO, "Starting GPS receiver");
    
    // 初始化NMEA解析器
    if (nmea_parser_init() != 0) {
        log_message(LOG_ERROR, "NMEA parser initialization failed");
        return -1;
    }
    
    // 初始化数据滤波器
    if (data_filter_init() != 0) {
        log_message(LOG_ERROR, "Data filter initialization failed");
        return -2;
    }
    
    // 初始化环形缓冲区
    if (rb_init(100) != 0) {  // 100个GPS数据点的缓冲
        log_message(LOG_ERROR, "Ring buffer initialization failed");
        return -3;
    }
    
    // 初始化上次有效位置
    memset(&last_valid_position, 0, sizeof(GPSData));
    
    gps_running = 1;
    log_message(LOG_INFO, "GPS receiver started successfully");
    
    return 0;
}

/**
 * @brief 停止GPS接收器
 */
void gps_receiver_stop(void) {
    log_message(LOG_INFO, "Stopping GPS receiver");
    
    gps_running = 0;
    
    // 清理资源
    rb_cleanup();
    data_filter_cleanup();
    nmea_parser_cleanup();
    
    log_message(LOG_INFO, "GPS receiver stopped");
}

/**
 * @brief 接收GPS数据
 */
int gps_receive_data(GPSData *data) {
    char nmea_sentence[256];
    int ret;
    
    if (!gps_running) {
        log_message(LOG_ERROR, "GPS receiver not running");
        return -1;
    }
    
    if (data == NULL) {
        log_message(LOG_ERROR, "Invalid GPS data pointer");
        return -2;
    }
    
    // 从串口读取NMEA数据（这里模拟）
    // TODO: 实际的串口读取代码
    ret = read_nmea_from_serial(nmea_sentence, sizeof(nmea_sentence));
    if (ret != 0) {
        log_message(LOG_WARNING, "Failed to read NMEA data from serial");
        data->valid = 0;
        return -3;
    }
    
    // 解析NMEA语句
    ret = parse_nmea_sentence(nmea_sentence, data);
    if (ret != 0) {
        log_message(LOG_WARNING, "Failed to parse NMEA sentence: %s", nmea_sentence);
        data->valid = 0;
        return -4;
    }
    
    // 滤波处理
    ret = filter_gps_data(data, &last_valid_position);
    if (ret != 0) {
        log_message(LOG_WARNING, "GPS data filtered out (abnormal)");
        data->valid = 0;
        return -5;
    }
    
    // 数据有效，写入环形缓冲区
    if (data->valid) {
        rb_write(data);
        memcpy(&last_valid_position, data, sizeof(GPSData));
        log_message(LOG_DEBUG, "GPS: lat=%.6f, lon=%.6f, speed=%.2f, sats=%d", 
                   data->latitude, data->longitude, data->speed, data->satellite_count);
    }
    
    return 0;
}

/**
 * @brief 更新当前位置
 */
void update_current_position(GPSData *data) {
    if (data && data->valid) {
        memcpy(&last_valid_position, data, sizeof(GPSData));
        log_message(LOG_DEBUG, "Current position updated");
    }
}

