"""
AI服务层模块

专注于AI相关的服务，包括：
- AI API调用 (ai_client.py)
- 提示词管理 (ai_prompt_manager.py) 
- AI内容优化 (ai_content_optimizer.py)
"""

from .ai_client import generate_test_cases, moxingfenxi, call_ai_api

__all__ = [
    'generate_test_cases',
    'moxingfenxi', 
    'call_ai_api'
] 