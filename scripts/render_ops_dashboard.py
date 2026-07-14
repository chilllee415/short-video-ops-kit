#!/usr/bin/env python3
"""Render the operations dashboard HTML from a template and JSON data."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


PLACEHOLDER = "__OPS_DASHBOARD_DATA__"
REQUIRED_TOP_LEVEL_KEYS = ("account", "demand", "execution", "benchmark")


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_workspace() -> Path:
    env = os.environ.get("SHORT_VIDEO_OPS_WORKSPACE")
    if env:
        return Path(env).expanduser().resolve()
    raise SystemExit(
        "workspace is required. Pass it as an argument or set SHORT_VIDEO_OPS_WORKSPACE."
    )


def load_dashboard_data(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    missing = [key for key in REQUIRED_TOP_LEVEL_KEYS if key not in data]
    if missing:
        raise SystemExit(f"dashboard data missing required keys: {', '.join(missing)}")
    return data


def encode_for_script(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")


def render_dashboard(template_path: Path, data_path: Path, output_path: Path) -> None:
    template = template_path.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        raise SystemExit(f"template missing placeholder {PLACEHOLDER}: {template_path}")

    dashboard_data = load_dashboard_data(data_path)
    html = template.replace(PLACEHOLDER, encode_for_script(dashboard_data))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    print(f"rendered dashboard: {output_path}")
    print(f"template: {template_path}")
    print(f"data: {data_path}")
    print(f"bytes: {output_path.stat().st_size}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "workspace",
        nargs="?",
        help="User workspace root. Defaults to SHORT_VIDEO_OPS_WORKSPACE.",
    )
    parser.add_argument("--template", help="Template HTML path.")
    parser.add_argument("--data", help="Dashboard JSON data path.")
    parser.add_argument("--output", help="Rendered HTML output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workspace = (
        Path(args.workspace).expanduser().resolve()
        if args.workspace
        else default_workspace()
    )
    root = system_root()

    template_path = (
        Path(args.template).expanduser().resolve()
        if args.template
        else root / "templates/internal-pages/ops-dashboard.template.html"
    )
    data_path = (
        Path(args.data).expanduser().resolve()
        if args.data
        else workspace / "presentation/ops-dashboard.json"
    )
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else workspace
        / "presentation/internal-pages/运营大盘.html"
    )

    render_dashboard(template_path, data_path, output_path)


if __name__ == "__main__":
    main()
