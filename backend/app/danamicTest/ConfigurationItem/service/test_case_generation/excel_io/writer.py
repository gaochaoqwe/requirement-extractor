"""
Excel 写入模块
- write_formatted_cases_to_excel: 适配增强服务，复用 test_case_form_handler 的单行填充逻辑
- write_realtime_cases_to_excel: 适配实时服务，使用简单表头直接写入
"""
from typing import List, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)


def write_formatted_cases_to_excel(formatted_cases: List[Dict[str, Any]], excel_path: str, sheet_name: str) -> bool:
    """将格式化后的用例写入 Excel（增强服务路径），不再依赖 test_case_form_handler。

    采用与实时写入一致的轻量表头，字段做合理映射：
    - sequence_number -> 序号
    - test_item_name -> 测试项名称
    - test_case_number -> 测试项标识/测试用例编号（若两者都需要，优先填充对应列）
    - test_case_name -> 测试用例名称
    - test_type -> 测试类型
    - requirement_traceability -> 软件需求追踪关系
    - input_conditions -> 输入条件/测试步骤
    - expected_results -> 预期结果
    - test_personnel -> 测试人员
    其余列留空或采用默认值。
    """
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

        # 打开或创建工作簿
        try:
            wb = openpyxl.load_workbook(excel_path)
        except FileNotFoundError:
            wb = openpyxl.Workbook()

        # 获取或创建工作表
        if sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
        else:
            ws = wb.create_sheet(sheet_name)

        # 🔧 定义蓝色填充样式（与project_info模块保持一致）
        light_blue_fill = PatternFill(start_color="99CCFF", end_color="99CCFF", fill_type="solid")
        
        # 🔧 定义边框样式
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        headers = [
            "序号", "测试项名称", "测试项标识", "测试用例名称", "测试用例编号",
            "测试类型", "测试描述", "输入条件", "预期结果", "通过判据",
            "设计人", "设计时间", "测试人员", "测试时间", "测试结果",
            "测试结论", "执行年月", "发现问题数", "软件需求追踪关系"
        ]
        # 写入标题
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = thin_border

        # 行数据写入
        for idx, case in enumerate(formatted_cases, 1):
            row_idx = idx + 1
            row_data = [
                case.get('sequence_number', idx),
                case.get('test_item_name', ''),
                case.get('test_item_identifier', case.get('test_case_number', f'TI{idx:03d}')),
                case.get('test_case_name', ''),
                case.get('test_case_number', f'TC{idx:03d}'),
                case.get('test_type', '功能测试'),
                case.get('test_description', case.get('requirement_traceability', '')),
                case.get('input_conditions', ''),
                case.get('expected_results', ''),
                case.get('pass_criteria', '测试步骤执行结果与预期一致'),
                case.get('case_designer', ''),
                case.get('design_time', ''),
                case.get('test_personnel', ''),
                case.get('test_time', ''),
                case.get('test_result', ''),
                case.get('test_conclusion', ''),
                case.get('execution_year_month', ''),
                case.get('issues_found_count', 0),
                case.get('software_requirement_trace', case.get('requirement_traceability', '')),
            ]
            for col, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_idx, column=col, value=value)
                cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
                cell.border = thin_border
                
                # 🔧 为所有填充数据的单元格添加蓝色背景（除了待填写的字段）
                if value is not None and str(value).strip():  # 只有有内容的单元格才着色
                    # 测试结果列（第15列）通常是待填写的，不着色
                    if col != 15:  # 测试结果列不着色
                        cell.fill = light_blue_fill

        # 自动列宽
        for column in ws.columns:
            max_length = 0
            try:
                column_letter = column[0].column_letter
            except Exception:
                continue
            for cell in column:
                try:
                    text = str(cell.value) if cell.value is not None else ''
                    max_length = max(max_length, len(text))
                except Exception:
                    pass
            ws.column_dimensions[column_letter].width = min(max_length + 2, 50)

        wb.save(excel_path)
        try:
            wb.close()
        except Exception:
            pass
        return True
    except Exception as e:
        logger.error(f"[excel_io] 写入增强服务用例到Excel失败: {e}")
        return False


def write_realtime_cases_to_excel(test_cases: List[Dict[str, Any]], excel_path: str, sheet_name: str) -> bool:
    """将实时服务用例写入 Excel，包含简单表头与基础样式"""
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

        logger.info(f"[excel_io] 开始写入测试用例到Excel: {excel_path}")
        logger.info(f"[excel_io] 目标工作表: {sheet_name}")
        logger.info(f"[excel_io] 测试用例数量: {len(test_cases)}")

        # 打开或创建工作簿
        try:
            # 检查文件是否存在且不为空
            if os.path.exists(excel_path) and os.path.getsize(excel_path) > 0:
                workbook = openpyxl.load_workbook(excel_path)
                logger.info(f"[excel_io] 成功加载现有Excel文件")
            else:
                workbook = openpyxl.Workbook()
                logger.info(f"[excel_io] 创建新的Excel工作簿（文件不存在或为空）")
        except Exception as load_error:
            logger.warning(f"[excel_io] 加载Excel文件失败: {load_error}，创建新工作簿")
            workbook = openpyxl.Workbook()
        
        # 获取或创建工作表
        if sheet_name in workbook.sheetnames:
            worksheet = workbook[sheet_name]
            logger.info(f"[excel_io] 使用现有工作表: {sheet_name}")
            # 清空现有数据（保留表头）
            for row in worksheet.iter_rows(min_row=2):
                for cell in row:
                    cell.value = None
        else:
            worksheet = workbook.create_sheet(sheet_name)
            logger.info(f"[excel_io] 创建新工作表: {sheet_name}")

        # 🔧 定义蓝色填充样式（与project_info模块保持一致）
        light_blue_fill = PatternFill(start_color="99CCFF", end_color="99CCFF", fill_type="solid")
        
        # 🔧 定义边框样式
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        headers = [
            "ID", "序号", "软件配置项名称", "被测软件版本", "测试轮次", "需求追溯", "测试项名称", 
            "测试项标识", "测试用例名称", "测试用例编号", "测试类型", "测试描述", "预置条件",
            "前提与约束", "终止条件", "输入条件", "预期结果", "通过准则", "用例设计人", "校对人",
            "设计时间", "校对时间", "测试人员", "监督人员", "测试时间", "测试结果", "测试结论",
            "问题报告单编号", "执行年月", "用例发现问题数"
        ]
        
        # 写入标题行
        logger.info(f"[excel_io] 写入表头，共 {len(headers)} 列")
        for col, header in enumerate(headers, 1):
            cell = worksheet.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = thin_border

        # 写入数据
        logger.info(f"[excel_io] 开始写入 {len(test_cases)} 条测试用例数据")
        for idx, case in enumerate(test_cases, 1):
            row_idx = idx + 1
            row_data = [
                '',  # 1. ID - 不填充
                case.get('sequence_number', idx),  # 2. 序号
                case.get('software_item_name', ''),  # 3. 软件配置项名称
                case.get('software_version', ''),  # 4. 被测软件版本
                case.get('test_round', '第一轮'),  # 5. 测试轮次
                case.get('requirement_traceability', ''),  # 6. 需求追溯
                case.get('test_item_name', ''),  # 7. 测试项名称
                case.get('test_item_identifier', ''),  # 8. 测试项标识
                case.get('test_case_name', ''),  # 9. 测试用例名称
                case.get('test_case_number', f'TC{idx:03d}'),  # 10. 测试用例编号
                case.get('test_type', '功能测试'),  # 11. 测试类型
                case.get('test_description', ''),  # 12. 测试描述
                case.get('preconditions', '被测软件正常加载，检测仪、调试计算机上电、测试环境连接正常'),  # 13. 预置条件
                case.get('prerequisites_constraints', '无'),  # 14. 前提与约束
                "正常终止条件:按正常测试步骤完成测试过程.\n异常终止条件:被测软件功能实现错误、测试用例设计错误、操作错误、测试环境出现异常情况。",  # 15. 终止条件
                case.get('input_conditions', case.get('input_actions', '')),  # 16. 输入条件
                case.get('expected_results', ''),  # 17. 预期结果
                case.get('pass_criteria', '实测结果与预期结果一致表明测试通过，否则测试不通过'),  # 18. 通过准则
                case.get('case_designer', case.get('test_personnel', '测试人员')),  # 19. 用例设计人
                case.get('reviewer', case.get('supervisor', '主管')),  # 20. 校对人
                case.get('design_time', ''),  # 21. 设计时间
                case.get('review_time', case.get('design_time', '')),  # 22. 校对时间
                case.get('test_personnel', '测试人员'),  # 23. 测试人员
                case.get('supervisor', '主管'),  # 24. 监督人员
                case.get('test_time', ''),  # 25. 测试时间
                case.get('test_result', ''),  # 26. 测试结果（待填写）
                case.get('test_conclusion', '通过'),  # 27. 测试结论
                case.get('issue_report_number', ''),  # 28. 问题报告单编号
                case.get('execution_year_month', ''),  # 29. 执行年月
                case.get('issues_found_count', 0),  # 30. 用例发现问题数
            ]
            
            logger.debug(f"[excel_io] 写入第 {idx} 行数据: {case.get('test_case_name', 'N/A')}")
            
            for col, value in enumerate(row_data, 1):
                cell = worksheet.cell(row=row_idx, column=col, value=value)
                # 为多行文本内容设置自动换行
                if col in [15, 16, 17]:  # 终止条件、输入条件、预期结果
                    cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
                else:
                    cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
                cell.border = thin_border
                
                # 🔧 为所有填充数据的单元格添加蓝色背景（除了待填写的字段）
                if value is not None and str(value).strip():  # 只有有内容的单元格才着色
                    # 待填写的字段不着色：ID(1)、测试结果(26)、问题报告单编号(28)
                    if col not in [1, 26, 28]:
                        cell.fill = light_blue_fill

        # 自动列宽
        logger.info(f"[excel_io] 设置自动列宽")
        for column in worksheet.columns:
            max_length = 0
            try:
                column_letter = column[0].column_letter
            except Exception:
                continue
            for cell in column:
                try:
                    cell_val = str(cell.value) if cell.value is not None else ''
                    max_length = max(max_length, len(cell_val))
                except Exception:
                    pass
            worksheet.column_dimensions[column_letter].width = min(max_length + 2, 50)

        # 保存文件
        logger.info(f"[excel_io] 保存Excel文件: {excel_path}")
        workbook.save(excel_path)
        logger.info(f"[excel_io] Excel文件保存成功")
        
        try:
            workbook.close()
            logger.info(f"[excel_io] Excel工作簿已关闭")
        except Exception as close_error:
            logger.warning(f"[excel_io] 关闭工作簿时出现警告: {close_error}")
        
        # 🔧 新增：应用组织资产库内容的颜色标记
        try:
            apply_database_source_highlighting_to_test_cases(excel_path, sheet_name)
        except Exception as color_error:
            logger.warning(f"[excel_io] 应用颜色标记时出现警告: {color_error}")
            
        logger.info(f"[excel_io] 成功写入 {len(test_cases)} 条测试用例到Excel")
        return True
        
    except Exception as e:
        logger.error(f"[excel_io] ❌ 写入实时服务用例到Excel失败: {e}")
        import traceback
        logger.error(f"[excel_io] 异常详情: {traceback.format_exc()}")
        return False


def apply_database_source_highlighting_to_test_cases(excel_path: str, sheet_name: str) -> bool:
    """
    为测试用例表中来自组织资产库的内容应用特殊颜色标记
    
    Args:
        excel_path: Excel文件路径
        sheet_name: 工作表名称
        
    Returns:
        bool: 颜色标记是否成功
    """
    try:
        from openpyxl import load_workbook
        from openpyxl.styles import PatternFill
        
        wb = load_workbook(excel_path)
        sheet = wb[sheet_name]
        
        # 定义组织资产库内容的特殊颜色（黄色背景）
        db_source_fill = PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid")  # 浅黄色
        
        # 遍历所有数据行（从第2行开始）
        marked_count = 0
        for row_idx in range(2, sheet.max_row + 1):
            # 🔧 新增：检查测试用例名称列（第9列）
            case_name_cell = sheet.cell(row=row_idx, column=9)
            if case_name_cell.value and str(case_name_cell.value).startswith('[DB_SOURCE]'):
                # 移除标记并应用颜色
                clean_value = str(case_name_cell.value).replace('[DB_SOURCE]', '').strip()
                case_name_cell.value = clean_value
                case_name_cell.fill = db_source_fill
                logger.info(f"第{row_idx}行测试用例名称列（第9列）应用组织资产库标记颜色（黄色）")
                marked_count += 1
            
            # 🔧 新增：检查测试描述列（第11列）
            test_description_cell = sheet.cell(row=row_idx, column=11)
            if test_description_cell.value and '[DB_SOURCE]' in str(test_description_cell.value):
                # 移除标记并应用颜色
                clean_value = str(test_description_cell.value).replace('[DB_SOURCE]', '').strip()
                test_description_cell.value = clean_value
                test_description_cell.fill = db_source_fill
                logger.info(f"第{row_idx}行测试描述列（第11列）应用组织资产库标记颜色（黄色）")
                marked_count += 1
            
            # 检查输入条件列（第16列）
            input_cell = sheet.cell(row=row_idx, column=16)
            if input_cell.value and str(input_cell.value).startswith('[DB_SOURCE]'):
                # 移除标记并应用颜色
                clean_value = str(input_cell.value).replace('[DB_SOURCE]', '').strip()
                input_cell.value = clean_value
                input_cell.fill = db_source_fill
                logger.info(f"第{row_idx}行输入条件列（第16列）应用组织资产库标记颜色（黄色）")
                marked_count += 1
            
            # 检查预期结果列（第17列）
            expected_cell = sheet.cell(row=row_idx, column=17)
            if expected_cell.value and str(expected_cell.value).startswith('[DB_SOURCE]'):
                # 移除标记并应用颜色
                clean_value = str(expected_cell.value).replace('[DB_SOURCE]', '').strip()
                expected_cell.value = clean_value
                expected_cell.fill = db_source_fill
                logger.info(f"第{row_idx}行预期结果列（第17列）应用组织资产库标记颜色（黄色）")
                marked_count += 1
        
        wb.save(excel_path)
        logger.info(f"测试用例表组织资产库内容颜色标记完成，共标记 {marked_count} 个单元格")
        return True
        
    except Exception as e:
        logger.error(f"应用测试用例表组织资产库颜色标记时发生错误: {str(e)}")
        return False
