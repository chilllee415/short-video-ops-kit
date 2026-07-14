#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date, datetime
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = {
    "run_id_suffix": "daily-viral-mining",
    "youtube_queries": [
        "AI agents clearly explained",
        "ChatGPT agent tutorial automation",
        "AI automation tutorial for beginners",
        "AI workflow tutorial content creation",
        "Claude Code tutorial AI agents",
        "Codex AI workflow",
        "AI coding agent real workflow",
    ],
    "bilibili_queries": [
        "AI 教程 工作流",
        "AI 自动化 工作流 教程",
        "普通人 学 AI 教程",
        "AI 自媒体 工作流",
        "AI Agent 帮你干活 教程",
        "Codex 教程 工作流",
    ],
    "per_query": 6,
    "min_youtube_views": 50000,
    "min_bilibili_views": 50000,
    "min_score": 30,
    "max_transcripts": 8,
    "bilibili_hot_limit": 20,
    "bilibili_rank_limit": 20,
    "include_local_douyin": True,
}


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def merged_config(path: Path | None) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    if path:
        config.update(load_json_object(path))
    return config


def list_value(config: dict[str, Any], key: str) -> list[str]:
    value = config.get(key) or []
    if not isinstance(value, list):
        raise SystemExit(f"config.{key} must be an array")
    return [str(item) for item in value if str(item).strip()]


def int_value(config: dict[str, Any], key: str) -> int:
    value = config.get(key, DEFAULT_CONFIG[key])
    try:
        return int(value)
    except (TypeError, ValueError):
        raise SystemExit(f"config.{key} must be an integer") from None


def bool_value(config: dict[str, Any], key: str) -> bool:
    value = config.get(key, DEFAULT_CONFIG[key])
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def run(cmd: list[str], cwd: Path) -> None:
    print("+ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def update_manifest(workspace: Path, run_id: str, command: list[str], config_path: Path | None) -> None:
    manifest_path = workspace / "runs" / run_id / "run.manifest.json"
    manifest = load_json_object(manifest_path)
    manifest["automation_profile"] = "daily-viral-mining"
    manifest["commands"] = [" ".join(command)]
    if config_path:
        manifest["config"] = str(config_path)
        inputs = manifest.get("inputs") or []
        if isinstance(inputs, list):
            rel = str(config_path)
            try:
                rel = str(config_path.relative_to(workspace))
            except ValueError:
                pass
            if rel not in inputs:
                inputs.append(rel)
            manifest["inputs"] = inputs
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def write_summary(workspace: Path, run_id: str) -> Path:
    output_root = workspace / "runs" / run_id / "outputs"
    analysis_path = output_root / "teaching-video-script-analysis.json"
    payload = load_json_object(analysis_path)
    analyses = payload.get("analyses") if isinstance(payload.get("analyses"), list) else []
    counts = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}

    lines = [
        f"# Daily Viral Mining: {run_id}",
        "",
        f"- Generated at: {payload.get('generated_at', datetime.now().isoformat(timespec='seconds'))}",
        f"- YouTube candidates: {counts.get('youtube_candidates', 0)}",
        f"- Bilibili candidates: {counts.get('bilibili_candidates', 0)}",
        f"- Analyzed items: {counts.get('analyzed_items', 0)}",
        "",
        "## Top Analyzed Items",
        "",
    ]
    for index, item in enumerate(analyses[:10], start=1):
        source = item.get("source") if isinstance(item, dict) else {}
        if not isinstance(source, dict):
            source = {}
        title = source.get("title") or ""
        platform = source.get("platform") or ""
        views = source.get("views") or 0
        url = source.get("url") or ""
        hooks = ", ".join(item.get("hook_patterns") or []) if isinstance(item, dict) else ""
        lines.extend(
            [
                f"### {index}. {title}",
                "",
                f"- Platform: {platform}",
                f"- Views: {views}",
                f"- URL: {url}",
                f"- Hook patterns: {hooks}",
                "",
            ]
        )

    summary_path = output_root / "daily-viral-mining-summary.md"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    return summary_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run daily viral video mining and copy structure analysis.")
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--run-id", default="")
    args = parser.parse_args()

    system_root = Path(__file__).resolve().parents[1]
    workspace = args.workspace.resolve()
    default_config_path = workspace / "data/benchmarks/raw/references/teaching-video-scripts/daily-viral-mining.config.json"
    config_path = args.config.resolve() if args.config else default_config_path
    config = merged_config(config_path if config_path.exists() else None)
    run_id = args.run_id or f"{args.date}-{config.get('run_id_suffix', 'daily-viral-mining')}"

    run(["python3", "scripts/validate_workspace.py", str(workspace)], system_root)

    command = [
        "python3",
        "scripts/collect_teaching_video_scripts.py",
        str(workspace),
        "--run-id",
        run_id,
        "--per-query",
        str(int_value(config, "per_query")),
        "--min-youtube-views",
        str(int_value(config, "min_youtube_views")),
        "--min-bilibili-views",
        str(int_value(config, "min_bilibili_views")),
        "--min-score",
        str(int_value(config, "min_score")),
        "--max-transcripts",
        str(int_value(config, "max_transcripts")),
        "--bilibili-hot-limit",
        str(int_value(config, "bilibili_hot_limit")),
        "--bilibili-rank-limit",
        str(int_value(config, "bilibili_rank_limit")),
    ]
    for query in list_value(config, "youtube_queries"):
        command.extend(["--youtube-query", query])
    for query in list_value(config, "bilibili_queries"):
        command.extend(["--bilibili-query", query])
    if bool_value(config, "include_local_douyin"):
        command.append("--include-local-douyin")

    run(command, system_root)
    update_manifest(workspace, run_id, command, config_path if config_path.exists() else None)
    summary_path = write_summary(workspace, run_id)
    run(["python3", "scripts/validate_workspace.py", str(workspace)], system_root)

    print(f"run_id: {run_id}")
    print(f"summary: {summary_path}")


if __name__ == "__main__":
    main()
