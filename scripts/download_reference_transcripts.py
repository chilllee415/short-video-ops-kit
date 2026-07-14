#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from collect_teaching_video_scripts import (
    DEFAULT_BILIBILI_QUERIES,
    DEFAULT_DOUYIN_QUERIES,
    DEFAULT_YOUTUBE_QUERIES,
    TIKHUB_STRATEGY_ENDPOINTS,
    bilibili_hot,
    bilibili_rank,
    bilibili_search,
    dedupe,
    douyin_tikhub_billboard,
    download_youtube_subtitle,
    excluded_without_body,
    get_bilibili_detail,
    get_douyin_transcript,
    has_usable_body,
    load_env_file,
    normalize_bilibili,
    normalize_youtube,
    parse_int,
    score_candidate,
    youtube_search,
)


def source_from_candidate(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "platform": item.get("platform"),
        "creator": item.get("creator"),
        "title": item.get("title"),
        "url": item.get("url"),
        "id": item.get("id"),
        "views": item.get("views"),
        "likes": item.get("likes"),
        "comments": item.get("comments"),
        "shares": item.get("shares"),
        "collects": item.get("collects"),
        "upload_date": item.get("upload_date"),
        "duration_seconds": item.get("duration_seconds"),
        "source_query": item.get("source_query"),
        "source_strategy": item.get("source_strategy"),
    }


def read_transcript_text(transcript: dict[str, Any]) -> str:
    clean_path = transcript.get("clean_path")
    if clean_path and Path(clean_path).exists():
        return Path(clean_path).read_text(encoding="utf-8", errors="ignore")
    return ""


def collection_item(candidate: dict[str, Any], transcript: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": source_from_candidate(candidate),
        "transcript": transcript,
        "transcript_text": read_transcript_text(transcript),
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# {payload['run_name']}",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Workspace: {payload['workspace']}",
        f"- YouTube candidates: {payload['counts']['youtube_candidates']}",
        f"- Bilibili candidates: {payload['counts']['bilibili_candidates']}",
        f"- Douyin candidates: {payload['counts']['douyin_candidates']}",
        f"- Downloaded transcript items: {payload['counts']['downloaded_items']}",
        f"- Excluded without usable body: {payload['counts']['excluded_no_transcript']}",
        "",
        "## Downloaded Items",
        "",
    ]
    for index, item in enumerate(payload["items"], start=1):
        source = item.get("source") or {}
        transcript = item.get("transcript") or {}
        lines.extend(
            [
                f"### {index}. {source.get('title')}",
                "",
                f"- Platform: {source.get('platform')}",
                f"- URL: {source.get('url')}",
                f"- Transcript status: {transcript.get('status')}",
                f"- Transcript source: {transcript.get('text_source') or '-'}",
                f"- Transcript chars: {transcript.get('char_count')}",
                f"- Text file: {transcript.get('clean_path')}",
                f"- Video file: {transcript.get('video_path') or '-'}",
                f"- Audio file: {transcript.get('audio_path') or '-'}",
                "",
            ]
        )
    excluded = payload.get("excluded_no_transcript") or []
    if excluded:
        lines.extend(["## Excluded Without Usable Body", ""])
        for index, item in enumerate(excluded, start=1):
            source = item.get("source") or {}
            transcript = item.get("transcript") or {}
            lines.append(f"- {index}. {source.get('platform')} | {source.get('title')} | {transcript.get('status')} | {item.get('reason')}")
    path.write_text("\n".join(lines), encoding="utf-8")


def load_research_plan(workspace: Path, plan_run_id: str) -> dict[str, Any]:
    plan_path = workspace / "runs" / plan_run_id / "outputs" / "reference-research-plan.json"
    if not plan_path.exists():
        raise SystemExit(f"reference research plan not found: {plan_path}")
    try:
        value = json.loads(plan_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid reference research plan: {plan_path}: {exc}") from None
    if not isinstance(value, dict):
        raise SystemExit(f"reference research plan must be a JSON object: {plan_path}")
    return value


def plan_queries(plan: dict[str, Any], platform: str) -> list[str]:
    groups = plan.get("query_groups") or {}
    values = groups.get(platform) or []
    return [str(value).strip() for value in values if str(value).strip()]


def plan_int(plan: dict[str, Any], section: str, key: str, fallback: int) -> int:
    value = (plan.get(section) or {}).get(key)
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return parsed if parsed >= 0 else fallback


def plan_bool(plan: dict[str, Any], section: str, key: str, fallback: bool) -> bool:
    value = (plan.get(section) or {}).get(key)
    if isinstance(value, bool):
        return value
    return fallback


def plan_str(plan: dict[str, Any], section: str, key: str, fallback: str) -> str:
    value = (plan.get(section) or {}).get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def main() -> None:
    parser = argparse.ArgumentParser(description="Download reference video transcripts only. No strategy decomposition is performed.")
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--plan-run-id", default="")
    parser.add_argument("--youtube-query", action="append", default=[])
    parser.add_argument("--bilibili-query", action="append", default=[])
    parser.add_argument("--douyin-query", action="append", default=[])
    parser.add_argument("--per-query", type=int, default=6)
    parser.add_argument("--min-youtube-views", type=int, default=50_000)
    parser.add_argument("--min-bilibili-views", type=int, default=50_000)
    parser.add_argument("--min-douyin-likes", type=int, default=1_000)
    parser.add_argument("--min-score", type=int, default=30)
    parser.add_argument("--max-youtube-transcripts", type=int, default=6)
    parser.add_argument("--max-bilibili-transcripts", type=int, default=3)
    parser.add_argument("--max-douyin-transcripts", type=int, default=6)
    parser.add_argument("--bilibili-hot-limit", type=int, default=0)
    parser.add_argument("--bilibili-rank-limit", type=int, default=0)
    parser.add_argument("--douyin-limit", type=int, default=8)
    parser.add_argument("--douyin-strategy", action="append", choices=sorted(TIKHUB_STRATEGY_ENDPOINTS), default=[])
    parser.add_argument("--env-file", type=Path, default=None)
    parser.add_argument("--tikhub-base-url", default="")
    parser.add_argument("--min-transcript-chars", type=int, default=120)
    parser.add_argument("--allow-description-body", action="store_true")
    parser.add_argument("--allow-metadata-only", action="store_true")
    parser.add_argument("--download-douyin-video", action="store_true")
    parser.add_argument("--transcribe-missing", action="store_true")
    parser.add_argument("--asr-provider", choices=["auto", "groq", "openai", "local-whisper"], default="auto")
    parser.add_argument("--local-whisper-model", default="tiny")
    args = parser.parse_args()

    if args.env_file:
        load_env_file(args.env_file.expanduser().resolve())

    workspace = args.workspace.resolve()
    if not workspace.exists():
        raise SystemExit(f"workspace not found: {workspace}")

    research_plan = load_research_plan(workspace, args.plan_run_id) if args.plan_run_id else {}
    if research_plan:
        args.per_query = plan_int(research_plan, "download_args", "per_query", args.per_query)
        args.min_youtube_views = plan_int(research_plan, "download_args", "min_youtube_views", args.min_youtube_views)
        args.min_bilibili_views = plan_int(research_plan, "download_args", "min_bilibili_views", args.min_bilibili_views)
        args.min_douyin_likes = plan_int(research_plan, "download_args", "min_douyin_likes", args.min_douyin_likes)
        args.max_youtube_transcripts = plan_int(research_plan, "download_args", "max_youtube_transcripts", args.max_youtube_transcripts)
        args.max_bilibili_transcripts = plan_int(research_plan, "download_args", "max_bilibili_transcripts", args.max_bilibili_transcripts)
        args.max_douyin_transcripts = plan_int(research_plan, "download_args", "max_douyin_transcripts", args.max_douyin_transcripts)
        args.douyin_limit = plan_int(research_plan, "download_args", "douyin_limit", args.douyin_limit)
        args.min_transcript_chars = plan_int(research_plan, "download_args", "min_transcript_chars", args.min_transcript_chars)
        args.download_douyin_video = plan_bool(research_plan, "download_args", "download_douyin_video", args.download_douyin_video)
        args.transcribe_missing = plan_bool(research_plan, "download_args", "transcribe_missing", args.transcribe_missing)
        args.asr_provider = plan_str(research_plan, "download_args", "asr_provider", args.asr_provider)
        args.local_whisper_model = plan_str(research_plan, "download_args", "local_whisper_model", args.local_whisper_model)

    run_id = args.run_id or f"{datetime.now().date().isoformat()}-reference-transcript-download"
    raw_root = workspace / "data/benchmarks/raw/references/transcript-downloads" / run_id
    output_root = workspace / "runs" / run_id / "outputs"
    raw_root.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)

    youtube_queries = args.youtube_query or plan_queries(research_plan, "youtube") or DEFAULT_YOUTUBE_QUERIES
    bilibili_queries = args.bilibili_query or plan_queries(research_plan, "bilibili") or DEFAULT_BILIBILI_QUERIES
    douyin_queries = args.douyin_query or plan_queries(research_plan, "douyin") or DEFAULT_DOUYIN_QUERIES
    douyin_strategies = args.douyin_strategy or ["high_like", "high_completion", "low_fan"]
    tikhub_token = os.getenv("TIKHUB_API_KEY", "").strip()
    tikhub_base_url = args.tikhub_base_url.strip() or os.getenv("TIKHUB_BASE_URL", "").strip() or "https://api.tikhub.io"

    youtube_candidates: list[dict[str, Any]] = []
    for query in youtube_queries:
        youtube_candidates.extend(normalize_youtube(item, query) for item in youtube_search(query, args.per_query))
    bilibili_candidates: list[dict[str, Any]] = []
    for query in bilibili_queries:
        bilibili_candidates.extend(normalize_bilibili(item, query) for item in bilibili_search(query, args.per_query))
    bilibili_candidates.extend(normalize_bilibili(item, "bilibili_hot") for item in bilibili_hot(args.bilibili_hot_limit))
    bilibili_candidates.extend(normalize_bilibili(item, "bilibili_rank") for item in bilibili_rank(args.bilibili_rank_limit))

    douyin_candidates: list[dict[str, Any]] = []
    if tikhub_token:
        for query in douyin_queries:
            douyin_candidates.extend(
                douyin_tikhub_billboard(query, douyin_strategies, args.douyin_limit, tikhub_base_url, tikhub_token, raw_root / "douyin")
            )

    youtube_candidates = [
        item for item in dedupe(youtube_candidates)
        if parse_int(item.get("views")) >= args.min_youtube_views and score_candidate(item) > args.min_score
    ]
    bilibili_candidates = [
        item for item in dedupe(bilibili_candidates)
        if parse_int(item.get("views")) >= args.min_bilibili_views and score_candidate(item) > args.min_score
    ]
    douyin_candidates = [
        item for item in dedupe(douyin_candidates)
        if (
            parse_int(item.get("likes")) >= args.min_douyin_likes
            or parse_int(item.get("views")) >= args.min_youtube_views
            or score_candidate(item) > args.min_score
        )
    ]

    youtube_candidates.sort(key=lambda item: (score_candidate(item), parse_int(item.get("views"))), reverse=True)
    bilibili_candidates.sort(key=lambda item: (score_candidate(item), parse_int(item.get("views"))), reverse=True)
    douyin_candidates.sort(key=lambda item: (score_candidate(item), parse_int(item.get("likes")), parse_int(item.get("views"))), reverse=True)

    items: list[dict[str, Any]] = []
    excluded_no_transcript: list[dict[str, Any]] = []

    def append_download(candidate: dict[str, Any], transcript: dict[str, Any]) -> None:
        if args.allow_metadata_only or has_usable_body(transcript, args.min_transcript_chars, allow_description_body=args.allow_description_body):
            items.append(collection_item(candidate, transcript))
        else:
            excluded_no_transcript.append(excluded_without_body(candidate, transcript, args.min_transcript_chars))

    for candidate in youtube_candidates[: args.max_youtube_transcripts]:
        append_download(candidate, download_youtube_subtitle(candidate, raw_root / "youtube"))
    for candidate in bilibili_candidates[: args.max_bilibili_transcripts]:
        append_download(candidate, get_bilibili_detail(candidate, raw_root / "bilibili"))
    for candidate in douyin_candidates[: args.max_douyin_transcripts]:
        append_download(
            candidate,
            get_douyin_transcript(
                candidate,
                raw_root / "douyin",
                tikhub_token,
                tikhub_base_url,
                args.min_transcript_chars,
                download_video=args.download_douyin_video,
                transcribe_missing=args.transcribe_missing,
                asr_provider=args.asr_provider,
                local_whisper_model=args.local_whisper_model,
            ),
        )

    payload = {
        "run_name": run_id,
        "workflow_id": "reference-transcript-download",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "workspace": str(workspace),
        "raw_root": str(raw_root),
        "source_plan_run_id": args.plan_run_id,
        "source_plan": {
            "content_scene": research_plan.get("content_scene"),
            "stage_direction": research_plan.get("stage_direction"),
            "priority_pain_ids": research_plan.get("priority_pain_ids"),
        } if research_plan else {},
        "queries": {
            "youtube": youtube_queries,
            "bilibili": bilibili_queries,
            "douyin": douyin_queries,
            "douyin_strategies": douyin_strategies,
            "tikhub_configured": bool(tikhub_token),
        },
        "filters": {
            "per_query": args.per_query,
            "min_youtube_views": args.min_youtube_views,
            "min_bilibili_views": args.min_bilibili_views,
            "min_douyin_likes": args.min_douyin_likes,
            "min_score": args.min_score,
            "min_transcript_chars": args.min_transcript_chars,
            "allow_description_body": args.allow_description_body,
            "allow_metadata_only": args.allow_metadata_only,
            "download_douyin_video": args.download_douyin_video,
            "transcribe_missing": args.transcribe_missing,
            "asr_provider": args.asr_provider,
            "local_whisper_model": args.local_whisper_model,
        },
        "counts": {
            "youtube_candidates": len(youtube_candidates),
            "bilibili_candidates": len(bilibili_candidates),
            "douyin_candidates": len(douyin_candidates),
            "downloaded_items": len(items),
            "excluded_no_transcript": len(excluded_no_transcript),
        },
        "candidates": {
            "youtube": youtube_candidates,
            "bilibili": bilibili_candidates,
            "douyin": douyin_candidates,
        },
        "items": items,
        "excluded_no_transcript": excluded_no_transcript,
    }

    json_path = output_root / "reference-transcript-collection.json"
    md_path = output_root / "reference-transcript-collection.md"
    manifest_path = workspace / "runs" / run_id / "run.manifest.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    manifest_path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "workflow_id": "reference-transcript-download",
                "generated_at": payload["generated_at"],
                "inputs": [
                    f"runs/{args.plan_run_id}/outputs/reference-research-plan.json" if args.plan_run_id else "platform search queries",
                    "TikHub credential" if tikhub_token else "TikHub not configured",
                ],
                "outputs": [str(json_path.relative_to(workspace)), str(md_path.relative_to(workspace)), str(raw_root.relative_to(workspace))],
                "notes": "Downloads/transcribes reference body text only. Strategy decomposition runs separately.",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    print(f"wrote {manifest_path}")
    print(f"raw files: {raw_root}")


if __name__ == "__main__":
    main()
