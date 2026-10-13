"""
配置项测试问题报告单格式设置器

负责设置配置项测试问题报告单的格式、颜色和样式。
"""

import logging
import openpyxl
from openpyxl.styles import PatternFill, Border, Side, Alignment
from typing import Dict, List, Optional, Any
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class ConfigurationItemIssueReportFormatter:
    """配置项测试问题报告单格式设置器"""
    
    def __init__(self):
        """初始化格式设置器"""
        self.logger = logger
        self.color_fills = self._get_color_fills()
        self.border_style = self._get_border_style()
    
    def apply_formatting(
        self,
        excel_file_path: str,
        sheet_name: str,
        issue_report_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        应用配置项测试问题报告单格式设置
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            issue_report_data: 问题报告数据（可选，用于动态格式设置）
            
        Returns:
            bool: 格式设置是否成功
        """
        try:
            self.logger.debug(f"开始应用配置项测试问题报告单格式: {sheet_name}")
            
            # 打开Excel工作簿
            wb = openpyxl.load_workbook(excel_file_path)
            
            # 获取工作表
            if sheet_name not in wb.sheetnames:
                self.logger.error(f"工作表 '{sheet_name}' 不存在")
                return False
            
            sheet = wb[sheet_name]
            
            # 获取问题数量
            issue_count = issue_report_data.get('issue_count', 16) if issue_report_data else 16
            
            # 应用颜色填充
            self._apply_color_fills(sheet, issue_count)
            
            # 应用边框样式
            self._apply_borders(sheet, issue_count)
            
            # 应用对齐方式
            self._apply_alignment(sheet, issue_count)
            
            # 保存文件
            wb.save(excel_file_path)
            
            self.logger.debug("配置项测试问题报告单格式设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"应用配置项测试问题报告单格式时发生错误: {str(e)}")
            return False
    
    def _apply_color_fills(self, sheet, issue_count: int) -> None:
        """应用颜色填充"""
        start_row = 2  # 数据从第2行开始
        
        for i in range(issue_count):
            current_row = start_row + i
            
            # 根据单元格填充状态设置颜色
            self._set_row_colors_selective(sheet, current_row, i + 1)
            
        self.logger.debug(f"颜色填充完成，共处理{issue_count}行")
    
    def _set_row_colors_selective(self, sheet, row: int, item_index: int) -> None:
        """设置选择性行颜色（只对有内容的列设置颜色）"""
        light_yellow_fill = self.color_fills['light_yellow']
        light_green_fill = self.color_fills['light_green']
        light_blue_fill = self.color_fills['light_blue']
        
        # 🔧 修复：只对实际填充内容的列设置颜色，没有内容的列保持原有颜色
        # 根据excel_filler.py中的填充逻辑，以下列都是程序填写的：
        program_filled_columns = [
            1,   # 问题序号
            2,   # 软件名称  
            3,   # 软件版本
            4,   # 测试轮次
            5,   # 问题编号
            6,   # 是否历史问题
            7,   # 关联版本
            8,   # 关联问题编号
            9,   # 测试活动
            10,  # 问题类型
            11,  # 问题等级
            12,  # 问题数目
            13,  # 问题名称
            14,  # 问题来源
            15,  # 问题描述
            16,  # 测评意见
            17,  # 修复优先级
            18,  # 测试人员
            19,  # 测试时间
            20,  # 研制单位意见
            21,  # 问题修复时间
            22,  # 研发人员
            23,  # 签名时间
            24,  # 总师意见
            25,  # 完成年月
            26,  # 处理结果
            27,  # 确认意见
            28,  # 确认人
            29,  # 确认时间
            30,  # 验证版本
            31,  # 是否典型问题
            32   # 是否低级错误
        ]
        
        # 🔧 增强：确保未填充的列保持原始模板颜色（绿色）
        max_columns = 32  # 问题报告单总列数
        
        # 首先，对所有列检查并处理
        for col in range(1, max_columns + 1):
            cell = sheet.cell(row=row, column=col)
            
            # 如果是程序填写的列，并且有内容，设置为蓝色
            if col in program_filled_columns and cell.value is not None and str(cell.value).strip():
                cell.fill = light_blue_fill
                self.logger.debug(f"设置第{row}行第{col}列为蓝色（有内容）: '{cell.value}'")
            # 如果没有内容，确保保持绿色（模板原色）
            elif cell.value is None or not str(cell.value).strip():
                # 如果单元格当前没有背景色或是白色，设置为绿色（模板颜色）
                if cell.fill.start_color.rgb is None or cell.fill.start_color.rgb == '00000000' or cell.fill.start_color.rgb == 'FFFFFFFF':
                    cell.fill = light_green_fill
                    self.logger.debug(f"恢复第{row}行第{col}列为绿色（空单元格）")
                # 如果已经有颜色（不是白色），保持不变
                else:
                    # 保持原有颜色
                    pass
    
    def _get_filled_columns(self, sheet, row: int) -> set:
        """
        检查指定行中哪些列是实际填充的（有有意义的数据）
        
        Returns:
            set: 填充的列号集合
        """
        filled_columns = set()
        unfilled_columns = set()
        
        # 检查每一列的值
        for col in range(1, 33):  # 检查1-32列
            cell = sheet.cell(row=row, column=col)
            cell_value = cell.value
            
            # 判断是否为有意义的填充数据
            if self._is_meaningful_data(cell_value, col):
                filled_columns.add(col)
            else:
                unfilled_columns.add(col)
        
        # 添加调试日志，但只为第一行显示详细信息避免日志过多
        if row == 2:  # 第一行数据
            self.logger.info(f"问题报告单颜色设置 - 列填充状态分析（第{row}行）:")
            self.logger.info(f"  已填充列（将设置颜色）: {sorted(filled_columns)}")
            self.logger.info(f"  未填充列（不设置颜色）: {sorted(unfilled_columns)}")
            
            # 显示关键列的状态
            key_columns = {13: '问题名称', 14: '问题来源', 7: '关联版本', 8: '关联问题编号', 24: '总师意见'}
            for col, name in key_columns.items():
                cell_value = sheet.cell(row=row, column=col).value
                status = '已填充' if col in filled_columns else '未填充'
                self.logger.info(f"  列{col}({name}): '{cell_value}' -> {status}")
        
        return filled_columns
    
    def _is_meaningful_data(self, value, column: int) -> bool:
        """
        判断单元格的值是否为有意义的填充数据
        
        Args:
            value: 单元格值
            column: 列号
            
        Returns:
            bool: 是否为有意义数据
        """
        # 如果值为None，则不是填充数据
        if value is None:
            return False
        
        # 转换为字符串进行判断
        str_value = str(value).strip()
        
        # 空字符串不是有意义数据
        if not str_value:
            return False
        
        # 特殊处理：对于特定列，空格或特定占位符不算有意义数据
        if column == 13:  # 问题名称列
            # 空字符串不算有意义数据
            return False
        elif column == 14:  # 问题来源列
            # 空格不算有意义数据
            return str_value != ' '
        elif column == 7:  # 关联版本列
            # 空字符串不算有意义数据
            return False
        elif column == 8:  # 关联问题编号列
            # 单个空格不算有意义数据
            return str_value != ' '
        elif column == 24:  # 总师意见列
            # 空字符串不算有意义数据
            return False
        
        # 其他列，只要不是空就算有意义数据
        return True
    
    def _apply_borders(self, sheet, issue_count: int) -> None:
        """应用边框样式"""
        # 应用边框到所有数据行和列
        max_row = 1 + issue_count  # 标题行 + 数据行
        max_col = 32  # 32列
        
        for row in sheet.iter_rows(min_row=1, max_row=max_row, min_col=1, max_col=max_col):
            for cell in row:
                cell.border = self.border_style
        
        self.logger.debug(f"边框样式应用完成，范围: 1-{max_row}行, 1-{max_col}列")
    
    def _apply_alignment(self, sheet, issue_count: int) -> None:
        """应用对齐方式"""
        # 应用对齐方式到所有数据行和列
        max_row = 1 + issue_count  # 标题行 + 数据行
        max_col = 32  # 32列
        
        alignment = Alignment(wrap_text=True, vertical='center')
        
        for row in sheet.iter_rows(min_row=1, max_row=max_row, min_col=1, max_col=max_col):
            for cell in row:
                cell.alignment = alignment
        
        self.logger.debug(f"对齐方式应用完成，范围: 1-{max_row}行, 1-{max_col}列")
    
    def _get_color_fills(self) -> Dict[str, PatternFill]:
        """获取颜色填充样式"""
        return {
            'light_yellow': PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid"),
            'light_green': PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid"),
            'light_blue': PatternFill(start_color="99CCFF", end_color="99CCFF", fill_type="solid"),
            'light_orange': PatternFill(start_color="FFD700", end_color="FFD700", fill_type="solid"),
            'light_pink': PatternFill(start_color="FFB6C1", end_color="FFB6C1", fill_type="solid")
        }
    
    def _get_border_style(self) -> Border:
        """获取边框样式"""
        return Border(
            left=Side(style='thin', color='000000'),
            right=Side(style='thin', color='000000'),
            top=Side(style='thin', color='000000'),
            bottom=Side(style='thin', color='000000')
        )
    
    def highlight_configuration_item_specific_fields(
        self,
        excel_file_path: str,
        sheet_name: str,
        issue_count: int = 16
    ) -> bool:
        """
        高亮显示配置项测试特有的字段
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            issue_count: 问题数量
            
        Returns:
            bool: 高亮设置是否成功
        """
        try:
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            # 配置项测试特有字段使用橙色高亮
            orange_fill = self.color_fills['light_orange']
            
            start_row = 2
            for i in range(issue_count):
                current_row = start_row + i
                
                # 问题报告单编号（第5列）- 配置项测试特有的编号格式（CT-前缀）
                sheet.cell(row=current_row, column=5).fill = orange_fill
                
                # 测试活动（第9列）- 配置项测试的分类逻辑
                sheet.cell(row=current_row, column=9).fill = orange_fill
                
                # 问题类型（第10列）- 配置项测试的分类逻辑
                sheet.cell(row=current_row, column=10).fill = orange_fill
            
            wb.save(excel_file_path)
            self.logger.info("配置项测试特有字段高亮完成")
            return True
            
        except Exception as e:
            self.logger.error(f"高亮配置项测试特有字段时发生错误: {str(e)}")
            return False
    
    def highlight_auto_generated_fields(
        self,
        excel_file_path: str,
        sheet_name: str,
        issue_count: int = 16
    ) -> bool:
        """
        高亮显示自动生成的字段
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            issue_count: 问题数量
            
        Returns:
            bool: 高亮设置是否成功
        """
        try:
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            # 自动生成字段使用粉色高亮
            pink_fill = self.color_fills['light_pink']
            
            start_row = 2
            for i in range(issue_count):
                current_row = start_row + i
                
                # 自动生成的字段
                auto_generated_columns = [
                    1,   # 编号
                    5,   # 问题报告单编号
                    11,  # 问题等级
                    12,  # 问题数目
                    16,  # 测评单位意见
                    17,  # 问题修复优先级
                    20,  # 研制单位意见
                    21,  # 问题修复时间
                    26,  # 问题处理结果
                    27,  # 问题确认意见
                    31,  # 是否典型问题
                    32   # 是否低级错误
                ]
                
                for col in auto_generated_columns:
                    sheet.cell(row=current_row, column=col).fill = pink_fill
            
            wb.save(excel_file_path)
            self.logger.info("自动生成字段高亮完成")
            return True
            
        except Exception as e:
            self.logger.error(f"高亮自动生成字段时发生错误: {str(e)}")
            return False
    
    def apply_conditional_formatting(
        self,
        excel_file_path: str,
        sheet_name: str,
        issue_report_data: Dict[str, Any]
    ) -> bool:
        """
        应用条件格式设置
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            issue_report_data: 问题报告数据
            
        Returns:
            bool: 条件格式设置是否成功
        """
        try:
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            issue_classification = issue_report_data.get('issue_classification', [])
            issue_count = len(issue_classification)
            
            start_row = 2
            for i, classification in enumerate(issue_classification):
                current_row = start_row + i
                test_activity = classification.get('test_activity', '')
                
                # 根据测试活动类型设置特殊颜色
                if test_activity == '文档审查':
                    # 文档审查问题使用特殊标记
                    sheet.cell(row=current_row, column=9).fill = self.color_fills['light_blue']
                elif test_activity == '代码审查':
                    # 代码审查问题使用特殊标记
                    sheet.cell(row=current_row, column=9).fill = self.color_fills['light_green']
                elif test_activity == '静态分析':  # 🔧 新增：静态分析的颜色设置
                    # 静态分析问题使用特殊标记（使用浅紫色或其他区分色）
                    sheet.cell(row=current_row, column=9).fill = self.color_fills['light_purple'] if 'light_purple' in self.color_fills else self.color_fills['light_green']
                elif test_activity == '动态测试':
                    # 动态测试问题使用特殊标记
                    sheet.cell(row=current_row, column=9).fill = self.color_fills['light_yellow']
            
            wb.save(excel_file_path)
            self.logger.info("条件格式设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"应用条件格式设置时发生错误: {str(e)}")
            return False
    
    def reset_formatting(
        self,
        excel_file_path: str,
        sheet_name: str,
        issue_count: int = 16
    ) -> bool:
        """
        重置格式设置
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            issue_count: 问题数量
            
        Returns:
            bool: 重置是否成功
        """
        try:
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            # 清除所有格式
            max_row = 1 + issue_count
            max_col = 32
            
            for row in sheet.iter_rows(min_row=1, max_row=max_row, min_col=1, max_col=max_col):
                for cell in row:
                    cell.fill = PatternFill()  # 清除填充
                    cell.border = Border()     # 清除边框
                    cell.alignment = Alignment()  # 清除对齐
            
            wb.save(excel_file_path)
            self.logger.info("格式重置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"重置格式时发生错误: {str(e)}")
            return False
