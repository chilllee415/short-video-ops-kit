#!/usr/bin/env python3
"""Create a clean Short Video Ops workspace from the public template."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configure_mode(workspace: Path, mode: str, project_id: str, display_name: str, category: str) -> None:
    root = system_root()
    policy_source = root / "templates/workspace-policies" / f"{mode}.policy.json"
    shutil.copy2(policy_source, workspace / "workspace.policy.json")

    manifest_path = workspace / "project.manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["project_id"] = project_id
    manifest["display_name"] = display_name
    manifest["category"] = category
    manifest["operating_mode"] = mode
    manifest["workspace_policy"] = "workspace.policy.json"
    write_json(manifest_path, manifest)

    registry_path = workspace / "project.registry.json"
    registry = {
        "project_id": project_id,
        "display_name": display_name,
        "category": category,
        "workspace_path": str(workspace),
        "status": "initialized",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_run_at": ""
    }
    write_json(registry_path, registry)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path, help="Directory to create. It must not already exist.")
    parser.add_argument(
        "--mode",
        choices=("personal", "commercial"),
        default="personal",
        help="personal is for one creator; commercial is for client delivery.",
    )
    parser.add_argument("--project-id", help="Stable project identifier; defaults to the workspace directory name.")
    parser.add_argument("--display-name", help="Human-readable project name; defaults to the project ID.")
    parser.add_argument("--category", default="generic", help="Unconfirmed project category; defaults to generic.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target = args.workspace.expanduser().resolve()
    if target.exists():
        raise SystemExit(f"workspace already exists: {target}\nChoose a new empty path instead of overwriting data.")

    source = system_root() / "templates/project-workspace"
    shutil.copytree(source, target)
    project_id = args.project_id or target.name
    display_name = args.display_name or project_id
    configure_mode(target, args.mode, project_id, display_name, args.category)
    subprocess.run(
        [sys.executable, str(system_root() / "scripts/update_ops_dashboard.py"), str(target)],
        check=True,
    )

    print(f"created {args.mode} workspace: {target}")
    print("next steps:")
    print(f"  1. Open {target / 'presentation/internal-pages/运营大盘.html'}")
    print("  2. Complete the first-run questionnaire and copy its structured prompt to Codex")
    print("  3. Review and explicitly confirm the positioning and strategy drafts before they are written")
    print(f"  4. Run: python3 {system_root() / 'scripts/validate_workspace.py'} {target}")
    print(f"  5. Run: python3 {system_root() / 'scripts/update_ops_dashboard.py'} {target}")


if __name__ == "__main__":
    main()
