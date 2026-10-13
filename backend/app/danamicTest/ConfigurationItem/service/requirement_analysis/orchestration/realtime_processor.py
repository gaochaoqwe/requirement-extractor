"""
配置项测试需求分析表实时处理服务

实现真正的流式处理：
1. 英文标识最先生成
2. 逐个处理测试项，生成一个存储一个
3. 避免大数组存储所有AI生成内容
"""

import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from ..test_generation.functional.functional_test_creator import ConfigurationItemRequirementAnalysisDataProcessor
from ..test_generation.functional.performance_test_extractor import PerformanceSeparator
from ..test_generation.functional.interface_test_template_generator import InterfaceTestTemplateGenerator  # 🔧 新增：接口测试模板生成器
from ..test_generation.functional.strength_test_generator import StrengthTestGenerator  # 🔧 新增：强度测试生成器
from ..test_generation.functional.allowance_test_generator import AllowanceTestGenerator  # 🔧 新增：余量测试生成器
from ..test_generation.functional.security_test_generator import SecurityTestGenerator  # 🔧 新增：安全性测试生成器
from ..test_generation.functional.maintainability_test_generator import MaintainabilityTestGenerator  # 🔧 新增：可维护性测试生成器
from ..test_generation.functional.reliability_test_generator import ReliabilityTestGenerator  # 🔧 新增：可靠性测试生成器
from ..test_generation.content_generators.test_content_generator import ConfigurationItemTestContentGenerator
from ..content_analysis.interface_analyzer import InterfaceTestExtractor
from ..document_parsing.parsers.performance_chapter_extractor import PerformanceChapterExtractor
from ..content_analysis.performance_analyzer import PerformanceAIAnalyzer
from ..excel_operations.excel_main_filler import ConfigurationItemRequirementAnalysisExcelFiller
from ..excel_operations.formatting.table_formatter import ConfigurationItemRequirementAnalysisFormatter
from ..excel_operations.excel_reader import ConfigurationItemRequirementAnalysisReader
from ..document_parsing.parsers.interface_table_parser import InterfaceTableParser

# 导入任务日志函数
from ....utils.logging_utils.logger import log_info, log_debug, log_error, log_warning

# 配置日志
logger = logging.getLogger(__name__)

# 导入英文标识生成器
from ..test_generation.functional.english_identifier_generator import identifier_generator

class RealtimeRequirementAnalysisService:
    """实时配置项测试需求分析表服务"""
    
    def __init__(self):
        """初始化实时处理服务"""
        self.logger = logger
        self.data_processor = ConfigurationItemRequirementAnalysisDataProcessor()
        self.excel_filler = ConfigurationItemRequirementAnalysisExcelFiller()
        self.formatter = ConfigurationItemRequirementAnalysisFormatter()
        self.reader = ConfigurationItemRequirementAnalysisReader()
        self.test_content_generator = ConfigurationItemTestContentGenerator()
        self.interface_extractor = InterfaceTestExtractor()
        self.interface_parser = InterfaceTableParser()
        self.performance_separator = PerformanceSeparator()
        self.performance_chapter_extractor = PerformanceChapterExtractor()
        self.performance_ai_analyzer = PerformanceAIAnalyzer()
        self.interface_test_template_generator = InterfaceTestTemplateGenerator() # 🔧 初始化接口测试模板生成器
        self.strength_test_generator = StrengthTestGenerator()  # 🔧 初始化强度测试生成器
        self.allowance_test_generator = AllowanceTestGenerator()  # 🔧 初始化余量测试生成器
        self.security_test_generator = SecurityTestGenerator()  # 🔧 初始化安全性测试生成器
        self.maintainability_test_generator = MaintainabilityTestGenerator()  # 🔧 初始化可维护性测试生成器
        self.reliability_test_generator = ReliabilityTestGenerator()  # 🔧 初始化可靠性测试生成器
    
    def generate_requirement_analysis_table_realtime(
        self,
        excel_file_path: str,
        sheet_name: str,
        ruanjian_xinxi: Dict[str, List[str]],
        ruanjian_name: str,
        diama_biangeng_xuqiu: Dict[str, str],
        file_path: str,
        ceshileixing: str,
        neirong_dict: List[str],
        biaoshihao_ceshixianng: List[str],
        AI_fenx_flag_Anniu: int,
        jianceyi_flag: int,
        apply_formatting: bool = True,
        user_software_info: Optional[Dict[str, str]] = None,
        task_id: Optional[str] = None,
        product_type: Optional[str] = None
    ) -> bool:
        """
        实时生成配置项测试需求分析表
        
        流程：
        1. 提取基础测试项
        2. 逐个处理每个测试项：
           a) 生成英文标识（最先）
           b) 生成测试描述和方法
           c) 立即存储到数据库
           d) 处理性能/边界测试项
           e) 立即存储性能/边界测试项
        """
        try:
            if not task_id:
                self.logger.error("实时处理模式必须提供 task_id")
                return False
            
            log_info(f"[REALTIME] 开始实时生成需求分析表: {sheet_name}", "realtime_service")
            log_info(f"[REALTIME] 产品类型: {product_type}", "realtime_service")
            
            # 保存产品类型到实例变量，供后续方法使用
            self._current_product_type = product_type
            
            # 第一步：提取基础信息和原始测试项（不包含AI生成内容）
            basic_info = self._extract_basic_info(ruanjian_xinxi, user_software_info)
            original_test_items = self._extract_original_test_items(
                diama_biangeng_xuqiu, neirong_dict, biaoshihao_ceshixianng
            )
            
            log_info(f"[REALTIME] 提取到 {len(original_test_items)} 个原始测试项", "realtime_service")
            
            # 第二步：逐个处理测试项
            processed_count = 0
            
            # 🔧 修复：使用独立的索引计数器，避免索引冲突
            current_index = 1  # 当前可用的索引
            
            for i, original_item in enumerate(original_test_items):
                try:
                    log_info(f"[REALTIME] 开始处理第 {i+1} 个测试项: {original_item.get('name')}", "realtime_service")
                    
                    # 2.1 生成英文标识（最先生成）
                    english_identifier = self._generate_english_identifier_first(original_item, i)
                    log_info(f"[REALTIME] 英文标识生成完成: {english_identifier}", "realtime_service")
                    
                    # 2.2 生成功能测试项的完整数据
                    functional_test_item = self._build_complete_test_item(
                        original_item, english_identifier, basic_info, current_index, '功能测试'  # 🔧 使用当前索引
                    )
                    
                    # 2.3 生成AI内容（测试描述和方法）
                    func_requirement_sub_desc, test_description, test_method = self._generate_ai_content_for_single_item(
                        functional_test_item, jianceyi_flag, product_type
                    )
                    # 🔧 功能测试项的需求子项描述保持原有值，不使用AI生成的
                    # functional_test_item['requirement_sub_description'] 保持不变
                    functional_test_item['test_description'] = test_description
                    functional_test_item['test_method'] = test_method
                    
                    # 2.4 立即存储功能测试项
                    if not self._store_single_item_to_db(functional_test_item, task_id):
                        log_error(f"[REALTIME] 功能测试项存储失败: {functional_test_item.get('name')}", "realtime_service")
                        return False
                    
                    processed_count += 1
                    current_index += 1  # 🔧 递增索引
                    log_info(f"[REALTIME] 功能测试项存储完成: {functional_test_item.get('name')}", "realtime_service")
                    
                    # 2.5 处理性能测试项（如果需要）
                    performance_item = self._extract_performance_item(functional_test_item)
                    if performance_item:
                        # 🔧 修复：使用独立的整数索引
                        performance_item['index'] = current_index
                        
                        # 🔧 修改：生成性能测试项的完整AI内容（包括需求子项描述）
                        perf_requirement_sub_desc, perf_description, perf_method = self._generate_ai_content_for_single_item(
                            performance_item, jianceyi_flag
                        )
                        performance_item['requirement_sub_description'] = perf_requirement_sub_desc
                        performance_item['test_description'] = perf_description
                        performance_item['test_method'] = perf_method
                        
                        # 立即存储性能测试项
                        if not self._store_single_item_to_db(performance_item, task_id):
                            log_error(f"[REALTIME] 性能测试项存储失败: {performance_item.get('name')}", "realtime_service")
                            return False
                        
                        processed_count += 1
                        current_index += 1  # 🔧 递增索引
                        log_info(f"[REALTIME] 性能测试项存储完成: {performance_item.get('name')}", "realtime_service")
                    
                    # 2.6 处理边界测试项（如果需要）
                    boundary_item = self._extract_boundary_item(functional_test_item)
                    if boundary_item:
                        # 🔧 修复：使用独立的整数索引
                        boundary_item['index'] = current_index
                        
                        # 🔧 修改：生成边界测试项的完整AI内容（包括需求子项描述）
                        boundary_requirement_sub_desc, boundary_description, boundary_method = self._generate_ai_content_for_single_item(
                            boundary_item, jianceyi_flag
                        )
                        boundary_item['requirement_sub_description'] = boundary_requirement_sub_desc
                        boundary_item['test_description'] = boundary_description
                        boundary_item['test_method'] = boundary_method
                        
                        # 立即存储边界测试项
                        if not self._store_single_item_to_db(boundary_item, task_id):
                            log_error(f"[REALTIME] 边界测试项存储失败: {boundary_item.get('name')}", "realtime_service")
                            return False
                        
                        processed_count += 1
                        current_index += 1  # 🔧 递增索引
                        log_info(f"[REALTIME] 边界测试项存储完成: {boundary_item.get('name')}", "realtime_service")
                
                except Exception as e:
                    log_error(f"[REALTIME] 处理测试项失败: {original_item.get('name')} - {e}", "realtime_service")
                    return False
            
            # 第2.7步：处理接口测试项（在边界测试之后）
            log_info("[REALTIME] 开始处理接口测试项", "realtime_service")
            interface_processed_count = self._process_interface_tests(
                file_path, basic_info, task_id, current_index, jianceyi_flag  # 🔧 传递当前索引
            )
            processed_count += interface_processed_count
            current_index += interface_processed_count  # 🔧 更新索引
            
            # 第2.8步：处理性能章节的测试项（性能测试项和余量测试项）
            log_info("[REALTIME] 开始处理性能章节测试项", "realtime_service")
            chapter_processed_count = self._process_performance_chapter_tests(
                file_path, basic_info, task_id, current_index, jianceyi_flag  # 🔧 传递当前索引
            )
            processed_count += chapter_processed_count
            current_index += chapter_processed_count  # 🔧 更新索引
            
            # 第2.9步：添加安全性测试项
            log_info("[REALTIME] 开始添加安全性测试项", "realtime_service")
            security_processed_count = self._process_security_tests(basic_info, task_id, current_index, jianceyi_flag)
            processed_count += security_processed_count
            current_index += security_processed_count  # 🔧 更新索引
            
            # 第2.10步：添加固定的强度测试项
            log_info("[REALTIME] 开始添加固定强度测试项", "realtime_service")
            strength_processed_count = self._process_fixed_strength_tests(basic_info, task_id, current_index, jianceyi_flag)
            processed_count += strength_processed_count
            current_index += strength_processed_count  # 🔧 更新索引
            
            # 第2.11步：添加可维护性测试项
            log_info("[REALTIME] 开始添加可维护性测试项", "realtime_service")
            maintainability_processed_count = self._process_maintainability_tests(basic_info, task_id, current_index, jianceyi_flag)
            processed_count += maintainability_processed_count
            current_index += maintainability_processed_count  # 🔧 更新索引
            
            # 第2.12步：添加可靠性测试项
            log_info("[REALTIME] 开始添加可靠性测试项", "realtime_service")
            reliability_processed_count = self._process_reliability_tests(basic_info, task_id, current_index, jianceyi_flag)
            processed_count += reliability_processed_count
            current_index += reliability_processed_count  # 🔧 更新索引
            
            # 第三步：从数据库渲染Excel
            log_info(f"[REALTIME] 所有测试项处理完成，共处理 {processed_count} 个，开始渲染Excel", "realtime_service")
            
            if not self.excel_filler.render_from_db(excel_file_path, sheet_name, task_id):
                self.logger.error("从数据库渲染Excel失败")
                return False
            
            # 第四步：应用格式（可选）
            if apply_formatting:
                if not self.formatter.apply_formatting(
                    excel_file_path=excel_file_path,
                    sheet_name=sheet_name,
                    test_count=processed_count
                ):
                    self.logger.warning("格式设置失败，但数据填充成功")
            
            log_info(f"[REALTIME] 实时需求分析表生成完成，共处理 {processed_count} 个测试项", "realtime_service")
            return True
            
        except Exception as e:
            self.logger.error(f"实时生成需求分析表时发生错误: {str(e)}")
            log_error(f"[REALTIME] 生成异常: {str(e)}", "realtime_service", exception=e)
            return False
    
    def _generate_english_identifier_first(self, original_item: Dict[str, Any], index: int) -> str:
        """
        最先生成英文标识，使用新的英文标识生成器
        """
        log_info(f"[REALTIME] 开始生成英文标识 (第{index+1}个测试项)", "realtime_service")
        
        # 使用新的英文标识生成器
        english_identifier = identifier_generator.generate_functional_identifier(original_item, index)
        log_info(f"[REALTIME] 英文标识生成完成: {english_identifier}", "realtime_service")
        
        return english_identifier
    
    def _build_complete_test_item(
        self, 
        original_item: Dict[str, Any], 
        english_identifier: str, 
        basic_info: Dict[str, str], 
        index: int,
        test_type: str = '功能测试'
    ) -> Dict[str, Any]:
        """构建完整的测试项数据，英文标识已经生成"""
        
        software_id = basic_info.get('software_identifier', '')
        software_version = basic_info.get('software_version', '')
        
        # 🔧 修复：根据测试类型生成正确的标识符后缀
        if test_type == '性能测试':
            type_suffix = 'PF01'
        elif test_type == '边界测试':
            type_suffix = 'BD01'
        else:
            type_suffix = 'FN01'  # 功能测试或其他
        
        # 生成依赖英文标识的其他标识符
        standard_requirement_identifier = f"CT-{software_id}-{software_version}-{english_identifier}-{type_suffix}"
        test_item_identifier = f"CT-{software_id}-{software_version}-{english_identifier}-{type_suffix}"
        
        # 生成软件需求规格说明追踪字段
        software_name = basic_info.get('software_name', '')
        requirement_name = original_item.get('name', '')
        
        # 修复：添加章节编号到追踪关系中
        chapter_number = original_item.get('chapter_number', '')
        if chapter_number and chapter_number.strip() and chapter_number != '未找到具体章节号':
            # 格式：《软件名称软件需求规格说明》 章节编号 需求名称
            software_requirement_trace = f"《{software_name}软件需求规格说明》 {chapter_number} {requirement_name}"
        else:
            # 如果没有章节编号，保持原格式
            software_requirement_trace = f"《{software_name}软件需求规格说明》 {requirement_name}"
        
        # 上游名称追踪：构建完整测试项前记录原始名称与pure_name
        try:
            log_info(
                f"[UPSTREAM_NAME_TRACE] BUILD idx={index} raw_name='{requirement_name}' pure_name='{original_item.get('pure_name', '')}'",
                "realtime_service",
            )
        except Exception:
            pass
        
        complete_item = {
            **original_item,
            'index': index,
            'english_identifier': english_identifier,
            'standard_sub_requirement_identifier': standard_requirement_identifier,
            'test_item_identifier': test_item_identifier,
            'software_identifier': software_id,
            'software_version': software_version,
            'software_name': software_name,
            'software_requirement_trace': software_requirement_trace,  # 修复：设置软件需求规格说明追踪
            'adequacy_requirement': '所有用例执行完毕，对于未执行的用例说明未执行原因。',
            'pass_criteria': '各测试步骤、测试用例执行结果与预期一致，功能实现正确'
        }
        
        log_info(f"[REALTIME] 完整测试项构建完成: {complete_item.get('name')}", "realtime_service")
        return complete_item
    
    def _generate_ai_content_for_single_item(self, test_item: Dict[str, Any], jianceyi_flag: int = 0, product_type: Optional[str] = None) -> Tuple[str, str, str]:
        """
        为单个测试项生成AI内容
        
        Args:
            test_item: 测试项字典
            jianceyi_flag: 检测仪标志
            
        Returns:
            Tuple[str, str, str]: (需求子项描述, 测试描述, 测试方法)
        """
        try:
            # 确定测试类型
            test_type = self._determine_test_type(test_item)
            test_name = test_item.get('name', '')
            
            # 🔧 检查是否需要AI生成完整内容（性能和边界测试项）
            if test_item.get('ai_generation_required', False) and test_type in ['性能测试', '边界测试']:
                log_info(f"[REALTIME] 为{test_type}生成完整AI内容（包括需求子项描述）: {test_name}", "realtime_service")
                
                # 获取完整需求内容
                full_requirement = test_item.get('full_requirement_for_ai', '')
                if not full_requirement:
                    full_requirement = test_item.get('requirement_description', '')
                
                # 配置AI参数
                jianceyi_flag_str = "有检测仪" if jianceyi_flag == 1 else "无检测仪"
                ai_config = {
                    'jianceyi_flag': jianceyi_flag_str
                }
                
                # 根据测试类型调用相应的AI生成方法
                if test_type == '性能测试':
                    requirement_sub_desc, test_desc, test_method = self.test_content_generator._generate_performance_test_content(
                        test_name, full_requirement, ai_config
                    )
                elif test_type == '边界测试':
                    requirement_sub_desc, test_desc, test_method = self.test_content_generator._generate_boundary_test_content(
                        test_name, full_requirement, ai_config
                    )
                else:
                    # 不应该到这里，但作为保险
                    requirement_sub_desc = f"{test_type}需求描述"
                    test_desc = f"验证{test_name}的{test_type}是否符合需求规定"
                    test_method = f"按照{test_type}规范对{test_name}进行验证"
                
                log_info(f"[REALTIME] {test_type}完整AI内容生成完成: {test_name}", "realtime_service")
                return requirement_sub_desc, test_desc, test_method
                
            else:
                # 🔧 功能测试项或其他测试项，使用原有逻辑
                test_items = [test_item]  # 只处理一个测试项
                
                # 根据测试类型配置AI选项
                jianceyi_flag_str = "有检测仪" if jianceyi_flag == 1 else "无检测仪"
                ai_config = {
                    'enable_ai': True,
                    'enable_test_description': True,
                    'enable_test_method': True,
                    'jianceyi_flag': jianceyi_flag_str
                }
                
                log_info(f"[REALTIME] 为{test_type}生成AI内容: {test_name} (检测仪: {jianceyi_flag_str})", "realtime_service")
                
                test_descriptions, test_methods = self.test_content_generator.generate_test_content(
                    test_items, ai_config, product_type
                )
                
                description = test_descriptions[0] if test_descriptions else ''
                method = test_methods[0] if test_methods else ''
                
                # 功能测试项的需求子项描述使用原有的requirement_sub_description
                requirement_sub_desc = test_item.get('requirement_sub_description', '')
                
                log_info(f"[REALTIME] AI内容生成完成: {test_name} ({test_type})", "realtime_service")
                return requirement_sub_desc, description, method
            
        except Exception as e:
            log_error(f"[REALTIME] AI内容生成失败: {e}", "realtime_service")
            # 根据测试类型返回相应的默认内容
            test_type = self._determine_test_type(test_item)
            name = test_item.get('name', '功能')
            
            if test_type == '性能测试':
                return (
                    f'{name}的性能要求',
                    f'验证{name}的性能指标是否满足需求规格说明中的性能要求',
                    f'1. 配置性能测试环境；2. 设置性能测试参数和负载；3. 执行{name}相关的性能测试；4. 监控和记录性能数据；5. 验证性能指标是否达标'
                )
            elif test_type == '边界测试':
                return (
                    f'{name}的边界条件',
                    f'验证{name}在边界条件下的处理是否符合需求规格说明中的边界要求',
                    f'1. 确定{name}的边界值范围；2. 设置边界测试用例；3. 执行边界值测试；4. 验证边界处理结果；5. 确认异常边界的处理机制'
                )
            elif test_type == '余量测试':
                return (
                    f'{name}的余量要求',
                    f'验证{name}的余量处理是否符合需求规格说明中的余量要求',
                    f'1. 确定{name}的余量范围；2. 设置余量测试场景；3. 执行余量测试；4. 验证余量处理结果；5. 确认系统在余量条件下的稳定性'
                )
            elif test_type == '强度测试':
                return (
                    f'{name}的强度要求',
                    f'验证{name}在高强度负载下的稳定性是否符合需求规格说明中的强度要求',
                    f'1. 配置强度测试环境；2. 设置高强度负载参数；3. 执行{name}相关的强度测试；4. 监控系统稳定性；5. 验证强度测试结果'
                )
            else:  # 功能测试或其他
                return (
                    test_item.get('requirement_sub_description', f'{name}的功能要求'),
                    f'验证{name}的实现是否符合需求规格说明中的功能要求',
                    f'1. 设置测试环境和条件；2. 执行{name}相关的功能操作；3. 检查功能执行结果；4. 验证结果是否符合预期'
                )
    
    def _store_single_item_to_db(self, test_item: Dict[str, Any], task_id: str) -> bool:
        """将单个测试项立即存储到数据库"""
        try:
            log_info(f"[REALTIME] [DB_DEBUG] 开始存储测试项: {test_item.get('name')}", "realtime_service")
            log_info(f"[REALTIME] [DB_DEBUG] 尝试导入数据库模块...", "realtime_service")
            
            from ....db.optimized_models import OptimizedDynamicTestDatabase
            log_info(f"[REALTIME] [DB_DEBUG] 数据库模块导入成功", "realtime_service")
            
            db = OptimizedDynamicTestDatabase()
            log_info(f"[REALTIME] [DB_DEBUG] 数据库实例创建成功", "realtime_service")
            
            row_index = test_item.get('index', 1)
            log_info(f"[REALTIME] [DB_DEBUG] 行索引: {row_index}", "realtime_service")
            # 上游名称追踪：入库前记录原始名称与pure_name
            try:
                raw_name = test_item.get('name', '')
                pure_name = test_item.get('pure_name', '')
                log_info(
                    f"[UPSTREAM_NAME_TRACE] STORE idx={row_index} raw_name='{raw_name}' pure_name='{pure_name}'",
                    "realtime_service",
                )
            except Exception:
                pass
            
            # 🔧 修复：确保需求名称不带测试类型后缀
            def extract_pure_requirement_name(name: str) -> str:
                """提取纯净的需求名称，去除所有测试类型后缀"""
                if not name:
                    return ''
                
                # 去除各种测试类型后缀（支持中英文括号）
                suffixes_to_remove = [
                    '（性能测试）', '（边界测试）', '（余量测试）', '（强度测试）',
                    '(性能测试)', '(边界测试)', '(余量测试)', '(强度测试)'
                ]
                
                clean_name = str(name).strip()
                for suffix in suffixes_to_remove:
                    if clean_name.endswith(suffix):
                        clean_name = clean_name[:-len(suffix)].strip()
                        break
                
                return clean_name
            
            # 获取纯净的需求名称（不带后缀）
            pure_requirement_name = extract_pure_requirement_name(test_item.get('name', ''))
            
            # 构建行数据
            row_data = {
                'id': f"{task_id}_{int(row_index * 10):04d}",  # 修复：将浮点数转换为整数进行格式化
                'task_id': task_id,
                'requirement_id': f"REQ_{task_id}_{int(row_index * 10):04d}",  # 修复：浮点数格式化
                'index_number': row_index,
                'software_name': test_item.get('software_name', ''),
                'software_version': test_item.get('software_version', ''),
                'round_info': '第一轮',
                'standard_sub_requirement_name': pure_requirement_name,  # 🔧 使用纯净名称
                'standard_sub_requirement_identifier': test_item.get('test_item_identifier', ''),
                'standard_sub_requirement_unit': '0.2',
                'task_requirement_trace': '无',
                'software_requirement_trace': test_item.get('software_requirement_trace', ''),
                'software_requirement_name': pure_requirement_name,  # 🔧 使用纯净名称
                'software_requirement_identifier': test_item.get('english_identifier', ''),
                'requirement_description': self._format_requirement_description(test_item.get('requirement_description', '')),
                'test_type': self._determine_test_type(test_item),
                'test_item_name': test_item.get('name', ''),
                'test_item_identifier': test_item.get('test_item_identifier', ''),
                'process_identifier': test_item.get('software_requirement_trace', ''),
                'requirement_sub_description': test_item.get('requirement_sub_description', self._format_requirement_description(test_item.get('requirement_description', ''))),
                'test_description': test_item.get('test_description', ''),
                'test_method': test_item.get('test_method', ''),
                'adequacy_requirement': test_item.get('adequacy_requirement', ''),
                'pass_criteria': test_item.get('pass_criteria', ''),
                'english_identifier': test_item.get('english_identifier', ''),
                'software_identifier': test_item.get('software_identifier', ''),
                'session_id': 'unknown' # Placeholder, actual session_id would need to be passed or generated
            }
            
            # 🔧 添加调试日志，追踪名称处理过程
            try:
                log_info(
                    f"[UPSTREAM_SAVE_TRACE] SAVE idx={row_index} standard_sub_requirement_name(col6)='{row_data['standard_sub_requirement_name']}', "
                    f"software_requirement_name(col11)='{row_data['software_requirement_name']}', "
                    f"test_item_name='{row_data['test_item_name']}'",
                    "realtime_service",
                )
            except Exception:
                pass
            
            log_info(f"[REALTIME] [DB_DEBUG] 行数据构建完成，开始保存到数据库...", "realtime_service")
            log_info(f"[REALTIME] [DB_DEBUG] Task ID: {task_id}, Row Index: {row_index}", "realtime_service")
            
            result = db.save_requirement_row(task_id, row_index, row_data)
            log_info(f"[REALTIME] [DB_DEBUG] 数据库保存结果: {result}", "realtime_service")
            
            if result is not None:
                log_info(f"[REALTIME] 数据库存储成功: {test_item.get('name')} (行{row_index})", "realtime_service")
                return True
            else:
                log_error(f"[REALTIME] 数据库存储返回None: {test_item.get('name')}", "realtime_service")
                return False
                
        except Exception as e:
            import traceback
            log_error(f"[REALTIME] 数据库存储异常: {test_item.get('name')} - {e}", "realtime_service")
            log_error(f"[REALTIME] [DB_DEBUG] 异常堆栈: {traceback.format_exc()}", "realtime_service")
            return False
    
    def _extract_basic_info(self, ruanjian_xinxi: Dict[str, List[str]], user_software_info: Optional[Dict[str, str]]) -> Dict[str, str]:
        """提取基础信息"""
        # 修复：支持软件标识的多种字段名
        software_identifier = ''
        if user_software_info:
            # 优先使用 software_identifier，然后是兼容字段 software_id
            software_identifier = user_software_info.get('software_identifier', '') or user_software_info.get('software_id', '')
        
        # 如果还是空，从ruanjian_xinxi获取
        if not software_identifier:
            software_identifier = ruanjian_xinxi.get('软件标识', [''])[0]
        
        # 获取软件版本
        software_version = user_software_info.get('software_version', '') if user_software_info else ruanjian_xinxi.get('被测软件版本', [''])[0]
        
        # 构建基础标识符
        base_identifier = f"CT-{software_identifier}-{software_version}" if software_identifier and software_version else "CT-UNKNOWN"
            
        return {
            'software_name': ruanjian_xinxi.get('软件名称', [''])[0],
            'software_version': software_version,
            'software_identifier': software_identifier,
            'base_identifier': base_identifier,
        }
    
    def _extract_original_test_items(
        self, 
        diama_biangeng_xuqiu: Dict[str, str], 
        neirong_dict: List[str], 
        biaoshihao_ceshixianng: List[str]
    ) -> List[Dict[str, Any]]:
        """提取原始测试项（不包含AI生成内容）"""
        test_items = []
        
        for i, (key, requirement_info) in enumerate(diama_biangeng_xuqiu.items()):
            # 修复：适应新的数据结构，章节编号现在直接在顶层
            chapter_number = ''
            if isinstance(requirement_info, dict):
                # 首先尝试从顶层获取章节编号（新结构）
                chapter_number = requirement_info.get('chapter_number', '')
                log_info(f"[REALTIME] [CHAPTER_DEBUG] 测试项 '{key}' 从顶层提取到章节编号: '{chapter_number}'", "realtime_service")
                
                # 如果顶层没有，再尝试从description中获取（旧结构兼容）
                if not chapter_number:
                    description_data = requirement_info.get('description', {})
                    if isinstance(description_data, dict):
                        chapter_number = description_data.get('chapter_number', '')
                        log_info(f"[REALTIME] [CHAPTER_DEBUG] 测试项 '{key}' 从description中提取到章节编号: '{chapter_number}'", "realtime_service")
                    else:
                        log_info(f"[REALTIME] [CHAPTER_DEBUG] 测试项 '{key}' description不是字典类型", "realtime_service")
            else:
                log_info(f"[REALTIME] [CHAPTER_DEBUG] 测试项 '{key}' requirement_info不是字典类型", "realtime_service")
            
            test_item = {
                'name': key,
                'pure_name': key,
                'requirement_description': requirement_info if isinstance(requirement_info, dict) else neirong_dict[i] if i < len(neirong_dict) else '',
                'software_requirement_trace': '',  # 将在构建完整测试项时设置
                'chapter_number': chapter_number  # 修复：从新数据结构中正确提取章节编号
            }
            test_items.append(test_item)
        
        return test_items
    
    def _extract_performance_item(self, functional_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从功能测试项中提取性能测试项（使用PerformanceSeparator的智能逻辑）"""
        try:
            # 使用PerformanceSeparator的智能提取逻辑
            performance_content = self.performance_separator._extract_performance_content(functional_item)
            
            if performance_content:
                # 🔧 修复：移除小数偏移逻辑，索引由调用方设置
                # 使用临时索引，实际索引将在调用方设置
                temp_index = functional_item.get('index', 1)
                
                # 使用PerformanceSeparator创建性能测试项
                performance_item = self.performance_separator._create_performance_test_item(
                    functional_item, performance_content, temp_index
                )
                log_info(f"[REALTIME] 使用PerformanceSeparator提取性能测试项: {performance_item.get('name')}", "realtime_service")
                return performance_item
            
            return None
            
        except Exception as e:
            log_error(f"[REALTIME] 使用PerformanceSeparator提取性能测试项失败: {e}", "realtime_service")
            return None
    
    def _extract_boundary_item(self, functional_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从功能测试项中提取边界测试项（使用PerformanceSeparator的智能逻辑）"""
        try:
            # 使用PerformanceSeparator的智能边界检测逻辑
            if self.performance_separator._has_boundary_content(functional_item):
                # 提取边界内容
                boundary_content = self.performance_separator._extract_boundary_content(functional_item)
                
                if boundary_content:
                    # 🔧 修复：移除小数偏移逻辑，索引由调用方设置
                    # 使用临时索引，实际索引将在调用方设置
                    temp_index = functional_item.get('index', 1)
                    
                    # 使用PerformanceSeparator创建边界测试项
                    boundary_item = self.performance_separator._create_boundary_test_item(
                        functional_item, boundary_content, temp_index
                    )
                    log_info(f"[REALTIME] 使用PerformanceSeparator提取边界测试项: {boundary_item.get('name')}", "realtime_service")
                    return boundary_item
            
            return None
            
        except Exception as e:
            log_error(f"[REALTIME] 使用PerformanceSeparator提取边界测试项失败: {e}", "realtime_service")
            return None
    
    def _process_performance_chapter_tests(
        self, 
        file_path: str, 
        basic_info: Dict[str, Any], 
        task_id: str, 
        current_count: int,
        jianceyi_flag: int = 0
    ) -> int:
        """
        处理性能章节的测试项（性能测试项和余量测试项）
        
        Args:
            file_path: 文档路径
            basic_info: 基本信息
            task_id: 任务ID
            current_count: 当前已处理的测试项数量
            jianceyi_flag: 检测仪标志 (0: 无检测仪, 1: 有检测仪)
            
        Returns:
            int: 处理的测试项数量
        """
        processed_count = 0
        
        try:
            # 第一步：尝试从性能章节提取测试项
            chapter_tests = self._extract_performance_chapter_tests(file_path, basic_info, current_count)
            
            if chapter_tests:
                # 处理性能章节的性能测试项
                if chapter_tests.get('performance_tests'):
                    for perf_test in chapter_tests['performance_tests']:
                        # 🔧 修复：性能章节的测试项已经通过AI分析生成了完整内容，无需再次生成
                        # 性能测试项已包含：test_description, test_method, requirement_description
                        # 这些都是在 performance_ai_analyzer.analyze_performance_requirements 中生成的
                        
                        # 立即存储
                        if self._store_single_item_to_db(perf_test, task_id):
                            processed_count += 1
                            log_info(f"[REALTIME] 性能章节性能测试项存储完成: {perf_test.get('name')}", "realtime_service")
                        else:
                            log_error(f"[REALTIME] 性能章节性能测试项存储失败: {perf_test.get('name')}", "realtime_service")
                
                # 处理性能章节的余量测试项
                if chapter_tests.get('allowance_tests'):
                    for allowance_test in chapter_tests['allowance_tests']:
                        # 🔧 修复：余量章节的测试项已经通过AI分析生成了完整内容，无需再次生成
                        # 余量测试项已包含：test_description, test_method, extracted_requirement
                        # 这些都是在 performance_ai_analyzer.analyze_performance_requirements 中生成的
                        
                        # 立即存储
                        if self._store_single_item_to_db(allowance_test, task_id):
                            processed_count += 1
                            log_info(f"[REALTIME] 性能章节余量测试项存储完成: {allowance_test.get('name')}", "realtime_service")
                        else:
                            log_error(f"[REALTIME] 性能章节余量测试项存储失败: {allowance_test.get('name')}", "realtime_service")
                    
                    log_info(f"[REALTIME] 从性能章节提取了 {len(chapter_tests['allowance_tests'])} 个余量测试项", "realtime_service")
                else:
                    # 如果性能章节没有余量测试项，使用默认的余量测试项
                    log_info("[REALTIME] 性能章节未找到余量测试项，使用默认余量测试项", "realtime_service")
                    default_allowance_count = self._add_default_allowance_tests(basic_info, task_id, current_count + processed_count)
                    processed_count += default_allowance_count
            else:
                # 如果没有找到性能章节，使用默认的余量测试项
                log_info("[REALTIME] 未找到性能章节，使用默认余量测试项", "realtime_service")
                default_allowance_count = self._add_default_allowance_tests(basic_info, task_id, current_count + processed_count)
                processed_count += default_allowance_count
            
            return processed_count
            
        except Exception as e:
            log_error(f"[REALTIME] 处理性能章节测试项失败: {e}", "realtime_service")
            return 0
    
    def _extract_performance_chapter_tests(
        self, 
        file_path: str, 
        basic_info: Dict[str, Any], 
        current_test_count: int
    ) -> Optional[Dict[str, List[Dict[str, Any]]]]:
        """
        从性能章节提取测试项（复用data_processor的逻辑）
        """
        try:
            # 获取标准化文档路径
            session_dir = os.path.dirname(file_path) if file_path else None
            if not session_dir:
                log_warning("[REALTIME] 无法确定会话目录，跳过性能章节提取", "realtime_service")
                return None
                
            standardized_doc_path = self.performance_chapter_extractor.get_standardized_document_path(session_dir)
            if not standardized_doc_path:
                log_info("[REALTIME] 未找到标准化文档，跳过性能章节提取", "realtime_service")
                return None
            
            # 提取性能章节内容
            chapter_data = self.performance_chapter_extractor.extract_performance_chapter_content(standardized_doc_path)
            if not chapter_data:
                log_info("[REALTIME] 未找到性能需求章节", "realtime_service")
                return None
            
            # AI分析性能需求内容
            analysis_result = self.performance_ai_analyzer.analyze_performance_requirements(
                chapter_data['content'], 
                chapter_data
            )
            
            if not analysis_result or (not analysis_result.get('allowance_tests') and not analysis_result.get('performance_tests')):
                log_info("[REALTIME] 性能需求分析未产生有效结果", "realtime_service")
                return None
            
            # 转换为标准测试项格式（复用data_processor的逻辑）
            result = {
                'allowance_tests': [],
                'performance_tests': []
            }
            
            # 🔧 修复：先处理性能测试项，再处理余量测试项，确保正确的索引顺序
            # 处理性能测试项
            if analysis_result.get('performance_tests'):
                for i, performance_item in enumerate(analysis_result['performance_tests']):
                    # 🔧 修复：使用正确的全局索引，索引从1开始
                    global_index = current_test_count + i + 1
                    performance_index = i  # 章节内的索引，用于英文标识生成
                    # 🔧 将性能章节内容传递给转换方法
                    performance_item['chapter_content'] = chapter_data['content']
                    converted_item = self._convert_chapter_performance_item(
                        performance_item, basic_info, performance_index, global_index
                    )
                    if converted_item:
                        result['performance_tests'].append(converted_item)
            
            # 处理余量测试项
            if analysis_result.get('allowance_tests'):
                for i, allowance_item in enumerate(analysis_result['allowance_tests']):
                    # 🔧 修复：余量测试项应该在性能测试项之后，索引从1开始
                    global_index = current_test_count + len(result['performance_tests']) + i + 1
                    allowance_index = i  # 章节内的索引，用于英文标识生成
                    # 🔧 将性能章节内容传递给转换方法
                    allowance_item['chapter_content'] = chapter_data['content']
                    converted_item = self._convert_chapter_allowance_item(
                        allowance_item, basic_info, allowance_index, global_index
                    )
                    if converted_item:
                        result['allowance_tests'].append(converted_item)
            
            return result if (result['allowance_tests'] or result['performance_tests']) else None
            
        except Exception as e:
            log_error(f"[REALTIME] 从性能章节提取测试项失败: {e}", "realtime_service")
            return None
    
    def _add_default_allowance_tests(
        self, 
        basic_info: Dict[str, Any], 
        task_id: str, 
        current_count: int
    ) -> int:
        """
        添加默认的余量测试项
        """
        try:
            # 复用data_processor的固定余量测试项创建逻辑
            from ..test_generation.functional.functional_test_creator import ConfigurationItemRequirementAnalysisDataProcessor
            temp_processor = ConfigurationItemRequirementAnalysisDataProcessor()
            
            default_allowance_tests = temp_processor._create_fixed_allowance_tests(
                basic_info=basic_info,
                current_test_count=current_count
            )
            
            processed_count = 0
            if default_allowance_tests:
                for allowance_test in default_allowance_tests:
                    # 生成AI内容
                    _, description, method = self._generate_ai_content_for_single_item(allowance_test, 0)  # 这里保持0，因为_process_chapter_analysis_tests没有jianceyi_flag参数
                    allowance_test['test_description'] = description
                    allowance_test['test_method'] = method
                    
                    # 立即存储
                    if self._store_single_item_to_db(allowance_test, task_id):
                        processed_count += 1
                        log_info(f"[REALTIME] 默认余量测试项存储完成: {allowance_test.get('name')}", "realtime_service")
                    else:
                        log_error(f"[REALTIME] 默认余量测试项存储失败: {allowance_test.get('name')}", "realtime_service")
            
            return processed_count
            
        except Exception as e:
            log_error(f"[REALTIME] 添加默认余量测试项失败: {e}", "realtime_service")
            return 0
    
    def _convert_chapter_allowance_item(
        self, 
        allowance_item: Dict[str, Any], 
        basic_info: Dict[str, Any], 
        allowance_index: int,
        global_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        将性能章节分析结果转换为标准余量测试项格式
        """
        try:
            # 直接使用已实现的方法
            return self._create_chapter_allowance_test_item(
                allowance_item, basic_info, allowance_index, global_index
            )
            
        except Exception as e:
            log_error(f"[REALTIME] 转换章节余量测试项失败: {e}", "realtime_service")
            return None
    
    def _convert_chapter_performance_item(
        self, 
        performance_item: Dict[str, Any], 
        basic_info: Dict[str, Any], 
        performance_index: int,
        global_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        将性能章节分析结果转换为标准性能测试项格式
        """
        try:
            # 直接使用已实现的方法
            return self._create_chapter_performance_test_item(
                performance_item, basic_info, performance_index, global_index
            )
            
        except Exception as e:
            log_error(f"[REALTIME] 转换章节性能测试项失败: {e}", "realtime_service")
            return None
    
    def _determine_test_type(self, test_item: Dict[str, Any]) -> str:
        """根据测试项名称和内容确定测试类型"""
        # 🔧 修复：优先使用已设置的test_type字段
        existing_test_type = test_item.get('test_type', '')
        if existing_test_type and existing_test_type != '':
            return existing_test_type
        
        test_name = test_item.get('name', '')
        
        # 🔧 扩展：支持更多测试类型的识别
        if '安全性测试' in test_name or '安全' in test_name:
            return '安全性测试'
        elif '（性能测试）' in test_name or '性能测试' in test_name:
            return '性能测试'
        elif '（边界测试）' in test_name or '边界测试' in test_name:
            return '边界测试'
        elif '（余量测试）' in test_name or test_name.startswith('余量测试-') or '余量' in test_name:
            return '余量测试'
        elif '（强度测试）' in test_name or test_name.startswith('强度测试-') or '强度测试' in test_name:
            return '强度测试'
        elif '接口测试' in test_name or '接口' in test_name:
            return '接口测试'
        else:
            return '功能测试'  # 原始功能测试项
    
    def _format_requirement_description(self, requirement_description: Any) -> str:
        """
        将需求描述格式化为标准的a-h格式
        
        Args:
            requirement_description: 需求描述，可能是字典或字符串
            
        Returns:
            str: 格式化后的需求描述文本
        """
        if not requirement_description:
            return ""
        
        # 如果是字符串，直接返回
        if isinstance(requirement_description, str):
            return requirement_description
        
        # 如果是字典，转换为a-h格式
        if isinstance(requirement_description, dict):
            formatted_parts = []
            
            # a) 标识号
            identifier = requirement_description.get('identifier') or requirement_description.get('标识号')
            if identifier:
                formatted_parts.append(f"a) 标识号：{identifier}")
            
            # b) 说明
            description = requirement_description.get('description') or requirement_description.get('说明')
            if description:
                formatted_parts.append(f"b) 说明：{description}")
            
            # c) 进入条件
            entry_condition = requirement_description.get('entry_condition') or requirement_description.get('进入条件')
            if entry_condition:
                formatted_parts.append(f"c) 进入条件：{entry_condition}")
            
            # d) 输入
            input_data = requirement_description.get('input') or requirement_description.get('输入')
            if input_data:
                formatted_parts.append(f"d) 输入：\n{self._format_list_content(input_data)}")
            
            # e) 输出
            output_data = requirement_description.get('output') or requirement_description.get('输出')
            if output_data:
                formatted_parts.append(f"e) 输出：\n{self._format_list_content(output_data)}")
            
            # f) 处理
            processing = requirement_description.get('processing') or requirement_description.get('处理')
            if processing:
                formatted_parts.append(f"f) 处理：\n{self._format_numbered_content(processing)}")
            
            # g) 性能
            performance = requirement_description.get('performance') or requirement_description.get('性能')
            if performance:
                formatted_parts.append(f"g) 性能：\n{self._format_list_content(performance)}")
            
            # h) 约束与限制
            constraints = requirement_description.get('constraints') or requirement_description.get('约束与限制')
            if constraints:
                formatted_parts.append(f"h) 约束与限制：\n{self._format_list_content(constraints)}")
            
            return "\n".join(formatted_parts)
        
        # 其他情况，转为字符串
        return str(requirement_description)
    
    def _format_list_content(self, content: str) -> str:
        """格式化列表内容，添加适当的缩进和符号"""
        if not content:
            return ""
        
        lines = content.strip().split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # 如果行已经有符号，保持原样
                if line.startswith(('-', '•', '·', '1.', '2.', '3.', '4.', '5.')):
                    formatted_lines.append(f" {line}")
                else:
                    formatted_lines.append(f" - {line}")
        
        return "\n".join(formatted_lines)
    
    def _format_numbered_content(self, content: str) -> str:
        """格式化编号内容，确保正确的编号格式"""
        if not content:
            return ""
        
        lines = content.strip().split('\n')
        formatted_lines = []
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line:
                # 如果行已经有编号，保持原样
                if line[0].isdigit() and '.' in line[:3]:
                    formatted_lines.append(f" {line}")
                else:
                    formatted_lines.append(f" {i}. {line}")
        
        return "\n".join(formatted_lines) 
    
    def _process_chapter_analysis_tests(self, file_path: str, basic_info: Dict[str, Any], task_id: str, current_count: int) -> int:
        """
        从固定章节提取余量测试项和性能测试项
        
        Args:
            file_path: 文档路径
            basic_info: 基础信息
            task_id: 任务ID
            current_count: 当前测试项数量
            
        Returns:
            int: 处理的测试项数量
        """
        try:
            log_info("[REALTIME] 开始从固定章节分析余量和性能测试项", "realtime_service")
            
            # 导入性能章节提取器和分析器
            from ..content_analysis.performance_analyzer import PerformanceAIAnalyzer
            from ..document_parsing.parsers.performance_chapter_extractor import PerformanceChapterExtractor
            
            # 提取性能章节内容
            extractor = PerformanceChapterExtractor()
            chapter_data = extractor.extract_performance_chapter_content(file_path)
            
            if not chapter_data:
                log_warning("[REALTIME] 未找到性能需求章节，跳过章节分析", "realtime_service")
                return 0
            
            log_info(f"[REALTIME] 找到性能需求章节: {chapter_data['chapter_number']} {chapter_data['chapter_title']}", "realtime_service")
            
            # 使用AI分析器分析章节内容
            analyzer = PerformanceAIAnalyzer()
            analysis_result = analyzer.analyze_performance_requirements(
                chapter_data['content'], 
                {
                    'chapter_number': chapter_data['chapter_number'],
                    'chapter_title': chapter_data['chapter_title']
                }
            )
            
            if not analysis_result:
                log_warning("[REALTIME] 性能需求章节分析失败", "realtime_service")
                return 0
            
            processed_count = 0
            
            # 处理提取到的性能测试项
            performance_tests = analysis_result.get('performance_tests', [])
            if performance_tests:
                log_info(f"[REALTIME] 开始处理 {len(performance_tests)} 个章节性能测试项", "realtime_service")
                for perf_test in performance_tests:
                    perf_item = self._create_chapter_performance_test_item(
                        perf_test, basic_info, current_count + processed_count + 1
                    )
                    if self._store_single_item_to_db(perf_item, task_id):
                        processed_count += 1
                        log_info(f"[REALTIME] 章节性能测试项存储完成: {perf_test.get('name', '未知')}", "realtime_service")
                    else:
                        log_error(f"[REALTIME] 章节性能测试项存储失败: {perf_test.get('name', '未知')}", "realtime_service")
            
            # 处理提取到的余量测试项
            allowance_tests = analysis_result.get('allowance_tests', [])
            if allowance_tests:
                log_info(f"[REALTIME] 开始处理 {len(allowance_tests)} 个章节余量测试项", "realtime_service")
                for allow_test in allowance_tests:
                    allow_item = self._create_chapter_allowance_test_item(
                        allow_test, basic_info, current_count + processed_count + 1
                    )
                    if self._store_single_item_to_db(allow_item, task_id):
                        processed_count += 1
                        log_info(f"[REALTIME] 章节余量测试项存储完成: {allow_test.get('name', '未知')}", "realtime_service")
                    else:
                        log_error(f"[REALTIME] 章节余量测试项存储失败: {allow_test.get('name', '未知')}", "realtime_service")
            
            log_info(f"[REALTIME] 章节分析测试项处理完成，共处理 {processed_count} 个", "realtime_service")
            return processed_count
            
        except Exception as e:
            log_error(f"[REALTIME] 处理章节分析测试项失败: {e}", "realtime_service")
            import traceback
            log_error(f"[REALTIME] 章节分析错误详情: {traceback.format_exc()}", "realtime_service")
            return 0
    
    def _create_chapter_performance_test_item(self, perf_test: Dict[str, Any], basic_info: Dict[str, Any], performance_index: int, global_index: int) -> Dict[str, Any]:
        """创建章节性能测试项"""
        software_id = basic_info.get('software_identifier', '')
        software_version = basic_info.get('software_version', '')
        software_name = basic_info.get('software_name', '')
        
        english_identifier = identifier_generator.generate_performance_chapter_identifier(performance_index)
        test_item_identifier = f"CT-{software_id}-{software_version}-{english_identifier}-PF{performance_index+1:02d}"
        
        # 🔧 使用性能章节内容作为软件需求描述和需求子项描述
        chapter_content = perf_test.get('chapter_content', perf_test.get('description', ''))
        
        return {
            'index': global_index,  # 🔧 修复：使用全局索引而不是章节内索引
            'name': perf_test.get('name', '章节性能测试'),
            'pure_name': perf_test.get('name', '章节性能测试'),
            'test_item_name': perf_test.get('name', '章节性能测试'),
            'standard_sub_requirement_name': perf_test.get('pure_name', perf_test.get('name', '章节性能测试')),
            'requirement_name': perf_test.get('name', '章节性能测试'),
            'software_requirement_name': perf_test.get('pure_name', perf_test.get('name', '章节性能测试')),
            'standard_sub_requirement_identifier': test_item_identifier,
            'test_item_identifier': test_item_identifier,
            'english_identifier': english_identifier,
            'software_identifier': software_id,
            'software_version': software_version,
            'software_name': software_name,
            'test_type': '性能测试',
            'requirement_description': chapter_content,  # 🔧 使用章节内容
            'requirement_sub_description': perf_test.get('requirement_description', ''),  # 🔧 使用AI分析的需求描述
            'test_description': perf_test.get('test_description', ''),
            'test_method': perf_test.get('test_method', ''),
            'pass_criteria': perf_test.get('pass_criteria', '各测试步骤、测试用例执行结果与预期一致，性能满足要求'),
            'adequacy_requirement': '所有性能测试用例执行完毕，对于未执行的用例说明未执行原因。',
            'software_requirement_trace': f"《{software_name}软件需求规格说明》 {perf_test.get('chapter_number', '')} {perf_test.get('chapter_name', '性能需求')}".strip(),
            'software_requirement_trace_relation': f"《{software_name}软件需求规格说明》 {perf_test.get('chapter_number', '')} {perf_test.get('chapter_name', '性能需求')}".strip(),
            'task_requirement_trace': '无',
            'standard_sub_requirement_unit': '0.2',
            'chapter_number': perf_test.get('chapter_number', ''),
            '_is_chapter_performance_item': True,
            # 🔧 关键修复：性能章节测试项已经通过AI分析生成，不需要再次AI生成
            'ai_generation_required': False,
            'full_requirement_for_ai': chapter_content  # 保留完整需求内容以备需要
        }
    
    def _create_chapter_allowance_test_item(self, allow_test: Dict[str, Any], basic_info: Dict[str, Any], allowance_index: int, global_index: int) -> Dict[str, Any]:
        """创建章节余量测试项"""
        software_id = basic_info.get('software_identifier', '')
        software_version = basic_info.get('software_version', '')
        software_name = basic_info.get('software_name', '')
        
        english_identifier = identifier_generator.generate_allowance_chapter_identifier(allowance_index)
        test_item_identifier = f"CT-{software_id}-{software_version}-{english_identifier}-AL{allowance_index+1:02d}"
        
        # 🔧 使用性能章节内容作为软件需求描述和需求子项描述
        chapter_content = allow_test.get('chapter_content', allow_test.get('description', ''))
        
        return {
            'index': global_index,  # 🔧 修复：使用全局索引而不是章节内索引
            'name': allow_test.get('name', '章节余量测试'),
            'pure_name': allow_test.get('name', '章节余量测试'),
            'test_item_name': allow_test.get('name', '章节余量测试'),
            'standard_sub_requirement_name': allow_test.get('pure_name', allow_test.get('name', '章节余量测试')),
            'requirement_name': allow_test.get('name', '章节余量测试'),
            'software_requirement_name': allow_test.get('pure_name', allow_test.get('name', '章节余量测试')),
            'standard_sub_requirement_identifier': test_item_identifier,
            'test_item_identifier': test_item_identifier,
            'english_identifier': english_identifier,
            'software_identifier': software_id,
            'software_version': software_version,
            'software_name': software_name,
            'test_type': '余量测试',
            'requirement_description': chapter_content,  # 🔧 使用章节内容
            'requirement_sub_description': allow_test.get('extracted_requirement', ''),  # 🔧 使用AI分析的需求描述
            'test_description': allow_test.get('test_description', ''),
            'test_method': allow_test.get('test_method', ''),
            'pass_criteria': allow_test.get('pass_criteria', '各测试步骤、测试用例执行结果与预期一致，余量满足要求'),
            'adequacy_requirement': '所有余量测试用例执行完毕，对于未执行的用例说明未执行原因。',
            'software_requirement_trace': f"《{software_name}软件需求规格说明》 {allow_test.get('chapter_number', '')} {allow_test.get('chapter_name', '性能需求')}".strip(),
            'software_requirement_trace_relation': f"《{software_name}软件需求规格说明》 {allow_test.get('chapter_number', '')} {allow_test.get('chapter_name', '性能需求')}".strip(),
            'task_requirement_trace': '无',
            'standard_sub_requirement_unit': '0.2',
            'chapter_number': allow_test.get('chapter_number', ''),
            '_is_chapter_allowance_item': True,
            # 🔧 关键修复：余量章节测试项已经通过AI分析生成，不需要再次AI生成
            'ai_generation_required': False,
            'full_requirement_for_ai': chapter_content  # 保留完整需求内容以备需要
        }
    
    def _process_fixed_strength_tests(self, basic_info: Dict[str, Any], task_id: str, current_count: int, jianceyi_flag: int = 0) -> int:
        """
        处理固定的强度测试项
        
        Args:
            basic_info: 基础信息
            task_id: 任务ID
            current_count: 当前测试项数量
            
        Returns:
            int: 处理的强度测试项数量
        """
        try:
            log_info(f"[REALTIME] 开始处理强度测试项，当前计数: {current_count}", "realtime_service")
            
            # 🔧 使用新的强度测试生成器
            strength_tests = self.strength_test_generator.create_fixed_strength_tests(basic_info, current_count)
            
            processed_count = 0
            for strength_test in strength_tests:
                # 生成AI内容
                _, description, method = self._generate_ai_content_for_single_item(strength_test, jianceyi_flag)
                strength_test['test_description'] = description
                strength_test['test_method'] = method
                
                # 立即存储
                if self._store_single_item_to_db(strength_test, task_id):
                    processed_count += 1
                    log_info(f"[REALTIME] 强度测试项存储完成: {strength_test.get('name')}", "realtime_service")
                else:
                    log_error(f"[REALTIME] 强度测试项存储失败: {strength_test.get('name')}", "realtime_service")
            
            log_info(f"[REALTIME] 强度测试项处理完成，共处理 {processed_count} 个", "realtime_service")
            return processed_count
            
        except Exception as e:
            log_error(f"[REALTIME] 处理强度测试项失败: {e}", "realtime_service")
            import traceback
            log_error(f"[REALTIME] 强度测试项错误详情: {traceback.format_exc()}", "realtime_service")
            return 0
    
    def _process_security_tests(self, basic_info: Dict[str, Any], task_id: str, current_count: int, jianceyi_flag: int = 0) -> int:
        """
        处理安全性测试项
        
        Args:
            basic_info: 基础信息
            task_id: 任务ID
            current_count: 当前测试项数量
            
        Returns:
            int: 处理的安全性测试项数量
        """
        try:
            log_info(f"[REALTIME] 开始处理安全性测试项，当前计数: {current_count}", "realtime_service")
            
            # 使用安全性测试生成器
            security_tests = self.security_test_generator.create_security_tests(basic_info, current_count)
            
            processed_count = 0
            for security_test in security_tests:
                # 生成AI内容
                _, description, method = self._generate_ai_content_for_single_item(security_test, jianceyi_flag)
                security_test['test_description'] = description
                security_test['test_method'] = method
                
                # 立即存储
                if self._store_single_item_to_db(security_test, task_id):
                    processed_count += 1
                    log_info(f"[REALTIME] 安全性测试项存储完成: {security_test.get('name')}", "realtime_service")
                else:
                    log_error(f"[REALTIME] 安全性测试项存储失败: {security_test.get('name')}", "realtime_service")
            
            log_info(f"[REALTIME] 安全性测试项处理完成，共处理 {processed_count} 个", "realtime_service")
            return processed_count
            
        except Exception as e:
            log_error(f"[REALTIME] 处理安全性测试项失败: {e}", "realtime_service")
            import traceback
            log_error(f"[REALTIME] 安全性测试项错误详情: {traceback.format_exc()}", "realtime_service")
            return 0
    
    def _process_maintainability_tests(self, basic_info: Dict[str, Any], task_id: str, current_count: int, jianceyi_flag: int = 0) -> int:
        """
        处理可维护性测试项
        
        Args:
            basic_info: 基础信息
            task_id: 任务ID
            current_count: 当前测试项数量
            
        Returns:
            int: 处理的可维护性测试项数量
        """
        try:
            log_info(f"[REALTIME] 开始处理可维护性测试项，当前计数: {current_count}", "realtime_service")
            
            # 使用可维护性测试生成器
            maintainability_tests = self.maintainability_test_generator.create_maintainability_tests(basic_info, current_count)
            
            processed_count = 0
            for maintainability_test in maintainability_tests:
                # 生成AI内容
                _, description, method = self._generate_ai_content_for_single_item(maintainability_test, jianceyi_flag)
                maintainability_test['test_description'] = description
                maintainability_test['test_method'] = method
                
                # 立即存储
                if self._store_single_item_to_db(maintainability_test, task_id):
                    processed_count += 1
                    log_info(f"[REALTIME] 可维护性测试项存储完成: {maintainability_test.get('name')}", "realtime_service")
                else:
                    log_error(f"[REALTIME] 可维护性测试项存储失败: {maintainability_test.get('name')}", "realtime_service")
            
            log_info(f"[REALTIME] 可维护性测试项处理完成，共处理 {processed_count} 个", "realtime_service")
            return processed_count
            
        except Exception as e:
            log_error(f"[REALTIME] 处理可维护性测试项失败: {e}", "realtime_service")
            import traceback
            log_error(f"[REALTIME] 可维护性测试项错误详情: {traceback.format_exc()}", "realtime_service")
            return 0
    
    def _process_reliability_tests(self, basic_info: Dict[str, Any], task_id: str, current_count: int, jianceyi_flag: int = 0) -> int:
        """
        处理可靠性测试项
        
        Args:
            basic_info: 基础信息
            task_id: 任务ID
            current_count: 当前测试项数量
            
        Returns:
            int: 处理的可靠性测试项数量
        """
        try:
            log_info(f"[REALTIME] 开始处理可靠性测试项，当前计数: {current_count}", "realtime_service")
            
            # 使用可靠性测试生成器
            reliability_tests = self.reliability_test_generator.create_reliability_tests(basic_info, current_count)
            
            processed_count = 0
            for reliability_test in reliability_tests:
                # 生成AI内容
                _, description, method = self._generate_ai_content_for_single_item(reliability_test, jianceyi_flag)
                reliability_test['test_description'] = description
                reliability_test['test_method'] = method
                
                # 立即存储
                if self._store_single_item_to_db(reliability_test, task_id):
                    processed_count += 1
                    log_info(f"[REALTIME] 可靠性测试项存储完成: {reliability_test.get('name')}", "realtime_service")
                else:
                    log_error(f"[REALTIME] 可靠性测试项存储失败: {reliability_test.get('name')}", "realtime_service")
            
            log_info(f"[REALTIME] 可靠性测试项处理完成，共处理 {processed_count} 个", "realtime_service")
            return processed_count
            
        except Exception as e:
            log_error(f"[REALTIME] 处理可靠性测试项失败: {e}", "realtime_service")
            import traceback
            log_error(f"[REALTIME] 可靠性测试项错误详情: {traceback.format_exc()}", "realtime_service")
            return 0
    
    def _process_interface_tests(self, file_path: str, basic_info: Dict[str, Any], task_id: str, current_count: int, jianceyi_flag: int = 0) -> int:
        """
        处理接口测试项（在所有功能测试项之后）
        
        Args:
            file_path: 文档路径
            basic_info: 基础信息
            task_id: 任务ID
            current_count: 当前测试项数量
            jianceyi_flag: 检测仪标志 (0: 无检测仪, 1: 有检测仪)
            
        Returns:
            int: 处理的接口测试项数量
        """
        try:
            log_info("[REALTIME] 开始提取接口表格数据", "realtime_service")
            
            # 构建标准化需求规格说明文档路径
            import os
            base_dir = os.path.dirname(file_path)
            standardized_file_path = None
            
            # 查找标准化文档
            for filename in os.listdir(base_dir):
                if filename.startswith('standardized_requirement_') and filename.endswith('.docx'):
                    standardized_file_path = os.path.join(base_dir, filename)
                    break
            
            if not standardized_file_path:
                log_warning("[REALTIME] 未找到标准化需求规格说明文档，跳过接口测试项生成", "realtime_service")
                return 0
            
            log_info(f"[REALTIME] 使用标准化文档提取接口表格: {standardized_file_path}", "realtime_service")
            
            # 1. 从标准化Word文档提取接口表格数据
            interface_data = self.interface_parser.extract_interface_table_from_docx(standardized_file_path)
            
            if not interface_data:
                log_info("[REALTIME] 未找到接口表格数据，跳过接口测试项生成", "realtime_service")
                return 0
            
            log_info(f"[REALTIME] 成功提取 {len(interface_data)} 个接口", "realtime_service")
            
            # 2. 转换为接口测试项
            software_name = basic_info.get('software_name', '')
            software_id = basic_info.get('software_identifier', '')
            software_version = basic_info.get('software_version', '')
            
            interface_tests = self.interface_extractor.extract_interface_tests(
                interface_data=interface_data,
                project_name=f"{software_name}软件需求规格说明",
                base_identifier=f"CT-{software_id}-{software_version}",
                software_name=software_name,  # 🔧 添加软件名称参数
                software_version=software_version  # 🔧 添加软件版本参数
            )
            
            if not interface_tests:
                log_warning("[REALTIME] 未生成任何接口测试项", "realtime_service")
                return 0
            
            log_info(f"[REALTIME] 成功生成 {len(interface_tests)} 个接口测试项", "realtime_service")
            
            # 3. 逐个处理接口测试项
            processed_count = 0
            
            for i, interface_test in enumerate(interface_tests):
                # 调整索引
                interface_test['index'] = current_count + i + 1
                
                log_info(f"[REALTIME] 为接口测试生成模板内容: {interface_test.get('name')}", "realtime_service")
                
                # 🔧 修改：使用固定模板生成器而不是AI生成
                interface_name = interface_test.get('name', '')
                interface_desc = interface_test.get('requirement_description', '')
                
                # 使用接口测试模板生成器
                test_description, test_method = self.interface_test_template_generator.generate_interface_test_content(
                    interface_name=interface_name,
                    interface_desc=interface_desc
                )
                
                interface_test['test_description'] = test_description
                interface_test['test_method'] = test_method
                
                log_info(f"[REALTIME] 接口测试模板内容生成完成: {interface_name}", "realtime_service")
                
                # 5. 立即存储接口测试项
                if self._store_single_item_to_db(interface_test, task_id):
                    processed_count += 1
                    log_info(f"[REALTIME] 接口测试项存储完成: {interface_test.get('name')}", "realtime_service")
                else:
                    log_error(f"[REALTIME] 接口测试项存储失败: {interface_test.get('name')}", "realtime_service")
            
            log_info(f"[REALTIME] 接口测试项处理完成，共处理 {processed_count} 个", "realtime_service")
            return processed_count
            
        except Exception as e:
            log_error(f"[REALTIME] 处理接口测试项失败: {e}", "realtime_service")
            import traceback
            log_error(f"[REALTIME] 接口测试项错误详情: {traceback.format_exc()}", "realtime_service")
            return 0