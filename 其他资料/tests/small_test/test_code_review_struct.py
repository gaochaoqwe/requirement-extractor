#!/usr/bin/env python3
"""
测试代码审查模块的结构体全局变量识别功能
"""
import sys
import os
import re

# 复制代码审查模块的解析逻辑进行测试
def test_code_review_struct_support():
    """测试代码审查模块的结构体支持"""
    
    # 测试代码 - 包含各种结构体全局变量
    test_code = '''
// 结构体定义
struct Point {
    int x, y;
};

struct Config {
    char name[64];
    int value;
    bool enabled;
};

// 全局结构体变量
struct Point origin;                    // 基本结构体变量
static struct Point center = {0, 0};    // 静态结构体变量
extern struct Point target;             // 外部结构体变量
const struct Config default_config;     // 常量结构体变量

// 结构体指针
struct Point *current_point;            // 结构体指针
static struct Config *global_config;   // 静态结构体指针

// 结构体数组
struct Point points[100];               // 结构体数组
static struct Config configs[10];      // 静态结构体数组

// 匿名结构体
struct {
    int width;
    int height;
} screen_size;

// typedef 结构体
typedef struct {
    float x, y, z;
} Vector3;

Vector3 world_origin;                   // typedef结构体变量
Vector3 camera_pos = {0.0, 0.0, 1.0};  // typedef结构体变量，带初始化

// 联合体
union Data {
    int i;
    float f;
    char c[4];
};

union Data global_data;                 // 全局联合体变量
static union Data buffer;              // 静态联合体变量

// 枚举
enum Status {
    IDLE,
    RUNNING,
    STOPPED
};

enum Status current_status;             // 全局枚举变量

void test_function() {
    // 局部变量，不应该被识别为全局变量
    struct Point local_point;
    static struct Config local_config;  // 局部静态变量
}
'''

    print("=== 测试代码审查模块的结构体全局变量识别 ===")
    
    # 使用与代码审查模块相同的解析逻辑
    results = extract_globals_like_code_review(test_code)
    
    print(f"找到 {len(results)} 个全局变量：")
    for g in results:
        print(f"  - {g['name']} (第{g['line']}行): {g['code']}")
    
    # 预期的结构体相关全局变量
    expected_struct_vars = [
        'origin',           # struct Point origin;
        'center',           # static struct Point center = {0, 0};
        'target',           # extern struct Point target;
        'default_config',   # const struct Config default_config;
        'current_point',    # struct Point *current_point;
        'global_config',    # static struct Config *global_config;
        'points',           # struct Point points[100];
        'configs',          # static struct Config configs[10];
        'screen_size',      # struct { ... } screen_size;
        'world_origin',     # Vector3 world_origin;
        'camera_pos',       # Vector3 camera_pos = {0.0, 0.0, 1.0};
        'global_data',      # union Data global_data;
        'buffer',           # static union Data buffer;
        'current_status',   # enum Status current_status;
    ]
    
    found_names = [g['name'] for g in results]
    struct_found = [name for name in found_names if name in expected_struct_vars]
    
    print(f"\n期望的结构体相关变量 ({len(expected_struct_vars)} 个):")
    for name in expected_struct_vars:
        status = "✅" if name in found_names else "❌"
        print(f"  {status} {name}")
    
    print(f"\n实际找到的结构体相关变量 ({len(struct_found)} 个):")
    for name in struct_found:
        print(f"  ✅ {name}")
    
    # 检查结果
    missing = set(expected_struct_vars) - set(found_names)
    
    if not missing:
        print(f"\n🎉 代码审查模块完全支持结构体全局变量识别！")
        print(f"   成功识别了 {len(struct_found)}/{len(expected_struct_vars)} 个结构体相关变量")
        return True
    else:
        print(f"\n❌ 代码审查模块结构体支持不完整：")
        print(f"  缺失的变量: {missing}")
        return False


def extract_globals_like_code_review(code: str):
    """模拟代码审查模块的全局变量提取逻辑"""
    results = []
    
    # 移除注释
    code_no_comment = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    code_no_comment = re.sub(r'//.*$', '', code_no_comment, flags=re.MULTILINE)
    
    lines = code_no_comment.splitlines()
    brace_depth = 0
    paren_depth = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
            
        # 跟踪大括号和圆括号深度
        brace_depth += line.count('{') - line.count('}')
        paren_depth += line.count('(') - line.count(')')
        
        # 只在顶层（brace_depth==0）处理
        if brace_depth > 0:
            continue
            
        # 跳过预处理指令
        if stripped.startswith('#'):
            continue
            
        # 跳过函数声明/定义（包含括号的行）
        if '(' in stripped and ')' in stripped and not stripped.endswith(';'):
            continue
            
        # 改进的全局变量匹配模式（与代码审查模块相同）
        patterns = [
            # 基本类型：int var = value; static int var; extern int var;
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*(?:unsigned\s+|signed\s+)?(?:int|char|short|long|float|double|bool|void|size_t|uint32_t|int32_t)\s*\*?\s*([a-zA-Z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:=\s*[^;]+)?\s*;',
            
            # 复合类型：struct Type var; union Type var; enum Type var;
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*(?:struct|union|enum)\s+\w+\s*\*?\s*([a-zA-Z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:=\s*[^;]+)?\s*;',
            
            # 匿名结构体：struct { ... } var;
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*(?:struct|union)\s*\{[^}]*\}\s*([a-zA-Z_]\w*)\s*(?:=\s*[^;]+)?\s*;',
            
            # typedef类型：MyType var;
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*[A-Z]\w*\s+([a-zA-Z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:=\s*[^;]+)?\s*;',
            
            # 函数指针：int (*func_ptr)(int); 
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*\w+\s*\(\s*\*\s*([a-zA-Z_]\w*)\s*\)\s*\([^)]*\)\s*(?:=\s*[^;]+)?\s*;',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, stripped)
            if match:
                var_name = match.group(1)
                # 避免匹配到类型名或关键字
                if var_name not in ['int', 'char', 'float', 'double', 'void', 'bool', 'short', 'long']:
                    results.append({
                        "name": var_name,
                        "code": stripped,
                        "line": i + 1
                    })
                break
    
    return results


if __name__ == "__main__":
    test_code_review_struct_support() 