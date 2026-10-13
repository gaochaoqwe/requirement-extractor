from typing import Dict, Any, List
from pathlib import Path
import json
import os

from ...ai.openai.client import AIClient
from ...ai.parser.all_graph_parser import build_project_call_graph


def _compact_call_graph(project_root: str, max_nodes: int = 400, max_edges: int = 800) -> Dict[str, Any]:
    # 导入并发日志系统
    from ....utils.concurrent_logger import log_concurrent_info, log_concurrent_warning, log_concurrent_debug
    
    log_concurrent_debug(f"[调用图构建] 开始构建项目调用关系图: {project_root}", "chain_planner")
    
    try:
        graph = build_project_call_graph(project_root)
        log_concurrent_info(f"[调用图构建] 原始调用图包含 {len(graph)} 个函数", "chain_planner")
        
        # 调试原始图的结构
        if isinstance(graph, dict):
            if 'edges' in graph and 'nodes' in graph:
                log_concurrent_debug(f"[调用图构建] 原始图为标准格式，节点: {len(graph.get('nodes', []))}, 边: {len(graph.get('edges', []))}", "chain_planner")
            else:
                log_concurrent_debug(f"[调用图构建] 原始图为函数字典格式，前3个函数: {list(graph.keys())[:3]}", "chain_planner")
                # 调试函数信息结构
                if graph:
                    first_func = list(graph.values())[0]
                    log_concurrent_debug(f"[调用图构建] 函数信息示例: {first_func}", "chain_planner")
        
        # graph 结构是 {func_name: func_info} 其中func_info包含calls字段
        nodes = []
        edges = []
        
        # 处理原始调用图数据
        if isinstance(graph, dict) and 'edges' in graph and 'nodes' in graph:
            # 如果已经是标准格式
            nodes = graph.get('nodes', [])[:max_nodes]
            edges = graph.get('edges', [])[:max_edges]
            log_concurrent_debug(f"[调用图构建] 使用标准格式，节点: {len(nodes)}, 边: {len(edges)}", "chain_planner")
        else:
            # 转换函数信息格式为节点-边格式
            for i, (func_name, func_info) in enumerate(list(graph.items())[:max_nodes]):
                # 添加节点（包含文件信息）
                file_path = func_info.get('file_path', '')
                relative_path = os.path.relpath(file_path, project_root) if file_path else 'unknown'
                nodes.append({
                    'name': func_name,
                    'file': relative_path,
                    'id': func_name
                })
                
                # 添加调用边
                calls = func_info.get('calls', [])
                for callee in calls:
                    if callee in graph:  # 只添加项目内部的调用关系
                        edges.append({
                            'caller': func_name,     # 添加caller字段
                            'callee': callee,        # 添加callee字段
                            'source': func_name,     # 保持原有字段
                            'target': callee,        # 保持原有字段
                            'caller_file': relative_path
                        })
                    if len(edges) >= max_edges:
                        break
                
                if len(edges) >= max_edges:
                    break
            
            log_concurrent_info(f"[调用图构建] 转换完成 - 节点: {len(nodes)}, 边: {len(edges)}", "chain_planner")
            
            if len(nodes) == 0:
                log_concurrent_warning(f"[调用图构建] ⚠️ 未找到任何函数！可能的原因:", "chain_planner")
                log_concurrent_warning(f"  1. 项目目录为空或不包含C/C++源文件", "chain_planner")
                log_concurrent_warning(f"  2. 源文件解析失败", "chain_planner")
                log_concurrent_warning(f"  3. tree-sitter解析器未正确初始化", "chain_planner")
            
    except Exception as e:
        log_concurrent_warning(f"[调用图构建] 构建调用关系图时出错: {e}", "chain_planner")
        nodes = []
        edges = []
    
    result = {'nodes': nodes, 'edges': edges}
    log_concurrent_debug(f"[调用图构建] 最终调用图: {len(nodes)} 节点, {len(edges)} 边", "chain_planner")
    return result


def _build_planning_prompt(software_type: str,
                           kb: Dict[str, Any],
                           entry_function: str,
                           dir_context: List[str],
                           file_summaries: List[Dict[str, str]],
                           call_graph_snip: Dict[str, Any]) -> str:
    dir_preview = "\n".join(dir_context[:200])
    kb_text = (kb.get('kb_text') or '')[:3000]
    defect_text = (kb.get('defect_text') or '')[:1500]

    files_block = "\n".join([f"- {it['file']}: {it.get('summary','')}" for it in file_summaries[:300]])
    graph_json = json.dumps(call_graph_snip)[:6000]

    return f"""
你是资深软件架构与领域专家。请基于函数调用关系和入口函数，为业务功能级别审查制定"调用链路清单"。

**核心要求：**
1. 必须根据函数交联情况（调用关系）制定审查链路
2. 必须从入口函数"{entry_function}"出发，沿调用路径划分功能链路
3. 每个审查链路代表一个完整的业务功能项
4. 所有链路加起来需要覆盖整个代码库
5. 每个链路应包含从调用者到被调用者的完整调用路径

**分析步骤：**
1. 找到入口函数"{entry_function}"
2. 分析从入口函数开始的各个调用分支
3. 将相关的调用路径组织成功能链路
4. 确保每个链路是一个独立且完整的功能模块

输出：严格JSON格式，字段如下：
{{
  "chains": [
    {{
      "name": "功能名称（如：系统初始化链路、图像处理链路等）",
      "rationale": "基于调用关系的划分依据",
      "entry_point": "{entry_function}",
      "functions": [{{"file": "相对路径", "function": "函数名"}}, ...],
      "call_edges": [{{"caller": {{"file":"...","function":"..."}}", "callee": {{"file":"...","function":"..."}}"}},...],
      "coverage_description": "此链路覆盖的功能范围"
    }}
  ]
}}

【软件类型】{software_type}
【领域知识】\n{kb_text}
【典型缺陷】\n{defect_text}
【入口函数】{entry_function}
【项目结构】\n{dir_preview}
【文件功能】\n{files_block}
【函数调用关系图（重要！）】\n{graph_json}

请仔细分析调用关系图，确保链路划分反映真实的函数调用流程。
"""


def plan_chains(task_id: int,
                software_type: str,
                kb: Dict[str, Any],
                entry_function: str,
                project_root: str,
                dir_context: List[str],
                files_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # 导入并发日志系统
    from ....utils.concurrent_logger import log_concurrent_info, log_concurrent_debug, log_concurrent_warning
    
    file_summaries = [{"file": d.get("file"), "summary": d.get("summary", "")} for d in files_docs]
    graph_snip = _compact_call_graph(project_root)
    graph_json = json.dumps(graph_snip)[:6000]  # 生成JSON字符串供日志使用
    prompt = _build_planning_prompt(software_type, kb, entry_function, dir_context, file_summaries, graph_snip)

    # 记录AI输入信息
    log_concurrent_info(f"[链路规划] 开始调用AI进行链路规划", "chain_planner")
    log_concurrent_info(f"[链路规划] 软件类型: {software_type}, 入口函数: {entry_function}", "chain_planner")
    log_concurrent_info(f"[链路规划] 文件概述数量: {len(file_summaries)}, 调用图节点数: {len(graph_snip.get('nodes', []))}, 调用边数: {len(graph_snip.get('edges', []))}", "chain_planner")
    
    # 详细记录调用关系图信息
    if graph_snip.get('nodes') or graph_snip.get('edges'):
        log_concurrent_info(f"[链路规划] 调用关系图样例节点: {[n.get('name', 'unknown') for n in graph_snip.get('nodes', [])[:10]]}", "chain_planner")
        log_concurrent_info(f"[链路规划] 调用关系图样例边: {[(e.get('source'), e.get('target')) for e in graph_snip.get('edges', [])[:10]]}", "chain_planner")
        log_concurrent_debug(f"[链路规划] 完整调用关系图JSON（长度: {len(graph_json)} 字符）:\n{graph_json}", "chain_planner")
    else:
        log_concurrent_warning(f"[链路规划] ⚠️ 调用关系图为空！无法为AI提供函数调用信息", "chain_planner")
        log_concurrent_warning(f"[链路规划] 调用关系图原始数据: {graph_snip}", "chain_planner")
    
    log_concurrent_debug(f"[链路规划] 完整AI输入提示词（长度: {len(prompt)} 字符）:\n{prompt}", "chain_planner")

    # 使用链路审查专用配置文件
    # 路径: planner -> business_review -> service -> ConfigurationItem -> codeReview -> app -> utils
    chain_review_config_path = (
        Path(__file__).parent  # planner
        .parent  # business_review
        .parent  # service
        .parent  # ConfigurationItem
        .parent  # codeReview
        .parent  # app
        / "utils" / "chain_review_config.json"
    )
    client = AIClient(config_path=str(chain_review_config_path))
    result, raw = client.call_ai_stream(prompt)
    
    # 记录AI输出信息
    log_concurrent_info(f"[链路规划] AI响应完成", "chain_planner")
    log_concurrent_debug(f"[链路规划] AI原始响应（长度: {len(raw)} 字符）:\n{raw}", "chain_planner")
    log_concurrent_debug(f"[链路规划] AI解析结果:\n{json.dumps(result, ensure_ascii=False, indent=2)}", "chain_planner")
    
    chains = result.get('chains') or []
    log_concurrent_info(f"[链路规划] 成功解析出 {len(chains)} 条链路", "chain_planner")
    
    # 记录每条链路的基本信息
    for i, chain in enumerate(chains):
        chain_name = chain.get('name', f'链路{i+1}')
        functions_count = len(chain.get('functions', []))
        edges_count = len(chain.get('call_edges', []))
        log_concurrent_info(f"[链路规划] 链路 {i+1}: {chain_name}, 包含 {functions_count} 个函数, {edges_count} 个调用边", "chain_planner")
        log_concurrent_debug(f"[链路规划] 链路 {i+1} 详细信息:\n{json.dumps(chain, ensure_ascii=False, indent=2)}", "chain_planner")
    
    # 兜底：如果返回不是列表，置空
    if not isinstance(chains, list):
        log_concurrent_warning(f"[链路规划] AI返回结果不是列表格式，重置为空列表", "chain_planner")
        chains = []
    return chains 