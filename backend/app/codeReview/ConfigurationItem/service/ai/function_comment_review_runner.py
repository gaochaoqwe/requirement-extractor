"""
轻量注释专项审查任务

并行于主函数审查执行，仅检查两类问题：
1. 注释掉的代码可能带来的影响
2. 中文注释与代码逻辑明显不符
"""
import json
import os
import re
from typing import Any, Dict, List

from ...config import ALLOWED_CODE_EXTENSIONS
from ...config_database import get_db
from ...db.repository.function_repo import FunctionRepository
from ...db.repository.problem_repo import ProblemRepository
from .rules.codeReview import get_rules
from ...utils.concurrent_logger import (
    clear_current_thread_task,
    log_concurrent_debug,
    log_concurrent_error,
    log_concurrent_info,
    log_concurrent_warning,
    set_current_thread_task,
)
from ...utils.task_cancel_manager import task_cancel_manager
from .openai.client import AIClient
from .parser.function_parser import extract_functions_from_code, read_file_with_encoding

_COMMENT_REVIEW_PROMPT = """你是一名资深C/C++代码审查专家，现在只检查“注释专项问题”，且只能报告以下两类问题：
1. 注释掉的代码很可能导致关键逻辑被移除，进而产生实际问题
2. 中文注释与代码行为明显不符

你的目标是“高精度、低误报”，宁可少报也不要猜测。

严格要求：
- 只允许输出上述两类问题，禁止扩展到其他代码质量问题
- 必须高置信度，宁可少报也不要猜测
- 如果只是调试残留、备选实现、普通说明性注释，不能报告
- 如果中文注释只是过于简略、抽象、不够精确，但不构成明显冲突，不能报告
- 只有在从当前函数代码本身就能明确判断时，才允许报告
- 不允许基于“可能作者本意是这样”进行推断
- 若证据不足，必须返回空数组

对两类问题的进一步判定标准：

一、关于“注释掉的代码风险”
只有当被注释内容满足以下至少一项时才报告：
- 明显是会改变控制流的语句，如 if / else / return / break / continue / goto
- 明显是资源处理、状态更新、错误处理、数据赋值、函数调用等关键逻辑
- 从上下文可明确看出，当前函数因为这段代码被注释掉而遗漏了必要步骤

以下情况绝对不要报告：
- 注释中的示例代码、历史备选写法、调试打印、临时试验代码
- 只是看起来像代码，但无法确认对当前逻辑有实际影响
- 单纯的宏开关注释、说明性注释、伪代码说明

二、关于“中文注释与代码不符”
只有当中文注释与代码行为存在“明显冲突”时才报告，例如：
- 注释说“成功”但代码处理的是失败分支
- 注释说“发送”但代码实际是接收
- 注释说“释放资源”但代码没有释放、或执行的是完全不同动作
- 注释说“判断为空”但条件实际是非空

以下情况绝对不要报告：
- 注释描述粒度和代码粒度不同
- 注释较抽象，而代码是其具体实现
- 注释不够完整、不够专业、不够精确
- 仅仅是命名风格或术语习惯差异

输出要求：
- 如未发现问题，返回空数组
- 每个问题都必须能归类为“注释掉代码风险”或“中文注释与代码明显不符”之一
- description_issue 中必须明确写出属于哪一类问题
- description_location 是前端定位字段，必须严格使用这个格式：`<文件路径>文件的<函数名>函数的<行号或行号范围>行：<对应代码语句>源代码为：\n<保留关键上下文的源代码>`
- 例如：`tiny_test\\math_utils.c文件的auth_check函数的10-11行：// if (strcmp(password, \"123456\") != 0) {{源代码为：\nint auth_check(const char *password) {{\n    ......\n    // if (strcmp(password, \"123456\") != 0) {{\n    //     return 0;\n    // }}\n    return 1;\n}}`
- `源代码为：`后必须原样保留问题所在函数的关键上下文源代码；无关代码可以用`......`省略，但问题代码语句和必要上下文必须保持源代码原样
- 在JSON字符串中，`description_location`里的源码换行必须使用`\\n`表示，不能直接换行
- 绝对不要输出成 `tiny_test\\math_utils.c:auth_check的第10-11行：...` 这种格式
- 绝对不要省略“文件的”“函数的”“行：”“源代码为：”这几个关键字
- 如果无法确认精确行号，也必须给出最接近的行号或行号范围，并仍然遵守上述固定格式

禁止报告的问题类型如下：
{forbidden_rules}

请严格按以下JSON输出，不要输出任何额外说明：
{{
  "problems": [
    {{
      "file_name": "代码文件名称",
      "source_code": "当前函数完整代码",
      "problem_reason": "问题根因，需明确是注释掉代码风险或注释与代码不符",
      "issue_level": "建议改进|一般问题|重要问题",
      "issue_name": "问题名称",
      "issue_location": "代码文件名称:函数名称",
      "description_requirement": "从函数代码上下文推断该函数的预期功能和行为要求，描述该函数原本应当完成什么任务，如果无法从代码推断则描述问题代码语句所在的功能模块职责",
      "description_issue": "问题描述，且必须明确写出问题类别",
      "description_location": "xx文件的xx函数的xx行：问题代码语句源代码为：\\n保留关键上下文的源代码",
      "description_impact": "影响分析"
    }}
  ]
}}

当前文件：{file_path}
当前函数：{function_name}

函数代码如下：
```{language}
{source_code}
```
"""

_COMMENT_BLOCK_RE = re.compile(r'//.*?$|/\*[\s\S]*?\*/', re.MULTILINE)
_COMMENTED_CODE_HINT_RE = re.compile(
    r'^\s*(?:if|else|for|while|switch|return|goto|break|continue|[A-Za-z_]\w*\s*\(|[A-Za-z_]\w*\s*=|\*?[A-Za-z_]\w*\s*=|#\s*if|#\s*ifdef|#\s*ifndef)'
)
_CHINESE_RE = re.compile(r'[\u4e00-\u9fff]')
_ALLOWED_ISSUE_LEVELS = {'建议改进', '一般问题', '重要问题'}


def _extract_comment_blocks(source_code: str) -> List[str]:
    return [match.group(0) for match in _COMMENT_BLOCK_RE.finditer(source_code)]


def _has_commented_out_code(source_code: str) -> bool:
    for block in _extract_comment_blocks(source_code):
        lines = block.splitlines()
        for line in lines:
            text = re.sub(r'^\s*(//|/\*|\*)\s?', '', line).strip()
            text = text.replace('*/', '').strip()
            if text and _COMMENTED_CODE_HINT_RE.match(text):
                return True
    return False


def _has_chinese_comment(source_code: str) -> bool:
    return any(_CHINESE_RE.search(block) for block in _extract_comment_blocks(source_code))


def _should_review_function(source_code: str) -> bool:
    return _has_commented_out_code(source_code) or _has_chinese_comment(source_code)


def _read_candidate_functions(project_root: str) -> List[Dict[str, Any]]:
    all_functions: List[Dict[str, Any]] = []

    print(f"[comment_review][scan] 开始扫描项目目录: {project_root}")
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in {'__pycache__', '.git', 'node_modules', 'call_graph', 'call_graphs'}]
        for file_name in files:
            ext = os.path.splitext(file_name)[1].lower()
            if ext not in ALLOWED_CODE_EXTENSIONS:
                continue

            full_path = os.path.join(root, file_name)
            rel_path = os.path.relpath(full_path, project_root)
            print(f"[comment_review][scan] 检查文件: {rel_path}, ext={ext}")
            try:
                code, _ = read_file_with_encoding(full_path)
                if not code:
                    print(f"[comment_review][scan] 文件内容为空，跳过: {rel_path}")
                    continue
            except Exception as exc:
                print(f"[comment_review][scan] 读取文件失败: {rel_path}, error={exc}")
                log_concurrent_warning(f"[注释专项] 读取文件失败，跳过: {rel_path}, error={exc}", "comment_review")
                continue

            language = 'cpp' if ext in {'.cpp', '.cc', '.cxx', '.hpp', '.hxx'} else 'c'
            try:
                functions_in_file = extract_functions_from_code(code, language=language)
                print(f"[comment_review][scan] 解析函数成功: {rel_path}, count={len(functions_in_file)}")
            except Exception as exc:
                print(f"[comment_review][scan] 解析函数失败: {rel_path}, error={exc}")
                log_concurrent_warning(f"[注释专项] 解析函数失败，跳过: {rel_path}, error={exc}", "comment_review")
                continue

            for func_data in functions_in_file:
                function_name = func_data.get('function_name') or func_data.get('name')
                source_code = func_data.get('source_code')
                if not function_name or not source_code:
                    print(f"[comment_review][scan] 函数信息不完整，跳过: {rel_path}, function_name={function_name}")
                    continue
                should_review = _should_review_function(source_code)
                print(f"[comment_review][scan] 函数判定: {rel_path}:{function_name}, should_review={should_review}")
                if not should_review:
                    continue
                all_functions.append({
                    'function_name': function_name,
                    'source_code': source_code,
                    'file_path': rel_path,
                    'start_line': func_data.get('start_line') or 1,
                    'end_line': func_data.get('end_line') or max(1, len(source_code.splitlines())),
                    'language': language,
                })

    print(f"[comment_review][scan] 候选函数总数: {len(all_functions)}")
    return all_functions


def _parse_ai_result(result: Any, raw: str) -> Dict[str, Any]:
    if isinstance(result, dict) and isinstance(result.get('problems', []), list):
        return result

    cleaned = (raw or '').strip()
    if not cleaned:
        return {'problems': []}

    if cleaned.startswith('```'):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            cleaned = '\n'.join(lines[1:-1]).strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict) and isinstance(parsed.get('problems', []), list):
            return parsed
    except Exception:
        pass

    return {'problems': []}


def _classify_problem_text(problem: Dict[str, Any]) -> str:
    combined = ' '.join(
        str(problem.get(field, '') or '')
        for field in ('problem_reason', 'issue_name', 'description_issue', 'description_requirement', 'description_impact')
    )
    if any(keyword in combined for keyword in ['注释掉', '注释代码', '被注释', '注释掉的代码', '关键逻辑被移除']):
        return 'commented_out_code'
    if any(keyword in combined for keyword in ['注释与代码不符', '注释不符', '注释错误', '中文注释', '与代码行为明显不符']):
        return 'comment_mismatch'
    return ''


def _is_valid_problem(problem: Dict[str, Any]) -> bool:
    issue_level = str(problem.get('issue_level', '') or '').strip()
    if issue_level and issue_level not in _ALLOWED_ISSUE_LEVELS:
        return False

    description_issue = str(problem.get('description_issue', '') or '').strip()
    description_location = str(problem.get('description_location', '') or '').strip()
    if not description_issue or not description_location:
        return False
    if '文件的' not in description_location or '函数的' not in description_location or '行：' not in description_location:
        return False

    problem_type = _classify_problem_text(problem)
    if not problem_type:
        return False

    if problem_type == 'commented_out_code':
        required_keywords = ['注释掉', '注释代码', '被注释', '关键逻辑被移除']
        if not any(keyword in description_issue for keyword in required_keywords):
            return False

    if problem_type == 'comment_mismatch':
        required_keywords = ['注释与代码', '注释不符', '中文注释']
        if not any(keyword in description_issue for keyword in required_keywords):
            return False

    return True


def _build_function_aware_comment_snippet(function_code: str, line_no: int = 0, context: int = 3) -> str:
    source = (function_code or '').strip('\n')
    if not source:
        return ''

    lines = source.splitlines()
    if not lines:
        return ''

    if line_no <= 0 or line_no > len(lines):
        line_no = 1

    target_idx = line_no - 1
    open_idx = 0
    for idx, line in enumerate(lines):
        if '{' in line:
            open_idx = idx
            break

    close_idx = len(lines) - 1
    depth = 0
    seen_open = False
    for idx in range(open_idx, len(lines)):
        for char in lines[idx]:
            if char == '{':
                depth += 1
                seen_open = True
            elif char == '}' and seen_open:
                depth -= 1
                if depth == 0:
                    close_idx = idx
                    break
        if seen_open and depth == 0:
            break

    context_start = max(open_idx + 1, target_idx - context)
    context_end = min(close_idx - 1, target_idx + context)

    snippet = []
    snippet.extend(lines[:open_idx + 1])
    if context_start > open_idx + 1:
        snippet.append('......')
    if context_start <= context_end:
        snippet.extend(lines[context_start:context_end + 1])
    if context_end < close_idx - 1:
        snippet.append('......')
    if close_idx > open_idx:
        snippet.append(lines[close_idx])

    return '\n'.join(snippet)


def _ensure_description_location_source(description_location: str, func: Dict[str, Any]) -> str:
    location = (description_location or '').strip()
    if not location:
        return location

    if any(marker in location for marker in ('源代码为：', '源程序为：', '源代码为:', '源程序为:')):
        return location

    source_code = (func.get('source_code') or '').strip('\n')
    if not source_code:
        return location

    return f"{location}源代码为：\n{source_code}"


def _ensure_description_location_source(description_location: str, func: Dict[str, Any]) -> str:
    location = (description_location or '').strip()
    if not location:
        return location

    source_code = (func.get('source_code') or '').strip('\n')
    if not source_code:
        return location

    marker_match = re.search(r'(源代码为：|源程序为：|源代码为:|源程序为:)', location)
    prefix = location[:marker_match.start()].rstrip() if marker_match else location
    marker = marker_match.group(1) if marker_match else '源代码为：'

    line_no = 0
    line_match = re.search(r'(\d+)(?:\s*-\s*\d+)?\s*行', prefix)
    if line_match:
        absolute_line = int(line_match.group(1))
        try:
            start_line = int(func.get('start_line') or 1)
        except Exception:
            start_line = 1
        relative_line = absolute_line - start_line + 1
        line_no = relative_line if relative_line > 0 else absolute_line

    snippet = _build_function_aware_comment_snippet(source_code, line_no)
    if not snippet:
        return location

    return f"{prefix}{marker}\n{snippet}"


def _normalize_problem(problem: Dict[str, Any], func: Dict[str, Any]) -> Dict[str, Any]:
    reason = (problem.get('problem_reason') or '').strip()
    if not reason:
        reason = '发现注释掉代码风险或中文注释与代码逻辑不符'

    issue_level = (problem.get('issue_level') or '').strip()
    if issue_level not in _ALLOWED_ISSUE_LEVELS:
        issue_level = '一般问题'

    issue_name = (problem.get('issue_name') or '').strip() or '注释专项审查问题'
    description_issue = (problem.get('description_issue') or '').strip()
    description_location = _ensure_description_location_source(
        (problem.get('description_location') or '').strip(),
        func,
    )
    description_impact = (problem.get('description_impact') or '').strip()

    return {
        'file_name': problem.get('file_name') or func['file_path'],
        'source_code': problem.get('source_code') or func['source_code'],
        'problem_reason': reason,
        'issue_level': issue_level,
        'issue_name': issue_name,
        'issue_location': problem.get('issue_location') or f"{func['file_path']}:{func['function_name']}",
        'description_requirement': problem.get('description_requirement') or '注释应准确反映代码行为，且不应通过注释掉代码的方式移除关键逻辑。',
        'description_issue': description_issue,
        'description_location': description_location,
        'description_impact': description_impact,
    }


def _review_single_function(ai_client: AIClient, func: Dict[str, Any]) -> List[Dict[str, Any]]:
    prompt = _COMMENT_REVIEW_PROMPT.format(
        forbidden_rules=get_rules(),
        file_path=func['file_path'],
        function_name=func['function_name'],
        source_code=func['source_code'],
        language=func['language'],
    )

    print(
        f"[comment_review][ai] 开始审查函数: {func['file_path']}:{func['function_name']}, "
        f"source_len={len(func['source_code'])}, prompt_len={len(prompt)}"
    )

    try:
        result, raw = ai_client.call_ai_stream(prompt)
        print(
            f"[comment_review][ai] AI返回: {func['file_path']}:{func['function_name']}, "
            f"result_type={type(result).__name__}, raw_len={len(raw or '')}"
        )
        parsed = _parse_ai_result(result, raw)
        problems = parsed.get('problems', [])
        print(
            f"[comment_review][ai] 解析结果: {func['file_path']}:{func['function_name']}, "
            f"parsed_keys={list(parsed.keys()) if isinstance(parsed, dict) else 'n/a'}, "
            f"problems_type={type(problems).__name__}, problems_count={len(problems) if isinstance(problems, list) else 'n/a'}"
        )
        if not isinstance(problems, list):
            print(f"[comment_review][ai] problems不是list，直接返回空: {func['file_path']}:{func['function_name']}")
            return []

        normalized_problems: List[Dict[str, Any]] = []
        for idx, problem in enumerate(problems, start=1):
            if not isinstance(problem, dict):
                print(f"[comment_review][ai] 问题项不是dict，跳过: index={idx}, value={problem}")
                continue
            normalized = _normalize_problem(problem, func)
            is_valid = _is_valid_problem(normalized)
            print(
                f"[comment_review][ai] 问题校验: {func['file_path']}:{func['function_name']}, "
                f"index={idx}, issue_name={normalized.get('issue_name')}, is_valid={is_valid}"
            )
            if not is_valid:
                log_concurrent_debug(
                    f"[注释专项] 过滤低置信度问题: {func['file_path']}:{func['function_name']} -> {normalized.get('issue_name', '')}",
                    "comment_review",
                )
                continue
            normalized_problems.append(normalized)

        print(
            f"[comment_review][ai] 函数审查完成: {func['file_path']}:{func['function_name']}, "
            f"valid_problems={len(normalized_problems)}"
        )
        return normalized_problems
    except Exception as exc:
        print(f"[comment_review][ai] AI审查异常: {func['file_path']}:{func['function_name']}, error={exc}")
        log_concurrent_warning(
            f"[注释专项] AI审查失败: {func['file_path']}:{func['function_name']}, error={exc}",
            "comment_review",
        )
        return []


def run_function_comment_review_task(task_id: int, file_id: int, project_root: str) -> Dict[str, Any]:
    """运行轻量注释专项审查任务。"""
    print(f"[comment_review][task] 任务启动: task_id={task_id}, file_id={file_id}, project_root={project_root}")
    set_current_thread_task(task_id, file_id, thread_name='comment_review')
    db_gen = get_db()
    db = next(db_gen)

    try:
        log_concurrent_info(f"[注释专项] 任务启动，项目目录: {project_root}", "comment_review")

        candidate_functions = _read_candidate_functions(project_root)
        print(f"[comment_review][task] 候选函数数量: {len(candidate_functions)}")
        log_concurrent_info(
            f"[注释专项] 共筛选出 {len(candidate_functions)} 个候选函数进行检查",
            "comment_review",
        )

        if not candidate_functions:
            print(f"[comment_review][task] 无候选函数，直接完成: task_id={task_id}")
            return {'status': 'completed', 'reviewed_functions': 0, 'problems': 0}

        func_repo = FunctionRepository(db)
        prob_repo = ProblemRepository(db)
        ai_client = AIClient()
        print(f"[comment_review][task] AIClient初始化完成: task_id={task_id}")

        reviewed_count = 0
        problem_count = 0

        for func in candidate_functions:
            if task_cancel_manager.is_cancelled(task_id):
                print(f"[comment_review][task] 任务被取消: task_id={task_id}, reviewed_count={reviewed_count}")
                log_concurrent_warning(f"[注释专项] 任务 {task_id} 已取消，停止执行", "comment_review")
                return {'status': 'cancelled', 'reviewed_functions': reviewed_count, 'problems': problem_count}

            reviewed_count += 1
            print(f"[comment_review][task] 开始处理函数: {func['file_path']}:{func['function_name']}, index={reviewed_count}")
            log_concurrent_debug(
                f"[注释专项] 正在检查 {func['file_path']}:{func['function_name']}",
                "comment_review",
            )

            db_func = func_repo.get_or_create_function({
                'file_id': file_id,
                'function_name': func['function_name'],
                'source_code': func['source_code'],
                'file_path': func['file_path'],
                'start_line': func['start_line'],
                'end_line': func['end_line'],
            })
            print(f"[comment_review][task] 函数记录就绪: db_func_id={db_func.id}, function={func['function_name']}")

            problems = _review_single_function(ai_client, func)
            print(f"[comment_review][task] AI审查返回问题数: {len(problems)}, function={func['function_name']}")
            for idx, problem in enumerate(problems, start=1):
                print(
                    f"[comment_review][task] 准备落库问题: function={func['function_name']}, "
                    f"index={idx}, issue_name={problem.get('issue_name')}, source={problem.get('problem_source', 'comment_review')}"
                )
                prob_repo.create_problem({
                    'task_id': task_id,
                    'file_id': file_id,
                    'function_id': db_func.id,
                    'file_name': problem['file_name'],
                    'source_code': problem['source_code'],
                    'problem_reason': problem['problem_reason'],
                    'problem_source': 'comment_review',
                    'issue_level': problem['issue_level'],
                    'issue_name': problem['issue_name'],
                    'issue_location': problem['issue_location'],
                    'description_requirement': problem['description_requirement'],
                    'description_issue': problem['description_issue'],
                    'description_location': problem['description_location'],
                    'description_impact': problem['description_impact'],
                })
                problem_count += 1

            db.commit()
            print(
                f"[comment_review][task] 单函数处理完成并提交事务: {func['file_path']}:{func['function_name']}, "
                f"reviewed_count={reviewed_count}, total_problems={problem_count}"
            )

        log_concurrent_info(
            f"[注释专项] 任务完成，共检查 {reviewed_count} 个函数，发现 {problem_count} 个问题",
            "comment_review",
        )
        print(f"[comment_review][task] 任务完成: task_id={task_id}, reviewed_functions={reviewed_count}, problems={problem_count}")
        return {'status': 'completed', 'reviewed_functions': reviewed_count, 'problems': problem_count}
    except Exception as exc:
        db.rollback()
        print(f"[comment_review][task] 任务异常: task_id={task_id}, error={exc}")
        log_concurrent_error("[注释专项] 执行失败", "comment_review", exc)
        return {'status': 'failed', 'reviewed_functions': 0, 'problems': 0, 'error': str(exc)}
    finally:
        print(f"[comment_review][task] 任务结束，关闭数据库: task_id={task_id}")
        db.close()
        clear_current_thread_task()

