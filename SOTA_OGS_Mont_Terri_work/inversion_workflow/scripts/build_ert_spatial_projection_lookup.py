#!/usr/bin/env python3
"""Build a spatial lookup from the ERT inversion mesh to the OGS bulk mesh.

The ERT archive stores daily/monthly inversion fields on a mesh that is not the OGS
FEM mesh.  This script creates the geometry part of the observation operator: ERT
cell centroids are transformed into the local OGS 2-D coordinate frame and mapped to
OGS bulk cells.  It does not evaluate residuals because OGS state outputs and the
final ERT support mask are still separate steps.
"""

from __future__ import annotations

import argparse
import json
import math
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from build_mesh_observation_lookup import locate_point, read_vtu_mesh


DEFAULT_ERT_Y_OFFSET = 500.0
DEFAULT_RECOMMENDED_RADIUS_M = 1.5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
    )
    parser.add_argument(
        "--ert-zip",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/ert/source_files/ERT_meas_Niche_open.zip"),
    )
    parser.add_argument(
        "--ogs-mesh",
        type=Path,
        default=Path("GESA_model_original/projection_on_mesh_2025-09-05/bulk.vtu"),
    )
    parser.add_argument(
        "--reference-vtk-member",
        default="",
        help="ERT VTK member used as the reference mesh. Defaults to the first matched timestep.",
    )
    parser.add_argument(
        "--ert-x-offset",
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--ert-y-offset",
        type=float,
        default=DEFAULT_ERT_Y_OFFSET,
        help="Shift applied to raw ERT y/z coordinates before OGS lookup.",
    )
    parser.add_argument(
        "--ert-coordinate-scale",
        type=float,
        default=1.0,
    )
    parser.add_argument(
        "--recommended-radius-m",
        type=float,
        default=DEFAULT_RECOMMENDED_RADIUS_M,
        help="Approximate central ERT support radius from the local slide note.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/processed_observations/ert_spatial_projection_lookup.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/processed_observations/ert_spatial_projection_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/processed_observations/ert_spatial_projection_operator.md"),
    )
    return parser.parse_args()


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def finite(value: Any) -> bool:
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def json_number(value: Any) -> float | None:
    return float(value) if finite(value) else None


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def first_reference_member(processed_dir: Path) -> str:
    timesteps = pd.read_csv(processed_dir / "ert_timesteps.csv")
    matched = timesteps[timesteps["has_matching_vtk"].map(bool_value)]
    if matched.empty:
        raise SystemExit("No matching ERT VTK member is listed in ert_timesteps.csv")
    return str(matched.iloc[0]["matching_vtk_member"])


def read_reference_ert_mesh(zip_path: Path, member: str) -> Any:
    try:
        import meshio  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on local runtime
        raise SystemExit(
            "meshio is required for ERT VTK lookup generation. "
            "Run with the system Python that has meshio installed."
        ) from exc

    with zipfile.ZipFile(zip_path) as archive:
        if member not in archive.namelist():
            raise SystemExit(f"Reference VTK member not found in {zip_path}: {member}")
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / "reference_ert.vtk"
            tmp_path.write_bytes(archive.read(member))
            return meshio.read(tmp_path)


def array_for_cell_data(mesh: Any, name: str, cell_type: str) -> np.ndarray:
    data = mesh.cell_data_dict.get(name, {}).get(cell_type)
    if data is None:
        return np.full(mesh.cells[0].data.shape[0], math.nan)
    return np.asarray(data, dtype=float).reshape(-1)


def triangle_area(points_2d: np.ndarray) -> float:
    a, b, c = points_2d
    ab = b - a
    ac = c - a
    return 0.5 * abs(float(ab[0] * ac[1] - ab[1] * ac[0]))


def build_lookup(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any], str]:
    processed_dir = args.processed_dir
    reference_member = args.reference_vtk_member or first_reference_member(processed_dir)
    ert_mesh = read_reference_ert_mesh(args.ert_zip, reference_member)
    ogs_mesh = read_vtu_mesh(args.ogs_mesh)
    ert_operator = json.loads((processed_dir / "ert_observation_operator_summary.json").read_text(encoding="utf-8"))
    timesteps = pd.read_csv(processed_dir / "ert_timesteps.csv")

    if len(ert_mesh.cells) != 1:
        raise SystemExit(f"Expected one ERT cell block, found {len(ert_mesh.cells)}")
    cell_block = ert_mesh.cells[0]
    cell_type = str(cell_block.type)
    if cell_block.data.shape[1] < 3:
        raise SystemExit(f"Expected triangle-like ERT cells, found {cell_type} with shape {cell_block.data.shape}")

    raw_points = np.asarray(ert_mesh.points, dtype=float)
    cells = np.asarray(cell_block.data[:, :3], dtype=int)
    vertices_raw = raw_points[cells]
    raw_centroids = vertices_raw.mean(axis=1)
    transformed_vertices = np.column_stack(
        [
            vertices_raw[:, :, 0].reshape(-1) * args.ert_coordinate_scale + args.ert_x_offset,
            vertices_raw[:, :, 1].reshape(-1) * args.ert_coordinate_scale + args.ert_y_offset,
        ]
    ).reshape(vertices_raw.shape[0], vertices_raw.shape[1], 2)
    transformed_centroids = transformed_vertices.mean(axis=1)

    log_rho = array_for_cell_data(ert_mesh, "Resistivity(log10)", cell_type)
    rho = array_for_cell_data(ert_mesh, "Resistivity/Ohmm", cell_type)
    ratio = array_for_cell_data(ert_mesh, "ratio", cell_type)
    marker = array_for_cell_data(ert_mesh, "_Marker", cell_type)

    rows: list[dict[str, Any]] = []
    for cell_id, (raw_centroid, model_centroid, model_vertices) in enumerate(
        zip(raw_centroids, transformed_centroids, transformed_vertices, strict=True)
    ):
        lookup = locate_point(ogs_mesh, float(model_centroid[0]), float(model_centroid[1]))
        radius = float(np.linalg.norm(model_centroid))
        inside_ogs_cell = str(lookup["lookup_status"]) == "inside_cell"
        inside_recommended_radius = radius <= args.recommended_radius_m
        rows.append(
            {
                "source_file": relative(args.ert_zip),
                "reference_vtk_member": reference_member,
                "ert_cell_id": cell_id,
                "ert_cell_type": cell_type,
                "raw_centroid_x": float(raw_centroid[0]),
                "raw_centroid_y_or_z": float(raw_centroid[1]),
                "raw_centroid_z": float(raw_centroid[2]) if raw_centroid.shape[0] > 2 else math.nan,
                "model_x": float(model_centroid[0]),
                "model_y": float(model_centroid[1]),
                "ert_to_model_transform": (
                    f"model_x = raw_x * {args.ert_coordinate_scale:g} + {args.ert_x_offset:g}; "
                    f"model_y = raw_y * {args.ert_coordinate_scale:g} + {args.ert_y_offset:g}"
                ),
                "ert_cell_area_m2_transformed": triangle_area(model_vertices),
                "radial_distance_from_model_origin_m": radius,
                "within_approx_1p5m_center_support": inside_recommended_radius,
                "sample_log10_resistivity": json_number(log_rho[cell_id]),
                "sample_resistivity_ohm_m": json_number(rho[cell_id]),
                "sample_ratio": json_number(ratio[cell_id]),
                "sample_marker": json_number(marker[cell_id]),
                "ogs_lookup_status": lookup["lookup_status"],
                "inside_ogs_mesh_bbox": bool(lookup["inside_mesh_bbox"]),
                "inside_ogs_cell": inside_ogs_cell,
                "distance_to_ogs_mesh_bbox_m": lookup["distance_to_mesh_bbox_m"],
                "ogs_containing_cell_id": lookup["containing_cell_id"],
                "ogs_nearest_cell_id": lookup["nearest_cell_id"],
                "ogs_lookup_cell_id": lookup["lookup_cell_id"],
                "ogs_lookup_material_id": lookup["lookup_material_id"],
                "ogs_nearest_centroid_x": lookup["nearest_centroid_x"],
                "ogs_nearest_centroid_y": lookup["nearest_centroid_y"],
                "ogs_nearest_centroid_distance_m": lookup["nearest_centroid_distance_m"],
                "ready_for_residual_after_ogs_output": bool(inside_ogs_cell and inside_recommended_radius),
                "model_quantity_to_sample": "theta_model = porosity * liquid_saturation",
                "predicted_quantity_after_calibration": "log10 bulk resistivity using ert_water_content_resistivity_operator.csv",
                "support_caveat": (
                    "The 1.5 m support flag is an approximate centre-radius screen. "
                    "The exact 35 cm-in-rock ERT support mask still needs the agreed ERT/FEM tunnel-contour definition."
                ),
            }
        )

    lookup_df = pd.DataFrame(rows)
    matched_vtk = int(timesteps["has_matching_vtk"].map(bool_value).sum())
    summary = {
        "status": "projection_lookup_ready_transform_assumed_ogs_outputs_pending",
        "ert_zip": str(args.ert_zip),
        "reference_vtk_member": reference_member,
        "ogs_mesh": str(args.ogs_mesh),
        "ert_cells": int(lookup_df.shape[0]),
        "ert_points": int(raw_points.shape[0]),
        "ert_cell_type": cell_type,
        "raw_ert_bounds": {
            "min": [json_number(v) for v in np.nanmin(raw_points, axis=0)],
            "max": [json_number(v) for v in np.nanmax(raw_points, axis=0)],
        },
        "transformed_ert_bounds": {
            "min": [json_number(v) for v in np.nanmin(transformed_centroids, axis=0)],
            "max": [json_number(v) for v in np.nanmax(transformed_centroids, axis=0)],
        },
        "ogs_mesh_bounds": {
            "min": [json_number(v) for v in ogs_mesh.mesh_min],
            "max": [json_number(v) for v in ogs_mesh.mesh_max],
        },
        "transform": {
            "model_x": f"raw_x * {args.ert_coordinate_scale:g} + {args.ert_x_offset:g}",
            "model_y": f"raw_y * {args.ert_coordinate_scale:g} + {args.ert_y_offset:g}",
        },
        "lookup_status_counts": lookup_df["ogs_lookup_status"].value_counts().to_dict(),
        "inside_ogs_cell_rows": int(lookup_df["inside_ogs_cell"].sum()),
        "inside_ogs_mesh_bbox_rows": int(lookup_df["inside_ogs_mesh_bbox"].sum()),
        "within_approx_1p5m_center_support_rows": int(lookup_df["within_approx_1p5m_center_support"].sum()),
        "ready_for_residual_after_ogs_output_rows": int(lookup_df["ready_for_residual_after_ogs_output"].sum()),
        "ert_timesteps": int(timesteps.shape[0]),
        "ert_timesteps_with_matching_vtk": matched_vtk,
        "ert_timesteps_missing_matching_vtk": int(timesteps.shape[0] - matched_vtk),
        "calibration_relation_id": ert_operator.get("recommended_relation_id"),
        "calibration_status": ert_operator.get("status"),
        "remaining_blocker": (
            "Confirm the ERT-to-OGS coordinate transform and exact near-niche support mask, "
            "then sample OGS theta outputs and form log-resistivity residuals."
        ),
        "notes": [
            "Raw ERT VTK coordinates are shifted by +500 m in the second coordinate by default, matching the local slide convention that FEM x/y is interpreted in ERT x/z.",
            "The lookup uses ERT cell centroids, not electrode-pair forward modelling; it is a pragmatic common-support approximation.",
            "The approximate 1.5 m radius flag follows the local slide note, but the exact 35 cm-in-rock mask is not reconstructed here.",
            "Numerical residuals should use log10 resistivity after OGS theta is sampled and converted with the documented ERT calibration relation.",
        ],
    }
    markdown = write_markdown_text(summary)
    return lookup_df, summary, markdown


def write_markdown_text(summary: dict[str, Any]) -> str:
    relation = summary.get("calibration_relation_id", "n/a")
    lines = [
        "# ERT Spatial Projection Operator",
        "",
        "This file documents the current spatial support lookup between the ERT inversion mesh and the OGS bulk mesh.",
        "",
        "## Current Status",
        "",
        f"- Status: `{summary['status']}`",
        f"- Reference VTK: `{summary['reference_vtk_member']}`",
        f"- ERT cells: {summary['ert_cells']}",
        f"- ERT timesteps with matching VTK: {summary['ert_timesteps_with_matching_vtk']} of {summary['ert_timesteps']}",
        f"- OGS inside-cell rows: {summary['inside_ogs_cell_rows']}",
        f"- Approximate 1.5 m centre-support rows: {summary['within_approx_1p5m_center_support_rows']}",
        f"- Rows ready for residual after OGS output and support confirmation: {summary['ready_for_residual_after_ogs_output_rows']}",
        f"- Calibration relation: `{relation}`",
        "",
        "## Coordinate Transform",
        "",
        f"- `model_x = {summary['transform']['model_x']}`",
        f"- `model_y = {summary['transform']['model_y']}`",
        "",
        f"Raw ERT bounds: `{summary['raw_ert_bounds']}`",
        "",
        f"Transformed ERT centroid bounds: `{summary['transformed_ert_bounds']}`",
        "",
        f"OGS mesh bounds: `{summary['ogs_mesh_bounds']}`",
        "",
        "The +500 m shift in the second ERT coordinate is recorded as an explicit assumption.  It places the ERT inversion domain around the local OGS coordinate frame, but it still needs confirmation against the agreed ERT/FEM coordinate convention.",
        "",
        "## Residual Path",
        "",
        "1. Sample OGS `theta_model = porosity * liquid_saturation` at `ogs_lookup_cell_id` for the ERT lookup rows.",
        "2. Convert sampled theta to resistivity with `ert_water_content_resistivity_operator.csv`.",
        "3. Compare in log10 resistivity space against the ERT VTK `Resistivity(log10)` field.",
        "4. Use the support flags to restrict residuals to the agreed near-niche ERT support.",
        "",
        "## Remaining Blocker",
        "",
        summary["remaining_blocker"],
        "",
        "The lookup is intentionally not an active objective term yet: it is a reproducible geometry bridge for later OGS state-output evaluation.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    lookup, summary, markdown = build_lookup(args)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    lookup.to_csv(args.output_csv, index=False)
    args.summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    args.markdown_output.write_text(markdown, encoding="utf-8")
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.summary_output}")
    print(f"wrote {args.markdown_output}")
    print(f"ERT projection rows: {summary['ert_cells']}")


if __name__ == "__main__":
    main()
