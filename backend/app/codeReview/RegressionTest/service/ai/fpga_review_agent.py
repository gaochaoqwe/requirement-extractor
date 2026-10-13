"""FPGA代码审查Agent - 基于ReAct模式的智能FPGA审查

针对FPGA代码特点设计的Agent，支持：
- Verilog (.v)
- VHDL (.vhd, .vhdl)

提供FPGA专用工具：
1. 查询模块端口定义
2. 查询信号声明
3. 查询子模块实例化
4. 查询状态机定义
5. 查询时钟和复位信号
6. 查询参数/泛型定义
"""
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from .openai.client import AIClient
from .parser.fpga.fpga_parser import extract_fpga_files_from_code, read_file_with_encoding
from ...utils.concurrent_logger import log_concurrent_info, log_concurrent_warning, log_concurrent_debug, log_concurrent_error


class FPGAReviewAgent:
    """FPGA代码审查Agent - 基于ReAct模式的智能审查"""
    
    def __init__(self, project_root: str, language: str = 'verilog'):
        """
        初始化FPGA Agent
        
        Args:
            project_root: 项目根目录
            language: FPGA语言（verilog/vhdl）
        """
        self.project_root = Path(project_root)
        self.language = language
        self.ai_client = AIClient()
        
        # Agent配置
        self.max_iterations = 50  # 最多50轮推理
        self.max_tool_calls_per_iteration = 5  # 每轮最多5个工具调用
        
        # 缓存，避免重复读取
        self.file_cache = {}
        self.module_cache = {}
    
    def review_module(
        self,
        module_code: str,
        module_name: str,
        file_path: str,
        forbidden_rules: str
    ) -> Dict[str, Any]:
        """
        审查FPGA模块/实体
        
        Args:
            module_code: 模块代码
            module_name: 模块名
            file_path: 文件路径
            forbidden_rules: 禁止报告的规则
            
        Returns:
            审查结果 {problems: [], function_info: {}}
        """
        log_concurrent_info(f"[FPGA Agent] 开始审查模块: {module_name}", "fpga_review_agent")
        
        # 初始化对话历史
        conversation = []
        
        # 系统提示词
        system_prompt = self._build_system_prompt(forbidden_rules)
        conversation.append({"role": "system", "content": system_prompt})
        
        # 初始任务
        initial_task = self._build_initial_task(module_code, module_name, file_path)
        conversation.append({"role": "user", "content": initial_task})
        
        # ReAct循环
        final_result = None
        for iteration in range(self.max_iterations):
            current_iteration = iteration + 1
            log_concurrent_debug(f"[FPGA Agent] 第 {current_iteration} 轮推理", "fpga_review_agent")
            
            # 推理提醒
            if current_iteration == 15:
                conversation.append({
                    "role": "user",
                    "content": "⚠️ 提醒：已经进行了15轮推理，请尽快完成审查并给出结论。"
                })
            elif current_iteration == 20:
                conversation.append({
                    "role": "user",
                    "content": "⚠️ 重要提醒：已经进行了20轮推理，请立即总结并输出最终审查结果（JSON格式）。"
                })
            
            # 调用AI
            response = self._call_ai_with_tools(conversation)
            
            # 检查是否完成
            if response.get('finished'):
                final_result = response.get('result', {})
                log_concurrent_info(f"[FPGA Agent] 审查完成，发现 {len(final_result.get('problems', []))} 个问题", "fpga_review_agent")
                break
            
            # 执行工具调用
            if response.get('tool_calls'):
                tool_results = self._execute_tools(response['tool_calls'])
                
                # 准备tool_calls格式
                clean_tool_calls = [
                    {
                        "id": tc.get('id'),
                        "type": tc.get('type'),
                        "function": tc.get('function')
                    }
                    for tc in response['tool_calls']
                ]
                
                # 添加AI响应到历史
                conversation.append({
                    "role": "assistant",
                    "content": response.get('content', ''),
                    "tool_calls": clean_tool_calls
                })
                
                # 添加工具结果
                for tool_call, tool_result in zip(response['tool_calls'], tool_results):
                    conversation.append({
                        "role": "tool",
                        "tool_call_id": tool_call.get('id'),
                        "name": tool_call.get('function', {}).get('name'),
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })
            else:
                log_concurrent_warning(f"[FPGA Agent] AI未调用工具也未给出答案", "fpga_review_agent")
                break
        
        # 返回结果或默认值
        if final_result is None:
            log_concurrent_warning(
                f"[FPGA Agent] 在{self.max_iterations}轮推理后仍未完成审查", 
                "fpga_review_agent"
            )
            final_result = {
                "problems": [],
                "function_info": {
                    "function_name": module_name,
                    "function_description": "审查超时未完成",
                    "commented_code": module_code
                }
            }
        
        return final_result
    
    def _build_system_prompt(self, forbidden_rules: str) -> str:
        """构建FPGA专用系统提示词"""
        lang_name = "Verilog" if self.language == 'verilog' else "VHDL"
        return f"""你是一名专业的FPGA代码审查专家Agent。你的任务是审查{lang_name}代码，找出潜在的代码问题。

**你是一个Agent**，这意味着：
1. 你可以主动调用工具来获取需要的信息
2. 你不需要一次性得到所有信息，可以根据需要逐步探索
3. 你应该根据代码的复杂性决定是否需要查看依赖函数或全局变量

**⚠️ 重要提示**：
- 请尽量在 **20轮推理内** 完成审查
- 不要过度探索，聚焦于影响功能的关键问题
- 如果代码逻辑清晰且无明显问题，可以直接给出结论


**禁止报告的问题类型**：
{forbidden_rules}

**输出格式要求**：
最终必须输出标准JSON格式的审查结果。

字段含义：
- file_name: 文件名
- source_code: 模块代码
- problem_reason: 问题根本原因
- issue_level: 问题等级（建议改进、一般问题、重要问题）
- issue_name: 问题名称
- issue_location: 问题来源（文件名+模块名）
- description_requirement: 需求描述
- description_issue: 问题描述
- description_location: 问题定位（格式：xx文件的xx模块的xx行：问题代码语句）
- description_impact: 影响分析

**function_info字段含义**：
- function_name: 模块名称
- function_description: 模块功能描述
- commented_code: 注释后的代码（**必须添加尽可能详细注释**）

JSON示例：
{{{{
  "problems": [
    {{{{
      "file_name": "counter.v",
      "source_code": "...",
      "problem_reason": "异步复位信号未经同步处理",
      "issue_level": "重要问题",
      "issue_name": "异步信号同步问题",
      "issue_location": "counter.v:counter",
      "description_requirement": "异步信号应先经过同步器处理",
      "description_issue": "rst信号直接使用，可能导致亚稳态",
      "description_location": "counter.v文件的counter模块的15行：always @(posedge clk or negedge rst)",
      "description_impact": "可能导致状态机错乱或数据损坏"
    }}}}
  ],
  "function_info": {{{{
    "function_name": "counter",
    "function_description": "这是一个8位同步计数器模块，支持异步复位和使能控制",
    "commented_code": "// 8位同步计数器模块\\\\nmodule counter(\\\\n    input clk,        // 系统时钟输入，上升沿有效\\\\n    input rst_n,      // 异步复位信号，低电平有效\\\\n    input enable,     // 计数使能信号，高电平有效\\\\n    output reg [7:0] count  // 8位计数输出，寄存器类型\\\\n);\\\\n\\\\n// 主要计数逻辑：同步时序逻辑块\\\\nalways @(posedge clk or negedge rst_n) begin\\\\n    if (!rst_n) begin\\\\n        // 异步复位：立即将计数器清零\\\\n        count <= 8'b0;\\\\n    end else if (enable) begin\\\\n        // 使能有效时：在时钟上升沿递增计数\\\\n        count <= count + 1'b1;\\\\n    end\\\\n    // 使能无效时：保持当前计数值不变\\\\nend\\\\n\\\\nendmodule"
  }}}}
}}}}

**关键要求**：
- 返回完整可解析的JSON
- 字符串中换行符用\\\\n转义
- function_info字段必须始终提供
- issue_level必须是"建议改进"、"一般问题"、"重要问题"之一
"""
    
    def _build_initial_task(self, module_code: str, module_name: str, file_path: str) -> str:
        """构建初始任务"""
        lang_name = "Verilog" if self.language == 'verilog' else "VHDL"
        return f"""请审查以下{lang_name}模块：

**文件**：{file_path}
**模块名**：{module_name}
**代码**：
```{self.language}
{module_code}
```

**请开始全面审查**。您可以：
1. 根据您的专业判断，识别任何类型的潜在问题

**审查完成后，请严格按照系统提示词中的JSON格式输出结果，特别注意：**

** - commented_code详细注释要求：**
1. **添加尽量多详细的注释**
2. **注释要解释代码的具体作用和设计意图**
"""
    
    def _call_ai_with_tools(self, conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
        """调用AI（支持function calling）"""
        
        # FPGA专用工具定义
        tools_definition = [
            {
                "type": "function",
                "function": {
                    "name": "get_module_ports",
                    "description": "获取FPGA模块的端口定义（输入/输出端口、位宽、类型）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "module_name": {
                                "type": "string",
                                "description": "模块名称"
                            }
                        },
                        "required": ["module_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_signal_declarations",
                    "description": "获取模块内信号声明（wire, reg, signal等）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "module_name": {
                                "type": "string",
                                "description": "模块名称"
                            },
                            "signal_type": {
                                "type": "string",
                                "enum": ["all", "wire", "reg", "signal"],
                                "description": "信号类型过滤，默认all"
                            }
                        },
                        "required": ["module_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_submodule_instances",
                    "description": "获取模块中实例化的子模块列表及其端口连接",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "module_name": {
                                "type": "string",
                                "description": "父模块名称"
                            }
                        },
                        "required": ["module_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_state_machines",
                    "description": "查找并分析模块中的状态机定义（状态声明、状态转换）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "module_name": {
                                "type": "string",
                                "description": "模块名称"
                            }
                        },
                        "required": ["module_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_clock_reset_signals",
                    "description": "获取模块中的时钟和复位信号定义及使用情况",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "module_name": {
                                "type": "string",
                                "description": "模块名称"
                            }
                        },
                        "required": ["module_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_parameters",
                    "description": "获取模块的参数/泛型定义（parameter, generic）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "module_name": {
                                "type": "string",
                                "description": "模块名称"
                            }
                        },
                        "required": ["module_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_pattern",
                    "description": "在代码中搜索特定模式（如always块、process块、敏感列表等）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern_type": {
                                "type": "string",
                                "enum": ["always", "process", "assign", "sensitivity", "clock_domain"],
                                "description": "搜索模式类型"
                            },
                            "module_name": {
                                "type": "string",
                                "description": "模块名称（可选，不指定则搜索所有模块）"
                            }
                        },
                        "required": ["pattern_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file_content",
                    "description": "读取指定文件的完整内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径（相对于项目根目录）"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            }
        ]
        
        try:
            log_concurrent_debug(f"[FPGA Agent] 调用AI，对话轮数: {len(conversation)}", "fpga_review_agent")
            
            max_tokens = self.ai_client.model_params.get("max_tokens", None)
            
            api_params = {
                "model": self.ai_client.default_model,
                "messages": conversation,
                "tools": tools_definition,
                "tool_choice": "auto",
                "temperature": 0.2
            }
            
            if max_tokens is not None and max_tokens > 0:
                api_params["max_tokens"] = max_tokens
            
            response = self.ai_client.client.chat.completions.create(**api_params)
            
            message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason
            
            # 处理工具调用
            if message.tool_calls:
                return {
                    'finished': False,
                    'tool_calls': [
                        {
                            'id': tc.id,
                            'type': tc.type,
                            'function': {
                                'name': tc.function.name,
                                'arguments': tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ],
                    'content': message.content or ''
                }
            
            # 尝试解析最终JSON结果
            content = message.content or ''
            if content.strip():
                # 记录AI的原始响应到日志
                log_concurrent_info(
                    f"[FPGA Agent] AI返回最终结果，原始响应内容：\n{'='*60}\n{content}\n{'='*60}",
                    "fpga_review_agent"
                )
                
                result = self._try_parse_json(content)
                if result:
                    # 如果解析成功，记录详细的模块信息
                    if isinstance(result, dict):
                        function_info = result.get('function_info', {})
                        if function_info:
                            log_concurrent_info(
                                f"[FPGA Agent] 模块信息解析成功：\n"
                                f"{'='*60}\n"
                                f"模块名称: {function_info.get('function_name', 'N/A')}\n"
                                f"功能描述: {function_info.get('function_description', 'N/A')}\n"
                                f"注释后代码长度: {len(function_info.get('commented_code', ''))} 字符\n"
                                f"发现问题数量: {len(result.get('problems', []))}\n"
                                f"{'='*60}",
                                "fpga_review_agent"
                            )
                            
                            # 单独记录注释后的代码（如果存在）
                            commented_code = function_info.get('commented_code', '')
                            if commented_code:
                                log_concurrent_info(
                                    f"[FPGA Agent] AI返回的注释后代码：\n"
                                    f"{'='*60}\n"
                                    f"{commented_code}\n"
                                    f"{'='*60}",
                                    "fpga_review_agent"
                                )
                        
                        # 记录发现的问题详情
                        problems = result.get('problems', [])
                        if problems:
                            log_concurrent_info(
                                f"[FPGA Agent] 发现的问题详情：\n{'='*60}",
                                "fpga_review_agent"
                            )
                            for i, problem in enumerate(problems, 1):
                                log_concurrent_info(
                                    f"问题 {i}:\n"
                                    f"  等级: {problem.get('issue_level', 'N/A')}\n"
                                    f"  名称: {problem.get('issue_name', 'N/A')}\n"
                                    f"  位置: {problem.get('description_location', 'N/A')}\n"
                                    f"  描述: {problem.get('description_issue', 'N/A')[:200]}{'...' if len(problem.get('description_issue', '')) > 200 else ''}",
                                    "fpga_review_agent"
                                )
                            log_concurrent_info(f"{'='*60}", "fpga_review_agent")
                    
                    return {'finished': True, 'result': result}
            
            return {'finished': False, 'content': content}
            
        except Exception as e:
            log_concurrent_error(f"[FPGA Agent] AI调用失败", "fpga_review_agent", e)
            return {'finished': False, 'error': str(e)}
    
    def _try_parse_json(self, content: str) -> Optional[Dict[str, Any]]:
        """尝试解析JSON内容"""
        try:
            # 移除可能的markdown代码块标记
            content = re.sub(r'^```json\s*', '', content, flags=re.MULTILINE)
            content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)
            content = content.strip()
            
            result = json.loads(content)
            
            # 验证必需字段
            if 'problems' in result and 'function_info' in result:
                return result
            
        except json.JSONDecodeError as e:
            log_concurrent_debug(f"[FPGA Agent] JSON解析失败: {e}", "fpga_review_agent")
        except Exception as e:
            log_concurrent_debug(f"[FPGA Agent] 结果验证失败: {e}", "fpga_review_agent")
        
        return None
    
    def _execute_tools(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """执行工具调用"""
        results = []
        
        for tool_call in tool_calls:
            function_name = tool_call['function']['name']
            try:
                arguments = json.loads(tool_call['function']['arguments'])
            except json.JSONDecodeError:
                arguments = {}
            
            log_concurrent_debug(f"[FPGA Agent] 执行工具: {function_name}({arguments})", "fpga_review_agent")
            
            # 路由到对应的工具方法
            if function_name == 'get_module_ports':
                result = self._tool_get_module_ports(arguments)
            elif function_name == 'get_signal_declarations':
                result = self._tool_get_signal_declarations(arguments)
            elif function_name == 'get_submodule_instances':
                result = self._tool_get_submodule_instances(arguments)
            elif function_name == 'find_state_machines':
                result = self._tool_find_state_machines(arguments)
            elif function_name == 'get_clock_reset_signals':
                result = self._tool_get_clock_reset_signals(arguments)
            elif function_name == 'get_parameters':
                result = self._tool_get_parameters(arguments)
            elif function_name == 'search_pattern':
                result = self._tool_search_pattern(arguments)
            elif function_name == 'read_file_content':
                result = self._tool_read_file_content(arguments)
            else:
                result = {'error': f'Unknown tool: {function_name}'}
            
            results.append(result)
        
        return results
    
    # ========== FPGA专用工具实现 ==========
    
    def _tool_get_module_ports(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """工具：获取模块端口定义"""
        module_name = args.get('module_name', '')
        
        try:
            # 在项目中搜索模块定义
            for file_path in self.project_root.rglob('*.[vV]'):  # Verilog
                code, _ = read_file_with_encoding(str(file_path))
                if not code:
                    continue
                
                # 简单解析：查找module声明
                pattern = rf'module\s+{module_name}\s*(?:#\([^)]*\))?\s*\(([^;]*)\);'
                match = re.search(pattern, code, re.DOTALL)
                if match:
                    ports_str = match.group(1)
                    # 解析端口列表
                    ports = []
                    for line in ports_str.split(','):
                        line = line.strip()
                        if line:
                            # 简化的端口解析
                            port_match = re.match(r'(input|output|inout)\s+(?:wire|reg)?\s*(?:\[[^\]]+\])?\s*(\w+)', line)
                            if port_match:
                                direction, name = port_match.groups()
                                ports.append({'name': name, 'direction': direction, 'definition': line})
                    
                    return {'found': True, 'module': module_name, 'ports': ports, 'file': str(file_path.relative_to(self.project_root))}
            
            # VHDL支持
            for file_path in self.project_root.rglob('*.vhd*'):
                code, _ = read_file_with_encoding(str(file_path))
                if not code:
                    continue
                
                pattern = rf'entity\s+{module_name}\s+is(.*?)end\s+entity'
                match = re.search(pattern, code, re.DOTALL | re.IGNORECASE)
                if match:
                    entity_body = match.group(1)
                    # 提取port定义
                    port_match = re.search(r'port\s*\((.*?)\);', entity_body, re.DOTALL | re.IGNORECASE)
                    if port_match:
                        ports_str = port_match.group(1)
                        return {'found': True, 'module': module_name, 'ports_definition': ports_str, 'file': str(file_path.relative_to(self.project_root))}
            
            return {'found': False, 'module': module_name, 'message': '未找到模块定义'}
            
        except Exception as e:
            return {'error': str(e)}
    
    def _tool_get_signal_declarations(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """工具：获取信号声明"""
        module_name = args.get('module_name', '')
        signal_type = args.get('signal_type', 'all')
        
        try:
            # 搜索模块并提取信号声明
            for file_path in self.project_root.rglob('*.[vV]'):
                code, _ = read_file_with_encoding(str(file_path))
                if not code:
                    continue
                
                # 查找module内容
                pattern = rf'module\s+{module_name}\s*[^;]*;(.*?)endmodule'
                match = re.search(pattern, code, re.DOTALL)
                if match:
                    module_body = match.group(1)
                    signals = []
                    
                    # 查找wire声明
                    if signal_type in ['all', 'wire']:
                        for wire_match in re.finditer(r'wire\s+(?:\[[^\]]+\])?\s*(\w+)\s*;', module_body):
                            signals.append({'type': 'wire', 'name': wire_match.group(1)})
                    
                    # 查找reg声明
                    if signal_type in ['all', 'reg']:
                        for reg_match in re.finditer(r'reg\s+(?:\[[^\]]+\])?\s*(\w+)\s*;', module_body):
                            signals.append({'type': 'reg', 'name': reg_match.group(1)})
                    
                    return {'found': True, 'module': module_name, 'signals': signals, 'count': len(signals)}
            
            return {'found': False, 'module': module_name}
            
        except Exception as e:
            return {'error': str(e)}
    
    def _tool_get_submodule_instances(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """工具：获取子模块实例化"""
        module_name = args.get('module_name', '')
        
        try:
            for file_path in self.project_root.rglob('*.[vV]'):
                code, _ = read_file_with_encoding(str(file_path))
                if not code:
                    continue
                
                pattern = rf'module\s+{module_name}\s*[^;]*;(.*?)endmodule'
                match = re.search(pattern, code, re.DOTALL)
                if match:
                    module_body = match.group(1)
                    instances = []
                    
                    # 查找实例化模式：module_name instance_name (...)
                    for inst_match in re.finditer(r'(\w+)\s+(?:#\([^)]*\))?\s*(\w+)\s*\([^;]+\);', module_body):
                        sub_module_name, instance_name = inst_match.groups()
                        instances.append({'submodule': sub_module_name, 'instance_name': instance_name})
                    
                    return {'found': True, 'module': module_name, 'instances': instances, 'count': len(instances)}
            
            return {'found': False, 'module': module_name}
            
        except Exception as e:
            return {'error': str(e)}
    
    def _tool_find_state_machines(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """工具：查找状态机"""
        module_name = args.get('module_name', '')
        
        try:
            for file_path in self.project_root.rglob('*.[vV]'):
                code, _ = read_file_with_encoding(str(file_path))
                if not code:
                    continue
                
                pattern = rf'module\s+{module_name}\s*[^;]*;(.*?)endmodule'
                match = re.search(pattern, code, re.DOTALL)
                if match:
                    module_body = match.group(1)
                    
                    # 查找状态定义（parameter或localparam）
                    states = []
                    for state_match in re.finditer(r'(?:parameter|localparam)\s+(\w+)\s*=\s*[\w\']+', module_body):
                        state_name = state_match.group(1)
                        if 'STATE' in state_name.upper() or 'ST_' in state_name.upper():
                            states.append(state_name)
                    
                    # 查找case语句（状态转换）
                    case_blocks = re.findall(r'case\s*\((\w+)\)(.*?)endcase', module_body, re.DOTALL)
                    
                    return {
                        'found': True,
                        'module': module_name,
                        'states': states,
                        'state_count': len(states),
                        'case_blocks_count': len(case_blocks)
                    }
            
            return {'found': False, 'module': module_name}
            
        except Exception as e:
            return {'error': str(e)}
    
    def _tool_get_clock_reset_signals(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """工具：获取时钟和复位信号"""
        module_name = args.get('module_name', '')
        
        try:
            for file_path in self.project_root.rglob('*.[vV]'):
                code, _ = read_file_with_encoding(str(file_path))
                if not code:
                    continue
                
                # 查找always块的敏感列表
                clocks = []
                resets = []
                
                for always_match in re.finditer(r'always\s*@\s*\(([^)]+)\)', code):
                    sensitivity = always_match.group(1)
                    
                    # 查找时钟信号（posedge/negedge）
                    for clk_match in re.finditer(r'(?:posedge|negedge)\s+(\w+)', sensitivity):
                        sig_name = clk_match.group(1)
                        if 'clk' in sig_name.lower() or 'clock' in sig_name.lower():
                            if sig_name not in clocks:
                                clocks.append(sig_name)
                        elif 'rst' in sig_name.lower() or 'reset' in sig_name.lower():
                            if sig_name not in resets:
                                resets.append(sig_name)
                
                if clocks or resets:
                    return {'found': True, 'clocks': clocks, 'resets': resets}
            
            return {'found': False, 'message': '未找到时钟或复位信号'}
            
        except Exception as e:
            return {'error': str(e)}
    
    def _tool_get_parameters(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """工具：获取参数定义"""
        module_name = args.get('module_name', '')
        
        try:
            for file_path in self.project_root.rglob('*.[vV]'):
                code, _ = read_file_with_encoding(str(file_path))
                if not code:
                    continue
                
                pattern = rf'module\s+{module_name}\s*#?\s*\(([^;]*?)\)\s*\('
                match = re.search(pattern, code, re.DOTALL)
                if match:
                    param_section = match.group(1)
                    parameters = []
                    
                    for param_match in re.finditer(r'parameter\s+(?:\w+\s+)?(\w+)\s*=\s*([^,)]+)', param_section):
                        name, value = param_match.groups()
                        parameters.append({'name': name.strip(), 'default_value': value.strip()})
                    
                    return {'found': True, 'module': module_name, 'parameters': parameters}
            
            return {'found': False, 'module': module_name}
            
        except Exception as e:
            return {'error': str(e)}
    
    def _tool_search_pattern(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """工具：搜索代码模式"""
        pattern_type = args.get('pattern_type', '')
        module_name = args.get('module_name')
        
        try:
            results = []
            
            for file_path in self.project_root.rglob('*.[vV]'):
                code, _ = read_file_with_encoding(str(file_path))
                if not code:
                    continue
                
                if pattern_type == 'always':
                    # 查找always块
                    for match in re.finditer(r'always\s*@\s*\([^)]+\)', code):
                        results.append({
                            'file': str(file_path.relative_to(self.project_root)),
                            'pattern': match.group(0)
                        })
                
                elif pattern_type == 'assign':
                    # 查找assign语句
                    for match in re.finditer(r'assign\s+\w+\s*=\s*[^;]+;', code):
                        results.append({
                            'file': str(file_path.relative_to(self.project_root)),
                            'pattern': match.group(0)
                        })
            
            return {'found': len(results) > 0, 'pattern_type': pattern_type, 'matches': results[:10], 'total_count': len(results)}
            
        except Exception as e:
            return {'error': str(e)}
    
    def _tool_read_file_content(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """工具：读取文件内容"""
        file_path = args.get('file_path', '')
        
        try:
            full_path = self.project_root / file_path
            if not full_path.exists():
                return {'error': f'文件不存在: {file_path}'}
            
            code, encoding = read_file_with_encoding(str(full_path))
            return {'success': True, 'file': file_path, 'content': code[:5000], 'encoding': encoding}  # 限制长度
            
        except Exception as e:
            return {'error': str(e)}