---
name: short-video-ops
description: Run a contract-backed short-video operations loop from account performance and confirmed strategy through strategy-bounded topic discovery, candidate topics, benchmark research, execution planning, dashboard rendering, and publish feedback. Use when operating or debugging a short-video-ops workspace.
---

# Short-video operations

Read `project.manifest.json`, `data.contract.json`, `workspace.policy.json`, and the selected workflow manifest before reading business data. Resolve paths from the workspace root; never search another workspace to fill missing inputs.

## Onboarding preflight

Before running any downstream node, inspect the manifest-declared account, audience, and offer profiles plus `config/strategy/strategy-brief.json`. Positioning and strategy are not ready when files are absent, still contain public-template examples, positioning lacks confirmed provenance, or strategy is not confirmed by the user.

If either is not ready, pause the loop and confirm the account stage, primary niche, creator role, target audience, audience needs, real resources, stage goal, commercial destination, sustainable formats, exclusions, and future plan. Do not assume an AI, knowledge, commerce, or lifestyle niche. Generate multiple direction proposals from those facts, let the user choose or revise one, then summarize the proposed values and wait for explicit confirmation before writing them. Until then, do not discover topics, mine benchmarks, write scripts, create a `ready` plan, or refresh the dashboard with inferred conclusions.

If the user provides a structured first-run questionnaire payload, validate it against those same fields instead of repeating every question. Identify contradictions or missing fields, produce one positioning draft and one stage-strategy draft, and ask for explicit confirmation. Treat the questionnaire and generated drafts as unconfirmed intake until the user approves them.

## Daily order

```text
operations diagnosis
-> confirmed strategy boundary
-> user-side topic evidence
-> candidate topics
-> topic-specific benchmark research
-> execution plan
-> dashboard render and verification
-> publish feedback
```

## Skill routing

- Use `short-video-topic-discovery` for strategy assessment, opportunity signals, candidate lanes, and the 2+1 selection.
- Use `short-video-benchmark-mining` only after topics are selected, for per-topic reference search and structural deconstruction.
- Use `short-video-copywriting` after benchmark deconstruction, for evidence-backed spoken scripts and shot actions.
- Keep manifest and schema boundaries authoritative even when a specialized Skill is installed.

## Semantic boundaries

- Strategy is stable direction, not a topic, tool, stage, or performance symptom.
- Operations data tunes hook, pacing, duration, proof timing, CTA, and topic mix; it does not prove demand.
- Formal topics start from a confirmed strategy search space plus attributable `audience_pain`, `search_interest`, `hot_topic`, `industry_signal`, `market_task`, or `content_gap` signals.
- Creator content and popularity are `supply_content`; use them after topic creation for structure only.
- A ready topic requires `topic_id -> strategy_id -> strategy_assessment_id -> search_scope_ids -> signal_ids` lineage; `pain_id` is optional.
- A blocked plan contains no executable topics and cannot update the dashboard.
- Presentation files are outputs, never evidence.

Write only declared node outputs. Daily automation must not change profile, confirmed strategy, user-selected topics, or published records. Preserve real source dates and report missing access instead of inventing data.
