/**
 * @file param_loader.h
 * @brief 配置参数加载器接口
 */

#ifndef PARAM_LOADER_H
#define PARAM_LOADER_H

#include "../common/types.h"

/**
 * @brief 初始化参数加载器
 * @param config_path 配置文件路径
 * @return 成功返回SUCCESS，失败返回错误码
 */
ReturnCode param_loader_init(const char* config_path);

/**
 * @brief 获取整数配置项
 * @param section 配置段名
 * @param key 配置键名
 * @param default_value 默认值
 * @return 配置值或默认值
 */
int param_loader_get_int(const char* section, const char* key, int default_value);

/**
 * @brief 获取字符串配置项
 * @param section 配置段名
 * @param key 配置键名
 * @param default_value 默认值
 * @return 配置值或默认值
 */
const char* param_loader_get_string(const char* section, const char* key, const char* default_value);

/**
 * @brief 验证关键配置参数
 * @return 验证通过返回SUCCESS，否则返回错误码
 */
ReturnCode param_loader_validate_config(void);

/**
 * @brief 重新加载配置文件
 * @return 成功返回SUCCESS，失败返回错误码
 */
ReturnCode param_loader_reload(void);

/**
 * @brief 清理参数加载器
 */
void param_loader_cleanup(void);

#endif // PARAM_LOADER_H 