#!/usr/bin/env python3
"""Remove current topic and selection records whose evidence lineage no longer resolves."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def write_object(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    workspace = args.workspace.expanduser().resolve()
    lane_paths = [
        workspace / "work/topics/conservative/current.json",
        workspace / "work/topics/experimental/current.json",
    ]
    selected_path = workspace / "work/topics/selections/daily.json"
    selected = load_object(selected_path)
    pain_bank = load_object(workspace / "data/topic-research/current/pain-bank.json")
    reference_bank = load_object(workspace / "data/benchmarks/current/reference-bank.json")
    strategy = load_object(workspace / "config/strategy/strategy-brief.json")

    pain_ids = {str(item.get("pain_id")) for item in pain_bank.get("pains") or [] if item.get("pain_id")}
    reference_ids = {
        str(item.get("reference_id")) for item in reference_bank.get("references") or [] if item.get("reference_id")
    }
    strategy_id = str(strategy.get("strategy_id") or "")
    removed: list[dict[str, Any]] = []
    kept_ids: set[str] = set()
    cleaned_at = datetime.now().astimezone().isoformat(timespec="seconds")
    for lane_path in lane_paths:
        lane = load_object(lane_path)
        kept: list[dict[str, Any]] = []
        for topic in lane.get("topics") or []:
            reasons: list[str] = []
            pain_id = str(topic.get("pain_id") or "")
            if pain_id and pain_ids and pain_id not in pain_ids:
                reasons.append("missing_pain_id")
            if strategy_id and str(topic.get("strategy_id") or "") != strategy_id:
                reasons.append("strategy_id_mismatch")
            missing_refs = [str(ref) for ref in topic.get("reference_ids") or [] if str(ref) not in reference_ids]
            if missing_refs:
                reasons.append("missing_reference_ids:" + ",".join(missing_refs))
            if not (topic.get("reference_ids") or topic.get("evidence_ids") or topic.get("signal_ids")):
                reasons.append("missing_evidence_lineage")
            if reasons:
                removed.append({"lane": lane.get("lane"), "topic": topic, "reasons": reasons})
            else:
                kept.append(topic)
                if topic.get("topic_id"):
                    kept_ids.add(str(topic["topic_id"]))
        lane["topics"] = kept
        lane["status"] = "cleaned_broken_lineage"
        lane["generated_at"] = cleaned_at
        lane["blockers"] = list(lane.get("blockers") or [])
        write_object(lane_path, lane)

    removed_selected = [item for item in selected.get("selected") or [] if str(item.get("topic_id")) not in kept_ids]
    selected["selected"] = [item for item in selected.get("selected") or [] if str(item.get("topic_id")) in kept_ids]
    selected["status"] = "cleaned_broken_lineage"
    selected["generated_at"] = cleaned_at
    write_object(selected_path, selected)

    archive = {
        "workflow_id": "topic-lineage-cleanup",
        "run_id": args.run_id,
        "cleaned_at": cleaned_at,
        "removed_topics": removed,
        "removed_selected": removed_selected,
        "remaining_topic_ids": sorted(kept_ids),
    }
    output = workspace / "runs" / args.run_id / "outputs/topic-lineage-cleanup.json"
    write_object(output, archive)
    print(f"removed topics: {len(removed)}")
    print(f"removed selected entries: {len(removed_selected)}")
    print(f"remaining topics: {len(kept)}")
    print(f"archive: {output}")


if __name__ == "__main__":
    main()
