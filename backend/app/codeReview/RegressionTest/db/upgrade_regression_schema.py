"""
回归测试数据库结构升级脚本

用于将已存在的 regression_test_* 表结构升级到支持双版本与函数配对的版本。
"""

import sys
from pathlib import Path


def main():
    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from backend.app.codeReview.RegressionTest.db.database import migrate_database, check_database

    migrate_database()
    check_database()


if __name__ == "__main__":
    main()
