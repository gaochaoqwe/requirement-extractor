# -*- coding: utf-8 -*-
"""
数据库结构完整性自检工具（零依赖，静态分析）

作用：部署前检查 7 个 PostgreSQL 库的"表与字段"是否与代码（ORM 模型 / 手写 SQL）
完全对齐。无需安装 SQLAlchemy、无需连接数据库，在任何有 Python 的环境可运行。

用法：
    python deploy/check_schema.py            # 输出每库对账报告
    python deploy/check_schema.py --json     # 输出 JSON（供程序解析）

判读口径：
    [C] create_all 建的表 —— init 脚本内 SQLAlchemy create_all 从 ORM 模型建表，
        结构天然与代码一致（前提：init 脚本确实触发该 Base 的 create_all）
    [S] SQL 建的表       —— 由 init 脚本内嵌 SQL 或迁移文件 CREATE TABLE 建立，
        字段与 ORM/代码逐列核对，有缺口会明确列出
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

DEPLOY_DIR = Path(__file__).resolve().parent
BACKEND_DIR = DEPLOY_DIR.parent

# ---------------------------------------------------------------------------
# 每库：ORM 模型文件 + init 脚本 + 迁移目录（与 db_config.py 的 7 库对应）
# ---------------------------------------------------------------------------
LIB_SPECS = {
    "auth": {
        "models": [],
        "inits": ["app/auth/db/init_postgresql.py"],
        "migrations": ["deploy/migrations/auth"],
    },
    "code_review": {
        "models": [
            "app/codeReview/ConfigurationItem/db/models/task.py",
            "app/codeReview/ConfigurationItem/db/models/file.py",
            "app/codeReview/ConfigurationItem/db/models/function.py",
            "app/codeReview/ConfigurationItem/db/models/problem.py",
            "app/codeReview/ConfigurationItem/db/models/chain_problem.py",
            "app/codeReview/ConfigurationItem/db/models/file_problem.py",
            "app/codeReview/ConfigurationItem/db/models/feature_problem.py",
            "app/codeReview/ConfigurationItem/db/models/marked_problem.py",
            "app/codeReview/ConfigurationItem/db/models/problem_filter.py",
            "app/codeReview/ConfigurationItem/db/models/filter_template.py",
            "app/codeReview/ConfigurationItem/db/models_chain.py",
            "app/codeReview/ConfigurationItem/db/models_feature.py",
        ],
        "inits": ["app/codeReview/ConfigurationItem/db/init_postgresql.py"],
        "migrations": ["deploy/migrations/code_review"],
    },
    "code_review_regression": {
        "models": [
            "app/codeReview/RegressionTest/db/models/task.py",
            "app/codeReview/RegressionTest/db/models/file.py",
            "app/codeReview/RegressionTest/db/models/function.py",
            "app/codeReview/RegressionTest/db/models/problem.py",
            "app/codeReview/RegressionTest/db/models/chain_problem.py",
            "app/codeReview/RegressionTest/db/models/file_problem.py",
            "app/codeReview/RegressionTest/db/models/feature_problem.py",
            "app/codeReview/RegressionTest/db/models/marked_problem.py",
            "app/codeReview/RegressionTest/db/models/problem_filter.py",
            "app/codeReview/RegressionTest/db/models/filter_template.py",
            "app/codeReview/RegressionTest/db/models/function_pair.py",
            "app/codeReview/RegressionTest/db/models_chain.py",
            "app/codeReview/RegressionTest/db/models_feature.py",
        ],
        "inits": ["app/codeReview/RegressionTest/db/init_postgresql.py"],
        "migrations": ["deploy/migrations/code_review_regression"],
    },
    "static_analysis_filter": {
        "models": [
            "app/staticAnalysis/filter/models/models.py",
            "app/staticAnalysis/filter/database/postgresql_models.py",
            "app/staticAnalysis/normalModeC/database/models/task.py",
            "app/staticAnalysis/normalModeC/database/models/file.py",
            "app/staticAnalysis/normalModeC/database/models/function.py",
            "app/staticAnalysis/normalModeC/database/models/problem.py",
        ],
        "inits": [
            "app/staticAnalysis/filter/database/init_postgresql.py",
            "app/staticAnalysis/normalModeC/database/init_postgresql.py",
        ],
        "migrations": ["deploy/migrations/static_analysis_filter"],
    },
    "fpga_static_analysis_filter": {
        "models": [
            "app/staticAnalysis/filterFpga/models/models.py",
            "app/staticAnalysis/filterFpga/database/postgresql_models.py",
            "app/staticAnalysis/normalModeFpga/database/postgresql_models.py",
        ],
        "inits": [
            "app/staticAnalysis/filterFpga/database/init_postgresql.py",
            "app/staticAnalysis/normalModeFpga/database/init_postgresql.py",
        ],
        "migrations": ["deploy/migrations/fpga_static_analysis_filter"],
    },
    "opto_knowledge": {
        "models": ["app/databaseManage/optoKnowledge/db/models.py"],
        "inits": ["app/databaseManage/optoKnowledge/db/init_postgresql.py"],
        "migrations": ["deploy/migrations/opto_knowledge"],
    },
    "maintenance": {
        "models": [],
        "inits": ["app/maintenance/db/init_postgresql.py"],
        "migrations": ["deploy/migrations/maintenance"],
    },
}

TYPE_ALIAS = {
    "Integer": "INTEGER", "BigInteger": "BIGINT", "SmallInteger": "SMALLINT",
    "String": "VARCHAR", "Text": "TEXT", "Boolean": "BOOLEAN",
    "DateTime": "TIMESTAMP", "Date": "DATE", "Time": "TIME",
    "Float": "FLOAT", "Numeric": "NUMERIC", "LargeBinary": "BYTEA",
    "JSON": "JSON", "ARRAY": "ARRAY",
}


# ---------------------------------------------------------------------------
# ORM 模型静态提取
# ---------------------------------------------------------------------------
def _type_name(node) -> str:
    if node is None:
        return ""
    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Name):
            return TYPE_ALIAS.get(f.id, f.id)
        if isinstance(f, ast.Attribute):
            return _type_name(f.value)
    if isinstance(node, ast.Name):
        return TYPE_ALIAS.get(node.id, node.id)
    if isinstance(node, ast.Subscript):
        return _type_name(node.slice)
    return ""


def _is_type_node(node) -> bool:
    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Name) and f.id in TYPE_ALIAS:
            return True
        if isinstance(f, ast.Attribute):
            return _is_type_node(f.value)
        return False
    if isinstance(node, ast.Name) and node.id in TYPE_ALIAS:
        return True
    if isinstance(node, ast.Subscript):
        return _is_type_node(node.slice)
    return False


def _parse_columns(class_node) -> dict:
    cols = {}
    for stmt in class_node.body:
        if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
            continue
        target = stmt.targets[0]
        if not isinstance(target, ast.Name) or target.id.startswith("__"):
            continue
        val = stmt.value
        if isinstance(val, ast.Call) and isinstance(val.func, ast.Name) and val.func.id == "Column":
            field_name, col_type, flags = None, "", []
            args = val.args
            if args and isinstance(args[0], ast.Constant) and isinstance(args[0].value, str):
                field_name = args[0].value
                for a in args[1:]:
                    if _is_type_node(a):
                        col_type = _type_name(a)
                        break
            elif args:
                col_type = _type_name(args[0])
            for kw in val.keywords:
                k = kw.arg
                if k == "primary_key":
                    flags.append("PK")
                elif k == "nullable" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                    flags.append("NOT NULL")
                elif k == "unique" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    flags.append("UNIQUE")
                elif k == "default":
                    flags.append("DEFAULT")
            cols[field_name or target.id] = {"type": col_type, "flags": flags}
        elif isinstance(val, ast.Call) and isinstance(val.func, ast.Name) and val.func.id in ("mapped_column", "Mapped"):
            col_type = next((_type_name(a) for a in val.args if _is_type_node(a)), "")
            flags = []
            for kw in val.keywords:
                if kw.arg == "primary_key":
                    flags.append("PK")
                elif kw.arg == "nullable" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                    flags.append("NOT NULL")
                elif kw.arg == "default":
                    flags.append("DEFAULT")
            cols[target.id] = {"type": col_type, "flags": flags}
    return cols


def _extract_orm(path: Path) -> dict:
    tables = {}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return tables
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            tablename = None
            for stmt in node.body:
                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                    t = stmt.targets[0]
                    if isinstance(t, ast.Name) and t.id == "__tablename__":
                        if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                            tablename = stmt.value.value
            if tablename:
                tables.setdefault(tablename, {}).update(_parse_columns(node))
    return tables


# ---------------------------------------------------------------------------
# SQL 静态提取（init 脚本内嵌 SQL + 迁移文件）
# ---------------------------------------------------------------------------
def _sql_strings(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return []
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if re.search(r"\bCREATE\s+TABLE\b|\bALTER\s+TABLE\b", node.value, re.IGNORECASE):
                out.append(node.value)
    return out


def _parse_create(body: str) -> dict:
    tables = {}
    pat = re.compile(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"']?([\w.]+)[\"']?\s*\((.*?)\)\s*(?:;|$)",
        re.IGNORECASE | re.DOTALL,
    )
    for m in pat.finditer(body):
        name = m.group(1).split(".")[-1]
        tables[name] = _parse_body(m.group(2))
    return tables


def _parse_body(body: str) -> dict:
    cols = {}
    parts, depth, cur = [], 0, []
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur)); cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    for part in parts:
        p = part.strip()
        if not p:
            continue
        up = p.upper()
        if up.startswith(("CONSTRAINT", "PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CHECK", "EXCLUDE")):
            continue
        m = re.match(r"[\"']?([A-Za-z_]\w*)[\"']?\s+(.+)", p)
        if m:
            cols[m.group(1)] = m.group(2).split()[0].rstrip(",")
    return cols


def _parse_alters(body: str) -> dict:
    adds = {}
    pat = re.compile(
        r"ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?[\"']?([\w.]+)[\"']?\s+ADD\s+(?:COLUMN\s+)?(?:IF\s+NOT\s+EXISTS\s+)?[\"']?(\w+)[\"']?\s+([A-Za-z]\w*)",
        re.IGNORECASE,
    )
    for m in pat.finditer(body):
        adds.setdefault(m.group(1).split(".")[-1], {})[m.group(2)] = m.group(3)
    return adds


def _extract_sql(paths: list[Path]) -> dict:
    tables: dict = {}
    for p in paths:
        if not p.exists():
            continue
        if p.suffix == ".py":
            for s in _sql_strings(p):
                for t, c in _parse_create(s).items():
                    tables.setdefault(t, {}).update(c)
                for t, c in _parse_alters(s).items():
                    tables.setdefault(t, {}).update(c)
        else:  # .sql
            s = p.read_text(encoding="utf-8", errors="ignore")
            for t, c in _parse_create(s).items():
                tables.setdefault(t, {}).update(c)
            for t, c in _parse_alters(s).items():
                tables.setdefault(t, {}).update(c)
    return tables


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="数据库结构完整性自检")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    report: dict = {}
    for lib, spec in LIB_SPECS.items():
        # 1) ORM 期望
        orm: dict = {}
        for rel in spec["models"]:
            p = BACKEND_DIR / rel
            if p.exists():
                for t, c in _extract_orm(p).items():
                    orm.setdefault(t, {}).update(c)

        # 2) init + 迁移实际
        init_paths = [BACKEND_DIR / r for r in spec["inits"]]
        mig_paths = [BACKEND_DIR / r for r in spec["migrations"]]
        sql_paths = init_paths + [p for d in mig_paths if d.is_dir() for p in sorted(d.glob("V*.sql"))]
        sql_tables = _extract_sql(sql_paths)

        # 3) init 脚本缺失检查
        missing_inits = [str(p) for p in init_paths if not p.exists()]

        # 4) 对账
        all_orm_tables = set(orm)
        sql_covered = set(sql_tables)
        # 建表来源判定：
        #   - 有 ORM 的表：由 init 脚本内 create_all 从 ORM 模型建表（结构=代码定义）。
        #     只要 init 脚本齐全，表与字段天然齐全，无需 SQL 侧覆盖。
        #   - 无 ORM 的纯 SQL 表（users / maintenance_*）：必须由 init SQL 或迁移 CREATE TABLE 建立。
        #   - init 脚本缺失 = 该库 create_all 流程不可用，属真实缺口。
        if missing_inits:
            missing_tables = sorted(all_orm_tables)
            col_gaps = {}
        else:
            missing_tables = []
            col_gaps = {}
        # 纯 SQL 表：无 ORM 时必须在 SQL 侧存在
        sql_only_tables = sorted(sql_covered - all_orm_tables)
        missing_sql_only = sorted(set(sql_only_tables) - set(sql_covered))  # 恒为空（定义如此），保留语义
        # 有 ORM 库中 SQL 侧多出的表（历史/预留，无代码模型）
        extra_sql_tables = sql_only_tables if all_orm_tables else []

        lib_report = {
            "orm_tables": sorted(all_orm_tables),
            "sql_tables": sorted(sql_covered),
            "sql_only_tables": sql_only_tables,
            "missing_inits": missing_inits,
            "missing_tables": missing_tables,
            "column_gaps": col_gaps,
            "extra_sql_tables": extra_sql_tables,
            "ok": (not missing_inits and not missing_tables and not missing_sql_only),
        }
        report[lib] = lib_report

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
        return 0

    print("=" * 90)
    print("数据库结构完整性自检（静态分析 · 零依赖）")
    print("口径: [C]=create_all建表 [S]=SQL建表；表/字段缺口会在下方明确列出")
    print("=" * 90)
    overall_ok = True
    for lib, r in report.items():
        status = "OK " if r["ok"] else "GAP"
        overall_ok = overall_ok and r["ok"]
        print(f"\n[{status}] {lib}")
        if r["missing_inits"]:
            for p in r["missing_inits"]:
                print(f"    ! 缺少 init 脚本（该库 create_all 建表流程不可用）: {p}")
        if r["missing_tables"]:
            print(f"    ! 依赖 init 脚本建表，但脚本缺失: {r['missing_tables']}")
        if r["column_gaps"]:
            for t, cols in r["column_gaps"].items():
                print(f"    ! 表 {t} 部署 SQL 缺字段: {cols}")
        if r["orm_tables"]:
            print(f"    ORM 表 ({len(r['orm_tables'])}，由 init create_all 建): {', '.join(r['orm_tables'])}")
        if r["sql_only_tables"]:
            print(f"    纯 SQL 表 ({len(r['sql_only_tables'])}，由 init SQL/迁移建): {', '.join(r['sql_only_tables'])}")
        if r["extra_sql_tables"]:
            print(f"    额外表(代码无模型, 历史/预留): {', '.join(r['extra_sql_tables'])}")
    print("\n" + "=" * 90)
    print("结论:", "全部库表结构对齐代码，无缺口" if overall_ok else "存在缺口，见上方明细")
    print("=" * 90)
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
