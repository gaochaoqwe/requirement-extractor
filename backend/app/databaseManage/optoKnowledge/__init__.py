"""
光电知识系统模块（独立）

提供：
- 知识图谱节点/边管理
- TipTap 富文本存储
- 本地附件上传与下载
"""

try:
    from .api.router import router
    from .db.database import init_database as init_db

    __all__ = ["router", "init_db"]
except Exception as e:
    print(f"警告: optoKnowledge 模块导入失败: {e}")
    router = None
    init_db = lambda: None
    __all__ = ["router", "init_db"]
