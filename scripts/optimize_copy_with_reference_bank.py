#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


KEYWORD_GROUPS = {
    "codex": ["codex"],
    "workflow": ["工作流", "流程", "自动化", "系统", "重构", "推倒重做"],
    "short_video": ["短视频", "视频", "播放", "爆款", "文案", "选题", "账号"],
    "data": ["数据", "垂域", "素材库", "参考库", "下载", "拆解"],
    "conversion": ["粉丝群", "知识星球", "评论", "回复", "关注", "私信", "体验"],
    "teaching": ["教学", "教程", "干货", "技巧", "方法"],
    "proof": ["20万", "两周", "一个月", "跑到", "效果", "质量", "结果"],
}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        if default is not None:
            return default
        raise SystemExit(f"missing file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid json: {path}: {exc}") from None
    if not isinstance(data, dict):
        raise SystemExit(f"expected json object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def sentences(value: str) -> list[str]:
    parts = re.split(r"(?<=[。！？!?])\s*|\n+", value)
    return [clean_text(part) for part in parts if clean_text(part)]


def keyword_hits(text: str) -> dict[str, list[str]]:
    lower_text = text.lower()
    hits: dict[str, list[str]] = {}
    for group, keywords in KEYWORD_GROUPS.items():
        found = []
        for keyword in keywords:
            if keyword.lower() in lower_text:
                found.append(keyword)
        if found:
            hits[group] = found
    return hits


def analyze_draft(draft: str) -> dict[str, Any]:
    draft = clean_text(draft)
    first_80 = draft[:80]
    first_sentence = sentences(draft)[0] if sentences(draft) else draft[:80]
    hits = keyword_hits(draft)
    flags = {
        "mentions_codex": bool(re.search(r"codex", draft, re.I)),
        "codex_in_first_80_chars": bool(re.search(r"codex", first_80, re.I)),
        "has_numeric_proof": bool(re.search(r"\d+\s*(万|千|天|周|月|块|元|%)?", draft)),
        "has_workflow_packaging": bool(hits.get("workflow")),
        "has_data_thesis": bool(hits.get("data")),
        "has_clear_cta": bool(hits.get("conversion")),
        "has_three_part_structure": bool(re.search(r"第一|第二|第三|一，|二，|三，|首先|接着|最后", draft)),
    }

    gaps: list[str] = []
    if not flags["codex_in_first_80_chars"]:
        gaps.append("开头没有尽早出现 Codex，观众可能先以为这是普通运营复盘。")
    if not flags["has_numeric_proof"]:
        gaps.append("缺少可感知结果，建议前 5 秒给播放、时间、版本迭代或素材库规模。")
    if not flags["has_workflow_packaging"]:
        gaps.append("工作流不是主视觉，建议把三个能力说成一个被 Codex 跑起来的系统。")
    thesis_positions = [draft.find(keyword) for keyword in ["垂域", "提示词", "Codex 写得", "AI 写得"]]
    thesis_positions = [position for position in thesis_positions if position >= 0]
    if thesis_positions and min(thesis_positions) < 120:
        gaps.append("垂域数据观点出现太早，最好先给新版系统的结果，再解释为什么数据决定输出。")
    if not flags["has_clear_cta"]:
        gaps.append("CTA 不够明确，建议绑定关键词，而不是只说关注。")
    if len(draft) > 520:
        gaps.append("口播偏长，适合压成 55-70 秒，三段工作流每段只讲结果。")

    strengths: list[str] = []
    if flags["mentions_codex"]:
        strengths.append("Codex 是明确主角，可以承接账号定位。")
    if flags["has_three_part_structure"]:
        strengths.append("三段式结构已经成立，适合做教学类短视频。")
    if flags["has_data_thesis"]:
        strengths.append("垂域数据观点有方法论价值，能从展示过渡到付费承接。")

    return {
        "first_sentence": first_sentence,
        "char_count": len(draft),
        "keyword_hits": hits,
        "flags": flags,
        "strengths": strengths or ["已有核心事实，但需要更强的结果钩子和案例借鉴。"],
        "gaps": gaps or ["主线成立，重点优化开头证明、案例借鉴和 CTA。"],
        "recommended_rewrite_path": [
            "先事件化：我用 Codex 把短视频工作流推倒重做了。",
            "再给旧版不足：能复盘过去，但不能持续找灵感、拆爆款、改文案。",
            "然后展示新版三件事：看账号、找需求、拆爆款。",
            "最后升维方法论：Codex 写得好不好，取决于持续喂入的垂域数据。",
            "CTA 绑定关键词：回复「内容工作流」体验或进群。",
        ],
    }


def reference_text(ref: dict[str, Any]) -> str:
    fields = [
        ref.get("reference_id"),
        ref.get("platform"),
        ref.get("creator"),
        ref.get("title"),
        ref.get("observed_metric"),
        ref.get("rewrite_notes"),
        " ".join(ref.get("content_intents") or []),
        " ".join(ref.get("title_patterns") or []),
        " ".join(ref.get("usable_for") or []),
        " ".join(ref.get("do_not_copy") or []),
    ]
    deconstruction = ref.get("strategy_deconstruction") or {}
    fields.extend(
        [
            " ".join(deconstruction.get("strategy_tags") or []),
            " ".join(deconstruction.get("hook_types") or []),
            " ".join(deconstruction.get("structure") or []),
            deconstruction.get("hook_reason") or "",
        ]
    )
    return clean_text(" ".join(str(field or "") for field in fields))


def score_reference(ref: dict[str, Any], draft_analysis: dict[str, Any], strategy: dict[str, Any]) -> tuple[float, list[str]]:
    text = reference_text(ref)
    lower_text = text.lower()
    score = float(ref.get("strategy_fit_score") or 0) / 10.0
    reasons: list[str] = []

    for group, keywords in draft_analysis["keyword_hits"].items():
        matches = [keyword for keyword in keywords if keyword.lower() in lower_text]
        if matches:
            weight = 4.0 if group in {"codex", "workflow", "short_video"} else 2.5
            score += weight + min(len(matches), 3)
            reasons.append(f"匹配 {group}: {', '.join(matches[:3])}")

    platform = str(ref.get("platform") or "")
    creator = str(ref.get("creator") or "")
    intents = " ".join(ref.get("content_intents") or [])
    usable = " ".join(ref.get("usable_for") or [])
    title = str(ref.get("title") or "")
    notes = str(ref.get("rewrite_notes") or "")

    if strategy.get("source_policy", {}).get("user_data_first") and (
        "internal" in platform or platform == "script_archive" or bool(ref.get("is_first_party"))
    ):
        score += 6
        reasons.append("用户自己的高分内容优先")
    if draft_analysis["flags"]["has_workflow_packaging"] and ("workflow" in intents or "workflow" in usable or "工作流" in notes):
        score += 7
        reasons.append("可借工作流包装方式")
    if draft_analysis["flags"]["has_data_thesis"] and ("data" in intents or "数据" in notes or "素材" in text):
        score += 5
        reasons.append("可借数据/素材库论证")
    if draft_analysis["flags"]["has_numeric_proof"] and re.search(r"views=|likes=|播放|估值|10块|20万|\d+", text):
        score += 4
        reasons.append("可借数字结果开头")
    if creator == "Yapie程序员哥" or "一人公司" in title or "10块" in title:
        score += 5
        reasons.append("可借 Yapie 的事件化结果表达")
    if "generic tutorials" in " ".join(strategy.get("avoid") or []) and intents == "general_teaching":
        score -= 4
        reasons.append("泛教程适配度下调")

    return score, reasons or ["策略适配分较高，可作为辅助参考"]


def borrow_suggestions(ref: dict[str, Any]) -> list[str]:
    suggestions: list[str] = []
    usable = set(ref.get("usable_for") or [])
    deconstruction = ref.get("strategy_deconstruction") or {}
    if "hook" in usable:
        suggestions.append("借开头方式：先给结果/反差/数字，不先讲概念。")
    if "proof pattern" in usable:
        suggestions.append("借证明方式：用数据、录屏或产物做可信度。")
    if "workflow explanation" in usable or "structure reference" in usable:
        suggestions.append("借结构：把复杂能力拆成 3 个可见动作。")
    if "CTA logic" in usable:
        suggestions.append("借转化：让用户评论关键词获取完整流程。")
    if deconstruction.get("hook_reason"):
        suggestions.append(f"借停留逻辑：{deconstruction['hook_reason']}")
    if not suggestions:
        suggestions.append("只借选题角度和节奏，不借具体表达。")
    return suggestions


def select_references(references: list[dict[str, Any]], draft_analysis: dict[str, Any], strategy: dict[str, Any], top_k: int) -> list[dict[str, Any]]:
    scored = []
    for ref in references:
        if not isinstance(ref, dict):
            continue
        score, reasons = score_reference(ref, draft_analysis, strategy)
        scored.append(
            {
                "reference_id": ref.get("reference_id"),
                "platform": ref.get("platform"),
                "creator": ref.get("creator"),
                "title": ref.get("title"),
                "url": ref.get("url"),
                "score": round(score, 2),
                "match_reasons": reasons,
                "borrow": borrow_suggestions(ref),
                "do_not_copy": ref.get("do_not_copy") or [],
                "rewrite_notes": ref.get("rewrite_notes"),
            }
        )
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def suggested_revision(draft_analysis: dict[str, Any]) -> str:
    return "\n".join(
        [
            "我用 Codex，把短视频工作流推倒重做了。",
            "上一版跑到过 20 万播放，但用下来我发现，它只能复盘过去的数据，还不能持续帮我找灵感、拆爆款、优化文案。",
            "所以这两周，我让 Codex 学会了三件事。",
            "第一，看账号。每天分析作品表现，更新账号方向和运营策略。",
            "第二，找需求。根据运营方向，全网搜真实吐槽、用户痛点和具体案例，先搞清楚大家到底关心什么。",
            "第三，拆爆款。围绕这些话题找相关视频，拆开头、痛点、结构和转化，再反过来优化我的文案。",
            "我现在最大的感受是：Codex 写得好不好，不只看提示词，而是看你有没有持续喂给它垂域数据。",
            "这套升级版我已经放到粉丝群了，想体验的可以回复「内容工作流」。",
        ]
    )


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    analysis = payload["draft_analysis"]
    lines = [
        f"# {payload['run_name']}",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Draft chars: {analysis['char_count']}",
        "",
        "## 原稿诊断",
        "",
        f"- First sentence: {analysis['first_sentence']}",
        "",
        "Strengths:",
    ]
    lines.extend(f"- {item}" for item in analysis["strengths"])
    lines.extend(["", "Gaps:"])
    lines.extend(f"- {item}" for item in analysis["gaps"])
    lines.extend(["", "## 推荐借鉴案例", ""])
    for ref in payload["selected_references"]:
        lines.extend(
            [
                f"### {ref['reference_id']} | score {ref['score']}",
                "",
                f"- Title: {ref.get('title')}",
                f"- Creator: {ref.get('creator')}",
                f"- Why: {'; '.join(ref.get('match_reasons') or [])}",
                f"- Borrow: {'; '.join(ref.get('borrow') or [])}",
                f"- Do not copy: {'; '.join(str(item) for item in (ref.get('do_not_copy') or [])[:5])}",
                "",
            ]
        )
    lines.extend(
        [
            "## 改写方向",
            "",
            "```text",
            payload["suggested_revision"],
            "```",
            "",
            "## 给文案生成器的约束",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["copywriting_constraints"])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a draft and retrieve reusable reference patterns before rewriting.")
    parser.add_argument("workspace", type=Path, help="User-data workspace, e.g. /path/to/client-workspace")
    parser.add_argument("--current-draft", default="")
    parser.add_argument("--draft-file", type=Path)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    if not workspace.exists():
        raise SystemExit(f"workspace not found: {workspace}")

    draft = args.current_draft
    if args.draft_file:
        draft = args.draft_file.read_text(encoding="utf-8")
    draft = clean_text(draft)
    if not draft:
        raise SystemExit("provide --current-draft or --draft-file")

    strategy = load_json(workspace / "config/strategy/strategy-brief.json", default={})
    profile = load_json(workspace / "config/profile/account.profile.json", default={})
    reference_bank = load_json(workspace / "data/benchmarks/current/reference-bank.json", default={"references": []})
    references = reference_bank.get("references") or []

    draft_analysis = analyze_draft(draft)
    selected = select_references(references, draft_analysis, strategy, max(1, args.top_k))

    run_id = args.run_id or f"{datetime.now().date().isoformat()}-copy-reference-match"
    output_root = workspace / "runs" / run_id / "outputs"
    output_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_name": run_id,
        "workflow_id": "copy-optimization-reference-match",
        "generated_at": now_iso(),
        "workspace": str(workspace),
        "inputs": [
            "config/profile/account.profile.json",
            "config/strategy/strategy-brief.json",
            "data/benchmarks/current/reference-bank.json",
        ],
        "original_draft": draft,
        "account_positioning": profile.get("positioning") or profile.get("account_positioning"),
        "strategy_id": strategy.get("strategy_id"),
        "draft_analysis": draft_analysis,
        "selected_references": selected,
        "suggested_revision": suggested_revision(draft_analysis),
        "copywriting_constraints": [
            "必须第一句或第二句出现 Codex，避免被理解成普通运营复盘。",
            "借鉴案例只借结构、节奏、证明方式和 CTA，不复述原句。",
            "先展示旧版不够用和新版能做什么，再讲垂域数据方法论。",
            "三段工作流每段只讲一个结果，不展开完整教程。",
            "CTA 用关键词承接到粉丝群/流程体验，避免泛泛说关注。",
        ],
    }

    json_path = output_root / "copy-reference-match.json"
    md_path = output_root / "copy-reference-match.md"
    manifest_path = workspace / "runs" / run_id / "run.manifest.json"
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    write_json(
        manifest_path,
        {
            "run_id": run_id,
            "workflow_id": "copy-optimization-reference-match",
            "generated_at": payload["generated_at"],
            "inputs": payload["inputs"],
            "outputs": [
                f"runs/{run_id}/outputs/copy-reference-match.json",
                f"runs/{run_id}/outputs/copy-reference-match.md",
            ],
            "notes": "Draft analysis and reference retrieval only. Use selected patterns to rewrite; do not copy reference wording or media.",
        },
    )
    print(f"wrote {json_path}")


if __name__ == "__main__":
    main()
