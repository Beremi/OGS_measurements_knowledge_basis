#!/usr/bin/env python3
"""Compare conditional scenario-winning permeability fields cell by cell."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import meshio
import numpy as np


THRESHOLDS = [
    (1e-6, "1em06"),
    (0.01, "0p01"),
    (0.05, "0p05"),
    (0.10, "0p10"),
    (0.25, "0p25"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate-summary",
        type=Path,
        default=Path("inversion_workflow/conditional_field_candidates/CONDITIONAL_FIELD_CANDIDATES_SUMMARY.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/conditional_field_candidates"),
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return json_ready(value.tolist())
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if not math.isfinite(float(value)) else float(value)
    return value


def triangle6_block(mesh: meshio.Mesh) -> np.ndarray:
    for block in mesh.cells:
        if block.type == "triangle6":
            return np.asarray(block.data)
    raise ValueError("Mesh has no triangle6 cell block")


def triangle6_centroids_and_areas(mesh: meshio.Mesh) -> tuple[np.ndarray, np.ndarray]:
    cells = triangle6_block(mesh)
    points = mesh.points[cells[:, :3], :2]
    centroids = points.mean(axis=1)
    a = points[:, 0, :]
    b = points[:, 1, :]
    c = points[:, 2, :]
    ab = b - a
    ac = c - a
    cross_z = ab[:, 0] * ac[:, 1] - ab[:, 1] * ac[:, 0]
    area = 0.5 * np.abs(cross_z)
    return centroids, area


def load_field(path: Path) -> dict[str, Any]:
    mesh = meshio.read(path)
    data = mesh.cell_data_dict
    if "k_i_rd" not in data or "triangle6" not in data["k_i_rd"]:
        raise ValueError(f"{path} lacks triangle6 k_i_rd")
    k = np.asarray(data["k_i_rd"]["triangle6"], dtype=float)
    if k.ndim != 2 or k.shape[1] != 4:
        raise ValueError(f"{path} k_i_rd has shape {k.shape}; expected (n, 4)")
    eig = np.linalg.eigvalsh(k.reshape((-1, 2, 2)))
    log_min = np.log10(eig[:, 0])
    log_max = np.log10(eig[:, 1])
    return {
        "mesh": mesh,
        "k": k,
        "log_min": log_min,
        "log_max": log_max,
        "log_geom": 0.5 * (log_min + log_max),
        "ratio": eig[:, 1] / eig[:, 0],
    }


def quantile_stats(values: np.ndarray, prefix: str) -> dict[str, float | int]:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return {f"{prefix}_finite_count": 0}
    quantiles = np.quantile(finite, [0.0, 0.05, 0.5, 0.95, 1.0])
    return {
        f"{prefix}_finite_count": int(finite.size),
        f"{prefix}_min": float(quantiles[0]),
        f"{prefix}_p05": float(quantiles[1]),
        f"{prefix}_p50": float(quantiles[2]),
        f"{prefix}_p95": float(quantiles[3]),
        f"{prefix}_max": float(quantiles[4]),
        f"{prefix}_mean": float(np.mean(finite)),
        f"{prefix}_mean_abs": float(np.mean(np.abs(finite))),
        f"{prefix}_max_abs": float(np.max(np.abs(finite))),
    }


def compare_candidate(
    candidate: dict[str, Any],
    reference: dict[str, Any],
    centroids: np.ndarray,
    areas: np.ndarray,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    run_id = candidate["run_id"]
    field = load_field(Path(candidate["packaged_mesh"]))
    if field["k"].shape != reference["k"].shape:
        raise ValueError(f"{run_id} shape {field['k'].shape} differs from reference {reference['k'].shape}")
    delta = field["log_geom"] - reference["log_geom"]
    abs_delta = np.abs(delta)
    with np.errstate(divide="ignore", invalid="ignore"):
        tensor_rel_fro = np.linalg.norm(field["k"] - reference["k"], axis=1) / np.linalg.norm(reference["k"], axis=1)
    summary = {
        "run_id": run_id,
        "run_kind": candidate.get("run_kind"),
        "scenario_count": candidate.get("scenario_count"),
        "scenario_ids": ";".join(candidate.get("scenario_ids", [])),
        "cell_count": int(delta.size),
        "area_m2": float(np.sum(areas)),
        "area_weighted_mean_delta_log10_k_geom": float(np.average(delta, weights=areas)),
        "area_weighted_mean_abs_delta_log10_k_geom": float(np.average(abs_delta, weights=areas)),
        "area_weighted_rms_delta_log10_k_geom": float(np.sqrt(np.average(delta * delta, weights=areas))),
        "max_abs_delta_cell_id": int(np.argmax(abs_delta)),
    }
    summary.update(quantile_stats(delta, "delta_log10_k_geom"))
    summary.update(quantile_stats(tensor_rel_fro, "relative_tensor_frobenius"))
    for threshold, key in THRESHOLDS:
        mask = abs_delta > threshold
        summary[f"cells_abs_delta_gt_{key}"] = int(np.sum(mask))
        summary[f"area_m2_abs_delta_gt_{key}"] = float(np.sum(areas[mask]))
    top_indices = np.argsort(-abs_delta)[:25]
    top_rows: list[dict[str, Any]] = []
    for rank, index in enumerate(top_indices, start=1):
        top_rows.append(
            {
                "run_id": run_id,
                "rank": rank,
                "cell_id": int(index),
                "centroid_x_m": float(centroids[index, 0]),
                "centroid_y_m": float(centroids[index, 1]),
                "cell_area_m2": float(areas[index]),
                "reference_log10_k_geom": float(reference["log_geom"][index]),
                "candidate_log10_k_geom": float(field["log_geom"][index]),
                "delta_log10_k_geom": float(delta[index]),
                "abs_delta_log10_k_geom": float(abs_delta[index]),
                "reference_log10_k_min": float(reference["log_min"][index]),
                "candidate_log10_k_min": float(field["log_min"][index]),
                "reference_log10_k_max": float(reference["log_max"][index]),
                "candidate_log10_k_max": float(field["log_max"][index]),
                "relative_tensor_frobenius": float(tensor_rel_fro[index]),
            }
        )
    return summary, top_rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Conditional Field Difference Audit",
        "",
        "This audit compares every conditional scenario-winning permeability field to",
        "the current active-objective field using the geometric-mean log10",
        "permeability of the `k_i_rd` tensor in each mesh cell.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Reference run: `{summary['reference_run_id']}`",
        f"- Compared candidate fields: {summary['compared_candidate_count']}",
        f"- Cell count per field: {summary['cell_count']}",
        "",
        "## Candidate Differences",
        "",
        "| Candidate | Scenarios | Mean abs delta log10 k | RMS delta log10 k | Max abs delta | Cells >0.05 log10 | Cells >0.10 log10 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["candidate_summaries"]:
        lines.append(
            f"| `{row['run_id']}` | {row['scenario_ids']} | "
            f"{row['delta_log10_k_geom_mean_abs']:.6g} | "
            f"{row['area_weighted_rms_delta_log10_k_geom']:.6g} | "
            f"{row['delta_log10_k_geom_max_abs']:.6g} | "
            f"{row['cells_abs_delta_gt_0p05']} | {row['cells_abs_delta_gt_0p10']} |"
        )
    lines.extend(["", "## Interpretation", ""])
    for item in summary["interpretation"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Files",
            "",
            f"- Candidate summary CSV: `{summary['summary_csv']}`",
            f"- Top changed cells CSV: `{summary['top_cells_csv']}`",
            f"- JSON summary: `{summary['summary_json']}`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_audit(args: argparse.Namespace) -> dict[str, Any]:
    package = read_json(args.candidate_summary)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    reference_run_id = package.get("current_run_id")
    candidates = package.get("candidates", [])
    reference_candidate = next((candidate for candidate in candidates if candidate.get("run_id") == reference_run_id), None)
    if not reference_candidate:
        raise ValueError(f"Reference run {reference_run_id} not found in candidate package")
    reference = load_field(Path(reference_candidate["packaged_mesh"]))
    centroids, areas = triangle6_centroids_and_areas(reference["mesh"])

    summary_rows: list[dict[str, Any]] = []
    top_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        if candidate.get("run_id") == reference_run_id:
            continue
        candidate_summary, candidate_top_rows = compare_candidate(candidate, reference, centroids, areas)
        summary_rows.append(candidate_summary)
        top_rows.extend(candidate_top_rows)
    summary_rows = sorted(summary_rows, key=lambda row: row["delta_log10_k_geom_mean_abs"], reverse=True)
    summary_csv = output_dir / "conditional_field_difference_summary.csv"
    top_cells_csv = output_dir / "conditional_field_difference_top_cells.csv"
    summary_json = output_dir / "CONDITIONAL_FIELD_DIFFERENCE_AUDIT.json"
    markdown = output_dir / "CONDITIONAL_FIELD_DIFFERENCE_AUDIT.md"
    write_csv(summary_csv, summary_rows)
    write_csv(top_cells_csv, top_rows)
    max_mean_abs = max((row["delta_log10_k_geom_mean_abs"] for row in summary_rows), default=0.0)
    max_changed_gt_005 = max((row["cells_abs_delta_gt_0p05"] for row in summary_rows), default=0)
    max_changed_gt_010 = max((row["cells_abs_delta_gt_0p10"] for row in summary_rows), default=0)
    summary = {
        "status": "conditional_field_difference_audit_generated",
        "reference_run_id": reference_run_id,
        "candidate_package": str(args.candidate_summary),
        "compared_candidate_count": len(summary_rows),
        "cell_count": int(reference["k"].shape[0]),
        "total_area_m2": float(np.sum(areas)),
        "max_candidate_mean_abs_delta_log10_k_geom": max_mean_abs,
        "max_cells_abs_delta_gt_0p05": max_changed_gt_005,
        "max_cells_abs_delta_gt_0p10": max_changed_gt_010,
        "summary_csv": str(summary_csv),
        "top_cells_csv": str(top_cells_csv),
        "summary_json": str(summary_json),
        "markdown": str(markdown),
        "candidate_summaries": summary_rows,
        "interpretation": [
            "All comparisons are against the current active-objective field, not against the frozen source model.",
            "Small local-basis differences indicate nearly identical permeability tensors with different diagnostic ranks.",
            "Large smooth-field differences identify gate-dependent alternatives that would need explicit acceptance before promotion.",
        ],
    }
    summary_json.write_text(json.dumps(json_ready(summary), indent=2) + "\n", encoding="utf-8")
    write_markdown(markdown, summary)
    return summary


def main() -> None:
    args = parse_args()
    build_audit(args)


if __name__ == "__main__":
    main()
