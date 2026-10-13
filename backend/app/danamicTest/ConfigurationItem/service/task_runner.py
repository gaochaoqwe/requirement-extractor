"""
动态测试-配置项测试任务执行器
负责异步执行表单生成任务并记录详细日志
"""
import uuid
import asyncio
import time
from typing import Dict, Any, Callable
from pathlib import Path

from ..utils.logging_utils.logger import set_current_task, log_info, log_error, log_warning, finalize_task_log
from ..utils.logging_utils.performance_monitor import start_task_monitoring, end_task_monitoring, monitor_step, ConfigurationTestSteps
from ..main import ConfigurationTestManager

# 全局任务状态存储
task_status = {}

def clear_all_tasks():
    """清理所有任务状态（服务重启时调用）"""
    global task_status
    task_status.clear()
    # log_info("已清理所有任务状态", "task_manager")

def generate_task_id() -> str:
    """生成唯一的任务ID"""
    return str(uuid.uuid4())

def update_task_progress(task_id: str, progress: int, message: str):
    """
    更新任务进度的辅助函数
    
    Args:
        task_id: 任务ID
        progress: 进度百分比 (0-100)
        message: 进度消息
    """
    if task_id in task_status:
        task_status[task_id]["progress"] = progress
        task_status[task_id]["message"] = message
        # log_info(f"任务进度更新: {progress}% - {message}", "task_manager")

def run_form_generation_task(
    session_id: str,
    basic_info: Dict[str, Any],
    ai_analysis: bool = True,
    deep_analysis: bool = True,
    task_id: str = None
) -> str:
    """
    执行表单生成任务（后台任务）
    
    Args:
        session_id: 会话ID
        basic_info: 基本信息
        ai_analysis: 是否启用AI分析
        deep_analysis: 是否启用深度分析
        task_id: 任务ID（如果未提供则生成新的）
        
    Returns:
        str: 任务ID
    """
    # 使用提供的任务ID或生成新的任务ID
    if task_id is None:
        task_id = generate_task_id()
    
    # 初始化任务状态
    task_status[task_id] = {
        "status": "running",
        "progress": 0,
        "message": "任务初始化中...",
        "session_id": session_id,
        "start_time": None,
        "end_time": None,
        "generated_files": [],
        "error": None
    }
    
    try:
        # 设置当前任务日志
        set_current_task(task_id, session_id)
        # log_info(f"开始执行动态测试表单生成任务", "task_manager")
        # log_info(f"任务参数: session_id={session_id}, ai_analysis={ai_analysis}, deep_analysis={deep_analysis}", "task_manager")
        
        # 启动性能监控
        start_task_monitoring("配置项测试任务")
        
        # 更新任务状态
        task_status[task_id]["start_time"] = str(time.time())
        update_task_progress(task_id, 5, "正在初始化配置项测试管理器...")
        
        # 创建配置项测试管理器
        with monitor_step(ConfigurationTestSteps.INIT, "创建配置项测试管理器"):
            # log_info("创建配置项测试管理器", "task_manager")
            config_manager = ConfigurationTestManager()
        
        # 更新进度
        update_task_progress(task_id, 15, "正在验证会话和文件...")
        
        # 验证会话目录是否存在
        with monitor_step(ConfigurationTestSteps.VALIDATE_INPUT, "验证会话目录和输入文件"):
            # 修复路径指向backend目录下的uploads
            backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
            session_dir = backend_dir / "uploads" / "dynamic" / "configuration" / session_id
            if not session_dir.exists():
                raise FileNotFoundError(f"会话目录不存在: {session_dir}")
            
            # log_info(f"会话目录验证通过: {session_dir}", "task_manager")
        
        # 🚀 新增：检查标准化文档状态
        update_task_progress(task_id, 20, "正在检查标准化文档状态...")
        
        # 导入标准化管理器
        from ..utils.standardization_manager import get_standardization_manager
        standardization_manager = get_standardization_manager()
        
        # 获取标准化进度信息
        progress_info = standardization_manager.get_standardization_progress_info(session_id)
        log_info(f"标准化状态: {progress_info}", "task_manager")
        
        # 如果标准化正在进行中，等待一段时间
        if progress_info.get('status') == 'processing':
            update_task_progress(task_id, 22, "标准化正在进行中，等待完成...")
            log_info("检测到标准化正在进行中，等待3分钟...", "task_manager")
            
            # 等待标准化完成（最多3分钟）
            # 修复路径指向backend目录下的uploads
            backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
            session_dir = backend_dir / "uploads" / "dynamic" / "configuration" / session_id
            requirement_file = None
            for req_file in session_dir.glob("requirement_*"):
                requirement_file = str(req_file)
                break
            
            if requirement_file:
                # 🔧 修复：使用同步方法等待标准化
                wait_timeout = 180  # 3分钟
                start_time = time.time()
                check_interval = 5  # 每5秒检查一次
                
                while time.time() - start_time < wait_timeout:
                    # 检查是否已有标准化文档
                    standardized_path = standardization_manager.get_standardized_document_path(
                        session_id, requirement_file
                    )
                    if standardized_path:
                        log_info(f"等待成功，将使用标准化文档: {standardized_path}", "task_manager")
                        break
                    
                    # 检查标准化状态
                    current_status = standardization_manager._get_standardization_status(session_id)
                    if current_status:
                        if current_status.get('status') == 'completed':
                            # 再次检查文件
                            standardized_path = standardization_manager.get_standardized_document_path(
                                session_id, requirement_file
                            )
                            if standardized_path:
                                log_info(f"标准化完成，使用标准化文档: {standardized_path}", "task_manager")
                                break
                        elif current_status.get('status') == 'failed':
                            log_info("标准化失败，将使用原始文档继续处理", "task_manager")
                            break
                    
                    # 更新进度显示
                    elapsed = time.time() - start_time
                    remaining = wait_timeout - elapsed
                    update_task_progress(task_id, 22, f"等待标准化完成... ({remaining:.0f}秒)")
                    
                    # 等待后重试
                    time.sleep(check_interval)
                
                # 检查最终结果
                final_standardized_path = standardization_manager.get_standardized_document_path(
                    session_id, requirement_file
                )
                if not final_standardized_path:
                    log_info("等待超时，将使用原始文档继续处理", "task_manager")
        
        update_task_progress(task_id, 25, "正在分析需求文档...")
        
        # 创建进度更新回调函数
        def progress_callback(progress: int, message: str):
            """进度更新回调函数"""
            # 将内部进度映射到25%-85%的范围
            mapped_progress = 25 + int((progress / 100) * 60)
            update_task_progress(task_id, mapped_progress, message)
        
        # 调用表单生成
        with monitor_step(ConfigurationTestSteps.BUILD_FORMS, "执行完整表单生成流程"):
            # log_info("开始调用配置项测试管理器生成表单", "task_manager")
            result = config_manager.generate_complete_forms(
                session_id=session_id,
                basic_info=basic_info,
                ai_analysis=ai_analysis,
                deep_analysis=deep_analysis,
                task_id=task_id,
                progress_callback=progress_callback  # 传递进度回调
            )
        
        # 更新进度
        update_task_progress(task_id, 90, "正在整理生成结果...")
        
        with monitor_step(ConfigurationTestSteps.SAVE_RESULTS, "整理和保存生成结果"):
            # log_info(f"表单生成完成，结果: {result}", "task_manager")
            pass
        
        # 更新最终状态
        task_status[task_id]["status"] = "completed"
        task_status[task_id]["progress"] = 100
        task_status[task_id]["message"] = "任务完成"
        task_status[task_id]["end_time"] = str(time.time())
        task_status[task_id]["generated_files"] = result.get("generated_files", [])
        
        # log_info("动态测试表单生成任务完成", "task_manager")
        
        # 结束性能监控
        end_task_monitoring("配置项测试任务")
        
    except Exception as e:
        # log_error(f"表单生成任务失败", "task_manager", e)
        
        # 更新错误状态
        task_status[task_id]["status"] = "failed"
        task_status[task_id]["progress"] = 0
        task_status[task_id]["message"] = f"任务失败: {str(e)}"
        task_status[task_id]["error"] = str(e)
        task_status[task_id]["end_time"] = str(time.time())
        
    finally:
        # 完成日志记录
        finalize_task_log()
    
    return task_id

def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        Dict[str, Any]: 任务状态信息
    """
    return task_status.get(task_id, {
        "status": "not_found",
        "progress": 0,
        "message": "任务不存在",
        "error": "Task not found"
    })

def cleanup_completed_tasks():
    """
    清理已完成的任务状态（可选，用于内存管理）
    """
    completed_tasks = [
        task_id for task_id, status in task_status.items()
        if status["status"] in ["completed", "failed"]
    ]
    
    # 保留最近100个任务，清理更早的任务
    if len(completed_tasks) > 100:
        tasks_to_remove = completed_tasks[:-100]
        for task_id in tasks_to_remove:
            del task_status[task_id]
            log_info(f"清理任务状态: {task_id}", "task_manager")


# ============================================================================
# 分步生成任务函数
# ============================================================================

def run_step1_project_info_task(
    session_id: str,
    basic_info: Dict[str, Any],
    optional_info: Dict[str, Any],
    code_lines: int = None,
    task_id: str = None
) -> str:
    """
    步骤1: 生成项目信息表（项目基本信息 + 软件配置项信息）
    
    Args:
        session_id: 会话ID
        basic_info: 基本信息
        optional_info: 可选信息
        code_lines: 代码行数
        task_id: 任务ID
        
    Returns:
        任务ID
    """
    import shutil
    import openpyxl
    
    if task_id is None:
        task_id = generate_task_id()
    
    # 初始化任务状态
    task_status[task_id] = {
        "status": "running",
        "progress": 0,
        "message": "步骤1初始化中...",
        "session_id": session_id,
        "start_time": str(time.time()),
        "end_time": None,
        "generated_files": [],
        "error": None
    }
    
    try:
        set_current_task(task_id, session_id)
        log_info(f"========== 开始执行步骤1: 生成项目信息表 ==========", "task_manager")
        log_info(f"任务ID: {task_id}, 会话ID: {session_id}", "task_manager")
        log_info(f"基本信息: {basic_info}", "task_manager")
        log_info(f"可选信息: {optional_info}", "task_manager")
        log_info(f"代码行数: {code_lines}", "task_manager")
        
        # 导入状态管理器
        from .state_manager import GenerationStateManager
        
        # 获取会话目录
        backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
        session_dir = backend_dir / "uploads" / "dynamic" / "configuration" / session_id
        log_info(f"会话目录: {session_dir}", "task_manager")
        
        if not session_dir.exists():
            error_msg = f"会话目录不存在: {session_dir}"
            log_error(error_msg, "task_manager")
            raise FileNotFoundError(error_msg)
        
        # 初始化状态管理器
        state_manager = GenerationStateManager(session_dir)
        
        # 检查是否可以开始步骤1
        can_start, reason = state_manager.can_start_step("step1_project_info")
        if not can_start:
            raise ValueError(f"无法开始步骤1: {reason}")
        
        update_task_progress(task_id, 10, "正在准备Excel文件...")
        
        # 导入资源管理器
        from ..resources.resource_manager import ResourceManager
        resource_manager = ResourceManager()
        
        # 准备Excel模板
        template_file = resource_manager.get_template_path('需求分析表(精准测试工具生成).xlsx')
        output_dir = session_dir / "output"
        output_dir.mkdir(exist_ok=True)
        
        excel_file_path = output_dir / '项目信息表.xlsx'
        
        # 复制模板文件
        shutil.copy2(template_file, excel_file_path)
        
        update_task_progress(task_id, 20, "正在填充项目基本信息表...")
        
        # 合并基本信息和可选信息
        full_info = {**basic_info, **optional_info}
        if code_lines:
            full_info['code_lines'] = code_lines
        
        # 导入填充器
        from .project_info.service import ProjectInfoService
        from .software_config.service import SoftwareConfigService
        from .form_builder.table_fillers.project_info_table_filler import ProjectInfoTableFiller
        from .form_builder.table_fillers.software_config_table_filler import SoftwareConfigTableFiller
        
        # 初始化服务和填充器
        project_info_service = ProjectInfoService()
        software_config_service = SoftwareConfigService()
        project_info_filler = ProjectInfoTableFiller(project_info_service)
        software_config_filler = SoftwareConfigTableFiller(software_config_service)
        
        # 准备参数
        zhuguan_name = basic_info.get('test_manager', '')
        ceshiren_name = basic_info.get('test_personnel', '')
        kaifarenxinxi = [
            basic_info.get('developer', ''),
            basic_info.get('development_department', '')
        ]
        xinghao_xinxi_list = None  # 暂时为None，后续可以从配置中获取
        
        # 准备软件信息字典
        ruanjian_xinxi_duqu_temp = {}
        ruanjian_name = basic_info.get('software_name', '')
        
        # 填充项目基本信息表
        success = project_info_filler.fill_project_info_table(
            excel_file_path=str(excel_file_path),
            sheet_name='项目基本信息',
            ruanjian_xinxi_duqu_temp=ruanjian_xinxi_duqu_temp,
            ruanjian_name=ruanjian_name,
            zhuguan_name=zhuguan_name,
            ceshiren_name=ceshiren_name,
            kaifarenxinxi=kaifarenxinxi,
            xinghao_xinxi_list=xinghao_xinxi_list,
            user_software_info=full_info
        )
        
        if not success:
            raise Exception("项目基本信息表填充失败")
        
        update_task_progress(task_id, 60, "正在填充软件配置项信息表...")
        
        # 准备软件配置项所需参数
        suoshulingyu = full_info.get('domain', '通用领域')
        
        # 填充软件配置项信息表
        success = software_config_filler.fill_software_config_table(
            excel_file_path=str(excel_file_path),
            sheet_name='软件配置项信息',
            ruanjian_xinxi_duqu_temp=ruanjian_xinxi_duqu_temp,
            ruanjian_name=ruanjian_name,
            kaifarenxinxi=kaifarenxinxi,
            suoshulingyu=suoshulingyu,
            xinghao_xinxi_list=xinghao_xinxi_list,
            zhuguan_name=zhuguan_name,
            ceshiren_name=ceshiren_name,
            user_software_info=full_info,
            code_lines=code_lines
        )
        
        if not success:
            raise Exception("软件配置项信息表填充失败")
        
        update_task_progress(task_id, 90, "正在更新状态...")
        
        # 收集生成的文件
        generated_files = ['项目信息表.xlsx']  # 两个sheet都在同一个Excel文件中
        
        # 更新状态文件
        state_manager.update_step_status(
            step_name="step1_project_info",
            completed=True,
            output_files=generated_files,
            task_id=task_id
        )
        
        # 更新任务状态
        task_status[task_id]["status"] = "completed"
        task_status[task_id]["progress"] = 100
        task_status[task_id]["message"] = "步骤1完成"
        task_status[task_id]["end_time"] = str(time.time())
        task_status[task_id]["generated_files"] = generated_files
        
        log_info(f"步骤1完成，生成文件: {generated_files}", "task_manager")
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        log_error(f"========== 步骤1执行失败 ==========", "task_manager", e)
        log_error(f"错误类型: {type(e).__name__}", "task_manager")
        log_error(f"错误消息: {str(e)}", "task_manager")
        log_error(f"错误详情:\n{error_detail}", "task_manager")
        
        # 更新错误状态
        task_status[task_id]["status"] = "failed"
        task_status[task_id]["progress"] = 0
        task_status[task_id]["message"] = f"步骤1失败: {str(e)}"
        task_status[task_id]["error"] = str(e)
        task_status[task_id]["end_time"] = str(time.time())
        
        # 更新状态文件
        try:
            from .state_manager import GenerationStateManager
            backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
            session_dir = backend_dir / "uploads" / "dynamic" / "configuration" / session_id
            state_manager = GenerationStateManager(session_dir)
            state_manager.update_step_status(
                step_name="step1_project_info",
                completed=False,
                task_id=task_id,
                error=str(e)
            )
            log_info(f"步骤1错误状态已保存到状态文件", "task_manager")
        except Exception as state_error:
            log_error(f"保存错误状态失败: {str(state_error)}", "task_manager")
    
    finally:
        finalize_task_log()
    
    return task_id


def run_step2_test_issue_task(
    session_id: str,
    task_id: str = None
) -> str:
    """
    步骤2: 在用户上传的Excel上添加策划表与问题单sheet
    
    Args:
        session_id: 会话ID
        task_id: 任务ID
        
    Returns:
        任务ID
    """
    import shutil
    import openpyxl
    
    if task_id is None:
        task_id = generate_task_id()
    
    # 初始化任务状态
    task_status[task_id] = {
        "status": "running",
        "progress": 0,
        "message": "步骤2初始化中...",
        "session_id": session_id,
        "start_time": str(time.time()),
        "end_time": None,
        "generated_files": [],
        "error": None
    }
    
    try:
        set_current_task(task_id, session_id)
        log_info(f"========== 开始执行步骤2: 生成策划表与问题单 ==========", "task_manager")
        log_info(f"任务ID: {task_id}, 会话ID: {session_id}", "task_manager")
        
        # 导入状态管理器
        from .state_manager import GenerationStateManager
        
        # 获取会话目录
        backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
        session_dir = backend_dir / "uploads" / "dynamic" / "configuration" / session_id
        log_info(f"会话目录: {session_dir}", "task_manager")
        
        if not session_dir.exists():
            error_msg = f"会话目录不存在: {session_dir}"
            log_error(error_msg, "task_manager")
            raise FileNotFoundError(error_msg)
        
        # 初始化状态管理器
        state_manager = GenerationStateManager(session_dir)
        state = state_manager.load_state()
        
        # 检查是否可以开始步骤2
        can_start, reason = state_manager.can_start_step("step2_test_issue")
        if not can_start:
            raise ValueError(f"无法开始步骤2: {reason}")
        
        update_task_progress(task_id, 10, "正在获取用户上传的Excel文件...")
        
        # 获取用户上传的Excel文件
        uploaded_file = state.get("step2_uploaded_file")
        if not uploaded_file or not Path(uploaded_file).exists():
            raise FileNotFoundError("未找到用户上传的项目信息表，请先上传")
        
        log_info(f"使用用户上传的Excel: {uploaded_file}", "task_manager")
        
        update_task_progress(task_id, 20, "正在复制文件到输出目录...")
        
        # 复制到output目录（保留用户修改的内容）
        output_dir = session_dir / "output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "完整表单.xlsx"
        shutil.copy2(uploaded_file, output_file)
        log_info(f"文件已复制到: {output_file}", "task_manager")
        
        update_task_progress(task_id, 30, "正在获取基本信息和目录数据...")
        
        # 获取基本信息和目录数据
        basic_info = state_manager.get_basic_info()
        catalog_items = state_manager.get_catalog_items()
        
        log_info(f"基本信息: {basic_info}", "task_manager")
        log_info(f"目录项数量: {len(catalog_items)}", "task_manager")
        
        # 从catalog_items重建requirements_dict
        requirements_dict = {
            item.get('name', ''): item.get('description', f"验证{item.get('name', '')}功能")
            for item in catalog_items
            if item.get('name')
        }
        log_info(f"需求字典数量: {len(requirements_dict)}", "task_manager")
        
        update_task_progress(task_id, 50, "正在填充项目策划表sheet...")
        
        # 导入填充器
        from .project_plan.service import ConfigurationItemProjectPlanService
        from .issue_report.service import ConfigurationItemIssueReportService
        from .form_builder.table_fillers.project_plan_table_filler import ProjectPlanTableFiller
        from .form_builder.table_fillers.issue_report_table_filler import IssueReportTableFiller
        
        # 初始化服务
        project_plan_service = ConfigurationItemProjectPlanService()
        issue_report_service = ConfigurationItemIssueReportService()
        project_plan_filler = ProjectPlanTableFiller(project_plan_service)
        issue_report_filler = IssueReportTableFiller(issue_report_service)
        
        # 填充项目策划表sheet（在已存在的sheet上填充数据）
        success = project_plan_filler.fill_project_plan_table(
            excel_file_path=str(output_file),
            sheet_name='项目策划表',
            ruanjian_name=basic_info.get('software_name', ''),
            xinghao_xinxi_list=None,
            total_lines=basic_info.get('code_lines', 1000),
            zhuguan_name=basic_info.get('test_manager', ''),
            ceshiren_name=basic_info.get('test_personnel', ''),
            requirement_names=list(requirements_dict.keys()),
            requirements_dict=requirements_dict
        )
        
        if not success:
            raise Exception("项目策划表填充失败")
        
        log_info("项目策划表sheet填充成功", "task_manager")
        
        update_task_progress(task_id, 80, "正在填充问题报告单sheet...")
        
        # 填充问题报告单sheet（在已存在的sheet上填充数据）
        success = issue_report_filler.fill_issue_report_table(
            excel_file_path=str(output_file),
            sheet_name='问题报告单',
            ruanjian_xinxi_duqu_temp={},
            ruanjian_name=basic_info.get('software_name', ''),
            zhuguan_name=basic_info.get('test_manager', ''),
            ceshiren_name=basic_info.get('test_personnel', ''),
            kaifarenxinxi=[
                basic_info.get('developer', ''),
                basic_info.get('development_department', '')
            ],
            suoshulingyu=basic_info.get('domain', '通用领域'),
            apply_formatting=True
        )
        
        if not success:
            raise Exception("问题报告单填充失败")
        
        log_info("问题报告单sheet填充成功", "task_manager")
        
        update_task_progress(task_id, 95, "正在更新状态...")
        
        # 收集生成的文件（保持用户上传的文件名或使用统一名称）
        generated_files = ['完整表单.xlsx']
        
        # 更新状态文件
        state_manager.update_step_status(
            step_name="step2_test_issue",
            completed=True,
            output_files=generated_files,
            task_id=task_id
        )
        
        # 更新任务状态
        task_status[task_id]["status"] = "completed"
        task_status[task_id]["progress"] = 100
        task_status[task_id]["message"] = "步骤2完成"
        task_status[task_id]["end_time"] = str(time.time())
        task_status[task_id]["generated_files"] = generated_files
        
        log_info(f"步骤2完成，生成文件: {generated_files}", "task_manager")
        
    except Exception as e:
        log_error(f"步骤2执行失败", "task_manager", e)
        
        # 更新错误状态
        task_status[task_id]["status"] = "failed"
        task_status[task_id]["progress"] = 0
        task_status[task_id]["message"] = f"步骤2失败: {str(e)}"
        task_status[task_id]["error"] = str(e)
        task_status[task_id]["end_time"] = str(time.time())
        
        # 更新状态文件
        try:
            from .state_manager import GenerationStateManager
            backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
            session_dir = backend_dir / "uploads" / "dynamic" / "configuration" / session_id
            state_manager = GenerationStateManager(session_dir)
            state_manager.update_step_status(
                step_name="step2_test_issue",
                completed=False,
                task_id=task_id,
                error=str(e)
            )
        except:
            pass
    
    finally:
        finalize_task_log()
    
    return task_id


def run_step3a_requirement_basic_task(
    session_id: str,
    basic_info: Dict[str, Any],
    ai_analysis: bool = True,
    deep_analysis: bool = True,
    task_id: str = None
) -> str:
    """
    步骤3a: 生成需求分析表基础信息（除测试项描述和测试方法外的所有列）
    
    Args:
        session_id: 会话ID
        basic_info: 基本信息
        ai_analysis: 是否启用AI分析
        deep_analysis: 是否启用深度分析
        task_id: 任务ID
        
    Returns:
        任务ID
    """
    import openpyxl
    
    if task_id is None:
        task_id = generate_task_id()
    
    # 初始化任务状态
    task_status[task_id] = {
        "status": "running",
        "progress": 0,
        "message": "步骤3a初始化中...",
        "session_id": session_id,
        "start_time": str(time.time()),
        "end_time": None,
        "generated_files": [],
        "error": None
    }
    
    try:
        set_current_task(task_id, session_id)
        log_info(f"========== 开始执行步骤3a: 生成需求分析表基础信息 ==========", "task_manager")
        log_info(f"任务ID: {task_id}, 会话ID: {session_id}", "task_manager")
        
        # 导入状态管理器
        from .state_manager import GenerationStateManager
        
        # 获取会话目录
        backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
        session_dir = backend_dir / "uploads" / "dynamic" / "configuration" / session_id
        log_info(f"会话目录: {session_dir}", "task_manager")
        
        if not session_dir.exists():
            error_msg = f"会话目录不存在: {session_dir}"
            log_error(error_msg, "task_manager")
            raise FileNotFoundError(error_msg)
        
        # 初始化状态管理器
        state_manager = GenerationStateManager(session_dir)
        state = state_manager.load_state()
        
        # 检查步骤2是否完成
        step2_completed = state.get('completed_steps', {}).get('step2_test_issue', {}).get('completed', False)
        if not step2_completed:
            raise ValueError("请先完成步骤2")
        
        update_task_progress(task_id, 10, "正在获取用户上传的Excel文件...")
        
        # 获取用户上传的Excel文件
        uploaded_file = state.get("step3_uploaded_file")
        if not uploaded_file or not Path(uploaded_file).exists():
            raise FileNotFoundError("未找到用户上传的表单，请先上传")
        
        log_info(f"使用用户上传的Excel: {uploaded_file}", "task_manager")
        
        update_task_progress(task_id, 20, "正在准备需求分析表生成...")
        
        # 导入需求分析服务
        from .requirement_analysis.orchestration.requirement_analysis_service import RequirementAnalysisService
        requirement_analysis_service = RequirementAnalysisService()
        
        # 查找需求文档
        requirement_file = None
        for req_file in session_dir.glob("requirement_*"):
            requirement_file = str(req_file)
            break
        
        if not requirement_file:
            raise FileNotFoundError("未找到需求文档")
        
        # 使用上传的文件作为基础
        import shutil
        output_dir = session_dir / "output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "需求分析表_基础.xlsx"
        shutil.copy2(uploaded_file, output_file)
        log_info(f"文件已复制到: {output_file}", "task_manager")
        
        # planning_file 指向用户上传的文件，用于读取项目策划表数据
        planning_file = str(uploaded_file)
        
        log_info(f"使用需求文档: {requirement_file}", "task_manager")
        log_info(f"使用项目策划表: {planning_file}", "task_manager")
        
        update_task_progress(task_id, 40, "正在生成需求分析表基础信息...")
        
        # 准备基本信息
        analysis_info = {
            **basic_info,
            'ai_analysis': ai_analysis,
            'deep_analysis': deep_analysis
        }
        
        # 生成需求分析表
        analysis_result = requirement_analysis_service.generate_requirement_analysis(
            requirement_doc_path=requirement_file,
            planning_table_path=planning_file,
            basic_info=analysis_info,
            output_dir=str(output_dir)
        )
        
        update_task_progress(task_id, 70, "正在清空测试项描述和测试方法列...")
        
        # 清空测试项描述(列19)和测试方法(列20)
        try:
            wb = openpyxl.load_workbook(str(output_file))
            if '需求分析表' in wb.sheetnames:
                sheet = wb['需求分析表']
                # 清空列19和列20（从第2行开始，第1行是表头）
                for row in range(2, sheet.max_row + 1):
                    sheet.cell(row=row, column=19, value='')  # 测试项描述
                    sheet.cell(row=row, column=20, value='')  # 测试方法
                wb.save(str(output_file))
                log_info("已清空测试项描述和测试方法列", "task_manager")
        except Exception as e:
            log_warning(f"清空列时出错（不影响主流程）: {e}", "task_manager")
        
        update_task_progress(task_id, 95, "正在更新状态...")
        
        # 收集生成的文件
        generated_files = ['需求分析表_基础.xlsx']
        
        # 更新状态文件
        state_manager.update_step_status(
            step_name="step3a_requirement_basic",
            completed=True,
            output_files=generated_files,
            task_id=task_id
        )
        
        # 更新任务状态
        task_status[task_id]["status"] = "completed"
        task_status[task_id]["progress"] = 100
        task_status[task_id]["message"] = "步骤3a完成"
        task_status[task_id]["end_time"] = str(time.time())
        task_status[task_id]["generated_files"] = generated_files
        
        log_info(f"步骤3a完成，生成文件: {generated_files}", "task_manager")
        
    except Exception as e:
        log_error(f"步骤3a执行失败", "task_manager", e)
        
        # 更新错误状态
        task_status[task_id]["status"] = "failed"
        task_status[task_id]["progress"] = 0
        task_status[task_id]["message"] = f"步骤3a失败: {str(e)}"
        task_status[task_id]["error"] = str(e)
        task_status[task_id]["end_time"] = str(time.time())
        
        # 更新状态文件
        try:
            from .state_manager import GenerationStateManager
            backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
            session_dir = backend_dir / "uploads" / "dynamic" / "configuration" / session_id
            state_manager = GenerationStateManager(session_dir)
            state_manager.update_step_status(
                step_name="step3a_requirement_basic",
                completed=False,
                task_id=task_id,
                error=str(e)
            )
        except:
            pass
    
    finally:
        finalize_task_log()
    
    return task_id


def run_step3b_test_items_task(
    session_id: str,
    basic_info: Dict[str, Any],
    ai_analysis: bool = True,
    task_id: str = None
) -> str:
    """
    步骤3b: 完善需求分析表（填充测试项描述和测试方法）
    
    Args:
        session_id: 会话ID
        basic_info: 基本信息
        ai_analysis: 是否启用AI分析
        task_id: 任务ID
        
    Returns:
        任务ID
    """
    import openpyxl
    
    if task_id is None:
        task_id = generate_task_id()
    
    # 初始化任务状态
    task_status[task_id] = {
        "status": "running",
        "progress": 0,
        "message": "步骤3b初始化中...",
        "session_id": session_id,
        "start_time": str(time.time()),
        "end_time": None,
        "generated_files": [],
        "error": None
    }
    
    try:
        set_current_task(task_id, session_id)
        log_info(f"========== 开始执行步骤3b: 填充测试项描述和测试方法 ==========", "task_manager")
        log_info(f"任务ID: {task_id}, 会话ID: {session_id}", "task_manager")
        
        # 导入状态管理器
        from .state_manager import GenerationStateManager
        
        # 获取会话目录
        backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
        session_dir = backend_dir / "uploads" / "dynamic" / "configuration" / session_id
        log_info(f"会话目录: {session_dir}", "task_manager")
        
        if not session_dir.exists():
            error_msg = f"会话目录不存在: {session_dir}"
            log_error(error_msg, "task_manager")
            raise FileNotFoundError(error_msg)
        
        # 初始化状态管理器
        state_manager = GenerationStateManager(session_dir)
        state = state_manager.load_state()
        
        # 检查步骤3a是否完成
        step3a_completed = state.get('completed_steps', {}).get('step3a_requirement_basic', {}).get('completed', False)
        if not step3a_completed:
            raise ValueError("请先完成步骤3a")
        
        update_task_progress(task_id, 10, "正在获取用户上传的Excel文件...")
        
        # 获取用户上传的Excel文件（步骤3a的结果）
        uploaded_file = state.get("step3b_uploaded_file")
        if not uploaded_file or not Path(uploaded_file).exists():
            raise FileNotFoundError("未找到用户上传的需求分析表基础版，请先上传")
        
        log_info(f"使用用户上传的Excel: {uploaded_file}", "task_manager")
        
        update_task_progress(task_id, 20, "正在准备测试项生成...")
        
        # 导入需求分析服务
        from .requirement_analysis.orchestration.requirement_analysis_service import RequirementAnalysisService
        requirement_analysis_service = RequirementAnalysisService()
        
        # 查找需求文档
        requirement_file = None
        for req_file in session_dir.glob("requirement_*"):
            requirement_file = str(req_file)
            break
        
        if not requirement_file:
            raise FileNotFoundError("未找到需求文档")
        
        # 复制用户上传的文件到输出目录
        import shutil
        output_dir = session_dir / "output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "需求分析表_完整.xlsx"
        shutil.copy2(uploaded_file, output_file)
        log_info(f"文件已复制到: {output_file}", "task_manager")
        
        # 查找项目策划表（从原始上传的文件中）
        step2_uploaded = state.get("step3_uploaded_file")  # 步骤2上传的文件
        if not step2_uploaded:
            raise FileNotFoundError("未找到项目策划表")
        
        planning_file = str(step2_uploaded)
        
        log_info(f"使用需求文档: {requirement_file}", "task_manager")
        log_info(f"使用项目策划表: {planning_file}", "task_manager")
        
        update_task_progress(task_id, 40, "正在生成完整的需求分析表...")
        
        # 准备基本信息
        analysis_info = {
            **basic_info,
            'ai_analysis': ai_analysis,
            'deep_analysis': False  # 步骤3b只需要生成测试项，不需要深度分析
        }
        
        # 生成完整的需求分析表（包含测试项描述和测试方法）
        analysis_result = requirement_analysis_service.generate_requirement_analysis(
            requirement_doc_path=requirement_file,
            planning_table_path=planning_file,
            basic_info=analysis_info,
            output_dir=str(output_dir)
        )
        
        update_task_progress(task_id, 70, "正在提取测试项描述和测试方法...")
        
        # 从完整生成的结果中提取测试项描述和测试方法，填充到用户上传的文件中
        try:
            # 假设完整生成结果保存在临时位置
            temp_result_file = output_dir / (analysis_result.get('output_file', '需求分析表.xlsx'))
            
            if temp_result_file.exists() and temp_result_file != output_file:
                wb_temp = openpyxl.load_workbook(str(temp_result_file))
                wb_user = openpyxl.load_workbook(str(output_file))
                
                if '需求分析表' in wb_temp.sheetnames and '需求分析表' in wb_user.sheetnames:
                    sheet_temp = wb_temp['需求分析表']
                    sheet_user = wb_user['需求分析表']
                    
                    # 复制列19和列20（测试项描述和测试方法）
                    for row in range(2, min(sheet_temp.max_row, sheet_user.max_row) + 1):
                        test_desc = sheet_temp.cell(row=row, column=19).value
                        test_method = sheet_temp.cell(row=row, column=20).value
                        sheet_user.cell(row=row, column=19, value=test_desc)
                        sheet_user.cell(row=row, column=20, value=test_method)
                    
                    wb_user.save(str(output_file))
                    log_info("已填充测试项描述和测试方法", "task_manager")
                    
                    # 删除临时文件
                    temp_result_file.unlink()
        except Exception as e:
            log_warning(f"填充测试项时出错: {e}，使用完整生成结果", "task_manager")
        
        update_task_progress(task_id, 95, "正在更新状态...")
        
        # 收集生成的文件
        generated_files = ['需求分析表_完整.xlsx']
        
        # 更新状态文件（标记步骤3完整完成）
        state_manager.update_step_status(
            step_name="step3b_test_items",
            completed=True,
            output_files=generated_files,
            task_id=task_id
        )
        
        # 同时更新step3_requirement_analysis为完成（兼容步骤4的依赖检查）
        state_manager.update_step_status(
            step_name="step3_requirement_analysis",
            completed=True,
            output_files=generated_files,
            task_id=task_id
        )
        
        # 更新任务状态
        task_status[task_id]["status"] = "completed"
        task_status[task_id]["progress"] = 100
        task_status[task_id]["message"] = "步骤3b完成"
        task_status[task_id]["end_time"] = str(time.time())
        task_status[task_id]["generated_files"] = generated_files
        
        log_info(f"步骤3b完成，生成文件: {generated_files}", "task_manager")
        
    except Exception as e:
        log_error(f"步骤3b执行失败", "task_manager", e)
        
        # 更新错误状态
        task_status[task_id]["status"] = "failed"
        task_status[task_id]["progress"] = 0
        task_status[task_id]["message"] = f"步骤3b失败: {str(e)}"
        task_status[task_id]["error"] = str(e)
        task_status[task_id]["end_time"] = str(time.time())
        
        # 更新状态文件
        try:
            from .state_manager import GenerationStateManager
            backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
            session_dir = backend_dir / "uploads" / "dynamic" / "configuration" / session_id
            state_manager = GenerationStateManager(session_dir)
            state_manager.update_step_status(
                step_name="step3b_test_items",
                completed=False,
                task_id=task_id,
                error=str(e)
            )
        except:
            pass
    
    finally:
        finalize_task_log()
    
    return task_id


def run_step3_requirement_analysis_task(
    session_id: str,
    basic_info: Dict[str, Any],
    ai_analysis: bool = True,
    deep_analysis: bool = True,
    task_id: str = None
) -> str:
    """
    步骤3: 生成需求分析表（基于项目策划表）
    [保留用于兼容性，实际应使用step3a和step3b]
    
    Args:
        session_id: 会话ID
        basic_info: 基本信息
        ai_analysis: 是否启用AI分析
        deep_analysis: 是否启用深度分析
        task_id: 任务ID
        
    Returns:
        任务ID
    """
    if task_id is None:
        task_id = generate_task_id()
    
    # 初始化任务状态
    task_status[task_id] = {
        "status": "running",
        "progress": 0,
        "message": "步骤3初始化中...",
        "session_id": session_id,
        "start_time": str(time.time()),
        "end_time": None,
        "generated_files": [],
        "error": None
    }
    
    try:
        set_current_task(task_id, session_id)
        log_info(f"开始执行步骤3: 生成需求分析表", "task_manager")
        
        # 导入状态管理器
        from .state_manager import GenerationStateManager
        
        # 获取会话目录
        backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
        session_dir = backend_dir / "uploads" / "dynamic" / "configuration" / session_id
        
        if not session_dir.exists():
            raise FileNotFoundError(f"会话目录不存在: {session_dir}")
        
        # 初始化状态管理器
        state_manager = GenerationStateManager(session_dir)
        
        # 检查是否可以开始步骤3
        can_start, reason = state_manager.can_start_step("step3_requirement_analysis")
        if not can_start:
            raise ValueError(f"无法开始步骤3: {reason}")
        
        update_task_progress(task_id, 10, "正在获取用户上传的Excel文件...")
        
        # 获取用户上传的Excel文件
        state = state_manager.load_state()
        uploaded_file = state.get("step3_uploaded_file")
        if not uploaded_file or not Path(uploaded_file).exists():
            raise FileNotFoundError("未找到用户上传的表单，请先上传")
        
        log_info(f"使用用户上传的Excel: {uploaded_file}", "task_manager")
        
        update_task_progress(task_id, 20, "正在准备需求分析表生成...")
        
        # 导入需求分析服务
        from .requirement_analysis.orchestration.requirement_analysis_service import RequirementAnalysisService
        requirement_analysis_service = RequirementAnalysisService()
        
        # 查找需求文档
        requirement_file = None
        for req_file in session_dir.glob("requirement_*"):
            requirement_file = str(req_file)
            break
        
        if not requirement_file:
            raise FileNotFoundError("未找到需求文档")
        
        # 使用上传的文件作为基础（包含前4个sheet的数据）
        import shutil
        output_dir = session_dir / "output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "完整表单.xlsx"
        shutil.copy2(uploaded_file, output_file)
        log_info(f"文件已复制到: {output_file}", "task_manager")
        
        # planning_file 指向用户上传的文件，用于读取项目策划表数据
        planning_file = str(uploaded_file)
        
        log_info(f"使用需求文档: {requirement_file}", "task_manager")
        log_info(f"使用项目策划表: {planning_file}", "task_manager")
        
        update_task_progress(task_id, 40, "正在生成需求分析表...")
        
        # 准备基本信息
        analysis_info = {
            **basic_info,
            'ai_analysis': ai_analysis,
            'deep_analysis': deep_analysis
        }
        
        # 生成需求分析表
        analysis_result = requirement_analysis_service.generate_requirement_analysis(
            requirement_doc_path=requirement_file,
            planning_table_path=planning_file,
            basic_info=analysis_info,
            output_dir=str(output_dir)
        )
        
        update_task_progress(task_id, 90, "正在更新状态...")
        
        # 收集生成的文件
        generated_files = []
        
        if analysis_result.get('success'):
            generated_files.append(analysis_result.get('output_file', '需求分析表.xlsx'))
        
        # 更新状态文件
        state_manager.update_step_status(
            step_name="step3_requirement_analysis",
            completed=True,
            output_files=generated_files,
            task_id=task_id
        )
        
        # 更新任务状态
        task_status[task_id]["status"] = "completed"
        task_status[task_id]["progress"] = 100
        task_status[task_id]["message"] = "步骤3完成"
        task_status[task_id]["end_time"] = str(time.time())
        task_status[task_id]["generated_files"] = generated_files
        
        log_info(f"步骤3完成，生成文件: {generated_files}", "task_manager")
        
    except Exception as e:
        log_error(f"步骤3执行失败", "task_manager", e)
        
        # 更新错误状态
        task_status[task_id]["status"] = "failed"
        task_status[task_id]["progress"] = 0
        task_status[task_id]["message"] = f"步骤3失败: {str(e)}"
        task_status[task_id]["error"] = str(e)
        task_status[task_id]["end_time"] = str(time.time())
        
        # 更新状态文件
        try:
            from .state_manager import GenerationStateManager
            backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
            session_dir = backend_dir / "uploads" / "dynamic" / "configuration" / session_id
            state_manager = GenerationStateManager(session_dir)
            state_manager.update_step_status(
                step_name="step3_requirement_analysis",
                completed=False,
                task_id=task_id,
                error=str(e)
            )
        except:
            pass
    
    finally:
        finalize_task_log()
    
    return task_id


def run_step4_test_case_task(
    session_id: str,
    basic_info: Dict[str, Any],
    ai_analysis: bool = True,
    task_id: str = None
) -> str:
    """
    步骤4: 生成测试用例单（基于需求分析表）
    
    Args:
        session_id: 会话ID
        basic_info: 基本信息
        ai_analysis: 是否启用AI分析
        task_id: 任务ID
        
    Returns:
        任务ID
    """
    if task_id is None:
        task_id = generate_task_id()
    
    # 初始化任务状态
    task_status[task_id] = {
        "status": "running",
        "progress": 0,
        "message": "步骤4初始化中...",
        "session_id": session_id,
        "start_time": str(time.time()),
        "end_time": None,
        "generated_files": [],
        "error": None
    }
    
    try:
        set_current_task(task_id, session_id)
        log_info(f"开始执行步骤4: 生成测试用例单", "task_manager")
        
        # 导入状态管理器
        from .state_manager import GenerationStateManager
        
        # 获取会话目录
        backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
        session_dir = backend_dir / "uploads" / "dynamic" / "configuration" / session_id
        
        if not session_dir.exists():
            raise FileNotFoundError(f"会话目录不存在: {session_dir}")
        
        # 初始化状态管理器
        state_manager = GenerationStateManager(session_dir)
        
        # 检查是否可以开始步骤4
        can_start, reason = state_manager.can_start_step("step4_test_case")
        if not can_start:
            raise ValueError(f"无法开始步骤4: {reason}")
        
        update_task_progress(task_id, 10, "正在获取用户上传的Excel文件...")
        
        # 获取用户上传的Excel文件
        state = state_manager.load_state()
        uploaded_file = state.get("step4_uploaded_file")
        if not uploaded_file or not Path(uploaded_file).exists():
            raise FileNotFoundError("未找到用户上传的表单，请先上传")
        
        log_info(f"使用用户上传的Excel: {uploaded_file}", "task_manager")
        
        update_task_progress(task_id, 20, "正在准备测试用例生成...")
        
        # 导入测试用例服务
        from .test_case_generation.test_case_service import TestCaseService
        test_case_service = TestCaseService()
        
        # 使用上传的文件作为基础（包含前5个sheet的数据）
        import shutil
        output_dir = session_dir / "output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "完整表单.xlsx"
        shutil.copy2(uploaded_file, output_file)
        log_info(f"文件已复制到: {output_file}", "task_manager")
        
        # analysis_file 指向用户上传的文件，用于读取需求分析表数据
        analysis_file = str(uploaded_file)
        
        log_info(f"使用需求分析表: {analysis_file}", "task_manager")
        
        update_task_progress(task_id, 40, "正在生成测试用例...")
        
        # 生成测试用例
        test_case_result = test_case_service.generate_test_cases(
            requirement_analysis_path=analysis_file,
            basic_info=basic_info,
            ai_analysis=ai_analysis,
            output_dir=str(output_dir)
        )
        
        update_task_progress(task_id, 90, "正在更新状态...")
        
        # 收集生成的文件
        generated_files = []
        
        if test_case_result.get('success'):
            generated_files.append(test_case_result.get('output_file', '测试用例单.xlsx'))
        
        # 更新状态文件
        state_manager.update_step_status(
            step_name="step4_test_case",
            completed=True,
            output_files=generated_files,
            task_id=task_id
        )
        
        # 更新任务状态
        task_status[task_id]["status"] = "completed"
        task_status[task_id]["progress"] = 100
        task_status[task_id]["message"] = "步骤4完成"
        task_status[task_id]["end_time"] = str(time.time())
        task_status[task_id]["generated_files"] = generated_files
        
        log_info(f"步骤4完成，生成文件: {generated_files}", "task_manager")
        
    except Exception as e:
        log_error(f"步骤4执行失败", "task_manager", e)
        
        # 更新错误状态
        task_status[task_id]["status"] = "failed"
        task_status[task_id]["progress"] = 0
        task_status[task_id]["message"] = f"步骤4失败: {str(e)}"
        task_status[task_id]["error"] = str(e)
        task_status[task_id]["end_time"] = str(time.time())
        
        # 更新状态文件
        try:
            from .state_manager import GenerationStateManager
            backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
            session_dir = backend_dir / "uploads" / "dynamic" / "configuration" / session_id
            state_manager = GenerationStateManager(session_dir)
            state_manager.update_step_status(
                step_name="step4_test_case",
                completed=False,
                task_id=task_id,
                error=str(e)
            )
        except:
            pass
    
    finally:
        finalize_task_log()
    
    return task_id 