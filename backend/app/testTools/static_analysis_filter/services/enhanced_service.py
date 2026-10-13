"""
增强的静态分析问题过滤服务 - 支持规则分类和AI分析
"""
import uuid
import time
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from ..models.models import StaticAnalysisSession, StaticAnalysisIssue
from ..database.database import get_db_session
from ..database.rules_database import get_rules_database
from ..database.cwe_rules_database import get_cwe_rules_database
from ..config.config import FILTER_CONFIG, OUTPUT_COLUMNS, BATCH_PROCESSING_CONFIG
from ..utils.logger import setup_session_logger
from .excel_processor import ExcelProcessor
from .code_analysis_agent_v2 import CodeAnalysisAgentV2
import logging
from datetime import datetime

class EnhancedStaticAnalysisFilterService:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        
        # ===== 双数据库支持 =====
        self.gjb_db = get_rules_database()  # GJB8114规则数据库
        self.cwe_db = get_cwe_rules_database()  # CWE规则数据库
        self.rules_db = self.gjb_db  # 保持向后兼容
        
        # ===== 双日志器支持 =====
        self.log_dir = Path(__file__).parent.parent / "logs" / session_id
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.gjb_logger = self._create_logger("GJB8114")
        self.cwe_logger = self._create_logger("CWE")
        self.logger = self.gjb_logger  # 保持向后兼容
        
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
        
        self.cwe_total_issues = 0
        self.cwe_processed_issues = 0
        self.cwe_current_analyzing_issue = ""
        self.cwe_tool_calls_count = 0
        self.cwe_status = "pending"
    
    def _create_logger(self, rule_type: str):
        """
        创建特定规则类型的日志器
        rule_type: "GJB8114" 或 "CWE"
        """
        logger = logging.getLogger(f"{self.session_id}_{rule_type}")
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        
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
        
    def process_uploaded_files(self, excel_file_path: str, original_filename: str, 
                             codebase_path: str, selected_rules: List[str] = None, 
                             filter_keywords: List[str] = None) -> Dict[str, Any]:
        """
        处理上传的静态分析Excel文件和代码库（支持双sheet）
        """
        try:
            self.gjb_logger.info(f"开始处理上传文件: {original_filename}")
            self.cwe_logger.info(f"开始处理上传文件: {original_filename}")
            
            # 初始化进度跟踪
            self.original_filename = original_filename
            self.codebase_path = codebase_path
            self.current_status = "processing"
            self.selected_rules = selected_rules or []
            
            # 记录用户选择的规则
            if self.selected_rules:
                self.gjb_logger.info(f"用户选择了 {len(self.selected_rules)} 个规则，将只处理这些规则对应的问题")
                self.cwe_logger.info(f"用户选择了 {len(self.selected_rules)} 个规则，将只处理这些规则对应的问题")
            else:
                self.gjb_logger.info("用户未指定规则选择，将处理所有问题")
                self.cwe_logger.info("用户未指定规则选择，将处理所有问题")
            
            # === 新增：解析Excel中的双sheet ===
            import openpyxl
            wb = openpyxl.load_workbook(excel_file_path)
            
            # 解析GJB8114 sheet
            gjb_sheet_name = "GJB_8114（国家军用标准CC++语言可靠性编程规范）"
            if gjb_sheet_name in wb.sheetnames:
                self.gjb_logger.info(f"开始解析GJB8114 sheet: {gjb_sheet_name}")
                self.gjb_issues = self._parse_excel_sheet(wb[gjb_sheet_name], "gjb", self.gjb_db, self.gjb_logger)
                self.gjb_total_issues = len(self.gjb_issues)
                self.gjb_logger.info(f"GJB8114 sheet解析完成，发现 {self.gjb_total_issues} 个问题")
            else:
                self.gjb_logger.warning(f"未找到GJB8114 sheet: {gjb_sheet_name}")
            
            # 解析CWE sheet
            cwe_sheet_name = "C_CPP缺陷检测项（CWE通用缺陷）"
            if cwe_sheet_name in wb.sheetnames:
                self.cwe_logger.info(f"开始解析CWE sheet: {cwe_sheet_name}")
                self.cwe_issues = self._parse_excel_sheet(wb[cwe_sheet_name], "cwe", self.cwe_db, self.cwe_logger)
                self.cwe_total_issues = len(self.cwe_issues)
                self.cwe_logger.info(f"CWE sheet解析完成，发现 {self.cwe_total_issues} 个问题")
            else:
                self.cwe_logger.warning(f"未找到CWE sheet: {cwe_sheet_name}")
            
            # 保持向后兼容
            self.total_issues = self.gjb_total_issues + self.cwe_total_issues
            
            # === 新增：保存到数据库 ===
            self._save_issues_to_database(excel_file_path, original_filename)
            
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
    
    def _parse_excel_sheet(self, sheet, rule_type: str, db, logger) -> List[Dict]:
        """
        解析单个Excel sheet
        rule_type: "gjb" 或 "cwe"
        """
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
                
                issue_file = sheet.cell(row, file_col).value
                issue_line = sheet.cell(row, line_col).value
                issue_desc = sheet.cell(row, desc_col).value if desc_col else ""
                
                # 分类问题
                accuracy_type, rule_info = db.classify_issue_by_rule_name(str(issue_name))
                
                # === 新增：根据用户选择的规则进行过滤 ===
                rule_code = rule_info.get("rule_code") if rule_info else None
                
                # 如果用户选择了规则列表，只保留选中的规则
                if self.selected_rules and rule_code:
                    if rule_code not in self.selected_rules:
                        filtered_count += 1
                        logger.debug(f"规则未选中，跳过问题: {rule_code} - {issue_name}")
                        continue
                
                issues.append({
                    "issue_name": str(issue_name),
                    "issue_file": str(issue_file) if issue_file else "",
                    "issue_line": int(issue_line) if issue_line else 0,
                    "issue_description": str(issue_desc) if issue_desc else "",
                    "rule_type": rule_type,
                    "accuracy_type": accuracy_type,
                    "rule_info": rule_info,
                    "is_filtered": False,
                    "ai_analysis": None
                })
            
            if filtered_count > 0:
                logger.info(f"从sheet中读取了 {len(issues)} 个问题（已根据规则选择过滤掉 {filtered_count} 个问题）")
            else:
                logger.info(f"从sheet中读取了 {len(issues)} 个问题")
            return issues
            
        except Exception as e:
            logger.error(f"解析sheet时出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return issues
    
    async def process_session_enhanced(self) -> Dict[str, Any]:
        """
        增强的会话处理 - 支持并行处理GJB和CWE规则
        """
        start_time = time.time()
        
        try:
            self.gjb_logger.info(f"开始增强处理会话: {self.session_id}")
            self.cwe_logger.info(f"开始增强处理会话: {self.session_id}")
            
            # === 并行处理GJB和CWE规则 ===
            # 创建两个并发任务
            gjb_task = asyncio.create_task(self._process_rule_type(self.gjb_issues, "gjb", self.gjb_db, self.gjb_logger))
            cwe_task = asyncio.create_task(self._process_rule_type(self.cwe_issues, "cwe", self.cwe_db, self.cwe_logger))
            
            # 等待两个任务完成
            gjb_result, cwe_result = await asyncio.gather(
                gjb_task,
                cwe_task,
                return_exceptions=True
            )
            
            # 检查结果
            success = True
            message_parts = []
            
            if isinstance(gjb_result, Exception):
                self.gjb_logger.error(f"GJB处理失败: {gjb_result}")
                self.gjb_status = "error"
                success = False
                message_parts.append(f"GJB: 错误 - {str(gjb_result)}")
            else:
                self.gjb_status = "completed"
                message_parts.append(f"GJB: 处理完成 ({gjb_result.get('processed', 0)}个)")
            
            if isinstance(cwe_result, Exception):
                self.cwe_logger.error(f"CWE处理失败: {cwe_result}")
                self.cwe_status = "error"
                success = False
                message_parts.append(f"CWE: 错误 - {str(cwe_result)}")
            else:
                self.cwe_status = "completed"
                message_parts.append(f"CWE: 处理完成 ({cwe_result.get('processed', 0)}个)")
            
            # 更新最终状态
            execution_time = time.time() - start_time
            message = " | ".join(message_parts)
            
            self._update_session_status("completed" if success else "error")
            self.current_status = "completed" if success else "error"
            
            self.gjb_logger.info(f"会话处理完成 - {message}, 耗时: {execution_time:.2f}秒")
            self.cwe_logger.info(f"会话处理完成 - {message}, 耗时: {execution_time:.2f}秒")
            
            return {
                "success": success,
                "message": message,
                "gjb_result": gjb_result if not isinstance(gjb_result, Exception) else None,
                "cwe_result": cwe_result if not isinstance(cwe_result, Exception) else None
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"增强处理会话时出错: {str(e)}"
            self.logger.error(f"{error_msg}, 耗时: {execution_time:.2f}秒")
            
            self._update_session_status("error")
            self.current_status = "error"
            
            return {"success": False, "error": error_msg}
    
    async def _process_rule_type(self, issues: List[Dict], rule_type: str, db, logger):
        """
        处理特定类型的规则（GJB或CWE）
        """
        logger.info(f"开始处理{rule_type.upper()}问题，共{len(issues)}个")
        
        if not issues:
            logger.warning(f"{rule_type.upper()}问题列表为空")
            # 更新状态为completed，避免前端一直显示pending
            if rule_type == "gjb":
                self.gjb_status = "completed"
            else:
                self.cwe_status = "completed"
            return {
                "processed": 0,
                "filtered": 0,
                "total": 0
            }
        
        processed = 0
        filtered = 0
        
        # 只处理不确定规则的问题（需要AI分析）
        uncertain_issues = [issue for issue in issues if issue['accuracy_type'] == 'uncertain']
        
        logger.info(f"需要AI分析的不确定问题: {len(uncertain_issues)}个")
        
        # 更新总数
        if rule_type == "gjb":
            self.gjb_total_issues = len(uncertain_issues)
            self.gjb_status = "processing"
        else:
            self.cwe_total_issues = len(uncertain_issues)
            self.cwe_status = "processing"
        
        # 如果没有代码库，跳过AI分析
        if not self.codebase_path:
            logger.warning("未提供代码库，跳过AI分析")
            return {
                "processed": 0,
                "filtered": 0,
                "total": len(uncertain_issues)
            }
        
        # 创建AI Agent
        from .code_analysis_agent_v2 import CodeAnalysisAgentV2
        agent = CodeAnalysisAgentV2(self.session_id, self.codebase_path)
        
        for idx, issue in enumerate(uncertain_issues, 1):
            # 更新当前分析状态
            if rule_type == "gjb":
                self.gjb_current_analyzing_issue = issue['issue_name']
            else:
                self.cwe_current_analyzing_issue = issue['issue_name']
            
            logger.info(f"[{idx}/{len(uncertain_issues)}] 分析: {issue['issue_name']}")
            
            try:
                # 获取规则信息
                rule_info = issue.get('rule_info')
                if not rule_info:
                    logger.warning(f"无法获取规则信息: {issue['issue_name']}")
                    processed += 1
                    # 更新已处理数量
                    if rule_type == "gjb":
                        self.gjb_processed_issues = processed
                    else:
                        self.cwe_processed_issues = processed
                    continue
                
                # 执行AI分析
                analysis_result = agent.analyze_uncertain_issue(issue, rule_info)
                
                # 更新工具调用次数
                if rule_type == "gjb":
                    self.gjb_tool_calls_count += analysis_result.get('tool_calls_count', 0)
                else:
                    self.cwe_tool_calls_count += analysis_result.get('tool_calls_count', 0)
                
                # 根据AI分析结果判断是否过滤
                is_real_issue = analysis_result.get('is_real_issue', True)
                confidence = analysis_result.get('confidence', 0.5)
                
                should_filter = not is_real_issue and confidence >= 0.7
                issue['is_filtered'] = should_filter
                issue['ai_analysis'] = analysis_result
                
                # === 立即更新数据库中的过滤状态 ===
                db_session = get_db_session()
                try:
                    db_issue = db_session.query(StaticAnalysisIssue).filter(
                        StaticAnalysisIssue.session_id == self.session_id,
                        StaticAnalysisIssue.issue_name == issue['issue_name'],
                        StaticAnalysisIssue.issue_file == issue.get('issue_file', ''),
                        StaticAnalysisIssue.rule_type == rule_type
                    ).first()
                    
                    if db_issue:
                        db_issue.is_filtered = should_filter
                        db_issue.filter_reason = f"AI判断为{'误报' if should_filter else '真实问题'}（置信度{confidence:.2f}）"
                        db_issue.ai_analyzed = True
                        db_issue.ai_is_real_issue = is_real_issue
                        db_issue.ai_confidence = confidence
                        db_issue.ai_analysis_result = str(analysis_result.get('analysis_result', ''))
                        db_issue.ai_reasoning = str(analysis_result.get('reasoning', ''))
                        db_issue.ai_evidence = str(analysis_result.get('evidence', ''))
                        db_issue.ai_recommendations = str(analysis_result.get('recommendations', ''))
                        db_session.commit()
                        logger.debug(f"已更新数据库: issue_id={db_issue.id}, is_filtered={should_filter}")
                    else:
                        logger.warning(f"未在数据库中找到对应问题: {issue['issue_name']}")
                except Exception as e:
                    logger.error(f"更新数据库失败: {str(e)}")
                    db_session.rollback()
                finally:
                    db_session.close()
                
                if should_filter:
                    filtered += 1
                    logger.info(f"[过滤] AI判断为误报 (置信度: {confidence:.2f})")
                else:
                    logger.info(f"[保留] AI判断为真实问题 (置信度: {confidence:.2f})")
                
                processed += 1
                
                # 更新已处理数量
                if rule_type == "gjb":
                    self.gjb_processed_issues = processed
                else:
                    self.cwe_processed_issues = processed
                
            except Exception as e:
                logger.error(f"分析问题时出错: {str(e)}")
                processed += 1
                # 更新已处理数量
                if rule_type == "gjb":
                    self.gjb_processed_issues = processed
                else:
                    self.cwe_processed_issues = processed
                continue
        
        logger.info(f"{rule_type.upper()}处理完成: 处理{processed}个，过滤{filtered}个")
        
        return {
            "processed": processed,
            "filtered": filtered,
            "total": len(uncertain_issues)
        }
    
    async def _phase1_rule_classification(self, issues: List[StaticAnalysisIssue]):
        """第一阶段：规则分类和基础过滤"""
        self.logger.info("开始第一阶段：规则分类和基础过滤")
        
        PROCESSING_BATCH_SIZE = BATCH_PROCESSING_CONFIG["processing_batch_size"]
        filtered_count = 0
        processed_count = 0
        accurate_count = 0
        uncertain_count = 0
        
        # 分批处理
        for batch_start in range(0, len(issues), PROCESSING_BATCH_SIZE):
            batch_end = min(batch_start + PROCESSING_BATCH_SIZE, len(issues))
            batch_issues = issues[batch_start:batch_end]
            current_batch = (batch_start // PROCESSING_BATCH_SIZE) + 1
            total_batches = (len(issues) + PROCESSING_BATCH_SIZE - 1) // PROCESSING_BATCH_SIZE
            
            self.logger.info(f"处理第{current_batch}/{total_batches}批次，{len(batch_issues)}个问题")
            
            # 批量分析问题
            batch_updates = []
            batch_filtered_count = 0
            batch_accurate_count = 0
            batch_uncertain_count = 0
            
            for issue in batch_issues:
                try:
                    # 1. 规则分类 - 优先使用GJB规则编号进行精确匹配
                    self.logger.info(f"=== 处理问题 ID: {issue.id} ===")
                    self.logger.info(f"问题名称: {issue.issue_name}")
                    self.logger.info(f"GJB规则编号: {issue.gjb_rule_code}")
                    
                    if issue.gjb_rule_code:
                        # 使用GJB规则编号进行精确匹配
                        rule_info = self.rules_db.get_rule_by_code(issue.gjb_rule_code)
                        if rule_info:
                            accuracy_type = rule_info['accuracy_type']
                            self.logger.info(f"通过GJB编号匹配到规则: {rule_info.get('rule_code')} - {accuracy_type}")
                        else:
                            # 如果数据库中没有该规则，尝试使用问题名称匹配
                            self.logger.warning(f"GJB编号 {issue.gjb_rule_code} 未在数据库中找到，尝试名称匹配")
                            accuracy_type, rule_info = self.rules_db.classify_issue_by_rule_name(issue.issue_name or "")
                            if rule_info:
                                self.logger.info(f"通过名称匹配到规则: {rule_info.get('rule_code')} - {accuracy_type}")
                            else:
                                self.logger.warning(f"名称匹配也失败，问题名称: {issue.issue_name}")
                    else:
                        # 没有GJB规则编号，使用问题名称匹配
                        self.logger.info("没有GJB规则编号，使用问题名称匹配")
                        accuracy_type, rule_info = self.rules_db.classify_issue_by_rule_name(issue.issue_name or "")
                        if rule_info:
                            self.logger.info(f"通过名称匹配到规则: {rule_info.get('rule_code')} - {accuracy_type}")
                        else:
                            self.logger.warning(f"名称匹配失败，问题名称: {issue.issue_name}")
                    
                    # 2. 检查规则是否被用户选中
                    rule_code = rule_info.get('rule_code') if rule_info else None
                    self.logger.info(f"规则代码: {rule_code}, 准确性类型: {accuracy_type}")
                    
                    if self.selected_rules and rule_code and rule_code not in self.selected_rules:
                        is_filtered = True
                        filter_reason = f"规则未被选中: {rule_code}"
                        self.logger.info(f"过滤原因: {filter_reason}")
                    elif accuracy_type == 'accurate':
                        # 确定规则的问题直接保留，不应用基础过滤规则
                        is_filtered = False
                        filter_reason = ""
                        self.logger.info("确定规则 - 直接保留")
                    elif accuracy_type == 'uncertain':
                        # 不确定规则的问题不过滤，留给AI分析阶段判断
                        is_filtered = False
                        filter_reason = ""
                        self.logger.info("不确定规则 - 保留，等待AI分析")
                    else:
                        # 未知类型，应用基础过滤规则
                        is_filtered, filter_reason = self._apply_basic_filter_rules(issue)
                        if is_filtered:
                            self.logger.info(f"未知规则类型 - 过滤掉，原因: {filter_reason}")
                        else:
                            self.logger.info("未知规则类型 - 保留")
                    
                    # 判断规则类型（GJB还是CWE）
                    if issue.sheet_name and ('GJB' in issue.sheet_name or '8114' in issue.sheet_name):
                        rule_type = 'gjb'
                    elif issue.sheet_name and ('CWE' in issue.sheet_name or '缺陷检测' in issue.sheet_name):
                        rule_type = 'cwe'
                    elif issue.gjb_rule_code and issue.gjb_rule_code.startswith('GJB_R_'):
                        rule_type = 'gjb'
                    elif rule_code and rule_code.startswith('S_'):
                        rule_type = 'cwe'
                    else:
                        rule_type = 'unknown'
                    
                    # 收集更新数据
                    update_data = {
                        'id': issue.id,
                        'rule_type': rule_type,  # 添加规则类型
                        'rule_accuracy_type': accuracy_type,
                        'is_filtered': is_filtered,
                        'filter_reason': filter_reason
                    }
                    
                    # 如果匹配到规则，记录规则信息
                    if rule_info:
                        update_data['rule_code'] = rule_info.get('rule_code')
                    
                    # 生成格式化的位置信息
                    if issue.issue_file and issue.issue_line:
                        update_data['issue_location'] = f"{issue.issue_file}文件{issue.issue_line}行"
                    
                    # 生成问题总结
                    update_data['issue_summary'] = issue.issue_name
                    
                    batch_updates.append(update_data)
                    
                    # 统计分类
                    if is_filtered:
                        batch_filtered_count += 1
                    
                    # 无论是否过滤，都要统计准确性类型
                    if accuracy_type == 'accurate':
                        batch_accurate_count += 1
                        self.logger.info(f"统计: 确定规则 +1, 当前批次确定规则数: {batch_accurate_count}")
                    elif accuracy_type == 'uncertain':
                        batch_uncertain_count += 1
                        self.logger.info(f"统计: 不确定规则 +1, 当前批次不确定规则数: {batch_uncertain_count}")
                    else:
                        self.logger.error(f"⚠️ 未知的准确性类型: {accuracy_type}, 问题ID: {issue.id}")
                    
                except Exception as e:
                    self.logger.error(f"分析问题项 {issue.id} 时出错: {str(e)}")
                    continue
            
            # 批量更新数据库
            if batch_updates:
                self._batch_update_issues(batch_updates)
            
            # 更新进度
            batch_processed = len(batch_issues)
            processed_count += batch_processed
            filtered_count += batch_filtered_count
            accurate_count += batch_accurate_count
            uncertain_count += batch_uncertain_count
            
            # 更新内存进度
            self.processed_issues = processed_count
            self.filtered_issues = filtered_count
            self.accurate_issues = accurate_count
            self.uncertain_issues = uncertain_count
            
            self.logger.info(f"批次{current_batch}处理完成，已处理{processed_count}/{len(issues)}个问题")
        
        self.logger.info("=" * 80)
        self.logger.info(f"第一阶段统计汇总:")
        self.logger.info(f"  总问题数: {len(issues)}")
        self.logger.info(f"  确定规则: {accurate_count} 个")
        self.logger.info(f"  不确定规则: {uncertain_count} 个")
        self.logger.info(f"  过滤掉: {filtered_count} 个")
        self.logger.info(f"  确定规则 + 不确定规则 = {accurate_count + uncertain_count}")
        
        if accurate_count + uncertain_count != len(issues):
            self.logger.error(f"⚠️ 警告: 分类数量不匹配！")
            self.logger.error(f"  总数: {len(issues)}, 分类后总数: {accurate_count + uncertain_count}")
            self.logger.error(f"  差异: {len(issues) - (accurate_count + uncertain_count)} 个问题未正确分类")
        
        self.logger.info("=" * 80)
    
    async def _phase2_ai_analysis(self, issues: List[StaticAnalysisIssue]):
        """第二阶段：AI分析不确定规则的问题"""
        self.logger.info("开始第二阶段：AI分析不确定规则的问题")
        
        # 更新状态为AI分析中
        self._update_session_status("ai_analyzing")
        self.current_status = "ai_analyzing"
        
        # 获取需要AI分析的问题（不确定规则且未被过滤的问题）
        self.logger.info(f"第二阶段收到 {len(issues)} 个问题")
        
        # 调试：检查每个问题的属性
        for issue in issues:
            rule_type = getattr(issue, 'rule_accuracy_type', None)
            is_filtered = issue.is_filtered
            self.logger.debug(f"问题ID {issue.id}: rule_accuracy_type={rule_type}, is_filtered={is_filtered}")
        
        uncertain_issues = [
            issue for issue in issues 
            if not issue.is_filtered and getattr(issue, 'rule_accuracy_type', None) == 'uncertain'
        ]
        
        self.logger.info(f"筛选出 {len(uncertain_issues)} 个不确定规则问题需要AI分析")
        
        if not uncertain_issues:
            self.logger.warning("没有需要AI分析的问题 - 可能是rule_accuracy_type未正确设置")
            return
        
        self.logger.info(f"找到{len(uncertain_issues)}个需要AI分析的问题")
        
        # 更新详细进度信息
        self.total_uncertain_issues = len(uncertain_issues)
        
        # 创建AI Agent V2（支持Function Calling）
        agent = CodeAnalysisAgentV2(self.session_id, self.codebase_path)
        
        ai_analyzed_count = 0
        
        # 逐个分析（AI分析比较耗时，不适合批量）
        for i, issue in enumerate(uncertain_issues, 1):
            try:
                # 更新当前分析进度
                self.current_issue_index = i
                self.current_analyzing_issue = issue.issue_name
                
                self.logger.info(f"AI分析进度: {i}/{len(uncertain_issues)} - {issue.issue_name}")
                
                # 获取规则信息 - 优先使用GJB规则编号
                rule_info = None
                if hasattr(issue, 'gjb_rule_code') and issue.gjb_rule_code:
                    rule_info = self.rules_db.get_rule_by_code(issue.gjb_rule_code)
                elif hasattr(issue, 'rule_code') and issue.rule_code:
                    rule_info = self.rules_db.get_rule_by_code(issue.rule_code)
                
                if not rule_info:
                    # 如果没有规则信息，重新分类
                    accuracy_type, rule_info = self.rules_db.classify_issue_by_rule_name(issue.issue_name or "")
                
                if not rule_info:
                    self.logger.warning(f"无法获取问题的规则信息: {issue.issue_name}")
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
                    self.logger.info(f"AI判断为误报（置信度{analysis_result.get('confidence')}），标记为过滤")
                    db = get_db_session()
                    try:
                        issue_to_filter = db.query(StaticAnalysisIssue).filter(
                            StaticAnalysisIssue.id == issue.id
                        ).first()
                        if issue_to_filter:
                            issue_to_filter.is_filtered = True
                            issue_to_filter.filter_reason = f"AI判断为误报（置信度{analysis_result.get('confidence')}）"
                            db.commit()
                            self.logger.info(f"问题 {issue.id} 已标记为过滤")
                    finally:
                        db.close()
                
                ai_analyzed_count += 1
                self.ai_analyzed_issues = ai_analyzed_count
                
                # 每分析10个问题记录一次进度
                if ai_analyzed_count % 10 == 0:
                    self.logger.info(f"AI分析进度: {ai_analyzed_count}/{len(uncertain_issues)}")
                
            except Exception as e:
                self.logger.error(f"AI分析问题 {issue.id} 时出错: {str(e)}")
                continue
        
        self.logger.info(f"第二阶段完成 - AI分析了{ai_analyzed_count}个问题")
        
        # 重新统计过滤数量（包括AI判断为误报的）
        db = get_db_session()
        try:
            filtered_count = db.query(StaticAnalysisIssue).filter(
                StaticAnalysisIssue.session_id == self.session_id,
                StaticAnalysisIssue.is_filtered == True
            ).count()
            self.filtered_issues = filtered_count
            self.logger.info(f"AI分析后，总过滤数量: {filtered_count}")
        finally:
            db.close()
    
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
                db.commit()
                self.gjb_logger.info(f"会话记录已创建: {self.session_id}")
                
                # 2. 批量插入问题记录
                from ..config.config import BATCH_PROCESSING_CONFIG
                BATCH_SIZE = BATCH_PROCESSING_CONFIG["db_insert_batch_size"]
                
                # 合并所有问题
                all_issues = []
                
                # 添加GJB问题
                for issue in self.gjb_issues:
                    all_issues.append(StaticAnalysisIssue(
                        session_id=self.session_id,
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
                for issue in self.cwe_issues:
                    all_issues.append(StaticAnalysisIssue(
                        session_id=self.session_id,
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
    
    def _get_pending_issues(self) -> List[StaticAnalysisIssue]:
        """获取待处理的问题项"""
        db = get_db_session()
        try:
            return db.query(StaticAnalysisIssue).filter(
                StaticAnalysisIssue.session_id == self.session_id
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
    
    def generate_enhanced_output_file(self, rule_type: str = 'all', content_type: str = 'all') -> Dict[str, Any]:
        """
        生成增强的输出Excel文件（从数据库查询）
        
        Args:
            rule_type: 'all', 'gjb', 'cwe' - 选择生成哪种规则的问题单
            content_type: 'all', 'accurate', 'uncertain' - 选择包含哪类问题
        """
        try:
            self.logger.info(f"开始生成增强输出文件（从数据库查询）- 规则类型:{rule_type}, 内容类型:{content_type}")
            
            # 从数据库查询问题
            db = get_db_session()
            try:
                query = db.query(StaticAnalysisIssue).filter(
                    StaticAnalysisIssue.session_id == self.session_id
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
                
                # 根据content_type过滤
                if content_type == 'accurate':
                    query = query.filter(StaticAnalysisIssue.rule_accuracy_type == 'accurate')
                    self.logger.info("过滤条件: 只包含确定规则")
                elif content_type == 'uncertain':
                    query = query.filter(
                        StaticAnalysisIssue.rule_accuracy_type == 'uncertain',
                        StaticAnalysisIssue.is_filtered == False
                    )
                    self.logger.info("过滤条件: 只包含未过滤的不确定规则")
                elif content_type == 'all':
                    query = query.filter(StaticAnalysisIssue.is_filtered == False)
                    self.logger.info("过滤条件: 包含所有未过滤的问题")
                
                # 按行号排序
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
            
            # 根据类型生成不同的文件名
            file_type_suffix = ""
            if rule_type == 'gjb':
                file_type_suffix = "GJB8114_"
            elif rule_type == 'cwe':
                file_type_suffix = "CWE_"
            
            if content_type == 'accurate':
                file_type_suffix += "确定规则_"
            elif content_type == 'uncertain':
                file_type_suffix += "不确定规则_"
            elif content_type == 'all':
                file_type_suffix += "完整_"
            
            output_filename = f"{file_type_suffix}问题单_{self.session_id}_{timestamp}.xlsx"
            from ..config.config import UPLOAD_DIR
            output_path = UPLOAD_DIR / "outputs" / output_filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建新的Excel文件
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
            workbook = openpyxl.Workbook()
            worksheet = workbook.active
            
            # 设置sheet标题
            if rule_type == 'gjb':
                worksheet.title = "GJB8114问题"
            elif rule_type == 'cwe':
                worksheet.title = "CWE问题"
            else:
                worksheet.title = "所有问题"
            
            # 问题单格式的表头
            headers = [
                "问题名称", "问题来源", "问题复现", "问题总结", "测试活动", "问题类型", "问题等级", "问题个数",
                "问题名称", "问题来源", "问题描述", "测评单位意见"
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
            
            # 写入数据（按照问题单格式）
            for idx, issue in enumerate(selected_issues, 1):
                # 提取issue信息（从数据库对象）
                issue_name = issue.issue_name or ''
                file_path = issue.issue_file or ''
                line_number = issue.issue_line or ''
                description = issue.issue_description or ''
                severity = '一般问题'  # 可以根据规则代码判断严重性
                accuracy_type = issue.rule_accuracy_type or 'uncertain'
                
                # 构建问题来源
                problem_source = f"{file_path}文件{line_number}行" if file_path and line_number else "代码文件"
                
                # 构建问题描述（规范化格式）
                # 1. 需求描述（将"禁止"转为正向描述）
                requirement_desc = issue_name
                if '禁止' in issue_name:
                    requirement_desc = issue_name  # 保持原样作为需求
                    problem_name = issue_name.replace('禁止', '存在')
                elif '必须' in issue_name:
                    requirement_desc = issue_name
                    problem_name = issue_name.replace('必须', '缺少')
                else:
                    problem_name = issue_name
                
                # 2. 获取AI分析结果（如果有）
                ai_reasoning = issue.ai_reasoning or ''
                ai_confidence = issue.ai_confidence or 0.0
                
                # 3. 构建完整的问题描述
                # 基础部分 - 需求描述
                problem_desc_parts = [f"需求描述:{requirement_desc}。"]
                
                # 问题描述字段 - 如果有AI分析，将reasoning放在这里
                if ai_reasoning and accuracy_type == 'uncertain':
                    problem_desc_parts.append(f"问题描述:{problem_name}。AI深度分析:{ai_reasoning}")
                else:
                    problem_desc_parts.append(f"问题描述:{problem_name}。")
                
                # 问题定位
                problem_desc_parts.append(f"问题定位: {problem_source},具体内容如下：\"{description}\"。")
                
                # 影响分析
                problem_desc_parts.append(f"影响分析: {problem_name},在某些特定场景下容易引发代码逻辑混乱，进而引发软件故障。")
                
                # 合并所有部分
                problem_description = "\n".join(problem_desc_parts)
                
                # 4. 测评单位意见
                test_unit_opinion = f"请开发人员针对{problem_name}问题对代码进行修改，保证代码实现正确。"
                
                # 构建数据行
                row = [
                    problem_name,          # 问题名称
                    problem_source,        # 问题来源
                    description[:100] if description else '',  # 问题复现（简短）
                    problem_name,          # 问题总结
                    "静态分析",            # 测试活动
                    "程序问题",            # 问题类型
                    severity,              # 问题等级
                    "1",                   # 问题个数
                    problem_name,          # 问题名称（重复列）
                    problem_source,        # 问题来源（重复列）
                    problem_description,   # 问题描述（详细）
                    test_unit_opinion      # 测评单位意见
                ]
                worksheet.append(row)
                
                # 根据问题类型设置行的背景色
                row_num = idx + 1  # 考虑表头占1行
                row_fill = None
                
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
            
            # 设置列宽
            worksheet.column_dimensions['A'].width = 30
            worksheet.column_dimensions['B'].width = 25
            worksheet.column_dimensions['C'].width = 40
            worksheet.column_dimensions['D'].width = 30
            worksheet.column_dimensions['E'].width = 12
            worksheet.column_dimensions['F'].width = 12
            worksheet.column_dimensions['G'].width = 12
            worksheet.column_dimensions['H'].width = 10
            worksheet.column_dimensions['I'].width = 30
            worksheet.column_dimensions['J'].width = 25
            worksheet.column_dimensions['K'].width = 60
            worksheet.column_dimensions['L'].width = 40
            
            # 添加说明行（如果包含多种类型的问题）
            if content_type == 'all':
                # 在第一行之前插入说明
                worksheet.insert_rows(1)
                
                # 合并单元格用于显示说明
                worksheet.merge_cells('A1:L1')
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
            if content_type == 'all':
                worksheet.freeze_panes = 'A3'  # 冻结前2行（说明行+表头）
            else:
                worksheet.freeze_panes = 'A2'  # 冻结表头行
            
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
    
    def generate_output_file(self, rule_type: str = 'all', content_type: str = 'all') -> Dict[str, Any]:
        """
        生成输出文件（别名方法，用于兼容API）
        
        Args:
            rule_type: 'all', 'gjb', 'cwe' - 选择生成哪种规则的问题单
            content_type: 'all', 'accurate', 'uncertain' - 选择包含哪类问题
        """
        return self.generate_enhanced_output_file(rule_type=rule_type, content_type=content_type)
    
    def get_enhanced_memory_status(self) -> Dict[str, Any]:
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
            # 统计GJB数据
            gjb_total = len(self.gjb_issues)
            gjb_accurate = sum(1 for issue in self.gjb_issues if issue.get('accuracy_type') == 'accurate')
            gjb_uncertain = sum(1 for issue in self.gjb_issues if issue.get('accuracy_type') == 'uncertain')
            gjb_filtered = sum(1 for issue in self.gjb_issues if issue.get('is_filtered', False))
            gjb_retained = gjb_total - gjb_filtered
            
            # 计算GJB进度
            gjb_progress = 0
            if self.gjb_total_issues > 0:
                gjb_progress = int((self.gjb_processed_issues / self.gjb_total_issues) * 100)
            elif gjb_total > 0:
                # 有问题但没有不确定问题需要AI处理，进度100%
                gjb_progress = 100
            
            # 判断GJB状态
            if gjb_total == 0:
                # 没有任何问题
                gjb_status = "pending"
            elif self.gjb_total_issues == 0:
                # 有问题但没有不确定问题需要AI处理（全部是确定规则）
                gjb_status = "completed"
            elif self.gjb_processed_issues >= self.gjb_total_issues:
                # AI处理完成
                gjb_status = "completed"
            else:
                # AI处理中
                gjb_status = "processing"
            
            # 统计CWE数据
            cwe_total = len(self.cwe_issues)
            cwe_accurate = sum(1 for issue in self.cwe_issues if issue.get('accuracy_type') == 'accurate')
            cwe_uncertain = sum(1 for issue in self.cwe_issues if issue.get('accuracy_type') == 'uncertain')
            cwe_filtered = sum(1 for issue in self.cwe_issues if issue.get('is_filtered', False))
            cwe_retained = cwe_total - cwe_filtered
            
            # 计算CWE进度
            cwe_progress = 0
            if self.cwe_total_issues > 0:
                cwe_progress = int((self.cwe_processed_issues / self.cwe_total_issues) * 100)
            elif cwe_total > 0:
                # 有问题但没有不确定问题需要AI处理，进度100%
                cwe_progress = 100
            
            # 判断CWE状态
            if cwe_total == 0:
                # 没有任何问题
                cwe_status = "pending"
            elif self.cwe_total_issues == 0:
                # 有问题但没有不确定问题需要AI处理（全部是确定规则）
                cwe_status = "completed"
            elif self.cwe_processed_issues >= self.cwe_total_issues:
                # AI处理完成
                cwe_status = "completed"
            else:
                # AI处理中
                cwe_status = "processing"
            
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
                    "status": gjb_status
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
                    "status": cwe_status
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
                    "status": "pending"
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
                    "status": "pending"
                }
            }
