# Architecture

## Goal

Build a commercial short-video operations system where every workflow knows:

```text
what data to read
what data to write
which strategy is confirmed
which user pain is being served
which output is only a run artifact
which feedback should return to strategy review
```

## Layers

```text
01 Raw Data
  source exports, comments, DMs, competitor links, reference content

02 Normalized Assets
  account snapshot, audience signals, pain bank, competitor map, reference bank

03 Strategy
  confirmed strategy brief, scoring weights, decision log

04 Generated Outputs
  topic radar, selected topics, scripts, recording plans

05 Publish
  publishing plan and posted video records

06 Feedback
  post metrics, feedback learning, strategy delta

07 Skills
  workspace skills, raw legacy imports, commercial candidates, distilled capability assets

99 Runs
  immutable run inputs, outputs, and logs
```

## Non-Negotiable Rules

1. Topic generation must read a confirmed strategy.
2. A formal topic must reference `pain_id`.
3. Reference content can supply structure, but cannot decide direction.
4. Feedback can create `strategy-delta`, but cannot overwrite `strategy-brief`.
5. Missing data produces a missing-data report instead of invented conclusions.
6. Raw legacy skills are not active capabilities until they are indexed, reviewed, and assigned to a workflow.

## Data Spine

```text
account.profile
  -> account-snapshot
  -> pain-bank
  -> strategy-brief
  -> reference-bank
  -> topic-candidates
  -> selected-topics
  -> scripts / recording-plans
  -> posted-videos
  -> feedback-learning
  -> strategy-delta
  -> strategy-confirmation
```

## Why Pain Bank Is Central

The system should not ask:

```text
What trending topic can we copy?
```

It should ask:

```text
Which target user has which repeated pain, and what visible result can we show?
```

Reference mining happens after pain and strategy are known.

## Agent Contract

Every agent should:

1. Read repository `directory.index.json` when it needs to understand the public project structure.
2. Resolve the workspace root from an explicit path or `SHORT_VIDEO_OPS_WORKSPACE`.
3. Read workspace `project.manifest.json`.
4. Read workspace `workspace.index.json`.
5. Read workspace `workspace.policy.json`.
6. Read its workflow manifest under `manifests/`.
7. Check required inputs.
8. Validate inputs when schema is available.
9. Refuse to fabricate missing data.
10. Write outputs only to declared paths.
11. Leave a run record under `runs/<run-id>/`.

## Data Source Model

The code repository and customer data source are separate.

```text
short-video-ops/system/       public system repo
client-workspace/             private data source, can live anywhere
```

The agent only needs one runtime input:

```text
workspace_root
```

From there, it reads:

```text
workspace_root/project.manifest.json
workspace_root/workspace.index.json
```

Do not store real workspaces inside this repository. Keep user data in a separate user-data project such as `short-video-ops/user-data/<workspace-id>`.

## Operating Modes

The same system supports two modes:

```text
personal     self-use workspace
commercial   client delivery or packaged workflow
```

Both modes use the same directory structure. The difference is policy:

```text
personal:
  allows private operator context
  allows faster internal iteration
  does not require white-label export by default

commercial:
  forbids operator personal identity in outputs
  requires white-label behavior
  requires stricter strategy confirmation and data isolation
```

The mode is declared in `project.manifest.json` and enforced through `workspace.policy.json`.

## Public vs Private

Public repository:

```text
schemas
manifests
templates
scripts
docs
examples
commercial-safe skills
```

Private/customer workspace:

```text
raw user data
comments and DMs
customer interviews
internal strategy decisions
published performance data
raw legacy skills and personal skill notes
```

Never commit private workspaces.
