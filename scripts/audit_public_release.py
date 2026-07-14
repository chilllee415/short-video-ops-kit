#!/usr/bin/env python3
"""Offline release audit for the reusable Short Video Ops system."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_WORKFLOW_IDS = {
    "auto-ops-diagnosis",
    "pain-bank-builder",
    "strategy-confirmation",
    "reference-mining",
    "reference-research-plan",
    "reference-transcript-download",
    "reference-strategy-deconstruction",
    "reference-bank-ingest",
    "topic-candidates",
    "topic-candidates-conservative",
    "topic-candidates-experimental",
    "topic-selection-mix",
    "script-planning",
    "copy-optimization-reference-match",
    "feedback-learning",
    "daily-ops-loop",
}
PUBLIC_FORBIDDEN_MARKERS = (
    "/" + "Users/",
    "ayu-" + "personal",
    "ayun-" + "avatar",
    "fit_for_" + "ayu",
    "@" + "ayu",
)


@dataclass
class Result:
    name: str
    ok: bool
    detail: str


def run(command: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)


def schema_results(workspace: Path | None) -> list[Result]:
    results: list[Result] = []
    workflow_schema = json.loads((ROOT / "schemas/workflow-manifest.schema.json").read_text(encoding="utf-8"))
    workflow_ids: set[str] = set()
    errors: list[str] = []
    for path in sorted((ROOT / "manifests").glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            jsonschema.validate(payload, workflow_schema)
            workflow_ids.add(str(payload["workflow_id"]))
        except Exception as exc:  # noqa: BLE001 - audit should aggregate all failures
            errors.append(f"{path.name}: {str(exc).splitlines()[0]}")
    missing = sorted(EXPECTED_WORKFLOW_IDS - workflow_ids)
    extra = sorted(workflow_ids - EXPECTED_WORKFLOW_IDS)
    if missing:
        errors.append(f"missing workflow ids: {', '.join(missing)}")
    if extra:
        errors.append(f"unexpected workflow ids: {', '.join(extra)}")
    results.append(Result("workflow manifests", not errors, "; ".join(errors) or f"{len(workflow_ids)} valid manifests"))

    if workspace is None:
        return results

    artifact_pairs = (
        ("project.manifest.json", "project-manifest.schema.json"),
        ("workspace.index.json", "directory-index.schema.json"),
        ("workspace.policy.json", "workspace-policy.schema.json"),
        ("data/operations/current/account-snapshot.json", "account-snapshot.schema.json"),
        ("data/topic-research/current/pain-bank.json", "pain-bank.schema.json"),
        ("config/strategy/strategy-brief.json", "strategy-brief.schema.json"),
        ("work/topics/conservative/current.json", "topic-lane.schema.json"),
        ("work/topics/experimental/current.json", "topic-lane.schema.json"),
        ("work/topics/selections/daily.json", "topic-selection.schema.json"),
        ("data/topic-research/current/topic-signals.json", "topic-signals.schema.json"),
        ("work/plans/daily.json", "daily-content-plan.schema.json"),
        ("data/feedback/current/learning.json", "feedback-learning.schema.json"),
        ("presentation/status.json", "presentation-status.schema.json"),
    )
    artifact_errors: list[str] = []
    for data_rel, schema_name in artifact_pairs:
        try:
            data_path = workspace / data_rel
            schema_path = ROOT / "schemas" / schema_name
            jsonschema.validate(
                json.loads(data_path.read_text(encoding="utf-8")),
                json.loads(schema_path.read_text(encoding="utf-8")),
            )
        except Exception as exc:  # noqa: BLE001
            artifact_errors.append(f"{data_rel}: {str(exc).splitlines()[0]}")
    results.append(Result("workspace schemas", not artifact_errors, "; ".join(artifact_errors) or f"{len(artifact_pairs)} artifacts valid"))
    return results


def public_boundary_result() -> Result:
    findings: list[str] = []
    text_suffixes = {".md", ".json", ".py", ".sh", ".html", ".txt", ".yml", ".yaml"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix not in text_suffixes:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in PUBLIC_FORBIDDEN_MARKERS:
            if marker in text:
                findings.append(f"{path.relative_to(ROOT)} contains {marker!r}")
    return Result("public/private boundary", not findings, "; ".join(findings[:12]) or "no personal paths or operator identifiers")


def dashboard_contract_result(path: Path) -> Result:
    text = path.read_text(encoding="utf-8")
    markers = (
        '<section id="p2">',
        'id="demandRadar"',
        'id="painFeed"',
        'id="shootFeed"',
        'id="topicGrid"',
        "function renderDemandBoard()",
        "M.demand.sourceMix",
        "var sourceCells = sourceMix.slice(0,5).map",
        "function openDemandDrawer(topic)",
        "function persistDrawerCandidate()",
        "function renderExecutionPlan()",
        "function renderOnboardingGate()",
        'id="workspaceDataLink"',
        'id="strategyConsoleOpen"',
        "function renderStrategyConsole()",
        "function buildStrategyChangePrompt(changeRequest)",
        "复制修改请求，交给 Codex",
        "分析并生成三套内容方向",
        "function analyzeOnboardingAnswers(answers)",
        "function buildPlanningText(answers, proposal)",
        "复制并交给 Codex 确认",
        "if(!rows.length){",
        "暂无作品数据",
        "drawerPrimaryAction.addEventListener('click'",
        "localStorage.setItem(drawerCandidateKey(kind)",
        "e.key === 'Enter' || e.key === ' '",
        "if(e.key === 'Escape') closeDrawer()",
    )
    missing = [marker for marker in markers if marker not in text]
    return Result("P2 dashboard contract", not missing, "; missing: ".join(missing) if missing else "render, keyboard, drawer, persistence contracts present")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def prepare_release_fixture(workspace: Path) -> None:
    strategy_id = "S-2026-W01-example"
    assessment_id = "SA-2026-01-07-example"
    scope_ids = ["scope-example-main"]
    signal_ids = ["DS-example-001"]
    topic_specs = (
        ("T-example-001", "conservative", 1, "Turn scattered feedback into a ranked content plan."),
        ("T-example-002", "conservative", 2, "Turn repeated file checks into an automated report."),
        ("T-example-003", "experimental", 1, "Test a visible run ledger for AI agent work."),
    )

    account_profile_path = workspace / "config/profile/account.profile.json"
    account_profile = json.loads(account_profile_path.read_text(encoding="utf-8"))
    account_profile.update(
        {
            "positioning_status": "confirmed",
            "positioning_provenance": {
                "positioning_source_type": "release_fixture",
                "positioning_source_ref": "templates/project-workspace/config/profile/account.profile.json",
                "confirmation_quote": account_profile["positioning"],
                "confirmed_at": "2026-01-07",
            },
        }
    )
    write_json(account_profile_path, account_profile)

    strategy_path = workspace / "config/strategy/strategy-brief.json"
    strategy = json.loads(strategy_path.read_text(encoding="utf-8"))
    strategy.update(
        {
            "strategy_id": strategy_id,
            "status": "confirmed",
            "confirmed_by_user": True,
            "stage_goal": "Validate result-first demonstrations.",
            "target_audience_ids": ["knowledge-workers"],
            "priority_pain_ids": ["P-example-001"],
            "primary_strategy": "Show a visible result before explaining the repeatable workflow.",
        }
    )
    write_json(strategy_path, strategy)

    assessment_path = workspace / "data/topic-research/current/strategy-assessment.json"
    assessment = json.loads(assessment_path.read_text(encoding="utf-8"))
    assessment.update(
        {
            "assessment_id": assessment_id,
            "run_date": "2026-01-07",
            "generated_at": "2026-01-07T10:00:00+08:00",
            "strategy_id": strategy_id,
        }
    )
    assessment["evidence_window"].update({"start": "2026-01-01", "end": "2026-01-07"})
    write_json(assessment_path, assessment)

    signals = json.loads((ROOT / "examples/topic-signals.template.json").read_text(encoding="utf-8"))
    write_json(workspace / "data/topic-research/current/topic-signals.json", signals)

    candidates: dict[str, list[dict]] = {"conservative": [], "experimental": []}
    for topic_id, lane, rank, title in topic_specs:
        candidate = {
            "topic_id": topic_id,
            "lane": lane,
            "lane_rank": rank,
            "strategy_id": strategy_id,
            "strategy_assessment_id": assessment_id,
            "account_fit": {
                "fit_status": "core" if lane == "conservative" else "adjacent_experiment",
                "persona_match": True,
                "problem_domain_match": True,
                "first_person_proof": True,
                "content_role": "automation_result",
                "fit_reason": "The example can be demonstrated with a first-person visible result.",
                "proof_asset": "Synthetic before/after screen recording.",
            },
            "search_scope_ids": scope_ids,
            "signal_ids": signal_ids,
            "evidence_ids": signal_ids,
            "reference_ids": ["R-example-001"],
            "validation_hypothesis": "A result-first demonstration will improve qualified engagement.",
            "title": title,
            "target_role": "knowledge worker",
            "scene": "repeated knowledge-work task",
            "hook": "Show the completed result first.",
            "visible_result": "A repeated task becomes a verified output.",
            "cta": "Comment with the repeated task you want to automate.",
            "score": {"strategy_fit": 90, "visible_result": 92},
        }
        if lane == "experimental":
            candidate["expires_at"] = "2026-01-14"
        candidates[lane].append(candidate)

    lane_ids = {}
    for lane, quota in (("conservative", 60), ("experimental", 40)):
        lane_id = f"{lane}-20260107-example"
        lane_ids[lane] = lane_id
        lane_payload = {
            "candidate_set_id": lane_id,
            "lane": lane,
            "status": "ready",
            "strategy_id": strategy_id,
            "strategy_assessment_id": assessment_id,
            "generated_at": "2026-01-07T10:30:00+08:00",
            "quota_percent": quota,
            "blockers": [],
            "topics": candidates[lane],
        }
        if lane == "experimental":
            lane_payload["expires_at"] = "2026-01-14"
        write_json(workspace / f"work/topics/{lane}/current.json", lane_payload)

    selected = [
        {"topic_id": "T-example-001", "lane": "conservative", "selection_rank": 1},
        {"topic_id": "T-example-002", "lane": "conservative", "selection_rank": 2},
        {"topic_id": "T-example-003", "lane": "experimental", "selection_rank": 3},
    ]
    write_json(
        workspace / "work/topics/selections/daily.json",
        {
            "selection_id": "selection-20260107-example",
            "selection_date": "2026-01-07",
            "status": "ready",
            "mix_policy": {"candidate_ratio": {"conservative": 60, "experimental": 40}, "daily_ratio": {"conservative": 2, "experimental": 1}},
            "source_candidate_sets": lane_ids,
            "blockers": [],
            "selected": selected,
        },
    )

    plan = json.loads((ROOT / "examples/daily-content-plan.template.json").read_text(encoding="utf-8"))
    base_plan = plan["plans"][0]
    plans = []
    plan_types = (("primary", "Main topic"), ("convert", "Conversion topic"), ("lab", "Experiment topic"))
    for (topic_id, _lane, _rank, title), (plan_type, label) in zip(topic_specs, plan_types):
        item = dict(base_plan)
        item.update({"topic_id": topic_id, "type": plan_type, "label": label, "title": title})
        plans.append(item)
    plan["plans"] = plans
    write_json(workspace / "work/plans/daily.json", plan)

    write_json(
        workspace / "data/benchmarks/current/reference-bank.json",
        {
            "updated_at": "2026-01-07T11:00:00+08:00",
            "references": [
                {
                    "reference_id": "R-example-001",
                    "platform": "example",
                    "title": "Synthetic result-first workflow reference",
                    "source_url": "https://example.com/reference",
                    "observed_at": "2026-01-07",
                    "evidence_role": "supply_content",
                    "strategy_id": strategy_id,
                    "pain_id": "P-example-001",
                }
            ],
        },
    )

    deconstructions = []
    for topic_id, _lane, _rank, _title in topic_specs:
        deconstructions.append(
            {
                "topic_id": topic_id,
                "reference_id": "R-example-001",
                "hook_pattern": "visible result first",
                "proof_pattern": "screen-recorded before and after",
                "structure_pattern": "result, input, process, verification",
                "pacing_pattern": "fast opening, slower proof",
                "cta_pattern": "one task-specific keyword",
            }
        )
    write_json(
        workspace / "runs/release-daily-loop/outputs/reference-strategy-deconstruction.json",
        {"status": "complete", "topic_deconstructions": deconstructions},
    )


def offline_smoke_result() -> Result:
    with tempfile.TemporaryDirectory(prefix="short-video-ops-release-") as temp:
        temp_root = Path(temp)
        workspace = temp_root / "workspace"
        shutil.copytree(ROOT / "templates/project-workspace", workspace)
        source_output = workspace / "runs/release-source/outputs"
        source_output.mkdir(parents=True, exist_ok=True)
        (source_output / "reference-strategy-deconstruction.json").write_text(
            json.dumps(
                {
                    "source_run_id": "release-source",
                    "decompositions": [
                        {"source": {"platform": "example", "id": "sample-1", "title": "Synthetic reference"}}
                    ],
                }
            ),
            encoding="utf-8",
        )
        prepare_release_fixture(workspace)
        commands = (
            [sys.executable, "scripts/validate_workspace.py", str(workspace)],
            [sys.executable, "scripts/generate_reference_research_plan.py", str(workspace), "--run-id", "release-smoke"],
            [sys.executable, "scripts/generate_daily_scene_radar.py", str(workspace), "--date", "2026-01-07", "--output", str(temp_root / "daily.json")],
            [sys.executable, "scripts/generate_topics_from_deconstruction.py", str(workspace), "--reference-strategy-run-id", "release-source", "--run-id", "release-topics"],
            [sys.executable, "scripts/optimize_copy_with_reference_bank.py", str(workspace), "--current-draft", "展示一个可见结果，再解释工作流。", "--run-id", "release-copy-match"],
            [sys.executable, "scripts/finalize_daily_ops_loop.py", str(workspace), "--run-id", "release-daily-loop", "--allow-non-today"],
            [sys.executable, "scripts/build_ops_dashboard_data.py", str(workspace), "--output", str(temp_root / "dashboard.json")],
            [sys.executable, "scripts/render_ops_dashboard.py", str(workspace), "--data", str(temp_root / "dashboard.json"), "--output", str(temp_root / "dashboard.html")],
            [sys.executable, "scripts/generate_weekly_topic_library.py", "--input", "examples/topic-candidates.template.json", "--output", str(temp_root / "weekly.html")],
        )
        failures: list[str] = []
        for command in commands:
            completed = run(command)
            if completed.returncode:
                failures.append(f"{' '.join(command[1:3])}: {(completed.stderr or completed.stdout).strip()}")
        outputs = (
            temp_root / "daily.json",
            temp_root / "dashboard.json",
            temp_root / "dashboard.html",
            temp_root / "weekly.html",
            workspace / "runs/release-topics/outputs/topic-candidates.json",
            workspace / "runs/release-copy-match/outputs/copy-reference-match.json",
            workspace / "runs/release-daily-loop/outputs/daily-ops-closure.json",
        )
        for output in outputs:
            if not output.exists() or output.stat().st_size < 100:
                failures.append(f"missing or empty output: {output.name}")
        dashboard_payload = json.loads((temp_root / "dashboard.json").read_text(encoding="utf-8"))
        onboarding = ((dashboard_payload.get("meta") or {}).get("onboarding") or {})
        if onboarding.get("required") is not False:
            failures.append("confirmed release fixture incorrectly triggers first-run onboarding")
        if onboarding.get("questionnaireVersion") != "2.0":
            failures.append("dashboard does not expose questionnaire version 2.0")
        return Result("offline smoke", not failures, "; ".join(failures) or f"{len(commands)} commands passed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, help="Optional private workspace to validate without modifying it.")
    parser.add_argument("--dashboard-html", type=Path, help="Optional rendered dashboard; defaults to the public template.")
    parser.add_argument("--skip-smoke", action="store_true", help="Skip temporary offline generator tests.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workspace = args.workspace.expanduser().resolve() if args.workspace else None
    dashboard = (
        args.dashboard_html.expanduser().resolve()
        if args.dashboard_html
        else ROOT / "templates/internal-pages/ops-dashboard.template.html"
    )
    results = schema_results(workspace)
    results.extend([public_boundary_result(), dashboard_contract_result(dashboard)])
    if not args.skip_smoke:
        results.append(offline_smoke_result())

    for result in results:
        print(f"{'PASS' if result.ok else 'FAIL'}\t{result.name}\t{result.detail}")
    failed = [result for result in results if not result.ok]
    print(f"summary\t{len(results) - len(failed)} passed\t{len(failed)} failed")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
