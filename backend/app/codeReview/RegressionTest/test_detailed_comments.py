#!/usr/bin/env python3
"""
测试详细注释功能

这个脚本用于验证修改后的提示词是否能让AI返回更详细的注释
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_function_review_prompt():
    """测试函数审查Agent的提示词修改"""
    print("=" * 60)
    print("测试函数审查Agent的详细注释要求")
    print("=" * 60)
    
    try:
        from service.ai.function_review_agent import FunctionReviewAgent
        
        # 创建Agent实例
        agent = FunctionReviewAgent(
            project_root=str(project_root),
            language='c'
        )
        
        # 构建测试提示词
        test_prompt = agent._build_system_prompt("测试禁止规则")
        
        # 检查关键的详细注释要求
        detailed_requirements = [
            "必须添加详细注释",
            "为每一行重要代码添加详细注释",
            "解释代码的具体作用和业务含义",
            "变量声明：说明用途、大小、数据类型选择原因",
            "函数调用：说明调用目的、参数含义、预期结果",
            "条件判断：说明判断条件的业务含义",
            "循环：说明循环目的、边界条件",
            "返回语句：说明返回值含义",
            "对于潜在问题的代码，要在注释中标注风险"
        ]
        
        all_found = True
        for requirement in detailed_requirements:
            if requirement in test_prompt:
                print(f"✓ {requirement}")
            else:
                print(f"✗ {requirement}")
                all_found = False
        
        # 检查示例是否更详细
        if "// 输入处理函数，从标准输入读取字符串" in test_prompt:
            print("✓ 示例包含详细的函数注释")
        else:
            print("✗ 示例缺少详细的函数注释")
            all_found = False
            
        if "// 声明10字节字符数组作为输入缓冲区" in test_prompt:
            print("✓ 示例包含详细的变量注释")
        else:
            print("✗ 示例缺少详细的变量注释")
            all_found = False
            
        if "// 【安全风险】使用gets()函数读取用户输入" in test_prompt:
            print("✓ 示例包含风险标注")
        else:
            print("✗ 示例缺少风险标注")
            all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_fpga_review_prompt():
    """测试FPGA审查Agent的提示词修改"""
    print("\n" + "=" * 60)
    print("测试FPGA审查Agent的详细注释要求")
    print("=" * 60)
    
    try:
        from service.ai.fpga_review_agent import FPGAReviewAgent
        
        # 创建Agent实例
        agent = FPGAReviewAgent(
            project_root=str(project_root),
            language='verilog'
        )
        
        # 构建测试提示词
        test_prompt = agent._build_system_prompt("测试禁止规则")
        
        # 检查关键的详细注释要求
        detailed_requirements = [
            "必须添加详细注释",
            "为每一行重要代码添加行内注释或行上注释",
            "端口声明、信号声明、时钟逻辑、组合逻辑、状态机、实例化",
            "解释信号用途、时序关系、业务逻辑、设计意图",
            "时钟域、复位策略、状态转换、资源使用",
            "端口声明：说明信号用途、位宽选择、电气特性",
            "信号声明：说明数据流向、时序关系、驱动源",
            "时钟逻辑：说明时钟域、触发条件、时序约束",
            "组合逻辑：说明逻辑功能、延迟特性",
            "状态机：说明状态含义、转换条件",
            "实例化：说明子模块功能、参数配置、连接关系",
            "对于潜在问题的代码，要在注释中标注设计风险"
        ]
        
        all_found = True
        for requirement in detailed_requirements:
            if requirement in test_prompt:
                print(f"✓ {requirement}")
            else:
                print(f"✗ {requirement}")
                all_found = False
        
        # 检查FPGA示例是否更详细
        if "// 8位同步计数器模块" in test_prompt:
            print("✓ 示例包含详细的模块注释")
        else:
            print("✗ 示例缺少详细的模块注释")
            all_found = False
            
        if "// 系统时钟输入，上升沿有效" in test_prompt:
            print("✓ 示例包含详细的端口注释")
        else:
            print("✗ 示例缺少详细的端口注释")
            all_found = False
            
        if "// 异步复位：立即将计数器清零" in test_prompt:
            print("✓ 示例包含详细的逻辑注释")
        else:
            print("✗ 示例缺少详细的逻辑注释")
            all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_initial_task_prompts():
    """测试初始任务提示词的修改"""
    print("\n" + "=" * 60)
    print("测试初始任务提示词的详细注释要求")
    print("=" * 60)
    
    try:
        from service.ai.function_review_agent import FunctionReviewAgent
        from service.ai.fpga_review_agent import FPGAReviewAgent
        
        # 测试函数审查Agent的初始任务
        func_agent = FunctionReviewAgent(project_root=str(project_root), language='c')
        func_task = func_agent._build_initial_task("int main(){return 0;}", "main", "test.c")
        
        func_requirements = [
            "特别重要 - commented_code详细注释要求",
            "必须为每一行重要代码添加详细注释",
            "注释要解释代码的具体作用和业务含义",
            "对于潜在问题的代码，要在注释中标注风险"
        ]
        
        func_all_found = True
        print("函数审查Agent初始任务:")
        for req in func_requirements:
            if req in func_task:
                print(f"  ✓ {req}")
            else:
                print(f"  ✗ {req}")
                func_all_found = False
        
        # 测试FPGA审查Agent的初始任务
        fpga_agent = FPGAReviewAgent(project_root=str(project_root), language='verilog')
        fpga_task = fpga_agent._build_initial_task("module test(); endmodule", "test", "test.v")
        
        fpga_requirements = [
            "特别重要 - commented_code详细注释要求",
            "必须为每一行重要代码添加详细注释",
            "FPGA特有注释要求",
            "对于潜在问题的代码，要在注释中标注设计风险"
        ]
        
        fpga_all_found = True
        print("\nFPGA审查Agent初始任务:")
        for req in fpga_requirements:
            if req in fpga_task:
                print(f"  ✓ {req}")
            else:
                print(f"  ✗ {req}")
                fpga_all_found = False
        
        return func_all_found and fpga_all_found
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("AI代码审查模块 - 详细注释功能测试")
    print("=" * 60)
    print("测试目标：验证修改后的提示词能让AI返回更详细的注释")
    
    # 运行各项测试
    func_ok = test_function_review_prompt()
    fpga_ok = test_fpga_review_prompt()
    task_ok = test_initial_task_prompts()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if func_ok and fpga_ok and task_ok:
        print("🎉 所有详细注释要求验证通过！")
        print("\n修改内容总结：")
        print("✓ 函数审查Agent - 增加了详细注释要求和示例")
        print("✓ FPGA审查Agent - 增加了FPGA特有的详细注释要求")
        print("✓ 初始任务提示词 - 强调了commented_code的详细要求")
        print("\n现在AI会返回更详细的注释，包括：")
        print("- 每行代码的具体作用和业务含义")
        print("- 变量用途、函数调用目的、条件判断逻辑")
        print("- FPGA特有的时序关系、信号用途、设计意图")
        print("- 潜在问题代码的风险标注")
        print("\n下次运行代码审查时，AI返回的注释应该会更加详细！")
    else:
        print("⚠️ 部分测试未通过，请检查修改是否完整")
        if not func_ok:
            print("- 函数审查Agent的提示词需要进一步检查")
        if not fpga_ok:
            print("- FPGA审查Agent的提示词需要进一步检查")
        if not task_ok:
            print("- 初始任务提示词需要进一步检查")

if __name__ == "__main__":
    main()
