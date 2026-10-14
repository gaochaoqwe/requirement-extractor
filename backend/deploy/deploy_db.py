"""
统一数据库部署入口（方案 A）

一条命令完成全部 7 个 PostgreSQL 库的「建库 / 建用户 / 授权 / 补列迁移」，
并用 `schema_migrations` 版本表记录每个库已应用到的版本。

用法示例：
    # 查看受管数据库与迁移清单
    python deploy_db.py --list

    # 检查各库当前版本（不改动任何数据）
    python deploy_db.py --verify

    # 一键部署：建库/建用户/授权 + 应用全部迁移（幂等，可重复执行）
    python deploy_db.py --yes

    # 只建库与用户，不跑迁移
    python deploy_db.py --create-only --yes

    # 只跑迁移（库已存在时）
    python deploy_db.py --migrate-only --yes

    # 全新环境：先复用各模块原有初始化脚本建基础表，再补迁移
    python deploy_db.py --bootstrap --yes

    # 演练，不实际改动
    python deploy_db.py --dry-run

说明：
    - 所有迁移均为幂等语句，重复执行安全；首次纳管已有环境不会破坏数据。
    - 基础表（ORM create_all 建立的那些）不在这里重建，由后端启动时或
      --bootstrap 复用各模块原有 init_postgresql.py 建立；本脚本专注
      「建库 + 增量迁移」，消灭手工在 Navicat 里粘贴 SQL 的历史做法。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# 允许直接 `python deploy/deploy_db.py` 运行
sys.path.insert(0, str(Path(__file__).resolve().parent))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from db_config import ADMIN_HOST, ADMIN_PASSWORD, ADMIN_PORT, ADMIN_USER, TARGETS, DbTarget, get_target
from migration_runner import MigrationRunner, discover_migrations

# ---------------------------------------------------------------------------
# 终端着色（Windows 下不保证，故仅用于提示前缀）
# ---------------------------------------------------------------------------
OK = "[OK]"
SKIP = "[--]"
WARN = "[!!]"
ERR = "[XX]"


def log(msg: str = "") -> None:
    print(msg)


def connect_admin():
    conn = psycopg2.connect(
        host=ADMIN_HOST,
        port=ADMIN_PORT,
        dbname="postgres",
        user=ADMIN_USER,
        password=ADMIN_PASSWORD,
        connect_timeout=8,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


# ---------------------------------------------------------------------------
# 建库 / 建用户 / 授权
# ---------------------------------------------------------------------------
def ensure_role(conn, target: DbTarget) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (target.user,))
        if cur.fetchone():
            cur.execute(f'ALTER USER "{target.user}" WITH PASSWORD %s', (target.password,))
            return f"{SKIP} 用户已存在: {target.user}"
        cur.execute(f'CREATE USER "{target.user}" WITH PASSWORD %s', (target.password,))
        return f"{OK} 创建用户: {target.user}"


def ensure_database(conn, target: DbTarget) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target.db_name,))
        if cur.fetchone():
            return f"{SKIP} 数据库已存在: {target.db_name}"
        cur.execute(f'CREATE DATABASE "{target.db_name}" ENCODING \'UTF8\'')
    grant_privileges(conn, target)
    return f"{OK} 创建数据库: {target.db_name}"


def grant_privileges(conn, target: DbTarget) -> None:
    """授予库级 + schema 级 + 默认权限（重复执行无害）。"""
    with conn.cursor() as cur:
        cur.execute(f'GRANT ALL PRIVILEGES ON DATABASE "{target.db_name}" TO "{target.user}"')
    # schema 级授权需要连到目标库
    with psycopg2.connect(
        host=ADMIN_HOST, port=ADMIN_PORT, dbname=target.db_name,
        user=ADMIN_USER, password=ADMIN_PASSWORD, connect_timeout=8,
    ) as db_conn:
        db_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with db_conn.cursor() as cur:
            cur.execute(f'GRANT ALL ON SCHEMA public TO "{target.user}"')
            cur.execute(f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "{target.user}"')
            cur.execute(f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "{target.user}"')
            cur.execute(
                f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{target.user}"'
            )
            cur.execute(
                f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "{target.user}"'
            )


def create_targets(targets: list[DbTarget], dry_run: bool) -> None:
    log("=" * 74)
    log("  步骤 1/2  建库 / 建用户 / 授权")
    log("=" * 74)
    if dry_run:
        for t in targets:
            log(f"  {SKIP} [演练] 将确保: 数据库={t.db_name}  用户={t.user}")
        return

    try:
        admin = connect_admin()
    except Exception as exc:                              # noqa: BLE001
        log(f"  {ERR} 无法连接 PostgreSQL 管理员账号 "
            f"({ADMIN_USER}@{ADMIN_HOST}:{ADMIN_PORT}): {exc}")
        log("       请确认 PostgreSQL 已启动，且 backend/.env 中的管理员配置正确。")
        raise SystemExit(1)

    # 注意：不能使用 `with admin:` —— psycopg2 的连接上下文管理器
    # 在 autocommit 模式下也会开启事务块，导致 CREATE DATABASE
    # 报 "无法在事务块中运行"。这里直接循环，autocommit 下每句独立提交。
    for t in targets:
        try:
            log(f"  {ensure_role(admin, t)}  ({t.description})")
            log(f"  {ensure_database(admin, t)}")
        except Exception as exc:                      # noqa: BLE001
            log(f"  {ERR} [{t.key}] 建库失败: {exc}")
    admin.close()
    log("")


# ---------------------------------------------------------------------------
# 复用各模块原有初始化脚本（可选）
# ---------------------------------------------------------------------------
def bootstrap_legacy(targets: list[DbTarget], dry_run: bool) -> None:
    log("=" * 74)
    log("  步骤 1.5/2  --bootstrap 复用各模块原有初始化脚本建立基础表")
    log("=" * 74)
    for t in targets:
        scripts = t.all_legacy_init_paths
        if not scripts:
            log(f"  {SKIP} [{t.key}] 无原有初始化脚本，跳过")
            continue
        for script in scripts:
            if not script.exists():
                log(f"  {SKIP} [{t.key}] 缺少脚本 {script.relative_to(script.parents[3])}，跳过")
                continue
            if dry_run:
                log(f"  {SKIP} [演练] 将执行: {script.relative_to(script.parents[3])}")
                continue
            log(f"  [..] [{t.key}] 执行 {script.name} ...")
            try:
                proc = subprocess.run(
                    [sys.executable, "-X", "utf8", str(script), "--yes"],
                    cwd=str(script.parent),
                    capture_output=True, text=True, timeout=600,
                )
                if proc.returncode == 0:
                    log(f"  {OK} [{t.key}] {script.name} 基础表初始化完成")
                else:
                    tail = (proc.stdout or proc.stderr or "").strip().splitlines()[-1:]
                    log(f"  {WARN} [{t.key}] {script.name} 返回码 {proc.returncode}，"
                        f"输出尾部: {tail}")
            except Exception as exc:                          # noqa: BLE001
                log(f"  {WARN} [{t.key}] {script.name} 执行失败: {exc}")
    log("")


# ---------------------------------------------------------------------------
# 迁移
# ---------------------------------------------------------------------------
def migrate_targets(targets: list[DbTarget], dry_run: bool, strict: bool) -> int:
    log("=" * 74)
    log("  步骤 2/2  应用版本化迁移（schema_migrations 记录版本）")
    log("=" * 74)

    total_applied = 0
    total_failed = 0
    for t in targets:
        migrations = discover_migrations(t.migrations_dir)
        log("")
        log(f"  ── [{t.key}] {t.db_name}  共 {len(migrations)} 个迁移文件")
        if not migrations:
            log(f"     {SKIP} 无迁移文件（该库为纯 ORM 表，或无增量变更）")
            continue

        runner = MigrationRunner(t, logger=log, strict=strict)
        try:
            result = runner.apply(dry_run=dry_run)
        except Exception as exc:                          # noqa: BLE001
            log(f"     {ERR} 连接或执行失败: {exc}")
            if "does not exist" in str(exc) and "database" in str(exc):
                log("         提示：库/用户尚未创建，请先去掉 --migrate-only 重跑。")
            total_failed += len(migrations)
            continue

        for mig in result.applied:
            log(f"     {'[演练] ' if dry_run else ''}{OK} V{mig.version} {mig.description}")
        for mig in result.skipped:
            log(f"     {SKIP} V{mig.version} {mig.description}（已应用）")
        for mig in result.failed:
            log(f"     {ERR} V{mig.version} {mig.description}（有语句失败）")

        for se in result.statement_errors:
            snippet = " ".join(se.sql.split())[:90]
            log(f"        ! V{se.version} 语句失败: {snippet}...")
            log(f"          原因: {se.error}")

        total_applied += len(result.applied)
        total_failed += len(result.failed)

    log("")
    log("-" * 74)
    verb = "待应用" if dry_run else "已应用"
    log(f"  迁移汇总：{verb} {total_applied} 个，失败 {total_failed} 个")
    log("-" * 74)
    return total_failed


# ---------------------------------------------------------------------------
# 列表 / 校验
# ---------------------------------------------------------------------------
def cmd_list(targets: list[DbTarget]) -> None:
    log("=" * 74)
    log("  受管数据库与迁移清单")
    log("=" * 74)
    for t in targets:
        log("")
        log(f"  [{t.key}]  库={t.db_name}  用户={t.user}@{t.host}:{t.port}")
        log(f"          {t.description}")
        if t.extra_notes:
            log(f"          备注: {t.extra_notes}")
        migrations = discover_migrations(t.migrations_dir)
        if not migrations:
            log(f"          迁移: （无）")
        for mig in migrations:
            log(f"          V{mig.version}  {mig.description}  ({len(mig.statements)} 条语句)")


def cmd_verify(targets: list[DbTarget]) -> int:
    log("=" * 74)
    log("  各库迁移版本校验")
    log("=" * 74)
    problems = 0
    for t in targets:
        log("")
        log(f"  [{t.key}] {t.db_name}")
        runner = MigrationRunner(t)
        rows = runner.verify()
        if rows and rows[0].get("reachable") is False:
            log(f"     {ERR} 无法连接/库不存在: {rows[0]['error']}")
            problems += 1
            continue
        if not rows:
            log(f"     {SKIP} 无迁移文件")
            continue
        for r in rows:
            mark = {"applied": OK, "pending": WARN, "changed": WARN}.get(r["status"], "?")
            extra = ""
            if r["status"] == "pending":
                extra = "  ← 待应用"
                problems += 1
            elif r["status"] == "changed":
                extra = "  ← 文件已改动，与已应用版本不一致"
                problems += 1
            log(f"     {mark} V{r['version']} {r['description']} [{r['status']}]{extra}")
    log("")
    log("-" * 74)
    log(f"  校验结果：{'全部一致' if problems == 0 else f'有 {problems} 处需要处理'}")
    log("-" * 74)
    return problems


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="统一数据库部署入口（建库 + 版本化迁移）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--targets", default="", help="逗号分隔的目标 key，默认全部")
    parser.add_argument("--yes", "-y", action="store_true", help="跳过交互确认")
    parser.add_argument("--create-only", action="store_true", help="只建库/用户/授权，不跑迁移")
    parser.add_argument("--migrate-only", action="store_true", help="只跑迁移，不建库")
    parser.add_argument("--bootstrap", action="store_true", help="先复用各模块原有初始化脚本建基础表")
    parser.add_argument("--strict", action="store_true", help="任一语句失败即中止该库")
    parser.add_argument("--dry-run", action="store_true", help="演练，不实际改动")
    parser.add_argument("--verify", action="store_true", help="只校验各库当前版本")
    parser.add_argument("--list", action="store_true", help="列出受管数据库与迁移")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.targets:
        targets = [get_target(k.strip()) for k in args.targets.split(",") if k.strip()]
    else:
        targets = list(TARGETS)

    if args.list:
        cmd_list(targets)
        return 0
    if args.verify:
        return 1 if cmd_verify(targets) else 0

    log("")
    log("#" * 74)
    log("#  统一数据库部署  ——  建库 / 建用户 / 授权 / 版本化迁移")
    log("#" * 74)
    log(f"  目标库数量: {len(targets)}")
    for t in targets:
        log(f"    - {t.key:32s} {t.db_name}")
    log(f"  管理员: {ADMIN_USER}@{ADMIN_HOST}:{ADMIN_PORT}")
    log(f"  模式: {'演练(dry-run)' if args.dry_run else '实际执行'}"
        f"{' | create-only' if args.create_only else ''}"
        f"{' | migrate-only' if args.migrate_only else ''}"
        f"{' | bootstrap' if args.bootstrap else ''}")
    log("")

    if not args.yes and not args.dry_run:
        try:
            resp = input("确认执行？(yes/no): ").strip().lower()
        except EOFError:
            resp = "no"
        if resp not in ("yes", "y"):
            log("已取消。")
            return 0

    if not args.migrate_only:
        create_targets(targets, args.dry_run)

    if args.bootstrap and not args.migrate_only:
        bootstrap_legacy(targets, args.dry_run)

    failed = 0
    if not args.create_only:
        failed = migrate_targets(targets, args.dry_run, args.strict)

    log("")
    if failed:
        log(f"{ERR} 部署完成，但有 {failed} 个迁移文件存在失败语句，请查看上方日志。")
        return 2
    log(f"{OK} 部署完成。可用 `python deploy_db.py --verify` 复核各库版本。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
