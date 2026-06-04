#!/usr/bin/env python3
"""Map processed CD-A measurement coordinates onto the OGS bulk mesh."""

from __future__ import annotations

import argparse
import json
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_BGR_TO_MODEL_X_OFFSET = 4.63
DEFAULT_BGR_TO_MODEL_Y_OFFSET = -1.28


@dataclass(frozen=True)
class Mesh2D:
    points: np.ndarray
    cells: np.ndarray
    material_ids: np.ndarray
    vertices: np.ndarray
    centroids: np.ndarray
    tri_min: np.ndarray
    tri_max: np.ndarray
    mesh_min: np.ndarray
    mesh_max: np.ndarray


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mesh",
        type=Path,
        default=Path("GESA_model_original/projection_on_mesh_2025-09-05/bulk.vtu"),
        help="OGS VTU bulk mesh used for coordinate lookup.",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
        help="Directory containing processed coordinate CSVs.",
    )
    parser.add_argument(
        "--bgr-to-model-x-offset",
        type=float,
        default=DEFAULT_BGR_TO_MODEL_X_OFFSET,
        help="Offset for converting BGR model X to 2D model x.",
    )
    parser.add_argument(
        "--bgr-to-model-y-offset",
        type=float,
        default=DEFAULT_BGR_TO_MODEL_Y_OFFSET,
        help="Offset for converting BGR model Z to 2D model y.",
    )
    parser.add_argument(
        "--segment-sample-spacing",
        type=float,
        default=0.10,
        help="Approximate spacing in metres for borehole line samples.",
    )
    return parser.parse_args()


def parse_numeric_array(text: str | None, dtype: Any = float) -> np.ndarray:
    if not text:
        return np.array([], dtype=dtype)
    return np.fromstring(text, sep=" ", dtype=dtype)


def find_data_array(parent: ET.Element, name: str) -> ET.Element:
    for node in parent.findall("DataArray"):
        if node.attrib.get("Name") == name:
            return node
    raise KeyError(name)


def read_vtu_mesh(path: Path) -> Mesh2D:
    root = ET.parse(path).getroot()
    piece = root.find(".//Piece")
    if piece is None:
        raise ValueError(f"VTU Piece element not found in {path}")
    points_node = piece.find("./Points")
    cells_node = piece.find("./Cells")
    if points_node is None or cells_node is None:
        raise ValueError(f"VTU Points/Cells elements not found in {path}")

    points_array = points_node.find("DataArray")
    if points_array is None:
        raise ValueError(f"VTU Points DataArray not found in {path}")
    n_components = int(points_array.attrib.get("NumberOfComponents", "3"))
    points = parse_numeric_array(points_array.text, float).reshape((-1, n_components))

    connectivity = parse_numeric_array(find_data_array(cells_node, "connectivity").text, int)
    offsets = parse_numeric_array(find_data_array(cells_node, "offsets").text, int)
    starts = np.concatenate(([0], offsets[:-1]))
    cells = np.array([connectivity[start:stop] for start, stop in zip(starts, offsets)], dtype=int)
    if cells.ndim != 2 or cells.shape[1] < 3:
        raise ValueError("Only explicit triangle-like cells are supported")

    material_ids = np.full(cells.shape[0], -1, dtype=int)
    cell_data = piece.find("./CellData")
    if cell_data is not None:
        for data_array in cell_data.findall("DataArray"):
            if data_array.attrib.get("Name") == "MaterialIDs":
                values = parse_numeric_array(data_array.text, int)
                if values.size == cells.shape[0]:
                    material_ids = values.astype(int)
                break

    vertices = points[cells[:, :3], :2]
    centroids = vertices.mean(axis=1)
    tri_min = vertices.min(axis=1)
    tri_max = vertices.max(axis=1)
    mesh_min = points[:, :2].min(axis=0)
    mesh_max = points[:, :2].max(axis=0)
    return Mesh2D(
        points=points,
        cells=cells,
        material_ids=material_ids,
        vertices=vertices,
        centroids=centroids,
        tri_min=tri_min,
        tri_max=tri_max,
        mesh_min=mesh_min,
        mesh_max=mesh_max,
    )


def point_to_bbox_distance(point: np.ndarray, mesh: Mesh2D) -> float:
    dx = max(mesh.mesh_min[0] - point[0], 0.0, point[0] - mesh.mesh_max[0])
    dy = max(mesh.mesh_min[1] - point[1], 0.0, point[1] - mesh.mesh_max[1])
    return float(math.hypot(dx, dy))


def barycentric_inside(point: np.ndarray, triangle: np.ndarray, eps: float = 1e-10) -> bool:
    x, y = point
    x1, y1 = triangle[0]
    x2, y2 = triangle[1]
    x3, y3 = triangle[2]
    denominator = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
    if abs(denominator) < eps:
        return False
    a = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / denominator
    b = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / denominator
    c = 1.0 - a - b
    return a >= -eps and b >= -eps and c >= -eps


def locate_point(mesh: Mesh2D, x: float, y: float) -> dict[str, Any]:
    point = np.array([x, y], dtype=float)
    inside_bbox = bool(np.all(point >= mesh.mesh_min) and np.all(point <= mesh.mesh_max))
    candidate_mask = np.all(point >= mesh.tri_min - 1e-10, axis=1) & np.all(point <= mesh.tri_max + 1e-10, axis=1)
    containing_cell = -1
    for cell_id in np.flatnonzero(candidate_mask):
        if barycentric_inside(point, mesh.vertices[cell_id]):
            containing_cell = int(cell_id)
            break

    deltas = mesh.centroids - point
    nearest_cell = int(np.argmin(np.einsum("ij,ij->i", deltas, deltas)))
    nearest_distance = float(np.linalg.norm(mesh.centroids[nearest_cell] - point))
    lookup_cell = containing_cell if containing_cell >= 0 else nearest_cell
    status = "inside_cell" if containing_cell >= 0 else (
        "inside_mesh_bbox_nearest_cell" if inside_bbox else "outside_mesh_bbox_nearest_cell"
    )
    return {
        "lookup_status": status,
        "inside_mesh_bbox": inside_bbox,
        "distance_to_mesh_bbox_m": point_to_bbox_distance(point, mesh),
        "containing_cell_id": containing_cell,
        "nearest_cell_id": nearest_cell,
        "lookup_cell_id": int(lookup_cell),
        "lookup_material_id": int(mesh.material_ids[lookup_cell]),
        "nearest_centroid_x": float(mesh.centroids[nearest_cell, 0]),
        "nearest_centroid_y": float(mesh.centroids[nearest_cell, 1]),
        "nearest_centroid_distance_m": nearest_distance,
    }


def add_lookup_columns(df: pd.DataFrame, mesh: Mesh2D, x_col: str, y_col: str) -> pd.DataFrame:
    lookup_rows = []
    for _, row in df.iterrows():
        x = float(row[x_col])
        y = float(row[y_col])
        lookup = locate_point(mesh, x, y)
        lookup_rows.append({"lookup_x": x, "lookup_y": y, **lookup})
    return pd.concat([df.reset_index(drop=True), pd.DataFrame(lookup_rows)], axis=1)


def normalize_segment_label(label: str) -> tuple[str, str] | None:
    match = re.match(r"^(.*)\s+(Anfang|Ende)$", label.strip())
    if not match:
        return None
    return match.group(1), match.group(2)


def build_borehole_points(
    processed_dir: Path,
    mesh: Mesh2D,
    bgr_to_model_x_offset: float,
    bgr_to_model_y_offset: float,
) -> pd.DataFrame:
    df = pd.read_csv(processed_dir / "borehole_coordinates.csv")
    df["model_xy_x_from_bgr"] = df["bgr_model_x"] + bgr_to_model_x_offset
    df["model_xy_y_from_bgr_z"] = df["bgr_model_z"] + bgr_to_model_y_offset
    df["bgr_to_model_transform_note"] = (
        f"model x = BGR X + {bgr_to_model_x_offset:g}; "
        f"model y = BGR Z + {bgr_to_model_y_offset:g}; BGR Y is ignored for this 2D lookup"
    )
    return add_lookup_columns(df, mesh, "model_xy_x_from_bgr", "model_xy_y_from_bgr_z")


def build_measurement_points(processed_dir: Path, mesh: Mesh2D) -> pd.DataFrame:
    df = pd.read_csv(processed_dir / "measurement_coordinates_xy.csv")
    df["lookup_coordinate_frame"] = "2D_Model (x/y)"
    return add_lookup_columns(df, mesh, "model_xy_x", "model_xy_y")


def build_mesh_cells(mesh: Mesh2D) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "cell_id": np.arange(mesh.cells.shape[0], dtype=int),
            "material_id": mesh.material_ids,
            "centroid_x": mesh.centroids[:, 0],
            "centroid_y": mesh.centroids[:, 1],
            "bbox_min_x": mesh.tri_min[:, 0],
            "bbox_min_y": mesh.tri_min[:, 1],
            "bbox_max_x": mesh.tri_max[:, 0],
            "bbox_max_y": mesh.tri_max[:, 1],
        }
    )


def build_line_samples(
    borehole_points: pd.DataFrame,
    mesh: Mesh2D,
    spacing: float,
) -> pd.DataFrame:
    endpoints: dict[tuple[str, str], dict[str, pd.Series]] = {}
    for _, row in borehole_points.iterrows():
        parsed = normalize_segment_label(str(row["label"]))
        if parsed is None:
            continue
        segment_label, endpoint_name = parsed
        key = (str(row["group"]), segment_label)
        endpoints.setdefault(key, {})[endpoint_name] = row

    rows: list[dict[str, Any]] = []
    for (group, segment_label), pair in sorted(endpoints.items()):
        if "Anfang" not in pair or "Ende" not in pair:
            continue
        start = pair["Anfang"]
        end = pair["Ende"]
        start_xy = np.array([float(start["model_xy_x_from_bgr"]), float(start["model_xy_y_from_bgr_z"])])
        end_xy = np.array([float(end["model_xy_x_from_bgr"]), float(end["model_xy_y_from_bgr_z"])])
        vector = end_xy - start_xy
        length = float(np.linalg.norm(vector))
        intervals = max(1, int(math.ceil(length / spacing)))
        for sample_idx in range(intervals + 1):
            fraction = sample_idx / intervals
            point = start_xy + fraction * vector
            lookup = locate_point(mesh, float(point[0]), float(point[1]))
            rows.append(
                {
                    "group": group,
                    "segment_label": segment_label,
                    "start_label": start["label"],
                    "end_label": end["label"],
                    "sample_index": sample_idx,
                    "sample_count": intervals + 1,
                    "sample_fraction": fraction,
                    "distance_along_segment_m": length * fraction,
                    "segment_length_2d_m": length,
                    "sample_spacing_target_m": spacing,
                    "lookup_x": float(point[0]),
                    "lookup_y": float(point[1]),
                    **lookup,
                }
            )
    return pd.DataFrame(rows)


def summarize_status(df: pd.DataFrame) -> dict[str, int]:
    return {str(key): int(value) for key, value in df["lookup_status"].value_counts().sort_index().items()}


def main() -> None:
    args = parse_args()
    mesh_path = args.mesh.resolve()
    processed_dir = args.processed_dir.resolve()
    mesh = read_vtu_mesh(mesh_path)

    measurement_points = build_measurement_points(processed_dir, mesh)
    borehole_points = build_borehole_points(
        processed_dir,
        mesh,
        args.bgr_to_model_x_offset,
        args.bgr_to_model_y_offset,
    )
    line_samples = build_line_samples(borehole_points, mesh, args.segment_sample_spacing)
    mesh_cells = build_mesh_cells(mesh)

    measurement_points.to_csv(processed_dir / "measurement_mesh_lookup.csv", index=False)
    borehole_points.to_csv(processed_dir / "borehole_mesh_lookup.csv", index=False)
    line_samples.to_csv(processed_dir / "borehole_line_mesh_samples.csv", index=False)
    mesh_cells.to_csv(processed_dir / "ogs_bulk_mesh_cells.csv", index=False)

    summary = {
        "mesh": str(mesh_path),
        "processed_dir": str(processed_dir),
        "points": int(mesh.points.shape[0]),
        "cells": int(mesh.cells.shape[0]),
        "mesh_min_x": float(mesh.mesh_min[0]),
        "mesh_min_y": float(mesh.mesh_min[1]),
        "mesh_max_x": float(mesh.mesh_max[0]),
        "mesh_max_y": float(mesh.mesh_max[1]),
        "bgr_to_2d_model_transform": {
            "model_x": f"BGR X + {args.bgr_to_model_x_offset:g}",
            "model_y": f"BGR Z + {args.bgr_to_model_y_offset:g}",
            "ignored_axis": "BGR Y",
        },
        "generated": {
            "measurement_mesh_lookup.csv": {
                "rows": int(measurement_points.shape[0]),
                "lookup_status": summarize_status(measurement_points),
            },
            "borehole_mesh_lookup.csv": {
                "rows": int(borehole_points.shape[0]),
                "lookup_status": summarize_status(borehole_points),
            },
            "borehole_line_mesh_samples.csv": {
                "rows": int(line_samples.shape[0]),
                "segments": int(line_samples["segment_label"].nunique()) if not line_samples.empty else 0,
                "lookup_status": summarize_status(line_samples) if not line_samples.empty else {},
            },
            "ogs_bulk_mesh_cells.csv": {
                "rows": int(mesh_cells.shape[0]),
            },
        },
    }
    (processed_dir / "mesh_lookup_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print(f"mesh: {mesh.points.shape[0]} points, {mesh.cells.shape[0]} cells")
    print(f"mesh bounds x=[{mesh.mesh_min[0]:.6g}, {mesh.mesh_max[0]:.6g}], y=[{mesh.mesh_min[1]:.6g}, {mesh.mesh_max[1]:.6g}]")
    for name, details in summary["generated"].items():
        print(f"{name}: {details['rows']} rows")
        if "lookup_status" in details:
            print(f"  status: {details['lookup_status']}")


if __name__ == "__main__":
    main()
