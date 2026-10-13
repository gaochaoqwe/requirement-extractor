"""
功能点审查Runner：协调功能点审查流程
"""
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List
from pathlib import Path

from ..ai.openai.client import AIClient
from .agent_tools import AgentTools
from .agent_executor import AgentExecutor
from ..business_review.kb.loader import load_kb
from ...config_database_feature import get_feature_db_session  # 使用功能审查数据库切换模块
from ...db.sync_task_data import sync_task_to_feature_db
from ...db.repository.feature_repo import FeatureRepository, FeatureReviewProblemRepository
from ...db.repository.task_repo import TaskRepository
from ..ai.analysis_runner import normalize_problem
from .logger import FeatureReviewLogger, TaskLogger

# 从配置文件导入功能点审查并发度
from ...config import FEATURE_CONCURRENT_REQUESTS


# 功能点审查进度缓存
_FEATURE_PROGRESS: Dict[int, Dict[str, Any]] = {}
_PROGRESS_LOCK = threading.Lock()


def _init_progress(task_id: int, total: int):
    """初始化进度"""
    with _PROGRESS_LOCK:
        _FEATURE_PROGRESS[task_id] = {
            "status": "processing",
            "total": total,
            "completed": 0,
            "current_feature": "",
            "message": "",
        }


def _update_progress(task_id: int, inc: int = 0, current_feature: str = None, message: str = None):
    """更新进度"""
    with _PROGRESS_LOCK:
        p = _FEATURE_PROGRESS.get(task_id)
        if not p:
            return
        p["completed"] = min(p["total"], p.get("completed", 0) + inc)
        if current_feature is not None:
            p["current_feature"] = current_feature
        if message is not None:
            p["message"] = message


def _finalize_progress(task_id: int, status: str, message: str = ""):
    """完成进度"""
    with _PROGRESS_LOCK:
        p = _FEATURE_PROGRESS.get(task_id)
        if not p:
            _FEATURE_PROGRESS[task_id] = {"status": status, "total": 0, "completed": 0, "message": message}
            return
        p["status"] = status
        p["message"] = message


def get_progress(task_id: int) -> Dict[str, Any]:
    """获取进度"""
    with _PROGRESS_LOCK:
        return _FEATURE_PROGRESS.get(task_id, {"status": "idle", "total": 0, "completed": 0, "message": ""})


def _process_single_feature(
    task_id: int,
    feature_index: int,
    feature: Dict[str, str],
    total_features: int,
    project_root: str,
    software_type: str,
    entry_function: str,
    kb: Dict[str, Any]
) -> None:
    """
    处理单个功能点（用于并发执行）
    
    Args:
        task_id: 任务ID
        feature_index: 功能点索引（1-based）
        feature: 功能点信息 {"name": "...", "description": "..."}
        total_features: 总功能点数
        project_root: 项目根目录
        software_type: 软件类型
        entry_function: 入口函数
        kb: 知识库
    """
    feature_name = feature.get("name", f"功能点{feature_index}")
    feature_description = feature.get("description", "")
    
    # 创建临时feature_id用于日志（后面会被真实的feature_id替换）
    temp_feature_id = feature_index
    logger = None
    
    print(f"\n--- 处理功能点 {feature_index}/{total_features}: {feature_name} ---")
    _update_progress(task_id, inc=0, current_feature=feature_name, message=f"正在分析功能点: {feature_name}")
    
    # 为每个线程创建独立的AI客户端和Agent
    ai_client = AIClient()
    tools = AgentTools(project_root, task_id)
    agent = AgentExecutor(tools, ai_client, max_iterations=10)
    
    try:
        with get_feature_db_session() as db:
            feature_repo = FeatureRepository(db)
            problem_repo = FeatureReviewProblemRepository(db)
            
            # 创建功能点记录
            feature_repo._ensure_schema()
            feature_record = feature_repo.create_feature({
                "task_id": task_id,
                "feature_name": feature_name,
                "feature_description": feature_description,
                "software_type": software_type,
                "domain": software_type.split('/')[0] if '/' in software_type else "",
                "entry_function": entry_function,
                "status": "processing"
            })
            db.commit()
            
            # 创建日志器（使用真实的feature_id）
            logger = FeatureReviewLogger(task_id, feature_record.id, feature_name)
            logger.log_summary(f"开始处理功能点 {feature_index}/{total_features}")
            logger.log_summary(f"功能名称: {feature_name}")
            logger.log_summary(f"功能描述: {feature_description}")
            
            # 步骤1：使用Agent探索代码，找到功能实现
            print(f"  步骤1: Agent探索代码...")
            logger.log_exploration("=" * 60)
            logger.log_exploration("步骤1: 开始Agent代码探索")
            logger.log_exploration("=" * 60)
            
            exploration_result = _explore_feature_code(
                agent=agent,
                feature_name=feature_name,
                feature_description=feature_description,
                entry_function=entry_function,
                kb=kb,
                software_type=software_type,
                logger=logger
            )
            
            _update_progress(task_id, inc=1, message=f"{feature_name}: 代码探索完成")
            logger.log_exploration("代码探索阶段完成")
            
            if not exploration_result.get("success"):
                error_msg = exploration_result.get('error', '未知错误')
                print(f"  代码探索失败: {error_msg}")
                logger.log_error(f"代码探索失败: {error_msg}")
                feature_repo.update_feature(feature_record.id, {
                    "status": "failed",
                    "implementation_description": f"探索失败: {error_msg}"
                })
                db.commit()
                logger.finalize(status="failed", problems_count=0)
                return
            
            # 提取探索结果
            implementation_info = exploration_result.get("result", {})
            implementation_description = implementation_info.get("implementation_description", "")
            related_files = implementation_info.get("related_files", [])
            related_functions = implementation_info.get("related_functions", [])
            
            # 更新功能点记录
            feature_repo.update_feature(feature_record.id, {
                "implementation_description": implementation_description,
                "related_files": json.dumps(related_files, ensure_ascii=False),
                "related_functions": json.dumps(related_functions, ensure_ascii=False),
                "code_locations": json.dumps(implementation_info.get("code_locations", []), ensure_ascii=False)
            })
            db.commit()
            
            print(f"  找到相关文件: {len(related_files)}个")
            print(f"  找到相关函数: {len(related_functions)}个")
            logger.log_exploration(f"探索结果: {len(related_files)} 个文件，{len(related_functions)} 个函数")
            logger.log_exploration(f"实现描述: {implementation_description}")
            for i, func in enumerate(related_functions[:10], 1):  # 只记录前10个
                logger.log_exploration(f"  相关函数 {i}: {func}")
            
            # 步骤2: 对找到的代码进行审查
            print(f"  步骤2: 审查功能实现...")
            logger.log_review("=" * 60)
            logger.log_review("步骤2: 开始审查功能实现")
            logger.log_review("=" * 60)
            
            review_result = _review_feature_implementation(
                agent=agent,
                feature_name=feature_name,
                feature_description=feature_description,
                implementation_description=implementation_description,
                related_files=related_files,
                related_functions=related_functions,
                kb=kb,
                software_type=software_type,
                logger=logger
            )
            
            _update_progress(task_id, inc=1, message=f"{feature_name}: 审查完成")
            
            if not review_result.get("success"):
                error_msg = review_result.get('error', '未知错误')
                print(f"  审查失败: {error_msg}")
                logger.log_error(f"审查失败: {error_msg}")
                feature_repo.update_feature(feature_record.id, {"status": "completed"})
                db.commit()
                logger.finalize(status="completed", problems_count=0)
                return
            
            # 步骤3: 保存审查结果
            print(f"  步骤3: 保存审查结果...")
            problems = review_result.get("result", {}).get("problems", [])
            logger.log_review(f"审查完成，发现 {len(problems)} 个问题")
            
            for idx, problem in enumerate(problems, 1):
                normalized = normalize_problem(problem)
                logger.log_review(f"问题 {idx}/{len(problems)}: {normalized.get('issue_name', 'N/A')}")
                logger.log_review(f"  等级: {normalized.get('issue_level', '一般问题')}")
                logger.log_review(f"  位置: {normalized.get('issue_location', 'N/A')}")
                
                problem_record = {
                    "task_id": task_id,
                    "feature_id": feature_record.id,
                    "feature_name": feature_name,
                    "feature_description": feature_description,
                    "implementation_path": json.dumps(related_functions, ensure_ascii=False),
                    "implementation_description": implementation_description,
                    "related_files": json.dumps(related_files, ensure_ascii=False),
                    "related_functions": json.dumps(related_functions, ensure_ascii=False),
                    "code_locations": json.dumps(implementation_info.get("code_locations", []), ensure_ascii=False),
                    "issue_name": normalized.get("issue_name", "未命名问题"),
                    "issue_level": normalized.get("issue_level", "建议改进"),
                    "issue_location": normalized.get("issue_location", ""),
                    "file_name": normalized.get("file_name", ""),
                    "function_name": normalized.get("function_name", ""),
                    "line": normalized.get("line"),  # 行号，可能为None
                    "source_code": normalized.get("source_code", ""),
                    "problem_reason": normalized.get("problem_reason", ""),
                    "description_requirement": normalized.get("description_requirement", ""),
                    "description_issue": normalized.get("description_issue", ""),
                    "description_location": normalized.get("description_location", ""),
                    "description_impact": normalized.get("description_impact", ""),
                    "business_rule": normalized.get("business_rule", ""),
                    "suggestion": normalized.get("suggestion", ""),
                    "software_type": software_type,
                    "domain": software_type.split('/') [0] if '/' in software_type else "",
                }
                problem_repo.create_problem(problem_record)
            
            db.commit()
            logger.log_summary(f"已保存 {len(problems)} 个问题到数据库")
            
            # 更新功能点状态
            feature_repo.update_feature(feature_record.id, {"status": "completed"})
            db.commit()
            
            print(f"  发现 {len(problems)} 个问题")
            logger.finalize(status="completed", problems_count=len(problems))
            _update_progress(task_id, inc=1, message=f"{feature_name}: 完成")
            
    except Exception as e:
        print(f"  处理功能点异常: {e}")
        import traceback
        traceback.print_exc()
        
        if logger:
            logger.log_error(f"处理功能点异常", exception=e)
            logger.finalize(status="failed", problems_count=0)
        
        # 更新功能点状态为失败
        try:
            with get_feature_db_session() as db:
                feature_repo = FeatureRepository(db)
                feature_repo.update_feature(feature_record.id, {
                    "status": "failed",
                    "implementation_description": f"处理异常: {str(e)}"
                })
                db.commit()
        except:
            pass


def run(
    task_id: int,
    project_root: str,
    features: List[Dict[str, str]],  # [{"name": "功能名", "description": "功能描述"}, ...]
    software_type: str,
    entry_function: str = "main",
    options: Dict[str, Any] = None
) -> None:
    """
    执行功能点审查
    
    Args:
        task_id: 任务ID
        project_root: 项目根目录
        features: 功能点列表
        software_type: 软件类型（领域/类型）
        entry_function: 入口函数
        options: 额外选项
    """
    print(f"\n========== 开始功能点审查 ==========")
    print(f"任务ID: {task_id}")
    
    # 同步任务数据到功能审查数据库
    print(f"同步任务数据到功能审查数据库...")
    if not sync_task_to_feature_db(task_id):
        print(f"❌ 任务数据同步失败，审查终止")
        _finalize_progress(task_id, "failed", "任务数据同步失败")
        return
    print(f"✅ 任务数据同步成功")
    print(f"项目根目录: {project_root}")
    print(f"功能点数量: {len(features)}")
    print(f"软件类型: {software_type}")
    
    # 创建任务级别日志
    task_logger = TaskLogger(task_id)
    task_logger.log(f"开始功能点审查")
    task_logger.log(f"项目根目录: {project_root}")
    task_logger.log(f"功能点数量: {len(features)}")
    task_logger.log(f"软件类型: {software_type}")
    
    try:
        _init_progress(task_id, total=len(features) * 3)  # 每个功能点3个步骤
        
        # 加载知识库（功能点审查需要业务知识）
        print(f"加载知识库: {software_type}")
        task_logger.log(f"加载知识库: {software_type}")
        kb = load_kb(software_type)
        _update_progress(task_id, inc=1, message="知识库加载完成")
        task_logger.log("知识库加载完成")
        
        # 注意：每个线程会创建独立的AI客户端和Agent实例
        _update_progress(task_id, inc=1, message="准备并发处理")
        
        # 并发处理功能点
        print(f"\n使用 {FEATURE_CONCURRENT_REQUESTS} 个线程并发处理功能点")
        
        with ThreadPoolExecutor(max_workers=FEATURE_CONCURRENT_REQUESTS) as executor:
            # 提交所有功能点处理任务
            futures = []
            for i, feature in enumerate(features, 1):
                future = executor.submit(
                    _process_single_feature,
                    task_id=task_id,
                    feature_index=i,
                    feature=feature,
                    total_features=len(features),
                    project_root=project_root,
                    software_type=software_type,
                    entry_function=entry_function,
                    kb=kb
                )
                futures.append(future)
            
            # 等待所有任务完成
            print(f"\n等待所有功能点处理完成...")
            for future in as_completed(futures):
                try:
                    future.result()  # 获取结果，如果有异常会在这里抛出
                except Exception as e:
                    print(f"功能点处理任务异常: {e}")
                    import traceback
                    traceback.print_exc()
        
        _finalize_progress(task_id, "completed", f"功能点审查完成，共处理{len(features)}个功能点")
        print(f"\n========== 功能点审查完成 ==========")
        task_logger.finalize(total_features=len(features), status="completed")
        
    except Exception as e:
        print(f"功能点审查执行失败: {e}")
        import traceback
        traceback.print_exc()
        task_logger.log(f"功能点审查执行失败: {e}", level="ERROR")
        _finalize_progress(task_id, "failed", f"功能点审查失败: {str(e)}")
        task_logger.finalize(total_features=len(features), status="failed")
        raise


def _explore_feature_code(
    agent: AgentExecutor,
    feature_name: str,
    feature_description: str,
    entry_function: str,
    kb: Dict[str, Any],
    software_type: str,
    logger: FeatureReviewLogger = None
) -> Dict[str, Any]:
    """
    使用Agent探索功能点对应的代码实现
    
    Returns:
        探索结果，包含相关文件、函数、实现描述等
    """
    if logger:
        logger.log_exploration(f"开始探索功能点: {feature_name}")
        logger.log_exploration(f"入口函数: {entry_function}")
    kb_text = kb.get("kb_text", "")[:2000]  # 限制长度
    
    system_prompt = f"""你是一名资深的{software_type}软件架构师和代码分析专家。

【任务目标】
根据用户提供的功能描述，在代码库中探索并找到实现该功能的相关代码。

【领域知识】
{kb_text}

【可用工具】
- list_directory: 列出目录内容，了解项目结构
- search_function_by_name: 按函数名搜索函数
- search_function_in_file: 在文件中搜索特定函数
- read_file_range: 读取文件的指定行范围

【探索策略】
1. 首先使用list_directory了解项目结构
2. 从入口函数({entry_function})开始
3. 根据功能描述和文件/函数名称推断相关代码位置
4. 使用read_file_range查看具体实现
5. 搜索相关的函数和数据结构

【输出要求】
完成探索后，请输出JSON格式结果：
{{
  "implementation_description": "详细描述该功能在代码库中是如何实现的（中文）",
  "related_files": ["文件1.c", "文件2.h", ...],
  "related_functions": ["函数1", "函数2", ...],
  "code_locations": [
    {{"file": "文件路径", "function": "函数名", "description": "作用描述"}},
    ...
  ]
}}

请充分利用工具探索代码库，找到功能实现的完整路径。"""
    
    user_query = f"""请帮我在代码库中找到以下功能的实现：

【功能名称】{feature_name}

【功能描述】
{feature_description}

【入口函数】{entry_function}

请开始探索！"""
    
    if logger:
        logger.log_exploration("调用AI Agent进行代码探索...")
    
    result = agent.execute(system_prompt, user_query)
    
    if logger:
        logger.log_exploration(f"探索完成，成功: {result.get('success', False)}")
    
    return result


def _review_feature_implementation(
    agent: AgentExecutor,
    feature_name: str,
    feature_description: str,
    implementation_description: str,
    related_files: List[str],
    related_functions: List[str],
    kb: Dict[str, Any],
    software_type: str,
    logger: FeatureReviewLogger = None
) -> Dict[str, Any]:
    """
    审查功能点的具体实现
    
    Returns:
        审查结果，包含发现的问题
    """
    if logger:
        logger.log_review(f"开始审查功能实现")
        logger.log_review(f"相关文件数: {len(related_files)}")
        logger.log_review(f"相关函数数: {len(related_functions)}")
    kb_text = kb.get("kb_text", "")[:2000]
    typical_defects = kb.get("typical_defects_text", "")[:1500]
    
    system_prompt = f"""你是一名资深的{software_type}代码审查专家。

【任务目标】
对已经找到的功能实现代码进行深入审查，发现潜在的问题。

【领域知识】
{kb_text}

【典型缺陷模式】
{typical_defects}

【审查重点】
1. 功能实现是否符合功能描述的要求
2. 业务逻辑正确性
3. 异常处理和边界条件
4. 代码质量和可维护性
5. 性能问题
6. 领域规则符合性

【可用工具】
- read_file_range: 读取文件指定行范围，查看具体实现
- search_function_in_file: 搜索具体函数的代码

【输出要求】
完成审查后，输出JSON格式结果：
{{
  "problems": [
    {{
      "issue_name": "问题名称（中文）",
      "issue_level": "重要问题|一般问题|建议改进",
      "issue_location": "文件名:函数名",
      "file_name": "文件名",
      "function_name": "函数名",
      "line": 123,
      "source_code": "相关代码片段",
      "problem_reason": "为什么是问题（中文）",
      "description_requirement": "功能要求（中文）",
      "description_issue": "问题详细描述（中文）",
      "description_location": "问题位置详细说明（中文）",
      "description_impact": "可能的影响（中文）",
      "business_rule": "违反的业务规则（如有）",
      "suggestion": "改进建议（中文）"
    }},
    ...
  ]
}}

注意：line字段为问题所在行号（整数），用于代码定位，如果无法确定可不提供。
如果没有发现问题，problems数组为空即可。"""
    
    files_list = ", ".join(related_files[:10])  # 限制数量
    functions_list = ", ".join(related_functions[:20])
    
    user_query = f"""请审查以下功能的实现：

【功能名称】{feature_name}

【功能描述】
{feature_description}

【实现说明】
{implementation_description}

【相关文件】{files_list}

【相关函数】{functions_list}

请仔细审查这些代码，使用工具查看具体实现，发现潜在问题。"""
    
    if logger:
        logger.log_review("调用AI Agent进行代码审查...")
    
    result = agent.execute(system_prompt, user_query)
    
    if logger:
        logger.log_review(f"审查完成，成功: {result.get('success', False)}")
    
    return result


def run_in_background(
    task_id: int,
    project_root: str,
    features: List[Dict[str, str]],
    software_type: str,
    entry_function: str = "main",
    options: Dict[str, Any] = None
):
    """在后台线程中运行功能点审查"""
    th = threading.Thread(
        target=run,
        args=(task_id, project_root, features, software_type, entry_function, options or {}),
        daemon=True
    )
    th.start()

