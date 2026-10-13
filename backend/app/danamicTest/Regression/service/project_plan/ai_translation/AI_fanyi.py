import requests
from pathlib import Path

try:
    from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.Regression.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug


from .lixianfenyi_bao import format_sentence

# 配置相关参数
try:
    from ....config import OLLAMA_HOST, OLLAMA_MODEL
except ImportError:
    # 如果没有配置文件，使用默认值
    OLLAMA_HOST = "http://localhost:11434"
    OLLAMA_MODEL = "llama2"
# 将汉语翻译成英语的函数
def translate_chinese_to_english(chinese_text):
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
            res = requests.post(url=f'{OLLAMA_HOST}/api/generate', json=params,verify=False)
            # 发送 POST 请求到指定的 URL，参数为 `params`
            # 注意：`unl` 应改为 `url`，否则会报错
            response = res.json()["response"]
            data = response
            data=format_sentence(data)           #对数据进行格式转换
            # 将提取的 JSON 字符串解析为 Python 对象
        except Exception as e:
            max_loop = max_loop - 1  # 当发生异常时，减少重试次数
            log_info(str(e), Path(__file__).stem)
            log_info(' Api分析函数错误(没有数据库情况下的需求分析)!!!!!!', Path(__file__).stem)
    return data  # 返回解析后的 JSON 数据
