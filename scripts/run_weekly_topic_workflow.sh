#!/usr/bin/env bash
set -euo pipefail

workspace="${1:-${SHORT_VIDEO_OPS_WORKSPACE:-}}"

if [[ -z "$workspace" ]]; then
  echo "usage: scripts/run_weekly_topic_workflow.sh /path/to/user-data-workspace" >&2
  echo "or set SHORT_VIDEO_OPS_WORKSPACE=/path/to/user-data-workspace" >&2
  exit 2
fi

system_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$system_root"
python3 scripts/validate_workspace.py "$workspace"
SHORT_VIDEO_OPS_WORKSPACE="$workspace" python3 scripts/generate_weekly_topic_library.py
python3 scripts/validate_workspace.py "$workspace"
