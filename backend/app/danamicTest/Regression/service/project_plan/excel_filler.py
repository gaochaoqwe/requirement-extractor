"""
回归测试项目策划表Excel填充器

负责将回归测试项目策划表数据填充到Excel文件中。
"""

import logging
import openpyxl
from typing import Dict, List, Optional, Any
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class RegressionProjectPlanExcelFiller:
    """回归测试项目策划表Excel填充器"""
    
    def __init__(self):
        """初始化Excel填充器"""
        self.logger = logger
    
    def fill_project_plan_sheet_legacy(
        self,
        excel_file_path: str,
        sheet_name: str,
        ruanjian_xinxi: Dict[str, List[str]],
        ruanjian_name: str,
        diama_biangeng_xuqiu: Dict[str, str],
        file_path: str,
        ceshiren_name: str,
        kaifarenxinxi: List[str],
        zhuguan_name: str,
        biaoshihao_ceshixianng: List[str],
        daima_chayi_hangshu: int
    ) -> List[str]:
        """
        填充回归测试项目策划表内容（兼容原有接口）
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            ruanjian_xinxi: 软件信息字典
            ruanjian_name: 软件名称
            diama_biangeng_xuqiu: 代码变更需求字典
            file_path: 文档文件路径
            ceshiren_name: 测试人员名称
            kaifarenxinxi: 开发人员信息
            zhuguan_name: 主管名称
            biaoshihao_ceshixianng: 标识号测试项列表
            daima_chayi_hangshu: 代码差异行数
            
        Returns:
            List[str]: 生成的英文标识号列表
        """
        try:
            self.logger.info(f"开始填充回归测试项目策划表（兼容模式）: {sheet_name}")
            
            # 打开Excel工作簿
            wb = openpyxl.load_workbook(excel_file_path)
            
            # 获取工作表
            if sheet_name not in wb.sheetnames:
                self.logger.error(f"工作表 '{sheet_name}' 不存在")
                return [f'SRC-NAME{i+1}' for i in range(len(diama_biangeng_xuqiu))]
            
            sheet = wb[sheet_name]
            
            # 基本信息
            len_dict = len(diama_biangeng_xuqiu)
            allkeys = list(diama_biangeng_xuqiu.keys())
            
            # 读取文档获取章节号
            zhangjiehao, zhangjiehao_du = self._read_document_chapters(file_path, allkeys, ruanjian_name)
            
            # 计算时间和规模
            ceshi_start_time, ceshi_end_time = self._calculate_test_time(daima_chayi_hangshu)
            ceshiguimo_jisuan = self._calculate_test_scale(daima_chayi_hangshu)
            
            # 填充项目基本信息
            self._fill_project_basic_info(
                sheet, ruanjian_name, ruanjian_xinxi, kaifarenxinxi, 
                daima_chayi_hangshu, ceshiguimo_jisuan, len_dict, 
                ceshi_start_time, ceshi_end_time
            )
            
            # 填充测试项数据
            self._fill_test_items_legacy(
                sheet, allkeys, zhangjiehao, zhuguan_name, ceshiren_name, 
                biaoshihao_ceshixianng, len_dict
            )
            
            # 填充文档范围信息
            self._fill_document_scope_info(sheet, ruanjian_name, len_dict)
            
            # 应用格式
            self._apply_legacy_formatting(sheet, len_dict, zhangjiehao)
            
            # 保存文件
            wb.save(excel_file_path)
            
            self.logger.info("回归测试项目策划表填充完成（兼容模式）")
            return biaoshihao_ceshixianng
            
        except Exception as e:
            self.logger.error(f"填充回归测试项目策划表时发生错误: {str(e)}")
            return [f'SRC-NAME{i+1}' for i in range(len(diama_biangeng_xuqiu))]
    
    def fill_project_plan_sheet(
        self,
        excel_file_path: str,
        sheet_name: str,
        project_plan_data: Dict[str, Any]
    ) -> bool:
        """
        填充项目策划表工作表
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            project_plan_data: 项目策划表数据
            
        Returns:
            bool: 填充是否成功
        """
        try:
            self.logger.info(f"开始填充回归测试项目策划表: {sheet_name}")
            
            # 打开Excel工作簿
            wb = openpyxl.load_workbook(excel_file_path)
            
            # 获取工作表
            if sheet_name not in wb.sheetnames:
                self.logger.error(f"工作表 '{sheet_name}' 不存在")
                return False
            
            sheet = wb[sheet_name]
            
            # 获取数据
            project_info = project_plan_data.get('project_info', {})
            test_items = project_plan_data.get('test_items', [])
            personnel_info = project_plan_data.get('personnel_info', {})
            document_info = project_plan_data.get('document_info', {})
            
            # 填充项目信息
            self._fill_project_info_new(sheet, project_info)
            
            # 填充测试项数据
            self._fill_test_items_new(sheet, test_items, personnel_info)
            
            # 填充文档信息
            self._fill_document_info_new(sheet, document_info, len(test_items))
            
            # 保存文件
            wb.save(excel_file_path)
            
            self.logger.info("回归测试项目策划表填充完成")
            return True
            
        except Exception as e:
            self.logger.error(f"填充回归测试项目策划表时发生错误: {str(e)}")
            return False
    
    def _read_document_chapters(self, file_path: str, allkeys: List[str], ruanjian_name: str) -> tuple:
        """读取文档章节号"""
        try:
            from ...forms.formFilter.document_reader import read_word_document
            return read_word_document(file_path, allkeys, ruanjian_name)
        except Exception as e:
            self.logger.error(f"读取文档章节号时发生错误: {str(e)}")
            return ['未找到具体章节号'] * len(allkeys), []
    
    def _calculate_test_time(self, daima_chayi_hangshu: int) -> tuple:
        """计算测试时间"""
        try:
            from ...forms.formFilter.time_calculator import ceshi_start_end_time
            return ceshi_start_end_time(daima_chayi_hangshu)
        except Exception as e:
            self.logger.error(f"计算测试时间时发生错误: {str(e)}")
            return '2024-01-01', '2024-01-31'
    
    def _calculate_test_scale(self, daima_chayi_hangshu: int) -> int:
        """计算测试规模"""
        try:
            from ...forms.formFilter.project_info_form_filler import ceshiguimo_fenxi
            return ceshiguimo_fenxi(daima_chayi_hangshu)
        except Exception as e:
            self.logger.error(f"计算测试规模时发生错误: {str(e)}")
            return daima_chayi_hangshu
    
    def _fill_project_basic_info(
        self,
        sheet,
        ruanjian_name: str,
        ruanjian_xinxi: Dict[str, List[str]],
        kaifarenxinxi: List[str],
        daima_chayi_hangshu: int,
        ceshiguimo_jisuan: int,
        len_dict: int,
        ceshi_start_time: str,
        ceshi_end_time: str
    ):
        """填充项目基本信息"""
        xiangyulaiyuan = kaifarenxinxi[1] if len(kaifarenxinxi) > 1 else ''
        ruanjian_biaoshi = ruanjian_xinxi.get('软件标识', [''])[0]
        
        # 填充基本项目信息
        sheet.cell(row=2, column=5, value=ruanjian_name)     # 1、项目名称
        sheet.cell(row=3, column=5, value=ruanjian_biaoshi)  # 2、项目编号
        sheet.cell(row=4, column=5, value=xiangyulaiyuan)    # 3、项目来源
        sheet.cell(row=5, column=5, value='光电')                # 4、专业方向
        sheet.cell(row=6, column=5, value=str(daima_chayi_hangshu))               # 6、结算测试代码行数（行）
        sheet.cell(row=7, column=5, value=str(ceshiguimo_jisuan))                 # 7、实际测试代码行数（行）
        sheet.cell(row=8, column=5, value=len_dict)          # 8、采集的原始需求个数
        sheet.cell(row=9, column=5, value=ceshi_start_time)  # 7、计划开始日期
        sheet.cell(row=10, column=5, value=ceshi_end_time)   # 8、计划完成日期
        sheet.cell(row=11, column=5, value=len_dict)         # 10、测试需求数
        sheet.cell(row=12, column=5, value='是')             # 11、是否紧急项目
    
    def _fill_test_items_legacy(
        self,
        sheet,
        allkeys: List[str],
        zhangjiehao: List[str],
        zhuguan_name: str,
        ceshiren_name: str,
        biaoshihao_ceshixianng: List[str],
        len_dict: int
    ):
        """填充测试项数据（兼容模式）"""
        # 对测试项的内容进行填写
        index = 0
        for item in range(18, 18 + len_dict):
            sheet.cell(row=item, column=2, value=index + 1)            # 1、序号
            sheet.cell(row=item, column=3, value=allkeys[index])       # 2、软件需求
            sheet.cell(row=item, column=4, value=allkeys[index])       # 3、标准子需求名称
            sheet.cell(row=item, column=5, value=0.2)                  # 4、标准子需求单位
            sheet.cell(row=item, column=6, value=zhangjiehao[index])   # 5、需求分析
            sheet.cell(row=item, column=7, value='重要')                # 6、重要程度
            sheet.cell(row=item, column=8, value='是')                  # 7、是否充分测试
            sheet.cell(row=item, column=9, value=zhuguan_name)        # 8、需求分析
            sheet.cell(row=item, column=10, value=ceshiren_name)       # 9、文档审查
            sheet.cell(row=item, column=11, value=ceshiren_name)       # 9、静态分析
            sheet.cell(row=item, column=12, value=ceshiren_name)       # 11、代码审查
            sheet.cell(row=item, column=13, value=ceshiren_name)       # 12、动态测试（L）
            sheet.cell(row=item, column=14, value=biaoshihao_ceshixianng[index])  # 13、测试标识（M）
            index = index + 1
    
    def _fill_project_info_new(self, sheet, project_info: Dict[str, Any]):
        """填充项目信息（新接口）"""
        sheet.cell(row=2, column=5, value=project_info.get('project_name', ''))
        sheet.cell(row=3, column=5, value=project_info.get('project_number', ''))
        sheet.cell(row=4, column=5, value=project_info.get('project_source', ''))
        sheet.cell(row=5, column=5, value=project_info.get('professional_direction', '光电'))
        sheet.cell(row=6, column=5, value=project_info.get('settlement_code_lines', ''))
        sheet.cell(row=7, column=5, value=project_info.get('actual_code_lines', ''))
        sheet.cell(row=8, column=5, value=project_info.get('original_requirements_count', ''))
        sheet.cell(row=9, column=5, value=project_info.get('planned_start_date', ''))
        sheet.cell(row=10, column=5, value=project_info.get('planned_end_date', ''))
        sheet.cell(row=11, column=5, value=project_info.get('test_requirements_count', ''))
        sheet.cell(row=12, column=5, value=project_info.get('is_urgent', '是'))
    
    def _fill_test_items_new(self, sheet, test_items: List[Dict[str, Any]], personnel_info: Dict[str, str]):
        """填充测试项数据（新接口）"""
        for i, test_item in enumerate(test_items):
            row = 18 + i
            sheet.cell(row=row, column=2, value=test_item.get('index', i + 1))
            sheet.cell(row=row, column=3, value=test_item.get('name', ''))
            sheet.cell(row=row, column=4, value=test_item.get('standard_name', ''))
            sheet.cell(row=row, column=5, value=test_item.get('standard_unit', 0.2))
            sheet.cell(row=row, column=6, value=test_item.get('chapter_number', ''))
            sheet.cell(row=row, column=7, value=test_item.get('importance', '重要'))
            sheet.cell(row=row, column=8, value=test_item.get('full_test', '是'))
            sheet.cell(row=row, column=9, value=personnel_info.get('requirements_analyst', ''))
            sheet.cell(row=row, column=10, value=personnel_info.get('document_reviewer', ''))
            sheet.cell(row=row, column=11, value=personnel_info.get('static_analyst', ''))
            sheet.cell(row=row, column=12, value=personnel_info.get('code_reviewer', ''))
            sheet.cell(row=row, column=13, value=personnel_info.get('dynamic_tester', ''))
            sheet.cell(row=row, column=14, value=test_item.get('test_identifier', ''))
    
    def _fill_document_scope_info(self, sheet, ruanjian_name: str, len_dict: int):
        """填充文档范围信息"""
        # 生成策划表最后4列的内容
        sheet.cell(row=16 + len_dict + 2, column=3).value = f"文档审查范围：\n1.《{ruanjian_name}软件变更与影响域分析报告》；\n2.《{ruanjian_name}需求规格说明》；"
        sheet.cell(row=16 + len_dict + 3, column=3).value = "静态分析范围:\n全部手写代码；"
        sheet.cell(row=16 + len_dict + 4, column=3).value = "代码审查范围:\n全部手写代码；"
        sheet.cell(row=16 + len_dict + 5, column=3).value = "环境其他要求:\n本次测试使用产品加检测仪环境；"
        sheet.cell(row=16 + len_dict + 6, column=3).value = "其他要求:\n无；"
    
    def _fill_document_info_new(self, sheet, document_info: Dict[str, str], test_count: int):
        """填充文档信息（新接口）"""
        sheet.cell(row=16 + test_count + 2, column=3).value = document_info.get('document_review_scope', '')
        sheet.cell(row=16 + test_count + 3, column=3).value = document_info.get('static_analysis_scope', '')
        sheet.cell(row=16 + test_count + 4, column=3).value = document_info.get('code_review_scope', '')
        sheet.cell(row=16 + test_count + 5, column=3).value = document_info.get('environment_requirements', '')
        sheet.cell(row=16 + test_count + 6, column=3).value = document_info.get('other_requirements', '')
    
    def _apply_legacy_formatting(self, sheet, len_dict: int, zhangjiehao: List[str]):
        """应用格式（兼容模式）"""
        from openpyxl.styles import PatternFill, Border, Side, Alignment
        
        # 设置边框和格式
        border_style = Border(
            left=Side(style='thin', color='000000'), 
            right=Side(style='thin', color='000000'), 
            top=Side(style='thin', color='000000'), 
            bottom=Side(style='thin', color='000000')
        )
        light_yellow_fill = PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid")
        red_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
        
        for row1 in range(18, 18 + len_dict):  # 行
            for column in range(1, 14):
                # 获取当前单元格
                cell = sheet.cell(row=row1, column=column)
                sheet.cell(row=row1, column=column).fill = light_yellow_fill
                # 设置边框和格式
                cell.border = border_style
                cell.alignment = Alignment(wrap_text=True, vertical='center')
        
        # 对未找到的章节号进行颜色标识，避免发生将错误的结果直接写入到报告中
        weizhaodao_xiabiao = [index for index, value in enumerate(zhangjiehao) if value == '未找到具体章节号']
        if len(weizhaodao_xiabiao) > 0:
            for row1 in weizhaodao_xiabiao:  # 行
                for column in range(1, 14):
                    # 获取当前单元格
                    cell = sheet.cell(row=18 + row1, column=column)
                    sheet.cell(row=18 + row1, column=column).fill = red_fill
                    # 设置边框和格式
                    cell.border = border_style
                    cell.alignment = Alignment(wrap_text=True, vertical='center')
    
    def update_single_test_item(
        self,
        excel_file_path: str,
        sheet_name: str,
        item_index: int,
        field_name: str,
        field_value: str
    ) -> bool:
        """
        更新单个测试项的字段
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            item_index: 测试项索引（从1开始）
            field_name: 字段名称
            field_value: 字段值
            
        Returns:
            bool: 更新是否成功
        """
        try:
            self.logger.info(f"更新测试项{item_index}的字段{field_name}")
            
            # 打开Excel工作簿
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            # 计算行号（测试项从第18行开始）
            row = 17 + item_index
            
            # 字段映射
            field_mapping = {
                'name': 3,                    # 软件需求
                'standard_name': 4,           # 标准子需求名称
                'standard_unit': 5,           # 标准子需求单位
                'chapter_number': 6,          # 章节号
                'importance': 7,              # 重要程度
                'full_test': 8,               # 是否充分测试
                'test_identifier': 14         # 测试标识
            }
            
            # 获取列号
            if field_name not in field_mapping:
                self.logger.error(f"未知的字段名称: {field_name}")
                return False
            
            col = field_mapping[field_name]
            
            # 更新单元格
            sheet.cell(row=row, column=col).value = field_value
            
            # 保存文件
            wb.save(excel_file_path)
            
            self.logger.info(f"测试项{item_index}的字段{field_name}更新完成")
            return True
            
        except Exception as e:
            self.logger.error(f"更新单个测试项字段时发生错误: {str(e)}")
            return False
    
    def get_filled_data_summary(
        self,
        excel_file_path: str,
        sheet_name: str,
        test_count: int
    ) -> Dict[str, Any]:
        """
        获取已填充数据的摘要
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            test_count: 测试项数量
            
        Returns:
            Dict[str, Any]: 数据摘要
        """
        try:
            # 打开Excel工作簿
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            filled_items = 0
            test_details = []
            
            start_row = 18
            for i in range(test_count):
                current_row = start_row + i
                
                # 检查关键字段是否已填充
                test_name = sheet.cell(row=current_row, column=3).value
                test_identifier = sheet.cell(row=current_row, column=14).value
                
                if test_name and test_identifier:
                    filled_items += 1
                
                # 收集详细信息
                detail = {
                    'index': i + 1,
                    'test_name': test_name or '',
                    'standard_name': sheet.cell(row=current_row, column=4).value or '',
                    'chapter_number': sheet.cell(row=current_row, column=6).value or '',
                    'test_identifier': test_identifier or ''
                }
                test_details.append(detail)
            
            summary = {
                'total_items': test_count,
                'filled_items': filled_items,
                'completion_rate': round(filled_items / test_count * 100, 2) if test_count > 0 else 0,
                'test_details': test_details
            }
            
            self.logger.info(f"数据摘要: 共{test_count}项，已填充{filled_items}项")
            return summary
            
        except Exception as e:
            self.logger.error(f"获取数据摘要时发生错误: {str(e)}")
            return {}
    
    def backup_sheet_data(
        self,
        excel_file_path: str,
        sheet_name: str,
        backup_file_path: str
    ) -> bool:
        """
        备份工作表数据
        
        Args:
            excel_file_path: 源Excel文件路径
            sheet_name: 工作表名称
            backup_file_path: 备份文件路径
            
        Returns:
            bool: 备份是否成功
        """
        try:
            import shutil
            
            self.logger.info(f"备份回归测试项目策划表数据: {sheet_name}")
            
            # 复制整个文件
            shutil.copy2(excel_file_path, backup_file_path)
            
            self.logger.info(f"回归测试项目策划表数据备份完成: {backup_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"备份回归测试项目策划表数据时发生错误: {str(e)}")
            return False
