/**
 * @file config_loader.h
 * @brief 配置文件加载接口
 */

#ifndef CONFIG_LOADER_H
#define CONFIG_LOADER_H

#define MAX_CONFIG_LINE_LEN 256

// 配置参数结构
typedef struct {
    int gps_baudrate;
    int map_update_interval;
    int log_level;
    char server_address[64];
    int server_port;
} SystemConfig;

/**
 * @brief 加载配置文件
 * @param filepath 配置文件路径
 * @return 0表示成功，非0表示失败
 */
int load_config_file(const char *filepath);

/**
 * @brief 解析配置行
 * @param line 配置行字符串
 * @return 0表示成功，非0表示失败
 */
int parse_config_line(const char *line);

/**
 * @brief 验证配置参数
 * @return 0表示有效，非0表示无效
 */
int validate_config(void);

/**
 * @brief 获取配置
 * @return 配置结构指针
 */
SystemConfig* get_config(void);

/**
 * @brief 清理配置
 */
void cleanup_config(void);

#endif // CONFIG_LOADER_H

