"""
增强的静态分析问题过滤服务 - 支持规则分类和AI分析
"""
import uuid
import time
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from app.staticAnalysis.filter.models.models import StaticAnalysisSession, StaticAnalysisIssue
from app.staticAnalysis.filter.database.database import get_db_session
from app.staticAnalysis.filter.database.rules_database_factory import get_rules_database, get_cwe_rules_database
from app.staticAnalysis.filter.config.config import FILTER_CONFIG, OUTPUT_COLUMNS, BATCH_PROCESSING_CONFIG
from app.staticAnalysis.filter.utils.logger import setup_session_logger
from app.staticAnalysis.filter.services.excel_processor import ExcelProcessor
from app.staticAnalysis.filter.services.code_analysis_agent_v2 import CodeAnalysisAgentV2
import logging
from datetime import datetime
from sqlalchemy import func

# 模块级日志器，用于统一输出调试信息到主日志/控制台
module_logger = logging.getLogger(__name__)

class EnhancedStaticAnalysisFilterService:
    def __init__(self, session_id: str = None, task_id: int = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.task_id = task_id  # 任务ID（数据库自增ID）
        
        # ===== 双数据库支持 =====
        self.gjb_db = get_rules_database()  # GJB8114规则数据库
        self.cwe_db = get_cwe_rules_database()  # CWE规则数据库
        self.rules_db = self.gjb_db  # 保持向后兼容
        
        # ===== 延迟创建日志器 =====
        # 只有在有task_id时才创建日志器，否则使用临时日志器
        self.log_dir = None
        self.gjb_logger = None
        self.cwe_logger = None
        self.logger = None
        
        if task_id:
            self._init_loggers_with_task_id(task_id)
        else:
            # 创建临时的内存日志器，不写入文件
            self._init_temp_loggers()
        
        # 自定义关键词过滤规则
        self.custom_filters = {}  # 格式: {"GJB_R_01_01_01": ["kw1", "kw2"]}
        
        self.excel_processor = ExcelProcessor(self.session_id)
        
        # 内存进度跟踪变量（保留旧的，用于向后兼容）
        self.total_issues = 0
        self.filtered_issues = 0
        self.processed_issues = 0
        self.ai_analyzed_issues = 0
        self.accurate_issues = 0
        self.uncertain_issues = 0
        self.current_status = "pending"
        self.original_filename = ""
        self.output_filename = ""
        self.codebase_path = None
        self.selected_rules = []
        # 操作人员姓名（由API注入）
        self.operator_name: Optional[str] = None
        
        # 详细进度信息（用于前端显示 - 保留旧的）
        self.current_analyzing_issue = ""
        self.current_issue_index = 0
        self.total_uncertain_issues = 0
        self.tool_calls_count = 0
        
        # ===== 双问题列表 =====
        self.gjb_issues = []  # GJB8114问题
        self.cwe_issues = []  # CWE问题
        
        # ===== 双进度跟踪 =====
        self.gjb_total_issues = 0
        self.gjb_processed_issues = 0
        self.gjb_current_analyzing_issue = ""
        self.gjb_tool_calls_count = 0
        self.gjb_status = "pending"
        self.gjb_accurate_ready = False  # 新增：GJB确定规则是否已就绪
        
        self.cwe_total_issues = 0
        self.cwe_processed_issues = 0
        self.cwe_current_analyzing_issue = ""
        self.cwe_tool_calls_count = 0
        self.cwe_status = "pending"
        self.cwe_accurate_ready = False  # 新增：CWE确定规则是否已就绪
        
        # ===== 预生成文件缓存 =====
        self.gjb_cached_filename = None  # GJB预生成的文件名
        self.cwe_cached_filename = None  # CWE预生成的文件名
    
    def _create_logger(self, rule_type: str):
        """
        创建特定规则类型的日志器
        rule_type: "GJB8114" 或 "CWE"
        """
        logger = logging.getLogger(f"{self.session_id}_{rule_type}")
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        logger.propagate = False
        
        # 日志文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"static_analysis_{rule_type}_{self.session_id}_{timestamp}.log"
        
        file_handler = logging.FileHandler(str(log_file), encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"=" * 100)
        logger.info(f"{rule_type}规则静态分析日志 - 会话ID: {self.session_id}")
        logger.info(f"=" * 100)
        
        return logger
    
    def _init_loggers_with_task_id(self, task_id: int):
        """使用task_id初始化日志器"""
        log_folder = str(task_id)
        self.log_dir = Path(__file__).parent.parent / "logs" / log_folder
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.gjb_logger = self._create_logger("GJB8114")
        self.cwe_logger = self._create_logger("CWE")
        self.logger = self.gjb_logger  # 保持向后兼容
    
    def _init_temp_loggers(self):
        """创建临时的静默日志器，等待task_id后创建文件日志器"""
        import logging
        
        # 创建临时的GJB日志器，使用NullHandler（不输出任何内容）
        self.gjb_logger = logging.getLogger(f"StaticAnalysis_GJB_{self.session_id}")
        self.gjb_logger.setLevel(logging.DEBUG)
        self.gjb_logger.handlers.clear()
        self.gjb_logger.addHandler(logging.NullHandler())
        self.gjb_logger.propagate = False
        
        # 创建临时的CWE日志器
        self.cwe_logger = logging.getLogger(f"StaticAnalysis_CWE_{self.session_id}")
        self.cwe_logger.setLevel(logging.DEBUG)
        self.cwe_logger.handlers.clear()
        self.cwe_logger.addHandler(logging.NullHandler())
        self.cwe_logger.propagate = False
        
        # 保持向后兼容
        self.logger = self.gjb_logger
    
    def _switch_to_task_id_logging(self):
        """从临时日志器切换到使用task_id的文件日志器"""
        if not self.task_id:
            return
        
        # 创建task_id日志目录和文件日志器
        self._init_loggers_with_task_id(self.task_id)
        
        # 记录切换完成
        self.gjb_logger.info(f"已切换到文件日志器 - Task ID: {self.task_id}, 日志目录: {self.log_dir}")
        self.cwe_logger.info(f"已切换到文件日志器 - Task ID: {self.task_id}, 日志目录: {self.log_dir}")
        
        # 清理可能存在的session_id临时文件夹
        self._cleanup_temp_session_folder()
        
        # 切换到任务日志后再次记录操作人员，确保写入任务日志目录
        if self.operator_name:
            self.gjb_logger.info(f"操作人员: {self.operator_name}")
            self.cwe_logger.info(f"操作人员: {self.operator_name}")
    
    def _cleanup_temp_session_folder(self):
        """清理可能存在的session_id临时文件夹"""
        try:
            import shutil
            temp_session_dir = Path(__file__).parent.parent / "logs" / self.session_id
            if temp_session_dir.exists() and temp_session_dir.is_dir():
                self.gjb_logger.info(f"清理临时session文件夹: {temp_session_dir}")
                shutil.rmtree(temp_session_dir)
                self.gjb_logger.info(f"临时session文件夹已清理")
        except Exception as e:
            self.gjb_logger.warning(f"清理临时session文件夹失败: {e}")
        
    def process_uploaded_files(self, excel_file_path: str, original_filename: str, 
                             codebase_path: str, selected_rules: List[str] = None, 
                             filter_keywords: List[str] = None, custom_filters: Dict[str, List[str]] = None, 
                             max_issues_per_rule: int = 0) -> Dict[str, Any]:
        """备份版本实现：处理上传Excel和代码库，使用稳定的双sheet解析和批量入库逻辑"""
        try:
            self.gjb_logger.info(f"开始处理上传文件: {original_filename}")
            self.cwe_logger.info(f"开始处理上传文件: {original_filename}")
            
            # 初始化进度跟踪
            self.original_filename = original_filename
            self.codebase_path = codebase_path
            self.current_status = "processing"
            self.selected_rules = selected_rules or []
            self.custom_filters = custom_filters or {}
            self.max_issues_per_rule = max_issues_per_rule
            
            # 记录用户选择的规则
            if self.selected_rules:
                self.gjb_logger.info(f"用户选择了 {len(self.selected_rules)} 个规则，将只处理这些规则对应的问题")
                self.cwe_logger.info(f"用户选择了 {len(self.selected_rules)} 个规则，将只处理这些规则对应的问题")
            else:
                self.gjb_logger.info("用户未指定规则选择，将处理所有问题")
                self.cwe_logger.info("用户未指定规则选择，将处理所有问题")
            
            # 记录自定义过滤规则
            if self.custom_filters:
                self.gjb_logger.info(f"应用自定义过滤规则: {len(self.custom_filters)} 条")
                self.cwe_logger.info(f"应用自定义过滤规则: {len(self.custom_filters)} 条")
                for rule_code, keywords in self.custom_filters.items():
                    self.gjb_logger.info(f"  {rule_code}: 同时包含关键词 {keywords} 的问题将被过滤")
                    self.cwe_logger.info(f"  {rule_code}: 同时包含关键词 {keywords} 的问题将被过滤")
            
            # 记录问题数量限制配置
            if self.max_issues_per_rule > 0:
                self.gjb_logger.info(f"每个规则最多保留 {self.max_issues_per_rule} 个问题（采用均匀分布采样）")
                self.cwe_logger.info(f"每个规则最多保留 {self.max_issues_per_rule} 个问题（采用均匀分布采样）")
            else:
                self.gjb_logger.info("不限制每个规则的问题数量")
                self.cwe_logger.info("不限制每个规则的问题数量")
            
            # 解析Excel中的双sheet（与备份版本一致）
            import openpyxl
            wb = openpyxl.load_workbook(excel_file_path)
            
            # 解析GJB8114 sheet
            gjb_sheet_name = "GJB_8114（国家军用标准CC++语言可靠性编程规范）"
            if gjb_sheet_name in wb.sheetnames:
                self.gjb_logger.info(f"开始解析GJB8114 sheet: {gjb_sheet_name}")
                self.gjb_issues = self._parse_excel_sheet(wb[gjb_sheet_name], "gjb", self.gjb_db, self.gjb_logger)
                gjb_all_count = len(self.gjb_issues)
                self.gjb_logger.info(f"GJB8114 sheet解析完成，发现 {gjb_all_count} 个问题")
                
                # 统计确定和不确定规则的数量
                gjb_accurate_count = sum(1 for issue in self.gjb_issues if issue.get('accuracy_type') == 'accurate')
                gjb_uncertain_count = sum(1 for issue in self.gjb_issues if issue.get('accuracy_type') == 'uncertain')
                self.gjb_logger.info(f"GJB8114分类: 确定规则 {gjb_accurate_count} 个, 不确定规则 {gjb_uncertain_count} 个")
                
                # 设置 gjb_total_issues 为需要AI处理的不确定问题数量
                self.gjb_total_issues = gjb_uncertain_count
                
                # [FIX] 不在这里设置 accurate_ready，等数据入库和文件预生成后再设置
                
                if gjb_all_count == 0:
                    self.gjb_logger.warning(f"GJB8114 sheet为空，无问题需要处理，直接标记为完成")
                    self.gjb_status = "completed"
            else:
                self.gjb_logger.warning(f"未找到GJB8114 sheet: {gjb_sheet_name}，直接标记为完成")
                self.gjb_issues = []
                self.gjb_total_issues = 0
                self.gjb_status = "completed"
                self.gjb_accurate_ready = True
            
            # 解析CWE sheet
            cwe_sheet_name = "C_CPP缺陷检测项（CWE通用缺陷）"
            if cwe_sheet_name in wb.sheetnames:
                self.cwe_logger.info(f"开始解析CWE sheet: {cwe_sheet_name}")
                self.cwe_issues = self._parse_excel_sheet(wb[cwe_sheet_name], "cwe", self.cwe_db, self.cwe_logger)
                cwe_all_count = len(self.cwe_issues)
                self.cwe_logger.info(f"CWE sheet解析完成，发现 {cwe_all_count} 个问题")
                
                # 统计确定和不确定规则的数量
                cwe_accurate_count = sum(1 for issue in self.cwe_issues if issue.get('accuracy_type') == 'accurate')
                cwe_uncertain_count = sum(1 for issue in self.cwe_issues if issue.get('accuracy_type') == 'uncertain')
                self.cwe_logger.info(f"CWE分类: 确定规则 {cwe_accurate_count} 个, 不确定规则 {cwe_uncertain_count} 个")
                
                # 设置 cwe_total_issues 为需要AI处理的不确定问题数量
                self.cwe_total_issues = cwe_uncertain_count
                
                # [FIX] 不在这里设置 accurate_ready，等数据入库和文件预生成后再设置
                
                if cwe_all_count == 0:
                    self.cwe_logger.warning(f"CWE sheet为空，无问题需要处理，直接标记为完成")
                    self.cwe_status = "completed"
            else:
                self.cwe_logger.warning(f"未找到CWE sheet: {cwe_sheet_name}，直接标记为完成")
                self.cwe_issues = []
                self.cwe_total_issues = 0
                self.cwe_status = "completed"
                self.cwe_accurate_ready = True
            
            # 计算全部问题总数（用于向后兼容）
            gjb_all_total = len(self.gjb_issues)
            cwe_all_total = len(self.cwe_issues)
            self.total_issues = gjb_all_total + cwe_all_total
            
            # 应用问题数量采样（与备份版本一致）
            if self.max_issues_per_rule > 0:
                self.gjb_logger.info(f"开始对GJB8114问题应用均匀分布采样，每个规则最多保留 {self.max_issues_per_rule} 个问题")
                self.cwe_logger.info(f"开始对CWE问题应用均匀分布采样，每个规则最多保留 {self.max_issues_per_rule} 个问题")
                
                original_gjb_count = len(self.gjb_issues)
                original_cwe_count = len(self.cwe_issues)
                
                self.gjb_issues = self._apply_distributed_sampling(self.gjb_issues, self.gjb_logger)
                self.cwe_issues = self._apply_distributed_sampling(self.cwe_issues, self.cwe_logger)
                
                # 采样后重新统计全部问题数量
                gjb_all_total = len(self.gjb_issues)
                cwe_all_total = len(self.cwe_issues)
                self.total_issues = gjb_all_total + cwe_all_total
                
                # 重新统计不确定问题数量（需要AI处理的）
                gjb_uncertain_after_sampling = sum(1 for issue in self.gjb_issues if issue.get('accuracy_type') == 'uncertain')
                cwe_uncertain_after_sampling = sum(1 for issue in self.cwe_issues if issue.get('accuracy_type') == 'uncertain')
                self.gjb_total_issues = gjb_uncertain_after_sampling
                self.cwe_total_issues = cwe_uncertain_after_sampling
                
                self.gjb_logger.info(f"GJB8114采样完成：{original_gjb_count} -> {gjb_all_total} 个问题（不确定: {gjb_uncertain_after_sampling}）")
                self.cwe_logger.info(f"CWE采样完成：{original_cwe_count} -> {cwe_all_total} 个问题（不确定: {cwe_uncertain_after_sampling}）")
            
            # 保存到数据库
            self._save_issues_to_database(excel_file_path, original_filename)
            
            # [FIX] 数据入库完成后，预生成文件缓存，然后再设置 accurate_ready
            self._pre_generate_cache_files()
            
            # [FIX] 所有准备工作完成后，设置 accurate_ready = True
            if gjb_all_total > 0 or len(self.gjb_issues) > 0:
                self.gjb_accurate_ready = True
                self.gjb_logger.info(f"GJB文件缓存已生成，设置 accurate_ready = True")
            
            if cwe_all_total > 0 or len(self.cwe_issues) > 0:
                self.cwe_accurate_ready = True
                self.cwe_logger.info(f"CWE文件缓存已生成，设置 accurate_ready = True")
            
            self.gjb_logger.info(f"文件处理成功 - 会话ID: {self.session_id}")
            self.cwe_logger.info(f"文件处理成功 - 会话ID: {self.session_id}")
            
            return {
                "success": True,
                "gjb_count": self.gjb_total_issues,
                "cwe_count": self.cwe_total_issues,
                "total_issues": self.total_issues
            }
                
        except Exception as e:
            self.current_status = "error"
            error_msg = f"处理上传文件时出错: {str(e)}"
            self.gjb_logger.error(error_msg)
            self.cwe_logger.error(error_msg)
            import traceback
            self.gjb_logger.error(traceback.format_exc())
            return {"success": False, "error": error_msg}
    
    def _apply_distributed_sampling(self, issues: List[Dict], logger) -> List[Dict]:
        """
        对问题列表应用均匀分布采样，每个规则最多保留max_issues_per_rule个问题
        
        Args:
            issues: 问题列表
            logger: 日志器
            
        Returns:
            采样后的问题列表
        """
        if not issues or self.max_issues_per_rule <= 0:
            return issues
        
        # 按规则代码分组
        from collections import defaultdict
        issues_by_rule = defaultdict(list)
        for issue in issues:
            rule_code = issue.get('rule_code', 'UNKNOWN')
            issues_by_rule[rule_code].append(issue)
        
        sampled_issues = []
        for rule_code, rule_issues in issues_by_rule.items():
            original_count = len(rule_issues)
            
            if original_count <= self.max_issues_per_rule:
                # 问题数量未超过限制，保留全部
                sampled_issues.extend(rule_issues)
            else:
                # 应用均匀分布采样
                # 计算采样间隔
                step = original_count / self.max_issues_per_rule
                sampled_indices = [int(i * step) for i in range(self.max_issues_per_rule)]
                
                # 确保最后一个索引有效
                sampled_indices = [min(idx, original_count - 1) for idx in sampled_indices]
                
                # 采样
                sampled = [rule_issues[idx] for idx in sampled_indices]
                sampled_issues.extend(sampled)
                
                logger.info(f"规则 {rule_code}: 采样 {original_count} -> {len(sampled)} 个问题")
        
        return sampled_issues
    
    def _parse_excel_sheet(self, sheet, rule_type: str, db, logger) -> List[Dict]:
        """备份版本实现：解析单个Excel sheet 并按规则分类"""
        issues = []
        
        try:
            # 读取表头
            headers = {}
            for col in range(1, sheet.max_column + 1):
                header = sheet.cell(1, col).value
                if header:
                    headers[header] = col
            
            logger.info(f"找到列: {list(headers.keys())}")
            
            # 查找关键列
            name_col = headers.get("缺陷名称") or headers.get("问题名称")
            file_col = headers.get("文件路径") or headers.get("问题文件")
            line_col = headers.get("行号") or headers.get("问题行号")
            desc_col = headers.get("缺陷说明") or headers.get("问题描述")
            
            if not all([name_col, file_col, line_col]):
                logger.error("缺少必要的列")
                return issues
            
            # 读取数据行
            filtered_count = 0  # 统计被过滤掉的问题数
            for row in range(2, sheet.max_row + 1):
                issue_name = sheet.cell(row, name_col).value
                if not issue_name:
                    continue
                
                # 调试：记录原始缺陷名称，便于定位匹配问题
                logger.debug(f"[{rule_type.upper()}] 原始缺陷名称: {str(issue_name)[:120]}")
                
                issue_file = sheet.cell(row, file_col).value
                issue_line = sheet.cell(row, line_col).value
                issue_desc = sheet.cell(row, desc_col).value if desc_col else ""
                
                # 分类问题（这里会调用已增强的规则数据库，包括GJB编号补零和前缀转换）
                accuracy_type, rule_info = db.classify_issue_by_rule_name(str(issue_name))
                if rule_info:
                    logger.info(f"[{rule_type.upper()}] 分类成功: {accuracy_type} -> {rule_info.get('rule_code')} | 原始: {str(issue_name)[:80]}")
                else:
                    logger.warning(f"[{rule_type.upper()}] 分类失败: {accuracy_type} | 原始: {str(issue_name)[:100]}")
                
                # 规则编号
                rule_code = rule_info.get("rule_code") if rule_info else None
                
                # 记录到 issues 列表（与备份版本结构一致）
                issues.append({
                    "issue_name": str(issue_name),
                    "issue_file": str(issue_file) if issue_file else "",
                    "issue_line": int(issue_line) if issue_line else 0,
                    "issue_description": str(issue_desc) if issue_desc else "",
                    "rule_type": rule_type,
                    "accuracy_type": accuracy_type,
                    "rule_code": rule_code,
                    "gjb_rule_code": (rule_code if (rule_code and rule_type == "gjb") else ""),
                    "rule_info": rule_info,
                    "is_filtered": False,
                    "ai_analysis": None
                })
            
            logger.info(f"从sheet中读取了 {len(issues)} 个问题")
            return issues
            
        except Exception as e:
            logger.error(f"解析sheet时出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return issues

    async def _phase2_ai_analysis(self, issues: List[StaticAnalysisIssue]):
        """第二阶段：AI分析不确定规则的问题"""
        self.logger.info("开始第二阶段：AI分析不确定规则的问题")
        
        # 更新状态为AI分析中
        self._update_session_status("ai_analyzing")
        self.current_status = "ai_analyzing"
        
        # 获取需要AI分析的问题（不确定规则且未被过滤的问题），并按 GJB/CWE 分开
        self.logger.info(f"第二阶段收到 {len(issues)} 个问题")
        
        # 调试：检查每个问题的属性
        for issue in issues:
            rule_type = getattr(issue, 'rule_accuracy_type', None)
            is_filtered = issue.is_filtered
            self.logger.debug(f"问题ID {issue.id}: rule_accuracy_type={rule_type}, is_filtered={is_filtered}")
        
        # 筛选需要AI分析的问题：不确定规则 + 未被过滤 + 勾选的规则
        selected_rules_set = set(self.selected_rules) if self.selected_rules else set()
        
        uncertain_gjb = [
            issue for issue in issues
            if not issue.is_filtered
            and getattr(issue, 'rule_accuracy_type', None) == 'uncertain'
            and getattr(issue, 'rule_type', None) == 'gjb'
            and (not selected_rules_set or getattr(issue, 'rule_code', None) in selected_rules_set)
        ]
        uncertain_cwe = [
            issue for issue in issues
            if not issue.is_filtered
            and getattr(issue, 'rule_accuracy_type', None) == 'uncertain'
            and getattr(issue, 'rule_type', None) == 'cwe'
            and (not selected_rules_set or getattr(issue, 'rule_code', None) in selected_rules_set)
        ]
        
        # [FIX] 用实际筛选出的"勾选规则的不确定问题数"更新total_issues
        # 这样前端进度条才能正确显示（例如：1/1 而不是 1/2）
        self.gjb_total_issues = len(uncertain_gjb)
        self.cwe_total_issues = len(uncertain_cwe)
        
        # 更新状态（如果有不确定问题需要处理）
        if len(uncertain_gjb) > 0:
            self.gjb_status = "processing"
            self.gjb_logger.info(f"GJB有 {len(uncertain_gjb)} 个不确定问题需要AI分析（已过滤勾选规则）")
        else:
            # 如果没有需要AI分析的GJB问题，直接标记为完成
            self.gjb_status = "completed"
            self.gjb_logger.info(f"GJB没有需要AI分析的问题（勾选规则中无不确定问题），标记为完成")
        
        if len(uncertain_cwe) > 0:
            self.cwe_status = "processing"
            self.cwe_logger.info(f"CWE有 {len(uncertain_cwe)} 个不确定问题需要AI分析（已过滤勾选规则）")
        else:
            # 如果没有需要AI分析的CWE问题，直接标记为完成
            self.cwe_status = "completed"
            self.cwe_logger.info(f"CWE没有需要AI分析的问题（勾选规则中无不确定问题），标记为完成")
        
        total_uncertain_issues = self.gjb_total_issues + self.cwe_total_issues
        self.logger.info(f"筛选出需要AI分析的问题: GJB={self.gjb_total_issues}, CWE={self.cwe_total_issues}, 合计={total_uncertain_issues}")
        if total_uncertain_issues == 0:
            self.logger.warning("没有需要AI分析的问题 - 可能是rule_accuracy_type未正确设置")
            return
        
        # 更新详细进度信息（保持向后兼容）
        self.total_uncertain_issues = total_uncertain_issues
        
        # [并行优化] 创建两个独立的协程分别处理GJB和CWE，实现并行AI审查
        async def analyze_issues_batch(issues: list, rule_type: str):
            """并行处理一批问题的AI分析"""
            if not issues:
                return
            
            # 为每个批次创建独立的Agent，使用任务专属的logger
            task_logger = self.gjb_logger if rule_type == 'gjb' else self.cwe_logger
            agent = CodeAnalysisAgentV2(self.session_id, self.codebase_path, logger=task_logger)
            
            for i, issue in enumerate(issues, 1):
                try:
                    issue_name = issue.issue_name
                    
                    # 更新分类型的当前分析项
                    if rule_type == 'gjb':
                        self.gjb_current_analyzing_issue = issue_name
                    else:
                        self.cwe_current_analyzing_issue = issue_name
                    
                    self.logger.info(f"[{rule_type.upper()}] AI分析进度: {i}/{len(issues)} - {issue_name}")
                    
                    # 获取规则信息
                    rule_info = None
                    if hasattr(issue, 'gjb_rule_code') and issue.gjb_rule_code:
                        rule_info = self.rules_db.get_rule_by_code(issue.gjb_rule_code)
                    elif hasattr(issue, 'rule_code') and issue.rule_code:
                        rule_info = self.rules_db.get_rule_by_code(issue.rule_code)
                    
                    if not rule_info:
                        accuracy_type, rule_info = self.rules_db.classify_issue_by_rule_name(issue_name or "")
                    
                    if not rule_info:
                        self.logger.warning(f"[{rule_type.upper()}] 无法获取问题的规则信息: {issue_name}")
                        # [FIX] 即使无法获取规则信息，也要更新进度计数，避免前端进度条卡住
                        if rule_type == 'gjb':
                            self.gjb_processed_issues += 1
                        else:
                            self.cwe_processed_issues += 1
                        continue
                    
                    # 准备问题数据
                    issue_data = {
                        "issue_name": issue.issue_name,
                        "issue_file": issue.issue_file,
                        "issue_line": issue.issue_line,
                        "issue_description": issue.issue_description
                    }
                    
                    # 执行AI分析
                    analysis_result = agent.analyze_uncertain_issue(issue_data, rule_info)
                    
                    # 更新数据库
                    self._update_issue_ai_analysis(issue.id, analysis_result)
                    
                    # 如果AI判断为误报且置信度高，标记为过滤
                    if not analysis_result.get("is_real_issue") and analysis_result.get("confidence", 0) >= 0.7:
                        self.logger.info(f"[{rule_type.upper()}] AI判断为误报（置信度{analysis_result.get('confidence')}），标记为过滤")
                        db = get_db_session()
                        try:
                            issue_to_filter = db.query(StaticAnalysisIssue).filter(
                                StaticAnalysisIssue.id == issue.id
                            ).first()
                            if issue_to_filter:
                                issue_to_filter.is_filtered = True
                                issue_to_filter.filter_reason = f"AI判断为误报（置信度{analysis_result.get('confidence')}）"
                                db.commit()
                                self.logger.info(f"[{rule_type.upper()}] 问题 {issue.id} 已标记为过滤")
                        finally:
                            db.close()
                    
                    # 更新分类型的已处理计数
                    if rule_type == 'gjb':
                        self.gjb_processed_issues += 1
                        self.gjb_tool_calls_count = agent.tool_call_count
                    else:
                        self.cwe_processed_issues += 1
                        self.cwe_tool_calls_count = agent.tool_call_count
                    
                    # 每分析5个问题记录一次进度
                    if i % 5 == 0:
                        self.logger.info(f"[{rule_type.upper()}] AI分析进度: {i}/{len(issues)}")
                    
                except Exception as e:
                    self.logger.error(f"[{rule_type.upper()}] AI分析问题 {issue.id} 时出错: {str(e)}")
                    # [FIX] 即使AI分析出错，也要更新进度计数，避免前端进度条卡住
                    if rule_type == 'gjb':
                        self.gjb_processed_issues += 1
                    else:
                        self.cwe_processed_issues += 1
                    continue
        
        # [并行执行] 同时启动GJB和CWE的AI分析任务
        self.logger.info("开始并行AI分析: GJB和CWE同时进行")
        await asyncio.gather(
            analyze_issues_batch(uncertain_gjb, 'gjb'),
            analyze_issues_batch(uncertain_cwe, 'cwe')
        )
        
        # 统计总的AI分析数量
        total_analyzed = self.gjb_processed_issues + self.cwe_processed_issues
        self.logger.info(f"第二阶段完成 - AI分析了{total_analyzed}个问题 (GJB: {self.gjb_processed_issues}, CWE: {self.cwe_processed_issues})")
        
        # 重新统计过滤数量（包括AI判断为误报的）
        db = get_db_session()
        try:
            filtered_count = db.query(StaticAnalysisIssue).filter(
                StaticAnalysisIssue.task_id == self.task_id,
                StaticAnalysisIssue.is_filtered == True
            ).count()
            self.filtered_issues = filtered_count
            self.logger.info(f"AI分析后，总过滤数量: {filtered_count}")
        finally:
            db.close()
        
        # 标记分类型状态完成
        if self.gjb_total_issues == 0 or self.gjb_processed_issues >= self.gjb_total_issues:
            self.gjb_status = "completed"
        if self.cwe_total_issues == 0 or self.cwe_processed_issues >= self.cwe_total_issues:
            self.cwe_status = "completed"
    
    async def _phase3_generate_results(self):
        """第三阶段：生成最终结果"""
        self.logger.info("开始第三阶段：生成最终结果")
        
        # 生成输出文件
        self.logger.info("开始自动生成Excel输出文件")
        output_result = self.generate_enhanced_output_file()
        
        if output_result["success"]:
            self.output_filename = output_result["filename"]
            self.logger.info(f"Excel文件自动生成成功: {self.output_filename}")
        
        self.logger.info("第三阶段完成")
    
    def _apply_basic_filter_rules(self, issue: StaticAnalysisIssue) -> Tuple[bool, str]:
        """
        应用基础过滤规则（保持原有逻辑）
        """
        issue_name = issue.issue_name or ""
        
        # 1. 检查排除关键字
        for keyword in FILTER_CONFIG["exclude_keywords"]:
            if keyword in issue_name:
                return True, f"包含排除关键字: {keyword}"
        
        # 2. 检查名称长度
        if len(issue_name) < FILTER_CONFIG["min_name_length"]:
            return True, f"问题名称过短: {len(issue_name)}字符"
        
        # 3. 检查是否包含有效关键字
        has_valid_keyword = False
        for keyword in FILTER_CONFIG["include_keywords"]:
            if keyword in issue_name:
                has_valid_keyword = True
                break
        
        if not has_valid_keyword:
            return True, "不包含有效关键字"
        
        return False, ""  # 不过滤
    
    async def process_session_enhanced(self) -> Dict[str, Any]:
        """
        增强流程总控：在已完成上传/解析/入库后，执行AI分析与结果生成。
        由 API 后台任务调用。
        """
        try:
            self.logger.info("开始增强会话处理 (process_session_enhanced)")
            if not self.task_id:
                # 尝试通过已有状态推断task_id是否已设置
                self.logger.warning("task_id 未设置，可能未完成入库阶段。将继续尝试，但可能无可分析的问题。")
            
            # 读取当前任务的所有问题
            db = get_db_session()
            try:
                issues = db.query(StaticAnalysisIssue).filter(
                    StaticAnalysisIssue.task_id == self.task_id
                ).all()
            finally:
                db.close()

            self.logger.info(f"读取到 {len(issues)} 条问题，开始AI分析阶段")
            await self._phase2_ai_analysis(issues)

            self.logger.info("AI分析完成，开始结果生成阶段")
            await self._phase3_generate_results()

            self.current_status = "completed"
            self._update_session_status("completed")  # 更新数据库中的状态为completed
            self.logger.info("增强会话处理完成")
            return {"success": True, "message": "增强处理完成"}
        except Exception as e:
            import traceback
            self.current_status = "error"
            self._update_session_status("error")  # 更新数据库中的状态为error
            self.logger.error(f"增强会话处理失败: {e}")
            self.logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
    def _update_session_codebase_path(self, codebase_path: str):
        """更新会话的代码库路径"""
        if not codebase_path:
            return
            
        db = get_db_session()
        try:
            session = db.query(StaticAnalysisSession).filter(
                StaticAnalysisSession.session_id == self.session_id
            ).first()
            
            if session:
                session.codebase_path = codebase_path
                db.commit()
        finally:
            db.close()
    
    def _save_issues_to_database(self, file_path: str, original_filename: str):
        """保存问题数据到数据库"""
        try:
            self.gjb_logger.info(f"开始保存问题数据到数据库 - 会话ID: {self.session_id}")
            self.gjb_logger.info(f"GJB问题数: {len(self.gjb_issues)}, CWE问题数: {len(self.cwe_issues)}")
            
            db = get_db_session()
            
            try:
                # 1. 创建会话记录
                session = StaticAnalysisSession(
                    session_id=self.session_id,
                    original_filename=original_filename,
                    file_path=file_path,
                    codebase_path=self.codebase_path,
                    status="processing",
                    total_issues=self.total_issues,
                    accurate_issues=0,
                    uncertain_issues=0,
                    filtered_issues=0
                )
                db.add(session)
                
                # 【修复】在add之后、commit之前设置operator_name
                if self.operator_name:
                    session.operator_name = self.operator_name
                    self.gjb_logger.info(f"设置操作人员: {self.operator_name}")
                
                db.commit()
                db.refresh(session)  # 刷新以获取自增ID
                
                # 获取任务ID并重新创建日志器
                self.task_id = session.id
                self.gjb_logger.info(f"会话记录已创建 - Session ID: {self.session_id}, Task ID: {self.task_id}")
                
                # 立即切换到task_id日志目录
                self._switch_to_task_id_logging()
                # 切换到任务日志后再次记录操作人员，确保写入任务日志目录
                if self.operator_name:
                    self.gjb_logger.info(f"操作人员: {self.operator_name}")
                    self.cwe_logger.info(f"操作人员: {self.operator_name}")
                
                # ===== 在入库后，计算每类问题的AI待处理总数与初始状态 =====
                # [FIX] 不在这里设置 accurate_ready，等文件预生成后再设置
                try:
                    self.gjb_total_issues = sum(1 for i in self.gjb_issues if i.get("accuracy_type") == "uncertain")
                    self.cwe_total_issues = sum(1 for i in self.cwe_issues if i.get("accuracy_type") == "uncertain")
                    # 初始状态：如果有不确定问题则为processing，否则直接completed
                    self.gjb_status = "processing" if self.gjb_total_issues > 0 else "completed"
                    self.cwe_status = "processing" if self.cwe_total_issues > 0 else "completed"
                    self.gjb_logger.info(f"初始进度: GJB 待AI={self.gjb_total_issues}, 状态={self.gjb_status}")
                    self.cwe_logger.info(f"初始进度: CWE 待AI={self.cwe_total_issues}, 状态={self.cwe_status}")
                except Exception as _e:
                    self.gjb_logger.warning(f"初始化进度信息失败: {_e}")
                
                # 2. 批量插入问题记录
                from ..config.config import BATCH_PROCESSING_CONFIG
                BATCH_SIZE = BATCH_PROCESSING_CONFIG["db_insert_batch_size"]
                
                # 合并所有问题
                all_issues = []
                
                # 添加GJB问题
                try:
                    gjb_acc_cnt = sum(1 for i in self.gjb_issues if i.get("accuracy_type") == "accurate")
                    gjb_unc_cnt = sum(1 for i in self.gjb_issues if i.get("accuracy_type") == "uncertain")
                    gjb_unk_cnt = sum(1 for i in self.gjb_issues if i.get("accuracy_type") not in ("accurate", "uncertain"))
                    self.gjb_logger.info(f"GJB保存前分类统计: accurate={gjb_acc_cnt}, uncertain={gjb_unc_cnt}, unknown={gjb_unk_cnt}")
                except Exception as _e:
                    self.gjb_logger.warning(f"统计GJB分类信息失败: {str(_e)}")
                for issue in self.gjb_issues:
                    all_issues.append(StaticAnalysisIssue(
                        task_id=self.task_id,
                        row_index=issue.get("row_index", 0),
                        sheet_name=issue.get("sheet_name", ""),
                        issue_name=issue.get("issue_name", ""),
                        issue_file=issue.get("issue_file", ""),
                        issue_line=issue.get("issue_line", ""),
                        issue_description=issue.get("issue_description", ""),
                        gjb_rule_code=issue.get("gjb_rule_code", ""),
                        rule_type="gjb",  # 标记为GJB类型
                        rule_code=issue.get("rule_code", ""),
                        rule_accuracy_type=issue.get("accuracy_type", "unknown"),  # 保存准确度类型
                        is_filtered=False
                    ))
                
                # 添加CWE问题
                try:
                    cwe_acc_cnt = sum(1 for i in self.cwe_issues if i.get("accuracy_type") == "accurate")
                    cwe_unc_cnt = sum(1 for i in self.cwe_issues if i.get("accuracy_type") == "uncertain")
                    cwe_unk_cnt = sum(1 for i in self.cwe_issues if i.get("accuracy_type") not in ("accurate", "uncertain"))
                    self.gjb_logger.info(f"CWE保存前分类统计: accurate={cwe_acc_cnt}, uncertain={cwe_unc_cnt}, unknown={cwe_unk_cnt}")
                except Exception as _e:
                    self.gjb_logger.warning(f"统计CWE分类信息失败: {str(_e)}")
                for issue in self.cwe_issues:
                    all_issues.append(StaticAnalysisIssue(
                        task_id=self.task_id,
                        row_index=issue.get("row_index", 0),
                        sheet_name=issue.get("sheet_name", ""),
                        issue_name=issue.get("issue_name", ""),
                        issue_file=issue.get("issue_file", ""),
                        issue_line=issue.get("issue_line", ""),
                        issue_description=issue.get("issue_description", ""),
                        gjb_rule_code="",  # CWE问题没有GJB编号
                        rule_type="cwe",  # 标记为CWE类型
                        rule_code=issue.get("rule_code", ""),
                        rule_accuracy_type=issue.get("accuracy_type", "unknown"),  # 保存准确度类型
                        is_filtered=False
                    ))
                
                # 分批插入
                total_batches = (len(all_issues) + BATCH_SIZE - 1) // BATCH_SIZE
                self.gjb_logger.info(f"将分{total_batches}个批次插入{len(all_issues)}条问题记录")
                
                for batch_idx in range(0, len(all_issues), BATCH_SIZE):
                    batch_issues = all_issues[batch_idx:batch_idx + BATCH_SIZE]
                    current_batch = (batch_idx // BATCH_SIZE) + 1
                    
                    self.gjb_logger.info(f"插入第{current_batch}/{total_batches}批次，{len(batch_issues)}条记录")
                    db.add_all(batch_issues)
                    db.commit()
                
                self.gjb_logger.info(f"问题数据保存完成 - 总计: {len(all_issues)}条")
                
            except Exception as e:
                db.rollback()
                self.gjb_logger.error(f"保存问题数据失败: {str(e)}")
                import traceback
                self.gjb_logger.error(traceback.format_exc())
                raise
            finally:
                db.close()
                
        except Exception as e:
            self.gjb_logger.error(f"保存问题数据到数据库时出错: {str(e)}")
            raise
    
    def _pre_generate_cache_files(self):
        """
        预生成文件缓存，避免用户点击下载时文件还未准备好
        在数据入库完成后立即调用，生成GJB和CWE的下载文件
        """
        try:
            self.gjb_logger.info("[预生成] 开始预生成文件缓存")
            
            # 预生成GJB文件（如果有GJB问题）
            if len(self.gjb_issues) > 0:
                try:
                    self.gjb_logger.info(f"[预生成] 开始生成GJB缓存文件，问题数: {len(self.gjb_issues)}")
                    result = self.generate_enhanced_output_file(
                        rule_type='gjb',
                        content_type='all',
                        include_unselected=False,
                        split=True,  # 使用四分分类格式
                        highlight_ai=False  # 未经AI过滤
                    )
                    if result.get("success"):
                        self.gjb_cached_filename = result.get("filename")
                        self.gjb_logger.info(f"[预生成] GJB缓存文件生成成功: {self.gjb_cached_filename}")
                    else:
                        self.gjb_logger.error(f"[预生成] GJB缓存文件生成失败: {result.get('error')}")
                except Exception as e:
                    self.gjb_logger.error(f"[预生成] 生成GJB缓存文件异常: {str(e)}")
                    import traceback
                    self.gjb_logger.error(traceback.format_exc())
            else:
                self.gjb_logger.info("[预生成] GJB问题为空，跳过文件生成")
            
            # 预生成CWE文件（如果有CWE问题）
            if len(self.cwe_issues) > 0:
                try:
                    self.cwe_logger.info(f"[预生成] 开始生成CWE缓存文件，问题数: {len(self.cwe_issues)}")
                    result = self.generate_enhanced_output_file(
                        rule_type='cwe',
                        content_type='all',
                        include_unselected=False,
                        split=True,  # 使用四分分类格式
                        highlight_ai=False  # 未经AI过滤
                    )
                    if result.get("success"):
                        self.cwe_cached_filename = result.get("filename")
                        self.cwe_logger.info(f"[预生成] CWE缓存文件生成成功: {self.cwe_cached_filename}")
                    else:
                        self.cwe_logger.error(f"[预生成] CWE缓存文件生成失败: {result.get('error')}")
                except Exception as e:
                    self.cwe_logger.error(f"[预生成] 生成CWE缓存文件异常: {str(e)}")
                    import traceback
                    self.cwe_logger.error(traceback.format_exc())
            else:
                self.cwe_logger.info("[预生成] CWE问题为空，跳过文件生成")
            
            self.gjb_logger.info("[预生成] 文件缓存预生成完成")
            
        except Exception as e:
            self.gjb_logger.error(f"[预生成] 预生成文件缓存时出错: {str(e)}")
            import traceback
            self.gjb_logger.error(traceback.format_exc())
            # 不抛出异常，允许流程继续
    
    def _get_pending_issues(self) -> List[StaticAnalysisIssue]:
        """获取待处理的问题项"""
        db = get_db_session()
        try:
            return db.query(StaticAnalysisIssue).filter(
                StaticAnalysisIssue.task_id == self.task_id
            ).all()
        finally:
            db.close()
    
    def _update_session_status(self, status: str):
        """更新会话状态"""
        db = get_db_session()
        try:
            session = db.query(StaticAnalysisSession).filter(
                StaticAnalysisSession.session_id == self.session_id
            ).first()
            
            if session:
                session.status = status
                session.filtered_issues = self.filtered_issues
                session.ai_analyzed_issues = self.ai_analyzed_issues
                session.accurate_issues = self.accurate_issues
                session.uncertain_issues = self.uncertain_issues
                db.commit()
        finally:
            db.close()
    
    def _batch_update_issues(self, updates: List[Dict]) -> None:
        """批量更新问题项状态"""
        if not updates:
            return
            
        db = get_db_session()
        try:
            # 使用SQLAlchemy的批量更新功能
            for update_data in updates:
                issue_id = update_data.pop('id')
                db.query(StaticAnalysisIssue).filter(
                    StaticAnalysisIssue.id == issue_id
                ).update(update_data, synchronize_session=False)
            
            db.commit()
            
        except Exception as e:
            self.logger.error(f"批量更新问题状态时出错: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def _update_issue_ai_analysis(self, issue_id: int, analysis_result: Dict[str, Any]):
        """更新问题的AI分析结果"""
        db = get_db_session()
        try:
            issue = db.query(StaticAnalysisIssue).filter(
                StaticAnalysisIssue.id == issue_id
            ).first()
            
            if issue:
                issue.ai_analyzed = True
                issue.ai_is_real_issue = analysis_result.get("is_real_issue", False)
                issue.ai_confidence = analysis_result.get("confidence", 0.0)
                issue.ai_analysis_result = analysis_result.get("analysis_result", "")
                issue.ai_evidence = json.dumps(analysis_result.get("evidence", []), ensure_ascii=False)
                issue.ai_reasoning = analysis_result.get("reasoning", "")
                issue.ai_recommendations = analysis_result.get("recommendations", "")
                
                # 如果AI判断为误报且置信度较高，可以考虑过滤掉
                if (not analysis_result.get("is_real_issue", True) and 
                    analysis_result.get("confidence", 0.0) > 0.8):
                    issue.is_filtered = True
                    issue.filter_reason = f"AI判断为误报 (置信度: {analysis_result.get('confidence', 0.0):.2f})"
                
                db.commit()
        finally:
            db.close()

    def _write_filtered_sheet(self, ws, filtered_issues, highlight_ai=False):
        """
        [NEW] 写入"过滤后问题"sheet，包含"问题归属"列
        filtered_issues: [(issue, ownership), ...]  ownership为"确定勾选"或"不确定勾选（AI已确认）"
        """
        from openpyxl.styles import Font, PatternFill, Alignment

        # 表头（增加"问题归属"列作为第一列）
        headers = ["问题归属", "测试活动", "问题类型", "问题等级", "问题数目", "问题名称",
                   "问题来源", "问题描述（四段式）", "测评单位意见"]
        ws.append(headers)
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment

        # 样式
        ai_confirm_highlight_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        normal_alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

        from ..database.postgresql_database import get_db_session as get_pg_session
        from ..database.postgresql_models import CWERule, GJB8114Rule

        for idx, (issue, ownership) in enumerate(filtered_issues, 1):
            file_path = issue.issue_file or ''
            line_number = issue.issue_line or ''
            defect_desc = issue.issue_description or ''
            problem_source = f"{file_path}文件{line_number}行" if file_path and line_number else "代码文件"

            rule_code = issue.rule_code or ''
            rt = (issue.rule_type or '').lower()
            rule_problem_name = rule_requirement = rule_impact = rule_suggestion = ''
            db2 = get_pg_session()
            try:
                if rt == 'gjb':
                    r = db2.query(GJB8114Rule).filter(GJB8114Rule.rule_code == rule_code).first()
                else:
                    r = db2.query(CWERule).filter(CWERule.rule_code == rule_code).first()
                if r:
                    rule_problem_name = r.problem_name or ''
                    rule_requirement = r.requirement_description or ''
                    rule_impact = r.impact_analysis or ''
                    rule_suggestion = r.improvement_suggestion or ''
            finally:
                db2.close()

            wenti_mingcheng = rule_problem_name or (issue.issue_name or '')
            guifan = 'GJB8114' if rt == 'gjb' else 'CWE'
            xuqiu_miaoshu = f"根据{guifan}编码规范要求{rule_code}条规定：{rule_requirement}".strip()
            wenti_miaoshu = wenti_mingcheng
            wenti_dingwei = f"{problem_source}，具体内容如下：\"{defect_desc}\""
            yingxiang_fenxi = rule_impact
            four_part = (
                f"需求描述：{xuqiu_miaoshu}。\n"
                f"问题描述：{wenti_miaoshu}。\n"
                f"问题定位：{wenti_dingwei}。\n"
                f"影响分析：{yingxiang_fenxi}"
            ).replace('。。', '。')

            def _strip_leading_suggestion(s: str) -> str:
                t = (s or '').strip()
                if t.startswith('建议'):
                    return t[2:].lstrip('：: \u3000')
                if t.startswith('修改意见：'):
                    return t[5:]
                if t.startswith('修改意见:'):
                    return t[4:]
                return t

            sug_core = _strip_leading_suggestion(rule_suggestion)
            test_unit_opinion = (
                "1.请确认是否是问题\n"
                f"2. 若是问题，建议{sug_core}"
            )

            row = [
                ownership,  # [NEW] 问题归属列
                "静态分析", "程序问题", "一般问题", "1",
                wenti_mingcheng, problem_source, four_part, test_unit_opinion
            ]
            ws.append(row)

            row_num = idx + 1
            # 如果是AI确认的问题且需要高亮，设置绿色背景
            if ownership == '不确定勾选（AI已确认）' and highlight_ai:
                for cell in ws[row_num]:
                    cell.fill = ai_confirm_highlight_fill
                    cell.alignment = normal_alignment
            else:
                for cell in ws[row_num]:
                    cell.alignment = normal_alignment

        # 设置列宽（第一列"问题归属"稍宽）
        ws.column_dimensions['A'].width = 25  # 问题归属列
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 10
        ws.column_dimensions['F'].width = 30
        ws.column_dimensions['G'].width = 28
        ws.column_dimensions['H'].width = 70
        ws.column_dimensions['I'].width = 50
        ws.freeze_panes = 'A2'
    
    def generate_enhanced_output_file(self, rule_type: str = 'all', content_type: str = 'all', include_unselected: bool = False, split: bool = False, highlight_ai: bool = False) -> Dict[str, Any]:
        """
        生成增强的输出Excel文件（从数据库查询）
        
        Args:
            rule_type: 'all', 'gjb', 'cwe' - 选择生成哪种规则的问题单
            content_type: 'all', 'accurate', 'uncertain' - 选择包含哪类问题
        """
        try:
            self.logger.info(f"开始生成增强输出文件（从数据库查询）- 规则类型:{rule_type}, 内容类型:{content_type}, split={split}, highlight_ai={highlight_ai}")
            
            # 从数据库查询问题
            db = get_db_session()
            try:
                # 调试：输出当前会话在数据库中的分布情况
                try:
                    total_in_session = db.query(func.count(StaticAnalysisIssue.id)).filter(
                        StaticAnalysisIssue.task_id == self.task_id
                    ).scalar()
                    self.logger.info(f"[DB] 当前任务问题总数: {total_in_session}")
                    dist = db.query(
                        StaticAnalysisIssue.rule_type,
                        StaticAnalysisIssue.rule_accuracy_type,
                        func.count(StaticAnalysisIssue.id)
                    ).filter(
                        StaticAnalysisIssue.task_id == self.task_id
                    ).group_by(
                        StaticAnalysisIssue.rule_type,
                        StaticAnalysisIssue.rule_accuracy_type
                    ).all()
                    for rt, at, cnt in dist:
                        self.logger.info(f"[DB] 分布 - rule_type={rt}, accuracy={at}, count={cnt}")
                except Exception as _e:
                    self.logger.warning(f"[DB] 统计分布时异常: {str(_e)}")
                
                query = db.query(StaticAnalysisIssue).filter(
                    StaticAnalysisIssue.task_id == self.task_id
                )
                
                # 根据rule_type过滤
                if rule_type == 'gjb':
                    query = query.filter(StaticAnalysisIssue.rule_type == 'gjb')
                    self.logger.info("过滤条件: 只包含GJB8114规则")
                elif rule_type == 'cwe':
                    query = query.filter(StaticAnalysisIssue.rule_type == 'cwe')
                    self.logger.info("过滤条件: 只包含CWE规则")
                else:
                    self.logger.info("过滤条件: 包含所有规则类型")
                
                # 根据content_type过滤（当未要求split时生效）
                if content_type == 'accurate' and not split:
                    query = query.filter(StaticAnalysisIssue.rule_accuracy_type == 'accurate')
                    if not include_unselected:
                        # 仅包含用户勾选的规则对应的问题
                        # 优先根据用户选择的规则进行过滤，避免仅依赖 is_filtered 标记
                        # [FIX] 优先使用内存中的selected_rules，若无则从数据库读取is_selected字段
                        if self.selected_rules:
                            selected = list(self.selected_rules)
                            self.logger.info(f"[问题单生成] 使用内存中的勾选规则: {len(selected)}条")
                        else:
                            # 从数据库读取勾选状态
                            try:
                                from app.staticAnalysis.filter.database.postgresql_models import GJB8114Rule, CWERule
                                if rule_type == 'gjb':
                                    db_selected = db.query(GJB8114Rule.rule_code).filter(GJB8114Rule.is_selected == True).all()
                                    selected = [r[0] for r in db_selected]
                                    self.logger.info(f"[问题单生成] 从数据库加载GJB勾选规则: {len(selected)}条")
                                elif rule_type == 'cwe':
                                    db_selected = db.query(CWERule.rule_code).filter(CWERule.is_selected == True).all()
                                    selected = [r[0] for r in db_selected]
                                    self.logger.info(f"[问题单生成] 从数据库加载CWE勾选规则: {len(selected)}条")
                                else:
                                    # 全部规则类型，合并GJB和CWE
                                    gjb_selected = db.query(GJB8114Rule.rule_code).filter(GJB8114Rule.is_selected == True).all()
                                    cwe_selected = db.query(CWERule.rule_code).filter(CWERule.is_selected == True).all()
                                    selected = [r[0] for r in gjb_selected] + [r[0] for r in cwe_selected]
                                    self.logger.info(f"[问题单生成] 从数据库加载全部勾选规则: GJB={len(gjb_selected)}, CWE={len(cwe_selected)}, 总计={len(selected)}")
                            except Exception as e:
                                self.logger.error(f"[问题单生成] 从数据库加载勾选规则失败: {e}")
                                selected = []  # 失败时使用空列表
                        
                        if selected:
                            if rule_type == 'gjb':
                                try:
                                    from app.staticAnalysis.filter.database.postgresql_rules_database import PostgreSQLRulesDatabase
                                    normalized = set()
                                    for code in selected:
                                        normalized.add(code)
                                        try:
                                            gjb_fmt = PostgreSQLRulesDatabase.convert_to_gjb_format(code)
                                            if gjb_fmt:
                                                normalized.add(gjb_fmt)
                                        except Exception:
                                            pass
                                    query = query.filter(StaticAnalysisIssue.rule_code.in_(list(normalized)))
                                    self.logger.info(f"过滤条件: 只包含确定规则 且 仅选中规则 (GJB), 规则数={len(normalized)}")
                                except Exception as _e:
                                    self.logger.warning(f"规则规范化失败，回退is_filtered过滤: {_e}")
                                    query = query.filter(StaticAnalysisIssue.is_filtered == False)
                            else:
                                # CWE规则直接按原样过滤
                                query = query.filter(StaticAnalysisIssue.rule_code.in_(selected))
                                self.logger.info(f"过滤条件: 只包含确定规则 且 仅选中规则 (CWE), 规则数={len(selected)}")
                        else:
                            # 若无选中列表，回退到 is_filtered 过滤
                            query = query.filter(StaticAnalysisIssue.is_filtered == False)
                            self.logger.info("过滤条件: 只包含确定规则 且 仅选中规则 (回退is_filtered)")
                    else:
                        self.logger.info("过滤条件: 只包含确定规则（包含未勾选条目）")
                elif content_type == 'uncertain' and not split:
                    if include_unselected:
                        # 未经AI过滤：包含所有不确定问题（不受 is_filtered 限制）
                        query = query.filter(StaticAnalysisIssue.rule_accuracy_type == 'uncertain')
                        self.logger.info("过滤条件: 包含所有不确定规则（不受is_filtered限制）")
                    else:
                        query = query.filter(
                            StaticAnalysisIssue.rule_accuracy_type == 'uncertain',
                            StaticAnalysisIssue.is_filtered == False
                        )
                        self.logger.info("过滤条件: 只包含未过滤的不确定规则")
                elif content_type == 'all' and not split:
                    query = query.filter(StaticAnalysisIssue.is_filtered == False)
                    self.logger.info("过滤条件: 包含所有未过滤的问题")
                
                # 当 split=True 且 content_type == 'all' 时，我们需要获取该 rule_type 下的所有问题用于后续分组
                if split and content_type == 'all':
                    selected_issues = query.order_by(StaticAnalysisIssue.row_index).all()
                else:
                    # 常规路径
                    selected_issues = query.order_by(StaticAnalysisIssue.row_index).all()
                
                if not selected_issues:
                    self.logger.warning(f"没有符合条件的问题项 - 规则类型:{rule_type}, 内容类型:{content_type}")
                    return {"success": False, "error": "没有符合条件的问题项"}
                
            finally:
                db.close()
            
            self.logger.info(f"准备生成Excel文件，包含 {len(selected_issues)} 个保留问题")
            
            # 生成输出文件路径
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 根据类型生成不同的文件名（简化版）
            if rule_type == 'gjb':
                rule_prefix = "8114"
            elif rule_type == 'cwe':
                rule_prefix = "CWE"
            else:
                rule_prefix = "全部"
            
            if content_type == 'accurate':
                content_suffix = "确定规则"
            elif content_type == 'uncertain':
                content_suffix = "不确定规则"
            else:
                content_suffix = "全部问题单"
            
            output_filename = f"{rule_prefix}_{content_suffix}.xlsx"
            from ..config.config import UPLOAD_DIR
            output_path = UPLOAD_DIR / "outputs" / output_filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建新的Excel文件
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
            workbook = openpyxl.Workbook()
            worksheet = workbook.active
            
            # 如果是split模式，创建四个Sheet分别写入
            if split and content_type == 'all':
                # 预处理选中规则集合
                # [FIX] 优先使用内存中的selected_rules，若无则从数据库读取is_selected字段
                if self.selected_rules:
                    selected = set(self.selected_rules)
                    self.logger.info(f"[问题单生成] 使用内存中的勾选规则: {len(selected)}条")
                else:
                    # 从数据库读取勾选状态
                    try:
                        from app.staticAnalysis.filter.database.postgresql_models import GJB8114Rule, CWERule
                        if rule_type == 'gjb':
                            db_selected = db.query(GJB8114Rule.rule_code).filter(GJB8114Rule.is_selected == True).all()
                            selected = set([r[0] for r in db_selected])
                            self.logger.info(f"[问题单生成] 从数据库加载GJB勾选规则: {len(selected)}条")
                        elif rule_type == 'cwe':
                            db_selected = db.query(CWERule.rule_code).filter(CWERule.is_selected == True).all()
                            selected = set([r[0] for r in db_selected])
                            self.logger.info(f"[问题单生成] 从数据库加载CWE勾选规则: {len(selected)}条")
                        else:
                            # 全部规则类型，合并GJB和CWE
                            gjb_selected = db.query(GJB8114Rule.rule_code).filter(GJB8114Rule.is_selected == True).all()
                            cwe_selected = db.query(CWERule.rule_code).filter(CWERule.is_selected == True).all()
                            selected = set([r[0] for r in gjb_selected] + [r[0] for r in cwe_selected])
                            self.logger.info(f"[问题单生成] 从数据库加载全部勾选规则: GJB={len(gjb_selected)}, CWE={len(cwe_selected)}, 总计={len(selected)}")
                    except Exception as e:
                        self.logger.error(f"[问题单生成] 从数据库加载勾选规则失败: {e}")
                        selected = set()  # 失败时使用空集合
                
                if rule_type == 'gjb' and selected:
                    try:
                        from app.staticAnalysis.filter.database.postgresql_rules_database import PostgreSQLRulesDatabase
                        normalized = set()
                        for code in selected:
                            normalized.add(code)
                            try:
                                gjb_fmt = PostgreSQLRulesDatabase.convert_to_gjb_format(code)
                                if gjb_fmt:
                                    normalized.add(gjb_fmt)
                            except Exception:
                                pass
                        selected = normalized
                    except Exception as _e:
                        self.logger.warning(f"GJB规则规范化失败，仍按原样匹配选中集合: {_e}")

                def issue_selected(issue):
                    try:
                        return (issue.rule_code or '') in selected if selected else False
                    except Exception:
                        return False

                # 分组：准确/不确定 × 勾选/未勾选。不确定组包含所有不确定（不看is_filtered）
                accurate_selected = [i for i in selected_issues if (i.rule_accuracy_type == 'accurate' and issue_selected(i))]
                accurate_unselected = [i for i in selected_issues if (i.rule_accuracy_type == 'accurate' and not issue_selected(i))]
                uncertain_selected = [i for i in selected_issues if (i.rule_accuracy_type == 'uncertain' and issue_selected(i))]
                uncertain_unselected = [i for i in selected_issues if (i.rule_accuracy_type == 'uncertain' and not issue_selected(i))]

                # [NEW] 构建过滤后问题列表：确定勾选 + 不确定勾选中AI确认
                filtered_issues = []
                # 1. 确定勾选的全部问题
                for issue in accurate_selected:
                    filtered_issues.append((issue, '确定勾选'))
                # 2. 不确定勾选中AI确认的问题
                for issue in uncertain_selected:
                    if issue.ai_is_real_issue is True:
                        filtered_issues.append((issue, '不确定勾选（AI已确认）'))

                # 重建工作簿：第一个活动sheet用于第一个分组
                workbook.remove(worksheet)

                # [NEW] 先创建"过滤后问题"sheet（作为第一个sheet）
                if filtered_issues:
                    ws_filtered = workbook.create_sheet(title="过滤后问题", index=0)
                    self._write_filtered_sheet(ws_filtered, filtered_issues, highlight_ai)
                    self.logger.info(f"[问题单生成] 生成'过滤后问题'sheet，共 {len(filtered_issues)} 条问题")

                sheet_defs = [
                    ("确定规则（勾选）", accurate_selected),
                    ("确定规则（未勾选）", accurate_unselected),
                    ("不确定规则（勾选）", uncertain_selected),
                    ("不确定规则（未勾选）", uncertain_unselected),
                ]

                def write_sheet(ws, items):
                    headers = [
                        "测试活动", "问题类型", "问题等级", "问题数目", "问题名称",
                        "问题来源", "问题描述（四段式）", "测评单位意见"
                    ]
                    ws.append(headers)
                    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
                    header_font = Font(bold=True, color="FFFFFF", size=11)
                    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                    for cell in ws[1]:
                        cell.fill = header_fill
                        cell.font = header_font
                        cell.alignment = header_alignment

                    # 样式
                    uncertain_retained_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
                    ai_confirm_highlight_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")  # 浅绿色
                    normal_alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

                    from ..database.postgresql_database import get_db_session as get_pg_session
                    from ..database.postgresql_models import CWERule, GJB8114Rule

                    for idx, issue in enumerate(items, 1):
                        file_path = issue.issue_file or ''
                        line_number = issue.issue_line or ''
                        defect_desc = issue.issue_description or ''
                        problem_source = f"{file_path}文件{line_number}行" if file_path and line_number else "代码文件"

                        rule_code = issue.rule_code or ''
                        rt = (issue.rule_type or '').lower()
                        rule_problem_name = rule_requirement = rule_impact = rule_suggestion = ''
                        db2 = get_pg_session()
                        try:
                            if rt == 'gjb':
                                r = db2.query(GJB8114Rule).filter(GJB8114Rule.rule_code == rule_code).first()
                            else:
                                r = db2.query(CWERule).filter(CWERule.rule_code == rule_code).first()
                            if r:
                                rule_problem_name = r.problem_name or ''
                                rule_requirement = r.requirement_description or ''
                                rule_impact = r.impact_analysis or ''
                                rule_suggestion = r.improvement_suggestion or ''
                        finally:
                            db2.close()

                        wenti_mingcheng = rule_problem_name or (issue.issue_name or '')
                        guifan = 'GJB8114' if rt == 'gjb' else 'CWE'
                        xuqiu_miaoshu = f"根据{guifan}编码规范要求{rule_code}条规定：{rule_requirement}".strip()
                        wenti_miaoshu = wenti_mingcheng
                        wenti_dingwei = f"{problem_source}，具体内容如下：\"{defect_desc}\""
                        yingxiang_fenxi = rule_impact
                        four_part = (
                            f"需求描述：{xuqiu_miaoshu}。\n"
                            f"问题描述：{wenti_miaoshu}。\n"
                            f"问题定位：{wenti_dingwei}。\n"
                            f"影响分析：{yingxiang_fenxi}"
                        ).replace('。。', '。')

                        def _strip_leading_suggestion(s: str) -> str:
                            t = (s or '').strip()
                            if t.startswith('建议'):
                                return t[2:].lstrip('：: \u3000')
                            if t.startswith('修改意见：'):
                                return t[5:]
                            if t.startswith('修改意见:'):
                                return t[4:]
                            return t

                        sug_core = _strip_leading_suggestion(rule_suggestion)
                        test_unit_opinion = (
                            "1.请确认是否是问题\n"
                            f"2. 若是问题，建议{sug_core}"
                        )

                        row = [
                            "静态分析", "程序问题", "一般问题", "1",
                            wenti_mingcheng, problem_source, four_part, test_unit_opinion
                        ]
                        ws.append(row)

                        row_num = idx + 1
                        accuracy_type = (issue.rule_accuracy_type or '').lower()
                        for cell in ws[row_num]:
                            # 在split模式下：
                            # - 未经AI过滤（highlight_ai=False）：不对不确定问题设置任何底色
                            # - AI过滤后（highlight_ai=True）：仅在“不确定规则（勾选）”sheet中，对 ai_is_real_issue=True 的条目以绿色高亮
                            if accuracy_type == 'uncertain':
                                if highlight_ai and ws.title == '不确定规则（勾选）' and (issue.ai_is_real_issue is True):
                                    cell.fill = ai_confirm_highlight_fill
                            cell.alignment = normal_alignment

                    ws.column_dimensions['A'].width = 12
                    ws.column_dimensions['B'].width = 12
                    ws.column_dimensions['C'].width = 12
                    ws.column_dimensions['D'].width = 10
                    ws.column_dimensions['E'].width = 30
                    ws.column_dimensions['F'].width = 28
                    ws.column_dimensions['G'].width = 70
                    ws.column_dimensions['H'].width = 50
                    ws.freeze_panes = 'A2'

                for title, items in sheet_defs:
                    ws = workbook.create_sheet(title=title)
                    write_sheet(ws, items)

                # 设定文件名（简化版）
                if rule_type == 'gjb':
                    rule_prefix = "8114"
                elif rule_type == 'cwe':
                    rule_prefix = "CWE"
                else:
                    rule_prefix = "全部"
                
                ai_status = "AI过滤后" if highlight_ai else "未经AI过滤"
                output_filename = f"{rule_prefix}_全部问题单（{ai_status}）.xlsx"
                from ..config.config import UPLOAD_DIR
                output_path = UPLOAD_DIR / "outputs" / output_filename
                output_path.parent.mkdir(parents=True, exist_ok=True)
                workbook.remove(workbook[workbook.sheetnames[0]]) if 'Sheet' in workbook.sheetnames else None
                workbook.save(str(output_path))
                self.logger.info(f"增强输出文件（四分分类）生成成功: {output_path}")
                return {"success": True, "filename": output_filename, "output_path": str(output_path)}

            # 非split：保持原单Sheet逻辑
            # 设置sheet标题
            if rule_type == 'gjb':
                worksheet.title = "GJB8114问题"
            elif rule_type == 'cwe':
                worksheet.title = "CWE问题"
            else:
                worksheet.title = "所有问题"
            
            # 按需求输出A-H八列
            headers = [
                "测试活动", "问题类型", "问题等级", "问题数目", "问题名称",
                "问题来源", "问题描述（四段式）", "测评单位意见"
            ]
            worksheet.append(headers)
            
            # 设置表头样式
            header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF", size=11)
            header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
            
            # 定义颜色样式
            # AI分析保留的不确定问题：浅黄色背景
            uncertain_retained_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
            # 确定规则问题：不设置颜色，保持默认白色背景
            # 普通文本对齐方式
            normal_alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            
            # 辅助：去除建议前缀
            def _strip_leading_suggestion(s: str) -> str:
                t = (s or '').strip()
                if t.startswith('建议'):
                    return t[2:].lstrip('：: \u3000')
                if t.startswith('修改意见：'):
                    return t[5:]
                if t.startswith('修改意见:'):
                    return t[4:]
                return t

            # 写入数据（A-H列）
            from ..database.postgresql_database import get_db_session as get_pg_session
            from ..database.postgresql_models import CWERule, GJB8114Rule

            for idx, issue in enumerate(selected_issues, 1):
                # 基础字段（来自上传表单的K/L/M列映射）
                file_path = issue.issue_file or ''
                line_number = issue.issue_line or ''
                defect_desc = issue.issue_description or ''  # M列缺陷说明
                problem_source = f"{file_path}文件{line_number}行" if file_path and line_number else "代码文件"

                # 读取规则文本（按rule_type分表）
                rule_code = issue.rule_code or ''
                rt = (issue.rule_type or '').lower()
                rule_problem_name = ''
                rule_requirement = ''
                rule_impact = ''
                rule_suggestion = ''
                db2 = get_pg_session()
                try:
                    if rt == 'gjb':
                        r = db2.query(GJB8114Rule).filter(GJB8114Rule.rule_code == rule_code).first()
                    else:
                        r = db2.query(CWERule).filter(CWERule.rule_code == rule_code).first()
                    if r:
                        rule_problem_name = r.problem_name or ''
                        rule_requirement = r.requirement_description or ''
                        rule_impact = r.impact_analysis or ''
                        rule_suggestion = r.improvement_suggestion or ''
                finally:
                    db2.close()

                # 列 E：问题名称（优先用规则库字段）
                wenti_mingcheng = rule_problem_name or (issue.issue_name or '')

                # 列 G：问题描述（四段式）
                guifan = 'GJB8114' if rt == 'gjb' else 'CWE'
                xuqiu_miaoshu = f"根据{guifan}编码规范要求{rule_code}条规定：{rule_requirement}".strip()
                wenti_miaoshu = wenti_mingcheng
                wenti_dingwei = f"{problem_source}，具体内容如下：\"{defect_desc}\""
                yingxiang_fenxi = rule_impact
                four_part = (
                    f"需求描述：{xuqiu_miaoshu}。\n"
                    f"问题描述：{wenti_miaoshu}。\n"
                    f"问题定位：{wenti_dingwei}。\n"
                    f"影响分析：{yingxiang_fenxi}"
                ).replace('。。', '。')

                # 列 H：测评单位意见
                sug_core = _strip_leading_suggestion(rule_suggestion)
                test_unit_opinion = (
                    "1.请确认是否是问题\n"
                    f"2. 若是问题，建议{sug_core}"
                )

                row = [
                    "静态分析",           # A 测试活动
                    "程序问题",           # B 问题类型
                    "一般问题",           # C 问题等级
                    "1",                 # D 问题数目
                    wenti_mingcheng,      # E 问题名称（来自规则库）
                    problem_source,       # F 问题来源（K/L列）
                    four_part,            # G 问题描述（四段式）
                    test_unit_opinion     # H 测评单位意见
                ]
                worksheet.append(row)
                
                # 根据问题类型设置行的背景色
                row_num = idx + 1  # 考虑表头占1行
                row_fill = None
                accuracy_type = (issue.rule_accuracy_type or '').lower()
                
                # 只为不确定规则（uncertain）标记颜色，确定规则保持白色
                if accuracy_type == 'uncertain' and not issue.is_filtered:
                    # AI分析保留的不确定问题：浅黄色
                    row_fill = uncertain_retained_fill
                # 确定规则（accurate）不设置颜色，保持默认白色
                
                # 应用样式到该行的所有单元格
                for cell in worksheet[row_num]:
                    if row_fill:
                        cell.fill = row_fill
                    cell.alignment = normal_alignment
            
            # 设置列宽（前6列较窄，后2列较宽）
            worksheet.column_dimensions['A'].width = 12
            worksheet.column_dimensions['B'].width = 12
            worksheet.column_dimensions['C'].width = 12
            worksheet.column_dimensions['D'].width = 10
            worksheet.column_dimensions['E'].width = 30
            worksheet.column_dimensions['F'].width = 28
            worksheet.column_dimensions['G'].width = 70
            worksheet.column_dimensions['H'].width = 50
            
            # 添加说明行（如果包含多种类型的问题）
            if content_type == 'all':
                # 在第一行之前插入说明
                worksheet.insert_rows(1)
                
                # 合并单元格用于显示说明
                worksheet.merge_cells('A1:H1')
                legend_cell = worksheet['A1']
                legend_cell.value = (
                    "颜色说明：【白色背景】= 确定规则问题（基于语法分析直接确定，高可信度）  "
                    "【黄色背景】= AI深度分析后保留的不确定规则问题（经过上下文分析，确认为真实问题）"
                )
                legend_cell.font = Font(bold=True, italic=True, size=10, color="1F4E78")
                legend_cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
                legend_cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                
                # 调整说明行高度
                worksheet.row_dimensions[1].height = 30
            
            # 冻结首行（表头）
            worksheet.freeze_panes = 'A2'
            
            # 保存文件
            workbook.save(str(output_path))
            self.logger.info(f"增强输出文件生成成功: {output_path}")
            
            return {
                "success": True,
                "filename": output_filename,
                "output_path": str(output_path)
            }
                
        except Exception as e:
            error_msg = f"生成增强输出文件时出错: {str(e)}"
            self.logger.error(error_msg)
            import traceback
            self.logger.error(f"错误堆栈: {traceback.format_exc()}")
            return {"success": False, "error": error_msg}

    def generate_output_file(self, rule_type: str = 'all', content_type: str = 'all', include_unselected: bool = False, split: bool = False, highlight_ai: bool = False) -> Dict[str, Any]:
        """
        生成输出文件（别名方法，用于兼容API）
        
        Args:
            rule_type: 'all', 'gjb', 'cwe' - 选择生成哪种规则的问题单
            content_type: 'all', 'accurate', 'uncertain' - 选择包含哪类问题
            include_unselected: bool - 是否包含未选中的问题
        """
        return self.generate_enhanced_output_file(rule_type=rule_type, content_type=content_type, include_unselected=include_unselected, split=split, highlight_ai=highlight_ai)
    
    def get_memory_status(self) -> Dict[str, Any]:
        """
        获取增强的基于内存变量的处理状态
        """
        try:
            # 计算进度百分比
            progress_percentage = 0
            if self.total_issues > 0:
                progress_percentage = (self.processed_issues / self.total_issues) * 100
            
            # 判断整体状态
            if self.processed_issues >= self.total_issues and self.total_issues > 0:
                if self.current_status == "ai_analyzing":
                    overall_status = "ai_analyzing"
                else:
                    overall_status = "completed"
                    self.current_status = "completed"
            else:
                overall_status = self.current_status
            
            return {
                "success": True,
                "session_id": self.session_id,
                "status": overall_status,
                "progress": progress_percentage,
                "original_filename": self.original_filename,
                "total_issues": self.total_issues,
                "processed_issues": self.processed_issues,
                "filtered_issues": self.filtered_issues,
                "ai_analyzed_issues": self.ai_analyzed_issues,
                "accurate_issues": self.accurate_issues,
                "uncertain_issues": self.uncertain_issues,
                "retained_issues": self.processed_issues - self.filtered_issues,
                "has_codebase": bool(self.codebase_path),
                "error_message": None,
                "output_filename": self.output_filename,
                # 详细进度信息
                "current_analyzing_issue": self.current_analyzing_issue,
                "current_issue_index": self.current_issue_index,
                "total_uncertain_issues": self.total_uncertain_issues,
                "tool_calls_count": self.tool_calls_count
            }
            
        except Exception as e:
            error_msg = f"获取增强内存状态时出错: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def get_detailed_status(self) -> Dict[str, Any]:
        """
        获取详细状态（包含GJB和CWE两部分）
        返回格式：
        {
            "gjb": {
                "total_issues": 10,  # 总问题数
                "accurate_issues": 6,  # 确定规则问题数
                "uncertain_issues": 4,  # 不确定规则问题数
                "filtered_issues": 2,  # 过滤掉的问题数
                "retained_issues": 8,  # 剩余问题数
                "processed_issues": 4,  # 已处理的不确定问题数
                "current_analyzing_issue": "...",
                "tool_calls_count": 15,
                "progress": 50,
                "status": "processing"
            },
            "cwe": { ... }
        }
        """
        try:
            # 统计GJB数据（优先内存，必要时回退DB）
            gjb_total = len(self.gjb_issues)
            gjb_accurate = sum(1 for issue in self.gjb_issues if issue.get('accuracy_type') == 'accurate')
            gjb_uncertain = sum(1 for issue in self.gjb_issues if issue.get('accuracy_type') == 'uncertain')
            # 注意：is_filtered 字段在AI分析过程中可能在数据库中更新，但内存列表未同步
            # 因此，如果有task_id，优先从数据库查询过滤数量以确保准确性
            if self.task_id:
                db_temp = get_db_session()
                try:
                    gjb_filtered = db_temp.query(StaticAnalysisIssue).filter(
                        StaticAnalysisIssue.task_id == self.task_id,
                        StaticAnalysisIssue.rule_type == 'gjb',
                        StaticAnalysisIssue.is_filtered == True
                    ).count()
                finally:
                    db_temp.close()
            else:
                gjb_filtered = sum(1 for issue in self.gjb_issues if issue.get('is_filtered', False))
            gjb_retained = gjb_total - gjb_filtered
            
            if (gjb_total == 0 or (self.gjb_total_issues == 0 and self.task_id)) and self.task_id:
                # 从数据库回退统计，避免内存被重建导致前端显示为0
                db = get_db_session()
                try:
                    from sqlalchemy import and_
                    gjb_total = db.query(StaticAnalysisIssue).filter(
                        StaticAnalysisIssue.task_id == self.task_id,
                        StaticAnalysisIssue.rule_type == 'gjb'
                    ).count()
                    gjb_uncertain = db.query(StaticAnalysisIssue).filter(
                        StaticAnalysisIssue.task_id == self.task_id,
                        StaticAnalysisIssue.rule_type == 'gjb',
                        StaticAnalysisIssue.rule_accuracy_type == 'uncertain'
                    ).count()
                    gjb_accurate = db.query(StaticAnalysisIssue).filter(
                        StaticAnalysisIssue.task_id == self.task_id,
                        StaticAnalysisIssue.rule_type == 'gjb',
                        StaticAnalysisIssue.rule_accuracy_type == 'accurate'
                    ).count()
                    gjb_filtered = db.query(StaticAnalysisIssue).filter(
                        StaticAnalysisIssue.task_id == self.task_id,
                        StaticAnalysisIssue.rule_type == 'gjb',
                        StaticAnalysisIssue.is_filtered == True
                    ).count()
                    gjb_retained = gjb_total - gjb_filtered
                    # 同步AI待处理总数
                    if self.gjb_total_issues == 0:
                        self.gjb_total_issues = gjb_uncertain
                finally:
                    db.close()
            
            # 计算GJB进度
            gjb_progress = 0
            if self.gjb_total_issues > 0:
                gjb_progress = int((self.gjb_processed_issues / self.gjb_total_issues) * 100)
            elif gjb_total > 0 or self.gjb_status == "completed":
                # 有问题但没有不确定问题需要AI处理，或者已标记为完成，进度100%
                gjb_progress = 100
            
            # 使用内存中的状态（优先），而不是重新计算
            # 这样可以确保在process_uploaded_files中设置的状态能够被正确返回
            gjb_status = self.gjb_status
            
            # 统计CWE数据（优先内存，必要时回退DB）
            cwe_total = len(self.cwe_issues)
            cwe_accurate = sum(1 for issue in self.cwe_issues if issue.get('accuracy_type') == 'accurate')
            cwe_uncertain = sum(1 for issue in self.cwe_issues if issue.get('accuracy_type') == 'uncertain')
            # 注意：is_filtered 字段在AI分析过程中可能在数据库中更新，但内存列表未同步
            # 因此，如果有task_id，优先从数据库查询过滤数量以确保准确性
            if self.task_id:
                db_temp = get_db_session()
                try:
                    cwe_filtered = db_temp.query(StaticAnalysisIssue).filter(
                        StaticAnalysisIssue.task_id == self.task_id,
                        StaticAnalysisIssue.rule_type == 'cwe',
                        StaticAnalysisIssue.is_filtered == True
                    ).count()
                finally:
                    db_temp.close()
            else:
                cwe_filtered = sum(1 for issue in self.cwe_issues if issue.get('is_filtered', False))
            cwe_retained = cwe_total - cwe_filtered
            
            if (cwe_total == 0 or (self.cwe_total_issues == 0 and self.task_id)) and self.task_id:
                db = get_db_session()
                try:
                    cwe_total = db.query(StaticAnalysisIssue).filter(
                        StaticAnalysisIssue.task_id == self.task_id,
                        StaticAnalysisIssue.rule_type == 'cwe'
                    ).count()
                    cwe_uncertain = db.query(StaticAnalysisIssue).filter(
                        StaticAnalysisIssue.task_id == self.task_id,
                        StaticAnalysisIssue.rule_type == 'cwe',
                        StaticAnalysisIssue.rule_accuracy_type == 'uncertain'
                    ).count()
                    cwe_accurate = db.query(StaticAnalysisIssue).filter(
                        StaticAnalysisIssue.task_id == self.task_id,
                        StaticAnalysisIssue.rule_type == 'cwe',
                        StaticAnalysisIssue.rule_accuracy_type == 'accurate'
                    ).count()
                    cwe_filtered = db.query(StaticAnalysisIssue).filter(
                        StaticAnalysisIssue.task_id == self.task_id,
                        StaticAnalysisIssue.rule_type == 'cwe',
                        StaticAnalysisIssue.is_filtered == True
                    ).count()
                    cwe_retained = cwe_total - cwe_filtered
                    if self.cwe_total_issues == 0:
                        self.cwe_total_issues = cwe_uncertain
                finally:
                    db.close()
            
            # 计算CWE进度
            cwe_progress = 0
            if self.cwe_total_issues > 0:
                cwe_progress = int((self.cwe_processed_issues / self.cwe_total_issues) * 100)
            elif cwe_total > 0 or self.cwe_status == "completed":
                # 有问题但没有不确定问题需要AI处理，或者已标记为完成，进度100%
                cwe_progress = 100
            
            # 使用内存中的状态（优先），而不是重新计算
            # 这样可以确保在process_uploaded_files中设置的状态能够被正确返回
            cwe_status = self.cwe_status
            
            return {
                "gjb": {
                    "total_issues": gjb_total,
                    "accurate_issues": gjb_accurate,
                    "uncertain_issues": gjb_uncertain,
                    "filtered_issues": gjb_filtered,
                    "retained_issues": gjb_retained,
                    "ai_processing_total": self.gjb_total_issues,  # 需要AI处理的不确定问题总数
                    "ai_processed_issues": self.gjb_processed_issues,  # AI已处理的不确定问题数
                    "current_analyzing_issue": self.gjb_current_analyzing_issue,
                    "tool_calls_count": self.gjb_tool_calls_count,
                    "progress": gjb_progress,
                    "status": gjb_status,
                    "accurate_ready": self.gjb_accurate_ready  # 新增：确定规则是否已就绪
                },
                "cwe": {
                    "total_issues": cwe_total,
                    "accurate_issues": cwe_accurate,
                    "uncertain_issues": cwe_uncertain,
                    "filtered_issues": cwe_filtered,
                    "retained_issues": cwe_retained,
                    "ai_processing_total": self.cwe_total_issues,  # 需要AI处理的不确定问题总数
                    "ai_processed_issues": self.cwe_processed_issues,  # AI已处理的不确定问题数
                    "current_analyzing_issue": self.cwe_current_analyzing_issue,
                    "tool_calls_count": self.cwe_tool_calls_count,
                    "progress": cwe_progress,
                    "status": cwe_status,
                    "accurate_ready": self.cwe_accurate_ready  # 新增：确定规则是否已就绪
                }
            }
        except Exception as e:
            self.logger.error(f"获取详细状态时出错: {str(e)}")
            # 返回默认值
            return {
                "gjb": {
                    "total_issues": 0,
                    "accurate_issues": 0,
                    "uncertain_issues": 0,
                    "filtered_issues": 0,
                    "retained_issues": 0,
                    "ai_processing_total": 0,
                    "ai_processed_issues": 0,
                    "current_analyzing_issue": "",
                    "tool_calls_count": 0,
                    "progress": 0,
                    "status": "pending",
                    "accurate_ready": False
                },
                "cwe": {
                    "total_issues": 0,
                    "accurate_issues": 0,
                    "uncertain_issues": 0,
                    "filtered_issues": 0,
                    "retained_issues": 0,
                    "ai_processing_total": 0,
                    "ai_processed_issues": 0,
                    "current_analyzing_issue": "",
                    "tool_calls_count": 0,
                    "progress": 0,
                    "status": "pending",
                    "accurate_ready": False
                }
            }
