#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML解析模块 - 专门处理DOCX内部XML结构解析

功能：
1. 解析numbering.xml - 获取编号定义
2. 解析styles.xml - 获取样式定义
3. 解析document.xml - 获取段落内容
4. 样式级别检测
"""

import xml.etree.ElementTree as ET
import re
import zipfile
from typing import Dict, List, Optional, Any
from pathlib import Path


class DocxXmlParser:
    """DOCX XML解析器"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        
        # XML命名空间
        self.namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
        }
    
    def _debug_print(self, message: str, category: str = "XML"):
        """调试输出"""
        if self.debug_mode:
            print(f"[{category}] {message}")
    
    def parse_numbering_xml(self, docx_zip: zipfile.ZipFile) -> Dict[str, Dict]:
        """解析编号定义 (numbering.xml)"""
        
        numbering_defs = {}
        
        try:
            numbering_xml = docx_zip.read('word/numbering.xml')
            root = ET.fromstring(numbering_xml)
            
            self._debug_print("解析 numbering.xml")
            
            # 解析抽象编号定义
            abstract_nums = {}
            for abstract_num in root.findall('.//w:abstractNum', self.namespaces):
                abstract_num_id = abstract_num.get(f'{{{self.namespaces["w"]}}}abstractNumId')
                
                levels = {}
                for lvl in abstract_num.findall('.//w:lvl', self.namespaces):
                    ilvl = lvl.get(f'{{{self.namespaces["w"]}}}ilvl')
                    
                    # 获取编号格式
                    lvl_text_elem = lvl.find('.//w:lvlText', self.namespaces)
                    lvl_text = lvl_text_elem.get(f'{{{self.namespaces["w"]}}}val') if lvl_text_elem is not None else ""
                    
                    # 获取起始数字
                    start_elem = lvl.find('.//w:start', self.namespaces)
                    start_val = int(start_elem.get(f'{{{self.namespaces["w"]}}}val')) if start_elem is not None else 1
                    
                    # 获取编号格式类型
                    num_fmt_elem = lvl.find('.//w:numFmt', self.namespaces)
                    num_fmt = num_fmt_elem.get(f'{{{self.namespaces["w"]}}}val') if num_fmt_elem is not None else "decimal"
                    
                    levels[int(ilvl)] = {
                        'lvl_text': lvl_text,
                        'start': start_val,
                        'num_fmt': num_fmt
                    }
                
                abstract_nums[abstract_num_id] = levels
            
            # 解析编号实例
            for num in root.findall('.//w:num', self.namespaces):
                num_id = num.get(f'{{{self.namespaces["w"]}}}numId')
                
                abstract_num_id_elem = num.find('.//w:abstractNumId', self.namespaces)
                if abstract_num_id_elem is not None:
                    abstract_num_id = abstract_num_id_elem.get(f'{{{self.namespaces["w"]}}}val')
                    
                    if abstract_num_id in abstract_nums:
                        numbering_defs[num_id] = abstract_nums[abstract_num_id]
            
            self._debug_print(f"找到 {len(numbering_defs)} 个编号定义")
            
        except KeyError:
            self._debug_print("numbering.xml 不存在")
        except Exception as e:
            self._debug_print(f"解析 numbering.xml 失败: {e}", "ERROR")
        
        return numbering_defs
    
    def parse_styles_xml(self, docx_zip: zipfile.ZipFile) -> Dict[str, Dict]:
        """解析样式定义 (styles.xml)"""
        
        style_defs = {}
        
        try:
            styles_xml = docx_zip.read('word/styles.xml')
            root = ET.fromstring(styles_xml)
            
            self._debug_print("解析 styles.xml")
            
            for style in root.findall('.//w:style[@w:type="paragraph"]', self.namespaces):
                style_id = style.get(f'{{{self.namespaces["w"]}}}styleId')
                name_elem = style.find('.//w:name', self.namespaces)
                name = name_elem.get(f'{{{self.namespaces["w"]}}}val') if name_elem is not None else ''
                
                # 检查大纲级别
                outline_level = None
                outline_elem = style.find('.//w:outlineLvl', self.namespaces)
                if outline_elem is not None:
                    outline_level = int(outline_elem.get(f'{{{self.namespaces["w"]}}}val'))
                
                # 扩展标题样式识别
                heading_level = self.detect_heading_level_from_style(name, style_id)
                is_heading = heading_level is not None
                
                # 排除7级及以上标题
                if is_heading and heading_level >= 7:
                    self._debug_print(f"排除过深标题样式: {name} (级别{heading_level})", "EXCLUDE")
                    is_heading = False
                    heading_level = None
                
                if outline_level is not None and outline_level >= 6:
                    self._debug_print(f"排除过深大纲级别: {name} (大纲级别{outline_level})", "EXCLUDE")
                    outline_level = None
                
                style_defs[style_id] = {
                    'name': name,
                    'is_heading': is_heading,
                    'heading_level': heading_level,
                    'outline_level': outline_level
                }
            
            self._debug_print(f"找到 {len(style_defs)} 个段落样式")
            
        except KeyError:
            self._debug_print("styles.xml 不存在")
        except Exception as e:
            self._debug_print(f"解析 styles.xml 失败: {e}", "ERROR")
        
        return style_defs
    
    def detect_heading_level_from_style(self, style_name: str, style_id: str) -> Optional[int]:
        """从样式名称检测标题级别（全面增强版）"""
        
        if not style_name and not style_id:
            return None
        
        # 将样式名称和ID都纳入检测范围
        text_to_check = f"{style_name} {style_id}".lower()
        
        # 模式1：英文标题格式
        english_patterns = [
            r'heading\s*(\d+)',          # Heading 1, Heading1, heading 2
            r'title\s*(\d+)',            # Title 1, title2
            r'level\s*(\d+)',            # Level 1, level2
            r'head\s*(\d+)',             # Head 1, head2
        ]
        
        # 模式2：中文数字格式
        chinese_digit_patterns = [
            r'标题\s*(\d+)',              # 标题1, 标题 2
            r'(\d+)\s*级标题',            # 1级标题, 2级标题
            r'第(\d+)级标题',             # 第1级标题, 第2级标题
            r'(\d+)\s*级条标题',          # 1级条标题, 2级条标题
            r'(\d+)\s*级',                # 1级, 2级
            r'正文标题\s*(\d+)',          # 正文标题1, 正文标题2
            r'章节标题\s*(\d+)',          # 章节标题1, 章节标题2
            r'测试标题\s*(\d+)',          # 测试标题1, 测试标题2
        ]
        
        # 模式3：中文文字格式
        chinese_text_patterns = [
            r'一级(条?标题|标题|条|)',     # 一级标题, 一级条标题, 一级条, 一级
            r'二级(条?标题|标题|条|)',     # 二级标题, 二级条标题, 二级条, 二级
            r'三级(条?标题|标题|条|)',     # 三级标题, 三级条标题, 三级条, 三级
            r'四级(条?标题|标题|条|)',     # 四级标题, 四级条标题, 四级条, 四级
            r'五级(条?标题|标题|条|)',     # 五级标题, 五级条标题, 五级条, 五级
            r'六级(条?标题|标题|条|)',     # 六级标题, 六级条标题, 六级条, 六级
        ]
        
        # 模式4：中文序数格式
        chinese_ordinal_patterns = [
            r'标题(一|二|三|四|五|六)',     # 标题一, 标题二, 标题三
            r'第(一|二|三|四|五|六)级',     # 第一级, 第二级, 第三级
            r'第(一|二|三|四|五|六)章',     # 第一章, 第二章, 第三章
            r'第(一|二|三|四|五|六)节',     # 第一节, 第二节, 第三节
        ]
        
        # 模式5：特殊格式
        special_patterns = [
            r'章标题',                    # 章标题 → 1级
            r'节标题',                    # 节标题 → 2级  
            r'条标题',                    # 条标题 → 3级
            r'款标题',                    # 款标题 → 4级
            r'项标题',                    # 项标题 → 5级
            r'目标题',                    # 目标题 → 6级
        ]
        
        # 检测英文和中文数字格式
        for patterns in [english_patterns, chinese_digit_patterns]:
            for pattern in patterns:
                match = re.search(pattern, text_to_check)
                if match:
                    level = int(match.group(1))
                    if 1 <= level <= 6:  # 只接受1-6级
                        return level
        
        # 检测中文文字格式
        chinese_level_map = {
            '一级': 1, '二级': 2, '三级': 3, 
            '四级': 4, '五级': 5, '六级': 6
        }
        
        for pattern in chinese_text_patterns:
            match = re.search(pattern, text_to_check)
            if match:
                level_text = match.group(0)[:2]  # 取前两个字符，如"一级"
                if level_text in chinese_level_map:
                    return chinese_level_map[level_text]
        
        # 检测中文序数格式
        chinese_ordinal_map = {
            '一': 1, '二': 2, '三': 3, 
            '四': 4, '五': 5, '六': 6
        }
        
        for pattern in chinese_ordinal_patterns:
            match = re.search(pattern, text_to_check)
            if match:
                ordinal = match.group(1)
                if ordinal in chinese_ordinal_map:
                    return chinese_ordinal_map[ordinal]
        
        # 检测特殊格式
        special_level_map = {
            '章标题': 1, '节标题': 2, '条标题': 3,
            '款标题': 4, '项标题': 5, '目标题': 6
        }
        
        for pattern in special_patterns:
            if re.search(pattern, text_to_check):
                return special_level_map[pattern.replace('\\', '')]
        
        return None
    
    def parse_document_xml(self, docx_zip: zipfile.ZipFile) -> List[Dict[str, Any]]:
        """解析文档内容 (document.xml)"""
        
        paragraphs = []
        char_offset = 0
        
        try:
            document_xml = docx_zip.read('word/document.xml')
            root = ET.fromstring(document_xml)
            
            self._debug_print("🔍 开始解析 document.xml")
            
            total_paras = len(root.findall('.//w:p', self.namespaces))
            self._debug_print(f"📊 文档总段落数: {total_paras}")
            
            for para_index, para in enumerate(root.findall('.//w:p', self.namespaces)):
                para_info = self._parse_paragraph(para, para_index, char_offset)
                
                # 详细调试信息
                if self.debug_mode and para_info:
                    text_preview = para_info['text'][:100] + ('...' if len(para_info['text']) > 100 else '')
                    print(f"📄 段落{para_index}: '{text_preview}'")
                    print(f"    numId={para_info['num_id']}, ilvl={para_info['ilvl']}")
                    print(f"    styleId='{para_info['style_id']}', outlineLevel={para_info['outline_level']}")
                    
                    # 增加大纲级别的详细分析
                    if para_info['outline_level'] is not None:
                        actual_level = para_info['outline_level'] + 1  # Word大纲级别从0开始，我们从1开始
                        print(f"    🎯 大纲级别检测: XML级别={para_info['outline_level']} -> 实际级别={actual_level}")
                    
                    # 分析是否可能是标题
                    is_likely_heading = (
                        para_info['num_id'] is not None or  # 有自动编号
                        para_info['outline_level'] is not None or  # 有大纲级别
                        (para_info['style_id'] and any(pattern in para_info['style_id'].lower() 
                                                     for pattern in ['heading', 'title', '标题']))  # 标题样式
                    )
                    if is_likely_heading:
                        print(f"    🔍 可能的标题特征检测通过")
                
                if para_info and para_info['text'].strip():
                    paragraphs.append(para_info)
                    # 更新字符偏移量（包括文本长度和换行符）
                    char_offset += len(para_info['text']) + 1
                    
                    if self.debug_mode:
                        print(f"    ✓ 保留为第{len(paragraphs)}个有效段落")
                elif self.debug_mode and para_info:
                    print(f"    ❌ 跳过空段落")
            
            self._debug_print(f"✅ 解析完成，有效段落数: {len(paragraphs)}/{total_paras}")
            
        except Exception as e:
            self._debug_print(f"❌ 解析 document.xml 失败: {e}", "ERROR")
            import traceback
            if self.debug_mode:
                print(f"详细错误信息: {traceback.format_exc()}")
            raise
        
        return paragraphs
    
    def _parse_paragraph(self, para_elem, para_index: int = 0, char_start_offset: int = 0) -> Optional[Dict[str, Any]]:
        """解析单个段落"""
        
        # 获取段落属性
        para_props = para_elem.find('.//w:pPr', self.namespaces)
        
        # 获取文本内容
        text_parts = []
        for text_elem in para_elem.findall('.//w:t', self.namespaces):
            if text_elem.text:
                text_parts.append(text_elem.text)
        
        text = ''.join(text_parts).strip()
        if not text:
            return None
        
        # 获取编号信息
        num_pr = para_props.find('.//w:numPr', self.namespaces) if para_props is not None else None
        num_id = None
        ilvl = None
        
        if num_pr is not None:
            num_id_elem = num_pr.find('.//w:numId', self.namespaces)
            ilvl_elem = num_pr.find('.//w:ilvl', self.namespaces)
            
            num_id = num_id_elem.get(f'{{{self.namespaces["w"]}}}val') if num_id_elem is not None else None
            ilvl = int(ilvl_elem.get(f'{{{self.namespaces["w"]}}}val')) if ilvl_elem is not None else None
        
        # 获取样式信息
        style_id = None
        if para_props is not None:
            style_elem = para_props.find('.//w:pStyle', self.namespaces)
            style_id = style_elem.get(f'{{{self.namespaces["w"]}}}val') if style_elem is not None else None
        
        # 获取大纲级别
        outline_lvl = None
        if para_props is not None:
            outline_lvl_elem = para_props.find('.//w:outlineLvl', self.namespaces)
            outline_lvl = int(outline_lvl_elem.get(f'{{{self.namespaces["w"]}}}val')) if outline_lvl_elem is not None else None
        
        return {
            'text': text,
            'num_id': num_id,
            'ilvl': ilvl,
            'style_id': style_id,
            'outline_level': outline_lvl,
            'char_count': len(text),
            # 新增位置信息
            'paragraph_index': para_index,
            'char_start_offset': char_start_offset,
            'char_end_offset': char_start_offset + len(text)
        } 