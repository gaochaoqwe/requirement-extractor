"""
表单构建工具模块
包含表单构建过程中使用的通用工具方法
"""

import os
import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

try:
    from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

# 需求位置缓存管理器
try:
    from ...utils.position_cache_manager import RequirementPositionCacheManager
except ImportError:
    log_warning("无法导入RequirementPositionCacheManager，将跳过位置缓存功能")
    RequirementPositionCacheManager = None


def extract_requirements_from_catalog(catalog_file_path: str, requirement_file_path: str = None, session_id: str = None) -> Dict[str, str]:
    """
    从需求目录文档中提取需求条目
    
    完整保留原始form_builder_service.py中的_extract_requirements_from_catalog逻辑
    包括多层回退机制和完整的错误处理
    
    Args:
        catalog_file_path: 目录文档路径
        requirement_file_path: 需求文档路径（用于位置缓存）
        session_id: 会话ID（用于位置缓存）
        
    Returns:
        Dict[str, str]: 提取的需求字典
    """
    try:
        from ..requirement_analysis import DocxRequirementParser
        
        # 创建需求规格说明匹配器
        spec_matcher = DocxRequirementParser()
        
        # 如果有需求规格说明文档，使用完整流程
        if requirement_file_path and os.path.exists(requirement_file_path):
            # log_info("使用需求规格说明匹配流程", "form_utils")
            
            # 首先尝试使用最新的增强算法
            if hasattr(spec_matcher, 'generate_requirements_from_spec_enhanced'):
                # log_info("尝试使用最新增强算法", "form_utils")
                enhanced_requirements = spec_matcher.generate_requirements_from_spec_enhanced(
                    catalog_file_path=catalog_file_path,
                    requirement_file_path=requirement_file_path
                )
                
                if enhanced_requirements:
                    # log_info(f"最新增强算法成功获取到 {len(enhanced_requirements)} 个需求", "form_utils")
                    return enhanced_requirements
                else:
                    # log_warning("最新增强算法未获取到需求，回退到传统方法", "form_utils")
            
                    pass
            # 回退到传统算法
            # log_info("使用传统需求规格说明匹配", "form_utils")
            requirements = spec_matcher.generate_requirements_from_spec(
                catalog_file_path=catalog_file_path,
                requirement_file_path=requirement_file_path,
                session_id=session_id
            )
            
            if requirements:
                # log_info(f"传统算法获取到 {len(requirements)} 个需求", "form_utils")
                return requirements
                
        # 如果需求匹配失败或没有需求文档，回退到目录解析
        # log_info("回退到基础目录解析", "form_utils")
        requirement_chapters = spec_matcher.parse_catalog_document(catalog_file_path)
        
        if requirement_chapters:
            # log_info(f"从目录解析获取到 {len(requirement_chapters)} 个章节", "form_utils")
            # 为每个章节提供基础描述
            basic_requirements = {}
            for req_name in requirement_chapters.keys():
                basic_requirements[req_name] = f"验证{req_name}的功能实现和性能要求"
            return basic_requirements
                
        # 🚫 移除默认需求，强制要求正确的数据提取
        log_error("❌ 未能从任何来源提取需求条目，拒绝使用默认数据！", "form_utils")
        return {}
        
    except Exception as e:
        log_error(f"❌ 提取需求条目时发生错误: {e}", "form_utils", e)
        # 🚫 移除默认需求，强制要求正确的数据提取
        return {}


def read_first_two_rows_as_dict(file_path: str) -> Dict[str, str]:
    """
    读取Word文档的前两行作为字典（可选功能，失败时返回空字典）
    
    Args:
        file_path: 文件路径
        
    Returns:
        Dict[str, str]: 提取的信息字典（如果失败则为空字典）
    """
    try:
        from ...utils.document_utils.docx_reader import read_word_first_two_rows
        result = read_word_first_two_rows(file_path)
        # log_debug(f"从文档前两行提取信息成功: {result}", "form_utils")
        return result
    except Exception as e:
        # 🔧 将错误级别降低为debug，因为这是可选功能，系统有其他机制提取软件信息
        # log_debug(f"从文档前两行提取信息失败（将使用用户提供的信息）: {e}", "form_utils")
        return {}


def update_software_info_with_user_data(ruanjian_xinxi: Dict, user_info: Dict):
    """
    使用用户提供的信息更新软件信息
    
    Args:
        ruanjian_xinxi: 原始软件信息字典（会被修改）
        user_info: 用户提供的信息字典
    """
    if not user_info:
        return
        
    # 更新软件名称
    if user_info.get('software_name'):
        ruanjian_xinxi['软件名称'] = user_info['software_name']
        # log_info(f"更新软件名称: {user_info['software_name']}", "form_utils")
    
    # 更新软件版本
    if user_info.get('software_version'):
        ruanjian_xinxi['被测软件版本'] = user_info['software_version']
        # log_info(f"更新软件版本: {user_info['software_version']}", "form_utils")
    
    # 更新软件标识
    if user_info.get('software_id'):
        ruanjian_xinxi['软件标识'] = user_info['software_id']
        # log_info(f"更新软件标识: {user_info['software_id']}", "form_utils")


def extract_software_name(ruanjian_xinxi: Dict, user_info: Dict) -> str:
    """
    提取软件名称
    
    Args:
        ruanjian_xinxi: 软件信息字典
        user_info: 用户信息字典
        
    Returns:
        str: 软件名称
    """
    # 优先使用用户提供的软件名称
    if user_info and user_info.get('software_name'):
        return user_info['software_name']
    
    # 从软件信息中提取
    if '软件名称' in ruanjian_xinxi:
        return ruanjian_xinxi['软件名称']
    
    # 默认名称
    return "未知软件"


def prepare_final_requirements(requirements_dict: Dict[str, str], software_name: str) -> Dict:
    """
    准备最终的需求描述
    
    Args:
        requirements_dict: 需求字典
        software_name: 软件名称
        
    Returns:
        Dict: 处理后的需求字典
    """
    try:
        # log_debug(f"准备最终需求 - 输入需求数量: {len(requirements_dict)}", "form_utils")
        # log_debug(f"软件名称: {software_name}", "form_utils")
        
        # 过滤和清理需求
        final_requirements = {}
        
        for req_id, req_data in requirements_dict.items():
            if isinstance(req_data, dict):
                # 如果是字典格式，保持结构
                final_requirements[req_id] = req_data
            else:
                # 如果是字符串，转换为字典格式
                final_requirements[req_id] = {
                    'name': str(req_data),
                    'description': str(req_data)
                }
        
        # log_info(f"最终需求准备完成: {len(final_requirements)} 个条目", "form_utils")
        return final_requirements
        
    except Exception as e:
        # log_error(f"准备最终需求时发生错误: {e}", "form_utils")
        return requirements_dict


def validate_word_document(file_path: str) -> Tuple[bool, str]:
    """
    验证Word文档的有效性
    
    完整保留原始form_builder_service.py中的check_word_document_xuqiushuoming逻辑
    
    Args:
        file_path: 文档路径
        
    Returns:
        tuple[bool, str]: (是否有效, 错误信息)
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return False, "文件不存在"
        
        # 检查文件扩展名
        if not file_path.lower().endswith('.docx'):
            return False, "文件格式不正确，需要.docx格式"
        
        # 尝试读取文档
        try:
            from docx import Document
            doc = Document(file_path)
            
            # 检查文档是否有内容
            if len(doc.paragraphs) == 0:
                return False, "文档内容为空"
            
            return True, ""
            
        except Exception as e:
            return False, f"文档读取失败: {str(e)}"
            
    except Exception as e:
        return False, f"文档检查失败: {str(e)}"


def clean_requirement_text(text: str) -> str:
    """
    清理需求文本，移除多余的空白字符和特殊字符
    
    Args:
        text: 原始文本
        
    Returns:
        str: 清理后的文本
    """
    if not text:
        return ""
    
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    
    # 移除首尾空白
    text = text.strip()
    
    # 移除特殊的Unicode字符
    text = re.sub(r'[\ufeff\u200b\u200c\u200d]', '', text)
    
    return text


def format_requirement_id(index: int, prefix: str = "REQ") -> str:
    """
    格式化需求ID
    
    Args:
        index: 需求索引（从1开始）
        prefix: ID前缀
        
    Returns:
        str: 格式化的需求ID
    """
    return f"{prefix}-{index:03d}"


def extract_chapter_number(text: str) -> str:
    """
    从文本中提取章节编号
    
    Args:
        text: 包含章节编号的文本
        
    Returns:
        str: 章节编号
    """
    # 常见的章节编号格式
    patterns = [
        r'(\d+(?:\.\d+)*)\s*[．.]?',  # 1.1.1、1.2.3 等格式
        r'第?([一二三四五六七八九十\d]+)章',  # 第一章、第二章等
        r'([ABCDEFGHIJKLMNOPQRSTUVWXYZ](?:\.\d+)*)',  # A.1、B.2.1等
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return ""


def get_default_software_info() -> Dict[str, str]:
    """
    获取默认的软件信息模板
    
    Returns:
        Dict[str, str]: 默认软件信息
    """
    return {
        '软件名称': '未知软件',
        '软件标识': 'UNKNOWN',
        '被测软件版本': '1.0.0',
        '所属领域': '通用软件',
        '飞机型号': '通用型号',
        '项目总师': '待确定',
        '开发部门': '软件研发部',
        '总设计师': '待确定'
    } 