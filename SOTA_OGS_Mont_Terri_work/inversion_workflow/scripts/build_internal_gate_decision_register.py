#!/usr/bin/env python3
"""Record local decisions for internal measurement-gate closure items."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


INTERNAL_DECISION_IDS = [
    "nmr_bound_water",
    "nmr_default_promotion",
    "perm_error_model",
    "perm_likelihood_policy",
    "rh_uncertainty",
    "taupe_group_weights",
    "taupe_support",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--closure-request",
        type=Path,
        default=Path("inversion_workflow/measurement_gate_closure_request.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("inversion_workflow/internal_gate_decision_register.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/internal_gate_decision_register_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/internal_gate_decision_register.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files"),
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def finite(value: Any) -> bool:
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(float(value)) else float(value)
    if value is pd.NA or value is None:
        return None
    return value


def compact_request(closure: pd.DataFrame, request_id: str) -> dict[str, Any]:
    row = closure[closure["request_id"].astype(str).eq(request_id)]
    if row.empty:
        return {}
    return row.iloc[0].to_dict()


def build_decisions(repo: Path, closure: pd.DataFrame) -> list[dict[str, Any]]:
    nmr_decision = read_json(repo / "inversion_workflow/nmr_objective_decision_summary.json")
    nmr_activation = read_json(repo / "inversion_workflow/nmr_trend_anomaly_active_objective_summary.json")
    nmr_followup = read_json(
        repo / "inversion_workflow/runs/nmr_trend_anomaly_followup_plan/NMR_TREND_ANOMALY_FOLLOWUP_PLAN.json"
    )
    permeability = read_json(
        repo / "inversion_workflow/processed_observations/permeability_measurement_semantics_summary.json"
    )
    permeability_policy = read_json(repo / "inversion_workflow/permeability_likelihood_policy_audit_summary.json")
    permeability_policy_decision = read_json(
        repo / "inversion_workflow/permeability_likelihood_decision_request_summary.json"
    )
    rh_uncertainty = read_json(repo / "inversion_workflow/processed_observations/rh_boundary_uncertainty_summary.json")
    taupe_series = read_json(repo / "inversion_workflow/taupe_series_weight_sensitivity_summary.json")
    taupe_semantics = read_json(repo / "inversion_workflow/processed_observations/taupe_tdr_semantics_summary.json")
    nmr_best = nmr_activation.get("best_trend_anomaly_active_objective", {})

    decisions = [
        {
            "request_id": "nmr_bound_water",
            "local_decision_status": "local_policy_recorded_executable_mode_available",
            "local_policy": (
                "Use within-label trend/anomaly residuals as the preferred provisional NMR likelihood "
                "for reporting/search scenarios; keep raw absolute-theta NMR as an archival/conditional "
                "objective for the current active files."
            ),
            "objective_or_operator": (
                "(theta_model - weighted_label_mean(theta_model)) - "
                "(theta_NMR_obs - weighted_label_mean(theta_NMR_obs)) within observation_family + measurement_label."
            ),
            "weights_or_uncertainty": "Use existing NMR sigma values for centered residuals; do not fit absolute offsets.",
            "activation_effect": (
                "Executable for future candidate evaluations with --state-objective-mode "
                "nmr_within_label_trend_anomaly; see nmr_default_promotion for the separate default-objective policy."
            ),
            "external_confirmation": "Optional check with BGR/NMR source on bound/interlayer-water interpretation.",
            "key_evidence": (
                f"recommended={nmr_decision.get('recommended_option_id')}; executable_status="
                f"{nmr_activation.get('status')}; best_run={nmr_activation.get('best_trend_anomaly_active_objective', {}).get('run_id')}; "
                f"validation_delta={nmr_activation.get('diagnostic_validation_max_abs_delta')}; "
                f"followup={nmr_followup.get('recommendation')}."
            ),
            "source_artifacts": (
                "inversion_workflow/nmr_objective_decision.md; "
                "inversion_workflow/nmr_trend_anomaly_active_objective.md; "
                "inversion_workflow/runs/nmr_trend_anomaly_followup_plan/NMR_TREND_ANOMALY_FOLLOWUP_PLAN.md"
            ),
        },
        {
            "request_id": "nmr_default_promotion",
            "stream": "nmr_water_content",
            "priority": "high",
            "gate_id": "NMR_DEFAULT_PROMOTION",
            "gate_status": "internal_policy",
            "required_for_active_likelihood": "false",
            "closure_request_text": (
                "Decide whether the implemented within-label trend/anomaly NMR objective should become the "
                "default reporting/search objective."
            ),
            "local_decision_status": "local_policy_recorded_not_promoted_default",
            "local_policy": (
                "Do not promote the within-label trend/anomaly NMR mode to the default objective for the "
                "current report state. Keep it as the preferred provisional NMR likelihood and as an explicit "
                "scenario/sensitivity path until the modelling team accepts changing the objective semantics."
            ),
            "objective_or_operator": (
                "Default objective remains raw absolute-theta NMR plus direct permeability. The promoted-mode "
                "candidate operator is the centered within-label NMR trend/anomaly residual."
            ),
            "weights_or_uncertainty": (
                "No new default weights are assigned. The explicit trend/anomaly mode reuses NMR sigma values "
                "inside centered observation-family/measurement-label groups."
            ),
            "activation_effect": (
                "The historical raw-objective combined files stay authoritative for the active incumbent; "
                "trend/anomaly rankings are reported as provisional scenario evidence and must be invoked by "
                "explicit mode or scenario audit."
            ),
            "external_confirmation": (
                "No external reply is needed for the current not-default policy; re-open if collaborators want "
                "to promote trend/anomaly NMR as the reporting/search default."
            ),
            "key_evidence": (
                f"active_objective_changed={nmr_decision.get('active_objective_changed')}; "
                f"recommended={nmr_decision.get('recommended_option_id')}; best_recommended_run="
                f"{nmr_decision.get('best_recommended_run')}; executable_best={nmr_best.get('run_id')}; "
                f"raw_incumbent_rank_under_trend={nmr_activation.get('raw_incumbent_rank_under_trend_anomaly')}; "
                f"trend_winner_raw_rank={nmr_activation.get('trend_anomaly_winner_raw_rank')}; "
                f"followup={nmr_followup.get('recommendation')}; median_state_beating_candidates="
                f"{nmr_followup.get('unevaluated_candidates_beating_incumbent_under_median_state')}."
            ),
            "source_artifacts": (
                "inversion_workflow/nmr_objective_decision.md; "
                "inversion_workflow/nmr_trend_anomaly_active_objective.md; "
                "inversion_workflow/runs/nmr_trend_anomaly_followup_plan/NMR_TREND_ANOMALY_FOLLOWUP_PLAN.md; "
                "inversion_workflow/conditional_field_selection_scenarios.md"
            ),
        },
        {
            "request_id": "perm_error_model",
            "local_decision_status": "local_policy_recorded_current_objective_approved",
            "local_policy": (
                "Approve the current first-pass gas-pulse residual as log10 intrinsic permeability, "
                "with duplicate-aware interval weights and sigma=0.5 log10 units. Keep the gas/slip/"
                "liquid-equivalent caveat explicit."
            ),
            "objective_or_operator": (
                "residual = log10(e^T K e interval/support response) - log10(k_obs); "
                "K remains the intrinsic permeability tensor field."
            ),
            "weights_or_uncertainty": (
                "sigma=0.5 log10 units; duplicate observations with same campaign, segment, depth, "
                "and value share total weight 1."
            ),
            "activation_effect": (
                "Direct permeability remains an active objective stream; do not describe the values as "
                "water hydraulic conductivity, relative permeability, or cell-wise tensor components."
            ),
            "external_confirmation": "Optional BGR check on gas/slip correction and liquid-equivalent wording.",
            "key_evidence": (
                f"target_rows={permeability.get('target_rows')}; active_rows="
                f"{permeability.get('usable_current_rows') or permeability.get('target_builder_summary', {}).get('usable_for_current_ogs_fit')}; "
                "permeability semantics audit records scalar interval intrinsic-permeability interpretation."
            ),
            "source_artifacts": (
                "inversion_workflow/processed_observations/permeability_measurement_semantics.md; "
                "inversion_workflow/scripts/evaluate_permeability_targets.py"
            ),
        },
        {
            "request_id": "perm_likelihood_policy",
            "local_decision_status": "local_policy_recorded_not_promoted_default",
            "local_policy": (
                "Keep the current duplicate-weighted rowwise Gaussian direct-permeability objective as the "
                "recorded default for the current report state. Treat robust row likelihoods, support-cell "
                "aggregation, and configured-scalar-range outlier handling as explicit scenario/decision "
                "options until the modelling team changes the objective semantics."
            ),
            "objective_or_operator": (
                "Default remains residual = log10(e^T K e interval/support response) - log10(k_obs) with "
                "duplicate-aware row weights. Candidate alternatives are robust row residuals, support-cell "
                "mean/median aggregation, configured-scalar-range outlier gating, or a new parameterization gate."
            ),
            "weights_or_uncertainty": (
                "Default sigma remains 0.5 log10 units. Non-default policies must state their kernel/grouping, "
                "weights, outlier disposition, and reranking rule before they are used for field selection."
            ),
            "activation_effect": (
                "No default objective change. More routine OGS runs under the current smooth/local-basis family "
                "should wait until either this rowwise policy is explicitly accepted with a new parameterization "
                "or a robust/aggregated likelihood scenario is approved and reranked."
            ),
            "external_confirmation": (
                "Optional BGR/Gesa confirmation if the policy depends on gas-pulse interpretation, scalar interval "
                "support, or the treatment of configured-scalar-range outliers."
            ),
            "key_evidence": (
                f"policy_status={permeability_policy.get('status')}; current_gaussian_objective="
                f"{permeability_policy.get('current_gaussian_objective')}; support_mean_objective="
                f"{permeability_policy.get('support_mean_unit_objective')}; support_median_objective="
                f"{permeability_policy.get('support_median_unit_objective')}; conflict_groups="
                f"{permeability_policy.get('support_groups_with_observed_range_ge_1_log10')}; "
                f"top10_loss_share={permeability_policy.get('row_loss_top_10_share')}; "
                f"decision_request={permeability_policy_decision.get('status')}."
            ),
            "source_artifacts": (
                "inversion_workflow/permeability_likelihood_policy_audit.md; "
                "inversion_workflow/permeability_likelihood_decision_request.md; "
                "inversion_workflow/permeability_residual_conflict_audit.md"
            ),
        },
        {
            "request_id": "rh_uncertainty",
            "local_decision_status": "local_policy_recorded_external_provenance_still_required",
            "local_policy": (
                "Keep RH/suction as boundary-provenance and uncertainty-envelope evidence only. Do not "
                "replace the active OGS XML boundary curve, activate a suction/retention residual, or "
                "release retention parameters until active-curve provenance is confirmed."
            ),
            "objective_or_operator": (
                "Local RH-derived curves remain candidate boundary scenarios and diagnostics, not hard residuals."
            ),
            "weights_or_uncertainty": (
                "Use the RH5/RH6 median/mean policy envelope to quantify uncertainty; no likelihood sigma assigned."
            ),
            "activation_effect": (
                "RH remains boundary-audit-only. Candidate curves may be run as future forcing scenarios only "
                "after provenance/extension policy is accepted."
            ),
            "external_confirmation": "BGR/Gesa provenance for active curve generation, constants, time axis, and sensor screening required.",
            "key_evidence": (
                f"candidate_curves={rh_uncertainty.get('candidate_count')}; envelope_dates="
                f"{rh_uncertainty.get('envelope_date_count')}; active_outside_envelope="
                f"{rh_uncertainty.get('active_curve_outside_envelope_count')}; "
                f"overlap_p50_range={rh_uncertainty.get('overlap', {}).get('pressure_range_mpa', {}).get('p50')} MPa."
            ),
            "source_artifacts": (
                "inversion_workflow/processed_observations/rh_boundary_uncertainty.md; "
                "inversion_workflow/processed_observations/rh_boundary_provenance_request.md"
            ),
        },
        {
            "request_id": "taupe_group_weights",
            "local_decision_status": "local_policy_recorded_diagnostic_only",
            "local_policy": (
                "For diagnostics, report aggregate-row and grouped-weight sensitivity side by side; if Taupe "
                "is later activated as a trend likelihood, use grouped weights so A3/A4 sensors and EDZ bands "
                "are not over-weighted by row count."
            ),
            "objective_or_operator": (
                "Trend/anomaly residual over mapped Taupe/TDR bands; absolute water-content residual remains inactive."
            ),
            "weights_or_uncertainty": (
                "Preferred future hard-likelihood baseline: equal sensor or equal series/EDZ-band groups with "
                "row weights normalized within group; keep aggregate-row weighting as sensitivity."
            ),
            "activation_effect": (
                "Does not activate Taupe until unit/calibration and uncertainty gates close; gives the future "
                "weighting rule so the internal grouping question is no longer implicit."
            ),
            "external_confirmation": "Taupe/TDR provider confirmation of unit calibration and uncertainty still required.",
            "key_evidence": (
                f"runs={taupe_series.get('run_count')}; compared_series={taupe_series.get('compared_series_count')}; "
                f"distinct_winners={taupe_series.get('series_best_run_distinct_count')}; "
                f"best_mean_rank_run={taupe_series.get('best_mean_weighting_rank', {}).get('run_id')}."
            ),
            "source_artifacts": (
                "inversion_workflow/taupe_series_weight_sensitivity.md; "
                "inversion_workflow/processed_observations/taupe_tdr_observation_operator.md"
            ),
        },
        {
            "request_id": "taupe_support",
            "local_decision_status": "local_policy_recorded_support_mask_fixed_for_current_mesh",
            "local_policy": (
                "Limit current Taupe/TDR model comparisons to A3/A4 mapped Niche-4 support. Keep A7/A8 and "
                "outside-support rows as documented exclusions/validation context until a larger mesh or "
                "approved support mapping exists."
            ),
            "objective_or_operator": (
                "Band-average OGS theta trend over mapped A3/A4 intervals only; no fallback projection for A7/A8."
            ),
            "weights_or_uncertainty": (
                "A3/A4 groups only for current diagnostics; excluded support must not contribute residual weight."
            ),
            "activation_effect": (
                "Taupe support decision is explicit for the current mesh, but hard-residual activation still "
                "depends on unit/calibration and uncertainty confirmation."
            ),
            "external_confirmation": "Provider confirmation useful for A7/A8 geometry/support if those sensors should be included.",
            "key_evidence": (
                f"mapped_trend_rows={taupe_semantics.get('mapped_trend_rows')}; "
                f"outside_mesh_rows={taupe_semantics.get('outside_current_mesh_rows')}; "
                f"trend_ready_series={taupe_semantics.get('trend_ready_series')}; "
                "series-weight audit compared A3/A4 and left A7/A8 outside current mesh support."
            ),
            "source_artifacts": (
                "inversion_workflow/processed_observations/taupe_tdr_semantics.md; "
                "inversion_workflow/taupe_series_weight_sensitivity.md"
            ),
        },
    ]

    closure_lookup = {request_id: compact_request(closure, request_id) for request_id in INTERNAL_DECISION_IDS}
    for decision in decisions:
        request = closure_lookup.get(decision["request_id"], {})
        decision["stream"] = request.get("stream", "") or decision.get("stream", "")
        decision["priority"] = request.get("priority", "") or decision.get("priority", "")
        decision["gate_id"] = request.get("gate_id", "") or decision.get("gate_id", "")
        decision["gate_status"] = request.get("gate_status", "") or decision.get("gate_status", "")
        decision["required_for_active_likelihood"] = request.get("required_for_active_likelihood", "") or decision.get(
            "required_for_active_likelihood", ""
        )
        decision["closure_request_text"] = request.get("exact_request", "") or decision.get("closure_request_text", "")
    return decisions


def write_markdown(path: Path, rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    lines = [
        "# Internal Gate Decision Register",
        "",
        "This register records local modelling decisions for the internal or internal-with-optional-confirmation items in the measurement gate-closure package.",
        "It does not close external source requests for ERT, RH provenance, Taupe unit calibration, or other-HM numeric exports.",
        "",
        "## Summary",
        "",
        f"- Status: `{summary['status']}`",
        f"- Internal decisions represented: {summary['decision_count']}",
        f"- Local policies recorded: {summary['local_policy_recorded_count']}",
        f"- Active/ready internal policies: {summary['active_or_ready_internal_policy_count']}",
        f"- Diagnostic or boundary-only policies: {summary['diagnostic_or_boundary_policy_count']}",
        f"- Diagnostic/boundary policies still gated before hard activation: {summary['still_external_or_activation_gated_count']}",
        f"- Rows with optional confirmation caveats: {summary['remaining_confirmation_or_promotion_caveat_count']}",
        "",
        "## Decision Table",
        "",
        "| Request | Stream | Local status | Activation effect | External confirmation |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['request_id']}`",
                    f"`{row['stream']}`",
                    f"`{row['local_decision_status']}`",
                    str(row["activation_effect"]).replace("|", "\\|"),
                    str(row["external_confirmation"]).replace("|", "\\|"),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Details", ""])
    for row in rows:
        lines.extend(
            [
                f"### `{row['request_id']}`",
                "",
                f"- Gate: `{row['gate_id']}` (`{row['gate_status']}`)",
                f"- Local policy: {row['local_policy']}",
                f"- Objective/operator: {row['objective_or_operator']}",
                f"- Weights/uncertainty: {row['weights_or_uncertainty']}",
                f"- Activation effect: {row['activation_effect']}",
                f"- External confirmation: {row['external_confirmation']}",
                f"- Key evidence: {row['key_evidence']}",
                f"- Source artifacts: {row['source_artifacts']}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def copy_outputs(catalogue_dir: Path, paths: list[Path]) -> list[dict[str, str]]:
    catalogue_dir.mkdir(parents=True, exist_ok=True)
    copies = []
    for source in paths:
        target = catalogue_dir / source.name
        if source.exists():
            shutil.copy2(source, target)
        copies.append({"source": str(source), "catalogue_copy": str(target)})
    return copies


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[2]
    output = (repo / args.output if not args.output.is_absolute() else args.output).resolve()
    summary_output = (repo / args.summary_output if not args.summary_output.is_absolute() else args.summary_output).resolve()
    markdown_output = (repo / args.markdown_output if not args.markdown_output.is_absolute() else args.markdown_output).resolve()
    closure_path = (repo / args.closure_request if not args.closure_request.is_absolute() else args.closure_request).resolve()
    catalogue_dir = (repo / args.catalogue_dir if not args.catalogue_dir.is_absolute() else args.catalogue_dir).resolve()

    closure = pd.read_csv(closure_path)
    rows = build_decisions(repo, closure)
    frame = pd.DataFrame(rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)

    status_counts = frame["local_decision_status"].value_counts().to_dict()
    diagnostic_or_boundary_statuses = {
        "local_policy_recorded_external_provenance_still_required",
        "local_policy_recorded_diagnostic_only",
        "local_policy_recorded_support_mask_fixed_for_current_mesh",
    }
    still_gated = frame[frame["local_decision_status"].astype(str).isin(diagnostic_or_boundary_statuses)]
    remaining_caveats = frame[
        frame["activation_effect"].astype(str).str.contains("still|until|default|remains|depends", case=False, regex=True)
        & ~frame["local_decision_status"].astype(str).eq("local_policy_recorded_not_promoted_default")
    ]
    summary = {
        "status": "internal_gate_decision_register_generated",
        "decision_count": int(frame.shape[0]),
        "local_policy_recorded_count": int(frame["local_decision_status"].astype(str).str.startswith("local_policy").sum()),
        "active_or_ready_internal_policy_count": int(
            frame["local_decision_status"]
            .astype(str)
            .isin(
                [
                    "local_policy_recorded_executable_mode_available",
                    "local_policy_recorded_current_objective_approved",
                ]
            )
            .sum()
        ),
        "diagnostic_or_boundary_policy_count": int(
            frame["local_decision_status"]
            .astype(str)
            .isin(
                [
                    "local_policy_recorded_external_provenance_still_required",
                    "local_policy_recorded_diagnostic_only",
                    "local_policy_recorded_support_mask_fixed_for_current_mesh",
                ]
            )
            .sum()
        ),
        "not_promoted_default_policy_count": int(
            frame["local_decision_status"].astype(str).eq("local_policy_recorded_not_promoted_default").sum()
        ),
        "nmr_default_promotion_status": (
            frame.loc[
                frame["request_id"].astype(str).eq("nmr_default_promotion"), "local_decision_status"
            ].iloc[0]
            if frame["request_id"].astype(str).eq("nmr_default_promotion").any()
            else None
        ),
        "permeability_likelihood_policy_status": (
            frame.loc[
                frame["request_id"].astype(str).eq("perm_likelihood_policy"), "local_decision_status"
            ].iloc[0]
            if frame["request_id"].astype(str).eq("perm_likelihood_policy").any()
            else None
        ),
        "status_counts": {str(key): int(value) for key, value in status_counts.items()},
        "still_external_or_activation_gated_count": int(still_gated.shape[0]),
        "remaining_confirmation_or_promotion_caveat_count": int(remaining_caveats.shape[0]),
        "required_for_active_likelihood_decision_count": int(
            frame["required_for_active_likelihood"].astype(str).str.lower().eq("true").sum()
        ),
        "generated_files": [str(output.relative_to(repo)), str(summary_output.relative_to(repo)), str(markdown_output.relative_to(repo))],
    }
    write_markdown(markdown_output, rows, summary)
    summary["catalogue_copies"] = copy_outputs(catalogue_dir, [output, summary_output, markdown_output])
    summary_output.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    copy_outputs(catalogue_dir, [summary_output])
    print(json.dumps(json_ready(summary), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
