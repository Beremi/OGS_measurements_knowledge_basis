#!/usr/bin/env python3
"""Build a request package for historical permeability endpoint geometry."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REQUESTED_FIELD_SET = (
    "For each borehole/trace: start/collar point x,y,z; end/tip point x,y,z; "
    "coordinate frame; depth-zero reference; positive along-borehole direction; "
    "whether workbook depth is interval centre or interval start; borehole diameter "
    "or packer interval length if it differs from 0.10 m; and coordinate uncertainty."
)

FALLBACK_REQUEST = (
    "If labelled coordinates are unavailable, provide an explicitly approved "
    "digitized trace from the original layout/figure, the source figure/file used, "
    "the digitization transform, and an uncertainty to apply to mapped interval "
    "locations."
)

SOURCE_EVIDENCE = {
    "characterization_pdf": (
        "Ziefle et al. characterization paper, Section 4.3 / PDF text around p. 7: "
        "pulse tests in BCD-A24 to BCD-A27; BCD-A24 and BCD-A26 vertical, "
        "BCD-A25 and BCD-A27 horizontal, and BFM-D19 nearly horizontal; pulse tests "
        "in March 2021 and evapometer measurements in June/July 2020."
    ),
    "workbook_probe": (
        "Permeability_CDA_all_2025.xlsx sheet 2021 contains block labels for "
        "BCDA_24/25/26/27; 2025-09-05_CD-A_Permeability.xlsx sheet "
        "2021_BCDA27_19 contains labels for BCDA_26, BCDA_27 Closed twin, and "
        "BFM-D19 Open twin. These workbook labels are measurement-table headings, "
        "not start/end coordinates."
    ),
    "visualisation_probe": (
        "VisualisationCDA.dat contains generic zones Permeability_bhrg and "
        "Permeability_Meas_points, but the recovered zones do not attach "
        "unambiguous BCD-A24/25/26/27 or BFM-D19 start/end labels to the points."
    ),
    "available_geometry_reference": (
        "The current coordinate/mesh line-sample layer has labelled endpoints for "
        "BCD-A32 to BCD-A35 and Taupe BCD-A3/A4/A7/A8, which proves the expected "
        "format, but not for BCD-A24/25/26/27 or BFM-D19."
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=None,
        help="Optional permeability catalogue derived_files directory to copy outputs into.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(float(value)) else float(value)
    if value is pd.NA or value is None:
        return None
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def unique_join(series: pd.Series) -> str:
    values: list[str] = []
    for value in series.dropna():
        text = str(value).strip()
        if text and text.lower() != "nan" and text not in values:
            values.append(text)
    return "; ".join(values)


def fmt_float(value: Any, digits: int = 4) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if not np.isfinite(number):
        return "n/a"
    return f"{number:.{digits}g}"


def fmt_sci(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if not np.isfinite(number):
        return "n/a"
    return f"{number:.3e}"


def catalogue_dir_from(processed_dir: Path) -> Path:
    resolved = processed_dir.resolve()
    project_root = resolved.parents[2]
    return (
        project_root
        / "cda_knowledge_base"
        / "measurements"
        / "permeability_pulse_tests"
        / "derived_files"
    )


def source_file_paths(processed_dir: Path) -> list[Path]:
    project_root = processed_dir.resolve().parents[2]
    source_dir = project_root / "cda_knowledge_base" / "measurements" / "permeability_pulse_tests" / "source_files"
    return [
        source_dir / "Permeability_CDA_all_2025.xlsx",
        source_dir / "2025-09-05_CD-A_Permeability.xlsx",
        source_dir / "2025-09-05_Ziefle_et_al_2023_Characterization.pdf",
    ]


def requested_labels(segment: str) -> tuple[str, str, str]:
    if segment == "BFM-D19":
        return "BFM-D19 Anfang", "BFM-D19 Ende", "tentative BFM-D19 label convention"
    return f"{segment} Anfang", f"{segment} Ende", "matches existing BCD-Axx Anfang/Ende convention"


def summarize_available_geometry(segment_geometry: pd.DataFrame) -> list[dict[str, Any]]:
    if segment_geometry.empty:
        return []
    columns = [
        "segment_label",
        "segment_group",
        "start_label",
        "end_label",
        "segment_length_2d_m",
        "inside_cell_samples",
        "outside_samples",
    ]
    return segment_geometry[[column for column in columns if column in segment_geometry.columns]].to_dict(
        orient="records"
    )


def build_request_rows(missing: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    if missing.empty:
        return pd.DataFrame()
    blocked = targets[targets["target_status"].astype(str).eq("missing_segment_geometry")].copy()
    blocked["positive_permeability"] = pd.to_numeric(blocked["permeability_m2"], errors="coerce").gt(0)
    rows: list[dict[str, Any]] = []
    for _, missing_row in missing.sort_values("normalized_segment_label").iterrows():
        segment = str(missing_row["normalized_segment_label"])
        group = blocked[blocked["normalized_segment_label"].astype(str).eq(segment)].copy()
        start_label, end_label, label_note = requested_labels(segment)
        source_rows = pd.to_numeric(group.get("source_row_1based"), errors="coerce")
        permeability = pd.to_numeric(group.get("permeability_m2"), errors="coerce")
        log10_perm = pd.to_numeric(group.get("log10_permeability_m2"), errors="coerce")
        depths = pd.to_numeric(group.get("borehole_depth_m"), errors="coerce")
        intervals = pd.to_numeric(group.get("interval_length_m"), errors="coerce")
        positive = group[group["positive_permeability"]]
        rows.append(
            {
                "normalized_segment_label": segment,
                "block_label": missing_row.get("block_label"),
                "request_priority": "high",
                "requested_start_label": start_label,
                "requested_end_label": end_label,
                "requested_label_note": label_note,
                "requested_coordinate_frame": (
                    "same local/model frame used by Coordinates_NMR_Taupe_characborehole.xlsx, "
                    "borehole_line_mesh_samples.csv, and the 2D OGS projection"
                ),
                "requested_fields": REQUESTED_FIELD_SET,
                "fallback_if_coordinates_unavailable": FALLBACK_REQUEST,
                "blocked_rows": int(group.shape[0]),
                "positive_blocked_rows": int(positive.shape[0]),
                "source_files": unique_join(group["source_file"]) if "source_file" in group else missing_row.get("source_files"),
                "source_sheets": unique_join(group["source_sheet"]) if "source_sheet" in group else missing_row.get("source_sheets"),
                "source_row_min_1based": int(source_rows.min()) if source_rows.notna().any() else None,
                "source_row_max_1based": int(source_rows.max()) if source_rows.notna().any() else None,
                "campaign_years": unique_join(group["campaign_year"]) if "campaign_year" in group else "",
                "campaign_notes": unique_join(group["campaign_note"]) if "campaign_note" in group else "",
                "twin_inferred": missing_row.get("twin_inferred"),
                "direction_inferred": missing_row.get("direction_inferred"),
                "depth_min_m": float(depths.min()) if depths.notna().any() else missing_row.get("depth_min_m"),
                "depth_max_m": float(depths.max()) if depths.notna().any() else missing_row.get("depth_max_m"),
                "interval_length_values_m": unique_join(intervals.astype(str)) if intervals.notna().any() else "",
                "permeability_m2_min": float(permeability.min()) if permeability.notna().any() else None,
                "permeability_m2_median": float(permeability.median()) if permeability.notna().any() else None,
                "permeability_m2_max": float(permeability.max()) if permeability.notna().any() else None,
                "log10_permeability_min": float(log10_perm.min()) if log10_perm.notna().any() else missing_row.get("log10_permeability_min"),
                "log10_permeability_median": float(log10_perm.median()) if log10_perm.notna().any() else None,
                "log10_permeability_max": float(log10_perm.max()) if log10_perm.notna().any() else missing_row.get("log10_permeability_max"),
                "geometry_evidence_status": missing_row.get("geometry_evidence_status"),
                "geometry_evidence_source_file": missing_row.get("geometry_evidence_source_file"),
                "geometry_evidence_locator": missing_row.get("geometry_evidence_locator"),
                "current_activation_status": "blocked_missing_labelled_endpoint_geometry",
                "activation_rule": (
                    "Activate only after start/end coordinates or an approved digitized trace allow "
                    "the workbook depth intervals to be sampled on the OGS mesh."
                ),
                "model_impact_if_provided": (
                    "Adds these rows to the same finite-interval log10 intrinsic-permeability "
                    "objective as the active BCD-A32/A33 pulse-test rows, subject to mesh-domain checks."
                ),
                "why_not_inferred_now": (
                    "Orientation is source-backed, but no collected coordinate table maps this label "
                    "to start/end points; generic visualisation zones are not label-resolved enough."
                ),
            }
        )
    return pd.DataFrame(rows)


def build_blocked_rows(targets: pd.DataFrame, request: pd.DataFrame) -> pd.DataFrame:
    blocked = targets[targets["target_status"].astype(str).eq("missing_segment_geometry")].copy()
    if blocked.empty:
        return pd.DataFrame()
    keep_request = [
        "normalized_segment_label",
        "requested_start_label",
        "requested_end_label",
        "requested_coordinate_frame",
        "current_activation_status",
        "activation_rule",
    ]
    merged = blocked.merge(request[keep_request], on="normalized_segment_label", how="left")
    columns = [
        "observation_id",
        "normalized_segment_label",
        "block_label",
        "requested_start_label",
        "requested_end_label",
        "source_file",
        "source_sheet",
        "source_row_1based",
        "campaign_year",
        "campaign_note",
        "twin",
        "direction_inferred_from_label",
        "borehole_depth_m",
        "interval_length_m",
        "permeability_m2",
        "transmissibility_m3",
        "log10_permeability_m2",
        "geometry_evidence_status",
        "geometry_evidence_source_file",
        "geometry_evidence_locator",
        "target_status",
        "usable_for_current_ogs_fit",
        "fit_use_recommendation",
        "requested_coordinate_frame",
        "current_activation_status",
        "activation_rule",
    ]
    return merged[[column for column in columns if column in merged.columns]].sort_values(
        ["normalized_segment_label", "borehole_depth_m", "observation_id"],
        na_position="last",
    )


def build_summary(
    request: pd.DataFrame,
    blocked: pd.DataFrame,
    segment_geometry: pd.DataFrame,
    outputs: dict[str, str],
) -> dict[str, Any]:
    status_counts = (
        blocked["target_status"].fillna("missing").value_counts().sort_index().to_dict()
        if not blocked.empty
        else {}
    )
    direction_counts = (
        request["direction_inferred"].fillna("missing").value_counts().sort_index().to_dict()
        if not request.empty
        else {}
    )
    return {
        "request_segment_count": int(request.shape[0]),
        "blocked_row_count": int(blocked.shape[0]),
        "positive_blocked_row_count": int(
            pd.to_numeric(blocked.get("permeability_m2"), errors="coerce").gt(0).sum()
        )
        if not blocked.empty
        else 0,
        "target_status_counts": {str(key): int(value) for key, value in status_counts.items()},
        "direction_counts": {str(key): int(value) for key, value in direction_counts.items()},
        "segments": request["normalized_segment_label"].tolist() if not request.empty else [],
        "source_evidence": SOURCE_EVIDENCE,
        "requested_field_set": REQUESTED_FIELD_SET,
        "fallback_request": FALLBACK_REQUEST,
        "available_geometry_reference": summarize_available_geometry(segment_geometry),
        "outputs": outputs,
        "activation_decision": (
            "No historical BCD-A24/25/26/27 or BFM-D19 row is activated by this package; "
            "the package defines exactly what external geometry is still needed."
        ),
    }


def table_lines(request: pd.DataFrame) -> list[str]:
    lines = [
        "| Segment | Block label | Rows | Depth range m | Direction | Twin | k range m2 | log10 k range | Requested endpoints |",
        "| --- | --- | ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for _, row in request.iterrows():
        depth_range = f"{fmt_float(row['depth_min_m'], 3)}-{fmt_float(row['depth_max_m'], 3)}"
        k_range = f"{fmt_sci(row['permeability_m2_min'])}-{fmt_sci(row['permeability_m2_max'])}"
        log_range = f"{fmt_float(row['log10_permeability_min'], 5)}-{fmt_float(row['log10_permeability_max'], 5)}"
        endpoints = f"`{row['requested_start_label']}` / `{row['requested_end_label']}`"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['normalized_segment_label']}`",
                    str(row.get("block_label", "")),
                    str(int(row["blocked_rows"])),
                    depth_range,
                    str(row.get("direction_inferred", "")),
                    str(row.get("twin_inferred", "")) if not pd.isna(row.get("twin_inferred", "")) else "",
                    k_range,
                    log_range,
                    endpoints,
                ]
            )
            + " |"
        )
    return lines


def write_markdown(
    path: Path,
    request: pd.DataFrame,
    summary: dict[str, Any],
    raw_source_files: list[Path],
) -> None:
    outputs = summary["outputs"]
    lines = [
        "# Historical Permeability Endpoint Geometry Request",
        "",
        "This package converts the remaining historical permeability geometry gap into a",
        "specific external-data request.  It does not infer or digitize endpoints by",
        "itself, because the collected files only prove orientation and measurement",
        "values for these rows, not label-resolved start/end coordinates.",
        "",
        "## Current State",
        "",
        f"- Blocked segments: {summary['request_segment_count']}",
        f"- Blocked interpreted rows: {summary['blocked_row_count']}",
        f"- Positive blocked rows: {summary['positive_blocked_row_count']}",
        "- Activation status: `blocked_missing_labelled_endpoint_geometry` for every row listed here.",
        "",
        "## Endpoint Request Table",
        "",
        *table_lines(request),
        "",
        "## What To Ask BGR/Gesa For",
        "",
        "For each row in the table, request the following geometry metadata:",
        "",
        f"- {REQUESTED_FIELD_SET}",
        f"- {FALLBACK_REQUEST}",
        "- Confirm whether the listed workbook depth is measured from the borehole collar along the borehole trace.",
        "- Confirm whether the 10 cm interval should be treated as centred on the reported depth, starting at the reported depth, or using another packer convention.",
        "- For BFM-D19, confirm how the evapometer values/depths map to the BFM-D19 borehole trace and whether the `Evapometer` zone in `VisualisationCDA.dat` is the correct spatial support.",
        "",
        "Email-ready text:",
        "",
        "```text",
        "Could you please provide labelled endpoint geometry for BCD-A24, BCD-A25, BCD-A26, BCD-A27, and BFM-D19 in the same local coordinate frame as the CD-A coordinate workbook / OGS projection?",
        "",
        "For each trace we need start/collar and end/tip x,y,z coordinates, the depth-zero reference, the positive along-borehole direction, the convention for the reported permeability depth values, and an uncertainty estimate. If original coordinates are unavailable, an approved digitized trace with source figure/file and uncertainty would be sufficient for a gated model test.",
        "",
        "The reason is that 98 interpreted permeability/evapometer rows are already extracted and orientation-classified, but they cannot be projected into OGS cells until these endpoints are labelled.",
        "```",
        "",
        "## Source Evidence Used",
        "",
    ]
    for key, value in SOURCE_EVIDENCE.items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Why These Rows Stay Inactive",
            "",
            "The active direct permeability operator samples a finite interval on a labelled",
            "borehole trace and compares the workbook value to a log-space directional",
            "intrinsic-permeability response.  Without labelled endpoints, the interval",
            "centre and direction cannot be mapped to OGS cells.  Using the generic",
            "`Permeability_bhrg` or `Permeability_Meas_points` Tecplot zones without a",
            "label mapping would silently assign measurements to unsupported locations.",
            "",
            "## Raw Value Files",
            "",
        ]
    )
    for source_file in raw_source_files:
        lines.append(f"- `{source_file}`")
    lines.extend(
        [
            "",
            "## Generated Files",
            "",
            f"- Request table: `{outputs['request_csv']}`",
            f"- Blocked-row table: `{outputs['blocked_rows_csv']}`",
            f"- Summary JSON: `{outputs['summary_json']}`",
            f"- This note: `{outputs['markdown']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def copy_to_catalogue(paths: list[Path], catalogue_dir: Path) -> list[str]:
    catalogue_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for path in paths:
        destination = catalogue_dir / path.name
        shutil.copy2(path, destination)
        copied.append(str(destination))
    return copied


def main() -> None:
    args = parse_args()
    processed = args.processed_dir
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    catalogue_dir = args.catalogue_dir or catalogue_dir_from(processed)

    targets = read_csv(processed / "permeability_observation_targets.csv")
    missing = read_csv(processed / "permeability_missing_geometry_audit.csv")
    segment_geometry = read_csv(processed / "permeability_segment_geometry.csv")
    if targets.empty or missing.empty:
        raise SystemExit("permeability target and missing-geometry audit files are required")

    output_paths = {
        "request_csv": output_dir / "permeability_endpoint_geometry_request.csv",
        "blocked_rows_csv": output_dir / "permeability_endpoint_geometry_blocked_rows.csv",
        "summary_json": output_dir / "permeability_endpoint_geometry_request_summary.json",
        "markdown": output_dir / "permeability_endpoint_geometry_request.md",
    }
    outputs = {key: str(value) for key, value in output_paths.items()}

    request = build_request_rows(missing, targets)
    blocked = build_blocked_rows(targets, request)
    summary = build_summary(request, blocked, segment_geometry, outputs)

    request.to_csv(output_paths["request_csv"], index=False)
    blocked.to_csv(output_paths["blocked_rows_csv"], index=False)
    output_paths["summary_json"].write_text(
        json.dumps(json_ready(summary), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_markdown(output_paths["markdown"], request, summary, source_file_paths(processed))

    copied = copy_to_catalogue(list(output_paths.values()), catalogue_dir)
    summary["catalogue_copies"] = copied
    output_paths["summary_json"].write_text(
        json.dumps(json_ready(summary), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    shutil.copy2(output_paths["summary_json"], catalogue_dir / output_paths["summary_json"].name)

    for label, path in outputs.items():
        print(f"wrote {label}: {path}")
    print(f"catalogue copies: {len(copied)}")
    print(f"blocked segments: {summary['request_segment_count']}")
    print(f"blocked rows: {summary['blocked_row_count']}")


if __name__ == "__main__":
    main()
