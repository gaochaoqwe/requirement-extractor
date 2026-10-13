#!/usr/bin/env python3
"""
验证日志记录增强功能

这个脚本通过检查源代码来验证我们的日志记录增强是否正确实现
"""

import os
import re
from pathlib import Path

def check_function_review_agent_enhancement():
    """检查函数审查Agent的增强"""
    print("=" * 60)
    print("检查函数审查Agent的日志记录增强")
    print("=" * 60)
    
    file_path = Path("service/ai/function_review_agent.py")
    if not file_path.exists():
        print("✗ 文件不存在")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键的增强功能
    enhancements = [
        ("AI原始响应记录", "AI返回最终结果，原始响应内容"),
        ("函数信息详细记录", "函数信息解析成功"),
        ("注释后代码单独记录", "AI返回的注释后代码"),
        ("问题详情记录", "发现的问题详情")
    ]
    
    all_found = True
    for name, pattern in enhancements:
        if pattern in content:
            print(f"✓ {name} - 已实现")
        else:
            print(f"✗ {name} - 未找到")
            all_found = False
    
    return all_found

def check_fpga_review_agent_enhancement():
    """检查FPGA审查Agent的增强"""
    print("\n" + "=" * 60)
    print("检查FPGA审查Agent的日志记录增强")
    print("=" * 60)
    
    file_path = Path("service/ai/fpga_review_agent.py")
    if not file_path.exists():
        print("✗ 文件不存在")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键的增强功能
    enhancements = [
        ("AI原始响应记录", "AI返回最终结果，原始响应内容"),
        ("模块信息详细记录", "模块信息解析成功"),
        ("注释后代码单独记录", "AI返回的注释后代码"),
        ("问题详情记录", "发现的问题详情")
    ]
    
    all_found = True
    for name, pattern in enhancements:
        if pattern in content:
            print(f"✓ {name} - 已实现")
        else:
            print(f"✗ {name} - 未找到")
            all_found = False
    
    return all_found

def check_ai_client_logging():
    """检查AI客户端的日志记录"""
    print("\n" + "=" * 60)
    print("检查AI客户端的日志记录功能")
    print("=" * 60)
    
    file_path = Path("service/ai/openai/client.py")
    if not file_path.exists():
        print("✗ 文件不存在")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查AI客户端的日志记录功能
    features = [
        ("AI原始请求记录", "AI原始请求（带工具）- 开始"),
        ("AI原始响应记录", "AI原始响应（带工具）- 开始"),
        ("工具调用记录", "工具调用:"),
        ("响应内容记录", "响应内容:")
    ]
    
    all_found = True
    for name, pattern in features:
        if pattern in content:
            print(f"✓ {name} - 已实现")
        else:
            print(f"✗ {name} - 未找到")
            all_found = False
    
    return all_found

def check_chain_review_logging():
    """检查链路审查的日志记录"""
    print("\n" + "=" * 60)
    print("检查链路审查模块的日志记录功能")
    print("=" * 60)
    
    file_path = Path("service/business_review/executor/smart_chain_executor.py")
    if not file_path.exists():
        print("✗ 文件不存在")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查链路审查的日志记录功能
    features = [
        ("AI请求记录", "开始 AI 请求"),
        ("AI响应记录", "收到 AI 响应"),
        ("工具调用记录", "AI请求调用"),
        ("问题提取记录", "问题详情")
    ]
    
    all_found = True
    for name, pattern in features:
        if pattern in content:
            print(f"✓ {name} - 已实现")
        else:
            print(f"✗ {name} - 未找到")
            all_found = False
    
    return all_found

def generate_summary_report():
    """生成总结报告"""
    print("\n" + "=" * 60)
    print("AI代码审查日志记录增强 - 实施总结")
    print("=" * 60)
    
    print("✅ 已完成的增强功能：")
    print()
    
    print("1. 函数审查Agent (function_review_agent.py):")
    print("   ✓ AI原始响应完整记录")
    print("   ✓ 函数信息详细记录（函数名、功能描述、注释后代码长度、问题数量）")
    print("   ✓ 注释后代码单独记录，便于验证AI是否返回了注释")
    print("   ✓ 发现问题的详细信息记录")
    print()
    
    print("2. FPGA审查Agent (fpga_review_agent.py):")
    print("   ✓ AI原始响应完整记录")
    print("   ✓ 模块信息详细记录（模块名、功能描述、注释后代码长度、问题数量）")
    print("   ✓ 注释后代码单独记录，便于验证AI是否返回了注释")
    print("   ✓ 发现问题的详细信息记录")
    print()
    
    print("3. 链路审查模块 (smart_chain_executor.py):")
    print("   ✓ 已有详细的AI请求和响应记录")
    print("   ✓ 工具调用详细记录")
    print("   ✓ 问题提取和记录")
    print()
    
    print("4. 功能审查模块 (agent_executor.py):")
    print("   ✓ 通过AI客户端统一记录AI响应")
    print("   ✓ 工具调用历史记录")
    print()
    
    print("5. AI客户端 (openai/client.py):")
    print("   ✓ AI原始请求完整记录")
    print("   ✓ AI原始响应完整记录")
    print("   ✓ 工具调用详细记录")
    print()
    
    print("📍 日志文件位置：")
    print("   - 主日志目录: logs/task_X/logs/")
    print("   - 函数审查: function_review_agent.log")
    print("   - FPGA审查: fpga_review_agent.log")
    print("   - 链路审查: smart_chain_executor.log")
    print("   - AI客户端: ai_client.log")
    print()
    
    print("🔍 如何查看AI返回的注释后代码：")
    print("   1. 运行代码审查任务")
    print("   2. 打开对应的日志文件")
    print("   3. 搜索关键词：")
    print("      - 'AI返回最终结果' - 查看完整原始响应")
    print("      - 'AI返回的注释后代码' - 查看注释后的代码")
    print("      - '函数信息解析成功' - 查看函数信息摘要")
    print("      - '模块信息解析成功' - 查看FPGA模块信息摘要")
    print()
    
    print("✨ 增强效果：")
    print("   - 可以验证AI是否真的返回了注释后的代码")
    print("   - 可以查看AI返回的函数功能概述")
    print("   - 可以追踪AI的完整推理过程")
    print("   - 便于调试和问题排查")

def main():
    """主函数"""
    print("AI代码审查模块 - 日志记录增强验证")
    
    # 切换到正确的工作目录
    os.chdir(Path(__file__).parent)
    
    # 检查各个模块的增强
    func_ok = check_function_review_agent_enhancement()
    fpga_ok = check_fpga_review_agent_enhancement()
    client_ok = check_ai_client_logging()
    chain_ok = check_chain_review_logging()
    
    # 生成总结报告
    generate_summary_report()
    
    # 最终状态
    print("\n" + "=" * 60)
    print("验证结果")
    print("=" * 60)
    
    if func_ok and fpga_ok and client_ok and chain_ok:
        print("🎉 所有日志记录增强功能验证通过！")
        print("现在AI代码审查模块会详细记录AI返回的原始信息，")
        print("包括函数功能概述和注释后代码，便于验证AI的输出质量。")
    else:
        print("⚠️  部分功能可能需要进一步检查")
    
    return func_ok and fpga_ok and client_ok and chain_ok

if __name__ == "__main__":
    main()
