#!/usr/bin/env python3
"""Resolve topic-discovery context from an explicit workspace contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROLES = {
    "account_profile": "account_profile",
    "audience_profile": "audience_profile",
    "offer_profile": "offer_profile",
    "strategy": "strategy_brief",
    "topic_discovery_policy": "topic_discovery_policy",
    "topic_selection_policy": "topic_selection_policy",
    "benchmark_mining_policy": "benchmark_mining_policy",
    "account_snapshot": "account_snapshot",
    "content_performance": "content_performance",
    "strategy_assessment": "strategy_assessment",
    "topic_signals": "topic_signals",
    "topic_candidates_conservative": "topic_candidates_conservative",
    "topic_candidates_experimental": "topic_candidates_experimental",
    "selected_topics": "topic_selection",
}


def load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def safe_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise SystemExit(f"manifest path escapes workspace: {relative}")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    root = args.workspace.expanduser().resolve()
    manifest_path = root / "project.manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"missing workspace manifest: {manifest_path}")
    manifest = load_object(manifest_path)
    current = manifest.get("current")
    if not isinstance(current, dict):
        raise SystemExit("project.manifest.json missing current object")

    available, missing = {}, []
    for role, key in ROLES.items():
        relative = current.get(key)
        if not isinstance(relative, str):
            missing.append(role)
            continue
        path = safe_path(root, relative)
        if path.is_file():
            available[role] = str(path)
        else:
            missing.append(role)

    print(json.dumps({
        "workspace": str(root),
        "mode": "manifest",
        "available": available,
        "missing": sorted(missing),
        "api_required": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
