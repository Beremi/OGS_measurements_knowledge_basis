#!/usr/bin/env python3
"""Build cross-stream hybrid permeability fields around the active incumbent.

The current active sampler is paused because additional smooth-family OGS runs did
not improve the incumbent.  This script makes a cheap next-field-family screen: it
geometrically blends the active incumbent's permeability magnitude with magnitude
patterns from the cross-stream diagnostic winners, while preserving the active
field's tensor orientation and anisotropy ratio.

The output fields are direct-permeability screens only.  They do not promote ERT,
Taupe/TDR, or offset-robust NMR diagnostics into the likelihood and they do not run
OGS.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import meshio
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_permeability_targets import evaluate_targets  # noqa: E402
from fit_smooth_permeability_field_from_targets import make_cell_data, read_cell_field  # noqa: E402


TARGET_ROLE_ORDER = [
    "mean_rank_all_streams",
    "mean_rank_diagnostics_only",
    "worst_rank_all_streams",
    "ert",
    "nmr_label_bias",
    "nmr_trend_anomaly",
    "taupe",
    "mean_normalized_loss_all_streams",
]

SOURCE_SCORE_COLUMNS = [
    "current_combined_objective",
    "label_bias_combined_objective",
    "trend_anomaly_combined_objective",
    "ert_residual_mae_log10",
    "taupe_trend_mae",
    "active_objective_rank",
    "nmr_label_bias_rank",
    "nmr_trend_anomaly_rank",
    "ert_mae_rank",
    "taupe_mae_rank",
    "mean_rank_all_streams",
    "mean_rank_diagnostics_only",
    "worst_rank_all_streams",
    "top10_stream_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scorecard-summary",
        type=Path,
        default=Path("inversion_workflow/cross_stream_candidate_scorecard_summary.json"),
    )
    parser.add_argument(
        "--scorecard-csv",
        type=Path,
        default=Path("inversion_workflow/cross_stream_candidate_scorecard.csv"),
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("inversion_workflow/runs"),
    )
    parser.add_argument(
        "--active-run-id",
        default="",
        help="Override the active incumbent run id. Defaults to the scorecard active incumbent.",
    )
    parser.add_argument("--field-name", default="k_i_rd")
    parser.add_argument("--magnitude-field-name", default="k_mag_rd")
    parser.add_argument(
        "--magnitude-source",
        choices=["tensor_geometric_mean", "stored_field"],
        default="tensor_geometric_mean",
        help=(
            "Use the geometric mean derived from k_i_rd by default. Some executed runs "
            "carry an unchanged k_mag_rd metadata field even when k_i_rd changes."
        ),
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
        default=Path("inversion_workflow/runs/cross_stream_hybrid_field_plan"),
    )
    parser.add_argument("--alpha", type=float, nargs="*", default=[0.25, 0.50, 0.75])
    parser.add_argument("--include-endpoints", action="store_true")
    parser.add_argument("--log10-sigma", type=float, default=0.5)
    parser.add_argument("--batch-size", type=int, default=3)
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


def safe_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return cleaned or "target"


def alpha_label(alpha: float) -> str:
    return f"{alpha:.2f}".replace(".", "p").replace("-", "m")


def first_cell_signature(mesh: meshio.Mesh) -> tuple[str, tuple[int, ...], int]:
    if not mesh.cells:
        raise ValueError("mesh contains no cells")
    block = mesh.cells[0]
    return block.type, tuple(np.asarray(block.data).shape), int(mesh.points.shape[0])


def read_scalar_cell_field(mesh: meshio.Mesh, field_name: str) -> np.ndarray:
    if not mesh.cells:
        raise ValueError("mesh contains no cells")
    cell_type = mesh.cells[0].type
    try:
        field = np.asarray(mesh.cell_data_dict[field_name][cell_type], dtype=float)
    except KeyError as exc:
        available = sorted(mesh.cell_data_dict.keys())
        raise KeyError(f"field {field_name!r} not found; available: {available}") from exc
    if field.ndim == 2 and field.shape[1] == 1:
        field = field[:, 0]
    if field.ndim != 1:
        raise ValueError(f"field {field_name!r} must be scalar; got shape {field.shape}")
    return field


def tensor_geometric_magnitude(field: np.ndarray) -> np.ndarray:
    if field.ndim == 1 or field.shape[1] == 1:
        magnitude = np.asarray(field, dtype=float).reshape(-1)
    elif field.shape[1] == 4:
        determinant = field[:, 0] * field[:, 3] - field[:, 1] * field[:, 2]
        magnitude = np.sqrt(determinant)
    else:
        raise ValueError(f"k_i_rd must be scalar or four-component tensor; got shape {field.shape}")
    if np.any(magnitude <= 0.0) or not np.isfinite(magnitude).all():
        raise ValueError("derived permeability magnitude must be positive and finite")
    return magnitude


def magnitude_for_mesh(mesh: meshio.Mesh, field: np.ndarray, field_name: str, source: str) -> np.ndarray:
    if source == "stored_field":
        return read_scalar_cell_field(mesh, field_name)
    return tensor_geometric_magnitude(field)


def scorecard_rows_by_run(scorecard_csv: Path) -> dict[str, dict[str, Any]]:
    if not scorecard_csv.exists():
        return {}
    frame = pd.read_csv(scorecard_csv)
    if "run_id" not in frame.columns:
        return {}
    return {
        str(row["run_id"]): json_ready(row)
        for row in frame.to_dict(orient="records")
        if pd.notna(row.get("run_id"))
    }


def select_targets(summary: dict[str, Any], score_rows: dict[str, dict[str, Any]], active_run_id: str) -> list[dict[str, Any]]:
    winners = summary.get("stream_winners", {})
    grouped: dict[str, dict[str, Any]] = {}
    for role in TARGET_ROLE_ORDER:
        row = winners.get(role, {})
        if not isinstance(row, dict):
            continue
        run_id = str(row.get("run_id") or "").strip()
        if not run_id or run_id == active_run_id:
            continue
        if run_id not in grouped:
            source_row = dict(score_rows.get(run_id, row))
            grouped[run_id] = {
                "target_run_id": run_id,
                "target_roles": [],
                "source_scorecard_row": source_row,
            }
        grouped[run_id]["target_roles"].append(role)

    targets = []
    for index, item in enumerate(grouped.values(), start=1):
        primary = str(item["target_roles"][0])
        label = primary if len(item["target_roles"]) == 1 else f"{primary}_plus{len(item['target_roles']) - 1}"
        item["target_index"] = index
        item["target_label"] = safe_id(label)
        targets.append(item)
    return targets


def check_compatible_mesh(active: meshio.Mesh, target: meshio.Mesh, active_path: Path, target_path: Path) -> None:
    active_sig = first_cell_signature(active)
    target_sig = first_cell_signature(target)
    if active_sig != target_sig:
        raise ValueError(
            f"mesh signatures differ: {active_path} has {active_sig}, {target_path} has {target_sig}"
        )
    if len(active.cells) != len(target.cells):
        raise ValueError(f"mesh cell block counts differ: {active_path} vs {target_path}")
    for active_block, target_block in zip(active.cells, target.cells):
        if active_block.type != target_block.type or not np.array_equal(active_block.data, target_block.data):
            raise ValueError(f"mesh cell connectivity differs: {active_path} vs {target_path}")


def write_hybrid_mesh(
    active_mesh: meshio.Mesh,
    field_name: str,
    magnitude_field_name: str,
    hybrid_field: np.ndarray,
    hybrid_magnitude: np.ndarray,
    alpha: float,
    target_delta: np.ndarray,
    applied_delta: np.ndarray,
    target_index: int,
    output_mesh: Path,
) -> None:
    extras = {
        magnitude_field_name: hybrid_magnitude,
        "k_cross_stream_hybrid_alpha_rd": np.full(hybrid_magnitude.shape[0], float(alpha)),
        "k_cross_stream_hybrid_log10_multiplier_rd": applied_delta,
        "k_cross_stream_hybrid_target_log10_delta_rd": target_delta,
        "k_cross_stream_hybrid_target_index_rd": np.full(hybrid_magnitude.shape[0], int(target_index)),
    }
    output_mesh.parent.mkdir(parents=True, exist_ok=True)
    meshio.write_points_cells(
        output_mesh,
        active_mesh.points,
        active_mesh.cells,
        point_data=active_mesh.point_data,
        cell_data=make_cell_data(active_mesh, field_name, hybrid_field, extras),
        field_data=active_mesh.field_data,
    )


def candidate_priority(row: pd.Series) -> float:
    delta = float(row.get("direct_objective_delta_vs_active", np.inf))
    worst_rank = row.get("source_worst_rank_all_streams", np.nan)
    mean_rank = row.get("source_mean_rank_all_streams", np.nan)
    alpha = float(row.get("alpha", 0.5))
    rank_penalty = 0.0
    if np.isfinite(worst_rank):
        rank_penalty += 0.01 * float(worst_rank)
    if np.isfinite(mean_rank):
        rank_penalty += 0.002 * float(mean_rank)
    return delta + rank_penalty + 0.001 * abs(alpha - 0.5)


def diverse_batch(results: pd.DataFrame, batch_size: int) -> pd.DataFrame:
    rows: list[pd.Series] = []
    seen_targets: set[str] = set()
    ordered = results.sort_values(["execution_priority_score", "objective_value", "candidate_id"])
    for _, row in ordered.iterrows():
        target_run = str(row["target_run_id"])
        if target_run in seen_targets:
            continue
        rows.append(row)
        seen_targets.add(target_run)
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
    best = summary.get("best_direct_candidate", {})
    lines = [
        "# Cross-Stream Hybrid Field Plan",
        "",
        "This artifact screens a new permeability-field family after the active production sampler pause.",
        "It blends the active incumbent's log-magnitude field with the magnitude patterns of cross-stream",
        "diagnostic winners, while preserving the active tensor orientation and anisotropy ratio.",
        "",
        "The score is the direct permeability pulse-test layer only. These fields have not been run through",
        "OGS and do not change the active likelihood or promote gated diagnostic streams.",
        "",
        "## Evidence",
        "",
        f"- Active run: `{summary['active_run_id']}`",
        f"- Active mesh: `{summary['active_mesh']}`",
        f"- Magnitude source: `{summary['magnitude_source']}`",
        f"- Target winner runs: {summary['target_run_count']}",
        f"- Candidate fields screened: {summary['candidate_count']}",
        f"- Active direct objective: {float(summary['active_direct_objective']):.6f}",
        f"- Active weighted RMSE log10: {float(summary['active_weighted_rmse_log10']):.6f}",
        f"- Activation gate: {summary['activation_gate']}",
        "",
        "## Best Direct Hybrid",
        "",
        f"- Candidate: `{best.get('candidate_id')}`",
        f"- Target run: `{best.get('target_run_id')}`",
        f"- Target roles: `{best.get('target_roles')}`",
        f"- Blend alpha: {float(best.get('alpha', np.nan)):.2f}",
        f"- Direct objective: {float(best.get('objective_value', np.nan)):.6f}",
        f"- Delta versus active: {float(best.get('direct_objective_delta_vs_active', np.nan)):+.6f}",
        f"- Weighted RMSE log10: {float(best.get('weighted_rmse_log10', np.nan)):.6f}",
        "",
        "## Top Screened Fields",
        "",
        "| Rank | Candidate | Target roles | Alpha | Objective | Delta | RMSE | Source ranks |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for _, row in results.head(12).iterrows():
        ranks = (
            f"A={row.get('source_active_objective_rank')}, "
            f"NMR={row.get('source_nmr_label_bias_rank')}, "
            f"ERT={row.get('source_ert_mae_rank')}, "
            f"Taupe={row.get('source_taupe_mae_rank')}"
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row["rank_by_direct_objective"])),
                    f"`{row['candidate_id']}`",
                    f"`{row['target_roles']}`",
                    f"{float(row['alpha']):.2f}",
                    f"{float(row['objective_value']):.3f}",
                    f"{float(row['direct_objective_delta_vs_active']):+.3f}",
                    f"{float(row['weighted_rmse_log10']):.3f}",
                    ranks,
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
            "| Batch rank | Candidate | Target run | Alpha | Objective | Delta | Priority score |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in batch.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row["execution_batch_rank"])),
                    f"`{row['candidate_id']}`",
                    f"`{row['target_run_id']}`",
                    f"{float(row['alpha']):.2f}",
                    f"{float(row['objective_value']):.3f}",
                    f"{float(row['direct_objective_delta_vs_active']):+.3f}",
                    f"{float(row['execution_priority_score']):.3f}",
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
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[2]
    output_dir = resolve(repo, args.output_dir).resolve()
    scorecard_summary_path = resolve(repo, args.scorecard_summary).resolve()
    scorecard_csv_path = resolve(repo, args.scorecard_csv).resolve()
    runs_dir = resolve(repo, args.runs_dir).resolve()
    targets_path = resolve(repo, args.targets).resolve()
    target_cells_path = resolve(repo, args.target_cells).resolve()

    if output_dir.exists() and any(output_dir.iterdir()) and not args.overwrite:
        raise SystemExit(f"output directory exists, pass --overwrite to replace/update: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    scorecard_summary = read_json(scorecard_summary_path)
    active_run_id = (
        args.active_run_id.strip()
        or str(scorecard_summary.get("active_incumbent_cross_stream", {}).get("run_id") or "")
        or "local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000"
    )
    active_mesh_path = runs_dir / active_run_id / "bulk_w_projections.vtu"
    if not active_mesh_path.exists():
        raise FileNotFoundError(f"active mesh not found: {active_mesh_path}")

    score_rows = scorecard_rows_by_run(scorecard_csv_path)
    target_specs = select_targets(scorecard_summary, score_rows, active_run_id)
    if not target_specs:
        raise SystemExit("no non-active cross-stream winner targets found in scorecard summary")

    alphas = sorted({float(alpha) for alpha in args.alpha})
    if args.include_endpoints:
        alphas = sorted({0.0, 1.0, *alphas})
    if any(alpha < 0.0 or alpha > 1.0 for alpha in alphas):
        raise ValueError("all alpha values must lie in [0, 1]")

    active_mesh = meshio.read(active_mesh_path)
    active_field = read_cell_field(active_mesh, args.field_name)
    active_magnitude = magnitude_for_mesh(
        active_mesh,
        active_field,
        args.magnitude_field_name,
        args.magnitude_source,
    )
    active_stored_magnitude = read_scalar_cell_field(active_mesh, args.magnitude_field_name)
    if active_field.shape[0] != active_magnitude.shape[0]:
        raise ValueError("active tensor and magnitude fields have different cell counts")
    if np.any(active_magnitude <= 0.0) or not np.isfinite(active_magnitude).all():
        raise ValueError(f"active magnitude field {args.magnitude_field_name!r} must be positive and finite")

    active_evaluation, active_direct_summary = evaluate_targets(
        mesh_path=active_mesh_path,
        field_name=args.field_name,
        targets_path=targets_path,
        target_cells_path=target_cells_path,
        log10_sigma=args.log10_sigma,
        include_non_usable=True,
    )
    active_evaluation.to_csv(output_dir / "active_incumbent_permeability_fit_evaluation.csv", index=False)
    (output_dir / "active_incumbent_permeability_fit_summary.json").write_text(
        json.dumps(json_ready(active_direct_summary), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    active_direct_objective = float(active_direct_summary["objective_value"])

    rows: list[dict[str, Any]] = []
    generated_targets: list[dict[str, Any]] = []
    for spec in target_specs:
        target_run_id = str(spec["target_run_id"])
        target_mesh_path = runs_dir / target_run_id / "bulk_w_projections.vtu"
        if not target_mesh_path.exists():
            generated_targets.append({**spec, "status": "missing_mesh", "mesh": str(target_mesh_path)})
            continue

        target_mesh = meshio.read(target_mesh_path)
        check_compatible_mesh(active_mesh, target_mesh, active_mesh_path, target_mesh_path)
        target_field = read_cell_field(target_mesh, args.field_name)
        target_magnitude = magnitude_for_mesh(
            target_mesh,
            target_field,
            args.magnitude_field_name,
            args.magnitude_source,
        )
        target_stored_magnitude = read_scalar_cell_field(target_mesh, args.magnitude_field_name)
        if target_magnitude.shape[0] != active_magnitude.shape[0]:
            raise ValueError(f"target magnitude cell count mismatch: {target_mesh_path}")
        if np.any(target_magnitude <= 0.0) or not np.isfinite(target_magnitude).all():
            raise ValueError(f"target magnitude field {args.magnitude_field_name!r} must be positive and finite")

        target_log_delta = np.log10(target_magnitude) - np.log10(active_magnitude)
        generated_targets.append(
            {
                **spec,
                "status": "available",
                "mesh": str(target_mesh_path),
                "target_log10_delta_min": float(np.min(target_log_delta)),
                "target_log10_delta_max": float(np.max(target_log_delta)),
                "target_log10_delta_mean_abs": float(np.mean(np.abs(target_log_delta))),
                "stored_k_mag_max_abs_delta_vs_active": float(
                    np.max(np.abs(target_stored_magnitude - active_stored_magnitude))
                ),
            }
        )

        target_roles = ";".join(str(role) for role in spec["target_roles"])
        source_row = dict(spec.get("source_scorecard_row", {}))
        for alpha in alphas:
            applied_delta = float(alpha) * target_log_delta
            scale = np.power(10.0, applied_delta)
            hybrid_field = active_field * scale[:, None]
            hybrid_magnitude = active_magnitude * scale
            candidate_id = f"cross_hybrid_{spec['target_label']}_a{alpha_label(alpha)}"
            candidate_dir = output_dir / candidate_id
            mesh_path = candidate_dir / "bulk_w_projections.vtu"
            write_hybrid_mesh(
                active_mesh,
                args.field_name,
                args.magnitude_field_name,
                hybrid_field,
                hybrid_magnitude,
                float(alpha),
                target_log_delta,
                applied_delta,
                int(spec["target_index"]),
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

            row: dict[str, Any] = {
                "candidate_id": candidate_id,
                "target_run_id": target_run_id,
                "target_roles": target_roles,
                "target_index": int(spec["target_index"]),
                "alpha": float(alpha),
                "mesh": str(mesh_path),
                "evaluation_csv": str(evaluation_path),
                "summary_json": str(summary_path),
                "objective_value": direct_summary.get("objective_value"),
                "weighted_rmse_log10": direct_summary.get("weighted_rmse_log10"),
                "weighted_mean_abs_log10_residual": direct_summary.get("weighted_mean_abs_log10_residual"),
                "max_abs_log10_residual": direct_summary.get("max_abs_log10_residual"),
                "used_in_objective_rows": direct_summary.get("used_in_objective_rows"),
                "effective_objective_weight": direct_summary.get("effective_objective_weight"),
                "direct_objective_delta_vs_active": float(direct_summary["objective_value"]) - active_direct_objective,
                "target_log10_delta_min": float(np.min(target_log_delta)),
                "target_log10_delta_max": float(np.max(target_log_delta)),
                "applied_log10_delta_min": float(np.min(applied_delta)),
                "applied_log10_delta_max": float(np.max(applied_delta)),
                "applied_log10_delta_mean_abs": float(np.mean(np.abs(applied_delta))),
            }
            for column in SOURCE_SCORE_COLUMNS:
                row[f"source_{column}"] = source_row.get(column)
            rows.append(row)

    if not rows:
        raise SystemExit("no hybrid candidates could be generated")

    results = pd.DataFrame(rows)
    results["objective_value"] = pd.to_numeric(results["objective_value"], errors="coerce")
    results = results.sort_values(["objective_value", "candidate_id"], na_position="last").reset_index(drop=True)
    results["rank_by_direct_objective"] = range(1, results.shape[0] + 1)
    results["execution_priority_score"] = results.apply(candidate_priority, axis=1)
    results = results.sort_values(["rank_by_direct_objective", "execution_priority_score", "candidate_id"]).reset_index(drop=True)

    batch = diverse_batch(results, args.batch_size).copy()
    batch["execution_batch_rank"] = range(1, batch.shape[0] + 1)

    scores_path = output_dir / "cross_stream_hybrid_candidate_scores.csv"
    batch_path = output_dir / "next_cross_stream_hybrid_candidate_batch.csv"
    target_path = output_dir / "cross_stream_hybrid_targets.json"
    summary_json_path = output_dir / "CROSS_STREAM_HYBRID_FIELD_PLAN.json"
    summary_md_path = output_dir / "CROSS_STREAM_HYBRID_FIELD_PLAN.md"
    results.to_csv(scores_path, index=False)
    batch.to_csv(batch_path, index=False)
    target_path.write_text(json.dumps(json_ready(generated_targets), indent=2, sort_keys=True), encoding="utf-8")

    best = json_ready(results.iloc[0].to_dict())
    best_delta = float(best["direct_objective_delta_vs_active"])
    if best_delta < 0.0:
        interpretation = (
            "At least one hybrid improves the direct permeability screen, so the top diverse rows are "
            "defensible candidates for a deliberate OGS diagnostic batch. They are not final-field "
            "evidence until release-gated OGS outputs and the active combined objective are evaluated."
        )
    else:
        interpretation = (
            "No hybrid improves the direct permeability screen. The generated fields are useful only "
            "as deliberate diagnostic probes of cross-stream magnitude patterns; they do not justify "
            "spending OGS runs on the active objective alone."
        )

    summary = {
        "status": "cross_stream_hybrid_field_plan_generated_not_executed",
        "active_run_id": active_run_id,
        "active_mesh": str(active_mesh_path),
        "field_name": args.field_name,
        "magnitude_field_name": args.magnitude_field_name,
        "magnitude_source": args.magnitude_source,
        "scorecard_summary": str(scorecard_summary_path),
        "scorecard_csv": str(scorecard_csv_path),
        "targets": str(targets_path),
        "target_cells": str(target_cells_path),
        "output_dir": str(output_dir),
        "target_run_count": int(sum(1 for item in generated_targets if item.get("status") == "available")),
        "target_runs": json_ready(generated_targets),
        "alpha_values": alphas,
        "candidate_count": int(results.shape[0]),
        "active_direct_objective": active_direct_objective,
        "active_weighted_rmse_log10": active_direct_summary.get("weighted_rmse_log10"),
        "best_direct_candidate": best,
        "best_direct_objective": best.get("objective_value"),
        "best_direct_delta_vs_active": best.get("direct_objective_delta_vs_active"),
        "recommended_execution_batch_size": int(batch.shape[0]),
        "results_csv": str(scores_path),
        "next_candidate_batch_csv": str(batch_path),
        "target_manifest_json": str(target_path),
        "summary_markdown": str(summary_md_path),
        "activation_gate": (
            "Planning and direct-permeability screen only; execute with the existing OGS candidate harness "
            "only after deciding that cross-stream diagnostic probing is worth a release-gated run batch."
        ),
        "interpretation": interpretation,
        "notes": [
            "The hybrid changes only the run-local k_i_rd magnitude by geometric interpolation in log10 space.",
            "The active tensor orientation and anisotropy ratio are preserved by scalar multiplication of each tensor.",
            "By default the magnitude is derived from k_i_rd because stored k_mag_rd metadata is unchanged across some executed runs.",
            "ERT, Taupe/TDR, and NMR diagnostic winners remain gated diagnostics; their ranks only choose target patterns.",
        ],
    }
    summary_json_path.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(summary_md_path, results, batch, summary)

    print(f"wrote {scores_path}")
    print(f"wrote {batch_path}")
    print(f"wrote {summary_json_path}")
    print(f"wrote {summary_md_path}")
    print(f"best candidate: {best['candidate_id']}")
    print(f"best direct objective: {float(best['objective_value']):.6g}")
    print(f"best delta vs active: {best_delta:+.6g}")


if __name__ == "__main__":
    main()
