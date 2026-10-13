#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
中文转拼音工具模块
用于将中文文本转换为拼音首字母
"""

import re


def chinese_to_pinyin_initials(text: str, uppercase: bool = True) -> str:
    """
    将中文文本转换为拼音首字母
    
    Args:
        text: 中文文本
        uppercase: 是否转换为大写，默认True
        
    Returns:
        str: 拼音首字母字符串
        
    Examples:
        >>> chinese_to_pinyin_initials("随动控制软件")
        'SDKZRJ'
        >>> chinese_to_pinyin_initials("雷达探测系统")
        'LDTCXT'
    """
    try:
        # 尝试导入pypinyin库
        from pypinyin import lazy_pinyin, Style
        
        # 获取每个汉字的拼音首字母
        pinyin_list = lazy_pinyin(text, style=Style.FIRST_LETTER)
        
        # 只保留字母（过滤掉数字、符号等）
        initials = ''.join([p[0] for p in pinyin_list if p and p[0].isalpha()])
        
        # 转换为大写或小写
        return initials.upper() if uppercase else initials.lower()
        
    except ImportError:
        # 如果没有安装pypinyin，使用简单的映射表
        return _chinese_to_pinyin_initials_fallback(text, uppercase)


def _chinese_to_pinyin_initials_fallback(text: str, uppercase: bool = True) -> str:
    """
    备用方案：使用简化的拼音首字母映射表
    仅支持常用汉字
    """
    # 常用汉字拼音首字母映射（简化版）
    pinyin_dict = {
        # 常用字拼音首字母映射
        '随': 's', '动': 'd', '控': 'k', '制': 'z', '软': 'r', '件': 'j',
        '雷': 'l', '达': 'd', '探': 't', '测': 'c', '系': 'x', '统': 't',
        '红': 'h', '外': 'w', '吊': 'd', '舱': 'c', '火': 'h', '控': 'k',
        '显': 'x', '示': 's', '对': 'd', '抗': 'k', '告': 'g', '警': 'j',
        '转': 'z', '塔': 't', '光': 'g', '电': 'd', '管': 'g', '理': 'l',
        '数': 's', '据': 'j', '处': 'c', '理': 'l', '信': 'x', '息': 'x',
        '通': 't', '讯': 'x', '网': 'w', '络': 'l', '安': 'a', '全': 'q',
        '导': 'd', '航': 'h', '定': 'd', '位': 'w', '跟': 'g', '踪': 'z',
        '识': 's', '别': 'b', '图': 't', '像': 'x', '处': 'c', '理': 'l',
        '视': 's', '频': 'p', '音': 'y', '频': 'p', '传': 'c', '感': 'g',
        '器': 'q', '模': 'm', '块': 'k', '单': 'd', '元': 'y', '组': 'z',
        '平': 'p', '台': 't', '服': 'f', '务': 'w', '应': 'y', '用': 'y',
        '程': 'c', '序': 'x', '接': 'j', '口': 'k', '协': 'x', '议': 'y',
        '驱': 'q', '动': 'd', '配': 'p', '置': 'z', '参': 'c', '数': 's',
        '运': 'y', '行': 'x', '监': 'j', '控': 'k', '诊': 'z', '断': 'd',
        '维': 'w', '护': 'h', '升': 's', '级': 'j', '备': 'b', '份': 'f',
    }
    
    result = []
    for char in text:
        if char in pinyin_dict:
            result.append(pinyin_dict[char])
        elif char.isalpha():
            # 如果是英文字母，直接保留
            result.append(char.lower())
    
    initials = ''.join(result)
    return initials.upper() if uppercase else initials.lower()


def get_software_short_name_en(software_short_name: str) -> str:
    """
    根据中文软件简称生成英文简称
    
    Args:
        software_short_name: 中文软件简称
        
    Returns:
        str: 英文简称（大写字母）
        
    Examples:
        >>> get_software_short_name_en("随动控制软件")
        'SDKZRJ'
        >>> get_software_short_name_en("雷达探测系统运控软件")
        'LDTCXTYKRJ'
    """
    if not software_short_name:
        return ""
    
    # 转换为拼音首字母（大写）
    return chinese_to_pinyin_initials(software_short_name, uppercase=True)


# 测试代码
if __name__ == "__main__":
    test_cases = [
        "随动控制软件",
        "雷达探测系统",
        "红外成像模块",
        "火控管理软件",
        "显示控制单元",
    ]
    
    print("=== 中文转拼音首字母测试 ===")
    for test in test_cases:
        result = chinese_to_pinyin_initials(test)
        print(f"{test:15s} -> {result}")

