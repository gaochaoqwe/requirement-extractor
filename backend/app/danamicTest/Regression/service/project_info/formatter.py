"""
回归测试项目基本信息格式设置器

负责设置回归测试项目基本信息表的格式、样式和颜色。
"""

import logging
import openpyxl
from openpyxl.styles import PatternFill, Border, Side, Alignment
from typing import Dict, List, Optional, Any
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class RegressionProjectInfoFormatter:
    """回归测试项目基本信息格式设置器"""
    
    def __init__(self):
        """初始化格式设置器"""
        self.logger = logger
        self.colors = self._get_color_definitions()
        self.borders = self._get_border_definitions()
        self.alignment = self._get_alignment_definitions()
    
    def apply_formatting(
        self,
        excel_file_path: str,
        sheet_name: str,
        project_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        应用回归测试项目基本信息表格式
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            project_data: 项目数据字典（用于动态颜色设置）
            
        Returns:
            bool: 格式设置是否成功
        """
        try:
            self.logger.info(f"开始设置回归测试项目基本信息表格式: {sheet_name}")
            
            # 打开Excel工作簿
            wb = openpyxl.load_workbook(excel_file_path)
            
            # 获取工作表
            if sheet_name not in wb.sheetnames:
                self.logger.error(f"工作表 '{sheet_name}' 不存在")
                return False
            
            sheet = wb[sheet_name]
            
            # 应用各种格式
            self._apply_dynamic_colors(sheet)
            self._apply_borders(sheet)
            self._apply_alignment(sheet)
            self._apply_regression_specific_formatting(sheet)
            
            # 保存文件
            wb.save(excel_file_path)
            
            self.logger.info("回归测试项目基本信息表格式设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"设置回归测试项目基本信息表格式时发生错误: {str(e)}")
            return False
    
    def _apply_dynamic_colors(self, sheet) -> None:
        """
        应用动态颜色设置
        
        Args:
            sheet: openpyxl工作表对象
        """
        # 定义颜色填充
        light_blue_fill = self.colors['light_blue']
        light_green_fill = self.colors['light_green']
        
        # 需要动态设置颜色的字段
        dynamic_fields = [
            (4, 3, '飞机型号'),
            (5, 3, '软件项目代号'),
            (6, 3, '所属领域'),
            (7, 3, '项目总师'),
            (8, 3, '研制部门'),
            (9, 3, '主任设计师'),
            (10, 3, '开发人员'),
            (11, 3, '测试主管')
        ]
        
        for row, col, field_name in dynamic_fields:
            cell_value = sheet.cell(row=row, column=col).value
            has_data = cell_value and str(cell_value).strip()
            
            # 根据是否有数据设置颜色
            if has_data:
                sheet.cell(row=row, column=col).fill = light_blue_fill
                color_desc = "蓝色(已填写)"
            else:
                sheet.cell(row=row, column=col).fill = light_green_fill
                color_desc = "绿色(待填写)"
            
            self.logger.debug(f"{field_name}字段颜色设置: 值='{cell_value}', 颜色={color_desc}")
        
        # 固定值字段设置为蓝色（已填写）
        fixed_fields = [
            (12, 3, '测试级别'),
            (13, 3, '测试类别'),
            (14, 3, '测试环境')
        ]
        
        for row, col, field_name in fixed_fields:
            sheet.cell(row=row, column=col).fill = light_blue_fill
            self.logger.debug(f"{field_name}字段设置为蓝色(固定值)")
    
    def _apply_borders(self, sheet) -> None:
        """
        应用边框设置
        
        Args:
            sheet: openpyxl工作表对象
        """
        thin_border = self.borders['thin']
        
        # 为数据区域添加边框（行3-14，列1-3）
        for row in range(3, 15):
            for col in range(1, 4):
                sheet.cell(row=row, column=col).border = thin_border
        
        self.logger.debug("边框设置完成")
    
    def _apply_alignment(self, sheet) -> None:
        """
        应用对齐设置
        
        Args:
            sheet: openpyxl工作表对象
        """
        center_alignment = self.alignment['center']
        
        # 为数据区域设置对齐方式（行3-14，列1-3）
        for row in range(3, 15):
            for col in range(1, 4):
                sheet.cell(row=row, column=col).alignment = center_alignment
        
        self.logger.debug("对齐设置完成")
    
    def _apply_regression_specific_formatting(self, sheet) -> None:
        """
        应用回归测试特有的格式设置
        
        Args:
            sheet: openpyxl工作表对象
        """
        # 回归测试特有的格式设置
        # 例如：为测试级别字段设置特殊颜色表示这是回归测试
        regression_fill = self.colors.get('light_orange', self.colors['light_blue'])
        
        # 测试级别字段使用特殊颜色
        sheet.cell(row=12, column=3).fill = regression_fill
        
        self.logger.debug("回归测试特有格式设置完成")
    
    def _get_color_definitions(self) -> Dict[str, PatternFill]:
        """
        获取颜色定义
        
        Returns:
            Dict[str, PatternFill]: 颜色填充对象字典
        """
        return {
            'light_yellow': PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid"),
            'light_green': PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid"),
            'light_blue': PatternFill(start_color="99CCFF", end_color="99CCFF", fill_type="solid"),
            'light_orange': PatternFill(start_color="FFD699", end_color="FFD699", fill_type="solid")  # 回归测试专用
        }
    
    def _get_border_definitions(self) -> Dict[str, Border]:
        """
        获取边框定义
        
        Returns:
            Dict[str, Border]: 边框对象字典
        """
        thin_side = Side(style='thin')
        
        return {
            'thin': Border(
                left=thin_side,
                right=thin_side,
                top=thin_side,
                bottom=thin_side
            )
        }
    
    def _get_alignment_definitions(self) -> Dict[str, Alignment]:
        """
        获取对齐定义
        
        Returns:
            Dict[str, Alignment]: 对齐对象字典
        """
        return {
            'center': Alignment(
                horizontal='center',
                vertical='center',
                wrap_text=True
            )
        }
    
    def apply_custom_formatting(
        self,
        excel_file_path: str,
        sheet_name: str,
        custom_rules: Dict[str, Any]
    ) -> bool:
        """
        应用自定义格式规则
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            custom_rules: 自定义格式规则
            
        Returns:
            bool: 格式设置是否成功
        """
        try:
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            # 应用自定义颜色规则
            if 'colors' in custom_rules:
                self._apply_custom_colors(sheet, custom_rules['colors'])
            
            # 应用自定义边框规则
            if 'borders' in custom_rules:
                self._apply_custom_borders(sheet, custom_rules['borders'])
            
            # 应用自定义对齐规则
            if 'alignment' in custom_rules:
                self._apply_custom_alignment(sheet, custom_rules['alignment'])
            
            wb.save(excel_file_path)
            
            self.logger.info("自定义格式设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"应用自定义格式时发生错误: {str(e)}")
            return False
    
    def _apply_custom_colors(self, sheet, color_rules: Dict[str, Any]) -> None:
        """应用自定义颜色规则"""
        # 实现自定义颜色逻辑
        pass
    
    def _apply_custom_borders(self, sheet, border_rules: Dict[str, Any]) -> None:
        """应用自定义边框规则"""
        # 实现自定义边框逻辑
        pass
    
    def _apply_custom_alignment(self, sheet, alignment_rules: Dict[str, Any]) -> None:
        """应用自定义对齐规则"""
        # 实现自定义对齐逻辑
        pass
