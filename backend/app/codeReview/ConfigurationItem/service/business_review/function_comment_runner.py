"""
函数注释任务 - 并行于链路审查，为代码目录树中的所有函数生成 AI 注释

设计原则：
- 并发度为 1，不影响链路审查的 API 限额
- 轻量单次调用，不使用 ReAct 多轮模式
- 结果存入 function_comments 表，前端按需查询
"""
import threading
import time
import json
from pathlib import Path
from typing import List, Dict, Any

from ...db.database_chain import get_chain_db_session
from ...db.models_chain import FunctionComment
from ...utils.concurrent_logger import (
    log_concurrent_info, log_concurrent_warning,
    log_concurrent_debug, log_concurrent_error
)


# ----------------------------------------------------------------
# Prompt
# ----------------------------------------------------------------

_COMMENT_PROMPT = """\
你是一名 C/C++ 代码注释专家。请对下面的函数进行注释，要求：
1. 在关键代码行上方或行尾用中文添加简洁注释，说明该行的作用
2. 不要修改任何代码逻辑
3. 提供一句话的函数功能描述

严格按以下 JSON 格式输出，不要输出任何其他内容：
{{"function_description": "...", "commented_code": "..."}}

函数代码：
```c
{code}
```
"""


# ----------------------------------------------------------------
# 工具函数
# ----------------------------------------------------------------

def _read_file(path: Path) -> str:
    """读取文件内容，自动检测编码"""
    for enc in ('utf-8', 'gbk', 'latin-1'):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return path.read_bytes().decode('utf-8', errors='replace')


def _extract_functions_from_file(file_path: Path, project_root: Path) -> List[Dict[str, Any]]:
    """
    从单个 .c/.h 文件中提取所有函数（名称 + 源码 + 相对路径）
    使用 tree-sitter 解析，与函数审查保持一致
    """
    results = []
    rel_path = str(file_path.relative_to(project_root))

    try:
        content = _read_file(file_path)
    except Exception:
        return results

    # 尝试使用 tree-sitter
    try:
        from ..ai.parser.function_parser import extract_functions_from_code
        
        # 检测语言
        file_ext = file_path.suffix.lower()
        if file_ext in ('.c', '.h'):
            language = 'c'
        elif file_ext in ('.cpp', '.cc', '.cxx', '.hpp', '.h++'):
            language = 'cpp'
        else:
            language = 'c'
        
        # 使用 tree-sitter 提取函数
        functions = extract_functions_from_code(content, language)
        
        for func_info in functions:
            # tree-sitter 返回的格式
            func_name = func_info.get('function_name')
            func_code = func_info.get('source_code')
            
            if not func_name or not func_code:
                continue
            
            # 添加调试日志
            print(f"[函数提取] 函数: {func_name}, 长度: {len(func_code)}")
            print(f"[函数提取] 函数代码前100字符: {func_code[:100]}")
            print(f"[函数提取] 函数代码后100字符: {func_code[-100:]}")
            
            if len(func_code) < 20 or len(func_code) > 8000:
                print(f"[函数提取] 跳过 {func_name}，长度不符合要求 (长度: {len(func_code)})")
                continue

            results.append({
                'file_path': rel_path,
                'function_name': func_name,
                'source_code': func_code,
            })
        
        return results
        
    except Exception as e:
        print(f"[函数提取] tree-sitter 提取失败: {e}，回退到正则表达式")
        # 回退到正则表达式
        return _extract_functions_regex_fallback(file_path, project_root, content)


def _extract_functions_regex_fallback(file_path: Path, project_root: Path, content: str) -> List[Dict[str, Any]]:
    """
    回退方案：使用正则表达式提取函数
    """
    import re
    results = []
    rel_path = str(file_path.relative_to(project_root))
    
    # 匹配函数定义起始行
    func_header_re = re.compile(
        r'^(?:(?:static|inline|extern|volatile|const)\s+)*'
        r'[\w\s\*]+?\s+(\w+)\s*\([^;]*\)\s*\{',
        re.MULTILINE
    )

    for m in func_header_re.finditer(content):
        func_name = m.group(1)
        if func_name in ('if', 'while', 'for', 'switch', 'return', 'else'):
            continue
        start = m.start()
        
        # 找到函数头中的 { 位置
        brace_start = m.end() - 1
        
        # 从 { 之后开始匹配括号
        depth = 1
        pos = brace_start + 1
        end = pos
        
        while pos < len(content):
            ch = content[pos]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = pos + 1
                    break
            pos += 1

        func_code = content[start:end].strip()
        
        print(f"[函数提取-回退] 函数: {func_name}, 长度: {len(func_code)}")
        
        if len(func_code) < 20 or len(func_code) > 8000:
            print(f"[函数提取-回退] 跳过 {func_name}，长度不符合要求 (长度: {len(func_code)})")
            continue

        results.append({
            'file_path': rel_path,
            'function_name': func_name,
            'source_code': func_code,
        })

    return results


def _collect_all_functions(project_root: str) -> List[Dict[str, Any]]:
    """遍历项目目录，收集所有 C/C++ 函数"""
    root = Path(project_root)
    IGNORE_DIRS = {'call_graph', 'call_graphs', '__pycache__', '.git', 'node_modules'}
    EXTENSIONS = {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp'}

    all_funcs = []
    for f in root.rglob('*'):
        if any(part in IGNORE_DIRS for part in f.parts):
            continue
        if f.is_file() and f.suffix in EXTENSIONS:
            funcs = _extract_functions_from_file(f, root)
            all_funcs.extend(funcs)
    return all_funcs


def _already_commented(task_id: int, file_path: str, function_name: str) -> bool:
    """检查数据库中是否已有该函数的注释（支持断点续传）"""
    try:
        with get_chain_db_session() as db:
            exists = db.query(FunctionComment).filter(
                FunctionComment.task_id == task_id,
                FunctionComment.file_path == file_path,
                FunctionComment.function_name == function_name,
                FunctionComment.status == 'completed'
            ).first()
            return exists is not None
    except Exception:
        return False


def _save_comment(task_id: int, file_path: str, function_name: str,
                  function_description: str, commented_code: str, status: str = 'completed'):
    """保存注释结果到数据库"""
    try:
        with get_chain_db_session() as db:
            db.query(FunctionComment).filter(
                FunctionComment.task_id == task_id,
                FunctionComment.file_path == file_path,
                FunctionComment.function_name == function_name,
            ).delete()
            record = FunctionComment(
                task_id=task_id,
                file_path=file_path,
                function_name=function_name,
                function_description=function_description,
                commented_code=commented_code,
                status=status,
            )
            db.add(record)
            db.commit()
    except Exception as e:
        log_concurrent_warning(
            f"[函数注释] 保存失败 {function_name}: {e}",
            "function_comment_runner"
        )


def _call_ai_for_comment(source_code: str) -> Dict[str, Any]:
    """单次调用 AI 生成注释（轻量，不使用 ReAct 多轮）"""
    from ..ai.openai.client import AIClient

    client = AIClient()
    prompt = _COMMENT_PROMPT.format(code=source_code)
    
    # 记录发送给 AI 的内容
    print(f"\n{'='*80}")
    print(f"[AI输入] 发送给AI的Prompt长度: {len(prompt)}")
    print(f"[AI输入] 源代码长度: {len(source_code)}")
    print(f"[AI输入] 源代码内容:\n{source_code}")
    print(f"{'='*80}\n")
    
    try:
        result, raw = client.call_ai_stream(prompt)
        
        # 记录 AI 的原始返回
        print(f"\n{'='*80}")
        print(f"[AI输出] 原始响应长度: {len(raw)}")
        print(f"[AI输出] 原始响应内容:\n{raw}")
        print(f"[AI输出] 解析后的结果: {result}")
        print(f"{'='*80}\n")
        
        if result and isinstance(result, dict):
            # 记录解析后的 commented_code
            commented_code = result.get('function_info', {}).get('commented_code', '')
            func_desc = result.get('function_info', {}).get('function_description', '')
            print(f"[AI解析] commented_code长度: {len(commented_code)}")
            print(f"[AI解析] function_description长度: {len(func_desc)}")
            print(f"[AI解析] commented_code内容:\n{commented_code}\n")
            return result
        if raw:
            cleaned = raw.strip()
            if cleaned.startswith('```'):
                lines = cleaned.split('\n')
                cleaned = '\n'.join(lines[1:-1])
            return json.loads(cleaned)
    except Exception as e:
        log_concurrent_warning(
            f"[函数注释] AI 调用失败: {e}",
            "function_comment_runner"
        )
        print(f"[AI错误] 调用失败: {e}\n")
    return {}


# ----------------------------------------------------------------
# 主任务
# ----------------------------------------------------------------

def run_function_comment_task(task_id: int, project_root: str):
    """
    函数注释主任务（在独立线程中运行，并发=1）

    Args:
        task_id: 链路审查任务 ID
        project_root: 代码项目根目录
    """
    log_concurrent_info(
        f"[函数注释] 任务 {task_id} 启动，项目目录: {project_root}",
        "function_comment_runner"
    )

    try:
        funcs = _collect_all_functions(project_root)
        log_concurrent_info(
            f"[函数注释] 共发现 {len(funcs)} 个函数，开始逐一注释（并发=1）",
            "function_comment_runner"
        )
    except Exception as e:
        log_concurrent_error(
            f"[函数注释] 遍历函数失败",
            "function_comment_runner", e
        )
        return

    for idx, func_info in enumerate(funcs, 1):
        file_path = func_info['file_path']
        func_name = func_info['function_name']
        source_code = func_info['source_code']

        # 已有注释则跳过
        if _already_commented(task_id, file_path, func_name):
            log_concurrent_debug(
                f"[函数注释] 跳过已注释: {file_path}:{func_name}",
                "function_comment_runner"
            )
            continue

        log_concurrent_info(
            f"[函数注释] ({idx}/{len(funcs)}) {file_path}:{func_name}",
            "function_comment_runner"
        )

        result = _call_ai_for_comment(source_code)
        if result:
            _save_comment(
                task_id=task_id,
                file_path=file_path,
                function_name=func_name,
                function_description=result.get('function_description', ''),
                commented_code=result.get('commented_code', source_code),
                status='completed'
            )
        else:
            _save_comment(
                task_id=task_id,
                file_path=file_path,
                function_name=func_name,
                function_description='',
                commented_code=source_code,
                status='failed'
            )

        # 短暂等待，避免触发限流
        time.sleep(0.5)

    log_concurrent_info(
        f"[函数注释] 任务 {task_id} 全部完成，共处理 {len(funcs)} 个函数",
        "function_comment_runner"
    )


def start_function_comment_task_async(task_id: int, project_root: str) -> threading.Thread:
    """
    在后台线程中启动函数注释任务（daemon，不阻塞链路审查）

    Returns:
        启动的后台线程
    """
    t = threading.Thread(
        target=run_function_comment_task,
        args=(task_id, project_root),
        daemon=True,
        name=f"func_comment_{task_id}"
    )
    t.start()
    log_concurrent_info(
        f"[函数注释] 后台注释线程已启动 (task_id={task_id})",
        "function_comment_runner"
    )
    return t

