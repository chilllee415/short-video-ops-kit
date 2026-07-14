#!/usr/bin/env python3
"""Validate the daily content plan, rebuild the V2 dashboard, and close the run."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import jsonschema


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"missing file: {path}") from None
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid json: {path}: {exc}") from None
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def write_object(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_presentation_status(
    workspace: Path,
    status: str,
    reason: str,
    source_date: str = "",
) -> None:
    html_path = workspace / "presentation/internal-pages/运营大盘.html"
    status_path = workspace / "presentation/status.json"
    existing = load_object(status_path) if status_path.exists() else {}
    write_object(
        status_path,
        {
            "status": status,
            "as_of": source_date,
            "reason": reason,
            "canonical_dashboard_exists": status == "ready" and html_path.exists(),
            "next_action": (
                "Review blockers and rebuild upstream evidence."
                if status != "ready"
                else "Use publish feedback in the next operations cycle."
            ),
            "invalidated_artifacts": [] if status == "ready" else list(existing.get("invalidated_artifacts") or []),
        },
    )


def validate_strategy_assessment(
    assessment: dict[str, Any], plan: dict[str, Any], signals: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    assessment_id = str(assessment.get("assessment_id") or "")
    if plan.get("strategy_assessment_id") != assessment_id:
        errors.append("plan strategy_assessment_id does not match current strategy assessment")
    if plan.get("strategy_id") != assessment.get("strategy_id"):
        errors.append("plan strategy_id does not match current strategy assessment")
    if signals.get("strategy_assessment_ref") != "data/topic-research/current/strategy-assessment.json":
        errors.append("topic signals do not reference the canonical strategy assessment")
    decision = assessment.get("decision")
    if (signals.get("topic_search_scope") or {}).get("strategy_decision") != decision:
        errors.append("topic search scope strategy_decision does not match current assessment")
    proposal = assessment.get("proposed_strategy_change") or {}
    window = assessment.get("evidence_window") or {}
    if decision == "run_validation_experiment" and not assessment.get("validation_experiments"):
        errors.append("run_validation_experiment requires at least one validation experiment")
    if decision == "propose_strategy_adjustment":
        if proposal.get("status") != "proposed":
            errors.append("propose_strategy_adjustment requires proposed_strategy_change.status=proposed")
        if proposal.get("requires_user_confirmation") is not True:
            errors.append("strategy adjustment proposals require user confirmation")
        if int(window.get("comparable_post_count") or 0) < 3:
            errors.append("strategy adjustment requires at least 3 comparable public posts")
        if int(window.get("execution_variant_count") or 0) < 2:
            errors.append("strategy adjustment requires at least 2 execution variants")
    return errors


def validate_lineage(
    plan: dict[str, Any], workspace: Path, signals: dict[str, Any], assessment: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    strategy_id = str(plan.get("strategy_id") or "")
    strategy = load_object(workspace / "config/strategy/strategy-brief.json")
    account_profile = load_object(workspace / "config/profile/account.profile.json")
    reference_bank = load_object(workspace / "data/benchmarks/current/reference-bank.json")
    conservative_lane = load_object(workspace / "work/topics/conservative/current.json")
    experimental_lane = load_object(workspace / "work/topics/experimental/current.json")
    topic_selection = load_object(workspace / "work/topics/selections/daily.json")
    confirmed_strategy_id = str(strategy.get("strategy_id") or "")
    policy = load_object(workspace / "workspace.policy.json")
    confirmation_required = bool(
        ((policy.get("workflow_rules") or {}).get("strategy_confirmation_required_for_formal_topics"))
    )
    if account_profile.get("positioning_status") != "confirmed":
        errors.append(
            "account positioning is not confirmed; formal topic generation must stop before search"
        )
    provenance = account_profile.get("positioning_provenance") or {}
    required_provenance = {
        "positioning_source_type",
        "positioning_source_ref",
        "confirmation_quote",
        "confirmed_at",
    }
    if account_profile.get("positioning_status") == "confirmed" and not all(
        provenance.get(field) for field in required_provenance
    ):
        errors.append("confirmed account positioning is missing required provenance")
    if (
        plan.get("status") == "ready"
        and confirmation_required
        and strategy.get("confirmed_by_user") is not True
    ):
        errors.append(
            "a ready daily plan requires strategy-brief.json confirmed_by_user=true"
        )
    known_reference_ids = {
        str(item.get("reference_id")) for item in reference_bank.get("references") or [] if item.get("reference_id")
    }
    topic_by_id: dict[str, dict[str, Any]] = {}
    for lane_name, lane_artifact in (
        ("conservative", conservative_lane),
        ("experimental", experimental_lane),
    ):
        for raw_item in lane_artifact.get("topics") or []:
            if not raw_item.get("topic_id"):
                continue
            item = dict(raw_item)
            item["_lane"] = lane_name
            topic_by_id[str(item["topic_id"])] = item
    known_topic_ids = set(topic_by_id)
    selected_rows = topic_selection.get("selected") or []
    selected_ids = [str(item.get("topic_id")) for item in selected_rows if item.get("topic_id")]
    if plan.get("status") == "ready":
        if conservative_lane.get("status") != "ready":
            errors.append("conservative topic lane must be ready")
        if experimental_lane.get("status") != "ready":
            errors.append("experimental topic lane must be ready")
        if topic_selection.get("status") != "ready":
            errors.append("mixed topic selection must be ready")
        selected_counts = {
            "conservative": sum(1 for row in selected_rows if row.get("lane") == "conservative"),
            "experimental": sum(1 for row in selected_rows if row.get("lane") == "experimental"),
        }
        if selected_counts != {"conservative": 2, "experimental": 1}:
            errors.append("daily topic selection must contain 2 conservative and 1 experimental topic")
        plan_ids = [str(item.get("topic_id")) for item in plan.get("plans") or []]
        if plan_ids != selected_ids:
            errors.append("daily plan topics and order must match mixed topic selection")
    signal_by_id = {
        str(item.get("signal_id")): item
        for item in signals.get("signals") or []
        if item.get("signal_id")
    }
    if confirmed_strategy_id and strategy_id != confirmed_strategy_id:
        errors.append("plan strategy_id does not match confirmed strategy-brief.json")
    for index, item in enumerate(plan.get("plans") or [], start=1):
        prefix = f"plans[{index}]"
        if item.get("strategy_id") != strategy_id:
            errors.append(f"{prefix}.strategy_id does not match plan strategy_id")
        if item.get("strategy_assessment_id") != assessment.get("assessment_id"):
            errors.append(f"{prefix}.strategy_assessment_id does not match current assessment")
        if not item.get("search_scope_ids"):
            errors.append(f"{prefix}.search_scope_ids is required")
        signal_ids = item.get("signal_ids") or item.get("evidence_ids") or []
        if not signal_ids:
            errors.append(f"{prefix} needs signal_ids")
        evidence = [signal_by_id.get(str(signal_id)) for signal_id in signal_ids]
        valid_topic_signals = [
            signal
            for signal in evidence
            if signal and signal.get("evidence_role") in {
                "audience_pain",
                "search_interest",
                "hot_topic",
                "industry_signal",
                "market_task",
                "content_gap",
            }
        ]
        if plan.get("status") == "ready" and not valid_topic_signals:
            errors.append(
                f"{prefix} requires at least one strategy-matched opportunity signal; "
                "strategy/execution evidence, operational constraints and supply content are context only"
            )
        if known_topic_ids and str(item.get("topic_id")) not in known_topic_ids:
            errors.append(f"{prefix}.topic_id is not present in either candidate lane")
        if plan.get("status") == "ready" and str(item.get("topic_id")) not in selected_ids:
            errors.append(f"{prefix}.topic_id is not present in mixed daily selection")
        candidate = topic_by_id.get(str(item.get("topic_id"))) or {}
        account_fit = candidate.get("account_fit") or {}
        lane_name = candidate.get("_lane")
        if lane_name == "conservative":
            if account_fit.get("fit_status") != "core":
                errors.append(f"{prefix} conservative topic must have fit_status=core")
            for field in ("persona_match", "problem_domain_match", "first_person_proof"):
                if account_fit.get(field) is not True:
                    errors.append(f"{prefix}.account_fit.{field} must be true for conservative topics")
        elif lane_name == "experimental":
            if account_fit.get("fit_status") not in {"core", "adjacent_experiment"}:
                errors.append(f"{prefix} experimental topic has an invalid fit_status")
            for field in ("persona_match", "first_person_proof"):
                if account_fit.get(field) is not True:
                    errors.append(f"{prefix}.account_fit.{field} must be true for experimental topics")
            if not candidate.get("validation_hypothesis") or not candidate.get("expires_at"):
                errors.append(f"{prefix} experimental topic requires validation_hypothesis and expires_at")
            else:
                try:
                    if date.fromisoformat(str(candidate["expires_at"])[:10]) < date.fromisoformat(str(plan.get("plan_date"))):
                        errors.append(f"{prefix} experimental topic is expired")
                except ValueError:
                    errors.append(f"{prefix} experimental topic has an invalid expires_at")
        else:
            errors.append(f"{prefix} has no candidate lane")
        if not account_fit.get("fit_reason") or not account_fit.get("content_role"):
            errors.append(f"{prefix}.account_fit requires fit_reason and content_role")
        unknown_references = [
            str(ref_id) for ref_id in item.get("reference_ids") or [] if known_reference_ids and str(ref_id) not in known_reference_ids
        ]
        if unknown_references:
            errors.append(f"{prefix}.reference_ids are not present in reference-bank.json: {', '.join(unknown_references)}")
    return errors


def validate_topic_coverage(signals: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    checked = [item for item in signals.get("checked_sources") or [] if item.get("status") == "checked"]
    discovery = {str(item.get("platform")) for item in checked if item.get("source_class") == "discovery"}
    search_scope = signals.get("topic_search_scope") or {}
    query_families = {str(item) for item in search_scope.get("query_families") or [] if item}
    coverage = signals.get("coverage_status")
    if coverage == "complete" and (len(query_families) < 3 or len(discovery) < 2):
        errors.append("complete topic coverage requires a complete search scope, three query families, and two discovery platforms")
    if plan.get("status") == "ready" and coverage == "blocked":
        errors.append("a ready daily plan cannot use blocked topic coverage")
    if plan.get("status") == "ready" and not signals.get("signals"):
        errors.append("a ready daily plan requires at least one attributable topic opportunity signal")
    return errors


def validate_benchmark_deconstruction(
    workspace: Path, run_id: str, plan: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    path = workspace / "runs" / run_id / "outputs" / "reference-strategy-deconstruction.json"
    if not path.exists():
        return ["missing reference-strategy-deconstruction.json for this run"]
    artifact = load_object(path)
    if artifact.get("status") != "complete":
        errors.append("benchmark deconstruction status must be complete")
    rows = artifact.get("topic_deconstructions") or []
    required_fields = {
        "hook_pattern",
        "proof_pattern",
        "structure_pattern",
        "pacing_pattern",
        "cta_pattern",
    }
    for index, item in enumerate(plan.get("plans") or [], start=1):
        topic_id = str(item.get("topic_id") or "")
        reference_ids = {str(value) for value in item.get("reference_ids") or []}
        matched = [
            row
            for row in rows
            if str(row.get("topic_id") or "") == topic_id
            and str(row.get("reference_id") or "") in reference_ids
        ]
        complete = [
            row for row in matched if all(row.get(field) for field in required_fields)
        ]
        if not complete:
            errors.append(
                f"plans[{index}] topic {topic_id} needs at least one matched reference with "
                "Hook, proof, structure, pacing, and CTA deconstruction"
            )
    return errors


def run(command: list[str], cwd: Path) -> None:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise SystemExit(f"command failed ({' '.join(command)}):\n{detail}")
    if completed.stdout:
        print(completed.stdout.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--run-id", default=f"{date.today().isoformat()}-daily-ops-loop")
    parser.add_argument(
        "--benchmark-run-id",
        help="Use an immutable benchmark deconstruction produced by an earlier run.",
    )
    parser.add_argument("--allow-non-today", action="store_true", help="Allow closing a historical or test plan.")
    args = parser.parse_args()

    root = system_root()
    workspace = args.workspace.expanduser().resolve()
    plan_path = workspace / "work/plans/daily.json"
    schema_path = root / "schemas/daily-content-plan.schema.json"
    signals_path = workspace / "data/topic-research/current/topic-signals.json"
    signals_schema_path = root / "schemas/topic-signals.schema.json"
    assessment_path = workspace / "data/topic-research/current/strategy-assessment.json"
    assessment_schema_path = root / "schemas/strategy-assessment.schema.json"
    plan = load_object(plan_path)
    schema = load_object(schema_path)
    signals = load_object(signals_path)
    signals_schema = load_object(signals_schema_path)
    assessment = load_object(assessment_path)
    assessment_schema = load_object(assessment_schema_path)

    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    schema_errors = sorted(validator.iter_errors(plan), key=lambda error: list(error.path))
    if schema_errors:
        messages = [f"{'.'.join(map(str, error.path)) or '<root>'}: {error.message}" for error in schema_errors]
        write_presentation_status(
            workspace,
            "failed_validation",
            "Daily plan schema failed: " + "; ".join(messages),
            str(plan.get("plan_date") or ""),
        )
        raise SystemExit("daily content plan schema failed:\n- " + "\n- ".join(messages))

    signal_validator = jsonschema.Draft202012Validator(
        signals_schema, format_checker=jsonschema.FormatChecker()
    )
    signal_errors = sorted(signal_validator.iter_errors(signals), key=lambda error: list(error.path))
    if signal_errors:
        messages = [f"{'.'.join(map(str, error.path)) or '<root>'}: {error.message}" for error in signal_errors]
        write_presentation_status(
            workspace,
            "failed_validation",
            "Topic signals schema failed: " + "; ".join(messages),
            str(plan.get("plan_date") or ""),
        )
        raise SystemExit("topic signals schema failed:\n- " + "\n- ".join(messages))

    assessment_validator = jsonschema.Draft202012Validator(
        assessment_schema, format_checker=jsonschema.FormatChecker()
    )
    assessment_schema_errors = sorted(
        assessment_validator.iter_errors(assessment), key=lambda error: list(error.path)
    )
    if assessment_schema_errors:
        messages = [f"{'.'.join(map(str, error.path)) or '<root>'}: {error.message}" for error in assessment_schema_errors]
        write_presentation_status(
            workspace,
            "failed_validation",
            "Strategy assessment schema failed: " + "; ".join(messages),
            str(plan.get("plan_date") or ""),
        )
        raise SystemExit("strategy assessment schema failed:\n- " + "\n- ".join(messages))

    if plan.get("status") == "blocked":
        blockers = (plan.get("research_summary") or {}).get("missing_or_blocked") or []
        reason = "; ".join(str(item) for item in blockers) or "Daily plan is blocked."
        write_presentation_status(
            workspace,
            "blocked",
            reason,
            str((plan.get("source_dates") or {}).get("topic") or plan.get("plan_date") or ""),
        )
        raise SystemExit("a blocked daily plan must not rebuild or publish the dashboard")

    assessment_errors = validate_strategy_assessment(assessment, plan, signals)
    if assessment_errors:
        write_presentation_status(
            workspace,
            "failed_validation",
            "; ".join(assessment_errors),
            str((plan.get("source_dates") or {}).get("topic") or plan.get("plan_date") or ""),
        )
        raise SystemExit("strategy assessment validation failed:\n- " + "\n- ".join(assessment_errors))

    lineage_errors = validate_lineage(plan, workspace, signals, assessment)
    if lineage_errors:
        write_presentation_status(
            workspace,
            "failed_validation",
            "; ".join(lineage_errors),
            str((plan.get("source_dates") or {}).get("topic") or plan.get("plan_date") or ""),
        )
        raise SystemExit("daily content plan lineage failed:\n- " + "\n- ".join(lineage_errors))
    coverage_errors = validate_topic_coverage(signals, plan)
    if coverage_errors:
        write_presentation_status(
            workspace,
            "failed_validation",
            "; ".join(coverage_errors),
            str((plan.get("source_dates") or {}).get("topic") or plan.get("plan_date") or ""),
        )
        raise SystemExit("topic-evidence coverage failed:\n- " + "\n- ".join(coverage_errors))

    benchmark_run_id = args.benchmark_run_id or args.run_id
    deconstruction_errors = validate_benchmark_deconstruction(
        workspace, benchmark_run_id, plan
    )
    if deconstruction_errors:
        write_presentation_status(
            workspace,
            "failed_validation",
            "; ".join(deconstruction_errors),
            str((plan.get("source_dates") or {}).get("reference") or plan.get("plan_date") or ""),
        )
        raise SystemExit(
            "benchmark deconstruction validation failed:\n- "
            + "\n- ".join(deconstruction_errors)
        )

    if not args.allow_non_today and plan.get("plan_date") != date.today().isoformat():
        raise SystemExit(
            f"daily content plan is not for today: {plan.get('plan_date')} (today: {date.today().isoformat()})"
        )

    run([sys.executable, "scripts/validate_workspace.py", str(workspace)], root)
    run([sys.executable, "scripts/update_ops_dashboard.py", str(workspace)], root)
    run(
        [
            sys.executable,
            "scripts/verify_ops_dashboard_html.py",
            str(workspace),
            "--run-id",
            args.run_id,
        ],
        root,
    )

    dashboard_path = workspace / "presentation/ops-dashboard.json"
    html_path = workspace / "presentation/internal-pages/运营大盘.html"
    dashboard = load_object(dashboard_path)
    embedded_plan = ((dashboard.get("meta") or {}).get("sourceStatus") or {}).get("daily_plan") or {}
    if not embedded_plan.get("exists"):
        raise SystemExit("dashboard did not register daily-content-plan.json as a source")

    closure = {
        "workflow_id": "daily-ops-loop",
        "run_id": args.run_id,
        "status": plan.get("status"),
        "closed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "plan_id": plan.get("plan_id"),
        "plan_date": plan.get("plan_date"),
        "strategy_id": plan.get("strategy_id"),
        "strategy_assessment_id": assessment.get("assessment_id"),
        "strategy_decision": assessment.get("decision"),
        "benchmark_run_id": benchmark_run_id,
        "topic_ids": [item.get("topic_id") for item in plan.get("plans") or []],
        "source_dates": plan.get("source_dates"),
        "topic_coverage": signals.get("coverage_status"),
        "checked_topic_sources": [
            item.get("platform") for item in signals.get("checked_sources") or [] if item.get("status") == "checked"
        ],
        "dashboard": str(dashboard_path.relative_to(workspace)),
        "html": str(html_path.relative_to(workspace)),
        "html_verification": "passed",
        "blockers": (plan.get("research_summary") or {}).get("missing_or_blocked") or [],
    }
    output_root = workspace / "runs" / args.run_id / "outputs"
    write_object(output_root / "daily-ops-closure.json", closure)
    run_manifest_path = workspace / "runs" / args.run_id / "run.manifest.json"
    run_manifest = load_object(run_manifest_path) if run_manifest_path.exists() else {}
    run_manifest.update(
        {
            "workflow_id": "daily-ops-loop",
            "run_id": args.run_id,
            "status": plan.get("status"),
            "started_from": "work/plans/daily.json",
            "closed_at": closure["closed_at"],
        }
    )
    existing_outputs = list(run_manifest.get("outputs") or [])
    for output in [
        "outputs/daily-ops-closure.json",
        "outputs/dashboard-html-verification.json",
        "../../work/plans/daily.json",
        "../../presentation/ops-dashboard.json",
        "../../presentation/internal-pages/运营大盘.html",
    ]:
        if output not in existing_outputs:
            existing_outputs.append(output)
    run_manifest["outputs"] = existing_outputs
    write_object(run_manifest_path, run_manifest)
    write_presentation_status(
        workspace,
        "ready",
        "Dashboard data and HTML passed schema, lineage, evidence, coverage, and semantic verification.",
        str((dashboard.get("meta") or {}).get("sourceDate") or plan.get("plan_date") or ""),
    )
    print(f"closed daily ops loop: {args.run_id}")
    print(f"plan status: {plan.get('status')}")
    print(f"rendered: {html_path}")


if __name__ == "__main__":
    main()
