#!/usr/bin/env python3
"""Inspect history and prepare a new or refreshed Douyin comment analysis run."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_env() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


load_env()
WORKSPACE = Path(os.getenv("DOUYIN_INSIGHT_WORKSPACE") or ROOT / "workspace").expanduser().resolve()
RUNS = WORKSPACE / "runs"
SITE = WORKSPACE / "site"
INDEX = SITE / "comment-insight-index.json"
ACCOUNT_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def validate_account(account: str) -> None:
    if not ACCOUNT_PATTERN.fullmatch(account):
        raise SystemExit("账号只能包含字母、数字、下划线和连字符，长度不超过 64")


def load_index() -> dict:
    if not INDEX.exists():
        return {"updatedAt": "", "reports": []}
    return json.loads(INDEX.read_text(encoding="utf-8"))


def report_for(account: str) -> dict | None:
    return next((row for row in load_index().get("reports", []) if str(row.get("accountId")) == account), None)


def inspect(account: str) -> dict:
    validate_account(account)
    report = report_for(account)
    detail = SITE / f"{account}.html"
    return {
        "accountId": account,
        "exists": bool(report),
        "action": "update" if report else "new",
        "report": report,
        "detailPage": str(detail) if detail.exists() else "",
        "indexPage": str(SITE / "comment-insight-index.html"),
    }


def latest_input(account: str) -> Path | None:
    candidates = sorted(RUNS.glob(f"*/{account}/analysis-input.json"), reverse=True)
    return candidates[0] if candidates else None


def prepare(args: argparse.Namespace) -> dict:
    if not 1 <= args.works <= 20:
        raise SystemExit("--works 必须在 1 到 20 之间")
    if not 1 <= args.comments <= 1000:
        raise SystemExit("--comments 必须在 1 到 1000 之间")
    state = inspect(args.account)
    if args.mode == "reuse":
        analysis_input = latest_input(args.account)
        if not analysis_input:
            raise SystemExit(f"没有可复用的历史分析输入：{args.account}")
        run_dir = analysis_input.parent
        action = "reuse"
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        run_dir = RUNS / stamp / args.account
        run_dir.mkdir(parents=True, exist_ok=True)
        command = [
            sys.executable,
            str(Path(__file__).with_name("fetch_account_data.py")),
            args.account,
            "--out", str(run_dir),
            "--works", str(args.works),
            "--comments", str(args.comments),
        ]
        subprocess.run(command, check=True)
        analysis_input = run_dir / "analysis-input.json"
        subprocess.run([
            sys.executable,
            str(Path(__file__).with_name("analyze_comments.py")),
            "--input", str(run_dir / "collected.json"),
            "--output", str(analysis_input),
        ], check=True)
        action = state["action"]

    findings = run_dir / "findings.json"
    final_analysis = run_dir / "analysis.json"
    if not findings.exists():
        findings.write_text(json.dumps({
            "lane": "待归纳",
            "summary": "待 Codex 基于真实评论归纳",
            "metrics": {},
            "viewpoints": [],
            "opportunities": [],
            "run": {"status": "awaiting_analysis"},
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "accountId": args.account,
        "action": action,
        "analysisInput": str(analysis_input),
        "findings": str(findings),
        "finalAnalysis": str(final_analysis),
        "siteDir": str(SITE),
    }
    (run_dir / "run-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    inspect_parser = sub.add_parser("inspect")
    inspect_parser.add_argument("--account", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--account", required=True)
    prepare_parser.add_argument("--mode", choices=("auto", "refresh", "reuse"), default="auto")
    prepare_parser.add_argument("--works", type=int, default=20)
    prepare_parser.add_argument("--comments", type=int, default=100)
    args = parser.parse_args()
    result = inspect(args.account) if args.command == "inspect" else prepare(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
