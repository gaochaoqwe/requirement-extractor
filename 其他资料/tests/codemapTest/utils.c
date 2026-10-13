#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "utils.h"

// 打印欢迎消息
void print_welcome_message() {
    printf("欢迎使用代码地图测试程序！\n");
    printf("这个程序用于测试函数调用关系的可视化。\n");
    log_message("程序启动");
}

// 清理资源
void cleanup_resources() {
    printf("正在清理资源...\n");
    log_message("资源清理完成");
    printf("程序结束。\n");
}

// 记录日志消息
// BUG8: 没有检查message是否为NULL，可能导致空指针解引用
void log_message(const char* message) {
    char* timestamp = get_current_time();
    // BUG9: 如果message为NULL，这里会崩溃
    printf("[LOG %s] %s\n", timestamp, message);
    free(timestamp);
}

// 验证输入值
int validate_input(int value) {
    if (value < 0) {
        log_message("警告：输入值为负数");
        return 0;
    }
    if (value > 1000) {
        log_message("警告：输入值过大");
        return 0;
    }
    return 1;
}

// 获取当前时间字符串
// BUG10: 返回的指针需要调用者free，但没有在注释中说明，容易造成内存泄漏
// BUG11: 没有检查malloc是否成功
char* get_current_time() {
    time_t now = time(NULL);
    // BUG12: malloc可能返回NULL，但这里没有检查
    char* timestr = malloc(20);
    // BUG13: 如果malloc失败，这里会导致空指针解引用
    strftime(timestr, 20, "%H:%M:%S", localtime(&now));
    return timestr;
} 