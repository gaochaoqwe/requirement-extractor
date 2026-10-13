"""
提示词处理模块
"""

from .deepReviewPrompt import get_deep_review_prompt
from .diffMappingPrompt import (
    get_diff_mapping_prompt,
    get_fallback_mapping_prompt,
    build_change_details_section,
    build_tasks_section
)
