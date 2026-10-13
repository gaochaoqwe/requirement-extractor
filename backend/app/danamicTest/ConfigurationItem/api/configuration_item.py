
"""
配置项测试API端点 - 主入口文件

为了保持向后兼容性，此文件现在导入并重新导出主路由。
实际的API实现已经拆分到多个专门的文件中：

- upload_api.py: 文件上传相关API
- form_api.py: 表单生成相关API
- dropdown_api.py: 下拉数据管理API
- ocr_api.py: OCR功能API
- main_router.py: 主路由整合

这种拆分提供了更好的代码组织和维护性。
"""

try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

# 导入主路由
from .main_router import router

# 为了向后兼容，保留原有的导出
__all__ = ["router"]

# 记录模块重构信息
log_info("配置项测试API已重构为模块化结构", "configuration_item")
