"""
AI 提示词构建模块
纯函数：不依赖外部环境，便于单元测试与复用
"""
from typing import List


def build_system_prompt(requirement_name: str, ceshileixing: str, jianceyi_flag: str) -> str:
    """构建系统提示词"""
    detector_instruction = ""
    if jianceyi_flag == "有检测仪":
        detector_instruction = "注意：测试用例中测试激励的输入和被测软件状态的监控都是通过检测仪实现的。"

    json_example = f'''{{
  "test_cases": [
    {{
      "case_name": "基本功能验证",
      "input_conditions": "步骤1：启动测试环境；步骤2：配置相关参数；步骤3：执行功能操作；步骤4：验证执行结果",
      "expected_results": "完成步骤1：测试环境启动成功；完成步骤3：功能操作执行正常；完成步骤4：功能验证通过"
    }},
    {{
      "case_name": "功能验证测试",
      "input_conditions": "步骤1：启动测试环境；步骤2：输入正常参数；步骤3：执行功能操作；步骤4：检查功能结果",
      "expected_results": "完成步骤1：测试环境启动成功；完成步骤3：功能操作执行正常；完成步骤4：功能验证通过"
    }}
  ]
}}'''

    return f"""你是一个专业的软件测试工程师，专门负责根据测试方法生成详细的测试用例。

你的任务是根据提供的测试方法，生成对应的测试用例。每个测试用例必须包含以下四个部分：
1. case_name（测试用例名称）：格式为"具体描述"
2. input_conditions（输入条件）：按"步骤1：xxx；步骤2：xxx"格式列出执行步骤
3. expected_results（预期结果）：按"完成步骤X：xxx"格式列出对应结果

注意：不需要生成case_description字段，测试用例描述将直接使用需求分析表中的测试项描述。

{detector_instruction}

测试类型：{ceshileixing}

请根据测试描述和测试方法生成1-2个测试用例，专注于验证需求功能的正确实现。

输出格式必须严格遵循以下JSON格式：
{json_example}"""


def build_user_prompt(
    test_method: str,
    test_description: str,
    requirement_name: str,
    requirement_desc: str,
    ceshileixing: str,
    method_index: int = 1,
) -> str:
    """构建用户提示词"""
    return f"""请根据以下测试方法生成对应的测试用例：

**需求名称**: {requirement_name}
**测试方法**: {test_method}
**测试描述**: {test_description}
**需求描述**: {requirement_desc}
**测试类型**: {ceshileixing}
**方法序号**: {method_index}

要求：
1. 每个测试用例都必须与提供的测试方法直接相关
2. 测试用例名称应简洁明确地描述测试内容
3. 生成2-4个测试用例，包括正常场景和异常场景
4. 确保测试步骤详细、可执行
5. 输出必须为严格的JSON格式，不包含任何其他内容"""


def build_batch_test_case_prompt(
    requirement_name: str,
    requirement_desc: str,
    requirement_sub_desc: str,
    description_items: List[str],
    method_items: List[str],
    ceshileixing: str,
    jianceyi_flag: str,
) -> str:
    """构建批量测试用例生成的AI Prompt（纯函数）
    说明：description_items/method_items 可能仅各包含一段“整段文本”，AI 必须先自行拆分。
    """
    # 合并为整段展示，便于AI自行拆分
    description_block = "\n".join([s for s in (description_items or []) if isinstance(s, str) and s.strip()]) or ""
    method_block = "\n".join([s for s in (method_items or []) if isinstance(s, str) and s.strip()]) or ""

    detector_instruction = ""
    if jianceyi_flag == "有检测仪":
        detector_instruction = "注意：测试用例中测试激励的输入和被测软件状态的监控都是通过检测仪实现的。"

    prompt = f"""
你是资深的软件测试工程师。请基于“整段的测试项描述与测试方法”先进行拆分与对齐，再为每个拆分后的测试方法生成测试用例。

【需求信息】
需求名称: {requirement_name}
需求描述: {requirement_desc}
需求子项描述: {requirement_sub_desc}
测试类型: {ceshileixing}
{detector_instruction}

【原始整段文本（可能包含多条）】
1) 测试项描述（可能包含多条）:
"""
    prompt += (description_block or "(无)") + "\n\n"
    prompt += """2) 测试方法（可能包含多条）:
"""
    prompt += (method_block or "(无)") + "\n\n"

    prompt += """【拆分与对齐规则】
1. 以“测试方法”为主进行拆分；识别以下常见分隔：
   - 换行
   - 编号样式：1、2、3、/ 1. 2. / （1）（2）/ (1)(2)
   - 中文/英文分号：； ;
2. 若“测试项描述”也包含多条，按顺序与方法进行一一对齐；如数量不等，以方法为准，对齐不到的用最近一条描述作为上下文。
3. 输出中每个方法对应1-3条测试用例，覆盖正常与异常场景。
4. 每条测试用例的 case_description 必须严格等于其对应的“测试项描述”文本（即该方法所对齐到的那一条描述），不得自拟、不得扩写。
5. 保持“测试步骤/预期结果”格式清晰，便于直接执行。

【输出格式（严格 JSON）】
请严格返回如下 JSON 结构：

{
  "test_cases_by_method": [
    {
      "method_index": 1,
      "test_method": "拆分后的第1条测试方法完整文本",
      "test_cases": [
        {
          "case_name": "具体测试点1",
          "case_description": "此处必须等于与该方法对齐的那一条测试项描述原文",
          "input_conditions": "步骤1：...；步骤2：...；步骤3：...",
          "expected_results": "完成步骤1：...；完成步骤2：...；完成步骤3：..."
        },
        {
          "case_name": "具体测试点2",
          "case_description": "此处必须等于与该方法对齐的那一条测试项描述原文",
          "input_conditions": "步骤1：...；步骤2：...",
          "expected_results": "完成步骤1：...；完成步骤2：..."
        }
      ]
    },
    {
      "method_index": 2,
      "test_method": "拆分后的第2条测试方法完整文本",
      "test_cases": [
        {
          "case_name": "具体测试点",
          "case_description": "此处必须等于与该方法对齐的那一条测试项描述原文",
          "input_conditions": "步骤1：...",
          "expected_results": "完成步骤1：..."
        }
      ]
    }
  ]
}
"""
    prompt += """【强约束】
1. method_index 从1开始，按拆分顺序递增。
2. test_method 必须是对应拆分后的完整方法文本。
3. 每条测试用例的 case_description 必须等于与该方法对齐的测试项描述原文。
4. 每个 test_cases 为该方法对应的所有用例，内容具体、不可留空或使用占位符。
5. 仅输出 JSON，不要包含任何解释性文字。
"""

    return prompt.strip()
