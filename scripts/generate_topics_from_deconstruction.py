#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"missing file: {path}") from None
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid json: {path}: {exc}") from None
    if not isinstance(value, dict):
        raise SystemExit(f"expected json object: {path}")
    return value


def slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()[:32] or "topic"


def find_pain(pain_bank: dict[str, Any], *keywords: str) -> str:
    for pain in pain_bank.get("pains", []):
        if not isinstance(pain, dict):
            continue
        text = json.dumps(pain, ensure_ascii=False)
        if all(keyword in text for keyword in keywords):
            return str(pain.get("pain_id") or "")
    for pain in pain_bank.get("pains", []):
        if isinstance(pain, dict) and pain.get("pain_id"):
            return str(pain["pain_id"])
    return ""


def reference_ids(deconstruction: dict[str, Any]) -> list[str]:
    ids = []
    for item in deconstruction.get("decompositions", []):
        source = item.get("source") or {}
        platform = source.get("platform") or "reference"
        item_id = source.get("id") or slug(source.get("title") or platform)
        ids.append(f"{platform}:{item_id}")
    return ids


def candidate_topics(strategy: dict[str, Any], pain_bank: dict[str, Any], deconstruction: dict[str, Any]) -> list[dict[str, Any]]:
    strategy_id = strategy.get("strategy_id") or "strategy-current"
    refs = reference_ids(deconstruction)
    p_content = find_pain(pain_bank, "知识博主", "选题") or find_pain(pain_bank, "内容")
    p_data = find_pain(pain_bank, "后台", "数据") or p_content
    p_codex = find_pain(pain_bank, "Codex", "新手") or p_content
    common_evidence = [
        f"reference-deconstruction:{deconstruction.get('source_run_id')}",
        "current-draft:codex-content-flow",
    ]
    return [
        {
            "topic_id": "TEST-CODEX-FLOW-001",
            "pain_id": p_content,
            "strategy_id": strategy_id,
            "reference_ids": refs,
            "evidence_ids": common_evidence,
            "priority": "A",
            "title": "最近几条数据不错，不是我懂运营，是我让 Codex 先跑了一遍内容系统。",
            "target_role": "知识博主/短视频创作者",
            "scene": "账号从定位、选题、文案到录制计划都靠人临时判断，流程不可复用。",
            "hook": "很多人问我怎么做出这几条数据，其实答案不是运营技巧，而是一套 Codex 内容生产系统。",
            "visible_result": "展示 7 个工作流目录和其中一个工作流输出的选题/文案/录制计划。",
            "cta": "想看完整流程拆解，评论“流程”。",
            "score": {"pain": 5, "frequency": 5, "demo": 5, "payment": 4, "productization": 5, "strategy_fit": 5, "evidence_quality": 4},
        },
        {
            "topic_id": "TEST-CODEX-FLOW-002",
            "pain_id": p_content,
            "strategy_id": strategy_id,
            "reference_ids": refs,
            "evidence_ids": common_evidence,
            "priority": "A",
            "title": "别再只问提示词了，AI 视频质量其实取决于提示词、数据和技能三件事。",
            "target_role": "AI 新手/知识付费学习者",
            "scene": "用户以为 AI 输出差是提示词问题，忽略垂直数据和专业技能。",
            "hook": "AI 给你的不是标准答案，是基于你喂进去的信息算出来的高概率结果。",
            "visible_result": "用同一选题展示普通提示词和流程化输入后的输出差异。",
            "cta": "我把这套提示词、数据、技能框架放在知识星球里继续拆。",
            "score": {"pain": 5, "frequency": 5, "demo": 4, "payment": 5, "productization": 5, "strategy_fit": 5, "evidence_quality": 4},
        },
        {
            "topic_id": "TEST-CODEX-FLOW-003",
            "pain_id": p_data,
            "strategy_id": strategy_id,
            "reference_ids": refs,
            "evidence_ids": common_evidence,
            "priority": "A",
            "title": "我做教学类视频前，不会先写文案，而是先让 Codex 查一遍对标爆款。",
            "target_role": "短视频创作者/内容运营",
            "scene": "想做教学转化内容，但不知道对标内容该查哪些、怎么拆。",
            "hook": "这条视频不是我拍脑袋写的，是先跑了一个竞品分析工作流。",
            "visible_result": "展示 reference research plan、正文下载结果和拆解报告三张输出。",
            "cta": "想看这个竞品分析工作流，评论“竞品”。",
            "score": {"pain": 5, "frequency": 4, "demo": 5, "payment": 4, "productization": 5, "strategy_fit": 5, "evidence_quality": 5},
        },
        {
            "topic_id": "TEST-CODEX-FLOW-004",
            "pain_id": p_codex,
            "strategy_id": strategy_id,
            "reference_ids": refs,
            "evidence_ids": common_evidence,
            "priority": "B",
            "title": "一句提示词和一套流程，差别到底有多大？我用同一个视频选题跑给你看。",
            "target_role": "Codex 新手/AI 工具使用者",
            "scene": "用户知道 Codex 强，但还停留在把它当聊天机器人。",
            "hook": "你给 AI 一句话，它只能猜；你给它一套流程，它才开始像助理。",
            "visible_result": "同题对比：一句 prompt 输出 vs 研究计划+参考正文+策略拆解输出。",
            "cta": "想拿这套流程模板，评论“模板”。",
            "score": {"pain": 4, "frequency": 4, "demo": 5, "payment": 4, "productization": 5, "strategy_fit": 5, "evidence_quality": 4},
        },
        {
            "topic_id": "TEST-CODEX-FLOW-005",
            "pain_id": p_content,
            "strategy_id": strategy_id,
            "reference_ids": refs,
            "evidence_ids": common_evidence,
            "priority": "B",
            "title": "七个工作流里，最该先搭的不是文案，而是数据下载和正文拆解。",
            "target_role": "知识博主/课程型创作者",
            "scene": "创作者直接优化文案，缺少对标正文和结构证据。",
            "hook": "如果没有正文，所谓爆款拆解基本都是猜。",
            "visible_result": "展示抖音/YouTube 正文集合和策略拆解报告。",
            "cta": "想看下载和拆解脚本，评论“正文”。",
            "score": {"pain": 4, "frequency": 4, "demo": 5, "payment": 4, "productization": 4, "strategy_fit": 5, "evidence_quality": 4},
        },
    ]


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# {payload['run_name']}",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Source deconstruction: {payload['source_reference_strategy_run_id']}",
        f"- Topic candidates: {len(payload['topics'])}",
        "",
    ]
    for topic in payload["topics"]:
        lines.extend(
            [
                f"## {topic['topic_id']} | {topic['priority']}",
                "",
                f"- Title: {topic['title']}",
                f"- Pain: {topic['pain_id']}",
                f"- Hook: {topic['hook']}",
                f"- Visible result: {topic['visible_result']}",
                f"- CTA: {topic['cta']}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate topic candidates from a reference strategy deconstruction run.")
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--reference-strategy-run-id", required=True)
    parser.add_argument("--run-id", default="")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    if not workspace.exists():
        raise SystemExit(f"workspace not found: {workspace}")
    deconstruction_path = workspace / "runs" / args.reference_strategy_run_id / "outputs" / "reference-strategy-deconstruction.json"
    deconstruction = load_json(deconstruction_path)
    strategy = load_json(workspace / "config/strategy/strategy-brief.json")
    pain_bank = load_json(workspace / "data/topic-research/current/pain-bank.json")
    run_id = args.run_id or f"{datetime.now().date().isoformat()}-topic-candidates-from-reference"
    output_root = workspace / "runs" / run_id / "outputs"
    output_root.mkdir(parents=True, exist_ok=True)

    topics = candidate_topics(strategy, pain_bank, deconstruction)
    payload = {
        "run_name": run_id,
        "workflow_id": "topic-candidates-test",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "workspace": str(workspace),
        "source_reference_strategy_run_id": args.reference_strategy_run_id,
        "source_reference_strategy_path": str(deconstruction_path),
        "status": "test_output_only_not_written_to_formal_topic_radar",
        "topics": topics,
        "selected": topics[:3],
    }

    json_path = output_root / "topic-candidates.json"
    md_path = output_root / "topic-candidates.md"
    manifest_path = workspace / "runs" / run_id / "run.manifest.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    manifest_path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "workflow_id": "topic-candidates-test",
                "generated_at": payload["generated_at"],
                "inputs": [
                    str(deconstruction_path.relative_to(workspace)),
                    "config/strategy/strategy-brief.json",
                    "data/topic-research/current/pain-bank.json",
                ],
                "outputs": [str(json_path.relative_to(workspace)), str(md_path.relative_to(workspace))],
                "notes": "Test output only. Does not overwrite either current candidate lane or the daily mixed selection.",
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
