"""
为影响域分析报告审查组合提示词的模块
"""
import os
import json
import logging

# 配置日志
logger = logging.getLogger("wordllm")
logger.setLevel(logging.INFO)

from docx import Document

def read_word_document(file_path):
    """读取Word文档内容"""
    try:
        doc = Document(file_path)
        return '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
    except Exception as e:
        raise Exception(f"读取Word文档失败: {str(e)}")

def compose_impactreport_prompt(impact_report_content, prompt_file_path, rules_path=None, template_path=None):
    """
    组合用于审查影响域分析报告的提示词，自动拼接模板内容、规则内容和原始报告内容
    Args:
        impact_report_content: 影响域分析报告的内容
        prompt_file_path: 提示词模板文件路径
        rules_path: 规则文件路径（json）
        template_path: 模板文件路径（docx）
    Returns:
        组合后的完整提示词
    """
    try:
        # 读取提示词模板
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            sys_prompt = f.read().strip()
        
        # 读取模板内容
        template = ''
        if template_path:
            if template_path.lower().endswith('.docx'):
                template = read_word_document(template_path)
            else:
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = f.read().strip()
        
        # 读取规则内容
        rule_str = ''
        if rules_path:
            with open(rules_path, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            # 兼容数组或对象格式
            if isinstance(rules, list):
                rule_str = '\n'.join([f"- {r['name']}: {r['description']}" for r in rules])
            elif isinstance(rules, dict) and 'rules' in rules:
                rule_str = '\n'.join([f"- {r['name']}: {r['description']}" for r in rules['rules']])
        
        # 拼接prompt
        prompt = (
            f"{sys_prompt}\n\n"
            f"【影响域分析报告模板】\n{template}\n\n" if template else f"{sys_prompt}\n\n"
        )
        if rule_str:
            prompt += f"【影响域分析报告审查规则】\n{rule_str}\n\n"
        prompt += f"【影响域分析报告原文内容】\n{impact_report_content}\n"
        return prompt
    except Exception as e:
        logger.error(f"组合提示词时出错: {e}")
        # 回退提示词
        fallback_prompt = f"""
        请分析以下影响域分析报告，指出其中存在的问题：
        
        {impact_report_content}
        
        请以JSON格式返回问题列表，格式为：
        {{
          "problems": [
            {{
              "issue_name": "问题名称",
              "description_issue": "问题描述"
            }}
          ]
        }}
        """
        return fallback_prompt
