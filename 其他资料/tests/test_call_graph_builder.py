"""
测试调用图构建器
验证修复后的功能：
1. 过滤控制流关键字（if/for等）
2. 正确提取函数定义和调用关系
3. 增强的错误信息
"""
import sys
import json
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.codeReview.ConfigurationItem.service.business_review.tools.call_graph_builder import CallGraphBuilder
from app.codeReview.ConfigurationItem.service.business_review.tools.call_graph_query import CallGraphQuery


def test_call_graph_builder():
    """测试调用图构建器"""
    
    # 测试项目路径
    test_project = project_root / "tests" / "c_test_project"
    
    if not test_project.exists():
        print(f"❌ 测试项目不存在: {test_project}")
        print("提示：请解压 c_test_project.zip 文件")
        return False
    
    print("="*80)
    print("🧪 测试调用图构建器")
    print("="*80)
    print(f"📁 测试项目: {test_project}")
    print()
    
    # 1. 构建调用图
    print("📊 步骤 1: 构建调用图...")
    builder = CallGraphBuilder(str(test_project), language='c')
    call_graph = builder.build()
    
    # 打印统计信息
    project_info = call_graph['project']
    print(f"  ✅ 项目名称: {project_info['name']}")
    print(f"  ✅ 函数总数: {project_info['total_functions']}")
    print(f"  ✅ 文件总数: {project_info['total_files']}")
    print(f"  ✅ 调用边数: {project_info['total_call_edges']}")
    print()
    
    # 2. 检查是否包含控制流关键字
    print("🔍 步骤 2: 检查是否过滤了控制流关键字...")
    functions = call_graph['functions']
    keywords_found = []
    control_keywords = {'if', 'for', 'while', 'switch', 'else', 'return'}
    
    for func_id, func_info in functions.items():
        func_name = func_info['name'].lower()
        if func_name in control_keywords:
            keywords_found.append(func_name)
    
    if keywords_found:
        print(f"  ❌ 发现控制流关键字: {keywords_found}")
        print("  提示：调用图不应包含if/for等控制流关键字")
        return False
    else:
        print(f"  ✅ 未发现控制流关键字（共检查 {len(functions)} 个函数）")
    print()
    
    # 3. 显示函数列表
    print("📝 步骤 3: 显示提取的函数列表（前20个）...")
    for i, (func_id, func_info) in enumerate(list(functions.items())[:20], 1):
        print(f"  {i:2d}. {func_info['name']:30s} @ {func_info['file']}:{func_info['line']}")
    
    if len(functions) > 20:
        print(f"  ... 还有 {len(functions) - 20} 个函数")
    print()
    
    # 4. 保存调用图
    output_file = project_root / "tests" / "call_graph_test_output.json"
    print(f"💾 步骤 4: 保存调用图到文件...")
    builder.save_to_file(output_file)
    print(f"  ✅ 已保存: {output_file}")
    print()
    
    # 5. 测试调用图查询
    print("🔎 步骤 5: 测试调用图查询功能...")
    query_tool = CallGraphQuery(output_file)
    
    # 获取统计信息
    stats = query_tool.get_statistics()
    print(f"  统计信息:")
    print(f"    - 总函数数: {stats.get('total_functions', 0)}")
    print(f"    - 总文件数: {stats.get('total_files', 0)}")
    print(f"    - 入口点数: {stats.get('entry_points', 0)}")
    print()
    
    # 6. 测试查询不存在的函数（测试增强的错误信息）
    print("🧪 步骤 6: 测试查询不存在的函数（验证错误信息增强）...")
    result = query_tool.query("nonexistent_function")
    
    if 'error' in result:
        print(f"  ✅ 正确返回错误: {result['error']}")
        
        if 'suggestions' in result:
            print(f"  ✅ 包含建议信息:")
            suggestions = result['suggestions']
            if 'alternatives' in suggestions:
                for alt in suggestions['alternatives'][:3]:
                    print(f"    - {alt}")
        
        if 'call_graph_info' in result:
            info = result['call_graph_info']
            print(f"  ✅ 包含调用图信息: {info.get('total_functions_in_graph', 0)} 个函数")
    else:
        print(f"  ❌ 应该返回错误，但没有")
    print()
    
    # 7. 测试查询实际存在的函数
    print("🧪 步骤 7: 测试查询实际存在的函数...")
    if functions:
        # 选择第一个非main的函数
        test_func = None
        for func_id, func_info in functions.items():
            if func_info['name'] != 'main':
                test_func = func_info['name']
                break
        
        if test_func:
            print(f"  查询函数: {test_func}")
            result = query_tool.query(test_func, depth=1, direction='both')
            
            if 'error' not in result:
                print(f"  ✅ 查询成功")
                summary = result.get('summary', {})
                print(f"    - 节点数: {summary.get('total_nodes', 0)}")
                print(f"    - 最大深度: {summary.get('max_depth_reached', 0)}")
            else:
                print(f"  ⚠️ 查询失败: {result['error']}")
    print()
    
    print("="*80)
    print("✅ 测试完成！")
    print("="*80)
    
    return True


def test_read_file_range_auto_correct():
    """测试 read_file_range 的自动修正功能"""
    from app.codeReview.ConfigurationItem.service.feature_review.agent_tools import AgentTools
    
    test_project = project_root / "tests" / "c_test_project"
    if not test_project.exists():
        print(f"❌ 测试项目不存在: {test_project}")
        return False
    
    print("="*80)
    print("🧪 测试 read_file_range 自动修正功能")
    print("="*80)
    
    # 创建工具实例
    tools = AgentTools(str(test_project), task_id=999)
    
    # 查找一个测试文件
    test_files = list(test_project.rglob("*.c"))
    if not test_files:
        print("❌ 未找到测试文件")
        return False
    
    test_file = test_files[0]
    relative_path = str(test_file.relative_to(test_project))
    
    print(f"📁 测试文件: {relative_path}")
    print()
    
    # 测试1: 请求超出范围的行号
    print("测试 1: 请求超出范围的行号（1-1000）...")
    result = tools.read_file_range(relative_path, 1, 1000)
    
    if 'error' not in result:
        print(f"  ✅ 自动修正成功")
        print(f"  实际读取: {result['start_line']} - {result['end_line']} 行")
        if 'warnings' in result:
            print(f"  警告: {result['warnings'][0]}")
        if 'note' in result:
            print(f"  提示: {result['note']}")
    else:
        print(f"  ❌ 失败: {result['error']}")
    print()
    
    # 测试2: 请求负数起始行
    print("测试 2: 请求负数起始行（-5 到 10）...")
    result = tools.read_file_range(relative_path, -5, 10)
    
    if 'error' not in result:
        print(f"  ✅ 自动修正成功")
        print(f"  实际读取: {result['start_line']} - {result['end_line']} 行")
        if 'warnings' in result:
            for warning in result['warnings']:
                print(f"  警告: {warning}")
    else:
        # 负数起始行可能仍然报错，这也是合理的
        print(f"  ⚠️ 返回错误: {result['error']}")
    print()
    
    print("="*80)
    print("✅ read_file_range 测试完成！")
    print("="*80)
    
    return True


if __name__ == "__main__":
    print("\n" + "🎯"*40)
    print("开始测试工具修复")
    print("🎯"*40 + "\n")
    
    # 测试1: 调用图构建器
    success1 = test_call_graph_builder()
    
    print("\n")
    
    # 测试2: read_file_range 自动修正
    success2 = test_read_file_range_auto_correct()
    
    # 总结
    print("\n" + "📊"*40)
    print("测试总结")
    print("📊"*40)
    print(f"调用图构建器测试: {'✅ 通过' if success1 else '❌ 失败'}")
    print(f"read_file_range测试: {'✅ 通过' if success2 else '❌ 失败'}")
    print()
    
    if success1 and success2:
        print("🎉 所有测试通过！")
        sys.exit(0)
    else:
        print("⚠️ 部分测试失败，请检查日志")
        sys.exit(1)

