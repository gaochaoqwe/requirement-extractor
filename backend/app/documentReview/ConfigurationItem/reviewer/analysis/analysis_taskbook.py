import json

import logging
logger = logging.getLogger(__name__)

def parse_taskbook_model_output(model_output):
    """
    解析研制任务书模型返回的字符串或dict，返回问题单列表，适配 violas 字段。
    """
    if isinstance(model_output, str):
        raw_str_output = model_output.strip()
        logger.debug(f"传入 parse_taskbook_model_output 的原始字符串 (前500字符): {raw_str_output[:500]}")

        # 1. 处理 <think>...</think> 或前导 </think> 标签
        last_think_end_tag_index = raw_str_output.rfind("</think>")
        if last_think_end_tag_index != -1:
            raw_str_output = raw_str_output[last_think_end_tag_index + len("</think>"):]
            raw_str_output = raw_str_output.lstrip()
            logger.info(f"移除了 <think> 标签后的内容 (前500字符): {raw_str_output[:500]}")

        cleaned_output = raw_str_output # 更新 cleaned_output 以便后续处理

        # 2. 尝试移除Markdown代码块标记
        if cleaned_output.startswith('```json') and cleaned_output.endswith('```'):
            cleaned_output = cleaned_output[7:-3].strip()
            logger.info("移除了 ```json ... ``` 代码块标记")
        elif cleaned_output.startswith('```') and cleaned_output.endswith('```'):
            cleaned_output = cleaned_output[3:-3].strip()
            logger.info("移除了 ``` ... ``` 代码块标记")

        # 移除 UTF-8 BOM (Byte Order Mark) 如果存在
        if cleaned_output.startswith('\ufeff'):
            cleaned_output = cleaned_output[1:]
            logger.info("移除了 UTF-8 BOM")

        try:
            logger.debug(f"清理后的模型输出 (前500字符): {cleaned_output[:500]}")
            data = json.loads(cleaned_output)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"导致解析失败的内容 (前500字符): {cleaned_output[:500]}")
            raise ValueError(f'模型返回内容不是合法JSON: {e.message}')
        except Exception as e:
            logger.error(f"处理模型输出时发生未知错误: {e}")
            logger.error(f"导致错误的内容 (前500字符): {cleaned_output[:500]}")
            raise ValueError(f'处理模型输出时发生未知错误: {str(e)}')
    else:
        data = model_output
    if 'problems' not in data or not isinstance(data['problems'], list):
        raise ValueError('模型返回内容缺少problems数组')
    # 字段兼容性处理：如果有 issue_source 转为 violation_rules
    for item in data['problems']:
        if 'issue_source' in item:
            item['violation_rules'] = item.pop('issue_source')
    return data['problems']
