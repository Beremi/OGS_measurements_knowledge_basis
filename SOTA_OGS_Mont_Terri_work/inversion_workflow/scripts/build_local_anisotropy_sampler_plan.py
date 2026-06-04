#!/usr/bin/env python3
"""Screen local anisotropy changes around direct permeability target supports.

Most accepted CDA permeability candidates so far modify tensor magnitude while
keeping orientation and anisotropy ratio fixed.  This script tests the next
permissible degree of freedom for the frozen OGS model: run-local changes to the
`k_i_rd` tensor orientation and anisotropy ratio near mapped pulse-test cells,
while preserving each cell's geometric-mean permeability.

The output is a direct pulse-test screen only.  Candidate meshes must still go
through the existing OGS candidate harness before any combined-objective claim.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import meshio
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_permeability_targets import evaluate_targets  # noqa: E402
from fit_smooth_permeability_field_from_targets import cell_centroids, make_cell_data, read_cell_field  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-mesh",
        type=Path,
        default=Path("inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/bulk_w_projections.vtu"),
        help="Active incumbent mesh containing a tensor cell-data field.",
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
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/runs/local_anisotropy_sampler_plan"),
    )
    parser.add_argument("--field-name", default="k_i_rd")
    parser.add_argument("--length-scale-m", type=float, nargs="*", default=[0.0015, 0.0030, 0.0075, 0.0150])
    parser.add_argument("--blend-strength", type=float, nargs="*", default=[0.50, 1.00])
    parser.add_argument("--target-ratio", type=float, nargs="*", default=[2.5, 6.0, 12.0])
    parser.add_argument(
        "--mode",
        nargs="*",
        default=["residual_sign", "parallel_all", "perpendicular_all", "isotropize"],
        choices=["residual_sign", "parallel_all", "perpendicular_all", "isotropize"],
    )
    parser.add_argument("--cutoff-factor", type=float, default=3.0)
    parser.add_argument("--min-k-eigenvalue", type=float, default=1.0e-22)
    parser.add_argument("--max-k-eigenvalue", type=float, default=1.0e-12)
    parser.add_argument("--log10-sigma", type=float, default=0.5)
    parser.add_argument("--execution-batch-size", type=int, default=3)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


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


def safe_number_label(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".").replace(".", "p").replace("-", "m")


def candidate_label(mode: str, length_scale: float, strength: float, target_ratio: float) -> str:
    return (
        f"local_anis_{mode}_l{safe_number_label(length_scale)}"
        f"_s{safe_number_label(strength)}_r{safe_number_label(target_ratio)}"
    )


def tensor_components(field: np.ndarray) -> dict[str, np.ndarray]:
    if field.ndim != 2 or field.shape[1] != 4:
        raise ValueError(f"local anisotropy screen requires a four-component tensor field; got {field.shape}")
    mats = field.reshape((-1, 2, 2))
    mats = 0.5 * (mats + np.swapaxes(mats, 1, 2))
    eigvals, eigvecs = np.linalg.eigh(mats)
    eigvals = np.clip(eigvals, 1.0e-300, np.inf)
    minor = eigvals[:, 0]
    major = eigvals[:, 1]
    geometric_mean = np.sqrt(minor * major)
    ratio = major / minor
    theta = np.arctan2(eigvecs[:, 1, 1], eigvecs[:, 0, 1])
    theta = np.mod(theta, math.pi)
    return {
        "geometric_mean": geometric_mean,
        "ratio": ratio,
        "theta_rad": theta,
        "theta_deg": np.degrees(theta),
    }


def nematic(theta_rad: np.ndarray | float) -> np.ndarray:
    theta = np.asarray(theta_rad, dtype=float)
    return np.stack([np.cos(2.0 * theta), np.sin(2.0 * theta)], axis=-1)


def theta_from_nematic(vectors: np.ndarray) -> np.ndarray:
    theta = 0.5 * np.arctan2(vectors[:, 1], vectors[:, 0])
    return np.mod(theta, math.pi)


def tensor_from_components(
    geometric_mean: np.ndarray,
    theta_rad: np.ndarray,
    ratio: np.ndarray,
    min_k: float,
    max_k: float,
) -> np.ndarray:
    ratio = np.clip(ratio, 1.0, np.inf)
    ratio_sqrt = np.sqrt(ratio)
    k_major = np.clip(geometric_mean * ratio_sqrt, min_k, max_k)
    k_minor = np.clip(geometric_mean / ratio_sqrt, min_k, max_k)
    cos_t = np.cos(theta_rad)
    sin_t = np.sin(theta_rad)
    major_xx = cos_t * cos_t
    major_xy = cos_t * sin_t
    major_yy = sin_t * sin_t
    minor_xx = sin_t * sin_t
    minor_xy = -sin_t * cos_t
    minor_yy = cos_t * cos_t
    kxx = k_major * major_xx + k_minor * minor_xx
    kxy = k_major * major_xy + k_minor * minor_xy
    kyy = k_major * major_yy + k_minor * minor_yy
    return np.stack([kxx, kxy, kxy, kyy], axis=1)


def build_anchor_table(
    baseline_evaluation: pd.DataFrame,
    target_cells_path: Path,
) -> pd.DataFrame:
    cells = pd.read_csv(target_cells_path)
    fit = baseline_evaluation[
        baseline_evaluation["used_in_objective"]
        & np.isfinite(baseline_evaluation["log10_residual_pred_minus_obs"])
    ].copy()
    columns = [
        "observation_id",
        "campaign_year",
        "normalized_segment_label",
        "borehole_depth_m",
        "observed_log10_permeability_m2",
        "predicted_log10_permeability_m2",
        "log10_residual_pred_minus_obs",
        "objective_weight",
        "segment_tangent_x",
        "segment_tangent_y",
    ]
    merged = cells.merge(fit[columns], on="observation_id", how="inner", suffixes=("_cell", ""))
    merged = merged[merged["usable_for_current_ogs_fit"].map(bool_value)].copy()
    merged = merged[np.isfinite(merged["log10_residual_pred_minus_obs"])]
    merged["lookup_cell_id"] = merged["lookup_cell_id"].astype(int)
    merged["anchor_weight"] = (
        merged["cell_weight"].astype(float)
        * merged["objective_weight"].astype(float)
        * (1.0 + np.minimum(np.abs(merged["log10_residual_pred_minus_obs"].astype(float)), 3.0))
    )
    tangent_x = merged["segment_tangent_x"].astype(float).to_numpy()
    tangent_y = merged["segment_tangent_y"].astype(float).to_numpy()
    merged["segment_theta_rad"] = np.mod(np.arctan2(tangent_y, tangent_x), math.pi)
    merged["segment_theta_deg"] = np.degrees(merged["segment_theta_rad"])
    merged["residual_action"] = np.where(
        merged["log10_residual_pred_minus_obs"].astype(float) <= 0.0,
        "raise_directional_k_parallel_to_segment",
        "lower_directional_k_by_putting_major_axis_perpendicular",
    )
    return merged.reset_index(drop=True)


def target_anchor_theta(anchors: pd.DataFrame, mode: str) -> np.ndarray:
    base = anchors["segment_theta_rad"].to_numpy(dtype=float)
    if mode == "parallel_all":
        return base
    if mode == "perpendicular_all":
        return np.mod(base + 0.5 * math.pi, math.pi)
    if mode == "residual_sign":
        residual = anchors["log10_residual_pred_minus_obs"].to_numpy(dtype=float)
        return np.mod(base + np.where(residual <= 0.0, 0.0, 0.5 * math.pi), math.pi)
    if mode == "isotropize":
        return base
    raise ValueError(f"unknown mode: {mode}")


def build_candidate_field(
    base: dict[str, np.ndarray],
    centroids: np.ndarray,
    anchors: pd.DataFrame,
    mode: str,
    length_scale: float,
    strength: float,
    target_ratio: float,
    cutoff_factor: float,
    min_k: float,
    max_k: float,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    anchor_cells = anchors["lookup_cell_id"].to_numpy(dtype=int)
    anchor_xy = centroids[anchor_cells]
    anchor_weights = anchors["anchor_weight"].to_numpy(dtype=float)
    anchor_theta = target_anchor_theta(anchors, mode)
    anchor_vectors = nematic(anchor_theta)

    weight_sum = np.zeros(centroids.shape[0], dtype=float)
    vector_sum = np.zeros((centroids.shape[0], 2), dtype=float)
    nearest_distance = np.full(centroids.shape[0], math.nan, dtype=float)
    cutoff = cutoff_factor * length_scale
    for cell_id, xy in enumerate(centroids):
        distances = np.linalg.norm(anchor_xy - xy, axis=1)
        nearest_distance[cell_id] = float(distances.min()) if distances.size else math.nan
        active = distances <= cutoff
        if not np.any(active):
            continue
        weights = np.exp(-0.5 * (distances[active] / length_scale) ** 2) * anchor_weights[active]
        total = float(np.sum(weights))
        if total <= 0.0 or not np.isfinite(total):
            continue
        weight_sum[cell_id] = total
        vector_sum[cell_id] = np.sum(weights[:, None] * anchor_vectors[active], axis=0) / total

    active_vector = nematic(base["theta_rad"])
    has_target = weight_sum > 0.0
    target_vector = active_vector.copy()
    norms = np.linalg.norm(vector_sum[has_target], axis=1)
    nonzero = norms > 0.0
    target_subset = target_vector[has_target]
    target_subset[nonzero] = vector_sum[has_target][nonzero] / norms[nonzero, None]
    target_vector[has_target] = target_subset

    blend = np.clip(strength * np.minimum(weight_sum, 1.0), 0.0, 1.0)
    if mode == "isotropize":
        mixed_vector = active_vector
        target_log_ratio = np.zeros_like(base["ratio"])
    else:
        mixed_vector = (1.0 - blend[:, None]) * active_vector + blend[:, None] * target_vector
        target_log_ratio = np.full_like(base["ratio"], math.log(float(target_ratio)))
    mixed_norm = np.linalg.norm(mixed_vector, axis=1)
    too_small = mixed_norm <= 1.0e-12
    mixed_vector[~too_small] = mixed_vector[~too_small] / mixed_norm[~too_small, None]
    mixed_vector[too_small] = active_vector[too_small]

    active_log_ratio = np.log(np.clip(base["ratio"], 1.0, np.inf))
    new_log_ratio = (1.0 - blend) * active_log_ratio + blend * target_log_ratio
    new_ratio = np.exp(new_log_ratio)
    new_theta = theta_from_nematic(mixed_vector)
    field = tensor_from_components(
        base["geometric_mean"],
        new_theta,
        new_ratio,
        min_k,
        max_k,
    )
    metadata = {
        "blend": blend,
        "weight_sum": weight_sum,
        "nearest_distance": nearest_distance,
        "theta_rad": new_theta,
        "theta_deg": np.degrees(new_theta),
        "ratio": new_ratio,
    }
    return field, metadata


def write_candidate_mesh(
    mesh: meshio.Mesh,
    field_name: str,
    field: np.ndarray,
    base: dict[str, np.ndarray],
    metadata: dict[str, np.ndarray],
    output_mesh: Path,
) -> None:
    extras = {
        "k_mag_rd": base["geometric_mean"],
        "k_theta_deg_rd": metadata["theta_deg"],
        "k_anisotropy_ratio_rd": metadata["ratio"],
        "k_local_anisotropy_blend_weight_rd": metadata["blend"],
        "k_local_anisotropy_anchor_weight_sum_rd": metadata["weight_sum"],
        "k_local_anisotropy_nearest_anchor_distance_m_rd": metadata["nearest_distance"],
    }
    output_mesh.parent.mkdir(parents=True, exist_ok=True)
    meshio.write_points_cells(
        output_mesh,
        mesh.points,
        mesh.cells,
        point_data=mesh.point_data,
        cell_data=make_cell_data(mesh, field_name, field, extras),
        field_data=mesh.field_data,
    )


def diverse_batch(results: pd.DataFrame, batch_size: int) -> pd.DataFrame:
    rows: list[pd.Series] = []
    seen_modes: set[str] = set()
    ordered = results.sort_values(["objective_value", "mean_blend_weight_affected", "candidate_id"])
    for _, row in ordered.iterrows():
        mode = str(row["mode"])
        if mode in seen_modes:
            continue
        rows.append(row)
        seen_modes.add(mode)
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
    best = summary["best_candidate"]
    lines = [
        "# Local Anisotropy Sampler Plan",
        "",
        "This screen tests local tensor orientation and anisotropy-ratio changes around",
        "mapped direct pulse-test supports.  It preserves each cell's geometric-mean",
        "permeability from the active incumbent and changes only the anisotropic split",
        "and principal direction in the run-local `k_i_rd` mesh field.",
        "",
        "The score is the direct permeability pulse-test layer only.  These fields have",
        "not been run through OGS and should not be treated as combined-objective",
        "evidence until the existing release-gated candidate harness executes them.",
        "",
        "## Evidence",
        "",
        f"- Input mesh: `{summary['input_mesh']}`",
        f"- Candidate fields screened: {summary['candidate_count']}",
        f"- Anchor rows: {summary['anchor_row_count']}",
        f"- Unique anchor cells: {summary['unique_anchor_cells']}",
        f"- Baseline direct objective: {float(summary['baseline_direct_objective']):.6f}",
        f"- Baseline weighted RMSE log10: {float(summary['baseline_weighted_rmse_log10']):.6f}",
        "",
        "## Best Direct Candidate",
        "",
        f"- Candidate: `{best['candidate_id']}`",
        f"- Mode: `{best['mode']}`",
        f"- Length scale: {float(best['length_scale_m']):.4f} m",
        f"- Blend strength: {float(best['blend_strength']):.2f}",
        f"- Target anisotropy ratio: {float(best['target_ratio']):.2f}",
        f"- Direct objective: {float(best['objective_value']):.6f}",
        f"- Direct objective delta vs baseline: {float(best['direct_objective_delta_vs_baseline']):+.6f}",
        f"- Weighted RMSE log10: {float(best['weighted_rmse_log10']):.6f}",
        "",
        "## Top Candidates",
        "",
        "| Rank | Candidate | Mode | Length [m] | Strength | Ratio | Objective | Delta | RMSE |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in results.head(12).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row["rank_by_direct_objective"])),
                    f"`{row['candidate_id']}`",
                    f"`{row['mode']}`",
                    f"{float(row['length_scale_m']):.4f}",
                    f"{float(row['blend_strength']):.2f}",
                    f"{float(row['target_ratio']):.2f}",
                    f"{float(row['objective_value']):.3f}",
                    f"{float(row['direct_objective_delta_vs_baseline']):+.3f}",
                    f"{float(row['weighted_rmse_log10']):.3f}",
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
            "| Batch rank | Candidate | Mode | Objective | Delta |",
            "| ---: | --- | --- | ---: | ---: |",
        ]
    )
    for _, row in batch.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row["execution_batch_rank"])),
                    f"`{row['candidate_id']}`",
                    f"`{row['mode']}`",
                    f"{float(row['objective_value']):.3f}",
                    f"{float(row['direct_objective_delta_vs_baseline']):+.3f}",
                ]
            )
            + " |"
        )
    lines.extend(["", "## Interpretation", "", summary["interpretation"], ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[2]
    output_dir = (repo / args.output_dir if not args.output_dir.is_absolute() else args.output_dir).resolve()
    input_mesh = (repo / args.input_mesh if not args.input_mesh.is_absolute() else args.input_mesh).resolve()
    targets_path = (repo / args.targets if not args.targets.is_absolute() else args.targets).resolve()
    target_cells_path = (repo / args.target_cells if not args.target_cells.is_absolute() else args.target_cells).resolve()

    if output_dir.exists():
        if not args.overwrite:
            raise SystemExit(f"output directory exists, pass --overwrite to replace: {output_dir}")
        import shutil

        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    mesh = meshio.read(input_mesh)
    baseline_field = read_cell_field(mesh, args.field_name)
    base = tensor_components(baseline_field)
    centroids = cell_centroids(mesh)

    baseline_evaluation, baseline_summary = evaluate_targets(
        mesh_path=input_mesh,
        field_name=args.field_name,
        targets_path=targets_path,
        target_cells_path=target_cells_path,
        log10_sigma=args.log10_sigma,
        include_non_usable=True,
    )
    baseline_eval_path = output_dir / "active_incumbent_permeability_fit_evaluation.csv"
    baseline_summary_path = output_dir / "active_incumbent_permeability_fit_summary.json"
    baseline_evaluation.to_csv(baseline_eval_path, index=False)
    baseline_summary_path.write_text(json.dumps(json_ready(baseline_summary), indent=2, sort_keys=True), encoding="utf-8")
    anchors = build_anchor_table(baseline_evaluation, target_cells_path)
    if anchors.empty:
        raise SystemExit("no direct permeability anchor rows available")
    anchor_path = output_dir / "local_anisotropy_anchor_rows.csv"
    anchors.to_csv(anchor_path, index=False)

    rows: list[dict[str, Any]] = []
    for mode in args.mode:
        ratio_values = [1.0] if mode == "isotropize" else [float(value) for value in args.target_ratio]
        for length_scale in args.length_scale_m:
            for strength in args.blend_strength:
                for target_ratio in ratio_values:
                    candidate_id = candidate_label(mode, float(length_scale), float(strength), float(target_ratio))
                    candidate_dir = output_dir / candidate_id
                    mesh_path = candidate_dir / "bulk_w_projections.vtu"
                    field, metadata = build_candidate_field(
                        base,
                        centroids,
                        anchors,
                        mode,
                        float(length_scale),
                        float(strength),
                        float(target_ratio),
                        float(args.cutoff_factor),
                        float(args.min_k_eigenvalue),
                        float(args.max_k_eigenvalue),
                    )
                    write_candidate_mesh(mesh, args.field_name, field, base, metadata, mesh_path)
                    evaluation, summary = evaluate_targets(
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
                    summary_path.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
                    affected = metadata["blend"] > 0.0
                    rows.append(
                        {
                            "rank_by_direct_objective": 0,
                            "candidate_id": candidate_id,
                            "mode": mode,
                            "length_scale_m": float(length_scale),
                            "blend_strength": float(strength),
                            "target_ratio": float(target_ratio),
                            "mesh": str(mesh_path),
                            "evaluation_csv": str(evaluation_path),
                            "summary_json": str(summary_path),
                            "objective_value": float(summary["objective_value"]),
                            "objective_value_after_global_shift": float(summary["objective_value_after_global_shift"]),
                            "weighted_rmse_log10": float(summary["weighted_rmse_log10"]),
                            "weighted_rmse_log10_after_global_shift": float(summary["weighted_rmse_log10_after_global_shift"]),
                            "weighted_mean_abs_log10_residual": float(summary["weighted_mean_abs_log10_residual"]),
                            "max_abs_log10_residual": float(summary["max_abs_log10_residual"]),
                            "used_in_objective_rows": int(summary["used_in_objective_rows"]),
                            "effective_objective_weight": float(summary["effective_objective_weight"]),
                            "direct_objective_delta_vs_baseline": float(summary["objective_value"])
                            - float(baseline_summary["objective_value"]),
                            "affected_cells": int(np.count_nonzero(affected)),
                            "mean_blend_weight_affected": float(np.mean(metadata["blend"][affected])) if np.any(affected) else 0.0,
                            "max_blend_weight": float(np.max(metadata["blend"])),
                            "new_ratio_min": float(np.min(metadata["ratio"])),
                            "new_ratio_median": float(np.median(metadata["ratio"])),
                            "new_ratio_max": float(np.max(metadata["ratio"])),
                            "new_theta_deg_p05": float(np.percentile(metadata["theta_deg"], 5)),
                            "new_theta_deg_p50": float(np.percentile(metadata["theta_deg"], 50)),
                            "new_theta_deg_p95": float(np.percentile(metadata["theta_deg"], 95)),
                        }
                    )

    results = pd.DataFrame(rows).sort_values(
        ["objective_value", "mean_blend_weight_affected", "candidate_id"],
        na_position="last",
    ).reset_index(drop=True)
    results["rank_by_direct_objective"] = range(1, results.shape[0] + 1)
    batch = diverse_batch(results, int(args.execution_batch_size)).copy()
    batch["execution_batch_rank"] = range(1, batch.shape[0] + 1)

    results_path = output_dir / "local_anisotropy_sampler_scores.csv"
    batch_path = output_dir / "next_local_anisotropy_candidate_batch.csv"
    summary_json_path = output_dir / "LOCAL_ANISOTROPY_SAMPLER_PLAN.json"
    summary_md_path = output_dir / "LOCAL_ANISOTROPY_SAMPLER_PLAN.md"
    results.to_csv(results_path, index=False)
    batch.to_csv(batch_path, index=False)

    best = json_ready(results.iloc[0].to_dict())
    best_delta = float(best["direct_objective_delta_vs_baseline"])
    if best_delta < 0.0:
        interpretation = (
            "At least one local anisotropy candidate improves the direct permeability screen, "
            "so the top diverse rows are defensible candidates for a release-gated OGS diagnostic batch. "
            "This is not combined-objective evidence until OGS state outputs are evaluated."
        )
    else:
        interpretation = (
            "No local anisotropy candidate improves the direct permeability screen. "
            "The active direct target data do not currently justify releasing local tensor orientation "
            "or anisotropy ratio as a new OGS execution family."
        )
    summary = {
        "status": "local_anisotropy_sampler_plan_generated_not_executed",
        "input_mesh": str(input_mesh),
        "output_dir": str(output_dir),
        "field_name": args.field_name,
        "targets": str(targets_path),
        "target_cells": str(target_cells_path),
        "anchor_rows_csv": str(anchor_path),
        "anchor_row_count": int(anchors.shape[0]),
        "unique_anchor_cells": int(anchors["lookup_cell_id"].nunique()),
        "candidate_count": int(results.shape[0]),
        "execution_batch_size": int(batch.shape[0]),
        "length_scale_m_values": [float(value) for value in args.length_scale_m],
        "blend_strength_values": [float(value) for value in args.blend_strength],
        "target_ratio_values": [float(value) for value in args.target_ratio],
        "modes": list(args.mode),
        "baseline_direct_objective": float(baseline_summary["objective_value"]),
        "baseline_weighted_rmse_log10": float(baseline_summary["weighted_rmse_log10"]),
        "baseline_ratio_min": float(np.min(base["ratio"])),
        "baseline_ratio_median": float(np.median(base["ratio"])),
        "baseline_ratio_max": float(np.max(base["ratio"])),
        "baseline_theta_deg_p05": float(np.percentile(base["theta_deg"], 5)),
        "baseline_theta_deg_p50": float(np.percentile(base["theta_deg"], 50)),
        "baseline_theta_deg_p95": float(np.percentile(base["theta_deg"], 95)),
        "best_candidate": best,
        "best_direct_objective": best.get("objective_value"),
        "best_direct_delta_vs_baseline": best.get("direct_objective_delta_vs_baseline"),
        "top_candidates": [json_ready(row) for row in results.head(12).to_dict(orient="records")],
        "execution_batch": [json_ready(row) for row in batch.to_dict(orient="records")],
        "results_csv": str(results_path),
        "next_candidate_batch_csv": str(batch_path),
        "summary_markdown": str(summary_md_path),
        "activation_gate": (
            "Planning and direct-permeability screen only; execute with the existing OGS candidate harness "
            "only if the direct screen provides a clear improvement or if a deliberate tensor-anisotropy "
            "diagnostic probe is needed."
        ),
        "interpretation": interpretation,
        "notes": [
            "Geometric-mean permeability is preserved from the active incumbent.",
            "Residual-sign mode aligns the major axis with the segment when the baseline underpredicts and perpendicular to it when the baseline overpredicts.",
            "The generated mesh updates k_i_rd plus tensor metadata fields k_mag_rd, k_theta_deg_rd, and k_anisotropy_ratio_rd.",
        ],
    }
    summary_json_path.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(summary_md_path, results, batch, summary)

    print(f"wrote {results_path}")
    print(f"wrote {batch_path}")
    print(f"wrote {summary_json_path}")
    print(f"wrote {summary_md_path}")
    print(f"best candidate: {best['candidate_id']}")
    print(f"best direct objective: {float(best['objective_value']):.6g}")
    print(f"best delta vs baseline: {best_delta:+.6g}")


if __name__ == "__main__":
    main()
