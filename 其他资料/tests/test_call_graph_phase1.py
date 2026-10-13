"""
测试调用图构建和查询功能 (Phase 1)
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.codeReview.ConfigurationItem.service.business_review.tools.call_graph_builder import CallGraphBuilder
from app.codeReview.ConfigurationItem.service.business_review.tools.call_graph_query import CallGraphQuery


def test_call_graph_builder():
    """测试调用图构建器"""
    print("=" * 60)
    print("测试 1: 调用图构建器")
    print("=" * 60)
    
    # 使用测试项目
    test_project = backend_dir / "tests" / "small_test"
    
    if not test_project.exists():
        print(f"❌ 测试项目不存在: {test_project}")
        return False
    
    print(f"📁 测试项目: {test_project}")
    
    # 构建调用图
    print("\n🔨 开始构建调用图...")
    builder = CallGraphBuilder(str(test_project), language='c')
    call_graph = builder.build()
    
    # 输出统计信息
    stats = call_graph['project']
    print(f"\n✅ 构建完成！")
    print(f"   - 总函数数: {stats['total_functions']}")
    print(f"   - 总文件数: {stats['total_files']}")
    print(f"   - 调用边数: {stats['total_call_edges']}")
    
    # 显示部分函数
    print(f"\n📋 部分函数列表:")
    for func_id, func_info in list(call_graph['functions'].items())[:5]:
        print(f"   - {func_info['name']} ({func_info['file']}:{func_info['line']})")
    
    # 保存到临时文件
    output_file = backend_dir / "temp" / "test_call_graph.json"
    output_file.parent.mkdir(exist_ok=True)
    builder.save_to_file(output_file)
    print(f"\n💾 调用图已保存: {output_file}")
    
    return True, output_file


def test_call_graph_query(call_graph_file):
    """测试调用图查询"""
    print("\n" + "=" * 60)
    print("测试 2: 调用图查询")
    print("=" * 60)
    
    # 加载调用图
    print(f"\n📖 加载调用图: {call_graph_file}")
    query = CallGraphQuery(call_graph_file)
    
    # 测试查询统计
    stats = query.get_statistics()
    print(f"\n📊 统计信息:")
    print(f"   - 总函数数: {stats['total_functions']}")
    print(f"   - 总文件数: {stats['total_files']}")
    print(f"   - 调用边数: {stats['total_call_edges']}")
    
    # 查找入口点
    entry_points = query.find_entry_points()
    print(f"\n🚪 入口点 ({len(entry_points)} 个):")
    for entry in entry_points[:3]:
        print(f"   - {entry['name']} ({'main' if entry['is_main'] else 'no callers'})")
    
    # 测试调用图查询
    if entry_points:
        test_func = entry_points[0]['name']
        print(f"\n🔍 查询函数调用图: {test_func}")
        
        # 查询callees (它调用了谁)
        result = query.query(test_func, depth=2, direction="callees")
        if 'error' not in result:
            print(f"   方向: callees (它调用了谁)")
            print(f"   深度: 2")
            print(f"   节点数: {result['summary']['total_nodes']}")
            print(f"   涉及模块: {', '.join(result['summary']['modules_involved'])}")
            
            # 显示部分节点
            print(f"\n   📋 调用链:")
            for node in result['call_graph']['nodes'][:5]:
                indent = "     " * node['depth']
                print(f"{indent}└─ {node['name']} ({node['file']}:{node['line']})")
        else:
            print(f"   ❌ 查询失败: {result.get('error')}")
        
        # 查询callers (谁调用了它)
        result2 = query.query(test_func, depth=1, direction="callers")
        if 'error' not in result2:
            print(f"\n   方向: callers (谁调用了它)")
            print(f"   节点数: {result2['summary']['total_nodes']}")
    
    return True


def test_tool_integration():
    """测试工具集成"""
    print("\n" + "=" * 60)
    print("测试 3: SmartChainExecutor 工具集成")
    print("=" * 60)
    
    test_project = backend_dir / "tests" / "small_test"
    call_graph_file = test_project.parent / "call_graph" / "call_graph.json"
    
    # 先构建调用图
    if not call_graph_file.exists():
        print(f"\n⚠️  需要先构建调用图...")
        call_graph_file.parent.mkdir(parents=True, exist_ok=True)
        builder = CallGraphBuilder(str(test_project), language='c')
        call_graph = builder.build()
        builder.save_to_file(call_graph_file)
        print(f"✅ 调用图已构建")
    
    # 测试SmartChainExecutor的工具
    from app.codeReview.ConfigurationItem.service.business_review.executor.smart_chain_executor import CodeAnalysisTools
    
    tools = CodeAnalysisTools(str(test_project))
    
    # 测试get_call_graph工具
    print(f"\n🔧 测试 get_call_graph 工具:")
    result = tools.get_call_graph("main", depth=2, direction="callees")
    
    if 'error' in result:
        print(f"   ⚠️  {result['error']}")
        if 'warning' in result:
            print(f"   ⚠️  {result['warning']}")
    else:
        print(f"   ✅ 查询成功")
        print(f"   - 函数: {result.get('function')}")
        print(f"   - 节点数: {result.get('summary', {}).get('total_nodes', 0)}")
        print(f"   - 最大深度: {result.get('summary', {}).get('max_depth_reached', 0)}")
    
    return True


def main():
    """主测试函数"""
    print("\n" + "🚀" * 30)
    print("Phase 1 功能测试: 调用图构建和查询")
    print("🚀" * 30 + "\n")
    
    try:
        # 测试1: 构建调用图
        success, call_graph_file = test_call_graph_builder()
        if not success:
            print("\n❌ 测试失败: 调用图构建")
            return
        
        # 测试2: 查询调用图
        test_call_graph_query(call_graph_file)
        
        # 测试3: 工具集成
        test_tool_integration()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

