#!/usr/bin/env python3
"""Build a strict activation-gate audit for all measurement streams.

Coverage and likelihood artifacts describe how measurements can enter the frozen
OGS workflow.  This audit turns those descriptions into explicit pass/fail gate
checks so the report can distinguish active residuals, diagnostics, support layers,
and streams that need external provenance or numeric exports before promotion.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


STATUS_ORDER = {
    "pass": 0,
    "warn": 1,
    "fail": 2,
    "not_applicable": 3,
    "missing_evidence": 4,
}

DECISION_ORDER = {
    "active": 0,
    "active_with_tracked_caveats": 1,
    "support_layer_ready": 2,
    "diagnostic_only": 3,
    "boundary_audit_only": 4,
    "not_ready_for_hard_residual": 5,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/stream_activation_gate_audit"),
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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
        number = float(value)
        return None if not np.isfinite(number) else number
    if value is None or value is pd.NA:
        return None
    return value


def display_path(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    return int(pd.read_csv(path, usecols=[0]).shape[0])


def add_check(
    checks: list[dict[str, Any]],
    *,
    stream: str,
    gate_id: str,
    gate_label: str,
    status: str,
    required_for_active_likelihood: bool,
    evidence: str,
    blocker_or_caveat: str,
    artifacts: str,
) -> None:
    checks.append(
        {
            "stream": stream,
            "gate_id": gate_id,
            "gate_label": gate_label,
            "status": status,
            "required_for_active_likelihood": bool(required_for_active_likelihood),
            "evidence": evidence,
            "blocker_or_caveat": blocker_or_caveat,
            "authoritative_artifacts": artifacts,
        }
    )


def decision_for(checks: list[dict[str, Any]], stream: str, fallback: str) -> str:
    rows = [row for row in checks if row["stream"] == stream]
    required = [row for row in rows if row["required_for_active_likelihood"]]
    if any(row["status"] in {"fail", "missing_evidence"} for row in required):
        return fallback
    if any(row["status"] == "warn" for row in required):
        return "active_with_tracked_caveats"
    return "active"


def summarize_streams(checks: list[dict[str, Any]], decisions: dict[str, dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for stream, meta in decisions.items():
        stream_checks = [row for row in checks if row["stream"] == stream]
        required = [row for row in stream_checks if row["required_for_active_likelihood"]]
        counts = {status: 0 for status in STATUS_ORDER}
        for row in stream_checks:
            counts[row["status"]] = counts.get(row["status"], 0) + 1
        blockers = [
            row["blocker_or_caveat"]
            for row in required
            if row["status"] in {"fail", "missing_evidence"} and row["blocker_or_caveat"]
        ]
        warnings = [
            row["blocker_or_caveat"]
            for row in required
            if row["status"] == "warn" and row["blocker_or_caveat"]
        ]
        rows.append(
            {
                "stream": stream,
                "promotion_decision": meta["promotion_decision"],
                "current_model_role": meta["current_model_role"],
                "active_objective_rows": int(meta.get("active_objective_rows", 0) or 0),
                "gate_count": len(stream_checks),
                "required_gate_count": len(required),
                "pass_count": counts.get("pass", 0),
                "warn_count": counts.get("warn", 0),
                "fail_count": counts.get("fail", 0),
                "missing_evidence_count": counts.get("missing_evidence", 0),
                "hard_blockers": "; ".join(blockers),
                "tracked_caveats": "; ".join(warnings),
                "next_action": meta["next_action"],
                "primary_artifacts": meta["primary_artifacts"],
            }
        )
    frame = pd.DataFrame(rows)
    frame["decision_rank"] = frame["promotion_decision"].map(lambda value: DECISION_ORDER.get(str(value), 99))
    return frame.sort_values(["decision_rank", "stream"]).drop(columns=["decision_rank"]).reset_index(drop=True)


def write_markdown(path: Path, stream_frame: pd.DataFrame, checks_frame: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# Measurement Stream Activation Gate Audit",
        "",
        "This audit is stricter than the measurement inventory. It records whether each",
        "stream is active, conditional, diagnostic-only, or blocked from hard residual",
        "weights by missing support, calibration, uncertainty, provenance, or numeric",
        "source data.",
        "",
        "## Summary",
        "",
        f"- Streams audited: {summary['stream_count']}",
        f"- Streams active now: {summary['active_stream_count']}",
        f"- Active objective rows: {summary['active_objective_rows']}",
        f"- Streams not ready for hard residuals: {summary['not_ready_for_hard_residual_count']}",
        f"- Diagnostic/boundary-only streams: {summary['diagnostic_or_boundary_only_count']}",
        "",
        "## Stream Decisions",
        "",
        "| Stream | Decision | Active rows | Gate counts | Blockers / caveats | Next action |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for _, row in stream_frame.iterrows():
        counts = (
            f"pass={int(row['pass_count'])}, warn={int(row['warn_count'])}, "
            f"fail={int(row['fail_count'])}, missing={int(row['missing_evidence_count'])}"
        )
        blockers = row["hard_blockers"] or row["tracked_caveats"] or "none"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['stream']}`",
                    f"`{row['promotion_decision']}`",
                    str(int(row["active_objective_rows"])),
                    counts,
                    str(blockers).replace("|", "\\|"),
                    str(row["next_action"]).replace("|", "\\|"),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Failed Or Warning Gates", ""])
    flagged = checks_frame[
        checks_frame["status"].isin(["fail", "missing_evidence", "warn"])
        & checks_frame["required_for_active_likelihood"].astype(bool)
    ].copy()
    if flagged.empty:
        lines.append("No required activation gates are flagged.")
    else:
        lines.extend(
            [
                "| Stream | Gate | Status | Evidence | Blocker / caveat |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for _, row in flagged.iterrows():
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{row['stream']}`",
                        str(row["gate_label"]).replace("|", "\\|"),
                        f"`{row['status']}`",
                        str(row["evidence"]).replace("|", "\\|"),
                        str(row["blocker_or_caveat"]).replace("|", "\\|"),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Only direct permeability and NMR currently provide active objective rows,",
            "and NMR remains conditional on the bound/interlayer-water bias treatment.",
            "ERT, Taupe/TDR, and RH have useful forward diagnostics, but their hard",
            "likelihood promotion is blocked by transform/support/uncertainty,",
            "unit/calibration/weighting, and boundary-provenance gates, respectively.",
            "Other HM monitoring has support geometry and qualitative constraints but no",
            "hard-residual-ready numeric exports.  This is why the current inversion",
            "should not be described as a final all-measurement fit.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def build_audit(repo: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    processed = read_json(repo / "inversion_workflow/processed_observations/processed_observation_summary.json")
    coverage = read_json(repo / "inversion_workflow/measurement_operator_coverage_summary.json")
    likelihood = read_json(repo / "inversion_workflow/measurement_likelihood_model_summary.json")
    direct_state = read_json(repo / "inversion_workflow/runs/direct_fit_observation_run/state_observation_evaluation_summary.json")
    nmr_bound = read_json(repo / "inversion_workflow/processed_observations/nmr_bound_water_sensitivity_summary.json")
    nmr_bias = read_json(repo / "inversion_workflow/nmr_candidate_bias_sensitivity_summary.json")
    ert_diag = read_json(repo / "inversion_workflow/runs/direct_fit_observation_run/ert_resistivity_diagnostic_summary.json")
    ert_disc = read_json(repo / "inversion_workflow/ert_candidate_discrimination_summary.json")
    ert_support = read_json(repo / "inversion_workflow/ert_support_sensitivity_summary.json")
    taupe_diag = read_json(repo / "inversion_workflow/runs/direct_fit_observation_run/taupe_tdr_trend_diagnostic_summary.json")
    taupe_disc = read_json(repo / "inversion_workflow/taupe_candidate_discrimination_summary.json")
    taupe_weight = read_json(repo / "inversion_workflow/taupe_series_weight_sensitivity_summary.json")
    rh_provenance = read_json(repo / "inversion_workflow/processed_observations/rh_boundary_provenance_request_summary.json")
    rh_curves = read_json(repo / "inversion_workflow/processed_observations/rh_boundary_candidate_curve_summary.json")
    rh_uncertainty = read_json(repo / "inversion_workflow/processed_observations/rh_boundary_uncertainty_summary.json")
    other_hm = read_json(repo / "inversion_workflow/processed_observations/other_hm_numeric_source_audit_summary.json")
    release_gate = read_json(repo / "inversion_workflow/inversion_release_gate_audit.json")

    processed_total = sum(int(row.get("rows", 0) or 0) for row in processed.get("generated", []))
    active_state_rows = int(direct_state.get("used_in_objective_rows", 0) or likelihood.get("state_evaluation_status_counts", {}).get("evaluated", 0) or 0)
    direct_rows = csv_rows(repo / "inversion_workflow/processed_observations/permeability_observation_targets.csv")
    direct_cells = csv_rows(repo / "inversion_workflow/processed_observations/permeability_observation_cells.csv")
    state_rows = int(likelihood.get("state_target_rows", 0) or 0)
    checks: list[dict[str, Any]] = []
    nmr_required_offset_p95 = nmr_bound.get("required_offset_quantiles_usable", {}).get("p95")

    add_check(
        checks,
        stream="permeability_pulse_tests",
        gate_id="PERM_DATA",
        gate_label="positive interpreted permeability rows and provenance",
        status="pass" if direct_rows >= 200 else "fail",
        required_for_active_likelihood=True,
        evidence=f"target rows={direct_rows}; processed observation tables total rows={processed_total}",
        blocker_or_caveat="",
        artifacts="permeability_observation_targets.csv; permeability_measurement_semantics.md",
    )
    add_check(
        checks,
        stream="permeability_pulse_tests",
        gate_id="PERM_SUPPORT",
        gate_label="inside-mesh interval support for active rows",
        status="pass" if direct_cells >= 75 else "fail",
        required_for_active_likelihood=True,
        evidence=f"mapped cell rows={direct_cells}; current active objective rows=75",
        blocker_or_caveat="98 older permeability rows remain blocked by missing endpoint geometry" if direct_rows > direct_cells else "",
        artifacts="permeability_observation_cells.csv; permeability_missing_geometry_audit.md",
    )
    add_check(
        checks,
        stream="permeability_pulse_tests",
        gate_id="PERM_ERROR_MODEL",
        gate_label="broad gas-pulse model-error scale",
        status="warn",
        required_for_active_likelihood=True,
        evidence="current evaluator uses sigma=0.5 log10 units and duplicate-aware weights",
        blocker_or_caveat="Gas/slip/liquid-equivalent interpretation remains a tracked model-error caveat.",
        artifacts="evaluate_permeability_targets.py; permeability_measurement_semantics.md",
    )

    add_check(
        checks,
        stream="nmr_water_content",
        gate_id="NMR_SAMPLED_OUTPUTS",
        gate_label="sampled OGS theta outputs at usable target times",
        status="pass" if active_state_rows > 0 else "fail",
        required_for_active_likelihood=True,
        evidence=f"state target rows={state_rows}; active NMR objective rows={active_state_rows}",
        blocker_or_caveat="",
        artifacts="state_observation_evaluation_summary.json; ogs_state_sampling_summary.json",
    )
    add_check(
        checks,
        stream="nmr_water_content",
        gate_id="NMR_BOUND_WATER",
        gate_label="bound/interlayer-water bias quantified",
        status="warn",
        required_for_active_likelihood=True,
        evidence=(
            f"bound-water usable-row required-offset p95={nmr_required_offset_p95}; "
            f"bias audit runs={nmr_bias.get('run_count')}; rank correlation="
            f"{nmr_bias.get('current_vs_label_bias_rank_correlation')}"
        ),
        blocker_or_caveat="Raw absolute theta residuals remain conditional until a free-water/bound-water correction or anomaly residual is accepted.",
        artifacts="nmr_bound_water_sensitivity_summary.json; nmr_candidate_bias_sensitivity_summary.json",
    )

    add_check(
        checks,
        stream="ert_resistivity",
        gate_id="ERT_OPERATOR",
        gate_label="theta-to-resistivity operator and projection lookup generated",
        status="pass" if int(ert_diag.get("compared_rows", 0) or 0) > 0 else "fail",
        required_for_active_likelihood=True,
        evidence=(
            f"direct-run compared rows={ert_diag.get('compared_rows')}; "
            f"compared output times={ert_diag.get('compared_output_times')}"
        ),
        blocker_or_caveat="",
        artifacts="ert_observation_operator.md; ert_spatial_projection_operator.md; ert_resistivity_diagnostic_summary.json",
    )
    add_check(
        checks,
        stream="ert_resistivity",
        gate_id="ERT_TRANSFORM_SUPPORT",
        gate_label="coordinate transform and exact support mask confirmed",
        status="fail",
        required_for_active_likelihood=True,
        evidence=(
            f"support variants={ert_support.get('support_variant_count')}; "
            f"best mean support-rank run={ert_support.get('best_mean_support_rank', {}).get('run_id')}; "
            f"rank correlations vs default={ert_support.get('rank_correlations_vs_default_support')}"
        ),
        blocker_or_caveat="ERT-to-OGS transform and exact near-niche support mask remain assumed, not confirmed.",
        artifacts="ert_support_sensitivity_summary.json; ert_spatial_projection_operator.md",
    )
    add_check(
        checks,
        stream="ert_resistivity",
        gate_id="ERT_UNCERTAINTY",
        gate_label="inversion-field uncertainty/correlation model assigned",
        status="fail",
        required_for_active_likelihood=True,
        evidence=(
            f"cross-run ERT MAE range={ert_disc.get('ert_mae_log10_range')}; "
            "no pixel/time covariance model is recorded"
        ),
        blocker_or_caveat="No defensible ERT residual sigma/correlation model is available; pixels cannot be treated as independent rows.",
        artifacts="ert_candidate_discrimination_summary.json; measurement_likelihood_model.md",
    )

    add_check(
        checks,
        stream="taupe_tdr",
        gate_id="TAUPE_TREND_OPERATOR",
        gate_label="trend operator and sampled OGS comparison generated",
        status="pass" if int(taupe_diag.get("compared_rows", 0) or 0) > 0 else "fail",
        required_for_active_likelihood=True,
        evidence=f"compared rows={taupe_diag.get('compared_rows')}; compared series={taupe_diag.get('compared_series')}",
        blocker_or_caveat="",
        artifacts="taupe_tdr_trend_diagnostic_summary.json; taupe_tdr_observation_operator.md",
    )
    add_check(
        checks,
        stream="taupe_tdr",
        gate_id="TAUPE_UNIT_CALIBRATION",
        gate_label="Taupe workbook unit and absolute calibration confirmed",
        status="fail",
        required_for_active_likelihood=True,
        evidence="absolute candidate conversions remain sanity checks; Topp physical rows are zero in current audit",
        blocker_or_caveat="Taupe values are not confirmed as volumetric water-content percent, permittivity, or another ARDP-derived proxy.",
        artifacts="taupe_tdr_semantics.md; measurement_likelihood_model.md",
    )
    add_check(
        checks,
        stream="taupe_tdr",
        gate_id="TAUPE_GROUP_WEIGHTS",
        gate_label="series/group weighting and uncertainty model accepted",
        status="warn",
        required_for_active_likelihood=True,
        evidence=(
            f"series-weight runs={taupe_weight.get('run_count')}; compared series="
            f"{taupe_weight.get('compared_series_count')}; distinct per-series winners="
            f"{taupe_weight.get('series_best_run_distinct_count')}"
        ),
        blocker_or_caveat="Series-specific uncertainty and grouped weighting remain part of the calibration gate.",
        artifacts="taupe_series_weight_sensitivity_summary.json",
    )
    add_check(
        checks,
        stream="taupe_tdr",
        gate_id="TAUPE_SUPPORT",
        gate_label="all relevant Taupe sensors inside current mesh support",
        status="warn",
        required_for_active_likelihood=True,
        evidence=f"uncompared/outside-support series={taupe_weight.get('uncompared_series_count')}",
        blocker_or_caveat="A7/A8 remain outside the current Niche-4 mesh support.",
        artifacts="taupe_series_weight_sensitivity_summary.json; taupe_tdr_semantics.md",
    )

    add_check(
        checks,
        stream="relative_humidity_suction",
        gate_id="RH_KELVIN",
        gate_label="Kelvin conversion and candidate curves generated",
        status="pass" if int(rh_curves.get("candidate_count", 0) or 0) > 0 else "fail",
        required_for_active_likelihood=True,
        evidence=(
            f"candidate curves={rh_curves.get('candidate_count')}; "
            f"preferred candidate={rh_curves.get('preferred_policy_candidate')}"
        ),
        blocker_or_caveat="",
        artifacts="rh_boundary_candidate_curve_summary.json; rh_measurement_semantics.md",
    )
    add_check(
        checks,
        stream="relative_humidity_suction",
        gate_id="RH_ACTIVE_CURVE_PROVENANCE",
        gate_label="active OGS pressure curve provenance confirmed",
        status="fail",
        required_for_active_likelihood=True,
        evidence=(
            f"provenance request rows={rh_provenance.get('request_rows')}; "
            f"active outside candidate envelope={rh_uncertainty.get('active_curve_outside_envelope_count')}"
        ),
        blocker_or_caveat="Active boundary curve generation, sensor screening, time axis, constants, and extension policy are not confirmed.",
        artifacts="rh_boundary_provenance_request_summary.json; rh_boundary_uncertainty_summary.json",
    )
    add_check(
        checks,
        stream="relative_humidity_suction",
        gate_id="RH_UNCERTAINTY",
        gate_label="boundary/retention uncertainty model accepted",
        status="fail",
        required_for_active_likelihood=True,
        evidence=(
            f"envelope dates={rh_uncertainty.get('envelope_date_count')}; "
            f"overlap pressure-range p50={rh_uncertainty.get('overlap', {}).get('pressure_range_mpa', {}).get('p50')}"
        ),
        blocker_or_caveat="Local RH-derived envelope is quantified but not accepted as replacement forcing or retention likelihood.",
        artifacts="rh_boundary_uncertainty_summary.json; rh_boundary_uncertainty.md",
    )

    add_check(
        checks,
        stream="other_hm_monitoring",
        gate_id="HM_SUPPORT",
        gate_label="layout geometry and qualitative targets catalogued",
        status="pass" if int(other_hm.get("local_support_ready_request_count", 0) or 0) > 0 else "fail",
        required_for_active_likelihood=False,
        evidence=f"support-ready request classes={other_hm.get('local_support_ready_request_count')}",
        blocker_or_caveat="",
        artifacts="other_hm_monitoring.md; other_hm_numeric_source_audit_summary.json",
    )
    add_check(
        checks,
        stream="other_hm_monitoring",
        gate_id="HM_NUMERIC_EXPORTS",
        gate_label="hard-residual-ready numeric time series located",
        status="fail",
        required_for_active_likelihood=True,
        evidence=(
            f"hard-ready request classes={other_hm.get('hard_residual_ready_request_count')}; "
            f"zip numeric-candidate members={other_hm.get('source_bundle', {}).get('zip_member_numeric_candidate_count')}"
        ),
        blocker_or_caveat=other_hm.get("remaining_blocker", "numeric exports are missing"),
        artifacts="other_hm_numeric_source_audit_summary.json; other_hm_missing_numeric_request.md",
    )
    add_check(
        checks,
        stream="other_hm_monitoring",
        gate_id="HM_UNCERTAINTY",
        gate_label="units, epochs, reference conventions, uncertainty, and quality flags available",
        status="fail",
        required_for_active_likelihood=True,
        evidence=other_hm.get("activation_gate", ""),
        blocker_or_caveat="Required metadata for hard HM residual weights are absent from the current local bundle.",
        artifacts="other_hm_numeric_source_audit.md",
    )

    add_check(
        checks,
        stream="geometry_support",
        gate_id="GEOM_LOOKUPS",
        gate_label="measurement-to-mesh support lookups generated",
        status="pass" if coverage.get("observation_groups") == 9 else "fail",
        required_for_active_likelihood=False,
        evidence=f"observation groups={coverage.get('observation_groups')}; state sample rows={coverage.get('state_sample_rows')}",
        blocker_or_caveat="",
        artifacts="measurement_mesh_lookup.csv; borehole_line_mesh_samples.csv",
    )
    add_check(
        checks,
        stream="model_projection_inputs",
        gate_id="RELEASE_GATE",
        gate_label="run-local active parameter release gate passes",
        status="pass" if release_gate.get("status") == "pass" else "fail",
        required_for_active_likelihood=False,
        evidence=(
            f"release-gate status={release_gate.get('status')}; checks={release_gate.get('check_count')}; "
            f"failures={release_gate.get('failure_count')}"
        ),
        blocker_or_caveat="",
        artifacts="inversion_release_gate_audit.json; inversion_release_gate_audit.md",
    )

    decisions = {
        "permeability_pulse_tests": {
            "promotion_decision": "active_with_tracked_caveats",
            "current_model_role": "active direct parameter likelihood on k_i_rd directional permeability",
            "active_objective_rows": 75,
            "next_action": "Keep active; obtain endpoint geometry if older permeability rows should enter.",
            "primary_artifacts": "permeability_observation_targets.csv; permeability_fit_summary.json",
        },
        "nmr_water_content": {
            "promotion_decision": "active_with_tracked_caveats",
            "current_model_role": "active state likelihood from sampled theta=phi*S_l rows",
            "active_objective_rows": active_state_rows,
            "next_action": "Keep active but conditional; decide whether final objective uses label-bias or trend/anomaly residual.",
            "primary_artifacts": "state_observation_evaluation_summary.json; nmr_bound_water_sensitivity_summary.json",
        },
        "ert_resistivity": {
            "promotion_decision": decision_for(checks, "ert_resistivity", "diagnostic_only"),
            "current_model_role": "external resistivity diagnostic under assumed transform/support",
            "active_objective_rows": 0,
            "next_action": "Confirm ERT-to-OGS transform, exact support mask, and inversion uncertainty/correlation before assigning weights.",
            "primary_artifacts": "ert_resistivity_diagnostic_summary.json; ert_support_sensitivity_summary.json",
        },
        "taupe_tdr": {
            "promotion_decision": decision_for(checks, "taupe_tdr", "diagnostic_only"),
            "current_model_role": "baseline-normalized trend diagnostic on mapped A3/A4 bands",
            "active_objective_rows": 0,
            "next_action": "Confirm Taupe workbook units/calibration and adopt a grouped uncertainty model; A7/A8 remain outside support.",
            "primary_artifacts": "taupe_tdr_trend_diagnostic_summary.json; taupe_series_weight_sensitivity_summary.json",
        },
        "relative_humidity_suction": {
            "promotion_decision": decision_for(checks, "relative_humidity_suction", "boundary_audit_only"),
            "current_model_role": "boundary forcing provenance and Kelvin-pressure consistency audit",
            "active_objective_rows": 0,
            "next_action": "Get BGR/Gesa provenance for active open-niche pressure curve before replacement forcing or retention likelihood.",
            "primary_artifacts": "rh_boundary_provenance_request_summary.json; rh_boundary_uncertainty_summary.json",
        },
        "other_hm_monitoring": {
            "promotion_decision": decision_for(checks, "other_hm_monitoring", "not_ready_for_hard_residual"),
            "current_model_role": "qualitative validation and support geometry only",
            "active_objective_rows": 0,
            "next_action": "Locate Geoscope, laser-scan, and levelling numeric exports with epochs, units, support, and uncertainty.",
            "primary_artifacts": "other_hm_numeric_source_audit_summary.json; other_hm_missing_numeric_request.md",
        },
        "geometry_support": {
            "promotion_decision": "support_layer_ready",
            "current_model_role": "support/prior layer, not a likelihood residual",
            "active_objective_rows": 0,
            "next_action": "Continue propagating mapping status; add missing historical endpoint geometry where needed.",
            "primary_artifacts": "measurement_mesh_lookup.csv; borehole_line_mesh_samples.csv",
        },
        "model_projection_inputs": {
            "promotion_decision": "support_layer_ready",
            "current_model_role": "run-local mesh-field injection and release-gate guard",
            "active_objective_rows": 0,
            "next_action": "Keep using release-gated run preparation; do not release later parameters until stream gates pass.",
            "primary_artifacts": "inversion_release_gate_audit.md; inversion_parameter_release_plan.md",
        },
    }

    checks_frame = pd.DataFrame(checks).sort_values(
        ["stream", "required_for_active_likelihood", "status"],
        ascending=[True, False, True],
        key=lambda col: col.map(STATUS_ORDER) if col.name == "status" else col,
    ).reset_index(drop=True)
    stream_frame = summarize_streams(checks, decisions)
    summary = {
        "status": "measurement_stream_activation_gate_audit_generated",
        "stream_count": int(stream_frame.shape[0]),
        "gate_check_count": int(checks_frame.shape[0]),
        "active_stream_count": int(stream_frame["active_objective_rows"].gt(0).sum()),
        "active_objective_rows": int(stream_frame["active_objective_rows"].sum()),
        "promotion_decision_counts": stream_frame["promotion_decision"].value_counts().sort_index().to_dict(),
        "not_ready_for_hard_residual_count": int(
            stream_frame["promotion_decision"].isin(["not_ready_for_hard_residual"]).sum()
        ),
        "diagnostic_or_boundary_only_count": int(
            stream_frame["promotion_decision"].isin(["diagnostic_only", "boundary_audit_only"]).sum()
        ),
        "required_gate_fail_count": int(
            checks_frame[
                checks_frame["required_for_active_likelihood"]
                & checks_frame["status"].isin(["fail", "missing_evidence"])
            ].shape[0]
        ),
        "required_gate_warn_count": int(
            checks_frame[
                checks_frame["required_for_active_likelihood"]
                & checks_frame["status"].eq("warn")
            ].shape[0]
        ),
        "highest_priority_gate_actions": [
            "Keep the active direct-permeability/NMR objective conditional; do not claim a final all-measurement fit.",
            "Confirm ERT transform, exact support mask, and inversion uncertainty/correlation before ERT residual weights.",
            "Confirm Taupe/TDR units/calibration and grouped uncertainty before Taupe residual weights.",
            "Resolve RH active-curve provenance before replacement boundary forcing or retention likelihood.",
            "Locate hard-residual-ready Geoscope/laser/levelling exports before other-HM residual weights.",
        ],
    }
    return stream_frame, checks_frame, summary


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[2]
    output_dir = (repo / args.output_dir if not args.output_dir.is_absolute() else args.output_dir).resolve()
    catalogue_dir = (repo / args.catalogue_dir if not args.catalogue_dir.is_absolute() else args.catalogue_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    stream_frame, checks_frame, summary = build_audit(repo)

    stream_csv = output_dir / "measurement_stream_activation_gate_audit.csv"
    checks_csv = output_dir / "measurement_stream_activation_gate_checks.csv"
    summary_json = output_dir / "measurement_stream_activation_gate_audit_summary.json"
    markdown = output_dir / "measurement_stream_activation_gate_audit.md"
    stream_frame.to_csv(stream_csv, index=False)
    checks_frame.to_csv(checks_csv, index=False)
    summary_json.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(markdown, stream_frame, checks_frame, summary)

    catalogue_derived = catalogue_dir / "derived_files"
    catalogue_derived.mkdir(parents=True, exist_ok=True)
    copies = []
    for path in [stream_csv, checks_csv, summary_json, markdown]:
        target = catalogue_derived / path.name
        shutil.copy2(path, target)
        copies.append({"source": display_path(path, repo), "catalogue_copy": display_path(target, repo)})
    summary["catalogue_copies"] = copies
    summary_json.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    shutil.copy2(summary_json, catalogue_derived / summary_json.name)
    write_markdown(markdown, stream_frame, checks_frame, summary)
    shutil.copy2(markdown, catalogue_derived / markdown.name)

    print(f"wrote {stream_csv}")
    print(f"wrote {checks_csv}")
    print(f"wrote {summary_json}")
    print(f"wrote {markdown}")
    print(f"required gate failures: {summary['required_gate_fail_count']}")


if __name__ == "__main__":
    main()
