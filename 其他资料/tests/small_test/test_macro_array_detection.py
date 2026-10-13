#!/usr/bin/env python3
"""
测试宏定义和数组变量识别功能
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.staticAnalysis.service.ai.parser.function_parser import (
    extract_macros_from_code, extract_arrays_from_code, extract_functions_from_code
)
from app.staticAnalysis.service.ai.parser.global_var_parser import extract_globals_from_code
from app.staticAnalysis.service.ai.parser.smart_global_detector import detect_actual_global_usage

def test_macro_detection():
    """测试宏定义识别"""
    print("=== 测试宏定义识别 ===")
    
    # 读取测试文件
    test_files = [
        'test_macros_arrays.h',
        'test_macros_arrays.c'
    ]
    
    all_macros = {}
    
    for test_file in test_files:
        file_path = os.path.join(os.path.dirname(__file__), test_file)
        if not os.path.exists(file_path):
            print(f"警告: 测试文件 {test_file} 不存在")
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        macros = extract_macros_from_code(code, 'c')
        print(f"\n文件 {test_file} 中找到 {len(macros)} 个宏定义:")
        
        for macro in macros:
            print(f"  - {macro['name']} (第{macro['line']}行): {macro['code'][:50]}...")
            all_macros[macro['name']] = {
                'file': test_file,
                'line': macro['line'],
                'code': macro['code'],
                'type': 'macro'
            }
    
    print(f"\n总共找到 {len(all_macros)} 个唯一宏定义: {list(all_macros.keys())}")
    return all_macros

def test_array_detection():
    """测试数组变量识别"""
    print("\n=== 测试数组变量识别 ===")
    
    # 读取测试文件
    test_files = [
        'test_macros_arrays.h',
        'test_macros_arrays.c'
    ]
    
    all_arrays = {}
    
    for test_file in test_files:
        file_path = os.path.join(os.path.dirname(__file__), test_file)
        if not os.path.exists(file_path):
            print(f"警告: 测试文件 {test_file} 不存在")
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        arrays = extract_arrays_from_code(code, 'c')
        print(f"\n文件 {test_file} 中找到 {len(arrays)} 个数组变量:")
        
        for array in arrays:
            print(f"  - {array['name']} (第{array['line']}行): {array['code'][:50]}...")
            all_arrays[array['name']] = {
                'file': test_file,
                'line': array['line'],
                'code': array['code'],
                'type': 'array'
            }
    
    print(f"\n总共找到 {len(all_arrays)} 个唯一数组变量: {list(all_arrays.keys())}")
    return all_arrays

def test_global_var_detection():
    """测试全局变量识别"""
    print("\n=== 测试全局变量识别 ===")
    
    # 读取测试文件
    test_files = [
        'test_macros_arrays.h',
        'test_macros_arrays.c'
    ]
    
    all_globals = {}
    
    for test_file in test_files:
        file_path = os.path.join(os.path.dirname(__file__), test_file)
        if not os.path.exists(file_path):
            print(f"警告: 测试文件 {test_file} 不存在")
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        globals_vars = extract_globals_from_code(code, 'c')
        print(f"\n文件 {test_file} 中找到 {len(globals_vars)} 个全局变量:")
        
        for gvar in globals_vars:
            print(f"  - {gvar['name']} (第{gvar['line']}行): {gvar['code'][:50]}...")
            all_globals[gvar['name']] = {
                'file': test_file,
                'line': gvar['line'],
                'code': gvar['code'],
                'type': 'variable'
            }
    
    print(f"\n总共找到 {len(all_globals)} 个唯一全局变量: {list(all_globals.keys())}")
    return all_globals

def test_function_usage_detection():
    """测试函数中的使用情况检测"""
    print("\n=== 测试函数中的使用情况检测 ===")
    
    # 读取测试文件
    test_file = 'test_macros_arrays.c'
    file_path = os.path.join(os.path.dirname(__file__), test_file)
    
    if not os.path.exists(file_path):
        print(f"警告: 测试文件 {test_file} 不存在")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    
    # 提取所有函数
    functions = extract_functions_from_code(code, 'c')
    print(f"\n在 {test_file} 中找到 {len(functions)} 个函数")
    
    # 收集所有全局项目（变量、宏、数组）
    all_globals = test_global_var_detection()
    all_macros = test_macro_detection()
    all_arrays = test_array_detection()
    
    # 合并所有全局项目
    all_global_items = {}
    all_global_items.update(all_globals)
    all_global_items.update(all_macros)
    all_global_items.update(all_arrays)
    
    print(f"\n总共有 {len(all_global_items)} 个全局项目可供检测")
    
    # 测试每个函数中使用的全局项目
    for func in functions:
        print(f"\n--- 分析函数: {func['function_name']} ---")
        used_items = detect_actual_global_usage(func['source_code'], all_global_items, 'c')
        print(f"使用的全局项目: {used_items}")
        
        # 按类型分组显示
        used_vars = [item for item in used_items if all_global_items[item]['type'] == 'variable']
        used_macros = [item for item in used_items if all_global_items[item]['type'] == 'macro']
        used_arrays = [item for item in used_items if all_global_items[item]['type'] == 'array']
        
        if used_vars:
            print(f"  使用的变量: {used_vars}")
        if used_macros:
            print(f"  使用的宏: {used_macros}")
        if used_arrays:
            print(f"  使用的数组: {used_arrays}")
        
        if not used_items:
            print("  未使用任何全局项目")

def main():
    """主测试函数"""
    print("开始测试宏定义和数组变量识别功能")
    print("=" * 50)
    
    try:
        # 测试各种识别功能
        test_macro_detection()
        test_array_detection()
        test_global_var_detection()
        test_function_usage_detection()
        
        print("\n" + "=" * 50)
        print("所有测试完成!")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 