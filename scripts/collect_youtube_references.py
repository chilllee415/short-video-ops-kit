#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


PREFERRED_INTENT_KEYWORDS = {
    "business_outcome": [
        "business",
        "businesses",
        "client",
        "clients",
        "customer",
        "customers",
        "revenue",
        "sales",
        "lead",
        "leads",
        "agency",
        "company",
        "companies",
        "teams",
        "enterprise",
        "startup",
        "owner",
    ],
    "workflow_automation": [
        "workflow",
        "workflows",
        "automate",
        "automated",
        "automation",
        "process",
        "system",
        "operations",
        "ops",
        "agent",
        "agents",
        "integrate",
        "integration",
    ],
    "case_study": [
        "case study",
        "real use",
        "real world",
        "real-world",
        "results",
        "raw results",
        "what i found",
        "what businesses want",
        "i built",
        "built",
        "tested",
        "testing",
        "100 hours",
    ],
    "role_scenario": [
        "for creators",
        "for agencies",
        "for marketers",
        "for sales",
        "for teams",
        "for operators",
        "for business",
        "for small business",
        "for entrepreneurs",
    ],
    "comparison_decision": [
        " vs ",
        "versus",
        "which",
        "better",
        "honest",
        "comparison",
        "stop picking",
    ],
}

DEPRIORITIZED_INTENT_KEYWORDS = {
    "tutorial_setup": [
        "tutorial",
        "beginner",
        "beginners",
        "guide",
        "setup",
        "install",
        "course",
        "full course",
        "complete",
        "master",
        "learn",
        "from scratch",
        "ultimate",
    ],
    "provider_sales": [
        "$",
        "ai automation agency",
        "agency niches",
        "sign your first",
        "get clients",
        "client in",
        "selling ai automation",
        "selling ai automations",
        "from $0",
        "make money",
        "side hustle",
        "cold email",
        "outreach",
    ],
}


def run_yt_dlp(args: list[str]) -> list[dict[str, Any]]:
    if not shutil.which("yt-dlp"):
        raise SystemExit("yt-dlp is required. Install it before running YouTube reference mining.")
    proc = subprocess.run(
        ["yt-dlp", "--dump-json", "--ignore-errors", *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    rows: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def video_url(item: dict[str, Any]) -> str:
    if item.get("webpage_url"):
        return str(item["webpage_url"])
    if item.get("url") and str(item["url"]).startswith("http"):
        return str(item["url"])
    if item.get("id"):
        return f"https://www.youtube.com/watch?v={item['id']}"
    return ""


def title_pattern(title: str) -> list[str]:
    lower = title.lower()
    patterns = []
    checks = [
        ("vs / comparison", [" vs ", "versus", "which", "better"]),
        ("beginner guide", ["beginner", "guide", "from scratch", "intro", "setup"]),
        ("full course", ["full course", "complete", "master", "ultimate"]),
        ("time-compressed promise", ["minutes", "hour", "in 7", "in 10", "in 30"]),
        ("honest test", ["honest", "raw results", "testing", "100 hours", "what i found"]),
        ("build demo", ["i built", "build", "same app", "project"]),
        ("worth learning", ["worth", "tools", "need to see", "actually use"])
    ]
    for label, keywords in checks:
        if any(word in lower for word in keywords):
            patterns.append(label)
    return patterns or ["topic keyword"]


def classify_intents(text: str) -> list[str]:
    lower = f" {text.lower()} "
    intents = []
    for label, keywords in PREFERRED_INTENT_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            intents.append(label)
    for label, keywords in DEPRIORITIZED_INTENT_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            intents.append(label)
    return intents or ["topic_keyword"]


def strategy_fit_score(title: str, source_label: str, retrieval_strategy: dict[str, Any]) -> int:
    preferred = retrieval_strategy.get("preferred_intents") or [
        "business_outcome",
        "workflow_automation",
        "case_study",
        "role_scenario",
        "comparison_decision",
    ]
    deprioritized = retrieval_strategy.get("deprioritized_intents") or [
        "tutorial_setup",
        "provider_sales",
    ]
    title_intents = set(classify_intents(title))
    source_intents = set(classify_intents(source_label))
    score = 50

    for intent in preferred:
        if intent in title_intents:
            score += 10
        elif intent in source_intents:
            score += 4

    for intent in deprioritized:
        if intent in title_intents:
            score -= 16
        elif intent in source_intents:
            score -= 6

    if {"business_outcome", "workflow_automation"}.issubset(title_intents | source_intents):
        score += 8
    if {"case_study", "business_outcome"}.issubset(title_intents | source_intents):
        score += 6
    if "tutorial_setup" in title_intents and not ({"business_outcome", "workflow_automation"} & title_intents):
        score -= 10

    return max(0, min(100, score))


def normalize(
    item: dict[str, Any],
    source_type: str,
    source_label: str,
    strategy: dict[str, Any],
    retrieval_strategy: dict[str, Any],
) -> dict[str, Any]:
    title = str(item.get("title") or "")
    intent_text = f"{title} {source_label}"
    return {
        "source_type": source_type,
        "source_label": source_label,
        "title": title,
        "channel": item.get("channel") or item.get("uploader") or "",
        "url": video_url(item),
        "view_count": item.get("view_count") or 0,
        "upload_date": item.get("upload_date") or "",
        "duration_seconds": item.get("duration") or 0,
        "title_patterns": title_pattern(title),
        "content_intents": classify_intents(intent_text),
        "strategy_fit_score": strategy_fit_score(title, source_label, retrieval_strategy),
        "rewrite_lens": strategy.get("rewrite_principle", ""),
        "breakdown_prompt": {
            "why_it_works": "What user anxiety, promise, or decision problem makes this video clickable?",
            "portable_structure": "Which title structure, proof method, or demo sequence can be reused?",
            "do_not_copy": "Which words, footage, screenshots, claims, or creator-specific assets must be avoided?",
            "chinese_rewrite": "How can this become a Chinese short-video topic for the confirmed strategy?",
            "recording_plan": "What original screen recording or workflow demo can verify the rewritten angle?"
        }
    }


def collect_search(
    query: str,
    limit: int,
    strategy: dict[str, Any],
    retrieval_strategy: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = run_yt_dlp([f"ytsearch{limit}:{query}"])
    return [normalize(item, "query", query, strategy, retrieval_strategy) for item in rows]


def collect_channel(
    channel: dict[str, Any],
    limit: int,
    strategy: dict[str, Any],
    retrieval_strategy: dict[str, Any],
) -> list[dict[str, Any]]:
    url = str(channel.get("url") or "")
    if not url:
        return []
    rows = run_yt_dlp(["--flat-playlist", "--playlist-end", str(limit), url])
    label = str(channel.get("name") or url)
    normalized = []
    for item in rows:
        value = normalize(item, "competitor_channel", label, strategy, retrieval_strategy)
        value["channel_reason"] = channel.get("why", "")
        normalized.append(value)
    return normalized


def dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for item in items:
        key = item.get("url") or item.get("title")
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# YouTube Reference Run: {payload.get('run_name', '')}",
        "",
        f"- Generated at: {payload.get('generated_at', '')}",
        f"- Strategy: {payload.get('strategy', {}).get('primary_strategy', '')}",
        f"- Total candidates: {len(payload.get('candidates', []))}",
        "",
        "## Candidates",
        ""
    ]
    for index, item in enumerate(payload.get("candidates", []), start=1):
        patterns = ", ".join(item.get("title_patterns") or [])
        lines.extend([
            f"### {index}. {item.get('title', '')}",
            "",
            f"- Source: {item.get('source_type')} / {item.get('source_label')}",
            f"- Channel: {item.get('channel', '')}",
            f"- Views: {item.get('view_count', 0)}",
            f"- Upload: {item.get('upload_date', '')}",
            f"- URL: {item.get('url', '')}",
            f"- Strategy fit: {item.get('strategy_fit_score', 0)}",
            f"- Title patterns: {patterns}",
            f"- Content intents: {', '.join(item.get('content_intents') or [])}",
            "",
            "拆解待填：",
            "",
            "- 为什么可能有效：",
            "- 可复刻结构：",
            "- 不可直接抄：",
            "- 中文用户场景重写：",
            "- 自己录屏验证：",
            "- 推荐选题：",
            ""
        ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect YouTube reference candidates for short-video topic mining.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    strategy = config.get("strategy") or {}
    retrieval_strategy = config.get("retrieval_strategy") or {}
    limits = config.get("limits") or {}
    per_query = int(limits.get("per_query", 5))
    per_channel = int(limits.get("per_channel", 8))
    min_views = int(limits.get("min_views", 0))

    items: list[dict[str, Any]] = []
    for query in config.get("topic_queries", []) + config.get("strategy_queries", []):
        items.extend(collect_search(str(query), per_query, strategy, retrieval_strategy))
    for channel in config.get("competitor_channels", []):
        if isinstance(channel, dict):
            items.extend(collect_channel(channel, per_channel, strategy, retrieval_strategy))

    candidates = [item for item in dedupe(items) if int(item.get("view_count") or 0) >= min_views]
    sort_mode = str(retrieval_strategy.get("sort") or "strategy_fit_then_views")
    if sort_mode == "views":
        candidates.sort(key=lambda item: int(item.get("view_count") or 0), reverse=True)
    else:
        candidates.sort(
            key=lambda item: (
                int(item.get("strategy_fit_score") or 0),
                int(item.get("view_count") or 0),
            ),
            reverse=True,
        )

    payload = {
        "run_name": config.get("run_name", "youtube-reference-run"),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "strategy": strategy,
        "retrieval_strategy": retrieval_strategy,
        "official_sources": config.get("official_sources", []),
        "candidates": candidates,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.markdown:
        write_markdown(args.markdown, payload)
    print(f"wrote {args.out}")
    if args.markdown:
        print(f"wrote {args.markdown}")


if __name__ == "__main__":
    main()
