"""
回归测试软件配置项信息服务

提供回归测试软件配置项信息表的完整服务接口，整合数据处理、Excel填充和格式设置功能。
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .data_processor import RegressionSoftwareConfigDataProcessor
from .excel_filler import RegressionSoftwareConfigExcelFiller
from .formatter import RegressionSoftwareConfigFormatter

# 配置日志
logger = logging.getLogger(__name__)

class RegressionSoftwareConfigService:
    """回归测试软件配置项信息服务"""
    
    def __init__(self):
        """初始化回归测试软件配置项信息服务"""
        self.logger = logger
        self.data_processor = RegressionSoftwareConfigDataProcessor()
        self.excel_filler = RegressionSoftwareConfigExcelFiller()
        self.formatter = RegressionSoftwareConfigFormatter()
    
    def generate_software_config_table(
        self,
        excel_file_path: str,
        sheet_name: str,
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
        impact_analysis_doc_path: Optional[str] = None,
        apply_formatting: bool = True
    ) -> bool:
        """
        生成回归测试软件配置项信息表
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
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
            apply_formatting: 是否应用格式设置
            
        Returns:
            bool: 生成是否成功
        """
        try:
            self.logger.info(f"开始生成回归测试软件配置项信息表: {sheet_name}")
            
            # 第一步：组织数据
            software_config_data = self.data_processor.organize_software_config_data(
                ruanjian_name=ruanjian_name,
                ceshiren_name=ceshiren_name,
                zhuguan_name=zhuguan_name,
                daima_chayi_hangshu=daima_chayi_hangshu,
                xinghao_xinxi_list=xinghao_xinxi_list,
                ruanjian_xinxi_duqu_temp=ruanjian_xinxi_duqu_temp,
                ceshileixing=ceshileixing,
                user_software_info=user_software_info,
                planning_requirements_count=planning_requirements_count,
                analysis_requirements_count=analysis_requirements_count,
                code_path=code_path,
                requirement_doc_path=requirement_doc_path,  # 添加需求文档路径参数
                impact_analysis_doc_path=impact_analysis_doc_path
            )
            
            # 验证数据
            if not self.data_processor.validate_software_config_data(software_config_data):
                self.logger.error("回归测试软件配置项数据验证失败")
                return False
            
            # 第二步：填充Excel
            # 设置需求文档路径（如果提供）
            if requirement_doc_path:
                self.excel_filler.set_requirement_doc_path(requirement_doc_path)
                self.logger.info(f"设置需求文档路径用于环境信息提取: {requirement_doc_path}")
            
            # 设置AI分析函数（如果可用）
            try:
                from ..test_case_generation.test_analysis import moxingfenxi
                
                # 创建一个适合环境信息提取的AI分析包装函数
                def environment_ai_analysis(prompt: str) -> str:
                    """环境信息AI分析包装函数"""
                    try:
                        log_debug(f"AI环境分析开始，提示词长度: {len(prompt)}", "software_config_service")
                        result = moxingfenxi(
                            str_temp=prompt,  # 修正参数名
                            ceshi_leixing="环境信息提取",  # 修正参数名
                            jianceyi_flag=0  # 修正参数名
                        )
                        
                        log_debug(f"AI环境分析结果类型: {type(result)}", "software_config_service")
                        log_debug(f"AI环境分析原始返回内容: {result}", "software_config_service")  # 添加原始内容日志
                        
                        if result and isinstance(result, dict):
                            # 尝试从结果中提取环境信息
                            description = result.get('test_description', '')
                            method = result.get('test_method', '')
                            combined_result = f"{description}\n{method}"
                            return combined_result
                        else:
                            return str(result) if result else ""
                            
                    except Exception as e:
                        logger.error(f"AI环境分析时发生错误: {str(e)}")
                        return ""
                
                self.excel_filler.set_ai_analysis_function(environment_ai_analysis)
                self.logger.info("设置AI分析函数用于环境信息提取")
            except ImportError as e:
                self.logger.info(f"AI分析函数不可用，将使用基于规则的匹配: {e}")
            
            if not self.excel_filler.fill_software_config_sheet(
                excel_file_path=excel_file_path,
                sheet_name=sheet_name,
                software_config_data=software_config_data
            ):
                self.logger.error("Excel填充失败")
                return False
            
            # 第三步：应用格式（可选）
            if apply_formatting:
                if not self.formatter.apply_formatting(
                    excel_file_path=excel_file_path,
                    sheet_name=sheet_name,
                    software_config_data=software_config_data
                ):
                    self.logger.warning("格式设置失败，但数据填充成功")
            
            # 记录数据来源信息
            data_sources = software_config_data.get('data_sources', {})
            code_statistics = software_config_data.get('code_statistics', {})
            self.logger.info(f"数据来源: {data_sources}")
            self.logger.info(f"代码统计: 原始行数={code_statistics.get('original_code_lines', 0)}, 最终行数={code_statistics.get('final_code_lines', 0)}")
            
            # 获取填充结果摘要
            summary = self.excel_filler.get_filled_data_summary(excel_file_path, sheet_name)
            self.logger.info(f"填充结果摘要: 共填充 {len([v for v in summary.values() if v.strip()])} 个字段")
            
            self.logger.info("回归测试软件配置项信息表生成完成")
            return True
            
        except Exception as e:
            self.logger.error(f"生成回归测试软件配置项信息表时发生错误: {str(e)}")
            return False
    
    def generate_software_config_table_legacy(
        self,
        excel_file_path: str,
        sheet_name: str,
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
        impact_analysis_doc_path: Optional[str] = None
    ) -> bool:
        """
        生成回归测试软件配置项信息表（兼容原有接口）
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
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
            impact_analysis_doc_path: 影响域分析报告路径
            
        Returns:
            bool: 生成是否成功
        """
        return self.generate_software_config_table(
            excel_file_path=excel_file_path,
            sheet_name=sheet_name,
            ruanjian_name=ruanjian_name,
            ceshiren_name=ceshiren_name,
            zhuguan_name=zhuguan_name,
            daima_chayi_hangshu=daima_chayi_hangshu,
            xinghao_xinxi_list=xinghao_xinxi_list,
            ruanjian_xinxi_duqu_temp=ruanjian_xinxi_duqu_temp,
            ceshileixing=ceshileixing,
            user_software_info=user_software_info,
            planning_requirements_count=planning_requirements_count,
            analysis_requirements_count=analysis_requirements_count,
            code_path=code_path,
            impact_analysis_doc_path=impact_analysis_doc_path,
            apply_formatting=True
        )
    
    def update_software_config_field(
        self,
        excel_file_path: str,
        sheet_name: str,
        field_name: str,
        field_value: str,
        apply_formatting: bool = True
    ) -> bool:
        """
        更新回归测试软件配置项信息表中的单个字段
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            field_name: 字段名称
            field_value: 字段值
            apply_formatting: 是否应用格式设置
            
        Returns:
            bool: 更新是否成功
        """
        try:
            self.logger.info(f"更新回归测试软件配置项信息字段: {field_name} = {field_value}")
            
            # 获取字段映射
            cell_mapping = self.excel_filler._get_cell_mapping()
            
            if field_name not in cell_mapping:
                self.logger.error(f"未知的字段名称: {field_name}")
                return False
            
            # 更新单个字段
            import openpyxl
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            row, col = cell_mapping[field_name]
            sheet.cell(row=row, column=col, value=field_value)
            
            wb.save(excel_file_path)
            
            # 重新应用格式（可选）
            if apply_formatting:
                self.formatter.apply_formatting(excel_file_path, sheet_name)
            
            self.logger.info(f"字段 {field_name} 更新完成")
            return True
            
        except Exception as e:
            self.logger.error(f"更新回归测试软件配置项信息字段时发生错误: {str(e)}")
            return False
    
    def get_software_config_status(
        self,
        excel_file_path: str,
        sheet_name: str
    ) -> Dict[str, Any]:
        """
        获取回归测试软件配置项信息表的状态
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            Dict[str, Any]: 状态信息
        """
        try:
            # 获取填充数据摘要
            summary = self.excel_filler.get_filled_data_summary(excel_file_path, sheet_name)
            
            # 统计填充情况
            total_fields = len(summary)
            filled_fields = sum(1 for value in summary.values() if value.strip())
            empty_fields = total_fields - filled_fields
            
            # 分类统计
            basic_fields = ['software_name', 'software_short_name', 'software_id', 'software_version']
            filled_basic = sum(1 for field in basic_fields if summary.get(field, '').strip())
            
            # 回归测试特有字段统计
            regression_fields = ['base_version', 'developer_workload']
            filled_regression = sum(1 for field in regression_fields if summary.get(field, '').strip())
            
            status = {
                'total_fields': total_fields,
                'filled_fields': filled_fields,
                'empty_fields': empty_fields,
                'completion_rate': round(filled_fields / total_fields * 100, 2) if total_fields > 0 else 0,
                'basic_info_completion': round(filled_basic / len(basic_fields) * 100, 2),
                'regression_fields_completion': round(filled_regression / len(regression_fields) * 100, 2),
                'field_details': summary,
                'table_type': '回归测试软件配置项信息'
            }
            
            self.logger.info(f"回归测试软件配置项信息表状态: 完成率 {status['completion_rate']}%")
            return status
            
        except Exception as e:
            self.logger.error(f"获取回归测试软件配置项信息表状态时发生错误: {str(e)}")
            return {}
    
    def validate_software_config_table(
        self,
        excel_file_path: str,
        sheet_name: str,
        required_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        验证回归测试软件配置项信息表的完整性
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            required_fields: 必需字段列表
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            # 获取当前数据
            summary = self.excel_filler.get_filled_data_summary(excel_file_path, sheet_name)
            
            # 回归测试的默认必需字段
            if required_fields is None:
                required_fields = [
                    'software_name', 'software_id', 'software_version', 
                    'responsible_person', 'programming_language'
                ]
            
            # 检查必需字段
            missing_required = []
            for field in required_fields:
                if field not in summary or not summary[field].strip():
                    missing_required.append(field)
            
            # 检查回归测试重要字段
            regression_important = [
                'base_version', 'developer_workload', 'config_management_status'
            ]
            missing_regression = []
            for field in regression_important:
                if field not in summary or not summary[field].strip():
                    missing_regression.append(field)
            
            validation_result = {
                'is_valid': len(missing_required) == 0,
                'missing_required_fields': missing_required,
                'missing_regression_fields': missing_regression,
                'validation_message': self._get_validation_message(missing_required, missing_regression),
                'table_type': '回归测试软件配置项信息'
            }
            
            self.logger.info(f"回归测试软件配置项信息表验证结果: {validation_result}")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"验证回归测试软件配置项信息表时发生错误: {str(e)}")
            return {'is_valid': False, 'error': str(e)}
    
    def _get_validation_message(self, missing_required: List[str], missing_regression: List[str]) -> str:
        """
        生成验证消息
        
        Args:
            missing_required: 缺失的必需字段
            missing_regression: 缺失的回归测试字段
            
        Returns:
            str: 验证消息
        """
        if not missing_required and not missing_regression:
            return "回归测试软件配置项信息表验证通过，所有重要字段都已填写"
        
        messages = []
        
        if missing_required:
            messages.append(f"缺失必需字段: {', '.join(missing_required)}")
        
        if missing_regression:
            messages.append(f"缺失回归测试重要字段: {', '.join(missing_regression)}")
        
        return "; ".join(messages)
    
    def highlight_regression_specific_content(
        self,
        excel_file_path: str,
        sheet_name: str
    ) -> bool:
        """
        高亮显示回归测试特有的内容
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            bool: 高亮设置是否成功
        """
        try:
            return self.formatter.highlight_regression_specific_fields(excel_file_path, sheet_name)
        except Exception as e:
            self.logger.error(f"高亮回归测试特有内容时发生错误: {str(e)}")
            return False
    
    def highlight_ai_generated_content(
        self,
        excel_file_path: str,
        sheet_name: str
    ) -> bool:
        """
        高亮显示AI生成的内容
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            bool: 高亮设置是否成功
        """
        try:
            return self.formatter.highlight_ai_generated_fields(excel_file_path, sheet_name)
        except Exception as e:
            self.logger.error(f"高亮AI生成内容时发生错误: {str(e)}")
            return False
