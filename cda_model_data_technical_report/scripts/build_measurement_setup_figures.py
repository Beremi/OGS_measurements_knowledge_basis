#!/usr/bin/env python3
"""Build measurement setup and data-shape figures for the CD-A report."""

from __future__ import annotations

import base64
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET
import zipfile

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "cda_model_data_technical_report"
FIG = REPORT / "figures"
PROC = ROOT / "SOTA_OGS_Mont_Terri_work" / "inversion_workflow" / "processed_observations"
OGS_INPUTS = ROOT / "SOTA_OGS_Mont_Terri_work" / "inversion_workflow" / "current_permeability_field" / "ogs_run_inputs"
ERT_MESH_CACHE: dict[tuple[str, str], dict[str, np.ndarray]] = {}


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(PROC / name)


def save(fig: plt.Figure, name: str) -> None:
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=230)
    plt.close(fig)


def plot_mesh(ax: plt.Axes, mesh: pd.DataFrame, title: str) -> None:
    colors = np.where(mesh["material_id"].to_numpy() == 0, "#dadada", "#eeeeee")
    ax.scatter(mesh["centroid_x"], mesh["centroid_y"], s=1.0, c=colors, edgecolors="none", zorder=0)
    ax.set_aspect("equal", adjustable="box")
    pad = 0.25
    ax.set_xlim(mesh["centroid_x"].min() - pad, mesh["centroid_x"].max() + pad)
    ax.set_ylim(mesh["centroid_y"].min() - pad, mesh["centroid_y"].max() + pad)
    ax.set_xlabel("model x [m]")
    ax.set_ylabel("model y [m]")
    ax.set_title(title)
    ax.grid(alpha=0.18, linewidth=0.4)


def line_segments(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {seg: g.sort_values("sample_index") for seg, g in df.groupby("segment_label")}


def annotate_end(ax: plt.Axes, df: pd.DataFrame, label: str, *, color: str = "black") -> None:
    if df.empty:
        return
    row = df.sort_values("sample_index").iloc[-1]
    ax.text(row["lookup_x"], row["lookup_y"], label, fontsize=7, color=color,
            ha="left", va="center", clip_on=True)


def annotate_points(ax: plt.Axes, df: pd.DataFrame, *, x: str, y: str, label: str,
                    fontsize: float = 6.5) -> None:
    for _, row in df.iterrows():
        ax.text(row[x], row[y], str(row[label]), fontsize=fontsize, ha="left",
                va="bottom", clip_on=True)


def style_time_axis(ax: plt.Axes) -> None:
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(alpha=0.25)


def read_appended_vtu_arrays(path: Path) -> dict[str, np.ndarray]:
    """Read compact OGS VTU submeshes whose offsets are base64 character offsets."""
    text = path.read_text(errors="replace")
    match = re.search(r"<AppendedData[^>]*>\s*_(.*?)\s*</AppendedData>", text, re.S)
    if not match:
        raise ValueError(f"No appended data block in {path}")
    appended = match.group(1).strip().replace("\n", "").replace(" ", "")
    root = ET.fromstring(text)

    arrays: list[tuple[int, ET.Element]] = []
    for data_array in root.findall(".//DataArray"):
        offset = data_array.get("offset")
        if offset is not None:
            arrays.append((int(offset), data_array))
    arrays.sort(key=lambda item: item[0])

    dtype_map = {
        "Float64": "<f8",
        "Int64": "<i8",
        "UInt64": "<u8",
        "UInt8": "u1",
    }
    decoded: dict[str, np.ndarray] = {}
    for idx, (offset, data_array) in enumerate(arrays):
        end = arrays[idx + 1][0] if idx + 1 < len(arrays) else len(appended)
        chunk = appended[offset:end]
        chunk += "=" * ((4 - len(chunk) % 4) % 4)
        raw = base64.b64decode(chunk)
        payload_len = struct.unpack("<Q", raw[:8])[0]
        payload = raw[8:8 + payload_len]
        dtype = dtype_map[data_array.get("type", "")]
        values = np.frombuffer(payload, dtype=dtype).copy()
        components = int(data_array.get("NumberOfComponents") or "1")
        if components > 1:
            values = values.reshape((-1, components))
        decoded[data_array.get("Name") or data_array.tag] = values
    return decoded


def boundary_segments_from_vtu(name: str) -> list[np.ndarray]:
    arrays = read_appended_vtu_arrays(OGS_INPUTS / f"{name}.vtu")
    points = arrays["Points"][:, :2]
    connectivity = arrays["connectivity"]
    offsets = arrays["offsets"]
    segments: list[np.ndarray] = []
    start = 0
    for offset in offsets:
        cell = connectivity[start:int(offset)]
        start = int(offset)
        if len(cell) >= 2:
            # OGS boundary files use VTK_QUADRATIC_EDGE: endpoints first, midpoint third.
            segments.append(points[cell[:2]])
    return segments


def add_boundary_segments(ax: plt.Axes, name: str, *, color: str, linewidth: float,
                          alpha: float = 1.0, linestyle: str = "-", label: str | None = None,
                          zorder: int = 5) -> None:
    segments = boundary_segments_from_vtu(name)
    if not segments:
        return
    collection = LineCollection(segments, colors=color, linewidths=linewidth,
                                alpha=alpha, linestyles=linestyle, label=label,
                                zorder=zorder)
    ax.add_collection(collection)


def build_boundary_conditions_domain(mesh: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.4, 7.0))
    colors = np.where(mesh["material_id"].to_numpy() == 0, "#d0d0d0", "#eeeeee")
    ax.scatter(mesh["centroid_x"], mesh["centroid_y"], s=1.0, c=colors,
               edgecolors="none", zorder=0)

    # Mechanical constraints on the outer box.
    for mesh_name, label in [
        ("cd-a_left", "mechanical fixed normal displacement"),
        ("cd-a_right", None),
        ("cd-a_top", None),
        ("cd-a_bottom", None),
    ]:
        add_boundary_segments(ax, mesh_name, color="#d95f02", linewidth=3.2,
                              alpha=0.95, linestyle="--", label=label, zorder=4)

    # Hydraulic Dirichlet supports.
    add_boundary_segments(ax, "cd-a_top", color="#2166ac", linewidth=2.3,
                          alpha=0.98, label="hydraulic pressure Dirichlet", zorder=7)
    add_boundary_segments(ax, "cd-a_niche4", color="#762a83", linewidth=2.4,
                          alpha=0.98, label="open-niche pressure curve", zorder=8)

    ax.text(0.0, 5.22, r"top: $p=1.5$ MPa, $u_y=0$", ha="center", va="bottom",
            fontsize=8.2, color="#1f1f1f",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#777777", alpha=0.92))
    ax.text(-5.28, 0.0, r"left: $u_x=0$", ha="right", va="center", rotation=90,
            fontsize=8.2, bbox=dict(boxstyle="round,pad=0.25", fc="white",
                                    ec="#777777", alpha=0.92))
    ax.text(5.28, 0.0, r"right: $u_x=0$", ha="left", va="center", rotation=90,
            fontsize=8.2, bbox=dict(boxstyle="round,pad=0.25", fc="white",
                                    ec="#777777", alpha=0.92))
    ax.text(0.0, -5.24, r"bottom: $u_y=0$", ha="center", va="top", fontsize=8.2,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#777777", alpha=0.92))
    ax.text(1.45, 0.35, r"open niche: $p=p_{\rm open}(t)$", ha="left", va="center",
            fontsize=8.2, color="#3f0b4f",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#762a83", alpha=0.92))
    ax.text(2.05, -4.55, r"$T=298.15$ K on `bulk_all' support", ha="left", va="center",
            fontsize=8.0, color="#1b7837",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#1b7837", alpha=0.92))

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-5.55, 5.55)
    ax.set_ylim(-5.55, 5.55)
    ax.set_xlabel("model x [m]")
    ax.set_ylabel("model y [m]")
    ax.set_title("Active OGS boundary-condition supports")
    ax.grid(alpha=0.18, linewidth=0.4)
    ax.legend(loc="lower left", fontsize=7.3, frameon=True)
    save(fig, "boundary_conditions_domain.png")


def load_reference_ert_mesh(ert: pd.DataFrame) -> dict[str, np.ndarray]:
    """Load the reference ERT VTK topology and transform its nodes into model x/y."""
    zip_path = Path(str(ert["source_file"].iloc[0]))
    member = str(ert["reference_vtk_member"].iloc[0])
    cache_key = (str(zip_path), member)
    if cache_key in ERT_MESH_CACHE:
        return ERT_MESH_CACHE[cache_key]

    with zipfile.ZipFile(zip_path) as archive:
        lines = archive.read(member).decode("latin1", errors="replace").splitlines()

    point_idx = next(i for i, line in enumerate(lines) if line.startswith("POINTS "))
    point_count = int(lines[point_idx].split()[1])
    point_tokens: list[str] = []
    cursor = point_idx + 1
    while len(point_tokens) < 3 * point_count:
        point_tokens.extend(lines[cursor].split())
        cursor += 1
    raw_points = np.array(point_tokens[: 3 * point_count], dtype=float).reshape(point_count, 3)

    cell_idx = next(i for i, line in enumerate(lines) if line.startswith("CELLS "))
    parts = lines[cell_idx].split()
    cell_count = int(parts[1])
    cell_token_count = int(parts[2])
    cell_tokens: list[str] = []
    cursor = cell_idx + 1
    while len(cell_tokens) < cell_token_count:
        cell_tokens.extend(lines[cursor].split())
        cursor += 1

    cell_values = np.array(cell_tokens[:cell_token_count], dtype=int)
    cells: list[list[int]] = []
    pos = 0
    for _ in range(cell_count):
        vertices = int(cell_values[pos])
        cells.append(cell_values[pos + 1 : pos + 1 + vertices].tolist())
        pos += vertices + 1
    triangle_cells = np.array([cell for cell in cells if len(cell) == 3], dtype=int)

    # The processed projection table states: model_x = raw_x, model_y = raw_y + 500.
    model_points = np.column_stack([raw_points[:, 0], raw_points[:, 1] + 500.0])
    result = {"points": model_points, "cells": triangle_cells}
    ERT_MESH_CACHE[cache_key] = result
    return result


def ert_cell_ids(ert: pd.DataFrame, mask: pd.Series | np.ndarray | None = None) -> np.ndarray:
    if mask is None:
        selected = ert
    else:
        selected = ert[mask]
    return selected["ert_cell_id"].astype(int).to_numpy()


def ert_triangles(ert_mesh: dict[str, np.ndarray], cell_ids: np.ndarray) -> np.ndarray:
    cells = ert_mesh["cells"]
    valid = cell_ids[(cell_ids >= 0) & (cell_ids < len(cells))]
    return ert_mesh["points"][cells[valid]]


def add_ert_wire(ax: plt.Axes, ert_mesh: dict[str, np.ndarray], cell_ids: np.ndarray,
                 *, color: str, alpha: float, linewidth: float, label: str | None = None) -> None:
    triangles = ert_triangles(ert_mesh, cell_ids)
    if len(triangles) == 0:
        return
    segments = np.concatenate([triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]])
    lines = LineCollection(segments, colors=color, linewidths=linewidth, alpha=alpha, label=label)
    ax.add_collection(lines)


def add_ert_nodes(ax: plt.Axes, ert_mesh: dict[str, np.ndarray], cell_ids: np.ndarray,
                  *, color: str, alpha: float, size: float, label: str | None = None) -> None:
    cells = ert_mesh["cells"]
    valid = cell_ids[(cell_ids >= 0) & (cell_ids < len(cells))]
    if len(valid) == 0:
        return
    node_ids = np.unique(cells[valid].ravel())
    pts = ert_mesh["points"][node_ids]
    ax.scatter(pts[:, 0], pts[:, 1], s=size, color=color, alpha=alpha,
               edgecolors="none", label=label, zorder=4)


def add_ert_colored_cells(ax: plt.Axes, ert_mesh: dict[str, np.ndarray], ert: pd.DataFrame,
                          cell_ids: np.ndarray) -> PolyCollection:
    cells = ert_mesh["cells"]
    valid = cell_ids[(cell_ids >= 0) & (cell_ids < len(cells))]
    triangles = ert_triangles(ert_mesh, valid)
    value_map = ert.set_index("ert_cell_id")["sample_log10_resistivity"]
    values = value_map.reindex(valid).to_numpy(dtype=float)
    collection = PolyCollection(
        triangles,
        array=values,
        cmap="viridis",
        edgecolors=(1, 1, 1, 0.35),
        linewidths=0.035,
        alpha=0.95,
    )
    ax.add_collection(collection)
    return collection


def truthy(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin({"true", "1", "yes"})


def select_ert_near_niche_cells(ert: pd.DataFrame, count: int = 10) -> pd.DataFrame:
    candidates = ert[truthy(ert["inside_ogs_cell"])
                     & truthy(ert["within_approx_1p5m_center_support"])].copy()
    if candidates.empty:
        candidates = ert[truthy(ert["inside_ogs_cell"])].copy()
    if candidates.empty:
        return candidates

    candidates["radius"] = np.hypot(candidates["model_x"], candidates["model_y"])
    candidates["angle"] = (np.arctan2(candidates["model_y"], candidates["model_x"]) + 2 * np.pi) % (2 * np.pi)
    radius_target = float(candidates["radius"].quantile(0.20))
    radius_scale = max(float(candidates["radius"].std()), 0.08)
    angle_targets = np.linspace(0, 2 * np.pi, count, endpoint=False)

    selected_indices: list[int] = []
    for target in angle_targets:
        remaining = candidates.drop(index=selected_indices, errors="ignore")
        if remaining.empty:
            break
        angular_distance = np.abs((remaining["angle"] - target + np.pi) % (2 * np.pi) - np.pi)
        radial_distance = np.abs(remaining["radius"] - radius_target)
        score = angular_distance / (np.pi / count) + radial_distance / radius_scale
        selected_indices.append(int(score.idxmin()))

    selected = candidates.loc[selected_indices].copy()
    selected["sample_label"] = [f"E{i}" for i in range(1, len(selected) + 1)]
    return selected


def read_vtk_cell_scalar_selected(archive: zipfile.ZipFile, member: str,
                                  scalar_name: str, cell_ids: np.ndarray) -> np.ndarray:
    lines = archive.read(member).decode("latin1", errors="replace").splitlines()
    cell_data_idx = next(i for i, line in enumerate(lines) if line.startswith("CELL_DATA "))
    scalar_idx = next(
        i for i in range(cell_data_idx + 1, len(lines))
        if lines[i].startswith(f"SCALARS {scalar_name} ")
    )
    cursor = scalar_idx + 1
    if cursor < len(lines) and lines[cursor].startswith("LOOKUP_TABLE"):
        cursor += 1

    needed_values = int(np.max(cell_ids)) + 1
    tokens: list[str] = []
    while len(tokens) < needed_values and cursor < len(lines):
        line = lines[cursor].strip()
        if line.startswith(("SCALARS ", "POINT_DATA ", "CELL_DATA ")):
            break
        tokens.extend(line.split())
        cursor += 1

    if len(tokens) < needed_values:
        raise ValueError(f"{member} has only {len(tokens)} values for {scalar_name}")
    values = np.asarray(tokens[:needed_values], dtype=float)
    return values[cell_ids]


def build_ert_near_niche_timeseries(timesteps: pd.DataFrame, cell_ids: np.ndarray) -> pd.DataFrame:
    ts = timesteps.copy()
    ts["timestamp_iso"] = pd.to_datetime(ts["timestamp_iso"], errors="coerce")
    ts = ts.dropna(subset=["timestamp_iso", "matching_vtk_member"])
    if "has_matching_vtk" in ts.columns:
        ts = ts[truthy(ts["has_matching_vtk"])]
    ts = ts.sort_values("timestamp_iso")

    records: list[dict[str, object]] = []
    for source_file, group in ts.groupby("source_file", sort=False):
        zip_path = Path(str(source_file))
        if not zip_path.is_absolute():
            zip_path = ROOT / zip_path
        with zipfile.ZipFile(zip_path) as archive:
            for row in group.itertuples(index=False):
                member = str(row.matching_vtk_member)
                values = read_vtk_cell_scalar_selected(
                    archive, member, "Resistivity(log10)", cell_ids
                )
                record: dict[str, object] = {"timestamp_iso": row.timestamp_iso}
                for cell_id, value in zip(cell_ids, values):
                    record[int(cell_id)] = float(value)
                records.append(record)

    if not records:
        return pd.DataFrame(columns=["timestamp_iso", *[int(cell_id) for cell_id in cell_ids]])
    return pd.DataFrame.from_records(records).sort_values("timestamp_iso")


def plot_hm_zone_map(ax: plt.Axes, zones: pd.DataFrame, title: str) -> None:
    palette = {
        "mini_piezometer": "#1b9e77",
        "extensometer": "#d95f02",
        "laser_scan_surface": "#7570b3",
        "laser_scan_geodetic_support": "#e7298a",
        "miniprisma_geodesy": "#66a61e",
        "convergence_points": "#e6ab02",
        "evapometer": "#a6761d",
    }
    for mtype, group in zones.groupby("measurement_type"):
        color = palette.get(mtype, "#666666")
        for _, row in group.iterrows():
            width = row["x_max"] - row["x_min"]
            height = row["z_max"] - row["z_min"]
            if np.isfinite(width) and np.isfinite(height) and width > 0 and height > 0:
                ax.add_patch(Rectangle((row["x_min"], row["z_min"]), width, height,
                                       facecolor=color, edgecolor=color, alpha=0.12,
                                       linewidth=0.8))
        size = np.clip(group["nodes"].to_numpy() / 60.0, 18, 160)
        ax.scatter(group["x_mean"], group["z_mean"], s=size, color=color,
                   edgecolor="white", linewidth=0.35, alpha=0.85,
                   label=mtype.replace("_", " "))
        annotate_points(ax, group, x="x_mean", y="z_mean", label="zone_name", fontsize=6.2)

    ax.set_title(title)
    ax.set_xlabel("source visualisation x")
    ax.set_ylabel("source visualisation z")
    if not zones.empty:
        xmin, xmax = zones["x_min"].min(), zones["x_max"].max()
        zmin, zmax = zones["z_min"].min(), zones["z_max"].max()
        dx = max(float(xmax - xmin), 0.5)
        dz = max(float(zmax - zmin), 0.5)
        ax.set_xlim(xmin - 0.08 * dx, xmax + 0.18 * dx)
        ax.set_ylim(zmin - 0.10 * dz, zmax + 0.14 * dz)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=6.2, loc="best")


def build_all_locations(mesh: pd.DataFrame, lookup: pd.DataFrame, lines: pd.DataFrame, ert: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.2, 7.2))
    plot_mesh(ax, mesh, "Measurement support on current OGS mesh")

    ert_mesh = load_reference_ert_mesh(ert)
    inside_ert = ert[ert["inside_ogs_cell"].astype(bool)]
    support_ert = inside_ert[inside_ert["within_approx_1p5m_center_support"].astype(bool)]
    add_ert_wire(ax, ert_mesh, ert_cell_ids(inside_ert), color="#9ecae1", alpha=0.18,
                 linewidth=0.18, label="ERT triangular mesh")
    add_ert_nodes(ax, ert_mesh, ert_cell_ids(support_ert), color="#2171b5", alpha=0.38,
                  size=1.3, label="ERT approx. support nodes")

    marker = {"NMR": "o", "Suction": "^", "Taupe": "s", "Permeablilty": "D"}
    color = {"NMR": "#2a7f62", "Suction": "#8856a7", "Taupe": "#d95f0e", "Permeablilty": "#b2182b"}
    for mtype, group in lookup.groupby("measurement_type"):
        ax.scatter(group["lookup_x"], group["lookup_y"], s=32, marker=marker.get(mtype, "o"),
                   color=color.get(mtype, "black"), edgecolor="white", linewidth=0.35,
                   label=mtype.replace("Permeablilty", "Permeability"), zorder=4)

    for seg, group in line_segments(lines).items():
        if group["group"].iloc[0] == "Charac. Bohrungen":
            ax.plot(group["lookup_x"], group["lookup_y"], color="#b2182b", linewidth=1.5, alpha=0.75, zorder=3)
        elif group["group"].iloc[0] == "Taupe":
            ax.plot(group["lookup_x"], group["lookup_y"], color="#d95f0e", linewidth=1.4, alpha=0.75, zorder=3)
    ax.legend(loc="upper right", fontsize=7, frameon=True)
    save(fig, "setup_all_measurement_locations_mesh.png")


def build_ert(mesh: pd.DataFrame, ert: pd.DataFrame, timesteps: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4))
    plot_mesh(axes[0], mesh, "ERT projected support")
    ert_mesh = load_reference_ert_mesh(ert)
    inside = ert[ert["inside_ogs_cell"].astype(bool)]
    support = inside[inside["within_approx_1p5m_center_support"].astype(bool)]
    add_ert_wire(axes[0], ert_mesh, ert_cell_ids(inside), color="#9ecae1", alpha=0.26,
                 linewidth=0.20, label="ERT triangular cells inside OGS mesh")
    add_ert_nodes(axes[0], ert_mesh, ert_cell_ids(support), color="#08519c", alpha=0.65,
                  size=1.6, label="approx. 1.5 m support nodes")
    axes[0].legend(fontsize=7)

    sc = add_ert_colored_cells(axes[1], ert_mesh, ert, ert_cell_ids(inside))
    add_ert_nodes(axes[1], ert_mesh, ert_cell_ids(inside), color="black", alpha=0.10, size=0.25)
    axes[1].set_aspect("equal", adjustable="box")
    axes[1].set_title("Reference ERT triangular mesh: log10 resistivity")
    axes[1].set_xlabel("model x [m]")
    axes[1].set_ylabel("model y [m]")
    axes[1].grid(alpha=0.18, linewidth=0.4)
    fig.colorbar(sc, ax=axes[1], label="log10 ohm m")

    ts = timesteps.copy()
    ts["timestamp_iso"] = pd.to_datetime(ts["timestamp_iso"], errors="coerce")
    counts = ts.dropna(subset=["timestamp_iso"]).set_index("timestamp_iso").resample("MS").size()
    axes[2].bar(counts.index, counts.values, width=25, color="#3182bd")
    axes[2].xaxis.set_major_locator(mdates.YearLocator())
    axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axes[2].set_title("ERT time coverage")
    axes[2].set_ylabel("timestep entries per month")
    axes[2].set_xlabel("date")
    axes[2].grid(axis="y", alpha=0.25)
    save(fig, "setup_ert_location_data.png")


def build_nmr(mesh: pd.DataFrame, boreholes: pd.DataFrame, weekly: pd.DataFrame, seasonal: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4))
    plot_mesh(axes[0], mesh, "NMR measurement labels on mesh")
    nmr = boreholes[boreholes["group"].eq("NMR")]
    axes[0].scatter(nmr["lookup_x"], nmr["lookup_y"], s=42, color="#2a7f62", edgecolor="white", linewidth=0.4)
    for _, row in nmr.iterrows():
        axes[0].text(row["lookup_x"], row["lookup_y"], row["label"].replace("NMR_", ""), fontsize=6, ha="left", va="bottom")

    wk = weekly.copy()
    wk["date_iso"] = pd.to_datetime(wk["date_iso"], errors="coerce")
    for station, group in wk.dropna(subset=["date_iso"]).groupby("station"):
        axes[1].plot(group["date_iso"], group["water_content_vol_percent"], marker=".", linewidth=0.9, label=station)
    axes[1].set_title("NMR weekly water content")
    axes[1].set_ylabel("volumetric water content [vol.%]")
    axes[1].set_xlabel("date")
    axes[1].legend(fontsize=7)
    axes[1].grid(alpha=0.25)
    axes[1].xaxis.set_major_locator(mdates.YearLocator())
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    sea = seasonal.copy()
    sea["campaign_date"] = pd.to_datetime(sea["campaign_date"], errors="coerce")
    sea4 = sea[sea["niche"].eq("Niche 4")].dropna(subset=["campaign_date"])
    if not sea4.empty:
        latest_date = sea4["campaign_date"].max()
        latest = sea4[sea4["campaign_date"].eq(latest_date)].copy()
        latest = latest.sort_values("position")
        axes[2].errorbar(latest["position"], latest["water_content_vol_percent"],
                         yerr=latest["wc_ci95_vol_percent"], fmt="o", color="#238b45", ecolor="#74c476")
        axes[2].set_title(f"NMR seasonal profile, Niche 4, {latest_date.date()}")
        axes[2].tick_params(axis="x", rotation=65, labelsize=7)
    axes[2].set_ylabel("water content [vol.%]")
    axes[2].set_xlabel("measurement position")
    axes[2].grid(axis="y", alpha=0.25)
    save(fig, "setup_nmr_location_data.png")


def build_permeability(mesh: pd.DataFrame, lines: pd.DataFrame, cells: pd.DataFrame, targets: pd.DataFrame, mesh_cells: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4))
    plot_mesh(axes[0], mesh, "Permeability pulse-test intervals")
    char_lines = {k: v for k, v in line_segments(lines).items() if v["group"].iloc[0] == "Charac. Bohrungen"}
    for seg, group in char_lines.items():
        axes[0].plot(group["lookup_x"], group["lookup_y"], linewidth=1.4, label=seg)
        annotate_end(axes[0], group, seg)
    merged = cells.merge(mesh_cells[["cell_id", "centroid_x", "centroid_y"]], left_on="lookup_cell_id", right_on="cell_id", how="left")
    active = merged[merged["usable_for_current_ogs_fit"].astype(str).eq("True")]
    sc = axes[0].scatter(active["centroid_x"], active["centroid_y"], c=active["log10_permeability_m2"],
                         s=38, cmap="magma", edgecolor="white", linewidth=0.25, zorder=4)
    fig.colorbar(sc, ax=axes[0], label="log10 k [m2]")

    t = targets[targets["positive_permeability"].astype(str).eq("True") if "positive_permeability" in targets.columns else targets["permeability_m2"].gt(0)].copy()
    if "positive_permeability" not in targets.columns:
        t = targets[targets["permeability_m2"].gt(0)].copy()
    for seg, group in t.groupby("normalized_segment_label"):
        axes[1].scatter(group["borehole_depth_m"], group["log10_permeability_m2"], s=16, alpha=0.75, label=seg)
    axes[1].invert_xaxis()
    axes[1].set_xlabel("borehole depth [m]")
    axes[1].set_ylabel("log10 permeability [m2]")
    axes[1].set_title("Interpreted permeability by depth")
    axes[1].grid(alpha=0.25)
    axes[1].legend(fontsize=6, ncol=2)

    usable_counts = targets["target_status"].value_counts().sort_index()
    axes[2].barh(usable_counts.index, usable_counts.values, color="#b2182b")
    axes[2].set_title("Permeability target status")
    axes[2].set_xlabel("rows")
    axes[2].tick_params(axis="y", labelsize=7)
    axes[2].grid(axis="x", alpha=0.25)
    save(fig, "setup_permeability_location_data.png")


def build_taupe(mesh: pd.DataFrame, lines: pd.DataFrame, taupe: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4))
    plot_mesh(axes[0], mesh, "Taupe/TDR borehole supports")
    for seg, group in line_segments(lines).items():
        if group["group"].iloc[0] != "Taupe":
            continue
        axes[0].plot(group["lookup_x"], group["lookup_y"], linewidth=1.7, alpha=0.85)
        annotate_end(axes[0], group, seg, color="#d95f0e")

    tp = taupe.copy()
    tp["date_iso"] = pd.to_datetime(tp["date_iso"], errors="coerce")
    subset = tp[tp["sensor"].isin(["A3", "A4"]) & tp["edz_band_cm"].isin(["0-50", "0-10", "40-50"])].dropna(subset=["date_iso"])
    for (sensor, band), group in subset.groupby(["sensor", "edz_band_cm"]):
        axes[1].plot(group["date_iso"], group["taupe_value"], linewidth=0.9, label=f"{sensor} {band}")
    axes[1].set_title("Taupe/TDR workbook values")
    axes[1].set_ylabel("workbook value [unit pending]")
    axes[1].set_xlabel("date")
    axes[1].legend(fontsize=6, ncol=2)
    axes[1].grid(alpha=0.25)
    axes[1].xaxis.set_major_locator(mdates.YearLocator())
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    latest_date = tp["date_iso"].max()
    latest = tp[tp["date_iso"].eq(latest_date) & tp["sensor"].isin(["A3", "A4"])].copy()
    latest = latest.sort_values(["sensor", "edz_min_cm"])
    for sensor, group in latest.groupby("sensor"):
        axes[2].plot(group["edz_min_cm"], group["taupe_value"], marker="o", linewidth=1, label=sensor)
    axes[2].set_title(f"Latest EDZ-band profile, {latest_date.date()}")
    axes[2].set_xlabel("EDZ band lower edge [cm]")
    axes[2].set_ylabel("workbook value [unit pending]")
    axes[2].legend(fontsize=7)
    axes[2].grid(alpha=0.25)
    save(fig, "setup_taupe_location_data.png")


def build_rh(mesh: pd.DataFrame, lookup: pd.DataFrame, rh: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4))
    plot_mesh(axes[0], mesh, "RH/suction coordinate rows")
    su = lookup[lookup["measurement_type"].eq("Suction")]
    axes[0].scatter(su["lookup_x"], su["lookup_y"], s=48, marker="^", color="#8856a7", edgecolor="white", linewidth=0.4)
    for i, (_, row) in enumerate(su.iterrows(), start=1):
        axes[0].text(row["lookup_x"], row["lookup_y"], f"RH/S{i}", fontsize=6, ha="left", va="bottom")

    rr = rh.copy()
    rr["date_iso"] = pd.to_datetime(rr["date_iso"], errors="coerce")
    rr = rr.dropna(subset=["date_iso"])
    rr, _ = filter_rh_plot_rows(rr)
    for sensor, group in rr.groupby("sensor"):
        axes[1].plot(group["date_iso"], group["rh_percent"], linewidth=0.85, label=sensor)
    axes[1].axhline(95, color="black", linestyle="--", linewidth=0.8, alpha=0.65)
    axes[1].set_title("RH workbook time series")
    axes[1].set_ylabel("relative humidity [%]")
    axes[1].set_xlabel("date")
    axes[1].legend(fontsize=7)
    axes[1].grid(alpha=0.25)
    axes[1].xaxis.set_major_locator(mdates.YearLocator())
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    for sensor, group in rr.groupby("sensor"):
        axes[2].plot(group["date_iso"], group["liquid_pressure_gauge_pa_kelvin"] / 1e6, linewidth=0.85, label=sensor)
    axes[2].set_title("Kelvin liquid-pressure conversion")
    axes[2].set_ylabel("gauge liquid pressure [MPa]")
    axes[2].set_xlabel("date")
    axes[2].grid(alpha=0.25)
    axes[2].xaxis.set_major_locator(mdates.YearLocator())
    axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    save(fig, "setup_rh_location_data.png")


def filter_rh_plot_rows(rh: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove the known RH7/RH8 logger-corruption episode from plots only."""
    if "low_outlier_rh_lt_50" in rh.columns:
        low_outlier = truthy(rh["low_outlier_rh_lt_50"])
    else:
        low_outlier = rh["rh_percent"].lt(50)
    dropout_window = (
        rh["sensor"].isin(["RH7", "RH8"])
        & rh["date_iso"].ge(pd.Timestamp("2022-02-28"))
        & rh["date_iso"].le(pd.Timestamp("2022-03-30"))
    )
    plot_corruption = low_outlier | dropout_window
    return rh.loc[~plot_corruption].copy(), int(plot_corruption.sum())


def build_other_hm(mesh: pd.DataFrame) -> None:
    lev = read_csv("other_hm_levelling_displacements.csv")
    qual = read_csv("other_hm_qualitative_targets.csv")
    zones = read_csv("other_hm_visualisation_zones.csv")

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4))
    plot_mesh(axes[0], mesh, "Other-HM hard-residual geometry")
    axes[0].text(0.5, 0.5,
                 "Geoscope / laser / levelling context is catalogued,\n"
                 "but no mesh-ready hard-residual point/line table\n"
                 "with epoch, support and uncertainty is available yet.",
                 transform=axes[0].transAxes, ha="center", va="center",
                 fontsize=8, bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#a63a3a", alpha=0.9))

    lev = lev.copy()
    lev["point_label"] = lev["point_name"].astype(str) + "\\n" + lev["location"].astype(str)
    colors = np.where(lev["height_difference_mm"] >= 0, "#3182bd", "#de2d26")
    axes[1].bar(np.arange(len(lev)), lev["height_difference_mm"], color=colors)
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[1].set_xticks(np.arange(len(lev)))
    axes[1].set_xticklabels(lev["point_label"], rotation=65, ha="right", fontsize=6)
    axes[1].set_ylabel("height difference [mm]")
    axes[1].set_title("Extracted precision-levelling values")
    axes[1].grid(axis="y", alpha=0.25)

    counts = qual["measurement_type"].value_counts().sort_values()
    axes[2].barh(counts.index, counts.values, color="#756bb1")
    axes[2].set_title("Other-HM evidence currently catalogued")
    axes[2].set_xlabel("structured evidence rows")
    axes[2].tick_params(axis="y", labelsize=7)
    axes[2].grid(axis="x", alpha=0.25)
    save(fig, "setup_other_hm_location_data.png")

    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    interesting = zones[zones["measurement_type"].isin([
        "mini_piezometer", "extensometer", "laser_scan_surface", "laser_scan_geodetic_support",
        "permeability_support", "rh_suction_support", "taupe_tdr_support", "nmr_support",
        "fracture_or_crack_geometry",
    ])].copy()
    for mtype, group in interesting.groupby("measurement_type"):
        ax.scatter(group["x_mean"], group["z_mean"], s=np.clip(group["nodes"] / 80, 12, 90), alpha=0.65, label=mtype.replace("_", " "))
    ax.set_title("Other-HM/support zones in source visualisation frame")
    ax.set_xlabel("source x mean")
    ax.set_ylabel("source z mean")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=6, ncol=2)
    save(fig, "setup_other_hm_source_layout.png")


def build_bedding_angle(mesh: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.3, 6.6))
    plot_mesh(ax, mesh, "Bedding-informed tensor orientation")

    angle_deg = 144.0
    angle = np.deg2rad(angle_deg)
    center = np.array([0.0, 0.0])
    length = 2.4
    vec = np.array([np.cos(angle), np.sin(angle)])
    perp = np.array([-np.sin(angle), np.cos(angle)])

    ax.plot([center[0] - length * vec[0], center[0] + length * vec[0]],
            [center[1] - length * vec[1], center[1] + length * vec[1]],
            color="#b2182b", linewidth=2.4, label=r"$K_\parallel$ / bedding angle 144 deg")
    ax.annotate("", xy=center + length * vec, xytext=center,
                arrowprops=dict(arrowstyle="-|>", color="#b2182b", linewidth=2.4))
    ax.plot([center[0] - 1.2 * perp[0], center[0] + 1.2 * perp[0]],
            [center[1] - 1.2 * perp[1], center[1] + 1.2 * perp[1]],
            color="#2171b5", linewidth=1.8, linestyle="--", label=r"$K_\perp$")

    arc_theta = np.linspace(0, angle, 90)
    radius = 0.75
    ax.plot(center[0] + radius * np.cos(arc_theta),
            center[1] + radius * np.sin(arc_theta),
            color="#333333", linewidth=1.0)
    ax.text(center[0] - 0.18, center[1] + 0.82, "144 deg", fontsize=9,
            ha="right", va="center")
    ax.text(center[0] + length * vec[0], center[1] + length * vec[1],
            "bedding / fixed tensor angle", color="#b2182b", fontsize=8,
            ha="right", va="bottom")
    ax.text(0.03, 0.04,
            "Structural prior only: this angle fixes the current permeability tensor orientation;\n"
            "it is not a measured residual and has no time dimension.",
            transform=ax.transAxes, fontsize=8, ha="left", va="bottom",
            bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#777777", alpha=0.92))
    ax.legend(fontsize=8, loc="upper right")
    save(fig, "bedding_angle_on_mesh.png")


def build_ert_split(mesh: pd.DataFrame, ert: pd.DataFrame, timesteps: pd.DataFrame) -> None:
    inside = ert[ert["inside_ogs_cell"].astype(bool)]
    support = inside[inside["within_approx_1p5m_center_support"].astype(bool)]
    ert_mesh = load_reference_ert_mesh(ert)
    selected = select_ert_near_niche_cells(ert, count=10)

    fig, ax = plt.subplots(figsize=(8.3, 6.7))
    plot_mesh(ax, mesh, "ERT placement on current OGS mesh")
    add_ert_wire(ax, ert_mesh, ert_cell_ids(inside), color="#9ecae1", alpha=0.28,
                 linewidth=0.20, label="ERT triangular cells inside OGS mesh")
    add_ert_nodes(ax, ert_mesh, ert_cell_ids(inside), color="#6baed6", alpha=0.18,
                  size=0.55, label="ERT mesh nodes")
    add_ert_nodes(ax, ert_mesh, ert_cell_ids(support), color="#08519c", alpha=0.70,
                  size=1.8, label="approx. 1.5 m support nodes")
    ax.legend(fontsize=8, loc="upper right")
    save(fig, "ert_mesh_placement.png")

    fig, axes = plt.subplots(2, 1, figsize=(8.6, 8.4), gridspec_kw={"height_ratios": [2.7, 1.9]})
    sc = add_ert_colored_cells(axes[0], ert_mesh, ert, ert_cell_ids(inside))
    add_ert_nodes(axes[0], ert_mesh, ert_cell_ids(inside), color="black", alpha=0.10, size=0.28)
    colors = plt.get_cmap("tab10").colors
    if not selected.empty:
        for idx, (_, row) in enumerate(selected.iterrows()):
            color = colors[idx % len(colors)]
            axes[0].scatter(row["model_x"], row["model_y"], s=44, color=color,
                            edgecolor="white", linewidth=0.7, zorder=6)
            axes[0].text(row["model_x"], row["model_y"], row["sample_label"],
                         fontsize=7.2, weight="bold", color="black",
                         ha="center", va="center", zorder=7)
    axes[0].set_aspect("equal", adjustable="box")
    axes[0].set_title("ERT projected triangular mesh and near-niche time-series cells")
    axes[0].set_xlabel("model x [m]")
    axes[0].set_ylabel("model y [m]")
    axes[0].grid(alpha=0.18, linewidth=0.4)
    fig.colorbar(sc, ax=axes[0], label="log10 resistivity [ohm m]")

    if selected.empty:
        axes[1].text(0.5, 0.5, "No near-niche ERT cells available", transform=axes[1].transAxes,
                     ha="center", va="center")
    else:
        selected_cell_ids = selected["ert_cell_id"].astype(int).to_numpy()
        series = build_ert_near_niche_timeseries(timesteps, selected_cell_ids)
        for idx, (_, row) in enumerate(selected.iterrows()):
            cell_id = int(row["ert_cell_id"])
            if cell_id not in series.columns:
                continue
            axes[1].plot(series["timestamp_iso"], series[cell_id], linewidth=0.85,
                         color=colors[idx % len(colors)], alpha=0.92,
                         label=str(row["sample_label"]))
        axes[1].legend(fontsize=6.8, ncol=5, loc="upper right", frameon=True)
    axes[1].set_title("ERT log10-resistivity time series at selected near-niche cells")
    axes[1].set_ylabel("log10 resistivity [ohm m]")
    axes[1].set_xlabel("date")
    style_time_axis(axes[1])
    save(fig, "ert_data_visualisation.png")


def build_nmr_split(mesh: pd.DataFrame, boreholes: pd.DataFrame, weekly: pd.DataFrame, seasonal: pd.DataFrame) -> None:
    nmr = boreholes[boreholes["group"].eq("NMR")]

    fig, ax = plt.subplots(figsize=(8.3, 6.7))
    plot_mesh(ax, mesh, "NMR placement on current OGS mesh")
    ax.scatter(nmr["lookup_x"], nmr["lookup_y"], s=52, color="#2a7f62",
               edgecolor="white", linewidth=0.4, zorder=5)
    label_df = nmr.copy()
    label_df["short_label"] = label_df["label"].str.replace("NMR_", "", regex=False)
    annotate_points(ax, label_df, x="lookup_x", y="lookup_y", label="short_label", fontsize=6.4)
    save(fig, "nmr_mesh_placement.png")

    wk = weekly.copy()
    wk["date_iso"] = pd.to_datetime(wk["date_iso"], errors="coerce")
    sea = seasonal.copy()
    sea["campaign_date"] = pd.to_datetime(sea["campaign_date"], errors="coerce")

    fig, axes = plt.subplots(2, 1, figsize=(8.4, 8.0), gridspec_kw={"height_ratios": [1.35, 1.0]})
    for station, group in wk.dropna(subset=["date_iso"]).groupby("station"):
        axes[0].plot(group["date_iso"], group["water_content_vol_percent"],
                     marker=".", linewidth=1.0, label=station)
    axes[0].set_title("NMR weekly water-content time series")
    axes[0].set_ylabel("water content [vol.%]")
    axes[0].set_xlabel("date")
    axes[0].legend(fontsize=8)
    style_time_axis(axes[0])

    sea4 = sea[sea["niche"].eq("Niche 4")].dropna(subset=["campaign_date"])
    if not sea4.empty:
        latest_date = sea4["campaign_date"].max()
        latest = sea4[sea4["campaign_date"].eq(latest_date)].copy().sort_values("position")
        axes[1].errorbar(latest["position"], latest["water_content_vol_percent"],
                         yerr=latest["wc_ci95_vol_percent"], fmt="o", color="#238b45",
                         ecolor="#74c476", capsize=2.5)
        axes[1].set_title(f"NMR latest Niche 4 seasonal profile ({latest_date.date()})")
        axes[1].tick_params(axis="x", rotation=65, labelsize=7)
    axes[1].set_ylabel("water content [vol.%]")
    axes[1].set_xlabel("position")
    axes[1].grid(axis="y", alpha=0.25)
    save(fig, "nmr_data_visualisation.png")


def build_permeability_split(mesh: pd.DataFrame, lines: pd.DataFrame, cells: pd.DataFrame,
                             targets: pd.DataFrame, mesh_cells: pd.DataFrame) -> None:
    char_lines = {k: v for k, v in line_segments(lines).items() if v["group"].iloc[0] == "Charac. Bohrungen"}
    merged = cells.merge(mesh_cells[["cell_id", "centroid_x", "centroid_y"]],
                         left_on="lookup_cell_id", right_on="cell_id", how="left")
    active = merged[merged["usable_for_current_ogs_fit"].astype(str).eq("True")]

    fig, ax = plt.subplots(figsize=(8.3, 6.7))
    plot_mesh(ax, mesh, "Permeability pulse-test placement on current OGS mesh")
    for seg, group in char_lines.items():
        ax.plot(group["lookup_x"], group["lookup_y"], linewidth=1.6, alpha=0.8, label=seg)
        annotate_end(ax, group, seg)
    sc = ax.scatter(active["centroid_x"], active["centroid_y"], c=active["log10_permeability_m2"],
                    s=44, cmap="magma", edgecolor="white", linewidth=0.3, zorder=4)
    fig.colorbar(sc, ax=ax, label="observed log10 k [m2]")
    ax.legend(fontsize=6.8, loc="upper right")
    save(fig, "permeability_mesh_placement.png")

    if "positive_permeability" in targets.columns:
        t = targets[targets["positive_permeability"].astype(str).eq("True")].copy()
    else:
        t = targets[targets["permeability_m2"].gt(0)].copy()

    open_t = t[t["twin"].eq("open")].copy()
    xmin = max(0.0, float(open_t["borehole_depth_m"].min()) - 0.10)
    xmax = float(open_t["borehole_depth_m"].max()) + 0.15
    ymin = np.floor(float(open_t["log10_permeability_m2"].min()) - 0.25)
    ymax = np.ceil(float(open_t["log10_permeability_m2"].max()) + 0.25)
    segment_colors = {
        "BCD-A32": "#1b9e77",
        "BCD-A33": "#d95f02",
        "BFM-D19": "#7570b3",
    }

    def style_depth_axis(ax: plt.Axes) -> None:
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_xlabel("borehole depth [m]")
        ax.set_ylabel("log10 permeability [m2]")
        ax.grid(alpha=0.25)

    def panel_note(ax: plt.Axes, text: str) -> None:
        ax.text(0.03, 0.04, text, transform=ax.transAxes, ha="left", va="bottom",
                fontsize=7.2, bbox=dict(boxstyle="round,pad=0.25", fc="white",
                                        ec="#777777", alpha=0.92))

    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.8), sharex=True, sharey=True)
    campaign_specs = [
        (2021, "2021 open-twin context"),
        (2024, "2024 open-twin active support"),
    ]
    for ax, (year, title) in zip(axes, campaign_specs):
        sub = open_t[open_t["campaign_year"].eq(year)]
        for seg, group in sub.groupby("normalized_segment_label"):
            color = segment_colors.get(seg, "#555555")
            active_rows = group[group["usable_for_current_ogs_fit"].astype(bool)]
            inactive_rows = group[~group["usable_for_current_ogs_fit"].astype(bool)]
            if not active_rows.empty:
                ax.scatter(active_rows["borehole_depth_m"], active_rows["log10_permeability_m2"],
                           s=28, color=color, edgecolor="white", linewidth=0.25,
                           alpha=0.88, label=f"{seg} active")
            if not inactive_rows.empty:
                ax.scatter(inactive_rows["borehole_depth_m"], inactive_rows["log10_permeability_m2"],
                           s=34, facecolor="none", edgecolor=color, linewidth=1.1,
                           alpha=0.92, label=f"{seg} inactive")
        nonpositive = targets[
            targets["twin"].eq("open")
            & targets["campaign_year"].eq(year)
            & ~targets["permeability_m2"].gt(0)
        ]
        plotted = int(len(sub))
        active_count = int(sub["usable_for_current_ogs_fit"].astype(bool).sum())
        note = f"positive plotted: {plotted}\nactive in current fit: {active_count}"
        if len(nonpositive):
            note += f"\nnonpositive/missing omitted: {len(nonpositive)}"
        panel_note(ax, note)
        ax.set_title(title)
        style_depth_axis(ax)
        ax.legend(fontsize=6.3, loc="upper left")
    save(fig, "permeability_open_twin_by_campaign.png")

    active_open = open_t[open_t["usable_for_current_ogs_fit"].astype(bool)].copy()
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.8), sharex=True, sharey=True)
    sheet_styles = {
        "2024_OT": ("o", "#1f78b4", "April 2024 workbook"),
        "2024": ("^", "#e31a1c", "2024 horiz./vert. sheet"),
    }
    for ax, seg in zip(axes, ["BCD-A32", "BCD-A33"]):
        sub = active_open[active_open["normalized_segment_label"].eq(seg)]
        for sheet, group in sub.groupby("source_sheet"):
            marker, color, label = sheet_styles.get(str(sheet), ("s", "#555555", str(sheet)))
            ax.scatter(group["borehole_depth_m"], group["log10_permeability_m2"],
                       s=30, marker=marker, color=color, edgecolor="white",
                       linewidth=0.25, alpha=0.86, label=label)
        direction = ", ".join(sorted(sub["direction_inferred_from_label"].dropna().astype(str).unique()))
        panel_note(ax, f"{seg}\nactive rows: {len(sub)}\ndirection: {direction}")
        ax.set_title(f"{seg} active open-twin rows")
        style_depth_axis(ax)
        ax.legend(fontsize=6.3, loc="upper left")
    save(fig, "permeability_active_open_by_borehole.png")


def build_taupe_split(mesh: pd.DataFrame, lines: pd.DataFrame, taupe: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.3, 6.7))
    plot_mesh(ax, mesh, "Taupe/TDR placement on current OGS mesh")
    for seg, group in line_segments(lines).items():
        if group["group"].iloc[0] != "Taupe":
            continue
        ax.plot(group["lookup_x"], group["lookup_y"], color="#d95f0e", linewidth=1.8, alpha=0.86)
        annotate_end(ax, group, seg, color="#d95f0e")
    save(fig, "taupe_mesh_placement.png")

    tp = taupe.copy()
    tp["date_iso"] = pd.to_datetime(tp["date_iso"], errors="coerce")

    fig, axes = plt.subplots(2, 1, figsize=(8.4, 8.0), gridspec_kw={"height_ratios": [1.35, 1.0]})
    subset = tp[tp["sensor"].isin(["A3", "A4"]) & tp["edz_band_cm"].isin(["0-50", "0-10", "40-50"])].dropna(subset=["date_iso"])
    for (sensor, band), group in subset.groupby(["sensor", "edz_band_cm"]):
        axes[0].plot(group["date_iso"], group["taupe_value"], linewidth=0.95, label=f"{sensor} {band}")
    axes[0].set_title("Taupe/TDR workbook values through time")
    axes[0].set_ylabel("workbook value [unit pending]")
    axes[0].set_xlabel("date")
    axes[0].legend(fontsize=6.8, ncol=2)
    style_time_axis(axes[0])

    latest_date = tp["date_iso"].max()
    latest = tp[tp["date_iso"].eq(latest_date) & tp["sensor"].isin(["A3", "A4"])].copy()
    latest = latest.sort_values(["sensor", "edz_min_cm"])
    for sensor, group in latest.groupby("sensor"):
        axes[1].plot(group["edz_min_cm"], group["taupe_value"], marker="o", linewidth=1.2, label=sensor)
    axes[1].set_title(f"Latest A3/A4 EDZ-band profile ({latest_date.date()})")
    axes[1].set_xlabel("EDZ band lower edge [cm]")
    axes[1].set_ylabel("workbook value [unit pending]")
    axes[1].legend(fontsize=8)
    axes[1].grid(alpha=0.25)
    save(fig, "taupe_data_visualisation.png")


def build_rh_split(mesh: pd.DataFrame, lookup: pd.DataFrame, rh: pd.DataFrame) -> None:
    su = lookup[lookup["measurement_type"].eq("Suction")].copy()

    fig, ax = plt.subplots(figsize=(8.3, 6.7))
    plot_mesh(ax, mesh, "RH/suction placement on current OGS mesh")
    ax.scatter(su["lookup_x"], su["lookup_y"], s=58, marker="^", color="#8856a7",
               edgecolor="white", linewidth=0.4, zorder=5)
    su["label"] = [f"RH/S{i}" for i in range(1, len(su) + 1)]
    annotate_points(ax, su, x="lookup_x", y="lookup_y", label="label", fontsize=6.4)
    save(fig, "rh_mesh_placement.png")

    rr = rh.copy()
    rr["date_iso"] = pd.to_datetime(rr["date_iso"], errors="coerce")
    rr = rr.dropna(subset=["date_iso"])
    rr, removed_count = filter_rh_plot_rows(rr)

    fig, axes = plt.subplots(2, 1, figsize=(8.4, 8.0), sharex=True)
    for sensor, group in rr.groupby("sensor"):
        axes[0].plot(group["date_iso"], group["rh_percent"], linewidth=0.9, label=sensor)
    axes[0].axhline(95, color="black", linestyle="--", linewidth=0.8, alpha=0.65)
    axes[0].set_title("RH workbook time series")
    axes[0].set_ylabel("relative humidity [%]")
    axes[0].legend(fontsize=8)
    axes[0].grid(alpha=0.25)
    axes[0].text(
        0.02, 0.04,
        f"{removed_count} RH7/RH8 rows from the\nFeb--Mar 2022 dropout omitted",
        transform=axes[0].transAxes,
        ha="left",
        va="bottom",
        fontsize=7.2,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#777777", alpha=0.92),
    )

    for sensor, group in rr.groupby("sensor"):
        axes[1].plot(group["date_iso"], group["liquid_pressure_gauge_pa_kelvin"] / 1e6,
                     linewidth=0.9, label=sensor)
    axes[1].set_title("Kelvin liquid-pressure conversion")
    axes[1].set_ylabel("gauge liquid pressure [MPa]")
    axes[1].set_xlabel("date")
    style_time_axis(axes[1])
    save(fig, "rh_data_visualisation.png")


def build_other_hm_split() -> None:
    zones = read_csv("other_hm_visualisation_zones.csv")
    lev = read_csv("other_hm_levelling_displacements.csv")

    hm_specs = [
        ("hm_mini_piezometer_positions.png", ["mini_piezometer"], "Mini-piezometer source support"),
        ("hm_extensometer_positions.png", ["extensometer"], "Extensometer source supports"),
        ("hm_laser_scan_positions.png", ["laser_scan_surface", "laser_scan_geodetic_support"],
         "Laser-scan surfaces and geodetic supports"),
        ("hm_miniprisma_positions.png", ["miniprisma_geodesy"], "Miniprisma geodetic positions"),
        ("hm_convergence_positions.png", ["convergence_points"], "Niche convergence-point supports"),
        ("hm_evapometer_position.png", ["evapometer"], "Evapometer support"),
    ]
    for filename, types, title in hm_specs:
        sub = zones[zones["measurement_type"].isin(types)].copy()
        fig, ax = plt.subplots(figsize=(8.2, 5.5))
        plot_hm_zone_map(ax, sub, title)
        save(fig, filename)

    cracks = zones[zones["measurement_type"].eq("fracture_or_crack_geometry")].copy()
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 5.0), gridspec_kw={"width_ratios": [1.1, 1.0]})
    plot_hm_zone_map(axes[0], cracks.head(1), "Crack/fracture source extent")
    axes[0].text(0.04, 0.05,
                 "Kluft_0--Kluft_21 share the same exported source-frame extent;\n"
                 "separate hard residual positions require the Geoscope crackmeter export.",
                 transform=axes[0].transAxes, ha="left", va="bottom", fontsize=7.5,
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#777777", alpha=0.92))
    crack_counts = cracks.sort_values("zone_name")
    axes[1].barh(crack_counts["zone_name"], crack_counts["elements"], color="#de2d26")
    axes[1].set_title("Individual Kluft zones in source file")
    axes[1].set_xlabel("source elements")
    axes[1].tick_params(axis="y", labelsize=6)
    axes[1].grid(axis="x", alpha=0.25)
    save(fig, "hm_crackmeter_positions.png")

    lev = lev.copy()
    lev["point_label"] = lev["point_name"].astype(str) + "\n" + lev["location"].astype(str)
    fig, ax = plt.subplots(figsize=(8.8, 4.9))
    colors = np.where(lev["height_difference_mm"] >= 0, "#3182bd", "#de2d26")
    ax.bar(np.arange(len(lev)), lev["height_difference_mm"], color=colors)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(np.arange(len(lev)))
    ax.set_xticklabels(lev["point_label"], rotation=65, ha="right", fontsize=7)
    ax.set_ylabel("height difference [mm]")
    ax.set_title("Precision-levelling slide-summary values")
    ax.grid(axis="y", alpha=0.25)
    save(fig, "hm_levelling_values.png")


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    mesh = read_csv("ogs_bulk_mesh_cells.csv")
    lookup = read_csv("measurement_mesh_lookup.csv")
    boreholes = read_csv("borehole_mesh_lookup.csv")
    lines = read_csv("borehole_line_mesh_samples.csv")
    ert = read_csv("ert_spatial_projection_lookup.csv")

    build_boundary_conditions_domain(mesh)
    build_all_locations(mesh, lookup, lines, ert)
    build_ert(mesh, ert, read_csv("ert_timesteps.csv"))
    build_nmr(mesh, boreholes, read_csv("nmr_weekly.csv"), read_csv("nmr_seasonal_profiles.csv"))
    build_permeability(mesh, lines, read_csv("permeability_observation_cells.csv"),
                       read_csv("permeability_observation_targets.csv"), mesh)
    build_taupe(mesh, lines, read_csv("taupe_tdr_bands.csv"))
    build_rh(mesh, lookup, read_csv("rh_open_twin_kelvin.csv"))
    build_other_hm(mesh)
    build_bedding_angle(mesh)
    build_ert_split(mesh, ert, read_csv("ert_timesteps.csv"))
    build_nmr_split(mesh, boreholes, read_csv("nmr_weekly.csv"), read_csv("nmr_seasonal_profiles.csv"))
    build_permeability_split(mesh, lines, read_csv("permeability_observation_cells.csv"),
                             read_csv("permeability_observation_targets.csv"), mesh)
    build_taupe_split(mesh, lines, read_csv("taupe_tdr_bands.csv"))
    build_rh_split(mesh, lookup, read_csv("rh_open_twin_kelvin.csv"))
    build_other_hm_split()


if __name__ == "__main__":
    main()
