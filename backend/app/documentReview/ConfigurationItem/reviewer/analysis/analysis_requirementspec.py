import json

def parse_violation_rules_model_output(model_output):
    """
    解析需求规格说明模型返回的字符串或dict，返回问题单列表
    """
    if isinstance(model_output, str):
        raw_str_output = model_output.strip()
        # logger.debug(f"传入 parse_violation_rules_model_output 的原始字符串 (前500字符): {raw_str_output[:500]}") # 可选的日志

        # 1. 处理 <think>...</think> 或前导 </think> 标签
        last_think_end_tag_index = raw_str_output.rfind("</think>")
        if last_think_end_tag_index != -1:
            raw_str_output = raw_str_output[last_think_end_tag_index + len("</think>"):]
            raw_str_output = raw_str_output.lstrip()
            # logger.info(f"移除了 <think> 标签后的内容 (前500字符): {raw_str_output[:500]}") # 可选的日志

        # 移除 UTF-8 BOM (Byte Order Mark) 如果存在，因为 json.loads 对此敏感
        if raw_str_output.startswith('\ufeff'):
            raw_str_output = raw_str_output[1:]
            # logger.info("移除了 UTF-8 BOM") # 可选的日志

        # 尝试移除Markdown代码块标记，以防万一
        if raw_str_output.startswith('```json') and raw_str_output.endswith('```'):
            raw_str_output = raw_str_output[7:-3].strip()
        elif raw_str_output.startswith('```') and raw_str_output.endswith('```'):
            raw_str_output = raw_str_output[3:-3].strip()

        try:
            data = json.loads(raw_str_output)
        except Exception:
            raise ValueError('模型返回内容不是合法JSON')
    else:
        data = model_output
    if 'problems' not in data or not isinstance(data['problems'], list):
        raise ValueError('模型返回内容缺少problems数组')
    return data['problems']
