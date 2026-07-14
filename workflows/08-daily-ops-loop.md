# 08 Daily Ops Loop

Run one ordered evidence chain without mixing data layers:

```text
stable positioning + confirmed content strategy ─────────────┐
                                                             v
operations data -> strategy health decision -> topic search space -> find topics
                 -> execution constraints                     -> candidate topics
                                                              -> benchmark structure
                                                              -> execution plan
                                                              -> dashboard
                                                              -> publish feedback
```

Read the workspace `data.contract.json` and this workflow's manifest before every run.

## Layer meanings

| Layer | Function | May influence | Must not become |
| --- | --- | --- | --- |
| Account strategy | Set durable audience, direction, topic strategy, conversion path, boundaries | Topic search scope | Daily observation or single topic |
| Operations data | Diagnose views, retention, completion, interaction, profile visits, leads, and topic performance | Strategy evidence plus Hook, pacing, duration, proof timing and CTA constraints | Account positioning |
| Strategy assessment | Separate direction health from execution, cadence, audience quality and conversion | Keep, optimize execution, validate, or propose a content-strategy adjustment | Automatic strategy rewrite |
| Topic discovery | Build the search space from positioning, confirmed strategy and assessment, then find opportunity signals | Candidate topics | Confirmed account strategy |
| Benchmark research | Learn packaging from content about an already selected problem | Hook, proof, structure, pacing, CTA | Demand proof or strategy |
| Execution plan | Apply operating constraints to candidate topics | Script and recording plan | Strategy |
| Dashboard | Present verified upstream artifacts | Nothing upstream | Source of truth |

## Topic signal roles

Every daily topic signal must declare `evidence_role`:

- `audience_pain`: a user-side question, complaint, request, comment, DM, or customer statement.
- `search_interest`: a search suggestion, related search, rising query, or attributable search-intent signal.
- `hot_topic`: a current event, product change, concept, or discussion that is rising inside the account's industry or adjacent track.
- `industry_signal`: a niche change, case, debate, method, or underserved angle.
- `market_task`: a repeated responsibility or business job shown by authoritative market evidence, such as job descriptions or workflow records.
- `content_gap`: a relevant audience, scene, counterexample, result, or implementation angle that existing content has not covered well.
- `strategy_evidence`: first-party evidence used to evaluate whether the current content direction remains supported.
- `execution_constraint`: account performance evidence used to optimize Hook, pacing, proof and CTA.
- `operational_constraint`: legacy first-party constraint role; normalize to one of the two roles above in new runs.
- `supply_content`: a creator tutorial, competitor post, reference video, or popular article. Use it only in benchmark research.

A formal topic needs confirmed-strategy fit plus at least one attributable opportunity signal from the first six roles. Pain is one input, not a mandatory root. A like count can support attention/packaging validation, but it cannot change account strategy by itself.

## Node order

### 1. Observe operations

Read the newest real account and post data. Preserve the real source date.

Write `ops-diagnosis.json` with:

- metric changes and topic-performance patterns;
- current packaging/script problems;
- tactical constraints for Hook, pacing, duration, proof timing, CTA, and topic mix;
- missing first-party fields.

Do not generate account direction here. Strategy changes may only be proposed in `strategy-delta.json`.

### 2. Load the strategy boundary

Read `config/profile/` and confirmed `config/strategy/strategy-brief.json`. Write a run-scoped `topic-research-brief.json` that states:

- account positioning, industry and target audience;
- main content tracks, niche boundaries and current-stage plan;
- allowed/excluded scenes and future directions;
- query families for core track, audience problems, search interest, hot topics, industry change, adjacent angles and future direction;
- what operational constraints will later shape execution but not the search space.

Do not edit profile or strategy.

### 3. Assess strategy health

Write `data/topic-research/current/strategy-assessment.json`. Evaluate direction, execution, cadence, audience quality and conversion separately. Choose exactly one decision:

- `continue_current`
- `optimize_execution`
- `run_validation_experiment`
- `propose_strategy_adjustment`

Insufficient evidence must produce a validation experiment. Proposing an adjustment requires at least three comparable public posts, two execution variants and persistently weak target response. Never overwrite positioning or confirmed strategy.

### 4. Find topics

Treat this as strategy-bounded topic discovery, not pain collection and not benchmark-only search.

Cover at least three query families. Use comments, DMs, customer dialogue, platform search suggestions, trend tools, forum questions, industry news/changes, competitor gaps, repeated jobs and job descriptions. Persist every signal with its role, matched search-scope ids and provenance.

Supply-side content found during discovery must be marked `supply_content`. It may support attention or packaging confidence only after strategy fit is established.

Write the dated raw capture, canonical `data/topic-research/current/topic-signals.json`, and `topic-discovery-result.json`. If the search scope is incomplete or there is no attributable strategy-matched opportunity signal, stop with `blocked`; do not invent candidates.

The assessment decision changes search mode: reinforce the current direction, search for stronger angles, generate controlled validation pairs, or compare the current direction with clearly labeled adjacent proposals.

### 5. Build isolated candidate lanes

Generate candidate topics from validated opportunity signals. Every formal topic must carry:

```text
topic_id -> lane -> confirmed strategy_id -> strategy_assessment_id -> account_fit -> search_scope_ids -> signal_ids
```

`pain_id` is optional and only used when the topic maps to a maintained pain-bank entry. Build and rank the conservative and experimental lanes independently. Conservative supply is 60% and must be core account fit; experimental supply is 40%, must have first-person proof, a validation hypothesis and an expiry. Neither writer may read or overwrite the other lane.

Join the two ready lanes at a separate selection node. A three-topic day is exactly two conservative plus one experimental. The selector does not recompute one global score and cannot promote an experimental topic into the conservative lane.

### 6. Research matching benchmarks

Only after the mixed selection exists, fan out per selected topic to find content addressing the same topic, audience, scene or angle. Record real metrics separately from structural judgment. Learn Hook, proof, structure, pacing, and CTA; never copy source language, media, or cases or change lane membership.

### 7. Build the plan

Use operations data here—not when establishing the search space—to optimize each candidate's title, first 3 seconds, length, information density, proof placement, CTA, topic mix and experiment design.

Write `work/plans/daily.json` with real source dates and complete lineage.

### 8. Render and verify

Run the finalizer only when the plan is not blocked and every formal topic has valid strategy scope plus opportunity signals. The finalizer validates schema, signal roles, lineage, freshness, and HTML bindings before writing closure.

The HTML may not hard-code current strategy conclusions, scan status, timestamps, or scores. It must render them from upstream JSON.

### 9. Ingest publish feedback

When new real posts or metrics exist, normalize them from `data/feedback/raw/` into `data/feedback/current/learning.json`. Strategy changes remain proposals in `data/feedback/current/strategy-delta.json`; the daily workflow cannot change confirmed strategy or publish content.

## Finalizer

```bash
python3 scripts/finalize_daily_ops_loop.py \
  /path/to/client-workspace \
  --run-id YYYY-MM-DD-daily-ops-loop
```
