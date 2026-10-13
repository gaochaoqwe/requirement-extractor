from typing import Any, Dict


def build_fpga_rule_prompt(rule: Dict[str, Any], file_item: Dict[str, Any]) -> str:
    language = file_item.get('language', 'verilog')
    display_language = 'VHDL' if language == 'vhdl' else 'Verilog'
    return f"""你是一名严格的FPGA静态分析审查助手。\n请仅针对当前这1条规则审查当前这1个文件。\n\n规则编号：{rule.get('rule_code', '')}\n规则名称：{rule.get('rule_name', '')}\n规则说明：{rule.get('rule_description', '')}\n规则准确性：{rule.get('accuracy_type', '')}\n规则语言：{rule.get('language', '')}\n\n文件路径：{file_item.get('file_path', '')}\n语言：{display_language}\n文件源码：\n```{language}\n{file_item.get('source_code', '')}\n```\n\n要求：\n1. 只能审查这1条规则。\n2. 如果没有命中该规则，返回空问题列表。\n3. 输出必须是JSON对象，格式为：\n{{\n  \"problems\": [\n    {{\n      \"violation_rules\": \"规则编号\",\n      \"issue_level\": \"建议改进/一般问题/重要问题\",\n      \"issue_name\": \"问题名称\",\n      \"issue_location\": \"文件路径:行号\",\n      \"description_requirement\": \"需求描述\",\n      \"description_issue\": \"问题描述\",\n      \"description_location\": \"问题定位\",\n      \"description_impact\": \"影响分析\"\n    }}\n  ]\n}}\n\n不要输出多余说明。"""
