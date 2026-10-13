"""
回归测试Excel处理包

提供Excel文件处理和软件名称提取功能。
"""

import os
import glob
import re


def check_word_document_xuqiushuoming1(folder_path):
    """
    判断文件夹下是否存在docx文件,如果是就返回对应的路径,如果不是就返回0
    
    Args:
        folder_path: 文件夹路径
        
    Returns:
        str or int: 文件路径或0
    """
    try:
        # 1、docx文档识别
        # 构建文件路径的通配符
        pattern = os.path.join(folder_path, "*需求规格说明*.docx")
        # 使用glob模块获取匹配的文件列表
        matching_files = glob.glob(pattern)
        if matching_files:
            return matching_files[0]
        else:
            return 0  # 或者返回一个空列表 []
    except Exception as e:
        print(f"发生异常: {e}")
        return 0


def extract_software_name1(file_path):
    """
    从文件路径中提取软件名称
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 软件名称
    """
    # 使用正则表达式匹配软件名称部分
    match = re.search(r'[^\\/:*?"<>|\r\n]+软件', file_path)
    if match:
        return match.group(0)
    return 'No_name' 