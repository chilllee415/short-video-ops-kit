#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


REFERENCE_BANK_PATH = Path("data/benchmarks/current/reference-bank.json")


INTENT_MAP = {
    "系统展示型": "workflow_packaging",
    "教学拆步型": "tutorial_deconstruction",
    "个人复盘型": "personal_recap",
    "知识付费承接型": "paid_conversion",
    "反焦虑信任型": "anti_anxiety_trust",
    "泛教学型": "general_teaching",
    "成果前置": "result_first",
    "新手友好": "beginner_friendly",
    "反坑/反焦虑": "anti_pitfall",
    "工作流包装": "workflow_packaging",
    "数字框架": "numeric_hook",
    "主题承诺": "topic_promise",
}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"missing file: {path}") from None
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid json: {path}: {exc}") from None
    if not isinstance(data, dict):
        raise SystemExit(f"expected json object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slug(value: str, limit: int = 48) -> str:
    normalized = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", value or "")
    normalized = normalized.strip("-").lower()
    return normalized[:limit].strip("-") or "reference"


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        value = str(value).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def relative_to_workspace(workspace: Path, value: Any) -> str:
    if not value:
        return ""
    path = Path(str(value))
    if path.is_absolute():
        try:
            return str(path.relative_to(workspace))
        except ValueError:
            return str(path)
    return str(path)


def metric_text(source: dict[str, Any]) -> str:
    metric_keys = ["views", "likes", "comments", "shares", "collects"]
    parts = []
    for key in metric_keys:
        value = source.get(key)
        if value not in (None, "", 0, "0"):
            parts.append(f"{key}={value}")
    if source.get("duration_seconds"):
        parts.append(f"duration_seconds={source['duration_seconds']}")
    return ", ".join(parts) if parts else "metadata collected; public metric unavailable"


def mapped_intents(item: dict[str, Any]) -> list[str]:
    hook = item.get("hook") or {}
    raw_tags = list(item.get("strategy_tags") or []) + list(hook.get("hook_types") or [])
    intents = [INTENT_MAP.get(tag, slug(tag, limit=32)) for tag in raw_tags]
    return unique(intents)


def title_patterns(item: dict[str, Any]) -> list[str]:
    hook = item.get("hook") or {}
    raw = list(hook.get("hook_types") or []) + list(item.get("strategy_tags") or [])
    patterns = [f"hook:{tag}" for tag in hook.get("hook_types") or []]
    patterns.extend(f"strategy:{tag}" for tag in item.get("strategy_tags") or [])
    if not patterns:
        patterns = [f"pattern:{tag}" for tag in raw]
    return unique(patterns)


def usable_for(item: dict[str, Any]) -> list[str]:
    result = ["structure reference"]
    hook = item.get("hook") or {}
    if hook.get("hook_types") or hook.get("opening_preview"):
        result.append("hook")
    if item.get("proof_assets"):
        result.append("proof pattern")
    if item.get("workflow_nodes") or any("工作流" in str(tag) for tag in item.get("strategy_tags") or []):
        result.append("workflow explanation")
    cta_style = (item.get("cta") or {}).get("style") or ""
    if cta_style and "弱 CTA" not in cta_style and "无显性 CTA" not in cta_style:
        result.append("CTA logic")
    if item.get("transferable_strategy"):
        result.append("rewrite strategy")
    return unique(result)


def fit_score(item: dict[str, Any]) -> int:
    source = item.get("source") or {}
    transcript = item.get("transcript") or {}
    score = 68
    if source.get("creator"):
        score += 4
    if source.get("likes") or source.get("views"):
        score += 8
    if int(transcript.get("char_count") or 0) >= 300:
        score += 6
    if item.get("strategy_tags"):
        score += 5
    if (item.get("hook") or {}).get("hook_types"):
        score += 5
    if item.get("transferable_strategy"):
        score += 4
    if "收益承诺要弱化" in " ".join(item.get("risks") or []):
        score -= 2
    return max(60, min(score, 96))


def rewrite_notes(item: dict[str, Any]) -> str:
    source = item.get("source") or {}
    hook = item.get("hook") or {}
    points = list(item.get("transferable_strategy") or [])
    if hook.get("why_it_stops_scroll"):
        points.append(f"停留逻辑：{hook['why_it_stops_scroll']}")
    if source.get("creator"):
        points.append(f"只借 {source['creator']} 的结构和策略，不借原句、素材和画面。")
    return " ".join(unique(points)) or "保留选题方向，重写证明方式、案例和 CTA。"


def do_not_copy(item: dict[str, Any]) -> list[str]:
    risks = list(item.get("risks") or [])
    risks.extend(
        [
            "original wording",
            "original footage or audio",
            "creator-specific personal story",
            "unsupported income or valuation claims",
        ]
    )
    return unique(risks)


def compact(value: Any, limit: int = 72) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def dashboard_steps(values: list[Any]) -> list[dict[str, Any]]:
    times = ["0-3s", "3-12s", "12-22s", "22-30s"]
    fallback = [
        "结果前置：先把可见结果亮出来",
        "场景输入：说明用户原来卡在哪里",
        "过程证明：用录屏/文件/表格证明",
        "评论承接：只留一个关键词",
    ]
    raw = unique([str(value) for value in values], limit=4) or fallback
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
                "name": compact(name, 14),
                "desc": compact(desc, 48),
                "hot": index == 0,
            }
        )
    return steps


def dashboard_detail(item: dict[str, Any], strategy: dict[str, Any]) -> dict[str, Any]:
    hook = item.get("hook") or {}
    cta = item.get("cta") or {}
    hook_formula = " + ".join(unique(list(hook.get("hook_types") or []) + list(item.get("strategy_tags") or []), limit=2))
    proof_assets = item.get("proof_assets") or []
    why_works = unique(
        [
            hook.get("why_it_stops_scroll"),
            *(item.get("transferable_strategy") or []),
            *(proof_assets[:1] if isinstance(proof_assets, list) else []),
            "只借结构和证明方式，不照搬原句和画面。",
        ],
        limit=3,
    )
    return {
        "structure": dashboard_steps(item.get("structure") or []),
        "hookFormula": hook_formula or "结果前置 + 结构复用",
        "visualTricks": unique(
            list(item.get("workflow_nodes") or [])[:2]
            + list(item.get("strategy_tags") or [])
            + ["录屏推进", "结果证明"],
            limit=4,
        ),
        "whyWorks": why_works,
        "rewrite": {
            "hook": compact(strategy.get("primary_strategy") or "先展示一个可见结果，再解释用户场景。", 80),
            "script": "前 3 秒先亮出结果；中段用自己的真实场景重拍证明链；结尾只保留一个评论/私信关键词。",
            "cta": strategy.get("conversion_path") or cta.get("style") or "评论关键词进入诊断。",
        },
    }


def reference_id(source: dict[str, Any]) -> str:
    platform = slug(str(source.get("platform") or "reference"), limit=20)
    raw_id = source.get("id") or source.get("url") or source.get("title") or "item"
    return f"R-{platform}-{slug(str(raw_id), limit=64)}"


def normalize_item(
    workspace: Path,
    deconstruction_run_id: str,
    deconstruction: dict[str, Any],
    item: dict[str, Any],
    strategy: dict[str, Any],
) -> dict[str, Any]:
    source = item.get("source") or {}
    transcript = item.get("transcript") or {}
    pain_ids = list(strategy.get("priority_pain_ids") or [])
    if not pain_ids:
        pain_ids = ["unmapped"]

    return {
        "reference_id": reference_id(source),
        "platform": source.get("platform") or "reference",
        "creator": source.get("creator") or "",
        "title": source.get("title") or "",
        "url": source.get("url") or "",
        "observed_metric": metric_text(source),
        "upload_date": source.get("upload_date"),
        "strategy_fit_score": fit_score(item),
        "content_intents": mapped_intents(item),
        "title_patterns": title_patterns(item),
        "mapped_pain_ids": pain_ids,
        "usable_for": usable_for(item),
        "rewrite_notes": rewrite_notes(item),
        "do_not_copy": do_not_copy(item),
        "source_run_id": deconstruction.get("source_run_id"),
        "deconstruction_run_id": deconstruction_run_id,
        "source_strategy": source.get("source_strategy") or source.get("source_query") or "",
        "dashboard_detail": dashboard_detail(item, strategy),
        "transcript": {
            "status": transcript.get("status"),
            "text_source": transcript.get("text_source"),
            "char_count": transcript.get("char_count"),
            "clean_path": relative_to_workspace(workspace, transcript.get("clean_path")),
            "video_path": relative_to_workspace(workspace, transcript.get("video_path")),
            "audio_path": relative_to_workspace(workspace, transcript.get("audio_path")),
        },
        "strategy_deconstruction": {
            "strategy_tags": item.get("strategy_tags") or [],
            "hook_types": (item.get("hook") or {}).get("hook_types") or [],
            "hook_reason": (item.get("hook") or {}).get("why_it_stops_scroll") or "",
            "structure": item.get("structure") or [],
            "proof_assets": item.get("proof_assets") or [],
            "workflow_nodes": item.get("workflow_nodes") or [],
            "concept_bridges": item.get("concept_bridges") or [],
            "cta_style": (item.get("cta") or {}).get("style") or "",
        },
        "ingested_at": now_iso(),
    }


def load_reference_bank(workspace: Path) -> dict[str, Any]:
    path = workspace / REFERENCE_BANK_PATH
    if path.exists():
        return load_json(path)
    return {
        "reference_bank_id": "reference-bank",
        "updated_at": now_iso(),
        "source_run": "",
        "strategy_overlay": {},
        "references": [],
    }


def merge_references(bank: dict[str, Any], additions: list[dict[str, Any]]) -> tuple[dict[str, Any], list[str], list[str]]:
    references = bank.setdefault("references", [])
    if not isinstance(references, list):
        raise SystemExit("reference bank field `references` must be a list")

    by_id = {str(ref.get("reference_id")): index for index, ref in enumerate(references) if isinstance(ref, dict)}
    by_url = {str(ref.get("url")): index for index, ref in enumerate(references) if isinstance(ref, dict) and ref.get("url")}

    inserted: list[str] = []
    updated: list[str] = []
    for ref in additions:
        ref_id = str(ref.get("reference_id"))
        url = str(ref.get("url") or "")
        if ref_id in by_id:
            references[by_id[ref_id]] = {**references[by_id[ref_id]], **ref}
            updated.append(ref_id)
        elif url and url in by_url:
            existing_index = by_url[url]
            existing_id = str(references[existing_index].get("reference_id"))
            references[existing_index] = {**references[existing_index], **ref, "reference_id": existing_id}
            updated.append(existing_id)
        else:
            by_id[ref_id] = len(references)
            if url:
                by_url[url] = len(references)
            references.append(ref)
            inserted.append(ref_id)

    bank["updated_at"] = now_iso()
    return bank, inserted, updated


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# {payload['run_name']}",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Deconstruction run: {payload['deconstruction_run_id']}",
        f"- Source run: {payload.get('source_run_id') or ''}",
        f"- Mode: {payload['mode']}",
        f"- Additions: {len(payload['additions'])}",
        f"- Inserted: {len(payload['inserted_reference_ids'])}",
        f"- Updated: {len(payload['updated_reference_ids'])}",
        "",
        "## References",
        "",
    ]
    for ref in payload["additions"]:
        lines.extend(
            [
                f"### {ref['reference_id']}",
                "",
                f"- Title: {ref.get('title')}",
                f"- Creator: {ref.get('creator')}",
                f"- Metrics: {ref.get('observed_metric')}",
                f"- Score: {ref.get('strategy_fit_score')}",
                f"- Borrow: {', '.join(ref.get('usable_for') or [])}",
                f"- Notes: {ref.get('rewrite_notes')}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote a 04c reference deconstruction run into the durable reference bank.")
    parser.add_argument("workspace", type=Path, help="User-data workspace, e.g. /path/to/client-workspace")
    parser.add_argument("--deconstruction-run-id", required=True)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--write-bank", action="store_true", help="Update data/benchmarks/current/reference-bank.json. Omit for dry run.")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    if not workspace.exists():
        raise SystemExit(f"workspace not found: {workspace}")

    deconstruction_path = workspace / "runs" / args.deconstruction_run_id / "outputs/reference-strategy-deconstruction.json"
    deconstruction = load_json(deconstruction_path)
    strategy_path = workspace / "config/strategy/strategy-brief.json"
    strategy = load_json(strategy_path) if strategy_path.exists() else {}

    additions = [
        normalize_item(workspace, args.deconstruction_run_id, deconstruction, item, strategy)
        for item in deconstruction.get("decompositions", [])
        if isinstance(item, dict)
    ]
    if not additions:
        raise SystemExit("no decompositions found to promote")

    run_id = args.run_id or f"{datetime.now().date().isoformat()}-reference-bank-ingest"
    output_root = workspace / "runs" / run_id / "outputs"
    output_root.mkdir(parents=True, exist_ok=True)

    bank = load_reference_bank(workspace)
    merged_bank, inserted, updated = merge_references(bank, additions)
    mode = "write_bank" if args.write_bank else "dry_run"

    if args.write_bank:
        write_json(workspace / REFERENCE_BANK_PATH, merged_bank)

    payload = {
        "run_name": run_id,
        "workflow_id": "reference-bank-ingest",
        "generated_at": now_iso(),
        "workspace": str(workspace),
        "mode": mode,
        "deconstruction_run_id": args.deconstruction_run_id,
        "source_run_id": deconstruction.get("source_run_id"),
        "inputs": [
            str(deconstruction_path.relative_to(workspace)),
            "config/strategy/strategy-brief.json",
            str(REFERENCE_BANK_PATH),
        ],
        "outputs": [
            f"runs/{run_id}/outputs/reference-bank-additions.json",
            f"runs/{run_id}/outputs/reference-bank-additions.md",
        ],
        "bank_written": args.write_bank,
        "inserted_reference_ids": inserted,
        "updated_reference_ids": updated,
        "additions": additions,
    }

    json_path = output_root / "reference-bank-additions.json"
    md_path = output_root / "reference-bank-additions.md"
    manifest_path = workspace / "runs" / run_id / "run.manifest.json"
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    write_json(
        manifest_path,
        {
            "run_id": run_id,
            "workflow_id": "reference-bank-ingest",
            "generated_at": payload["generated_at"],
            "inputs": payload["inputs"],
            "outputs": payload["outputs"] + ([str(REFERENCE_BANK_PATH)] if args.write_bank else []),
            "bank_written": args.write_bank,
            "inserted_reference_ids": inserted,
            "updated_reference_ids": updated,
            "notes": "Promotes strategy deconstruction into durable reference-bank entries. Original wording/media remain source-only and must not be copied.",
        },
    )
    print(f"wrote {json_path}")
    if args.write_bank:
        print(f"updated {workspace / REFERENCE_BANK_PATH}")
    else:
        print("dry run only; pass --write-bank to update reference-bank.json")


if __name__ == "__main__":
    main()
