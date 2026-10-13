"""
FPGA问题单输出生成器 - 生成格式化的Excel问题单
"""
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.staticAnalysis.filterFpga.database.postgresql_database import get_db_session
from app.staticAnalysis.filterFpga.database.postgresql_models import StaticAnalysisIssue, FPGARule, StaticAnalysisSession
from app.staticAnalysis.filterFpga.utils.logger import setup_module_logger

logger = setup_module_logger(__name__, "fpga_output_generator.log")


class FpgaOutputGenerator:
    """FPGA问题单生成器"""
    
    # 输出列定义（8列）- 删除前4列
    OUTPUT_COLUMNS = [
        "测试活动",
        "问题类型",
        "问题等级",
        "问题数目",
        "问题名称",
        "问题来源",
        "问题描述（四段式）",
        "测评单位意见"
    ]
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logger = logger
    
    def generate_output_file(self, output_path: str, rule_type: str = "all", 
                           accuracy: str = "all") -> Dict[str, Any]:
        """
        生成问题单Excel文件
        
        Args:
            output_path: 输出文件路径
            rule_type: 规则类型筛选 (all/fpga)
            accuracy: 准确度筛选 (all/accurate/uncertain)
        
        Returns:
            生成结果
        """
        try:
            self.logger.info(f"开始生成FPGA问题单 - session_id: {self.session_id}")
            
            # 从数据库获取问题
            issues = self._get_issues_from_db(rule_type, accuracy)
            
            if not issues:
                return {
                    "success": False,
                    "error": "没有找到符合条件的问题"
                }
            
            self.logger.info(f"找到 {len(issues)} 条问题，开始生成Excel")
            
            # 创建Excel
            workbook = openpyxl.Workbook()
            worksheet = workbook.active
            worksheet.title = "FPGA静态分析问题单"
            
            # 写入表头
            self._write_header(worksheet)
            
            # 写入数据
            self._write_data(worksheet, issues)
            
            # 设置格式
            self._set_excel_formatting(worksheet)
            
            # 保存文件
            workbook.save(output_path)
            workbook.close()
            
            self.logger.info(f"FPGA问题单生成成功: {output_path}")
            
            return {
                "success": True,
                "output_path": output_path,
                "issue_count": len(issues)
            }
            
        except Exception as e:
            error_msg = f"生成FPGA问题单失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    def _get_issues_from_db(self, rule_type: str, accuracy: str) -> List[Dict[str, Any]]:
        """从数据库获取问题"""
        session = get_db_session()
        try:
            # 获取当前会话（拿到代码库zip路径）
            sess = session.query(StaticAnalysisSession).filter(
                StaticAnalysisSession.session_id == self.session_id
            ).first()
            codebase_path = sess.codebase_path if sess else None
            # 通过join查询
            query = session.query(StaticAnalysisIssue).join(
                StaticAnalysisSession,
                StaticAnalysisIssue.task_id == StaticAnalysisSession.id
            ).filter(
                StaticAnalysisSession.session_id == self.session_id,
                StaticAnalysisIssue.is_filtered == False  # 只获取未过滤的问题
            )
            
            # 应用筛选条件
            if rule_type != "all":
                query = query.filter(StaticAnalysisIssue.rule_type == rule_type)
            
            if accuracy != "all":
                query = query.filter(StaticAnalysisIssue.rule_accuracy_type == accuracy)
            
            db_issues = query.all()
            
            # 转换为字典列表
            issues = []
            for issue in db_issues:
                # 获取规则信息
                rule = session.query(FPGARule).filter(
                    FPGARule.rule_code == issue.rule_code
                ).first()
                
                issues.append({
                    "rule_code": issue.rule_code,
                    "rule_content": rule.rule_content if rule else "",
                    "language": rule.language if rule else "",
                    "issue_title": rule.issue_title if rule else "",
                    "impact_analysis": rule.impact_analysis if rule else "",
                    "fix_suggestion": rule.fix_suggestion if rule else "",
                    "issue_file": issue.issue_file,
                    "issue_line": issue.issue_line,
                    "issue_description": issue.issue_description,
                    # 数据库模型无source_code字段，安全回退为空字符串
                    "source_code": getattr(issue, 'source_code', '') or "",
                    # 兼容模型字段：模型中为 ai_analysis_result
                    "ai_result": getattr(issue, 'ai_analysis_result', '') or "",
                    # 会话代码库路径（用于缺失源码时回填）
                    "codebase_path": codebase_path
                })
            
            return issues
            
        finally:
            session.close()
    
    def _write_header(self, worksheet):
        """写入表头"""
        for col_idx, col_name in enumerate(self.OUTPUT_COLUMNS, start=1):
            cell = worksheet.cell(row=1, column=col_idx, value=col_name)
            cell.font = Font(bold=True, size=11)
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
    
    def _write_data(self, worksheet, issues: List[Dict[str, Any]]):
        """写入数据行"""
        for row_idx, issue in enumerate(issues, start=2):
            # 分析问题并生成12列数据
            row_data = self._analyze_issue_for_output(issue)
            
            # 写入每一列
            for col_idx, value in enumerate(row_data, start=1):
                cell = worksheet.cell(row=row_idx, column=col_idx, value=value)
                cell.alignment = Alignment(vertical='center', wrap_text=True)
    
    def _analyze_issue_for_output(self, issue: Dict[str, Any]) -> List[str]:
        """
        分析问题并生成8列输出数据
        
        FPGA特定的问题单格式（新版）
        """
        rule_code = issue.get("rule_code", "")
        rule_content = issue.get("rule_content", "")
        issue_title = issue.get("issue_title", "")  # 数据库中的问题名称
        impact_analysis = issue.get("impact_analysis", "")  # 数据库中的影响分析
        fix_suggestion = issue.get("fix_suggestion", "")  # 数据库中的修改意见
        issue_file = issue.get("issue_file", "")
        issue_line = issue.get("issue_line", "")
        issue_description = issue.get("issue_description", "")
        
        # 根据文件扩展名判断语言类型
        import os
        file_ext = os.path.splitext(issue_file)[1].lower() if issue_file else ""
        if file_ext in ['.v', '.sv', '.vh', '.svh']:
            language = "VERILOG"
        elif file_ext in ['.vhd', '.vhdl']:
            language = "VHDL"
        else:
            # 兜底：尝试从issue中获取，如果没有则默认为空
            language = issue.get("language", "")
        source_code = issue.get("source_code", "")
        # 如果没有源码，尝试从会话的代码库zip即时提取
        if not source_code:
            codebase_path = issue.get("codebase_path")
            try:
                extracted = self._extract_code_from_zip(codebase_path, issue_file, issue_line)
                if extracted:
                    source_code = extracted
            except Exception:
                pass
        
        # 第1列：测试活动 - 固定为"代码审查"
        ceshi_huodong = "代码审查"
        
        # 第2列：问题类型 - 固定为"程序问题"
        wentileixing = "程序问题"
        
        # 第3列：问题等级 - 固定为"一般问题"
        wentidengji = "一般问题"
        
        # 第4列：问题数目 - 固定为"1"
        wenti_shumu = "1"
        
        # 第5列：问题名称 - 使用数据库中的issue_title字段
        wenti_mingcheng = issue_title if issue_title else f"{rule_code} - {rule_content[:30]}"
        
        # 第6列：问题来源 - 保持现状
        wenti_laiyuan = f"{issue_file}文件{issue_line}行"
        
        # 第7列：问题描述（四段式）
        wenti_siduan_miaoshu = self._generate_four_part_description(
            wenti_mingcheng, wenti_laiyuan, issue_description, 
            rule_code, rule_content, language, impact_analysis, source_code
        )
        
        # 第8列：测评单位意见
        ceping_danwei_yijian = self._generate_evaluation_opinion(fix_suggestion)
        
        return [
            ceshi_huodong,
            wentileixing,
            wentidengji,
            wenti_shumu,
            wenti_mingcheng,
            wenti_laiyuan,
            wenti_siduan_miaoshu,
            ceping_danwei_yijian
        ]

    def _extract_code_from_zip(self, zip_path: str, file_name: str, line_number: str) -> str:
        """从代码库zip中提取指定文件的某一行代码（带邻域回退，稳健匹配条目）"""
        if not zip_path or not file_name or not line_number:
            return ""
        import zipfile
        from pathlib import Path
        try:
            ln = int(str(line_number).strip())
        except Exception:
            return ""
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                entries = z.namelist()
                entry = self._find_best_zip_entry(entries, Path(file_name).name, original_path_hint=str(file_name))
                if not entry:
                    return ""
                try:
                    content = z.read(entry).decode('utf-8', errors='ignore')
                except Exception:
                    return ""
                lines = content.split('\n')
                if 1 <= ln <= len(lines):
                    extracted = lines[ln - 1].rstrip('\r').strip()
                    if not extracted:
                        for i in range(max(1, ln - 3), min(len(lines), ln + 3) + 1):
                            cand = lines[i - 1].rstrip('\r').strip()
                            if cand:
                                return cand
                    return extracted
                return ""
        except Exception:
            return ""

    def _find_best_zip_entry(self, entries: list, filename: str, original_path_hint: str = "") -> Optional[str]:
        """在zip条目中查找与给定文件名最匹配的条目。
        - 仅比较文件名（大小写不敏感）作为候选；
        - 使用原始路径后缀段匹配计分（越多越好）；
        - 次序：后缀匹配分 > 路径更短 > 字母序。
        """
        if not filename:
            return None
        from pathlib import PurePosixPath
        fname = filename.lower()
        candidates = [e for e in entries if PurePosixPath(e).name.lower() == fname]
        if not candidates:
            return None
        hint = (original_path_hint or "").replace('\\', '/').strip('/')
        hint_parts = [p.lower() for p in hint.split('/') if p]
        def score(entry: str):
            parts = [p.lower() for p in entry.split('/') if p]
            suffix = 0
            for a, b in zip(reversed(parts), reversed(hint_parts)):
                if a == b:
                    suffix += 1
                else:
                    break
            return (suffix, -len(parts), entry.lower())
        candidates.sort(key=score, reverse=True)
        return candidates[0]
    
    def _generate_four_part_description(self, wenti_mingcheng: str, wenti_laiyuan: str,
                                       issue_description: str, rule_code: str, 
                                       rule_content: str, language: str, 
                                       impact_analysis: str, source_code: str) -> str:
        """生成四段式问题描述"""
        
        # 确定规范文档名称
        if language.upper() == "VERILOG":
            guifan_name = "《可编程逻辑器件软件编码规范（Verilog篇）》"
        elif language.upper() == "VHDL":
            guifan_name = "《可编程逻辑器件软件编码规范（VHDL篇）》"
        else:
            guifan_name = "《可编程逻辑器件软件编码规范》"
        
        # 需求描述：根据《xxx》规则编号要求：规则内容
        xuqiu_miaoshu = f"根据{guifan_name}{rule_code}要求：{rule_content}"
        
        # 问题描述：使用数据库中的issue_title（问题名称）
        wenti_miaoshu_text = wenti_mingcheng
        
        # 问题定位：保持现状，包含文件、行号和具体内容
        if source_code:
            wenti_dingwei = f"{wenti_laiyuan}，具体内容如下：\"{source_code}\"，如上述内容所示，{wenti_miaoshu_text}"
        else:
            wenti_dingwei = f"{wenti_laiyuan}，具体内容如下：\"{issue_description}\"，如上述内容所示，{wenti_miaoshu_text}"
        
        # 影响分析：使用数据库中的impact_analysis字段
        yingxiang_fenxi = impact_analysis if impact_analysis else "影响代码质量和可维护性"
        
        # 组装四段式描述
        siduan_miaoshu = (
            f"需求描述：{xuqiu_miaoshu}。\n"
            f"问题描述：{wenti_miaoshu_text}。\n"
            f"问题定位：{wenti_dingwei}。\n"
            f"影响分析：{yingxiang_fenxi}"
        )
        
        return siduan_miaoshu.replace('。。', '。')
    
    def _generate_evaluation_opinion(self, fix_suggestion: str) -> str:
        """生成测评单位意见"""
        # 剔除"修改意见："前缀
        suggestion = fix_suggestion or "请根据规则要求进行修改。"
        if suggestion.startswith("修改意见："):
            suggestion = suggestion[5:]  # 去掉"修改意见："这5个字符
        elif suggestion.startswith("修改意见:"):
            suggestion = suggestion[4:]  # 去掉"修改意见:"这4个字符
        
        # 格式化输出
        opinion = (
            "1.请开发人员确认是否是问题\n"
            f"2.若是问题，{suggestion}"
        )
        
        return opinion
    
    def _set_excel_formatting(self, worksheet):
        """设置Excel格式"""
        from openpyxl.utils import get_column_letter
        
        # 设置行高
        for row in range(1, worksheet.max_row + 1):
            worksheet.row_dimensions[row].height = 40
        
        # 设置列宽：前6列为20，后2列为60
        for col in range(1, 9):  # 现在是8列
            col_letter = get_column_letter(col)
            if col <= 6:
                worksheet.column_dimensions[col_letter].width = 20
            else:
                worksheet.column_dimensions[col_letter].width = 60
