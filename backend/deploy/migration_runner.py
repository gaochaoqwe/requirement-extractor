"""
版本化迁移引擎

职责：
1. 在每个受管数据库中维护一张 `schema_migrations` 版本表，记录已应用的迁移；
2. 扫描 `deploy/migrations/<db_key>/` 下形如 `V001__描述.sql` 的迁移文件；
3. 按版本号顺序执行尚未应用的迁移，一条一句、幂等可重跑；
4. 提供「已应用 / 待应用 / 校验和不一致」的可视化查询，让任何环境当前处于哪个版本一目了然。

设计约定：
- 迁移文件内容必须幂等（`CREATE ... IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS`），
  这样重复执行、以及在已有环境上首次纳管都不会破坏数据。
- 单条语句失败不会中断整个文件：默认记录为 failed 并继续；`strict=True` 时立即中止。
- 版本号取自文件名 `V<数字>__<描述>.sql`；数字排序，而非字典序。
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2.extensions import connection as PGConnection

MIGRATION_FILE_RE = re.compile(r"^V?(\d+)__(.+)\.sql$", re.IGNORECASE)

MIGRATIONS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     VARCHAR(64)  PRIMARY KEY,
    description TEXT,
    checksum    VARCHAR(64),
    applied_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


# ---------------------------------------------------------------------------
# SQL 语句切分：尊重 $$ 美元引用、单/双引号、行注释与块注释
# ---------------------------------------------------------------------------
def split_sql_statements(sql: str) -> list[str]:
    """把一段可能包含多条语句的 SQL 拆成独立语句列表（去掉空语句与纯注释）。"""
    statements: list[str] = []
    buf: list[str] = []
    i = 0
    n = len(sql)
    dollar_tag: str | None = None   # 当前 $$tag$$ 标签
    in_single = False
    in_double = False
    in_line_comment = False
    in_block_comment = False

    while i < n:
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ""

        # 块注释
        if in_block_comment:
            buf.append(ch)
            if ch == "*" and nxt == "/":
                buf.append(nxt)
                i += 2
                in_block_comment = False
                continue
            i += 1
            continue

        # 行注释
        if in_line_comment:
            buf.append(ch)
            if ch == "\n":
                in_line_comment = False
            i += 1
            continue

        # 美元引用体内
        if dollar_tag is not None:
            if sql.startswith(dollar_tag, i):
                buf.append(dollar_tag)
                i += len(dollar_tag)
                dollar_tag = None
                continue
            buf.append(ch)
            i += 1
            continue

        # 单引号字符串
        if in_single:
            buf.append(ch)
            if ch == "'":
                if nxt == "'":          # 转义的单引号 ''
                    buf.append(nxt)
                    i += 2
                    continue
                in_single = False
            i += 1
            continue

        # 双引号标识符
        if in_double:
            buf.append(ch)
            if ch == '"':
                in_double = False
            i += 1
            continue

        # 顶层：识别各类起始标记
        if ch == "-" and nxt == "-":
            buf.append(ch)
            buf.append(nxt)
            i += 2
            in_line_comment = True
            continue
        if ch == "/" and nxt == "*":
            buf.append(ch)
            buf.append(nxt)
            i += 2
            in_block_comment = True
            continue
        if ch == "'":
            buf.append(ch)
            i += 1
            in_single = True
            continue
        if ch == '"':
            buf.append(ch)
            i += 1
            in_double = True
            continue
        if ch == "$":
            m = re.match(r"\$[A-Za-z_0-9]*\$", sql[i:])
            if m:
                dollar_tag = m.group(0)
                buf.append(dollar_tag)
                i += len(dollar_tag)
                continue
        if ch == ";":
            stmt = "".join(buf).strip()
            if _has_executable(stmt):
                statements.append(stmt)
            buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    tail = "".join(buf).strip()
    if _has_executable(tail):
        statements.append(tail)
    return statements


def _has_executable(stmt: str) -> bool:
    """去掉注释后是否还有实际 SQL 内容。"""
    stripped = re.sub(r"--[^\n]*", "", stmt)
    stripped = re.sub(r"/\*.*?\*/", "", stripped, flags=re.DOTALL)
    return bool(stripped.strip())


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------
@dataclass
class Migration:
    version: str          # 形如 "001"
    description: str
    path: Path
    checksum: str
    statements: list[str] = field(default_factory=list)


@dataclass
class StatementResult:
    version: str
    sql: str
    ok: bool
    error: str = ""


@dataclass
class ApplyResult:
    applied: list[Migration] = field(default_factory=list)
    skipped: list[Migration] = field(default_factory=list)       # 已应用过
    failed: list[Migration] = field(default_factory=list)
    statement_errors: list[StatementResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 迁移发现
# ---------------------------------------------------------------------------
def discover_migrations(migrations_dir: Path) -> list[Migration]:
    """扫描目录，返回按版本号升序排列的迁移列表。"""
    if not migrations_dir.exists():
        return []
    found: list[tuple[int, Migration]] = []
    for path in migrations_dir.glob("*.sql"):
        m = MIGRATION_FILE_RE.match(path.name)
        if not m:
            continue
        num = int(m.group(1))
        content = path.read_text(encoding="utf-8")
        migrations = Migration(
            version=f"{num:03d}",
            description=m.group(2).strip(),
            path=path,
            checksum=hashlib.sha256(content.encode("utf-8")).hexdigest()[:16],
            statements=split_sql_statements(content),
        )
        found.append((num, migrations))
    found.sort(key=lambda x: x[0])
    return [mig for _, mig in found]


# ---------------------------------------------------------------------------
# 引擎
# ---------------------------------------------------------------------------
class MigrationRunner:
    def __init__(self, target, logger=print, strict: bool = False):
        self.target = target
        self.log = logger
        self.strict = strict

    # -- 连接 ---------------------------------------------------------------
    def connect(self) -> PGConnection:
        return psycopg2.connect(
            host=self.target.host,
            port=self.target.port,
            dbname=self.target.db_name,
            user=self.target.user,
            password=self.target.password,
            connect_timeout=8,
        )

    # -- 版本表 -------------------------------------------------------------
    def ensure_migrations_table(self, conn: PGConnection) -> None:
        with conn.cursor() as cur:
            cur.execute(MIGRATIONS_TABLE_DDL)
        conn.commit()

    def applied_versions(self, conn: PGConnection) -> dict[str, dict]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT version, description, checksum, applied_at FROM schema_migrations"
            )
            rows = cur.fetchall()
        return {
            r[0]: {"description": r[1], "checksum": r[2], "applied_at": r[3]}
            for r in rows
        }

    # -- 执行 ---------------------------------------------------------------
    def pending(self, conn: PGConnection) -> list[Migration]:
        applied = self.applied_versions(conn)
        return [m for m in discover_migrations(self.target.migrations_dir)
                if m.version not in applied]

    def apply(self, dry_run: bool = False) -> ApplyResult:
        result = ApplyResult()
        migrations = discover_migrations(self.target.migrations_dir)

        with self.connect() as conn:
            # dry-run 严格只读：不创建 schema_migrations
            if dry_run:
                with conn.cursor() as cur:
                    cur.execute("SELECT to_regclass('public.schema_migrations')")
                    table_exists = cur.fetchone()[0] is not None
                applied = self.applied_versions(conn) if table_exists else {}
            else:
                self.ensure_migrations_table(conn)
                applied = self.applied_versions(conn)

            for mig in migrations:
                if mig.version in applied:
                    result.skipped.append(mig)
                    continue
                if dry_run:
                    result.applied.append(mig)
                    continue

                ok = self._apply_one(conn, mig, result)
                if ok:
                    result.applied.append(mig)
                else:
                    result.failed.append(mig)
                    if self.strict:
                        conn.rollback()
                        break
        return result

    def _apply_one(self, conn: PGConnection, mig: Migration, result: ApplyResult) -> bool:
        file_ok = True
        for stmt in mig.statements:
            try:
                with conn.cursor() as cur:
                    cur.execute(stmt)
                conn.commit()
            except Exception as exc:                      # noqa: BLE001
                conn.rollback()
                file_ok = False
                result.statement_errors.append(
                    StatementResult(mig.version, stmt, ok=False, error=str(exc).strip())
                )
                if self.strict:
                    return False
        if file_ok:
            self._record(conn, mig)
        return file_ok

    def _record(self, conn: PGConnection, mig: Migration) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO schema_migrations (version, description, checksum)
                VALUES (%s, %s, %s)
                ON CONFLICT (version) DO UPDATE
                    SET description = EXCLUDED.description,
                        checksum    = EXCLUDED.checksum
                """,
                (mig.version, mig.description, mig.checksum),
            )
        conn.commit()

    # -- 校验 ---------------------------------------------------------------
    def verify(self) -> list[dict]:
        """返回每个迁移的当前状态，用于 `--verify`。

        严格只读：不创建 schema_migrations；若该表不存在，则所有迁移视为 pending。
        """
        rows: list[dict] = []
        migrations = discover_migrations(self.target.migrations_dir)
        try:
            with self.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT to_regclass('public.schema_migrations')")
                    table_exists = cur.fetchone()[0] is not None
                applied = self.applied_versions(conn) if table_exists else {}
                reachable = True
        except Exception as exc:                          # noqa: BLE001
            return [{"error": str(exc).strip(), "reachable": False}]

        for mig in migrations:
            info = applied.get(mig.version)
            if info is None:
                status = "pending"
            elif info["checksum"] != mig.checksum:
                status = "changed"
            else:
                status = "applied"
            rows.append({
                "reachable": reachable,
                "version": mig.version,
                "description": mig.description,
                "status": status,
                "applied_at": info["applied_at"] if info else None,
            })
        return rows


def utcnow() -> datetime:
    return datetime.utcnow()
