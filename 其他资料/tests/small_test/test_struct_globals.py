#!/usr/bin/env python3
"""
测试结构体全局变量识别功能
"""
import sys
import os
import re

# 简化的解析函数，用于测试
def simple_extract_globals(code: str):
    """简化的全局变量提取函数"""
    results = []
    
    # 移除注释
    code_no_comment = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    code_no_comment = re.sub(r'//.*$', '', code_no_comment, flags=re.MULTILINE)
    
    # 先处理跨行的匿名结构体/联合体
    # 匹配 struct { ... } var_name; 或 union { ... } var_name;
    anonymous_pattern = r'(?:static\s+|extern\s+|const\s+|volatile\s+)*(?:struct|union)\s*\{[^}]*\}\s*([a-zA-Z_]\w*)\s*(?:=\s*[^;]+)?\s*;'
    anonymous_matches = re.finditer(anonymous_pattern, code_no_comment, re.DOTALL)
    
    for match in anonymous_matches:
        var_name = match.group(1)
        if var_name:
            # 计算行号
            line_num = code_no_comment[:match.start()].count('\n') + 1
            # 获取匹配的代码，替换换行符为空格以便显示
            matched_code = match.group(0).strip()
            matched_code = re.sub(r'\s+', ' ', matched_code)  # 压缩空白字符
            
            results.append({
                "name": var_name,
                "code": matched_code,
                "line": line_num
            })
    
    lines = code_no_comment.splitlines()
    brace_depth = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
            
        # 跟踪大括号深度
        brace_depth += line.count('{') - line.count('}')
        
        # 只在顶层（brace_depth==0）处理
        if brace_depth > 0:
            continue
            
        # 跳过预处理指令
        if stripped.startswith('#'):
            continue
            
        # 跳过函数声明/定义（包含括号的行）
        if '(' in stripped and ')' in stripped and not stripped.endswith(';'):
            continue
            
        # 全局变量匹配模式
        patterns = [
            # 基本类型：int var = value; static int var; extern int var;
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*(?:unsigned\s+|signed\s+)?(?:int|char|short|long|float|double|bool|void|size_t|uint32_t|int32_t)\s*\*?\s*([a-zA-Z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:=\s*[^;]+)?\s*;',
            
            # 复合类型：struct Type var; union Type var; enum Type var;
            r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*(?:struct|union|enum)\s+\w+\s*\*?\s*([a-zA-Z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:=\s*[^;]+)?\s*;',
            
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
                    # 检查是否已经被匿名结构体处理过
                    if not any(r['name'] == var_name for r in results):
                        results.append({
                            "name": var_name,
                            "code": stripped,
                            "line": i + 1
                        })
                break
    
    return results

def test_struct_globals():
    """测试结构体全局变量识别"""
    print("=== 测试结构体全局变量识别 ===")
    
    # 测试代码
    test_code = '''
// 结构体定义
struct Point {
    int x;
    int y;
};

struct Config {
    char name[64];
    int value;
    bool enabled;
};

// 全局结构体变量
struct Point origin;                    // 基本结构体变量
static struct Point center = {0, 0};    // 静态结构体变量，带初始化
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

    # 提取全局变量
    globals_found = simple_extract_globals(test_code)
    
    print(f"找到 {len(globals_found)} 个全局变量：")
    for g in globals_found:
        print(f"  - {g['name']} (第{g['line']}行): {g['code']}")
    
    # 预期的全局变量
    expected_globals = [
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
    
    found_names = [g['name'] for g in globals_found]
    
    print(f"\n期望找到的全局变量 ({len(expected_globals)} 个):")
    for name in expected_globals:
        print(f"  - {name}")
    
    print(f"\n实际找到的全局变量 ({len(found_names)} 个):")
    for name in found_names:
        print(f"  - {name}")
    
    # 检查结果
    missing = set(expected_globals) - set(found_names)
    extra = set(found_names) - set(expected_globals)
    
    if not missing and not extra:
        print("\n✅ 结构体全局变量识别测试通过！")
        return True
    else:
        print(f"\n❌ 结构体全局变量识别测试失败：")
        if missing:
            print(f"  缺失的变量: {missing}")
        if extra:
            print(f"  多余的变量: {extra}")
        return False

if __name__ == "__main__":
    test_struct_globals() 