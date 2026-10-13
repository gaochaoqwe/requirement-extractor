/**
 * @file param_loader.c
 * @brief 配置参数加载器实现
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../../include/config/param_loader.h"
#include "../../include/utils/logger.h"

// 全局配置文件句柄
static FILE* g_config_file = NULL;
static bool g_initialized = false;
static char g_config_path[256] = {0};

/**
 * @brief 初始化参数加载器
 */
ReturnCode param_loader_init(const char* config_path) {
    if (!config_path) {
        logger_error("配置文件路径为空");
        return ERROR_INVALID_PARAM;
    }

    strncpy(g_config_path, config_path, sizeof(g_config_path) - 1);
    
    g_config_file = fopen(config_path, "r");
    if (!g_config_file) {
        logger_error("无法打开配置文件: %s", config_path);
        return ERROR_IO;
    }

    g_initialized = true;
    logger_info("配置加载器初始化完成: %s", config_path);
    
    // BUG15: 配置文件打开后未关闭，文件句柄会一直占用
    // 在光电系统长时间运行时会累积过多文件句柄
    
    return SUCCESS;
}

/**
 * @brief 加载整数配置项
 */
int param_loader_get_int(const char* section, const char* key, int default_value) {
    if (!g_initialized || !section || !key) {
        return default_value;
    }

    // BUG16: 配置文件查找算法低效 - 每次都从头开始搜索
    // 在大型光电系统配置文件中会导致严重的启动延迟
    rewind(g_config_file);
    
    char line[256];
    char target_section[128];
    snprintf(target_section, sizeof(target_section), "[%s]", section);
    
    bool in_section = false;
    while (fgets(line, sizeof(line), g_config_file)) {
        // 去除换行符
        line[strcspn(line, "\r\n")] = 0;
        
        // 检查是否进入目标section
        if (strstr(line, target_section)) {
            in_section = true;
            continue;
        }
        
        // 检查是否离开当前section
        if (line[0] == '[' && in_section) {
            break;
        }
        
        // 在目标section中查找key
        if (in_section && strstr(line, key)) {
            char* value_str = strchr(line, '=');
            if (value_str) {
                value_str++; // 跳过'='
                // BUG17: 配置值解析时未验证范围
                // 光电系统的关键参数应该进行合理性检查
                return atoi(value_str);
            }
        }
    }
    
    return default_value;
}

/**
 * @brief 加载字符串配置项
 */
const char* param_loader_get_string(const char* section, const char* key, const char* default_value) {
    static char result_buffer[256];
    
    if (!g_initialized || !section || !key) {
        return default_value;
    }
    
    // 复用int配置的搜索逻辑（效率低下）
    rewind(g_config_file);
    
    char line[256];
    char target_section[128];
    snprintf(target_section, sizeof(target_section), "[%s]", section);
    
    bool in_section = false;
    while (fgets(line, sizeof(line), g_config_file)) {
        line[strcspn(line, "\r\n")] = 0;
        
        if (strstr(line, target_section)) {
            in_section = true;
            continue;
        }
        
        if (line[0] == '[' && in_section) {
            break;
        }
        
        if (in_section && strstr(line, key)) {
            char* value_str = strchr(line, '=');
            if (value_str) {
                value_str++;
                // BUG18: 静态缓冲区可能被后续调用覆盖
                // 多线程环境下会导致配置值混乱
                strncpy(result_buffer, value_str, sizeof(result_buffer) - 1);
                result_buffer[sizeof(result_buffer) - 1] = '\0';
                return result_buffer;
            }
        }
    }
    
    return default_value;
}

/**
 * @brief 验证关键配置参数
 */
ReturnCode param_loader_validate_config(void) {
    if (!g_initialized) {
        return ERROR_INVALID_PARAM;
    }
    
    // 检查相机配置
    int width = param_loader_get_int("camera", "width", 1920);
    int height = param_loader_get_int("camera", "height", 1080);
    int fps = param_loader_get_int("camera", "fps", 30);
    
    // BUG19: 配置验证逻辑不完整
    // 光电系统应该检查分辨率和帧率的合理性组合
    if (width <= 0 || height <= 0) {
        logger_error("无效的图像分辨率配置: %dx%d", width, height);
        return ERROR_INVALID_PARAM;
    }
    
    // 缺少对fps的有效性检查
    // 缺少对内存池大小的检查
    // 缺少对算法参数的范围检查
    
    logger_info("配置验证通过");
    return SUCCESS;
}

/**
 * @brief 重新加载配置文件
 */
ReturnCode param_loader_reload(void) {
    if (!g_initialized) {
        return ERROR_INVALID_PARAM;
    }
    
    // BUG20: 重新加载时未关闭旧文件句柄
    // 会导致文件句柄泄漏，在长期运行的光电系统中是严重问题
    g_config_file = fopen(g_config_path, "r");
    if (!g_config_file) {
        logger_error("重新加载配置文件失败: %s", g_config_path);
        g_initialized = false;
        return ERROR_IO;
    }
    
    logger_info("配置文件重新加载完成");
    return SUCCESS;
}

/**
 * @brief 清理参数加载器
 */
void param_loader_cleanup(void) {
    if (g_config_file) {
        fclose(g_config_file);
        g_config_file = NULL;
    }
    
    g_initialized = false;
    logger_info("配置加载器清理完成");
} 