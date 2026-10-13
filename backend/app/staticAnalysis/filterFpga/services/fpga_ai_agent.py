"""
FPGA代码分析AI Agent - 扩展CodeAnalysisAgentV2支持FPGA规则
"""
from typing import Dict, Any
import logging
import json


class FpgaAIAgent:
    """FPGA代码分析AI Agent的扩展方法"""
    
    @staticmethod
    def create_fpga_analysis_prompt(context: Dict[str, Any]) -> str:
        """
        为FPGA规则创建AI分析提示词
        
        Args:
            context: {
                "rule_code": "A-1-5",
                "rule_content": "规则描述",
                "file_name": "top.v",
                "line_number": "123",
                "source_code": "具体代码行",
                "code_context": "上下文代码",
                "description": "问题描述"
            }
        """
        rule_code = context.get("rule_code", "未知规则")
        rule_content = context.get("rule_content", "无规则描述")
        file_name = context.get("file_name", "未知文件")
        line_number = context.get("line_number", "未知行")
        source_code = context.get("source_code", "")
        code_context = context.get("code_context", "")
        description = context.get("description", "")
        
        # 判断语言类型
        language = "Verilog" if file_name.endswith(".v") else "VHDL"
        
        prompt = f"""你是一个专业的FPGA硬件描述语言（{language}）代码审查专家。你的任务是分析以下静态分析工具报告的问题是否为**真实存在的编码规范问题**。

**问题信息：**
- 规则编号：{rule_code}
- 规则内容：{rule_content}
- 问题位置：{file_name}:{line_number}
- 问题描述：{description}

**问题代码行：**
```{language.lower()}
{source_code}
```

**代码上下文：**
```{language.lower()}
{code_context}
```

**审查原则：**

✅ **应该保留的真实问题：**
- 明确违反了FPGA编码规范
- 可能导致综合错误或时序问题
- 不符合设计最佳实践
- 代码可读性差，违反命名规范
- 存在潜在的硬件实现风险

❌ **应该过滤的误报：**
- 代码符合规范，工具误判
- 虽然不是最佳实践，但在特定场景下合理
- 已有注释说明特殊用法
- 属于设计意图，不是错误

**请分析并返回JSON格式：**
```json
{{
    "should_retain": true/false,  // true表示保留问题，false表示过滤掉
    "confidence": 0.0-1.0,  // 置信度
    "reason": "详细说明为什么应该保留或过滤此问题",
    "evidence": ["支持你判断的代码证据"],
    "recommendation": "如果是真实问题，给出修改建议"
}}
```

请严格按照上述JSON格式返回，不要包含其他内容。
"""
        return prompt
    
    @staticmethod
    async def analyze_fpga_issue_with_agent(
        ai_client,
        context: Dict[str, Any],
        logger: logging.Logger
    ) -> Dict[str, Any]:
        """
        使用AI分析FPGA问题
        
        Args:
            ai_client: AI客户端
            context: 问题上下文
            logger: 日志器
        
        Returns:
            分析结果
        """
        try:
            prompt = FpgaAIAgent.create_fpga_analysis_prompt(context)
            
            logger.info(f"开始AI分析FPGA问题: {context.get('rule_code')} - {context.get('file_name')}:{context.get('line_number')}")
            
            # 调用AI（兼容两种客户端实现）
            if hasattr(ai_client, 'chat_completion'):
                logger.info("使用 chat_completion 接口调用AI")
                response = await ai_client.chat_completion(
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    temperature=0.3,
                    max_tokens=1000
                )
                content = response.get("content", "")
            else:
                logger.info("chat_completion 不可用，回退使用 _call_ai_async")
                result, raw = await ai_client._call_ai_async(prompt)
                # 将 result/原始文本转换为 content 供统一解析
                import json
                try:
                    content = json.dumps(result, ensure_ascii=False)
                except Exception:
                    content = str(raw)
            
            # 解析AI返回
            import re
            
            # 尝试提取JSON
            json_match = re.search(r'\{[^{}]*"should_retain"[^{}]*\}', content, re.DOTALL)
            if json_match:
                import json
                result = json.loads(json_match.group(0))
                logger.info(f"AI分析结果: should_retain={result.get('should_retain')}, confidence={result.get('confidence')}")
                return result
            else:
                logger.warning(f"AI返回格式不正确，默认保留问题。返回内容: {content[:200]}")
                return {
                    "should_retain": True,
                    "confidence": 0.5,
                    "reason": "AI返回格式错误，默认保留",
                    "evidence": [],
                    "recommendation": "需要人工审查"
                }
        
        except Exception as e:
            logger.error(f"AI分析FPGA问题失败: {str(e)}")
            return {
                "should_retain": True,
                "confidence": 0.5,
                "reason": f"分析失败: {str(e)}",
                "evidence": [],
                "recommendation": "需要人工审查"
            }
    
    @staticmethod
    async def analyze_fpga_issue_with_agent_v2(
        agent,  # CodeAnalysisAgentV2实例
        context: Dict[str, Any],
        logger: logging.Logger
    ) -> Dict[str, Any]:
        """
        使用Agent工具调用机制分析FPGA问题（V2版本 - 支持Function Calling）
        
        Args:
            agent: CodeAnalysisAgentV2实例
            context: 问题上下文
            logger: 日志器
        
        Returns:
            分析结果
        """
        try:
            rule_code = context.get("rule_code", "未知规则")
            rule_content = context.get("rule_content", "无规则描述")
            file_name = context.get("file_name", "未知文件")
            line_number = context.get("line_number", "未知行")
            source_code = context.get("source_code", "")
            code_context = context.get("code_context", "")
            description = context.get("description", "")
            
            # 判断语言类型
            language = "Verilog" if file_name.endswith(".v") else "VHDL"
            
            # 创建系统提示词（说明任务和输出格式）
            system_prompt = f"""你是一个专业的FPGA硬件描述语言（{language}）代码审查专家。你的任务是分析静态分析工具报告的问题是否为**真实存在的编码规范问题**。

**审查原则：**

✅ **应该保留的真实问题：**
- 明确违反了FPGA编码规范
- 可能导致综合错误或时序问题
- 不符合设计最佳实践
- 代码可读性差，违反命名规范
- 存在潜在的硬件实现风险

❌ **应该过滤的误报：**
- 代码符合规范，工具误判
- 虽然不是最佳实践，但在特定场景下合理
- 已有注释说明特殊用法
- 属于设计意图，不是错误

**你可以使用以下工具来辅助分析：**
- get_function_context: 获取问题行所在模块/函数的完整代码
- read_file_range: 读取文件指定行范围的代码
- search_code: 搜索相关的信号定义、模块实例化等
- get_file_outline: 查看文件整体结构
- list_directory: 浏览代码库目录结构

**输出要求：**
请返回JSON格式：
{{
    "should_retain": true/false,  // true表示保留问题，false表示过滤掉
    "confidence": 0.0-1.0,  // 置信度
    "reason": "详细说明为什么应该保留或过滤此问题",
    "evidence": ["支持你判断的代码证据"],
    "recommendation": "如果是真实问题，给出修改建议"
}}"""
            
            # 创建用户问题描述
            user_prompt = f"""**问题信息：**
- 规则编号：{rule_code}
- 规则内容：{rule_content}
- 问题位置：{file_name}:{line_number}
- 问题描述：{description}

**问题代码行：**
```{language.lower()}
{source_code}
```

**代码上下文：**
```{language.lower()}
{code_context}
```

请分析这个问题是否为真实的编码规范问题。你可以使用工具来获取更多代码上下文信息。"""
            
            logger.info(f"开始Agent分析FPGA问题: {rule_code} - {file_name}:{line_number}")
            logger.info(f"Agent可用工具数量: {len(agent.tools)}")
            
            # [FIX] 准备问题数据和规则信息，调用analyze_uncertain_issue方法（与C/C++版本一致）
            issue_data = {
                "issue_name": f"{rule_code} - {file_name}:{line_number}",
                "issue_file": file_name,
                "issue_line": str(line_number),
                "issue_description": description
            }
            
            rule_info = {
                "rule_code": rule_code,
                "rule_content": rule_content,
                "description": description
            }
            
            # 调用Agent分析（支持工具调用）
            analysis_result = agent.analyze_uncertain_issue(issue_data, rule_info)
            
            logger.info(f"Agent分析完成，工具调用次数: {agent.tool_call_count}")
            logger.info(f"AI分析结果: is_real_issue={analysis_result.get('is_real_issue')}, confidence={analysis_result.get('confidence')}")
            
            # 转换为FPGA格式的返回值
            return {
                "should_retain": analysis_result.get("is_real_issue", True),
                "confidence": analysis_result.get("confidence", 0.5),
                "reason": analysis_result.get("reason", "AI分析完成"),
                "evidence": analysis_result.get("evidence", []),
                "recommendation": analysis_result.get("recommendation", "")
            }
        
        except Exception as e:
            logger.error(f"Agent分析FPGA问题失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "should_retain": True,
                "confidence": 0.5,
                "reason": f"分析失败: {str(e)}",
                "evidence": [],
                "recommendation": "需要人工审查"
            }
