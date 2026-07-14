# Source inventory

Resolve all relative paths from the selected workspace root. Never search another workspace to fill a missing manifest target.

| Source | Canonical locator | Function | Daily write boundary |
| --- | --- | --- | --- |
| Workspace pointers | `project.manifest.json` | Current source and artifact paths | Migration only |
| Domain contract | `data.contract.json` | Meanings, precedence and lineage | Model change only |
| Identity | `config/profile/` | Audience, offer and positioning | User-confirmed only |
| Strategy | `config/strategy/strategy-brief.json` | Direction and exclusions | Separate approval flow |
| Policies | `config/policies/` | Discovery, selection and benchmark rules | Explicit policy revision |
| Operations | `data/operations/` | Performance and execution constraints | Capture and normalize |
| Topic research | `data/topic-research/` | Strategy assessment and opportunity signals | Replace current after validation |
| Benchmarks | `data/benchmarks/` | Reusable expression patterns | Update with provenance |
| Candidate topics | `work/topics/` | Conservative/experimental pools and selection | Rebuild pools; preserve explicit selections |
| Plans | `work/plans/` | Executable daily plan | Rebuild from valid upstream inputs |
| Feedback | `data/feedback/` | Next-cycle learning | Never overwrite strategy |
| Presentation | `presentation/` | Human review | Render only after gates |
| Runs | `runs/` | Audit trail and node outputs | Append per run |
