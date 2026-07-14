#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any


TODAY_CONTEXT = {
    "goal": "补一条15-20秒结果型短入口，用 Codex 直接跑完一个重复流程。",
    "available_materials": [
        "已有 Codex 自动帮你干活旧爆款数据",
        "已有 Codex 短视频运营助手旧代表作数据",
        "已有 Codex 新功能重复劳动脚本草稿",
        "已有 Codex direct-work reference-bank",
    ],
    "avoid": [
        "不讲泛 AI 应用诊断",
        "不讲原理和方法论开场",
        "不把外部搜索当作今天输入",
    ],
}


TOPIC_TEMPLATES: dict[str, dict[str, str]] = {
    "P-codex-001": {
        "id": "D-CODEX-001",
        "title": "我让 Codex 自动看完后台数据，下一条该拍什么它直接列出来。",
        "hook": "我让 Codex 自动看完后台数据，下一条该拍什么它直接列出来。",
        "ai_entry": "把作品数据、评论和历史结论交给 Codex，让它生成复盘日报和下一条拍摄建议。",
        "video_angle": "前2秒展示生成后的复盘表，随后切回后台数据，证明这不是空讲策略。",
    },
    "P-codex-002": {
        "id": "D-CODEX-002",
        "title": "我把一堆录屏素材丢给 Codex，它先帮我找出可剪片段。",
        "hook": "我把一堆录屏素材丢给 Codex，它先帮我找出可剪片段。",
        "ai_entry": "让 Codex 扫描素材文件夹，输出素材清单、可剪片段表和粗剪步骤。",
        "video_angle": "前2秒展示文件夹和输出表对比，重点拍“剪辑前最烦的一步没了”。",
    },
    "P-codex-003": {
        "id": "D-CODEX-003",
        "title": "客户说了一堆需求，我让 Codex 直接整理成报价前清单。",
        "hook": "客户说了一堆需求，我让 Codex 直接整理成报价前清单。",
        "ai_entry": "把客户 brief 输入 Codex，生成需求表、缺失信息、报价框架和跟进记录。",
        "video_angle": "用一段脱敏客户需求做前后对比，突出“报价慢不是不会报价，是资料没整理”。",
    },
    "P-codex-004": {
        "id": "D-CODEX-004",
        "title": "别让 AI 先写文案，先让 Codex 读完 100 条客户评价。",
        "hook": "别让 AI 先写文案，先让 Codex 读完 100 条客户评价。",
        "ai_entry": "让 Codex 把评价/评论分成高频痛点、卖点证据、可拍选题和避坑提醒。",
        "video_angle": "先展示四列表，再讲它怎么直接变成今天能拍的素材。",
    },
    "P-codex-005": {
        "id": "D-CODEX-005",
        "title": "周报别再从零写了，我让 Codex 从任务记录里自动整理。",
        "hook": "周报别再从零写了，我让 Codex 从任务记录里自动整理。",
        "ai_entry": "把任务记录、会议要点和项目状态交给 Codex，生成周报、风险和下周动作。",
        "video_angle": "用零散记录到周报的前后对比，强调“明天就能抄”。",
    },
    "P-codex-006": {
        "id": "D-CODEX-006",
        "title": "我不等灵感了，让 Codex 每天从数据里挑今天该拍什么。",
        "hook": "我不等灵感了，让 Codex 每天从数据里挑今天该拍什么。",
        "ai_entry": "让 Codex 读取痛点库、参考库和账号数据，生成当天 A/B/C 级选题。",
        "video_angle": "直接展示今日选题雷达页面，说明它不是搜索，而是本地运营调度。",
    },
    "P-codex-007": {
        "id": "D-CODEX-007",
        "title": "流程跑完前，我让 Codex 先检查一遍有没有漏项。",
        "hook": "流程跑完前，我让 Codex 先检查一遍有没有漏项。",
        "ai_entry": "把 SOP、样例文件和结果文件交给 Codex，输出漏项清单和补录动作。",
        "video_angle": "前2秒展示漏项清单，适合团队/运营主管场景。",
    },
    "P-codex-008": {
        "id": "D-CODEX-008",
        "title": "Codex 新手先别学一堆命令，先让它跑通一个真实小任务。",
        "hook": "Codex 新手先别学一堆命令，先让它跑通一个真实小任务。",
        "ai_entry": "从读取文件、执行命令、生成报告、写回结果这条最小链路开始。",
        "video_angle": "作为承接层内容，不抢主入口；适合接住看完结果演示的人。",
    },
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def refs_by_pain(reference_bank: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ref in reference_bank.get("references") or []:
        if not isinstance(ref, dict):
            continue
        for pain_id in ref.get("mapped_pain_ids") or []:
            grouped[str(pain_id)].append(ref)
    return grouped


def score_for_pain(pain: dict[str, Any], refs: list[dict[str, Any]]) -> dict[str, int]:
    status = str(pain.get("status") or "")
    role = str(pain.get("target_role") or "")
    freq = str(pain.get("frequency") or "")
    evidence_count = len(pain.get("evidence_ids") or [])
    internal_refs = sum(1 for ref in refs if str(ref.get("platform", "")).endswith("internal") or "internal" in str(ref.get("reference_id", "")))

    pain_score = 5 if status.endswith("_a") or status == "active_a" else 4
    frequency_score = 5 if "daily" in freq else 4 if "weekly" in freq else 3
    demo_score = 5 if any(word in str(pain.get("visible_result", "")) for word in ["表", "清单", "输出", "生成", "自动"]) else 4
    payment_score = 5 if any(word in role for word in ["小老板", "电商", "团队", "服务"]) else 4
    productization_score = 5 if pain.get("convertible_offer") else 4
    strategy_fit = 5 if str(pain.get("pain_id", "")).startswith("P-codex") else 3
    evidence_quality = min(5, 2 + min(2, len(refs)) + (1 if internal_refs or evidence_count >= 3 else 0))

    return {
        "pain": pain_score,
        "frequency": frequency_score,
        "demo": demo_score,
        "payment": payment_score,
        "productization": productization_score,
        "strategy_fit": strategy_fit,
        "evidence_quality": evidence_quality,
    }


def priority(score: dict[str, int]) -> str:
    base = sum(score[key] for key in ["pain", "frequency", "demo", "payment", "productization"]) * 4
    if base >= 92:
        return "A"
    if base >= 80:
        return "B"
    return "C"


def topic_from_pain(pain: dict[str, Any], refs: list[dict[str, Any]]) -> dict[str, Any]:
    pain_id = str(pain.get("pain_id", ""))
    template = TOPIC_TEMPLATES.get(pain_id, {})
    score = score_for_pain(pain, refs)
    evidence = []
    for ref in sorted(refs, key=lambda item: int(item.get("strategy_fit_score") or 0), reverse=True)[:3]:
        evidence.append(f"参考：{ref.get('title', '')}")
    evidence.extend(str(item) for item in (pain.get("evidence_ids") or [])[:2])

    title = template.get("title") or f"让 Codex 跑完这个重复动作：{pain.get('business_scene', '')}"
    return {
        "id": template.get("id") or f"D-{pain_id}",
        "pain_id": pain_id,
        "priority": priority(score),
        "role": pain.get("target_role", ""),
        "scene": pain.get("business_scene", ""),
        "pain": " / ".join(str(item) for item in (pain.get("user_words") or [])[:2]) or pain.get("business_scene", ""),
        "repeated_action": pain.get("repeated_action", ""),
        "ai_entry": template.get("ai_entry") or f"让 Codex 处理：{pain.get('visible_result', '')}",
        "visible_result": pain.get("visible_result", ""),
        "title": title,
        "hook": template.get("hook") or title,
        "video_angle": template.get("video_angle") or "先展示结果，再用一句话解释原来重复动作有多烦。",
        "cta": pain.get("convertible_offer", ""),
        "recording_plan_ref": f"work/plans/recording/{template.get('id') or pain_id}.md",
        "score": score,
        "evidence": evidence,
    }


def build_radar(workspace: Path, run_date: str, limit: int) -> dict[str, Any]:
    account = load_json(workspace / "config/profile" / "account.profile.json")
    audience = load_json(workspace / "config/profile" / "audience.profile.json")
    pain_bank = load_json(workspace / "data/topic-research/current/pain-bank.json")
    reference_bank = load_json(workspace / "data/benchmarks/current/reference-bank.json")
    account_snapshot = load_json(workspace / "data/operations/current/account-snapshot.json")

    grouped_refs = refs_by_pain(reference_bank)
    topics = [topic_from_pain(pain, grouped_refs.get(str(pain.get("pain_id")), [])) for pain in pain_bank.get("pains") or []]
    topics.sort(key=lambda topic: (-(sum(topic["score"][key] for key in ["pain", "frequency", "demo", "payment", "productization"])), topic["id"]))
    topics = topics[:limit]

    primary_audiences = [item.get("label", "") for item in audience.get("primary_audiences") or [] if isinstance(item, dict)]
    overlay = pain_bank.get("strategy_overlay") or {}
    account_id = str(account.get("account_id") or "client-account")
    account_handle = str(account.get("handle") or f"@{account_id}")
    operator = account.get("operator_profile") if isinstance(account.get("operator_profile"), dict) else {}

    return {
        "week": f"daily-{run_date}",
        "date_range": run_date,
        "generated_at": run_date,
        "title": "每日 Codex 干活场景雷达",
        "subtitle": "不重新搜索，只根据现有痛点库、参考库、账号数据和今日状态调度选题",
        "positioning": account.get("positioning", ""),
        "strategy_name": "Codex 直接上场干活",
        "workflow_slug": "daily-scene-radar",
        "action_label": "今日执行",
        "action_section_title": "今日执行",
        "action_subtitle": "进入脚本前，只检查今天能不能录出“Codex 已经搞定”的画面。",
        "footer_label": "每日场景雷达",
        "account_handle": account_handle,
        "operator_profile": {
            "name": operator.get("name") or account.get("display_name") or account_id,
            "label": operator.get("label") or "Short Video Ops",
            "role": operator.get("role") or "Workflow Creator",
            "tagline": operator.get("tagline") or "每条内容先给结果，再解释少做了哪件重复劳动。",
            "avatar": operator.get("avatar") or "./assets/account-avatar.png",
        },
        "account_positioning": {
            "label": "今日策略",
            "one_liner": overlay.get("summary") or "Codex 直接上场干活，把重复劳动干掉。",
            "audience": primary_audiences,
            "core_problem": account_snapshot.get("main_bottleneck", ""),
            "content_promise": "每条内容都是“你看，我让它搞定了”+ 对应痛点 + 观众看完觉得“我也能抄”。",
            "conversion": "评论关键词：日报 / 剪辑 / 报价 / 评价 / 选题 / SOP / 配置。",
            "boundaries": account.get("content_boundaries", []),
        },
        "weekly_question": TODAY_CONTEXT["goal"],
        "source_mix": [
            {
                "source": "抖音评论/私信",
                "use": "使用历史高表现内容和求工作流/模板/按场景改等强需求信号，不重新搜索。",
                "queries": [],
            },
            {
                "source": "B站",
                "use": "本次只读取已归一化 reference-bank，不新增搜索。",
                "queries": [],
            },
            {
                "source": "小红书",
                "use": "本次不搜索，只保留为后续每周补弹药来源。",
                "queries": [],
            },
            {
                "source": "招聘JD/岗位说明",
                "use": "本次不搜索，只用于判断岗位重复动作是否真实。",
                "queries": [],
            },
        ],
        "scoring_rubric": [
            {"key": "pain", "label": "痛感", "question": "这是不是一个用户已经烦到想立刻少做的动作？"},
            {"key": "frequency", "label": "频率", "question": "它是不是每天/每周重复发生？"},
            {"key": "demo", "label": "演示性", "question": "前2秒能不能看到 Codex 跑完后的结果？"},
            {"key": "payment", "label": "付费可能", "question": "这个人群是否有业务/时间/团队成本？"},
            {"key": "productization", "label": "产品化", "question": "能否沉淀成模板、SOP、脚本或轻交付？"},
        ],
        "weekly_strategy": {
            "focus_roles": primary_audiences,
            "content_ratio": {
                "短入口结果演示": "60%",
                "场景拆解": "20%",
                "承接教程": "10%",
                "服务筛选": "10%",
            },
            "selection_rule": "日更轻跑只选已有数据能支撑、无需外部搜索、今天可以录屏验证的题。",
            "avoid": TODAY_CONTEXT["avoid"],
        },
        "topics": topics,
        "weekly_actions": [
            "今天优先拍最高分 A 级题：前2秒只展示 Codex 输出结果。",
            "如果没有后台数据素材，就改拍批量素材整理，仍然保持文件夹前后对比。",
            "结尾只收一个关键词，不解释完整方法论。",
            "把今日选题结果保存到 run 记录，明天继续轻跑对比。",
        ],
        "daily_context": TODAY_CONTEXT,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a local daily scene radar without external search.")
    parser.add_argument("workspace", nargs="?", type=Path)
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    workspace = (args.workspace or Path.cwd()).resolve()
    output = args.output or workspace / "work/topics/daily-scenes.json"
    radar = build_radar(workspace, args.date, args.limit)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(radar, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"updated: {output}")
    print(f"topics: {len(radar['topics'])}")


if __name__ == "__main__":
    main()
