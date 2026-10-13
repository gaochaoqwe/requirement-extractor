import requests
import subprocess
import time
import re
import socket
from pathlib import Path

try:
    from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.Regression.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug


# 可选导入libretranslate
try:
    import libretranslate
    LIBRETRANSLATE_AVAILABLE = True
except ImportError:
    LIBRETRANSLATE_AVAILABLE = False
    log_info("警告: libretranslate模块不可用，某些翻译功能将被禁用", Path(__file__).stem)
# 启动 LibreTranslate 服务器
#**************************************************************************************************************************
# 启动 LibreTranslate 服务器

def start_libretranslate_server():
    if not LIBRETRANSLATE_AVAILABLE:
        log_info("libretranslate模块不可用，无法启动离线翻译服务器", Path(__file__).stem)
        return -1
    
    try:
        process = subprocess.Popen(['libretranslate', '--host', '0.0.0.0', '--port', '5000'])
        log_info('开始尝试启动离线翻译模型', Path(__file__).stem)
        # 等待一段时间，确保服务器启动
        time.sleep(10)
        return process
    except Exception as e:
        log_info(f"离线翻译模型打开错误(启动失败): {e}", Path(__file__).stem)
        return -1

# 停止 LibreTranslate 服务器
def stop_libretranslate_server(process):
    try:
        process.terminate()
        process.wait()  # 等待进程终止
        log_info("离线翻译模型已经关闭.", Path(__file__).stem)
    except Exception as e:
        log_info(f"离线翻译模型打开错误(关闭失败): {e}", Path(__file__).stem)

# 检查端口是否被占用
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# 翻译文本
def translate_texts(texts, source_lang='zh', target_lang='en'):
    if not LIBRETRANSLATE_AVAILABLE:
        log_info("libretranslate模块不可用，无法进行离线翻译", Path(__file__).stem)
        return texts  # 返回原文本
    
    try:
        # 检查服务器是否运行
        if not is_port_in_use(5000):
            log_info("离线翻译服务器未运行，请先启动服务器", Path(__file__).stem)
            return texts
        
        translated_texts = []
        for text in texts:
            response = requests.post('http://localhost:5000/translate', json={
                'q': text,
                'source': source_lang,
                'target': target_lang
            })
            if response.status_code == 200:
                translated_text = response.json()['translatedText']
                translated_texts.append(translated_text)
            else:
                log_info(f"翻译失败: {text}", Path(__file__).stem)
                translated_texts.append(text)  # 翻译失败时返回原文本
        return translated_texts
    except Exception as e:
        log_info(f"翻译过程中发生错误: {e}", Path(__file__).stem)
        return texts

# 格式化句子，确保符合驼峰命名法
def format_sentence(sentence):
    if not sentence:
        return ""
    
    # 移除特殊字符和数字
    sentence = re.sub(r'[^\w\s]', '', sentence)
    sentence = re.sub(r'\d+', '', sentence)
    
    # 分割单词并转换为驼峰命名法
    words = sentence.split()
    if not words:
        return ""
    
    # 第一个单词首字母大写，其余单词首字母也大写
    formatted_words = [word.capitalize() for word in words if word]
    
    return ''.join(formatted_words)


# 使用谷歌浏览器打开网页
def ceshihezi_open_shixian(webpath,GooglePath):
    # 调用函数打开指定网址
    try:
        # 设置谷歌浏览器的路径（根据你的操作系统修改路径）
        chrome_path = GooglePath  # Windows路径
        subprocess.run([chrome_path, webpath])
    except Exception as e:
        log_info(f"An error occurred: {e}", Path(__file__).stem)
