"""
配置项测试需求分析表数据处理器

负责处理和组织配置项测试需求分析表所需的数据。
包含性能测试项自动分离功能。
"""

import logging
import os
import glob
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from ...document_parsing.utils import extract_requirement_name, extract_chapter_number
from .performance_test_extractor import PerformanceSeparator
from ...content_analysis.interface_analyzer import InterfaceTestExtractor
from ...document_parsing.parsers.interface_table_parser import InterfaceTableParser
from ...document_parsing.parsers.performance_chapter_extractor import PerformanceChapterExtractor
from ...content_analysis.performance_analyzer import PerformanceAIAnalyzer

# 导入任务日志函数
from .....utils.logging_utils.logger import log_info, log_debug, log_error, log_warning

# 导入英文标识生成器
from .english_identifier_generator import identifier_generator

# 配置日志
logger = logging.getLogger(__name__)

class ConfigurationItemRequirementAnalysisDataProcessor:
    """配置项测试需求分析表数据处理器"""
    
    def __init__(self):
        """初始化数据处理器"""
        self.logger = logger
        self.performance_separator = PerformanceSeparator()  # 🔧 新增性能分离器
        self.interface_extractor = InterfaceTestExtractor()  # 🔧 新增接口测试提取器
        self.interface_parser = InterfaceTableParser()  # 🔧 新增接口表格解析器
        self.performance_chapter_extractor = PerformanceChapterExtractor()  # 🔧 新增性能章节提取器
        self.performance_ai_analyzer = PerformanceAIAnalyzer()  # 🔧 新增性能AI分析器
    
    def organize_requirement_analysis_data(
        self,
        ruanjian_xinxi: Dict[str, List[str]],
        ruanjian_name: str,
        diama_biangeng_xuqiu: Dict[str, str],
        file_path: str,
        ceshileixing: str,
        neirong_dict: List[str],
        biaoshihao_ceshixianng: List[str],
        AI_fenx_flag_Anniu: int,
        jianceyi_flag: int,
        user_software_info: Optional[Dict[str, str]] = None,
        chapter_dict: Optional[Dict[str, str]] = None  # 🔧 新增：章节编号字典
    ) -> Dict[str, Any]:
        """
        组织配置项测试需求分析表数据
        
        Args:
            ruanjian_xinxi: 软件信息字典
            ruanjian_name: 软件名称
            diama_biangeng_xuqiu: 代码变更需求字典
            file_path: 文档文件路径
            ceshileixing: 测试类型
            neirong_dict: 内容描述列表
            biaoshihao_ceshixianng: 标识号测试项列表
            AI_fenx_flag_Anniu: AI分析标志
            jianceyi_flag: 检测仪标志
            user_software_info: 用户软件信息（包含前端提供的版本信息）
            
        Returns:
            Dict[str, Any]: 组织好的需求分析表数据
        """
        try:
            log_info("开始组织配置项测试需求分析表数据")
            
            # Debug: 记录data_processor入口参数
            # log_debug(f"[DEBUG] ConfigurationItemRequirementAnalysisDataProcessor.organize_requirement_analysis_data 开始")
            # log_debug(f"   ruanjian_xinxi: {ruanjian_xinxi}")
            # log_debug(f"   ruanjian_name: {ruanjian_name}")
            # log_debug(f"   diama_biangeng_xuqiu: {diama_biangeng_xuqiu}")
            # log_debug(f"   file_path: {file_path}")
            # log_debug(f"   ceshileixing: {ceshileixing}")
            # log_debug(f"   neirong_dict: {neirong_dict}")
            # log_debug(f"   biaoshihao_ceshixianng: {biaoshihao_ceshixianng}")
            # log_debug(f"   AI_fenx_flag_Anniu: {AI_fenx_flag_Anniu}")
            # log_debug(f"   jianceyi_flag: {jianceyi_flag}")
            
            # 基本信息
            # log_debug(f"[DEBUG] 准备调用 _organize_basic_info")
            basic_info = self._organize_basic_info(
                ruanjian_xinxi, ruanjian_name, ceshileixing, user_software_info
            )
            # log_debug(f"[DEBUG] _organize_basic_info 返回: {basic_info}")
            
            # 测试项信息
            # log_debug(f"[DEBUG] 准备调用 _organize_test_items")
            test_items = self._organize_test_items(
                diama_biangeng_xuqiu, neirong_dict, biaoshihao_ceshixianng, basic_info, chapter_dict
            )
            # log_debug(f"[DEBUG] _organize_test_items 返回: {test_items}")
            
            # 执行性能和边界测试项分离
            # log_info("[DEBUG-PERF-SAVE] ===== 数据处理器：开始性能测试项分离 =====", "data_processor")
            # log_info("[DEBUG-PERF-SAVE] 分离前测试项列表:", "data_processor")
            for idx, item in enumerate(test_items):
                log_info(f"[DEBUG-PERF-SAVE] {idx+1}. {item.get('name')} (标识: {item.get('test_item_identifier')})", "data_processor")
            
            enhanced_test_items = self.performance_separator.separate_performance_and_boundary_tests(test_items)
            
            log_info("[DEBUG-PERF-SAVE] ===== 数据处理器：性能分离完成 =====", "data_processor")
            log_info(f"[DEBUG-PERF-SAVE] 分离后测试项列表 (总数: {len(enhanced_test_items)}):", "data_processor")
            for idx, item in enumerate(enhanced_test_items):
                item_type = "性能" if "性能测试" in item.get('name', '') else "边界" if "边界测试" in item.get('name', '') else "功能"
                log_info(f"[DEBUG-PERF-SAVE] {idx+1}. [{item_type}] {item.get('name')} (标识: {item.get('test_item_identifier')})", "data_processor")
            
            # 🔧 新增：接口测试项提取处理
            log_info("开始接口测试项提取处理", "data_processor")
            # log_debug(f"接口测试提取 - 输入参数检查:", "data_processor")
            # log_debug(f"  - file_path: {file_path}", "data_processor")
            # log_debug(f"  - 文件类型判断: {'目录文档' if 'catalog' in str(file_path) else '需求文档'}", "data_processor")
            
            try:
                # 🔧 修复：确保使用标准化需求文档而不是目录文档来提取接口信息
                interface_extraction_file = file_path
                if 'catalog' in str(file_path):
                    # 如果传入的是目录文档，需要找到对应的标准化需求文档
                    session_dir = os.path.dirname(file_path)
                    
                    # 🔧 优先查找标准化需求文档
                    standardized_files = glob.glob(os.path.join(session_dir, "standardized_requirement_*"))
                    requirement_files = glob.glob(os.path.join(session_dir, "requirement_*"))
                    
                    if standardized_files:
                        interface_extraction_file = standardized_files[0]  # 使用标准化需求文档
                        log_info(f"🔧 检测到目录文档，切换到标准化需求文档: {interface_extraction_file}", "data_processor")
                    elif requirement_files:
                        interface_extraction_file = requirement_files[0]  # 备选：使用原始需求文档
                        log_info(f"🔧 检测到目录文档，未找到标准化文档，使用原始需求文档: {interface_extraction_file}", "data_processor")
                    else:
                        log_warning(f"⚠️ 未找到任何需求文档，继续使用原路径: {file_path}", "data_processor")
                
                log_info(f"📄 接口提取使用文档: {interface_extraction_file}", "data_processor")
                log_debug(f"   文档类型: {'标准化需求文档' if 'standardized_requirement' in str(interface_extraction_file) else '原始需求文档' if 'requirement_' in str(interface_extraction_file) else '其他文档'}", "data_processor")
                
                # 提取接口表格数据
                interface_data = self.interface_parser.extract_interface_table_from_docx(interface_extraction_file)
                log_info(f"接口表格提取完成：发现{len(interface_data)}个接口", "data_processor")
                
                if interface_data:
                    log_debug(f"接口数据详情: {interface_data}", "data_processor")
                    
                    # 生成接口测试项
                    interface_tests = self.interface_extractor.extract_interface_tests(
                        interface_data=interface_data,
                        project_name=ruanjian_name,
                        base_identifier=basic_info.get('base_identifier', 'CT-UNKNOWN'),
                        software_name=basic_info.get('software_name', ruanjian_name),  # 🔧 添加软件名称
                        software_version=basic_info.get('software_version', '1.0')  # 🔧 添加软件版本
                    )
                    log_info(f"接口测试项生成完成：生成{len(interface_tests)}个接口测试项", "data_processor")
                    
                    # 将接口测试项添加到增强测试项中
                    if interface_tests:
                        # 调整索引，确保接口测试项的索引连续
                        for i, interface_test in enumerate(interface_tests):
                            interface_test['index'] = len(enhanced_test_items) + i + 1
                            log_debug(f"  接口测试项 {i+1}: {interface_test.get('name', '未知')} (标识: {interface_test.get('test_item_identifier', '未设置')})", "data_processor")
                        
                        enhanced_test_items.extend(interface_tests)
                        log_info(f"✅ 接口测试项集成完成：总测试项数量{len(enhanced_test_items)}", "data_processor")
                    else:
                        log_warning("⚠️ 接口测试项生成失败，返回列表为空", "data_processor")
                else:
                    log_info("📋 文档中未发现接口表格", "data_processor")
                    
            except Exception as interface_error:
                log_error(f"接口测试项提取失败: {interface_error}", "data_processor")
                import traceback
                log_error(f"接口提取错误详情: {traceback.format_exc()}", "data_processor")
            
            # 🔧 修复：将性能章节测试项移动到接口测试项之后
            log_info("开始从性能章节提取测试项（在接口测试项之后）", "data_processor")
            chapter_based_tests = self._extract_performance_chapter_tests(file_path, basic_info, len(enhanced_test_items))
            
            if chapter_based_tests:
                # 🔧 先添加性能章节的性能测试项（在余量测试项之前）
                if chapter_based_tests.get('performance_tests'):
                    enhanced_test_items.extend(chapter_based_tests['performance_tests'])
                    log_info(f"✅ 添加了{len(chapter_based_tests['performance_tests'])}个性能章节性能测试项", "data_processor")
                
                # 🔧 再添加性能章节的余量测试项
                if chapter_based_tests.get('allowance_tests'):
                    enhanced_test_items.extend(chapter_based_tests['allowance_tests'])
                    log_info(f"✅ 添加了{len(chapter_based_tests['allowance_tests'])}个性能章节余量测试项", "data_processor")
            else:
                # 回退到固定余量测试项（基于hanshutiqu_kaifa项目的思路）
                log_info("未找到性能章节，使用固定余量测试项", "data_processor")
                allowance_tests = self._create_fixed_allowance_tests(
                    basic_info=basic_info,
                    current_test_count=len(enhanced_test_items)
                )
                if allowance_tests:
                    enhanced_test_items.extend(allowance_tests)
                    log_info(f"添加固定余量测试项: {len(allowance_tests)}个", "data_processor")

            # 🔧 新增：添加固定的强度测试项（调整到余量测试之后）
            log_info("开始添加固定强度测试项", "data_processor")
            try:
                strength_tests = self._create_fixed_strength_tests(
                    basic_info=basic_info,
                    current_test_count=len(enhanced_test_items)
                )
                
                if strength_tests:
                    enhanced_test_items.extend(strength_tests)
                    log_info(f"✅ 添加了{len(strength_tests)}个固定强度测试项，总测试项数量{len(enhanced_test_items)}", "data_processor")
                else:
                    log_info("📋 没有添加强度测试项", "data_processor")
                    
            except Exception as strength_error:
                log_error(f"固定强度测试项添加失败: {strength_error}", "data_processor")
                import traceback
                log_error(f"强度测试添加错误详情: {traceback.format_exc()}", "data_processor")
            
            # 获取性能测试统计
            performance_stats = self.performance_separator.get_performance_statistics(enhanced_test_items)
            log_info(f"性能测试项统计：{performance_stats}", "data_processor")
            
            # 文档信息
            document_info = self._organize_document_info(file_path, ruanjian_name)
            
            # AI分析配置
            ai_config = self._organize_ai_config(AI_fenx_flag_Anniu, jianceyi_flag)
            
            # 格式设置配置
            formatting_config = self._get_formatting_config()
            
            requirement_analysis_data = {
                'basic_info': basic_info,
                'test_items': enhanced_test_items, # 使用增强后的测试项
                'document_info': document_info,
                'ai_config': ai_config,
                'formatting_config': formatting_config,
                'test_count': len(enhanced_test_items),  # 🔧 更新为增强后的数量
                'original_test_count': len(diama_biangeng_xuqiu),  # 🔧 保留原始数量
                'performance_stats': performance_stats,  # 🔧 添加性能统计
                'table_type': '配置项测试需求分析表'
            }
            
            log_info(f"需求分析表数据组织完成，原始{len(diama_biangeng_xuqiu)}个测试项，增强后{len(enhanced_test_items)}个测试项", "data_processor")
            return requirement_analysis_data
            
        except Exception as e:
            log_error(f"组织配置项测试需求分析表数据时发生错误: {str(e)}")
            # 🔧 添加详细的错误跟踪
            import traceback
            log_error(f"错误详情: {traceback.format_exc()}")
            
            # 🔧 返回基本的数据结构而不是空字典，避免后续处理失败
            try:
                basic_info = self._organize_basic_info(ruanjian_xinxi, ruanjian_name, ceshileixing, user_software_info)
                return {
                    'test_items': [],
                    'basic_info': basic_info,
                    'document_info': {'document_path': file_path, 'software_name': ruanjian_name},
                    'ai_config': {'enable_test_description': False, 'enable_test_method': False},
                    'formatting_config': self._get_formatting_config(),
                    'test_count': 0,
                    'table_type': '配置项测试需求分析表'
                }
            except Exception as inner_e:
                log_error(f"创建基本数据结构也失败: {inner_e}")
                return {}
    
    def _organize_basic_info(
        self,
        ruanjian_xinxi: Dict[str, List[str]],
        ruanjian_name: str,
        ceshileixing: str,
        user_software_info: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """组织基本信息"""
        # 🔧 优先使用前端提供的软件标识信息
        if user_software_info and user_software_info.get('software_id'):
            ruanjian_biaoshi = user_software_info.get('software_id')
            log_info(f"使用前端提供的软件标识: {ruanjian_biaoshi}", "data_processor")
        else:
            ruanjian_biaoshi = ruanjian_xinxi.get('软件标识', [''])[0]
            log_info(f"使用ruanjian_xinxi中的软件标识: {ruanjian_biaoshi}", "data_processor")
        
        # 🔧 优先使用前端提供的软件版本信息
        if user_software_info and user_software_info.get('software_version'):
            ruanjian_version = user_software_info.get('software_version')
            log_info(f"使用前端提供的软件版本: {ruanjian_version}", "data_processor")
        else:
            ruanjian_version = ruanjian_xinxi.get('被测软件版本', [''])[0]
            log_info(f"使用文档中的软件版本: {ruanjian_version}", "data_processor")
        
        # 生成测试需求标识前缀
        if ceshileixing == '回归测试':
            ceshi_xuqiu_biaoshi = 'CT_R-' + ruanjian_biaoshi + '_' + ruanjian_version + '_'
        elif ceshileixing == '配置项测试':
            ceshi_xuqiu_biaoshi = 'CT-' + ruanjian_biaoshi + '_' + ruanjian_version + '_'
        else:  # 系统测试
            ceshi_xuqiu_biaoshi = 'ST-' + ruanjian_biaoshi + '_' + ruanjian_version + '_'
        
        return {
            'software_name': ruanjian_name,
            'software_identifier': ruanjian_biaoshi,
            'software_version': ruanjian_version,
            'test_type': ceshileixing,
            'test_requirement_identifier_prefix': ceshi_xuqiu_biaoshi,
            'base_identifier': ceshi_xuqiu_biaoshi,  # 🔧 新增：基础标识符用于接口测试项
            'programming_language': ruanjian_xinxi.get('编程语言', ['C'])[0],
            'development_environment': ruanjian_xinxi.get('开发环境', ['SDK'])[0],
            'runtime_environment': ruanjian_xinxi.get('运行环境', ['Linux'])[0],
            'software_level': ruanjian_xinxi.get('软件等级', ['AAAA'])[0]
        }
    
    def _organize_test_items(
        self,
        diama_biangeng_xuqiu: Dict[str, str],
        neirong_dict: List[str],
        biaoshihao_ceshixianng: List[str],
        basic_info: Dict[str, Any],
        chapter_dict: Optional[Dict[str, str]] = None  # 🔧 新增：章节编号字典
    ) -> List[Dict[str, Any]]:
        """组织测试项信息"""
        # log_debug(f"[DEBUG] _organize_test_items 开始")
        # log_debug(f"   diama_biangeng_xuqiu: {diama_biangeng_xuqiu}")
        # log_debug(f"   neirong_dict: {neirong_dict}")
        # log_debug(f"   biaoshihao_ceshixianng: {biaoshihao_ceshixianng}")
        
        test_items = []
        allkeys = list(diama_biangeng_xuqiu.keys())
        # log_debug(f"   allkeys: {allkeys}")
        
        for i, test_item_name in enumerate(allkeys):
            # log_debug(f"处理第{i+1}个测试项:")
            # log_debug(f"   test_item_name (allkeys[{i}]): '{test_item_name}'")
            # log_debug(f"   biaoshihao_ceshixianng[{i}]: '{biaoshihao_ceshixianng[i] if i < len(biaoshihao_ceshixianng) else 'N/A'}'")
            
            # 提取纯需求名称和章节号
            pure_requirement_name = extract_requirement_name(test_item_name)
            chapter_number = extract_chapter_number(test_item_name)
            
            # 🔧 优先使用章节字典中的章节编号
            if chapter_dict and pure_requirement_name in chapter_dict:
                chapter_number = chapter_dict[pure_requirement_name]
                # log_debug(f"   从章节字典获取章节编号: '{pure_requirement_name}' -> '{chapter_number}'")
            elif not chapter_number:
                # 如果无法提取章节编号，尝试从test_item_name中提取
                chapter_number = extract_chapter_number(test_item_name)
                # log_debug(f"   从测试项名称提取章节编号: '{test_item_name}' -> '{chapter_number}'")
            
            log_debug(f"   extract_requirement_name('{test_item_name}') -> '{pure_requirement_name}'")
            # log_debug(f"   最终章节编号: '{chapter_number}'")
            
            # [FIX] 关键修复：正确生成英文标识符，而不是使用REQ-XXX格式
            # biaoshihao_ceshixianng 实际包含的是需求名称，不是英文标识符
            requirement_name_from_param = biaoshihao_ceshixianng[i] if i < len(biaoshihao_ceshixianng) else pure_requirement_name
            
            # 🔧 提前提取需求标识号（标识号），作为三个关键字段的优先来源
            requirement_id = self._extract_requirement_id(neirong_dict[i] if i < len(neirong_dict) else '')
            # log_debug(f"   提取需求标识号: '{requirement_id}'", "data_processor")
            
            # 🔧 生成英文标识符：优先使用标识号（去空格），无标识号则回退到旧规则
            if requirement_id and isinstance(requirement_id, str) and requirement_id.strip():
                english_identifier_correct = requirement_id.replace(' ', '')
            else:
                # 回退：使用英文标识生成器
                mock_item = {
                    'name': requirement_name_from_param,
                    'requirement_description': {},
                    'software_requirement_trace': ''
                }
                english_identifier_correct = identifier_generator.generate_functional_identifier(mock_item, i)
            # log_debug(f"   生成英文标识符: '{requirement_name_from_param}' -> '{english_identifier_correct}'", "data_processor")
            
            # [FIX] 生成完整的测试项标识符（CT格式）：优先基于标识号派生出的英文标识符
            software_id = basic_info.get('software_identifier', 'UNKNOWN')
            software_version = basic_info.get('software_version', '1.00')
            test_item_identifier = f"CT-{software_id}-{software_version}-{english_identifier_correct}-FN01"
            # log_debug(f"   生成测试项标识符: '{test_item_identifier}'", "data_processor")
            
            # 🔧 三列“继承”调整：name/英文标识符/test_item_identifier 优先继承自“标识号”
            display_name = requirement_id if (requirement_id and isinstance(requirement_id, str) and requirement_id.strip()) else requirement_name_from_param
            
            # 解析原始名称中的测试类型后缀，例如："用户身份验证功能（性能测试）"
            original_req_name = allkeys[i] if i < len(allkeys) else ''
            parsed_test_type = ''
            stripped_req_name = original_req_name
            try:
                if isinstance(original_req_name, str) and original_req_name.endswith(')') or original_req_name.endswith('）'):
                    # 同时兼容中文全角/半角括号
                    import re
                    m = re.search(r'[（(]([^（）()]*)[)）]\s*$', original_req_name)
                    if m:
                        parsed_test_type = m.group(1).strip()
                        stripped_req_name = re.sub(r'\s*[（(][^（）()]*[)）]\s*$', '', original_req_name).strip()
            except Exception:
                parsed_test_type = ''
                stripped_req_name = original_req_name

            test_item = {
                'index': i + 1,
                'name': display_name,  # 需求名称优先继承标识号
                'pure_name': display_name,  # 同步为显示名称
                'chapter_number': chapter_number or '',  # 🔧 使用提取的章节号
                # 标准子需求名称=原始需求名称（不带测试类型后缀）
                'standard_sub_requirement_name': stripped_req_name,
                'standard_sub_requirement_unit': '0.2',
                'task_requirement_trace': '无',
                # 软件需求规格说明需求名称=原始需求名称（不带测试类型后缀）
                'software_requirement_name': stripped_req_name,
                'software_requirement_identifier': requirement_id or '',  # 🔧 新增：需求标识符
                'requirement_description': neirong_dict[i] if i < len(neirong_dict) else '',
                'requirement_sub_description': neirong_dict[i] if i < len(neirong_dict) else '',
                'adequacy_requirement': '所有用例执行完毕，对于未执行的用例说明未执行原因。',
                'pass_criteria': '各测试步骤、测试用例执行结果与预期一致，功能实现正确',
                # 测试类型（例如 性能测试、边界测试）
                'test_type': parsed_test_type,
                'english_identifier': english_identifier_correct,  # [FIX] 真正的英文标识符（优先来自标识号）
                'test_item_identifier': test_item_identifier,  # [FIX] 完整的CT格式测试项标识符（基于上面的英文标识符）
                'software_requirement_trace': requirement_id or '',  # 🔧 使用提取的需求标识号
                'test_description': '',  # 将在测试内容生成时填充
                'test_method': ''  # 将在测试内容生成时填充
            }
            
            # log_debug(f"   最终test_item: {test_item}")
            test_items.append(test_item)
        
        # log_debug(f"[DEBUG] _organize_test_items 返回: {test_items}")
        return test_items
    
    def _extract_requirement_id(self, requirement_description: str) -> Optional[str]:
        """
        从需求描述中提取需求标识号
        
        Args:
            requirement_description: 需求描述文本
            
        Returns:
            Optional[str]: 提取的需求标识号（如REQ-1.1）
        """
        if not requirement_description:
            return None
        
        # 🔧 确保输入是字符串类型
        if not isinstance(requirement_description, str):
            try:
                requirement_description = str(requirement_description)
            except Exception as e:
                log_debug(f"需求描述转换为字符串失败: {e}", "data_processor")
                return None
        
        import re
        
        try:
            # 匹配模式：a) 标识号：REQ-X.X 或 a) 标识号：REQ - X.X
            patterns = [
                r'a\)\s*标识号[：:]\s*(REQ\s*-?\s*[\d\.]+)',
                r'标识号[：:]\s*(REQ\s*-?\s*[\d\.]+)',
                r'(REQ\s*-?\s*[\d\.]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, requirement_description, re.IGNORECASE)
                if match:
                    # 清理提取的标识号，移除多余空格
                    requirement_id = re.sub(r'\s+', '', match.group(1))
                    return requirement_id
            
            return None
            
        except Exception as e:
            log_debug(f"需求标识号提取失败: {e}", "data_processor")
            return None
    
    def _organize_document_info(self, file_path: str, ruanjian_name: str) -> Dict[str, str]:
        """组织文档信息"""
        return {
            'document_path': file_path,
            'software_name': ruanjian_name,
            'requirement_spec_name': f'《{ruanjian_name}需求规格说明》'
        }
    
    def _organize_ai_config(self, AI_fenx_flag_Anniu: int, jianceyi_flag: int) -> Dict[str, Any]:
        """组织AI分析配置 - 使用AI开关控制器"""
        # 导入AI开关控制器
        from ....utils.ai_switch_controller.ai_switch_controller import get_ai_controller, AIModule
        
        # 获取AI控制器实例
        ai_controller = get_ai_controller()
        
        # 获取需求分析模块的AI配置
        ai_config = ai_controller.get_ai_config(AIModule.REQUIREMENT_ANALYSIS)
        
        # 添加额外的配置项
        ai_config.update({
            'detector_flag': jianceyi_flag,
            'use_knowledge_optimization': True,  # 是否使用知识库优化
        })
        
        return ai_config
    
    def _get_formatting_config(self) -> Dict[str, Any]:
        """获取格式设置配置"""
        return {
            'colors': {
                'light_yellow': "FFFF99",
                'light_green': "CCFFCC",
                'light_blue': "99CCFF",
                'light_red': "FFC0CB",
                'red': "FF0000"
            },
            'column_ranges': {
                'basic_info': [2, 4],      # 基本信息列
                'round_info': [5, 5],      # 轮次信息列
                'requirement_info': [6, 13], # 需求信息列
                'test_type': [14, 14],     # 测试类型列
                'test_content': [15, 22]   # 测试内容列
            },
            'border_style': 'thin',
            'alignment': {
                'wrap_text': True,
                'vertical': 'center'
            }
        }
    
    def validate_requirement_analysis_data(self, requirement_analysis_data: Dict[str, Any]) -> bool:
        """
        验证配置项测试需求分析表数据的完整性
        
        Args:
            requirement_analysis_data: 需求分析表数据字典
            
        Returns:
            bool: 数据是否有效
        """
        try:
            # 检查必需的顶级键
            required_keys = ['basic_info', 'test_items', 'document_info', 'ai_config', 'test_count']
            for key in required_keys:
                if key not in requirement_analysis_data:
                    log_error(f"缺少必需的数据键: {key}")
                    return False
            
            # 检查基本信息
            basic_info = requirement_analysis_data['basic_info']
            required_basic_keys = ['software_name', 'software_identifier', 'test_type']
            for key in required_basic_keys:
                if key not in basic_info or not basic_info[key]:
                    log_error(f"基本信息缺少必需字段: {key}")
                    return False
            
            # 检查测试项数量一致性
            test_items = requirement_analysis_data['test_items']
            test_count = requirement_analysis_data['test_count']
            
            if len(test_items) != test_count:
                log_error(f"测试项数量不一致: {len(test_items)} != {test_count}")
                return False
            
            # 检查测试项完整性
            for i, test_item in enumerate(test_items):
                required_item_keys = ['index', 'name', 'english_identifier']
                for key in required_item_keys:
                    if key not in test_item or not test_item[key]:
                        log_error(f"测试项{i+1}缺少必需字段: {key}")
                        return False
            
            log_info("配置项测试需求分析表数据验证通过")
            return True
            
        except Exception as e:
            log_error(f"验证配置项测试需求分析表数据时发生错误: {str(e)}")
            return False
    
    def get_requirement_analysis_statistics(self, requirement_analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取配置项测试需求分析表统计信息
        
        Args:
            requirement_analysis_data: 需求分析表数据字典
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            test_items = requirement_analysis_data.get('test_items', [])
            basic_info = requirement_analysis_data.get('basic_info', {})
            ai_config = requirement_analysis_data.get('ai_config', {})
            
            # 基本统计
            statistics = {
                'total_test_items': requirement_analysis_data.get('test_count', 0),
                'software_name': basic_info.get('software_name', ''),
                'test_type': basic_info.get('test_type', ''),
                'ai_analysis_enabled': ai_config.get('enable_ai_analysis', False),
                'detector_flag': ai_config.get('detector_flag', 0),
                'table_type': '配置项测试需求分析表'
            }
            
            # 测试项类型统计
            test_types = {}
            for test_item in test_items:
                test_name = test_item.get('name', '')
                # 简单的类型分类
                if '故障' in test_name or '报警' in test_name:
                    test_type = '故障测试'
                elif '接口' in test_name:
                    test_type = '接口测试'
                elif '性能' in test_name:
                    test_type = '性能测试'
                else:
                    test_type = '功能测试'
                
                test_types[test_type] = test_types.get(test_type, 0) + 1
            
            statistics['test_type_distribution'] = test_types
            
            log_info(f"需求分析表统计: 共{statistics['total_test_items']}个测试项")
            return statistics
            
        except Exception as e:
            log_error(f"获取配置项测试需求分析表统计信息时发生错误: {str(e)}")
            return {}
    
    def extract_test_requirements(self, requirement_analysis_data: Dict[str, Any]) -> List[str]:
        """
        从需求分析表数据中提取测试需求列表
        
        Args:
            requirement_analysis_data: 需求分析表数据字典
            
        Returns:
            List[str]: 测试需求列表
        """
        try:
            test_items = requirement_analysis_data.get('test_items', [])
            requirements = [item.get('name', '') for item in test_items if item.get('name')]
            
            log_info(f"提取到{len(requirements)}个测试需求")
            return requirements
            
        except Exception as e:
            log_error(f"提取测试需求时发生错误: {str(e)}")
            return []
    
    def update_chapter_numbers(
        self,
        requirement_analysis_data: Dict[str, Any],
        chapter_numbers: List[str]
    ) -> bool:
        """
        更新测试项的章节号
        
        Args:
            requirement_analysis_data: 需求分析表数据字典
            chapter_numbers: 章节号列表
            
        Returns:
            bool: 更新是否成功
        """
        try:
            test_items = requirement_analysis_data.get('test_items', [])
            
            for i, chapter_number in enumerate(chapter_numbers):
                if i < len(test_items):
                    test_items[i]['chapter_number'] = chapter_number
            
            log_info(f"更新了{len(chapter_numbers)}个章节号")
            return True
            
        except Exception as e:
            log_error(f"更新章节号时发生错误: {str(e)}")
            return False
    
    def update_test_content(
        self,
        requirement_analysis_data: Dict[str, Any],
        test_descriptions: List[str],
        test_methods: List[str]
    ) -> bool:
        """更新测试内容到需求分析数据中
        
        Args:
            requirement_analysis_data: 需求分析数据
            test_descriptions: 测试描述列表
            test_methods: 测试方法列表
            
        Returns:
            bool: 更新是否成功
        """
        try:
            log_info(f"开始更新测试内容: {len(test_descriptions)}个描述, {len(test_methods)}个方法")
            
            test_items = requirement_analysis_data.get('test_items', [])
            
            for i, test_item in enumerate(test_items):
                if i < len(test_descriptions):
                    test_item['test_description'] = test_descriptions[i]
                    
                if i < len(test_methods):
                    test_item['test_method'] = test_methods[i]
            
            log_info(f"成功更新 {min(len(test_descriptions), len(test_items))} 个测试项的内容")
            return True
            
        except Exception as e:
            log_error(f"更新测试内容时发生错误: {str(e)}")
            return False
    
    def generate_test_identifiers(
        self,
        requirement_analysis_data: Dict[str, Any]
    ) -> List[str]:
        """
        生成测试项标识
        
        Args:
            requirement_analysis_data: 需求分析表数据字典
            
        Returns:
            List[str]: 测试项标识列表
        """
        try:
            basic_info = requirement_analysis_data.get('basic_info', {})
            test_items = requirement_analysis_data.get('test_items', [])
            
            ceshi_xuqiu_biaoshi = basic_info.get('test_requirement_identifier_prefix', 'CT-')
            
            # 导入测试类型分析器
            from .test_type_classifier import ceshi_leixing_biaoshi_choose
            
            test_identifiers = []
            for test_item in test_items:
                test_name = test_item.get('name', '')
                english_identifier = test_item.get('english_identifier', 'SRC-name')
                
                # 分析测试类型
                leixing_biaoshi, _ = ceshi_leixing_biaoshi_choose(test_name)
                
                # 生成完整的测试项标识
                test_identifier = ceshi_xuqiu_biaoshi + english_identifier + leixing_biaoshi
                test_identifiers.append(test_identifier)
            
            log_info(f"生成了{len(test_identifiers)}个测试项标识")
            return test_identifiers
            
        except Exception as e:
            log_error(f"生成测试项标识时发生错误: {str(e)}")
            return []

    def _create_fixed_strength_tests(self, basic_info: Dict[str, Any], current_test_count: int) -> List[Dict[str, Any]]:
        """
        创建固定的强度测试项
        
        Args:
            basic_info: 基础信息
            current_test_count: 当前测试项数量
            
        Returns:
            List[Dict[str, Any]]: 固定强度测试项列表
        """
        try:
            # 🔧 固定的强度测试定义（增加需求描述字段）
            fixed_strength_tests = [
                {
                    'name': '强度测试-运行时间测试',
                    'requirement_description': '软件需连续运行7.2个小时无功能异常',
                    'description': '测试软件连续运行7.2个小时是否会出现功能异常。',
                    'test_method': '步骤1：软件连续运行7.2个小时，通过调试计算机的内存监控及检测仪状态监控界面观察软件是否出现异常比如卡顿、故障等。'
                },
                {
                    'name': '强度测试-频繁指令处理测试',
                    'requirement_description': '软件需能处理高频率指令无故障',
                    'description': '测试软件对高频率的指令是否能进行处理。',
                    'test_method': '步骤1：通过检测仪连续、随机发送各种测试指令，连续发送三分钟以上，通过调试计算机的内存监控及检测仪状态监控界面观察软件是否出现故障或卡顿。'
                }
            ]
            
            strength_test_items = []
            base_identifier = basic_info.get('base_identifier', 'CT-UNKNOWN')
            
            for i, strength_def in enumerate(fixed_strength_tests, 1):
                # 生成强度测试项标识符 (按要求格式: CT-软件标识-版本-StrengthTest-ST01)
                strength_identifier = f"{base_identifier}-StrengthTest-ST{i:02d}"
                
                # 创建强度测试项
                strength_item = {
                    'index': current_test_count + i,
                    'name': strength_def['name'],
                    'pure_name': strength_def['name'],
                    'test_item_name': strength_def['name'],
                    'test_item_identifier': strength_identifier,
                    'test_type': '强度测试',
                    'software_requirement_trace': f"《{basic_info.get('software_name', '软件')}需求规格说明》 典型需求",  # 🔧 修改格式
                    'chapter_number': '',
                    'software_requirement_trace_relation': f"《{basic_info.get('software_name', '软件')}需求规格说明》 典型需求",  # 🔧 修改格式
                    'requirement_name': strength_def['name'],
                    'standard_sub_requirement_name': strength_def['name'],
                    'standard_sub_requirement_unit': '0.2',
                    'task_requirement_trace': '无',
                    'software_requirement_name': strength_def['name'],
                    'requirement_description': strength_def['requirement_description'],
                    'requirement_sub_description': strength_def['requirement_description'],
                    'test_description': strength_def['description'],
                    'test_method': strength_def['test_method'],
                    'pass_criteria': '各测试步骤、测试用例执行结果与预期一致，强度指标满足要求',
                    'adequacy_requirement': '所有强度测试用例执行完毕，对于未执行的用例说明未执行原因',
                    'english_identifier': identifier_generator.generate_strength_test_identifier(i),
                    '_is_strength_item': True,  # 标记为强度测试项
                    '_is_fixed_strength': True  # 标记为固定强度测试项
                }
                
                strength_test_items.append(strength_item)
                log_debug(f"创建固定强度测试项: {strength_def['name']}", "data_processor")
            
            log_info(f"固定强度测试项创建完成，共{len(strength_test_items)}项", "data_processor")
            return strength_test_items
            
        except Exception as e:
            log_error(f"创建固定强度测试项失败: {e}", "data_processor")
            import traceback
            log_error(f"错误详情: {traceback.format_exc()}", "data_processor")
            return []

    def _create_fixed_allowance_tests(self, basic_info: Dict[str, Any], current_test_count: int) -> List[Dict[str, Any]]:
        """
        创建固定的余量测试项（基于hanshutiqu_kaifa项目的思路）
        
        Args:
            basic_info: 基础信息
            current_test_count: 当前测试项数量
            
        Returns:
            List[Dict[str, Any]]: 固定余量测试项列表
        """
        try:
            # 🔧 固定的余量测试定义（增加需求描述字段）
            fixed_allowance_tests = [
                {
                    'name': '余量测试-内存余量（DDR）',
                    'requirement_description': '软件的DDR内存余量需大于30%',
                    'description': '测试软件的运行余量是否满足需求大于30%的要求。',
                    'test_method': '查看软件DDR存储空间的大小，以及软件编译后的软件的大小，两者相除，即为DDR空间的占有率，用1减去这个数即为软件的DDR存储余量。'
                },
                {
                    'name': '余量测试-内存余量（FLASH）',
                    'requirement_description': '软件的FLASH内存余量需大于30%',
                    'description': '测试软件的运行量是否满足需求大于30%的要求。',
                    'test_method': '软件通过代码审查计算软件，运行时需要占用的flash内存的大小，然后与FLASH的内存相除，，用1减去这个数即为软件的FLASH存储余量。'
                },
                {
                    'name': '余量测试-运行余量',
                    'requirement_description': '软件的CPU运行余量需大于30%',
                    'description': '测试软件的运行量是否满足需求大于30%的要求。',
                    'test_method': '软件正常运行，通过调试计算机中软件编译环境的内存监控功能查看软件的运行余量是否大于30%。'
                }
            ]
            
            allowance_test_items = []
            base_identifier = basic_info.get('base_identifier', 'CT-UNKNOWN')
            
            for i, allowance_def in enumerate(fixed_allowance_tests, 1):
                # 生成余量测试项标识符 (按要求格式: CT-软件标识-版本-AllowanceTest-AL01)
                allowance_identifier = f"{base_identifier}-AllowanceTest-AL{i:02d}"
                
                # 创建余量测试项
                allowance_item = {
                    'index': current_test_count + i,
                    'name': allowance_def['name'],
                    'pure_name': allowance_def['name'],
                    'test_item_name': allowance_def['name'],
                    'test_item_identifier': allowance_identifier,
                    'test_type': '余量测试',
                    'software_requirement_trace': '典型需求',  # 🔧 参考hanshutiqu_kaifa项目
                    'chapter_number': '',
                    'software_requirement_trace_relation': f"《{basic_info.get('software_name', '软件')}》 余量测试",  # 🔧 恢复余量测试的正确格式
                    'requirement_name': allowance_def['name'],
                    'standard_sub_requirement_name': allowance_def['name'],
                    'standard_sub_requirement_unit': '0.2',
                    'task_requirement_trace': '无',
                    'software_requirement_name': allowance_def['name'],
                    'requirement_description': allowance_def['requirement_description'],
                    'requirement_sub_description': allowance_def['requirement_description'],
                    'test_description': allowance_def['description'],
                    'test_method': allowance_def['test_method'],
                    'pass_criteria': '各测试步骤、测试用例执行结果与预期一致，余量满足要求',
                    'adequacy_requirement': '所有余量测试用例执行完毕，对于未执行的用例说明未执行原因。',
                    'english_identifier': identifier_generator.generate_fixed_allowance_identifier(i),
                    '_is_allowance_item': True,  # 标记为余量测试项
                    '_is_fixed_allowance': True  # 标记为固定余量测试项
                }
                
                allowance_test_items.append(allowance_item)
                log_debug(f"创建固定余量测试项: {allowance_def['name']}", "data_processor")
            
            log_info(f"固定余量测试项创建完成，共{len(allowance_test_items)}项", "data_processor")
            return allowance_test_items
            
        except Exception as e:
            log_error(f"创建固定余量测试项失败: {e}", "data_processor")
            import traceback
            log_error(f"错误详情: {traceback.format_exc()}", "data_processor")
            return []
    
    def _extract_performance_chapter_tests(self, file_path: str, basic_info: Dict[str, Any], current_test_count: int) -> Optional[Dict[str, List[Dict[str, Any]]]]:
        """
        从性能章节提取余量测试项和性能测试项
        
        Args:
            file_path: 文档路径
            basic_info: 基本信息
            current_test_count: 当前测试项数量
            
        Returns:
            包含余量测试项和性能测试项的字典，未找到返回None
        """
        try:
            # 获取标准化文档路径
            session_dir = os.path.dirname(file_path) if file_path else None
            if not session_dir:
                log_warning("无法确定会话目录，跳过性能章节提取", "data_processor")
                return None
                
            standardized_doc_path = self.performance_chapter_extractor.get_standardized_document_path(session_dir)
            if not standardized_doc_path:
                log_info("未找到标准化文档，跳过性能章节提取", "data_processor")
                return None
            
            # 提取性能章节内容
            chapter_data = self.performance_chapter_extractor.extract_performance_chapter_content(standardized_doc_path)
            if not chapter_data:
                log_info("未找到性能需求章节", "data_processor")
                return None
            
            # AI分析性能需求内容
            analysis_result = self.performance_ai_analyzer.analyze_performance_requirements(
                chapter_data['content'], 
                chapter_data
            )
            
            if not analysis_result or (not analysis_result.get('allowance_tests') and not analysis_result.get('performance_tests')):
                log_info("性能需求分析未产生有效结果", "data_processor")
                return None
            
            # 转换为标准测试项格式
            result = {
                'allowance_tests': [],
                'performance_tests': []
            }
            
            # 处理余量测试项
            for i, allowance_item in enumerate(analysis_result.get('allowance_tests', [])):
                test_item = self._create_allowance_test_item_from_chapter(
                    allowance_item, basic_info, current_test_count + len(result['allowance_tests']) + len(result['performance_tests']), i
                )
                result['allowance_tests'].append(test_item)
            
            # 处理性能测试项
            for i, performance_item in enumerate(analysis_result.get('performance_tests', [])):
                test_item = self._create_performance_test_item_from_chapter(
                    performance_item, basic_info, current_test_count + len(result['allowance_tests']) + len(result['performance_tests']), i
                )
                result['performance_tests'].append(test_item)
            
            log_info(f"性能章节测试项提取成功: {len(result['allowance_tests'])}个余量项, {len(result['performance_tests'])}个性能项", "data_processor")
            return result
            
        except Exception as e:
            log_error(f"性能章节测试项提取失败: {e}", "data_processor")
            import traceback
            log_error(f"详细错误: {traceback.format_exc()}", "data_processor")
            return None
    
    def _create_allowance_test_item_from_chapter(self, allowance_item: Dict[str, Any], basic_info: Dict[str, Any], index: int, allowance_index: int) -> Dict[str, Any]:
        """
        从性能章节分析结果创建余量测试项
        
        Args:
            allowance_item: 余量测试项分析结果
            basic_info: 基本信息
            index: 测试项索引
            allowance_index: 余量测试项索引
            
        Returns:
            标准格式的余量测试项
        """
        software_id = basic_info.get('software_identifier', 'UNKNOWN')
        software_version = basic_info.get('software_version', '1.00')
        
        # 生成测试项标识符 (按要求格式: CT-软件标识-版本-ChapterAllow-AL01)
        english_identifier = identifier_generator.generate_allowance_chapter_identifier(allowance_index)
        test_item_identifier = f"CT-{software_id}-{software_version}-{english_identifier}-AL{allowance_index+1:02d}"
        
        # 🔧 修改：优先使用AI生成的测试描述和方法，如果没有则使用默认值
        ai_test_description = allowance_item.get('test_description', '')
        ai_test_method = allowance_item.get('test_method', '')
        
        # 如果AI没有生成，则使用默认模板作为备用
        if not ai_test_description or not ai_test_method:
            default_allowance_tests = {
                'DDR内存余量': {
                    'description': '1测试软件的DDR内存余量是否满足需求大于30%的要求',
                    'test_method': '1查看软件DDR存储空间的大小，以及软件编译后的软件的大小，两者相除，即为DDR空间的占有率，用1减去这个数即为软件的DDR存储余量'
                },
                'FLASH内存余量': {
                    'description': '1测试软件的FLASH内存余量是否满足需求大于30%的要求',
                    'test_method': '1软件通过代码审查计算软件，运行时需要占用的flash内存的大小，然后与FLASH的内存相除，用1减去这个数即为软件的FLASH存储余量'
                },
                'CPU余量': {
                    'description': '1测试软件的CPU运行余量是否满足需求大于30%的要求',
                    'test_method': '1软件正常运行，通过调试计算机中软件编译环境的内存监控功能查看软件的运行余量是否大于30%'
                }
            }
            
            allowance_name = allowance_item['name']
            default_info = default_allowance_tests.get(allowance_name, {})
            
            if not ai_test_description:
                ai_test_description = default_info.get('description', f'测试{allowance_name}是否满足需求要求。')
            if not ai_test_method:
                ai_test_method = default_info.get('test_method', '通过监控工具检查系统资源使用情况，验证余量是否满足要求。')
        
        # 🔧 关键修改：需求子项描述使用从性能章节提取的内容，测试描述和方法使用AI生成的内容
        extracted_requirement = allowance_item.get('extracted_requirement', allowance_item.get('requirement_description', ''))
        
        return {
            'index': index + 1,
            'test_item_identifier': test_item_identifier,
            'name': allowance_item['name'],
            'pure_name': allowance_item['name'],
            'chapter_number': allowance_item.get('chapter_number', ''),
            'requirement_name': allowance_item['name'],
            'standard_sub_requirement_name': allowance_item['name'],
            'standard_sub_requirement_unit': '0.2',
            'task_requirement_trace': '无',
            'software_requirement_name': allowance_item['name'],
            'requirement_description': extracted_requirement,  # 使用从性能章节提取的完整需求描述
            'requirement_sub_description': extracted_requirement,  # 🔧 使用从性能章节提取的具体内容
            'test_description': ai_test_description,  # 🔧 使用AI生成的测试描述（参考默认模板）
            'test_method': ai_test_method,  # 🔧 使用AI生成的测试方法（参考默认模板）
            'pass_criteria': '各测试步骤、测试用例执行结果与预期一致，余量满足要求',
            'adequacy_requirement': '所有余量测试用例执行完毕，对于未执行的用例说明未执行原因。',
            'test_type': '余量测试',  # 🔧 添加正确的测试类型
            'english_identifier': english_identifier,
            '_is_allowance_item': True,  # 标记为余量测试项
            '_source': 'performance_chapter',  # 标记来源
            'software_requirement_trace': f"《{basic_info.get('software_name', '')}软件需求规格说明》 {allowance_item.get('chapter_number', '')} {allowance_item.get('chapter_name', '性能需求')}".strip(),
            'software_requirement_trace_relation': f"《{basic_info.get('software_name', '')}软件需求规格说明》 {allowance_item.get('chapter_number', '')} {allowance_item.get('chapter_name', '性能需求')}".strip()
        }
    
    def _create_performance_test_item_from_chapter(self, performance_item: Dict[str, Any], basic_info: Dict[str, Any], index: int, performance_index: int) -> Dict[str, Any]:
        """
        从性能章节分析结果创建性能测试项
        
        Args:
            performance_item: 性能测试项分析结果
            basic_info: 基本信息
            index: 测试项索引
            performance_index: 性能测试项索引
            
        Returns:
            标准格式的性能测试项
        """
        software_id = basic_info.get('software_identifier', 'UNKNOWN')
        software_version = basic_info.get('software_version', '1.00')
        
        # 生成测试项标识符 (按要求格式: CT-软件标识-版本-ChapterPerf-PF01)
        english_identifier = identifier_generator.generate_performance_chapter_identifier(performance_index)
        test_item_identifier = f"CT-{software_id}-{software_version}-{english_identifier}-PF{performance_index+1:02d}"
        
        # 🔧 关键修改：性能测试项使用AI生成的测试描述和方法
        extracted_requirement = performance_item.get('requirement_description', '')
        ai_test_description = performance_item.get('test_description', f'验证{performance_item["name"]}的性能指标是否符合需求规格说明中的要求')
        ai_test_method = performance_item.get('test_method', f'1、设置性能测试环境；2、执行{performance_item["name"]}相关操作；3、测量关键性能指标；4、验证性能结果是否符合要求')
        
        return {
            'index': index + 1,
            'test_item_identifier': test_item_identifier,
            'name': performance_item['name'],
            'pure_name': performance_item['name'],
            'chapter_number': performance_item.get('chapter_number', ''),
            'requirement_name': performance_item['name'],
            'standard_sub_requirement_name': performance_item['name'],
            'standard_sub_requirement_unit': '0.2',
            'task_requirement_trace': '无',
            'software_requirement_name': performance_item['name'],
            'requirement_description': extracted_requirement,  # 使用从性能章节提取的需求描述
            'requirement_sub_description': extracted_requirement,  # 🔧 使用从性能章节提取的具体内容
            'test_description': ai_test_description,  # 🔧 使用AI生成的测试描述
            'test_method': ai_test_method,  # 🔧 使用AI生成的测试方法
            'pass_criteria': '各测试步骤、测试用例执行结果与预期一致，性能满足要求',
            'adequacy_requirement': '所有性能测试用例执行完毕，对于未执行的用例说明未执行原因。',
            'test_type': '性能测试',  # 🔧 添加正确的测试类型
            'english_identifier': english_identifier,
            '_is_performance_item': True,  # 标记为性能测试项
            '_source': 'performance_chapter',  # 标记来源
            'software_requirement_trace': f"《{basic_info.get('software_name', '')}软件需求规格说明》 {performance_item.get('chapter_number', '')} {performance_item.get('chapter_name', '性能需求')}".strip(),
            'software_requirement_trace_relation': f"《{basic_info.get('software_name', '')}软件需求规格说明》 {performance_item.get('chapter_number', '')} {performance_item.get('chapter_name', '性能需求')}".strip()
        }
