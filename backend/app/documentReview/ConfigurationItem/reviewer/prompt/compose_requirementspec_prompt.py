import os
import json
from docx import Document

def read_word_document(file_path):
    """读取Word文档内容"""
    try:
        doc = Document(file_path)
        return '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
    except Exception as e:
        raise Exception(f"读取Word文档失败: {str(e)}")

def compose_requirementspec_prompt(requirementspec_content, taskbook_content, rules_path, template_path, prompt_path, chunk_index=None, total_chunks=None):
    """
    组合需求规格说明的系统提示词、模板内容、规则内容和原始需求规格说明、研制任务书内容
    返回完整的 prompt 字符串
    """
    try:
        # 读取系统提示词
        with open(prompt_path, 'r', encoding='utf-8') as f:
            sys_prompt = f.read().strip()
            
        # 读取模板内容（Word文档）
        if template_path.lower().endswith('.docx'):
            template = read_word_document(template_path)
        else:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read().strip()
                
        # 读取规则内容
        with open(rules_path, 'r', encoding='utf-8') as f:
            rules = json.load(f)
            
        rule_str = '\n'.join([f"- {r['name']}: {r['description']}" for r in rules.get('rules', [])])
        
        # 拼接prompt
        chunk_info = f"（第 {chunk_index+1}/{total_chunks} 块）" if chunk_index is not None and total_chunks is not None else ""
        chunk_instruction = f"注意：原始的需求规格说明被拆分成了多块，你现在接收到的是第{chunk_index+1}/{total_chunks}块。你需要根据需求规格说明模板判断当前给你的是哪个章节，请根据当前的章节对应的审查规则进行审查，不要使用其他章节的规则。" if chunk_index is not None and total_chunks is not None else ""
        
        prompt = (
            f"{sys_prompt}\n\n"
            f"{chunk_instruction}\n\n"
            f"【需求规格说明模板】\n{template}\n\n"
            f"【需求规格说明审查规则】\n{rule_str}\n\n"
            f"【研制任务书原文内容】\n{taskbook_content}\n\n"
            f"【需求规格说明原文内容{chunk_info}】\n{requirementspec_content}\n"
        )
        return prompt
    except Exception as e:
        raise Exception(f"构建提示词失败: {str(e)}")
