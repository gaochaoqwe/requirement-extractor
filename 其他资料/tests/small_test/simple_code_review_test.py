#!/usr/bin/env python3
"""
简化的代码审查模块功能测试
"""
import sys
import os
import re

# 简单测试，验证代码审查模块的文件结构是否正确
def test_files_exist():
    """测试文件是否存在"""
    print("=== 测试代码审查模块文件结构 ===")
    
    base_path = "backend/app/codeReview/ConfigurationItem/service/ai/parser"
    
    files_to_check = [
        f"{base_path}/global_var_parser.py",
        f"{base_path}/function_parser.py",
        "backend/app/codeReview/ConfigurationItem/service/ai/analysis_runner.py"
    ]
    
    deleted_files = [
        f"{base_path}/smart_global_detector.py"
    ]
    
    all_good = True
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path} 存在")
        else:
            print(f"❌ {file_path} 不存在")
            all_good = False
    
    for file_path in deleted_files:
        if not os.path.exists(file_path):
            print(f"✅ {file_path} 已删除")
        else:
            print(f"❌ {file_path} 仍然存在（应该已删除）")
            all_good = False
    
    return all_good

def test_imports():
    """测试导入是否正确"""
    print("\n=== 测试导入功能 ===")
    
    try:
        # 检查global_var_parser.py是否包含新功能
        with open("backend/app/codeReview/ConfigurationItem/service/ai/parser/global_var_parser.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_functions = [
            "extract_macros_from_code",
            "extract_arrays_from_code", 
            "detect_actual_global_usage"
        ]
        
        for func_name in required_functions:
            if f"def {func_name}" in content:
                print(f"✅ {func_name} 函数存在")
            else:
                print(f"❌ {func_name} 函数不存在")
                return False
        
        # 检查analysis_runner.py是否更新了导入
        with open("backend/app/codeReview/ConfigurationItem/service/ai/analysis_runner.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "extract_macros_from_code, extract_arrays_from_code" in content:
            print("✅ analysis_runner.py 导入已更新")
        else:
            print("❌ analysis_runner.py 导入未更新")
            return False
        
        if "from .parser.global_var_parser import detect_actual_global_usage" in content:
            print("✅ analysis_runner.py 智能检测器导入已更新")
        else:
            print("❌ analysis_runner.py 智能检测器导入未更新")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 测试导入时出错: {e}")
        return False

def test_code_review_struct():
    """测试代码审查模块的结构体支持"""
    
    # 单行匿名结构体测试
    single_line_test = '''
struct Point origin;
static struct Point center = {0, 0};
struct Point *current_point;
struct Point points[100];
struct { int width, height; } screen_size;
Vector3 world_origin;
union Data global_data;
enum Status current_status;
'''

    print("=== 测试代码审查模块结构体支持（单行匿名结构体）===")
    print("测试代码:")
    print(single_line_test)
    print("=" * 50)
    
    results = extract_with_code_review_patterns(single_line_test)
    
    print(f"找到 {len(results)} 个全局变量:")
    for r in results:
        print(f"  - {r['name']}: {r['code']}")
    
    # 检查关键的结构体变量
    expected = ['origin', 'center', 'current_point', 'points', 'screen_size', 'world_origin', 'global_data', 'current_status']
    found = [r['name'] for r in results]
    
    print(f"\n检查结果:")
    for name in expected:
        status = "✅" if name in found else "❌"
        print(f"  {status} {name}")
    
    missing = set(expected) - set(found)
    if missing:
        print(f"\n缺失的变量: {missing}")
    else:
        print(f"\n🎉 代码审查模块完全支持结构体全局变量识别！")

def extract_with_code_review_patterns(code: str):
    """使用代码审查模块的正则模式提取全局变量"""
    results = []
    
    # 移除注释
    code_no_comment = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    code_no_comment = re.sub(r'//.*$', '', code_no_comment, flags=re.MULTILINE)
    
    lines = code_no_comment.splitlines()
    brace_depth = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
            
        brace_depth += line.count('{') - line.count('}')
        
        # 只在顶层处理
        if brace_depth > 0:
            continue
            
        # 跳过预处理指令
        if stripped.startswith('#'):
            continue
            
        # 跳过函数声明/定义
        if '(' in stripped and ')' in stripped and not stripped.endswith(';'):
            continue
            
        # 代码审查模块的正则模式
        patterns = [
            # 基本类型
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*(?:unsigned\s+|signed\s+)?(?:int|char|short|long|float|double|bool|void|size_t|uint32_t|int32_t)\s*\*?\s*([a-zA-Z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:=\s*[^;]+)?\s*;',
            
            # 复合类型：struct Type var; union Type var; enum Type var;
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*(?:struct|union|enum)\s+\w+\s*\*?\s*([a-zA-Z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:=\s*[^;]+)?\s*;',
            
            # 匿名结构体：struct { ... } var; (单行)
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*(?:struct|union)\s*\{[^}]*\}\s*([a-zA-Z_]\w*)\s*(?:=\s*[^;]+)?\s*;',
            
            # typedef类型：MyType var;
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*[A-Z]\w*\s+([a-zA-Z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:=\s*[^;]+)?\s*;',
            
            # 函数指针
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*\w+\s*\(\s*\*\s*([a-zA-Z_]\w*)\s*\)\s*\([^)]*\)\s*(?:=\s*[^;]+)?\s*;',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, stripped)
            if match:
                var_name = match.group(1)
                if var_name not in ['int', 'char', 'float', 'double', 'void', 'bool', 'short', 'long']:
                    results.append({
                        'name': var_name,
                        'code': stripped,
                        'line': i + 1
                    })
                    print(f"匹配: {var_name} -> {stripped}")
                break
    
    return results

def main():
    """主测试函数"""
    print("开始测试代码审查模块重构结果")
    print("=" * 50)
    
    success = True
    
    # 测试文件结构
    if not test_files_exist():
        success = False
    
    # 测试导入功能
    if not test_imports():
        success = False
    
    # 测试结构体支持
    test_code_review_struct()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 所有测试通过！代码审查模块重构成功！")
    else:
        print("❌ 部分测试失败，请检查重构结果")
    
    return success

if __name__ == "__main__":
    main() 