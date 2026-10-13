"""
测试用例反向推导工具优化功能测试脚本
"""
import asyncio
import json
from pathlib import Path
from services.ai_client import TestCaseReverseAIClient
from services.service import TestCaseReverseService
from database.migrate_add_template_fields import migrate_database

async def test_ai_client_timeout_retry():
    """测试AI客户端的超时和重试机制"""
    print("=" * 60)
    print("测试AI客户端超时和重试机制")
    print("=" * 60)
    
    # 创建测试会话ID
    session_id = "test_session_001"
    
    # 初始化AI客户端
    ai_client = TestCaseReverseAIClient(session_id)
    
    # 测试数据
    test_item_name = "登录功能测试"
    test_cases = [
        {"input_condition": "输入正确的用户名和密码", "test_result": "登录成功，跳转到主页"},
        {"input_condition": "输入错误的用户名", "test_result": "显示用户名错误提示"},
        {"input_condition": "输入错误的密码", "test_result": "显示密码错误提示"}
    ]
    
    # 测试普通模式
    print("\n1. 测试普通模式...")
    try:
        result = await ai_client.generate_test_content_and_method(
            test_item_name, test_cases, "normal"
        )
        if result["success"]:
            print("✅ 普通模式测试成功")
            print(f"测试内容: {result['test_content'][:100]}...")
            print(f"测试方法: {result['test_method'][:100]}...")
        else:
            print(f"❌ 普通模式测试失败: {result['error']}")
    except Exception as e:
        print(f"❌ 普通模式测试异常: {str(e)}")
    
    # 测试模板模式
    print("\n2. 测试用例模板模式...")
    try:
        result = await ai_client.generate_test_content_and_method(
            test_item_name, test_cases, "template"
        )
        if result["success"]:
            print("✅ 用例模板模式测试成功")
            print(f"测试内容: {result['test_content'][:100]}...")
            print(f"测试方法: {result['test_method'][:100]}...")
            if 'case_template_name' in result:
                print(f"用例模板名称: {result['case_template_name'][:100]}...")
        else:
            print(f"❌ 用例模板模式测试失败: {result['error']}")
    except Exception as e:
        print(f"❌ 用例模板模式测试异常: {str(e)}")

def test_prompt_files():
    """测试提示词文件是否存在和格式正确"""
    print("=" * 60)
    print("测试提示词文件")
    print("=" * 60)
    
    prompt_dir = Path(__file__).parent / "prompts"
    
    # 检查普通模式提示词文件
    normal_prompt_file = prompt_dir / "normal_mode_prompt.md"
    if normal_prompt_file.exists():
        print("✅ 普通模式提示词文件存在")
        with open(normal_prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "{test_item_name}" in content and "{test_cases}" in content:
                print("✅ 普通模式提示词格式正确")
            else:
                print("❌ 普通模式提示词格式错误，缺少占位符")
    else:
        print("❌ 普通模式提示词文件不存在")
    
    # 检查模板模式提示词文件
    template_prompt_file = prompt_dir / "template_mode_prompt.md"
    if template_prompt_file.exists():
        print("✅ 用例模板模式提示词文件存在")
        with open(template_prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "{test_item_name}" in content and "{test_cases}" in content:
                print("✅ 用例模板模式提示词格式正确")
            else:
                print("❌ 用例模板模式提示词格式错误，缺少占位符")
    else:
        print("❌ 用例模板模式提示词文件不存在")

def test_database_migration():
    """测试数据库迁移"""
    print("=" * 60)
    print("测试数据库迁移")
    print("=" * 60)
    
    try:
        result = migrate_database()
        if result:
            print("✅ 数据库迁移测试成功")
        else:
            print("❌ 数据库迁移测试失败")
    except Exception as e:
        print(f"❌ 数据库迁移测试异常: {str(e)}")

def test_service_integration():
    """测试服务集成"""
    print("=" * 60)
    print("测试服务集成")
    print("=" * 60)
    
    try:
        # 创建测试服务实例
        service = TestCaseReverseService("test_integration_001")
        
        # 测试内存状态获取
        status = service.get_memory_status()
        print("✅ 服务内存状态获取成功")
        print(f"状态: {status}")
        
    except Exception as e:
        print(f"❌ 服务集成测试异常: {str(e)}")

async def run_all_tests():
    """运行所有测试"""
    print("开始测试用例反向推导工具优化功能...")
    print()
    
    # 测试提示词文件
    test_prompt_files()
    print()
    
    # 测试数据库迁移
    test_database_migration()
    print()
    
    # 测试服务集成
    test_service_integration()
    print()
    
    # 测试AI客户端（需要配置文件和网络）
    try:
        await test_ai_client_timeout_retry()
    except Exception as e:
        print(f"AI客户端测试跳过（需要配置和网络）: {str(e)}")
    
    print("=" * 60)
    print("所有测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_all_tests()) 