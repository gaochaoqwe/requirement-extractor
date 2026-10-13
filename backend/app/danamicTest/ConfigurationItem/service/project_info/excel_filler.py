"""
项目基本信息Excel填充器

负责将项目基本信息数据填充到Excel工作表中。
"""

import logging
import openpyxl
from typing import Dict, List, Optional, Any
from pathlib import Path
import re
from openpyxl.styles import Alignment

# 配置日志
logger = logging.getLogger(__name__)

class ProjectInfoExcelFiller:
    """项目基本信息Excel填充器"""
    
    def __init__(self):
        """初始化Excel填充器"""
        self.logger = logger
        self.cell_mapping = self._get_cell_mapping()
        # 默认居中对齐（水平+垂直），满足“项目来源部门/项目主管需要居中”的要求
        self._center_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    def _apply_center_alignment(self, sheet, row: int, column: int) -> None:
        """将指定单元格设置为居中对齐（水平/垂直）"""
        print(f"\n[EXCEL_FILLER] _apply_center_alignment 被调用:")
        print(f"  - row={row}, column={column}")
        
        try:
            cell = sheet.cell(row=row, column=column)
            print(f"  - 应用前对齐: horizontal={cell.alignment.horizontal}, vertical={cell.alignment.vertical}")
            
            cell.alignment = self._center_alignment
            
            print(f"  - 应用后对齐: horizontal={cell.alignment.horizontal}, vertical={cell.alignment.vertical}")
        except Exception as e:
            # 对齐失败不影响主流程
            print(f"  - 错误: 设置居中对齐失败: {e}")
            self.logger.warning(f"设置单元格对齐失败 row={row}, col={column}: {e}")
    
    def fill_project_info_sheet(
        self,
        excel_file_path: str,
        sheet_name: str,
        project_data: Dict[str, Any]
    ) -> bool:
        """
        填充项目基本信息工作表
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            project_data: 项目数据字典
            
        Returns:
            bool: 填充是否成功
        """
        try:
            self.logger.info(f"开始填充项目基本信息表: {sheet_name}")
            
            # 打开Excel工作簿
            wb = openpyxl.load_workbook(excel_file_path)
            
            # 获取工作表
            if sheet_name not in wb.sheetnames:
                self.logger.error(f"工作表 '{sheet_name}' 不存在")
                return False
            
            sheet = wb[sheet_name]
            
            # 填充数据
            self._fill_data_to_sheet(sheet, project_data)
            
            # 保存文件
            wb.save(excel_file_path)
            
            self.logger.info("项目基本信息表填充完成")
            return True
            
        except Exception as e:
            self.logger.error(f"填充项目基本信息表时发生错误: {str(e)}")
            return False
    
    def _fill_data_to_sheet(self, sheet, project_data: Dict[str, Any]) -> None:
        """
        将数据填充到工作表
        
        Args:
            sheet: openpyxl工作表对象
            project_data: 项目数据字典
        """
        user_info = project_data.get('user_software_info', {})
        xinghao_list = project_data.get('xinghao_xinxi_list', [])
        suoshulingyu = project_data.get('suoshulingyu', '')
        fixed_values = project_data.get('fixed_values', {})
        
        # 填充可选信息（优先使用用户输入）
        if user_info:
            self._fill_user_software_info(sheet, user_info, suoshulingyu)
        elif xinghao_list:
            self._fill_xinghao_info(sheet, xinghao_list)
        
        # 填充人员信息
        self._fill_personnel_info(sheet, project_data)
        
        # 填充固定值
        self._fill_fixed_values(sheet, fixed_values)
    
    def _fill_user_software_info(self, sheet, user_info: Dict[str, str], default_domain: str) -> None:
        """
        填充用户软件信息
        
        Args:
            sheet: openpyxl工作表对象
            user_info: 用户软件信息字典
            default_domain: 默认领域
        """
        print(f"\n[EXCEL_FILLER] _fill_user_software_info 收到的 user_info:")
        for key, value in user_info.items():
            print(f"  - {key}: '{value}'")
        
        # 飞机型号
        sheet.cell(row=4, column=3, value=user_info.get('aircraft_model', ''))
        
        # 软件项目代号
        sheet.cell(row=5, column=3, value=user_info.get('software_id', ''))
        
        # 所属领域
        domain_value = user_info.get('domain', default_domain)
        sheet.cell(row=6, column=3, value=domain_value)
        
        # 项目总师
        sheet.cell(row=7, column=3, value=user_info.get('project_director', ''))
        
        # 主任设计师
        sheet.cell(row=9, column=3, value=user_info.get('chief_designer', ''))
        
        # 研制部门（直接使用用户输入，不进行清理）
        development_dept = user_info.get('development_department', '')
        if development_dept:
            # 🔧 修复：直接使用原始部门名称，不进行清理
            sheet.cell(row=8, column=3, value=development_dept)
            self.logger.info(f"[DEBUG] 研制部门填充: '{development_dept}' (不清理)")
        
        # ✨ 新增：项目主管（第16行）
        project_manager = user_info.get('project_manager', '')
        print(f"\n[EXCEL_FILLER] 准备填充项目主管:")
        print(f"  - 从 user_info 获取的值: '{project_manager}'")
        print(f"  - 目标位置: row=16, column=3")
        
        # 需求：项目主管默认取前端"可选信息-项目主管"，并居中
        cell_c16 = sheet.cell(row=16, column=3)
        cell_c16.value = project_manager
        print(f"  - 已写入单元格，值为: '{cell_c16.value}'")
        
        # C列（值）居中
        self._apply_center_alignment(sheet, 16, 3)
        # B列（标签"项目主管"）也居中
        self._apply_center_alignment(sheet, 16, 2)
        
        # C列（值）设置为蓝色背景（与其他已填写数据保持一致）
        from openpyxl.styles import PatternFill
        light_blue_fill = PatternFill(start_color="99CCFF", end_color="99CCFF", fill_type="solid")
        cell_c16.fill = light_blue_fill
        
        print(f"  - 已应用居中对齐（B列和C列）")
        print(f"  - 已应用蓝色填充到C列")
        print(f"  - C列对齐: horizontal={cell_c16.alignment.horizontal}, vertical={cell_c16.alignment.vertical}")
        print(f"  - B列对齐: horizontal={sheet.cell(row=16, column=2).alignment.horizontal}, vertical={sheet.cell(row=16, column=2).alignment.vertical}")
        
        if project_manager:
            self.logger.info(f"[DEBUG] 项目主管填充: '{project_manager}'")
    
    def _fill_xinghao_info(self, sheet, xinghao_list: List[str]) -> None:
        """
        填充型号信息（备用数据源）
        
        Args:
            sheet: openpyxl工作表对象
            xinghao_list: 型号信息列表
        """
        if len(xinghao_list) >= 6:
            sheet.cell(row=4, column=3, value=xinghao_list[0])  # 飞机型号
            sheet.cell(row=5, column=3, value=xinghao_list[1])  # 软件项目代号
            sheet.cell(row=6, column=3, value=xinghao_list[2])  # 所属领域
            sheet.cell(row=7, column=3, value=xinghao_list[3])  # 项目总师
            sheet.cell(row=9, column=3, value=xinghao_list[5])  # 主任设计师
    
    def _fill_personnel_info(self, sheet, project_data: Dict[str, Any]) -> None:
        """
        填充人员信息
        
        Args:
            sheet: openpyxl工作表对象
            project_data: 项目数据字典
        """
        # 研制部门（如果用户信息中没有，使用开发人员信息中的）
        user_info = project_data.get('user_software_info', {})
        if not user_info.get('development_department'):
            yanzhibumen = project_data.get('yanzhibumen', '')
            if yanzhibumen:
                sheet.cell(row=8, column=3, value=yanzhibumen)
        
        # 开发人员
        kaifaren = project_data.get('kaifaren', '')
        sheet.cell(row=10, column=3, value=kaifaren)
        
        # 测试主管
        zhuguan_name = project_data.get('zhuguan_name', '')
        sheet.cell(row=11, column=3, value=zhuguan_name)
    
    def _fill_fixed_values(self, sheet, fixed_values: Dict[str, str]) -> None:
        """
        填充固定值
        
        Args:
            sheet: openpyxl工作表对象
            fixed_values: 固定值字典
        """
        print(f"\n[EXCEL_FILLER] _fill_fixed_values 开始")
        print(f"  - 收到的 fixed_values: {fixed_values}")
        
        # 测试级别
        sheet.cell(row=12, column=3, value=fixed_values.get('test_level', '配置项测试'))
        
        # 测试类别
        sheet.cell(row=13, column=3, value=fixed_values.get('test_category', '内部测试'))
        
        # 测试环境
        sheet.cell(row=14, column=3, value=fixed_values.get('test_environment', '半实物环境'))
        
        # ✨ 新增：项目来源部门（第15行）- 默认值"科技部"
        # 需求：第15行（序号12）项目来源部门默认"科技部"，并居中
        project_source_value = fixed_values.get('project_source_department', '科技部')
        print(f"\n[EXCEL_FILLER] 准备填充项目来源部门:")
        print(f"  - 值: '{project_source_value}'")
        print(f"  - 目标位置: row=15, column=3")
        
        sheet.cell(row=15, column=3, value=project_source_value)
        print(f"  - 已写入单元格，值为: '{sheet.cell(row=15, column=3).value}'")
        
        # C列（值）居中
        self._apply_center_alignment(sheet, 15, 3)
        # B列（标签"项目来源部门"）也居中
        self._apply_center_alignment(sheet, 15, 2)
        print(f"  - 已调用 _apply_center_alignment（B列和C列）")
        print(f"  - C列对齐: horizontal={sheet.cell(row=15, column=3).alignment.horizontal}, vertical={sheet.cell(row=15, column=3).alignment.vertical}")
        print(f"  - B列对齐: horizontal={sheet.cell(row=15, column=2).alignment.horizontal}, vertical={sheet.cell(row=15, column=2).alignment.vertical}")
    
    def _clean_department_name(self, department_info: str) -> str:
        """
        清理部门名称，移除可能包含的职位和人名信息
        
        Args:
            department_info: 原始部门信息
            
        Returns:
            str: 清理后的部门名称
        """
        if not department_info or not department_info.strip():
            return ""
        
        info = department_info.strip()
        
        # 常见的职位关键词列表（按优先级排序，长的在前面）
        position_keywords = [
            "主任设计师", "副主任设计师", "总设计师", "设计师", 
            "项目经理", "部门经理", "总经理", "主管", "经理", "总监", 
            "部长", "副部长", "主任", "副主任", "总工程师", "工程师", 
            "技术员", "专员", "负责人"
        ]
        
        # 查找第一个匹配的职位关键词，并提取其前面的部分作为部门
        for keyword in position_keywords:
            if keyword in info:
                keyword_index = info.find(keyword)
                department = info[:keyword_index].strip()
                if department:
                    return department
        
        # 如果没有找到职位关键词，尝试移除末尾的人名
        # 假设人名是2-4个连续的中文字符
        # 匹配中文姓名模式（在字符串末尾）
        name_pattern = r'[一-龥]{2,4}$'
        department = re.sub(name_pattern, '', info).strip()
        
        # 如果移除后还有内容且与原字符串不同，返回清理后的结果
        if department and department != info:
            return department
        
        # 最后的兜底策略：如果字符串很长，找可能的部门结尾标识
        if len(info) > 6:
            for i in range(len(info) - 1, 1, -1):
                if info[i] in ['部', '司', '组', '室', '处', '科', '院', '中心', '局']:
                    potential_dept = info[:i+1]
                    # 避免返回过短的结果
                    if len(potential_dept) >= 3:
                        return potential_dept
        
        # 如果都不行，返回原始信息
        return info
    
    def _get_cell_mapping(self) -> Dict[str, tuple]:
        """
        获取单元格映射关系
        
        Returns:
            Dict[str, tuple]: 字段名到单元格位置的映射
        """
        return {
            'aircraft_model': (4, 3),        # 飞机型号
            'software_id': (5, 3),           # 软件项目代号
            'domain': (6, 3),                # 所属领域
            'project_director': (7, 3),      # 项目总师
            'development_department': (8, 3), # 研制部门
            'chief_designer': (9, 3),        # 主任设计师
            'developer': (10, 3),            # 开发人员
            'test_manager': (11, 3),         # 测试主管
            'test_level': (12, 3),           # 测试级别
            'test_category': (13, 3),        # 测试类别
            'test_environment': (14, 3),     # 测试环境
            'project_source_department': (15, 3),  # 项目来源部门
            'project_manager': (16, 3)       # 项目主管
        }
    
    def get_filled_data_summary(self, excel_file_path: str, sheet_name: str) -> Dict[str, str]:
        """
        获取已填充数据的摘要（用于验证和调试）
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            Dict[str, str]: 已填充的数据摘要
        """
        try:
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            summary = {}
            for field, (row, col) in self.cell_mapping.items():
                cell_value = sheet.cell(row=row, column=col).value
                summary[field] = str(cell_value) if cell_value else ""
            
            return summary
            
        except Exception as e:
            self.logger.error(f"获取填充数据摘要时发生错误: {str(e)}")
            return {}
