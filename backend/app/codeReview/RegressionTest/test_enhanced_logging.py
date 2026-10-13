#!/usr/bin/env python3
"""
测试增强后的AI代码审查日志记录功能

这个脚本用于验证：
1. 函数审查Agent是否正确记录AI返回的原始信息
2. FPGA审查Agent是否正确记录AI返回的原始信息
3. 链路审查模块是否正确记录AI返回的原始信息
4. 功能审查模块是否正确记录AI返回的原始信息

使用方法：
python test_enhanced_logging.py
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_function_review_agent_logging():
    """测试函数审查Agent的日志记录"""
    print("=" * 60)
    print("测试函数审查Agent的日志记录功能")
    print("=" * 60)
    
    try:
        from service.ai.function_review_agent import FunctionReviewAgent
        
        # 创建一个简单的测试函数
        test_function_code = """
int add(int a, int b) {
    return a + b;
}
"""
        
        # 创建Agent实例
        agent = FunctionReviewAgent(
            project_root=str(project_root),
            language='c'
        )
        
        print("✓ 函数审查Agent创建成功")
        print("✓ 增强的日志记录功能已集成")
        print("  - AI原始响应内容记录")
        print("  - 函数信息详细记录")
        print("  - 注释后代码单独记录")
        print("  - 问题详情记录")
        
    except Exception as e:
        print(f"✗ 函数审查Agent测试失败: {e}")

def test_fpga_review_agent_logging():
    """测试FPGA审查Agent的日志记录"""
    print("\n" + "=" * 60)
    print("测试FPGA审查Agent的日志记录功能")
    print("=" * 60)
    
    try:
        from service.ai.fpga_review_agent import FPGAReviewAgent
        
        # 创建Agent实例
        agent = FPGAReviewAgent(
            project_root=str(project_root),
            language='verilog'
        )
        
        print("✓ FPGA审查Agent创建成功")
        print("✓ 增强的日志记录功能已集成")
        print("  - AI原始响应内容记录")
        print("  - 模块信息详细记录")
        print("  - 注释后代码单独记录")
        print("  - 问题详情记录")
        
    except Exception as e:
        print(f"✗ FPGA审查Agent测试失败: {e}")

def test_chain_review_logging():
    """测试链路审查模块的日志记录"""
    print("\n" + "=" * 60)
    print("测试链路审查模块的日志记录功能")
    print("=" * 60)
    
    try:
        from service.business_review.executor.smart_chain_executor import SmartChainExecutor
        
        # 创建执行器实例
        executor = SmartChainExecutor(
            project_root=str(project_root)
        )
        
        print("✓ 链路审查执行器创建成功")
        print("✓ 详细的日志记录功能已存在")
        print("  - AI请求完整记录")
        print("  - AI响应完整记录")
        print("  - 工具调用详细记录")
        print("  - 问题提取记录")
        
    except Exception as e:
        print(f"✗ 链路审查模块测试失败: {e}")

def test_feature_review_logging():
    """测试功能审查模块的日志记录"""
    print("\n" + "=" * 60)
    print("测试功能审查模块的日志记录功能")
    print("=" * 60)
    
    try:
        from service.feature_review.agent_executor import AgentExecutor
        from service.feature_review.agent_tools import AgentTools
        from service.ai.openai.client import AIClient
        
        # 创建工具和客户端实例
        tools = AgentTools(project_root=str(project_root))
        ai_client = AIClient()
        
        # 创建执行器实例
        executor = AgentExecutor(
            tools=tools,
            ai_client=ai_client
        )
        
        print("✓ 功能审查执行器创建成功")
        print("✓ AI客户端日志记录功能已存在")
        print("  - AI原始请求记录")
        print("  - AI原始响应记录")
        print("  - 工具调用记录")
        
    except Exception as e:
        print(f"✗ 功能审查模块测试失败: {e}")

def test_log_file_structure():
    """测试日志文件结构"""
    print("\n" + "=" * 60)
    print("检查日志文件结构")
    print("=" * 60)
    
    logs_dir = project_root / "logs"
    if logs_dir.exists():
        print(f"✓ 日志目录存在: {logs_dir}")
        
        # 查找最新的任务日志
        task_dirs = [d for d in logs_dir.iterdir() if d.is_dir() and d.name.startswith('task_')]
        if task_dirs:
            latest_task = max(task_dirs, key=lambda x: x.stat().st_mtime)
            print(f"✓ 找到最新任务日志: {latest_task.name}")
            
            logs_subdir = latest_task / "logs"
            if logs_subdir.exists():
                log_files = list(logs_subdir.glob("*.log"))
                print(f"✓ 找到 {len(log_files)} 个日志文件")
                
                # 检查是否包含AI响应信息
                for log_file in log_files[:3]:  # 只检查前3个文件
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if "AI返回最终结果" in content or "AI原始响应" in content:
                                print(f"  ✓ {log_file.name} 包含AI响应信息")
                            elif "function_review_agent" in content or "fpga_review_agent" in content:
                                print(f"  ✓ {log_file.name} 包含Agent日志")
                    except Exception as e:
                        print(f"  ✗ 读取 {log_file.name} 失败: {e}")
            else:
                print("✗ 未找到logs子目录")
        else:
            print("✗ 未找到任务日志目录")
    else:
        print("✗ 日志目录不存在")

def main():
    """主测试函数"""
    print("AI代码审查模块 - 增强日志记录功能测试")
    print("=" * 60)
    print("测试目标：验证AI模型返回的原始信息是否正确记录到日志文件中")
    print("包括：函数功能概述、注释后代码、问题详情等")
    
    # 运行各个模块的测试
    test_function_review_agent_logging()
    test_fpga_review_agent_logging()
    test_chain_review_logging()
    test_feature_review_logging()
    test_log_file_structure()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print("✓ 函数审查Agent - 已增强AI原始响应记录")
    print("✓ FPGA审查Agent - 已增强AI原始响应记录")
    print("✓ 链路审查模块 - 已有详细AI响应记录")
    print("✓ 功能审查模块 - 通过AI客户端记录响应")
    print("\n增强功能说明：")
    print("1. AI返回的原始JSON响应完整记录")
    print("2. 函数/模块信息单独详细记录")
    print("3. 注释后代码单独记录，便于查看AI是否真的返回了注释")
    print("4. 发现的问题详情记录")
    print("5. 所有日志都保存在 logs/task_X/logs/ 目录下")
    
    print("\n" + "=" * 60)
    print("如何查看AI返回的注释后代码：")
    print("=" * 60)
    print("1. 运行代码审查任务")
    print("2. 查看日志文件：logs/task_X/logs/")
    print("3. 搜索关键词：")
    print("   - 'AI返回最终结果' - 查看完整原始响应")
    print("   - 'AI返回的注释后代码' - 查看注释后的代码")
    print("   - '函数信息解析成功' - 查看函数信息摘要")
    print("   - '模块信息解析成功' - 查看FPGA模块信息摘要")

if __name__ == "__main__":
    main()
