#!/usr/bin/env python3
"""Sample richer local-basis permeability updates around an incumbent field."""

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
from evaluate_permeability_targets import evaluate_targets, weighted_prediction  # noqa: E402
from fit_smooth_permeability_field_from_targets import (  # noqa: E402
    build_anchor_table,
    cell_centroids,
    eigenvalue_limited_scale,
    make_cell_data,
    read_cell_field,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-mesh",
        type=Path,
        default=Path("inversion_workflow/runs/lower_support_loop_001_001_length_0p003m_shift_1p006/bulk_w_projections.vtu"),
        help="Incumbent mesh containing the tensor field to perturb.",
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
        default=Path("inversion_workflow/runs/local_basis_sampler_plan"),
    )
    parser.add_argument("--field-name", default="k_i_rd")
    parser.add_argument("--length-min-m", type=float, default=0.0015)
    parser.add_argument("--length-max-m", type=float, default=0.018)
    parser.add_argument("--sample-count", type=int, default=96)
    parser.add_argument("--seed", type=int, default=20260531)
    parser.add_argument("--basis-count", type=int, default=30)
    parser.add_argument("--deterministic-shrink", type=float, nargs="*", default=[0.25, 0.50, 0.75, 1.00, 1.25])
    parser.add_argument("--deterministic-length-m", type=float, nargs="*", default=[0.0015, 0.0025, 0.0035, 0.0050, 0.0075, 0.0100, 0.0150])
    parser.add_argument("--random-shrink-min", type=float, default=0.0)
    parser.add_argument("--random-shrink-max", type=float, default=1.35)
    parser.add_argument("--coefficient-noise-sigma", type=float, default=0.35)
    parser.add_argument("--max-abs-log10-increment", type=float, default=3.0)
    parser.add_argument("--min-k-eigenvalue", type=float, default=1.0e-22)
    parser.add_argument("--max-k-eigenvalue", type=float, default=1.0e-12)
    parser.add_argument("--log10-sigma", type=float, default=0.5)
    parser.add_argument("--max-proposals", type=int, default=12)
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


def candidate_label(index: int, source: str, length_scale: float, shrink: float) -> str:
    label = f"basis_{index:03d}_{source}_l_{length_scale:.4f}_s_{shrink:.3f}"
    return label.replace(".", "p").replace("-", "m")


def select_basis_anchors(anchors: pd.DataFrame, centroids: np.ndarray, basis_count: int) -> pd.DataFrame:
    if anchors.empty:
        raise ValueError("no anchor rows available")
    anchors = anchors.copy()
    anchors["anchor_abs_shift"] = anchors["anchor_log10_shift"].abs()
    if anchors.shape[0] <= basis_count:
        return anchors.sort_values(["lookup_cell_id"]).reset_index(drop=True)

    # Seed with the strongest requested shift, then use farthest-point selection so
    # both BCD-A32 and BCD-A33 supports keep local degrees of freedom.
    selected_indices: list[int] = [int(anchors["anchor_abs_shift"].idxmax())]
    remaining = set(int(idx) for idx in anchors.index)
    remaining.remove(selected_indices[0])
    while remaining and len(selected_indices) < basis_count:
        selected_cells = anchors.loc[selected_indices, "lookup_cell_id"].to_numpy(dtype=int)
        best_idx = None
        best_score = -math.inf
        for idx in remaining:
            cell_id = int(anchors.loc[idx, "lookup_cell_id"])
            distances = np.linalg.norm(centroids[selected_cells] - centroids[cell_id], axis=1)
            distance_score = float(distances.min())
            shift_score = float(anchors.loc[idx, "anchor_abs_shift"])
            score = distance_score * (1.0 + 0.25 * shift_score)
            if score > best_score:
                best_idx = idx
                best_score = score
        if best_idx is None:
            break
        selected_indices.append(best_idx)
        remaining.remove(best_idx)
    return anchors.loc[selected_indices].sort_values(["lookup_cell_id"]).reset_index(drop=True)


def basis_average_delta(
    centroids: np.ndarray,
    basis_cells: np.ndarray,
    coefficients: np.ndarray,
    length_scale: float,
    max_abs_increment: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    basis_xy = centroids[basis_cells]
    output = np.zeros(centroids.shape[0], dtype=float)
    weight_sum = np.zeros(centroids.shape[0], dtype=float)
    nearest_distance = np.full(centroids.shape[0], math.nan, dtype=float)
    cutoff = 3.0 * length_scale
    for cell_index, xy in enumerate(centroids):
        distances = np.linalg.norm(basis_xy - xy, axis=1)
        nearest_distance[cell_index] = float(distances.min()) if distances.size else math.nan
        active = distances <= cutoff
        if not np.any(active):
            continue
        weights = np.exp(-0.5 * (distances[active] / length_scale) ** 2)
        denom = float(weights.sum())
        if denom <= 0.0 or not np.isfinite(denom):
            continue
        output[cell_index] = float(np.sum(weights * coefficients[active]) / denom)
        weight_sum[cell_index] = denom
    return np.clip(output, -max_abs_increment, max_abs_increment), weight_sum, nearest_distance


def apply_log10_increment(
    field: np.ndarray,
    increment: np.ndarray,
    min_eigenvalue: float,
    max_eigenvalue: float,
) -> tuple[np.ndarray, np.ndarray]:
    requested_scale = np.power(10.0, increment)
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
            output.update(prediction)
            observed = float(output["observed_log10_permeability_m2"])
            predicted = float(prediction["predicted_log10_permeability_m2"])
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


def build_samples(args: argparse.Namespace, anchor_coefficients: np.ndarray) -> list[dict[str, Any]]:
    rng = np.random.default_rng(args.seed)
    samples: list[dict[str, Any]] = []
    seen: set[tuple[int, int, int]] = set()
    index = 1

    for length in args.deterministic_length_m:
        if not (args.length_min_m <= length <= args.length_max_m):
            continue
        for shrink in args.deterministic_shrink:
            coeffs = np.clip(
                anchor_coefficients * float(shrink),
                -args.max_abs_log10_increment,
                args.max_abs_log10_increment,
            )
            key = (round(length * 1_000_000), round(shrink * 1_000_000), 0)
            if key in seen:
                continue
            seen.add(key)
            samples.append(
                {
                    "candidate_id": candidate_label(index, "det", float(length), float(shrink)),
                    "length_scale_m": float(length),
                    "global_shrink": float(shrink),
                    "sample_source": "deterministic_residual_shrink",
                    "coefficients": coeffs,
                }
            )
            index += 1

    log_min = math.log(args.length_min_m)
    log_max = math.log(args.length_max_m)
    for _ in range(args.sample_count):
        length = math.exp(float(rng.uniform(log_min, log_max)))
        shrink = float(rng.uniform(args.random_shrink_min, args.random_shrink_max))
        noise_scale = args.coefficient_noise_sigma * np.maximum(np.abs(anchor_coefficients), 0.25)
        coeffs = anchor_coefficients * shrink + rng.normal(0.0, noise_scale)
        coeffs = np.clip(coeffs, -args.max_abs_log10_increment, args.max_abs_log10_increment)
        samples.append(
            {
                "candidate_id": candidate_label(index, "rnd", length, shrink),
                "length_scale_m": float(length),
                "global_shrink": shrink,
                "sample_source": "random_local_basis_residual_sampler",
                "coefficients": coeffs,
            }
        )
        index += 1
    return samples


def write_candidate_mesh(
    mesh: meshio.Mesh,
    field_name: str,
    adjusted_field: np.ndarray,
    requested_increment: np.ndarray,
    applied_increment: np.ndarray,
    weight_sum: np.ndarray,
    nearest_distance: np.ndarray,
    output_mesh: Path,
) -> None:
    extras = {
        "k_local_basis_requested_log10_increment_rd": requested_increment.reshape((-1, 1)),
        "k_local_basis_applied_log10_increment_rd": applied_increment.reshape((-1, 1)),
        "k_local_basis_weight_sum_rd": weight_sum.reshape((-1, 1)),
        "k_local_basis_nearest_anchor_distance_m_rd": nearest_distance.reshape((-1, 1)),
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


def diverse_batch(results: pd.DataFrame, batch_size: int) -> pd.DataFrame:
    rows: list[pd.Series] = []
    seen_signatures: set[tuple[int, float, float, float]] = set()
    for _, row in results.iterrows():
        signature = (
            int(row["affected_cells"]),
            round(float(row["sum_squared_applied_log10_increment_all_cells"]), 8),
            round(float(row["applied_log10_increment_min"]), 8),
            round(float(row["applied_log10_increment_max"]), 8),
        )
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        rows.append(row)
        if len(rows) >= batch_size:
            break
    if len(rows) < batch_size:
        chosen = {str(row["candidate_id"]) for row in rows}
        for _, row in results.iterrows():
            if str(row["candidate_id"]) in chosen:
                continue
            rows.append(row)
            if len(rows) >= batch_size:
                break
    return pd.DataFrame(rows)


def write_markdown(path: Path, results: pd.DataFrame, summary: dict[str, Any]) -> None:
    best = summary["best_candidate"]
    lines = [
        "# Local-Basis Permeability Sampler Plan",
        "",
        "This artifact is a richer direct-objective sampler around the current",
        "incumbent permeability field. It keeps the GESA model frozen, perturbs only",
        "`k_i_rd` in run-local mesh files, and samples independent local residual",
        "basis coefficients around the mapped pulse-test support cells.",
        "",
        "The score here is the direct permeability pulse-test layer only. The emitted",
        "batch must be run through the existing OGS candidate-search harness before it",
        "can be compared on the combined permeability plus sampled-state objective.",
        "",
        "## Evidence",
        "",
        f"- Input mesh: `{summary['input_mesh']}`",
        f"- Basis anchor cells: {summary['basis_anchor_count']}",
        f"- Candidate fields scored: {summary['candidate_count']}",
        f"- Baseline direct objective: {summary['baseline_direct_objective']:.6f}",
        f"- Baseline weighted RMSE log10: {summary['baseline_weighted_rmse_log10']:.6f}",
        "",
        "## Best Direct Candidate",
        "",
        f"- Candidate: `{best['candidate_id']}`",
        f"- Length scale: {float(best['length_scale_m']):.5f} m",
        f"- Global shrink: {float(best['global_shrink']):.3f}",
        f"- Direct objective: {float(best['objective_value']):.6f}",
        f"- Direct objective delta vs baseline: {float(best['direct_objective_delta_vs_baseline']):+.6f}",
        f"- Weighted RMSE log10: {float(best['weighted_rmse_log10']):.6f}",
        "",
        "## Top Candidates",
        "",
        "| Rank | Candidate | Source | Length [m] | Shrink | Objective | Delta | RMSE |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in results.head(12).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row["rank_by_direct_objective"])),
                    f"`{row['candidate_id']}`",
                    str(row["sample_source"]),
                    f"{float(row['length_scale_m']):.5f}",
                    f"{float(row['global_shrink']):.3f}",
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
            "## Proposed Diverse OGS Batch",
            "",
            f"The proposed OGS execution batch is `{summary['next_candidate_batch_csv']}`.",
            "",
            "| Batch rank | Candidate | Affected cells | Objective | Delta |",
            "| ---: | --- | ---: | ---: | ---: |",
        ]
    )
    for index, row in enumerate(summary["execution_batch"], start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    f"`{row['candidate_id']}`",
                    str(int(row["affected_cells"])),
                    f"{float(row['objective_value']):.3f}",
                    f"{float(row['direct_objective_delta_vs_baseline']):+.3f}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "Use it with `run_inversion_candidate_search.py --ogs-mode execute` to get",
            "the combined objective.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    centroids = cell_centroids(mesh)
    _, anchors_all = build_anchor_table(baseline_field, targets_path, target_cells_path)
    anchors = select_basis_anchors(anchors_all, centroids, args.basis_count)
    basis_cells = anchors["lookup_cell_id"].to_numpy(dtype=int)
    anchor_coefficients = anchors["anchor_log10_shift"].to_numpy(dtype=float)
    anchor_coefficients = np.clip(anchor_coefficients, -args.max_abs_log10_increment, args.max_abs_log10_increment)

    targets = pd.read_csv(targets_path)
    target_cells = pd.read_csv(target_cells_path)
    cells_by_observation = {str(key): group.copy() for key, group in target_cells.groupby("observation_id")}

    baseline_score = score_field(baseline_field, targets, cells_by_observation, args.log10_sigma)
    baseline_direct_objective = float(baseline_score["objective_value"])
    samples = build_samples(args, anchor_coefficients)

    rows: list[dict[str, Any]] = []
    field_cache: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}
    for sample in samples:
        requested, weight_sum, nearest_distance = basis_average_delta(
            centroids,
            basis_cells,
            np.asarray(sample["coefficients"], dtype=float),
            float(sample["length_scale_m"]),
            args.max_abs_log10_increment,
        )
        adjusted_field, applied = apply_log10_increment(
            baseline_field,
            requested,
            args.min_k_eigenvalue,
            args.max_k_eigenvalue,
        )
        score = score_field(adjusted_field, targets, cells_by_observation, args.log10_sigma)
        affected = applied != 0.0
        rows.append(
            {
                "rank_by_direct_objective": 0,
                "candidate_id": sample["candidate_id"],
                "length_scale_m": sample["length_scale_m"],
                "global_shrink": sample["global_shrink"],
                "sample_source": sample["sample_source"],
                "basis_anchor_count": int(len(basis_cells)),
                "affected_cells": int(np.count_nonzero(affected)),
                "requested_log10_increment_min": float(np.nanmin(requested)),
                "requested_log10_increment_max": float(np.nanmax(requested)),
                "applied_log10_increment_min": float(np.nanmin(applied)),
                "applied_log10_increment_max": float(np.nanmax(applied)),
                "mean_abs_applied_log10_increment_affected": float(np.nanmean(np.abs(applied[affected]))) if np.any(affected) else 0.0,
                "sum_squared_applied_log10_increment_all_cells": float(np.nansum(applied**2)),
                "objective_value": score["objective_value"],
                "weighted_rmse_log10": score["weighted_rmse_log10"],
                "weighted_mean_abs_log10_residual": score["weighted_mean_abs_log10_residual"],
                "max_abs_log10_residual": score["max_abs_log10_residual"],
                "used_in_objective_rows": score["used_in_objective_rows"],
                "effective_objective_weight": score["effective_objective_weight"],
                "direct_objective_delta_vs_baseline": float(score["objective_value"]) - baseline_direct_objective,
            }
        )
        field_cache[sample["candidate_id"]] = (adjusted_field, requested, applied, weight_sum, nearest_distance)

    results = pd.DataFrame(rows).sort_values(
        ["objective_value", "sum_squared_applied_log10_increment_all_cells", "candidate_id"]
    ).reset_index(drop=True)
    results["rank_by_direct_objective"] = range(1, results.shape[0] + 1)
    top = results.head(args.max_proposals).copy()

    for _, row in top.iterrows():
        candidate_id = str(row["candidate_id"])
        candidate_dir = output_dir / candidate_id
        mesh_path = candidate_dir / "bulk_w_projections.vtu"
        adjusted_field, requested, applied, weight_sum, nearest_distance = field_cache[candidate_id]
        write_candidate_mesh(mesh, args.field_name, adjusted_field, requested, applied, weight_sum, nearest_distance, mesh_path)
        evaluation, official_summary = evaluate_targets(
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
        summary_path.write_text(json.dumps(json_ready(official_summary), indent=2, sort_keys=True), encoding="utf-8")
        results.loc[results["candidate_id"] == candidate_id, "mesh"] = str(mesh_path)
        results.loc[results["candidate_id"] == candidate_id, "evaluation_csv"] = str(evaluation_path)
        results.loc[results["candidate_id"] == candidate_id, "summary_json"] = str(summary_path)

    top = results.head(args.max_proposals).copy()
    batch = diverse_batch(results, args.execution_batch_size).copy()
    batch["execution_batch_rank"] = range(1, batch.shape[0] + 1)
    results_path = output_dir / "local_basis_sampler_scores.csv"
    batch_path = output_dir / "next_local_basis_candidate_batch.csv"
    summary_json_path = output_dir / "LOCAL_BASIS_SAMPLER_PLAN.json"
    summary_md_path = output_dir / "LOCAL_BASIS_SAMPLER_PLAN.md"
    anchor_path = output_dir / "basis_anchor_cells.csv"
    results.to_csv(results_path, index=False)
    batch.to_csv(batch_path, index=False)
    anchors.to_csv(anchor_path, index=False)

    summary = {
        "input_mesh": str(input_mesh),
        "output_dir": str(output_dir),
        "field_name": args.field_name,
        "targets": str(targets_path),
        "target_cells": str(target_cells_path),
        "basis_anchor_count": int(len(basis_cells)),
        "candidate_count": int(results.shape[0]),
        "proposal_count": int(top.shape[0]),
        "execution_batch_size": int(args.execution_batch_size),
        "results_csv": str(results_path),
        "next_candidate_batch_csv": str(batch_path),
        "basis_anchor_cells_csv": str(anchor_path),
        "summary_markdown": str(summary_md_path),
        "baseline_direct_objective": baseline_direct_objective,
        "baseline_weighted_rmse_log10": baseline_score["weighted_rmse_log10"],
        "best_candidate": json_ready(results.iloc[0].to_dict()),
        "top_candidates": [json_ready(row) for row in top.to_dict(orient="records")],
        "execution_batch": [json_ready(row) for row in batch.to_dict(orient="records")],
        "notes": [
            "Direct pulse-test local-basis sampler only; OGS state outputs are not evaluated here.",
            "Independent local coefficients are sampled around residual-derived anchor shifts.",
            "Use next_local_basis_candidate_batch.csv with run_inversion_candidate_search.py for combined OGS-backed scoring.",
        ],
    }
    summary_json_path.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(summary_md_path, top, summary)

    print(f"wrote {results_path}")
    print(f"wrote {batch_path}")
    print(f"wrote {summary_json_path}")
    print(f"wrote {summary_md_path}")
    print(f"best candidate: {results.iloc[0]['candidate_id']}")
    print(f"best direct objective: {float(results.iloc[0]['objective_value']):.6g}")


if __name__ == "__main__":
    main()
