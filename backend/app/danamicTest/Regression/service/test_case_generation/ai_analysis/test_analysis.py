import requests
import json
import re
# 配置相关参数
try:
    from ....utils.config_utils.config import OLLAMA_HOST, OLLAMA_MODEL
except ImportError:
    try:
        from .....utils.config_utils.config import OLLAMA_HOST, OLLAMA_MODEL
    except ImportError:
        from app.danamicTest.Regression.utils.config_utils.config import OLLAMA_HOST, OLLAMA_MODEL


def translate_chinese_to_english(chinese_text):
    """
    将汉语翻译成英语的函数
    """
    # 构建请求参数
    params = {
        'system': '你是一个翻译专家，将汉语翻译成英语,翻译结果中不能出现汉语。',
        'prompt': chinese_text,
        'model': OLLAMA_MODEL,
        'stream': False
    }
    max_loop = 5  # 设置最大重试次数为 5 次
    data = None  # 初始化返回数据为 None
    while max_loop > 0 and not data:  # 当重试次数大于 0 且未获取到数据时，循环继续
        try:
            res = requests.post(url=f'{OLLAMA_HOST}/api/generate', json=params, verify=False)
            # 发送 POST 请求到指定的 URL，参数为 `params`
            response = res.json()["response"]
            
            # 处理think标签过滤
            if response:
                # 1. Handle <think>...</think> or leading </think>
                last_think_end_tag_index = response.rfind("</think>")
                if last_think_end_tag_index != -1:
                    response = response[last_think_end_tag_index + len("</think>"):]
                    response = response.lstrip()
                
                # 2. 移除任何剩余的<think>标签开始部分
                think_start_index = response.find("<think>")
                if think_start_index != -1:
                    response = response[:think_start_index]
            
            data = response
            # 简单的格式转换（去除多余空格和换行）
            if data:
                data = data.strip().replace('\n', ' ').replace('  ', ' ')
            
            # 将提取的 JSON 字符串解析为 Python 对象
            break  # 成功获取数据后退出循环
        except Exception as e:
            max_loop = max_loop - 1  # 当发生异常时，减少重试次数
            print(e)
            print(' AI翻译函数错误!!!!!!')
    return data  # 返回解析后的数据


# 其他非测试用例生成的AI分析功能（如果有的话）
def analyze_requirement_text(text):
    """分析需求文本的AI功能"""
    # ... 其他AI分析功能 ...
    pass


def analyze_code_impact(code_changes):
    """分析代码影响的AI功能"""
    # ... 其他AI分析功能 ...
    pass 