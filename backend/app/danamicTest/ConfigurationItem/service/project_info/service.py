"""
项目基本信息服务

提供项目基本信息表的完整服务接口，整合数据处理、Excel填充和格式设置功能。
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .data_processor import ProjectInfoDataProcessor
from .excel_filler import ProjectInfoExcelFiller
from .formatter import ProjectInfoFormatter

# 配置日志
logger = logging.getLogger(__name__)

class ProjectInfoService:
    """项目基本信息服务"""
    
    def __init__(self):
        """初始化项目基本信息服务"""
        self.logger = logger
        self.data_processor = ProjectInfoDataProcessor()
        self.excel_filler = ProjectInfoExcelFiller()
        self.formatter = ProjectInfoFormatter()
    
    def generate_project_info_table(
        self,
        excel_file_path: str,
        sheet_name: str,
        basic_info: Dict[str, Any],
        zhuguan_name: str,
        kaifarenxinxi: List[str],
        xinghao_xinxi_list: Optional[List[str]] = None,
        suoshulingyu: str = "通用领域",
        apply_formatting: bool = True
    ) -> bool:
        """
        生成项目基本信息表
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            basic_info: 基本信息字典
            zhuguan_name: 测试主管姓名
            kaifarenxinxi: 开发人员信息列表 [姓名, 研制部门]
            xinghao_xinxi_list: 型号信息列表（备用数据源）
            suoshulingyu: 所属领域
            apply_formatting: 是否应用格式设置
            
        Returns:
            bool: 生成是否成功
        """
        try:
            self.logger.info(f"开始生成项目基本信息表: {sheet_name}")
            
            # 第一步：组织数据
            project_data = self.data_processor.organize_project_data(
                basic_info=basic_info,
                zhuguan_name=zhuguan_name,
                kaifarenxinxi=kaifarenxinxi,
                xinghao_xinxi_list=xinghao_xinxi_list,
                suoshulingyu=suoshulingyu
            )
            
            # 验证数据
            if not self.data_processor.validate_project_data(project_data):
                self.logger.error("项目数据验证失败")
                return False
            
            # 第二步：填充Excel
            if not self.excel_filler.fill_project_info_sheet(
                excel_file_path=excel_file_path,
                sheet_name=sheet_name,
                project_data=project_data
            ):
                self.logger.error("Excel填充失败")
                return False
            
            # 第三步：应用格式（可选）
            if apply_formatting:
                if not self.formatter.apply_formatting(
                    excel_file_path=excel_file_path,
                    sheet_name=sheet_name,
                    project_data=project_data
                ):
                    self.logger.warning("格式设置失败，但数据填充成功")
            
            # 记录数据优先级信息
            priority_info = self.data_processor.get_data_priority_info(project_data)
            self.logger.info(f"数据来源优先级: {priority_info}")
            
            # 获取填充结果摘要
            summary = self.excel_filler.get_filled_data_summary(excel_file_path, sheet_name)
            self.logger.info(f"填充结果摘要: {summary}")
            
            self.logger.info("项目基本信息表生成完成")
            return True
            
        except Exception as e:
            self.logger.error(f"生成项目基本信息表时发生错误: {str(e)}")
            return False
    
    def update_project_info_field(
        self,
        excel_file_path: str,
        sheet_name: str,
        field_name: str,
        field_value: str,
        apply_formatting: bool = True
    ) -> bool:
        """
        更新项目基本信息表中的单个字段
        
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
            self.logger.info(f"更新项目基本信息字段: {field_name} = {field_value}")
            
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
            self.logger.error(f"更新项目基本信息字段时发生错误: {str(e)}")
            return False
    
    def get_project_info_status(
        self,
        excel_file_path: str,
        sheet_name: str
    ) -> Dict[str, Any]:
        """
        获取项目基本信息表的状态
        
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
            
            status = {
                'total_fields': total_fields,
                'filled_fields': filled_fields,
                'empty_fields': empty_fields,
                'completion_rate': round(filled_fields / total_fields * 100, 2) if total_fields > 0 else 0,
                'field_details': summary
            }
            
            self.logger.info(f"项目基本信息表状态: 完成率 {status['completion_rate']}%")
            return status
            
        except Exception as e:
            self.logger.error(f"获取项目基本信息表状态时发生错误: {str(e)}")
            return {}
    
    def validate_project_info_table(
        self,
        excel_file_path: str,
        sheet_name: str,
        required_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        验证项目基本信息表的完整性
        
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
            
            # 默认必需字段
            if required_fields is None:
                required_fields = ['test_manager', 'developer', 'test_level']
            
            # 检查必需字段
            missing_required = []
            for field in required_fields:
                if field not in summary or not summary[field].strip():
                    missing_required.append(field)
            
            # 检查可选字段
            optional_fields = ['aircraft_model', 'software_id', 'project_director', 'chief_designer']
            missing_optional = []
            for field in optional_fields:
                if field not in summary or not summary[field].strip():
                    missing_optional.append(field)
            
            validation_result = {
                'is_valid': len(missing_required) == 0,
                'missing_required_fields': missing_required,
                'missing_optional_fields': missing_optional,
                'validation_message': self._get_validation_message(missing_required, missing_optional)
            }
            
            self.logger.info(f"项目基本信息表验证结果: {validation_result}")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"验证项目基本信息表时发生错误: {str(e)}")
            return {'is_valid': False, 'error': str(e)}
    
    def _get_validation_message(self, missing_required: List[str], missing_optional: List[str]) -> str:
        """
        生成验证消息
        
        Args:
            missing_required: 缺失的必需字段
            missing_optional: 缺失的可选字段
            
        Returns:
            str: 验证消息
        """
        if not missing_required and not missing_optional:
            return "项目基本信息表验证通过，所有字段都已填写"
        
        messages = []
        
        if missing_required:
            messages.append(f"缺失必需字段: {', '.join(missing_required)}")
        
        if missing_optional:
            messages.append(f"缺失可选字段: {', '.join(missing_optional)}")
        
        return "; ".join(messages)
