"""
统一数据库部署配置

集中定义本项目所有 PostgreSQL 库的：库名、用户、密码、连接信息与迁移目录。
任何模块新增数据库，只需在这里加一条 DbTarget，其余流程自动纳入统一部署。

配置来源优先级：
1. 环境变量（沿用各模块既有的变量名，见 DbTarget.env_prefix，向后兼容）
2. backend/.env
3. 本文件内置默认值（与各模块 init_postgresql.py 的默认值保持一致）

注意：本文件只做声明，不建立任何连接。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# 定位路径
# ---------------------------------------------------------------------------
DEPLOY_DIR = Path(__file__).resolve().parent          # backend/deploy
BACKEND_DIR = DEPLOY_DIR.parent                        # backend
PROJECT_DIR = BACKEND_DIR.parent                       # 项目根
MIGRATIONS_DIR = DEPLOY_DIR / "migrations"
SNAPSHOTS_DIR = DEPLOY_DIR / "snapshots"

# ---------------------------------------------------------------------------
# 加载 .env（backend/.env，不覆盖已有环境变量）
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv

    _env_file = BACKEND_DIR / ".env"
    if _env_file.exists():
        load_dotenv(_env_file, override=False)
except ImportError:  # dotenv 缺失时静默降级
    pass


def _env(*names: str, default: str) -> str:
    """按顺序取第一个已设置的非空环境变量，否则返回默认值。"""
    for name in names:
        val = os.getenv(name)
        if val:
            return val
    return default


# ---------------------------------------------------------------------------
# PostgreSQL 管理员账号（仅用于 create role / database / grant）
# ---------------------------------------------------------------------------
ADMIN_HOST = _env("POSTGRES_HOST", "POSTGRES_ADMIN_HOST", default="localhost")
ADMIN_PORT = int(_env("POSTGRES_PORT", "POSTGRES_ADMIN_PORT", default="5432"))
ADMIN_USER = _env("POSTGRES_ADMIN_USER", default="postgres")
ADMIN_PASSWORD = _env("POSTGRES_ADMIN_PASSWORD", default="123456")


@dataclass(frozen=True)
class DbTarget:
    """一个受统一部署管理的 PostgreSQL 数据库。"""

    key: str                 # 逻辑标识，等于迁移子目录名
    db_name: str             # 数据库名
    user: str                # 数据库用户
    password: str            # 数据库用户密码
    host: str
    port: int
    description: str
    legacy_init: str = ""    # 相对 backend/ 的原有初始化脚本（用于 --bootstrap）
    extra_notes: str = ""

    @property
    def migrations_dir(self) -> Path:
        return MIGRATIONS_DIR / self.key

    @property
    def legacy_init_path(self) -> Path | None:
        return (BACKEND_DIR / self.legacy_init) if self.legacy_init else None


def _build_target(
    key: str,
    default_db: str,
    default_user: str,
    description: str,
    env_prefix: str | None = None,
    legacy_init: str = "",
    extra_notes: str = "",
    default_host: str | None = None,
    default_port: int | None = None,
) -> DbTarget:
    """按 env_prefix 组装一个目标；env_prefix=None 表示沿用全局 POSTGRES_*。"""
    if env_prefix == "POSTGRES_":
        # code_review：直接复用全局 POSTGRES_*
        host = _env("POSTGRES_HOST", default=default_host or ADMIN_HOST)
        port = int(_env("POSTGRES_PORT", default=str(default_port or ADMIN_PORT)))
        db = _env("POSTGRES_DB", default=default_db)
        user = _env("POSTGRES_USER", default=default_user)
        pwd = _env("POSTGRES_PASSWORD", default="123456")
    elif env_prefix == "POSTGRES_DB_REGRESSION":
        host = _env("POSTGRES_HOST", default=default_host or ADMIN_HOST)
        port = int(_env("POSTGRES_PORT", default=str(default_port or ADMIN_PORT)))
        db = _env("POSTGRES_DB_REGRESSION", default=default_db)
        user = _env("POSTGRES_USER", default=default_user)
        pwd = _env("POSTGRES_PASSWORD", default="123456")
    else:
        p = env_prefix or ""
        host = _env(f"{p}HOST", default=default_host or ADMIN_HOST)
        port = int(_env(f"{p}PORT", default=str(default_port or ADMIN_PORT)))
        db = _env(f"{p}DB", default=default_db)
        user = _env(f"{p}USER", default=default_user)
        pwd = _env(f"{p}PASSWORD", default="123456")

    return DbTarget(
        key=key,
        db_name=db,
        user=user,
        password=pwd,
        host=host,
        port=port,
        description=description,
        legacy_init=legacy_init,
        extra_notes=extra_notes,
    )


# ---------------------------------------------------------------------------
# 全部受管目标（顺序即部署顺序）
# ---------------------------------------------------------------------------
TARGETS: list[DbTarget] = [
    _build_target(
        key="auth",
        default_db="auth",
        default_user="auth",
        description="用户认证数据库",
        env_prefix="AUTH_POSTGRES_",
        legacy_init="app/auth/db/init_postgresql.py",
        extra_notes="含 users 表与默认账号；表结构为手写 SQL（非 ORM）。",
    ),
    _build_target(
        key="code_review",
        default_db="code_review",
        default_user="code_review",
        description="配置项代码审查（函数/链路/功能审查共用）",
        env_prefix="POSTGRES_",
        legacy_init="app/codeReview/ConfigurationItem/db/init_postgresql.py",
        extra_notes="基础表由 SQLAlchemy create_all 建立，迁移只负责补列/补表/补索引。",
    ),
    _build_target(
        key="code_review_regression",
        default_db="code_review_regression",
        default_user="code_review",
        description="回归测试代码审查（与配置项审查结构同构、库独立）",
        env_prefix="POSTGRES_DB_REGRESSION",
        legacy_init="app/codeReview/RegressionTest/db/init_postgresql.py",
        extra_notes="用户与 code_review 相同，但库独立。",
    ),
    _build_target(
        key="static_analysis_filter",
        default_db="static_analysis_filter",
        default_user="static_analysis",
        description="静态分析（C 语言）：工具模式 + 普通模式 nm_* 共用本库",
        env_prefix="STATIC_POSTGRES_",
        legacy_init="app/staticAnalysis/filter/database/init_postgresql.py",
        extra_notes="另有 normalModeC 的 nm_* 表由 app/staticAnalysis/normalModeC/database/init_postgresql.py 建立。",
    ),
    _build_target(
        key="fpga_static_analysis_filter",
        default_db="fpga_static_analysis_filter",
        default_user="fpga_analysis",
        description="静态分析（FPGA）：工具模式 + 普通模式 nm_fpga_* 共用本库",
        env_prefix="FPGA_POSTGRES_",
        legacy_init="app/staticAnalysis/filterFpga/database/init_postgresql.py",
        extra_notes="结构与 C 库同名但库独立，DDL 需分别执行。",
    ),
    _build_target(
        key="opto_knowledge",
        default_db="opto_knowledge",
        default_user="opto_knowledge",
        description="光电知识库",
        env_prefix="OPTO_POSTGRES_",
        legacy_init="app/databaseManage/optoKnowledge/db/init_postgresql.py",
        extra_notes="纯 ORM 表，无手写迁移；额外提供 seed 默认节点。",
    ),
    _build_target(
        key="maintenance",
        default_db="maintenance",
        default_user="maintenance",
        description="维护模块（公告免打扰 / 问题反馈）",
        env_prefix="MAINTENANCE_POSTGRES_",
        legacy_init="app/maintenance/db/init_postgresql.py",
        extra_notes="表结构为手写 SQL（非 ORM）。",
    ),
]


def get_target(key: str) -> DbTarget:
    for t in TARGETS:
        if t.key == key:
            return t
    raise KeyError(f"未知的数据库标识: {key}（可选: {', '.join(t.key for t in TARGETS)}）")
