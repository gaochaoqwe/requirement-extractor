/**
 * CWE测试辅助头文件
 * 用于增加跨文件分析的复杂度
 */

#ifndef CWE_UTILS_H
#define CWE_UTILS_H

#include <stddef.h>

// 最大用户数
#define MAX_USERS 100
#define MAX_NAME_LEN 50
#define BUFFER_SIZE 256

// 用户信息结构
typedef struct {
    char name[MAX_NAME_LEN];
    int id;
    int is_active;
} UserInfo;

// 系统配置结构
typedef struct {
    int max_connections;
    int timeout_seconds;
    char log_path[BUFFER_SIZE];
} SystemConfig;

// 全局变量声明（在cwe_utils.c中定义）
extern UserInfo g_users[MAX_USERS];
extern int g_user_count;
extern SystemConfig g_config;

// 工具函数声明
void init_system_config(void);
char* get_user_by_id(int user_id);
int validate_array_index(int index, int max_size);
void* safe_malloc(size_t size);
int is_user_authorized(int user_id);

#endif // CWE_UTILS_H

