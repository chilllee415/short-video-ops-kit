#!/usr/bin/env python3
"""Install this package as a Codex skill."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


NAME = "douyin-comment-insight"
SOURCE = Path(__file__).resolve().parent


def ignored(_: str, names: list[str]) -> set[str]:
    excluded = {
        "__pycache__", "workspace", ".env", ".git", ".github", "tests", ".venv",
        ".gitignore", "README.md", "CONTRIBUTING.md", "SECURITY.md", "LICENSE",
    }
    return {name for name in names if name in excluded or name.endswith(".pyc") or name.endswith(".zip")}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, default=Path.home() / ".codex" / "skills")
    parser.add_argument("--upgrade", action="store_true")
    args = parser.parse_args()
    destination = args.target.expanduser().resolve() / NAME
    if destination.exists() and not args.upgrade:
        raise SystemExit(f"Skill 已存在：{destination}。如需更新请增加 --upgrade")
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE, destination, dirs_exist_ok=True, ignore=ignored)
    (destination / "workspace" / "runs").mkdir(parents=True, exist_ok=True)
    (destination / "workspace" / "site").mkdir(parents=True, exist_ok=True)
    if not (destination / ".env").exists():
        shutil.copy2(destination / ".env.example", destination / ".env")
    print(f"已安装到：{destination}")
    print(f"请编辑：{destination / '.env'}")


if __name__ == "__main__":
    main()
