"""
测试 CodeAnalysisAgentV2 的工具调用功能

这个脚本会依次测试所有工具，确保它们能正确工作
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.staticAnalysis.filter.services.code_analysis_agent_v2 import CodeAnalysisAgentV2


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_result(tool_name, result):
    """打印工具调用结果"""
    print(f"\n【工具】{tool_name}")
    print(f"【结果】")
    result_str = json.dumps(result, ensure_ascii=False, indent=2)
    # 限制输出长度
    if len(result_str) > 2000:
        print(result_str[:2000] + "\n... (结果过长，已截断)")
    else:
        print(result_str)
    print("-" * 80)


def test_tools():
    """测试所有工具"""
    
    print_section("初始化测试环境")
    
    # 设置代码库路径
    codebase_path = Path(__file__).parent / "staticanalysisdiff"
    print(f"代码库路径: {codebase_path}")
    print(f"代码库是否存在: {codebase_path.exists()}")
    
    if not codebase_path.exists():
        print("❌ 错误：代码库路径不存在！")
        return
    
    # 初始化Agent（内部会自动创建logger和ai_client）
    agent = CodeAnalysisAgentV2("test_session", str(codebase_path))
    
    print(f"✅ Agent初始化成功，共 {len(agent.tools)} 个工具")
    
    # =================================================================
    # 测试 1: get_file_outline - 获取文件大纲
    # =================================================================
    print_section("测试 1: get_file_outline - 获取文件大纲")
    result = agent._tool_get_file_outline("cwe_test_cases.c")
    print_result("get_file_outline", result)
    
    if "error" not in result:
        print(f"✅ 成功：文件共 {result['total_lines']} 行")
        print(f"   找到 {result['function_count']} 个函数")
        print(f"   函数列表前5个:")
        for func in result['functions'][:5]:
            print(f"     - {func['name']} (第{func['line']}行): {func['signature']}")
    else:
        print(f"❌ 错误: {result['error']}")
    
    # =================================================================
    # 测试 2: read_file_range - 按行范围读取
    # =================================================================
    print_section("测试 2: read_file_range - 按行范围读取")
    result = agent._tool_read_file_range("cwe_test_cases.c", 1, 50)
    print_result("read_file_range", result)
    
    if "error" not in result:
        print(f"✅ 成功：读取了第 {result['start_line']}-{result['end_line']} 行")
        print(f"   文件总行数: {result['total_lines']}")
    else:
        print(f"❌ 错误: {result['error']}")
    
    # =================================================================
    # 测试 3: get_function_context - 获取函数上下文
    # =================================================================
    print_section("测试 3: get_function_context - 获取函数上下文")
    result = agent._tool_get_function_context("cwe_test_cases.c", 46)
    print_result("get_function_context", result)
    
    if "error" not in result:
        print(f"✅ 成功：找到函数 {result.get('function_name', '未知')}")
        print(f"   函数范围: 第{result['function_start']}-{result['function_end']}行")
    else:
        print(f"❌ 错误: {result['error']}")
    
    # =================================================================
    # 测试 4: get_variable_usage - 追踪变量使用
    # =================================================================
    print_section("测试 4: get_variable_usage - 追踪变量使用")
    result = agent._tool_get_variable_usage("cwe_test_cases.c", "buffer")
    print_result("get_variable_usage", result)
    
    if "error" not in result:
        print(f"✅ 成功：找到 {result['total_usages']} 处使用")
        print(f"   搜索范围: {result['search_range']}")
        print(f"   使用位置前5个:")
        for usage in result['usages'][:5]:
            print(f"     - 第{usage['line_number']}行 ({usage['type']}): {usage['content'][:60]}")
    else:
        print(f"❌ 错误: {result['error']}")
    
    # =================================================================
    # 测试 5: search_code - 搜索代码
    # =================================================================
    print_section("测试 5: search_code - 搜索代码")
    result = agent._tool_search_code("malloc", "*.c")
    print_result("search_code", result)
    
    if "error" not in result:
        print(f"✅ 成功：找到 {result['count']} 处匹配")
        print(f"   匹配位置前5个:")
        for match in result['results'][:5]:
            print(f"     - {match['file']}:{match['line']} - {match['content'][:60]}")
    else:
        print(f"❌ 错误: {result['error']}")
    
    # =================================================================
    # 测试 6: get_call_graph - 获取调用关系图
    # =================================================================
    print_section("测试 6: get_call_graph - 获取调用关系图")
    result = agent._tool_get_call_graph("allocate_buffer_with_overflow")
    print_result("get_call_graph", result)
    
    if "error" not in result:
        print(f"✅ 成功：找到函数 {result['function_name']}")
        if result['definition']:
            print(f"   定义位置: {result['definition']['file']}:{result['definition']['line']}")
        else:
            print(f"   ⚠️  警告：未找到函数定义")
        print(f"   被 {len(result['callers'])} 个函数调用")
        print(f"   调用了 {len(result['callees'])} 个函数")
    else:
        print(f"❌ 错误: {result['error']}")
    
    # =================================================================
    # 测试 7: list_directory - 列出目录
    # =================================================================
    print_section("测试 7: list_directory - 列出目录")
    result = agent._tool_list_directory(".")
    print_result("list_directory", result)
    
    if "error" not in result:
        print(f"✅ 成功：找到 {result['count']} 个项目")
        print(f"   项目列表前10个:")
        for item in result['items'][:10]:
            item_type = item['type']
            size_info = f" ({item['size']} bytes)" if item['type'] == 'file' else ""
            print(f"     - [{item_type}] {item['name']}{size_info}")
    else:
        print(f"❌ 错误: {result['error']}")
    
    # =================================================================
    # 边界测试：大文件读取限制
    # =================================================================
    print_section("边界测试: 超大范围读取（应该被限制）")
    result = agent._tool_read_file_range("cwe_test_cases.c", 1, 1000)
    print_result("read_file_range (超大范围)", result)
    
    if "error" in result:
        print(f"✅ 成功：正确拒绝了过大的请求")
        print(f"   错误信息: {result['error']}")
    else:
        print(f"⚠️  警告：没有限制大范围读取")
    
    # =================================================================
    # 边界测试：不存在的文件
    # =================================================================
    print_section("边界测试: 读取不存在的文件")
    result = agent._tool_get_file_outline("nonexistent.c")
    print_result("get_file_outline (不存在的文件)", result)
    
    if "error" in result:
        print(f"✅ 成功：正确处理了文件不存在的情况")
        print(f"   错误信息: {result['error']}")
    else:
        print(f"❌ 错误：应该返回错误，但返回了结果")
    
    print_section("测试完成")
    print("\n所有工具测试完成！\n")


if __name__ == "__main__":
    try:
        test_tools()
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
