#!/usr/bin/env python3
"""Render visual inspection maps for the packaged current permeability field."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-codex")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import meshio
import numpy as np
import pandas as pd
from matplotlib.tri import Triangulation


WORK_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mesh",
        type=Path,
        default=Path("inversion_workflow/current_permeability_field/current_best_bulk_w_projections.vtu"),
    )
    parser.add_argument(
        "--field-summary",
        type=Path,
        default=Path("inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD_SUMMARY.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/current_permeability_field/visual_inspection"),
    )
    return parser.parse_args()


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else WORK_ROOT / path


def read_json(path: Path) -> dict[str, Any]:
    resolved = resolve(path)
    if not resolved.exists():
        return {}
    return json.loads(resolved.read_text(encoding="utf-8"))


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
    if value is None:
        return None
    return value


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(WORK_ROOT))
    except ValueError:
        return str(path)


def cell_data(mesh: meshio.Mesh, name: str) -> np.ndarray:
    values = mesh.cell_data.get(name)
    if not values:
        raise KeyError(f"missing cell data {name!r}")
    array = np.asarray(values[0])
    if array.ndim == 2 and array.shape[1] == 1:
        return array[:, 0]
    return array


def triangle6_cells(mesh: meshio.Mesh) -> np.ndarray:
    for block in mesh.cells:
        if block.type == "triangle6":
            return np.asarray(block.data[:, :3], dtype=int)
        if block.type == "triangle":
            return np.asarray(block.data, dtype=int)
    raise ValueError("no triangle or triangle6 cells found")


def summarize(values: np.ndarray) -> dict[str, float | int]:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return {"finite_count": 0}
    return {
        "finite_count": int(finite.size),
        "min": float(np.min(finite)),
        "p05": float(np.quantile(finite, 0.05)),
        "p50": float(np.quantile(finite, 0.50)),
        "p95": float(np.quantile(finite, 0.95)),
        "max": float(np.max(finite)),
    }


def metric_frame(metrics: dict[str, np.ndarray]) -> pd.DataFrame:
    rows = []
    for name, values in metrics.items():
        row = {"metric": name}
        row.update(summarize(values))
        rows.append(row)
    return pd.DataFrame(rows)


def plot_cell_metric(
    *,
    path: Path,
    points: np.ndarray,
    triangles: np.ndarray,
    values: np.ndarray,
    title: str,
    colorbar_label: str,
    cmap: str = "viridis",
    overlay_orientation_deg: float | None = None,
) -> None:
    triangulation = Triangulation(points[:, 0], points[:, 1], triangles)
    fig, ax = plt.subplots(figsize=(8.2, 5.8), constrained_layout=True)
    image = ax.tripcolor(triangulation, facecolors=values, shading="flat", cmap=cmap)
    colorbar = fig.colorbar(image, ax=ax, shrink=0.90)
    colorbar.set_label(colorbar_label)
    ax.set_title(title)
    ax.set_xlabel("x / m")
    ax.set_ylabel("y / m")
    ax.set_aspect("equal", adjustable="box")
    if overlay_orientation_deg is not None:
        centroids = points[triangles].mean(axis=1)
        finite = np.isfinite(values)
        candidates = np.flatnonzero(finite)
        if candidates.size:
            step = max(1, candidates.size // 180)
            chosen = candidates[::step]
            theta = np.deg2rad(overlay_orientation_deg)
            ux = np.cos(theta)
            uy = np.sin(theta)
            ax.quiver(
                centroids[chosen, 0],
                centroids[chosen, 1],
                np.full(chosen.shape, ux),
                np.full(chosen.shape, uy),
                angles="xy",
                scale_units="xy",
                scale=35,
                color="black",
                alpha=0.40,
                width=0.0022,
            )
    fig.savefig(path, dpi=180)
    plt.close(fig)


def build(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    mesh_path = resolve(args.mesh)
    output_dir = resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    mesh = meshio.read(mesh_path)
    points = np.asarray(mesh.points[:, :2], dtype=float)
    triangles = triangle6_cells(mesh)

    k_i = np.asarray(cell_data(mesh, "k_i_rd"), dtype=float)
    tensors = k_i.reshape((-1, 2, 2))
    tensors = 0.5 * (tensors + np.swapaxes(tensors, 1, 2))
    eigvals = np.linalg.eigvalsh(tensors)
    eig_min = eigvals[:, 0]
    eig_max = eigvals[:, 1]
    k_geom = np.sqrt(eig_min * eig_max)
    log10_k_geom = np.log10(k_geom)
    log10_k_min = np.log10(eig_min)
    log10_k_max = np.log10(eig_max)
    anisotropy_ratio = eig_max / eig_min

    k_mag = np.asarray(cell_data(mesh, "k_mag_rd"), dtype=float)
    theta = np.asarray(cell_data(mesh, "k_theta_deg_rd"), dtype=float)
    local_increment = np.asarray(cell_data(mesh, "k_local_basis_applied_log10_increment_rd"), dtype=float)
    smooth_increment = np.asarray(cell_data(mesh, "k_smooth_applied_log10_multiplier_rd"), dtype=float)
    nearest_anchor = np.asarray(cell_data(mesh, "k_local_basis_nearest_anchor_distance_m_rd"), dtype=float)
    weight_sum = np.asarray(cell_data(mesh, "k_local_basis_weight_sum_rd"), dtype=float)
    n_rd = np.asarray(cell_data(mesh, "n_rd"), dtype=float)

    metrics = {
        "log10_k_geom_m2": log10_k_geom,
        "log10_k_eigen_min_m2": log10_k_min,
        "log10_k_eigen_max_m2": log10_k_max,
        "anisotropy_ratio": anisotropy_ratio,
        "theta_deg": theta,
        "k_mag_rd_m2": k_mag,
        "local_basis_applied_log10_increment": local_increment,
        "smooth_applied_log10_multiplier": smooth_increment,
        "local_basis_nearest_anchor_distance_m": nearest_anchor,
        "local_basis_weight_sum": weight_sum,
        "n_rd": n_rd,
    }
    summary_frame = metric_frame(metrics)
    summary_csv = output_dir / "current_field_visual_metric_summary.csv"
    summary_frame.to_csv(summary_csv, index=False)

    image_specs = [
        (
            "log10_k_geom_map.png",
            log10_k_geom,
            "Current field log10 geometric-mean permeability",
            "log10(k_geom / m2)",
            "viridis",
            float(np.nanmedian(theta)),
        ),
        (
            "log10_k_eigen_min_map.png",
            log10_k_min,
            "Current field log10 minor eigen-permeability",
            "log10(k_min / m2)",
            "magma",
            None,
        ),
        (
            "log10_k_eigen_max_map.png",
            log10_k_max,
            "Current field log10 major eigen-permeability",
            "log10(k_max / m2)",
            "plasma",
            None,
        ),
        (
            "local_basis_increment_map.png",
            local_increment,
            "Applied local-basis log10 permeability increment",
            "log10 increment",
            "coolwarm",
            None,
        ),
        (
            "nearest_anchor_distance_map.png",
            nearest_anchor,
            "Nearest local-basis anchor distance",
            "distance / m",
            "cividis",
            None,
        ),
        (
            "local_basis_weight_sum_map.png",
            weight_sum,
            "Local-basis kernel weight sum",
            "weight sum",
            "YlGnBu",
            None,
        ),
    ]
    generated_images = []
    for filename, values, title, label, cmap, orientation in image_specs:
        image_path = output_dir / filename
        plot_cell_metric(
            path=image_path,
            points=points,
            triangles=triangles,
            values=np.asarray(values, dtype=float),
            title=title,
            colorbar_label=label,
            cmap=cmap,
            overlay_orientation_deg=orientation,
        )
        generated_images.append(image_path)

    field_summary = read_json(args.field_summary)
    interpretation = field_summary.get("interpretation", {})
    summary = {
        "status": "current_field_visual_inspection_generated",
        "source_mesh": display_path(mesh_path),
        "output_dir": display_path(output_dir),
        "image_count": len(generated_images),
        "generated_images": [display_path(path) for path in generated_images],
        "metric_summary_csv": display_path(summary_csv),
        "mesh_points": int(mesh.points.shape[0]),
        "triangle_cells": int(triangles.shape[0]),
        "positive_definite_cells": int(np.isfinite(log10_k_geom).sum()),
        "x_extent_m": [float(np.nanmin(points[:, 0])), float(np.nanmax(points[:, 0]))],
        "y_extent_m": [float(np.nanmin(points[:, 1])), float(np.nanmax(points[:, 1]))],
        "key_metrics": {
            "log10_k_geom_m2": summarize(log10_k_geom),
            "log10_k_eigen_min_m2": summarize(log10_k_min),
            "log10_k_eigen_max_m2": summarize(log10_k_max),
            "anisotropy_ratio": summarize(anisotropy_ratio),
            "theta_deg": summarize(theta),
            "local_basis_applied_log10_increment": summarize(local_increment),
            "local_basis_nearest_anchor_distance_m": summarize(nearest_anchor),
            "n_rd": summarize(n_rd),
        },
        "current_field_run_id": field_summary.get("run_id"),
        "current_field_deliverable_status": interpretation.get("deliverable_status"),
        "notes": [
            "These plots are visual QA for the packaged active-objective incumbent, not a final promotion decision.",
            "The orientation overlay on the geometric-mean map uses the median k_theta_deg_rd value.",
            "The plots use the first three nodes of each triangle6 cell for 2D rendering; cell data values remain one value per triangle6 element.",
        ],
    }
    summary_json = output_dir / "current_field_visual_inspection_summary.json"
    summary_json.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(output_dir / "CURRENT_FIELD_VISUAL_INSPECTION.md", summary, summary_frame)
    return summary_frame, summary


def markdown_image(path: str, output_dir: Path) -> str:
    rel = Path(path).name
    return f"![{rel}]({rel})"


def write_markdown(path: Path, summary: dict[str, Any], summary_frame: pd.DataFrame) -> None:
    output_dir = path.parent
    image_lines = []
    for image in summary["generated_images"]:
        image_lines.extend([markdown_image(image, output_dir), ""])
    rows = []
    for _, row in summary_frame.iterrows():
        rows.append(
            "| "
            + " | ".join(
                [
                    f"`{row['metric']}`",
                    str(row.get("p05", "")),
                    str(row.get("p50", "")),
                    str(row.get("p95", "")),
                    str(row.get("max", "")),
                ]
            )
            + " |"
        )
    lines = [
        "# Current Field Visual Inspection",
        "",
        "This generated page renders the packaged current permeability-field VTU as",
        "cell-wise inspection maps. It is a QA view of the active-objective incumbent,",
        "not a final all-measurement promotion decision.",
        "",
        "## Summary",
        "",
        f"- Status: `{summary['status']}`",
        f"- Source mesh: `{summary['source_mesh']}`",
        f"- Current field run: `{summary.get('current_field_run_id')}`",
        f"- Deliverable status: `{summary.get('current_field_deliverable_status')}`",
        f"- Triangle cells rendered: {summary['triangle_cells']}",
        f"- Positive-definite rendered cells: {summary['positive_definite_cells']}",
        f"- Images generated: {summary['image_count']}",
        "",
        "## Images",
        "",
        *image_lines,
        "## Metric Summary",
        "",
        "| Metric | p05 | p50 | p95 | max |",
        "| --- | ---: | ---: | ---: | ---: |",
        *rows,
        "",
        "## Interpretation",
        "",
        "The current field keeps a fixed bedding-informed tensor orientation and fixed",
        "anisotropy ratio while applying smooth and local-basis magnitude changes. The",
        "visual maps make the spatial support of those magnitude changes inspectable",
        "next to the metric summary, and should be regenerated whenever the packaged",
        "current field changes.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    _, summary = build(parse_args())
    print(f"wrote {summary['output_dir']}/CURRENT_FIELD_VISUAL_INSPECTION.md")
    print(f"generated images: {summary['image_count']}")


if __name__ == "__main__":
    main()
