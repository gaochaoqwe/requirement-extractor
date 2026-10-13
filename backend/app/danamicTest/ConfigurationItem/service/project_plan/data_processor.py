"""
配置项测试项目策划表数据处理器

负责处理和组织配置项测试中项目策划表所需的数据。
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class ConfigurationItemProjectPlanDataProcessor:
    """配置项测试项目策划表数据处理器"""
    
    def __init__(self):
        """初始化数据处理器"""
        self.logger = logger
    
    def organize_project_plan_data(
        self,
        ruanjian_xinxi: Dict[str, List[str]],
        ruanjian_name: str,
        diama_biangeng_xuqiu: List[str],
        ceshileixing: str = "配置项测试",
        AI_fenx_flag_Anniu: int = 0
    ) -> Dict[str, Any]:
        """
        组织配置项测试项目策划表数据
        
        Args:
            ruanjian_xinxi: 软件信息字典
            ruanjian_name: 软件名称
            diama_biangeng_xuqiu: 代码变更需求列表
            ceshileixing: 测试类型
            AI_fenx_flag_Anniu: AI分析标志
            
        Returns:
            Dict[str, Any]: 组织好的项目策划表数据
        """
        try:
            self.logger.info("开始组织配置项测试项目策划表数据")
            
            # 基本信息
            basic_info = self._organize_basic_info(ruanjian_xinxi, ruanjian_name, ceshileixing)
            
            # 测试项信息
            test_items = self._organize_test_items(diama_biangeng_xuqiu)
            
            # 测试类型分析
            test_types = self._analyze_test_types(diama_biangeng_xuqiu)
            
            # 英文标识生成配置
            identifier_config = self._organize_identifier_config(AI_fenx_flag_Anniu)
            
            # 格式设置配置
            formatting_config = self._get_formatting_config()
            
            project_plan_data = {
                'basic_info': basic_info,
                'test_items': test_items,
                'test_types': test_types,
                'identifier_config': identifier_config,
                'formatting_config': formatting_config,
                'test_count': len(diama_biangeng_xuqiu),
                'table_type': '配置项测试项目策划表'
            }
            
            self.logger.info(f"项目策划表数据组织完成，共{len(diama_biangeng_xuqiu)}个测试项")
            return project_plan_data
            
        except Exception as e:
            self.logger.error(f"组织配置项测试项目策划表数据时发生错误: {str(e)}")
            return {}
    
    def _organize_basic_info(
        self,
        ruanjian_xinxi: Dict[str, List[str]],
        ruanjian_name: str,
        ceshileixing: str
    ) -> Dict[str, str]:
        """组织基本信息"""
        return {
            'software_name': ruanjian_name,
            'software_identifier': ruanjian_xinxi.get('软件标识', [''])[0],
            'software_version': ruanjian_xinxi.get('被测软件版本', [''])[0],
            'test_type': ceshileixing,
            'programming_language': ruanjian_xinxi.get('编程语言', ['C'])[0],
            'development_environment': ruanjian_xinxi.get('开发环境', ['SDK'])[0],
            'runtime_environment': ruanjian_xinxi.get('运行环境', ['Linux'])[0],
            'software_level': ruanjian_xinxi.get('软件等级', ['AAAA'])[0]
        }
    
    def _organize_test_items(self, diama_biangeng_xuqiu: List[str]) -> List[Dict[str, Any]]:
        """组织测试项信息"""
        test_items = []
        
        for i, test_item_name in enumerate(diama_biangeng_xuqiu):
            test_item = {
                'index': i + 1,
                'name': test_item_name,
                'description': '',  # 将在填充时根据内容字典填充
                'is_executed': '是',
                'remarks': '无',
                'english_identifier': '',  # 将在标识生成时填充
                'test_type_identifier': ''  # 将在类型分析时填充
            }
            test_items.append(test_item)
        
        return test_items
    
    def _analyze_test_types(self, diama_biangeng_xuqiu: List[str]) -> List[Dict[str, str]]:
        """分析测试类型"""
        test_types = []
        
        for test_item_name in diama_biangeng_xuqiu:
            # 基于测试项名称分析测试类型
            test_type_info = self._get_test_type_by_name(test_item_name)
            test_types.append(test_type_info)
        
        return test_types
    
    def _get_test_type_by_name(self, test_item_name: str) -> Dict[str, str]:
        """根据测试项名称获取测试类型"""
        # 配置项测试的测试类型映射
        type_mapping = {
            '功能': 'FN',
            '接口': 'IF', 
            '性能': 'PF',
            '数据': 'DT',
            '处理': 'PR',
            '控制': 'CT',
            '管理': 'MG',
            '监控': 'MN',
            '检测': 'DT',
            '故障': 'FT',
            '报警': 'AL',
            '通信': 'CM',
            '显示': 'DS',
            '输入': 'IN',
            '输出': 'OUT'
        }
        
        # 默认类型
        test_type = 'FN'  # 功能测试
        test_type_name = '功能测试'
        
        # 根据关键词匹配
        for keyword, type_code in type_mapping.items():
            if keyword in test_item_name:
                test_type = type_code
                test_type_name = f'{keyword}测试'
                break
        
        return {
            'type_code': test_type,
            'type_name': test_type_name,
            'test_item_name': test_item_name
        }
    
    def _organize_identifier_config(self, AI_fenx_flag_Anniu: int) -> Dict[str, Any]:
        """组织标识生成配置"""
        return {
            'use_ai_translation': AI_fenx_flag_Anniu == 1,
            'default_prefix': 'SRC-',
            'fallback_pattern': 'TestItem{hash}',
            'translation_service': 'ai_translation' if AI_fenx_flag_Anniu == 1 else 'default'  # 🔧 修复：移除libretranslate引用
        }
    
    def _get_formatting_config(self) -> Dict[str, Any]:
        """获取格式设置配置"""
        return {
            'colors': {
                'light_yellow': "FFFF99",
                'light_green': "CCFFCC", 
                'light_blue': "99CCFF"
            },
            'column_ranges': {
                'basic_info': [2, 5],      # 编号到测试项名称
                'identifiers': [6, 7],     # 英文标识和测试类型
                'descriptions': [8, 10]    # 描述、执行、备注
            },
            'border_style': 'thin',
            'alignment': {
                'wrap_text': True,
                'vertical': 'center'
            }
        }
    
    def validate_project_plan_data(self, project_plan_data: Dict[str, Any]) -> bool:
        """
        验证配置项测试项目策划表数据的完整性
        
        Args:
            project_plan_data: 项目策划表数据字典
            
        Returns:
            bool: 数据是否有效
        """
        try:
            # 检查必需的顶级键
            required_keys = ['basic_info', 'test_items', 'test_types', 'test_count']
            for key in required_keys:
                if key not in project_plan_data:
                    self.logger.error(f"缺少必需的数据键: {key}")
                    return False
            
            # 检查基本信息
            basic_info = project_plan_data['basic_info']
            required_basic_keys = ['software_name', 'software_version', 'test_type']
            for key in required_basic_keys:
                if key not in basic_info or not basic_info[key]:
                    self.logger.error(f"基本信息缺少必需字段: {key}")
                    return False
            
            # 检查测试项数量一致性
            test_items = project_plan_data['test_items']
            test_types = project_plan_data['test_types']
            test_count = project_plan_data['test_count']
            
            if len(test_items) != test_count:
                self.logger.error(f"测试项数量不一致: {len(test_items)} != {test_count}")
                return False
            
            if len(test_types) != test_count:
                self.logger.error(f"测试类型数量不一致: {len(test_types)} != {test_count}")
                return False
            
            # 检查测试项完整性
            for i, test_item in enumerate(test_items):
                required_item_keys = ['index', 'name']
                for key in required_item_keys:
                    if key not in test_item or not test_item[key]:
                        self.logger.error(f"测试项{i+1}缺少必需字段: {key}")
                        return False
            
            self.logger.info("配置项测试项目策划表数据验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"验证配置项测试项目策划表数据时发生错误: {str(e)}")
            return False
    
    def get_project_plan_statistics(self, project_plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取配置项测试项目策划表统计信息
        
        Args:
            project_plan_data: 项目策划表数据字典
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            test_types = project_plan_data.get('test_types', [])
            
            # 按测试类型统计
            type_stats = {}
            for test_type in test_types:
                type_name = test_type.get('type_name', '未知类型')
                type_stats[type_name] = type_stats.get(type_name, 0) + 1
            
            # 基本统计
            statistics = {
                'total_test_items': project_plan_data.get('test_count', 0),
                'software_name': project_plan_data.get('basic_info', {}).get('software_name', ''),
                'test_type': project_plan_data.get('basic_info', {}).get('test_type', ''),
                'type_distribution': type_stats,
                'table_type': '配置项测试项目策划表'
            }
            
            self.logger.info(f"项目策划表统计: 共{statistics['total_test_items']}个测试项")
            return statistics
            
        except Exception as e:
            self.logger.error(f"获取配置项测试项目策划表统计信息时发生错误: {str(e)}")
            return {}
    
    def extract_test_requirements(self, project_plan_data: Dict[str, Any]) -> List[str]:
        """
        从项目策划表数据中提取测试需求列表
        
        Args:
            project_plan_data: 项目策划表数据字典
            
        Returns:
            List[str]: 测试需求列表
        """
        try:
            test_items = project_plan_data.get('test_items', [])
            requirements = [item.get('name', '') for item in test_items if item.get('name')]
            
            self.logger.info(f"提取到{len(requirements)}个测试需求")
            return requirements
            
        except Exception as e:
            self.logger.error(f"提取测试需求时发生错误: {str(e)}")
            return []
    
    def update_test_item_description(
        self,
        project_plan_data: Dict[str, Any],
        item_index: int,
        description: str
    ) -> bool:
        """
        更新测试项描述
        
        Args:
            project_plan_data: 项目策划表数据字典
            item_index: 测试项索引（从0开始）
            description: 新的描述
            
        Returns:
            bool: 更新是否成功
        """
        try:
            test_items = project_plan_data.get('test_items', [])
            
            if 0 <= item_index < len(test_items):
                test_items[item_index]['description'] = description
                self.logger.info(f"更新测试项{item_index+1}的描述")
                return True
            else:
                self.logger.error(f"测试项索引超出范围: {item_index}")
                return False
                
        except Exception as e:
            self.logger.error(f"更新测试项描述时发生错误: {str(e)}")
            return False
