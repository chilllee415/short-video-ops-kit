# Operating Modes

The system supports two operating modes with the same data spine:

```text
personal     self-use, fast iteration, richer private context
commercial   client delivery, white-label, stricter isolation and export rules
```

The mode is declared in:

```text
project.manifest.json -> operating_mode
project.manifest.json -> workspace_policy
```

## Shared Spine

Both modes use the same workspace structure:

```text
config/profile/
config/strategy/
data/operations/
data/topic-research/
data/benchmarks/
data/feedback/
work/
presentation/
runs/
archive/
```

This prevents the product from splitting into two systems.

## Personal Mode

Use this when the operator is running their own account.

Characteristics:

- Can keep long-running personal context.
- Can store internal notes and experiments in the workspace.
- Can prioritize speed and iteration over packaging polish.
- Can use private account data directly.
- Does not need white-label export by default.

Still required:

- Do not fabricate data.
- Keep `pain_id` and `strategy_id` lineage.
- Keep feedback loop.

## Commercial Mode

Use this when delivering to customers or packaging the workflow for sale.

Characteristics:

- No operator personal identity in outputs.
- Customer data must be isolated by workspace.
- Exportable outputs must be white-label.
- Strategy must be user-confirmed before topic generation.
- References must not bypass pain bank.
- Feedback can suggest strategy changes but cannot overwrite confirmed strategy.

## Mode Decision

```text
Is this for the operator's own account?
  -> personal

Is this for a client, template, course, or paid delivery?
  -> commercial
```

## Policy Files

Default policies:

```text
templates/workspace-policies/personal.policy.json
templates/workspace-policies/commercial.policy.json
```

Each workspace can copy one policy into:

```text
workspace.policy.json
```
