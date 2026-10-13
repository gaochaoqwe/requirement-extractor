"""
规则数据库工厂

已完全迁移到PostgreSQL，仅使用PostgreSQL版本
"""
from app.staticAnalysis.filter.database.postgresql_rules_database import (
    get_gjb_rules_database as _get_gjb_rules_database,
    get_cwe_rules_database as _get_cwe_rules_database
)


def get_rules_database():
    """获取GJB规则数据库实例（PostgreSQL）"""
    return _get_gjb_rules_database()


def get_cwe_rules_database():
    """获取CWE规则数据库实例（PostgreSQL）"""
    return _get_cwe_rules_database()


# 导出统一接口
__all__ = ['get_rules_database', 'get_cwe_rules_database']

