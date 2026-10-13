"""
回归测试软件配置项信息格式设置器

负责设置回归测试软件配置项信息表的格式、样式和颜色。
"""

import logging
import openpyxl
from openpyxl.styles import PatternFill, Border, Side, Alignment
from typing import Dict, List, Optional, Any
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class RegressionSoftwareConfigFormatter:
    """回归测试软件配置项信息格式设置器"""
    
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
        应用回归测试软件配置项信息表格式
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            software_config_data: 软件配置数据字典（用于动态颜色设置）
            
        Returns:
            bool: 格式设置是否成功
        """
        try:
            self.logger.info(f"开始设置回归测试软件配置项信息表格式: {sheet_name}")
            
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
            
            self.logger.info("回归测试软件配置项信息表格式设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"设置回归测试软件配置项信息表格式时发生错误: {str(e)}")
            return False
    
    def _apply_dynamic_colors(self, sheet, software_config_data: Optional[Dict[str, Any]]) -> None:
        """
        应用动态颜色设置（回归测试专用）
        
        Args:
            sheet: openpyxl工作表对象
            software_config_data: 软件配置数据字典
        """
        # 定义颜色填充
        light_blue_fill = self.colors['light_blue']    # 已填写
        light_green_fill = self.colors['light_green']  # 待填写
        light_orange_fill = self.colors['light_orange'] # 回归测试特有标记
        
        # 基本软件信息（第2-16行）- 回归测试中大部分已填写
        self.logger.info("开始设置软件配置项信息表颜色（第2-16行）")
        
        # 已填写的基本信息字段
        filled_basic_rows = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
        for row in filled_basic_rows:
            sheet.cell(row=row, column=3).fill = light_blue_fill
            self.logger.debug(f"第{row}行设置为蓝色（已填写）")
        
        # 记录特殊字段的颜色设置
        if software_config_data:
            code_statistics = software_config_data.get('code_statistics', {})
            final_code_lines = code_statistics.get('final_code_lines', 0)
            self.logger.info(f"软件规模字段颜色设置: 第12行第3列设置为蓝色（已填写），值={final_code_lines}")
        
        # 项目管理信息（第17-31行）
        self._apply_management_colors(sheet, light_blue_fill, light_green_fill)
        
        # 项目详细信息（第32-49行）
        self._apply_detail_colors(sheet, light_blue_fill, light_green_fill, light_orange_fill)
        
        self.logger.info("回归测试软件配置项信息表颜色设置完成")
    
    def _apply_management_colors(self, sheet, light_blue_fill, light_green_fill) -> None:
        """应用项目管理信息颜色（第17-31行）"""
        self.logger.info("开始设置软件配置项信息表颜色（第17-31行）")
        
        for row in range(17, 32):
            if row in [17, 18]:  # 责任人、是否闭项（已填写）
                sheet.cell(row=row, column=3).fill = light_blue_fill
                self.logger.debug(f"第{row}行设置为蓝色（已填写）")
            elif row in [19, 20, 21, 22, 23]:  # 是否紧急、软件更改规模、测试代码规模、审查文档规模、编写测试文档规模（已填写）
                sheet.cell(row=row, column=3).fill = light_blue_fill
                self.logger.debug(f"第{row}行设置为蓝色（已填写）")
            elif row in [24, 25, 26, 27, 28, 29]:  # 测试时间相关（已填写）
                sheet.cell(row=row, column=3).fill = light_blue_fill
                self.logger.debug(f"第{row}行设置为蓝色（已填写）")
            elif row in [30, 31]:  # 测试深度、测试项数量（已填写）
                sheet.cell(row=row, column=3).fill = light_blue_fill
                self.logger.debug(f"第{row}行设置为蓝色（已填写）")
            else:
                sheet.cell(row=row, column=3).fill = light_green_fill
                self.logger.debug(f"第{row}行设置为绿色（待填写）")
    
    def _apply_detail_colors(self, sheet, light_blue_fill, light_green_fill, light_orange_fill) -> None:
        """应用项目详细信息颜色（第32-49行）"""
        self.logger.info("开始设置软件配置项信息表颜色（第32-49行）")
        
        for row in range(32, 50):
            if row in [32, 33, 34, 35, 36, 37, 38]:  # 备注、研制阶段、验证情况、配置管理状态、用途、关联重大事项、是否模型生成项目（已填写）
                sheet.cell(row=row, column=3).fill = light_blue_fill
                self.logger.debug(f"第{row}行设置为蓝色（已填写）")
            elif row in [39, 40, 41]:  # 有效测试代码规模、需求捕获总数、需求测试总数（已填写）
                sheet.cell(row=row, column=3).fill = light_blue_fill
                self.logger.debug(f"第{row}行设置为蓝色（已填写）")
            elif row in [42, 43, 44]:  # 是否合作项目、项目成员测试规模、项目成员投入工时（已填写）
                sheet.cell(row=row, column=3).fill = light_blue_fill
                self.logger.debug(f"第{row}行设置为蓝色（已填写）")
            elif row in [45, 46, 47, 48, 49]:  # 软件类型、开发人员工作量、标准需求数、是否出差项目（已填写）
                # 第46行（开发人员工作量）是回归测试特有字段，使用橙色标记
                if row == 46:
                    sheet.cell(row=row, column=3).fill = light_orange_fill
                    self.logger.debug(f"第{row}行设置为橙色（回归测试特有字段）")
                else:
                    sheet.cell(row=row, column=3).fill = light_blue_fill
                    self.logger.debug(f"第{row}行设置为蓝色（已填写）")
            else:
                sheet.cell(row=row, column=3).fill = light_green_fill
                self.logger.debug(f"第{row}行设置为绿色（待填写）")
    
    def _apply_borders(self, sheet) -> None:
        """
        应用边框设置
        
        Args:
            sheet: openpyxl工作表对象
        """
        thin_border = self.borders['thin']
        
        # 为数据区域添加边框（行1-49，列1-3）
        for row in range(1, 50):
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
        
        # 为数据区域设置对齐方式（行1-49，列1-3）
        for row in range(1, 50):
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
            'light_orange': PatternFill(start_color="FFD699", end_color="FFD699", fill_type="solid")  # 回归测试特有
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
    
    def highlight_regression_specific_fields(self, excel_file_path: str, sheet_name: str) -> bool:
        """
        高亮显示回归测试特有的字段
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            bool: 高亮设置是否成功
        """
        try:
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            # 回归测试特有字段使用特殊颜色
            regression_specific_fill = self.colors['light_orange']
            
            # 回归测试特有字段：被测软件基础版本、开发人员工作量
            regression_fields = [9, 46]  # 对应的行号
            
            for row in regression_fields:
                sheet.cell(row=row, column=3).fill = regression_specific_fill
            
            wb.save(excel_file_path)
            
            self.logger.info("回归测试特有字段高亮显示完成")
            return True
            
        except Exception as e:
            self.logger.error(f"高亮回归测试特有字段时发生错误: {str(e)}")
            return False
    
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
            ai_generated_fill = self.colors['light_yellow']
            
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
