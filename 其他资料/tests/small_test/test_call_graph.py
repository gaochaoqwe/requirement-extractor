print("脚本已启动")

import os
from pathlib import Path
from tree_sitter import Parser
from tree_sitter_languages import get_language

def _get_parser(lang: str) -> Parser:
    """获取语言解析器"""
    language = get_language(lang)
    parser = Parser()
    parser.set_language(language)
    return parser

def _node_text(node, code_bytes: bytes) -> str:
    """获取节点对应的源代码文本"""
    return code_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="ignore")

def _extract_callee_name(node, code_bytes: bytes):
    """提取被调用函数的名称"""
    print(f"\n解析调用节点: {node.type}")
    print(f"节点内容: {_node_text(node, code_bytes)}")
    
    while node is not None:
        print(f"  当前节点类型: {node.type}")
        if node.type in {"identifier", "field_identifier"}:
            name = _node_text(node, code_bytes)
            print(f"  找到标识符: {name}")
            return name
        if node.type in {"field_expression", "pointer_expression", "member_expression"}:
            print(f"  处理字段/指针/成员表达式")
            # 对于 obj.method() 或 ptr->method() 的情况
            field = node.child_by_field_name("field")
            if field and field.type in {"identifier", "field_identifier"}:
                name = _node_text(field, code_bytes)
                print(f"  找到成员函数: {name}")
                return name
            # 尝试从子节点中查找标识符
            for child in node.children:
                if child.type in {"identifier", "field_identifier"}:
                    name = _node_text(child, code_bytes)
                    print(f"  从子节点找到标识符: {name}")
                    return name
            node = field
            continue
        if node.type in {"qualified_identifier", "scoped_identifier"} and node.child_count:
            print(f"  处理限定标识符")
            # Get the last part of ns::func -> func
            name_node = node.child_by_field_name("name")
            if name_node:
                node = name_node
            else: # Fallback for other structures
                node = node.children[-1]
            continue
        
        # Fallback for other wrappers
        if node.child_count > 0:
            node = node.children[0]
        else:
            break
            
    print("  ! 未能提取标识符")
    return None

def _extract_function_name(node, code_bytes: bytes) -> str:
    """提取函数名称，包括类成员函数"""
    if node.type == "function_definition":
        declarator = node.child_by_field_name("declarator")
        if declarator:
            # 处理类成员函数
            if declarator.type == "function_declarator":
                # 获取函数名
                name_node = declarator.child_by_field_name("declarator")
                if name_node and name_node.type in {"identifier", "field_identifier"}:
                    return _node_text(name_node, code_bytes)
    return None

def build_call_graph(code: str, language: str = "c") -> dict:
    """构建函数调用图"""
    parser = _get_parser(language)
    tree = parser.parse(code.encode("utf-8"))
    root = tree.root_node
    code_bytes = code.encode("utf-8")

    # 收集函数定义
    defined_funcs = {}
    stack_nodes = [root]
    while stack_nodes:
        node = stack_nodes.pop()
        if node.type == "function_definition":
            func_name = _extract_function_name(node, code_bytes)
            if func_name:
                defined_funcs[func_name] = node
                print(f"找到函数定义: {func_name}")
        stack_nodes.extend(reversed(node.children))

    # 构建调用图
    call_graph = {name: set() for name in defined_funcs}
    print(f"已定义函数: {list(defined_funcs.keys())}")

    # 分析每个函数体中的调用
    for func_name, def_node in defined_funcs.items():
        body = def_node.child_by_field_name("body")
        if body is None:
            continue
            
        print(f"\n分析函数体: {func_name}")
        stack = [body]
        while stack:
            n = stack.pop()
            if n.type == "call_expression":
                print(f"\n找到调用表达式: {_node_text(n, code_bytes)[:100]}...")
                callee = n.child_by_field_name("function")
                if callee is not None:
                    print(f"  被调用者节点类型: {callee.type}")
                    print(f"  被调用者节点内容: {_node_text(callee, code_bytes)}")
                    called_name = _extract_callee_name(callee, code_bytes)
                    if called_name:
                        print(f"  => 函数 {func_name} 调用了 {called_name}")
                        call_graph[func_name].add(called_name)
                    else:
                        print(f"  ! 无法提取调用函数名")
            stack.extend(n.children)
    
    print(f"\n最终调用图: {call_graph}")
    return call_graph

def test_call_graph():
    try:
        # 获取测试文件路径
        current_dir = Path(__file__).parent
        test_file = current_dir / "cpp_class_calls.cpp"
        
        # 读取测试文件内容
        with open(test_file, 'r', encoding='utf-8') as f:
            code = f.read()
        
        print("\n=== 开始测试函数调用图构建 ===")
        print(f"测试文件: {test_file}")
        print("\n文件内容:")
        print("=" * 50)
        print(code)
        print("=" * 50)
        
        # 构建调用图
        call_graph = build_call_graph(code, language="cpp")
        
        # 验证结果
        print("\n=== 调用图分析结果 ===")
        for func_name, called_funcs in call_graph.items():
            print(f"\n函数: {func_name}")
            print(f"调用的函数: {list(called_funcs)}")
        
        # 验证关键函数调用
        expected_calls = {
            "perform_operations": {"add", "subtract", "multiply"},
            "add": set(),
            "subtract": set(),
            "multiply": set()
        }
        
        print("\n=== 验证结果 ===")
        success = True
        for func, expected in expected_calls.items():
            actual = call_graph.get(func, set())
            if actual != expected:
                print(f"❌ {func} 的调用关系不匹配:")
                print(f"  期望: {expected}")
                print(f"  实际: {actual}")
                success = False
            else:
                print(f"✅ {func} 的调用关系正确")
        
        if success:
            print("\n✅ 所有测试通过！")
        else:
            print("\n❌ 测试失败！")
    except Exception as e:
        import traceback
        print("发生异常：", e)
        traceback.print_exc()

if __name__ == "__main__":
    test_call_graph() 