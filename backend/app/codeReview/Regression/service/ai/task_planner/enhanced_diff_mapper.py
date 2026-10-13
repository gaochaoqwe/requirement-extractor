"""
增强的代码差异映射器 - 重新设计版本
按照用户要求实现：
1. 按函数级别扫描代码变更（而不是文件级别）
2. 每个变更单独请求AI模型进行映射
3. 清晰标识变更类型（增加/修改/删除）
4. 提供完整的函数体内容
5. 智能token管理和内容分片
"""
import json
import os
import uuid
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from app.codeReview.Regression.db.repository.diff_mapping_repo import DiffMappingRepository
from app.codeReview.Regression.db.repository.regression_task_repo import RegressionTaskRepository
from app.codeReview.Regression.service.ai.ai_tools.tree_sitter_diff_analyzer import TreeSitterDiffAnalyzer
from app.codeReview.Regression.service.ai.prompt.diffMappingPrompt import (
    get_diff_mapping_prompt,
    get_fallback_mapping_prompt, 
    build_change_details_section,
    build_tasks_section
)
from app.codeReview.Regression.service.ai.task_planner.deep_reviewer import estimate_tokens

# 导入回归测试的标准化日志系统
from app.codeReview.Regression.utils.concurrent_logger import (
    log_regression_concurrent_debug,
    log_regression_concurrent_info,
    log_regression_concurrent_error
)

# 导入并发配置
from app.codeReview.Regression.config import AI_CONCURRENT_REQUESTS


class EnhancedDiffMapper:
    """增强的代码差异映射器 - 函数级别变更检测版本"""
    
    def __init__(self, db: Session, analysis_task_id: str):
        self.db = db
        self.analysis_task_id = analysis_task_id
        self.regression_task_repo = RegressionTaskRepository(db)
        self.diff_mapping_repo = DiffMappingRepository(db)
        self.diff_analyzer = TreeSitterDiffAnalyzer(db)
    
    def map_diffs_to_tasks(
        self, 
        ai_client, 
        extract_path: str, 
        impact_report_content: str
    ) -> Dict[str, Any]:
        """
        将代码差异映射到任务（第二阶段的完整实现）
        采用函数级别的变更检测和映射策略
        
        Args:
            ai_client: AI客户端
            extract_path: 代码解压路径
            impact_report_content: 影响域分析报告内容
            
        Returns:
            Dict[str, Any]: 映射结果
        """
        result = {
            "success": False,
            "message": "",
            "total_files": 0,
            "total_changes": 0,
            "total_mappings": 0
        }
        
        try:
            log_regression_concurrent_info(f"[EnhancedDiffMapper] 开始第二阶段：函数级别代码差异映射，analysis_task_id={self.analysis_task_id}")
            
            # 步骤1：获取数据库中的任务列表
            tasks = self.regression_task_repo.get_tasks_by_analysis_id(self.analysis_task_id)
            if not tasks:
                result["message"] = "数据库中没有找到相关任务"
                return result
            
            log_regression_concurrent_info(f"[EnhancedDiffMapper] 从数据库加载了 {len(tasks)} 个任务")
            
            # 步骤2：扫描所有函数级别的变更
            function_changes = self._scan_function_level_changes(extract_path)
            if not function_changes:
                result["message"] = "没有找到函数级别的代码变更"
                result["success"] = True  # 没有变更也算成功
                return result
            
            log_regression_concurrent_info(f"[EnhancedDiffMapper] 扫描到 {len(function_changes)} 个函数级别变更")
            
            # 步骤3：逐个变更进行AI映射分析（支持并发和顺序两种模式）
            total_mappings = 0
            
            # 检查是否启用并发模式（可通过环境变量控制）
            enable_concurrent = os.environ.get("ENABLE_DIFF_MAPPING_CONCURRENT", "true").lower() == "true"
            
            # 支持并发处理的版本（推荐，当变更数量 > 1 且启用并发时）
            if len(function_changes) > 1 and enable_concurrent:
                log_regression_concurrent_info(f"[EnhancedDiffMapper] 使用并发模式处理 {len(function_changes)} 个函数变更")
                total_mappings = self._map_changes_concurrently(ai_client, function_changes, tasks, impact_report_content)
            else:
                mode_reason = "单个变更" if len(function_changes) <= 1 else "并发已禁用"
                log_regression_concurrent_info(f"[EnhancedDiffMapper] 使用顺序模式处理 {len(function_changes)} 个函数变更 ({mode_reason})")
                # 原有的顺序处理方式（保留兼容性）
                for change in function_changes:
                    mapping_result = self._map_single_change_to_tasks(
                        ai_client,
                        change,
                        tasks,
                        impact_report_content
                    )
                    
                    if mapping_result["success"]:
                        total_mappings += mapping_result["mappings_count"]
            
            # 步骤4：提交数据库事务
            self.db.commit()
            
            # 统计处理的文件数量
            processed_files = set(change["file_path"] for change in function_changes)
            
            result["success"] = True
            result["total_files"] = len(processed_files)
            result["total_changes"] = len(function_changes)
            result["total_mappings"] = total_mappings
            result["message"] = f"成功映射 {total_mappings} 个函数变更到任务"
            
            log_regression_concurrent_info(f"[EnhancedDiffMapper] 第二阶段完成：{result['message']}")
            return result
            
        except Exception as e:
            self.db.rollback()
            result["message"] = f"差异映射过程中出错: {str(e)}"
            log_regression_concurrent_error(f"[ERROR] {result['message']}")
            return result
    
    def _scan_function_level_changes(self, extract_path: str) -> List[Dict[str, Any]]:
        """
        扫描所有函数级别的变更
        
        Args:
            extract_path: 代码解压路径
            
        Returns:
            List[Dict[str, Any]]: 函数级别变更列表，每个变更包含：
            - file_path: 文件路径
            - function_name: 函数名
            - change_type: 变更类型 (added/modified/deleted)
            - old_code: 旧版本代码（如果有）
            - new_code: 新版本代码（如果有）
            - change_summary: 变更摘要
        """
        function_changes = []
        
        try:
            # 获取所有文件的差异
            file_diffs = self.diff_analyzer.get_all_file_diffs(extract_path)
            
            for file_path, diff_info in file_diffs.items():
                # 处理每个文件中的函数变更
                file_changes = self._extract_function_changes_from_file(file_path, diff_info)
                function_changes.extend(file_changes)
            
            log_regression_concurrent_info(f"[EnhancedDiffMapper] 总共扫描到 {len(function_changes)} 个函数级别变更")
            return function_changes
            
        except Exception as e:
            log_regression_concurrent_error(f"[ERROR] 扫描函数级别变更时出错: {e}")
            return []
    
    def _extract_function_changes_from_file(
        self, 
        file_path: str, 
        diff_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        从单个文件的差异信息中提取函数级别变更
        
        Args:
            file_path: 文件路径
            diff_info: 文件差异信息
            
        Returns:
            List[Dict[str, Any]]: 该文件的函数级别变更列表（只包含有实质性变更的函数）
        """
        changes = []
        
        try:
            functions = diff_info.get("functions", [])
            
            # 处理函数列表（根据实际的数据结构）
            if isinstance(functions, list):
                for func_info in functions:
                    func_name = func_info.get("function_name", "unknown")
                    change_type = func_info.get("change_type", "unknown")
                    
                    # 只处理有实质性变更的函数，跳过unchanged的函数
                    if change_type == "unchanged":
                        log_regression_concurrent_debug(f"[EnhancedDiffMapper] 跳过未变更的函数: {func_name}")
                        continue
                    
                    # 构建变更信息
                    change = {
                        "file_path": file_path,
                        "function_name": func_name,
                        "change_type": change_type,
                        "old_code": func_info.get("old_code", ""),
                        "new_code": func_info.get("new_code", ""),
                        "change_summary": self._generate_change_summary(func_name, change_type, func_info)
                    }
                    
                    # 添加相似性信息（如果有）
                    if "similarity_score" in func_info:
                        change["similarity_score"] = func_info["similarity_score"]
                        log_regression_concurrent_debug(f"[EnhancedDiffMapper] 函数 {func_name} 变更类型: {change_type}, 相似性: {func_info['similarity_score']:.3f}")
                    else:
                        log_regression_concurrent_debug(f"[EnhancedDiffMapper] 函数 {func_name} 变更类型: {change_type}")
                    
                    changes.append(change)
                    
            elif isinstance(functions, dict):
                # 兼容字典格式
                for func_name, func_info in functions.items():
                    change_type = func_info.get("change_type", "unknown")
                    
                    # 只处理有实质性变更的函数，跳过unchanged的函数
                    if change_type == "unchanged":
                        log_regression_concurrent_debug(f"[EnhancedDiffMapper] 跳过未变更的函数: {func_name}")
                        continue
                    
                    # 构建变更信息
                    change = {
                        "file_path": file_path,
                        "function_name": func_name,
                        "change_type": change_type,
                        "old_code": func_info.get("old_code", ""),
                        "new_code": func_info.get("new_code", ""),
                        "change_summary": self._generate_change_summary(func_name, change_type, func_info)
                    }
                    
                    # 添加相似性信息（如果有）
                    if "similarity_score" in func_info:
                        change["similarity_score"] = func_info["similarity_score"]
                        log_regression_concurrent_debug(f"[EnhancedDiffMapper] 函数 {func_name} 变更类型: {change_type}, 相似性: {func_info['similarity_score']:.3f}")
                    else:
                        log_regression_concurrent_debug(f"[EnhancedDiffMapper] 函数 {func_name} 变更类型: {change_type}")
                    
                    changes.append(change)
                
            log_regression_concurrent_info(f"[EnhancedDiffMapper] 文件 {file_path} 提取了 {len(changes)} 个有实质性变更的函数")
            return changes
            
        except Exception as e:
            log_regression_concurrent_error(f"[ERROR] 提取文件 {file_path} 的函数变更时出错: {e}")
            return []
    
    def _generate_change_summary(
        self, 
        func_name: str, 
        change_type: str, 
        func_info: Dict[str, Any]
    ) -> str:
        """
        生成变更摘要
        
        Args:
            func_name: 函数名
            change_type: 变更类型
            func_info: 函数信息
            
        Returns:
            str: 变更摘要
        """
        if change_type == "added":
            return f"新增函数 {func_name}"
        elif change_type == "deleted":
            return f"删除函数 {func_name}"
        elif change_type == "modified":
            return f"修改函数 {func_name}"
        else:
            return f"函数 {func_name} 发生变更"
    
    def _map_single_change_to_tasks(
        self,
        ai_client,
        change: Dict[str, Any],
        tasks: List[Any],
        impact_report_content: str
    ) -> Dict[str, Any]:
        """
        将单个函数变更映射到任务
        
        Args:
            ai_client: AI客户端
            change: 单个函数变更信息
            tasks: 任务列表
            impact_report_content: 影响域分析报告内容
            
        Returns:
            Dict[str, Any]: 映射结果
        """
        result = {
            "success": False,
            "message": "",
            "mappings_count": 0
        }
        
        try:
            log_regression_concurrent_debug(f"[EnhancedDiffMapper] 开始映射变更: {change['file_path']}::{change['function_name']} ({change['change_type']})")
            
            # 构建单个变更的映射提示词
            prompt = self._build_single_change_mapping_prompt(
                change,
                tasks,
                impact_report_content
            )
            
            # 记录提示词到日志
            timestamp = self._get_timestamp()
            self._save_prompt_to_log(
                prompt, 
                f"single_change_mapping_{timestamp}_{change['function_name']}.txt"
            )
            
            # 调用AI进行映射分析
            call_id = str(uuid.uuid4())[:8]
            log_regression_concurrent_debug(f"[AI分析] 开始单个变更映射分析 (ID: {call_id}, Function: {change['function_name']})")
            
            ai_result, _ = ai_client.call_ai_stream(prompt)
            
            if not isinstance(ai_result, dict):
                result["message"] = f"AI返回格式不正确: {ai_result}"
                return result
            
            # 处理AI返回的映射结果
            mappings_count = self._process_ai_mapping_result(ai_result, change)
            
            result["success"] = True
            result["mappings_count"] = mappings_count
            result["message"] = f"成功映射变更 {change['function_name']} 到 {mappings_count} 个任务"
            
            log_regression_concurrent_debug(f"[AI分析] 完成单个变更映射分析，生成 {mappings_count} 个映射")
            return result
            
        except Exception as e:
            result["message"] = f"映射单个变更时出错: {str(e)}"
            log_regression_concurrent_error(f"[ERROR] 映射单个变更时出错: {e}")
            return result
    
    def _build_single_change_mapping_prompt(
        self,
        change: Dict[str, Any],
        tasks: List[Any],
        impact_report_content: str
    ) -> str:
        """
        构建单个变更的映射提示词（简化版，不使用完整报告内容）
        
        Args:
            change: 单个函数变更信息
            tasks: 任务列表
            impact_report_content: 影响域分析报告内容（不再使用）
            
        Returns:
            str: 提示词
        """
        # 构建变更详情部分
        change_details = build_change_details_section(change)
        
        # 构建任务列表部分（任务中已包含原始报告内容）
        tasks_section = build_tasks_section(tasks)
        
        # 使用简化的提示词模板（不传递报告内容）
        full_prompt = get_diff_mapping_prompt(change_details, tasks_section, "")
        
        final_tokens = estimate_tokens(full_prompt)
        log_regression_concurrent_debug(f"[TOKEN] 简化映射提示词token数: {final_tokens}")
        
        return full_prompt
    
    def _process_report_for_mapping(
        self, 
        report_content: str, 
        change: Dict[str, Any], 
        max_tokens: int
    ) -> str:
        """
        为映射处理报告内容，优先保留与当前变更相关的内容
        """
        if not report_content:
            return "无报告内容"
        
        # 提取与当前变更相关的关键词
        function_name = change.get("function_name", "")
        file_path = change.get("file_path", "")
        
        keywords = []
        if function_name:
            keywords.append(function_name)
        if file_path:
            # 提取文件名（不包含路径）
            filename = os.path.basename(file_path).split('.')[0]
            keywords.append(filename)
        
        # 按行分析报告内容，寻找相关性
        lines = report_content.split('\n')
        relevant_lines = []
        context_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # 检查是否包含关键词
            is_relevant = any(keyword in line for keyword in keywords if keyword)
            
            if is_relevant:
                # 添加相关行及其上下文
                start_idx = max(0, i - 2)
                end_idx = min(len(lines), i + 3)
                context = lines[start_idx:end_idx]
                relevant_lines.extend([l.strip() for l in context if l.strip()])
            elif any(pattern in line for pattern in ['3.1', '3.2', '3.3', '需求变更', '设计变更', '代码变更']):
                # 保留重要的章节标题
                context_lines.append(line)
        
        # 组装内容
        result_lines = []
        
        # 首先添加相关内容
        if relevant_lines:
            result_lines.extend(list(set(relevant_lines)))  # 去重
        
        # 然后添加章节标题作为上下文
        result_lines.extend(context_lines)
        
        # 如果没有找到相关内容，使用通用策略
        if not result_lines:
            return self._compress_report_for_mapping(report_content, change)
        
        # 检查token限制
        current_content = '\n'.join(result_lines)
        current_tokens = estimate_tokens(current_content)
        
        if current_tokens <= max_tokens:
            return current_content
        
        # 如果超过限制，按优先级截断
        truncated_lines = []
        used_tokens = 0
        
        for line in result_lines:
            line_tokens = estimate_tokens(line + '\n')
            if used_tokens + line_tokens <= max_tokens:
                truncated_lines.append(line)
                used_tokens += line_tokens
            else:
                break
        
        result = '\n'.join(truncated_lines)
        if len(truncated_lines) < len(result_lines):
            result += '\n\n...(相关内容已截断)'
        
        return result
    
    def _compress_report_for_mapping(self, report_content: str, change: Dict[str, Any]) -> str:
        """压缩报告内容用于映射"""
        if not report_content:
            return "无报告内容"
        
        # 只保留最重要的信息，限制在500个字符内
        lines = report_content.split('\n')
        important_lines = []
        
        # 查找包含关键变更信息的行
        keywords = ['变更', '需求', '设计', '代码', '新增', '修改', '删除']
        
        for line in lines:
            line = line.strip()
            if any(keyword in line for keyword in keywords) and len(line) > 10:
                important_lines.append(line)
                if len('\n'.join(important_lines)) > 500:
                    break
        
        result = '\n'.join(important_lines)
        if len(result) > 500:
            result = result[:500] + '...'
        
        return result or "报告内容无法提取关键信息"
    
    def _build_fallback_mapping_prompt(
        self, 
        change: Dict[str, Any], 
        tasks: List[Any],
        impact_report_content: str
    ) -> str:
        """
        构建降级映射提示词，当正常提示词超过token限制时使用
        """
        log_regression_concurrent_debug(f"[TOKEN] 构建降级映射提示词")
        
        # 构建简化的变更详情
        function_name = change.get("function_name", "unknown")
        change_type = change.get("change_type", "unknown")
        
        change_details = f"## 代码变更详情\n- 函数名称: {function_name}\n- 变更类型: {change_type}\n\n"
        
        # 构建简化的任务列表（只显示前3个任务）
        limited_tasks = tasks[:3] if len(tasks) > 3 else tasks
        tasks_section = build_tasks_section(limited_tasks)
        
        # 使用降级提示词模板
        fallback_prompt = get_fallback_mapping_prompt(change_details, tasks_section)
        
        final_tokens = estimate_tokens(fallback_prompt)
        log_regression_concurrent_debug(f"[TOKEN] 降级映射提示词token数: {final_tokens}")
        
        return fallback_prompt
    
    def _process_ai_mapping_result(
        self,
        ai_result: Dict[str, Any],
        change: Dict[str, Any]
    ) -> int:
        """
        处理AI映射结果并存储到数据库
        
        Args:
            ai_result: AI返回的映射结果
            change: 原始变更信息
            
        Returns:
            int: 创建的映射记录数量
        """
        mappings_count = 0
        
        try:
            # 获取相关任务ID列表
            related_task_ids = ai_result.get("related_task_ids", [])
            
            # 确保是列表格式
            if not isinstance(related_task_ids, list):
                related_task_ids = [related_task_ids] if related_task_ids else []
            
            # 获取有效的任务ID列表（从数据库中获取）
            from app.codeReview.Regression.db.database import SessionLocal
            from app.codeReview.Regression.db.repository.regression_task_repo import RegressionTaskRepository
            
            temp_db = SessionLocal()
            try:
                task_repo = RegressionTaskRepository(temp_db)
                valid_tasks = task_repo.get_tasks_by_analysis_id(self.analysis_task_id)
                valid_task_ids = [task.task_id for task in valid_tasks]
                
                # 找到最后一个任务ID（其他变更任务）
                last_task_id = None
                if valid_task_ids:
                    # 按数字排序找到最大的任务ID
                    numeric_task_ids = []
                    for task_id in valid_task_ids:
                        try:
                            numeric_task_ids.append((int(task_id), task_id))
                        except ValueError:
                            pass
                    
                    if numeric_task_ids:
                        numeric_task_ids.sort()
                        last_task_id = numeric_task_ids[-1][1]  # 获取最大任务ID
                
            finally:
                temp_db.close()
            
            # 验证和修正AI返回的任务ID
            validated_task_ids = []
            for task_id in related_task_ids:
                task_id_str = str(task_id).strip()
                
                # 严格验证：任务ID必须是纯数字
                if not task_id_str.isdigit():
                    log_regression_concurrent_debug(f"[WARNING] AI返回了非数字任务ID: '{task_id_str}'，格式无效")
                    continue
                
                if task_id_str in valid_task_ids:
                    validated_task_ids.append(task_id_str)
                else:
                    log_regression_concurrent_debug(f"[WARNING] AI返回了无效的任务ID: {task_id_str}, 不在有效任务列表中: {valid_task_ids}")
            
            # 如果没有有效的任务ID，或者AI返回了无效的任务ID，则映射到最后一个任务（其他变更任务）
            if not validated_task_ids and last_task_id:
                validated_task_ids = [last_task_id]
                log_regression_concurrent_debug(f"[MAPPING] 代码变更 {change['function_name']} 没有有效的任务映射，映射到其他变更任务: {last_task_id}")
                
            # 记录验证结果
            if len(validated_task_ids) != len(related_task_ids):
                log_regression_concurrent_debug(f"[VALIDATION] 任务ID验证: 原始={related_task_ids}, 验证后={validated_task_ids}")
            
            # 为每个有效的任务创建映射记录
            for task_id in validated_task_ids:
                if task_id:  # 确保task_id不为空
                    try:
                        # 创建新的数据库会话来避免事务冲突
                        from app.codeReview.Regression.db.repository.diff_mapping_repo import DiffMappingRepository
                        
                        new_db = SessionLocal()
                        try:
                            mapping_repo = DiffMappingRepository(new_db)
                            
                            # 创建映射记录
                            mapping_record = mapping_repo.create_mapping({
                                "analysis_task_id": self.analysis_task_id,
                                "task_id": str(task_id),
                                "file_path": change["file_path"],
                                "function_name": change["function_name"],
                                "change_type": change["change_type"],
                                "old_code": change.get("old_code", ""),
                                "new_code": change.get("new_code", ""),
                                "diff_summary": change.get("change_summary", ""),
                                "mapping_confidence": ai_result.get("mapping_confidence", "low"),
                                "mapping_reason": ai_result.get("mapping_reason", ""),
                                "mapping_score": float(ai_result.get("mapping_score", 0.0)),
                                "mentioned_in_report": ai_result.get("mentioned_in_report", "no")
                            })
                            
                            new_db.commit()
                            mappings_count += 1
                            
                            log_regression_concurrent_debug(f"[DB] 成功创建映射记录: {change['function_name']} -> 任务{task_id}")
                            
                        except Exception as e:
                            new_db.rollback()
                            log_regression_concurrent_error(f"[ERROR] 创建映射记录失败: {e}")
                            raise e
                        finally:
                            new_db.close()
                            
                    except Exception as e:
                        log_regression_concurrent_error(f"[ERROR] 处理任务ID {task_id} 的映射时出错: {e}")
                        continue
            
            # 如果没有有效的映射，记录警告
            if mappings_count == 0:
                log_regression_concurrent_debug(f"[WARNING] 函数 {change['function_name']} 没有有效的任务映射")
            
            return mappings_count
            
        except Exception as e:
            log_regression_concurrent_error(f"[ERROR] 处理AI映射结果时出错: {e}")
            return 0
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        now = datetime.now()
        return now.strftime("%Y%m%d_%H%M%S_%f")
    
    def _save_prompt_to_log(self, prompt: str, filename: str) -> None:
        """保存提示词到日志文件"""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.abspath(os.path.join(base_dir, '..', '..', '..', '..', '..', '..'))
            log_dir = os.path.join(backend_dir, 'app', 'logs', 'prompts')
            os.makedirs(log_dir, exist_ok=True)
            
            log_path = os.path.join(log_dir, filename)
            
            prompt_data = {
                "model": "Qwen/QwQ-32B",
                "temperature": 0.1,
                "max_tokens": 8192,
                "system_prompt": None,
                "prompt": prompt,
                "timestamp": self._get_timestamp()
            }
            
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(prompt_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            log_regression_concurrent_error(f"[ERROR] 保存提示词到日志时出错: {e}") 

    def _map_changes_concurrently(self, ai_client, function_changes: List[Dict[str, Any]], 
                                  tasks: List[Dict[str, Any]], impact_report_content: str) -> int:
        """
        并发处理函数变更映射
        
        Args:
            ai_client: AI客户端
            function_changes: 函数变更列表
            tasks: 任务列表
            impact_report_content: 影响域报告内容
            
        Returns:
            int: 成功映射的总数量
        """
        total_changes = len(function_changes)
        total_mappings = 0
        processed_counter = {'count': 0}
        progress_lock = threading.Lock()
        
        # 使用线程池执行器进行并发处理
        max_workers = min(AI_CONCURRENT_REQUESTS, total_changes)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            log_regression_concurrent_info(f"启动差异映射并发处理，最大并发数: {max_workers}, 总变更数: {total_changes}")
            
            # 提交所有变更映射任务到线程池
            futures = []
            for i, change in enumerate(function_changes):
                future = executor.submit(
                    self._process_single_change_with_new_db,
                    ai_client, change, tasks, impact_report_content, i, 
                    total_changes, processed_counter, progress_lock
                )
                futures.append(future)
            
            # 等待所有任务完成
            for future in as_completed(futures):
                try:
                    mappings_count = future.result()  # 获取映射数量
                    total_mappings += mappings_count
                except Exception as e:
                    log_regression_concurrent_error(f"并发处理变更映射时发生错误", e)
            
            log_regression_concurrent_info(f"差异映射并发处理完成，总映射数: {total_mappings}")
        
        return total_mappings
    
    def _process_single_change_with_new_db(self, ai_client, change: Dict[str, Any], 
                                           tasks: List[Dict[str, Any]], impact_report_content: str,
                                           change_index: int, total_changes: int, 
                                           processed_counter: dict, progress_lock: threading.Lock) -> int:
        """
        使用新数据库会话处理单个变更映射（线程安全版本）
        
        Args:
            ai_client: AI客户端
            change: 变更信息
            tasks: 任务列表
            impact_report_content: 影响域报告内容
            change_index: 变更索引
            total_changes: 总变更数
            processed_counter: 已处理计数器
            progress_lock: 进度更新锁
            
        Returns:
            int: 映射数量
        """
        from ....db.database import get_db
        
        # 为每个线程创建独立的数据库会话
        db_gen = get_db()
        new_db = next(db_gen)
        
        try:
            # 使用实际线程ID设置线程专用日志
            actual_thread_id = threading.current_thread().ident
            thread_name = f"diff_mapper_worker_{actual_thread_id}"
            
            # 检查是否已经设置过线程任务（避免重复初始化）
            from ....utils.concurrent_logger import get_current_regression_thread_info, set_current_regression_thread_task
            current_task_id, current_file_id, current_log_file, current_thread_name = get_current_regression_thread_info()
            
            if current_task_id != self.analysis_task_id or current_thread_name != thread_name:
                # 使用file_id从主对象获取，如果没有则使用默认值
                file_id = getattr(self, 'file_id', 0)  # 如果没有file_id属性，使用默认值
                set_current_regression_thread_task(self.analysis_task_id, file_id, thread_name)
                log_regression_concurrent_info(f"差异映射线程 {thread_name} 初始化完成")
            
            change_name = f"{change['file_path']}::{change['function_name']}"
            log_regression_concurrent_info(f"线程 {thread_name} 开始处理变更: {change_name}")
            
            # 创建临时的EnhancedDiffMapper实例用于线程安全操作
            temp_mapper = EnhancedDiffMapper(new_db, self.analysis_task_id)
            
            # 调用单个变更映射方法
            mapping_result = temp_mapper._map_single_change_to_tasks(
                ai_client,
                change,
                tasks,
                impact_report_content
            )
            
            mappings_count = mapping_result.get("mappings_count", 0) if mapping_result.get("success") else 0
            
            # 更新进度
            with progress_lock:
                processed_counter['count'] += 1
                progress = (processed_counter['count'] / total_changes) * 100
                log_regression_concurrent_info(f"差异映射进度: {processed_counter['count']}/{total_changes} ({progress:.1f}%) - {change_name}")
            
            log_regression_concurrent_info(f"线程 {thread_name} 完成变更处理: {change_name}, 映射数: {mappings_count}")
            return mappings_count
                
        except Exception as e:
            new_db.rollback()
            log_regression_concurrent_error(f"处理变更 {change.get('function_name', 'unknown')} 时发生严重错误", e)
            return 0
            
        finally:
            # 确保数据库会话被正确关闭
            try:
                new_db.close()
            except Exception as e:
                print(f"关闭数据库会话时出错: {e}") 