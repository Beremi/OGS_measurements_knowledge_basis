#!/usr/bin/env python3
"""Package the current best permeability field and its acceptance caveats."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
from pathlib import Path
from typing import Any

import meshio
import numpy as np


DEFAULT_RUN_DIR = Path("inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000")
SUMMARY_FILES = [
    "RUN_MANIFEST.json",
    "combined_objective_summary.json",
    "combined_objective_components.csv",
    "permeability_fit_summary.json",
    "permeability_fit_evaluation.csv",
    "state_observation_evaluation_summary.json",
    "state_observation_evaluation.csv",
    "ogs_state_samples.csv",
    "ogs_output_inventory.csv",
    "ert_resistivity_diagnostic_summary.json",
    "taupe_tdr_trend_diagnostic_summary.json",
    "rh_boundary_curve_audit_summary.json",
    "INVERSION_RELEASE_GATE_AUDIT.json",
    "INVERSION_RELEASE_GATE_AUDIT.csv",
    "INVERSION_RELEASE_GATE_AUDIT.md",
    "OGS_RUN_INPUT_AUDIT.json",
    "OGS_RUN_INPUT_AUDIT.md",
    "OGS_EXECUTION_STATUS.json",
    "ogs_state_sampling_summary.json",
]
RUN_INPUT_FALLBACK_FILES = [
    "cd_a_open_niche_quad.prj",
    "01_processes_TRM.xml",
    "02_process_variables_TRM.xml",
    "03_parameters_TRM.xml",
    "03_parameters_TRM_orig.xml",
    "04_media_TRM.xml",
    "04_1_media_aqu_liq.xml",
    "04_2_media_twophase.xml",
    "05_1_fixed_timestepping.xml",
    "05_time_loop_TRM.xml",
    "06_nonlinear_solver_T.xml",
    "07_linear_solver_T.xml",
    "08_curves.xml",
    "08_08_open_niche_seasonal.xml",
    "bulk.vtu",
    "bulk_all.vtu",
    "bulk_w_projections.vtu",
    "cd-a_niche4.vtu",
    "cd-a_left.vtu",
    "cd-a_right.vtu",
    "cd-a_top.vtu",
    "cd-a_bottom.vtu",
    "closed_niche_seasonal_curve_shifted.xml",
    "open_niche_seasonal_curve_shifted.xml",
    "README.txt",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--output-dir", type=Path, default=Path("inversion_workflow/current_permeability_field"))
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def percentile_stats(name: str, values: np.ndarray, weights: np.ndarray | None = None) -> dict[str, Any]:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    row: dict[str, Any] = {
        "metric": name,
        "finite_count": int(finite.size),
    }
    if finite.size == 0:
        return row
    quantiles = np.quantile(finite, [0.0, 0.01, 0.05, 0.1, 0.5, 0.9, 0.95, 0.99, 1.0])
    row.update(
        {
            "min": quantiles[0],
            "p01": quantiles[1],
            "p05": quantiles[2],
            "p10": quantiles[3],
            "p50": quantiles[4],
            "p90": quantiles[5],
            "p95": quantiles[6],
            "p99": quantiles[7],
            "max": quantiles[8],
            "mean": float(np.mean(finite)),
            "std": float(np.std(finite)),
        }
    )
    if weights is not None and len(weights) == len(values):
        w = np.asarray(weights, dtype=float)
        mask = np.isfinite(values) & np.isfinite(w) & (w > 0)
        if np.any(mask):
            row["area_weighted_mean"] = float(np.average(values[mask], weights=w[mask]))
    return row


def triangle6_areas(mesh: meshio.Mesh) -> np.ndarray:
    triangles = None
    for block in mesh.cells:
        if block.type == "triangle6":
            triangles = block.data
            break
    if triangles is None:
        return np.array([])
    vertices = mesh.points[triangles[:, :3], :2]
    a = vertices[:, 0, :]
    b = vertices[:, 1, :]
    c = vertices[:, 2, :]
    ab = b - a
    ac = c - a
    cross_z = ab[:, 0] * ac[:, 1] - ab[:, 1] * ac[:, 0]
    return 0.5 * np.abs(cross_z)


def field_stats(mesh_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    mesh = meshio.read(mesh_path)
    cell_type = "triangle6"
    cell_data = mesh.cell_data_dict
    if "k_i_rd" not in cell_data or cell_type not in cell_data["k_i_rd"]:
        raise ValueError(f"{mesh_path} does not contain triangle6 cell data field k_i_rd")
    k_tensor = np.asarray(cell_data["k_i_rd"][cell_type], dtype=float)
    if k_tensor.ndim != 2 or k_tensor.shape[1] != 4:
        raise ValueError(f"Expected k_i_rd shape (n,4), got {k_tensor.shape}")
    matrices = k_tensor.reshape((-1, 2, 2))
    eig = np.linalg.eigvalsh(matrices)
    area = triangle6_areas(mesh)
    ratio = eig[:, 1] / eig[:, 0]
    metrics = {
        "k_xx_m2": matrices[:, 0, 0],
        "k_xy_m2": matrices[:, 0, 1],
        "k_yx_m2": matrices[:, 1, 0],
        "k_yy_m2": matrices[:, 1, 1],
        "k_eigen_min_m2": eig[:, 0],
        "k_eigen_max_m2": eig[:, 1],
        "k_eigen_ratio": ratio,
        "log10_k_eigen_min": np.log10(eig[:, 0]),
        "log10_k_eigen_max": np.log10(eig[:, 1]),
    }
    for optional in [
        "k_mag_rd",
        "k_anisotropy_ratio_rd",
        "k_theta_deg_rd",
        "n_rd",
        "k_local_basis_applied_log10_increment_rd",
        "k_local_basis_weight_sum_rd",
        "k_local_basis_nearest_anchor_distance_m_rd",
    ]:
        if optional in cell_data and cell_type in cell_data[optional]:
            metrics[optional] = np.asarray(cell_data[optional][cell_type], dtype=float).reshape(-1)
    rows = [percentile_stats(name, values, area if area.size == len(values) else None) for name, values in metrics.items()]
    summary = {
        "mesh_points": int(mesh.points.shape[0]),
        "triangle6_cell_count": int(k_tensor.shape[0]),
        "field_shape": list(k_tensor.shape),
        "tensor_component_order": "row-major [k_xx, k_xy, k_yx, k_yy]",
        "max_tensor_asymmetry_abs": float(np.max(np.abs(matrices[:, 0, 1] - matrices[:, 1, 0]))),
        "positive_definite_cell_count": int(np.sum((eig[:, 0] > 0) & (eig[:, 1] > 0))),
        "non_positive_definite_cell_count": int(np.sum(~((eig[:, 0] > 0) & (eig[:, 1] > 0)))),
        "total_triangle_area_m2": float(np.sum(area)) if area.size else None,
        "field_metrics": {row["metric"]: row for row in rows},
    }
    return rows, summary


def copy_inputs(run_dir: Path, output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    copied: dict[str, str] = {}
    mesh_source = run_dir / "bulk_w_projections.vtu"
    mesh_dest = output_dir / "current_best_bulk_w_projections.vtu"
    shutil.copy2(mesh_source, mesh_dest)
    copied[str(mesh_source)] = str(mesh_dest)
    for name in SUMMARY_FILES:
        source = run_dir / name
        if source.exists():
            dest = output_dir / name
            shutil.copy2(source, dest)
            copied[str(source)] = str(dest)
    return copied


def copy_run_input_snapshot(run_dir: Path, output_dir: Path) -> dict[str, str]:
    input_dir = output_dir / "ogs_run_inputs"
    input_dir.mkdir(parents=True, exist_ok=True)
    manifest = read_json(run_dir / "RUN_MANIFEST.json")
    names = manifest.get("copied_files") or RUN_INPUT_FALLBACK_FILES
    copied: dict[str, str] = {}
    for name in names:
        source = run_dir / str(name)
        if not source.exists() or not source.is_file():
            continue
        dest = input_dir / source.name
        shutil.copy2(source, dest)
        copied[str(source)] = str(dest)
    return copied


def file_manifest(copied_groups: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for role, copied in copied_groups.items():
        for source, dest in copied.items():
            dest_path = Path(dest)
            if not dest_path.exists():
                continue
            rows.append(
                {
                    "role": role,
                    "file_name": dest_path.name,
                    "source": source,
                    "packaged_path": dest,
                    "size_bytes": dest_path.stat().st_size,
                    "sha256": sha256_file(dest_path),
                }
            )
    return sorted(rows, key=lambda row: (row["role"], row["file_name"]))


def add_manifest_row(rows: list[dict[str, Any]], role: str, path: Path, source: str | None = None) -> None:
    rows.append(
        {
            "role": role,
            "file_name": path.name,
            "source": source or str(path),
            "packaged_path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    )


def write_file_manifest_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = ["role", "file_name", "source", "packaged_path", "size_bytes", "sha256"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "metric",
        "finite_count",
        "min",
        "p01",
        "p05",
        "p10",
        "p50",
        "p90",
        "p95",
        "p99",
        "max",
        "mean",
        "std",
        "area_weighted_mean",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_markdown(path: Path, summary: dict[str, Any]) -> None:
    objective = summary["combined_objective"]
    permeability = summary["permeability_fit"]
    state = summary["state_observation"]
    release = summary["release_gate"]
    ert = summary["ert_diagnostic"]
    taupe = summary["taupe_diagnostic"]
    field = summary["field"]
    metrics = field["field_metrics"]
    run_inputs = summary["run_input_snapshot"]
    lines = [
        "# Current Permeability Field Package",
        "",
        "This is the current best executed field under the active objective. It is a",
        "deliverable candidate field, not a final all-measurement inversion result.",
        "",
        f"- Run id: `{summary['run_id']}`",
        f"- Packaged mesh: `{summary['packaged_mesh']}`",
        f"- Source run directory: `{summary['source_run_dir']}`",
        f"- Run-local OGS input snapshot: `{summary['run_input_dir']}`",
        f"- Packaged file manifest: `{summary['file_manifest_csv']}`",
        f"- Release gate: `{release.get('status')}` with {release.get('failure_count')} failures",
        f"- OGS execution return code: `{summary['ogs_execution'].get('returncode')}`",
        f"- Active objective value: {objective.get('total_active_objective_value')}",
        f"- Active components: {objective.get('active_component_count')}",
        f"- Direct permeability rows used: {permeability.get('used_in_objective_rows')} "
        f"with weighted RMSE {permeability.get('weighted_rmse_log10')} log10 units",
        f"- NMR state rows used: {state.get('used_in_objective_rows')} "
        f"with normalized RMSE {state.get('rmse_normalized_residual')}",
        f"- ERT diagnostic MAE: {ert.get('area_weighted_residual_log10', {}).get('mae')} log10 units "
        f"(`{ert.get('status')}`)",
        f"- Taupe/TDR diagnostic MAE: {taupe.get('standardized_residual', {}).get('mae')} "
        f"(`{taupe.get('status')}`)",
        "",
        "## Field Geometry",
        "",
        f"- Mesh points: {field.get('mesh_points')}",
        f"- Triangle6 cells: {field.get('triangle6_cell_count')}",
        f"- Tensor field: `k_i_rd`, component order {field.get('tensor_component_order')}",
        f"- Positive-definite cells: {field.get('positive_definite_cell_count')}",
        f"- Max tensor asymmetry: {field.get('max_tensor_asymmetry_abs')}",
        f"- Total triangle area: {field.get('total_triangle_area_m2')} m2",
        "",
        "## Key Field Statistics",
        "",
        "| Metric | p05 | p50 | p95 | max |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for metric in ["k_eigen_min_m2", "k_eigen_max_m2", "k_eigen_ratio", "log10_k_eigen_min", "log10_k_eigen_max", "n_rd"]:
        row = metrics.get(metric, {})
        lines.append(
            f"| `{metric}` | {row.get('p05')} | {row.get('p50')} | {row.get('p95')} | {row.get('max')} |"
        )
    visual_dir = path.parent / "visual_inspection"
    visual_md = visual_dir / "CURRENT_FIELD_VISUAL_INSPECTION.md"
    if visual_md.exists():
        lines.extend(
            [
                "",
                "## Visual Inspection",
                "",
                "- `visual_inspection/CURRENT_FIELD_VISUAL_INSPECTION.md`",
                "- `visual_inspection/log10_k_geom_map.png`",
                "- `visual_inspection/log10_k_eigen_min_map.png`",
                "- `visual_inspection/log10_k_eigen_max_map.png`",
                "- `visual_inspection/local_basis_increment_map.png`",
                "- `visual_inspection/nearest_anchor_distance_map.png`",
                "- `visual_inspection/local_basis_weight_sum_map.png`",
                "",
                "The visual inspection maps are generated from the packaged VTU by",
                "`inversion_workflow/scripts/build_current_field_visual_inspection.py`. They are",
                "QA plots for the active-objective incumbent and do not promote this package to a",
                "final all-measurement inversion result.",
            ]
        )
    lines.extend(
        [
            "",
            "## Reproducible OGS Input Snapshot",
            "",
            "The frozen source model is not edited by this package.  The folder",
            "`ogs_run_inputs/` is a run-local snapshot of the exact project, XML includes,",
            "bulk meshes, boundary meshes, and seasonal curve files used by the accepted",
            "active-objective incumbent.",
            "",
            f"- Snapshot directory: `{summary['run_input_dir']}`",
            f"- Snapshot file count: {run_inputs.get('file_count')}",
            f"- Snapshot total size: {run_inputs.get('total_size_bytes')} bytes",
            "- Project file: `ogs_run_inputs/cd_a_open_niche_quad.prj`",
            "- Project mesh field file: `ogs_run_inputs/bulk_w_projections.vtu`",
            "- The root-level `current_best_bulk_w_projections.vtu` is a convenience copy of that run-local field mesh.",
            f"- SHA256 manifest: `{summary['file_manifest_csv']}`",
            "",
            "A rerun should be launched from `ogs_run_inputs/` with the project file",
            "`cd_a_open_niche_quad.prj` and a fresh output directory.  The generated",
            "`OGS_EXECUTION_STATUS.json` records the verified execution used for the current",
            "objective scores.",
            "",
            "## Caveats",
            "",
            "- This package preserves the frozen OGS equations and releases only the `k_i_rd` mesh-cell tensor field.",
            "- The active objective currently contains direct permeability pulse-test rows and conditional raw NMR state rows.",
            "- ERT and Taupe/TDR diagnostics are packaged as screening evidence only; their support/calibration/uncertainty gates remain open.",
            "- RH remains boundary/provenance evidence, not an active residual.",
            "- Other-HM monitoring remains inactive until hard-residual-ready numeric exports are supplied.",
            "- The NMR trend/anomaly mode is implemented but not promoted to the default active objective.",
            "",
            "## Packaged Files",
            "",
        ]
    )
    for source, dest in summary["copied_files"].items():
        lines.append(f"- `{Path(dest).name}` copied from `{source}`")
    lines.extend(
        [
            "",
            "## Run-Input Snapshot Files",
            "",
        ]
    )
    for source, dest in summary["run_input_files"].items():
        lines.append(f"- `{Path(dest).name}` copied from `{source}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    run_dir = args.run_dir
    output_dir = args.output_dir
    copied = copy_inputs(run_dir, output_dir)
    run_inputs = copy_run_input_snapshot(run_dir, output_dir)
    packaged_mesh = output_dir / "current_best_bulk_w_projections.vtu"
    stats_rows, field_summary = field_stats(packaged_mesh)
    stats_csv = output_dir / "current_best_field_stats.csv"
    write_csv(stats_csv, stats_rows)
    manifest_rows = file_manifest({"current_field_package": copied, "ogs_run_input_snapshot": run_inputs})
    add_manifest_row(manifest_rows, "current_field_package", stats_csv)
    manifest_rows = sorted(manifest_rows, key=lambda row: (row["role"], row["file_name"]))
    manifest_csv = output_dir / "packaged_file_manifest.csv"
    write_file_manifest_csv(manifest_csv, manifest_rows)
    combined = read_json(run_dir / "combined_objective_summary.json")
    permeability = read_json(run_dir / "permeability_fit_summary.json")
    state = read_json(run_dir / "state_observation_evaluation_summary.json")
    ert = read_json(run_dir / "ert_resistivity_diagnostic_summary.json")
    taupe = read_json(run_dir / "taupe_tdr_trend_diagnostic_summary.json")
    release = read_json(run_dir / "INVERSION_RELEASE_GATE_AUDIT.json")
    execution = read_json(run_dir / "OGS_EXECUTION_STATUS.json")
    summary = {
        "status": "current_permeability_field_package_generated",
        "run_id": run_dir.name,
        "source_run_dir": str(run_dir),
        "output_dir": str(output_dir),
        "packaged_mesh": str(packaged_mesh),
        "stats_csv": str(stats_csv),
        "run_input_dir": str(output_dir / "ogs_run_inputs"),
        "file_manifest_csv": str(manifest_csv),
        "copied_files": copied,
        "run_input_files": run_inputs,
        "packaged_file_manifest": manifest_rows,
        "run_input_snapshot": {
            "file_count": len(run_inputs),
            "total_size_bytes": int(sum(Path(dest).stat().st_size for dest in run_inputs.values() if Path(dest).exists())),
            "project_file": str(output_dir / "ogs_run_inputs" / "cd_a_open_niche_quad.prj"),
            "project_mesh": str(output_dir / "ogs_run_inputs" / "bulk_w_projections.vtu"),
        },
        "field": field_summary,
        "combined_objective": combined,
        "permeability_fit": permeability,
        "state_observation": state,
        "ert_diagnostic": ert,
        "taupe_diagnostic": taupe,
        "release_gate": release,
        "ogs_execution": execution,
        "interpretation": {
            "deliverable_status": "best_executed_active_objective_candidate_not_final_all_measurement_inversion",
            "active_likelihood_streams": ["direct permeability pulse tests", "raw NMR theta state residual"],
            "diagnostic_not_active_streams": ["ERT log-resistivity", "Taupe/TDR trend", "RH boundary provenance", "other-HM"],
            "main_remaining_gates": [
                "ERT transform/support and uncertainty",
                "Taupe unit/calibration and uncertainty",
                "RH active boundary-curve provenance",
                "other-HM numeric exports",
                "CTE confirmation",
                "NMR trend/anomaly default-promotion decision",
            ],
        },
    }
    summary_path = output_dir / "CURRENT_PERMEABILITY_FIELD_SUMMARY.json"
    summary_path.write_text(json.dumps(json_ready(summary), indent=2), encoding="utf-8")
    write_markdown(output_dir / "CURRENT_PERMEABILITY_FIELD.md", summary)


if __name__ == "__main__":
    main()
