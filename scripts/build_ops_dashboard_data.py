#!/usr/bin/env python3
"""Build ops-dashboard.json from the current user-data workspace."""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from statistics import mean
from typing import Any


REQUIRED_TOP_LEVEL_KEYS = ("account", "demand", "execution", "benchmark")
SOURCE_SPECS = {
    "account": ("data/operations/current/account-snapshot.json", 1),
    "post_metrics": ("data/feedback/raw/post-metrics.json", 1),
    "feedback": ("data/feedback/current/learning.json", 1),
    "demand_conservative": ("work/topics/conservative/current.json", 7),
    "demand_experimental": ("work/topics/experimental/current.json", 7),
    "topic_selection": ("work/topics/selections/daily.json", 1),
    "pain_bank": ("data/topic-research/current/pain-bank.json", 10),
    "daily_scene": ("work/topics/daily-scenes.json", 1),
    "benchmark": ("data/benchmarks/current/reference-bank.json", 3),
    "strategy": ("config/strategy/strategy-brief.json", 45),
    "strategy_assessment": ("data/topic-research/current/strategy-assessment.json", 1),
    "publishing": ("work/plans/publishing.json", 7),
    "daily_plan": ("work/plans/daily.json", 1),
    "daily_signals": ("data/topic-research/current/topic-signals.json", 1),
}
PLATFORM_INFO = {
    "dy": {"label": "抖音评论", "color": "#69e0d0", "icon": "douyin"},
    "douyin": {"label": "抖音", "color": "#69e0d0", "icon": "douyin"},
    "douyin_internal": {"label": "内部抖音", "color": "#69e0d0", "icon": "douyin"},
    "xhs": {"label": "小红书", "color": "#b490ff", "icon": "xhs"},
    "zhihu": {"label": "知乎", "color": "#7fb0ff", "icon": "zhihu"},
    "weibo": {"label": "微博", "color": "#ffb86b", "icon": "weibo"},
    "bili": {"label": "B站", "color": "#ff7aa8", "icon": "bili"},
    "bilibili": {"label": "B站", "color": "#ff7aa8", "icon": "bili"},
    "youtube": {"label": "YouTube", "color": "#7fb0ff", "icon": "youtube"},
    "script_archive": {"label": "脚本库", "color": "#63d9a0", "icon": "database"},
    "sync": {"label": "脚本库", "color": "#63d9a0", "icon": "database"},
}


def default_workspace() -> Path:
    env = os.environ.get("SHORT_VIDEO_OPS_WORKSPACE")
    if env:
        return Path(env).expanduser().resolve()
    raise SystemExit(
        "workspace is required. Pass it as an argument or set SHORT_VIDEO_OPS_WORKSPACE."
    )


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def percent(value: Any, digits: int = 2) -> str:
    if value is None:
        return ""
    n = float(value)
    if abs(n) <= 1:
        n *= 100
    text = f"{n:.{digits}f}".rstrip("0").rstrip(".")
    return f"{text}%"


def number_text(value: Any) -> str:
    if value is None:
        return ""
    n = float(value)
    if n >= 10000:
        text = f"{n / 10000:.2f}".rstrip("0").rstrip(".")
        return f"{text}万"
    if n.is_integer():
        return str(int(n))
    return f"{n:.1f}".rstrip("0").rstrip(".")


def parse_day(value: str | None) -> date | None:
    if not value:
        return None
    value = str(value)
    if re.fullmatch(r"\d{8}", value):
        return date.fromisoformat(f"{value[:4]}-{value[4:6]}-{value[6:8]}")
    return date.fromisoformat(value[:10])


def format_period(period: dict[str, Any]) -> str:
    start = period.get("start")
    end = period.get("end")
    if start and end:
        return f"{start} 至 {end}"
    return ""


def compact_title(title: str) -> str:
    return re.sub(r"\s+", " ", title or "").strip()


def compact_text(value: Any, limit: int = 80) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def first_text(*values: Any) -> str:
    for value in values:
        text = compact_text(value, 0)
        if text:
            return text
    return ""


def unique(values: list[Any], limit: int | None = None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = compact_text(value, 0)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
        if limit and len(result) >= limit:
            break
    return result


def parse_metric(metric_text: Any, key: str) -> int:
    text = str(metric_text or "")
    match = re.search(rf"{re.escape(key)}\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*([万wk]?)", text, re.I)
    if not match:
        return 0
    value = float(match.group(1))
    suffix = match.group(2).lower()
    if suffix in ("万", "w"):
        value *= 10000
    elif suffix == "k":
        value *= 1000
    return int(round(value))


def normalize_day(value: Any) -> str:
    if not value:
        return ""
    text = str(value)
    try:
        return parse_day(text).isoformat()
    except (ValueError, TypeError):
        return ""


def data_date(data: dict[str, Any], *keys: str) -> str:
    for key in keys:
        current: Any = data
        for part in key.split("."):
            if not isinstance(current, dict):
                current = None
                break
            current = current.get(part)
        day = normalize_day(current)
        if day:
            return day
    return ""


def age_days(day_text: str) -> int | None:
    day = normalize_day(day_text)
    if not day:
        return None
    return max(0, (date.today() - parse_day(day)).days)  # type: ignore[arg-type]


def freshness_state(day_text: str, max_age_days: int, exists: bool) -> str:
    if not exists:
        return "missing"
    age = age_days(day_text)
    if age is None:
        return "unknown"
    if age <= max_age_days:
        return "fresh"
    if age <= max_age_days * 2 + 1:
        return "aging"
    return "stale"


def source_record(
    workspace: Path,
    rel: str,
    data: dict[str, Any],
    date_value: str,
    max_age_days: int,
    fallback_used: bool = False,
) -> dict[str, Any]:
    path = workspace / rel
    updated = normalize_day(date_value)
    state = freshness_state(updated, max_age_days, path.exists())
    return {
        "path": rel,
        "exists": path.exists(),
        "updatedAt": updated,
        "ageDays": age_days(updated),
        "state": state,
        "fallbackUsed": fallback_used,
    }


def heat_from_score(score: dict[str, Any] | None, fallback: int) -> int:
    if not score:
        return fallback
    values = [float(v) for v in score.values() if isinstance(v, (int, float))]
    if not values:
        return fallback
    average = mean(values)
    normalized = average * 20 if average <= 5 else average
    return max(0, min(100, round(normalized)))


def action_label(topic: dict[str, Any], existing: dict[str, Any]) -> str:
    tags = existing.get("matchTags") or []
    if len(tags) >= 3:
        return tags[2]
    title = topic.get("title", "")
    visible = topic.get("visible_result", "")
    text = title + visible
    if "报价" in text or "brief" in text:
        return "商业承接"
    if "评价" in text or "评论" in text:
        return "结果前置"
    if "日历" in text or "选题" in text:
        return "选题系统"
    if "线索" in text or "诊断" in text:
        return "诊断入口"
    return "可复用"


def default_platforms(topic: dict[str, Any]) -> dict[str, int]:
    text = topic.get("title", "") + topic.get("target_role", "")
    if "电商" in text or "评价" in text:
        return {"dy": 40, "xhs": 25, "bili": 20, "zhihu": 10, "weibo": 5}
    if "报价" in text or "老板" in text:
        return {"dy": 35, "xhs": 18, "zhihu": 22, "weibo": 15, "bili": 10}
    if "知识" in text or "日历" in text:
        return {"dy": 42, "xhs": 20, "bili": 18, "zhihu": 15, "weibo": 5}
    return {"dy": 50, "xhs": 28, "zhihu": 12, "weibo": 6, "bili": 4}


def build_quotes(pain: dict[str, Any], existing: dict[str, Any]) -> list[dict[str, str]]:
    words = pain.get("user_words") or []
    if not words:
        return copy.deepcopy(existing.get("quotes") or [])
    platforms = ["xhs", "dy", "bili"]
    return [
        {"platform": platforms[i % len(platforms)], "text": text, "url": "#"}
        for i, text in enumerate(words[:3])
    ]


def platform_label(platform: str) -> str:
    return PLATFORM_INFO.get(platform, {}).get("label", platform or "素材")


def platform_key(platform: str) -> str:
    if platform in {"douyin", "douyin-creator-analytics"}:
        return "dy"
    if platform == "bilibili":
        return "bili"
    if platform == "xiaohongshu":
        return "xhs"
    return platform or "script_archive"


def signal_metric_summary(signal: dict[str, Any]) -> str:
    platform = str(signal.get("platform") or "")
    metric = signal.get("metric") or {}
    role = str(signal.get("evidence_role") or "")
    labels = {
        "xiaohongshu": "小红书",
        "bilibili": "B站",
        "reddit": "Reddit",
        "x": "X",
        "douyin-creator-analytics": "抖音后台",
    }
    label = labels.get(platform, platform_label(platform_key(platform)))

    if metric.get("editor_likes") is not None:
        parts = [f"{label} {number_text(metric['editor_likes'])}赞"]
        if metric.get("editor_collects") is not None:
            parts.append(f"{number_text(metric['editor_collects'])}藏")
        return " · ".join(parts)
    if metric.get("representative_likes") is not None:
        samples = metric.get("recent_samples")
        prefix = f"{label} {number_text(samples)}条样本" if samples is not None else label
        return f"{prefix} · 最高{number_text(metric['representative_likes'])}赞"
    if metric.get("views") is not None:
        view_unit = "浏览" if platform == "x" else "播放"
        parts = [f"{label} {number_text(metric['views'])}{view_unit}"]
        if metric.get("likes") is not None:
            parts.append(f"{number_text(metric['likes'])}赞")
        return " · ".join(parts)
    if metric.get("comments") is not None:
        return f"{label} {number_text(metric['comments'])}条讨论"
    if metric.get("likes") is not None:
        suffix = " · 明确付费需求" if role == "market_task" else ""
        return f"{label} {number_text(metric['likes'])}赞{suffix}"
    return ""


def build_topic_evidence_summary(
    topic: dict[str, Any], signals: dict[str, Any]
) -> list[str]:
    signal_by_id = {
        str(item.get("signal_id")): item
        for item in signals.get("signals") or []
        if item.get("signal_id")
    }
    summaries: list[str] = []
    used_platforms: set[str] = set()
    for signal_id in topic.get("signal_ids") or topic.get("evidence_ids") or []:
        signal = signal_by_id.get(str(signal_id))
        if not signal:
            continue
        key = platform_key(str(signal.get("platform") or ""))
        if key in used_platforms:
            continue
        summary = signal_metric_summary(signal)
        if not summary:
            continue
        summaries.append(summary)
        used_platforms.add(key)
        if len(summaries) == 2:
            break
    return summaries


def source_mix_from_signals(signals: dict[str, Any]) -> list[dict[str, Any]]:
    totals: Counter[str] = Counter()
    for signal in signals.get("signals") or []:
        key = platform_key(str(signal.get("platform") or ""))
        if key in PLATFORM_INFO:
            totals[key] += 1
    if not totals:
        return []
    total = sum(totals.values())
    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    result = []
    for key, value in ranked:
        info = PLATFORM_INFO[key]
        result.append(
            {
                "key": key,
                "label": "抖音账号数据" if key == "dy" else info["label"],
                "value": round(value / total * 100),
                "count": value,
                "icon": info["icon"],
                "color": info["color"],
            }
        )
    diff = 100 - sum(item["value"] for item in result)
    result[0]["value"] += diff
    return result


def aggregate_source_mix(topics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    totals: Counter[str] = Counter()
    for topic in topics:
        platforms = topic.get("platforms") or {}
        for key, value in platforms.items():
            if key not in PLATFORM_INFO:
                continue
            totals[platform_key(key)] += int(value or 0)

    if not totals:
        totals.update({"dy": 50, "xhs": 28, "zhihu": 12, "bili": 4, "sync": 6})
    if totals and "sync" not in totals:
        totals["sync"] = max(4, round(sum(totals.values()) * 0.06))

    total = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:5]
    mix = []
    for key, value in ranked:
        info = PLATFORM_INFO.get(key, PLATFORM_INFO["sync"])
        percent_value = max(1, round(value / total * 100))
        mix.append(
            {
                "key": key,
                "label": info["label"],
                "value": percent_value,
                "icon": info["icon"],
                "color": info["color"],
            }
        )

    diff = 100 - sum(item["value"] for item in mix)
    if mix:
        mix[0]["value"] += diff
    return mix


def cluster_keywords(topics: list[dict[str, Any]]) -> str:
    words = ["报价", "评价", "日历", "咨询", "选题", "工作流", "诊断", "复盘", "素材"]
    found: list[str] = []
    text = " ".join(str(t.get("title", "")) + " " + str(t.get("painSummary", "")) for t in topics[:6])
    for word in words:
        if word in text:
            found.append(word)
    return " / ".join(found[:3] or ["评价", "报价", "诊断"])


def dashboard_axis_values(topics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not topics:
        return [
            {"label": "机会强度", "value": 86},
            {"label": "传播潜力", "value": 82},
            {"label": "成交关联", "value": 80},
            {"label": "评论密度", "value": 76},
            {"label": "复用价值", "value": 78},
        ]
    def average_score(key: str, fallback: int) -> int:
        values = [
            float((topic.get("scoreDetail") or {}).get(key))
            for topic in topics
            if (topic.get("scoreDetail") or {}).get(key) is not None
        ]
        return round(mean(values)) if values else fallback

    return [
        {"label": "选题痛感", "value": average_score("pain", 0)},
        {"label": "发生频率", "value": average_score("frequency", 0)},
        {"label": "演示性", "value": average_score("demo", 0)},
        {"label": "成交关联", "value": average_score("payment", 0)},
        {"label": "证据质量", "value": average_score("evidence_quality", 0)},
    ]


def topic_action(topic: dict[str, Any]) -> str:
    tags = topic.get("matchTags") or []
    if len(tags) >= 3:
        return str(tags[2])
    return "结果前置"


def build_demand_insights(
    topics: list[dict[str, Any]],
    source_mix: list[dict[str, Any]],
    feedback: dict[str, Any],
) -> list[dict[str, str]]:
    top_source = source_mix[0] if source_mix else {"label": "抖音评论", "value": 50}
    effective = feedback.get("effective_hooks") or []
    return [
        {
            "label": "主信号源",
            "value": f"{top_source['label']} {top_source['value']}%",
            "note": "真实用户语言密度最高",
        },
        {
            "label": "高潜方向",
            "value": cluster_keywords(topics),
            "note": "适合做可见结果演示",
        },
        {
            "label": "转化判断",
            "value": topic_action(topics[0]) if topics else "先抓咨询入口",
            "note": compact_text(effective[0] if effective else "先给结果，再补方法论内容", 24),
        },
    ]


def topic_from_daily_scene(source: dict[str, Any]) -> dict[str, Any]:
    score = source.get("score") or {}
    if isinstance(score, dict):
        heat = heat_from_score(score, 86)
    else:
        heat = int(score or 86)
    return {
        "topic_id": source.get("topic_id") or source.get("id"),
        "pain_id": source.get("pain_id"),
        "priority": source.get("priority"),
        "title": source.get("title") or source.get("hook"),
        "target_role": source.get("target_role") or source.get("role"),
        "scene": source.get("scene"),
        "visible_result": source.get("visible_result"),
        "recording_plan_ref": source.get("recording_plan_ref"),
        "cta": source.get("cta"),
        "video_angle": source.get("video_angle"),
        "score": {"daily_scene": max(1, round(heat / 20))},
    }


def pain_topic_title(pain_id: str, pain_by_id: dict[str, dict[str, Any]]) -> str:
    pain = pain_by_id.get(pain_id) or {}
    if pain.get("visible_result"):
        return compact_text(pain["visible_result"], 18)
    scene = pain.get("business_scene") or pain.get("target_role") or pain_id
    return compact_text(scene, 18)


def normalize_reference_date(value: Any) -> str:
    day = normalize_day(value)
    if day:
        return day
    return "1970-01-01"


def structure_steps_from_text(values: list[Any]) -> list[dict[str, Any]]:
    times = ["0-3s", "3-12s", "12-22s", "22-30s"]
    fallback = [
        "结果前置：先把结果亮出来，不要先解释背景",
        "场景输入：交代用户原本卡在哪里",
        "过程证明：用录屏/文件/表格证明不是空讲",
        "评论承接：用一个关键词接住高意向用户",
    ]
    raw = unique(values, 4) or fallback
    while len(raw) < 4:
        raw.append(fallback[len(raw)])
    steps = []
    for index, value in enumerate(raw[:4]):
        name, sep, desc = value.partition("：")
        if not sep:
            name, desc = value, value
        steps.append(
            {
                "time": times[index],
                "name": compact_text(name, 12),
                "desc": compact_text(desc, 46),
                "hot": index == 0,
            }
        )
    return steps


def reference_visual_tricks(ref: dict[str, Any]) -> list[str]:
    raw = list(ref.get("usable_for") or []) + list(ref.get("content_intents") or [])
    mapping = {
        "hook": "钩子结构",
        "proof pattern": "证明画面",
        "structure reference": "结构节奏",
        "workflow explanation": "流程节点",
        "rewrite strategy": "改写策略",
        "direct_result_demo": "结果前置",
        "workflow_automation": "录屏推进",
        "creator_ops": "运营场景",
    }
    return unique([mapping.get(str(item), str(item)) for item in raw], 4) or ["结果前置", "录屏推进", "评论承接"]


def build_reference_detail(
    ref: dict[str, Any],
    existing: dict[str, Any],
    pain_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    existing_detail = copy.deepcopy(existing.get("detail") or {})
    explicit = copy.deepcopy(ref.get("dashboard_detail") or ref.get("detail") or {})
    if explicit:
        existing_detail.update(explicit)

    deconstruction = ref.get("strategy_deconstruction") or {}
    structure_source = explicit.get("structure") or deconstruction.get("structure") or []
    if structure_source and isinstance(structure_source[0], dict):
        structure = structure_source[:4]
    else:
        structure = structure_steps_from_text(list(structure_source))

    pain_id = str((ref.get("mapped_pain_ids") or [""])[0] or "")
    pain = pain_by_id.get(pain_id) or {}
    hook_types = deconstruction.get("hook_types") or ref.get("title_patterns") or ref.get("usable_for") or []
    hook_formula = first_text(explicit.get("hookFormula"), " + ".join(unique(hook_types, 2)), "结果前置 + 结构复用")
    proof_assets = deconstruction.get("proof_assets") or []
    why_works = unique(
        [
            ref.get("rewrite_notes"),
            deconstruction.get("hook_reason"),
            *(proof_assets[:1] if isinstance(proof_assets, list) else []),
            "只借结构和证明方式，不照搬原句和画面。",
        ],
        3,
    )
    cta = first_text(pain.get("convertible_offer"), "想看完整流程，评论关键词。")
    visible_result = first_text(pain.get("visible_result"), "把一个重复动作跑成可见结果。")
    scene = first_text(pain.get("business_scene"), ref.get("title"))
    rewrite = {
        "hook": compact_text(existing_detail.get("rewrite", {}).get("hook") or f"先别讲方法，先展示：{visible_result}", 70),
        "script": existing_detail.get("rewrite", {}).get("script")
        or f"前 3 秒亮出结果：{visible_result}\n中段用真实场景说明：{scene}\n最后只留一个动作：让用户用关键词进入诊断。",
        "cta": existing_detail.get("rewrite", {}).get("cta") or cta,
    }
    return {
        "url": first_text(explicit.get("url"), ref.get("url"), existing_detail.get("url")),
        "structure": structure,
        "hookFormula": hook_formula,
        "visualTricks": unique(existing_detail.get("visualTricks", []) + reference_visual_tricks(ref), 4),
        "whyWorks": why_works,
        "rewrite": rewrite,
    }


def benchmark_item_from_reference(
    ref: dict[str, Any],
    existing: dict[str, Any],
    pain_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    ref_id = str(ref.get("reference_id") or existing.get("id") or compact_text(ref.get("title"), 18))
    platform = platform_key(str(ref.get("platform") or existing.get("platform") or "script_archive"))
    pain_id = str((ref.get("mapped_pain_ids") or [existing.get("topicId") or ""])[0] or "")
    return {
        "id": ref_id,
        "platform": platform,
        "platformLabel": platform_label(platform),
        "creator": ref.get("creator") or existing.get("creator") or "workspace-owner",
        "title": compact_text(ref.get("title") or existing.get("title"), 90),
        "views": parse_metric(ref.get("observed_metric"), "views") or int(existing.get("views") or 0),
        "likes": parse_metric(ref.get("observed_metric"), "likes") or int(existing.get("likes") or 0),
        "topicId": pain_id,
        "topicTitle": pain_topic_title(pain_id, pain_by_id),
        "matchScore": int(ref.get("strategy_fit_score") or existing.get("matchScore") or 82),
        "date": normalize_reference_date(ref.get("upload_date") or ref.get("ingested_at") or existing.get("date")),
        "sourceRunId": ref.get("deconstruction_run_id") or ref.get("source_run_id") or "",
        "detail": build_reference_detail(ref, existing, pain_by_id),
    }


def build_source_status(workspace: Path) -> dict[str, dict[str, Any]]:
    data_cache = {
        key: read_json(workspace / rel, {})
        for key, (rel, _max_age) in SOURCE_SPECS.items()
    }
    date_keys = {
        "account": data_date(data_cache["account"], "period.end", "updated_at"),
        "post_metrics": data_date(data_cache["post_metrics"], "updated_at", "period.end"),
        "feedback": data_date(data_cache["feedback"], "period.end", "updated_at"),
        "demand_conservative": data_date(data_cache["demand_conservative"], "generated_at"),
        "demand_experimental": data_date(data_cache["demand_experimental"], "generated_at", "expires_at"),
        "topic_selection": data_date(data_cache["topic_selection"], "selection_date"),
        "pain_bank": data_date(data_cache["pain_bank"], "updated_at"),
        "daily_scene": data_date(data_cache["daily_scene"], "generated_at", "date_range"),
        "benchmark": data_date(data_cache["benchmark"], "updated_at"),
        "strategy": data_date(data_cache["strategy"], "updated_at", "confirmed_at"),
        "strategy_assessment": data_date(data_cache["strategy_assessment"], "run_date", "generated_at"),
        "publishing": data_date(data_cache["publishing"], "updated_at"),
    }
    status = {}
    for key, (rel, max_age) in SOURCE_SPECS.items():
        status[key] = source_record(workspace, rel, data_cache[key], date_keys.get(key, ""), max_age)
    return status


def build_account(base: dict[str, Any], workspace: Path) -> dict[str, Any]:
    account = copy.deepcopy(base.get("account") or {})
    snapshot = read_json(workspace / "data/operations/current/account-snapshot.json", {})
    post_metrics = read_json(workspace / "data/feedback/raw/post-metrics.json", {})
    account_profile = read_json(workspace / "config/profile/account.profile.json", {})
    strategy = read_json(workspace / "config/strategy/strategy-brief.json", {})
    strategy_assessment = read_json(workspace / "data/topic-research/current/strategy-assessment.json", {})

    period = snapshot.get("period") or {}
    metrics_summary = snapshot.get("metrics_summary") or {}
    recent = (metrics_summary.get("recent_window") or {}).get("recent_metrics") or {}
    content = metrics_summary.get("content_summary") or {}

    if period.get("end"):
        account["source"] = f"Douyin Creator Center · {period['end']}"
        account["diagnosisPeriod"] = format_period(period)
        account["overviewPeriod"] = format_period(period)
    positioning = str(account_profile.get("positioning") or "")
    positioning_label = positioning.rsplit("/", 1)[-1].strip() if positioning else "账号定位待确认"
    account["headline"] = positioning_label
    account["positioning"] = positioning
    account["stableStrategy"] = strategy.get("primary_strategy") or ""
    account["conversionPath"] = strategy.get("conversion_path") or ""
    decision_labels = {
        "continue_current": "保持当前策略",
        "optimize_execution": "方向成立，优化执行",
        "run_validation_experiment": "证据不足，先做验证",
        "propose_strategy_adjustment": "建议调整内容策略",
    }
    account["strategyHealthLabel"] = decision_labels.get(
        strategy_assessment.get("decision"), "策略待评估"
    )
    account["strategyHealthConclusion"] = strategy_assessment.get("conclusion") or ""
    account["strategyHealthConfidence"] = strategy_assessment.get("confidence") or ""
    account["diagnosedStage"] = snapshot.get("account_stage") or ""
    if snapshot.get("main_bottleneck"):
        account["summary"] = snapshot["main_bottleneck"]

    tags = []
    if recent.get("plays_display"):
        tags.append(f"近7日播放 {recent['plays_display']}")
    if recent.get("net_followers") is not None:
        tags.append(f"净增粉 {recent['net_followers']}")
    if recent.get("profile_visits") is not None:
        tags.append(f"主页访问 {recent['profile_visits']}")
    tags.append(account["strategyHealthLabel"])
    account["tags"] = tags[:4]

    watch_seconds = number_text(content.get("avg_watch_seconds"))
    overview = [
        {"label": "周期内投稿量", "value": number_text(content.get("export_post_count")), "note": "发布密度", "hot": True},
        {"label": "条均点击率", "value": percent(content.get("avg_cover_click_rate")), "note": "封面/标题"},
        {"label": "条均5s完播", "value": percent(content.get("avg_five_second_completion_rate")), "note": "前段承接"},
        {"label": "条均2s跳出", "value": percent(content.get("avg_two_second_bounce_rate")), "note": "首屏流失", "hot": True},
        {"label": "条均播放时长", "value": f"{watch_seconds}秒" if watch_seconds else "", "note": "内容密度"},
        {"label": "播放中位数", "value": number_text(content.get("median_plays")), "note": "稳定基线"},
        {"label": "条均点赞", "value": number_text(content.get("avg_likes")), "note": "公开认同"},
        {"label": "条均评论", "value": number_text(content.get("avg_comments")), "note": "需求表达"},
        {"label": "条均分享", "value": number_text(content.get("avg_shares")), "note": "外扩传播"},
    ]
    account["overview"] = [row for row in overview if row["value"]]

    posts = post_metrics.get("posts") or []
    public_posts = [
        p for p in posts
        if p.get("visibility") == "公开" and (p.get("metrics") or {}).get("plays", 0) > 0
    ]
    public_posts.sort(key=lambda p: p.get("publish_time") or "")
    if public_posts:
        account["playTrend"] = [
            {
                "date": (p.get("publish_time") or "")[5:10],
                "views": int((p.get("metrics") or {}).get("plays") or 0),
            }
            for p in public_posts[-7:]
        ]
        account["lossTrend"] = [
            {
                "date": (p.get("publish_time") or "")[5:10],
                "value": round(float((p.get("metrics") or {}).get("bounce_2s_rate") or 0) * 100, 2),
            }
            for p in public_posts[-7:]
            if (p.get("metrics") or {}).get("bounce_2s_rate") is not None
        ]

    start = parse_day(period.get("start"))
    end = parse_day(period.get("end"))
    recent_posts = []
    if start and end:
        for post in public_posts:
            day = parse_day(post.get("publish_time"))
            if day and start <= day <= end:
                recent_posts.append(post)

    completion_rates = [
        (p.get("metrics") or {}).get("completion_rate")
        for p in public_posts
        if (p.get("metrics") or {}).get("completion_rate") is not None
    ]
    avg_completion = recent.get("completion_rate")
    if avg_completion is None:
        avg_completion = mean(completion_rates) if completion_rates else None
    plays_display = recent.get("plays_display") or number_text(sum((p.get("metrics") or {}).get("plays", 0) for p in recent_posts))
    engagement = recent.get("interaction_index")
    plays_number = sum((p.get("metrics") or {}).get("plays", 0) for p in recent_posts)
    if engagement is None and plays_number:
        engagement = (recent.get("likes", 0) + recent.get("comments", 0) + recent.get("shares", 0)) / plays_number

    post_count = int(recent.get("posts") if recent.get("posts") is not None else len(recent_posts))
    has_performance_data = bool(
        public_posts
        or any(value is not None for value in recent.values())
        or any(value is not None for value in content.values())
    )
    if has_performance_data:
        account["radar"] = [
            {"label": "投稿活跃度", "value": f"{post_count}条", "peer": "按近7日公开投稿估算", "score": 15 if post_count == 0 else min(80, 20 + post_count * 15), "baseline": 64, "low": post_count <= 1},
            {"label": "播放量", "value": plays_display, "peer": "近7日滚动窗口", "score": 92, "baseline": 58},
            {"label": "完播率", "value": percent(avg_completion), "peer": "公开视频均值", "score": 42 if avg_completion and avg_completion < 0.08 else 58, "baseline": 59, "low": True},
            {"label": "互动指数", "value": percent(engagement), "peer": "赞评分享 / 近7日播放", "score": 88 if engagement and engagement > 0.03 else 62, "baseline": 52},
            {"label": "粉丝净增", "value": number_text(recent.get("net_followers")), "peer": "近7日滚动窗口", "score": 94, "baseline": 50},
        ]
        account["score"] = round(mean([row["score"] for row in account["radar"]]))
    else:
        account["radar"] = []
        account["score"] = None
        account["playTrend"] = []
        account["lossTrend"] = []

    return account


def build_demand(base: dict[str, Any], workspace: Path) -> dict[str, Any]:
    demand = copy.deepcopy(base.get("demand") or {})
    conservative = read_json(workspace / "work/topics/conservative/current.json", {})
    experimental = read_json(workspace / "work/topics/experimental/current.json", {})
    selection = read_json(workspace / "work/topics/selections/daily.json", {})
    pain_bank = read_json(workspace / "data/topic-research/current/pain-bank.json", {})
    feedback = read_json(workspace / "data/feedback/current/learning.json", {})
    daily_scene = read_json(workspace / "work/topics/daily-scenes.json", {})
    daily_signals = read_json(workspace / "data/topic-research/current/topic-signals.json", {})
    existing_by_id = {
        topic.get("id"): topic
        for topic in demand.get("topics", [])
        if topic.get("id")
    }
    pain_by_id = {
        pain.get("pain_id"): pain
        for pain in pain_bank.get("pains", [])
        if pain.get("pain_id")
    }

    topics = []
    candidates_by_id: dict[str, dict[str, Any]] = {}
    source_topics: list[dict[str, Any]] = []
    for lane_name, lane in (("conservative", conservative), ("experimental", experimental)):
        if lane.get("status") == "blocked":
            continue
        for raw_topic in lane.get("topics") or []:
            if not raw_topic.get("topic_id"):
                continue
            topic = copy.deepcopy(raw_topic)
            topic["_lane"] = lane_name
            candidates_by_id[str(topic["topic_id"])] = topic
            source_topics.append(topic)
    selected_ids = [
        str(item.get("topic_id"))
        for item in selection.get("selected") or []
        if item.get("topic_id")
    ]
    if not source_topics and daily_scene.get("topics"):
        source_topics = [topic_from_daily_scene(item) for item in daily_scene.get("topics", [])]

    for source in source_topics:
        topic_id = source.get("topic_id") or source.get("id")
        if not topic_id:
            continue
        existing = copy.deepcopy(existing_by_id.get(topic_id) or {})
        pain = pain_by_id.get(source.get("pain_id")) or {}
        priority = source.get("priority") or (existing.get("matchTags") or ["A"])[0][:1]
        visible_result = source.get("visible_result") or pain.get("visible_result") or ""
        scene = source.get("scene") or pain.get("business_scene") or ""
        cta = source.get("cta") or pain.get("convertible_offer") or ""

        topic = existing
        topic["id"] = topic_id
        topic["lane"] = source.get("_lane") or source.get("lane") or "legacy"
        topic["selected"] = str(topic_id) in selected_ids
        topic["selectionRank"] = selected_ids.index(str(topic_id)) + 1 if str(topic_id) in selected_ids else None
        topic["title"] = compact_title(source.get("title") or source.get("hook") or existing.get("title", ""))
        topic["heat"] = heat_from_score(source.get("score"), int(existing.get("heat") or 86))
        topic["scoreDetail"] = copy.deepcopy(source.get("score") or {})
        topic["platforms"] = existing.get("platforms") or default_platforms(source)
        topic["evidenceSummary"] = build_topic_evidence_summary(source, daily_signals)
        topic["matchTags"] = [
            f"{priority}优先级",
            source.get("pain_id") or (existing.get("matchTags") or ["", "pain_id"])[1],
            action_label(source, existing),
        ]
        topic["quotes"] = build_quotes(pain, existing)
        topic["painSummary"] = (
            f"场景：{scene}。"
            f"<b>可见结果：{visible_result}</b> "
            f"CTA：{cta}"
        ).strip()
        topic["cases"] = [
            {
                "title": f"目标人群 · {source.get('target_role') or pain.get('target_role') or '待确认人群'}",
                "note": source.get("video_angle") or pain.get("repeated_action") or "适合做可见结果录屏。",
            },
            {
                "title": "录制计划",
                "note": source.get("recording_plan_ref")
                or ((existing.get("cases") or [{}, {"note": ""}]) + [{"note": ""}])[1].get("note", ""),
            },
        ]
        topics.append(topic)

    if topics:
        topics.sort(
            key=lambda item: (bool(item.get("selected")), int(item.get("heat") or 0)),
            reverse=True,
        )
        demand["topics"] = topics

    demand["evidenceDate"] = normalize_day(
        daily_signals.get("run_date") or daily_signals.get("generated_at")
    )

    topics_for_summary = demand.get("topics") or []
    source_mix = source_mix_from_signals(daily_signals) or aggregate_source_mix(topics_for_summary)
    demand["sourceMix"] = source_mix
    demand["insights"] = build_demand_insights(topics_for_summary, source_mix, feedback)
    demand["radarAxes"] = dashboard_axis_values(topics_for_summary)
    demand["radarBrief"] = (
        f"本轮高潜选题方向集中在「{cluster_keywords(topics_for_summary)}」，"
        f"优先选择与账号主拍方向匹配、且能直接展示结果的题目。"
    )
    effective_hooks = feedback.get("effective_hooks") or []
    demand["strategyNote"] = (
        compact_text(effective_hooks[0], 80)
        if effective_hooks
        else "优先选择方向匹配、机会信号清晰且能展示结果的题目，再用运营数据优化拍法。"
    )
    demand["topicArchiveCount"] = len(topics_for_summary)
    return demand


def build_benchmark(base: dict[str, Any], workspace: Path) -> dict[str, Any]:
    benchmark = copy.deepcopy(base.get("benchmark") or {"items": []})
    reference_bank = read_json(workspace / "data/benchmarks/current/reference-bank.json", {})
    pain_bank = read_json(workspace / "data/topic-research/current/pain-bank.json", {})
    references = reference_bank.get("references") or []
    existing_items = benchmark.get("items") or []
    existing_by_id = {item.get("id"): item for item in existing_items if item.get("id")}
    existing_by_title = {item.get("title"): item for item in existing_items if item.get("title")}
    pain_by_id = {
        pain.get("pain_id"): pain
        for pain in pain_bank.get("pains", [])
        if pain.get("pain_id")
    }
    if references:
        benchmark["totalCount"] = len(references)
        items = []
        for ref in references:
            existing = (
                copy.deepcopy(existing_by_id.get(ref.get("reference_id")) or {})
                or copy.deepcopy(existing_by_title.get(ref.get("title")) or {})
            )
            items.append(benchmark_item_from_reference(ref, existing, pain_by_id))
        items.sort(key=lambda item: (int(item.get("matchScore") or 0), int(item.get("views") or 0)), reverse=True)
        benchmark["items"] = items
        benchmark["sourceUpdatedAt"] = reference_bank.get("updated_at") or ""
        benchmark["fallbackUsed"] = any(not item.get("sourceRunId") for item in items)
    elif "totalCount" not in benchmark:
        benchmark["totalCount"] = len(benchmark.get("items") or [])
    return benchmark


def plan_steps_from_topic(topic: dict[str, Any]) -> list[dict[str, str]]:
    result = result_text_from_topic(topic)
    cta = cta_from_topic(topic)
    return [
        {"time": "0-3s", "text": compact_text(result, 14) or "亮出结果"},
        {"time": "3-10s", "text": "输入真实场景"},
        {"time": "10-20s", "text": "输出表格/清单"},
        {"time": "20-30s", "text": compact_text(cta, 14) or "评论关键词"},
    ]


def result_text_from_topic(topic: dict[str, Any]) -> str:
    text = str(topic.get("painSummary") or "")
    match = re.search(r"可见结果：(.+?)(?:CTA：|$)", text)
    if match:
        return compact_text(re.sub(r"<[^>]+>", "", match.group(1)).strip(" 。"), 40)
    return compact_text(topic.get("title"), 40)


def cta_from_topic(topic: dict[str, Any]) -> str:
    text = re.sub(r"<[^>]+>", "", str(topic.get("painSummary") or ""))
    match = re.search(r"CTA：(.+)$", text)
    if match:
        return compact_text(match.group(1), 24)
    return "评论“诊断”"


def build_shoot_plan(topic: dict[str, Any], index: int) -> dict[str, Any]:
    types = [
        ("primary", "主推选题", "zap", "优先级"),
        ("convert", "转化选题", "route", "承接咨询"),
        ("lab", "实验选题", "flask-conical", "测试场景"),
    ]
    css, label, icon, score_label = types[index % len(types)]
    heat = int(topic.get("heat") or 0)
    return {
        "type": css,
        "label": label,
        "icon": icon,
        "score": f"{score_label} {heat}" if index == 0 else score_label,
        "title": topic.get("title") or "待选择题",
        "hook": f"前 3 秒：{result_text_from_topic(topic)}",
        "steps": plan_steps_from_topic(topic),
        "meta": [
            topic_action(topic),
            "预计 45-60 秒",
            cta_from_topic(topic),
        ],
    }


def build_execution(base: dict[str, Any], workspace: Path, demand: dict[str, Any], benchmark: dict[str, Any]) -> dict[str, Any]:
    execution = copy.deepcopy(base.get("execution") or {})
    feedback = read_json(workspace / "data/feedback/current/learning.json", {})
    daily_scene = read_json(workspace / "work/topics/daily-scenes.json", {})
    selected = read_json(workspace / "work/topics/selections/daily.json", {})
    publishing = read_json(workspace / "work/plans/publishing.json", {})
    daily_plan = read_json(workspace / "work/plans/daily.json", {})
    recording_plans = list((workspace / "work/plans/recording").glob("*.md"))

    topics = (demand.get("topics") or [])[:]
    topics.sort(key=lambda item: int(item.get("heat") or 0), reverse=True)
    refs = benchmark.get("items") or []
    feedback_count = int((feedback.get("summary") or {}).get("new_learning_entries") or 0)
    planned_posts = publishing.get("planned_posts") or []

    execution["feedbackCount"] = feedback_count
    execution["steps"] = [
        {"name": "选题", "state": "done" if selected.get("selected") or topics else "wait"},
        {"name": "拆解", "state": "done" if refs else "wait"},
        {"name": "脚本", "state": "active" if recording_plans or selected.get("selected") else "wait"},
        {"name": "门禁", "state": "done" if planned_posts else "wait"},
    ]

    if daily_plan.get("plans") and daily_plan.get("status") != "blocked":
        execution["steps"] = [
            {"name": "选题", "state": "done"},
            {"name": "拆解", "state": "done" if any(item.get("reference_ids") for item in daily_plan["plans"]) else "wait"},
            {"name": "脚本", "state": "active"},
            {"name": "门禁", "state": "done" if planned_posts else "wait"},
        ]
        execution["command"] = copy.deepcopy(daily_plan.get("command") or {})
        execution["command"].setdefault("date", daily_plan.get("plan_date") or date.today().isoformat())
        execution["schedule"] = copy.deepcopy(daily_plan.get("schedule") or [])
        icons = {"primary": "zap", "convert": "route", "lab": "flask-conical"}
        execution["plans"] = []
        for item in (daily_plan.get("plans") or [])[:3]:
            plan = copy.deepcopy(item)
            plan.setdefault("icon", icons.get(str(plan.get("type")), "circle"))
            execution["plans"].append(plan)
        execution["sourceUpdatedAt"] = daily_plan.get("plan_date") or date.today().isoformat()
        execution["planStatus"] = daily_plan.get("status") or "unknown"
        execution["researchSummary"] = copy.deepcopy(daily_plan.get("research_summary") or {})
        return execution

    if daily_plan.get("status") == "blocked":
        execution["planStatus"] = "blocked"
        execution["researchSummary"] = copy.deepcopy(daily_plan.get("research_summary") or {})

    top_topic = topics[0] if topics else {}
    action = topic_action(top_topic) if top_topic else "结果前置型入口"
    source_date = first_text(daily_scene.get("generated_at"), data_date(feedback, "period.end"), date.today().isoformat())
    weekly_actions = daily_scene.get("weekly_actions") or []
    effective = feedback.get("effective_hooks") or []
    ineffective = feedback.get("ineffective_hooks") or []
    execution["command"] = {
        "date": source_date,
        "titlePrefix": "今天优先拍",
        "highlight": action,
        "copy": (
            compact_text(weekly_actions[0], 96)
            if weekly_actions
            else "依据账号策略、选题机会和运营约束，今天用一条能看见结果的短视频补上新入口。"
        ),
        "keywords": ["诊断", "场景", "工作流"],
        "checks": unique([
            "15-20 秒",
            "先给结果",
            "评论关键词统一",
            "避开收益承诺",
        ], 4),
        "gates": [
            {"label": "KEEP", "text": compact_text(effective[0] if effective else "继续强化 AI 应用诊断，不做泛工具教程。", 36)},
            {"label": "TEST", "text": "用真实场景 + 前后对比测试转化入口。"},
            {"label": "CUT", "text": compact_text(ineffective[0] if ineffective else "减少资料包、提示词合集、空泛教程表达。", 36)},
        ],
    }
    execution["schedule"] = [
        {"time": "10:00", "text": "确认主推选题 Hook 与样例数据"},
        {"time": "11:30", "text": "录制 0-20 秒结果前置版本"},
        {"time": "14:00", "text": "剪出前后对比与 CTA 字幕"},
        {"time": "16:30", "text": "发布前检查：诊断入口 / 评论关键词 / 风险表述"},
    ]
    execution["plans"] = [build_shoot_plan(topic, index) for index, topic in enumerate(topics[:3])]
    execution["sourceUpdatedAt"] = source_date
    return execution


def build_meta(workspace: Path, status: dict[str, dict[str, Any]]) -> dict[str, Any]:
    snapshot = read_json(workspace / "data/operations/current/account-snapshot.json", {})
    strategy = read_json(workspace / "config/strategy/strategy-brief.json", {})
    account_profile = read_json(workspace / "config/profile/account.profile.json", {})
    identity = account_profile.get("dashboard_identity") or {}
    period = snapshot.get("period") or {}
    source_date = normalize_day(period.get("end"))
    strategy_date = status.get("strategy", {}).get("updatedAt") or source_date
    source_files = [rel for rel, _max_age in SOURCE_SPECS.values()]
    provenance = account_profile.get("positioning_provenance") or {}
    positioning_ready = bool(
        account_profile.get("positioning")
        and account_profile.get("positioning_status") == "confirmed"
        and all(
            provenance.get(field)
            for field in (
                "positioning_source_type",
                "positioning_source_ref",
                "confirmation_quote",
                "confirmed_at",
            )
        )
    )
    strategy_ready = bool(
        strategy.get("strategy_id")
        and strategy.get("status") == "confirmed"
        and strategy.get("confirmed_by_user") is True
        and strategy.get("stage_goal")
        and strategy.get("primary_strategy")
    )
    onboarding_items = [
        {
            "id": "positioning",
            "label": "确认账号定位",
            "description": "明确账号阶段、主赛道、创作者身份、目标用户，以及可持续使用的真实资源。",
            "complete": positioning_ready,
            "path": "config/profile/",
        },
        {
            "id": "strategy",
            "label": "确认运营策略",
            "description": "从三套方向中选择主方向，明确内容支柱、阶段目标、商业承接和 30／60／90 天规划。",
            "complete": strategy_ready,
            "path": "config/strategy/strategy-brief.json",
        },
    ]

    return {
        "workspacePath": str(workspace),
        "dataDirectory": str(workspace / "data"),
        "sourceDate": source_date,
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "dataRange": format_period(period),
        "strategyLabel": f"strategy-brief · {strategy_date[5:]}" if strategy_date else "strategy-brief",
        "strategyId": strategy.get("strategy_id", ""),
        "opsPeriodLabel": (
            f"Douyin Creator · {source_date[5:]} · topic-candidates + reference-bank"
            if source_date
            else "Douyin Creator · source date unavailable"
        ),
        "sourceFiles": source_files,
        "sourceStatus": status,
        "onboarding": {
            "questionnaireVersion": "2.0",
            "required": not (positioning_ready and strategy_ready),
            "title": "开始前，先配置账号定位和运营策略",
            "description": "这两项决定后续找什么选题、参考哪些爆款和如何安排内容。未确认前，系统不会生成可执行计划。",
            "workspacePath": str(workspace),
            "items": onboarding_items,
            "prompt": (
                f"我的 Short Video Ops 工作区路径是：{workspace}。请先检查这个工作区的账号定位和运营策略。"
                "如果缺失、仍是模板示例或尚未确认，"
                "请依次确认：账号阶段、主赛道、创作者身份、目标用户、核心需求、真实资源、阶段目标、"
                "商业承接、内容形式和未来规划。请先提供多个内容方向方案并总结给我确认，再写入配置；确认前不要找选题、"
                "拆爆款、写文案或生成 ready 计划。"
            ),
        },
        "identity": {
            "name": first_text(identity.get("name"), account_profile.get("display_name"), "你的短视频账号"),
            "role": first_text(identity.get("role"), "内容运营工作台"),
            "tagline": first_text(identity.get("tagline"), "把零散数据整理成清晰的下一步。"),
            "avatar": first_text(identity.get("avatar")),
        },
    }


def build_strategy_panel(workspace: Path) -> dict[str, Any]:
    account_profile = read_json(workspace / "config/profile/account.profile.json", {})
    audience_profile = read_json(workspace / "config/profile/audience.profile.json", {})
    offer_profile = read_json(workspace / "config/profile/offer.profile.json", {})
    strategy = read_json(workspace / "config/strategy/strategy-brief.json", {})
    audiences = audience_profile.get("primary_audiences") or []
    audience_labels = [
        first_text(item.get("label"), item.get("description"), item.get("audience_id"))
        for item in audiences
        if isinstance(item, dict)
    ]
    assumptions = unique(
        list(account_profile.get("assumptions_to_validate") or [])
        + list(strategy.get("assumptions_to_validate") or []),
        12,
    )
    confirmed = bool(
        account_profile.get("positioning_status") == "confirmed"
        and strategy.get("status") == "confirmed"
        and strategy.get("confirmed_by_user") is True
    )
    return {
        "status": "confirmed" if confirmed else "needs_confirmation",
        "statusLabel": "已确认" if confirmed else "待确认",
        "strategyId": strategy.get("strategy_id") or "",
        "positioning": account_profile.get("positioning") or "",
        "industry": account_profile.get("industry") or "",
        "creatorRole": account_profile.get("creator_role") or "",
        "audiences": audience_labels,
        "stageGoal": strategy.get("stage_goal") or "",
        "primaryStrategy": strategy.get("primary_strategy") or "",
        "contentPillars": strategy.get("content_pillars") or [],
        "contentRatio": strategy.get("content_ratio") or {},
        "topicPrinciples": strategy.get("topic_principles") or [],
        "conversionPath": strategy.get("conversion_path") or "",
        "productionCadence": strategy.get("production_cadence") or "",
        "offer": first_text(offer_profile.get("offer_name"), strategy.get("conversion_path")),
        "avoid": strategy.get("avoid") or account_profile.get("content_boundaries") or [],
        "assumptions": assumptions,
        "sourcePaths": [
            "config/profile/account.profile.json",
            "config/profile/audience.profile.json",
            "config/profile/offer.profile.json",
            "config/strategy/strategy-brief.json",
        ],
    }


def build_dashboard_data(workspace: Path, base_path: Path) -> dict[str, Any]:
    base = read_json(base_path, {})
    for key in REQUIRED_TOP_LEVEL_KEYS:
        base.setdefault(key, {})

    status = build_source_status(workspace)
    account = build_account(base, workspace)
    demand = build_demand(base, workspace)
    benchmark = build_benchmark(base, workspace)
    return {
        "meta": build_meta(workspace, status),
        "account": account,
        "demand": demand,
        "execution": build_execution(base, workspace, demand, benchmark),
        "benchmark": benchmark,
        "strategyPanel": build_strategy_panel(workspace),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "workspace",
        nargs="?",
        help="User workspace root. Defaults to SHORT_VIDEO_OPS_WORKSPACE.",
    )
    parser.add_argument("--base", help="Existing dashboard JSON used as fallback.")
    parser.add_argument("--output", help="Dashboard JSON output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workspace = (
        Path(args.workspace).expanduser().resolve()
        if args.workspace
        else default_workspace()
    )
    default_data_path = workspace / "presentation/ops-dashboard.json"
    base_path = Path(args.base).expanduser().resolve() if args.base else default_data_path
    output_path = Path(args.output).expanduser().resolve() if args.output else default_data_path

    data = build_dashboard_data(workspace, base_path)
    write_json(output_path, data)

    print(f"built dashboard data: {output_path}")
    print("sources:")
    for rel, _max_age in SOURCE_SPECS.values():
        print(f"- {workspace / rel}")


if __name__ == "__main__":
    main()
