"""
任务恢复执行模块

提供暂停任务的恢复执行功能，从上次中断的位置继续处理
"""
import os
import glob
from typing import List, Dict, Set
from sqlalchemy.orm import Session

from ...config_database import get_db
from ...db.repository.task_repo import TaskRepository
from ...db.repository.file_repo import FileRepository
from ...db.repository.function_repo import FunctionRepository
from ...db.repository.problem_repo import ProblemRepository
from ...utils.logger import log_info, log_warning, log_error
from ...config import ALLOWED_CODE_EXTENSIONS, FPGA_CODE_EXTENSIONS, get_file_type
from .parser import function_parser as fp
from .parser.global_var_parser import extract_globals_from_code, extract_macros_from_code, extract_arrays_from_code
from .analysis_runner import (
    _process_functions_concurrently,
    identify_project_type,
    _process_single_fpga_file_with_new_db
)


def resume_task_execution(task_id: int, code_file_id: int):
    """
    恢复暂停任务的执行
    
    Args:
        task_id: 任务ID
        code_file_id: 代码文件ID
    """
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        log_info(f"[任务恢复] 开始恢复任务执行: task_id={task_id}", "task_resume")
        
        task_repo = TaskRepository(db)
        file_repo = FileRepository(db)
        func_repo = FunctionRepository(db)
        prob_repo = ProblemRepository(db)
        
        # 获取任务信息
        task = task_repo.get_task(task_id)
        if not task:
            log_error(f"[任务恢复] 任务不存在: task_id={task_id}", "task_resume")
            return
        
        # 获取代码文件信息
        code_file = file_repo.get_file(code_file_id)
        if not code_file:
            log_error(f"[任务恢复] 代码文件不存在: file_id={code_file_id}", "task_resume")
            task_repo.update_task_status(task_id, "failed")
            db.commit()
            return
        
        extract_path = code_file.extract_path
        
        # 识别项目类型
        project_type = identify_project_type(extract_path)
        log_info(f"[任务恢复] 项目类型: {project_type}", "task_resume")
        
        # 根据项目类型选择恢复策略
        if project_type == "fpga":
            resume_fpga_task(task_id, extract_path, db, task_repo, file_repo)
        else:
            resume_c_cpp_task(task_id, extract_path, db, task_repo, file_repo, func_repo, prob_repo)
        
        log_info(f"[任务恢复] 任务恢复执行完成: task_id={task_id}", "task_resume")
        
    except Exception as e:
        log_error(f"[任务恢复] 任务恢复执行失败: task_id={task_id}", "task_resume", e)
        try:
            task_repo = TaskRepository(db)
            task_repo.update_task_status(task_id, "failed")
            db.commit()
        except:
            pass
    finally:
        db.close()


def _normalize_func_key(extract_path: str, file_path: str, function_name: str):
    """统一函数路径匹配的 key，避免绝对路径/相对路径、大小写等差异导致的匹配失败。"""
    try:
        base_path = file_path or ""
        if not os.path.isabs(base_path):
            base_path = os.path.join(extract_path, base_path)
        rel_path = os.path.relpath(base_path, extract_path)
    except Exception:
        rel_path = file_path or ""

    # 使用规范化路径 + 小写，提升匹配鲁棒性（主要针对 Windows）
    norm_rel_path = os.path.normcase(os.path.normpath(rel_path))
    return (norm_rel_path, function_name)


def resume_c_cpp_task(
    task_id: int,
    extract_path: str,
    db: Session,
    task_repo: TaskRepository,
    file_repo: FileRepository,
    func_repo: FunctionRepository,
    prob_repo: ProblemRepository
):
    """
    恢复C/C++项目任务
    
    Args:
        task_id: 任务ID
        extract_path: 代码解压路径
        db: 数据库会话
        task_repo: 任务仓储
        file_repo: 文件仓储
        func_repo: 函数仓储
        prob_repo: 问题仓储
    """
    try:
        log_info(f"[C/C++恢复] 开始恢复C/C++任务: task_id={task_id}", "task_resume")

        # 0. 记录恢复前任务进度
        task_before = task_repo.get_task(task_id)
        original_progress = getattr(task_before, "progress", None)
        log_info(
            f"[C/C++恢复] 恢复前任务进度: {original_progress}",
            "task_resume"
        )
        
        # 1. 获取已处理的函数列表，并统一路径格式
        processed_functions = func_repo.get_functions_by_task(task_id)
        processed_function_set = {
            _normalize_func_key(extract_path, f.file_path, f.function_name)
            for f in processed_functions
        }
        
        processed_count = len(processed_function_set)
        log_info(
            f"[C/C++恢复] 已处理函数数量: {processed_count}",
            "task_resume"
        )
        
        # 2. 重新扫描项目，获取所有函数
        all_functions = scan_all_c_cpp_functions(extract_path)
        total_function_count = len(all_functions)
        
        log_info(
            f"[C/C++恢复] 项目总函数数量: {total_function_count}",
            "task_resume"
        )
        
        # 3. 过滤出未处理的函数（使用统一后的路径 key）
        remaining_functions = [
            f for f in all_functions
            if _normalize_func_key(extract_path, f['file_path'], f['function_name']) not in processed_function_set
        ]
        remaining_count = len(remaining_functions)
        
        log_info(
            f"[C/C++恢复] 剩余未处理函数: {remaining_count}",
            "task_resume"
        )

        # 3.1 记录理论进度（仅用于日志观测，不修改实际进度）
        if total_function_count > 0:
            theoretical_progress = round(processed_count * 100 / total_function_count, 2)
        else:
            theoretical_progress = None
        log_info(
            f"[C/C++恢复] 理论进度(根据函数数推算): {theoretical_progress}",
            "task_resume"
        )
        
        if not remaining_functions:
            log_info(f"[C/C++恢复] 所有函数已处理完成，更新任务状态", "task_resume")
            task_repo.update_task_status(task_id, "completed")
            task_repo.update_task_progress(task_id, 100)
            db.commit()
            return
        
        # 4. 重新扫描全局变量
        all_global_vars = scan_global_variables(extract_path)
        
        log_info(
            f"[C/C++恢复] 全局变量数量: {len(all_global_vars)}",
            "task_resume"
        )
        
        # 5. 获取或创建文件记录
        # 🔧 修复：通过 task_id 查询 files 表，而不是从 task 对象获取不存在的 file_id
        existing_files = file_repo.get_files_by_task(task_id)
        
        if existing_files:
            # 使用已存在的文件记录
            file_id = existing_files[0].id
            log_info(
                f"[C/C++恢复] 找到已存在的文件记录: file_id={file_id}",
                "task_resume"
            )
        else:
            # 创建新文件记录
            log_info(
                f"[C/C++恢复] 未找到文件记录，创建新记录",
                "task_resume"
            )
            file_data = {
                "task_id": task_id,
                "file_name": os.path.basename(extract_path),
                "file_path": extract_path,
                "extract_path": extract_path,
                "status": "processing"
            }
            db_file = file_repo.create_file(file_data)
            db.commit()  # ✅ 确保提交到数据库
            file_id = db_file.id
            log_info(
                f"[C/C++恢复] 新文件记录已创建: file_id={file_id}",
                "task_resume"
            )
        
        # 6. 继续处理剩余函数
        log_info(
            f"[C/C++恢复] 开始处理剩余 {remaining_count} 个函数 (task_id={task_id}, file_id={file_id})",
            "task_resume"
        )
        
        # 在并发处理时传入已处理函数数量和项目总函数数，保证进度从暂停点继续
        _process_functions_concurrently(
            remaining_functions,
            file_id,
            task_id,
            db,
            extract_path,
            all_global_vars,
            func_repo,
            prob_repo,
            task_repo,
            already_processed_count=processed_count,
            total_project_functions=total_function_count,
        )

        # 6.1 记录并发处理完成后的任务进度，用于对比
        task_after = task_repo.get_task(task_id)
        final_progress = getattr(task_after, "progress", None)
        log_info(
            f"[C/C++恢复] 并发处理后任务进度: {final_progress}",
            "task_resume"
        )
        
        # 7. 更新任务状态为完成
        # 统计并更新问题总数
        total_problems = task_repo.update_task_total_problems(task_id)
        log_info(f"[C/C++恢复] 任务 {task_id} 问题总数统计完成: {total_problems} 个问题", "task_resume")
        
        task_repo.update_task_status(task_id, "completed")
        task_repo.update_task_progress(task_id, 100)
        db.commit()
        
        log_info(f"[C/C++恢复] C/C++任务恢复完成: task_id={task_id}", "task_resume")
        
    except Exception as e:
        log_error(f"[C/C++恢复] C/C++任务恢复失败: task_id={task_id}", "task_resume", e)
        task_repo.update_task_status(task_id, "failed")
        db.commit()
        raise


def resume_fpga_task(
    task_id: int,
    extract_path: str,
    db: Session,
    task_repo: TaskRepository,
    file_repo: FileRepository
):
    """
    恢复FPGA项目任务
    
    Args:
        task_id: 任务ID
        extract_path: 代码解压路径
        db: 数据库会话
        task_repo: 任务仓储
        file_repo: 文件仓储
    """
    try:
        log_info(f"[FPGA恢复] 开始恢复FPGA任务: task_id={task_id}", "task_resume")
        
        # 1. 获取已处理的文件列表
        from ...db.models.file import AnalysisFile
        processed_files = db.query(AnalysisFile).filter(
            AnalysisFile.task_id == task_id,
            AnalysisFile.status == 'completed'
        ).all()
        
        processed_file_paths = {f.file_path for f in processed_files}
        
        log_info(
            f"[FPGA恢复] 已处理文件数量: {len(processed_file_paths)}",
            "task_resume"
        )
        
        # 2. 扫描所有FPGA文件
        all_fpga_files = []
        for ext in FPGA_CODE_EXTENSIONS:
            files = glob.glob(f"{extract_path}/**/*{ext}", recursive=True)
            all_fpga_files.extend(files)
        
        log_info(
            f"[FPGA恢复] 项目总FPGA文件数量: {len(all_fpga_files)}",
            "task_resume"
        )
        
        # 3. 过滤出未处理的文件
        remaining_files = [
            f for f in all_fpga_files
            if f not in processed_file_paths
        ]
        
        log_info(
            f"[FPGA恢复] 剩余未处理文件: {len(remaining_files)}",
            "task_resume"
        )
        
        if not remaining_files:
            log_info(f"[FPGA恢复] 所有文件已处理完成，更新任务状态", "task_resume")
            # 统计并更新问题总数
            total_problems = task_repo.update_task_total_problems(task_id)
            log_info(f"[FPGA恢复] 任务 {task_id} 问题总数统计完成: {total_problems} 个问题", "task_resume")
            task_repo.update_task_status(task_id, "completed")
            task_repo.update_task_progress(task_id, 100)
            db.commit()
            return
        
        # 4. 继续处理剩余文件
        # 注意：FPGA文件处理逻辑较复杂，这里简化处理
        log_info(f"[FPGA恢复] 开始处理剩余 {len(remaining_files)} 个文件", "task_resume")
        
        # 这里需要调用FPGA文件处理逻辑
        # 由于FPGA处理逻辑较复杂，建议直接重新处理所有未完成的文件
        
        # 更新任务状态
        # 统计并更新问题总数
        total_problems = task_repo.update_task_total_problems(task_id)
        log_info(f"[FPGA恢复] 任务 {task_id} 问题总数统计完成: {total_problems} 个问题", "task_resume")
        task_repo.update_task_status(task_id, "completed")
        task_repo.update_task_progress(task_id, 100)
        db.commit()
        
        log_info(f"[FPGA恢复] FPGA任务恢复完成: task_id={task_id}", "task_resume")
        
    except Exception as e:
        log_error(f"[FPGA恢复] FPGA任务恢复失败: task_id={task_id}", "task_resume", e)
        task_repo.update_task_status(task_id, "failed")
        db.commit()
        raise


def scan_all_c_cpp_functions(extract_path: str) -> List[Dict]:
    """
    扫描项目中所有C/C++函数
    
    Args:
        extract_path: 代码解压路径
        
    Returns:
        函数列表
    """
    all_functions = []
    
    # 扫描所有C/C++文件
    for ext in ALLOWED_CODE_EXTENSIONS:
        files = glob.glob(f"{extract_path}/**/*{ext}", recursive=True)
        # 🔧 修复：对文件列表排序，确保每次审查顺序一致
        files.sort()
        
        for file_path in files:
            try:
                # 读取文件内容（返回内容和编码）
                from .parser.function_parser import read_file_with_encoding
                code, _ = read_file_with_encoding(file_path)
                
                if not code:
                    continue
                
                # 使用与主分析流程一致的语言判定逻辑
                raw_lang = get_file_type(file_path) or "c"
                # project_scanner 返回的 c_cpp 需要映射为 tree-sitter 支持的 c
                lang = "c" if raw_lang == "c_cpp" else raw_lang
                
                # 提取函数
                functions = fp.extract_functions_from_code(code, lang)
                
                # 🔧 修复：转换为相对路径，确保与正常任务启动时的格式一致
                rel_path = os.path.relpath(file_path, extract_path)
                
                for func in functions:
                    # 兼容 tree-sitter/正则两种返回结构
                    func_name = func.get('function_name') or func.get('name')
                    if not func_name:
                        continue
                    all_functions.append({
                        'function_name': func_name,
                        'source_code': func.get('source_code') or func.get('code', ''),
                        'file_path': rel_path,  # ✅ 使用相对路径
                        'start_line': func.get('start_line'),
                        'end_line': func.get('end_line')
                    })
                    
            except Exception as e:
                log_warning(f"扫描文件失败: {file_path}, error: {e}", "scan_functions")
                continue
    
    return all_functions


def scan_global_variables(extract_path: str) -> Dict:
    """
    扫描项目中所有全局变量
    
    Args:
        extract_path: 代码解压路径
        
    Returns:
        全局变量字典
    """
    all_global_vars = {}
    
    # 扫描所有C/C++文件
    for ext in ALLOWED_CODE_EXTENSIONS:
        files = glob.glob(f"{extract_path}/**/*{ext}", recursive=True)
        # 🔧 修复：对文件列表排序，确保每次审查顺序一致
        files.sort()
        
        for file_path in files:
            try:
                from .parser.function_parser import read_file_with_encoding
                code, _ = read_file_with_encoding(file_path)
                
                if not code:
                    continue

                # 使用与主分析流程一致的语言判定逻辑
                raw_lang = get_file_type(file_path) or "c"
                lang = "c" if raw_lang == "c_cpp" else raw_lang

                # 统一使用相对路径，便于日志与主流程对齐
                try:
                    rel_path = os.path.relpath(file_path, extract_path)
                except Exception:
                    rel_path = file_path
                
                # 提取全局变量
                globals_list = extract_globals_from_code(code, language=lang)
                for g_var in globals_list:
                    var_name = g_var.get("name")
                    if not var_name:
                        continue
                    if var_name not in all_global_vars:
                        all_global_vars[var_name] = {
                            "file": rel_path,
                            "line": g_var.get("line"),
                            "code": g_var.get("code"),
                            "type": "variable",
                        }
                
                # 提取宏定义
                macros_list = extract_macros_from_code(code, language=lang)
                for macro in macros_list:
                    macro_name = macro.get("name")
                    if not macro_name or macro_name in all_global_vars:
                        continue
                    all_global_vars[macro_name] = {
                        "file": rel_path,
                        "line": macro.get("line"),
                        "code": macro.get("code"),
                        "type": "macro",
                    }
                
                # 提取数组
                arrays_list = extract_arrays_from_code(code, language=lang)
                for array in arrays_list:
                    array_name = array.get("name")
                    if not array_name or array_name in all_global_vars:
                        continue
                    all_global_vars[array_name] = {
                        "file": rel_path,
                        "line": array.get("line"),
                        "code": array.get("code"),
                        "type": "array",
                    }
                
            except Exception as e:
                log_warning(f"扫描全局变量失败: {file_path}, error: {e}", "scan_globals")
                continue
    
    return all_global_vars
