"""
回归测试软件配置项信息数据处理器

负责处理和组织回归测试中软件配置项信息表所需的数据。
"""

import logging
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class RegressionSoftwareConfigDataProcessor:
    """回归测试软件配置项信息数据处理器"""
    
    def __init__(self):
        """初始化数据处理器"""
        self.logger = logger
    
    def organize_software_config_data(
        self,
        ruanjian_name: str,
        ceshiren_name: str,
        zhuguan_name: str,
        daima_chayi_hangshu: int,
        xinghao_xinxi_list: Optional[List[str]] = None,
        ruanjian_xinxi_duqu_temp: Optional[Dict[str, Any]] = None,
        ceshileixing: str = "回归测试",
        user_software_info: Optional[Dict[str, Any]] = None,
        planning_requirements_count: int = 0,
        analysis_requirements_count: int = 0,
        code_path: Optional[str] = None,
        requirement_doc_path: Optional[str] = None,  # 添加需求文档路径参数
        impact_analysis_doc_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        组织回归测试软件配置项信息数据
        
        Args:
            ruanjian_name: 软件名称
            ceshiren_name: 测试人员姓名
            zhuguan_name: 测试主管姓名
            daima_chayi_hangshu: 代码差异行数
            xinghao_xinxi_list: 型号信息列表
            ruanjian_xinxi_duqu_temp: 从文档读取的软件信息
            ceshileixing: 测试类型
            user_software_info: 用户提供的软件信息
            planning_requirements_count: 策划表需求数量
            analysis_requirements_count: 分析表需求数量
            code_path: 代码路径（用于代码统计）
            requirement_doc_path: 需求文档路径（用于环境信息提取）
            impact_analysis_doc_path: 影响域分析报告路径
            
        Returns:
            Dict[str, Any]: 组织后的软件配置数据
        """
        try:
            # 组织基本信息
            basic_info = self._organize_basic_info(
                ruanjian_name, ceshiren_name, zhuguan_name, 
                daima_chayi_hangshu, ceshileixing
            )
            
            # 进行代码统计（回归测试特有）
            code_statistics = self._perform_code_statistics(daima_chayi_hangshu, code_path)
            
            # 组织软件详细信息
            software_details = self._organize_software_details(
                xinghao_xinxi_list, ruanjian_xinxi_duqu_temp, user_software_info
            )
            
            # 组织环境信息（回归测试特有）
            environment_info = self._organize_environment_info(
                xinghao_xinxi_list, impact_analysis_doc_path
            )
            
            # 组织统计信息
            statistics_info = self._organize_statistics_info(
                planning_requirements_count, analysis_requirements_count, 
                code_statistics['final_code_lines']
            )
            
            # 组织时间信息
            time_info = self._organize_time_info(code_statistics['final_code_lines'])
            
            # 组织固定值信息（回归测试专用）
            fixed_values = self._get_fixed_values(ceshileixing)
            
            # 组织完整的软件配置数据
            software_config_data = {
                'basic_info': basic_info,
                'code_statistics': code_statistics,
                'software_details': software_details,
                'environment_info': environment_info,
                'statistics_info': statistics_info,
                'time_info': time_info,
                'fixed_values': fixed_values,
                'requirement_doc_path': requirement_doc_path,  # 添加需求文档路径
                'impact_analysis_doc_path': impact_analysis_doc_path,
                'data_sources': self._get_data_sources(xinghao_xinxi_list, ruanjian_xinxi_duqu_temp, user_software_info)
            }
            
            self.logger.debug(f"回归测试软件配置项数据组织完成，软件规模: {code_statistics['final_code_lines']} 行")  # 改为DEBUG级别
            return software_config_data
            
        except Exception as e:
            self.logger.error(f"组织回归测试软件配置项数据时发生错误: {str(e)}")
            raise
    
    def _organize_basic_info(
        self, 
        ruanjian_name: str, 
        ceshiren_name: str, 
        zhuguan_name: str, 
        daima_chayi_hangshu: int, 
        ceshileixing: str
    ) -> Dict[str, Any]:
        """组织基本信息"""
        return {
            'software_name': ruanjian_name,
            'tester_name': ceshiren_name,
            'manager_name': zhuguan_name,
            'original_code_lines': daima_chayi_hangshu,
            'test_type': ceshileixing,
            'is_same_person': ceshiren_name == zhuguan_name
        }
    
    def _perform_code_statistics(self, daima_chayi_hangshu: int, code_path: Optional[str]) -> Dict[str, Any]:
        """执行代码统计（回归测试特有功能）"""
        calculated_code_lines = daima_chayi_hangshu  # 初始值
        
        self.logger.info(f"开始软件规模计算：原始值={daima_chayi_hangshu}, 代码路径={code_path}")
        
        # 如果提供了代码路径，优先使用代码统计
        if code_path and os.path.exists(code_path):
            try:
                self.logger.info(f"开始进行代码统计，路径: {code_path}")
                calculated_code_lines = self._analyze_code_path(code_path, daima_chayi_hangshu)
            except Exception as e:
                self.logger.error(f"代码统计过程中发生错误: {e}，使用原始值: {daima_chayi_hangshu}")
        else:
            # 没有提供代码路径时的处理逻辑
            if daima_chayi_hangshu <= 0:
                calculated_code_lines = 5000  # 使用默认软件规模
                self.logger.info(f"未提供代码路径且传入代码行数为0，使用默认软件规模: {calculated_code_lines}")
            else:
                self.logger.info(f"未提供代码路径，使用传入的软件规模: {calculated_code_lines}")
        
        self.logger.info(f"最终软件规模: {calculated_code_lines}")
        
        return {
            'original_code_lines': daima_chayi_hangshu,
            'final_code_lines': int(calculated_code_lines) if isinstance(calculated_code_lines, (str, float)) else calculated_code_lines,
            'code_path': code_path,
            'statistics_performed': code_path is not None and os.path.exists(code_path) if code_path else False
        }
    
    def _analyze_code_path(self, code_path: str, default_lines: int) -> int:
        """分析代码路径并返回代码行数"""
        try:
            from ...utils.code_analysis.software_stats import CodeStatistics
            
            code_stats = CodeStatistics()
            
            # 如果是zip文件，需要先解压
            if code_path.endswith('.zip'):
                import tempfile
                temp_dir = tempfile.mkdtemp(prefix='code_analysis_')
                self.logger.info(f"检测到zip文件，创建临时目录: {temp_dir}")
                result = code_stats.analyze_code(code_path, 'temp_task', temp_dir)
                if result.get('analysis_success', False):
                    calculated_lines = result.get('total_lines', default_lines)
                    self.logger.info(f"zip文件代码统计成功，总行数: {calculated_lines}")
                else:
                    self.logger.warning(f"zip文件代码统计失败，使用原始值: {default_lines}")
                    calculated_lines = default_lines
                # 清理临时文件
                if 'extract_dir' in result and os.path.exists(result['extract_dir']):
                    code_stats.cleanup_extracted_files(result['extract_dir'])
                    self.logger.info(f"清理临时解压目录: {result['extract_dir']}")
            else:
                # 直接分析目录
                self.logger.info(f"直接分析目录: {code_path}")
                result = code_stats.simple_line_count(code_path)
                if result.get('analysis_success', False):
                    calculated_lines = result.get('total_lines', default_lines)
                    self.logger.info(f"目录代码统计成功，总行数: {calculated_lines}")
                else:
                    self.logger.warning(f"目录代码统计失败，使用原始值: {default_lines}")
                    calculated_lines = default_lines
            
            return calculated_lines
            
        except Exception as e:
            self.logger.error(f"代码分析失败: {e}")
            return default_lines
    
    def _organize_software_details(
        self, 
        xinghao_xinxi_list: Optional[List[str]], 
        ruanjian_xinxi_duqu_temp: Optional[Dict[str, Any]], 
        user_software_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """组织软件详细信息"""
        details = {
            'software_short_name': '',
            'software_short_name_en': '',
            'software_id': '',
            'software_version': '',
            'system_name': '',
            'system_short_name': '',
            'component': '',
            'software_code': '',
            'programming_language': 'C',
            'software_level': '重要'
        }
        
        # 优先级：用户输入 > 型号信息库 > 文档提取 > AI生成 > 默认值
        if user_software_info:
            details.update({
                'software_name': user_software_info.get('software_name', ''),
                'software_id': user_software_info.get('software_id', ''),
                'software_version': user_software_info.get('software_version', ''),
                'software_code': user_software_info.get('software_id', '')  # 软件代码与软件标识一致
            })
        
        if xinghao_xinxi_list and len(xinghao_xinxi_list) >= 18:
            details.update({
                'software_short_name': xinghao_xinxi_list[7],
                'software_short_name_en': xinghao_xinxi_list[8],
                'software_id': xinghao_xinxi_list[12] if not user_software_info or not user_software_info.get('software_id') else details['software_id'],
                'software_version': xinghao_xinxi_list[10] if not user_software_info or not user_software_info.get('software_version') else details['software_version'],
                'system_name': xinghao_xinxi_list[10],
                'system_short_name': xinghao_xinxi_list[11],
                'component': xinghao_xinxi_list[12],
                'software_code': xinghao_xinxi_list[13],
                'programming_language': xinghao_xinxi_list[14],
                'software_level': xinghao_xinxi_list[17]
            })
        
        if ruanjian_xinxi_duqu_temp:
            # 从文档中提取的信息
            for key, value in ruanjian_xinxi_duqu_temp.items():
                if key == '软件名称' and value:
                    details['software_name'] = value
        
        return details
    
    def _organize_environment_info(
        self, 
        xinghao_xinxi_list: Optional[List[str]], 
        impact_analysis_doc_path: Optional[str]
    ) -> Dict[str, Any]:
        """组织环境信息（回归测试特有）"""
        environment_info = {
            'development_environment': 'AcoreIde',
            'runtime_environment': '飞腾2000（天脉3）',
            'extraction_source': 'default'
        }
        
        # 如果有型号信息库，优先使用
        if xinghao_xinxi_list and len(xinghao_xinxi_list) >= 17:
            environment_info.update({
                'development_environment': xinghao_xinxi_list[15],
                'runtime_environment': xinghao_xinxi_list[16],
                'extraction_source': 'model_database'
            })
        else:
            # 尝试从影响域分析报告中提取
            if impact_analysis_doc_path and os.path.exists(impact_analysis_doc_path):
                try:
                    self.logger.info(f"从影响域分析报告提取环境信息: {impact_analysis_doc_path}")
                    extracted_env = self._extract_environment_from_document(impact_analysis_doc_path)
                    if extracted_env:
                        environment_info.update(extracted_env)
                        environment_info['extraction_source'] = 'document'
                except Exception as e:
                    self.logger.error(f"环境信息提取失败: {e}，使用默认值")
        
        self.logger.info(f"环境信息组织完成: {environment_info}")
        return environment_info
    
    def _extract_environment_from_document(self, doc_path: str) -> Optional[Dict[str, str]]:
        """从文档中提取环境信息"""
        try:
            # 这里可以集成环境信息提取器
            # from ...utils.environment_extraction.regression_environment_extractor import extract_environment_info
            # return extract_environment_info(doc_path)
            return {
                'development_environment': 'AcoreIde',
                'runtime_environment': '飞腾2000（天脉3）'
            }
        except Exception as e:
            self.logger.error(f"文档环境信息提取失败: {e}")
            return None
    
    def _organize_statistics_info(
        self, 
        planning_requirements_count: int, 
        analysis_requirements_count: int, 
        final_code_lines: int
    ) -> Dict[str, Any]:
        """组织统计信息"""
        # 计算测试规模
        ceshiguimo_jisuan = self._calculate_test_scale(final_code_lines)
        
        # 确保需求数量是有效的数字
        planning_count = max(planning_requirements_count, 0) if planning_requirements_count > 0 else 10
        analysis_count = max(analysis_requirements_count, 0) if analysis_requirements_count > 0 else 10
        
        return {
            'planning_requirements_count': planning_count,
            'analysis_requirements_count': analysis_count,
            'test_scale': ceshiguimo_jisuan,
            'effective_test_code_scale': ceshiguimo_jisuan,
            'software_change_scale': 0,
            'review_document_scale': 60,
            'test_document_scale': 0,
            'actual_test_workload': 5,
            'remaining_issues_count': 0,  # 回归测试默认为0
            'test_depth': '全面测试',
            'test_item_count': 0,  # 将在后续计算
            'standard_requirements_count': round(planning_count * 0.2)
        }
    
    def _organize_time_info(self, final_code_lines: int) -> Dict[str, Any]:
        """组织时间信息"""
        from ...forms.formFilter.time_calculator import ceshi_start_end_time
        
        try:
            ceshi_start_time, ceshi_end_time = ceshi_start_end_time(final_code_lines)
            return {
                'planned_start_time': ceshi_start_time,
                'planned_end_time': ceshi_end_time,
                'actual_start_time': ceshi_start_time,
                'actual_end_time': ceshi_end_time
            }
        except Exception as e:
            self.logger.warning(f"时间计算失败，使用默认值: {e}")
            return {
                'planned_start_time': '',
                'planned_end_time': '',
                'actual_start_time': '',
                'actual_end_time': ''
            }
    
    def _get_fixed_values(self, ceshileixing: str) -> Dict[str, Any]:
        """获取固定值配置（回归测试专用）"""
        return {
            'is_closed': '是',
            'is_urgent': '是',
            'development_stage': 'S',
            'verification_status': '所内验证',
            'config_management_status': '出库后更改' if ceshileixing == '回归测试' else '首次入库',
            'purpose': '联试',
            'related_major_issues': '无',
            'is_model_generated': '否',
            'software_type': '应用软件',
            'is_business_trip': '否',
            'remarks': '无',
            'developer_workload': ''  # 回归测试特有字段
        }
    
    def _get_data_sources(
        self, 
        xinghao_xinxi_list: Optional[List[str]], 
        ruanjian_xinxi_duqu_temp: Optional[Dict[str, Any]], 
        user_software_info: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """获取数据来源信息"""
        sources = {}
        
        if user_software_info:
            sources['user_input'] = "用户输入"
        if xinghao_xinxi_list:
            sources['model_database'] = "型号信息库"
        if ruanjian_xinxi_duqu_temp:
            sources['document_extraction'] = "文档提取"
        
        return sources
    
    def _calculate_test_scale(self, final_code_lines: int) -> int:
        """计算测试规模"""
        from ...forms.formFilter.time_calculator import ceshiguimo_fenxi
        
        try:
            return ceshiguimo_fenxi(final_code_lines)
        except Exception as e:
            self.logger.warning(f"测试规模计算失败，使用代码行数: {e}")
            return final_code_lines
    
    def validate_software_config_data(self, software_config_data: Dict[str, Any]) -> bool:
        """
        验证回归测试软件配置项数据的完整性
        
        Args:
            software_config_data: 软件配置数据字典
            
        Returns:
            bool: 验证结果
        """
        try:
            required_keys = ['basic_info', 'code_statistics', 'software_details', 'environment_info', 'statistics_info', 'time_info', 'fixed_values']
            
            for key in required_keys:
                if key not in software_config_data:
                    self.logger.warning(f"缺少必需的数据字段: {key}")
                    return False
            
            # 验证基本信息
            basic_info = software_config_data['basic_info']
            if not basic_info.get('software_name'):
                self.logger.warning("缺少软件名称")
                return False
            
            # 验证代码统计信息
            code_stats = software_config_data['code_statistics']
            if code_stats.get('final_code_lines', 0) <= 0:
                self.logger.warning("代码行数无效")
                return False
            
            self.logger.info("回归测试软件配置项数据验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"验证回归测试软件配置项数据时发生错误: {str(e)}")
            return False
