
try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源管理器模块

用于管理配置项测试生成过程中需要的所有资源文件路径
替换原始程序中的硬编码路径
"""

import os
from pathlib import Path

class ResourceManager:
    """资源文件管理器"""
    
    def __init__(self):
        # 获取当前模块的目录
        current_dir = Path(__file__).parent
        # 资源文件根目录 - 修复路径指向ConfigurationItem的resources目录
        self.resources_root = current_dir  # 当前文件就在resources目录中
        
        # 确保资源目录存在
        self.resources_root.mkdir(exist_ok=True)
        (self.resources_root / "database").mkdir(exist_ok=True)
        (self.resources_root / "templates").mkdir(exist_ok=True)
        (self.resources_root / "config").mkdir(exist_ok=True)
    
    @property
    def database_dir(self) -> Path:
        """数据库文件目录"""
        return self.resources_root / "database"
    
    @property
    def templates_dir(self) -> Path:
        """模板文件目录"""
        return self.resources_root / "templates"
    
    @property
    def config_dir(self) -> Path:
        """配置文件目录"""
        return self.resources_root / "config"
    
    # ==================== 数据库文件路径 ====================
    
    @property
    def test_item_common_desc_db(self) -> str:
        """测试项通用描述数据库 - 现在使用SQLite数据库"""
        try:
            # 尝试获取SQLite数据库路径
            from ....databaseManage.db.database import get_database_path
            return get_database_path()
        except ImportError:
            # 如果无法导入，回退到Excel文件
            log_warning("无法导入SQLite数据库，使用Excel文件", Path(__file__).stem)
            return str(self.database_dir / "测试项通用描述数据库.xlsx")
    
    @property
    def test_item_standard_desc_db(self) -> str:
        """测试项标准描述数据库 - 现在使用SQLite数据库"""
        try:
            # 尝试获取SQLite数据库路径
            from ....databaseManage.db.database import get_database_path
            return get_database_path()
        except ImportError:
            # 如果无法导入，回退到Excel文件
            log_warning("无法导入SQLite数据库，使用Excel文件", Path(__file__).stem)
            return str(self.database_dir / "测试项标准描述数据库.xlsx")
    
    @property
    def test_case_common_db(self) -> str:
        """测试用例通用数据库"""
        return str(self.database_dir / "测试用例通用数据库.xlsx")
    
    @property
    def test_case_standard_db(self) -> str:
        """测试用例标准数据库"""
        return str(self.database_dir / "测试用例标准数据库.xlsx")
    
    @property
    def software_model_info_db(self) -> str:
        """软件型号信息数据库"""
        return str(self.database_dir / "软件型号信息数据库.xlsx")
    
    @property
    def problem_report_db(self) -> str:
        """问题单数据库"""
        return str(self.database_dir / "问题单数据库.xlsx")
    
    @property
    def ai_code_defect_rules_db(self) -> str:
        """AI代码缺陷审核规则库"""
        return str(self.database_dir / "AI_代码缺陷审核规则库.xlsx")
    
    @property
    def software_defect_db(self) -> str:
        """软件典型缺陷库"""
        return str(self.database_dir / "软件典型缺陷库.xlsx")
    
    # ==================== 模板文件路径 ====================
    
    @property
    def planning_template(self) -> str:
        """策划初稿模板"""
        return str(self.templates_dir / "策划初稿.xlsx")
    
    @property
    def problem_report_template(self) -> str:
        """问题单设计模板"""
        return str(self.templates_dir / "问题单设计.xlsx")
    
    # ==================== 配置文件路径 ====================
    
    @property
    def test_personnel_list(self) -> str:
        """测试人员名单"""
        return str(self.config_dir / "测试人员名单.txt")
    
    @property
    def test_manager_list(self) -> str:
        """测试主管名单"""
        return str(self.config_dir / "测试主管名单.txt")
    
    @property
    def developer_list(self) -> str:
        """开发人员名单"""
        return str(self.config_dir / "开发人员名单.txt")
    
    @property
    def domain_classification(self) -> str:
        """领域分类库"""
        return str(self.config_dir / "领域分类库.txt")
    
    # ==================== 工具方法 ====================
    
    def get_templates_dir(self) -> str:
        """获取模板文件目录路径"""
        return str(self.templates_dir)
    
    def get_template_path(self, template_name: str) -> str:
        """获取指定模板文件的完整路径"""
        return str(self.templates_dir / template_name)
    
    def get_database_path(self, database_name: str) -> str:
        """获取指定数据库文件的完整路径"""
        return str(self.database_dir / database_name)
    
    def check_resource_exists(self, resource_path: str) -> bool:
        """检查资源文件是否存在"""
        return os.path.exists(resource_path)
    
    def get_missing_resources(self) -> list:
        """获取缺失的资源文件列表"""
        missing = []
        
        # 检查数据库文件
        database_files = [
            self.test_item_common_desc_db,
            self.test_item_standard_desc_db,
            self.test_case_common_db,
            self.test_case_standard_db,
            self.software_model_info_db,
            self.problem_report_db,
            self.ai_code_defect_rules_db,
            self.software_defect_db,
        ]
        
        # 检查模板文件
        template_files = [
            self.planning_template,
            self.problem_report_template,
        ]
        
        # 检查配置文件
        config_files = [
            self.test_personnel_list,
            self.test_manager_list,
            self.developer_list,
            self.domain_classification,
        ]
        
        all_files = database_files + template_files + config_files
        
        for file_path in all_files:
            if not self.check_resource_exists(file_path):
                missing.append(file_path)
        
        return missing
    
    def validate_resources(self) -> tuple:
        """验证所有资源文件是否存在"""
        missing = self.get_missing_resources()
        if missing:
            return False, missing
        return True, []
    
    def get_resource_summary(self) -> dict:
        """获取资源文件摘要信息"""
        return {
            "database_files": {
                "测试项通用描述数据库": self.test_item_common_desc_db,
                "测试项标准描述数据库": self.test_item_standard_desc_db,
                "测试用例通用数据库": self.test_case_common_db,
                "测试用例标准数据库": self.test_case_standard_db,
                "软件型号信息数据库": self.software_model_info_db,
                "问题单数据库": self.problem_report_db,
                "AI代码缺陷审核规则库": self.ai_code_defect_rules_db,
                "软件典型缺陷库": self.software_defect_db,
            },
            "template_files": {
                "策划初稿模板": self.planning_template,
                "问题单设计模板": self.problem_report_template,
            },
            "config_files": {
                "测试人员名单": self.test_personnel_list,
                "测试主管名单": self.test_manager_list,
                "开发人员名单": self.developer_list,
                "领域分类库": self.domain_classification,
            }
        }


# 创建全局资源管理器实例
resource_manager = ResourceManager()


def get_resource_manager() -> ResourceManager:
    """获取资源管理器实例"""
    return resource_manager


if __name__ == "__main__":
    # 测试资源管理器
    rm = get_resource_manager()
    
    log_info("=== 资源文件验证 ===", Path(__file__).stem)
    is_valid, missing = rm.validate_resources()
    
    if is_valid:
        log_info("✅ 所有资源文件都存在", Path(__file__).stem)
    else:
        log_info("❌ 缺失的资源文件:", Path(__file__).stem)
        for file in missing:
            log_info(f"  - {file}", Path(__file__).stem)
    
    log_info("\n=== 资源文件摘要 ===", Path(__file__).stem)
    summary = rm.get_resource_summary()
    
    for category, files in summary.items():
        log_info(f"\n{category}:", Path(__file__).stem)
        for name, path in files.items():
            status = "✅" if rm.check_resource_exists(path) else "❌"
            log_info(f"  {status} {name}: {path}", Path(__file__).stem) 