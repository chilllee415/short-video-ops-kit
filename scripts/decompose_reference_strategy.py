#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


CTA_KEYWORDS = ["评论", "关注", "私信", "资料", "课程", "星球", "领取", "subscribe", "comment", "course", "community"]
WORKFLOW_KEYWORDS = ["工作流", "流程", "自动化", "数据", "选题", "文案", "脚本", "视频", "剪辑", "录制", "知识库", "素材", "日程", "日报", "工具", "agent", "workflow", "automation"]
PROOF_KEYWORDS = ["数据", "播放", "粉丝", "提升", "倍", "效果", "结果", "案例", "给大家看", "工作台", "系统", "后台", "录屏", "截图", "show", "result"]
CONCEPT_KEYWORDS = ["为什么", "因为", "本质", "核心", "概率", "提示词", "上下文", "技能", "数据", "标准答案", "模型", "AI"]


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def split_units(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？!?])\s+|(?<=[.!?])\s+", text)
    if len(parts) < 4:
        parts = re.split(r"\s+(?=(?:那|然后|首先|第二|第三|比如|所以|但是|而|Now|And|So)\b)", text)
    return [clean_text(part) for part in parts if clean_text(part)]


def contains_any(text: str, keywords: list[str]) -> bool:
    lower = text.lower()
    return any(keyword.lower() in lower for keyword in keywords)


def first_matches(units: list[str], keywords: list[str], limit: int = 5) -> list[str]:
    matches = [unit for unit in units if contains_any(unit, keywords)]
    return matches[:limit]


def detect_hook(opening: str, title: str) -> list[str]:
    text = f"{title} {opening}".lower()
    tags: list[str] = []
    if contains_any(text, ["提升", "倍", "数据", "结果", "工作台", "系统", "给大家看", "show", "result"]):
        tags.append("成果前置")
    if contains_any(text, ["新人", "小白", "零基础", "beginner", "no coding"]):
        tags.append("新手友好")
    if contains_any(text, ["不是", "不要", "错", "反感", "坑", "wrong", "mistake"]):
        tags.append("反坑/反焦虑")
    if contains_any(text, ["工作流", "流程", "自动化", "workflow", "automation"]):
        tags.append("工作流包装")
    if re.search(r"\d+|一|二|三|四|五|六|七", text):
        tags.append("数字框架")
    return tags or ["主题承诺"]


def stage_map(units: list[str]) -> list[str]:
    stages = []
    joined = " ".join(units)
    if contains_any(joined[:500], PROOF_KEYWORDS):
        stages.append("开头先给结果/画面证据")
    if contains_any(joined, ["为什么", "痛点", "问题", "不知道", "复杂", "反感", "wrong", "mistake"]):
        stages.append("解释为什么要看：新手困惑或旧方法低效")
    if contains_any(joined, WORKFLOW_KEYWORDS):
        stages.append("展示工作流节点：把抽象能力拆成多个可见模块")
    if contains_any(joined, CONCEPT_KEYWORDS):
        stages.append("植入方法论概念：在流程后解释原理")
    if contains_any(joined, CTA_KEYWORDS):
        stages.append("结尾承接：评论/关注/资料/社群/课程")
    return stages or ["标题承诺 -> 解释 -> 演示 -> 收束"]


def classify_strategy(title: str, text: str) -> list[str]:
    joined = f"{title} {text}".lower()
    tags = []
    if contains_any(joined, ["工作台", "系统", "流程", "工作流", "workflow"]):
        tags.append("系统展示型")
    if contains_any(joined, ["教程", "step", "步骤", "手把手", "从0到1", "beginner"]):
        tags.append("教学拆步型")
    if contains_any(joined, ["我最近", "我的", "我用", "自己", "living proof"]):
        tags.append("个人复盘型")
    if contains_any(joined, ["课程", "资料", "社群", "community", "course"]):
        tags.append("知识付费承接型")
    if contains_any(joined, ["不要", "反感", "错", "坑", "wrong"]):
        tags.append("反焦虑信任型")
    return tags or ["泛教学型"]


def decompose_item(item: dict[str, Any]) -> dict[str, Any]:
    source = item.get("source") or {}
    transcript_info = item.get("transcript") or {}
    clean_path = transcript_info.get("clean_path")
    text = item.get("transcript_text") or ""
    if not text and clean_path and Path(clean_path).exists():
        text = Path(clean_path).read_text(encoding="utf-8", errors="ignore")
    text = clean_text(text)
    units = split_units(text)
    opening = clean_text(item.get("opening_preview") or text[:300])
    title = str(source.get("title") or "")
    return {
        "source": source,
        "transcript": {
            "status": transcript_info.get("status"),
            "text_source": transcript_info.get("text_source"),
            "char_count": len(text),
            "clean_path": clean_path,
            "video_path": transcript_info.get("video_path"),
            "audio_path": transcript_info.get("audio_path"),
        },
        "strategy_tags": classify_strategy(title, text),
        "hook": {
            "opening_preview": opening[:300],
            "hook_types": detect_hook(opening, title),
            "why_it_stops_scroll": infer_hook_reason(opening, title),
        },
        "structure": stage_map(units),
        "proof_assets": first_matches(units, PROOF_KEYWORDS),
        "workflow_nodes": first_matches(units, WORKFLOW_KEYWORDS, limit=8),
        "concept_bridges": first_matches(units, CONCEPT_KEYWORDS, limit=5),
        "cta": {
            "signals": [keyword for keyword in CTA_KEYWORDS if keyword.lower() in text.lower()][:8],
            "style": infer_cta_style(text),
        },
        "transferable_strategy": transferable_strategy(title, text),
        "risks": risk_notes(title, text),
    }


def infer_hook_reason(opening: str, title: str) -> str:
    text = f"{title} {opening}"
    if contains_any(text, ["工作台", "系统", "给大家看", "提升", "倍"]):
        return "先展示可见结果，观众会判断这不是空讲概念。"
    if contains_any(text, ["小白", "新人", "零基础"]):
        return "降低进入门槛，把复杂 AI 变成新手也能跟上的路径。"
    if contains_any(text, ["不要", "错", "坑", "wrong"]):
        return "用反常识或纠错制造停顿。"
    return "用主题承诺让目标观众判断是否继续看。"


def infer_cta_style(text: str) -> str:
    if contains_any(text, ["星球", "社群", "community"]):
        return "社群/星球承接"
    if contains_any(text, ["资料", "领取", "link in", "description"]):
        return "资料领取承接"
    if contains_any(text, ["评论", "comment"]):
        return "评论互动承接"
    if contains_any(text, ["关注", "subscribe"]):
        return "关注留存承接"
    return "弱 CTA 或无显性 CTA"


def transferable_strategy(title: str, text: str) -> list[str]:
    points = []
    if contains_any(text, ["工作台", "系统", "工作流"]):
        points.append("先展示系统/工作台，再解释背后的方法论。")
    if contains_any(text, ["提升", "倍", "效率", "结果"]):
        points.append("把 AI 价值翻译成效率、产出或可见结果。")
    if contains_any(text, ["第一", "第二", "第三", "步骤", "板块", "流程"]):
        points.append("用分层结构降低复杂度，让观众觉得可以跟做。")
    if contains_any(text, ["为什么", "因为", "核心", "本质"]):
        points.append("概念不要开场讲，放在流程展示之后做解释。")
    if contains_any(text, ["评论", "资料", "课程", "社群", "星球"]):
        points.append("CTA 承接到继续拆流程，而不是直接卖泛 AI 课。")
    return points or ["保留选题方向，重写证明方式和 CTA。"]


def risk_notes(title: str, text: str) -> list[str]:
    risks = ["不要复述原视频句子，只借结构。"]
    if contains_any(text, ["学完即接单", "赚钱", "副业", "百万", "million"]):
        risks.append("收益承诺要弱化，避免变成卖课感。")
    if len(text) > 10000:
        risks.append("长教程只能取开头钩子和结构，不要照搬完整课程。")
    if contains_any(text, ["tiny", "错字"]):
        risks.append("ASR 逐字稿需要人工校对后再引用。")
    return risks


def current_draft_analysis(draft: str, decompositions: list[dict[str, Any]]) -> dict[str, Any]:
    draft = clean_text(draft)
    return {
        "scene_fit": "AI 内容生产工作流复盘 / AI 自动化教学 / 知识星球承接",
        "best_reference_patterns": [
            "先把 Codex 跑出的结果变成开头证据。",
            "把七个工作流说成一个生产系统，而不是提示词合集。",
            "先讲为什么要积累数据，再讲“AI 是概率结果”。",
            "结尾承接到“完整流程拆解”，不要承接到泛 AI 课程。",
        ],
        "draft_gaps": draft_gaps(draft),
        "recommended_structure": [
            "0-3s：最近几条数据不错，很多人问技巧。我的答案不是运营技巧，而是一套 Codex 内容生产系统。",
            "3-12s：展示系统结果：账号定位、选题、竞品、文案、录制计划、视频生成都能先跑一遍。",
            "12-28s：解释七个工作流，每个只说名称和结果，不展开教程。",
            "28-42s：引出数据：为什么要先下载/整理数据，因为 AI 输出的是高概率结果。",
            "42-55s：知识框架：提示词、数据、技能，三者决定概率上限。",
            "55-65s：举教学类内容例子：账号运营工作流 -> 竞品分析工作流 -> 视频制作工作流。",
            "65s+：CTA：我把这套流程和每一步拆解放在知识星球/社群里，后面继续拆。",
        ],
        "reference_count": len(decompositions),
    }


def draft_gaps(draft: str) -> list[str]:
    gaps = []
    if "不太懂运营" in draft:
        gaps.append("“不太懂运营”可以保留人设，但不要放在证明之前；先给结果，再说反差。")
    if "xxxx" in draft.lower():
        gaps.append("七个工作流不能留占位，至少要给出 5-7 个具体名称。")
    if "AI给的从来不是标准答案" in draft or "标准答案" in draft:
        gaps.append("“AI 不是标准答案”是好概念，但要接在数据积累之后，不适合做开场。")
    if "知识星球" not in draft:
        gaps.append("当前文案还没有明确星球 CTA，建议用“流程拆解/模板/案例复盘”承接。")
    return gaps or ["当前故事线成立，重点是把证明前置、流程命名说清楚。"]


def find_source_collection(workspace: Path, source_run_id: str) -> Path:
    output_root = workspace / "runs" / source_run_id / "outputs"
    candidates = [
        output_root / "reference-transcript-collection.json",
        output_root / "teaching-video-script-analysis.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    expected = ", ".join(str(path) for path in candidates)
    raise SystemExit(f"source transcript collection not found. Expected one of: {expected}")


def source_items(source: dict[str, Any]) -> list[dict[str, Any]]:
    items = source.get("items")
    if isinstance(items, list):
        return items
    analyses = source.get("analyses")
    if isinstance(analyses, list):
        return analyses
    return []


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# {payload['run_name']}",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Source run: {payload['source_run_id']}",
        f"- Decomposed items: {len(payload['decompositions'])}",
        "",
        "## Current Draft Strategy",
        "",
        f"- Scene fit: {payload['current_draft_analysis']['scene_fit']}",
        "",
        "Recommended structure:",
    ]
    for step in payload["current_draft_analysis"]["recommended_structure"]:
        lines.append(f"- {step}")
    lines.extend(["", "Draft gaps:"])
    for gap in payload["current_draft_analysis"]["draft_gaps"]:
        lines.append(f"- {gap}")
    lines.extend(["", "## Reference Decompositions", ""])
    for index, item in enumerate(payload["decompositions"], start=1):
        source = item["source"]
        lines.extend([
            f"### {index}. {source.get('title')}",
            "",
            f"- Platform: {source.get('platform')}",
            f"- URL: {source.get('url')}",
            f"- Transcript chars: {item['transcript'].get('char_count')}",
            f"- Strategy tags: {', '.join(item.get('strategy_tags') or [])}",
            f"- Hook types: {', '.join(item['hook'].get('hook_types') or [])}",
            f"- CTA style: {item['cta'].get('style')}",
            "",
            "Structure:",
        ])
        for stage in item.get("structure") or []:
            lines.append(f"- {stage}")
        lines.append("")
        lines.append("Transferable strategy:")
        for point in item.get("transferable_strategy") or []:
            lines.append(f"- {point}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Decompose reference transcripts into reusable short-video strategy patterns.")
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--current-draft", default="")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    source_json = find_source_collection(workspace, args.source_run_id)
    source = json.loads(source_json.read_text(encoding="utf-8"))
    run_id = args.run_id or f"{args.source_run_id}-strategy-deconstruction"
    output_root = workspace / "runs" / run_id / "outputs"
    output_root.mkdir(parents=True, exist_ok=True)

    decompositions = [decompose_item(item) for item in source_items(source)]
    payload = {
        "run_name": run_id,
        "source_run_id": args.source_run_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "workspace": str(workspace),
        "source_collection": str(source_json),
        "current_draft": args.current_draft,
        "current_draft_analysis": current_draft_analysis(args.current_draft, decompositions),
        "decompositions": decompositions,
    }

    json_path = output_root / "reference-strategy-deconstruction.json"
    md_path = output_root / "reference-strategy-deconstruction.md"
    manifest_path = workspace / "runs" / run_id / "run.manifest.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    manifest_path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "workflow_id": "reference-strategy-deconstruction",
                "generated_at": payload["generated_at"],
                "inputs": [str(source_json.relative_to(workspace))],
                "outputs": [str(json_path.relative_to(workspace)), str(md_path.relative_to(workspace))],
                "notes": "Post-processes extracted transcripts; does not fetch or download platform data.",
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
