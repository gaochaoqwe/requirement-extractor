"""
配置项测试需求分析表格式设置器

负责设置配置项测试需求分析表的格式、颜色和样式。
"""

import logging
import openpyxl
from openpyxl.styles import PatternFill, Border, Side, Alignment
from typing import Dict, List, Optional, Any
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class ConfigurationItemRequirementAnalysisFormatter:
    """配置项测试需求分析表格式设置器"""
    
    def __init__(self):
        """初始化格式设置器"""
        self.logger = logger
        self.color_fills = self._get_color_fills()
        self.border_style = self._get_border_style()
        self.alignment_style = self._get_alignment_style()
    
    def apply_formatting(
        self,
        excel_file_path: str,
        sheet_name: str,
        test_count: int,
        requirement_analysis_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        应用配置项测试需求分析表格式设置
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            test_count: 测试项数量
            requirement_analysis_data: 需求分析表数据（可选，用于动态格式设置）
            
        Returns:
            bool: 格式设置是否成功
        """
        try:
            self.logger.info(f"开始应用配置项测试需求分析表格式: {sheet_name}")
            
            # 打开Excel工作簿
            wb = openpyxl.load_workbook(excel_file_path)
            
            # 获取工作表
            if sheet_name not in wb.sheetnames:
                self.logger.error(f"工作表 '{sheet_name}' 不存在")
                return False
            
            sheet = wb[sheet_name]
            
            # 应用颜色填充
            self._apply_color_fills(sheet, test_count)
            
            # 应用边框样式
            self._apply_borders(sheet, test_count)
            
            # 应用对齐方式
            self._apply_alignment(sheet, test_count)
            
            # 应用特殊格式（如章节号缺失标记）
            if requirement_analysis_data:
                self._apply_special_formatting(sheet, test_count, requirement_analysis_data)
            
            # 保存文件
            wb.save(excel_file_path)
            
            self.logger.info("配置项测试需求分析表格式设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"应用配置项测试需求分析表格式时发生错误: {str(e)}")
            return False
    
    def apply_legacy_formatting(
        self,
        excel_file_path: str,
        sheet_name: str,
        test_count: int,
        zhangjiehao: List[str]
    ) -> bool:
        """
        应用兼容模式的格式设置
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            test_count: 测试项数量
            zhangjiehao: 章节号列表
            
        Returns:
            bool: 格式设置是否成功
        """
        try:
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            # 应用基本格式
            self._apply_color_fills(sheet, test_count)
            self._apply_borders(sheet, test_count)
            self._apply_alignment(sheet, test_count)
            
            # 应用章节号缺失标记
            self._apply_missing_chapter_formatting(sheet, test_count, zhangjiehao)
            
            wb.save(excel_file_path)
            self.logger.info("配置项测试需求分析表格式设置完成（兼容模式）")
            return True
            
        except Exception as e:
            self.logger.error(f"应用兼容模式格式时发生错误: {str(e)}")
            return False
    
    def _apply_color_fills(self, sheet, test_count: int) -> None:
        """应用颜色填充"""
        start_row = 2  # 测试项数据从第2行开始
        
        for i in range(test_count):
            current_row = start_row + i
            
            # 配置项测试需求分析表的颜色方案
            self._set_row_colors(sheet, current_row)
            
        self.logger.debug(f"颜色填充完成，共处理{test_count}行")
    
    def _set_row_colors(self, sheet, row: int) -> None:
        """设置单行颜色"""
        # 统一使用蓝色填充，与软件配置项信息表保持一致
        light_blue_fill = self.color_fills['light_blue']
        
        # 基本信息列（2-4列）：统一使用蓝色（与软件配置项信息表保持一致）
        for col in range(2, 5):
            sheet.cell(row=row, column=col).fill = light_blue_fill
        
        # 轮次信息列（5列）：统一使用蓝色（与软件配置项信息表保持一致）
        sheet.cell(row=row, column=5).fill = light_blue_fill
        
        # 需求信息列（6-13列）：浅蓝色
        for col in range(6, 14):
            sheet.cell(row=row, column=col).fill = light_blue_fill
        
        # 测试类型列（14列）：统一使用蓝色（与软件配置项信息表保持一致）
        sheet.cell(row=row, column=14).fill = light_blue_fill
        
        # 测试内容列（15-22列）：浅蓝色
        for col in range(15, 23):
            sheet.cell(row=row, column=col).fill = light_blue_fill
    
    def _apply_borders(self, sheet, test_count: int) -> None:
        """应用边框样式"""
        # 应用边框到测试项数据行
        start_row = 2
        max_row = start_row + test_count - 1
        max_col = 22  # 配置项测试需求分析表有22列
        
        for row in sheet.iter_rows(min_row=1, max_row=max_row, min_col=1, max_col=max_col):
            for cell in row:
                cell.border = self.border_style
        
        self.logger.debug(f"边框样式应用完成，范围: 1-{max_row}行, 1-{max_col}列")
    
    def _apply_alignment(self, sheet, test_count: int) -> None:
        """应用对齐方式"""
        # 应用对齐方式到测试项数据行
        start_row = 2
        max_row = start_row + test_count - 1
        max_col = 22  # 配置项测试需求分析表有22列
        
        for row in sheet.iter_rows(min_row=1, max_row=max_row, min_col=1, max_col=max_col):
            for cell in row:
                cell.alignment = self.alignment_style
        
        self.logger.debug(f"对齐方式应用完成，范围: 1-{max_row}行, 1-{max_col}列")
    
    def _apply_special_formatting(self, sheet, test_count: int, requirement_analysis_data: Dict[str, Any]) -> None:
        """应用特殊格式设置"""
        try:
            test_items = requirement_analysis_data.get('test_items', [])
            # 🔧 修复：统一使用蓝色填充，与其他列保持一致
            light_blue_fill = self.color_fills['light_blue']
            
            start_row = 2
            for i, test_item in enumerate(test_items):
                current_row = start_row + i
                
                # 确保这些列也使用蓝色填充，保持颜色统一
                sheet.cell(row=current_row, column=10).fill = light_blue_fill  # 软件需求规格说明追踪
                sheet.cell(row=current_row, column=13).fill = light_blue_fill  # 软件需求描述
                sheet.cell(row=current_row, column=17).fill = light_blue_fill  # 软件需求规格说明条目追踪关系
            
            self.logger.debug("特殊格式设置完成")
            
        except Exception as e:
            self.logger.error(f"应用特殊格式设置时发生错误: {str(e)}")
    
    def _apply_missing_chapter_formatting(self, sheet, test_count: int, zhangjiehao: List[str]) -> None:
        """应用章节号缺失格式"""
        # 🔧 修复：统一使用蓝色填充，与其他列保持一致
        light_blue_fill = self.color_fills['light_blue']
        
        # 无论章节号是否找到，都使用蓝色填充，保持颜色统一
        start_row = 2
        for index in range(len(zhangjiehao)):
            current_row = start_row + index
            
            # 所有相关列都使用蓝色填充
            sheet.cell(row=current_row, column=10).fill = light_blue_fill  # 软件需求规格说明追踪
            sheet.cell(row=current_row, column=13).fill = light_blue_fill  # 软件需求描述
            sheet.cell(row=current_row, column=17).fill = light_blue_fill  # 软件需求规格说明条目追踪关系
            
            self.logger.info(f"已为{len(zhangjiehao)}个测试项应用蓝色填充")
    
    def _get_color_fills(self) -> Dict[str, PatternFill]:
        """获取颜色填充样式"""
        return {
            'light_yellow': PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid"),
            'light_green': PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid"),
            'light_blue': PatternFill(start_color="99CCFF", end_color="99CCFF", fill_type="solid"),
            'light_red': PatternFill(start_color="FFC0CB", end_color="FFC0CB", fill_type="solid"),
            'light_orange': PatternFill(start_color="FFD700", end_color="FFD700", fill_type="solid"),
            'light_pink': PatternFill(start_color="FFB6C1", end_color="FFB6C1", fill_type="solid"),
            'red': PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
        }
    
    def _get_border_style(self) -> Border:
        """获取边框样式"""
        return Border(
            left=Side(style='thin', color='000000'),
            right=Side(style='thin', color='000000'),
            top=Side(style='thin', color='000000'),
            bottom=Side(style='thin', color='000000')
        )
    
    def _get_alignment_style(self) -> Alignment:
        """获取对齐样式"""
        return Alignment(wrap_text=True, vertical='center')
    
    def highlight_configuration_item_specific_fields(
        self,
        excel_file_path: str,
        sheet_name: str,
        test_count: int
    ) -> bool:
        """
        高亮显示配置项测试特有的字段
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            test_count: 测试项数量
            
        Returns:
            bool: 高亮设置是否成功
        """
        try:
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            # 配置项测试特有字段使用橙色高亮
            orange_fill = self.color_fills['light_orange']
            
            start_row = 2
            for i in range(test_count):
                current_row = start_row + i
                
                # 配置项测试特有的字段
                sheet.cell(row=current_row, column=7).fill = orange_fill   # 标准子需求标识
                sheet.cell(row=current_row, column=12).fill = orange_fill  # 软件需求规格说明需求标识
                sheet.cell(row=current_row, column=14).fill = orange_fill  # 测试类型
                sheet.cell(row=current_row, column=16).fill = orange_fill  # 测试项标识
            
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
        test_count: int
    ) -> bool:
        """
        高亮显示自动生成的字段
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            test_count: 测试项数量
            
        Returns:
            bool: 高亮设置是否成功
        """
        try:
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            # 自动生成字段使用粉色高亮
            pink_fill = self.color_fills['light_pink']
            
            start_row = 2
            for i in range(test_count):
                current_row = start_row + i
                
                # 自动生成的字段
                auto_generated_columns = [
                    2,   # 编号
                    5,   # 轮次
                    7,   # 标准子需求标识
                    8,   # 标准子需求单位
                    9,   # 任务书需求追溯
                    10,  # 软件需求规格说明追踪（从文档读取）
                    12,  # 软件需求规格说明需求标识
                    14,  # 测试类型
                    16,  # 测试项标识
                    17,  # 软件需求规格说明条目追踪关系
                    18,  # 需求子项描述
                    19,  # 测试项描述（AI生成或数据库匹配）
                    20,  # 测试方法（AI生成或数据库匹配）
                    21,  # 充分性要求
                    22   # 通过准则
                ]
                
                for col in auto_generated_columns:
                    sheet.cell(row=current_row, column=col).fill = pink_fill
            
            wb.save(excel_file_path)
            self.logger.info("自动生成字段高亮完成")
            return True
            
        except Exception as e:
            self.logger.error(f"高亮自动生成字段时发生错误: {str(e)}")
            return False
    
    def highlight_ai_generated_content(
        self,
        excel_file_path: str,
        sheet_name: str,
        test_count: int
    ) -> bool:
        """
        高亮显示AI生成的内容
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            test_count: 测试项数量
            
        Returns:
            bool: 高亮设置是否成功
        """
        try:
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            # AI生成内容使用特殊颜色高亮
            ai_fill = PatternFill(start_color="E6E6FA", end_color="E6E6FA", fill_type="solid")  # 淡紫色
            
            start_row = 2
            for i in range(test_count):
                current_row = start_row + i
                
                # 检查测试描述和测试方法的内容特征
                test_description = sheet.cell(row=current_row, column=19).value or ''
                test_method = sheet.cell(row=current_row, column=20).value or ''
                
                # 简单判断是否为AI生成（基于内容长度和特征）
                if (len(test_description) > 100 or len(test_method) > 200 or 
                    ('AI' in test_description) or ('智能' in test_description)):
                    sheet.cell(row=current_row, column=19).fill = ai_fill  # 测试项描述
                    sheet.cell(row=current_row, column=20).fill = ai_fill  # 测试方法
            
            wb.save(excel_file_path)
            self.logger.info("AI生成内容高亮完成")
            return True
            
        except Exception as e:
            self.logger.error(f"高亮AI生成内容时发生错误: {str(e)}")
            return False
    
    def apply_conditional_formatting(
        self,
        excel_file_path: str,
        sheet_name: str,
        requirement_analysis_data: Dict[str, Any]
    ) -> bool:
        """
        应用条件格式设置
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            requirement_analysis_data: 需求分析表数据
            
        Returns:
            bool: 条件格式设置是否成功
        """
        try:
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            test_items = requirement_analysis_data.get('test_items', [])
            start_row = 2
            
            for i, test_item in enumerate(test_items):
                current_row = start_row + i
                test_name = test_item.get('name', '')
                
                # 根据测试项类型设置特殊颜色
                if '故障' in test_name or '报警' in test_name:
                    # 故障测试项使用特殊标记
                    sheet.cell(row=current_row, column=15).fill = self.color_fills['light_red']
                elif '接口' in test_name:
                    # 接口测试项使用特殊标记
                    sheet.cell(row=current_row, column=15).fill = self.color_fills['light_orange']
                elif '性能' in test_name:
                    # 性能测试项使用特殊标记
                    sheet.cell(row=current_row, column=15).fill = PatternFill(start_color="DDA0DD", end_color="DDA0DD", fill_type="solid")
            
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
        test_count: int
    ) -> bool:
        """
        重置格式设置
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            test_count: 测试项数量
            
        Returns:
            bool: 重置是否成功
        """
        try:
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            # 清除所有格式
            start_row = 2
            max_row = start_row + test_count - 1
            max_col = 22
            
            for row in sheet.iter_rows(min_row=start_row, max_row=max_row, min_col=1, max_col=max_col):
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
    
    def apply_header_formatting(
        self,
        excel_file_path: str,
        sheet_name: str
    ) -> bool:
        """
        应用标题行格式
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            bool: 标题格式设置是否成功
        """
        try:
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            # 标题行使用特殊格式
            header_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
            bold_font = openpyxl.styles.Font(bold=True)
            
            # 应用到第1行（标题行）
            for col in range(1, 23):  # 配置项测试需求分析表有22列
                cell = sheet.cell(row=1, column=col)
                cell.fill = header_fill
                cell.font = bold_font
                cell.border = self.border_style
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
            wb.save(excel_file_path)
            self.logger.info("标题行格式设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"应用标题行格式时发生错误: {str(e)}")
            return False
    
    def apply_database_source_highlighting(
        self,
        excel_file_path: str,
        sheet_name: str,
        test_items: List[Dict[str, Any]] = None
    ) -> bool:
        """
        为来自组织资产库的内容应用特殊颜色标记
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            test_items: 测试项数据列表（可选，不使用）
            
        Returns:
            bool: 颜色标记是否成功
        """
        try:
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            # 定义组织资产库内容的特殊颜色（红色字体）
            from openpyxl.styles import Font
            db_source_font = Font(color="FF0000")  # 红色字体
            
            # 🔧 修复：遍历Excel中的所有数据行，检查是否包含[DB_SOURCE]标记
            start_row = 2  # 数据从第2行开始
            max_row = sheet.max_row
            
            marked_count = 0
            
            for row_idx in range(start_row, max_row + 1):
                # 检查测试内容列（第19列）
                test_description_cell = sheet.cell(row=row_idx, column=19)
                if test_description_cell.value and '[DB_SOURCE]' in str(test_description_cell.value):
                    # 移除标记并应用红色字体
                    clean_content = str(test_description_cell.value).replace('[DB_SOURCE]', '').strip()
                    test_description_cell.value = clean_content
                    test_description_cell.font = db_source_font  # 应用红色字体
                    self.logger.info(f"第{row_idx}行测试内容列（第19列）应用组织资产库标记颜色（红色字体）")
                    marked_count += 1
                
                # 检查测试方法列（第20列）
                test_method_cell = sheet.cell(row=row_idx, column=20)
                if test_method_cell.value and '[DB_SOURCE]' in str(test_method_cell.value):
                    # 移除标记并应用红色字体
                    clean_method = str(test_method_cell.value).replace('[DB_SOURCE]', '').strip()
                    test_method_cell.value = clean_method
                    test_method_cell.font = db_source_font  # 应用红色字体
                    self.logger.info(f"第{row_idx}行测试方法列（第20列）应用组织资产库标记颜色（红色字体）")
                    marked_count += 1
            
            wb.save(excel_file_path)
            self.logger.info(f"组织资产库内容颜色标记完成，共标记 {marked_count} 个单元格")
            return True
            
        except Exception as e:
            self.logger.error(f"应用组织资产库颜色标记时发生错误: {str(e)}")
            return False
    
    def _process_database_marked_content(self, content_list: List[str]) -> Dict[str, Any]:
        """
        处理带有数据库标记的内容列表
        
        Args:
            content_list: 内容列表，可能包含[DB_SOURCE]标记
            
        Returns:
            Dict: {'text': 处理后的文本, 'has_db_source': 是否包含数据库内容}
        """
        processed_items = []
        has_db_source = False
        
        for i, content in enumerate(content_list, 1):
            if content.startswith('[DB_SOURCE]'):
                # 移除标记，添加特殊前缀标识
                clean_content = content.replace('[DB_SOURCE]', '').strip()
                processed_items.append(f"{i}{clean_content}")
                has_db_source = True
            else:
                processed_items.append(f"{i}{content}")
        
        return {
            'text': '\n'.join(processed_items),
            'has_db_source': has_db_source
        }
