"""
智能链路审查 - 渐进式功能发现

核心流程：
1. 渐进式功能发现（多轮迭代）
   - Round 1: 目录结构分析
   - Round 2: 函数签名分析
   - Round 3: main函数验证
2. 分批审查每个功能模块
3. 生成问题单
4. 支持实时进度推送

使用外部记忆文件支持多轮迭代和进度追踪
"""
import json
from typing import Dict, Any, List
from pathlib import Path

from .planner.progressive_discovery import ProgressiveDiscovery
from .executor.smart_chain_executor import SmartChainExecutor
from .tools.call_graph_builder import CallGraphBuilder
from ...config_database_chain import get_chain_db_session  # 使用链路审查数据库切换模块
from ...db.sync_task_data import sync_task_to_chain_db
from ...db.repository.problem_repo import ProblemRepository
from ...utils.concurrent_logger import log_concurrent_info, log_concurrent_warning, log_concurrent_debug, log_concurrent_error, init_concurrent_task


def run_smart_chain_review(
    task_id: int,
    project_root: str,
    file_id: int,
    entry_function: str,
    kb: Dict[str, Any]
) -> Dict[str, Any]:
    """
    运行智能链路审查
    
    Args:
        task_id: 任务ID
        project_root: 项目根目录
        file_id: 文件ID
        entry_function: 入口函数
        kb: 知识库
        
    Returns:
        审查结果统计
    """
    # 初始化日志文件夹
    log_folder = init_concurrent_task(task_id, file_id)
    
    log_concurrent_info(f"[智能链路审查] 任务 {task_id} 开始", "smart_chain_review")
    log_concurrent_info(f"[智能链路审查] 日志文件夹: {log_folder}", "smart_chain_review")
    log_concurrent_info(f"[智能链路审查] 入口函数: {entry_function}", "smart_chain_review")
    
    # 同步任务数据到链路审查数据库
    log_concurrent_info(f"[智能链路审查] 同步任务数据到链路审查数据库...", "smart_chain_review")
    if not sync_task_to_chain_db(task_id):
        log_concurrent_error(f"[智能链路审查] 任务数据同步失败", "smart_chain_review")
        return {
            "status": "sync_failed",
            "features_count": 0,
            "problems_count": 0
        }
    log_concurrent_info(f"[智能链路审查] 任务数据同步成功", "smart_chain_review")
    
    # 阶段0：构建调用图（预处理）
    log_concurrent_info(f"[智能链路审查] ========== 阶段0：构建调用图 ==========", "smart_chain_review")
    
    project_path = Path(project_root)
    call_graph_dir = project_path.parent / "call_graph"
    call_graph_file = call_graph_dir / "call_graph.json"
    
    # 检查是否已存在调用图
    if not call_graph_file.exists():
        try:
            log_concurrent_info(f"[调用图构建] 开始构建项目调用图...", "smart_chain_review")
            
            # 创建调用图目录
            call_graph_dir.mkdir(parents=True, exist_ok=True)
            
            # 构建调用图
            builder = CallGraphBuilder(project_root, language='c')
            call_graph_data = builder.build()
            
            # 保存调用图
            builder.save_to_file(call_graph_file)
            
            log_concurrent_info(
                f"[调用图构建] 完成！函数: {call_graph_data['project']['total_functions']}, "
                f"文件: {call_graph_data['project']['total_files']}, "
                f"调用边: {call_graph_data['project']['total_call_edges']}",
                "smart_chain_review"
            )
        except Exception as e:
            log_concurrent_error(f"[调用图构建] 失败，但继续执行审查", "smart_chain_review", e)
    else:
        log_concurrent_info(f"[调用图构建] 使用已存在的调用图: {call_graph_file}", "smart_chain_review")
    
    # 阶段1：渐进式功能发现
    log_concurrent_info(f"[智能链路审查] ========== 阶段1：渐进式功能发现 ==========", "smart_chain_review")
    
    log_concurrent_info(f"[智能链路审查] 使用渐进式多轮发现模式", "smart_chain_review")
    
    # 创建渐进式发现器
    progressive = ProgressiveDiscovery(
        task_id=task_id,
        project_root=project_root,
        language='c',  # 可以从项目配置获取
        entry_function=entry_function
    )
    
    # 运行渐进式发现
    discovery_result = progressive.run_discovery()
    
    # 从记忆中提取功能列表
    memory = progressive.memory.load_latest()
    features = memory.get("features", []) if memory else []
    
    log_concurrent_info(
        f"[智能链路审查] 渐进式发现完成，共 {discovery_result.get('total_rounds')} 轮",
        "smart_chain_review"
    )
    log_concurrent_info(
        f"[智能链路审查] 记忆文件: {discovery_result.get('memory_path')}",
        "smart_chain_review"
    )
    
    if not features:
        log_concurrent_warning(f"[智能链路审查] 未发现任何功能模块，审查终止", "smart_chain_review")
        return {
            "status": "no_features",
            "features_count": 0,
            "problems_count": 0
        }
    
    log_concurrent_info(f"[智能链路审查] 发现 {len(features)} 个功能模块", "smart_chain_review")
    
    # 阶段2：逐个审查功能模块
    log_concurrent_info(f"[智能链路审查] ========== 阶段2：分批审查 ==========", "smart_chain_review")
    
    # 标记发现阶段完成，审查阶段开始
    progressive.memory.mark_discovery_complete()
    progressive.memory.start_review()
    
    # 扁平化功能列表（包含所有子功能）
    def flatten_features(features_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """递归扁平化功能列表，包括所有子功能"""
        flattened = []
        for feature in features_list:
            flattened.append(feature)
            sub_features = feature.get('sub_features', []) or []
            if sub_features:
                flattened.extend(flatten_features(sub_features))
        return flattened
    
    all_features = flatten_features(features)
    log_concurrent_info(
        f"[智能链路审查] 扁平化后共 {len(all_features)} 个功能（包含子功能）",
        "smart_chain_review"
    )
    
    # 更新审查阶段的总功能数
    progressive.memory.set_review_total_features(len(all_features))
    
    executor = SmartChainExecutor(project_root, session_id=f"task_{task_id}")
    
    total_problems = 0
    feature_results = []
    
    for i, feature in enumerate(all_features, 1):
        feature_name = feature.get('name', f'功能{i}')
        log_concurrent_info(
            f"[智能链路审查] 审查功能 {i}/{len(all_features)}: {feature_name}",
            "smart_chain_review"
        )
        
        # 审查单个功能
        problems = executor.review_feature(feature, kb)
        # 记录AI原始输出，方便定位为何没有问题
        log_concurrent_debug(
            f"[智能链路审查] 功能 {feature_name} AI原始输出: {json.dumps(problems, ensure_ascii=False)}",
            "smart_chain_review"
        )
        
        log_concurrent_info(
            f"[智能链路审查] 功能 {feature_name} 发现 {len(problems)} 个问题",
            "smart_chain_review"
        )
        
        # 保存问题到数据库
        if problems:
            _save_chain_problems(task_id, feature, problems)
            total_problems += len(problems)
        
        feature_results.append({
            "feature_name": feature_name,
            "problems_count": len(problems)
        })
        
        # 更新审查进度到memory
        progressive.memory.update_review_progress(i)
    
    # 标记审查阶段完成
    progressive.memory.mark_review_complete()
    
    # 阶段3：生成总结
    log_concurrent_info(f"[智能链路审查] ========== 审查完成 ==========", "smart_chain_review")
    log_concurrent_info(f"[智能链路审查] 共审查 {len(all_features)} 个功能模块（包含子功能）", "smart_chain_review")
    log_concurrent_info(f"[智能链路审查] 共发现 {total_problems} 个问题", "smart_chain_review")
    
    return {
        "status": "completed",
        "features_count": len(all_features),
        "problems_count": total_problems,
        "feature_results": feature_results
    }


def _save_chain_problems(task_id: int, feature: Dict[str, Any], problems: List[Dict[str, Any]]):
    """保存链路审查问题到数据库"""
    try:
        feature_name = feature.get('name', '未命名功能')
        feature_description = feature.get('description', f"智能发现的功能模块: {feature_name}")
        call_chain = feature.get('call_chain', '')  # 提取调用链路
        
        with get_chain_db_session() as db:
            from ...db.models_chain import ChainReviewProblem
            
            for problem in problems:
                # AI返回的file_name现在是链路名称（如"信号采集与处理链路"）
                # 如果AI没有返回file_name，使用feature_name作为备用
                ai_file_name = problem.get('file_name', feature_name)
                
                chain_problem = ChainReviewProblem(
                    task_id=task_id,
                    chain_name=feature_name,
                    chain_function_description=feature_description,
                    call_chain=call_chain,
                    file_name=ai_file_name,  # 使用AI返回的链路名称
                    source_code=problem.get('source_code', ''),
                    problem_reason=problem.get('problem_reason', ''),
                    issue_level=problem.get('issue_level', '一般问题'),  # 默认值改为"一般问题"
                    issue_name=problem.get('issue_name', '业务问题'),
                    issue_location=problem.get('issue_location', ''),
                    description_requirement=problem.get('description_requirement', ''),
                    description_issue=problem.get('description_issue', ''),
                    description_location=problem.get('description_location', ''),
                    description_impact=problem.get('description_impact', '')
                )
                db.add(chain_problem)
            
            db.commit()
            log_concurrent_info(f"[数据库] 保存 {len(problems)} 个链路问题: {feature_name}", "smart_chain_review")
            
    except Exception as e:
        log_concurrent_warning(f"[数据库] 保存链路问题失败: {e}", "smart_chain_review")


def get_chain_review_progress(task_id: int) -> Dict[str, Any]:
    """
    获取链路审查进度（用于前端实时显示）
    
    Args:
        task_id: 任务ID
        
    Returns:
        进度信息字典
    """
    from .memory.memory_manager import MemoryManager
    
    try:
        # 尝试加载记忆文件
        # 需要从链路审查数据库获取项目路径
        from ...config_database_chain import get_chain_db_session
        from ...db.models_chain import ChainAnalysisTask, ChainAnalysisFile
        
        with get_chain_db_session() as db:
            task = db.query(ChainAnalysisTask).filter(ChainAnalysisTask.id == task_id).first()
            if not task:
                return {"status": "not_found", "message": "Task not found"}
            
            # 通过code_file_id查找文件记录
            if not task.code_file_id:
                return {"status": "error", "message": "Task has no associated file"}
            
            file_record = db.query(ChainAnalysisFile).filter(ChainAnalysisFile.id == task.code_file_id).first()
            if not file_record:
                return {"status": "error", "message": f"File {task.code_file_id} not found"}
            
            project_root = file_record.extract_path
        
        memory_manager = MemoryManager(task_id, project_root)
        memory = memory_manager.load_latest()
        
        if not memory:
            return {
                "status": "not_started",
                "message": "链路审查尚未开始或未启用",
                "progress": 0
            }
        
        discovery_status = memory.get("discovery", {}).get("status", "in_progress")
        current_round = memory.get("discovery", {}).get("current_round", 0)
        total_rounds = memory.get("discovery", {}).get("total_rounds", 3)
        
        # 获取审查状态（从memory.review字段）
        review_info = memory.get("review", {})
        review_status = review_info.get("status", "not_started")
        total_features = review_info.get("total_features", len(memory.get("features", [])))
        reviewed_features = review_info.get("reviewed_features", 0)
        
        # 判断整体状态（基于两个阶段的状态）
        if discovery_status == "completed" and review_status == "completed":
            overall_status = "completed"  # 全部完成
        elif discovery_status == "completed" and review_status == "in_progress":
            overall_status = "reviewing"  # 功能发现完成，正在审查
        elif discovery_status == "completed" and review_status == "not_started":
            overall_status = "reviewing"  # 功能发现完成，准备开始审查
        else:
            overall_status = "discovering"  # 正在发现功能
        
        # 重新设计进度计算：
        # 功能发现阶段（前50%）：分为3个round，每个占 50%/3 ≈ 16.67%
        # 功能审查阶段（后50%）：根据功能点数量动态计算
        
        # 1. 功能发现进度（0-50%）
        if discovery_status == "completed":
            discovery_progress = 50.0  # 完成时固定为50%
        else:
            # 每个round完成后增加 16.67%
            discovery_progress = (current_round / 3.0) * 50.0
        
        # 2. 功能审查进度（50-100%）
        if review_status == "completed":
            review_progress = 100.0
        elif review_status == "in_progress" and total_features > 0:
            # 从50%开始，根据已审查功能占比增加到100%
            review_progress = 50.0 + (reviewed_features / total_features) * 50.0
        else:
            review_progress = discovery_progress  # 审查未开始时，使用发现进度
        
        # 总进度
        overall_progress = review_progress
        
        # 为features附加问题统计
        enhanced_memory = _enhance_memory_with_issues(memory, task_id)
        
        # 构建结构化的Round信息（用于前端横向显示）
        rounds_info = _build_rounds_info(memory, discovery_status, current_round)
        
        # 获取当前正在审查的功能点名称（用于审查阶段显示）
        # 注意：需要使用扁平化后的功能列表，因为审查时是对扁平化列表进行的
        current_reviewing_feature = None
        if overall_status == "reviewing" and reviewed_features < total_features:
            features = memory.get("features", [])
            
            # 扁平化功能列表（与审查时保持一致）
            def flatten_features(features_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
                """递归扁平化功能列表，包括所有子功能"""
                flattened = []
                for feature in features_list:
                    flattened.append(feature)
                    sub_features = feature.get('sub_features', []) or []
                    if sub_features:
                        flattened.extend(flatten_features(sub_features))
                return flattened
            
            all_features = flatten_features(features)
            
            # 从扁平化列表中获取当前正在审查的功能
            if reviewed_features < len(all_features):
                current_reviewing_feature = all_features[reviewed_features].get('name', f'功能{reviewed_features + 1}')
        
        # 构建基本返回数据
        result = {
            "status": overall_status,
            "discovery_status": discovery_status,
            "current_round": current_round,
            "total_rounds": total_rounds,
            "discovery_progress": min(discovery_progress, 50.0),  # 最大50%
            "review_progress": min(review_progress, 100.0),        # 最大100%
            "overall_progress": min(overall_progress, 100.0),
            "features_count": total_features,
            "reviewed_features": reviewed_features,
            "current_activity": _get_current_activity(memory, overall_status, reviewed_features, total_features),
            "rounds_history": memory.get("metadata", {}).get("rounds_history", []),
            "memory": enhanced_memory,  # 增强后的记忆数据（包含问题统计）
            
            # 新增：结构化的显示信息
            "rounds_info": rounds_info,  # Round 1-3 的详细状态（用于前半段横向显示）
            "current_reviewing_feature": current_reviewing_feature,  # 当前审查的功能点名称（用于后半段显示）
            "current_feature": current_reviewing_feature,  # 别名，供前端使用
        }
        
        # 如果审查已完成，添加操作按钮信息
        if overall_status == "completed":
            result["show_action_buttons"] = True
            result["actions"] = [
                {
                    "type": "download",
                    "label": "下载审查结果",
                    "url": f"/api/code-review/business/download/{task_id}"
                },
                {
                    "type": "view_code",
                    "label": "代码视图",
                    "action": "navigate_to_codemap"
                }
            ]
        
        return result
    
    except Exception as e:
        log_concurrent_warning(f"获取链路审查进度失败: {e}", "smart_chain_review")
        return {
            "status": "error",
            "message": str(e),
            "progress": 0
        }


def _enhance_memory_with_issues(memory: Dict[str, Any], task_id: int) -> Dict[str, Any]:
    """
    为memory中的features附加问题统计
    
    从数据库查询每个功能的问题数量，并添加到feature对象中
    """
    import copy
    enhanced_memory = copy.deepcopy(memory)
    
    try:
        # 从链路审查数据库查询所有链路问题
        with get_chain_db_session() as db:
            from ...db.models_chain import ChainReviewProblem
            
            # 获取该任务的所有问题
            problems = db.query(ChainReviewProblem).filter(
                ChainReviewProblem.task_id == task_id
            ).all()
            
            # 统计每个链路名称的问题数量
            problem_counts = {}
            for problem in problems:
                chain_name = problem.chain_name
                if chain_name not in problem_counts:
                    problem_counts[chain_name] = 0
                problem_counts[chain_name] += 1
        
        # 为每个feature添加问题统计（递归处理sub_features）
        def add_issues_count(feature):
            feature_name = feature.get('name', '')
            feature['issues_count'] = problem_counts.get(feature_name, 0)
            
            # 递归处理子功能
            if 'sub_features' in feature and feature['sub_features']:
                for sub_feature in feature['sub_features']:
                    add_issues_count(sub_feature)
                    # 父功能的问题数包含所有子功能的问题数
                    feature['issues_count'] += sub_feature.get('issues_count', 0)
        
        # 处理所有顶层features
        features = enhanced_memory.get('features', [])
        for feature in features:
            add_issues_count(feature)
        
        log_concurrent_info(
            f"[进度统计] 为 {len(features)} 个功能附加了问题统计",
            "smart_chain_review"
        )
        
    except Exception as e:
        log_concurrent_warning(f"[进度统计] 附加问题统计失败: {e}", "smart_chain_review")
        # 失败时返回原始memory
        return memory
    
    return enhanced_memory


def _build_rounds_info(memory: Dict[str, Any], discovery_status: str, current_round: int) -> List[Dict[str, Any]]:
    """
    构建结构化的Round信息（用于前端横向显示）
    
    返回示例：
    [
        {
            "round": 1,
            "title": "目录结构分析",
            "description": "基于目录结构的粗粒度划分",
            "status": "completed",  # completed | in_progress | pending
            "timestamp": "2025/10/26 21:30:23"
        },
        ...
    ]
    """
    # Round 定义（固定3个round）
    rounds_definition = [
        {
            "round": 1,
            "title": "目录结构分析",
            "description": "基于目录结构的粗粒度划分"
        },
        {
            "round": 2,
            "title": "函数签名分析",
            "description": "分批分析（多个模块）+ 最终汇总"
        },
        {
            "round": 3,
            "title": "main函数验证",
            "description": "功能发现完成"
        }
    ]
    
    # 从 rounds_history 中获取时间戳
    rounds_history = memory.get("metadata", {}).get("rounds_history", [])
    round_timestamps = {}
    for history in rounds_history:
        round_num = history.get("round")
        timestamp = history.get("timestamp", "")
        if round_num and timestamp:
            # 格式化时间戳为 YYYY/MM/DD HH:MM:SS
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp)
                round_timestamps[round_num] = dt.strftime("%Y/%m/%d %H:%M:%S")
            except:
                round_timestamps[round_num] = timestamp
    
    # 构建结果
    rounds_info = []
    for round_def in rounds_definition:
        round_num = round_def["round"]
        
        # 确定状态
        if discovery_status == "completed":
            # 功能发现已完成，所有round都是completed
            status = "completed"
        elif current_round > round_num:
            # 当前轮次已超过该round
            status = "completed"
        elif current_round == round_num:
            # 正在进行该round
            status = "in_progress"
        else:
            # 尚未开始该round
            status = "pending"
        
        rounds_info.append({
            "round": round_num,
            "title": round_def["title"],
            "description": round_def["description"],
            "status": status,
            "timestamp": round_timestamps.get(round_num, "")
        })
    
    return rounds_info


def _get_current_activity(memory: Dict[str, Any], overall_status: str, reviewed_features: int, total_features: int) -> str:
    """根据记忆状态推断当前活动"""
    current_round = memory.get("discovery", {}).get("current_round", 0)
    discovery_status = memory.get("discovery", {}).get("status", "in_progress")
    
    if overall_status == "completed":
        return f"✅ 审查完成！共发现 {total_features} 个功能模块"
    
    if overall_status == "reviewing":
        if reviewed_features < total_features:
            return f"🔍 正在审查功能模块 ({reviewed_features}/{total_features})"
        else:
            return f"✅ 功能审查完成，正在汇总结果..."
    
    # discovering 状态
    if discovery_status == "completed":
        return "✅ 功能发现完成，准备开始审查..."
    elif current_round == 1:
        return "📊 Round 1: 正在分析目录结构..."
    elif current_round == 2:
        return "🔍 Round 2: 正在分析函数签名..."
    elif current_round == 3:
        return "✔️ Round 3: 正在验证main函数..."
    else:
        return f"🔄 Round {current_round}: 正在进行深度分析..."

