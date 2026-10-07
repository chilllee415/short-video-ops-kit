#!/usr/bin/env python3
"""Validate daily report sample fields against template placeholders."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "integrations/douyin-daily-report"
    template = (root / "templates/daily-report-template.html").read_text(encoding="utf-8")
    sample = json.loads((root / "examples/daily-report.sample.json").read_text(encoding="utf-8"))
    placeholders = set(re.findall(r"{{\s*([a-zA-Z0-9_]+)\s*}}", template))
    flat: dict[str, object] = {}

    def visit(value: object, prefix: str = "") -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                visit(item, f"{prefix}{key}_" if prefix else f"{key}_")
        else:
            flat[prefix.rstrip("_")] = value

    visit(sample)
    for key, value in sample.get("kpis", {}).items():
        if isinstance(value, (str, int, float)):
            flat[key] = value
    placeholders -= {"field_name", "numeric_value"}
    missing = sorted(placeholders - set(flat))
    if missing:
        raise SystemExit("sample missing template fields: " + ", ".join(missing))
    print(json.dumps({"ok": True, "placeholders": len(placeholders), "sample_fields": len(flat)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
