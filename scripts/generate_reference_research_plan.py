#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_DRAFT = """最近几条视频我数据还不错，很多粉丝问我有什么技巧策略，说实话，我不太懂运营，但我比较懂 AI。
今天这期我就分享下从账号从定位、选题、文案，到视频生成，是如何让 Codex 去帮我做的。
我给它的不是一句提示词，而是一整套策略。
"""


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def infer_scene(draft: str, strategy: dict[str, Any]) -> str:
    text = f"{draft} {json.dumps(strategy, ensure_ascii=False)}".lower()
    if "codex" in text and any(word in text for word in ["选题", "文案", "视频", "工作流", "workflow"]):
        return "AI 内容生产工作流复盘 + AI 教学转化 + 知识星球承接"
    if any(word in text for word in ["知识星球", "社群", "课程", "资料"]):
        return "AI 教学转化 + 社群/课程承接"
    if any(word in text for word in ["诊断", "场景", "咨询"]):
        return "AI 场景诊断 + 咨询筛选"
    return "AI 工作流教学 + 结果展示"


def query_groups(scene: str) -> dict[str, list[str]]:
    if "内容生产" in scene:
        return {
            "youtube": [
                "AI workflow content creation",
                "AI agents content creation workflow",
                "AI automation content creator workflow",
                "Codex AI agent workflow",
            ],
            "bilibili": [
                "AI 工作流 自媒体",
                "AI 自动化 工作流",
                "AI 选题 文案 工作流",
                "Codex 工作流",
            ],
            "douyin": [
                "AI 自动化工作流",
                "AI 自媒体 工作流",
                "AI 选题 文案",
                "AI 教学 知识星球",
            ],
        }
    return {
        "youtube": ["AI workflow tutorial", "AI automation tutorial", "AI agent workflow"],
        "bilibili": ["AI 工作流 教程", "AI 自动化 教程", "AI Agent 教程"],
        "douyin": ["AI 工作流", "AI 自动化", "AI 教程"],
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# {payload['run_name']}",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Workflow: {payload['workflow_id']}",
        f"- Stage direction: {payload['stage_direction']}",
        f"- Content scene: {payload['content_scene']}",
        "",
        "## Research Questions",
        "",
    ]
    for question in payload["research_questions"]:
        lines.append(f"- {question}")
    lines.extend(["", "## Query Groups", ""])
    for platform, queries in payload["query_groups"].items():
        lines.append(f"### {platform}")
        for query in queries:
            lines.append(f"- {query}")
        lines.append("")
    lines.extend(["## Inclusion Rules", ""])
    for rule in payload["inclusion_rules"]:
        lines.append(f"- {rule}")
    lines.extend(["", "## Exclusion Rules", ""])
    for rule in payload["exclusion_rules"]:
        lines.append(f"- {rule}")
    lines.extend(["", "## Downstream", "", f"- {payload['downstream_workflow']}"])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a reference research plan for the next transcript download workflow.")
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--current-draft", default=DEFAULT_DRAFT)
    parser.add_argument("--sample-youtube", type=int, default=1)
    parser.add_argument("--sample-bilibili", type=int, default=1)
    parser.add_argument("--sample-douyin", type=int, default=1)
    parser.add_argument("--min-transcript-chars", type=int, default=120)
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    if not workspace.exists():
        raise SystemExit(f"workspace not found: {workspace}")

    strategy = load_json(workspace / "config/strategy/strategy-brief.json")
    account_snapshot = load_json(workspace / "data/operations/current/account-snapshot.json")
    pain_bank = load_json(workspace / "data/topic-research/current/pain-bank.json")
    run_id = args.run_id or f"{datetime.now().date().isoformat()}-reference-research-plan"
    output_root = workspace / "runs" / run_id / "outputs"
    output_root.mkdir(parents=True, exist_ok=True)

    scene = infer_scene(args.current_draft, strategy)
    queries = query_groups(scene)
    stage_direction = strategy.get("stage_goal") or account_snapshot.get("main_bottleneck") or "结果呈现、场景诊断和工作流改造"
    priority_pains = strategy.get("priority_pain_ids") or [
        pain.get("pain_id") for pain in pain_bank.get("pains", [])[:4] if isinstance(pain, dict)
    ]

    payload = {
        "run_name": run_id,
        "workflow_id": "reference-research-plan",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "workspace": str(workspace),
        "stage_direction": stage_direction,
        "content_scene": scene,
        "current_draft": clean_text(args.current_draft),
        "priority_pain_ids": priority_pains,
        "research_questions": [
            "爆款开头如何把结果/数据/反差前置，而不是先讲概念？",
            "创作者如何把 AI 工作流拆成几个可理解模块？",
            "概念解释如何接到提示词、数据、技能，而不显得空讲？",
            "CTA 如何自然承接到知识星球/资料/流程拆解，而不是硬卖课？",
        ],
        "platform_mix": {
            "youtube": "英文一手/工作流结构参考",
            "bilibili": "中文长短教程结构参考",
            "douyin": "短视频钩子、节奏和转化参考",
        },
        "query_groups": queries,
        "sample_targets": {
            "youtube": args.sample_youtube,
            "bilibili": args.sample_bilibili,
            "douyin": args.sample_douyin,
        },
        "inclusion_rules": [
            "开头 3 秒有结果、反差、强承诺或可见画面。",
            "正文能拿到逐字稿，且不少于指定字符数。",
            "内容包含流程、系统、工作台、模板、数据、案例或 CTA。",
            "能映射到 Codex 提效、内容生产系统、知识星球承接。",
        ],
        "exclusion_rules": [
            "只有标题和简介、没有口播正文。",
            "主要卖暴富、副业、月入承诺。",
            "纯工具安装教程，无法迁移到账号策略。",
            "只讲概念，没有流程或证明。",
        ],
        "transcript_policy": f"min_transcript_chars={args.min_transcript_chars}; Douyin requires TikHub detail -> mp4 download -> ffmpeg audio extraction -> ASR.",
        "download_args": {
            "per_query": 2,
            "min_youtube_views": 10000,
            "min_bilibili_views": 5000,
            "min_douyin_likes": 500,
            "max_youtube_transcripts": args.sample_youtube,
            "max_bilibili_transcripts": args.sample_bilibili,
            "max_douyin_transcripts": args.sample_douyin,
            "douyin_limit": 3,
            "min_transcript_chars": args.min_transcript_chars,
            "download_douyin_video": True,
            "transcribe_missing": True,
            "asr_provider": "local-whisper",
            "local_whisper_model": "tiny",
        },
        "downstream_workflow": "reference-transcript-download",
    }

    json_path = output_root / "reference-research-plan.json"
    md_path = output_root / "reference-research-plan.md"
    manifest_path = workspace / "runs" / run_id / "run.manifest.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    manifest_path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "workflow_id": "reference-research-plan",
                "generated_at": payload["generated_at"],
                "inputs": [
                    "config/strategy/strategy-brief.json",
                    "data/operations/current/account-snapshot.json",
                    "data/topic-research/current/pain-bank.json",
                    "current draft",
                ],
                "outputs": [str(json_path.relative_to(workspace)), str(md_path.relative_to(workspace))],
                "notes": "Planning only; does not download or decompose reference videos.",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    print(f"wrote {manifest_path}")


if __name__ == "__main__":
    main()
