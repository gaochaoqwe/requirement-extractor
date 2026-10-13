"""
数据库结构快照工具

用途：把 7 个 PostgreSQL 库的**当前真实结构**用 pg_dump 导出为 SQL 快照。
这是消除「新环境与老环境 schema 对不齐」的最直接手段：
先在现有环境跑一次快照，即可得到一份权威基线，用于核对或归档。

用法：
    python snapshot_schema.py                 # 快照全部库
    python snapshot_schema.py --targets code_review,auth
    python snapshot_schema.py --pg-dump "C:/Program Files/PostgreSQL/16/bin/pg_dump.exe"

输出：backend/deploy/snapshots/<库名>_schema_<YYYYMMDD_HHMMSS>.sql

注意：
- 需要本机可执行 pg_dump（通常随 PostgreSQL 安装）。
- 本工具只读取结构（--schema-only），不含业务数据，不会修改数据库。
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from db_config import SNAPSHOTS_DIR, TARGETS, get_target  # noqa: E402


def find_pg_dump(explicit: str = "") -> str | None:
    if explicit:
        return explicit if Path(explicit).exists() else None
    # PATH
    found = shutil.which("pg_dump")
    if found:
        return found
    # Windows 常见安装位置
    for base in (r"C:\Program Files\PostgreSQL", r"C:\Program Files (x86)\PostgreSQL"):
        p = Path(base)
        if p.exists():
            for ver_dir in sorted(p.iterdir(), reverse=True):
                candidate = ver_dir / "bin" / "pg_dump.exe"
                if candidate.exists():
                    return str(candidate)
    return None


def snapshot(target, pg_dump: str) -> tuple[bool, str]:
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = SNAPSHOTS_DIR / f"{target.db_name}_schema_{stamp}.sql"

    env = dict(os.environ)
    env["PGPASSWORD"] = target.password
    cmd = [
        pg_dump,
        "--schema-only", "--no-owner", "--no-privileges",
        "-h", target.host, "-p", str(target.port),
        "-U", target.user, "-d", target.db_name,
        "-f", str(out_file),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=180)
    except Exception as exc:                              # noqa: BLE001
        return False, f"执行失败: {exc}"
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or "").strip()
    return True, str(out_file)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="导出各库结构快照（pg_dump --schema-only）")
    parser.add_argument("--targets", default="", help="逗号分隔的目标 key，默认全部")
    parser.add_argument("--pg-dump", default="", help="pg_dump 可执行文件路径")
    args = parser.parse_args(argv)

    targets = [get_target(k.strip()) for k in args.targets.split(",") if k.strip()] or list(TARGETS)

    pg_dump = find_pg_dump(args.pg_dump)
    if not pg_dump:
        print("[XX] 未找到 pg_dump。请安装 PostgreSQL 客户端，或用 --pg-dump 指定路径。")
        return 1
    print(f"[OK] 使用 pg_dump: {pg_dump}")
    print(f"[OK] 输出目录: {SNAPSHOTS_DIR}")
    print()

    failed = 0
    for t in targets:
        print(f"  [..] [{t.key}] {t.db_name} ...", end=" ", flush=True)
        ok, msg = snapshot(t, pg_dump)
        if ok:
            print(f"[OK] {Path(msg).name}")
        else:
            print(f"[XX] {msg}")
            failed += 1
    print()
    print(f"完成：成功 {len(targets) - failed}，失败 {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
