"""
回归测试需求分析表格式设置器

负责设置回归测试需求分析表的格式、颜色和样式。
"""

import logging
import openpyxl
from openpyxl.styles import PatternFill, Border, Side, Alignment
from typing import Dict, List, Optional, Any
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class RegressionRequirementAnalysisFormatter:
    """回归测试需求分析表格式设置器"""
    
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
        应用回归测试需求分析表格式设置
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            test_count: 测试项数量
            requirement_analysis_data: 需求分析表数据（可选，用于动态格式设置）
            
        Returns:
            bool: 格式设置是否成功
        """
        try:
            self.logger.info(f"开始应用回归测试需求分析表格式: {sheet_name}")
            
            # 打开Excel工作簿
            wb = openpyxl.load_workbook(excel_file_path)
            
            # 获取工作表
            if sheet_name not in wb.sheetnames:
                self.logger.error(f"工作表 '{sheet_name}' 不存在")
                return False
            
            sheet = wb[sheet_name]
            
            # 应用基本格式设置
            self._apply_header_formatting(sheet)
            self._apply_content_formatting(sheet, test_count)
            self._apply_border_formatting(sheet, test_count)
            
            # 保存文件
            wb.save(excel_file_path)
            
            self.logger.info("回归测试需求分析表格式设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"应用回归测试需求分析表格式时发生错误: {str(e)}")
            return False
    
    def _apply_header_formatting(self, sheet):
        """应用表头格式设置"""
        try:
            # 设置表头背景色和字体
            header_fill = self.color_fills['header']
            for col in range(1, 23):  # 22列
                cell = sheet.cell(row=1, column=col)
                cell.fill = header_fill
                cell.alignment = self.alignment_style
                
        except Exception as e:
            self.logger.error(f"应用表头格式时发生错误: {str(e)}")
    
    def _apply_content_formatting(self, sheet, test_count: int):
        """应用内容格式设置"""
        try:
            # 设置内容区域格式
            content_fill = self.color_fills['content']
            for row in range(2, test_count + 2):
                for col in range(1, 23):
                    cell = sheet.cell(row=row, column=col)
                    cell.fill = content_fill
                    cell.alignment = self.alignment_style
                    
        except Exception as e:
            self.logger.error(f"应用内容格式时发生错误: {str(e)}")
    
    def _apply_border_formatting(self, sheet, test_count: int):
        """应用边框格式设置"""
        try:
            # 设置边框
            for row in range(1, test_count + 2):
                for col in range(1, 23):
                    cell = sheet.cell(row=row, column=col)
                    cell.border = self.border_style
                    
        except Exception as e:
            self.logger.error(f"应用边框格式时发生错误: {str(e)}")
    
    def _get_color_fills(self) -> Dict[str, PatternFill]:
        """获取颜色填充样式"""
        return {
            'header': PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid"),
            'content': PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid"),
            'highlight': PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid")
        }
    
    def _get_border_style(self) -> Border:
        """获取边框样式"""
        thin_side = Side(border_style="thin", color="000000")
        return Border(
            left=thin_side,
            right=thin_side,
            top=thin_side,
            bottom=thin_side
        )
    
    def _get_alignment_style(self) -> Alignment:
        """获取对齐样式"""
        return Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True
        ) 