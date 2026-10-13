"""普通模式代码视图数据组装（对齐科代 mode filter/code-view 返回结构）。"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy.orm import Session

from app.staticAnalysis.normalModeC.database import (
    FileRepository,
    FunctionRepository,
    ProblemRepository,
    TaskRepository,
)
from app.staticAnalysis.normalModeC.services.rules import load_all_c_rules
from app.staticAnalysis.normalModeC.utils.context import get_normal_mode_c_context


def _build_source_snippet(source_code: str, line_no: int, context: int = 3) -> str:
    """截取问题行附近代码片段（函数签名 + ...... + 上下文 + ...... + 闭括号）。"""
    if not source_code:
        return ''
    lines = source_code.splitlines()
    if line_no <= 0 or line_no > len(lines):
        return source_code[:2000]
    target_idx = line_no - 1

    def _is_control(text):
        s = text.strip()
        return s.startswith(('if ', 'if(', 'for ', 'for(', 'while ', 'while(',
                              'switch ', 'switch(', 'else', 'do ', 'do{',
                              'struct ', 'enum ', 'union ', 'typedef '))

    brace_stack = []
    for idx, line in enumerate(lines[:target_idx + 1]):
        for ch in line:
            if ch == '{':
                brace_stack.append(idx)
            elif ch == '}' and brace_stack:
                brace_stack.pop()

    def _sig_start(open_idx):
        s = open_idx
        while s > 0:
            prev = lines[s - 1].strip()
            if not prev or prev.startswith('#') or prev.endswith((';', '}', '{')):
                break
            s -= 1
        return s

    func_open = func_sig = None
    for oi in reversed(brace_stack):
        ss = _sig_start(oi)
        sig = ' '.join(l.strip() for l in lines[ss:oi + 1])
        if '(' in sig and ')' in sig and not _is_control(sig):
            func_open, func_sig = oi, ss
            break

    if func_open is None:
        start = max(0, target_idx - context)
        end = min(len(lines) - 1, target_idx + context)
        snippet = []
        if start > 0:
            snippet.append('......')
        snippet.extend(lines[start:end + 1])
        if end < len(lines) - 1:
            snippet.append('......')
        return '\n'.join(snippet)


def _build_problem_sheet(
    rule_info: dict,
    issue_name: str,
    rule_code: str,
    rule_type: str,
    description_requirement: str,
    description_issue: str,
    description_location: str,
    description_impact: str,
    source_code: str,
    issue_file: str,
    issue_line: int,
) -> dict:
    """组装对齐工具模式的 problem_sheet（四段式 + 测评单位意见）。"""
    snippet = _build_source_snippet(source_code, issue_line) if source_code else ""
    source_code_part = f"\n源代码为：\n{snippet}" if snippet else ""

    guifan = "GJB8114" if rule_type == "gjb" else ("CWE" if rule_type == "cwe" else "FPGA")
    req_desc = description_requirement or rule_info.get("rule_description") or ""
    xuqiu = f"根据{guifan}编码规范要求{rule_code}条规定：{req_desc}".strip()

    problem_source = (
        f"{issue_file}文件{issue_line}行" if issue_file and issue_line else (issue_file or "代码文件")
    )
    defect_desc = description_issue or ""

    four_part = (
        f"需求描述：{xuqiu}。\n"
        f"问题描述：{issue_name}。\n"
        f"问题定位：{problem_source}，具体内容如下：\"{defect_desc}\"。{source_code_part}\n"
        f"影响分析：{description_impact}"
    ).replace("。。", "。")

    rule_suggestion = rule_info.get("improvement_suggestion") or ""
    sug_core = rule_suggestion
    for prefix in ("建议", "修改意见：", "修改意见:"):
        if sug_core.startswith(prefix):
            sug_core = sug_core[len(prefix):].lstrip("： 　")
            break

    test_unit_opinion = (
        "1.请确认是否是问题\n"
        f"2. 若是问题，建议{sug_core}" if sug_core else "1.请确认是否是问题"
    )

    return {
        "issue_name": issue_name,
        "four_part_description": four_part,
        "test_unit_opinion": test_unit_opinion,
    }


    depth = 0
    func_close = len(lines) - 1
    for idx in range(func_open, len(lines)):
        for ch in lines[idx]:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    func_close = idx
                    break
        if depth == 0 and idx >= func_open:
            break

    ctx_start = max(func_open + 1, target_idx - context)
    ctx_end = min(func_close - 1, target_idx + context)

    snippet = list(lines[func_sig:func_open + 1])
    if ctx_start > func_open + 1:
        snippet.append('......')
    if ctx_start <= ctx_end:
        snippet.extend(lines[ctx_start:ctx_end + 1])
    if ctx_end < func_close - 1:
        snippet.append('......')
    if func_close > func_open:
        snippet.append(lines[func_close])
    return '\n'.join(snippet)




def build_normal_mode_code_view_data(
    db: Session,
    task_id: int,
    domain: str = "c",
    rule_type: Optional[str] = None,
) -> Dict[str, Any]:
    _ = domain  # 兼容旧调用签名
    task = TaskRepository(db).get_task(task_id)
    if not task:
        raise ValueError("任务不存在")

    file_info = FileRepository(db).get_file(task.code_file_id)
    if not file_info or not file_info.extract_path:
        raise ValueError("代码文件不存在")
    if not os.path.exists(file_info.extract_path):
        raise ValueError("代码解压路径不存在")

    task_context = get_normal_mode_c_context(task_id)
    selected_rules = [
        str(code).strip()
        for code in (task_context.get("selected_rules") or [])
        if str(code).strip()
    ]

    all_rules = load_all_c_rules()

    if rule_type and rule_type not in ("mixed", "all", ""):
        all_rules = [
            rule for rule in all_rules
            if str(rule.get("rule_type", "")).lower() == str(rule_type).lower()
        ]

    rule_map = {
        str(rule.get("rule_code", "")).strip(): rule
        for rule in all_rules
        if rule.get("rule_code")
    }
    if not selected_rules:
        selected_rules = list(rule_map.keys())

    raw_problems = ProblemRepository(db).get_problems_by_task(task_id)
    normalized_problems = [
        _normalize_problem(problem, rule_map, default_rule_type=None)
        for problem in raw_problems
    ]
    if rule_type and rule_type not in ("mixed", "all", ""):
        normalized_problems = [
            problem for problem in normalized_problems
            if str(problem.get("rule_type", "")).lower() == str(rule_type).lower()
        ]

    problem_counts: Dict[str, int] = {}
    for problem in normalized_problems:
        code = str(problem.get("rule_code") or "").strip()
        if not code:
            continue
        problem_counts[code] = problem_counts.get(code, 0) + 1

    rules_payload = []
    for rule in all_rules:
        code = str(rule.get("rule_code") or "").strip()
        count = problem_counts.get(code, 0)
        is_selected = code in selected_rules
        accuracy = rule.get("accuracy_type") or "uncertain"
        in_filtered = count > 0 and is_selected
        if in_filtered:
            badge = "accurate" if accuracy == "accurate" else "ai_confirmed"
        else:
            badge = ""
        rules_payload.append({
            **rule,
            "problem_count": count,
            "ai_confirmed_count": count if accuracy == "uncertain" else 0,
            "is_selected": is_selected,
            "is_in_filtered": in_filtered,
            "filtered_badge": badge,
        })

    functions = FunctionRepository(db).get_functions_by_file(file_info.id)
    files_payload = _build_files_payload(functions, file_info.extract_path)

    return {
        "files": files_payload,
        "problems": normalized_problems,
        "rules": rules_payload,
        "selected_rules": selected_rules,
        "language_mode": task_context.get("language_mode") or "c",
        "domain": "normalModeC",
        "task_id": task_id,
    }


def _build_files_payload(functions: Sequence[Any], extract_path: str) -> List[Dict[str, Any]]:
    files: Dict[str, Dict[str, Any]] = {}
    for func in functions or []:
        # 注意：AnalysisFunction.to_dict() 会截断 source_code，这里直接读完整字段
        if hasattr(func, "file_path"):
            file_path = str(getattr(func, "file_path", "") or "").replace("\\", "/")
            source_code = getattr(func, "source_code", "") or ""
        else:
            func_dict = dict(func)
            file_path = str(func_dict.get("file_path") or "").replace("\\", "/")
            source_code = func_dict.get("source_code") or ""
        if not file_path:
            continue
        if file_path not in files:
            files[file_path] = {
                "file_name": os.path.basename(file_path),
                "file_path": file_path,
                "source_code": source_code,
            }
        elif not files[file_path].get("source_code") and source_code:
            files[file_path]["source_code"] = source_code

    # 如果函数表为空，兜底扫描目录
    if not files and extract_path and os.path.isdir(extract_path):
        for root, _, names in os.walk(extract_path):
            for name in names:
                abs_path = os.path.join(root, name)
                rel_path = os.path.relpath(abs_path, extract_path).replace("\\", "/")
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                except Exception:
                    content = ""
                files[rel_path] = {
                    "file_name": name,
                    "file_path": rel_path,
                    "source_code": content,
                }
    return list(files.values())


def _normalize_problem(
    problem: Dict[str, Any],
    rule_map: Dict[str, Dict[str, Any]],
    default_rule_type: Optional[str] = None,
) -> Dict[str, Any]:
    issue_location = str(problem.get("issue_location") or "")
    issue_file = str(problem.get("file_name") or "").replace("\\", "/")
    issue_line = _parse_issue_line(issue_location, issue_file)

    rule_code = str(problem.get("violation_rules") or "").strip()
    # 兼容 "A; B" 取第一条
    if ";" in rule_code:
        rule_code = rule_code.split(";")[0].strip()

    # GJB_R_01_01_01 -> R-1-1-1
    _gjb = re.match(r'^GJB_R_(\d{2})_(\d{2})_(\d{2})$', rule_code)
    if _gjb:
        rule_code = f"R-{int(_gjb.group(1))}-{int(_gjb.group(2))}-{int(_gjb.group(3))}"

    rule_info = rule_map.get(rule_code, {})
    rule_type = rule_info.get("rule_type") or default_rule_type or _infer_rule_type(rule_code)
    accuracy_type = rule_info.get("accuracy_type") or "uncertain"

    return {
        "id": problem.get("id"),
        "issue_name": problem.get("issue_name") or rule_info.get("rule_name") or rule_code,
        "issue_file": issue_file,
        "issue_line": issue_line,
        "issue_location": issue_location,
        "issue_description": problem.get("description_issue") or "",
        "issue_level": problem.get("issue_level") or "一般问题",
        "rule_code": rule_code,
        "rule_type": str(rule_type).lower(),
        "rule_accuracy_type": accuracy_type,
        "ai_analyzed": True,
        "ai_is_real_issue": True,
        "problem_status": 0,
        "file_name": issue_file,
        "violation_rules": rule_code,
        "description_requirement": problem.get("description_requirement") or rule_info.get("rule_description") or "",
        "description_issue": problem.get("description_issue") or "",
        "description_location": problem.get("description_location") or issue_location,
        "description_impact": problem.get("description_impact") or "",
        "problem_sheet": _build_problem_sheet(
            rule_info=rule_info,
            issue_name=problem.get("issue_name") or rule_info.get("rule_name") or rule_code,
            rule_code=rule_code,
            rule_type=str(rule_type).lower(),
            description_requirement=problem.get("description_requirement") or rule_info.get("rule_description") or "",
            description_issue=problem.get("description_issue") or "",
            description_location=problem.get("description_location") or issue_location,
            description_impact=problem.get("description_impact") or "",
            source_code=problem.get("source_code") or "",
            issue_file=issue_file,
            issue_line=issue_line,
        ),
        "function_name": problem.get("function_name") or "",
    }


def _parse_issue_line(issue_location: str, issue_file: str) -> int:
    text = str(issue_location or "").strip()
    if not text:
        return 1
    # 常见格式: path:12 或 path(12) 或 第12行
    match = re.search(r":(\d+)\s*$", text)
    if match:
        return int(match.group(1))
    match = re.search(r"\((\d+)\)\s*$", text)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+)\s*行", text)
    if match:
        return int(match.group(1))
    if text.isdigit():
        return int(text)
    # 若 location 就是文件名，返回 1
    if issue_file and text.replace("\\", "/") == issue_file:
        return 1
    return 1


def _infer_rule_type(rule_code: str) -> str:
    upper = str(rule_code or "").upper()
    if upper.startswith("CWE") or upper.startswith("S_"):
        return "cwe"
    if upper.startswith("FPGA") or "VHDL" in upper or "VERILOG" in upper:
        return "fpga"
    return "gjb"
