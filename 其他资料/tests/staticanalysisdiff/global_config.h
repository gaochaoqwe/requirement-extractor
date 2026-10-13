/**
 * 全局配置头文件
 * 包含全局宏定义、常量、结构体定义
 */
#ifndef GLOBAL_CONFIG_H
#define GLOBAL_CONFIG_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ========== 全局宏定义 ========== */

// 缓冲区大小定义
#define MAX_BUFFER_SIZE 256
#define SMALL_BUFFER_SIZE 64
#define TINY_BUFFER_SIZE 16

// 数组大小定义
#define MAX_USERS 100
#define MAX_MESSAGES 50
#define MAX_NAME_LENGTH 32

// 配置标志
#define ENABLE_LOGGING 1
#define DEBUG_MODE 0
#define SAFE_MODE 1

// 条件编译宏
#define USE_ADVANCED_FEATURES 1
#define VALIDATE_INPUT 1

/* ========== 全局结构体定义 ========== */

// 用户信息结构体
typedef struct {
    int user_id;
    char username[MAX_NAME_LENGTH];
    int age;
    int is_active;
} UserInfo;

// 消息结构体
typedef struct {
    int message_id;
    char content[MAX_BUFFER_SIZE];
    int sender_id;
    int is_read;
} Message;

// 配置结构体
typedef struct {
    int max_connections;
    int timeout_seconds;
    char server_name[SMALL_BUFFER_SIZE];
} SystemConfig;

/* ========== 全局变量声明 ========== */

// 用户数组（在 globals.c 中定义）
extern UserInfo g_users[MAX_USERS];
extern int g_user_count;

// 消息队列
extern Message g_messages[MAX_MESSAGES];
extern int g_message_count;

// 系统配置
extern SystemConfig g_system_config;

// 全局标志
extern int g_is_initialized;
extern int g_error_code;

/* ========== 函数声明 ========== */

// 初始化函数
void initialize_system(void);
void cleanup_system(void);

// 用户管理函数
int add_user(const char* username, int age);
UserInfo* get_user_by_id(int user_id);
int validate_user_index(int index);

// 消息处理函数
int send_message(int sender_id, const char* content);
Message* get_message_by_id(int message_id);

// 工具函数
int safe_string_copy(char* dest, const char* src, int dest_size);
int calculate_hash(const char* str);

#endif /* GLOBAL_CONFIG_H */

