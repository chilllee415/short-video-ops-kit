#!/usr/bin/env python3
"""Verify that the rendered V2 HTML carries and displays the latest dashboard semantics."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


EMBED_MARKER = "window.__DASHBOARD__ = "


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"missing file: {path}") from None
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid json: {path}: {exc}") from None
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def embedded_dashboard(html: str) -> dict[str, Any]:
    marker_at = html.find(EMBED_MARKER)
    if marker_at < 0:
        raise SystemExit("rendered HTML is missing the embedded dashboard payload")
    start = marker_at + len(EMBED_MARKER)
    try:
        value, _end = json.JSONDecoder().raw_decode(html[start:].lstrip())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"rendered HTML has an invalid embedded dashboard payload: {exc}") from None
    if not isinstance(value, dict):
        raise SystemExit("rendered HTML dashboard payload is not an object")
    return value


def label_map(rows: list[dict[str, Any]]) -> dict[str, str]:
    return {str(row.get("label")): str(row.get("value")) for row in rows if row.get("label")}


def percent_text(value: Any) -> str:
    if value is None:
        return ""
    text = f"{float(value) * 100:.2f}".rstrip("0").rstrip(".")
    return text + "%"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--run-id")
    args = parser.parse_args()

    workspace = args.workspace.expanduser().resolve()
    account_path = workspace / "data/operations/current/account-snapshot.json"
    account_profile_path = workspace / "config/profile/account.profile.json"
    strategy_path = workspace / "config/strategy/strategy-brief.json"
    dashboard_path = workspace / "presentation/ops-dashboard.json"
    plan_path = workspace / "work/plans/daily.json"
    conservative_path = workspace / "work/topics/conservative/current.json"
    experimental_path = workspace / "work/topics/experimental/current.json"
    selection_path = workspace / "work/topics/selections/daily.json"
    html_path = workspace / "presentation/internal-pages/运营大盘.html"

    account = load_object(account_path)
    account_profile = load_object(account_profile_path)
    strategy = load_object(strategy_path)
    dashboard = load_object(dashboard_path)
    plan = load_object(plan_path)
    conservative = load_object(conservative_path)
    experimental = load_object(experimental_path)
    selection = load_object(selection_path)
    html = html_path.read_text(encoding="utf-8")
    embedded = embedded_dashboard(html)
    errors: list[str] = []

    if embedded != dashboard:
        errors.append("HTML embedded dashboard payload does not exactly match ops-dashboard.json")

    expected_candidate_ids = {
        str(item.get("topic_id"))
        for lane in (conservative, experimental)
        for item in lane.get("topics") or []
        if item.get("topic_id")
    }
    dashboard_topics = (dashboard.get("demand") or {}).get("topics") or []
    dashboard_candidate_ids = {str(item.get("id")) for item in dashboard_topics if item.get("id")}
    if dashboard_candidate_ids != expected_candidate_ids:
        errors.append("dashboard candidate pool does not contain the complete conservative and experimental lanes")
    selected_ids = {
        str(item.get("topic_id"))
        for item in selection.get("selected") or []
        if item.get("topic_id")
    }
    dashboard_selected_ids = {
        str(item.get("id")) for item in dashboard_topics if item.get("selected") is True
    }
    if dashboard_selected_ids != selected_ids:
        errors.append("dashboard selected-topic flags do not match the mixed daily selection")

    # The canonical dashboard is a live presentation of the current workflow.
    # Recording/demo overrides belong in a separate artifact and must never
    # replace current facts after the canonical payload has been generated.
    if dashboard.get("recording"):
        errors.append("canonical dashboard contains a forbidden recording/demo override")
    if "RECORDING" in html:
        errors.append("canonical HTML still contains client-side recording-mode references")

    period = account.get("period") or {}
    expected_range = f"{period.get('start')} 至 {period.get('end')}"
    meta = dashboard.get("meta") or {}
    if meta.get("sourceDate") != period.get("end"):
        errors.append("dashboard sourceDate does not match account snapshot period.end")
    if meta.get("dataRange") != expected_range:
        errors.append("dashboard dataRange does not match account snapshot period")

    dashboard_account = dashboard.get("account") or {}
    stable_positioning = str(account_profile.get("positioning") or "")
    expected_headline = (
        stable_positioning.rsplit("/", 1)[-1].strip()
        if stable_positioning
        else "账号定位待确认"
    )
    stable_strategy = str(strategy.get("primary_strategy") or "")
    if dashboard_account.get("headline") != expected_headline:
        errors.append("dashboard positioning headline is not the objective positioning summary")
    direction_headline = str(dashboard_account.get("directionHeadline") or "")
    if not direction_headline or len(direction_headline) > 22:
        errors.append("dashboard directionHeadline must be a non-empty short direction of at most 22 characters")
    if dashboard_account.get("positioning") != stable_positioning:
        errors.append("dashboard positioning does not match account.profile.json")
    if dashboard_account.get("stableStrategy") != stable_strategy:
        errors.append("dashboard operating strategy does not match strategy-brief.json")
    if dashboard_account.get("headline") == account.get("account_stage"):
        errors.append("daily account stage was incorrectly promoted to the dashboard strategy headline")

    recent = (((account.get("metrics_summary") or {}).get("recent_window") or {}).get("recent_metrics") or {})
    radar = label_map((dashboard.get("account") or {}).get("radar") or [])
    expected_metrics = {
        "播放量": str(recent.get("plays_display") or ""),
        "完播率": percent_text(recent.get("completion_rate")),
        "互动指数": percent_text(recent.get("interaction_index")),
        "粉丝净增": str(recent.get("net_followers") if recent.get("net_followers") is not None else ""),
    }
    for label, expected in expected_metrics.items():
        if expected and radar.get(label) != expected:
            errors.append(f"dashboard {label} mismatch: expected {expected}, got {radar.get(label)}")

    execution_titles = {str(item.get("title")) for item in (dashboard.get("execution") or {}).get("plans") or []}
    if plan.get("status") != "blocked":
        for item in plan.get("plans") or []:
            if str(item.get("title")) not in execution_titles:
                errors.append(f"daily plan missing from rendered execution data: {item.get('title')}")
    else:
        blocked_titles = {str(item.get("title")) for item in plan.get("plans") or []}
        leaked_titles = sorted(blocked_titles & execution_titles)
        if leaked_titles:
            errors.append("blocked daily plan leaked into rendered execution data: " + ", ".join(leaked_titles))

    binding_contracts = [
        "var recentPlays = findByLabel(radar, '播放量');",
        "var row = findByLabel(radar, k.lookup);",
        "esc(recentPlays.value || '—')",
        "esc(finish.value || '—')",
    ]
    for contract in binding_contracts:
        if contract not in html:
            errors.append(f"HTML is missing current-period display binding: {contract}")
    if "formatWan(trendTotal)" in html:
        errors.append("HTML still maps the sum of recent posts to the current-period playback card")

    report = {
        "verified_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "failed" if errors else "passed",
        "source_date": meta.get("sourceDate"),
        "data_range": meta.get("dataRange"),
        "verified_metrics": expected_metrics,
        "verified_positioning": stable_positioning,
        "verified_strategy": stable_strategy,
        "verified_plan_titles": sorted(execution_titles),
        "html": str(html_path.relative_to(workspace)),
        "errors": errors,
    }
    if args.run_id:
        output = workspace / "runs" / args.run_id / "outputs/dashboard-html-verification.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if errors:
        raise SystemExit("dashboard HTML semantic verification failed:\n- " + "\n- ".join(errors))
    print("dashboard HTML semantic verification passed")
    print(f"source date: {meta.get('sourceDate')}")
    print(f"data range: {meta.get('dataRange')}")
    print("verified: " + ", ".join(f"{key}={value}" for key, value in expected_metrics.items()))


if __name__ == "__main__":
    main()
