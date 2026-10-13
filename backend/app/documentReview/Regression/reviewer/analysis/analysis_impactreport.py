"""
分析影响域报告的模块
"""
import json
import logging

# 配置日志
logger = logging.getLogger("wordllm")
logger.setLevel(logging.INFO)

def parse_impact_report_model_output(model_output):
    """
    解析模型输出的影响域分析报告审查结果
    
    Args:
        model_output: 模型输出的JSON内容
        
    Returns:
        处理后的审查结果
    """
    try:
        if not model_output or not isinstance(model_output, dict):
            logger.error(f"输入的模型输出不是有效的字典: {model_output}")
            return {"problems": []}
            
        if "problems" not in model_output:
            logger.warning(f"模型输出中没有'problems'字段: {model_output}")
            return {"problems": []}
            
        problems = model_output["problems"]
        if not isinstance(problems, list):
            logger.error(f"'problems'字段不是列表: {problems}")
            return {"problems": []}
            
        # 处理每个问题
        processed_problems = []
        for i, problem in enumerate(problems):
            if not isinstance(problem, dict):
                logger.warning(f"跳过非字典问题项 #{i}: {problem}")
                continue
                
            # 确保每个问题都有必要的字段
            processed_problem = {
                "doc_type": problem.get("doc_type", "regression"),
                "doc_name": problem.get("doc_name", "影响域分析报告"),
                "requirement_content": problem.get("requirement_content", ""),
                "violation_rules": problem.get("violation_rules", ""),
                "issue_name": problem.get("issue_name", ""),
                "issue_location": problem.get("issue_location", ""),
                "description_requirement": problem.get("description_requirement", ""),
                "description_issue": problem.get("description_issue", ""),
                "description_location": problem.get("description_location", ""),
                "description_impact": problem.get("description_impact", "")
            }
            processed_problems.append(processed_problem)
            
        logger.info(f"成功解析 {len(processed_problems)} 个问题")
        return {"problems": processed_problems}
        
    except Exception as e:
        logger.error(f"解析模型输出时出错: {e}")
        return {"problems": []}
