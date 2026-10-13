#!/usr/bin/env python3
import re

def test_struct_recognition():
    test_code = '''
struct Point {
    int x, y;
};

struct Point origin;
static struct Point center = {0, 0};
struct Point *current_point;
struct Point points[100];

struct {
    int width;
    int height;
} screen_size;

typedef struct {
    float x, y, z;
} Vector3;

Vector3 world_origin;
'''

    print("测试代码:")
    print(test_code)
    print("=" * 50)
    
    # 移除注释
    code_no_comment = re.sub(r'/\*.*?\*/', '', test_code, flags=re.DOTALL)
    code_no_comment = re.sub(r'//.*$', '', code_no_comment, flags=re.MULTILINE)
    
    print("处理后的代码:")
    print(repr(code_no_comment))
    print("=" * 50)
    
    # 先处理跨行的匿名结构体/联合体
    anonymous_pattern = r'(?:static\s+|extern\s+|const\s+|volatile\s+)*(?:struct|union)\s*\{[^}]*\}\s*([a-zA-Z_]\w*)\s*(?:=\s*[^;]+)?\s*;'
    anonymous_matches = re.finditer(anonymous_pattern, code_no_comment, re.DOTALL)
    
    results = []
    for match in anonymous_matches:
        var_name = match.group(1)
        if var_name:
            line_num = code_no_comment[:match.start()].count('\n') + 1
            matched_code = match.group(0).strip()
            matched_code = re.sub(r'\s+', ' ', matched_code)
            
            results.append({
                "name": var_name,
                "code": matched_code,
                "line": line_num,
                "type": "anonymous_struct"
            })
            print(f"匿名结构体: {var_name} -> {matched_code}")
    
    # 处理普通的结构体变量
    lines = code_no_comment.splitlines()
    brace_depth = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
            
        brace_depth += line.count('{') - line.count('}')
        
        if brace_depth > 0:
            continue
            
        if stripped.startswith('#'):
            continue
            
        if '(' in stripped and ')' in stripped and not stripped.endswith(';'):
            continue
        
        # 结构体变量模式
        struct_pattern = r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*(?:struct|union|enum)\s+\w+\s*\*?\s*([a-zA-Z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:=\s*[^;]+)?\s*;'
        match = re.match(struct_pattern, stripped)
        if match:
            var_name = match.group(1)
            if var_name and not any(r['name'] == var_name for r in results):
                results.append({
                    "name": var_name,
                    "code": stripped,
                    "line": i + 1,
                    "type": "struct_var"
                })
                print(f"结构体变量: {var_name} -> {stripped}")
        
        # typedef类型
        typedef_pattern = r'^(?:static\s+|extern\s+|const\s+|volatile\s+)*[A-Z]\w*\s+([a-zA-Z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:=\s*[^;]+)?\s*;'
        match = re.match(typedef_pattern, stripped)
        if match:
            var_name = match.group(1)
            if var_name and not any(r['name'] == var_name for r in results):
                results.append({
                    "name": var_name,
                    "code": stripped,
                    "line": i + 1,
                    "type": "typedef_var"
                })
                print(f"typedef变量: {var_name} -> {stripped}")
    
    print("=" * 50)
    print(f"总共找到 {len(results)} 个变量:")
    for r in results:
        print(f"  {r['name']} ({r['type']})")

if __name__ == "__main__":
    test_struct_recognition() 