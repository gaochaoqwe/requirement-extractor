"""
配置项测试问题报告单服务

提供配置项测试问题报告单的完整服务接口，整合数据处理、Excel填充和格式设置功能。
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .data_processor import ConfigurationItemIssueReportDataProcessor
from .excel_filler import ConfigurationItemIssueReportExcelFiller
from .formatter import ConfigurationItemIssueReportFormatter

# 配置日志
logger = logging.getLogger(__name__)

class ConfigurationItemIssueReportService:
    """配置项测试问题报告单服务"""
    
    def __init__(self):
        """初始化配置项测试问题报告单服务"""
        self.logger = logger
        self.data_processor = ConfigurationItemIssueReportDataProcessor()
        self.excel_filler = ConfigurationItemIssueReportExcelFiller()
        self.formatter = ConfigurationItemIssueReportFormatter()
    
    def generate_issue_report_table(
        self,
        excel_file_path: str,
        sheet_name: str,
        ruanjian_xinxi: Dict[str, List[str]],
        ruanjian_name: str,
        diama_biangeng_xuqiu: List[str],
        ceshiren_name: str,
        kaifarenxinxi: List[str],
        ceshileixing: str = "配置项测试",
        issue_count: int = 16,
        apply_formatting: bool = True
    ) -> bool:
        """
        生成配置项测试问题报告单
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            ruanjian_xinxi: 软件信息字典
            ruanjian_name: 软件名称
            diama_biangeng_xuqiu: 代码变更需求列表
            ceshiren_name: 测试人员姓名
            kaifarenxinxi: 开发人员信息列表
            ceshileixing: 测试类型
            issue_count: 问题数量
            apply_formatting: 是否应用格式设置
            
        Returns:
            bool: 生成是否成功
        """
        try:
            self.logger.debug(f"开始生成配置项测试问题报告单: {sheet_name}")
            
            # 第一步：组织数据
            issue_report_data = self.data_processor.organize_issue_report_data(
                ruanjian_xinxi=ruanjian_xinxi,
                ruanjian_name=ruanjian_name,
                diama_biangeng_xuqiu=diama_biangeng_xuqiu,
                ceshiren_name=ceshiren_name,
                kaifarenxinxi=kaifarenxinxi,
                ceshileixing=ceshileixing,
                issue_count=issue_count
            )
            
            # 验证数据
            if not self.data_processor.validate_issue_report_data(issue_report_data):
                self.logger.error("配置项测试问题报告单数据验证失败")
                return False
            
            # 第二步：填充Excel
            if not self.excel_filler.fill_issue_report_sheet(
                excel_file_path=excel_file_path,
                sheet_name=sheet_name,
                issue_report_data=issue_report_data
            ):
                self.logger.error("Excel填充失败")
                return False
            
            # 第三步：应用格式（可选）
            if apply_formatting:
                if not self.formatter.apply_formatting(
                    excel_file_path=excel_file_path,
                    sheet_name=sheet_name,
                    issue_report_data=issue_report_data
                ):
                    self.logger.warning("格式设置失败，但数据填充成功")
            
            # 记录统计信息
            statistics = self.data_processor.get_issue_statistics(issue_report_data)
            self.logger.info(f"问题统计: {statistics}")
            
            # 获取填充结果摘要
            summary = self.excel_filler.get_filled_data_summary(excel_file_path, sheet_name, issue_count)
            self.logger.info(f"填充结果摘要: 共填充 {summary.get('filled_issues', 0)} 个问题")
            
            self.logger.debug("配置项测试问题报告单生成完成")
            return True
            
        except Exception as e:
            self.logger.error(f"生成配置项测试问题报告单时发生错误: {str(e)}")
            return False
    
    def generate_issue_report_table_legacy(
        self,
        excel_file_path: str,
        sheet_name: str,
        ruanjian_xinxi: Dict[str, List[str]],
        ruanjian_name: str,
        diama_biangeng_xuqiu: List[str],
        ceshiren_name: str,
        kaifarenxinxi: List[str],
        ceshileixing: str = "配置项测试"
    ) -> bool:
        """
        生成配置项测试问题报告单（兼容原有接口）
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            ruanjian_xinxi: 软件信息字典
            ruanjian_name: 软件名称
            diama_biangeng_xuqiu: 代码变更需求列表
            ceshiren_name: 测试人员姓名
            kaifarenxinxi: 开发人员信息列表
            ceshileixing: 测试类型
            
        Returns:
            bool: 生成是否成功
        """
        return self.generate_issue_report_table(
            excel_file_path=excel_file_path,
            sheet_name=sheet_name,
            ruanjian_xinxi=ruanjian_xinxi,
            ruanjian_name=ruanjian_name,
            diama_biangeng_xuqiu=diama_biangeng_xuqiu,
            ceshiren_name=ceshiren_name,
            kaifarenxinxi=kaifarenxinxi,
            ceshileixing=ceshileixing,
            issue_count=16,
            apply_formatting=True
        )
    
    def update_issue_field(
        self,
        excel_file_path: str,
        sheet_name: str,
        issue_index: int,
        field_name: str,
        field_value: str,
        apply_formatting: bool = True
    ) -> bool:
        """
        更新配置项测试问题报告单中的单个字段
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            issue_index: 问题索引（从1开始）
            field_name: 字段名称
            field_value: 字段值
            apply_formatting: 是否重新应用格式设置
            
        Returns:
            bool: 更新是否成功
        """
        try:
            self.logger.debug(f"更新配置项测试问题报告单字段: 问题{issue_index}, {field_name} = {field_value}")
            
            # 更新单个字段
            if not self.excel_filler.update_single_issue(
                excel_file_path=excel_file_path,
                sheet_name=sheet_name,
                issue_index=issue_index,
                field_name=field_name,
                field_value=field_value
            ):
                return False
            
            # 重新应用格式（可选）
            if apply_formatting:
                self.formatter.apply_formatting(excel_file_path, sheet_name)
            
            self.logger.info(f"问题{issue_index}的字段{field_name}更新完成")
            return True
            
        except Exception as e:
            self.logger.error(f"更新配置项测试问题报告单字段时发生错误: {str(e)}")
            return False
    
    def get_issue_report_status(
        self,
        excel_file_path: str,
        sheet_name: str,
        issue_count: int = 16
    ) -> Dict[str, Any]:
        """
        获取配置项测试问题报告单的状态
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            issue_count: 问题数量
            
        Returns:
            Dict[str, Any]: 状态信息
        """
        try:
            # 获取填充数据摘要
            summary = self.excel_filler.get_filled_data_summary(excel_file_path, sheet_name, issue_count)
            
            # 统计填充情况
            total_issues = summary.get('total_issues', 0)
            filled_issues = summary.get('filled_issues', 0)
            empty_issues = total_issues - filled_issues
            
            # 分类统计
            issue_details = summary.get('issue_details', [])
            activity_stats = {'文档审查': 0, '代码审查': 0, '静态分析': 0, '动态测试': 0}  # 🔧 新增：静态分析
            type_stats = {'用户需求问题': 0, '软件需求问题': 0, '程序问题': 0}  # 🔧 新增：软件需求问题
            
            for detail in issue_details:
                test_activity = detail.get('test_activity', '')
                issue_type = detail.get('issue_type', '')
                
                if test_activity in activity_stats:
                    activity_stats[test_activity] += 1
                if issue_type in type_stats:
                    type_stats[issue_type] += 1
            
            status = {
                'total_issues': total_issues,
                'filled_issues': filled_issues,
                'empty_issues': empty_issues,
                'completion_rate': round(filled_issues / total_issues * 100, 2) if total_issues > 0 else 0,
                'activity_statistics': activity_stats,
                'type_statistics': type_stats,
                'issue_details': issue_details,
                'table_type': '配置项测试问题报告单'
            }
            
            self.logger.debug(f"配置项测试问题报告单状态: 完成率 {status['completion_rate']}%")
            return status
            
        except Exception as e:
            self.logger.error(f"获取配置项测试问题报告单状态时发生错误: {str(e)}")
            return {}
    
    def validate_issue_report_table(
        self,
        excel_file_path: str,
        sheet_name: str,
        required_fields: Optional[List[str]] = None,
        issue_count: int = 16
    ) -> Dict[str, Any]:
        """
        验证配置项测试问题报告单的完整性
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            required_fields: 必需字段列表
            issue_count: 问题数量
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            # 获取当前数据
            summary = self.excel_filler.get_filled_data_summary(excel_file_path, sheet_name, issue_count)
            
            # 配置项测试问题报告单的默认必需字段
            if required_fields is None:
                required_fields = [
                    'software_name', 'software_version', 'report_number', 
                    'test_activity', 'issue_type'
                ]
            
            # 检查必需字段
            missing_required = []
            issue_details = summary.get('issue_details', [])
            
            for i, detail in enumerate(issue_details):
                issue_missing = []
                for field in required_fields:
                    if field not in detail or not detail[field].strip():
                        issue_missing.append(field)
                
                if issue_missing:
                    missing_required.append({
                        'issue_index': i + 1,
                        'missing_fields': issue_missing
                    })
            
            # 检查配置项测试特有字段
            configuration_item_important = [
                'issue_description', 'evaluation_opinion', 'processing_result'
            ]
            missing_configuration_item = []
            
            for i, detail in enumerate(issue_details):
                issue_missing = []
                for field in configuration_item_important:
                    if field not in detail or not detail[field].strip():
                        issue_missing.append(field)
                
                if issue_missing:
                    missing_configuration_item.append({
                        'issue_index': i + 1,
                        'missing_fields': issue_missing
                    })
            
            validation_result = {
                'is_valid': len(missing_required) == 0,
                'missing_required_issues': missing_required,
                'missing_configuration_item_issues': missing_configuration_item,
                'validation_message': self._get_validation_message(missing_required, missing_configuration_item),
                'table_type': '配置项测试问题报告单'
            }
            
            self.logger.debug(f"配置项测试问题报告单验证结果: {validation_result}")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"验证配置项测试问题报告单时发生错误: {str(e)}")
            return {'is_valid': False, 'error': str(e)}
    
    def _get_validation_message(self, missing_required: List[Dict], missing_configuration_item: List[Dict]) -> str:
        """
        生成验证消息
        
        Args:
            missing_required: 缺失必需字段的问题列表
            missing_configuration_item: 缺失配置项测试字段的问题列表
            
        Returns:
            str: 验证消息
        """
        if not missing_required and not missing_configuration_item:
            return "配置项测试问题报告单验证通过，所有重要字段都已填写"
        
        messages = []
        
        if missing_required:
            count = len(missing_required)
            messages.append(f"有 {count} 个问题缺失必需字段")
        
        if missing_configuration_item:
            count = len(missing_configuration_item)
            messages.append(f"有 {count} 个问题缺失配置项测试重要字段")
        
        return "; ".join(messages)
    
    def highlight_configuration_item_specific_content(
        self,
        excel_file_path: str,
        sheet_name: str,
        issue_count: int = 16
    ) -> bool:
        """
        高亮显示配置项测试特有的内容
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            issue_count: 问题数量
            
        Returns:
            bool: 高亮设置是否成功
        """
        try:
            return self.formatter.highlight_configuration_item_specific_fields(excel_file_path, sheet_name, issue_count)
        except Exception as e:
            self.logger.error(f"高亮配置项测试特有内容时发生错误: {str(e)}")
            return False
    
    def highlight_auto_generated_content(
        self,
        excel_file_path: str,
        sheet_name: str,
        issue_count: int = 16
    ) -> bool:
        """
        高亮显示自动生成的内容
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            issue_count: 问题数量
            
        Returns:
            bool: 高亮设置是否成功
        """
        try:
            return self.formatter.highlight_auto_generated_fields(excel_file_path, sheet_name, issue_count)
        except Exception as e:
            self.logger.error(f"高亮自动生成内容时发生错误: {str(e)}")
            return False
