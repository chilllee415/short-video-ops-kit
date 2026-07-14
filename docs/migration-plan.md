# Migration Record

## Current Source Of Truth

Active work is split into two projects:

```text
short-video-ops/system/              workflow project
short-video-ops/user-data/<id>/      user data project
```

`short-video-ops/system` must not contain real account data, internal HTML reports, raw platform exports, user notes, legacy skill originals, or run outputs.

## What Was Migrated Into The Workflow Project

Only reusable workflow assets were migrated:

| Legacy asset | Current location |
| --- | --- |
| YouTube reference mining script | `scripts/collect_youtube_references.py` |
| YouTube reference run schema | `schemas/youtube-reference-run.schema.json` |
| YouTube strategy example config | `examples/youtube-codex-strategy.example.json` |
| Weekly topic radar renderer | `scripts/generate_weekly_topic_library.py` |
| Weekly topic radar synthetic example data | `examples/topic-candidates.template.json` |
| Reference mining workflow notes | `workflows/04-reference-mining.md` |
| Workflow blueprint | `docs/workflow-blueprint.md` |

## What Lives In The User Data Project

All user-specific data lives under the user data project:

| Data class | User-data location |
| --- | --- |
| Account profile and strategy | `short-video-ops/user-data/<id>/config/` |
| Raw and current account operations data | `short-video-ops/user-data/<id>/data/operations/` |
| User-side topic evidence and pain catalog | `short-video-ops/user-data/<id>/data/topic-research/` |
| Supply-side reference and competitor content | `short-video-ops/user-data/<id>/data/benchmarks/` |
| Published outcomes and feedback learning | `short-video-ops/user-data/<id>/data/feedback/` |
| Topic candidates, selections, plans, and scripts | `short-video-ops/user-data/<id>/work/` |
| Canonical dashboard artifacts | `short-video-ops/user-data/<id>/presentation/` |
| Legacy skill originals | `short-video-ops/user-data/<id>/archive/legacy-skills/raw-legacy/` |
| Run records | `short-video-ops/user-data/<id>/runs/` |

## Runtime Rule

Run system scripts from `short-video-ops/system` and point them at one user workspace:

```bash
export SHORT_VIDEO_OPS_WORKSPACE=/path/to/short-video-ops/user-data/<workspace-id>
python3 scripts/validate_workspace.py
```

Generate a topic radar HTML:

```bash
SHORT_VIDEO_OPS_WORKSPACE=/path/to/short-video-ops/user-data/<workspace-id> \
  python3 scripts/generate_weekly_topic_library.py
```

Collect YouTube reference candidates:

```bash
python3 scripts/collect_youtube_references.py \
  --config examples/youtube-codex-strategy.example.json \
  --out /path/to/short-video-ops/user-data/<workspace-id>/data/benchmarks/raw/references/youtube/run.json \
  --markdown /path/to/short-video-ops/user-data/<workspace-id>/data/benchmarks/raw/references/youtube/run.md
```

## Gate For Future Imports

Any future imported file must answer:

```text
Is this public workflow logic or private user data?
Which project should own it?
Which workflow owns it?
Which schema validates it?
Does it contain private identity, account data, or customer data?
```
