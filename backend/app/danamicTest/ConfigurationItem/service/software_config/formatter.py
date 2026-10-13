"""
软件配置项信息格式设置器

负责设置软件配置项信息表的格式、样式和颜色。
"""

import logging
import openpyxl
from openpyxl.styles import PatternFill, Border, Side, Alignment
from typing import Dict, List, Optional, Any
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class SoftwareConfigFormatter:
    """软件配置项信息格式设置器"""
    
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
        software_config_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        应用软件配置项信息表格式
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            software_config_data: 软件配置数据字典（用于动态颜色设置）
            
        Returns:
            bool: 格式设置是否成功
        """
        try:
            self.logger.info(f"开始设置软件配置项信息表格式: {sheet_name}")
            
            # 打开Excel工作簿
            wb = openpyxl.load_workbook(excel_file_path)
            
            # 获取工作表
            if sheet_name not in wb.sheetnames:
                self.logger.error(f"工作表 '{sheet_name}' 不存在")
                return False
            
            sheet = wb[sheet_name]
            
            # 应用各种格式
            self._apply_dynamic_colors(sheet, software_config_data)
            self._apply_borders(sheet)
            self._apply_alignment(sheet)
            
            # 保存文件
            wb.save(excel_file_path)
            
            self.logger.info("软件配置项信息表格式设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"设置软件配置项信息表格式时发生错误: {str(e)}")
            return False
    
    def _apply_dynamic_colors(self, sheet, software_config_data: Optional[Dict[str, Any]]) -> None:
        """
        应用动态颜色设置
        
        Args:
            sheet: openpyxl工作表对象
            software_config_data: 软件配置数据字典
        """
        # 定义颜色填充
        light_blue_fill = self.colors['light_blue']    # 已填写
        light_green_fill = self.colors['light_green']  # 待填写
        light_yellow_fill = self.colors['light_yellow'] # 特殊标记
        
        # 基本软件信息（第2-16行）- 大部分已填写
        filled_rows = [2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16]  # 已填写的行
        pending_rows = [9]  # 待填写的行（被测软件基础版本）
        
        for row in filled_rows:
            sheet.cell(row=row, column=3).fill = light_blue_fill
            
        for row in pending_rows:
            sheet.cell(row=row, column=3).fill = light_green_fill
        
        # 记录特殊字段的颜色设置
        if software_config_data:
            basic_info = software_config_data.get('basic_info', {})
            statistics_info = software_config_data.get('statistics_info', {})
            
            # 记录软件规模字段
            code_lines = basic_info.get('code_lines', 0)
            self.logger.info(f"软件规模字段颜色设置: 第12行第3列设置为蓝色（已填写），值={code_lines}")
            
            # 记录测试代码规模字段
            test_scale = statistics_info.get('test_scale', 0)
            self.logger.info(f"测试代码规模字段颜色设置: 第21行第3列设置为蓝色（已填写），值={test_scale}")
        
        # 责任人和项目状态（第17-19行）
        responsibility_rows = [17, 18]  # 修改为已填写（蓝色）
        for row in responsibility_rows:
            sheet.cell(row=row, column=3).fill = light_blue_fill  # 改为蓝色
            
        # 第19行单独处理
        sheet.cell(row=19, column=3).fill = light_green_fill  # 是否紧急保持绿色（待填写）
        
        # 规模和统计信息（第19-31行）
        self._apply_statistics_colors(sheet, light_blue_fill, light_green_fill)
        
        # 项目管理信息（第32-48行）
        self._apply_management_colors(sheet, light_blue_fill, light_green_fill)
        
        self.logger.info("软件配置项信息表颜色设置完成，所有已填写字段应为蓝色")
    
    def _apply_statistics_colors(self, sheet, light_blue_fill, light_green_fill) -> None:
        """应用统计信息颜色"""
        # 第19-31行的颜色设置
        for row in range(19, 32):
            if row in [19, 20, 21, 22, 23]:  # 规模相关（已填写）
                sheet.cell(row=row, column=3).fill = light_blue_fill
            elif row in [24, 25, 26, 27, 28, 29]:  # 时间和工作量相关（已填写）
                sheet.cell(row=row, column=3).fill = light_blue_fill
            elif row in [30, 31]:  # 测试深度和项数（已填写）
                sheet.cell(row=row, column=3).fill = light_blue_fill
            else:
                sheet.cell(row=row, column=3).fill = light_green_fill
    
    def _apply_management_colors(self, sheet, light_blue_fill, light_green_fill) -> None:
        """应用项目管理信息颜色"""
        # 第32-48行的颜色设置
        for row in range(32, 49):
            if row in [32, 33, 34, 35, 36, 37, 38]:  # 项目管理状态（已填写）
                sheet.cell(row=row, column=3).fill = light_blue_fill
            elif row in [39, 40, 41]:  # 需求统计（已填写）
                sheet.cell(row=row, column=3).fill = light_blue_fill
            elif row == 42:  # 是否合作项目（已填写）
                sheet.cell(row=row, column=3).fill = light_blue_fill
            elif row in [43, 44]:  # 项目成员信息（根据情况填写）
                sheet.cell(row=row, column=3).fill = light_blue_fill
            elif row in [45, 47]:  # 软件类型、是否出差项目（已填写）
                sheet.cell(row=row, column=3).fill = light_blue_fill
            elif row == 48:  # 标准需求数（已填写）
                sheet.cell(row=row, column=3).fill = light_blue_fill
            elif row == 46:  # 软件类别（待填写）
                sheet.cell(row=row, column=3).fill = light_green_fill
            else:
                sheet.cell(row=row, column=3).fill = light_green_fill
    
    def _apply_borders(self, sheet) -> None:
        """
        应用边框设置
        
        Args:
            sheet: openpyxl工作表对象
        """
        thin_border = self.borders['thin']
        
        # 为数据区域添加边框（行1-48，列1-3）
        for row in range(1, 49):
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
        
        # 为数据区域设置对齐方式（行1-48，列1-3）
        for row in range(1, 49):
            for col in range(1, 4):
                sheet.cell(row=row, column=col).alignment = center_alignment
        
        self.logger.debug("对齐设置完成")
    
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
            'light_orange': PatternFill(start_color="FFD699", end_color="FFD699", fill_type="solid")
        }
    
    def _get_border_definitions(self) -> Dict[str, Border]:
        """
        获取边框定义
        
        Returns:
            Dict[str, Border]: 边框对象字典
        """
        thin_side = Side(style='thin', color='000000')
        
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
        for field, color_info in color_rules.items():
            if 'row' in color_info and 'column' in color_info and 'color' in color_info:
                row = color_info['row']
                col = color_info['column']
                color = color_info['color']
                
                if color in self.colors:
                    sheet.cell(row=row, column=col).fill = self.colors[color]
    
    def _apply_custom_borders(self, sheet, border_rules: Dict[str, Any]) -> None:
        """应用自定义边框规则"""
        # 实现自定义边框逻辑
        pass
    
    def _apply_custom_alignment(self, sheet, alignment_rules: Dict[str, Any]) -> None:
        """应用自定义对齐规则"""
        # 实现自定义对齐逻辑
        pass
    
    def highlight_ai_generated_fields(self, excel_file_path: str, sheet_name: str) -> bool:
        """
        高亮显示AI生成的字段
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            bool: 高亮设置是否成功
        """
        try:
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            # AI生成的字段使用特殊颜色
            ai_generated_fill = self.colors['light_orange']
            
            # AI生成的字段：软件简称、软件简称（英文）、系统名称、系统简称、组件
            ai_fields = [3, 4, 6, 7, 8]  # 对应的行号
            
            for row in ai_fields:
                sheet.cell(row=row, column=3).fill = ai_generated_fill
            
            wb.save(excel_file_path)
            
            self.logger.info("AI生成字段高亮显示完成")
            return True
            
        except Exception as e:
            self.logger.error(f"高亮AI生成字段时发生错误: {str(e)}")
            return False
