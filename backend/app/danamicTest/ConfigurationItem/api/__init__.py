
"""
配置项测试API模块

本模块已重构为模块化结构，包含以下子模块：

- upload_api.py: 文件上传相关API
- form_api.py: 表单生成相关API
- dropdown_api.py: 下拉数据管理API
- ocr_api.py: OCR功能API
- main_router.py: 主路由整合
- configuration_item.py: 主入口文件（向后兼容）

使用方式：
from .configuration_item import router
或
from .main_router import router
"""

try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

# 导入主路由以便外部使用
from .configuration_item import router

# 导出主要组件
__all__ = ["router"]

# 记录模块加载信息
log_info("配置项测试API模块已加载（模块化结构）", "api_module")