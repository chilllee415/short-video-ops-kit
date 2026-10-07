#!/usr/bin/env python3
"""Run the complete report pipeline with fictional offline data."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(*arguments: str) -> None:
    subprocess.run([sys.executable, *arguments], cwd=ROOT, check=True)

def main() -> None:
    run("scripts/analyze_comments.py", "--input", "examples/demo-collected.json", "--output", "workspace/demo/analysis-input.json")
    run("scripts/finalize_analysis.py", "--input", "workspace/demo/analysis-input.json", "--findings", "examples/demo-findings.json", "--output", "workspace/demo/analysis.json")
    run("scripts/publish_report.py", "--account", "demo_account", "--data", "workspace/demo/analysis.json")
    run("scripts/validate_package.py", "--account", "demo_account")
    print(json.dumps({"ok": True, "indexPage": str((ROOT / "workspace/site/comment-insight-index.html").resolve()), "detailPage": str((ROOT / "workspace/site/demo_account.html").resolve())}, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
