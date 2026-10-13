#!/usr/bin/env python3
"""
测试代码审查模块的宏定义和数组变量识别功能
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

def test_code_review_module():
    """测试代码审查模块功能"""
    try:
        from app.codeReview.ConfigurationItem.service.ai.parser.global_var_parser import (
            extract_macros_from_code, extract_arrays_from_code, extract_globals_from_code, detect_actual_global_usage
        )
        
        # 测试代码
        test_code = '''
#define MAX_SIZE 1024
#define SQUARE(x) ((x) * (x))

int global_var = 0;
int global_array[MAX_SIZE];
static char static_buffer[256];

void test_function() {
    int local_var = 0;
    char local_array[10];
    
    global_var = SQUARE(5);
    global_array[0] = MAX_SIZE;
    static_buffer[0] = 'A';
}
'''

        print("=== 测试代码审查模块功能 ===")
        
        # 测试提取功能
        macros = extract_macros_from_code(test_code, 'c')
        arrays = extract_arrays_from_code(test_code, 'c')
        globals_vars = extract_globals_from_code(test_code, 'c')

        print(f'宏定义 ({len(macros)} 个): {[m["name"] for m in macros]}')
        print(f'数组变量 ({len(arrays)} 个): {[a["name"] for a in arrays]}')
        print(f'全局变量 ({len(globals_vars)} 个): {[g["name"] for g in globals_vars]}')

        # 测试智能检测
        all_items = {}
        for m in macros:
            all_items[m['name']] = {'file': 'test.c', 'line': m['line'], 'code': m['code'], 'type': 'macro'}
        for a in arrays:
            all_items[a['name']] = {'file': 'test.c', 'line': a['line'], 'code': a['code'], 'type': 'array'}
        for g in globals_vars:
            all_items[g['name']] = {'file': 'test.c', 'line': g['line'], 'code': g['code'], 'type': 'variable'}

        function_code = '''
void test_function() {
    int local_var = 0;
    char local_array[10];
    
    global_var = SQUARE(5);
    global_array[0] = MAX_SIZE;
    static_buffer[0] = 'A';
}
'''

        used_items = detect_actual_global_usage(function_code, all_items, 'c')
        print(f'函数中使用的全局项目 ({len(used_items)} 个): {used_items}')
        
        # 验证结果
        expected_used = ['global_var', 'SQUARE', 'global_array', 'MAX_SIZE', 'static_buffer']
        if set(used_items) == set(expected_used):
            print("✅ 智能检测功能正常!")
        else:
            print(f"❌ 智能检测结果不符合预期")
            print(f"   期望: {expected_used}")
            print(f"   实际: {used_items}")

        print("代码审查模块测试完成!")
        return True
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_code_review_module() 