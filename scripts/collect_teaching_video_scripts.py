#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_YOUTUBE_QUERIES = [
    "AI agents clearly explained",
    "ChatGPT agent tutorial automation",
    "AI automation tutorial for beginners",
    "AI workflow tutorial content creation",
    "Claude Code tutorial AI agents",
]

DEFAULT_BILIBILI_QUERIES = [
    "AI 教程 工作流",
    "AI 自动化 工作流 教程",
    "普通人 学 AI 教程",
    "AI 自媒体 工作流",
    "AI Agent 帮你干活 教程",
]

DEFAULT_DOUYIN_QUERIES = [
    "AI 教程",
    "AI 工作流",
    "AI 自动化",
    "AI 自媒体",
    "AI Agent",
    "Codex",
]

TIKHUB_STRATEGY_ENDPOINTS = {
    "low_fan": "/api/v1/douyin/billboard/fetch_hot_total_low_fan_list",
    "high_like": "/api/v1/douyin/billboard/fetch_hot_total_high_like_list",
    "high_completion": "/api/v1/douyin/billboard/fetch_hot_total_high_play_list",
    "high_growth": "/api/v1/douyin/billboard/fetch_hot_total_high_fan_list",
}

TIKHUB_STRATEGY_LABELS = {
    "low_fan": "低粉爆款",
    "high_like": "高点赞率",
    "high_completion": "高完播率",
    "high_growth": "高涨粉率",
}

TRANSCRIPT_KEYS = [
    "transcript",
    "transcription",
    "original_text",
    "originalText",
    "asr_text",
    "asrText",
    "subtitle",
    "subtitles",
    "caption",
    "captions",
    "ocr_text",
    "ocrText",
]

DESCRIPTION_TEXT_KEYS = [
    "desc",
    "description",
    "content",
    "text",
    "share_title",
]

TEACHING_KEYWORDS = [
    "tutorial",
    "guide",
    "explained",
    "beginner",
    "course",
    "learn",
    "step-by-step",
    "workflow",
    "教程",
    "教学",
    "讲透",
    "小白",
    "入门",
    "手把手",
    "工作流",
]

AI_KEYWORDS = [
    "ai",
    "agent",
    "agents",
    "chatgpt",
    "claude",
    "codex",
    "automation",
    "自动化",
    "智能体",
    "工作流",
]

CTA_KEYWORDS = [
    "comment",
    "subscribe",
    "link in",
    "description",
    "course",
    "community",
    "newsletter",
    "评论",
    "关注",
    "私信",
    "资料",
    "课程",
    "星球",
    "领取",
]


def run_command(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


def parse_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    text = str(value or "").replace(",", "").strip().strip("'\"")
    if not text:
        return 0
    match = re.search(r"\d+", text)
    return int(match.group()) if match else 0


def parse_duration_seconds(value: Any) -> int:
    if isinstance(value, int):
        return value
    text = str(value or "").strip().strip("'\"")
    if not text:
        return 0
    if text.isdigit():
        return int(text)
    parts = [parse_int(part) for part in text.split(":")]
    total = 0
    for part in parts:
        total = total * 60 + part
    return total


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in os.environ:
            continue
        os.environ[key] = value.strip().strip("'\"")


def safe_slug(value: str, default: str = "item") -> str:
    slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "-", value.strip())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return (slug or default)[:80]


def object_record(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def string_value(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    return ""


def first_string(record: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = string_value(record.get(key))
        if value:
            return value
    return ""


def first_number(record: dict[str, Any], keys: list[str]) -> int:
    for key in keys:
        value = parse_int(record.get(key))
        if value:
            return value
    return 0


def is_http_url(value: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def youtube_search(query: str, limit: int) -> list[dict[str, Any]]:
    if not shutil.which("yt-dlp"):
        return []
    proc = run_command(["yt-dlp", "--dump-json", "--ignore-errors", f"ytsearch{limit}:{query}"], timeout=180)
    rows: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def parse_bili_search(stdout: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw_line in stdout.splitlines():
        line = raw_line.rstrip()
        if line.startswith("- "):
            if current:
                rows.append(current)
            current = {}
            line = line[2:]
        elif current is None:
            continue
        else:
            line = line.strip()
        if ":" not in line or current is None:
            continue
        key, value = line.split(":", 1)
        current[key.strip()] = value.strip().strip("'\"")
    if current:
        rows.append(current)
    return [row for row in rows if row.get("bvid") or row.get("id")]


def parse_bili_json(stdout: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return parse_bili_search(stdout)
    data = payload.get("data") if isinstance(payload, dict) else payload
    if isinstance(data, dict):
        items = data.get("items") or []
    else:
        items = data
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict) and (item.get("bvid") or item.get("id"))]


def bilibili_search(query: str, limit: int) -> list[dict[str, Any]]:
    if not shutil.which("bili"):
        return []
    proc = run_command(["bili", "search", query, "--type", "video", "-n", str(limit), "--json"], timeout=120)
    return parse_bili_json(proc.stdout)


def bilibili_hot(limit: int) -> list[dict[str, Any]]:
    if limit <= 0 or not shutil.which("bili"):
        return []
    proc = run_command(["bili", "hot", "-n", str(limit), "--json"], timeout=120)
    return parse_bili_json(proc.stdout)


def bilibili_rank(limit: int) -> list[dict[str, Any]]:
    if limit <= 0 or not shutil.which("bili"):
        return []
    proc = run_command(["bili", "rank", "-n", str(limit), "--json"], timeout=120)
    return parse_bili_json(proc.stdout)


def normalize_youtube(item: dict[str, Any], query: str) -> dict[str, Any]:
    video_id = str(item.get("id") or "")
    url = str(item.get("webpage_url") or "")
    if not url and video_id:
        url = f"https://www.youtube.com/watch?v={video_id}"
    return {
        "platform": "youtube",
        "source_query": query,
        "id": video_id,
        "title": str(item.get("title") or ""),
        "creator": str(item.get("channel") or item.get("uploader") or ""),
        "url": url,
        "views": parse_int(item.get("view_count")),
        "upload_date": str(item.get("upload_date") or ""),
        "duration_seconds": parse_duration_seconds(item.get("duration")),
        "description": str(item.get("description") or ""),
    }


def normalize_bilibili(item: dict[str, Any], query: str) -> dict[str, Any]:
    bvid = str(item.get("bvid") or item.get("id") or "")
    owner = item.get("owner") if isinstance(item.get("owner"), dict) else {}
    stats = item.get("stats") if isinstance(item.get("stats"), dict) else {}
    return {
        "platform": "bilibili",
        "source_query": query,
        "id": bvid,
        "title": str(item.get("title") or ""),
        "creator": str(item.get("author") or owner.get("name") or ""),
        "url": str(item.get("url") or (f"https://www.bilibili.com/video/{bvid}" if bvid else "")),
        "views": parse_int(item.get("play") or stats.get("view")),
        "upload_date": "",
        "duration_seconds": parse_duration_seconds(item.get("duration_seconds") or item.get("duration")),
        "description": str(item.get("description") or ""),
    }


def tikhub_fetch_json(
    endpoint: str,
    token: str,
    base_url: str,
    *,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    timeout: int = 90,
) -> Any:
    url = f"{base_url.rstrip('/')}{endpoint}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "authorization": f"Bearer {token}",
            "content-type": "application/json",
            "user-agent": "short-video-ops-teaching-script-mining/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="ignore"))


def extract_tikhub_video_detail(value: Any) -> dict[str, Any]:
    root = object_record(value)
    data = object_record(root.get("data"))
    candidates = [
        object_record(data.get("aweme_detail")),
        object_record(data.get("aweme")),
        object_record(data.get("aweme_info")),
        object_record(data.get("data")),
        data,
        object_record(root.get("aweme_detail")),
        object_record(root.get("aweme_info")),
    ]
    for candidate in candidates:
        if candidate and (candidate.get("video") or candidate.get("aweme_id") or candidate.get("desc")):
            return candidate
    return {}


def unwrap_aweme_record(record: dict[str, Any]) -> dict[str, Any]:
    data = object_record(record.get("data"))
    candidates = [
        object_record(record.get("aweme_detail")),
        object_record(record.get("aweme_info")),
        object_record(record.get("aweme")),
        object_record(record.get("item")),
        object_record(data.get("aweme_detail")),
        object_record(data.get("aweme_info")),
        object_record(data.get("aweme")),
        record,
    ]
    for candidate in candidates:
        if candidate and (candidate.get("video") or candidate.get("aweme_id") or candidate.get("desc") or candidate.get("title")):
            return candidate
    return record


def collect_tikhub_video_records(value: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def visit(node: Any) -> None:
        if isinstance(node, list):
            for child in node:
                visit(child)
            return
        record = object_record(node)
        if not record:
            return
        candidate = unwrap_aweme_record(record)
        has_id = first_string(candidate, ["aweme_id", "item_id", "group_id", "id"])
        has_text = first_string(candidate, ["desc", "title", "description", "caption", "content"])
        if has_id and (has_text or candidate.get("video") or candidate.get("statistics")):
            rows.append(candidate)
        for child in record.values():
            if isinstance(child, list):
                visit(child)
            elif isinstance(child, dict) and child is not record:
                nested = unwrap_aweme_record(child)
                nested_id = first_string(nested, ["aweme_id", "item_id", "group_id", "id"])
                nested_text = first_string(nested, ["desc", "title", "description", "caption", "content"])
                if nested_id and (nested_text or nested.get("video") or nested.get("statistics")):
                    rows.append(nested)

    visit(value)
    return dedupe_records(rows)


def extract_tikhub_billboard_records(value: Any) -> list[dict[str, Any]]:
    root = object_record(value)
    outer_data = object_record(root.get("data"))
    inner_data = object_record(outer_data.get("data"))
    for node in [inner_data.get("objs"), outer_data.get("objs"), root.get("data")]:
        if isinstance(node, list):
            rows = [unwrap_aweme_record(object_record(item)) for item in node]
            rows = [item for item in rows if item]
            if rows:
                return dedupe_records(rows)
    return collect_tikhub_video_records(value)


def extract_tikhub_video_search_records(value: Any) -> list[dict[str, Any]]:
    root = object_record(value)
    data = object_record(root.get("data"))
    business_data = data.get("business_data")
    records: list[dict[str, Any]] = []
    if isinstance(business_data, list):
        for item in business_data:
            row = object_record(object_record(object_record(item).get("data")).get("aweme_info"))
            if row:
                records.append(row)
    if records:
        return dedupe_records(records)
    aweme_list = data.get("aweme_list")
    if isinstance(aweme_list, list):
        return dedupe_records([unwrap_aweme_record(object_record(item)) for item in aweme_list])
    return collect_tikhub_video_records(value)


def dedupe_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for record in records:
        key = first_string(record, ["aweme_id", "item_id", "group_id", "id"]) or first_string(record, ["desc", "title"])[:120]
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(record)
    return result


def extract_video_download_url(video: dict[str, Any]) -> str:
    candidates = [
        object_record(video.get("download_addr")),
        object_record(video.get("play_addr")),
        object_record(video.get("play_addr_h264")),
    ]
    bit_rate = video.get("bit_rate")
    if isinstance(bit_rate, list):
        for item in bit_rate:
            candidates.append(object_record(object_record(item).get("play_addr")))
    for candidate in candidates:
        url_list = candidate.get("url_list")
        if isinstance(url_list, list):
            for url in url_list:
                text = string_value(url)
                if is_http_url(text):
                    return text
        direct_url = first_string(candidate, ["url", "uri"])
        if is_http_url(direct_url):
            return direct_url
    return ""


def normalize_douyin_original_url(value: str) -> str:
    if is_http_url(value):
        return value
    if re.fullmatch(r"\d{8,}", value.strip()):
        return f"https://www.douyin.com/video/{value.strip()}"
    return ""


def normalize_douyin_record(record: dict[str, Any], query: str, strategy: str, index: int) -> dict[str, Any]:
    row = unwrap_aweme_record(record)
    author = object_record(row.get("author")) or object_record(row.get("user")) or object_record(row.get("author_info"))
    statistics = object_record(row.get("statistics")) or object_record(row.get("stats"))
    video = object_record(row.get("video"))
    aweme_id = first_string(row, ["aweme_id", "item_id", "group_id", "id"])
    title = first_string(row, ["desc", "title", "description", "item_title", "aweme_title", "content", "caption"]) or f"{query}相关爆款"
    creator = first_string(author, ["nickname", "nick_name", "author_name", "name"]) or first_string(row, ["nickname", "author", "author_name"]) or "抖音创作者"
    source_url = first_string(row, ["share_url", "aweme_url", "douyin_url", "detail_url", "url"])
    likes = first_number(statistics, ["digg_count", "like_count", "like_cnt"]) or first_number(row, ["digg_count", "like_count", "like_cnt"])
    comments = first_number(statistics, ["comment_count", "comments"]) or first_number(row, ["comment_count", "comments"])
    shares = first_number(statistics, ["share_count", "shares"]) or first_number(row, ["share_count", "shares"])
    collects = first_number(statistics, ["collect_count", "favorite_count", "collects"]) or first_number(row, ["collect_count", "favorite_count", "collects"])
    views = first_number(statistics, ["play_count", "view_count", "play_cnt"]) or first_number(row, ["play_count", "view_count", "play_cnt", "hot_value"])
    return {
        "platform": "douyin",
        "source_query": query,
        "source_strategy": strategy,
        "source_strategy_label": TIKHUB_STRATEGY_LABELS.get(strategy, strategy),
        "id": aweme_id,
        "title": title,
        "creator": creator,
        "url": normalize_douyin_original_url(source_url) or normalize_douyin_original_url(aweme_id),
        "views": views,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "collects": collects,
        "upload_date": str(first_number(row, ["create_time", "publish_time"]) or ""),
        "duration_seconds": parse_duration_seconds(first_number(row, ["duration", "video_duration"])),
        "description": title,
        "download_url": extract_video_download_url(video),
        "raw": row,
    }


def douyin_tikhub_search(query: str, limit: int, base_url: str, token: str, raw_dir: Path) -> list[dict[str, Any]]:
    payload = tikhub_fetch_json(
        "/api/v1/douyin/search/fetch_video_search_v2",
        token,
        base_url,
        method="POST",
        body={
            "keyword": query,
            "cursor": 0,
            "sort_type": "1",
            "publish_time": "0",
            "filter_duration": "0",
            "content_type": "1",
        },
    )
    write_json_file(raw_dir / f"search-{safe_slug(query)}.json", payload)
    return [
        normalize_douyin_record(record, query, "search", index + 1)
        for index, record in enumerate(extract_tikhub_video_search_records(payload)[:limit])
    ]


def douyin_tikhub_billboard(
    query: str,
    strategies: list[str],
    limit: int,
    base_url: str,
    token: str,
    raw_dir: Path,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for strategy in strategies:
        endpoint = TIKHUB_STRATEGY_ENDPOINTS.get(strategy)
        if not endpoint:
            continue
        try:
            payload = tikhub_fetch_json(
                endpoint,
                token,
                base_url,
                method="POST",
                body={"page": 1, "page_size": limit, "date_window": 24, "keyword": query, "tags": []},
            )
            write_json_file(raw_dir / f"billboard-{strategy}-{safe_slug(query)}.json", payload)
            records = extract_tikhub_billboard_records(payload)
            candidates.extend(normalize_douyin_record(record, query, strategy, index + 1) for index, record in enumerate(records[:limit]))
        except Exception as error:
            write_json_file(
                raw_dir / f"billboard-{strategy}-{safe_slug(query)}.error.json",
                {"strategy": strategy, "query": query, "error": str(error)[:500]},
            )
    if not candidates:
        try:
            candidates.extend(douyin_tikhub_search(query, limit, base_url, token, raw_dir))
        except Exception as error:
            write_json_file(raw_dir / f"search-{safe_slug(query)}.error.json", {"query": query, "error": str(error)[:500]})
    return candidates


def score_candidate(item: dict[str, Any]) -> int:
    title = item.get("title", "")
    lower = title.lower()
    score = 0
    score += min(40, parse_int(item.get("views")) // 25000)
    score += min(30, parse_int(item.get("likes")) // 5000)
    score += 20 if any(keyword in lower for keyword in AI_KEYWORDS) else 0
    score += 25 if any(keyword in lower for keyword in TEACHING_KEYWORDS) else 0
    if re.search(r"\b\d+\b|[一二三四五六七八九十]\s*个|[0-9]+\s*分钟", title):
        score += 8
    if any(keyword in lower for keyword in ["business", "workflow", "content", "赚钱", "自媒体", "工作流", "变现"]):
        score += 7
    return score


def dedupe(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in candidates:
        key = item.get("url") or f"{item.get('platform')}:{item.get('id')}"
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def clean_vtt(text: str) -> str:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == "WEBVTT" or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if "-->" in line or re.fullmatch(r"\d+", line):
            continue
        line = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", "", line)
        line = re.sub(r"</?c[^>]*>", "", line)
        line = re.sub(r"<[^>]+>", "", line)
        line = html.unescape(line)
        if line and (not lines or lines[-1] != line):
            lines.append(line)
    text = " ".join(lines)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def download_youtube_subtitle(item: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    url = str(item.get("url") or "")
    video_id = str(item.get("id") or "youtube")
    result = {
        "status": "not_attempted",
        "raw_path": "",
        "clean_path": "",
        "char_count": 0,
        "preview": "",
        "error": "",
    }
    if not url:
        result["status"] = "missing_url"
        return result
    output_dir.mkdir(parents=True, exist_ok=True)
    before = set(output_dir.glob(f"{video_id}*.vtt"))
    proc = run_command(
        [
            "yt-dlp",
            "--no-update",
            "--write-sub",
            "--write-auto-sub",
            "--sub-lang",
            "en,zh",
            "--sleep-requests",
            "1",
            "--skip-download",
            "-o",
            str(output_dir / "%(id)s.%(ext)s"),
            url,
        ],
        timeout=180,
    )
    after = set(output_dir.glob(f"{video_id}*.vtt"))
    vtt_files = sorted(after - before) or sorted(output_dir.glob(f"{video_id}*.vtt"))
    if not vtt_files:
        result["status"] = "unavailable"
        result["error"] = proc.stderr[-1000:]
        return result
    raw_path = vtt_files[0]
    clean_text = clean_vtt(raw_path.read_text(encoding="utf-8", errors="ignore"))
    clean_path = output_dir / f"{video_id}.clean.txt"
    clean_path.write_text(clean_text, encoding="utf-8")
    result.update(
        {
            "status": "downloaded",
            "raw_path": str(raw_path),
            "clean_path": str(clean_path),
            "char_count": len(clean_text),
            "preview": clean_text[:500],
        }
    )
    return result


def get_bilibili_detail(item: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    bvid = str(item.get("id") or "")
    result = {
        "status": "not_attempted",
        "raw_path": "",
        "clean_path": "",
        "char_count": 0,
        "preview": "",
        "error": "",
    }
    if not bvid or not shutil.which("bili"):
        result["status"] = "unavailable"
        return result
    output_dir.mkdir(parents=True, exist_ok=True)
    proc = run_command(["bili", "video", bvid], timeout=120)
    detail_path = output_dir / f"{bvid}.detail.yaml"
    detail_path.write_text(proc.stdout, encoding="utf-8")
    subtitle_match = re.search(r"text:\s*['\"]?(.+?)['\"]?\s*(?:\n\s*items:|\n\s*warnings:|\Z)", proc.stdout, re.S)
    subtitle_text = ""
    if subtitle_match:
        subtitle_text = subtitle_match.group(1).strip().strip("'\"")
    if subtitle_text:
        clean_path = output_dir / f"{bvid}.clean.txt"
        clean_path.write_text(subtitle_text, encoding="utf-8")
        result.update(
            {
                "status": "downloaded",
                "raw_path": str(detail_path),
                "clean_path": str(clean_path),
                "char_count": len(subtitle_text),
                "preview": subtitle_text[:500],
            }
        )
    elif shutil.which("opencli"):
        try:
            subtitle_proc = run_command(["opencli", "bilibili", "subtitle", bvid, "-f", "json", "--window", "background"], timeout=180)
        except subprocess.TimeoutExpired:
            result.update({"status": "metadata_only", "raw_path": str(detail_path), "error": "opencli subtitle timed out"})
            return result
        subtitle_path = output_dir / f"{bvid}.subtitle.json"
        subtitle_path.write_text(subtitle_proc.stdout, encoding="utf-8")
        subtitle_text = parse_opencli_bilibili_subtitle(subtitle_proc.stdout)
        if subtitle_text:
            clean_path = output_dir / f"{bvid}.clean.txt"
            clean_path.write_text(subtitle_text, encoding="utf-8")
            result.update(
                {
                    "status": "downloaded",
                    "raw_path": str(subtitle_path),
                    "clean_path": str(clean_path),
                    "char_count": len(subtitle_text),
                    "preview": subtitle_text[:500],
                }
            )
        else:
            result.update({"status": "metadata_only", "raw_path": str(detail_path), "error": (subtitle_proc.stderr or "no subtitle in opencli output")[-1000:]})
    else:
        result.update({"status": "metadata_only", "raw_path": str(detail_path), "error": "no subtitle in bili output"})
    return result


def parse_opencli_bilibili_subtitle(stdout: str) -> str:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        lines = []
        for raw_line in stdout.splitlines():
            line = raw_line.strip()
            if not line or line.startswith(("index", "---", "Usage:", "Update available")):
                continue
            lines.append(line)
        return clean_plain_text(" ".join(lines))
    rows: Any = payload
    if isinstance(payload, dict):
        rows = payload.get("data") or payload.get("items") or payload.get("rows") or payload.get("result") or []
    if not isinstance(rows, list):
        return ""
    parts = []
    for row in rows:
        record = object_record(row)
        text = first_string(record, ["content", "text", "body", "subtitle", "line"])
        if text:
            parts.append(text)
    return clean_plain_text(" ".join(parts))


def clean_plain_text(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def flatten_text_value(value: Any) -> str:
    if isinstance(value, str):
        return clean_plain_text(value)
    if isinstance(value, (int, float)):
        return ""
    if isinstance(value, list):
        parts = [flatten_text_value(item) for item in value]
        return clean_plain_text(" ".join(part for part in parts if part))
    record = object_record(value)
    if not record:
        return ""
    preferred = first_string(record, ["text", "content", "caption", "desc", "description", "sentence"])
    if preferred:
        return clean_plain_text(preferred)
    parts = [flatten_text_value(item) for item in record.values()]
    return clean_plain_text(" ".join(part for part in parts if part))


def collect_text_fields(value: Any, keys: list[str]) -> list[str]:
    texts: list[str] = []

    def visit(node: Any) -> None:
        if isinstance(node, list):
            for child in node:
                visit(child)
            return
        record = object_record(node)
        if not record:
            return
        for key, child in record.items():
            if key in keys:
                text = flatten_text_value(child)
                if text:
                    texts.append(text)
            if isinstance(child, (dict, list)):
                visit(child)

    visit(value)
    return texts


def pick_usable_text(texts: list[str], min_chars: int) -> str:
    seen: set[str] = set()
    cleaned: list[str] = []
    for text in texts:
        value = clean_plain_text(text)
        if len(value) < min_chars:
            continue
        if value in seen:
            continue
        seen.add(value)
        cleaned.append(value)
    cleaned.sort(key=len, reverse=True)
    return cleaned[0] if cleaned else ""


def extract_usable_tikhub_text(detail: dict[str, Any], fallback: dict[str, Any], min_chars: int) -> tuple[str, str]:
    bundle = {"detail": detail, "fallback": fallback}
    transcript = pick_usable_text(collect_text_fields(bundle, TRANSCRIPT_KEYS), min_chars)
    if transcript:
        return transcript, "transcript_or_subtitle"
    description = pick_usable_text(collect_text_fields(bundle, DESCRIPTION_TEXT_KEYS), min_chars)
    if description:
        return description, "description_or_caption"
    return "", ""


def fetch_douyin_detail(item: dict[str, Any], output_dir: Path, token: str, base_url: str) -> tuple[dict[str, Any], str, str]:
    aweme_id = str(item.get("id") or "")
    if not aweme_id or not token:
        return object_record(item.get("raw")), "", "missing_aweme_id_or_tikhub_token"
    try:
        payload = tikhub_fetch_json(
            "/api/v1/douyin/app/v3/fetch_one_video",
            token,
            base_url,
            params={"aweme_id": aweme_id},
        )
        path = output_dir / f"{safe_slug(aweme_id, 'douyin')}.detail.json"
        write_json_file(path, payload)
        return extract_tikhub_video_detail(payload), str(path), ""
    except Exception as error:
        return object_record(item.get("raw")), "", str(error)[:500]


def download_video_file(url: str, path: Path, referer: str = "https://www.douyin.com/") -> tuple[str, str]:
    if not is_http_url(url):
        return "", "missing_download_url"
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "accept": "video/webm,video/mp4,video/*,*/*;q=0.8",
            "referer": referer if is_http_url(referer) else "https://www.douyin.com/",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            content_type = response.headers.get("content-type", "")
            if "text/html" in content_type:
                return "", f"download_url_returned_html:{content_type}"
            path.write_bytes(response.read())
        return str(path), ""
    except Exception as error:
        return "", str(error)[:500]


def extract_audio_file(video_path: Path, audio_path: Path) -> tuple[str, str]:
    if not video_path.exists():
        return "", "video_file_not_found"
    if not shutil.which("ffmpeg"):
        return "", "ffmpeg not found"
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    proc = run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-b:a",
            "64k",
            str(audio_path),
        ],
        timeout=300,
    )
    if proc.returncode != 0 or not audio_path.exists() or audio_path.stat().st_size == 0:
        return "", (proc.stderr or proc.stdout or "ffmpeg audio extraction failed")[-1000:]
    return str(audio_path), ""


def read_clean_transcript(path: Path) -> str:
    transcript = clean_plain_text(path.read_text(encoding="utf-8", errors="ignore"))
    path.write_text(transcript, encoding="utf-8")
    return transcript


def transcribe_audio_with_agent_reach(audio_path: str, clean_path: Path, provider: str) -> tuple[str, str]:
    if not shutil.which("agent-reach"):
        return "", "agent-reach not found for transcription"
    proc = run_command(["agent-reach", "transcribe", "--provider", provider, audio_path, "-o", str(clean_path)], timeout=900)
    if clean_path.exists():
        transcript = read_clean_transcript(clean_path)
        if transcript:
            return transcript, ""
    return "", (proc.stderr or proc.stdout or "agent-reach transcription failed")[-1000:]


def transcribe_audio_with_local_whisper(audio_path: str, clean_path: Path, model: str) -> tuple[str, str]:
    if not shutil.which("whisper"):
        return "", "local whisper command not found"
    output_dir = clean_path.parent / "_whisper"
    output_dir.mkdir(parents=True, exist_ok=True)
    proc = run_command(
        [
            "whisper",
            audio_path,
            "--model",
            model,
            "--language",
            "zh",
            "--output_format",
            "txt",
            "--output_dir",
            str(output_dir),
            "--verbose",
            "False",
        ],
        timeout=1800,
    )
    source_txt = output_dir / f"{Path(audio_path).stem}.txt"
    if source_txt.exists():
        transcript = clean_plain_text(source_txt.read_text(encoding="utf-8", errors="ignore"))
        clean_path.write_text(transcript, encoding="utf-8")
        if transcript:
            return transcript, ""
    return "", (proc.stderr or proc.stdout or "local whisper transcription failed")[-1000:]


def get_douyin_transcript(
    item: dict[str, Any],
    output_dir: Path,
    token: str,
    base_url: str,
    min_chars: int,
    *,
    download_video: bool,
    transcribe_missing: bool,
    asr_provider: str,
    local_whisper_model: str,
) -> dict[str, Any]:
    aweme_id = str(item.get("id") or safe_slug(str(item.get("title") or "douyin"), "douyin"))
    result = {
        "status": "not_attempted",
        "raw_path": "",
        "clean_path": "",
        "video_path": "",
        "audio_path": "",
        "download_url": str(item.get("download_url") or ""),
        "text_source": "",
        "char_count": 0,
        "preview": "",
        "error": "",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    detail, detail_path, detail_error = fetch_douyin_detail(item, output_dir, token, base_url)
    if detail_path:
        result["raw_path"] = detail_path
    if detail_error:
        result["error"] = detail_error

    video = object_record(detail.get("video"))
    download_url = extract_video_download_url(video) or str(item.get("download_url") or "")
    if download_url:
        result["download_url"] = download_url

    detail_duration_ms = parse_int(object_record(detail.get("aweme_detail")).get("duration"))
    item_duration_seconds = parse_int(item.get("duration_seconds"))
    duration_seconds = item_duration_seconds or (detail_duration_ms // 1000 if detail_duration_ms else 0)

    text, text_source = extract_usable_tikhub_text(detail, object_record(item.get("raw")), min_chars)
    clean_path = output_dir / f"{safe_slug(aweme_id, 'douyin')}.clean.txt"
    if text and (text_source != "description_or_caption" or not transcribe_missing):
        clean_path.write_text(text, encoding="utf-8")
        result.update(
            {
                "status": "tikhub_text",
                "clean_path": str(clean_path),
                "text_source": text_source,
                "char_count": len(text),
                "preview": text[:500],
            }
        )
        return result

    video_path = output_dir / f"{safe_slug(aweme_id, 'douyin')}.mp4"
    should_download = download_video or transcribe_missing
    if should_download and download_url:
        saved_path, download_error = download_video_file(download_url, video_path, str(item.get("url") or ""))
        if saved_path:
            result["video_path"] = saved_path
        elif download_error:
            result["error"] = download_error

    if transcribe_missing:
        # Reference mining here targets short-form samples; skip hour-long录播-style assets.
        if duration_seconds and duration_seconds > 600:
            result["error"] = result["error"] or f"video too long for ASR fallback: {duration_seconds}s"
            result["status"] = "metadata_only"
            return result
        if not result["video_path"]:
            result["error"] = result["error"] or "video download failed before transcription"
        audio_path = output_dir / f"{safe_slug(aweme_id, 'douyin')}.mp3"
        if result["video_path"]:
            saved_audio_path, audio_error = extract_audio_file(Path(result["video_path"]), audio_path)
            if saved_audio_path:
                result["audio_path"] = saved_audio_path
            elif audio_error:
                result["error"] = audio_error

        source = result["audio_path"]
        if source:
            errors: list[str] = []
            transcript = ""
            text_source = ""
            if asr_provider == "local-whisper":
                transcript, error = transcribe_audio_with_local_whisper(source, clean_path, local_whisper_model)
                text_source = "local-whisper"
                if error:
                    errors.append(error)
            else:
                transcript, error = transcribe_audio_with_agent_reach(source, clean_path, asr_provider)
                text_source = "agent-reach-asr"
                if error:
                    errors.append(error)
                if not transcript and asr_provider == "auto" and shutil.which("whisper"):
                    transcript, error = transcribe_audio_with_local_whisper(source, clean_path, local_whisper_model)
                    text_source = "local-whisper"
                    if error:
                        errors.append(error)
            if len(transcript) >= min_chars:
                result.update(
                    {
                        "status": "transcribed",
                        "clean_path": str(clean_path),
                        "text_source": text_source,
                        "char_count": len(transcript),
                        "preview": transcript[:500],
                    }
                )
                return result
            if errors:
                result["error"] = "\n".join(errors)[-1500:]

    result["status"] = "metadata_only"
    return result


def has_usable_body(transcript_info: dict[str, Any], min_chars: int, *, allow_description_body: bool) -> bool:
    if transcript_info.get("text_source") == "description_or_caption" and not allow_description_body:
        return False
    return parse_int(transcript_info.get("char_count")) >= min_chars and transcript_info.get("status") not in {
        "metadata_only",
        "unavailable",
        "missing_url",
        "not_attempted",
    }


def excluded_without_body(item: dict[str, Any], transcript_info: dict[str, Any], min_chars: int) -> dict[str, Any]:
    text_source = transcript_info.get("text_source")
    if text_source == "description_or_caption":
        reason = "只拿到平台描述/标题文案，未拿到口播逐字稿或字幕，已排除出分析样本。"
    else:
        reason = f"正文低于 {min_chars} 字或未拿到可用逐字稿，已排除出分析样本。"
    return {
        "source": {
            "platform": item.get("platform"),
            "creator": item.get("creator"),
            "title": item.get("title"),
            "url": item.get("url"),
            "views": item.get("views"),
            "likes": item.get("likes"),
            "source_query": item.get("source_query"),
            "source_strategy": item.get("source_strategy"),
        },
        "transcript": transcript_info,
        "reason": reason,
    }


def detect_hook_patterns(title: str, transcript: str) -> list[str]:
    text = f"{title} {transcript[:800]}".lower()
    patterns: list[str] = []
    if any(word in text for word in ["i built", "我用", "我做", "做了个", "this video was", "1分钟", "一天", "3小时"]):
        patterns.append("result-first / 成果前置")
    if any(word in text for word in ["stop", "don't", "别", "不要", "坑", "truth", "真相", "避雷"]):
        patterns.append("anti-mistake / 反坑")
    if re.search(r"\b[345789]\b|[三四五六七八九十]\s*个|ways|steps|方法", text):
        patterns.append("numbered framework / 数字框架")
    if any(word in text for word in ["beginner", "小白", "零基础", "from scratch", "手把手"]):
        patterns.append("beginner-friendly / 新手友好")
    if any(word in text for word in ["workflow", "工作流", "system", "流程"]):
        patterns.append("workflow framing / 工作流包装")
    return patterns or ["topic promise / 主题承诺"]


def detect_cta(text: str) -> list[str]:
    lower = text.lower()
    return [keyword for keyword in CTA_KEYWORDS if keyword in lower][:8]


def infer_structure(title: str, transcript: str) -> list[str]:
    text = f"{title} {transcript}".lower()
    structure: list[str] = []
    if detect_hook_patterns(title, transcript):
        structure.append("0-5s: 用结果、反坑或强承诺让观众停下")
    if any(word in text for word in ["because", "why", "为什么", "原因"]):
        structure.append("解释观看理由：为什么这件事现在值得学")
    if any(word in text for word in ["step", "first", "second", "第三", "步骤", "流程"]):
        structure.append("分步骤展开：把复杂工具拆成可跟做路径")
    if any(word in text for word in ["demo", "screen", "show", "演示", "录屏", "看看"]):
        structure.append("用录屏/演示证明，不只口播解释")
    if detect_cta(text):
        structure.append("结尾承接：关注、评论、课程、资料或社群")
    return structure or ["标题承诺 -> 功能解释 -> 操作演示 -> 收尾承接"]


def analyze_candidate(item: dict[str, Any], transcript_info: dict[str, Any]) -> dict[str, Any]:
    transcript = str(transcript_info.get("preview") or "")
    full_transcript = ""
    clean_path = transcript_info.get("clean_path")
    if clean_path and Path(clean_path).exists():
        full_transcript = Path(clean_path).read_text(encoding="utf-8", errors="ignore")
    title = str(item.get("title") or "")
    joined = f"{title} {full_transcript}"
    return {
        "source": {
            "platform": item.get("platform"),
            "creator": item.get("creator"),
            "title": title,
            "url": item.get("url"),
            "views": item.get("views"),
            "likes": item.get("likes"),
            "comments": item.get("comments"),
            "shares": item.get("shares"),
            "collects": item.get("collects"),
            "upload_date": item.get("upload_date"),
            "duration_seconds": item.get("duration_seconds"),
            "source_query": item.get("source_query"),
            "source_strategy": item.get("source_strategy"),
        },
        "transcript": transcript_info,
        "transcript_text": full_transcript,
        "hook_patterns": detect_hook_patterns(title, full_transcript),
        "opening_preview": (full_transcript or transcript or title)[:300],
        "structure": infer_structure(title, full_transcript),
        "cta_signals": detect_cta(joined),
        "portable_points": [
            "先给可见结果或明确收益，再讲工具/概念",
            "把 AI 概念塞进具体流程里讲，避免开头像课堂",
            "用步骤名/工作流名建立专业感，但不要在短视频里展开全部细节",
            "结尾承接到资料、社群或课程时，强调继续拆流程，而不是直接卖课",
        ],
        "fit_for_account_script": [
            "开头用近期数据或 Codex 输出结果做证明",
            "中段讲“提示词、数据、技能”时必须绑定账号定位/竞品分析/视频制作三个真实工作流",
            "知识星球 CTA 更适合说“我把流程一层一层拆在里面”，不要说“买课学提示词”",
        ],
        "do_not_copy": [
            "不要复用原视频画面、字幕、口播原句和案例素材",
            "不要照搬收益承诺、月入表达或平台外导流话术",
            "不要把英文长教程结构原样搬到抖音，短视频只取前钩子和证明方式",
        ],
    }


def include_local_douyin_references(workspace: Path) -> list[dict[str, Any]]:
    path = workspace / "data/benchmarks/current/reference-bank.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    refs = []
    for ref in data.get("references", []):
        if ref.get("platform") != "douyin_internal":
            continue
        refs.append(
            {
                "source": {
                    "platform": ref.get("platform"),
                    "creator": ref.get("creator"),
                    "title": ref.get("title"),
                    "url": ref.get("url"),
                    "views": ref.get("observed_metric"),
                    "upload_date": ref.get("upload_date"),
                    "duration_seconds": None,
                },
                "transcript": {"status": "internal_reference_only"},
                "hook_patterns": ref.get("title_patterns") or [],
                "opening_preview": ref.get("rewrite_notes") or "",
                "structure": [
                    "结果前置",
                    "展示 Codex 已完成的任务",
                    "用工作流承接评论/私信需求",
                ],
                "cta_signals": ref.get("usable_for") or [],
                "portable_points": [
                    "用作账号内优先级最高的结构证据",
                    "证明“直接让 AI 干活”的表达强于抽象教程",
                ],
                "fit_for_account_script": [
                    "这条教学转化视频必须先展示账号工作流结果，再讲底层概念",
                ],
                "do_not_copy": ref.get("do_not_copy") or [],
            }
        )
    return refs


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# {payload['run_name']}",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Workspace: {payload['workspace']}",
        f"- YouTube candidates: {payload['counts']['youtube_candidates']}",
        f"- Bilibili candidates: {payload['counts']['bilibili_candidates']}",
        f"- Douyin candidates: {payload['counts'].get('douyin_candidates', 0)}",
        f"- Analyzed items: {payload['counts']['analyzed_items']}",
        f"- Excluded without usable body: {payload['counts'].get('excluded_no_transcript', 0)}",
        "",
        "## Overall Patterns",
        "",
    ]
    for pattern in payload["overall_patterns"]:
        lines.append(f"- {pattern}")
    lines.extend(["", "## Analyzed References", ""])
    for index, item in enumerate(payload["analyses"], start=1):
        source = item["source"]
        lines.extend(
            [
                f"### {index}. {source.get('title')}",
                "",
                f"- Platform: {source.get('platform')}",
                f"- Creator: {source.get('creator')}",
                f"- URL: {source.get('url')}",
                f"- Views: {source.get('views')}",
                f"- Transcript: {item['transcript'].get('status')}",
                f"- Transcript chars: {item['transcript'].get('char_count')}",
                f"- Original text file: {item['transcript'].get('clean_path')}",
                f"- Hook patterns: {', '.join(item.get('hook_patterns') or [])}",
                f"- CTA signals: {', '.join(item.get('cta_signals') or [])}",
                "",
                "Structure:",
            ]
        )
        for step in item.get("structure") or []:
            lines.append(f"- {step}")
        lines.extend(["", "Account script takeaways:"])
        for point in item.get("fit_for_account_script") or []:
            lines.append(f"- {point}")
        lines.append("")
    excluded = payload.get("excluded_no_transcript") or []
    if excluded:
        lines.extend(["## Excluded Without Usable Body", ""])
        for index, item in enumerate(excluded, start=1):
            source = item.get("source") or {}
            transcript = item.get("transcript") or {}
            lines.append(f"- {index}. {source.get('platform')} | {source.get('title')} | {transcript.get('status')} | {item.get('reason')}")
        lines.append("")
    lines.extend(["## Recommended Rewrite For Current Topic", ""])
    for point in payload["recommended_rewrite"]:
        lines.append(f"- {point}")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine viral AI teaching videos and download public transcripts for copy analysis.")
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--youtube-query", action="append", default=[])
    parser.add_argument("--bilibili-query", action="append", default=[])
    parser.add_argument("--douyin-query", action="append", default=[])
    parser.add_argument("--per-query", type=int, default=6)
    parser.add_argument("--min-youtube-views", type=int, default=50_000)
    parser.add_argument("--min-bilibili-views", type=int, default=50_000)
    parser.add_argument("--min-douyin-likes", type=int, default=1_000)
    parser.add_argument("--min-score", type=int, default=30)
    parser.add_argument("--max-transcripts", type=int, default=6)
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
    parser.add_argument("--include-local-douyin", action="store_true")
    args = parser.parse_args()

    if args.env_file:
        load_env_file(args.env_file.expanduser().resolve())

    workspace = args.workspace.resolve()
    if not workspace.exists():
        raise SystemExit(f"workspace not found: {workspace}")
    run_id = args.run_id or f"{datetime.now().date().isoformat()}-ai-teaching-script-mining"
    raw_root = workspace / "data/benchmarks/raw/references/teaching-video-scripts" / run_id
    output_root = workspace / "runs" / run_id / "outputs"
    output_root.mkdir(parents=True, exist_ok=True)
    raw_root.mkdir(parents=True, exist_ok=True)

    youtube_queries = args.youtube_query or DEFAULT_YOUTUBE_QUERIES
    bilibili_queries = args.bilibili_query or DEFAULT_BILIBILI_QUERIES
    douyin_queries = args.douyin_query or DEFAULT_DOUYIN_QUERIES
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

    analyses: list[dict[str, Any]] = []
    excluded_no_transcript: list[dict[str, Any]] = []

    def append_if_usable(item: dict[str, Any], transcript: dict[str, Any]) -> None:
        if args.allow_metadata_only or has_usable_body(
            transcript,
            args.min_transcript_chars,
            allow_description_body=args.allow_description_body,
        ):
            analyses.append(analyze_candidate(item, transcript))
        else:
            excluded_no_transcript.append(excluded_without_body(item, transcript, args.min_transcript_chars))

    selected_youtube = youtube_candidates[: args.max_transcripts]
    selected_bilibili = bilibili_candidates[: max(2, args.max_transcripts // 2)]
    selected_douyin = douyin_candidates[: args.max_douyin_transcripts]
    for item in selected_youtube:
        transcript = download_youtube_subtitle(item, raw_root / "youtube")
        append_if_usable(item, transcript)
    for item in selected_bilibili:
        transcript = get_bilibili_detail(item, raw_root / "bilibili")
        append_if_usable(item, transcript)
    for item in selected_douyin:
        transcript = get_douyin_transcript(
            item,
            raw_root / "douyin",
            tikhub_token,
            tikhub_base_url,
            args.min_transcript_chars,
            download_video=args.download_douyin_video,
            transcribe_missing=args.transcribe_missing,
            asr_provider=args.asr_provider,
            local_whisper_model=args.local_whisper_model,
        )
        append_if_usable(item, transcript)
    if args.include_local_douyin and args.allow_metadata_only:
        analyses.extend(include_local_douyin_references(workspace))

    payload = {
        "run_name": run_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "workspace": str(workspace),
        "raw_root": str(raw_root),
        "queries": {
            "youtube": youtube_queries,
            "bilibili": bilibili_queries,
            "douyin": douyin_queries,
            "douyin_strategies": douyin_strategies,
            "bilibili_hot_limit": args.bilibili_hot_limit,
            "bilibili_rank_limit": args.bilibili_rank_limit,
            "douyin_limit": args.douyin_limit,
            "tikhub_configured": bool(tikhub_token),
        },
        "filters": {
            "per_query": args.per_query,
            "min_youtube_views": args.min_youtube_views,
            "min_bilibili_views": args.min_bilibili_views,
            "min_douyin_likes": args.min_douyin_likes,
            "min_score": args.min_score,
            "max_transcripts": args.max_transcripts,
            "max_douyin_transcripts": args.max_douyin_transcripts,
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
            "analyzed_items": len(analyses),
            "excluded_no_transcript": len(excluded_no_transcript),
        },
        "candidates": {
            "youtube": youtube_candidates,
            "bilibili": bilibili_candidates,
            "douyin": douyin_candidates,
        },
        "analyses": analyses,
        "excluded_no_transcript": excluded_no_transcript,
        "overall_patterns": [
            "爆款 AI 教学视频通常先给结果、反坑或明确收益，再解释概念。",
            "长教程靠标题承诺和完整步骤吃搜索流量；抖音短视频只应借开头钩子和证明方式。",
            "高转化教学内容会把概念绑定到可见流程：案例、录屏、步骤名、前后对比。",
            "“提示词/数据/技能”适合做中段概念，不适合做开头。",
        ],
        "recommended_rewrite": [
            "当前视频开头先展示“Codex 已经帮我跑账号定位、选题、文案、视频制作”。",
            "再解释：我给它的不是一句提示词，而是一整套工作流。",
            "“AI 不是标准答案，是高概率结果”要接在“为什么要积累上下文”后面。",
            "知识星球 CTA 用“我把这套流程拆在里面”，避免泛卖课。",
        ],
    }

    json_path = output_root / "teaching-video-script-analysis.json"
    md_path = output_root / "teaching-video-script-analysis.md"
    manifest_path = workspace / "runs" / run_id / "run.manifest.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "workflow_id": "teaching-video-script-mining",
                "generated_at": payload["generated_at"],
                "inputs": [
                    "config/strategy/strategy-brief.json",
                    "data/benchmarks/current/reference-bank.json",
                    "Agent Reach: YouTube yt-dlp",
                    "Agent Reach: Bilibili bili-cli",
                    "TikHub: Douyin billboard/detail API" if tikhub_token else "TikHub: not configured",
                    "Agent Reach: ASR transcription" if args.transcribe_missing else "ASR transcription: disabled",
                ],
                "outputs": [
                    str(json_path.relative_to(workspace)),
                    str(md_path.relative_to(workspace)),
                    str(raw_root.relative_to(workspace)),
                ],
                "notes": "Requires usable body text for analysis by default. Metadata-only candidates are written to excluded_no_transcript.",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    print(f"wrote {manifest_path}")
    print(f"raw transcripts: {raw_root}")


if __name__ == "__main__":
    main()
