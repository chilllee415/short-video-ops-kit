#!/usr/bin/env python3
"""Render a daily report template without overwriting an existing output."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def flatten(value: object, prefix: str = "") -> dict[str, object]:
    result: dict[str, object] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            result.update(flatten(item, f"{prefix}{key}_" if prefix else f"{key}_"))
    else:
        result[prefix.rstrip("_")] = value
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite existing report: {args.output}")
    template = args.template.read_text(encoding="utf-8")
    payload = json.loads(args.data.read_text(encoding="utf-8"))
    data = flatten(payload)
    for key, value in payload.get("kpis", {}).items():
        if isinstance(value, (str, int, float)):
            data[key] = value
    for key, value in data.items():
        template = template.replace("{{" + key + "}}", html.escape(str(value)))
    template = template.replace("{{field_name}}", "field_name").replace("{{numeric_value}}", "numeric_value")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(template, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
