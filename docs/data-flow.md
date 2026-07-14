# Data Flow

## Workflow Flowchart

```text
Confirmed account strategy + operations facts
  -> Strategy-health assessment
  -> [Audience evidence || market signals]
  -> Normalize topic opportunities
  -> [Conservative candidates 60% || experimental candidates 40%]
  -> Mix selection (daily 2 + 1)
  -> Benchmark fan-out per selected topic
  -> Script Planning
  -> Publish
  -> Feedback Learning
  -> Strategy Delta
  -> Strategy Confirmation
```

## Data Ownership

| Data | Owner Workflow | Readers |
| --- | --- | --- |
| `account-snapshot.json` | auto-ops-diagnosis | strategy, topic radar |
| `audience-signals.json` | audience-evidence collector | topic opportunity normalizer |
| `market-signals.json` | market-signal collector | topic opportunity normalizer |
| `pain-bank.json` | pain-bank-builder | strategy, reference mining, topic radar, scripts |
| `strategy-brief.json` | strategy-confirmation | all downstream workflows |
| `reference-bank.json` | reference-mining | topic radar, scripts |
| `conservative/current.json` | conservative candidate writer | selection mix, script planning |
| `experimental/current.json` | experimental candidate writer | selection mix, script planning |
| `selections/daily.json` | selection mix writer | benchmark mining, script planning, feedback |
| `posted-videos.json` | publish | feedback-learning |
| `feedback-learning.json` | feedback-learning | strategy-confirmation, topic radar |
| `strategy-delta.json` | feedback-learning | strategy-confirmation |

## Workspace Index

Each workspace has `workspace.index.json`.

Its job is to answer:

```text
Where is user operations data?
Where is account strategy data?
Where is competitor data?
Where is reference content?
Where is customer voice data?
Which workflow owns each group?
Which normalized file should downstream agents read?
```

Agents should not guess data paths from memory. They should read `workspace.index.json` first, then read the workflow manifest.

## Single Data Source

At runtime, an agent should receive exactly one workspace root:

```text
workspace_root = /path/to/client-workspace
```

All workflow reads and writes are relative to this root.

This keeps the system simple:

```text
system repo = code, templates, schemas, manifests
workspace root = real data, strategy, generated outputs, feedback
```

The workspace root does not need to be committed and should usually live outside the system repository.

## Closed Loop

Feedback does not directly change strategy.

```text
post metrics
  -> feedback-learning
  -> strategy-delta
  -> user confirmation
  -> new strategy-brief
```

This prevents the system from overreacting to one post or chasing vanity metrics.

## Formal Topic Requirements

A topic is formal only if it has:

```text
topic_id
lane
strategy_id
strategy_assessment_id
account_fit
search_scope_ids
signal_ids
validation_hypothesis
```

Recommended:

```text
reference_ids
evidence_ids
recording_plan_ref
```

`pain_id` is optional when another attributable signal proves the opportunity. Conservative candidates require all account-fit gates. Experimental candidates additionally require an expiry and may only be promoted after comparable public tests plus user confirmation.

## Missing Data Behavior

Every workflow should stop with a structured missing-data report when required inputs are absent:

```json
{
  "status": "blocked_missing_data",
  "workflow_id": "topic-candidates",
  "missing_inputs": [
    "data/topic-research/current/pain-bank.json",
    "config/strategy/strategy-brief.json"
  ],
  "next_action": "Run pain-bank-builder and strategy-confirmation first."
}
```
