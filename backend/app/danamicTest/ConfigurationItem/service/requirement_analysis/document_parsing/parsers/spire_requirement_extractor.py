#!/usr/bin/env python3
"""
基于Spire.Doc的文档结构化匹配器
专门负责使用 Spire.Doc 库进行高精度的文档结构分析和需求匹配

核心功能：
1. 文档结构化提取 - 使用 Spire.Doc 精确解析 Word 文档结构
2. 章节级匹配 - 基于章节编号 + 标题的双重匹配机制  
3. 内容定位 - 精确定位需求条目的详细内容

匹配格式：
3.2.1 用户身份验证功能  
a) 标识号：REQ-1.1  
b) 说明：用户登录时必须通过多因素身份验证（MFA）确保安全性。  
c) 进入条件：用户尝试访问系统受限资源。  
...

技术特点：
- 依赖 Spire.Doc 库进行文档解析
- 支持复杂文档结构的精确识别
- 提供回退到传统匹配器的机制
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# 导入 spire_doc 模块
try:
    from app.danamicTest.ConfigurationItem.utils.spire_doc import SpireCatalogExtractor
    SPIRE_DOC_AVAILABLE = True
except ImportError as e:
    SPIRE_DOC_AVAILABLE = False
    print(f"Warning: spire.doc module not available: {e}")

# 导入日志工具
try:
    from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_debug, log_warning
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_error, log_debug, log_warning
    except ImportError:
        try:
            from .....utils.logging_utils.logger import log_info, log_error, log_debug, log_warning
        except ImportError:
            # 作为后备，使用print语句
            def log_info(msg, tag=""): print(f"INFO [{tag}] {msg}")
            def log_error(msg, tag=""): print(f"ERROR [{tag}] {msg}")
            def log_debug(msg, tag=""): print(f"DEBUG [{tag}] {msg}")
            def log_warning(msg, tag=""): print(f"WARNING [{tag}] {msg}")

class SpireRequirementExtractor:
    """基于Spire.Doc的需求提取器"""
    
    def __init__(self):
        """初始化匹配器"""
        self.spire_extractor = SpireCatalogExtractor() if SPIRE_DOC_AVAILABLE else None
        # 延迟导入避免循环导入
        self.fallback_matcher = None
        

    
    def _get_fallback_matcher(self):
        """获取回退匹配器（延迟加载）"""
        if self.fallback_matcher is None:
            try:
                from .requirement_spec_matcher import RequirementSpecMatcher
                self.fallback_matcher = RequirementSpecMatcher()
                log_debug("回退匹配器初始化成功", "enhanced_requirement_matcher")
            except Exception as e:
                log_error(f"回退匹配器初始化失败: {e}", "enhanced_requirement_matcher", e)
                # 如果无法创建回退匹配器，创建一个简单的回退方案
                self.fallback_matcher = self._create_simple_fallback()
        return self.fallback_matcher
    
    def _create_simple_fallback(self):
        """创建简单的回退方案"""
        class SimpleFallback:
            def find_requirement_content(self, file_path, requirement_names):
                """简单的回退实现"""
                return {}
        return SimpleFallback()
    

    
    def find_requirement_content_enhanced(self, requirement_file_path: str, requirement_list: List[Dict[str, str]]) -> Dict[str, Dict]:
        """
        增强版需求内容查找方法
        支持章节编号 + 需求名称的精确匹配
        
        Args:
            requirement_file_path: 需求规格说明文档路径
            requirement_list: 需求列表，每个需求包含 {'numbering': '3.2.1', 'title': '用户身份验证功能'}
            
        Returns:
            需求详细信息字典 {需求标识: {标识号, 说明, 处理过程, 性能要求等}}
        """
        if not os.path.exists(requirement_file_path):
            log_error(f"需求规格说明文档不存在: {requirement_file_path}", "enhanced_requirement_matcher")
            return {}
        
        if not SPIRE_DOC_AVAILABLE or not self.spire_extractor:
            log_info("spire_doc不可用，使用回退方案", "enhanced_requirement_matcher")
            # 提取需求名称列表用于回退方案
            requirement_names = [req.get('title', '') for req in requirement_list]
            return self._get_fallback_matcher().find_requirement_content(requirement_file_path, requirement_names)
        
        try:
            log_info(f"开始使用增强版匹配器分析文档: {requirement_file_path}", "enhanced_requirement_matcher")
            
            # 使用 spire_doc 提取文档中的所有结构化信息
            document_sections = self._extract_document_sections(requirement_file_path)
            
            if not document_sections:
                log_warning("文档结构化提取失败，使用回退方案", "enhanced_requirement_matcher")
                requirement_names = [req.get('title', '') for req in requirement_list]
                return self._get_fallback_matcher().find_requirement_content(requirement_file_path, requirement_names)
            
            log_info(f"成功提取 {len(document_sections)} 个文档段落", "enhanced_requirement_matcher")
            
            # 对每个需求进行精确匹配
            requirement_details = {}
            for req in requirement_list:
                numbering = req.get('numbering', '')
                title = req.get('title', '')
                
                if not numbering or not title:
                    log_warning(f"跳过无效需求: {req}", "enhanced_requirement_matcher")
                    continue
                
                # 创建需求标识符
                req_key = f"{numbering} {title}"
                
                # 执行精确匹配
                req_detail = self._find_requirement_by_numbering_and_title(
                    document_sections, numbering, title
                )
                
                requirement_details[req_key] = req_detail
                
                log_debug(f"匹配需求: {req_key} -> {req_detail.get('description', '未找到')[:50]}", 
                         "enhanced_requirement_matcher")
            
            log_info(f"成功匹配 {len(requirement_details)} 个需求条目", "enhanced_requirement_matcher")
            return requirement_details
            
        except Exception as e:
            log_error(f"增强版匹配失败: {e}", "enhanced_requirement_matcher", e)
            # 回退到原始匹配器
            requirement_names = [req.get('title', '') for req in requirement_list]
            return self._get_fallback_matcher().find_requirement_content(requirement_file_path, requirement_names)
    
    def _extract_document_sections(self, requirement_file_path: str) -> List[Dict]:
        """
        使用 spire_doc 提取文档的结构化章节信息
        
        Returns:
            章节信息列表，每个章节包含 {numbering, title, content, level}
        """
        try:
            # 使用 spire_doc 提取全文档信息（不仅仅是3.2.x章节）
            result = self.spire_extractor.extract_full_document_structure(requirement_file_path)
            
            if result.get('success', False):
                return result.get('sections', [])
            else:
                log_error(f"spire_doc提取失败: {result.get('error', '未知错误')}", "enhanced_requirement_matcher")
                return []
                
        except Exception as e:
            log_error(f"文档结构化提取失败: {e}", "enhanced_requirement_matcher", e)
            return []
    
    def _find_requirement_by_numbering_and_title(self, sections: List[Dict], target_numbering: str, target_title: str) -> Dict[str, str]:
        """
        根据章节编号和标题精确查找需求内容
        
        Args:
            sections: 文档章节列表
            target_numbering: 目标章节编号 (如 "3.2.1")
            target_title: 目标标题 (如 "用户身份验证功能")
            
        Returns:
            需求详细信息字典
        """
        requirement_info = {
            'identifier': 'No_find',
            'description': '无',
            'entry_condition': '无', 
            'input': '无',
            'output': '无',
            'processing': '无',
            'performance': '无',
            'constraints': '无'
        }
        
        # 第一步：精确匹配章节编号
        exact_matches = []
        for section in sections:
            section_numbering = section.get('numbering', '')
            section_title = section.get('title', '')
            
            # 精确编号匹配
            if section_numbering == target_numbering:
                exact_matches.append(section)
                log_debug(f"编号精确匹配: {target_numbering} -> {section_title}", "enhanced_requirement_matcher")
        
        # 第二步：在精确匹配的编号中进一步匹配标题
        best_match = None
        if exact_matches:
            for section in exact_matches:
                section_title = section.get('title', '')
                
                # 标题完全匹配
                if section_title == target_title:
                    best_match = section
                    log_debug(f"标题完全匹配: {target_title}", "enhanced_requirement_matcher")
                    break
                
                # 标题部分匹配
                if target_title in section_title or section_title in target_title:
                    best_match = section
                    log_debug(f"标题部分匹配: {target_title} <-> {section_title}", "enhanced_requirement_matcher")
                    break
                
                # 关键词匹配
                if self._calculate_title_similarity(target_title, section_title) > 0.5:
                    best_match = section
                    log_debug(f"标题相似度匹配: {target_title} <-> {section_title}", "enhanced_requirement_matcher")
        
        # 第三步：如果没有精确匹配，尝试模糊匹配
        if not best_match:
            log_debug(f"尝试模糊匹配: {target_numbering} {target_title}", "enhanced_requirement_matcher")
            best_match = self._fuzzy_match_requirement(sections, target_numbering, target_title)
        
        # 第四步：解析匹配到的章节内容
        if best_match:
            content = best_match.get('content', '')
            if content:
                requirement_info = self._extract_requirement_sections_from_content(content, target_title)
                log_info(f"成功匹配需求: {target_numbering} {target_title}", "enhanced_requirement_matcher")
            else:
                log_warning(f"找到匹配章节但内容为空: {target_numbering} {target_title}", "enhanced_requirement_matcher")
        else:
            log_warning(f"未找到匹配的需求: {target_numbering} {target_title}", "enhanced_requirement_matcher")
        
        # 如果没有找到描述，提供默认描述
        if requirement_info['description'] == '无':
            requirement_info['description'] = f'验证{target_title}的功能实现'
        
        return requirement_info
    
    def _fuzzy_match_requirement(self, sections: List[Dict], target_numbering: str, target_title: str) -> Optional[Dict]:
        """
        模糊匹配需求（当精确匹配失败时使用）
        """
        best_match = None
        best_score = 0
        
        for section in sections:
            section_numbering = section.get('numbering', '')
            section_title = section.get('title', '')
            
            # 计算编号相似度
            numbering_score = self._calculate_numbering_similarity(target_numbering, section_numbering)
            
            # 计算标题相似度
            title_score = self._calculate_title_similarity(target_title, section_title)
            
            # 综合评分（编号权重更高）
            total_score = numbering_score * 0.7 + title_score * 0.3
            
            if total_score > best_score and total_score > 0.3:  # 最低阈值
                best_score = total_score
                best_match = section
        
        if best_match:
            log_debug(f"模糊匹配成功，得分: {best_score:.2f}", "enhanced_requirement_matcher")
        
        return best_match
    
    def _calculate_numbering_similarity(self, target: str, candidate: str) -> float:
        """计算章节编号相似度"""
        if not target or not candidate:
            return 0.0
        
        # 完全匹配
        if target == candidate:
            return 1.0
        
        # 前缀匹配 (如 3.2.1 匹配 3.2.1.1)
        if candidate.startswith(target + '.') or target.startswith(candidate + '.'):
            return 0.8
        
        # 部分匹配 (如 3.2.1 与 3.2.2)
        target_parts = target.split('.')
        candidate_parts = candidate.split('.')
        
        common_parts = 0
        max_parts = max(len(target_parts), len(candidate_parts))
        
        for i in range(min(len(target_parts), len(candidate_parts))):
            if target_parts[i] == candidate_parts[i]:
                common_parts += 1
            else:
                break
        
        return common_parts / max_parts if max_parts > 0 else 0.0
    
    def _calculate_title_similarity(self, target: str, candidate: str) -> float:
        """计算标题相似度"""
        if not target or not candidate:
            return 0.0
        
        # 完全匹配
        if target == candidate:
            return 1.0
        
        # 包含匹配
        if target in candidate or candidate in target:
            return 0.8
        
        # 关键词匹配
        target_keywords = set(target.replace('功能', '').replace('模块', '').split())
        candidate_keywords = set(candidate.replace('功能', '').replace('模块', '').split())
        
        if target_keywords and candidate_keywords:
            overlap = len(target_keywords & candidate_keywords)
            union = len(target_keywords | candidate_keywords)
            return overlap / union if union > 0 else 0.0
        
        return 0.0
    
    def _extract_requirement_sections_from_content(self, content: str, req_name: str) -> Dict[str, str]:
        """
        从章节内容中提取需求的a)、b)、c)等详细信息段落
        （复用原始匹配器的逻辑）
        """
        return self._get_fallback_matcher()._extract_requirement_sections_from_content(content, req_name)
    
    # 为了保持兼容性，提供原始接口
    def find_requirement_content(self, requirement_file_path: str, requirement_names: List[str]) -> Dict[str, Dict]:
        """
        兼容性方法：接受需求名称列表，转换为增强版所需的格式
        """
        # 将需求名称列表转换为带编号的格式
        requirement_list = []
        for name in requirement_names:
            # 尝试从名称中提取编号，使用主匹配器的方法
            numbering, title = self._get_fallback_matcher()._parse_requirement_name(name)
            requirement_list.append({
                'numbering': numbering,
                'title': title
            })
        
        return self.find_requirement_content_enhanced(requirement_file_path, requirement_list)
    



# 为 spire_doc 模块添加全文档结构提取功能
def add_full_document_extraction_to_spire():
    """为 SpireCatalogExtractor 添加全文档结构提取功能"""
    
    def extract_full_document_structure(self, docx_path: str) -> Dict[str, any]:
        """
        提取整个文档的结构化信息（不仅仅是3.2.x章节）
        
        Returns:
            包含文档所有章节信息的字典
        """
        try:
            log_info(f"开始提取完整文档结构: {docx_path}", "spire_catalog_extractor")
            
            # 创建Document对象
            from spire.doc import Document
            document = Document()
            document.LoadFromFile(docx_path)
            
            # 提取所有段落
            all_items = self._extract_all_paragraphs(document)
            log_info(f"提取到 {len(all_items)} 个段落", "spire_catalog_extractor")
            
            # 识别所有标题（不只是3.2.x）
            all_headings = self._identify_all_headings(all_items)
            log_info(f"识别到 {len(all_headings)} 个标题", "spire_catalog_extractor")
            
            # 构建章节内容映射
            sections = self._build_section_content_mapping(all_headings, all_items)
            log_info(f"构建了 {len(sections)} 个章节的内容映射", "spire_catalog_extractor")
            
            return {
                'success': True,
                'sections': sections,
                'total_sections': len(sections),
                'message': f'成功提取 {len(sections)} 个章节'
            }
            
        except Exception as e:
            log_error(f"提取完整文档结构失败: {str(e)}", "spire_catalog_extractor")
            return {
                'success': False,
                'error': str(e),
                'sections': [],
                'total_sections': 0,
                'message': f'文档结构提取失败: {str(e)}'
            }
    
    def _identify_all_headings(self, all_items: List[Dict]) -> List[Dict]:
        """识别所有标题（扩展版，不仅限于3.2.x）"""
        headings = []
        
        for item in all_items:
            text = item.get('text', '').strip()
            if not text:
                continue
            
            # 检查是否为标题
            if self._is_heading_text(text):
                numbering, title = self._extract_numbering_and_title(text)
                if numbering or title:
                    level = self._calculate_heading_level(numbering)
                    
                    heading_info = {
                        'numbering': numbering,
                        'title': title,
                        'level': level,
                        'full_text': text,
                        'position': item.get('position', 0)
                    }
                    headings.append(heading_info)
        
        return headings
    
    def _is_heading_text(self, text: str) -> bool:
        """判断文本是否为标题"""
        # 长度过长的一般不是标题
        if len(text) > 100:
            return False
        
        # 包含章节编号格式的
        if re.match(r'^\d+(\.\d+)*\s+.+', text):
            return True
        
        # 样式信息表明是标题的
        # 这里可以根据需要扩展更多判断逻辑
        
        return False
    
    def _extract_numbering_and_title(self, text: str) -> Tuple[str, str]:
        """从文本中提取编号和标题"""
        pattern = r'^(\d+(?:\.\d+)*)\s+(.+)$'
        match = re.match(pattern, text.strip())
        
        if match:
            return match.group(1), match.group(2).strip()
        else:
            return '', text.strip()
    
    def _calculate_heading_level(self, numbering: str) -> int:
        """计算标题级别"""
        if not numbering:
            return 1
        
        return numbering.count('.') + 1
    
    def _build_section_content_mapping(self, headings: List[Dict], all_items: List[Dict]) -> List[Dict]:
        """构建章节与内容的映射关系"""
        sections = []
        
        for i, heading in enumerate(headings):
            # 获取当前标题的位置
            current_pos = heading.get('position', 0)
            
            # 获取下一个标题的位置（用于确定内容范围）
            next_pos = headings[i + 1].get('position', float('inf')) if i + 1 < len(headings) else float('inf')
            
            # 收集当前章节的内容
            section_content = []
            for item in all_items:
                item_pos = item.get('position', 0)
                if current_pos < item_pos < next_pos:
                    item_text = item.get('text', '').strip()
                    if item_text:
                        section_content.append(item_text)
            
            # 构建章节信息
            section_info = {
                'numbering': heading.get('numbering', ''),
                'title': heading.get('title', ''),
                'level': heading.get('level', 1),
                'content': '\n'.join(section_content),
                'full_heading': heading.get('full_text', ''),
                'position': current_pos
            }
            
            sections.append(section_info)
        
        return sections
    
    # 将方法添加到 SpireCatalogExtractor 类
    if SPIRE_DOC_AVAILABLE:
        SpireCatalogExtractor.extract_full_document_structure = extract_full_document_structure
        SpireCatalogExtractor._identify_all_headings = _identify_all_headings
        SpireCatalogExtractor._is_heading_text = _is_heading_text
        SpireCatalogExtractor._extract_numbering_and_title = _extract_numbering_and_title
        SpireCatalogExtractor._calculate_heading_level = _calculate_heading_level
        SpireCatalogExtractor._build_section_content_mapping = _build_section_content_mapping


# 初始化时添加扩展功能
add_full_document_extraction_to_spire()


# 便捷函数
def create_spire_requirement_extractor() -> SpireRequirementExtractor:
    """创建Spire需求提取器实例"""
    return SpireRequirementExtractor()


if __name__ == "__main__":
    # 测试代码
    matcher = create_spire_requirement_extractor()
    
    # 测试需求列表
    test_requirements = [
        {'numbering': '3.2.1', 'title': '用户身份验证功能'},
        {'numbering': '3.2.2', 'title': '数据批量导入功能'},
        {'numbering': '3.2.2.1', 'title': '实时通知推送功能'}
    ]
    
    # 测试文档路径（需要实际文件路径）
    test_doc_path = "test_requirement_spec.docx"
    
    if os.path.exists(test_doc_path):
        results = matcher.find_requirement_content_enhanced(test_doc_path, test_requirements)
        
        print("=== Spire.Doc需求匹配测试结果 ===")
        for req_key, details in results.items():
            print(f"\n需求: {req_key}")
            for field, value in details.items():
                print(f"  {field}: {value}")
    else:
        print(f"测试文档不存在: {test_doc_path}") 