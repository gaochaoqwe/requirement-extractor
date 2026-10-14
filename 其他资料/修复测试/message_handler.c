/**
 * 消息处理模块
 * 包含真实问题3，误报问题3和4
 */
#include "global_config.h"

/* ========== 真实问题3: 缓冲区溢出（需要理解宏定义关系） ========== */

int send_message(int sender_id, const char* content) {
    if (content == NULL) {
        return -1;
    }
    
    // 检查消息队列是否已满
    if (g_message_count >= MAX_MESSAGES) {
        return -1;
    }
    
    // 创建新消息
    Message* msg = &g_messages[g_message_count];
    msg->message_id = g_message_count;
    msg->sender_id = sender_id;
    msg->is_read = 0;
    
    // 🔴 真实问题：content可能比MAX_BUFFER_SIZE大，
    // 但这里没有检查长度就直接strcpy
    safe_string_copy(msg->content, content, MAX_BUFFER_SIZE);  // 危险！可能缓冲区溢出
    
    g_message_count++;
    
    return msg->message_id;
}

/* ========== 误报3: 看起来溢出但实际安全（使用了安全函数） ========== */

int send_safe_message(int sender_id, const char* content) {
    if (content == NULL) {
        return -1;
    }
    
    if (g_message_count >= MAX_MESSAGES) {
        return -1;
    }
    
    Message* msg = &g_messages[g_message_count];
    msg->message_id = g_message_count;
    msg->sender_id = sender_id;
    msg->is_read = 0;
    
    // 这里使用了安全的复制函数（在globals.c中定义）
    // 虽然也是strcpy家族，但这个是安全的
    safe_string_copy(msg->content, content, MAX_BUFFER_SIZE);
    
    g_message_count++;
    
    return msg->message_id;
}

/* ========== 误报4: 数组访问有完整的边界检查 ========== */

Message* get_message_by_id(int message_id) {
    // 完整的边界检查
    if (message_id < 0 || message_id >= g_message_count) {
        return NULL;
    }
    
    // 双重保险
    if (message_id >= MAX_MESSAGES) {
        return NULL;
    }
    
    return &g_messages[message_id];
}

int mark_message_as_read(int message_id) {
    Message* msg = get_message_by_id(message_id);
    if (msg != NULL) {
        msg->is_read = 1;
        return 0;
    }
    return -1;
}

/* ========== 用于测试的函数 ========== */

void print_all_messages(void) {
    printf("=== All Messages ===\n");
    for (int i = 0; i < g_message_count; i++) {
        printf("Message %d: %s (from user %d, read: %d)\n",
               g_messages[i].message_id,
               g_messages[i].content,
               g_messages[i].sender_id,
               g_messages[i].is_read);
    }
}

