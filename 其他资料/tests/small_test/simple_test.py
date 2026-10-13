#!/usr/bin/env python3
"""
简化的宏定义和数组变量识别测试
"""
import sys
import os
import re

# 直接实现简化版的解析功能进行测试
def extract_macros_simple(code):
    """简化版宏定义提取"""
    macros = []
    lines = code.splitlines()
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('#define'):
            macro_lines = [lines[i]]
            original_line_num = i + 1
            
            # 处理多行宏定义
            while i < len(lines) - 1 and lines[i].rstrip().endswith('\\'):
                i += 1
                macro_lines.append(lines[i])
            
            full_macro = '\n'.join(macro_lines)
            
            # 提取宏名称
            match = re.match(r'#define\s+([a-zA-Z_]\w*)', line)
            if match:
                macro_name = match.group(1)
                macros.append({
                    'name': macro_name,
                    'code': full_macro,
                    'line': original_line_num,
                    'type': 'macro'
                })
        i += 1
    
    return macros

def extract_arrays_simple(code):
    """简化版数组变量提取"""
    arrays = []
    lines = code.splitlines()
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or '//' in stripped:
            continue
        
        # 数组声明的简单模式
        patterns = [
            r'^(?:static\s+|extern\s+|const\s+)*(?:int|char|float|double)\s+([a-zA-Z_]\w*)\s*(\[[^\]]*\])',
            r'^(?:static\s+|extern\s+|const\s+)*(?:struct|union)\s+\w+\s+([a-zA-Z_]\w*)\s*(\[[^\]]*\])',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, stripped)
            if match:
                array_name = match.group(1)
                arrays.append({
                    'name': array_name,
                    'code': stripped,
                    'line': i + 1,
                    'type': 'array'
                })
                break
    
    return arrays

def extract_globals_simple(code):
    """简化版全局变量提取"""
    globals_vars = []
    lines = code.splitlines()
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or '//' in stripped:
            continue
        
        # 全局变量声明的简单模式
        patterns = [
            r'^(?:static\s+|extern\s+|const\s+)*(?:int|char|float|double|bool)\s+([a-zA-Z_]\w*)\s*(?:=|;)',
            r'^(?:struct|union)\s+\w+\s+([a-zA-Z_]\w*)\s*(?:=|;)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, stripped)
            if match:
                var_name = match.group(1)
                # 排除数组声明
                if '[' not in stripped:
                    globals_vars.append({
                        'name': var_name,
                        'code': stripped,
                        'line': i + 1,
                        'type': 'variable'
                    })
                break
    
    return globals_vars

def test_files():
    """测试文件解析"""
    test_files = ['test_macros_arrays.h', 'test_macros_arrays.c']
    
    all_items = {}
    
    for test_file in test_files:
        file_path = os.path.join(os.path.dirname(__file__), test_file)
        if not os.path.exists(file_path):
            print(f"警告: 文件 {test_file} 不存在")
            continue
        
        print(f"\n=== 分析文件: {test_file} ===")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 提取宏定义
        macros = extract_macros_simple(code)
        print(f"宏定义 ({len(macros)} 个):")
        for macro in macros:
            print(f"  - {macro['name']} (第{macro['line']}行)")
            all_items[macro['name']] = macro
        
        # 提取数组变量
        arrays = extract_arrays_simple(code)
        print(f"数组变量 ({len(arrays)} 个):")
        for array in arrays:
            print(f"  - {array['name']} (第{array['line']}行)")
            all_items[array['name']] = array
        
        # 提取全局变量
        globals_vars = extract_globals_simple(code)
        print(f"全局变量 ({len(globals_vars)} 个):")
        for gvar in globals_vars:
            print(f"  - {gvar['name']} (第{gvar['line']}行)")
            all_items[gvar['name']] = gvar
    
    print(f"\n=== 总结 ===")
    print(f"总共找到 {len(all_items)} 个全局项目:")
    
    macros_count = sum(1 for item in all_items.values() if item['type'] == 'macro')
    arrays_count = sum(1 for item in all_items.values() if item['type'] == 'array')
    vars_count = sum(1 for item in all_items.values() if item['type'] == 'variable')
    
    print(f"  宏定义: {macros_count} 个")
    print(f"  数组变量: {arrays_count} 个")
    print(f"  全局变量: {vars_count} 个")
    
    print(f"\n所有项目列表: {list(all_items.keys())}")
    
    return all_items

def test_usage_detection(all_items):
    """测试使用情况检测"""
    print(f"\n=== 测试使用情况检测 ===")
    
    # 模拟几个函数代码
    test_functions = [
        {
            'name': 'test_macro_usage',
            'code': '''
void test_macro_usage() {
    int size = MAX_SIZE;
    int min = MIN_VALUE;
    char name[64];
    strcpy(name, DEFAULT_NAME);
    int result = SQUARE(5);
    int max_val = MAX(10, 20);
    DEBUG_PRINT("size=%d", size);
    int local_val = LOCAL_MACRO;
}'''
        },
        {
            'name': 'test_array_usage',
            'code': '''
void test_array_usage() {
    global_array[0] = 100;
    global_buffer[0] = 'A';
    global_matrix[0][0] = 3.14f;
    static_array[0] = 200;
    local_static_array[0] = 2.718;
    
    int local_array[10];
    char local_str[BUFFER_SIZE];
    local_array[0] = 1;
}'''
        }
    ]
    
    for func in test_functions:
        print(f"\n--- 分析函数: {func['name']} ---")
        used_items = []
        
        for item_name, item_info in all_items.items():
            # 简单的使用检测：在代码中查找项目名称
            if re.search(r'\b' + re.escape(item_name) + r'\b', func['code']):
                used_items.append(item_name)
        
        print(f"使用的全局项目: {used_items}")
        
        # 按类型分组
        used_macros = [item for item in used_items if all_items[item]['type'] == 'macro']
        used_arrays = [item for item in used_items if all_items[item]['type'] == 'array']
        used_vars = [item for item in used_items if all_items[item]['type'] == 'variable']
        
        if used_macros:
            print(f"  使用的宏: {used_macros}")
        if used_arrays:
            print(f"  使用的数组: {used_arrays}")
        if used_vars:
            print(f"  使用的变量: {used_vars}")

def main():
    """主函数"""
    print("开始测试宏定义和数组变量识别功能")
    print("=" * 60)
    
    try:
        all_items = test_files()
        test_usage_detection(all_items)
        
        print("\n" + "=" * 60)
        print("测试完成!")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 