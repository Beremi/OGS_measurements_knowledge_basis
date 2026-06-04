#!/usr/bin/env python3
"""Map direct-permeability support-cell conflicts onto the current OGS mesh.

This audit is diagnostic only. It does not change OGS inputs, likelihood
semantics, candidate rankings, or field labels. Its purpose is to make the
same-support lower-bound result spatially inspectable.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import meshio
import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mesh",
        type=Path,
        default=Path("inversion_workflow/current_permeability_field/current_best_bulk_w_projections.vtu"),
        help="Current permeability-field VTU used for cell centroids.",
    )
    parser.add_argument(
        "--residual-audit",
        type=Path,
        default=Path("inversion_workflow/permeability_residual_conflict_audit.csv"),
    )
    parser.add_argument(
        "--support-cell-audit",
        type=Path,
        default=Path("inversion_workflow/permeability_residual_support_cell_audit.csv"),
    )
    parser.add_argument(
        "--policy-group-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_policy_group_summary.csv"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/permeability_support_conflict_spatial_audit.csv"),
    )
    parser.add_argument(
        "--row-output",
        type=Path,
        default=Path("inversion_workflow/permeability_support_conflict_spatial_rows.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/permeability_support_conflict_spatial_audit_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/permeability_support_conflict_spatial_audit.md"),
    )
    parser.add_argument(
        "--figure-output",
        type=Path,
        default=Path("inversion_workflow/permeability_support_conflict_spatial_audit.png"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/permeability_pulse_tests/derived_files/support_conflict_spatial_audit"),
    )
    parser.add_argument("--top-label-count", type=int, default=10)
    return parser.parse_args()


def resolve(repo: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo / path


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


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def first_cell_id(value: Any) -> int | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    first = text.split(";")[0].split(",")[0].strip()
    try:
        cell_id = int(float(first))
    except ValueError:
        return None
    return cell_id if cell_id >= 0 else None


def mesh_centroids(mesh_path: Path) -> pd.DataFrame:
    mesh = meshio.read(mesh_path)
    if not mesh.cells:
        raise ValueError(f"{mesh_path} contains no cells")
    block = mesh.cells[0]
    centroids = mesh.points[block.data].mean(axis=1)
    return pd.DataFrame(
        {
            "primary_cell_id": np.arange(centroids.shape[0], dtype=int),
            "cell_type": block.type,
            "centroid_x_m": centroids[:, 0],
            "centroid_y_m": centroids[:, 1],
            "centroid_z_m": centroids[:, 2] if centroids.shape[1] > 2 else 0.0,
        }
    )


def numeric(frame: pd.DataFrame, column: str, default: float = math.nan) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce")


def classify_cell(row: pd.Series) -> str:
    statuses = str(row.get("feasibility_statuses", ""))
    row_count = int(row.get("row_count", 0) or 0)
    observed_range = float(row.get("observed_log10_range", 0.0) or 0.0)
    max_abs = float(row.get("max_abs_residual", 0.0) or 0.0)
    if "observed_above_configured_scalar_range" in statuses:
        return "configured_scalar_range_conflict"
    if row_count > 1 and observed_range >= 2.0:
        return "large_same_support_observation_conflict"
    if row_count > 1 and observed_range >= 1.0:
        return "same_support_observation_conflict"
    if max_abs >= 1.0:
        return "large_single_row_residual"
    return "low_conflict_or_singleton"


def build_tables(
    mesh_path: Path,
    residual_path: Path,
    support_path: Path,
    policy_group_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    centroids = mesh_centroids(mesh_path)
    support = read_csv(support_path)
    residual = read_csv(residual_path)
    policy_group = read_csv(policy_group_path)

    if support.empty:
        raise ValueError(f"No support-cell rows found in {support_path}")

    support = support.copy()
    support["primary_cell_id"] = numeric(support, "primary_cell_id").astype("Int64")
    support = support.dropna(subset=["primary_cell_id"]).copy()
    support["primary_cell_id"] = support["primary_cell_id"].astype(int)

    if not policy_group.empty:
        policy_group = policy_group.copy()
        policy_group["primary_cell_id"] = numeric(policy_group, "primary_cell_id").astype("Int64")
        policy_group = policy_group.dropna(subset=["primary_cell_id"]).copy()
        policy_group["primary_cell_id"] = policy_group["primary_cell_id"].astype(int)
        keep = [
            "primary_cell_id",
            "gaussian_group_row_loss",
            "support_mean_group_loss",
            "support_median_group_loss",
            "group_policy_class",
        ]
        support = support.merge(policy_group[[c for c in keep if c in policy_group.columns]], on="primary_cell_id", how="left")

    cell_rows = support.merge(centroids, on="primary_cell_id", how="left")
    cell_rows["conflict_class"] = cell_rows.apply(classify_cell, axis=1)
    cell_rows["is_repeated_support_cell"] = numeric(cell_rows, "row_count").fillna(0).astype(int) > 1
    cell_rows["has_large_observed_range_ge_1_log10"] = numeric(cell_rows, "observed_log10_range").fillna(0.0) >= 1.0
    cell_rows["has_large_observed_range_ge_2_log10"] = numeric(cell_rows, "observed_log10_range").fillna(0.0) >= 2.0
    cell_rows = cell_rows.sort_values(
        ["max_abs_residual", "observed_log10_range", "primary_cell_id"],
        ascending=[False, False, True],
    )

    row_rows = pd.DataFrame()
    if not residual.empty:
        row_rows = residual.copy()
        row_rows["primary_cell_id"] = row_rows["selected_cell_ids"].map(first_cell_id)
        row_rows = row_rows.dropna(subset=["primary_cell_id"]).copy()
        row_rows["primary_cell_id"] = row_rows["primary_cell_id"].astype(int)
        row_rows = row_rows.merge(
            cell_rows[
                [
                    "primary_cell_id",
                    "centroid_x_m",
                    "centroid_y_m",
                    "centroid_z_m",
                    "observed_log10_range",
                    "max_abs_residual",
                    "conflict_class",
                ]
            ],
            on="primary_cell_id",
            how="left",
            suffixes=("", "_support_cell"),
        )
        keep = [
            "observation_id",
            "source_sheet",
            "campaign_year",
            "normalized_segment_label",
            "borehole_depth_m",
            "primary_cell_id",
            "centroid_x_m",
            "centroid_y_m",
            "centroid_z_m",
            "observed_log10_permeability_m2",
            "predicted_log10_permeability_m2",
            "log10_residual_pred_minus_obs",
            "abs_log10_residual",
            "objective_weight",
            "configured_scalar_feasibility_status",
            "residual_band",
            "residual_sign",
            "conflict_class",
            "recommended_next_action",
        ]
        row_rows = row_rows[[column for column in keep if column in row_rows.columns]].sort_values(
            ["abs_log10_residual", "observation_id"], ascending=[False, True]
        )

    active_support_cells = int(cell_rows.shape[0])
    repeated_cells = int(cell_rows["is_repeated_support_cell"].sum())
    ge1_cells = int(cell_rows["has_large_observed_range_ge_1_log10"].sum())
    ge2_cells = int(cell_rows["has_large_observed_range_ge_2_log10"].sum())
    configured_conflict_cells = int((cell_rows["conflict_class"] == "configured_scalar_range_conflict").sum())
    top_cell = cell_rows.iloc[0].to_dict() if not cell_rows.empty else {}
    summary = {
        "status": "permeability_support_conflict_spatial_audit_generated",
        "mesh": str(mesh_path),
        "mesh_cell_count": int(centroids.shape[0]),
        "active_support_cell_count": active_support_cells,
        "repeated_support_cell_count": repeated_cells,
        "support_cells_observed_range_ge_1_log10": ge1_cells,
        "support_cells_observed_range_ge_2_log10": ge2_cells,
        "configured_scalar_range_conflict_cell_count": configured_conflict_cells,
        "top_conflict_cell": json_ready(top_cell),
        "interpretation": (
            "The dominant direct-permeability residuals are spatially concentrated in repeated support cells. "
            "This supports the existing stop gate: another one-value-per-support-cell field in the same support map "
            "cannot remove mutually inconsistent pulse-test rows assigned to the same OGS cell."
        ),
    }
    return cell_rows, row_rows, summary


def fmt(value: Any, digits: int = 4) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if not np.isfinite(number):
        return "n/a"
    if abs(number) < 1.0e-5 and number != 0.0:
        return f"{number:.3e}"
    return f"{number:.{digits}g}"


def write_plot(path: Path, cells: pd.DataFrame, top_label_count: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plot_cells = cells.dropna(subset=["centroid_x_m", "centroid_y_m"]).copy()
    fig, ax = plt.subplots(figsize=(8.5, 6.5), constrained_layout=True)
    if plot_cells.empty:
        ax.text(0.5, 0.5, "No mapped support cells", ha="center", va="center")
        ax.set_axis_off()
    else:
        repeated = plot_cells[plot_cells["is_repeated_support_cell"]]
        single = plot_cells[~plot_cells["is_repeated_support_cell"]]
        if not single.empty:
            ax.scatter(
                single["centroid_x_m"],
                single["centroid_y_m"],
                s=28,
                c="#b8b8b8",
                edgecolors="#666666",
                linewidths=0.4,
                label="single active row",
                alpha=0.8,
            )
        scatter = ax.scatter(
            repeated["centroid_x_m"],
            repeated["centroid_y_m"],
            s=70 + 18 * repeated["row_count"].astype(float),
            c=repeated["observed_log10_range"].astype(float),
            cmap="magma_r",
            edgecolors="#101010",
            linewidths=0.7,
            label="repeated support cell",
        )
        colorbar = fig.colorbar(scatter, ax=ax)
        colorbar.set_label("observed log10(k) range within support cell")
        top = plot_cells.head(max(top_label_count, 0))
        for _, row in top.iterrows():
            label = f"{int(row['primary_cell_id'])}\\n{row.get('segments', '')}"
            ax.annotate(
                label,
                (float(row["centroid_x_m"]), float(row["centroid_y_m"])),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=7,
                color="#111111",
            )
        ax.set_title("Direct-permeability same-support conflicts in current field")
        ax.set_xlabel("mesh centroid x [m]")
        ax.set_ylabel("mesh centroid y [m]")
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, color="#dddddd", linewidth=0.5)
        ax.legend(loc="best", frameon=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def write_markdown(path: Path, figure_path: Path, cells: pd.DataFrame, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rel_figure = figure_path.name if figure_path.parent == path.parent else figure_path.as_posix()
    lines = [
        "# Permeability Support-Conflict Spatial Audit",
        "",
        "This diagnostic maps the active direct-permeability support cells onto the",
        "current OGS mesh. It is a visualization/audit layer only; it does not change",
        "likelihood semantics, field values, OGS inputs, or promotion decisions.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Mesh cells: {summary['mesh_cell_count']}",
        f"- Active support cells: {summary['active_support_cell_count']}",
        f"- Repeated support cells: {summary['repeated_support_cell_count']}",
        f"- Support cells with observed range >= 1 log10: {summary['support_cells_observed_range_ge_1_log10']}",
        f"- Support cells with observed range >= 2 log10: {summary['support_cells_observed_range_ge_2_log10']}",
        f"- Configured-scalar range conflict cells: {summary['configured_scalar_range_conflict_cell_count']}",
        "",
        f"![Support conflict map]({rel_figure})",
        "",
        "## Highest-Conflict Support Cells",
        "",
        "| Cell | Class | Rows | Segments | Depth range [m] | Observed range | Max abs residual | x [m] | y [m] |",
        "| ---: | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for _, row in cells.head(15).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row["primary_cell_id"])),
                    f"`{row['conflict_class']}`",
                    str(int(row["row_count"])),
                    f"`{row.get('segments', '')}`",
                    f"{fmt(row.get('depth_min_m'), 3)}-{fmt(row.get('depth_max_m'), 3)}",
                    fmt(row.get("observed_log10_range"), 4),
                    fmt(row.get("max_abs_residual"), 4),
                    fmt(row.get("centroid_x_m"), 4),
                    fmt(row.get("centroid_y_m"), 4),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            str(summary["interpretation"]),
            "The plotted cells are the same support cells used by the existing residual,",
            "likelihood-policy, and support lower-bound audits. The largest conflicts",
            "therefore represent observation-support/likelihood choices rather than a",
            "missing spatial degree of freedom in the current one-value-per-support-cell map.",
            "",
            "## Source Artifacts",
            "",
            "- `inversion_workflow/permeability_residual_conflict_audit.csv`",
            "- `inversion_workflow/permeability_residual_support_cell_audit.csv`",
            "- `inversion_workflow/permeability_likelihood_policy_group_summary.csv`",
            "- `inversion_workflow/current_permeability_field/current_best_bulk_w_projections.vtu`",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def copy_outputs(catalogue_dir: Path, paths: list[Path]) -> None:
    catalogue_dir.mkdir(parents=True, exist_ok=True)
    for path in paths:
        shutil.copy2(path, catalogue_dir / path.name)


def main() -> None:
    args = parse_args()
    repo = Path.cwd()
    mesh_path = resolve(repo, args.mesh).resolve()
    residual_path = resolve(repo, args.residual_audit).resolve()
    support_path = resolve(repo, args.support_cell_audit).resolve()
    policy_group_path = resolve(repo, args.policy_group_summary).resolve()
    output_csv = resolve(repo, args.output_csv).resolve()
    row_output = resolve(repo, args.row_output).resolve()
    summary_output = resolve(repo, args.summary_output).resolve()
    markdown_output = resolve(repo, args.markdown_output).resolve()
    figure_output = resolve(repo, args.figure_output).resolve()
    catalogue_dir = resolve(repo, args.catalogue_dir).resolve()

    cells, rows, summary = build_tables(mesh_path, residual_path, support_path, policy_group_path)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    cells.to_csv(output_csv, index=False)
    rows.to_csv(row_output, index=False)
    summary = {
        **summary,
        "output_csv": str(output_csv),
        "row_output_csv": str(row_output),
        "markdown_output": str(markdown_output),
        "figure_output": str(figure_output),
    }
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.write_text(json.dumps(json_ready(summary), indent=2), encoding="utf-8")
    write_plot(figure_output, cells, args.top_label_count)
    write_markdown(markdown_output, figure_output, cells, summary)
    copy_outputs(catalogue_dir, [output_csv, row_output, summary_output, markdown_output, figure_output])


if __name__ == "__main__":
    main()
