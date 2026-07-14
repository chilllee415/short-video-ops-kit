---
name: short-video-ops-semantic-layer
description: Interpret and audit a domain-first short-video-ops workspace. Use when reading, writing, automating, migrating, or debugging strategy, operating performance, topic evidence, benchmarks, plans, feedback, manifests, schemas, or dashboard artifacts.
---

# Short-video operations semantic layer

Use this skill before changing the daily workflow, its automation prompt, or workspace data.

## Required reading

1. Read `references/semantic-layer.md` for entity meanings and decision boundaries.
2. Read `references/source-inventory.md` before selecting files or checking freshness.
3. Read `references/evidence.md` when auditing a topic recommendation or prior run.
4. In the target workspace, read `data.contract.json`, `workspace.index.json`, and `project.manifest.json`. A newer, internally consistent live contract takes precedence.

## Onboarding preflight

Treat account positioning and confirmed strategy as user-owned L0/L1 inputs. Before reading downstream evidence, verify the manifest-declared profile files and `config/strategy/strategy-brief.json`. If they are absent, still contain public-template examples, lack confirmation provenance, or are not user-confirmed, ask the user to supply or confirm them and stop downstream execution. Never reconstruct L0/L1 from topics, benchmarks, performance symptoms, plans, or presentation files.

A first-run questionnaire is an L0/L1 intake aid, not confirmed configuration. It must collect niche-neutral facts before proposing direction: account stage, niche, creator role, audience, needs, real resources, business goal, sustainable formats, exclusions, and future plan. Its answers may produce multiple positioning and strategy proposals, but the selected proposal remains unconfirmed until the user explicitly approves the summarized meaning. Do not treat a browser-local draft, algorithmic recommendation, or copied prompt as confirmation by itself.

## Operating rules

- Resolve every input to one semantic layer before using it.
- Keep confirmed strategy stable unless the user approves a strategy change.
- Use operating data to tune hooks, pacing, duration, proof timing, CTA, and topic mix. Do not turn a performance symptom into a topic opportunity.
- Establish a formal topic only from attributable `audience_pain`, `search_interest`, `hot_topic`, `industry_signal`, `market_task`, or `content_gap` evidence inside the confirmed search scope.
- Treat creator posts and popularity as `supply_content`; use them after topic creation to find and deconstruct benchmarks.
- Treat plans and HTML as downstream outputs, never evidence.
- Trace every ready topic through `topic_id -> strategy_id -> strategy_assessment_id -> search_scope_ids -> signal_ids`; `pain_id` is optional.
- If valid evidence is missing, write a blocked result and do not refresh the dashboard with invented conclusions.
- State freshness using source dates, not file modification time.

## Output contract

For each workflow node, record its semantic level, input paths and accepted roles, output paths, prohibited reads and writes, status, and blockers. Run the workspace validator and daily finalizer before claiming completion.
