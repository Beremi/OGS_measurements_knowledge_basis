#!/usr/bin/env python3
"""Build a machine-readable likelihood/activation model for measurement streams."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
    )
    parser.add_argument(
        "--candidate-summary",
        type=Path,
        default=Path(
            "inversion_workflow/runs/local_refinement_candidate_search/"
            "local_refined_001_length_0p013m_summary.json"
        ),
    )
    parser.add_argument("--permeability-summary", type=Path, help="Override candidate permeability summary JSON.")
    parser.add_argument("--state-summary", type=Path, help="Override candidate state-observation summary JSON.")
    parser.add_argument("--combined-summary", type=Path, help="Override candidate combined-objective summary JSON.")
    parser.add_argument("--rh-boundary-summary", type=Path, help="Override candidate RH boundary-curve audit summary JSON.")
    parser.add_argument(
        "--nmr-bound-water-summary",
        type=Path,
        default=Path("inversion_workflow/processed_observations/nmr_bound_water_sensitivity_summary.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/measurement_likelihood_model.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/measurement_likelihood_model_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/measurement_likelihood_model.md"),
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def row_count(path: Path) -> int:
    if not path.exists():
        return 0
    return int(pd.read_csv(path, usecols=[0]).shape[0])


def bool_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].astype(str).str.lower().isin({"true", "1", "yes"}).sum())


def family_rows(frame: pd.DataFrame, family: str) -> pd.DataFrame:
    if frame.empty or "observation_family" not in frame.columns:
        return pd.DataFrame()
    return frame[frame["observation_family"].astype(str).eq(family)].copy()


def json_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(number):
        return None
    return number


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return json_number(value)
    if value is pd.NA or value is None:
        return None
    return value


def add_row(
    rows: list[dict[str, Any]],
    *,
    measurement_stream: str,
    activation_state: str,
    current_objective_rows: int,
    candidate_rows: int,
    usable_rows: int,
    model_link: str,
    prediction_quantity: str,
    residual_definition: str,
    residual_transform: str,
    likelihood_scale: str,
    weighting_rule: str,
    bias_or_model_error_terms: str,
    activation_gate: str,
    current_artifacts: str,
    source_basis: str,
    notes: str,
) -> None:
    rows.append(
        {
            "measurement_stream": measurement_stream,
            "activation_state": activation_state,
            "candidate_rows": candidate_rows,
            "usable_or_mapped_rows": usable_rows,
            "current_objective_rows": current_objective_rows,
            "model_link": model_link,
            "prediction_quantity": prediction_quantity,
            "residual_definition": residual_definition,
            "residual_transform": residual_transform,
            "likelihood_scale": likelihood_scale,
            "weighting_rule": weighting_rule,
            "bias_or_model_error_terms": bias_or_model_error_terms,
            "activation_gate": activation_gate,
            "current_artifacts": current_artifacts,
            "source_basis": source_basis,
            "notes": notes,
        }
    )


def build_rows(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    processed = args.processed_dir
    targets = read_csv(processed / "state_observation_targets.csv")
    perm_summary = read_json(processed / "permeability_target_summary.json")
    perm_semantics = read_json(processed / "permeability_measurement_semantics_summary.json")
    perm_policy = read_json(Path("inversion_workflow/permeability_likelihood_policy_audit_summary.json"))
    state_summary = read_json(processed / "state_observation_target_summary.json")
    ert_operator = read_json(processed / "ert_observation_operator_summary.json")
    ert_projection = read_json(processed / "ert_spatial_projection_summary.json")
    ert_semantics = read_json(processed / "ert_measurement_semantics_summary.json")
    ert_diagnostic = read_json(
        Path("inversion_workflow/runs/direct_fit_observation_run/ert_resistivity_diagnostic_summary.json")
    )
    ert_discrimination = read_json(Path("inversion_workflow/ert_candidate_discrimination_summary.json"))
    ert_support_sensitivity = read_json(Path("inversion_workflow/ert_support_sensitivity_summary.json"))
    taupe_operator = read_json(processed / "taupe_tdr_observation_operator_summary.json")
    taupe_semantics = read_json(processed / "taupe_tdr_semantics_summary.json")
    taupe_diagnostic = read_json(
        Path("inversion_workflow/runs/direct_fit_observation_run/taupe_tdr_trend_diagnostic_summary.json")
    )
    taupe_discrimination = read_json(Path("inversion_workflow/taupe_candidate_discrimination_summary.json"))
    taupe_weight_sensitivity = read_json(Path("inversion_workflow/taupe_series_weight_sensitivity_summary.json"))
    rh_semantics = read_json(processed / "rh_measurement_semantics_summary.json")
    rh_provenance = read_json(processed / "rh_boundary_provenance_request_summary.json")
    rh_candidate_curves = read_json(processed / "rh_boundary_candidate_curve_summary.json")
    rh_uncertainty = read_json(processed / "rh_boundary_uncertainty_summary.json")
    rh_candidate_rows = {
        str(row.get("candidate_id")): row
        for row in rh_candidate_curves.get("summary_rows", [])
        if isinstance(row, dict)
    }
    rh_preferred_curve = rh_candidate_rows.get(
        str(rh_candidate_curves.get("preferred_policy_candidate", "")),
        {},
    )
    other_hm = read_json(processed / "other_hm_monitoring_summary.json")
    other_hm_missing = read_json(processed / "other_hm_missing_numeric_request_summary.json")
    other_hm_source_audit = read_json(processed / "other_hm_numeric_source_audit_summary.json")
    nmr_bound_water = read_json(args.nmr_bound_water_summary)
    nmr_bias_sensitivity = read_json(Path("inversion_workflow/nmr_candidate_bias_sensitivity_summary.json"))
    candidate = read_json(args.candidate_summary)
    candidate_permeability = (
        read_json(args.permeability_summary)
        if args.permeability_summary
        else candidate.get("permeability_summary", {})
    )
    candidate_state = read_json(args.state_summary) if args.state_summary else candidate.get("state_summary", {})
    candidate_combined = (
        read_json(args.combined_summary)
        if args.combined_summary
        else candidate.get("combined_summary", {})
    )
    rh_boundary = (
        read_json(args.rh_boundary_summary)
        if args.rh_boundary_summary
        else candidate.get("rh_boundary_summary", {})
    )

    nmr_weekly = family_rows(targets, "NMR weekly")
    nmr_seasonal = family_rows(targets, "NMR seasonal")
    nmr_targets = pd.concat([nmr_weekly, nmr_seasonal], ignore_index=True)
    active_nmr_state_rows = int(candidate_state.get("used_in_objective_rows", 0) or 0)
    taupe_targets = family_rows(targets, "Taupe/TDR")
    rh_targets = family_rows(targets, "Suction/RH")
    ert_targets = family_rows(targets, "ERT open-niche time series")

    fixed_phi = json_number(nmr_bound_water.get("fixed_phi"))
    nmr_usable_rows = int(nmr_bound_water.get("usable_current_mesh_rows", bool_count(nmr_targets, "usable_for_current_state_fit")) or 0)
    nmr_above_phi = int(nmr_bound_water.get("uncorrected_usable_rows_above_fixed_phi", 0) or 0)
    required_offset_usable = nmr_bound_water.get("required_offset_quantiles_usable", {})
    required_offset_p95 = json_number(required_offset_usable.get("p95"))
    best_uniform_offset = nmr_bound_water.get("best_uniform_offset_by_simple_physical_count_usable", {})
    best_offset = json_number(best_uniform_offset.get("offset_fraction"))
    best_offset_nonphysical = best_uniform_offset.get("nonphysical_rows", "n/a")
    best_label_bias = nmr_bias_sensitivity.get("best_label_bias_combined", {})
    best_trend_anomaly = nmr_bias_sensitivity.get("best_trend_anomaly_combined", {})
    nmr_bias_runs = nmr_bias_sensitivity.get("run_count")
    nmr_bias_rank_corr = nmr_bias_sensitivity.get("current_vs_label_bias_rank_correlation")
    if fixed_phi is None:
        nmr_bound_water_note = "No generated bound-water sensitivity summary was found."
        nmr_bound_water_scale = "recommended activation should add an explicit bound/interlayer-water model-error floor"
    else:
        nmr_bound_water_note = (
            f"Bound-water sensitivity audit: fixed phi={fixed_phi:.3f}; "
            f"{nmr_above_phi} of {nmr_usable_rows} currently usable mapped rows exceed phi if interpreted "
            "as mobile theta without correction"
        )
        if required_offset_p95 is not None:
            nmr_bound_water_note += f"; usable-row required positive offset p95={required_offset_p95:.4f}"
        if best_offset is not None:
            nmr_bound_water_note += (
                f"; best tested uniform subtraction by simple physical-row count is {best_offset:.3f}, "
                f"leaving {best_offset_nonphysical} nonphysical usable rows"
            )
        if nmr_bias_runs:
            nmr_bound_water_note += (
                f"; cross-run bias/anomaly audit spans {nmr_bias_runs} runs, "
                f"best label-bias run={best_label_bias.get('run_id', 'n/a')} "
                f"with diagnostic combined objective={best_label_bias.get('label_bias_combined_objective', 'n/a')}, "
                f"best anomaly run={best_trend_anomaly.get('run_id', 'n/a')}, "
                f"current-vs-bias rank correlation={nmr_bias_rank_corr}"
            )
        nmr_bound_water_note += "."
        nmr_bound_water_scale = (
            "row sigma from reported 95 percent confidence interval with 0.01 fraction floor; "
            "absolute-residual activation must include the generated bound-water/bias audit, "
            f"with usable-row required-offset p95={required_offset_p95:.4f}"
            if required_offset_p95 is not None
            else (
                "row sigma from reported 95 percent confidence interval with 0.01 fraction floor; "
                "absolute-residual activation must include the generated bound-water/bias audit"
            )
        )

    taupe_phys = taupe_semantics.get(
        "candidate_absolute_interpretation_physical_rows",
        taupe_operator.get("candidate_absolute_interpretation_physical_rows", {}),
    )
    rows: list[dict[str, Any]] = []
    add_row(
        rows,
        measurement_stream="permeability_pulse_tests",
        activation_state="active_direct_parameter_likelihood",
        current_objective_rows=int(candidate_permeability.get("used_in_objective_rows", 0)),
        candidate_rows=int(perm_summary.get("target_rows", 0)),
        usable_rows=int(perm_summary.get("usable_for_current_ogs_fit", 0)),
        model_link="direct constraint on run-local intrinsic permeability tensor field k_i_rd",
        prediction_quantity="interval-weighted directional permeability e^T K e",
        residual_definition="log10(k_pred_m2) - log10(k_obs_m2)",
        residual_transform="Gaussian residual in log10 permeability space",
        likelihood_scale=(
            "current evaluator uses sigma = 0.5 log10 units; this is an intentionally broad first-pass scale; "
            "robust-tail and support-cell aggregation alternatives are diagnostic only unless explicitly approved"
        ),
        weighting_rule=(
            "duplicates with same campaign, segment, depth and observed log10(k) share unit weight; "
            "support-cell repeated/conflicting rows are now audited separately by the likelihood-policy diagnostic"
        ),
        bias_or_model_error_terms=(
            "gas pulse interpretation versus liquid-equivalent intrinsic permeability; "
            "Klinkenberg/slip correction provenance; 3D interval support represented in 2D; "
            "scalar interval value projected onto directional tensor response; "
            "gas transport in claystone can involve capillary water displacement and is not liquid relative permeability"
        ),
        activation_gate="already active for rows with positive interpreted k and inside-mesh interval mapping",
        current_artifacts=(
            "permeability_observation_targets.csv; permeability_observation_cells.csv; "
            "permeability_measurement_semantics.md; permeability_fit_evaluation.csv; permeability_fit_summary.json; "
            "permeability_residual_conflict_audit.md; permeability_likelihood_policy_audit.md; "
            "permeability_likelihood_decision_request.md"
        ),
        source_basis="local permeability workbook, characterization slides/paper, Klinkenberg1941, Marschall2005",
        notes=(
            f"Current candidate direct objective: {candidate_permeability.get('objective_value', 'n/a')}; "
            f"effective weight: {candidate_permeability.get('effective_objective_weight', 'n/a')}. "
            f"Semantics audit rows: {perm_semantics.get('target_rows', perm_summary.get('target_rows', 'n/a'))}; "
            f"positive rows: {perm_semantics.get('positive_rows', 'n/a')}; "
            f"usable current rows: {perm_semantics.get('usable_current_rows', perm_summary.get('usable_for_current_ogs_fit', 'n/a'))}; "
            f"usable segments: {', '.join(perm_semantics.get('usable_segments', [])) or 'n/a'}. "
            f"Likelihood policy audit status: {perm_policy.get('status', 'n/a')}; "
            f"top-10 row-loss share: {perm_policy.get('row_loss_top_10_share', 'n/a')}; "
            f"support-cell mean diagnostic objective: {perm_policy.get('support_mean_unit_objective', 'n/a')}; "
            f"conflicting support groups: {perm_policy.get('support_groups_with_observed_range_ge_1_log10', 'n/a')}; "
            "active row-Gaussian policy remains unchanged without a modelling-team decision; "
            "the decision request records robust/support-cell/scalar-outlier alternatives for future reranking."
        ),
    )
    add_row(
        rows,
        measurement_stream="NMR weekly and seasonal water content",
        activation_state=(
            "active_state_likelihood_from_sampled_ogs_outputs"
            if active_nmr_state_rows
            else "prepared_state_likelihood_pending_ogs_outputs"
        ),
        current_objective_rows=active_nmr_state_rows,
        candidate_rows=int(nmr_targets.shape[0]),
        usable_rows=bool_count(nmr_targets, "usable_for_current_state_fit"),
        model_link="sample OGS porosity*saturation at mapped NMR labels",
        prediction_quantity="theta_model = porosity * liquid_saturation",
        residual_definition="theta_model - theta_NMR_obs",
        residual_transform="Gaussian residual in volumetric water-content fraction after bias treatment",
        likelihood_scale=nmr_bound_water_scale,
        weighting_rule="one point target per dated NMR row; seasonal Niche 3 rows stay outside current Niche 4 fit",
        bias_or_model_error_terms=(
            "NMR detects hydrogen-bearing water, including bound/interlayer contributions that may not "
            "belong to mobile liquid saturation in the OGS Richards equation"
        ),
        activation_gate=(
            "requires sampled OGS state outputs and the generated bound-water sensitivity audit; "
            "prefer trend/anomaly residuals before absolute theta residuals"
        ),
        current_artifacts=(
            "nmr_weekly.csv; nmr_seasonal_profiles.csv; state_observation_targets.csv; "
            "state_observation_samples.csv; nmr_bound_water_sensitivity.md; "
            "nmr_candidate_bias_sensitivity.md"
        ),
        source_basis="WaterContentEDZ2024; NMR2026Local; Kleinberg1996NMR; Elsayed2020ClayNMR",
        notes=(
            f"Current sampled OGS evaluation uses {active_nmr_state_rows} NMR rows in the state objective. "
            "Delta/trend residuals remain safer than absolute saturation if no free-water correction is available. "
            + nmr_bound_water_note
        ),
    )
    add_row(
        rows,
        measurement_stream="ERT open-niche resistivity field",
        activation_state="resistivity_diagnostic_evaluated_transform_support_unconfirmed",
        current_objective_rows=0,
        candidate_rows=int(ert_targets.shape[0]),
        usable_rows=int(ert_projection.get("ready_for_residual_after_ogs_output_rows", 0)),
        model_link="project OGS theta field to ERT mesh/support and convert theta to resistivity",
        prediction_quantity="rho_pred = a * theta_model ** b on ERT/common mesh",
        residual_definition="log10(rho_pred) - log10(rho_ERT_inverted)",
        residual_transform="multiplicative/log-resistivity residual; no active sigma yet",
        likelihood_scale=(
            "defer numerical sigma until ERT-to-OGS transform, support mask, and inversion-field uncertainty are confirmed; support-sensitivity ranks are diagnostic only"
        ),
        weighting_rule="future weights should aggregate ERT cells by support/time to avoid treating correlated pixels as independent",
        bias_or_model_error_terms=(
            "empirical theta-resistivity calibration; clay surface conduction; ERT inversion smoothing; "
            "coordinate transform and OGS/ERT domain mismatch"
        ),
        activation_gate=(
            "Confirm ERT-to-OGS coordinate transform, exact near-niche support mask, and ERT inversion "
            "uncertainty/correlation before activation."
        ),
        current_artifacts=(
            "ert_timesteps.csv; ert_water_content_resistivity_operator.csv; "
            "ert_spatial_projection_lookup.csv; ert_measurement_semantics.md; "
            "ert_observation_operator.md; ert_spatial_projection_operator.md; "
            "direct_fit_observation_run/ert_resistivity_diagnostic.md; "
            "ert_candidate_discrimination.md; ert_support_sensitivity.md"
        ),
        source_basis="WaterContentEDZ2024; Archie1942; CDAModellingSlides2025",
        notes=(
            f"Recommended relation: {ert_operator.get('recommended_relation_id', 'n/a')}; "
            f"timestep rows: {ert_semantics.get('timestep_rows', ert_operator.get('ert_timesteps', 'n/a'))}; "
            f"with matching VTK: {ert_semantics.get('timesteps_with_matching_vtk', ert_operator.get('ert_timesteps_with_matching_vtk', 'n/a'))}; "
            f"missing VTK: {ert_semantics.get('timesteps_missing_matching_vtk', ert_operator.get('ert_timesteps_missing_matching_vtk', 'n/a'))}; "
            f"projection-ready rows: {ert_projection.get('ready_for_residual_after_ogs_output_rows', 'n/a')}; "
            f"direct-run compared rows: {ert_diagnostic.get('compared_rows', 'n/a')}; "
            f"compared output times: {ert_diagnostic.get('compared_output_times', 'n/a')}; "
            f"log10 residual MAE: {ert_diagnostic.get('area_weighted_residual_log10', {}).get('mae', 'n/a')}; "
            f"log10 residual RMSE: {ert_diagnostic.get('area_weighted_residual_log10', {}).get('rmse', 'n/a')}; "
            f"cross-run audited runs: {ert_discrimination.get('run_count', 'n/a')}; "
            f"full active-objective runs: {ert_discrimination.get('runs_with_full_active_combined_objective', 'n/a')}; "
            f"cross-run ERT MAE range: {ert_discrimination.get('ert_mae_log10_range', 'n/a')}; "
            f"best active-objective ERT MAE: {ert_discrimination.get('best_combined_ert_mae_log10', 'n/a')}; "
            f"combined-objective/ERT-MAE correlation: {ert_discrimination.get('combined_objective_ert_mae_correlation', 'n/a')}; "
            f"support-sensitivity selected runs: {ert_support_sensitivity.get('run_count', 'n/a')}; "
            f"support variants: {ert_support_sensitivity.get('support_variant_count', 'n/a')}; "
            f"best mean support-rank run: {ert_support_sensitivity.get('best_mean_support_rank', {}).get('run_id', 'n/a')}."
        ),
    )
    add_row(
        rows,
        measurement_stream="Taupe/TDR EDZ bands",
        activation_state="trend_diagnostic_evaluated_pending_absolute_calibration",
        current_objective_rows=0,
        candidate_rows=int(taupe_semantics.get("state_target_rows", taupe_targets.shape[0])),
        usable_rows=int(taupe_semantics.get("mapped_trend_rows", taupe_operator.get("mapped_trend_operator_rows", 0))),
        model_link="band-average OGS theta along mapped Taupe borehole intervals",
        prediction_quantity="baseline-normalized theta_model trend by sensor and EDZ band",
        residual_definition="model trend anomaly - observed Taupe/TDR anomaly",
        residual_transform="within-series trend diagnostic; absolute saturation residual inactive",
        likelihood_scale=(
            "no absolute sigma assigned; future trend sigma should be estimated per sensor/band after unit calibration; grouped-weight sensitivity remains diagnostic"
        ),
        weighting_rule="aggregate by sensor, EDZ band, and time; A7/A8 remain outside current mesh support",
        bias_or_model_error_terms=(
            "workbook unit not confirmed; TDR dielectric response is not automatically volumetric water content "
            "in claystone; band-average support differs from OGS cells"
        ),
        activation_gate=str(
            taupe_semantics.get(
                "remaining_blocker",
                taupe_operator.get("remaining_blocker", "confirm Taupe/TDR unit and calibration"),
            )
        ),
        current_artifacts=(
            "taupe_tdr_bands.csv; taupe_tdr_trend_operator.csv; "
            "taupe_tdr_semantics.md; taupe_tdr_observation_operator.md; "
            "direct_fit_observation_run/taupe_tdr_trend_diagnostic.md; "
            "taupe_candidate_discrimination.md; taupe_series_weight_sensitivity.md"
        ),
        source_basis="TaupeISU2026Local; CDAModellingSlides2025; Topp1980TDR",
        notes=(
            f"Mapped trend rows: {taupe_semantics.get('mapped_trend_rows', taupe_operator.get('mapped_trend_operator_rows', 'n/a'))}; "
            f"outside current mesh rows: {taupe_semantics.get('outside_current_mesh_rows', 'n/a')}; "
            f"trend-ready series: {taupe_semantics.get('trend_ready_series', 'n/a')}; "
            f"outside-support series: {taupe_semantics.get('outside_current_mesh_series', 'n/a')}; "
            f"direct-run compared trend rows: {taupe_diagnostic.get('compared_rows', 'n/a')}; "
            f"compared series: {taupe_diagnostic.get('compared_series', 'n/a')}; "
            f"trend diagnostic MAE: {taupe_diagnostic.get('standardized_residual', {}).get('mae', 'n/a')}; "
            f"cross-run audited runs: {taupe_discrimination.get('run_count', 'n/a')}; "
            f"full active-objective runs: {taupe_discrimination.get('runs_with_full_active_combined_objective', 'n/a')}; "
            f"cross-run Taupe MAE range: {taupe_discrimination.get('taupe_mae_range', 'n/a')}; "
            f"best active-objective Taupe MAE: {taupe_discrimination.get('best_combined_taupe_mae', 'n/a')}; "
            f"series-weight sensitivity runs: {taupe_weight_sensitivity.get('run_count', 'n/a')}; "
            f"compared A3/A4 series: {taupe_weight_sensitivity.get('compared_series_count', 'n/a')}; "
            f"uncompared A7/A8 series: {taupe_weight_sensitivity.get('uncompared_series_count', 'n/a')}; "
            f"distinct per-series winners: {taupe_weight_sensitivity.get('series_best_run_distinct_count', 'n/a')}; "
            f"best mean weighting-rank run: {taupe_weight_sensitivity.get('best_mean_weighting_rank', {}).get('run_id', 'n/a')}; "
            "absolute candidate conversions remain sanity checks "
            f"(WC-percent physical rows: {taupe_phys.get('taupe_value_as_vol_percent', 'n/a')}; "
            f"Topp physical rows: {taupe_phys.get('taupe_value_as_topp_epsilon', 'n/a')}; "
            f"linear eps6 physical rows: {taupe_phys.get('linear_mixing_epsilon_rock_6', 'n/a')})."
        ),
    )
    add_row(
        rows,
        measurement_stream="suction/relative humidity",
        activation_state="boundary_forcing_audit_not_point_likelihood",
        current_objective_rows=0,
        candidate_rows=int(rh_semantics.get("state_target_rows", rh_targets.shape[0])),
        usable_rows=int(rh_semantics.get("valid_non_low_outlier_rows", bool_count(rh_targets, "usable_for_current_state_fit"))),
        model_link="hydraulic boundary pressure curve and retention-curve consistency check",
        prediction_quantity="liquid pressure/capillary pressure implied by RH through Kelvin relation",
        residual_definition="active OGS boundary curve - RH-derived Kelvin pressure",
        residual_transform="boundary provenance audit; not a cell residual in current objective",
        likelihood_scale="no point-residual sigma assigned; sensor reliability split must enter any future curve-fit likelihood",
        weighting_rule="filter invalid/low-RH outliers; keep high-RH open-twin caution flag",
        bias_or_model_error_terms=(
            "temperature and density assumptions in Kelvin conversion; sensor reliability above 95 percent RH; "
            "unknown preprocessing used for 08_08_open_niche_seasonal.xml"
        ),
        activation_gate=str(
            rh_provenance.get(
                "remaining_blocker",
                rh_semantics.get(
                    "remaining_blocker",
                    "confirm generation/provenance of the OGS open-niche seasonal pressure curve",
                ),
            )
        ),
        current_artifacts=(
            "rh_open_twin_kelvin.csv; rh_boundary_curve_audit.csv; "
            "rh_measurement_semantics.md; rh_measurement_semantics_summary.json; "
            "rh_boundary_provenance_request.md; rh_boundary_provenance_request.csv; "
            "rh_boundary_candidate_curves.md; rh_boundary_candidate_curve_summary.json; "
            "rh_boundary_uncertainty.md; rh_boundary_uncertainty_summary.json"
        ),
        source_basis="WaterContentEDZ2024; Thomson1871Kelvin; TDMinutes2026Local",
        notes=(
            f"RH rows: {rh_semantics.get('rh_rows', rh_targets.shape[0])}; "
            f"valid non-low-outlier rows: {rh_semantics.get('valid_non_low_outlier_rows', 'n/a')}; "
            f"low-RH outliers: {rh_semantics.get('low_rh_outlier_rows', 'n/a')}; "
            f">95% open-twin caution rows: {rh_semantics.get('above_95_percent_open_twin_caution_rows', 'n/a')}; "
            f"compared rows: {rh_boundary.get('compared_rows', 'n/a')}; "
            f"median absolute mismatch MPa: {rh_boundary.get('overall_abs_residual_mpa', {}).get('median', 'n/a')}; "
            "active-curve implied RH rows below clean RH5/RH6 minimum: "
            f"{rh_semantics.get('active_curve', {}).get('rows_below_clean_rh5_rh6_collected_rh_min', 'n/a')}; "
            f"provenance request rows: {rh_provenance.get('request_rows', 'n/a')}; "
            f"evidence rows: {rh_provenance.get('evidence_rows', 'n/a')}; "
            f"candidate boundary curves: {rh_candidate_curves.get('candidate_count', 'n/a')}; "
            f"preferred candidate: {rh_candidate_curves.get('preferred_policy_candidate', 'n/a')}; "
            f"preferred overlap MAE MPa: {rh_preferred_curve.get('overlap_abs_residual_mpa_mae', 'n/a')}; "
            f"candidate rows after active curve: {rh_candidate_curves.get('comparison_status_counts', {}).get('after_active_curve_time_range_requires_curve_extension_or_new_forcing', 'n/a')}; "
            f"candidate-envelope dates: {rh_uncertainty.get('envelope_date_count', 'n/a')}; "
            f"overlap pressure-range p50 MPa: {rh_uncertainty.get('overlap', {}).get('pressure_range_mpa', {}).get('p50', 'n/a')}; "
            f"active outside candidate envelope rows: {rh_uncertainty.get('active_curve_outside_envelope_count', 'n/a')}; "
            f"active curve date span: {rh_provenance.get('active_curve_date_min', 'n/a')} to "
            f"{rh_provenance.get('active_curve_date_max', 'n/a')}."
        ),
    )
    add_row(
        rows,
        measurement_stream="other HM monitoring and levelling",
        activation_state="qualitative_validation_layer_numeric_series_missing",
        current_objective_rows=0,
        candidate_rows=row_count(processed / "other_hm_qualitative_targets.csv")
        + row_count(processed / "other_hm_levelling_displacements.csv"),
        usable_rows=int(other_hm.get("model_facing_rows", 0)),
        model_link="mechanical plausibility checks on displacement/stress and pressure responses",
        prediction_quantity="candidate-dependent displacement, pressure, and qualitative trend diagnostics",
        residual_definition="not yet a numerical residual except future levelling/geoscope series comparisons",
        residual_transform="validation gates before hard likelihood",
        likelihood_scale="no hard sigma assigned until Geoscope/laser-scan/extensometer time series are located",
        weighting_rule="avoid hard weighting of qualitative statements; use as rejection/diagnostic gates",
        bias_or_model_error_terms="simplified 2D model cannot explain every 3D deformation or crack/scan observation",
        activation_gate=str(
            other_hm_missing.get(
                "remaining_blocker",
                other_hm.get(
                "remaining_blocker",
                "locate Geoscope mini-piezometer/extensometer/crackmeter and laser-scan numeric exports",
                ),
            )
        ),
        current_artifacts=(
            "other_hm_monitoring.md; other_hm_qualitative_targets.csv; "
            "other_hm_levelling_displacements.csv; other_hm_missing_numeric_request.md; "
            "other_hm_missing_numeric_request.csv; other_hm_numeric_source_audit.md; "
            "other_hm_numeric_source_audit_summary.json"
        ),
        source_basis="InputHERMES2024Local; BGRModellingTD2026Local; LevellingTD2026Local",
        notes=(
            "Use to reject mechanically implausible permeability-only fits once OGS displacement outputs exist. "
            f"Missing numeric request rows: {other_hm_missing.get('request_rows', 'n/a')}; "
            f"evidence rows: {other_hm_missing.get('evidence_rows', 'n/a')}; "
            f"numeric source audit requests: {other_hm_source_audit.get('request_rows', 'n/a')}; "
            f"hard-residual-ready requests: "
            f"{other_hm_source_audit.get('hard_residual_ready_request_count', 'n/a')}; "
            f"support-ready requests: "
            f"{other_hm_source_audit.get('local_support_ready_request_count', 'n/a')}; "
            f"zip numeric-candidate members: "
            f"{other_hm_source_audit.get('source_bundle', {}).get('zip_member_numeric_candidate_count', 'n/a')}."
        ),
    )
    add_row(
        rows,
        measurement_stream="coordinates, borehole geometry, and bedding",
        activation_state="support_and_prior_layer",
        current_objective_rows=0,
        candidate_rows=row_count(processed / "measurement_coordinates_xy.csv")
        + row_count(processed / "borehole_coordinates.csv"),
        usable_rows=row_count(processed / "measurement_mesh_lookup.csv")
        + row_count(processed / "borehole_line_mesh_samples.csv"),
        model_link="observation support mapping and anisotropy-orientation prior",
        prediction_quantity="no direct physical residual",
        residual_definition="not a likelihood term",
        residual_transform="support/prior metadata",
        likelihood_scale="not applicable",
        weighting_rule="propagate mapping status to downstream measurement residuals",
        bias_or_model_error_terms="coordinate-frame mismatch and missing endpoint geometry dominate downstream risk",
        activation_gate="continue using as required support; add endpoint geometry for older permeability rows",
        current_artifacts="measurement_mesh_lookup.csv; borehole_mesh_lookup.csv; borehole_line_mesh_samples.csv",
        source_basis="coordinate workbooks; Ziefle2024Characterization; CDAModellingSlides2025",
        notes="This layer prevents outside-mesh and nearest-cell fallbacks from silently entering active objectives.",
    )

    likelihood = pd.DataFrame(rows)
    status_counts = {
        str(key): int(value)
        for key, value in likelihood["activation_state"].value_counts().sort_index().items()
    }
    summary = {
        "measurement_streams": int(likelihood.shape[0]),
        "active_streams_now": int(likelihood["current_objective_rows"].gt(0).sum()),
        "activation_state_counts": status_counts,
        "total_candidate_rows": int(likelihood["candidate_rows"].sum()),
        "total_current_objective_rows": int(likelihood["current_objective_rows"].sum()),
        "state_target_rows": int(state_summary.get("target_rows", 0)),
        "state_evaluation_status_counts": candidate_state.get("evaluation_status_counts", {}),
        "ert_support_sensitivity_runs": int(ert_support_sensitivity.get("run_count", 0) or 0),
        "ert_support_sensitivity_variant_count": int(ert_support_sensitivity.get("support_variant_count", 0) or 0),
        "ert_support_sensitivity_best_mean_rank_run": ert_support_sensitivity.get("best_mean_support_rank", {}).get("run_id"),
        "taupe_series_weight_sensitivity_runs": int(taupe_weight_sensitivity.get("run_count", 0) or 0),
        "taupe_series_weight_sensitivity_compared_series": int(taupe_weight_sensitivity.get("compared_series_count", 0) or 0),
        "taupe_series_weight_sensitivity_distinct_series_winners": int(taupe_weight_sensitivity.get("series_best_run_distinct_count", 0) or 0),
        "taupe_series_weight_sensitivity_best_mean_rank_run": taupe_weight_sensitivity.get("best_mean_weighting_rank", {}).get("run_id"),
        "rh_boundary_uncertainty_envelope_dates": int(rh_uncertainty.get("envelope_date_count", 0) or 0),
        "rh_boundary_uncertainty_active_outside_envelope_count": int(
            rh_uncertainty.get("active_curve_outside_envelope_count", 0) or 0
        ),
        "rh_boundary_uncertainty_overlap_pressure_range_p50_mpa": rh_uncertainty.get("overlap", {})
        .get("pressure_range_mpa", {})
        .get("p50"),
        "other_hm_numeric_source_audit_request_rows": int(other_hm_source_audit.get("request_rows", 0) or 0),
        "other_hm_numeric_source_audit_hard_ready_requests": int(
            other_hm_source_audit.get("hard_residual_ready_request_count", 0) or 0
        ),
        "other_hm_numeric_source_audit_support_ready_requests": int(
            other_hm_source_audit.get("local_support_ready_request_count", 0) or 0
        ),
        "current_candidate_total_active_objective": candidate_combined.get("total_active_objective_value"),
        "notes": [
            "This artifact records likelihood intent and activation gates, not just data coverage.",
            "Direct permeability pulse tests and sampled NMR rows are active for the current executed OGS candidate where usable observation times and required model quantities are covered.",
            "NMR is the first active state residual, but the generated bound-water sensitivity audit rules out treating raw absolute theta as a naive saturation residual.",
            "ERT and Taupe/TDR remain diagnostic until their support/calibration choices are confirmed.",
            "RH currently audits boundary-condition provenance and candidate-envelope uncertainty rather than acting as a cell residual.",
        ],
    }
    return likelihood, summary


def write_markdown(path: Path, likelihood: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# Measurement Likelihood And Activation Model",
        "",
        "This file records how each measurement stream should enter the inversion objective.",
        "It is deliberately stricter than a data inventory: a row can be present and mapped",
        "but still inactive if the measurement physics, support, or uncertainty model is not",
        "defensible yet.",
        "",
        f"- Measurement streams: {summary['measurement_streams']}",
        f"- Streams active in the objective now: {summary['active_streams_now']}",
        f"- Total current objective rows: {summary['total_current_objective_rows']}",
        f"- Current candidate total active objective: {summary.get('current_candidate_total_active_objective')}",
        "",
        "| Stream | Activation state | Residual / transform | Scale / weighting | Activation gate |",
        "| --- | --- | --- | --- | --- |",
    ]
    for _, row in likelihood.iterrows():
        residual = f"{row['residual_definition']}; {row['residual_transform']}"
        scale = f"{row['likelihood_scale']}; {row['weighting_rule']}"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["measurement_stream"]),
                    str(row["activation_state"]),
                    residual.replace("|", "/"),
                    scale.replace("|", "/"),
                    str(row["activation_gate"]).replace("|", "/"),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Stream Details", ""])
    for _, row in likelihood.iterrows():
        lines.extend(
            [
                f"### {row['measurement_stream']}",
                "",
                f"- Candidate rows: {int(row['candidate_rows'])}",
                f"- Usable or mapped rows: {int(row['usable_or_mapped_rows'])}",
                f"- Current objective rows: {int(row['current_objective_rows'])}",
                f"- Model link: {row['model_link']}",
                f"- Prediction quantity: {row['prediction_quantity']}",
                f"- Bias/model-error terms: {row['bias_or_model_error_terms']}",
                f"- Current artifacts: `{row['current_artifacts']}`",
                f"- Source basis: {row['source_basis']}",
                f"- Notes: {row['notes']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Practical Consequences",
            "",
            "- Do not convert every prepared target row into an active residual automatically.",
            "- Keep direct permeability in log-space because the measurement and parameter range span orders of magnitude.",
            "- Treat NMR absolute water content as biased unless a free-water/bound-water correction is accepted.",
            "- Treat ERT and Taupe/TDR as forward observation operators, not direct saturation or permeability measurements.",
            "- Treat RH as boundary-condition evidence unless the boundary curve generation is reconstructed.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    likelihood, summary = build_rows(args)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    likelihood.to_csv(args.output_csv, index=False)
    args.output_json.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(args.output_md, likelihood, summary)
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(f"measurement streams: {summary['measurement_streams']}")
    print(f"active streams now: {summary['active_streams_now']}")


if __name__ == "__main__":
    main()
