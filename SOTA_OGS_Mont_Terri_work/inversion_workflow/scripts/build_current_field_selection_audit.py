#!/usr/bin/env python3
"""Audit whether the packaged current permeability field is selectable as final."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--current-field-summary",
        type=Path,
        default=Path("inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD_SUMMARY.json"),
    )
    parser.add_argument(
        "--cross-stream-summary",
        type=Path,
        default=Path("inversion_workflow/cross_stream_candidate_scorecard_summary.json"),
    )
    parser.add_argument(
        "--nmr-trend-summary",
        type=Path,
        default=Path("inversion_workflow/nmr_trend_anomaly_active_objective_summary.json"),
    )
    parser.add_argument(
        "--stream-gate-summary",
        type=Path,
        default=Path("inversion_workflow/measurement_stream_activation_gate_audit_summary.json"),
    )
    parser.add_argument(
        "--external-intake-summary",
        type=Path,
        default=Path("inversion_workflow/external_gate_response_intake_summary.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/current_field_selection_audit.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/current_field_selection_audit_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/current_field_selection_audit.md"),
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def add_row(
    rows: list[dict[str, Any]],
    *,
    criterion_id: str,
    criterion: str,
    status: str,
    evidence: str,
    implication: str,
    source_artifacts: str,
) -> None:
    rows.append(
        {
            "criterion_id": criterion_id,
            "criterion": criterion,
            "status": status,
            "evidence": evidence,
            "implication": implication,
            "source_artifacts": source_artifacts,
        }
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["criterion_id", "criterion", "status", "evidence", "implication", "source_artifacts"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_markdown(path: Path, rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Current Field Selection Audit",
        "",
        "This audit is the selection record for the packaged permeability field. It",
        "separates acceptance as the current active-objective incumbent from rejection",
        "as a final all-measurement field.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Packaged run: `{summary['run_id']}`",
        f"- Active-objective decision: `{summary['active_objective_decision']}`",
        f"- Final all-measurement decision: `{summary['final_all_measurement_decision']}`",
        f"- Criteria passed: {summary['status_counts'].get('pass', 0)}",
        f"- Criteria with caveats: {summary['status_counts'].get('pass_with_caveat', 0)}",
        f"- Criteria blocked/gated: {summary['status_counts'].get('blocked_or_gated', 0)}",
        f"- Criteria failing final promotion: {summary['status_counts'].get('fails_final_promotion', 0)}",
        "",
        "## Decision Rationale",
        "",
    ]
    for reason in summary["decision_rationale"]:
        lines.append(f"- {reason}")
    lines.extend(
        [
            "",
            "## Criteria",
            "",
            "| Criterion | Status | Evidence | Implication |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| `{row['criterion_id']}` {row['criterion']} | `{row['status']}` | "
            f"{row['evidence']} | {row['implication']} |"
        )
    lines.extend(
        [
            "",
            "## Source Artifacts",
            "",
        ]
    )
    for artifact in summary["source_artifacts"]:
        lines.append(f"- `{artifact}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row["status"])
        counts[status] = counts.get(status, 0) + 1
    return counts


def build_audit(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    field = read_json(args.current_field_summary)
    scorecard = read_json(args.cross_stream_summary)
    nmr_trend = read_json(args.nmr_trend_summary)
    gate = read_json(args.stream_gate_summary)
    intake = read_json(args.external_intake_summary)

    run_id = str(field.get("run_id", ""))
    active = scorecard.get("active_incumbent_cross_stream", {})
    winners = scorecard.get("stream_winners", {})
    best_mean = winners.get("mean_rank_all_streams", {})
    nmr_winner = nmr_trend.get("best_trend_anomaly_active_objective", {})
    raw_incumbent_under_trend = nmr_trend.get("best_raw_combined_objective", {})
    field_geometry = field.get("field", {})
    combined = field.get("combined_objective", {})
    permeability = field.get("permeability_fit", {})
    state = field.get("state_observation", {})
    release = field.get("release_gate", {})
    interpretation = field.get("interpretation", {})

    field_ready = (
        field.get("status") == "current_permeability_field_package_generated"
        and Path(str(field.get("packaged_mesh", ""))).exists()
        and int(field_geometry.get("triangle6_cell_count", 0) or 0) > 0
        and int(field_geometry.get("positive_definite_cell_count", 0) or 0)
        == int(field_geometry.get("triangle6_cell_count", 0) or 0)
        and int(field_geometry.get("non_positive_definite_cell_count", 1)) == 0
    )
    release_ok = release.get("status") == "pass" and field.get("ogs_execution", {}).get("returncode") == 0
    active_rank = active.get("active_objective_rank")
    active_worst_rank = active.get("worst_rank_all_streams")
    active_mean_rank = active.get("mean_rank_all_streams")
    active_top10 = active.get("top10_stream_count")
    best_mean_run = best_mean.get("run_id")
    nmr_winner_run = nmr_winner.get("run_id")

    rows: list[dict[str, Any]] = []
    add_row(
        rows,
        criterion_id="C01_field_package_integrity",
        criterion="Packaged field is complete, positive-definite, and traceable to a release-gated OGS run.",
        status="pass" if field_ready and release_ok else "fails_final_promotion",
        evidence=(
            f"package status={field.get('status')}; mesh={field.get('packaged_mesh')}; "
            f"triangle6 cells={field_geometry.get('triangle6_cell_count')}; "
            f"positive-definite cells={field_geometry.get('positive_definite_cell_count')}; "
            f"non-positive-definite cells={field_geometry.get('non_positive_definite_cell_count')}; "
            f"release gate={release.get('status')}; OGS returncode={field.get('ogs_execution', {}).get('returncode')}."
        ),
        implication="The field is suitable for inspection, reruns, and active-objective comparison.",
        source_artifacts=str(args.current_field_summary),
    )
    add_row(
        rows,
        criterion_id="C02_active_objective_incumbent",
        criterion="Field is the current winner under the active direct-permeability plus raw-NMR objective.",
        status="pass" if active_rank == 1.0 and active.get("run_id") == run_id else "fails_final_promotion",
        evidence=(
            f"active rank={active_rank}; active objective={active.get('current_combined_objective')}; "
            f"direct objective={permeability.get('objective_value')}; raw NMR/state objective="
            f"{state.get('objective_value')}; active components={combined.get('active_component_count')}."
        ),
        implication="Accept as the active-objective incumbent, with the active objective's known caveats.",
        source_artifacts=f"{args.current_field_summary}; {args.cross_stream_summary}",
    )
    add_row(
        rows,
        criterion_id="C03_direct_permeability_fit",
        criterion="Direct gas-pulse permeability rows are represented as tensor-direction interval targets.",
        status="pass_with_caveat",
        evidence=(
            f"usable direct rows={permeability.get('used_in_objective_rows')}; "
            f"weighted RMSE log10={permeability.get('weighted_rmse_log10')}; "
            f"field={permeability.get('field_name')}; log10 sigma={permeability.get('log10_sigma')}."
        ),
        implication="This supports the field as a direct pulse-test fit, not as a liquid effective-permeability proof.",
        source_artifacts=str(args.current_field_summary),
    )
    add_row(
        rows,
        criterion_id="C04_raw_nmr_active_fit",
        criterion="Raw NMR theta rows are sampled from OGS outputs and active in the current objective.",
        status="pass_with_caveat",
        evidence=(
            f"NMR/state rows used={state.get('used_in_objective_rows')}; "
            f"raw normalized RMSE={state.get('rmse_normalized_residual')}; "
            f"state sample rows={state.get('state_sample_rows')}; raw active field rank="
            f"{active.get('active_objective_rank')}."
        ),
        implication="The raw-theta state fit is usable but remains conditional because bound/interlayer water can change the preferred residual.",
        source_artifacts=str(args.current_field_summary),
    )
    add_row(
        rows,
        criterion_id="C05_nmr_trend_anomaly_robustness",
        criterion="Field remains acceptable if the preferred provisional NMR trend/anomaly residual is promoted.",
        status="fails_final_promotion" if nmr_winner_run and nmr_winner_run != run_id else "pass_with_caveat",
        evidence=(
            f"trend/anomaly winner={nmr_winner_run}; current field trend/anomaly rank="
            f"{raw_incumbent_under_trend.get('diagnostic_trend_anomaly_combined_rank')}; "
            f"trend/anomaly winner raw-objective rank={nmr_trend.get('trend_anomaly_winner_raw_rank')}; "
            f"promotion gate={nmr_trend.get('activation_gate')}."
        ),
        implication="Do not call the packaged field final if NMR is promoted to the offset-robust residual without reranking field selection.",
        source_artifacts=str(args.nmr_trend_summary),
    )
    add_row(
        rows,
        criterion_id="C06_ert_diagnostic_consistency",
        criterion="Field is compatible with the provisional ERT log-resistivity diagnostic.",
        status="blocked_or_gated",
        evidence=(
            f"active-incumbent ERT rank={active.get('ert_mae_rank')}; ERT MAE log10="
            f"{active.get('ert_residual_mae_log10')}; ERT winner={winners.get('ert', {}).get('run_id')}; "
            f"required gate failures={gate.get('required_gate_fail_count')}."
        ),
        implication="ERT can screen the field, but cannot select a final field until transform/support/covariance gates are accepted.",
        source_artifacts=f"{args.cross_stream_summary}; {args.stream_gate_summary}",
    )
    add_row(
        rows,
        criterion_id="C07_taupe_diagnostic_consistency",
        criterion="Field is compatible with the provisional Taupe/TDR trend diagnostic.",
        status="blocked_or_gated",
        evidence=(
            f"active-incumbent Taupe rank={active.get('taupe_mae_rank')}; Taupe MAE="
            f"{active.get('taupe_trend_mae')}; Taupe winner={winners.get('taupe', {}).get('run_id')}; "
            f"required gate failures={gate.get('required_gate_fail_count')}."
        ),
        implication="Taupe/TDR cannot select a final field until workbook unit/calibration and grouped uncertainty are accepted.",
        source_artifacts=f"{args.cross_stream_summary}; {args.stream_gate_summary}",
    )
    add_row(
        rows,
        criterion_id="C08_cross_stream_consensus",
        criterion="Same field is supported by active objective plus NMR, ERT, and Taupe diagnostics.",
        status="fails_final_promotion" if best_mean_run != run_id or active_worst_rank != 1.0 else "pass",
        evidence=(
            f"best mean-rank run={best_mean_run}; active field mean rank={active_mean_rank}; "
            f"active field worst rank={active_worst_rank}; active field top-10 stream count={active_top10}; "
            f"top-10-all-stream candidates={scorecard.get('top10_all_stream_candidates', 0)}."
        ),
        implication="The packaged field is not the cross-stream consensus field under the current diagnostic scorecard.",
        source_artifacts=str(args.cross_stream_summary),
    )
    add_row(
        rows,
        criterion_id="C09_rh_other_hm_gate",
        criterion="RH and other-HM information can be used as hard residuals in final field selection.",
        status="blocked_or_gated",
        evidence=(
            f"promotion decisions={gate.get('promotion_decision_counts')}; "
            f"diagnostic/boundary-only streams={gate.get('diagnostic_or_boundary_only_count')}; "
            f"not-ready hard-residual streams={gate.get('not_ready_for_hard_residual_count')}."
        ),
        implication="RH remains boundary/provenance evidence and other-HM remains outside hard residual weighting.",
        source_artifacts=str(args.stream_gate_summary),
    )
    add_row(
        rows,
        criterion_id="C10_external_gate_closure",
        criterion="External calibration/provenance responses needed for final all-measurement selection are closed.",
        status="blocked_or_gated",
        evidence=(
            f"external intake status={intake.get('status')}; tracked requests="
            f"{intake.get('tracked_request_count')}; missing responses={intake.get('missing_response_count')}; "
            f"main remaining gates={interpretation.get('main_remaining_gates')}."
        ),
        implication="Final selection must wait for response filing or an explicit decision to exclude those gated streams.",
        source_artifacts=str(args.external_intake_summary),
    )

    counts = status_counts(rows)
    final_blocked = counts.get("fails_final_promotion", 0) > 0 or counts.get("blocked_or_gated", 0) > 0
    summary = {
        "status": "current_field_selection_audit_generated",
        "run_id": run_id,
        "active_objective_decision": (
            "accept_as_current_active_objective_incumbent" if active_rank == 1.0 and field_ready else "do_not_accept"
        ),
        "final_all_measurement_decision": (
            "do_not_promote_to_final_all_measurement_field" if final_blocked else "promotable"
        ),
        "status_counts": counts,
        "decision_rationale": [
            "The packaged field is complete, release-gated, and first under the current active objective.",
            "The active objective still contains only direct permeability and raw NMR state residuals.",
            "The preferred provisional NMR trend/anomaly residual selects a different run.",
            "The cross-stream scorecard's best mean-rank run differs from the packaged field.",
            "ERT, Taupe/TDR, RH, and other-HM streams remain gated by support, calibration, provenance, or numeric-export gaps.",
        ],
        "key_numbers": {
            "active_objective_rank": active_rank,
            "active_objective_value": active.get("current_combined_objective"),
            "direct_permeability_weighted_rmse_log10": permeability.get("weighted_rmse_log10"),
            "raw_nmr_rmse_normalized_residual": state.get("rmse_normalized_residual"),
            "nmr_trend_anomaly_rank": raw_incumbent_under_trend.get("diagnostic_trend_anomaly_combined_rank"),
            "nmr_trend_anomaly_winner": nmr_winner_run,
            "ert_rank": active.get("ert_mae_rank"),
            "taupe_rank": active.get("taupe_mae_rank"),
            "mean_rank_all_streams": active_mean_rank,
            "worst_rank_all_streams": active_worst_rank,
            "best_mean_rank_run": best_mean_run,
            "required_gate_fail_count": gate.get("required_gate_fail_count"),
            "missing_external_responses": intake.get("missing_response_count"),
        },
        "source_artifacts": [
            str(args.current_field_summary),
            str(args.cross_stream_summary),
            str(args.nmr_trend_summary),
            str(args.stream_gate_summary),
            str(args.external_intake_summary),
        ],
    }
    return rows, summary


def main() -> None:
    args = parse_args()
    rows, summary = build_audit(args)
    write_csv(args.output_csv, rows)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_markdown(args.output_md, rows, summary)


if __name__ == "__main__":
    main()
