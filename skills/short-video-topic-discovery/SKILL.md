---
name: short-video-topic-discovery
description: Assess a short-video account's confirmed direction, discover strategy-bounded topic opportunities, maintain separate 60/40 conservative and experimental candidate lanes, and select a 2+1 daily mix with evidence lineage.
---

# Short-video topic discovery

This skill owns the most judgment-heavy part of the system: finding topics. It does not diagnose the account, deconstruct benchmarks, write scripts, or render the dashboard.

## 1. Resolve the workspace

Run:

```bash
python3 scripts/discover_context.py /absolute/path/to/workspace
```

Read only paths returned by the workspace manifest. If multiple files could serve the same role, stop and report ambiguity.

Before generating candidates, verify the manifest-declared account, audience, and offer profiles plus `config/strategy/strategy-brief.json`. If positioning or strategy is absent, still a public-template example, lacks confirmed provenance, or is not user-confirmed, ask the user to confirm the target audience, problem domain, industry and main direction, first-person proof, stage goal, topic principles, exclusions, and conversion path. Wait for explicit confirmation; do not generate a candidate pool from inferred defaults.

## 2. Verify the strategy boundary

Require confirmed account positioning provenance and `config/strategy/strategy-brief.json`. A topic, tool name, campaign, performance symptom, or dashboard headline is not strategy.

Using account performance, classify the current direction as:

- `continue_current_strategy`: evidence supports continuing it;
- `optimize_execution`: direction remains valid, but hooks, proof, pacing, CTA or topic mix need work;
- `run_validation_experiment`: evidence is insufficient or mixed, so test without changing confirmed strategy;
- `propose_strategy_review`: repeated evidence suggests a direction change; output a proposal, never overwrite strategy automatically.

Write the assessment to the manifest-declared `strategy_assessment` path.

## 3. Build the search scope

Derive explicit scope IDs from positioning, audience, industry, main tracks, stage goal, exclusions and the assessment decision. Search for attributable opportunity signals across first-party questions, search interest, current topics, industry change, market tasks and content gaps. Record source, observed date, query, evidence role, scope IDs and momentum. Popular creator content is supply-side material, not topic proof.

## 4. Build physically separate candidate lanes

- Conservative lane, 60%: close to confirmed strategy, proven audience problems and established industry interest. Every candidate must be `account_fit.fit_status=core` with persona, problem-domain and first-person proof checks true.
- Experimental lane, 40%: adjacent but plausible opportunities based on newer signals. Every candidate declares a hypothesis, risk and success metric. Experiments cannot rewrite the conservative pool.

For a 10-topic pool, write six conservative and four experimental candidates to the separate manifest-declared files. Every candidate must keep `strategy_id`, `strategy_assessment_id`, `search_scope_ids`, `signal_ids`, lane, score components and a distinct publishable angle.

## 5. Select today's 2+1 mix

Rank candidates on account fit, audience value, evidence strength, timing, distinctiveness, demonstrability and production feasibility. Select two conservative topics plus one experimental topic. Selection does not delete the remaining candidates.

## Boundaries

- Do not alter account profile, confirmed strategy, published records, benchmarks, plans or HTML.
- Do not use operating symptoms as audience demand.
- Do not search benchmarks until formal candidates exist.
- Do not fill missing evidence with old runs or another workspace.
- Return `blocked` when provenance, strategy, coverage or lineage is insufficient.
