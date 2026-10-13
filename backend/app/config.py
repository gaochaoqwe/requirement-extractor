import os
import json

def get_config():
    """
    读取 config.json 并返回配置字典
    """
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)
