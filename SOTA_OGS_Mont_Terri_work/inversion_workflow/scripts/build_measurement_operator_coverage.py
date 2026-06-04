#!/usr/bin/env python3
"""Build a coverage audit for how each measurement stream enters the OGS workflow."""

from __future__ import annotations

import argparse
import json
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
        "--manifest-summary",
        type=Path,
        default=Path("inversion_workflow/processed_observations/manifest_summary.csv"),
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
    parser.add_argument("--run-input-audit", type=Path, help="Override candidate OGS run-input audit JSON.")
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/measurement_operator_coverage.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/measurement_operator_coverage_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/measurement_operator_coverage.md"),
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def row_count(path: Path) -> int:
    if not path.exists():
        return 0
    return int(pd.read_csv(path, usecols=[0]).shape[0])


def family_count(frame: pd.DataFrame, family: str) -> int:
    if frame.empty or "observation_family" not in frame.columns:
        return 0
    return int(frame["observation_family"].eq(family).sum())


def family_true_count(frame: pd.DataFrame, family: str, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    subset = frame[frame["observation_family"].eq(family)]
    return int(subset[column].astype(str).str.lower().isin({"true", "1", "yes"}).sum())


def sample_count(samples: pd.DataFrame, target_ids: pd.Series) -> int:
    if samples.empty or target_ids.empty:
        return 0
    return int(samples["target_id"].isin(set(target_ids.astype(str))).sum())


def mesh_lookup_status_count(mesh_summary: dict[str, Any], table: str, status: str) -> int | str:
    return (
        mesh_summary.get("generated", {})
        .get(table, {})
        .get("lookup_status", {})
        .get(status, "n/a")
    )


def add_manifest_context(row: dict[str, Any], manifest: pd.DataFrame) -> dict[str, Any]:
    match = manifest[manifest["observation_id"].eq(row["observation_id"])]
    if match.empty:
        return row
    item = match.iloc[0]
    row.setdefault("measurement_type", item["measurement_type"])
    row["manifest_model_role"] = item["model_role"]
    row["manifest_primary_quantity"] = item["primary_quantity"]
    row["manifest_model_quantity"] = item["model_quantity"]
    row["manifest_check_count"] = int(item["check_count"])
    row["manifest_check_types"] = item["check_types"]
    return row


def build_rows(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    processed = args.processed_dir
    manifest = pd.read_csv(args.manifest_summary)
    targets = pd.read_csv(processed / "state_observation_targets.csv")
    samples = pd.read_csv(processed / "state_observation_samples.csv")
    perm_summary = read_json(processed / "permeability_target_summary.json")
    state_summary = read_json(processed / "state_observation_target_summary.json")
    mesh_summary = read_json(processed / "mesh_lookup_summary.json")
    ert_operator = read_json(processed / "ert_observation_operator_summary.json")
    ert_projection = read_json(processed / "ert_spatial_projection_summary.json")
    ert_diagnostic = read_json(
        Path("inversion_workflow/runs/direct_fit_observation_run/ert_resistivity_diagnostic_summary.json")
    )
    ert_discrimination = read_json(Path("inversion_workflow/ert_candidate_discrimination_summary.json"))
    ert_support_sensitivity = read_json(Path("inversion_workflow/ert_support_sensitivity_summary.json"))
    taupe_operator = read_json(processed / "taupe_tdr_observation_operator_summary.json")
    taupe_diagnostic = read_json(
        Path("inversion_workflow/runs/direct_fit_observation_run/taupe_tdr_trend_diagnostic_summary.json")
    )
    taupe_discrimination = read_json(Path("inversion_workflow/taupe_candidate_discrimination_summary.json"))
    taupe_weight_sensitivity = read_json(Path("inversion_workflow/taupe_series_weight_sensitivity_summary.json"))
    nmr_bias_sensitivity = read_json(Path("inversion_workflow/nmr_candidate_bias_sensitivity_summary.json"))
    other_hm_summary = read_json(processed / "other_hm_monitoring_summary.json")
    other_hm_missing = read_json(processed / "other_hm_missing_numeric_request_summary.json")
    other_hm_source_audit = read_json(processed / "other_hm_numeric_source_audit_summary.json")
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
    ogs_environment = read_json(Path("inversion_workflow/OGS_ENVIRONMENT_AUDIT.json"))
    candidate = read_json(args.candidate_summary)
    candidate_id = candidate.get("run_id") or args.candidate_summary.parent.name
    candidate_combined = (
        read_json(args.combined_summary)
        if args.combined_summary
        else candidate.get("combined_summary", {})
    )
    candidate_permeability = (
        read_json(args.permeability_summary)
        if args.permeability_summary
        else candidate.get("permeability_summary", {})
    )
    candidate_state = read_json(args.state_summary) if args.state_summary else candidate.get("state_summary", {})
    candidate_run_input = (
        read_json(args.run_input_audit)
        if args.run_input_audit
        else candidate.get("run_input_audit", {})
    )
    rh_boundary = (
        read_json(args.rh_boundary_summary)
        if args.rh_boundary_summary
        else candidate.get("rh_boundary_summary", {})
    )

    nmr_targets = targets[targets["observation_family"].isin(["NMR weekly", "NMR seasonal"])]
    nmr_target_ids = nmr_targets["target_id"].astype(str)
    active_nmr_rows = int(candidate_state.get("used_in_objective_rows", 0) or 0)
    active_nmr_objective = candidate_state.get("objective_value", np.nan)
    taupe_targets = targets[targets["observation_family"].eq("Taupe/TDR")]
    taupe_target_ids = taupe_targets["target_id"].astype(str)

    rows: list[dict[str, Any]] = [
        {
            "observation_id": "ert_open_time_series",
            "measurement_type": "ERT",
            "raw_or_processed_rows": row_count(processed / "ert_timesteps.csv"),
            "target_rows": family_count(targets, "ERT open-niche time series"),
            "sample_rows": row_count(processed / "ert_spatial_projection_lookup.csv"),
            "mapped_or_usable_rows": int(ert_projection.get("ready_for_residual_after_ogs_output_rows", 0)),
            "active_objective_rows": 0,
            "active_objective_value": np.nan,
            "coverage_status": "resistivity_diagnostic_generated_transform_support_unconfirmed",
            "current_model_use": (
                "ERT timesteps are inventoried and matched to VTK files; theta-to-resistivity "
                "calibration and an ERT-cell to OGS-cell projection lookup now exist. A direct-run "
                f"log-resistivity diagnostic compares {ert_diagnostic.get('compared_rows', 'n/a')} "
                f"cell-time rows across {ert_diagnostic.get('compared_output_times', 'n/a')} output "
                "times. The cross-run audit spans "
                f"{ert_discrimination.get('run_count', 'n/a')} executed OGS runs and finds an ERT-MAE "
                f"range of {ert_discrimination.get('ert_mae_log10_range', 'n/a')} log10 units, but "
                "a support-sensitivity audit now quantifies the ranking changes across tighter radial "
                f"subsets for {ert_support_sensitivity.get('run_count', 'n/a')} selected runs. "
                "Coordinate/support assumptions and an uncertainty model are still needed before assigning "
                "residual weights."
            ),
            "blocking_next_step": "Confirm the ERT-to-OGS coordinate transform, exact near-niche support mask, and ERT uncertainty/correlation model before converting the diagnostic into weighted objective residuals.",
            "evidence_files": "ert_timesteps.csv; ert_archive_inventory.csv; ert_nmr_resistivity_pairs.csv; ert_water_content_resistivity_operator.csv; ert_spatial_projection_lookup.csv; ert_spatial_projection_operator.md; state_observation_targets.csv; direct_fit_observation_run/ert_resistivity_diagnostic.md; ert_candidate_discrimination.md; ert_support_sensitivity.md",
            "audit_detail": (
                "ERT operator status: "
                f"{ert_operator.get('status', 'not_built')}; default relation "
                f"{ert_operator.get('recommended_relation_id', 'n/a')}; projection status "
                f"{ert_projection.get('status', 'not_built')}; projection-ready rows "
                f"{ert_projection.get('ready_for_residual_after_ogs_output_rows', 'n/a')}; "
                f"diagnostic status {ert_diagnostic.get('status', 'not_built')}; "
                f"diagnostic compared rows {ert_diagnostic.get('compared_rows', 'n/a')}; "
                f"diagnostic log10 MAE {ert_diagnostic.get('area_weighted_residual_log10', {}).get('mae', 'n/a')}; "
                f"diagnostic log10 RMSE {ert_diagnostic.get('area_weighted_residual_log10', {}).get('rmse', 'n/a')}; "
                f"cross-run audited runs {ert_discrimination.get('run_count', 'n/a')}; "
                f"cross-run ERT MAE range {ert_discrimination.get('ert_mae_log10_range', 'n/a')}; "
                f"best active-objective ERT MAE {ert_discrimination.get('best_combined_ert_mae_log10', 'n/a')}; "
                f"combined-objective/ERT-MAE correlation {ert_discrimination.get('combined_objective_ert_mae_correlation', 'n/a')}; "
                f"support-sensitivity runs {ert_support_sensitivity.get('run_count', 'n/a')}; "
                f"support variants {ert_support_sensitivity.get('support_variant_count', 'n/a')}; "
                f"best mean support-rank run {ert_support_sensitivity.get('best_mean_support_rank', {}).get('run_id', 'n/a')}."
            ),
        },
        {
            "observation_id": "nmr_weekly_and_seasonal",
            "measurement_type": "NMR",
            "raw_or_processed_rows": row_count(processed / "nmr_weekly.csv") + row_count(processed / "nmr_seasonal_profiles.csv"),
            "target_rows": int(nmr_targets.shape[0]),
            "sample_rows": sample_count(samples, nmr_target_ids),
            "mapped_or_usable_rows": family_true_count(targets, "NMR weekly", "usable_for_current_state_fit")
            + family_true_count(targets, "NMR seasonal", "usable_for_current_state_fit"),
            "active_objective_rows": active_nmr_rows,
            "active_objective_value": active_nmr_objective,
            "coverage_status": (
                "active_state_residual_from_sampled_ogs_outputs"
                if active_nmr_rows
                else "state_residual_ready_pending_ogs"
            ),
            "current_model_use": (
                "NMR water-content targets are mapped to OGS lookup cells and compared "
                "with theta = porosity*saturation where sampled OGS outputs cover the "
                "target time and fixed porosity support. A cross-run bias/anomaly audit "
                f"spans {nmr_bias_sensitivity.get('run_count', 'n/a')} executed runs and shows "
                "that the current raw absolute-theta ranking is conditional on the unresolved "
                "bound/interlayer-water treatment."
            ),
            "blocking_next_step": "Retain the bound/interlayer-water uncertainty term; treat raw absolute NMR ranking as conditional until label-bias or trend/anomaly residuals are accepted.",
            "evidence_files": "nmr_weekly.csv; nmr_seasonal_profiles.csv; state_observation_targets.csv; state_observation_samples.csv; nmr_bound_water_sensitivity.md; nmr_candidate_bias_sensitivity.md",
            "audit_detail": (
                f"NMR bias/anomaly runs {nmr_bias_sensitivity.get('run_count', 'n/a')}; "
                f"best current run {nmr_bias_sensitivity.get('best_current_combined', {}).get('run_id', 'n/a')}; "
                f"best label-bias run {nmr_bias_sensitivity.get('best_label_bias_combined', {}).get('run_id', 'n/a')}; "
                f"best trend/anomaly run {nmr_bias_sensitivity.get('best_trend_anomaly_combined', {}).get('run_id', 'n/a')}; "
                f"current-vs-label-bias rank correlation {nmr_bias_sensitivity.get('current_vs_label_bias_rank_correlation', 'n/a')}."
            ),
        },
        {
            "observation_id": "permeability_pulse_tests",
            "measurement_type": "permeability_pulse_tests",
            "raw_or_processed_rows": row_count(processed / "permeability_interpreted_values.csv"),
            "target_rows": int(perm_summary.get("target_rows", 0)),
            "sample_rows": int(perm_summary.get("target_cell_rows", 0)),
            "mapped_or_usable_rows": int(perm_summary.get("usable_for_current_ogs_fit", 0)),
            "active_objective_rows": int(candidate_permeability.get("used_in_objective_rows", 0)),
            "active_objective_value": candidate_permeability.get("objective_value"),
            "coverage_status": "active_parameter_objective",
            "current_model_use": (
                "Pulse-test rows form the active direct log-permeability objective; "
                f"the current run-ready smooth candidate `{candidate_id}` has objective "
                f"{candidate_permeability.get('objective_value', float('nan')):.2f}. "
                f"{int(perm_summary.get('missing_segment_geometry', 0))} older rows are retained "
                "in a missing-geometry audit with orientation evidence but no cell projection."
            ),
            "blocking_next_step": "Use an optimizer or sampler over the combined objective before accepting a final fitted permeability field.",
            "evidence_files": "permeability_observation_targets.csv; permeability_observation_cells.csv; permeability_missing_geometry_audit.csv; smooth_permeability_candidate_search/SMOOTH_FIT_SUMMARY.json; candidate_smooth_0p025m_search_driver/permeability_fit_summary.json",
        },
        {
            "observation_id": "taupe_tdr_edz_bands",
            "measurement_type": "Taupe/TDR",
            "raw_or_processed_rows": row_count(processed / "taupe_tdr_bands.csv"),
            "target_rows": family_count(targets, "Taupe/TDR"),
            "sample_rows": sample_count(samples, taupe_target_ids),
            "mapped_or_usable_rows": int(targets["target_status"].eq("mapped_band_samples").sum()),
            "active_objective_rows": 0,
            "active_objective_value": np.nan,
            "coverage_status": "trend_operator_ready_absolute_calibration_pending",
            "current_model_use": (
                "Taupe/TDR band targets are mapped to borehole line-sample bands and "
                "have a baseline-normalized trend operator. The direct reference run now "
                f"compares {taupe_diagnostic.get('compared_rows', 'n/a')} mapped A3/A4 "
                "trend rows against sampled OGS theta as a diagnostic; absolute saturation "
                "residuals still need a confirmed Taupe unit/calibration. The cross-run "
                f"audit spans {taupe_discrimination.get('run_count', 'n/a')} sampled OGS "
                f"runs and finds a Taupe-MAE range of {taupe_discrimination.get('taupe_mae_range', 'n/a')}, "
                "so Taupe is currently a weak discriminator for this candidate family. A series-weight audit "
                f"now checks {taupe_weight_sensitivity.get('compared_series_count', 'n/a')} compared A3/A4 "
                f"series across {taupe_weight_sensitivity.get('run_count', 'n/a')} runs."
            ),
            "blocking_next_step": "Use the generated trend diagnostic to judge candidate behaviour; confirm Taupe unit/calibration and uncertainty before assigning absolute residual weights.",
            "evidence_files": "taupe_tdr_bands.csv; taupe_tdr_trend_operator.csv; taupe_tdr_observation_operator.md; borehole_line_mesh_samples.csv; state_observation_targets.csv; state_observation_samples.csv; direct_fit_observation_run/taupe_tdr_trend_diagnostic.md; taupe_candidate_discrimination.md; taupe_series_weight_sensitivity.md",
            "audit_detail": (
                "Taupe operator status: "
                f"{taupe_operator.get('status', 'not_built')}; mapped trend rows "
                f"{taupe_operator.get('mapped_trend_operator_rows', 'n/a')}; "
                f"diagnostic compared rows {taupe_diagnostic.get('compared_rows', 'n/a')}; "
                f"diagnostic status counts {taupe_diagnostic.get('diagnostic_status_counts', {})}; "
                f"cross-run audited runs {taupe_discrimination.get('run_count', 'n/a')}; "
                f"cross-run Taupe MAE range {taupe_discrimination.get('taupe_mae_range', 'n/a')}; "
                f"best active-objective Taupe MAE {taupe_discrimination.get('best_combined_taupe_mae', 'n/a')}; "
                f"series-weight sensitivity runs {taupe_weight_sensitivity.get('run_count', 'n/a')}; "
                f"compared series {taupe_weight_sensitivity.get('compared_series_count', 'n/a')}; "
                f"distinct per-series winners {taupe_weight_sensitivity.get('series_best_run_distinct_count', 'n/a')}; "
                f"best mean weighting-rank run {taupe_weight_sensitivity.get('best_mean_weighting_rank', {}).get('run_id', 'n/a')}; "
                "candidate physical rows "
                f"{taupe_operator.get('candidate_absolute_interpretation_physical_rows', {})}."
            ),
        },
        {
            "observation_id": "suction_relative_humidity_open_twin",
            "measurement_type": "suction_relative_humidity",
            "raw_or_processed_rows": row_count(processed / "rh_open_twin_kelvin.csv"),
            "target_rows": family_count(targets, "Suction/RH"),
            "sample_rows": 0,
            "mapped_or_usable_rows": family_true_count(targets, "Suction/RH", "usable_for_current_state_fit"),
            "active_objective_rows": 0,
            "active_objective_value": np.nan,
            "coverage_status": "boundary_forcing_audited_not_point_residual",
            "current_model_use": (
                "RH is converted to Kelvin liquid pressure and audited against the "
                "active open-niche OGS boundary curve. Local RH-derived candidate boundary "
                f"curves now exist ({rh_candidate_curves.get('candidate_count', 0)} policies; "
                f"preferred {rh_candidate_curves.get('preferred_policy_candidate', 'n/a')}), "
                f"and the candidate-envelope audit finds the active curve outside the local "
                f"RH-derived envelope on {rh_uncertainty.get('active_curve_outside_envelope_count', 'n/a')} "
                "overlap dates. "
                "RH is not treated as a point residual or verified replacement forcing."
            ),
            "blocking_next_step": str(
                rh_provenance.get(
                    "remaining_blocker",
                    "Confirm provenance/preprocessing of 08_08_open_niche_seasonal.xml because the RH audit shows a large curve mismatch.",
                )
            ),
            "evidence_files": (
                "rh_open_twin_kelvin.csv; rh_boundary_curve_audit_summary.json; "
                "rh_measurement_semantics_summary.json; rh_boundary_provenance_request.md; "
                "rh_boundary_provenance_request.csv; rh_boundary_candidate_curves.md; "
                "rh_boundary_candidate_curve_summary.json; rh_boundary_uncertainty.md; "
                "rh_boundary_uncertainty_summary.json; state_observation_targets.csv"
            ),
            "audit_detail": (
                f"RH audit compared {rh_boundary.get('compared_rows', 0)} rows; "
                f"median absolute residual {rh_boundary.get('overall_abs_residual_mpa', {}).get('median', float('nan')):.2f} MPa; "
                f"provenance request rows {rh_provenance.get('request_rows', 0)}; "
                f"evidence rows {rh_provenance.get('evidence_rows', 0)}; "
                f"candidate curves {rh_candidate_curves.get('candidate_count', 0)}; "
                f"preferred candidate {rh_candidate_curves.get('preferred_policy_candidate', 'n/a')} "
                f"MAE {rh_preferred_curve.get('overlap_abs_residual_mpa_mae', 'n/a')} MPa; "
                f"uncertainty envelope dates {rh_uncertainty.get('envelope_date_count', 'n/a')}; "
                f"overlap pressure-range p50 "
                f"{rh_uncertainty.get('overlap', {}).get('pressure_range_mpa', {}).get('p50', 'n/a')} MPa; "
                f"active outside envelope "
                f"{rh_uncertainty.get('active_curve_outside_envelope_count', 'n/a')}; "
                f"active curve date span {rh_provenance.get('active_curve_date_min', 'n/a')} to "
                f"{rh_provenance.get('active_curve_date_max', 'n/a')}."
            ),
        },
        {
            "observation_id": "coordinates_and_geometry",
            "measurement_type": "coordinates_geometry_layout",
            "raw_or_processed_rows": row_count(processed / "measurement_coordinates_xy.csv") + row_count(processed / "borehole_coordinates.csv"),
            "target_rows": 0,
            "sample_rows": row_count(processed / "measurement_mesh_lookup.csv")
            + row_count(processed / "borehole_mesh_lookup.csv")
            + row_count(processed / "borehole_line_mesh_samples.csv"),
            "mapped_or_usable_rows": row_count(processed / "measurement_mesh_lookup.csv"),
            "active_objective_rows": 0,
            "active_objective_value": np.nan,
            "coverage_status": "support_layer_ready",
            "current_model_use": "Coordinates drive measurement-to-mesh lookup and borehole/Taupe interval sampling.",
            "blocking_next_step": "Add missing endpoint geometry for older permeability intervals if those rows should enter the same target format.",
            "evidence_files": "measurement_coordinates_xy.csv; borehole_coordinates.csv; measurement_mesh_lookup.csv; borehole_line_mesh_samples.csv",
            "audit_detail": (
                "Mesh lookup outside point count: "
                f"{mesh_lookup_status_count(mesh_summary, 'measurement_mesh_lookup.csv', 'outside_mesh_bbox_nearest_cell')}."
            ),
        },
        {
            "observation_id": "bedding_structure",
            "measurement_type": "bedding_geology_structure",
            "raw_or_processed_rows": 0,
            "target_rows": 0,
            "sample_rows": 0,
            "mapped_or_usable_rows": 0,
            "active_objective_rows": 0,
            "active_objective_value": np.nan,
            "coverage_status": "structural_prior_ready",
            "current_model_use": "Bedding/geology gives the anisotropy-angle prior and structural caveats for local anomalies.",
            "blocking_next_step": "Decide whether future optimization should release anisotropy angle spatially or keep a global bedding-informed angle.",
            "evidence_files": "bedding_geology_structure source files; run_config.example.json; direct_permeability_prior_sweep/SWEEP_SUMMARY.json",
        },
        {
            "observation_id": "model_projection_inputs",
            "measurement_type": "model_projection_inputs",
            "raw_or_processed_rows": row_count(processed / "ogs_bulk_mesh_cells.csv"),
            "target_rows": 0,
            "sample_rows": 0,
            "mapped_or_usable_rows": row_count(processed / "ogs_bulk_mesh_cells.csv"),
            "active_objective_rows": 0,
            "active_objective_value": np.nan,
            "coverage_status": "workflow_support_ready",
            "current_model_use": (
                "Projection inputs provide the mesh-field injection path for n_rd and k_i_rd "
                "without changing OGS equations. The OGS environment audit status is "
                f"{ogs_environment.get('status', 'not_run')}; the current candidate run-input "
                f"audit status is {candidate_run_input.get('status', 'not_run')}."
            ),
            "blocking_next_step": "Use the collected OGS 6.5.4 SIF or host OGS executable for candidate comparisons, and verify projected boundary subdomains for production runs.",
            "evidence_files": "GESA_model_original/projection_on_mesh_2025-09-05; prepare_ogs_run.py; evaluate_inversion_candidate.py; OGS_ENVIRONMENT_AUDIT.json; OGS_RUN_INPUT_AUDIT.json",
            "audit_detail": (
                "OGS environment audit status: "
                f"{ogs_environment.get('status', 'not_run')}; selected executable "
                f"{ogs_environment.get('selected_executable') or 'none'}; selected container "
                f"{ogs_environment.get('selected_container') or 'none'}; runtime "
                f"{ogs_environment.get('runtime_status', {}).get('preferred_container_runtime') or 'none'}. "
                "Current candidate run-input audit status: "
                f"{candidate_run_input.get('status', 'not_run')}."
            ),
        },
        {
            "observation_id": "other_hm_monitoring",
            "measurement_type": "other_hm_monitoring",
            "raw_or_processed_rows": row_count(processed / "other_hm_visualisation_zones.csv")
            + row_count(processed / "other_hm_visualisation_text_labels.csv"),
            "target_rows": row_count(processed / "other_hm_qualitative_targets.csv")
            + row_count(processed / "other_hm_levelling_displacements.csv"),
            "sample_rows": row_count(processed / "other_hm_visualisation_zones.csv"),
            "mapped_or_usable_rows": int(other_hm_summary.get("model_facing_rows", 0)),
            "active_objective_rows": 0,
            "active_objective_value": np.nan,
            "coverage_status": "layout_and_qualitative_targets_ready_numeric_series_missing",
            "current_model_use": (
                "Other HM monitoring now has structured Tecplot layout zones, levelling "
                "summary rows, qualitative validation gates, a missing-export request "
                "package, and a numeric source audit. The source audit found "
                f"{other_hm_source_audit.get('hard_residual_ready_request_count', 'n/a')} "
                "hard-residual-ready request classes, so this stream remains outside "
                "the active objective until Geoscope and laser-scan numeric exports are located."
            ),
            "blocking_next_step": str(
                other_hm_missing.get(
                    "remaining_blocker",
                    other_hm_summary.get(
                    "remaining_blocker",
                    "Locate Geoscope mini-piezometer/extensometer/crackmeter time-series exports and laser-scan statistical interpretation files.",
                    ),
                )
            ),
            "evidence_files": (
                "other_hm_visualisation_zones.csv; other_hm_levelling_displacements.csv; "
                "other_hm_qualitative_targets.csv; other_hm_monitoring.md; "
                "other_hm_missing_numeric_request.md; other_hm_missing_numeric_request.csv; "
                "other_hm_numeric_source_audit.md; other_hm_numeric_source_audit_summary.json"
            ),
            "audit_detail": (
                "Other-HM inventory status: "
                f"{other_hm_summary.get('status', 'not_built')}; "
                f"{other_hm_summary.get('zone_rows', 0)} Tecplot zones, "
                f"{other_hm_summary.get('levelling_rows', 0)} levelling rows, "
                f"{other_hm_summary.get('qualitative_target_rows', 0)} qualitative targets; "
                f"{other_hm_missing.get('request_rows', 0)} missing-export request rows; "
                f"numeric source audit hard-ready requests "
                f"{other_hm_source_audit.get('hard_residual_ready_request_count', 'n/a')}; "
                f"support-ready requests "
                f"{other_hm_source_audit.get('local_support_ready_request_count', 'n/a')}; "
                f"zip numeric-candidate members "
                f"{other_hm_source_audit.get('source_bundle', {}).get('zip_member_numeric_candidate_count', 'n/a')}."
            ),
        },
    ]

    rows = [add_manifest_context(row, manifest) for row in rows]
    coverage = pd.DataFrame(rows)
    status_counts = {str(key): int(value) for key, value in coverage["coverage_status"].value_counts().to_dict().items()}
    summary = {
        "observation_groups": int(coverage.shape[0]),
        "active_objective_groups": int(coverage["active_objective_rows"].gt(0).sum()),
        "coverage_status_counts": status_counts,
        "state_target_rows": int(state_summary.get("target_rows", 0)),
        "state_sample_rows": int(candidate_state.get("state_sample_rows", state_summary.get("sample_rows", 0)) or 0),
        "state_lookup_rows": int(state_summary.get("sample_rows", 0)),
        "direct_permeability_target_rows": int(perm_summary.get("target_rows", 0)),
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
        "current_candidate_summary": str(args.candidate_summary),
        "current_candidate_total_active_objective": candidate_combined.get("total_active_objective_value"),
        "notes": [
            "Coverage status describes current model-entry readiness, not scientific sufficiency.",
            "Use measurement_likelihood_model.md for residual transforms, scales, bias terms, and activation gates.",
            "Direct permeability pulse tests and sampled NMR rows currently contribute finite objective rows for the current executed OGS candidate.",
            "Taupe/TDR, ERT and RH are represented, but remain diagnostic or boundary-forcing streams pending support/calibration/provenance choices.",
        ],
    }
    return coverage, summary


def write_markdown(path: Path, coverage: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# Measurement Operator Coverage Audit",
        "",
        "This file summarizes how each collected measurement stream currently enters the frozen OGS workflow.",
        "",
        f"- Observation groups: {summary['observation_groups']}",
        f"- Groups with active objective rows now: {summary['active_objective_groups']}",
        f"- Current candidate total active objective: {summary.get('current_candidate_total_active_objective')}",
        "",
        "| Measurement stream | Coverage status | Current model use | Rows/targets/samples | Next blocker |",
        "| --- | --- | --- | --- | --- |",
    ]
    for _, row in coverage.iterrows():
        counts = (
            f"processed {int(row['raw_or_processed_rows'])}; "
            f"targets {int(row['target_rows'])}; samples {int(row['sample_rows'])}; "
            f"usable/mapped {int(row['mapped_or_usable_rows'])}; active objective {int(row['active_objective_rows'])}"
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["measurement_type"]),
                    str(row["coverage_status"]),
                    str(row["current_model_use"]).replace("|", "/"),
                    counts,
                    str(row["blocking_next_step"]).replace("|", "/"),
                ]
            )
            + " |"
        )
    audit_details = coverage.dropna(subset=["audit_detail"]) if "audit_detail" in coverage.columns else pd.DataFrame()
    if not audit_details.empty:
        lines.extend(["", "## Audit Details", ""])
        for _, row in audit_details.iterrows():
            detail = str(row["audit_detail"]).strip()
            if detail and detail.lower() != "nan":
                lines.append(f"- `{row['measurement_type']}`: {detail}")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Active objective rows currently come from direct permeability pulse-test targets and sampled NMR state targets.",
            "- Residual transforms, likelihood scales, model-error terms, and activation gates are tracked separately in `measurement_likelihood_model.md`.",
            "- NMR state-observation rows activate only where sampled OGS outputs cover usable observation times and fixed support quantities.",
            "- ERT now has theta-to-resistivity calibration, a spatial lookup artifact, a direct-run log-resistivity diagnostic, a cross-run candidate discrimination audit, and a support-sensitivity audit, but still needs coordinate/support/uncertainty confirmation before numerical residual weights are assigned.",
            "- Taupe/TDR now has a baseline-normalized trend operator, cross-run discrimination audit, and series-weight sensitivity audit; absolute saturation residuals still need explicit unit/calibration choices.",
            "- RH now has local RH-derived candidate boundary curves, XML snippets, and a candidate-envelope uncertainty audit, but the active curve provenance and extension policy still need confirmation before replacement forcing or retention likelihood use.",
            "- Other HM monitoring now has a structured layout/qualitative layer, levelling summary rows, and a missing-export request package; Geoscope and laser-scan raw exports are still needed for hard residuals.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    coverage, summary = build_rows(args)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    coverage.to_csv(args.output_csv, index=False)
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(args.output_md, coverage, summary)
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(f"observation groups: {summary['observation_groups']}")


if __name__ == "__main__":
    main()
