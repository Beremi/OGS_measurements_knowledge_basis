#!/usr/bin/env python3
"""Screen structural and EDZ-shaped permeability field families.

The active production sampler is currently paused because smooth magnitude,
local-basis, local tensor-anisotropy, and cross-stream hybrid screens did not
identify a clearly better follow-up family for the active objective.  This script
adds one cheap, geometry-aware screen before spending more OGS runs: it applies
run-local log10 permeability multipliers shaped as central EDZ caps/shells,
bedding-parallel bands, and broad open-twin pulse-test corridors.

The score is the direct permeability pulse-test layer only.  Candidate meshes do
not modify the frozen source model and are not final inversion evidence until the
existing OGS candidate harness evaluates state outputs and release gates.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import meshio
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_permeability_targets import evaluate_targets, weighted_prediction  # noqa: E402
from fit_smooth_permeability_field_from_targets import (  # noqa: E402
    cell_centroids,
    eigenvalue_limited_scale,
    make_cell_data,
    read_cell_field,
)


DEFAULT_AMPLITUDES = [-1.0, -0.5, 0.5, 1.0, 1.5, 2.0]
BEDDING_THETA_DEG = 144.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-mesh",
        type=Path,
        default=Path("inversion_workflow/current_permeability_field/current_best_bulk_w_projections.vtu"),
        help="Current active/package mesh containing the tensor field to perturb.",
    )
    parser.add_argument(
        "--targets",
        type=Path,
        default=Path("inversion_workflow/processed_observations/permeability_observation_targets.csv"),
    )
    parser.add_argument(
        "--target-cells",
        type=Path,
        default=Path("inversion_workflow/processed_observations/permeability_observation_cells.csv"),
    )
    parser.add_argument(
        "--line-samples",
        type=Path,
        default=Path("inversion_workflow/processed_observations/borehole_line_mesh_samples.csv"),
    )
    parser.add_argument(
        "--ert-lookup",
        type=Path,
        default=Path("inversion_workflow/processed_observations/ert_spatial_projection_lookup.csv"),
    )
    parser.add_argument(
        "--current-field-summary",
        type=Path,
        default=Path("inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD_SUMMARY.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/runs/structural_edz_field_family_plan"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/structural_edz_field_family_plan"),
    )
    parser.add_argument("--field-name", default="k_i_rd")
    parser.add_argument("--magnitude-field-name", default="k_mag_rd")
    parser.add_argument("--amplitudes", type=float, nargs="*", default=DEFAULT_AMPLITUDES)
    parser.add_argument("--log10-sigma", type=float, default=0.5)
    parser.add_argument("--min-k-eigenvalue", type=float, default=1.0e-22)
    parser.add_argument("--max-k-eigenvalue", type=float, default=1.0e-12)
    parser.add_argument("--max-proposals", type=int, default=18)
    parser.add_argument("--batch-size", type=int, default=3)
    parser.add_argument(
        "--direct-improvement-threshold",
        type=float,
        default=0.25,
        help="Minimum objective decrease required before recommending OGS follow-up.",
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def resolve(repo: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo / path


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


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def safe_label(value: str) -> str:
    output = []
    for char in value.lower():
        if char.isalnum():
            output.append(char)
        elif char in {".", "-"}:
            output.append("p" if char == "." else "m")
        else:
            output.append("_")
    label = "".join(output).strip("_")
    while "__" in label:
        label = label.replace("__", "_")
    return label or "shape"


def format_number(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}".rstrip("0").rstrip(".").replace(".", "p").replace("-", "m")


def tensor_geometric_magnitude(field: np.ndarray) -> np.ndarray:
    if field.ndim == 1 or field.shape[1] == 1:
        magnitude = np.asarray(field, dtype=float).reshape(-1)
    elif field.shape[1] == 4:
        determinant = field[:, 0] * field[:, 3] - field[:, 1] * field[:, 2]
        magnitude = np.sqrt(np.clip(determinant, 1.0e-300, np.inf))
    else:
        raise ValueError(f"{field.shape} is not a scalar or 2D tensor field")
    if np.any(magnitude <= 0.0) or not np.isfinite(magnitude).all():
        raise ValueError("permeability magnitude must be positive and finite")
    return magnitude


def read_material_ids(mesh: meshio.Mesh) -> np.ndarray:
    if not mesh.cells:
        raise ValueError("mesh contains no cells")
    cell_type = mesh.cells[0].type
    try:
        values = mesh.cell_data_dict["MaterialIDs"][cell_type]
    except KeyError:
        return np.full(mesh.cells[0].data.shape[0], -1, dtype=int)
    return np.asarray(values, dtype=int).reshape(-1)


def normalize_shape(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    values = np.where(np.isfinite(values) & (values > 0.0), values, 0.0)
    maximum = float(np.max(values)) if values.size else 0.0
    if maximum <= 0.0:
        return values
    output = values / maximum
    output[output < 1.0e-8] = 0.0
    return output


def point_distance_to_polyline(points: np.ndarray, polyline: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return distance to nearest polyline segment and distance along that segment."""
    if polyline.shape[0] == 0:
        return (
            np.full(points.shape[0], math.inf, dtype=float),
            np.full(points.shape[0], math.nan, dtype=float),
        )
    if polyline.shape[0] == 1:
        distances = np.linalg.norm(points - polyline[0], axis=1)
        return distances, np.zeros(points.shape[0], dtype=float)

    best_distance = np.full(points.shape[0], math.inf, dtype=float)
    best_along = np.zeros(points.shape[0], dtype=float)
    cumulative = 0.0
    for start, end in zip(polyline[:-1], polyline[1:]):
        segment = end - start
        length = float(np.linalg.norm(segment))
        if length <= 0.0 or not np.isfinite(length):
            continue
        rel = points - start
        t = np.clip((rel @ segment) / (length**2), 0.0, 1.0)
        projection = start + t[:, None] * segment
        distance = np.linalg.norm(points - projection, axis=1)
        improved = distance < best_distance
        best_distance[improved] = distance[improved]
        best_along[improved] = cumulative + t[improved] * length
        cumulative += length
    return best_distance, best_along


def line_shape_data(line_samples_path: Path, centroids: np.ndarray) -> dict[str, dict[str, np.ndarray]]:
    if not line_samples_path.exists():
        return {}
    frame = pd.read_csv(line_samples_path)
    output: dict[str, dict[str, np.ndarray]] = {}
    for segment in ["BCD-A32", "BCD-A33"]:
        rows = frame[frame["segment_label"].astype(str).eq(segment)].copy()
        if rows.empty:
            continue
        rows = rows.sort_values("sample_index")
        polyline = rows[["lookup_x", "lookup_y"]].to_numpy(dtype=float)
        distances, along = point_distance_to_polyline(centroids, polyline)
        output[segment] = {
            "nearest_distance_m": distances,
            "distance_along_m": along,
            "line_length_m": np.full(centroids.shape[0], float(rows["segment_length_2d_m"].max())),
        }
    return output


def cell_support_features(
    mesh: meshio.Mesh,
    field: np.ndarray,
    centroids: np.ndarray,
    material_ids: np.ndarray,
    ert_lookup_path: Path,
    line_data: dict[str, dict[str, np.ndarray]],
) -> pd.DataFrame:
    radius = np.linalg.norm(centroids, axis=1)
    magnitude = tensor_geometric_magnitude(field)
    features = pd.DataFrame(
        {
            "cell_id": np.arange(centroids.shape[0], dtype=int),
            "material_id": material_ids,
            "centroid_x": centroids[:, 0],
            "centroid_y": centroids[:, 1],
            "radial_distance_from_origin_m": radius,
            "within_approx_1p5m_center_support": radius <= 1.5,
            "current_log10_k_geom_m2": np.log10(magnitude),
        }
    )
    if ert_lookup_path.exists():
        ert = pd.read_csv(ert_lookup_path)
        ready = ert[ert.get("ready_for_residual_after_ogs_output", False).map(bool_value)].copy()
        cell_counts = (
            pd.to_numeric(ready.get("ogs_lookup_cell_id", pd.Series(dtype=float)), errors="coerce")
            .dropna()
            .astype(int)
            .value_counts()
        )
        features["ert_ready_support_lookup_count"] = features["cell_id"].map(cell_counts).fillna(0).astype(int)
        features["inside_ert_ready_support_cells"] = features["ert_ready_support_lookup_count"] > 0
    else:
        features["ert_ready_support_lookup_count"] = 0
        features["inside_ert_ready_support_cells"] = False
    for segment, arrays in line_data.items():
        prefix = safe_label(segment)
        features[f"{prefix}_nearest_distance_m"] = arrays["nearest_distance_m"]
        features[f"{prefix}_distance_along_m"] = arrays["distance_along_m"]
    return features


def build_shapes(
    centroids: np.ndarray,
    features: pd.DataFrame,
    line_data: dict[str, dict[str, np.ndarray]],
) -> list[dict[str, Any]]:
    radius = features["radial_distance_from_origin_m"].to_numpy(dtype=float)
    shapes: list[dict[str, Any]] = []

    for cap_radius in [1.15, 1.30, 1.50]:
        for decay in [0.20, 0.40, 0.80]:
            raw = np.exp(-np.maximum(radius - cap_radius, 0.0) / decay)
            shapes.append(
                {
                    "family": "central_edz_cap_decay",
                    "shape_id": f"cap_r{format_number(cap_radius)}_d{format_number(decay)}",
                    "description": (
                        f"central EDZ cap with full weight inside r <= {cap_radius:.2f} m and "
                        f"exponential decay length {decay:.2f} m"
                    ),
                    "shape": normalize_shape(raw),
                    "cap_radius_m": cap_radius,
                    "decay_length_m": decay,
                }
            )

    for center in [0.85, 1.15, 1.45]:
        for width in [0.15, 0.30, 0.50]:
            raw = np.exp(-0.5 * ((radius - center) / width) ** 2)
            shapes.append(
                {
                    "family": "central_edz_shell",
                    "shape_id": f"shell_r{format_number(center)}_w{format_number(width)}",
                    "description": f"annular central EDZ shell centred at r = {center:.2f} m with width {width:.2f} m",
                    "shape": normalize_shape(raw),
                    "shell_center_radius_m": center,
                    "shell_width_m": width,
                }
            )

    theta = math.radians(BEDDING_THETA_DEG)
    bedding_major = np.array([math.cos(theta), math.sin(theta)], dtype=float)
    bedding_normal = np.array([-bedding_major[1], bedding_major[0]], dtype=float)
    normal_coord = centroids @ bedding_normal
    radial_window = np.exp(-0.5 * (radius / 2.75) ** 2)
    for offset in [-0.75, 0.0, 0.75]:
        for width in [0.25, 0.50, 0.75]:
            raw = np.exp(-0.5 * ((normal_coord - offset) / width) ** 2) * radial_window
            shapes.append(
                {
                    "family": "bedding_parallel_band",
                    "shape_id": f"bed_o{format_number(offset)}_w{format_number(width)}",
                    "description": (
                        f"bedding-parallel band using theta={BEDDING_THETA_DEG:.0f} deg, "
                        f"normal offset {offset:.2f} m, width {width:.2f} m"
                    ),
                    "shape": normalize_shape(raw),
                    "bedding_theta_deg": BEDDING_THETA_DEG,
                    "band_normal_offset_m": offset,
                    "band_width_m": width,
                }
            )

    if line_data:
        for width in [0.12, 0.25, 0.50]:
            raw = np.zeros(centroids.shape[0], dtype=float)
            for arrays in line_data.values():
                raw = np.maximum(raw, np.exp(-0.5 * (arrays["nearest_distance_m"] / width) ** 2))
            shapes.append(
                {
                    "family": "open_twin_broad_corridor",
                    "shape_id": f"open_corridor_w{format_number(width)}",
                    "description": f"broad corridor around mapped BCD-A32/A33 open-twin pulse-test lines, width {width:.2f} m",
                    "shape": normalize_shape(raw),
                    "corridor_width_m": width,
                }
            )

        for width in [0.12, 0.25, 0.50]:
            for decay in [0.45, 0.90, 1.50]:
                raw = np.zeros(centroids.shape[0], dtype=float)
                for arrays in line_data.values():
                    raw = np.maximum(
                        raw,
                        np.exp(-0.5 * (arrays["nearest_distance_m"] / width) ** 2)
                        * np.exp(-arrays["distance_along_m"] / decay),
                    )
                shapes.append(
                    {
                        "family": "open_twin_depth_decay_corridor",
                        "shape_id": f"open_decay_w{format_number(width)}_d{format_number(decay)}",
                        "description": (
                            f"open-twin corridor around BCD-A32/A33 with width {width:.2f} m and "
                            f"decay along borehole distance {decay:.2f} m"
                        ),
                        "shape": normalize_shape(raw),
                        "corridor_width_m": width,
                        "decay_along_borehole_m": decay,
                    }
                )
    return shapes


def apply_log10_multiplier(
    field: np.ndarray,
    requested_log10: np.ndarray,
    min_eigenvalue: float,
    max_eigenvalue: float,
) -> tuple[np.ndarray, np.ndarray]:
    requested_scale = np.power(10.0, requested_log10)
    applied_scale = np.ones(field.shape[0], dtype=float)
    for cell_id in range(field.shape[0]):
        applied_scale[cell_id] = eigenvalue_limited_scale(
            field[cell_id],
            float(requested_scale[cell_id]),
            min_eigenvalue,
            max_eigenvalue,
        )
    applied_log10 = np.log10(applied_scale)
    return field * applied_scale[:, None], applied_log10


def duplicate_weights(evaluation: pd.DataFrame, fit_mask: pd.Series) -> pd.Series:
    keys = (
        evaluation.loc[fit_mask, "campaign_year"].astype(str)
        + "|"
        + evaluation.loc[fit_mask, "normalized_segment_label"].astype(str)
        + "|"
        + evaluation.loc[fit_mask, "borehole_depth_m"].astype(float).round(6).astype(str)
        + "|"
        + evaluation.loc[fit_mask, "observed_log10_permeability_m2"].astype(float).round(8).astype(str)
    )
    counts = keys.value_counts()
    return 1.0 / keys.map(counts).astype(float)


def score_field(
    field: np.ndarray,
    targets: pd.DataFrame,
    cells_by_observation: dict[str, pd.DataFrame],
    log10_sigma: float,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for _, target in targets.iterrows():
        observation_id = str(target["observation_id"])
        usable = bool_value(target.get("usable_for_current_ogs_fit", False))
        cells = cells_by_observation.get(observation_id)
        has_cells = cells is not None and not cells.empty
        output: dict[str, Any] = {
            "observation_id": observation_id,
            "campaign_year": target.get("campaign_year", ""),
            "normalized_segment_label": target.get("normalized_segment_label", ""),
            "borehole_depth_m": target.get("borehole_depth_m", math.nan),
            "observed_log10_permeability_m2": target.get("log10_permeability_m2", math.nan),
            "used_in_objective": bool(usable and has_cells),
        }
        if usable and has_cells:
            prediction = weighted_prediction(field, target, cells)
            observed = float(output["observed_log10_permeability_m2"])
            predicted = float(prediction["predicted_log10_permeability_m2"])
            output.update(prediction)
            output["log10_residual_pred_minus_obs"] = predicted - observed
        else:
            output["predicted_log10_permeability_m2"] = math.nan
            output["log10_residual_pred_minus_obs"] = math.nan
        rows.append(output)

    evaluation = pd.DataFrame(rows)
    fit_mask = evaluation["used_in_objective"] & np.isfinite(evaluation["log10_residual_pred_minus_obs"])
    if not fit_mask.any():
        return {
            "objective_value": math.nan,
            "weighted_rmse_log10": math.nan,
            "weighted_mean_abs_log10_residual": math.nan,
            "max_abs_log10_residual": math.nan,
            "used_in_objective_rows": 0,
            "effective_objective_weight": math.nan,
        }
    weights = duplicate_weights(evaluation, fit_mask).to_numpy(dtype=float)
    residuals = evaluation.loc[fit_mask, "log10_residual_pred_minus_obs"].to_numpy(dtype=float)
    return {
        "objective_value": float(np.sum(0.5 * weights * (residuals / log10_sigma) ** 2)),
        "weighted_rmse_log10": float(np.sqrt(np.sum(weights * residuals**2) / np.sum(weights))),
        "weighted_mean_abs_log10_residual": float(np.sum(weights * np.abs(residuals)) / np.sum(weights)),
        "max_abs_log10_residual": float(np.max(np.abs(residuals))),
        "used_in_objective_rows": int(fit_mask.sum()),
        "effective_objective_weight": float(np.sum(weights)),
    }


def write_candidate_mesh(
    mesh: meshio.Mesh,
    field_name: str,
    magnitude_field_name: str,
    adjusted_field: np.ndarray,
    requested_log10: np.ndarray,
    applied_log10: np.ndarray,
    shape_weight: np.ndarray,
    family_code: int,
    output_mesh: Path,
) -> None:
    magnitude = tensor_geometric_magnitude(adjusted_field)
    extras = {
        magnitude_field_name: magnitude.reshape((-1, 1)),
        "k_structural_edz_requested_log10_multiplier_rd": requested_log10.reshape((-1, 1)),
        "k_structural_edz_applied_log10_multiplier_rd": applied_log10.reshape((-1, 1)),
        "k_structural_edz_shape_weight_rd": shape_weight.reshape((-1, 1)),
        "k_structural_edz_family_code_rd": np.full((shape_weight.shape[0], 1), int(family_code)),
    }
    output_mesh.parent.mkdir(parents=True, exist_ok=True)
    meshio.write_points_cells(
        output_mesh,
        mesh.points,
        mesh.cells,
        point_data=mesh.point_data,
        cell_data=make_cell_data(mesh, field_name, adjusted_field, extras),
        field_data=mesh.field_data,
    )


def family_code_map(shapes: list[dict[str, Any]]) -> dict[str, int]:
    families = sorted({str(shape["family"]) for shape in shapes})
    return {family: index + 1 for index, family in enumerate(families)}


def candidate_priority(row: pd.Series) -> float:
    delta = float(row.get("direct_objective_delta_vs_active", np.inf))
    magnitude_penalty = 0.005 * float(row.get("mean_abs_applied_log10_multiplier_affected", 0.0))
    support_penalty = 0.00001 * float(row.get("affected_cells", 0.0))
    target_touch = float(row.get("objective_support_cells_with_nonzero_applied", 0.0))
    target_touch_bonus = -0.001 * target_touch
    return delta + magnitude_penalty + support_penalty + target_touch_bonus


def diverse_batch(results: pd.DataFrame, batch_size: int) -> pd.DataFrame:
    rows: list[pd.Series] = []
    seen_families: set[str] = set()
    target_touching = results[
        pd.to_numeric(results["objective_support_cells_with_nonzero_applied"], errors="coerce").fillna(0) > 0
    ].copy()
    pool = target_touching if not target_touching.empty else results
    ordered = pool.sort_values(["execution_priority_score", "objective_value", "candidate_id"])
    for _, row in ordered.iterrows():
        family = str(row["family"])
        if family in seen_families:
            continue
        rows.append(row)
        seen_families.add(family)
        if len(rows) >= batch_size:
            break
    if len(rows) < batch_size:
        chosen = {str(row["candidate_id"]) for row in rows}
        for _, row in ordered.iterrows():
            if str(row["candidate_id"]) in chosen:
                continue
            rows.append(row)
            if len(rows) >= batch_size:
                break
    return pd.DataFrame(rows)


def write_markdown(path: Path, results: pd.DataFrame, batch: pd.DataFrame, summary: dict[str, Any]) -> None:
    best = summary["best_direct_candidate"]
    lines = [
        "# Structural/EDZ Field-Family Screen",
        "",
        "This artifact screens a different permeability-field family after the active production sampler pause.",
        "It applies geometry-shaped log10 permeability multipliers to the current run-local tensor field,",
        "preserving tensor orientation and anisotropy ratio while testing central EDZ, bedding-band,",
        "and open-twin corridor magnitude patterns.",
        "",
        "The score is the direct permeability pulse-test layer only. No OGS run is executed here,",
        "and the frozen source model is not modified.",
        "",
        "## Evidence",
        "",
        f"- Active/current run: `{summary.get('active_run_id')}`",
        f"- Input mesh: `{summary['input_mesh']}`",
        f"- Candidate fields screened: {summary['candidate_count']}",
        f"- Shape families: {', '.join(summary['families'])}",
        f"- Active direct objective: {float(summary['active_direct_objective']):.6f}",
        f"- Active weighted RMSE log10: {float(summary['active_weighted_rmse_log10']):.6f}",
        f"- Improving direct-screen candidates: {summary['improving_candidate_count']}",
        f"- Activation gate: {summary['activation_gate']}",
        "",
        "## Best Direct Structural Candidate",
        "",
        f"- Candidate: `{best.get('candidate_id')}`",
        f"- Family: `{best.get('family')}`",
        f"- Shape: `{best.get('shape_id')}`",
        f"- Log10 amplitude: {float(best.get('amplitude_log10', np.nan)):.3f}",
        f"- Direct objective: {float(best.get('objective_value', np.nan)):.6f}",
        f"- Delta versus active: {float(best.get('direct_objective_delta_vs_active', np.nan)):+.6f}",
        f"- Weighted RMSE log10: {float(best.get('weighted_rmse_log10', np.nan)):.6f}",
        "",
        "## Top Screened Fields",
        "",
        "| Rank | Candidate | Family | Amplitude | Objective | Delta | RMSE | Target cells |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in results.head(12).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row["rank_by_direct_objective"])),
                    f"`{row['candidate_id']}`",
                    f"`{row['family']}`",
                    f"{float(row['amplitude_log10']):.2f}",
                    f"{float(row['objective_value']):.3f}",
                    f"{float(row['direct_objective_delta_vs_active']):+.3f}",
                    f"{float(row['weighted_rmse_log10']):.3f}",
                    str(int(row["objective_support_cells_with_nonzero_applied"])),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Proposed Diagnostic Batch",
            "",
            f"The proposed screened batch is `{summary['next_candidate_batch_csv']}`.",
            "",
            "| Batch rank | Candidate | Family | Objective | Delta | Recommended action |",
            "| ---: | --- | --- | ---: | ---: | --- |",
        ]
    )
    for _, row in batch.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row["execution_batch_rank"])),
                    f"`{row['candidate_id']}`",
                    f"`{row['family']}`",
                    f"{float(row['objective_value']):.3f}",
                    f"{float(row['direct_objective_delta_vs_active']):+.3f}",
                    str(row["recommended_next_action"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            summary["interpretation"],
            "",
            "## Notes",
            "",
            "- Central EDZ shapes use the same approximate 1.5 m centre-support convention already documented for the ERT support screen.",
            "- Bedding-band shapes use the current report's bedding/anisotropy angle of 144 degrees.",
            "- Open-twin corridor shapes use mapped BCD-A32 and BCD-A33 borehole line samples, not individual residual-derived anchor coefficients.",
            "- Full direct-objective rankings include neutral geometry perturbations when they do not intersect active pulse-test support cells; the proposed batch prefers rows that perturb active target cells.",
            "- Candidate meshes are run-local VTU files under this plan directory and should only be passed to OGS after the activation gate is accepted.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_catalogue_artifacts(catalogue_dir: Path, artifacts: list[Path], repo: Path) -> list[dict[str, str]]:
    derived = catalogue_dir / "derived_files"
    derived.mkdir(parents=True, exist_ok=True)
    copies: list[dict[str, str]] = []
    for path in artifacts:
        if not path.exists():
            continue
        target = derived / path.name
        shutil.copy2(path, target)
        copies.append(
            {
                "source": os.path.relpath(path.resolve(), repo),
                "catalogue_copy": os.path.relpath(target.resolve(), repo),
            }
        )
    return copies


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[2]
    input_mesh = resolve(repo, args.input_mesh).resolve()
    output_dir = resolve(repo, args.output_dir).resolve()
    targets_path = resolve(repo, args.targets).resolve()
    target_cells_path = resolve(repo, args.target_cells).resolve()
    line_samples_path = resolve(repo, args.line_samples).resolve()
    ert_lookup_path = resolve(repo, args.ert_lookup).resolve()
    current_field_summary_path = resolve(repo, args.current_field_summary).resolve()
    catalogue_dir = resolve(repo, args.catalogue_dir).resolve()

    if output_dir.exists():
        if not args.overwrite:
            raise SystemExit(f"output directory exists, pass --overwrite to replace/update: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    mesh = meshio.read(input_mesh)
    field = read_cell_field(mesh, args.field_name)
    centroids = cell_centroids(mesh)
    material_ids = read_material_ids(mesh)
    line_data = line_shape_data(line_samples_path, centroids)
    features = cell_support_features(mesh, field, centroids, material_ids, ert_lookup_path, line_data)
    features_path = output_dir / "structural_edz_support_features.csv"
    features.to_csv(features_path, index=False)

    active_evaluation, active_summary = evaluate_targets(
        mesh_path=input_mesh,
        field_name=args.field_name,
        targets_path=targets_path,
        target_cells_path=target_cells_path,
        log10_sigma=args.log10_sigma,
        include_non_usable=True,
    )
    active_eval_path = output_dir / "active_incumbent_permeability_fit_evaluation.csv"
    active_summary_path = output_dir / "active_incumbent_permeability_fit_summary.json"
    active_evaluation.to_csv(active_eval_path, index=False)
    active_summary_path.write_text(json.dumps(json_ready(active_summary), indent=2, sort_keys=True), encoding="utf-8")
    active_objective = float(active_summary["objective_value"])

    targets = pd.read_csv(targets_path)
    target_cells = pd.read_csv(target_cells_path)
    cells_by_observation = {str(key): group.copy() for key, group in target_cells.groupby("observation_id")}
    objective_cell_ids = (
        pd.to_numeric(
            target_cells[target_cells["usable_for_current_ogs_fit"].map(bool_value)]["lookup_cell_id"],
            errors="coerce",
        )
        .dropna()
        .astype(int)
        .to_numpy()
    )
    objective_cell_ids = np.unique(
        objective_cell_ids[(objective_cell_ids >= 0) & (objective_cell_ids < field.shape[0])]
    )
    shapes = build_shapes(centroids, features, line_data)
    family_codes = family_code_map(shapes)

    rows: list[dict[str, Any]] = []
    field_cache: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]] = {}
    for shape in shapes:
        shape_weight = np.asarray(shape["shape"], dtype=float)
        nonzero = shape_weight > 0.0
        if not np.any(nonzero):
            continue
        for amplitude in sorted({float(value) for value in args.amplitudes if not math.isclose(float(value), 0.0)}):
            requested_log10 = amplitude * shape_weight
            adjusted_field, applied_log10 = apply_log10_multiplier(
                field,
                requested_log10,
                args.min_k_eigenvalue,
                args.max_k_eigenvalue,
            )
            score = score_field(adjusted_field, targets, cells_by_observation, args.log10_sigma)
            affected = np.abs(applied_log10) > 1.0e-10
            objective_shape = shape_weight[objective_cell_ids] if objective_cell_ids.size else np.array([], dtype=float)
            objective_applied = applied_log10[objective_cell_ids] if objective_cell_ids.size else np.array([], dtype=float)
            objective_applied_nonzero = np.abs(objective_applied) > 1.0e-10
            candidate_id = (
                f"struct_{safe_label(shape['family'])}_{safe_label(shape['shape_id'])}"
                f"_a{format_number(amplitude)}"
            )
            applied_affected = applied_log10[affected]
            row = {
                "rank_by_direct_objective": 0,
                "candidate_id": candidate_id,
                "family": shape["family"],
                "shape_id": shape["shape_id"],
                "shape_description": shape["description"],
                "amplitude_log10": amplitude,
                "shape_nonzero_cells": int(np.count_nonzero(nonzero)),
                "shape_mean_weight": float(np.mean(shape_weight)),
                "shape_p95_weight": float(np.percentile(shape_weight, 95)),
                "affected_cells": int(np.count_nonzero(affected)),
                "objective_support_cell_count": int(objective_cell_ids.size),
                "objective_support_cells_with_nonzero_shape": int(np.count_nonzero(objective_shape > 1.0e-8)),
                "objective_support_cells_with_nonzero_applied": int(np.count_nonzero(objective_applied_nonzero)),
                "mean_abs_applied_log10_multiplier_objective_support": (
                    float(np.mean(np.abs(objective_applied[objective_applied_nonzero])))
                    if np.any(objective_applied_nonzero)
                    else 0.0
                ),
                "max_abs_applied_log10_multiplier_objective_support": (
                    float(np.max(np.abs(objective_applied[objective_applied_nonzero])))
                    if np.any(objective_applied_nonzero)
                    else 0.0
                ),
                "requested_log10_multiplier_min": float(np.min(requested_log10[nonzero])),
                "requested_log10_multiplier_max": float(np.max(requested_log10[nonzero])),
                "applied_log10_multiplier_min": float(np.min(applied_affected)) if applied_affected.size else 0.0,
                "applied_log10_multiplier_max": float(np.max(applied_affected)) if applied_affected.size else 0.0,
                "mean_abs_applied_log10_multiplier_affected": (
                    float(np.mean(np.abs(applied_affected))) if applied_affected.size else 0.0
                ),
                "objective_value": score["objective_value"],
                "weighted_rmse_log10": score["weighted_rmse_log10"],
                "weighted_mean_abs_log10_residual": score["weighted_mean_abs_log10_residual"],
                "max_abs_log10_residual": score["max_abs_log10_residual"],
                "used_in_objective_rows": score["used_in_objective_rows"],
                "effective_objective_weight": score["effective_objective_weight"],
                "direct_objective_delta_vs_active": float(score["objective_value"]) - active_objective,
                "mesh": "",
                "evaluation_csv": "",
                "summary_json": "",
            }
            for key, value in shape.items():
                if key in {"shape", "family", "shape_id", "description"}:
                    continue
                row[key] = value
            rows.append(row)
            field_cache[candidate_id] = (
                adjusted_field,
                requested_log10,
                applied_log10,
                shape_weight,
                family_codes[str(shape["family"])],
            )

    if not rows:
        raise SystemExit("no structural/EDZ candidates were generated")

    results = pd.DataFrame(rows)
    results["objective_value"] = pd.to_numeric(results["objective_value"], errors="coerce")
    results = results.sort_values(["objective_value", "candidate_id"], na_position="last").reset_index(drop=True)
    results["rank_by_direct_objective"] = range(1, results.shape[0] + 1)
    results["execution_priority_score"] = results.apply(candidate_priority, axis=1)

    top = results.head(args.max_proposals).copy()
    for _, row in top.iterrows():
        candidate_id = str(row["candidate_id"])
        candidate_dir = output_dir / candidate_id
        mesh_path = candidate_dir / "bulk_w_projections.vtu"
        adjusted_field, requested_log10, applied_log10, shape_weight, family_code = field_cache[candidate_id]
        write_candidate_mesh(
            mesh,
            args.field_name,
            args.magnitude_field_name,
            adjusted_field,
            requested_log10,
            applied_log10,
            shape_weight,
            family_code,
            mesh_path,
        )
        evaluation, direct_summary = evaluate_targets(
            mesh_path=mesh_path,
            field_name=args.field_name,
            targets_path=targets_path,
            target_cells_path=target_cells_path,
            log10_sigma=args.log10_sigma,
            include_non_usable=True,
        )
        evaluation_path = candidate_dir / "permeability_fit_evaluation.csv"
        summary_path = candidate_dir / "permeability_fit_summary.json"
        evaluation.to_csv(evaluation_path, index=False)
        summary_path.write_text(json.dumps(json_ready(direct_summary), indent=2, sort_keys=True), encoding="utf-8")
        results.loc[results["candidate_id"].eq(candidate_id), "mesh"] = str(mesh_path)
        results.loc[results["candidate_id"].eq(candidate_id), "evaluation_csv"] = str(evaluation_path)
        results.loc[results["candidate_id"].eq(candidate_id), "summary_json"] = str(summary_path)

    results = results.sort_values(["rank_by_direct_objective", "execution_priority_score", "candidate_id"]).reset_index(drop=True)
    improving = results[results["direct_objective_delta_vs_active"] < 0.0].copy()
    best = json_ready(results.iloc[0].to_dict())
    best_delta = float(best["direct_objective_delta_vs_active"])
    materially_improves = best_delta <= -abs(float(args.direct_improvement_threshold))
    status = (
        "structural_edz_direct_screen_candidate_batch_ready"
        if materially_improves
        else "structural_edz_direct_screen_no_ogs_batch_recommended"
    )

    batch = diverse_batch(results, args.batch_size).copy()
    batch["execution_batch_rank"] = range(1, batch.shape[0] + 1)
    batch["recommended_next_action"] = (
        "eligible_for_release_gated_ogs_probe"
        if materially_improves
        else "do_not_run_for_active_objective_without_new_modelling_decision"
    )

    results_path = output_dir / "structural_edz_candidate_scores.csv"
    batch_path = output_dir / "next_structural_edz_candidate_batch.csv"
    summary_json_path = output_dir / "STRUCTURAL_EDZ_FIELD_FAMILY_PLAN.json"
    summary_md_path = output_dir / "STRUCTURAL_EDZ_FIELD_FAMILY_PLAN.md"
    results.to_csv(results_path, index=False)
    batch.to_csv(batch_path, index=False)

    current_field_summary = read_json(current_field_summary_path)
    active_run_id = current_field_summary.get("run_id") or current_field_summary.get("source_run_id") or "current_field"
    if materially_improves:
        interpretation = (
            "At least one structural/EDZ candidate materially improves the direct permeability screen. "
            "The diverse batch is a defensible next OGS probe only if the modelling decision is to test "
            "this field family under the existing release-gated candidate harness."
        )
    elif best_delta < 0.0:
        interpretation = (
            "The best structural/EDZ candidate improves the direct screen only marginally, below the "
            f"{abs(float(args.direct_improvement_threshold)):.2f} objective-unit materiality threshold. "
            "Do not spend OGS runs on this family for the active objective without an explicit diagnostic decision."
        )
    else:
        interpretation = (
            "No structural/EDZ candidate improves the direct permeability screen. The generated top meshes "
            "are useful as documented diagnostic probes, but they do not justify more active-objective OGS "
            "runs before measurement-stream gates or a different parameterization are addressed."
        )

    summary = {
        "status": status,
        "active_run_id": active_run_id,
        "input_mesh": str(input_mesh),
        "field_name": args.field_name,
        "magnitude_field_name": args.magnitude_field_name,
        "targets": str(targets_path),
        "target_cells": str(target_cells_path),
        "line_samples": str(line_samples_path),
        "ert_lookup": str(ert_lookup_path),
        "output_dir": str(output_dir),
        "families": sorted(family_codes.keys()),
        "family_codes": family_codes,
        "amplitudes_log10": sorted({float(value) for value in args.amplitudes if not math.isclose(float(value), 0.0)}),
        "candidate_count": int(results.shape[0]),
        "proposal_mesh_count": int(min(args.max_proposals, results.shape[0])),
        "improving_candidate_count": int(improving.shape[0]),
        "material_direct_improvement_threshold": abs(float(args.direct_improvement_threshold)),
        "active_direct_objective": active_objective,
        "active_weighted_rmse_log10": active_summary.get("weighted_rmse_log10"),
        "active_fit_evaluation_csv": str(active_eval_path),
        "active_fit_summary_json": str(active_summary_path),
        "best_direct_candidate": best,
        "best_direct_objective": best.get("objective_value"),
        "best_direct_delta_vs_active": best.get("direct_objective_delta_vs_active"),
        "recommended_execution_batch_size": int(batch.shape[0]),
        "results_csv": str(results_path),
        "next_candidate_batch_csv": str(batch_path),
        "support_features_csv": str(features_path),
        "summary_markdown": str(summary_md_path),
        "activation_gate": (
            "Run-local direct screen only. Execute the batch with the OGS candidate harness only if "
            "best_direct_delta_vs_active is below the materiality threshold and the modelling decision "
            "explicitly accepts structural/EDZ probing as the next family."
        ),
        "interpretation": interpretation,
        "support_feature_counts": {
            "cell_count": int(features.shape[0]),
            "active_permeability_objective_support_cells": int(objective_cell_ids.size),
            "material_id_counts": {
                str(key): int(value)
                for key, value in features["material_id"].value_counts().sort_index().to_dict().items()
            },
            "within_approx_1p5m_center_support_cells": int(features["within_approx_1p5m_center_support"].sum()),
            "ert_ready_support_cells": int(features["inside_ert_ready_support_cells"].sum()),
            "line_segments_available": sorted(line_data.keys()),
        },
        "notes": [
            "All candidates preserve tensor orientation and anisotropy ratio by scalar multiplication of k_i_rd.",
            "The central EDZ shapes use the existing approximate centre-radius support convention.",
            "The open-twin corridor shapes use mapped BCD-A32/BCD-A33 line geometry, not residual-derived local coefficients.",
            "ERT, Taupe/TDR, RH, and other HM streams remain gated; this screen is not a replacement for those gates.",
        ],
    }
    write_markdown(summary_md_path, results, batch, summary)

    catalogue_copies = copy_catalogue_artifacts(
        catalogue_dir,
        [results_path, batch_path, features_path, active_summary_path, summary_json_path, summary_md_path],
        repo,
    )
    summary["catalogue_copies"] = catalogue_copies
    summary_json_path.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(summary_md_path, results, batch, summary)
    copy_catalogue_artifacts(catalogue_dir, [summary_json_path, summary_md_path], repo)

    print(f"wrote {results_path}")
    print(f"wrote {batch_path}")
    print(f"wrote {summary_json_path}")
    print(f"wrote {summary_md_path}")
    print(f"status: {status}")
    print(f"best candidate: {best['candidate_id']}")
    print(f"best direct objective: {float(best['objective_value']):.6g}")
    print(f"best delta vs active: {best_delta:+.6g}")


if __name__ == "__main__":
    main()
