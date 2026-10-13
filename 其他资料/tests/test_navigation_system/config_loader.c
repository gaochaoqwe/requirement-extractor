/**
 * @file config_loader.c
 * @brief 配置文件加载实现
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "config_loader.h"
#include "logger.h"

// 全局配置
static SystemConfig g_config;

/**
 * @brief 加载配置文件
 */
int load_config_file(const char *filepath) {
    FILE *fp;
    char line[MAX_CONFIG_LINE_LEN];
    int line_num = 0;
    
    fp = fopen(filepath, "r");
    if (fp == NULL) {
        log_message(LOG_ERROR, "Cannot open config file: %s", filepath);
        return -1;
    }
    
    // 设置默认值
    g_config.gps_baudrate = 9600;
    g_config.map_update_interval = 60;
    g_config.log_level = 2; // INFO
    strcpy(g_config.server_address, "127.0.0.1");
    g_config.server_port = 8080;
    
    // 逐行读取配置
    while (fgets(line, sizeof(line), fp) != NULL) {  // 问题：sizeof(line)可能导致缓冲区溢出
        line_num++;
        
        // 跳过空行和注释
        if (line[0] == '\n' || line[0] == '#') {
            continue;
        }
        
        // 解析配置行
        if (parse_config_line(line) != 0) {
            log_message(LOG_WARNING, "Invalid config at line %d: %s", line_num, line);
        }
    }
    
    fclose(fp);
    log_message(LOG_INFO, "Config file loaded successfully");
    
    return 0;
}

/**
 * @brief 解析配置行
 */
int parse_config_line(const char *line) {
    char key[64];
    char value[192];
    
    // 简单的key=value解析
    if (sscanf(line, "%63[^=]=%191s", key, value) != 2) {
        return -1;
    }
    
    // 去除空格
    // 问题：没有实现去除空格的逻辑
    
    if (strcmp(key, "gps_baudrate") == 0) {
        g_config.gps_baudrate = atoi(value);
    } else if (strcmp(key, "map_update_interval") == 0) {
        g_config.map_update_interval = atoi(value);
    } else if (strcmp(key, "log_level") == 0) {
        g_config.log_level = atoi(value);
    } else if (strcmp(key, "server_address") == 0) {
        strncpy(g_config.server_address, value, sizeof(g_config.server_address) - 1);
    } else if (strcmp(key, "server_port") == 0) {
        g_config.server_port = atoi(value);
    } else {
        log_message(LOG_WARNING, "Unknown config key: %s", key);
        return -1;
    }
    
    return 0;
}

/**
 * @brief 验证配置参数
 */
int validate_config(void) {
    int valid = 1;
    
    // 验证波特率
    if (g_config.gps_baudrate != 9600 && g_config.gps_baudrate != 115200) {
        log_message(LOG_ERROR, "Invalid GPS baudrate: %d", g_config.gps_baudrate);
        valid = 0;
    }
    
    // 验证更新间隔
    if (g_config.map_update_interval < 10 || g_config.map_update_interval > 3600) {
        log_message(LOG_ERROR, "Invalid map update interval: %d", g_config.map_update_interval);
        valid = 0;
    }
    
    // 验证日志级别
    if (g_config.log_level < 0 || g_config.log_level > 4) {
        log_message(LOG_ERROR, "Invalid log level: %d", g_config.log_level);
        valid = 0;
    }
    
    // 验证服务器端口
    if (g_config.server_port < 1024 || g_config.server_port > 65535) {  // 问题：端口范围检查可能过于严格
        log_message(LOG_ERROR, "Invalid server port: %d", g_config.server_port);
        valid = 0;
    }
    
    return valid ? 0 : -1;
}

/**
 * @brief 获取配置
 */
SystemConfig* get_config(void) {
    return &g_config;
}

/**
 * @brief 清理配置
 */
void cleanup_config(void) {
    // 重置为默认值
    memset(&g_config, 0, sizeof(g_config));
}

