#!/usr/bin/env python3
"""Validate package structure, report index consistency, and secret hygiene."""
from __future__ import annotations

import argparse
import json
import py_compile
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--account")
    args = parser.parse_args()
    required = [
        ROOT / "SKILL.md",
        ROOT / ".env.example",
        ROOT / "LICENSE",
        ROOT / "README.md",
        ROOT / "scripts" / "workflow.py",
        ROOT / "scripts" / "publish_report.py",
        ROOT / "assets" / "templates" / "index.html",
        ROOT / "assets" / "templates" / "report.html",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("缺少文件：" + ", ".join(missing))
    for script in (ROOT / "scripts").glob("*.py"):
        py_compile.compile(str(script), doraise=True)
    scan_roots = [ROOT / "SKILL.md", ROOT / "scripts", ROOT / "assets", ROOT / "references", ROOT / "examples"]
    suspicious = re.compile(r"(?i)(?:sk-[a-z0-9_-]{16,}|bearer\s+[a-z0-9._-]{16,}|tikhub_api_key\s*=\s*(?!replace_)[^\s]+)")
    leaked = []
    for scan_root in scan_roots:
        paths = [scan_root] if scan_root.is_file() else scan_root.rglob("*") if scan_root.exists() else []
        for path in paths:
            if path.is_file() and path.suffix.lower() in {"", ".py", ".md", ".html", ".json", ".yaml", ".yml"}:
                if suspicious.search(path.read_text(encoding="utf-8", errors="ignore")):
                    leaked.append(str(path.relative_to(ROOT)))
    if leaked:
        raise SystemExit("疑似包含密钥：" + ", ".join(leaked))
    site = ROOT / "workspace" / "site"
    index_path = site / "comment-insight-index.json"
    reports = []
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        reports = index.get("reports", [])
        ids = [str(row.get("accountId")) for row in reports]
        if len(ids) != len(set(ids)):
            raise SystemExit("列表索引存在重复账号")
        for row in reports:
            if not (site / row["file"]).exists():
                raise SystemExit(f"详情页不存在：{row['file']}")
    if args.account and not any(str(row.get("accountId")) == args.account for row in reports):
        raise SystemExit(f"索引中没有账号：{args.account}")
    print(json.dumps({"ok": True, "scripts": len(list((ROOT / 'scripts').glob('*.py'))), "reports": len(reports), "secretScan": "passed"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
