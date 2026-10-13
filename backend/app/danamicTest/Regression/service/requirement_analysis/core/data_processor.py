"""
回归测试需求分析表数据处理器

负责回归测试需求分析表的数据组织、验证和处理功能，包括：
- 基本信息组织（软件信息、测试类型等）
- 测试项数据组织（22列完整信息）
- 文档信息组织（文档路径、软件名称等）
- AI配置组织（AI分析参数）
- 测试标识生成（回归测试专用标识）
- 数据验证和统计
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class RegressionRequirementAnalysisDataProcessor:
    """回归测试需求分析表数据处理器"""
    
    def __init__(self):
        """初始化回归测试需求分析表数据处理器"""
        self.logger = logger
        
        # 回归测试特有的测试标识前缀
        self.test_identifier_prefixes = {
            '回归测试': 'CT_R-',
            '配置项测试': 'CT-',
            '系统测试': 'ST-'
        }
        
        # 回归测试需求分析表列映射
        self.column_mapping = {
            'serial_number': 2,                           # 编号
            'software_name': 3,                           # 软件配置项名称
            'software_version': 4,                        # 被测软件版本
            'test_round': 5,                              # 轮次
            'standard_sub_requirement_name': 6,           # 标准子需求名称
            'standard_sub_requirement_identifier': 7,     # 标准子需求标识
            'standard_sub_requirement_unit': 8,           # 标准子需求单位
            'task_requirement_trace': 9,                  # 任务书需求追溯
            'software_requirement_spec_trace': 10,        # 软件需求规格说明追踪
            'software_requirement_name': 11,              # 软件需求规格说明需求名称
            'software_requirement_identifier': 12,        # 软件需求规格说明需求标识
            'software_requirement_description': 13,       # 软件需求描述
            'test_type': 14,                              # 测试类型
            'test_item_name': 15,                         # 测试项名称
            'test_item_identifier': 16,                   # 测试项标识
            'software_requirement_trace_relation': 17,    # 软件需求规格说明条目追踪关系
            'design_constraint': 18,                      # 设计约束
            'requirement_sub_item_description': 19,       # 需求子项描述
            'test_description': 20,                       # 测试项描述
            'test_method': 21,                            # 测试方法
            'adequacy_requirement': 22,                   # 充分性要求
            'pass_criteria': 23                           # 通过准则
        }
    
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
        jianceyi_flag: int
    ) -> Dict[str, Any]:
        """
        组织回归测试需求分析表数据
        
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
            
        Returns:
            Dict[str, Any]: 组织后的需求分析表数据
        """
        try:
            self.logger.info("开始组织回归测试需求分析表数据")
            
            # 组织基本信息
            basic_info = self._organize_basic_info(ruanjian_xinxi, ruanjian_name, ceshileixing)
            
            # 组织测试项信息
            test_items = self._organize_test_items(
                diama_biangeng_xuqiu, neirong_dict, biaoshihao_ceshixianng, basic_info
            )
            
            # 组织文档信息
            document_info = self._organize_document_info(file_path, ruanjian_name)
            
            # 组织AI配置
            ai_config = self._organize_ai_config(AI_fenx_flag_Anniu, jianceyi_flag)
            
            # 构建完整的需求分析表数据
            requirement_analysis_data = {
                'basic_info': basic_info,
                'test_items': test_items,
                'document_info': document_info,
                'ai_config': ai_config,
                'test_count': len(test_items),
                'table_type': '回归测试需求分析表',
                'column_mapping': self.column_mapping,
                'test_identifier_prefixes': self.test_identifier_prefixes
            }
            
            self.logger.info(f"回归测试需求分析表数据组织完成，共{len(test_items)}个测试项")
            return requirement_analysis_data
            
        except Exception as e:
            self.logger.error(f"组织回归测试需求分析表数据时发生错误: {str(e)}")
            return {}
    
    def _organize_basic_info(
        self,
        ruanjian_xinxi: Dict[str, List[str]],
        ruanjian_name: str,
        ceshileixing: str
    ) -> Dict[str, Any]:
        """
        组织基本信息
        
        Args:
            ruanjian_xinxi: 软件信息字典
            ruanjian_name: 软件名称
            ceshileixing: 测试类型
            
        Returns:
            Dict[str, Any]: 基本信息
        """
        # 提取软件基本信息
        software_identifier = ruanjian_xinxi.get('软件标识', [''])[0] if isinstance(ruanjian_xinxi.get('软件标识', ['']), list) else ruanjian_xinxi.get('软件标识', '')
        software_version = ruanjian_xinxi.get('被测软件版本', [''])[0] if isinstance(ruanjian_xinxi.get('被测软件版本', ['']), list) else ruanjian_xinxi.get('被测软件版本', '')
        
        # 生成测试需求标识前缀
        test_requirement_prefix = self._generate_test_requirement_prefix(
            ceshileixing, software_identifier, software_version
        )
        
        return {
            'software_name': ruanjian_name,
            'software_identifier': software_identifier,
            'software_version': software_version,
            'test_type': ceshileixing,
            'test_requirement_prefix': test_requirement_prefix,
            'test_round': '第一轮',
            'unit': '0.2',
            'task_trace': '无',
            'design_constraint': '无',
            'adequacy_requirement': '所有用例执行完毕，对于未执行的用例说明未执行原因。',
            'pass_criteria': '各测试步骤、测试用例执行结果与预期一致，功能实现正确'
        }
    
    def _organize_test_items(
        self,
        diama_biangeng_xuqiu: Dict[str, str],
        neirong_dict: List[str],
        biaoshihao_ceshixianng: List[str],
        basic_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        组织测试项信息
        
        Args:
            diama_biangeng_xuqiu: 代码变更需求字典
            neirong_dict: 内容描述列表
            biaoshihao_ceshixianng: 标识号测试项列表
            basic_info: 基本信息
            
        Returns:
            List[Dict[str, Any]]: 测试项列表
        """
        test_items = []
        test_names = list(diama_biangeng_xuqiu.keys())
        
        for index, test_name in enumerate(test_names):
            # 获取英文标识
            english_identifier = biaoshihao_ceshixianng[index] if index < len(biaoshihao_ceshixianng) else f'SRC-name{index}'
            
            # 获取需求描述
            requirement_description = neirong_dict[index] if index < len(neirong_dict) else ''
            
            # 构建测试项信息
            test_item = {
                'serial_number': index + 1,
                'name': test_name,
                'english_identifier': english_identifier,
                'requirement_description': requirement_description,
                'standard_sub_requirement_identifier': f'CT_R-{english_identifier}',
                'software_requirement_identifier': english_identifier,
                'test_description': '',  # 待生成
                'test_method': '',       # 待生成
                'test_type': '',         # 待分析
                'test_identifier': '',   # 待生成
                'chapter_number': '未找到具体章节号'  # 待读取
            }
            
            test_items.append(test_item)
        
        return test_items
    
    def _organize_document_info(self, file_path: str, ruanjian_name: str) -> Dict[str, Any]:
        """
        组织文档信息
        
        Args:
            file_path: 文档文件路径
            ruanjian_name: 软件名称
            
        Returns:
            Dict[str, Any]: 文档信息
        """
        return {
            'document_path': file_path,
            'software_name': ruanjian_name,
            'has_document': bool(file_path and Path(file_path).exists())
        }
    
    def _organize_ai_config(self, AI_fenx_flag_Anniu: int, jianceyi_flag: int) -> Dict[str, Any]:
        """
        组织AI配置
        
        Args:
            AI_fenx_flag_Anniu: AI分析标志
            jianceyi_flag: 检测仪标志
            
        Returns:
            Dict[str, Any]: AI配置
        """
        return {
            'enable_ai_analysis': AI_fenx_flag_Anniu == 1,
            'detector_flag': jianceyi_flag,
            'ai_analysis_attempts': 4,
            'use_knowledge_optimization': True
        }
    
    def _generate_test_requirement_prefix(
        self,
        ceshileixing: str,
        software_identifier: str,
        software_version: str
    ) -> str:
        """
        生成测试需求标识前缀
        
        Args:
            ceshileixing: 测试类型
            software_identifier: 软件标识
            software_version: 软件版本
            
        Returns:
            str: 测试需求标识前缀
        """
        prefix = self.test_identifier_prefixes.get(ceshileixing, 'CT-')
        return f"{prefix}{software_identifier}_{software_version}_"
    
    def generate_test_identifiers(
        self,
        requirement_analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成测试标识
        
        Args:
            requirement_analysis_data: 需求分析表数据
            
        Returns:
            Dict[str, Any]: 更新后的需求分析表数据
        """
        try:
            from .test_type_classifier import ceshi_leixing_biaoshi_choose
            
            basic_info = requirement_analysis_data.get('basic_info', {})
            test_items = requirement_analysis_data.get('test_items', [])
            test_requirement_prefix = basic_info.get('test_requirement_prefix', '')
            
            for test_item in test_items:
                test_name = test_item.get('name', '')
                english_identifier = test_item.get('english_identifier', '')
                
                # 分析测试类型和标识
                type_identifier, test_type = ceshi_leixing_biaoshi_choose(test_name)
                
                # 生成完整的测试项标识
                test_identifier = f"{test_requirement_prefix}{english_identifier}{type_identifier}"
                
                # 更新测试项信息
                test_item['test_type'] = test_type
                test_item['test_identifier'] = test_identifier
                test_item['type_identifier'] = type_identifier
            
            self.logger.info("测试标识生成完成")
            return requirement_analysis_data
            
        except Exception as e:
            self.logger.error(f"生成测试标识时发生错误: {str(e)}")
            return requirement_analysis_data
    
    def update_test_content(
        self,
        requirement_analysis_data: Dict[str, Any],
        test_descriptions: List[str],
        test_methods: List[str]
    ) -> Dict[str, Any]:
        """
        更新测试内容
        
        Args:
            requirement_analysis_data: 需求分析表数据
            test_descriptions: 测试描述列表
            test_methods: 测试方法列表
            
        Returns:
            Dict[str, Any]: 更新后的需求分析表数据
        """
        test_items = requirement_analysis_data.get('test_items', [])
        
        for index, test_item in enumerate(test_items):
            if index < len(test_descriptions):
                test_item['test_description'] = test_descriptions[index]
            if index < len(test_methods):
                test_item['test_method'] = test_methods[index]
        
        self.logger.info(f"测试内容更新完成，共更新{len(test_items)}个测试项")
        return requirement_analysis_data
    
    def update_chapter_numbers(
        self,
        requirement_analysis_data: Dict[str, Any],
        chapter_numbers: List[str]
    ) -> Dict[str, Any]:
        """
        更新章节号
        
        Args:
            requirement_analysis_data: 需求分析表数据
            chapter_numbers: 章节号列表
            
        Returns:
            Dict[str, Any]: 更新后的需求分析表数据
        """
        test_items = requirement_analysis_data.get('test_items', [])
        
        for index, test_item in enumerate(test_items):
            if index < len(chapter_numbers):
                test_item['chapter_number'] = chapter_numbers[index]
        
        self.logger.info(f"章节号更新完成，共更新{len(test_items)}个测试项")
        return requirement_analysis_data
    
    def validate_requirement_analysis_data(self, requirement_analysis_data: Dict[str, Any]) -> bool:
        """
        验证需求分析表数据
        
        Args:
            requirement_analysis_data: 需求分析表数据
            
        Returns:
            bool: 验证是否通过
        """
        try:
            # 检查必需的键
            required_keys = ['basic_info', 'test_items', 'document_info', 'ai_config']
            for key in required_keys:
                if key not in requirement_analysis_data:
                    self.logger.error(f"缺少必需的键: {key}")
                    return False
            
            # 检查测试项
            test_items = requirement_analysis_data.get('test_items', [])
            if not test_items:
                self.logger.error("测试项列表为空")
                return False
            
            # 检查每个测试项的必需字段
            required_test_item_fields = ['name', 'english_identifier']
            for index, test_item in enumerate(test_items):
                for field in required_test_item_fields:
                    if field not in test_item or not test_item[field]:
                        self.logger.error(f"测试项{index + 1}缺少必需字段: {field}")
                        return False
            
            self.logger.info("需求分析表数据验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"验证需求分析表数据时发生错误: {str(e)}")
            return False
    
    def get_requirement_analysis_statistics(self, requirement_analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取需求分析表统计信息
        
        Args:
            requirement_analysis_data: 需求分析表数据
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        test_items = requirement_analysis_data.get('test_items', [])
        basic_info = requirement_analysis_data.get('basic_info', {})
        
        # 统计测试类型分布
        test_type_distribution = {}
        for test_item in test_items:
            test_type = test_item.get('test_type', '未知')
            test_type_distribution[test_type] = test_type_distribution.get(test_type, 0) + 1
        
        # 统计内容完整性
        complete_descriptions = sum(1 for item in test_items if item.get('test_description'))
        complete_methods = sum(1 for item in test_items if item.get('test_method'))
        complete_identifiers = sum(1 for item in test_items if item.get('test_identifier'))
        
        return {
            'total_test_items': len(test_items),
            'software_name': basic_info.get('software_name', ''),
            'test_type': basic_info.get('test_type', ''),
            'test_type_distribution': test_type_distribution,
            'complete_descriptions': complete_descriptions,
            'complete_methods': complete_methods,
            'complete_identifiers': complete_identifiers,
            'completion_rate': {
                'descriptions': round(complete_descriptions / len(test_items) * 100, 2) if test_items else 0,
                'methods': round(complete_methods / len(test_items) * 100, 2) if test_items else 0,
                'identifiers': round(complete_identifiers / len(test_items) * 100, 2) if test_items else 0
            }
        }
