"""
回归测试代码审查报告下载API端点
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ...db.deps import get_db
from ...db.repository import TaskRepository, ProblemRepository, RegressionTaskRepository, DiffMappingRepository
import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from io import BytesIO
import os
from pathlib import Path
from typing import List, Dict, Any

router = APIRouter()

# 第一个sheet的列定义
PROBLEMS_SHEET_COLUMNS = [
    "任务信息",
    "文件名称",
    "源代码",
    "违反规则",
    "问题等级",
    "问题名称",
    "问题来源",
    "问题描述"
]

# 第二个sheet的基础列
MAPPINGS_SHEET_BASE_COLUMNS = [
    "任务信息",
    "原始报告内容"  # 新增列
]

@router.get("/download_report/{task_id}", summary="Download regression code review report as Excel")
def download_report(task_id: str, db: Session = Depends(get_db)):
    """
    下载回归测试代码审查报告
    
    Args:
        task_id: 任务ID (UUID字符串)
    
    Returns:
        Excel报告文件下载响应
    """
    # 检查任务是否存在
    task_repo = TaskRepository(db)
    task = task_repo.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在，ID: {task_id}")
    
    if task.status != "completed":
        raise HTTPException(status_code=400, detail=f"任务尚未完成，当前状态: {task.status}")
    
    # 获取回归测试任务和映射数据
    regression_task_repo = RegressionTaskRepository(db)
    diff_mapping_repo = DiffMappingRepository(db)
    problem_repo = ProblemRepository(db)
    
    # 获取回归测试任务列表
    regression_tasks = regression_task_repo.get_tasks_by_analysis_id(task_id)
    
    # 获取所有问题，按回归测试任务排序
    problems = problem_repo.get_problems_by_task_sorted_by_regression_task(task_id)
    
    # 获取所有代码映射
    all_mappings = diff_mapping_repo.get_mappings_by_analysis_id(task_id)

    # 创建Excel工作簿
    wb = openpyxl.Workbook()
    
    # 创建第一个sheet：审查问题单
    create_problems_sheet(wb, regression_tasks, problems)
    
    # 创建第二个sheet：代码映射信息
    create_mappings_sheet(wb, regression_tasks, all_mappings)

    # 导出为字节流
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    # 生成文件名
    filename = f"regression_review_result_task_{task_id}.xlsx"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    
    return StreamingResponse(
        output, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers=headers
    )


def create_problems_sheet(wb: openpyxl.Workbook, regression_tasks: List[Any], problems: List[Dict[str, Any]]) -> None:
    """
    创建审查问题单sheet
    
    Args:
        wb: Excel工作簿
        regression_tasks: 回归测试任务列表
        problems: 问题列表
    """
    # 使用默认的活动sheet
    ws = wb.active
    ws.title = "审查问题单"
    
    # 创建任务ID到任务名称的映射
    task_id_to_name = {}
    for task in regression_tasks:
        task_id_to_name[task.task_id] = task.task_name
    
    # 设置表头样式
    header_font = Font(bold=True)
    header_fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
    
    # 添加表头
    for col_idx, column_name in enumerate(PROBLEMS_SHEET_COLUMNS, 1):
        cell = ws.cell(row=1, column=col_idx, value=column_name)
        cell.font = header_font
        cell.fill = header_fill
    
    # 按任务ID排序问题列表
    # 注意：这里需要根据实际情况调整，因为问题记录可能没有直接的回归任务ID
    # 我们需要通过其他方式来确定问题属于哪个回归任务
    sorted_problems = sort_problems_by_task(problems, regression_tasks)
    
    # 添加问题数据
    for row_idx, problem in enumerate(sorted_problems, 2):
        # 获取任务信息
        task_name = get_task_name_for_problem(problem, task_id_to_name)
        
        # 合并四段式描述
        description = "\n".join([
            f"需求描述：{str(problem.get('description_requirement', ''))}",
            f"问题描述：{str(problem.get('description_issue', ''))}",
            f"问题定位：{str(problem.get('description_location', ''))}",
            f"影响分析：{str(problem.get('description_impact', ''))}"
        ])
        
        row_data = [
            task_name,
            problem.get("file_name", ""),
            problem.get("source_code", ""),
            problem.get("violation_rules", ""),
            problem.get("issue_level", ""),
            problem.get("issue_name", ""),
            problem.get("issue_location", ""),
            description
        ]
        
        for col_idx, value in enumerate(row_data, 1):
            ws.cell(row=row_idx, column=col_idx, value=value)
    
    # 设置列宽和自动换行
    wrap_alignment = Alignment(wrapText=True, vertical="top")
    for col_idx in range(1, len(PROBLEMS_SHEET_COLUMNS) + 1):
        column_letter = get_column_letter(col_idx)
        
        # 设置列宽
        if col_idx == 1:  # 任务信息列
            ws.column_dimensions[column_letter].width = 25
        elif col_idx == 2:  # 文件名称列
            ws.column_dimensions[column_letter].width = 30
        elif col_idx == 3:  # 源代码列
            ws.column_dimensions[column_letter].width = 50
        elif col_idx == 7:  # 问题描述列
            ws.column_dimensions[column_letter].width = 60
        else:
            ws.column_dimensions[column_letter].width = 20
        
        # 设置自动换行
        for row in ws.iter_rows(min_col=col_idx, max_col=col_idx):
            for cell in row:
                cell.alignment = wrap_alignment


def create_mappings_sheet(wb: openpyxl.Workbook, regression_tasks: List[Any], all_mappings: List[Any]) -> None:
    """
    创建代码映射信息sheet
    
    Args:
        wb: Excel工作簿
        regression_tasks: 回归测试任务列表
        all_mappings: 所有代码映射列表
    """
    # 创建新的sheet
    ws = wb.create_sheet(title="代码映射信息")
    
    # 创建任务ID到任务信息的映射
    task_id_to_info = {}
    for task in regression_tasks:
        task_id_to_info[task.task_id] = {
            'name': task.task_name,
            'original_content': task.original_report_content or '无原始报告内容'
        }
    
    # 按任务分组映射数据
    task_mappings = {}
    for mapping in all_mappings:
        task_id = mapping.task_id
        if task_id not in task_mappings:
            task_mappings[task_id] = []
        task_mappings[task_id].append(mapping)
    
    # 构建动态列头
    columns = MAPPINGS_SHEET_BASE_COLUMNS.copy()
    max_functions_per_task = 0
    
    # 计算每个任务的最大函数数量
    for task_id, mappings in task_mappings.items():
        function_count = len(mappings)
        if function_count > max_functions_per_task:
            max_functions_per_task = function_count
    
    # 添加函数列
    for i in range(max_functions_per_task):
        columns.append(f"函数{i+1}")
    
    # 设置表头样式
    header_font = Font(bold=True)
    header_fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
    
    # 添加表头
    for col_idx, column_name in enumerate(columns, 1):
        cell = ws.cell(row=1, column=col_idx, value=column_name)
        cell.font = header_font
        cell.fill = header_fill
    
    # 按任务ID排序添加数据
    sorted_task_ids = sorted(task_mappings.keys(), key=lambda x: int(x) if x.isdigit() else float('inf'))
    
    for row_idx, task_id in enumerate(sorted_task_ids, 2):
        mappings = task_mappings[task_id]
        task_info = task_id_to_info.get(task_id, {'name': f"任务{task_id}", 'original_content': '无原始报告内容'})
        
        # 第一列：任务信息
        ws.cell(row=row_idx, column=1, value=task_info['name'])
        
        # 第二列：原始报告内容
        ws.cell(row=row_idx, column=2, value=task_info['original_content'])
        
        # 后续列：函数映射信息
        for col_idx, mapping in enumerate(mappings, 3):  # 从第3列开始
            if col_idx <= len(columns):
                # 构建函数信息字符串
                function_info = build_function_info_string(mapping)
                ws.cell(row=row_idx, column=col_idx, value=function_info)
    
    # 设置列宽和自动换行
    wrap_alignment = Alignment(wrapText=True, vertical="top")
    for col_idx in range(1, len(columns) + 1):
        column_letter = get_column_letter(col_idx)
        
        # 设置列宽
        if col_idx == 1:  # 任务信息列
            ws.column_dimensions[column_letter].width = 25
        elif col_idx == 2:  # 原始报告内容列
            ws.column_dimensions[column_letter].width = 80
        else:  # 函数列
            ws.column_dimensions[column_letter].width = 60
        
        # 设置自动换行
        for row in ws.iter_rows(min_col=col_idx, max_col=col_idx):
            for cell in row:
                cell.alignment = wrap_alignment


def sort_problems_by_task(problems: List[Dict[str, Any]], regression_tasks: List[Any]) -> List[Dict[str, Any]]:
    """
    按任务排序问题列表
    
    Args:
        problems: 问题列表
        regression_tasks: 回归测试任务列表
        
    Returns:
        排序后的问题列表
    """
    # 创建任务ID排序映射
    task_order = {}
    for idx, task in enumerate(regression_tasks):
        task_order[task.task_id] = idx
    
    # 按回归测试任务ID排序，已在数据库查询中完成
    # 这里直接返回问题列表
    return problems


def get_task_name_for_problem(problem: Dict[str, Any], task_id_to_name: Dict[str, str]) -> str:
    """
    获取问题对应的任务名称
    
    Args:
        problem: 问题记录
        task_id_to_name: 任务ID到名称的映射
        
    Returns:
        任务名称
    """
    # 尝试多种可能的任务ID字段名
    regression_task_id = None
    
    # 检查可能的字段名
    possible_fields = ['regression_task_id', 'task_id', 'analysis_task_id']
    for field in possible_fields:
        if field in problem and problem[field]:
            regression_task_id = str(problem[field])  # 确保转换为字符串
            break
    
    if regression_task_id:
        # 直接匹配
        if regression_task_id in task_id_to_name:
            return task_id_to_name[regression_task_id]
        
        # 如果直接匹配失败，尝试字符串化匹配
        for task_id, task_name in task_id_to_name.items():
            if str(task_id) == str(regression_task_id):
                return task_name
    
    # 如果都没有匹配到，返回默认值
    return f"未关联任务(ID: {regression_task_id})" if regression_task_id else "未关联任务"


def build_function_info_string(mapping: Any) -> str:
    """
    构建函数信息字符串
    
    Args:
        mapping: 映射记录
        
    Returns:
        函数信息字符串
    """
    info_parts = []
    
    # 函数名和文件路径
    info_parts.append(f"函数名：{mapping.function_name}")
    info_parts.append(f"文件：{mapping.file_path}")
    info_parts.append(f"变更类型：{mapping.change_type}")
    
    # 代码差异
    if mapping.old_code and mapping.new_code:
        info_parts.append(f"旧版本代码：\n{mapping.old_code[:200]}...")
        info_parts.append(f"新版本代码：\n{mapping.new_code[:200]}...")
    elif mapping.new_code:
        info_parts.append(f"新增代码：\n{mapping.new_code[:200]}...")
    elif mapping.old_code:
        info_parts.append(f"删除代码：\n{mapping.old_code[:200]}...")
    
    # 映射信息
    if mapping.diff_summary:
        info_parts.append(f"变更摘要：{mapping.diff_summary}")
    
    return "\n".join(info_parts)
