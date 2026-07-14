# Repository Index

This is the human-readable index for `short-video-ops/system`.

Agent-readable repository metadata lives in `directory.index.json`. Each user-data workspace has its own `workspace.index.json`.

## Project Boundary

```text
short-video-ops/system/              workflow project
short-video-ops/user-data/<id>/      user data project
```

`short-video-ops/system` contains reusable workflow logic only. It must not contain real account data, raw exports, internal HTML reports, personal skill originals, or run outputs.

## Repository Structure

| Path | Purpose | Private Data |
| --- | --- | --- |
| `docs/` | 快速开始、运营大盘使用说明、架构与发布资料 | No |
| `schemas/` | JSON schemas for contracts and normalized assets | No |
| `manifests/` | Agent-readable workflow read/write contracts | No |
| `workflows/` | Human-readable workflow descriptions | No |
| `modes/` | Personal and commercial operating mode definitions | No |
| `skills/` | Commercial-safe skill promotion rules | No |
| `prompts/` | Copy-ready prompts for running the system with Codex | No |
| `templates/project-workspace/` | Empty user-data workspace template | No real data |
| `templates/workspace-policies/` | Default personal/commercial policies | No |
| `scripts/` | Validation, reference mining, and HTML rendering scripts | No |
| `examples/` | Public synthetic examples | No |

## User Data Workspace Structure

These directories live in `short-video-ops/user-data/<id>/`, not in this repository.

```text
project.manifest.json   Canonical pointers and workflow manifest references
workspace.index.json    Directory index for this workspace
workspace.policy.json   Operating mode policy
data.contract.json      Domain meanings, states, lineage, and boundaries
config/                 Account profile and confirmed strategy
data/operations/        Raw account inputs and current performance
data/topic-research/            User-side topic evidence and pain catalog
data/benchmarks/        Supply-side references and competitor content
data/feedback/          Published outcomes and learning
work/                   Topic candidates, selections, plans, and scripts
presentation/           Dashboard JSON, canonical HTML, and assets
runs/                   Immutable run records
archive/                Legacy and temporary artifacts excluded from automation
```

Agents should receive exactly one workspace root through `SHORT_VIDEO_OPS_WORKSPACE` or a CLI argument, then resolve all user data paths from that root.

## Data Groups

| Data Group | User-data Location | Normalized Location | Owner Workflow |
| --- | --- | --- | --- |
| User operations data | `data/operations/raw/` | `data/operations/current/account-snapshot.json`, `data/operations/current/content-performance.json` | `auto-ops-diagnosis` |
| Account strategy data | `config/profile/`, `config/strategy/` | `config/strategy/strategy-brief.json` | `strategy-confirmation` |
| Competitor data | `data/benchmarks/raw/competitors/` | `data/benchmarks/current/competitor-map.json` | `reference-mining` |
| Reference content | `data/benchmarks/raw/references/` | `data/benchmarks/current/reference-bank.json` | `reference-mining` |
| User demand / pain data | `data/topic-research/raw/customer-dialogue/`, `data/topic-research/current/audience-signals.json` | `data/topic-research/current/pain-bank.json` | `pain-bank-builder` |
| Publishing feedback | `data/feedback/raw/published-posts.json`, `data/feedback/raw/post-metrics.json` | `data/feedback/current/learning.json`, `data/feedback/current/strategy-delta.json` | `feedback-learning` |

## Runtime Scripts

| Script | Purpose |
| --- | --- |
| `scripts/create_workspace.py` | Create a clean personal or commercial workspace from the public template |
| `scripts/validate_workspace.py` | Validate a user-data workspace root and current pointers |
| `scripts/collect_youtube_references.py` | Collect YouTube reference candidates and score strategy fit |
| `scripts/generate_reference_research_plan.py` | Generate a platform/query/sample plan from strategy and current draft |
| `scripts/download_reference_transcripts.py` | Search reference videos, download media when needed, and extract usable transcripts only |
| `scripts/collect_teaching_video_scripts.py` | Legacy combined collector/analyzer for AI teaching videos |
| `scripts/decompose_reference_strategy.py` | Post-process extracted transcripts into reusable strategy deconstruction and current-draft guidance |
| `scripts/promote_reference_deconstruction.py` | Dry-run or write approved deconstruction into the durable reference bank |
| `scripts/generate_topics_from_deconstruction.py` | Generate test topic candidates from a reference strategy deconstruction run |
| `scripts/optimize_copy_with_reference_bank.py` | Diagnose a draft and retrieve reusable reference patterns before rewriting |
| `scripts/run_daily_viral_mining.py` | Daily runner for viral AI teaching/workflow video mining, transcript parsing, and run records |
| `scripts/generate_daily_scene_radar.py` | Build a topic evidence/scene radar from existing workspace assets |
| `scripts/build_ops_dashboard_data.py` | Build normalized operations-dashboard data and freshness status |
| `scripts/render_ops_dashboard.py` | Render a standalone operations dashboard from public template + private data |
| `scripts/update_ops_dashboard.py` | Rebuild dashboard data and HTML through one stable command |
| `scripts/generate_weekly_topic_library.py` | Render weekly topic radar HTML into the user-data workspace |
| `scripts/run_weekly_topic_workflow.sh` | Stable automation entry for validate -> render -> validate |
| `scripts/audit_public_release.py` | Validate schemas, P2 contract, public/private boundary, and offline smoke tests |

## Business Logic Docs

| Doc | Purpose |
| --- | --- |
| `docs/workflow-blueprint.md` | Overall short-video operations workflow blueprint |
| `docs/workflow-dependency-graph.md` | Workflow dependency graph and handoff rules |
| `docs/automation-business-logic.md` | Current automation policy, active schedules, manual boundaries, and strategy update rules |
| `docs/capability-coverage.md` | Tested P2 capability and workflow execution matrix |
| `docs/public-release.md` | External product copy, community/commercial boundary, and release gate |
| `docs/quick-start.md` | Plain-language installation and first-dashboard guide |
| `docs/ops-dashboard-guide.md` | Map dashboard sections to workflows and daily use |

## Workflow Order

```text
01 Auto Ops Diagnosis
02 Pain Bank Builder
03 Strategy Confirmation
04 Reference Mining
04a Reference Research Plan
04b Reference Transcript Download
04c Reference Strategy Deconstruction
04d Reference Bank Ingest
05 Weekly Topic Radar
06 Script Planning
06a Copy Optimization Reference Match
07 Feedback Learning
```

Do not run downstream workflows before strategy confirmation unless the workflow manifest explicitly allows it.

## Operating Modes

| Mode | Use Case | Main Difference |
| --- | --- | --- |
| `personal` | Operator's own account | Allows private operator context and faster internal iteration |
| `commercial` | Client delivery or packaged product | Requires white-label behavior and stricter data isolation |

## Update Rule

If a directory or data contract changes, update:

```text
README.md
INDEX.md
directory.index.json
templates/project-workspace/workspace.index.json
project.manifest.json when current pointers change
schemas/*.schema.json when asset contracts change
```
