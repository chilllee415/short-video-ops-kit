#!/usr/bin/env python3
"""Build dashboard data and render the operations dashboard in one command."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_workspace() -> Path:
    env = os.environ.get("SHORT_VIDEO_OPS_WORKSPACE")
    if env:
        return Path(env).expanduser().resolve()
    raise SystemExit(
        "workspace is required. Pass it as an argument or set SHORT_VIDEO_OPS_WORKSPACE."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "workspace",
        nargs="?",
        help="User workspace root. Defaults to SHORT_VIDEO_OPS_WORKSPACE.",
    )
    parser.add_argument("--template", help="Optional dashboard template path.")
    parser.add_argument("--data", help="Optional dashboard JSON path.")
    parser.add_argument("--output", help="Optional rendered HTML output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = system_root()
    workspace_path = (
        Path(args.workspace).expanduser().resolve()
        if args.workspace
        else default_workspace()
    )
    workspace = str(workspace_path)
    data_path = (
        str(Path(args.data).expanduser().resolve())
        if args.data
        else str(Path(workspace) / "presentation/ops-dashboard.json")
    )

    build_cmd = [
        sys.executable,
        str(root / "scripts/build_ops_dashboard_data.py"),
        workspace,
        "--output",
        data_path,
    ]
    render_cmd = [
        sys.executable,
        str(root / "scripts/render_ops_dashboard.py"),
        workspace,
        "--data",
        data_path,
    ]
    if args.template:
        render_cmd.extend(["--template", str(Path(args.template).expanduser().resolve())])
    if args.output:
        render_cmd.extend(["--output", str(Path(args.output).expanduser().resolve())])

    subprocess.run(build_cmd, check=True)
    subprocess.run(render_cmd, check=True)


if __name__ == "__main__":
    main()
