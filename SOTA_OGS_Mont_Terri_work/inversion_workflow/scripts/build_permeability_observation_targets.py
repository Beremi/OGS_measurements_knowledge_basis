#!/usr/bin/env python3
"""Build model-facing permeability pulse-test observation targets."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_INTERVAL_LENGTH_M = 0.10
CHARACTERIZATION_SOURCE = (
    "cda_knowledge_base/measurements/permeability_pulse_tests/source_files/"
    "2025-09-05_Ziefle_et_al_2023_Characterization.pdf"
)

KNOWN_UNMAPPED_SEGMENT_EVIDENCE = {
    "BCD-A24": {
        "direction": "vertical",
        "source_file": CHARACTERIZATION_SOURCE,
        "source_locator": "Section 4.3 / PDF text around p. 7",
        "evidence_note": "Boreholes BCD-A24 and BCD-A26 are reported as vertical pulse-test boreholes.",
    },
    "BCD-A25": {
        "direction": "horizontal",
        "source_file": CHARACTERIZATION_SOURCE,
        "source_locator": "Section 4.3 / PDF text around p. 7",
        "evidence_note": "Boreholes BCD-A25 and BCD-A27 are reported as horizontal pulse-test boreholes.",
    },
    "BCD-A26": {
        "direction": "vertical",
        "source_file": CHARACTERIZATION_SOURCE,
        "source_locator": "Section 4.3 / PDF text around p. 7",
        "evidence_note": "Boreholes BCD-A24 and BCD-A26 are reported as vertical pulse-test boreholes.",
    },
    "BCD-A27": {
        "direction": "horizontal",
        "source_file": CHARACTERIZATION_SOURCE,
        "source_locator": "Section 4.3 / PDF text around p. 7",
        "evidence_note": "Boreholes BCD-A25 and BCD-A27 are reported as horizontal pulse-test boreholes.",
    },
    "BFM-D19": {
        "direction": "nearly horizontal",
        "source_file": CHARACTERIZATION_SOURCE,
        "source_locator": "Section 4.3 / PDF text around p. 7",
        "evidence_note": "Borehole BFM-D19 is reported as nearly horizontal and measured by evapometer, not the COMDRILL pulse-test system.",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
    )
    parser.add_argument(
        "--interval-length",
        type=float,
        default=DEFAULT_INTERVAL_LENGTH_M,
        help="Pulse-test interval length in metres; used for along-borehole cell selection.",
    )
    return parser.parse_args()


def clean_token(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value).strip()


def normalize_segment_label(block_label: Any) -> str:
    text = clean_token(block_label)
    match = re.search(r"B[C]?D[A_-]?A[_-]?(\d+)", text, re.IGNORECASE)
    if not match:
        if re.search(r"BFM[-_ ]?D[-_ ]?19", text, re.IGNORECASE):
            return "BFM-D19"
        return ""
    return f"BCD-A{match.group(1)}"


def known_segment_evidence(segment_label: str) -> dict[str, str]:
    return KNOWN_UNMAPPED_SEGMENT_EVIDENCE.get(segment_label, {})


def status_rank(status: str) -> int:
    ranks = {
        "inside_cell": 0,
        "inside_mesh_bbox_nearest_cell": 1,
        "outside_mesh_bbox_nearest_cell": 2,
    }
    return ranks.get(status, 3)


def segment_geometry(line_samples: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for segment_label, group in line_samples.groupby("segment_label"):
        ordered = group.sort_values("sample_fraction")
        first = ordered.iloc[0]
        last = ordered.iloc[-1]
        dx = float(last["lookup_x"]) - float(first["lookup_x"])
        dy = float(last["lookup_y"]) - float(first["lookup_y"])
        length = float(first["segment_length_2d_m"])
        tangent_norm = math.hypot(dx, dy)
        rows.append(
            {
                "segment_label": segment_label,
                "segment_group": first["group"],
                "start_label": first["start_label"],
                "end_label": first["end_label"],
                "segment_length_2d_m": length,
                "tangent_x": dx / tangent_norm if tangent_norm else math.nan,
                "tangent_y": dy / tangent_norm if tangent_norm else math.nan,
                "sample_count": int(ordered.shape[0]),
                "inside_cell_samples": int((ordered["lookup_status"] == "inside_cell").sum()),
                "fallback_samples": int((ordered["lookup_status"] == "inside_mesh_bbox_nearest_cell").sum()),
                "outside_samples": int((ordered["lookup_status"] == "outside_mesh_bbox_nearest_cell").sum()),
            }
        )
    return pd.DataFrame(rows)


def selected_samples_for_interval(
    samples: pd.DataFrame,
    depth_m: float,
    interval_length_m: float,
) -> tuple[pd.DataFrame, str]:
    half_length = interval_length_m / 2.0
    window = samples[
        (samples["distance_along_segment_m"] >= depth_m - half_length)
        & (samples["distance_along_segment_m"] <= depth_m + half_length)
    ].copy()
    if not window.empty:
        return window, "interval_window"
    nearest_idx = (samples["distance_along_segment_m"] - depth_m).abs().idxmin()
    return samples.loc[[nearest_idx]].copy(), "nearest_sample_fallback"


def summarize_samples(samples: pd.DataFrame) -> dict[str, Any]:
    statuses = samples["lookup_status"].astype(str).tolist()
    best = min(statuses, key=status_rank)
    worst = max(statuses, key=status_rank)
    all_inside = all(status == "inside_cell" for status in statuses)
    all_outside = all(status == "outside_mesh_bbox_nearest_cell" for status in statuses)
    if all_inside:
        target_status = "mapped_inside_mesh"
    elif all_outside:
        target_status = "mapped_outside_mesh"
    else:
        target_status = "mapped_with_fallback_or_partial_outside"
    cell_ids = [int(value) for value in samples["lookup_cell_id"].tolist()]
    material_ids = [int(value) for value in samples["lookup_material_id"].tolist()]
    unique_cell_ids = sorted(set(cell_ids))
    unique_material_ids = sorted(set(material_ids))
    return {
        "target_status": target_status,
        "best_lookup_status": best,
        "worst_lookup_status": worst,
        "selected_sample_count": int(samples.shape[0]),
        "inside_cell_sample_count": int((samples["lookup_status"] == "inside_cell").sum()),
        "fallback_sample_count": int((samples["lookup_status"] == "inside_mesh_bbox_nearest_cell").sum()),
        "outside_sample_count": int((samples["lookup_status"] == "outside_mesh_bbox_nearest_cell").sum()),
        "selected_cell_ids": ";".join(map(str, unique_cell_ids)),
        "selected_material_ids": ";".join(map(str, unique_material_ids)),
        "center_lookup_cell_id": int(samples.iloc[(samples["distance_to_target_abs_m"].argmin())]["lookup_cell_id"]),
        "center_lookup_status": str(samples.iloc[(samples["distance_to_target_abs_m"].argmin())]["lookup_status"]),
    }


def fit_recommendation(target_status: str) -> tuple[bool, str]:
    if target_status == "mapped_inside_mesh":
        return True, "use_as_initial_direct_log_permeability_constraint"
    if target_status == "mapped_with_fallback_or_partial_outside":
        return False, "review_before_use_contains_fallback_or_partial_outside_samples"
    if target_status == "mapped_outside_mesh":
        return False, "exclude_from_current_local_ogs_fit_outside_mesh"
    if target_status == "missing_segment_geometry":
        return False, "exclude_until_borehole_geometry_is_available"
    if target_status == "not_usable_missing_or_nonpositive_permeability":
        return False, "exclude_missing_or_nonpositive_interpreted_value"
    if target_status == "missing_borehole_depth":
        return False, "exclude_until_borehole_depth_is_available"
    if target_status == "interval_exceeds_segment_extent":
        return False, "review_before_use_interval_extends_beyond_segment_geometry"
    return False, "review_before_use"


def build_targets(processed_dir: Path, interval_length_m: float) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    permeability = pd.read_csv(processed_dir / "permeability_interpreted_values.csv")
    line_samples = pd.read_csv(processed_dir / "borehole_line_mesh_samples.csv")
    geometry = segment_geometry(line_samples)
    geometry_by_segment = {row["segment_label"]: row for _, row in geometry.iterrows()}
    samples_by_segment = {
        segment_label: group.sort_values("distance_along_segment_m").copy()
        for segment_label, group in line_samples.groupby("segment_label")
    }

    targets: list[dict[str, Any]] = []
    target_cells: list[dict[str, Any]] = []
    for observation_index, row in permeability.reset_index(drop=True).iterrows():
        observation_id = f"perm_{observation_index:04d}"
        block_label = clean_token(row.get("block_label"))
        segment_label = normalize_segment_label(block_label)
        segment_evidence = known_segment_evidence(segment_label)
        direction_inferred = clean_token(row.get("direction_inferred")) or segment_evidence.get("direction", "")
        permeability_m2 = float(row["permeability_m2"]) if pd.notna(row.get("permeability_m2")) else math.nan
        depth_m = float(row["borehole_depth_m"]) if pd.notna(row.get("borehole_depth_m")) else math.nan
        base: dict[str, Any] = {
            "observation_id": observation_id,
            "source_file": row.get("source_file", ""),
            "source_sheet": row.get("source_sheet", ""),
            "source_row_1based": row.get("source_row_1based", ""),
            "campaign_year": row.get("campaign_year", ""),
            "campaign_note": row.get("campaign_note", ""),
            "block_label": block_label,
            "normalized_segment_label": segment_label,
            "twin": row.get("twin", ""),
            "direction_inferred_from_label": direction_inferred,
            "borehole_depth_m": depth_m,
            "interval_length_m": interval_length_m,
            "permeability_m2": permeability_m2,
            "transmissibility_m3": row.get("transmissibility_m3", math.nan),
            "log10_permeability_m2": math.log10(permeability_m2) if permeability_m2 > 0 else math.nan,
            "geometry_evidence_status": "orientation_only_endpoint_geometry_missing" if segment_evidence else "",
            "geometry_evidence_source_file": segment_evidence.get("source_file", ""),
            "geometry_evidence_locator": segment_evidence.get("source_locator", ""),
            "geometry_evidence_note": segment_evidence.get("evidence_note", ""),
            "measurement_semantics": (
                "gas pulse-test interpreted scalar permeability/transmissibility; "
                "treated as a noisy interval-scale constraint on intrinsic permeability, "
                "not as a cell-wise tensor component"
            ),
        }

        if not (permeability_m2 > 0):
            usable, recommendation = fit_recommendation("not_usable_missing_or_nonpositive_permeability")
            targets.append(
                {
                    **base,
                    "target_status": "not_usable_missing_or_nonpositive_permeability",
                    "usable_for_current_ogs_fit": usable,
                    "fit_use_recommendation": recommendation,
                    "target_gap": "The interpreted permeability value is missing, zero, or non-positive.",
                }
            )
            continue
        if not segment_label or segment_label not in samples_by_segment:
            usable, recommendation = fit_recommendation("missing_segment_geometry")
            target_gap = "No matching borehole endpoint geometry exists in borehole_line_mesh_samples.csv."
            if segment_evidence:
                target_gap = (
                    "Orientation evidence is available, but no labelled borehole endpoints exist in "
                    "borehole_line_mesh_samples.csv, so the interval cannot be projected to OGS cells."
                )
            targets.append(
                {
                    **base,
                    "target_status": "missing_segment_geometry",
                    "usable_for_current_ogs_fit": usable,
                    "fit_use_recommendation": recommendation,
                    "target_gap": target_gap,
                }
            )
            continue
        if not math.isfinite(depth_m):
            usable, recommendation = fit_recommendation("missing_borehole_depth")
            targets.append(
                {
                    **base,
                    "target_status": "missing_borehole_depth",
                    "usable_for_current_ogs_fit": usable,
                    "fit_use_recommendation": recommendation,
                    "target_gap": "The interpreted row has no usable borehole depth.",
                }
            )
            continue

        samples = samples_by_segment[segment_label]
        geom = geometry_by_segment[segment_label]
        segment_length = float(geom["segment_length_2d_m"])
        selected, selection_method = selected_samples_for_interval(samples, depth_m, interval_length_m)
        selected["distance_to_target_abs_m"] = (selected["distance_along_segment_m"] - depth_m).abs()
        sample_summary = summarize_samples(selected)
        interval_exceeds_segment = bool(depth_m - interval_length_m / 2.0 < 0 or depth_m + interval_length_m / 2.0 > segment_length)
        target_status = sample_summary["target_status"]
        target_gap = ""
        if interval_exceeds_segment:
            target_status = "interval_exceeds_segment_extent"
            target_gap = "The nominal 10 cm interval extends beyond the available borehole segment geometry."
        usable, recommendation = fit_recommendation(target_status)

        target = {
            **base,
            "geometry_evidence_status": "endpoint_geometry_available_from_borehole_line_samples",
            "geometry_evidence_source_file": "inversion_workflow/processed_observations/borehole_line_mesh_samples.csv",
            "geometry_evidence_locator": str(geom["segment_label"]),
            "geometry_evidence_note": "Labelled start/end coordinates and OGS line samples are available for this segment.",
            "target_status": target_status,
            "usable_for_current_ogs_fit": usable,
            "fit_use_recommendation": recommendation,
            "target_gap": target_gap,
            "segment_group": geom["segment_group"],
            "segment_start_label": geom["start_label"],
            "segment_end_label": geom["end_label"],
            "segment_length_2d_m": segment_length,
            "segment_tangent_x": geom["tangent_x"],
            "segment_tangent_y": geom["tangent_y"],
            "selection_method": selection_method,
            **sample_summary,
        }
        targets.append(target)

        grouped_cells = (
            selected.groupby(["lookup_cell_id", "lookup_material_id", "lookup_status"], dropna=False)
            .size()
            .reset_index(name="sample_count_in_cell")
        )
        total_selected = float(selected.shape[0])
        for _, cell_row in grouped_cells.iterrows():
            target_cells.append(
                {
                    "observation_id": observation_id,
                    "normalized_segment_label": segment_label,
                    "borehole_depth_m": depth_m,
                    "permeability_m2": permeability_m2,
                    "log10_permeability_m2": math.log10(permeability_m2),
                    "lookup_cell_id": int(cell_row["lookup_cell_id"]),
                    "lookup_material_id": int(cell_row["lookup_material_id"]),
                    "lookup_status": cell_row["lookup_status"],
                    "usable_for_current_ogs_fit": usable,
                    "cell_weight": float(cell_row["sample_count_in_cell"]) / total_selected,
                    "sample_count_in_cell": int(cell_row["sample_count_in_cell"]),
                    "measurement_semantics": "cell receives equal selected-sample weight for initial interval-average operator",
                }
            )

    return pd.DataFrame(targets), pd.DataFrame(target_cells), geometry


def build_missing_geometry_audit(targets: pd.DataFrame) -> pd.DataFrame:
    missing = targets[targets["target_status"].eq("missing_segment_geometry")].copy()
    rows: list[dict[str, Any]] = []
    for (segment_label, block_label), group in missing.groupby(
        ["normalized_segment_label", "block_label"], dropna=False
    ):
        directions = sorted(
            {clean_token(value) for value in group["direction_inferred_from_label"] if clean_token(value)}
        )
        twins = sorted({clean_token(value) for value in group["twin"] if clean_token(value)})
        source_files = sorted({clean_token(value) for value in group["source_file"] if clean_token(value)})
        source_sheets = sorted({clean_token(value) for value in group["source_sheet"] if clean_token(value)})
        evidence_statuses = sorted(
            {clean_token(value) for value in group["geometry_evidence_status"] if clean_token(value)}
        )
        evidence_sources = sorted(
            {clean_token(value) for value in group["geometry_evidence_source_file"] if clean_token(value)}
        )
        evidence_locators = sorted(
            {clean_token(value) for value in group["geometry_evidence_locator"] if clean_token(value)}
        )
        rows.append(
            {
                "normalized_segment_label": clean_token(segment_label),
                "block_label": clean_token(block_label),
                "rows": int(group.shape[0]),
                "positive_permeability_rows": int((group["permeability_m2"] > 0).sum()),
                "depth_min_m": float(group["borehole_depth_m"].min()),
                "depth_max_m": float(group["borehole_depth_m"].max()),
                "log10_permeability_min": float(group["log10_permeability_m2"].min()),
                "log10_permeability_max": float(group["log10_permeability_m2"].max()),
                "twin_inferred": ";".join(twins),
                "direction_inferred": ";".join(directions),
                "source_files": ";".join(source_files),
                "source_sheets": ";".join(source_sheets),
                "geometry_evidence_status": ";".join(evidence_statuses) or "endpoint_geometry_missing",
                "geometry_evidence_source_file": ";".join(evidence_sources),
                "geometry_evidence_locator": ";".join(evidence_locators),
                "audit_conclusion": (
                    "Do not use in current OGS cell objective until labelled start/end geometry "
                    "or an accepted digitized borehole trace is available."
                ),
            }
        )
    return pd.DataFrame(rows)


def write_missing_geometry_markdown(path: Path, audit: pd.DataFrame) -> None:
    orientation_rows = 0
    if not audit.empty:
        orientation_rows = int(audit["geometry_evidence_status"].astype(str).str.contains("orientation_only").sum())
    lines = [
        "# Permeability Missing Geometry Audit",
        "",
        "This audit keeps interpreted permeability rows that cannot yet be projected",
        "onto the local OGS mesh visible, without converting them into unsupported cell",
        "targets.",
        "",
        f"- Missing-geometry groups: {audit.shape[0]}",
        f"- Missing-geometry interpreted rows: {int(audit['rows'].sum()) if not audit.empty else 0}",
        f"- Groups with source-backed orientation only: {orientation_rows}",
        "",
        "| Segment | Block label | Rows | Depth range [m] | Direction evidence | Geometry status |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for _, row in audit.sort_values(["normalized_segment_label", "block_label"]).iterrows():
        depth = f"{row['depth_min_m']:.2f}-{row['depth_max_m']:.2f}"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['normalized_segment_label'] or 'unparsed'}`",
                    str(row["block_label"]).replace("|", "/"),
                    str(int(row["rows"])),
                    depth,
                    str(row["direction_inferred"] or "not inferred").replace("|", "/"),
                    str(row["geometry_evidence_status"]).replace("|", "/"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Source Evidence",
            "",
            "- The characterization paper states that BCD-A24 and BCD-A26 are vertical,",
            "  BCD-A25 and BCD-A27 are horizontal, and BFM-D19 is nearly horizontal.",
            "- The current coordinate workbook provides labelled endpoint geometry for",
            "  BCD-A32 to BCD-A35, but not for BCD-A24 to BCD-A27 or BFM-D19.",
            "- `VisualisationCDA.dat` contains permeability layout geometry, but the",
            "  recovered Tecplot zones do not attach unambiguous BCD-A24/25/26/27 or",
            "  BFM-D19 endpoint labels to the points, so they are not used for OGS",
            "  residual mapping.",
            "",
            "## Required To Activate These Rows",
            "",
            "- Labelled start/end coordinates for BCD-A24, BCD-A25, BCD-A26, BCD-A27 and",
            "  BFM-D19 in the same local frame as the OGS mesh, or",
            "- an explicitly approved digitization of Figure 3 / Figure 7 geometry from",
            "  the characterization paper with uncertainty assigned to the projected",
            "  interval locations.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    processed_dir = args.processed_dir.resolve()
    targets, target_cells, geometry = build_targets(processed_dir, args.interval_length)
    missing_geometry_audit = build_missing_geometry_audit(targets)

    targets.to_csv(processed_dir / "permeability_observation_targets.csv", index=False)
    target_cells.to_csv(processed_dir / "permeability_observation_cells.csv", index=False)
    geometry.to_csv(processed_dir / "permeability_segment_geometry.csv", index=False)
    missing_geometry_audit.to_csv(processed_dir / "permeability_missing_geometry_audit.csv", index=False)
    write_missing_geometry_markdown(
        processed_dir / "permeability_missing_geometry_audit.md",
        missing_geometry_audit,
    )

    summary = {
        "processed_dir": str(processed_dir),
        "interval_length_m": args.interval_length,
        "target_rows": int(targets.shape[0]),
        "target_cell_rows": int(target_cells.shape[0]),
        "segment_geometry_rows": int(geometry.shape[0]),
        "target_status": {
            str(key): int(value)
            for key, value in targets["target_status"].value_counts().sort_index().items()
        },
        "mapped_positive_targets": int(targets["target_status"].astype(str).str.startswith("mapped_").sum()),
        "usable_for_current_ogs_fit": int(targets["usable_for_current_ogs_fit"].sum()),
        "missing_segment_geometry": int((targets["target_status"] == "missing_segment_geometry").sum()),
        "missing_geometry_audit_rows": int(missing_geometry_audit.shape[0]),
        "missing_segment_geometry_with_orientation_evidence": int(
            targets["geometry_evidence_status"].eq("orientation_only_endpoint_geometry_missing").sum()
        ),
        "not_usable_missing_or_nonpositive_permeability": int(
            (targets["target_status"] == "not_usable_missing_or_nonpositive_permeability").sum()
        ),
        "notes": [
            "These targets are initial observation-operator inputs, not calibrated likelihoods.",
            "The scalar gas pulse-test value is not treated as a tensor component.",
            "Cell weights are derived from 0.1 m along-borehole samples selected inside the nominal interval window.",
            (
                "Older BCD-A24/25/26/27 and BFM-D19 rows retain source-backed orientation evidence, "
                "but remain excluded until labelled endpoint geometry is available."
            ),
        ],
    }
    (processed_dir / "permeability_target_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print(f"permeability_observation_targets.csv: {targets.shape[0]} rows")
    print(f"permeability_observation_cells.csv: {target_cells.shape[0]} rows")
    print(f"permeability_segment_geometry.csv: {geometry.shape[0]} rows")
    print(f"permeability_missing_geometry_audit.csv: {missing_geometry_audit.shape[0]} rows")
    print(f"target status: {summary['target_status']}")


if __name__ == "__main__":
    main()
