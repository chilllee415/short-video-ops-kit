#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import jsonschema


REQUIRED_CURRENT_KEYS = [
    "account_profile",
    "offer_profile",
    "audience_profile",
    "strategy_brief",
    "strategy_weights",
    "topic_discovery_policy",
    "topic_selection_policy",
    "benchmark_mining_policy",
    "account_snapshot",
    "content_performance",
    "strategy_assessment",
    "topic_signals",
    "audience_signals",
    "market_signals",
    "pain_bank",
    "competitor_map",
    "reference_bank",
    "topic_candidates_conservative",
    "topic_candidates_experimental",
    "topic_selection",
    "daily_plan",
    "publishing_plan",
    "published_posts",
    "post_metrics",
    "feedback_learning",
    "strategy_delta",
]

LEGACY_TOP_LEVEL_DIRS = {
    "00_profile", "01_raw", "02_normalized", "03_strategy", "04_generated",
    "05_publish", "06_feedback", "07_skills", "99_runs",
}

CURRENT_SCHEMAS = {
    "account_snapshot": "account-snapshot.schema.json",
    "strategy_assessment": "strategy-assessment.schema.json",
    "pain_bank": "pain-bank.schema.json",
    "strategy_brief": "strategy-brief.schema.json",
    "topic_candidates_conservative": "topic-lane.schema.json",
    "topic_candidates_experimental": "topic-lane.schema.json",
    "topic_selection": "topic-selection.schema.json",
    "feedback_learning": "feedback-learning.schema.json",
    "topic_signals": "topic-signals.schema.json",
    "market_signals": "market-signals.schema.json",
    "daily_plan": "daily-content-plan.schema.json",
}

ARTIFACT_SCHEMAS = {
    "dashboard_status": "presentation-status.schema.json",
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"missing file: {path}") from None
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid json: {path}: {exc}") from None
    if not isinstance(value, dict):
        raise SystemExit(f"expected json object: {path}")
    return value


def check_path(root: Path, rel: str) -> None:
    path = (root / rel).resolve()
    if not path.is_relative_to(root):
        raise SystemExit(f"manifest target escapes workspace: {rel}")
    if not path.exists():
        raise SystemExit(f"missing manifest target: {rel}")


def resolve_data_path(root: Path, rel: str) -> Path:
    return (root / rel).resolve()


def resolve_system_path(system_root: Path, rel: str) -> Path:
    path = (system_root / rel).resolve()
    if path.exists():
        return path

    # Backward compatibility for older templates that used ../../manifests.
    cleaned = rel
    while cleaned.startswith("../"):
        cleaned = cleaned[3:]
    fallback = (system_root / cleaned).resolve()
    if fallback.exists():
        return fallback

    raise SystemExit(f"missing system manifest target: {rel}")


def main() -> None:
    if len(sys.argv) > 2:
        raise SystemExit("usage: validate_workspace.py [workspace]")

    workspace_arg = sys.argv[1] if len(sys.argv) == 2 else os.environ.get("SHORT_VIDEO_OPS_WORKSPACE")
    if not workspace_arg:
        raise SystemExit("usage: validate_workspace.py [workspace]\nOr set SHORT_VIDEO_OPS_WORKSPACE=/path/to/workspace")

    root = Path(workspace_arg).resolve()
    system_root = Path(__file__).resolve().parents[1]
    manifest_path = root / "project.manifest.json"
    manifest = load_json(manifest_path)

    manifest_schema = load_json(system_root / "schemas/project-manifest.schema.json")
    jsonschema.Draft202012Validator(manifest_schema).validate(manifest)

    present_legacy = sorted(name for name in LEGACY_TOP_LEVEL_DIRS if (root / name).exists())
    if present_legacy:
        raise SystemExit("legacy top-level directories are not allowed: " + ", ".join(present_legacy))

    contract_rel = manifest.get("data_contract")
    if not isinstance(contract_rel, str):
        raise SystemExit("data_contract must be a path string")
    check_path(root, contract_rel)
    contract = load_json(root / contract_rel)
    if contract.get("path_model") != "domain-first":
        raise SystemExit("data contract must declare path_model=domain-first")

    workspace_index = manifest.get("workspace_index")
    if workspace_index is not None:
        if not isinstance(workspace_index, str):
            raise SystemExit("workspace_index must be a path string")
        index_path = root / workspace_index
        index = load_json(index_path)
        entries = index.get("entries")
        if not isinstance(entries, list):
            raise SystemExit("workspace.index.json missing entries array")
        for entry in entries:
            if not isinstance(entry, dict):
                raise SystemExit("workspace.index.json entries must be objects")
            rel = entry.get("path")
            if not isinstance(rel, str):
                raise SystemExit("workspace.index.json entry.path must be a string")
            check_path(root, rel)

    workspace_policy = manifest.get("workspace_policy")
    if workspace_policy is not None:
        if not isinstance(workspace_policy, str):
            raise SystemExit("workspace_policy must be a path string")
        policy = load_json(root / workspace_policy)
        manifest_mode = manifest.get("operating_mode")
        policy_mode = policy.get("mode")
        if manifest_mode and policy_mode and manifest_mode != policy_mode:
            raise SystemExit(f"operating_mode mismatch: manifest={manifest_mode}, policy={policy_mode}")

    current = manifest.get("current")
    if not isinstance(current, dict):
        raise SystemExit("project.manifest.json missing current object")

    missing_keys = [key for key in REQUIRED_CURRENT_KEYS if key not in current]
    if missing_keys:
        raise SystemExit(f"project.manifest.json missing current keys: {', '.join(missing_keys)}")

    for key, rel in current.items():
        if not isinstance(rel, str):
            raise SystemExit(f"current.{key} must be a path string")
        check_path(root, rel)
        if rel.endswith(".json"):
            value = load_json(root / rel)
            schema_name = CURRENT_SCHEMAS.get(key)
            if schema_name:
                schema = load_json(system_root / "schemas" / schema_name)
                errors = sorted(
                    jsonschema.Draft202012Validator(
                        schema, format_checker=jsonschema.FormatChecker()
                    ).iter_errors(value),
                    key=lambda error: list(error.path),
                )
                if errors:
                    detail = "; ".join(
                        f"{'.'.join(map(str, error.path)) or '<root>'}: {error.message}"
                        for error in errors
                    )
                    raise SystemExit(f"current.{key} schema failed: {detail}")

    artifacts = manifest.get("artifacts", {})
    if not isinstance(artifacts, dict):
        raise SystemExit("artifacts must be an object")
    for key, schema_name in ARTIFACT_SCHEMAS.items():
        rel = artifacts.get(key)
        if not isinstance(rel, str):
            raise SystemExit(f"artifacts.{key} must be a path string")
        check_path(root, rel)
        value = load_json(root / rel)
        schema = load_json(system_root / "schemas" / schema_name)
        jsonschema.Draft202012Validator(schema).validate(value)

    workflow_manifests = manifest.get("workflow_manifests", {})
    if not isinstance(workflow_manifests, dict):
        raise SystemExit("workflow_manifests must be an object")

    for workflow_id, rel in workflow_manifests.items():
        if not isinstance(rel, str):
            raise SystemExit(f"workflow_manifests.{workflow_id} must be a path string")
        path = resolve_data_path(root, rel)
        if not path.exists():
            path = resolve_system_path(system_root, rel)
        load_json(path)

    print(f"ok: {root}")


if __name__ == "__main__":
    main()
