"""
配置项测试需求分析表读取器

负责从Excel文件中读取配置项测试需求分析表的数据。
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class ConfigurationItemRequirementAnalysisReader:
    """配置项测试需求分析表读取器"""
    
    def __init__(self):
        """初始化读取器"""
        self.logger = logger
    
    def read_requirement_analysis_data(
        self,
        excel_file_path: str,
        sheet_name: str = '需求分析表'
    ) -> Tuple[Dict[str, Any], str]:
        """
        读取配置项测试需求分析表数据
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            Tuple[Dict[str, Any], str]: (需求分析表数据, 状态信息)
        """
        try:
            self.logger.info(f"开始读取配置项测试需求分析表: {excel_file_path}")
            
            # 导入必要的模块
            from ....utils.excel_processing.excel_reader import read_excel_with_sheet
            
            # 读取Excel数据
            df = read_excel_with_sheet(excel_file_path, sheet_name=sheet_name)
            
            # 检查数据完整性
            if df.shape[0] < 2:
                return {}, "需求分析表数据不足"
            
            # 提取基本信息（从第一行数据中提取）
            basic_info = self._extract_basic_info(df)
            
            # 提取测试项数据
            test_items = self._extract_test_items(df)
            
            # 组织返回数据
            requirement_analysis_data = {
                'basic_info': basic_info,
                'test_items': test_items,
                'test_count': len(test_items),
                'table_type': '配置项测试需求分析表'
            }
            
            status_msg = f"成功读取{len(test_items)}个测试项"
            
            self.logger.info(f"配置项测试需求分析表读取完成，共{len(test_items)}个测试项")
            return requirement_analysis_data, status_msg
            
        except Exception as e:
            self.logger.error(f"读取配置项测试需求分析表时发生错误: {str(e)}")
            return {}, f"读取失败: {e}"
    
    def _extract_basic_info(self, df) -> Dict[str, str]:
        """提取基本信息"""
        try:
            # 从第一行数据中提取基本信息
            if df.shape[0] > 1:
                first_row = df.iloc[1]  # 第二行是第一个测试项
                
                basic_info = {
                    'software_name': str(first_row.iloc[2]) if len(first_row) > 2 and first_row.iloc[2] is not None else '',
                    'software_version': str(first_row.iloc[3]) if len(first_row) > 3 and first_row.iloc[3] is not None else '',
                    'test_round': str(first_row.iloc[4]) if len(first_row) > 4 and first_row.iloc[4] is not None else '第一轮',
                    'test_type': '配置项测试'  # 默认类型
                }
                
                # 尝试从测试项标识中提取更多信息
                if len(first_row) > 15 and first_row.iloc[15] is not None:
                    test_identifier = str(first_row.iloc[15])
                    if test_identifier.startswith('CT-'):
                        basic_info['test_type'] = '配置项测试'
                    elif test_identifier.startswith('CT_R-'):
                        basic_info['test_type'] = '回归测试'
                    elif test_identifier.startswith('ST-'):
                        basic_info['test_type'] = '系统测试'
                
                return basic_info
            else:
                return {
                    'software_name': '',
                    'software_version': '',
                    'test_round': '第一轮',
                    'test_type': '配置项测试'
                }
                
        except Exception as e:
            self.logger.error(f"提取基本信息时发生错误: {str(e)}")
            return {}
    
    def _extract_test_items(self, df) -> List[Dict[str, Any]]:
        """提取测试项数据"""
        try:
            test_items = []
            
            # 从第二行开始读取测试项数据（第一行是标题）
            for index, row in df.iloc[1:].iterrows():
                # 检查是否为有效的测试项行
                if len(row) < 15 or row.iloc[14] is None or str(row.iloc[14]).strip() == '':
                    continue
                
                test_item_name = str(row.iloc[14]) if row.iloc[14] is not None else ''
                test_item = {
                    'index': int(row.iloc[1]) if row.iloc[1] is not None else index,
                    'software_name': str(row.iloc[2]) if row.iloc[2] is not None else '',
                    'software_version': str(row.iloc[3]) if row.iloc[3] is not None else '',
                    'test_round': str(row.iloc[4]) if row.iloc[4] is not None else '第一轮',
                    'standard_sub_requirement_name': str(row.iloc[5]) if row.iloc[5] is not None else '',
                    'standard_sub_requirement_identifier': str(row.iloc[6]) if row.iloc[6] is not None else '',
                    'standard_sub_requirement_unit': str(row.iloc[7]) if row.iloc[7] is not None else '0.2',
                    'task_requirement_trace': str(row.iloc[8]) if row.iloc[8] is not None else '无',
                    'software_requirement_spec_trace': str(row.iloc[9]) if row.iloc[9] is not None else '',
                    'software_requirement_name': str(row.iloc[10]) if row.iloc[10] is not None else '',
                    'software_requirement_identifier': str(row.iloc[11]) if row.iloc[11] is not None else '',
                    'software_requirement_description': str(row.iloc[12]) if row.iloc[12] is not None else '',
                    'test_type': str(row.iloc[13]) if row.iloc[13] is not None else '',
                    'test_item_name': test_item_name,
                    'pure_name': test_item_name,  # 为了兼容新模块，添加pure_name字段
                    'test_item_identifier': str(row.iloc[15]) if len(row) > 15 and row.iloc[15] is not None else '',
                    'software_requirement_trace_relation': str(row.iloc[16]) if len(row) > 16 and row.iloc[16] is not None else '',
                    'design_constraint': str(row.iloc[17]) if len(row) > 17 and row.iloc[17] is not None else '无',
                    'test_description': str(row.iloc[18]) if len(row) > 18 and row.iloc[18] is not None else '',
                    'test_method': str(row.iloc[19]) if len(row) > 19 and row.iloc[19] is not None else '',
                    'adequacy_requirement': str(row.iloc[20]) if len(row) > 20 and row.iloc[20] is not None else '',
                    'pass_criteria': str(row.iloc[21]) if len(row) > 21 and row.iloc[21] is not None else '',
                    'requirement_description': str(row.iloc[12]) if row.iloc[12] is not None else ''  # 为了兼容新模块
                }
                
                test_items.append(test_item)
            
            return test_items
            
        except Exception as e:
            self.logger.error(f"提取测试项数据时发生错误: {str(e)}")
            return []
    
    def validate_requirement_analysis_structure(
        self,
        excel_file_path: str,
        sheet_name: str = '需求分析表'
    ) -> bool:
        """
        验证配置项测试需求分析表结构
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            bool: 结构是否有效
        """
        try:
            from ....utils.excel_processing.excel_reader import read_excel_with_sheet
            
            df = read_excel_with_sheet(excel_file_path, sheet_name=sheet_name)
            
            # 检查基本结构
            if df.shape[0] < 2:  # 至少需要标题行和一行数据
                self.logger.error("配置项测试需求分析表行数不足")
                return False
            
            if df.shape[1] < 22:  # 至少需要22列
                self.logger.error("配置项测试需求分析表列数不足")
                return False
            
            # 检查关键列是否有数据
            test_item_names = df.iloc[1:, 14].dropna()  # 测试项名称列
            if len(test_item_names) == 0:
                self.logger.error("未找到有效的测试项数据")
                return False
            
            self.logger.info("配置项测试需求分析表结构验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"验证配置项测试需求分析表结构时发生错误: {str(e)}")
            return False
    
    def get_requirement_analysis_summary(
        self,
        excel_file_path: str,
        sheet_name: str = '需求分析表'
    ) -> Dict[str, Any]:
        """
        获取配置项测试需求分析表摘要信息
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            Dict[str, Any]: 摘要信息
        """
        try:
            requirement_analysis_data, status_msg = self.read_requirement_analysis_data(excel_file_path, sheet_name)
            
            if not requirement_analysis_data:
                return {
                    'total_test_items': 0,
                    'software_name': '',
                    'test_type': '',
                    'completion_rate': 0,
                    'status_message': status_msg,
                    'test_items_list': [],
                    'table_type': '配置项测试需求分析表'
                }
            
            basic_info = requirement_analysis_data.get('basic_info', {})
            test_items = requirement_analysis_data.get('test_items', [])
            
            # 统计完成情况
            completed_items = 0
            for test_item in test_items:
                if (test_item.get('test_description') and 
                    test_item.get('test_method') and 
                    test_item.get('test_item_identifier')):
                    completed_items += 1
            
            # 统计信息
            summary = {
                'total_test_items': len(test_items),
                'completed_test_items': completed_items,
                'software_name': basic_info.get('software_name', ''),
                'software_version': basic_info.get('software_version', ''),
                'test_type': basic_info.get('test_type', ''),
                'test_round': basic_info.get('test_round', ''),
                'completion_rate': round(completed_items / len(test_items) * 100, 2) if test_items else 0,
                'status_message': status_msg,
                'test_items_list': [item.get('test_item_name', '') for item in test_items[:5]],  # 前5个测试项作为示例
                'table_type': '配置项测试需求分析表'
            }
            
            self.logger.info(f"配置项测试需求分析表摘要: 共{summary['total_test_items']}个测试项")
            return summary
            
        except Exception as e:
            self.logger.error(f"获取配置项测试需求分析表摘要时发生错误: {str(e)}")
            return {
                'total_test_items': 0,
                'completed_test_items': 0,
                'software_name': '',
                'test_type': '',
                'completion_rate': 0,
                'status_message': f"读取失败: {e}",
                'test_items_list': [],
                'table_type': '配置项测试需求分析表'
            }
    
    def extract_test_requirements_only(
        self,
        excel_file_path: str,
        sheet_name: str = '需求分析表'
    ) -> List[str]:
        """
        仅提取测试需求列表
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            List[str]: 测试需求列表
        """
        try:
            requirement_analysis_data, _ = self.read_requirement_analysis_data(excel_file_path, sheet_name)
            test_items = requirement_analysis_data.get('test_items', [])
            
            test_requirements = [item.get('test_item_name', '') for item in test_items if item.get('test_item_name')]
            
            self.logger.info(f"提取到{len(test_requirements)}个测试需求")
            return test_requirements
            
        except Exception as e:
            self.logger.error(f"提取测试需求时发生错误: {str(e)}")
            return []
    
    def check_test_content_completeness(
        self,
        excel_file_path: str,
        sheet_name: str = '需求分析表'
    ) -> Dict[str, Any]:
        """
        检查测试内容完整性
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            Dict[str, Any]: 检查结果
        """
        try:
            requirement_analysis_data, status_msg = self.read_requirement_analysis_data(excel_file_path, sheet_name)
            test_items = requirement_analysis_data.get('test_items', [])
            
            # 检查各项内容的完整性
            missing_descriptions = []
            missing_methods = []
            missing_identifiers = []
            
            for i, test_item in enumerate(test_items):
                if not test_item.get('test_description') or test_item.get('test_description').strip() == '':
                    missing_descriptions.append(i)
                
                if not test_item.get('test_method') or test_item.get('test_method').strip() == '':
                    missing_methods.append(i)
                
                if not test_item.get('test_item_identifier') or test_item.get('test_item_identifier').strip() == '':
                    missing_identifiers.append(i)
            
            # 检查结果
            result = {
                'total_test_items': len(test_items),
                'missing_descriptions_count': len(missing_descriptions),
                'missing_descriptions_indices': missing_descriptions,
                'missing_methods_count': len(missing_methods),
                'missing_methods_indices': missing_methods,
                'missing_identifiers_count': len(missing_identifiers),
                'missing_identifiers_indices': missing_identifiers,
                'is_complete': (len(missing_descriptions) == 0 and 
                               len(missing_methods) == 0 and 
                               len(missing_identifiers) == 0),
                'status_message': status_msg
            }
            
            self.logger.info(f"测试内容完整性检查: 缺失描述{result['missing_descriptions_count']}个，缺失方法{result['missing_methods_count']}个")
            return result
            
        except Exception as e:
            self.logger.error(f"检查测试内容完整性时发生错误: {str(e)}")
            return {
                'total_test_items': 0,
                'missing_descriptions_count': 0,
                'missing_descriptions_indices': [],
                'missing_methods_count': 0,
                'missing_methods_indices': [],
                'missing_identifiers_count': 0,
                'missing_identifiers_indices': [],
                'is_complete': False,
                'status_message': f"检查失败: {e}"
            }
    
    def get_test_type_statistics(
        self,
        excel_file_path: str,
        sheet_name: str = '需求分析表'
    ) -> Dict[str, int]:
        """
        获取测试类型统计
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            Dict[str, int]: 测试类型统计
        """
        try:
            requirement_analysis_data, _ = self.read_requirement_analysis_data(excel_file_path, sheet_name)
            test_items = requirement_analysis_data.get('test_items', [])
            
            type_statistics = {}
            
            for test_item in test_items:
                test_type = test_item.get('test_type', '未知')
                type_statistics[test_type] = type_statistics.get(test_type, 0) + 1
            
            self.logger.info(f"测试类型统计: {type_statistics}")
            return type_statistics
            
        except Exception as e:
            self.logger.error(f"获取测试类型统计时发生错误: {str(e)}")
            return {}
    
    def export_test_items_to_dict(
        self,
        excel_file_path: str,
        sheet_name: str = '需求分析表'
    ) -> Dict[str, str]:
        """
        导出测试项为字典格式
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            Dict[str, str]: 测试项字典（测试项名称: 测试描述）
        """
        try:
            requirement_analysis_data, _ = self.read_requirement_analysis_data(excel_file_path, sheet_name)
            test_items = requirement_analysis_data.get('test_items', [])
            
            test_dict = {}
            for test_item in test_items:
                test_name = test_item.get('test_item_name', '')
                test_description = test_item.get('test_description', '')
                if test_name:
                    test_dict[test_name] = test_description
            
            self.logger.info(f"导出了{len(test_dict)}个测试项")
            return test_dict
            
        except Exception as e:
            self.logger.error(f"导出测试项字典时发生错误: {str(e)}")
            return {}
