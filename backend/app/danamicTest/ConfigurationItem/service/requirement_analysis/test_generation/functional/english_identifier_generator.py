"""
英文标识生成器

专门负责生成各种类型测试项的英文标识，统一管理标识生成规则。
从realtime_processor.py、functional_test_creator.py等文件中提取出来的功能。
"""

from typing import Dict, Any, Optional

# 灵活的日志导入
try:
    from .....utils.logging_utils.logger import log_info, log_warning, log_error, log_debug
except ImportError:
    try:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_warning, log_error, log_debug
    except ImportError:
        # 如果无法导入，定义占位符函数
        def log_info(msg, tag=""): print(f"[INFO] {msg}")
        def log_debug(msg, tag=""): print(f"[DEBUG] {msg}")
        def log_warning(msg, tag=""): print(f"[WARNING] {msg}")
        def log_error(msg, tag=""): print(f"[ERROR] {msg}")


class EnglishIdentifierGenerator:
    """英文标识生成器"""
    
    def __init__(self):
        self.logger_name = "english_identifier_generator"
    
    def generate_functional_identifier(self, original_item: Dict[str, Any], index: int) -> str:
        """
        生成功能测试项的英文标识
        
        优先级：
        1. 从需求描述中提取标识号
        2. 从追踪字段提取接口标识
        3. AI翻译需求名称
        4. 默认格式
        
        Args:
            original_item: 原始测试项数据
            index: 测试项索引（0开始）
            
        Returns:
            str: 英文标识
        """
        log_debug(f"[IDENTIFIER] 开始生成功能测试项英文标识 (第{index+1}个)", self.logger_name)
        
        # 优先级1：从需求描述中提取标识号
        requirement_desc = original_item.get('requirement_description', {})
        if isinstance(requirement_desc, dict):
            identifier = requirement_desc.get('identifier') or requirement_desc.get('标识号')
            if identifier and str(identifier).strip():
                result = str(identifier).strip().replace(' ', '')
                log_info(f"[IDENTIFIER] 使用需求描述中的标识号: {result}", self.logger_name)
                return result
        
        # 优先级2：从追踪字段提取接口标识
        trace_val = original_item.get('software_requirement_trace', '')
        if isinstance(trace_val, str) and trace_val.strip():
            result = trace_val.strip().replace(' ', '')
            log_info(f"[IDENTIFIER] 使用追踪字段中的标识: {result}", self.logger_name)
            return result
        
        # 优先级3：AI翻译需求名称
        requirement_name = original_item.get('name', f'测试项{index+1}')
        try:
            ai_identifier = self._translate_chinese_to_english(requirement_name)
            if ai_identifier:
                log_info(f"[IDENTIFIER] AI翻译结果: '{requirement_name}' -> '{ai_identifier}'", self.logger_name)
                return ai_identifier
        except Exception as e:
            log_warning(f"[IDENTIFIER] AI翻译失败: {e}", self.logger_name)
        
        # 优先级4：默认格式
        default_id = f"Function{index+1:03d}"
        log_info(f"[IDENTIFIER] 使用默认标识: {default_id}", self.logger_name)
        return default_id
    
    def generate_performance_chapter_identifier(self, performance_index: int) -> str:
        """
        生成从性能章节提取的性能测试项英文标识
        
        Args:
            performance_index: 性能测试项索引（0开始）
            
        Returns:
            str: 英文标识，格式：ChapterPerf001
        """
        identifier = f"ChapterPerf{performance_index+1:03d}"
        log_debug(f"[IDENTIFIER] 生成性能章节测试项标识: {identifier}", self.logger_name)
        return identifier
    
    def generate_allowance_chapter_identifier(self, allowance_index: int) -> str:
        """
        生成从性能章节提取的余量测试项英文标识
        
        Args:
            allowance_index: 余量测试项索引（0开始）
            
        Returns:
            str: 英文标识，格式：ChapterAllow001
        """
        identifier = f"ChapterAllow{allowance_index+1:03d}"
        log_debug(f"[IDENTIFIER] 生成余量章节测试项标识: {identifier}", self.logger_name)
        return identifier
    
    def generate_fixed_allowance_identifier(self, allowance_index: int) -> str:
        """
        生成固定余量测试项英文标识
        
        Args:
            allowance_index: 余量测试项索引（0开始）
            
        Returns:
            str: 英文标识，格式：AllowanceTest001
        """
        identifier = f"AllowanceTest{allowance_index+1:03d}"
        log_debug(f"[IDENTIFIER] 生成固定余量测试项标识: {identifier}", self.logger_name)
        return identifier
    
    def generate_strength_test_identifier(self, strength_index: int) -> str:
        """
        生成强度测试项英文标识
        
        Args:
            strength_index: 强度测试项索引（0开始）
            
        Returns:
            str: 英文标识，格式：StrengthTest001
        """
        identifier = f"StrengthTest{strength_index+1:03d}"
        log_debug(f"[IDENTIFIER] 生成强度测试项标识: {identifier}", self.logger_name)
        return identifier
    
    def generate_interface_test_identifier(self, interface_index: int) -> str:
        """
        生成接口测试项英文标识
        
        Args:
            interface_index: 接口测试项索引（0开始）
            
        Returns:
            str: 英文标识，格式：InterfaceTest001
        """
        identifier = f"InterfaceTest{interface_index+1:03d}"
        log_debug(f"[IDENTIFIER] 生成接口测试项标识: {identifier}", self.logger_name)
        return identifier
    
    def generate_reliability_test_identifier(self, reliability_index: int) -> str:
        """
        生成可靠性测试项英文标识
        
        Args:
            reliability_index: 可靠性测试项索引（0开始）
            
        Returns:
            str: 英文标识，格式：ReliabilityTest001
        """
        identifier = f"ReliabilityTest{reliability_index+1:03d}"
        log_debug(f"[IDENTIFIER] 生成可靠性测试项标识: {identifier}", self.logger_name)
        return identifier
    
    def _translate_chinese_to_english(self, chinese_text: str) -> Optional[str]:
        """
        使用AI翻译中文到英文标识符
        
        Args:
            chinese_text: 中文文本
            
        Returns:
            Optional[str]: 英文标识符，失败返回None
        """
        try:
            # 尝试导入AI翻译功能
            try:
                from ..ai_services.ai_content_optimizer import translate_chinese_to_english
            except ImportError:
                try:
                    from app.danamicTest.ConfigurationItem.service.requirement_analysis.test_generation.ai_services.ai_content_optimizer import translate_chinese_to_english
                except ImportError:
                    log_warning(f"[IDENTIFIER] AI翻译模块未找到", self.logger_name)
                    return None
            
            return translate_chinese_to_english(chinese_text)
        except Exception as e:
            log_warning(f"[IDENTIFIER] AI翻译失败: {e}", self.logger_name)
            return None


# 全局实例
identifier_generator = EnglishIdentifierGenerator() 