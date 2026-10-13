"""
文本处理工具模块 - 回归测试版本

用于处理需求分析相关的文本格式化和提取功能
从配置项模块复制并适配到回归测试模块
"""

import re
from typing import List, Optional


def extract_requirement_name(full_requirement_text: str) -> str:
    """
    从包含章节号的需求文本中提取纯需求名称
    
    输入格式示例:
    - "3.2.1 用户身份验证功能"
    - "3.2.2 数据批量导入功能" 
    - "3.2.2.1 实时通知推送功能"
    - "4.1.3.2.1 系统初始化检测"
    
    输出: 纯需求名称
    - "用户身份验证功能"
    - "数据批量导入功能"
    - "实时通知推送功能"
    - "系统初始化检测"
    
    Args:
        full_requirement_text: 包含章节号的完整需求文本
        
    Returns:
        str: 提取出的纯需求名称
    """
    if not full_requirement_text or not isinstance(full_requirement_text, str):
        return full_requirement_text or ""
    
    # 去除首尾空白
    text = full_requirement_text.strip()
    
    # 正则表达式匹配章节号模式
    # 匹配模式: 数字.数字.数字... (可能有多层) + 空格 + 需求名称
    chapter_pattern = r'^(\d+(?:\.\d+)*)\s+'
    
    # 查找章节号模式
    match = re.match(chapter_pattern, text)
    
    if match:
        # 提取章节号后的内容作为纯需求名称
        chapter_part = match.group(1)
        requirement_name = text[len(match.group(0)):].strip()
        return requirement_name
    else:
        # 如果没有找到章节号模式，返回原文本
        return text


def extract_requirement_names_batch(requirement_list: List[str]) -> List[str]:
    """
    批量提取需求名称
    
    Args:
        requirement_list: 包含章节号的需求文本列表
        
    Returns:
        List[str]: 提取出的纯需求名称列表
    """
    if not requirement_list:
        return []
    
    return [extract_requirement_name(req) for req in requirement_list]


def extract_chapter_number(full_requirement_text: str) -> Optional[str]:
    """
    从包含章节号的需求文本中提取章节号
    
    Args:
        full_requirement_text: 包含章节号的完整需求文本
        
    Returns:
        Optional[str]: 提取出的章节号，如果没有找到则返回None
    """
    if not full_requirement_text or not isinstance(full_requirement_text, str):
        return None
    
    text = full_requirement_text.strip()
    chapter_pattern = r'^(\d+(?:\.\d+)*)\s+'
    
    match = re.match(chapter_pattern, text)
    if match:
        return match.group(1)
    return None


def get_requirement_info(full_requirement_text: str) -> dict:
    """
    获取需求的完整信息，包括章节号和纯名称
    
    Args:
        full_requirement_text: 包含章节号的完整需求文本
        
    Returns:
        dict: 包含 'chapter_number' 和 'requirement_name' 的字典
    """
    return {
        'chapter_number': extract_chapter_number(full_requirement_text),
        'requirement_name': extract_requirement_name(full_requirement_text),
        'original_text': full_requirement_text
    }


# 测试函数
if __name__ == "__main__":
    # 测试用例
    test_cases = [
        "3.2.1 用户身份验证功能",
        "3.2.2 数据批量导入功能", 
        "3.2.2.1 实时通知推送功能",
        "4.1.3.2.1 系统初始化检测",
        "1.1 基础配置管理",
        "没有章节号的需求名称",
        "",
        "2.3.4.5.6.7 多层级需求功能"
    ]
    
    print("🧪 回归测试模块 - 需求名称提取测试:")
    for test_case in test_cases:
        result = extract_requirement_name(test_case)
        chapter = extract_chapter_number(test_case)
        print(f"原文: '{test_case}'")
        print(f"章节号: {chapter}")
        print(f"需求名称: '{result}'")
        print("---") 