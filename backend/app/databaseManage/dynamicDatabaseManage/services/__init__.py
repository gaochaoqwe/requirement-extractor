"""
业务逻辑服务层
"""
try:
    from .requirement_service import RequirementService
    from .intelligent_import_service import IntelligentImportService
    from .intelligent_export_service import IntelligentExportService
    
    __all__ = ["RequirementService", "IntelligentImportService", "IntelligentExportService"]
except ImportError as e:
    # 如果导入失败，设置默认值避免启动错误
    print(f"警告: 服务模块导入失败: {e}")
    
    # 创建占位符类
    class PlaceholderService:
        def __getattr__(self, name):
            def placeholder(*args, **kwargs):
                raise RuntimeError(f"服务模块未正确加载，方法 {name} 不可用")
            return placeholder
    
    RequirementService = PlaceholderService()
    IntelligentImportService = PlaceholderService()
    IntelligentExportService = PlaceholderService()
    
    __all__ = ["RequirementService", "IntelligentImportService", "IntelligentExportService"]