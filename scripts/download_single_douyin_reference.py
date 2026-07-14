#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from collect_teaching_video_scripts import (
    download_video_file,
    extract_audio_file,
    extract_tikhub_video_detail,
    extract_video_download_url,
    fetch_douyin_detail,
    first_number,
    first_string,
    get_douyin_transcript,
    load_env_file,
    object_record,
    parse_int,
    safe_slug,
    transcribe_audio_with_agent_reach,
    transcribe_audio_with_local_whisper,
)


def parse_aweme_id(value: str) -> str:
    text = value.strip()
    patterns = [
        r"/video/(\d{8,})",
        r"aweme_id=(\d{8,})",
        r"modal_id=(\d{8,})",
        r"(\d{8,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    raise SystemExit(f"could not find Douyin aweme_id in: {value}")


def source_url(value: str, aweme_id: str) -> str:
    text = value.strip()
    if text.startswith(("http://", "https://")):
        return text
    return f"https://www.douyin.com/video/{aweme_id}"


def source_from_detail(detail: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    author = object_record(detail.get("author")) or object_record(detail.get("user")) or object_record(detail.get("author_info"))
    statistics = object_record(detail.get("statistics")) or object_record(detail.get("stats"))
    video = object_record(detail.get("video"))
    title = first_string(detail, ["desc", "title", "description", "item_title", "aweme_title", "content", "caption"])
    creator = first_string(author, ["nickname", "nick_name", "author_name", "name"]) or str(fallback.get("creator") or "")
    aweme_id = first_string(detail, ["aweme_id", "item_id", "group_id", "id"]) or str(fallback.get("id") or "")
    return {
        "platform": "douyin",
        "id": aweme_id,
        "title": title or str(fallback.get("title") or ""),
        "creator": creator,
        "url": str(fallback.get("url") or (f"https://www.douyin.com/video/{aweme_id}" if aweme_id else "")),
        "create_time": detail.get("create_time") or detail.get("publish_time"),
        "duration_ms": parse_int(detail.get("duration") or video.get("duration")),
        "likes": first_number(statistics, ["digg_count", "like_count", "like_cnt"]),
        "comments": first_number(statistics, ["comment_count", "comments"]),
        "shares": first_number(statistics, ["share_count", "shares"]),
        "collects": first_number(statistics, ["collect_count", "favorite_count", "collects"]),
        "views": first_number(statistics, ["play_count", "view_count", "play_cnt"]),
        "raw_statistics": statistics,
    }


def read_transcript(path_value: str) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    if not path.exists():
        return ""
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8", errors="ignore")).strip()


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    source = payload["source"]
    transcript = payload["transcript"]
    text = payload.get("transcript_text") or ""
    lines = [
        f"# {source.get('title') or source.get('id')}",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- URL: {source.get('url')}",
        f"- Creator: {source.get('creator') or '-'}",
        f"- Aweme ID: {source.get('id')}",
        f"- Duration ms: {source.get('duration_ms') or '-'}",
        f"- Likes: {source.get('likes') or 0}",
        f"- Collects: {source.get('collects') or 0}",
        f"- Shares: {source.get('shares') or 0}",
        f"- Comments: {source.get('comments') or 0}",
        f"- Transcript status: {transcript.get('status')}",
        f"- Transcript source: {transcript.get('text_source') or '-'}",
        f"- Transcript chars: {transcript.get('char_count') or 0}",
        f"- Detail file: {transcript.get('raw_path') or '-'}",
        f"- Text file: {transcript.get('clean_path') or '-'}",
        f"- Video file: {transcript.get('video_path') or '-'}",
        f"- Audio file: {transcript.get('audio_path') or '-'}",
        "",
        "## Transcript",
        "",
        text or "_No usable transcript was produced._",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download and parse one Douyin viral reference through TikHub detail, video download, audio extraction, and ASR fallback."
    )
    parser.add_argument("workspace", type=Path)
    parser.add_argument("url_or_aweme_id")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--env-file", type=Path, default=None)
    parser.add_argument("--tikhub-base-url", default="")
    parser.add_argument("--tikhub-api-key-stdin", action="store_true")
    parser.add_argument("--min-transcript-chars", type=int, default=80)
    parser.add_argument("--asr-provider", choices=["auto", "groq", "openai", "local-whisper"], default="local-whisper")
    parser.add_argument("--local-whisper-model", default="small")
    parser.add_argument("--skip-video-download", action="store_true")
    parser.add_argument("--allow-metadata-only", action="store_true")
    args = parser.parse_args()

    if args.env_file:
        load_env_file(args.env_file.expanduser().resolve())

    token = os.getenv("TIKHUB_API_KEY", "").strip()
    if not token and args.tikhub_api_key_stdin:
        token = sys.stdin.readline().strip()
    if not token:
        raise SystemExit("TIKHUB_API_KEY is required. Export it, pass --env-file, or use --tikhub-api-key-stdin.")

    base_url = args.tikhub_base_url.strip() or os.getenv("TIKHUB_BASE_URL", "").strip() or "https://api.tikhub.io"
    workspace = args.workspace.resolve()
    if not workspace.exists():
        raise SystemExit(f"workspace not found: {workspace}")

    aweme_id = parse_aweme_id(args.url_or_aweme_id)
    run_id = args.run_id or f"{datetime.now().date().isoformat()}-douyin-{aweme_id}"
    raw_root = workspace / "data/benchmarks/raw/references/transcript-downloads" / run_id / "douyin"
    output_root = workspace / "runs" / run_id / "outputs"
    raw_root.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)

    item = {
        "platform": "douyin",
        "id": aweme_id,
        "title": "",
        "creator": "",
        "url": source_url(args.url_or_aweme_id, aweme_id),
    }
    transcript = get_douyin_transcript(
        item,
        raw_root,
        token,
        base_url,
        args.min_transcript_chars,
        download_video=not args.skip_video_download,
        transcribe_missing=True,
        asr_provider=args.asr_provider,
        local_whisper_model=args.local_whisper_model,
    )

    detail: dict[str, Any] = {}
    raw_path = transcript.get("raw_path")
    if raw_path and Path(raw_path).exists():
        detail_payload = json.loads(Path(raw_path).read_text(encoding="utf-8", errors="ignore"))
        detail = extract_tikhub_video_detail(detail_payload)
    elif not raw_path:
        detail, detail_path, detail_error = fetch_douyin_detail(item, raw_root, token, base_url)
        if detail_path:
            transcript["raw_path"] = detail_path
        if detail_error and not transcript.get("error"):
            transcript["error"] = detail_error

    if not args.skip_video_download and not transcript.get("video_path") and detail:
        download_url = extract_video_download_url(object_record(detail.get("video"))) or str(transcript.get("download_url") or "")
        if download_url:
            video_path = raw_root / f"{safe_slug(aweme_id, 'douyin')}.mp4"
            saved_video, video_error = download_video_file(download_url, video_path, item["url"])
            if saved_video:
                transcript["video_path"] = saved_video
                audio_path = raw_root / f"{safe_slug(aweme_id, 'douyin')}.mp3"
                saved_audio, audio_error = extract_audio_file(video_path, audio_path)
                if saved_audio:
                    transcript["audio_path"] = saved_audio
                elif audio_error and not transcript.get("error"):
                    transcript["error"] = audio_error
            elif video_error and not transcript.get("error"):
                transcript["error"] = video_error

    if not transcript.get("clean_path") and transcript.get("audio_path"):
        clean_path = raw_root / f"{safe_slug(aweme_id, 'douyin')}.clean.txt"
        errors: list[str] = []
        transcript_text = ""
        text_source = ""
        if args.asr_provider == "local-whisper":
            transcript_text, error = transcribe_audio_with_local_whisper(str(transcript["audio_path"]), clean_path, args.local_whisper_model)
            text_source = "local-whisper"
            if error:
                errors.append(error)
        else:
            transcript_text, error = transcribe_audio_with_agent_reach(str(transcript["audio_path"]), clean_path, args.asr_provider)
            text_source = "agent-reach-asr"
            if error:
                errors.append(error)
            if not transcript_text and args.asr_provider == "auto" and shutil.which("whisper"):
                transcript_text, error = transcribe_audio_with_local_whisper(str(transcript["audio_path"]), clean_path, args.local_whisper_model)
                text_source = "local-whisper"
                if error:
                    errors.append(error)
        if len(transcript_text) >= args.min_transcript_chars:
            transcript.update(
                {
                    "status": "transcribed",
                    "clean_path": str(clean_path),
                    "text_source": text_source,
                    "char_count": len(transcript_text),
                    "preview": transcript_text[:500],
                    "error": "",
                }
            )
        elif errors and not transcript.get("error"):
            transcript["error"] = "\n".join(errors)[-1500:]

    source = source_from_detail(detail, item)
    transcript_text = read_transcript(str(transcript.get("clean_path") or ""))
    payload = {
        "run_name": run_id,
        "workflow_id": "single-douyin-reference-download",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "workspace": str(workspace),
        "raw_root": str(raw_root),
        "source": source,
        "transcript": transcript,
        "transcript_text": transcript_text,
    }

    json_path = output_root / "single-douyin-reference.json"
    md_path = output_root / "single-douyin-reference.md"
    manifest_path = workspace / "runs" / run_id / "run.manifest.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    manifest_path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "workflow_id": "single-douyin-reference-download",
                "generated_at": payload["generated_at"],
                "inputs": ["explicit Douyin URL/aweme_id", "TikHub credential from environment/stdin"],
                "outputs": [
                    str(json_path.relative_to(workspace)),
                    str(md_path.relative_to(workspace)),
                    str(raw_root.parent.relative_to(workspace)),
                ],
                "notes": "Secret key is not persisted. Use this for user-supplied Douyin viral references before strategy decomposition.",
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
    if not args.allow_metadata_only and parse_int(transcript.get("char_count")) < args.min_transcript_chars:
        raise SystemExit("no usable transcript was produced; inspect the output files above for the TikHub/download/ASR error")


if __name__ == "__main__":
    main()
