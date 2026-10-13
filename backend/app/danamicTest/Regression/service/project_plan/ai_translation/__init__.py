"""
回归测试项目策划AI翻译模块

从ai/AI_fanyi.py和ai/lixianfenyi_bao.py重构而来，提供测试标识翻译功能
"""

from .AI_fanyi import translate_chinese_to_english
from .lixianfenyi_bao import (
    start_libretranslate_server, 
    stop_libretranslate_server, 
    translate_texts, 
    format_sentence,
    ceshihezi_open_shixian
)

__all__ = [
    'translate_chinese_to_english',
    'start_libretranslate_server',
    'stop_libretranslate_server', 
    'translate_texts',
    'format_sentence',
    'ceshihezi_open_shixian'
] 