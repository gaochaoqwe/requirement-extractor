/**
 * 测试文件：未初始化变量使用问题
 * 对应规则：GJB_R_01_11_01 - 变量禁止未赋值就使用
 */
#include <stdio.h>
#include <stdlib.h>

// 正常的变量初始化和使用
void normal_variable_usage() {
    int initialized_var = 42;
    char initialized_char = 'A';
    float initialized_float = 3.14f;
    
    printf("Initialized values: %d, %c, %.2f\n", 
           initialized_var, initialized_char, initialized_float);
}

// 存在未初始化变量使用问题的函数
void problematic_variable_usage() {
    int uninitialized_int;     // 未初始化
    char uninitialized_char;   // 未初始化
    float uninitialized_float; // 未初始化
    
    // 问题1：直接使用未初始化的变量
    printf("Uninitialized int: %d\n", uninitialized_int);  // 危险！
    
    // 问题2：在计算中使用未初始化变量
    int result = uninitialized_int + 10;  // 危险！
    printf("Result with uninitialized: %d\n", result);
    
    // 问题3：条件判断中使用未初始化变量
    if (uninitialized_char > 'A') {  // 危险！
        printf("Uninitialized char is greater than A\n");
    }
    
    // 问题4：数组操作中使用未初始化变量作为索引
    int array[10] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9};
    int bad_index;  // 未初始化
    printf("Array element: %d\n", array[bad_index]);  // 危险！可能越界
}

// 结构体中的未初始化问题
struct TestStruct {
    int value;
    char name[20];
    float ratio;
};

void struct_initialization_issue() {
    struct TestStruct test_struct;  // 未初始化
    
    // 问题：使用未初始化的结构体成员
    printf("Struct value: %d\n", test_struct.value);  // 危险！
    printf("Struct name: %s\n", test_struct.name);    // 危险！
    
    // 部分初始化，但仍有问题
    test_struct.value = 100;
    // test_struct.name 和 test_struct.ratio 仍未初始化
    printf("Struct ratio: %.2f\n", test_struct.ratio);  // 危险！
}

// 指针未初始化问题
void pointer_initialization_issue() {
    int *uninitialized_ptr;  // 未初始化的指针
    
    // 问题1：解引用未初始化的指针
    printf("Pointer value: %d\n", *uninitialized_ptr);  // 危险！
    
    // 问题2：向未初始化的指针写入
    *uninitialized_ptr = 42;  // 危险！
    
    // 问题3：使用未初始化指针进行内存操作
    free(uninitialized_ptr);  // 危险！
}

// 循环中的未初始化问题
void loop_initialization_issue() {
    int sum;  // 未初始化
    
    // 问题：在累加中使用未初始化的变量
    for (int i = 0; i < 10; i++) {
        sum += i;  // 危险！sum未初始化
    }
    
    printf("Sum: %d\n", sum);
}

// 看起来像未初始化但实际已初始化的情况（误报场景）
void false_positive_initialization() {
    int value;
    
    // 通过条件分支确保初始化
    int condition = 1;
    if (condition) {
        value = 100;  // 在使用前已初始化
    } else {
        value = 200;  // 所有分支都初始化了
    }
    
    // 这里使用value是安全的，因为所有代码路径都已初始化
    printf("Value is initialized: %d\n", value);  // 安全，已初始化
    
    // 另一个看起来可疑但安全的情况
    int result;
    result = 42;  // 在声明后立即初始化
    printf("Result: %d\n", result);  // 安全
}

int main() {
    printf("Testing uninitialized variable usage...\n");
    
    normal_variable_usage();
    problematic_variable_usage();  // 包含未初始化变量问题
    struct_initialization_issue(); // 包含结构体初始化问题
    pointer_initialization_issue(); // 包含指针初始化问题
    loop_initialization_issue();   // 包含循环中的初始化问题
    false_positive_initialization();  // 看起来可疑但实际安全
    
    return 0;
}
