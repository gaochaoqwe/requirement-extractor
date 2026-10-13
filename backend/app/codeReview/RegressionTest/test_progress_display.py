#!/usr/bin/env python3
"""
进度显示功能测试脚本

用于测试代码审查进度显示功能是否正常工作
"""

import asyncio
import sys
import os
import requests
import time
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def test_function_review_progress(task_id: int) -> Dict[str, Any]:
    """
    测试函数审查进度API
    
    Args:
        task_id: 任务ID
        
    Returns:
        进度信息
    """
    try:
        url = f"http://localhost:8000/api/codeReview/task_progress/{task_id}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 函数审查进度API测试成功")
            print(f"   任务ID: {data.get('task_id')}")
            print(f"   状态: {data.get('status')}")
            print(f"   进度: {data.get('progress')}%")
            print(f"   消息: {data.get('message', 'N/A')}")
            
            if data.get('details'):
                print(f"   详细信息: {data['details']}")
            
            return data
        else:
            print(f"❌ 函数审查进度API测试失败: HTTP {response.status_code}")
            print(f"   响应: {response.text}")
            return {}
            
    except Exception as e:
        print(f"❌ 函数审查进度API测试异常: {e}")
        return {}

def test_chain_review_progress(task_id: int) -> Dict[str, Any]:
    """
    测试链路审查进度API
    
    Args:
        task_id: 任务ID
        
    Returns:
        进度信息
    """
    try:
        url = f"http://localhost:8000/api/codeReview/progressive/progress/{task_id}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 链路审查进度API测试成功")
            print(f"   状态: {data.get('status')}")
            print(f"   总体进度: {data.get('overall_progress')}%")
            print(f"   发现进度: {data.get('discovery_progress')}%")
            print(f"   审查进度: {data.get('review_progress')}%")
            print(f"   消息: {data.get('message', 'N/A')}")
            
            return data
        else:
            print(f"❌ 链路审查进度API测试失败: HTTP {response.status_code}")
            print(f"   响应: {response.text}")
            return {}
            
    except Exception as e:
        print(f"❌ 链路审查进度API测试异常: {e}")
        return {}

def test_progress_polling(task_id: int, review_type: str = 'function', duration: int = 30):
    """
    测试进度轮询功能
    
    Args:
        task_id: 任务ID
        review_type: 审查类型 ('function' 或 'chain')
        duration: 测试持续时间（秒）
    """
    print(f"\n🔄 开始进度轮询测试 (任务ID: {task_id}, 类型: {review_type}, 持续: {duration}秒)")
    
    start_time = time.time()
    poll_count = 0
    
    while time.time() - start_time < duration:
        poll_count += 1
        print(f"\n--- 第 {poll_count} 次轮询 ---")
        
        if review_type == 'chain':
            data = test_chain_review_progress(task_id)
        else:
            data = test_function_review_progress(task_id)
        
        if data and data.get('status') in ['completed', 'failed']:
            print(f"✅ 任务已结束，状态: {data.get('status')}")
            break
        
        # 等待3秒再次轮询
        time.sleep(3)
    
    print(f"\n📊 轮询测试完成，共轮询 {poll_count} 次")

def main():
    """主函数"""
    print("🚀 代码审查进度显示功能测试")
    print("=" * 50)
    
    # 从命令行参数获取任务ID
    if len(sys.argv) < 2:
        print("❌ 请提供任务ID")
        print("用法: python test_progress_display.py <task_id> [review_type]")
        print("示例: python test_progress_display.py 123 function")
        print("示例: python test_progress_display.py 456 chain")
        return
    
    try:
        task_id = int(sys.argv[1])
    except ValueError:
        print("❌ 任务ID必须是数字")
        return
    
    review_type = sys.argv[2] if len(sys.argv) > 2 else 'function'
    
    if review_type not in ['function', 'chain']:
        print("❌ 审查类型必须是 'function' 或 'chain'")
        return
    
    print(f"📋 测试参数:")
    print(f"   任务ID: {task_id}")
    print(f"   审查类型: {review_type}")
    
    # 单次测试
    print(f"\n🧪 单次API测试")
    if review_type == 'chain':
        test_chain_review_progress(task_id)
    else:
        test_function_review_progress(task_id)
    
    # 询问是否进行轮询测试
    try:
        response = input(f"\n❓ 是否进行30秒轮询测试? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            test_progress_polling(task_id, review_type, 30)
    except KeyboardInterrupt:
        print(f"\n⏹️  测试被用户中断")
    
    print(f"\n✅ 测试完成")

if __name__ == "__main__":
    main()
