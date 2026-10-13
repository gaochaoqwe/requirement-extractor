/**
 * 测试文件：内存释放后使用问题
 * 对应规则：GJB_R_01_06_16 - 禁止使用已被释放了的内存空间
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 正常的内存管理
void normal_memory_usage() {
    char *buffer = (char*)malloc(100);
    
    if (buffer != NULL) {
        strcpy(buffer, "Hello, World!");
        printf("Normal usage: %s\n", buffer);
        free(buffer);
        buffer = NULL;  // 好习惯：释放后置空
    }
}

// 存在内存释放后使用问题的函数
void problematic_memory_usage() {
    char *data = (char*)malloc(50);
    
    if (data != NULL) {
        strcpy(data, "Test data");
        printf("Before free: %s\n", data);
        
        // 释放内存
        free(data);
        
        // 问题1：释放后仍然使用 - Use after free
        printf("After free: %s\n", data);  // 危险！使用已释放的内存
        
        // 问题2：释放后写入
        strcpy(data, "New data");  // 危险！向已释放的内存写入
        
        // 问题3：重复释放
        free(data);  // 危险！重复释放同一块内存
    }
}

// 更复杂的内存管理问题
void complex_memory_issue() {
    int *numbers = (int*)malloc(10 * sizeof(int));
    int *backup = numbers;  // 保存指针副本
    
    if (numbers != NULL) {
        // 初始化数组
        for (int i = 0; i < 10; i++) {
            numbers[i] = i * i;
        }
        
        // 释放内存
        free(numbers);
        numbers = NULL;
        
        // 问题：通过备份指针访问已释放的内存
        printf("Accessing freed memory: %d\n", backup[0]);  // 危险！
        
        // 问题：修改已释放的内存
        backup[5] = 999;  // 危险！
    }
}

// 函数返回已释放的内存指针
char* return_freed_pointer() {
    char *temp = (char*)malloc(20);
    
    if (temp != NULL) {
        strcpy(temp, "temporary");
        free(temp);  // 释放内存
        return temp; // 问题：返回已释放的指针
    }
    
    return NULL;
}

int main() {
    printf("Testing memory usage after free...\n");
    
    normal_memory_usage();
    problematic_memory_usage();  // 这个函数包含use-after-free问题
    complex_memory_issue();      // 这个函数也包含内存问题
    
    // 使用返回的已释放指针
    char *bad_ptr = return_freed_pointer();
    if (bad_ptr != NULL) {
        printf("Using returned freed pointer: %s\n", bad_ptr);  // 危险！
    }
    
    return 0;
}
