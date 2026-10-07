#!/usr/bin/env python3
"""Merge Codex-authored findings into a model-ready analysis input."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--findings", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    analysis = json.loads(args.input.read_text(encoding="utf-8"))
    findings = json.loads(args.findings.read_text(encoding="utf-8"))
    comment_ids = {str(comment.get("commentId", "")) for comment in analysis.get("comments", [])}
    invalid_evidence = []
    for collection in ("viewpoints", "opportunities"):
        for item in findings.get(collection, []):
            for comment_id in item.get("evidenceCommentIds", []):
                if str(comment_id) not in comment_ids:
                    invalid_evidence.append(f"{collection}:{item.get('id', '')}:{comment_id}")
    if invalid_evidence:
        raise SystemExit("发现不存在的证据评论 ID：" + ", ".join(invalid_evidence))
    analysis.update(findings)
    analysis["secUserId"] = analysis.get("profile", {}).get("secUserId", "")
    analysis["updatedAt"] = analysis.get("run", {}).get("completedAt") or analysis.get("updatedAt") or datetime.now(timezone.utc).isoformat()
    analysis.setdefault("metrics", {})["comments"] = len(analysis.get("comments", []))
    analysis["commentCount"] = len(analysis.get("comments", []))

    viewpoint_by_comment = {}
    for viewpoint in analysis.get("viewpoints", []):
        for comment_id in viewpoint.get("evidenceCommentIds", []):
            viewpoint_by_comment.setdefault(str(comment_id), viewpoint.get("id", ""))
    opportunity_by_comment = {}
    for opportunity in analysis.get("opportunities", []):
        for comment_id in opportunity.get("evidenceCommentIds", []):
            opportunity_by_comment.setdefault(str(comment_id), opportunity.get("id", ""))

    for comment in analysis.get("comments", []):
        comment_id = str(comment.get("commentId", ""))
        comment["viewpointId"] = viewpoint_by_comment.get(comment_id, "")
        comment["opportunityId"] = opportunity_by_comment.get(comment_id, "")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "comments": len(analysis.get("comments", []))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
