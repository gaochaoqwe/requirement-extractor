"""
代码地图API端点

提供代码地图相关的RESTful API接口，包括：
- 获取代码地图数据
- 获取节点详情
- 获取问题信息
- 搜索功能
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import json
import os
from pathlib import Path

from ...utils.logger import log_debug, log_warning

from ...db.deps import get_db
from ...config_database_chain import get_chain_db  # 使用智能数据库切换模块
from ...config_database_feature import get_feature_db  # 使用智能数据库切换模块
from ...db.repository import TaskRepository, ProblemRepository, FileRepository
from ...db.repository.chain_problem_repo import ChainProblemRepository
from ...db.repository.file_problem_repo import FileProblemRepository
from ...db.repository.function_repo import FunctionRepository
from ...service.codemap.codemap_builder import CodeMapBuilder, create_code_map
from ...service.ai.parser.fpga.fpga_parser import read_file_with_encoding
from ...schemas.responses.codemap import (
    CodeMapResponse, 
    NodeDetailResponse, 
    ProblemsResponse,
    SearchResponse
)

router = APIRouter()

def read_file_with_multiple_encodings(file_path: str) -> str:
    """
    使用多种编码尝试读取文件，避免中文乱码
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件内容（字符串）
    """
    # 尝试多种编码
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            log_debug(f"成功使用 {encoding} 编码读取文件: {file_path}", "codemap")
            return content
        except (UnicodeDecodeError, LookupError):
            continue
    
    # 如果所有编码都失败，尝试使用chardet检测（如果可用）
    try:
        import chardet
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        detected = chardet.detect(raw_data)
        encoding = detected.get('encoding', 'utf-8')
        log_debug(f"使用chardet检测到编码: {encoding} (置信度: {detected.get('confidence', 0):.2f})", "codemap")
        return raw_data.decode(encoding, errors='replace')
    except (ImportError, Exception):
        pass
    
    # 最后的fallback：使用UTF-8并替换错误字符
    log_warning(f"所有编码尝试失败，使用UTF-8+replace读取: {file_path}", "codemap")
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

@router.get("/codemap/{task_id}", response_model=CodeMapResponse, summary="获取代码地图数据")
async def get_code_map(
    task_id: int,
    mode: Optional[str] = Query(
        None,
        description="代码地图模式：function、file、chain、feature；默认根据任务类型自动匹配"
    ),
    db: Session = Depends(get_db)
):
    """
    获取指定任务的代码地图数据
    
    Args:
        task_id: 分析任务ID
        
    Returns:
        代码地图数据，包括节点、边、统计信息等
    """
    try:
        # 获取任务信息
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        # 自动判断模式：优先使用显式参数，其次使用任务元数据
        normalized_mode = (mode or "").strip().lower()

        if not normalized_mode:
            analysis_type = (getattr(task, "analysis_type", "") or "").strip().lower()
            task_name = (getattr(task, "task_name", "") or "").strip()
            task_desc = (getattr(task, "task_description", "") or "").strip()

            if analysis_type in {"chain", "chain_review", "business", "business_review"}:
                normalized_mode = "chain"
            elif analysis_type in {"feature", "feature_review"}:
                normalized_mode = "feature"
            elif any(keyword in task_name for keyword in ["链路", "业务"]):
                normalized_mode = "chain"
            elif any(keyword in task_desc for keyword in ["链路", "业务"]):
                normalized_mode = "chain"
            elif any(keyword in task_name for keyword in ["功能"]):
                normalized_mode = "feature"
            elif any(keyword in task_desc for keyword in ["功能"]):
                normalized_mode = "feature"
            else:
                normalized_mode = "function"
        else:
            if normalized_mode in {"chain_review", "business", "business_review", "chain-mode"}:
                normalized_mode = "chain"
            elif normalized_mode in {"feature_review", "feature-mode"}:
                normalized_mode = "feature"

        if normalized_mode not in {"function", "file", "chain", "feature"}:
            normalized_mode = "function"

        if normalized_mode != (mode or ""):  # 记录自动推断结果
            log_debug(
                f"Resolved code map mode for task {task_id}: request={mode}, detected={normalized_mode}",
                "codemap"
            )

        mode = normalized_mode
        
        # 获取文件信息
        file_repo = FileRepository(db)
        file_info = file_repo.get_file(task.code_file_id)
        if not file_info or not file_info.extract_path:
            raise HTTPException(status_code=404, detail="代码文件不存在")
        
        # 检查解压路径是否存在
        if not os.path.exists(file_info.extract_path):
            raise HTTPException(status_code=404, detail="代码解压路径不存在")
        
        # 根据模式获取不同的数据
        if mode == "file":
            # 文件模式：获取文件级别的数据
            file_problem_repo = FileProblemRepository(db)
            file_problems = file_problem_repo.get_problems_by_task(task_id)
            
            # 构建文件级别的代码地图
            code_map = create_code_map(
                project_root=file_info.extract_path,
                language="auto",
                problems=[],  # 文件模式不显示函数级问题
                functions=[]
            )
            
            # 构建文件树形结构，并将问题分配到对应文件
            files_dict = {}
            
            # 解析合并的文件功能概述
            file_summaries = {}
            if file_info.file_function_summary:
                # 格式: [file_path]\nsummary\n\n[file_path]\nsummary
                import re
                summary_text = file_info.file_function_summary
                # 使用正则表达式分割
                pattern = r'\[([^\]]+)\]\s*\n(.*?)(?=\n\n\[|$)'
                matches = re.findall(pattern, summary_text, re.DOTALL)
                for file_path, summary in matches:
                    file_name = os.path.basename(file_path.strip())
                    file_summaries[file_name] = summary.strip()
            
            # 首先扫描项目目录获取所有代码文件
            import glob
            from ...config import ALL_SUPPORTED_EXTENSIONS
            
            for ext in ALL_SUPPORTED_EXTENSIONS:
                pattern = os.path.join(file_info.extract_path, "**", f"*{ext}")
                matching_files = glob.glob(pattern, recursive=True)
                
                for full_path in matching_files:
                    file_name = os.path.basename(full_path)
                    if file_name not in files_dict:
                        # 读取文件源代码（尝试多种编码）
                        try:
                            source_code = read_file_with_multiple_encodings(full_path)
                        except Exception as e:
                            source_code = f"// 无法读取文件源代码: {str(e)}"
                        
                        # 计算相对路径
                        try:
                            relative_path = os.path.relpath(full_path, file_info.extract_path)
                        except:
                            relative_path = full_path
                        
                        files_dict[file_name] = {
                            'id': f'file_{len(files_dict)}',
                            'name': file_name,
                            'path': relative_path,
                            'full_path': full_path,
                            'type': 'file',
                            'source_code': source_code,
                            'file_function_summary': file_summaries.get(file_name, f"文件: {file_name}"),
                            'problems': [],
                            'problemCount': 0
                        }
            
            # 如果有文件问题，按文件名分组并添加到对应文件
            if file_problems:
                for problem in file_problems:
                    file_name = problem.file_name
                    
                    # 如果文件不在字典中，添加它（可能是已删除的文件）
                    if file_name not in files_dict:
                        # 尝试在项目根目录下查找文件
                        file_path = problem.file_path or file_name
                        source_code = ""
                        full_path = None
                        
                        if file_path and os.path.exists(file_path):
                            full_path = file_path
                            try:
                                source_code = read_file_with_multiple_encodings(file_path)
                            except Exception as e:
                                source_code = f"// 无法读取文件源代码: {str(e)}"
                        else:
                            # 在项目根目录下查找
                            search_pattern = os.path.join(file_info.extract_path, "**", file_name)
                            matching_files = glob.glob(search_pattern, recursive=True)
                            if matching_files:
                                full_path = matching_files[0]
                                try:
                                    source_code = read_file_with_multiple_encodings(full_path)
                                except Exception as e:
                                    source_code = f"// 无法读取文件源代码: {str(e)}"
                            else:
                                source_code = f"// 文件未找到: {file_name}"
                        
                        # 计算相对路径
                        if full_path:
                            try:
                                relative_path = os.path.relpath(full_path, file_info.extract_path)
                            except:
                                relative_path = file_path or file_name
                        else:
                            relative_path = file_path or file_name
                        
                        files_dict[file_name] = {
                            'id': f'file_{len(files_dict)}',
                            'name': file_name,
                            'path': relative_path,
                            'full_path': full_path,
                            'type': 'file',
                            'source_code': source_code,
                            'file_function_summary': file_summaries.get(file_name, f"文件: {file_name}"),
                            'problems': [],
                            'problemCount': 0
                        }
                    
                    # 添加问题到文件
                    problem_dict = problem.to_dict()
                    files_dict[file_name]['problems'].append(problem_dict)
                    files_dict[file_name]['problemCount'] += 1
            
            # 构建文件树形数据
            file_tree = []
            for file_name, file_data in files_dict.items():
                file_tree.append(file_data)
            
            # 按文件名排序
            file_tree.sort(key=lambda x: x['name'])
            
            # 设置文件数据到code_map
            code_map.file_tree = file_tree
            code_map.problems = [p.to_dict() for p in file_problems] if file_problems else []
            
        elif mode == "chain":
            # 链路模式：获取链路级别的数据
            # 使用链路审查数据库
            chain_db = next(get_chain_db())
            try:
                chain_problem_repo = ChainProblemRepository(chain_db)
                chain_problems = chain_problem_repo.get_problems_by_task(task_id)
            finally:
                chain_db.close()

            # 获取函数信息（用于获取函数的文件路径和源代码）
            function_repo = FunctionRepository(db)
            all_functions = function_repo.get_functions_by_file(file_info.id)

            # 构建函数名到函数详情的映射
            function_map = {}
            for func in all_functions:
                function_map[func.function_name] = {
                    'function_name': func.function_name,
                    'file_path': func.file_path,
                    'source_code': func.source_code,
                    'start_line': func.start_line,
                    'end_line': func.end_line,
                    'function_description': func.function_description,
                    'commented_code': func.commented_code
                }

            # 使用基础代码地图，提取函数信息
            base_map = create_code_map(
                project_root=file_info.extract_path,
                language="auto",
                problems=[],
                functions=all_functions
            )

            # 构建链路树形结构
            chains_dict = {}
            if chain_problems:
                for problem in chain_problems:
                    chain_name = problem.chain_name
                    if chain_name not in chains_dict:
                        chains_dict[chain_name] = {
                            'id': f'chain_{len(chains_dict)}',
                            'name': chain_name,
                            'type': 'chain',
                            'description': problem.chain_function_description or f'链路: {chain_name}',
                            'entry_function': problem.entry_function,
                            'functions': [],
                            'problems': [],
                            'problemCount': 0
                        }

                    problem_dict = problem.to_dict()
                    chains_dict[chain_name]['problems'].append(problem_dict)
                    chains_dict[chain_name]['problemCount'] += 1

                    if problem.affected_functions:
                        try:
                            import json
                            functions = json.loads(problem.affected_functions)
                            if isinstance(functions, list):
                                for func_full_name in functions:
                                    if ':' in func_full_name:
                                        parts = func_full_name.rsplit(':', 1)
                                        file_part = parts[0] if len(parts) > 1 else None
                                        func_name = parts[1] if len(parts) > 1 else func_full_name
                                    else:
                                        file_part = None
                                        func_name = func_full_name

                                    if not any(f.get('function_name') == func_name for f in chains_dict[chain_name]['functions']):
                                        if func_name in function_map:
                                            chains_dict[chain_name]['functions'].append(function_map[func_name])
                                        else:
                                            chains_dict[chain_name]['functions'].append({
                                                'function_name': func_name,
                                                'file_path': file_part,
                                                'source_code': f'// 函数 {func_name} 的源代码未找到\n// 原始标识: {func_full_name}',
                                                'start_line': 0,
                                                'end_line': 0
                                            })
                        except Exception:
                            functions = problem.affected_functions.split(',')
                            for func_full_name in functions:
                                func_full_name = func_full_name.strip()
                                if func_full_name:
                                    if ':' in func_full_name:
                                        parts = func_full_name.rsplit(':', 1)
                                        file_part = parts[0] if len(parts) > 1 else None
                                        func_name = parts[1] if len(parts) > 1 else func_full_name
                                    else:
                                        file_part = None
                                        func_name = func_full_name

                                    if not any(f.get('function_name') == func_name for f in chains_dict[chain_name]['functions']):
                                        if func_name in function_map:
                                            chains_dict[chain_name]['functions'].append(function_map[func_name])
                                        else:
                                            chains_dict[chain_name]['functions'].append({
                                                'function_name': func_name,
                                                'file_path': file_part,
                                                'source_code': f'// 函数 {func_name} 的源代码未找到\n// 原始标识: {func_full_name}',
                                                'start_line': 0,
                                                'end_line': 0
                                            })

            chain_tree_data = sorted(chains_dict.values(), key=lambda x: x['name'])
            chain_problems_data = [problem.to_dict() for problem in chain_problems] if chain_problems else []
            code_map = base_map
            
            # ✅ 修复链路模式代码树：从 file_tree 构建目录树结构
            file_tree_flat = code_map.get('file_tree', [])
            if file_tree_flat:
                # 构建目录树：递归组织文件路径为树形结构
                def build_directory_tree_from_files(file_list, root_path):
                    """
                    从扁平的文件列表构建目录树结构
                    
                    Args:
                        file_list: 扁平的文件列表 [{name, file_path, children: [functions]}]
                        root_path: 项目根路径
                    
                    Returns:
                        树形结构的根节点
                    """
                    import os
                    from pathlib import Path
                    
                    # 使用字典存储目录节点: path -> node
                    tree_nodes = {}
                    
                    # 根节点名称：从文件路径的第一段提取（最可靠，就是用户上传的代码库目录名）
                    # 例如 file_path='tiny_test/math_utils.c' -> root_name='tiny_test'
                    root_name = None
                    for fi in file_list:
                        fp = fi.get('file_path', fi.get('name', '')).replace('\\', '/')
                        parts = fp.split('/')
                        if len(parts) > 1:
                            root_name = parts[0]
                            break
                    if not root_name:
                        # 兜底：取 extract_path 下非 call_graph 的第一个子目录
                        try:
                            subdirs = sorted([d for d in os.listdir(root_path)
                                              if os.path.isdir(os.path.join(root_path, d)) and d != 'call_graph'])
                            root_name = subdirs[0] if subdirs else (os.path.basename(root_path) or 'project')
                        except Exception:
                            root_name = os.path.basename(root_path) or 'project'
                    root_node = {
                        'id': 'root',
                        'name': root_name,
                        'label': root_name,
                        'type': 'directory',
                        'path': root_path,
                        'children': [],
                        'problemCount': 0
                    }
                    tree_nodes[''] = root_node
                    
                    # 遍历所有文件
                    for file_info in file_list:
                        file_path = file_info.get('file_path', file_info.get('name', ''))
                        if not file_path:
                            continue
                        
                        # 规范化路径分隔符（Windows -> Unix）
                        file_path = file_path.replace('\\', '/')
                        
                        # 如果路径第一段与根节点名称相同，剥离该前缀，避免根节点名称重复出现
                        path_parts_check = file_path.split('/')
                        original_file_path = file_path  # 保留原始路径，用于 API 请求
                        if path_parts_check and path_parts_check[0] == root_name:
                            file_path = '/'.join(path_parts_check[1:]) if len(path_parts_check) > 1 else file_path
                        
                        # 拆分路径为各级目录和文件名
                        path_parts = file_path.split('/')
                        
                        # 构建目录层次结构
                        current_path = ''
                        parent_node = root_node
                        
                        # 处理目录部分（除最后一个文件名）
                        for i, part in enumerate(path_parts[:-1]):
                            current_path = f"{current_path}/{part}" if current_path else part
                            
                            # 如果该目录节点不存在，创建它
                            if current_path not in tree_nodes:
                                dir_node = {
                                    'id': f'dir:{current_path}',
                                    'name': part,
                                    'label': part,
                                    'type': 'directory',
                                    'path': current_path,
                                    'children': [],
                                    'problemCount': 0
                                }
                                tree_nodes[current_path] = dir_node
                                parent_node['children'].append(dir_node)
                            
                            parent_node = tree_nodes[current_path]
                        
                        # 处理文件节点（最后一个部分）
                        file_name = path_parts[-1]
                        file_node = {
                            'id': file_info.get('id', f'file:{file_path}'),
                            'name': file_name,
                            'label': file_name,
                            'type': 'file',
                            'path': original_file_path,  # 使用原始完整相对路径，供 API 请求
                            'file_path': original_file_path,
                            'children': file_info.get('children', []),  # 函数列表
                            'problemCount': file_info.get('problemCount', 0),
                            'problems': file_info.get('problems', [])
                        }
                        
                        parent_node['children'].append(file_node)
                        
                        # 累加问题数到父目录
                        problem_count = file_info.get('problemCount', 0)
                        if problem_count > 0:
                            # 向上传播问题数
                            temp_path = current_path
                            while temp_path in tree_nodes:
                                tree_nodes[temp_path]['problemCount'] += problem_count
                                # 找到父路径
                                if '/' in temp_path:
                                    temp_path = '/'.join(temp_path.split('/')[:-1])
                                else:
                                    break
                            root_node['problemCount'] += problem_count
                    
                    return root_node
                
                # 构建目录树
                directory_tree = build_directory_tree_from_files(file_tree_flat, file_info.extract_path)
                
                # 将目录树添加到 code_map 的 project 字段中
                if 'project' not in code_map:
                    code_map['project'] = {}
                code_map['project']['tree'] = directory_tree
                
                log_debug(
                    f"✅ 链路模式目录树构建成功: "
                    f"files={len(file_tree_flat)}, "
                    f"root_children={len(directory_tree.get('children', []))}",
                    "codemap"
                )

        else:
            # 函数模式（默认）：获取函数级别的数据
            problem_repo = ProblemRepository(db)
            problems = problem_repo.get_problems_by_task(task_id)
            
            # 获取函数信息（包含AI生成的描述和注释代码）
            function_repo = FunctionRepository(db)
            functions = function_repo.get_functions_by_file(file_info.id)
            
            # 构建函数级别的代码地图
            code_map = create_code_map(
                project_root=file_info.extract_path,
                language="auto",  # 自动检测项目类型
                problems=problems,
                functions=functions
            )
        
        # 转换为响应格式
        map_data = code_map
        map_data.setdefault("project", {})
        map_data["project"].update({
            "name": file_info.file_name,
            "mode": mode,
            "root_path": file_info.extract_path,
            "task_id": task.id
        })
        project_stats = map_data.setdefault("statistics", {}).setdefault("project", {})
        project_stats.setdefault("total_nodes", len(map_data.get("nodes", [])))
        project_stats.setdefault("total_edges", len(map_data.get("edges", [])))
        project_stats.setdefault("total_problems", len(map_data.get("problems", [])))

        # 在链路模式下，附加链路树和问题列表
        if mode == "chain":
            map_data.setdefault("chains", {})
            map_data["chains"].update({
                "tree": chain_tree_data,
                "problems": chain_problems_data,
                "problem_count": len(chain_problems_data)
            })
            chain_tree_preview = [item.get("name") for item in chain_tree_data[:5]]
        else:
            chain_tree_preview = []

        project_tree = map_data.get("project", {}).get("tree")
        log_debug(
            (
                f"codemap summary | task_id={task_id} | mode={mode} | nodes={len(map_data.get('nodes', []))} "
                f"| edges={len(map_data.get('edges', []))} | problems={len(map_data.get('problems', []))} "
                f"| project_tree={'yes' if project_tree else 'no'} | chain_tree_preview={chain_tree_preview}"
            ),
            "codemap"
        )

        if not project_tree:
            log_warning(
                (
                    f"codemap missing project tree | task_id={task_id} | mode={mode} | "
                    f"project_keys={list(map_data.get('project', {}).keys())}"
                ),
                "codemap"
            )
        
        return CodeMapResponse(
            success=True,
            data=map_data,
            message="代码地图获取成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取代码地图失败: {str(e)}")


@router.get("/codemap/{task_id}/file/{file_path:path}", summary="获取文件源代码")
async def get_file_source(
    task_id: int,
    file_path: str,
    db: Session = Depends(get_db)
):
    """
    获取指定文件的源代码
    
    Args:
        task_id: 分析任务ID
        file_path: 文件路径
        
    Returns:
        文件源代码内容
    """
    try:
        # 获取任务信息
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 获取文件信息
        file_repo = FileRepository(db)
        file_info = file_repo.get_file(task.code_file_id)
        if not file_info or not file_info.extract_path:
            raise HTTPException(status_code=404, detail="代码文件不存在")
        
        # 构建完整的文件路径
        full_file_path = os.path.join(file_info.extract_path, file_path)
        
        # 检查文件是否存在
        if not os.path.exists(full_file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 读取文件内容（尝试多种编码）
        try:
            source_code = read_file_with_multiple_encodings(full_file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")
        
        return {
            "success": True,
            "data": {
                "file_path": file_path,
                "source_code": source_code
            },
            "message": "文件源代码获取成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件源代码失败: {str(e)}")


@router.get("/codemap/{task_id}/node/{node_id}", response_model=NodeDetailResponse, summary="获取节点详情")
async def get_node_detail(
    task_id: int,
    node_id: str,
    db: Session = Depends(get_db)
):
    """
    获取指定节点的详细信息
    
    Args:
        task_id: 分析任务ID
        node_id: 节点ID
        
    Returns:
        节点详细信息，包括源代码、调用关系、问题等
    """
    try:
        # 获取任务和文件信息
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        file_repo = FileRepository(db)
        file_info = file_repo.get_file(task.code_file_id)
        if not file_info or not file_info.extract_path:
            raise HTTPException(status_code=404, detail="代码文件不存在")
        
        # 获取问题列表
        problem_repo = ProblemRepository(db)
        problems = problem_repo.get_problems_by_task(task_id)
        
        # 获取函数信息（包含AI生成的描述和注释代码）
        from ...db.repository.function_repo import FunctionRepository
        function_repo = FunctionRepository(db)
        functions = function_repo.get_functions_by_file(file_info.id)
        
        # 构建代码地图
        code_map = create_code_map(
            project_root=file_info.extract_path,
            language="auto",  # 自动检测项目类型
            problems=problems,
            functions=functions
        )
        
        # 查找指定节点
        target_node = None
        for node in code_map.nodes:
            if node.id == node_id:
                target_node = node
                break
        
        if not target_node:
            raise HTTPException(status_code=404, detail="节点不存在")
        
        # 获取相关的边信息
        incoming_edges = [edge for edge in code_map.edges if edge.target == node_id]
        outgoing_edges = [edge for edge in code_map.edges if edge.source == node_id]
        
        return NodeDetailResponse(
            success=True,
            data={
                "node": target_node.__dict__,
                "incoming_edges": [edge.__dict__ for edge in incoming_edges],
                "outgoing_edges": [edge.__dict__ for edge in outgoing_edges],
                "related_nodes": {
                    "callers": [edge.source for edge in incoming_edges if edge.type == "calls"],
                    "callees": [edge.target for edge in outgoing_edges if edge.type == "calls"],
                    "children": target_node.children,
                    "parent": target_node.parent
                }
            },
            message="节点详情获取成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取节点详情失败: {str(e)}")


@router.get("/codemap/{task_id}/problems", response_model=ProblemsResponse, summary="获取问题列表")
async def get_problems(
    task_id: int,
    node_id: Optional[str] = Query(None, description="节点ID，用于过滤特定节点的问题"),
    status: Optional[int] = Query(None, description="问题状态：1=新发现，2=已查看，3=已过滤，4=已标记"),
    exclude_filtered: Optional[bool] = Query(False, description="是否排除已过滤的问题（状态3）"),
    db: Session = Depends(get_db)
):
    """
    获取代码地图中的问题列表
    
    Args:
        task_id: 分析任务ID
        node_id: 可选，节点ID，用于过滤特定节点的问题
        status: 可选，按状态过滤
        exclude_filtered: 是否排除已过滤的问题
        
    Returns:
        问题列表
    """
    try:
        # 获取任务信息
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 获取问题列表
        problem_repo = ProblemRepository(db)
        
        # 根据状态获取问题
        if status is not None:
            problems = problem_repo.get_problems_by_status(task_id, status)
        else:
            problems = problem_repo.get_problems_by_task(task_id)
        
        # 如果需要排除已过滤的问题
        if exclude_filtered:
            problems = [p for p in problems if p.get('problem_status') != 3]
        
        # 如果指定了节点ID，过滤问题
        if node_id:
            # 解析节点ID获取函数名
            if node_id.startswith("func:"):
                parts = node_id.split(":")
                if len(parts) >= 3:
                    function_name = parts[2]
                    problems = [p for p in problems if p.get('function_name') == function_name]
        
        return ProblemsResponse(
            success=True,
            data=problems,
            message="问题列表获取成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取问题列表失败: {str(e)}")


@router.get("/codemap/{task_id}/search", response_model=SearchResponse, summary="搜索代码地图")
async def search_code_map(
    task_id: int,
    query: str = Query(..., description="搜索关键词"),
    search_type: str = Query("all", description="搜索类型：all, function, file, problem"),
    db: Session = Depends(get_db)
):
    """
    在代码地图中搜索
    
    Args:
        task_id: 分析任务ID
        query: 搜索关键词
        search_type: 搜索类型
        
    Returns:
        搜索结果
    """
    try:
        # 获取任务和文件信息
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        file_repo = FileRepository(db)
        file_info = file_repo.get_file(task.code_file_id)
        if not file_info or not file_info.extract_path:
            raise HTTPException(status_code=404, detail="代码文件不存在")
        
        # 获取问题列表
        problem_repo = ProblemRepository(db)
        problems = problem_repo.get_problems_by_task(task_id)
        
        # 获取函数信息（包含AI生成的描述和注释代码）
        from ...db.repository.function_repo import FunctionRepository
        function_repo = FunctionRepository(db)
        functions = function_repo.get_functions_by_file(file_info.id)
        
        # 构建代码地图
        code_map = create_code_map(
            project_root=file_info.extract_path,
            language="auto",  # 自动检测项目类型
            problems=problems,
            functions=functions
        )
        
        # 执行搜索
        results = []
        query_lower = query.lower()
        
        # 搜索节点
        if search_type in ["all", "function", "file"]:
            for node in code_map.nodes:
                if search_type == "function" and node.type != "function":
                    continue
                if search_type == "file" and node.type != "file":
                    continue
                
                # 搜索节点名称
                if query_lower in node.name.lower():
                    results.append({
                        "type": "node",
                        "id": node.id,
                        "name": node.name,
                        "node_type": node.type,
                        "file_path": node.file_path,
                        "match_type": "name"
                    })
                
                # 搜索源代码内容
                if query_lower in node.source_code.lower():
                    results.append({
                        "type": "node",
                        "id": node.id,
                        "name": node.name,
                        "node_type": node.type,
                        "file_path": node.file_path,
                        "match_type": "source_code"
                    })
        
        # 搜索问题
        if search_type in ["all", "problem"]:
            for problem in problems:
                problem_text = f"{problem.get('issue_name', '')} {problem.get('description_issue', '')} {problem.get('problem_reason', '')}"
                if query_lower in problem_text.lower():
                    results.append({
                        "type": "problem",
                        "id": f"problem:{problem.get('id')}",
                        "name": problem.get('issue_name', ''),
                        "description": problem.get('description_issue', ''),
                        "function_name": problem.get('function_name', ''),
                        "file_name": problem.get('file_name', ''),
                        "match_type": "content"
                    })
        
        return SearchResponse(
            success=True,
            data=results,
            message=f"搜索完成，找到{len(results)}个结果"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/codemap/{task_id}/statistics", summary="获取代码地图统计信息")
async def get_statistics(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    获取代码地图的统计信息
    
    Args:
        task_id: 分析任务ID
        
    Returns:
        统计信息
    """
    try:
        # 获取任务和文件信息
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        file_repo = FileRepository(db)
        file_info = file_repo.get_file(task.code_file_id)
        if not file_info or not file_info.extract_path:
            raise HTTPException(status_code=404, detail="代码文件不存在")
        
        # 获取问题列表
        problem_repo = ProblemRepository(db)
        problems = problem_repo.get_problems_by_task(task_id)
        
        # 获取函数信息（包含AI生成的描述和注释代码）
        from ...db.repository.function_repo import FunctionRepository
        function_repo = FunctionRepository(db)
        functions = function_repo.get_functions_by_file(file_info.id)
        
        # 构建代码地图
        code_map = create_code_map(
            project_root=file_info.extract_path,
            language="auto",  # 自动检测项目类型
            problems=problems,
            functions=functions
        )
        
        return {
            "success": True,
            "data": code_map.statistics,
            "message": "统计信息获取成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.post("/codemap/{task_id}/export", summary="导出代码地图")
async def export_code_map(
    task_id: int,
    export_format: str = Query("json", description="导出格式：json, dot, svg"),
    db: Session = Depends(get_db)
):
    """
    导出代码地图到指定格式
    
    Args:
        task_id: 分析任务ID
        export_format: 导出格式
        
    Returns:
        导出结果
    """
    try:
        # 获取任务和文件信息
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        file_repo = FileRepository(db)
        file_info = file_repo.get_file(task.code_file_id)
        if not file_info or not file_info.extract_path:
            raise HTTPException(status_code=404, detail="代码文件不存在")
        
        # 获取问题列表
        problem_repo = ProblemRepository(db)
        problems = problem_repo.get_problems_by_task(task_id)
        
        # 获取函数信息（包含AI生成的描述和注释代码）
        from ...db.repository.function_repo import FunctionRepository
        function_repo = FunctionRepository(db)
        functions = function_repo.get_functions_by_file(file_info.id)
        
        # 构建代码地图
        code_map = create_code_map(
            project_root=file_info.extract_path,
            language="auto",  # 自动检测项目类型
            problems=problems,
            functions=functions
        )
        
        # 根据格式导出
        if export_format == "json":
            builder = CodeMapBuilder(file_info.extract_path, "auto")
            data = builder.to_dict(code_map)
            return {
                "success": True,
                "data": data,
                "message": "JSON导出成功"
            }
        elif export_format == "dot":
            # 生成DOT格式（Graphviz）
            dot_content = _generate_dot_format(code_map)
            return {
                "success": True,
                "data": {"content": dot_content},
                "message": "DOT格式导出成功"
            }
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


def _generate_dot_format(code_map) -> str:
    """生成DOT格式的图形描述"""
    lines = ["digraph CodeMap {"]
    lines.append("  rankdir=TB;")
    lines.append("  node [shape=box];")
    
    # 添加节点
    for node in code_map.nodes:
        color = "lightblue" if node.type == "file" else "lightgreen"
        if node.problems:
            color = "lightcoral"
        
        label = f"{node.name}\\n({node.type})"
        if node.problems:
            label += f"\\n{len(node.problems)} problems"
        
        lines.append(f'  "{node.id}" [label="{label}", fillcolor="{color}", style=filled];')
    
    # 添加边
    for edge in code_map.edges:
        style = "solid" if edge.type == "calls" else "dashed"
        lines.append(f'  "{edge.source}" -> "{edge.target}" [style="{style}"];')
    
    lines.append("}")
    return "\n".join(lines) 