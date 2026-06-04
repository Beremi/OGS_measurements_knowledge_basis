#!/usr/bin/env python3
"""Build a request package for missing numeric other-HM monitoring exports."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


COMMON_TIME_SERIES_FIELDS = (
    "timestamp with timezone or stated local time; instrument id; measured value; "
    "unit; coordinate or trace/support id; zero/reference convention; calibration "
    "or conversion used by Geoscope; quality/status flags; maintenance/failure "
    "flags; sampling interval; and raw file provenance."
)

REQUEST_SPECS = [
    {
        "request_id": "geoscope_mini_piezometer_time_series",
        "priority": "high",
        "measurement_type": "mini_piezometer",
        "known_labels_or_scope": "BCD-A28 to BCD-A31",
        "current_evidence": (
            "2026 TD minutes say mini-piezometers BCD-A28 to BCD-A31 were working well; "
            "the HERMES input note lists pore-water pressure and piezometer/extensometer "
            "measurements as available CD-A data."
        ),
        "requested_files": (
            "Geoscope pressure time-series exports for BCD-A28, BCD-A29, BCD-A30, "
            "and BCD-A31, including calibration/status metadata."
        ),
        "requested_fields": (
            COMMON_TIME_SERIES_FIELDS
            + " Pressure convention must state absolute/gauge/head, pressure unit, "
            "temperature compensation, sensor elevation/depth, and whether values are "
            "liquid pore pressure or hydraulic head."
        ),
        "model_quantity": "liquid pore pressure or hydraulic head",
        "model_entry_if_provided": (
            "Candidate pressure residuals against OGS liquid_pressure/pressure-head "
            "samples after sensor coordinates and reference pressure are confirmed."
        ),
        "current_activation_status": "blocked_numeric_series_missing",
    },
    {
        "request_id": "geoscope_extensometer_time_series",
        "priority": "high",
        "measurement_type": "extensometer",
        "known_labels_or_scope": "all CD-A extensometers, with BCD-A9/B10 failure metadata",
        "current_evidence": (
            "2026 TD minutes report horizontal and vertical extensometers BCD-A9/B10 "
            "in the closed niche failed since September 2025; BGR modelling slides "
            "set displacements/strains from extensometers as a priority validation stream."
        ),
        "requested_files": (
            "Geoscope extensometer displacement/strain time-series exports, including "
            "instrument geometry and the September 2025 BCD-A9/B10 failure/status record."
        ),
        "requested_fields": (
            COMMON_TIME_SERIES_FIELDS
            + " Include anchor/collar geometry, orientation, gauge length, whether the "
            "reported value is displacement or strain, sign convention, and restart/zero "
            "changes after maintenance."
        ),
        "model_quantity": "displacement or strain",
        "model_entry_if_provided": (
            "Mechanical validation residuals or rejection gates against OGS displacement/"
            "strain diagnostics, respecting post-failure data-quality boundaries."
        ),
        "current_activation_status": "blocked_numeric_series_missing",
    },
    {
        "request_id": "geoscope_crackmeter_time_series",
        "priority": "medium",
        "measurement_type": "crackmeter",
        "known_labels_or_scope": "closed-niche ongoing trend and open-niche seasonal variation",
        "current_evidence": (
            "2026 TD minutes state crackmeter data show one ongoing trend in the closed "
            "niche and seasonal variation in the open niche."
        ),
        "requested_files": (
            "Geoscope crackmeter time-series exports for all CD-A crackmeter positions, "
            "including position labels and data-quality/status flags."
        ),
        "requested_fields": (
            COMMON_TIME_SERIES_FIELDS
            + " Include crackmeter location, measured aperture/displacement component, "
            "positive sign convention, zero/reference date, and any temperature correction."
        ),
        "model_quantity": "crack aperture or local relative displacement",
        "model_entry_if_provided": (
            "Qualitative or numeric deformation gates for open/closed twin contrast; "
            "hard residual only if support and sign convention can be matched to model output."
        ),
        "current_activation_status": "blocked_numeric_series_missing",
    },
    {
        "request_id": "laser_scan_statistical_interpretation_2026_04_20",
        "priority": "medium",
        "measurement_type": "laser_scan_surface",
        "known_labels_or_scope": "open_twin_LS and closed_twin_LS surfaces/statistical update",
        "current_evidence": (
            "2026 TD minutes say laser scans with statistical interpretation were sent "
            "in the 2026-04-20 Geoscope update; VisualisationCDA.dat contains open_twin_LS "
            "and closed_twin_LS surface zones."
        ),
        "requested_files": (
            "Laser-scan statistical interpretation files from the 2026-04-20 update, "
            "plus raw/registered point clouds or surface-difference products if available."
        ),
        "requested_fields": (
            "scan date/time; open/closed twin surface id; coordinate frame; registration "
            "targets and transform; displacement/difference statistic; uncertainty or "
            "registration error; masked/excluded areas; and raw/statistical file provenance."
        ),
        "model_quantity": "surface displacement or scan-difference field",
        "model_entry_if_provided": (
            "Surface-displacement validation or qualitative mechanical plausibility gate "
            "after OGS displacement output and survey frame are aligned."
        ),
        "current_activation_status": "blocked_statistical_export_missing",
    },
    {
        "request_id": "precision_levelling_full_survey_table",
        "priority": "low",
        "measurement_type": "precision_levelling",
        "known_labels_or_scope": "points 57, 58, CDA-C1 to CDA-C5, CDA-O1 to CDA-O5",
        "current_evidence": (
            "The levelling presentation gives a 12-point slide summary, but not a full "
            "survey table with all dates, covariance/reference frame, and processing details."
        ),
        "requested_files": (
            "Spreadsheet/table export of precision-levelling campaigns, including all "
            "campaign dates and reference-frame/covariance information."
        ),
        "requested_fields": (
            "point id; campaign date; elevation or height change; unit; reference point/"
            "frame; covariance or standard uncertainty; instrument/procedure metadata; "
            "and flags for excluded or adjusted points."
        ),
        "model_quantity": "vertical displacement",
        "model_entry_if_provided": (
            "Weighted displacement-validation residuals; the current slide-summary rows "
            "can only support sign/order-of-magnitude checks."
        ),
        "current_activation_status": "partial_slide_summary_available_full_table_missing",
    },
    {
        "request_id": "geoscope_boundary_and_auxiliary_context",
        "priority": "medium",
        "measurement_type": "boundary_context",
        "known_labels_or_scope": "RH, temperature, door/opening times, suction from Geoscope update",
        "current_evidence": (
            "2026 TD minutes say the Geoscope update covered RH, temperature, door "
            "opening times, and suction in addition to deformation/pressure streams."
        ),
        "requested_files": (
            "Auxiliary Geoscope exports for RH, temperature, door/opening times, and "
            "suction if they are distinct from the already catalogued RH/suction files."
        ),
        "requested_fields": (
            COMMON_TIME_SERIES_FIELDS
            + " Include sensor location, whether RH is percent or fraction, temperature "
            "unit, door/opening event definition, and suction conversion convention."
        ),
        "model_quantity": "boundary-condition forcing and disturbance context",
        "model_entry_if_provided": (
            "Boundary-condition provenance check for RH/temperature forcing and event "
            "exclusion windows, not a separate hard residual by default."
        ),
        "current_activation_status": "blocked_or_unverified_auxiliary_exports",
    },
]


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
        help="Optional other-HM catalogue derived_files directory to copy outputs into.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


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
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(float(value)) else float(value)
    if value is pd.NA or value is None:
        return None
    return value


def project_root_from(processed_dir: Path) -> Path:
    return processed_dir.resolve().parents[2]


def catalogue_dir_from(processed_dir: Path) -> Path:
    return (
        project_root_from(processed_dir)
        / "cda_knowledge_base"
        / "measurements"
        / "other_hm_monitoring"
        / "derived_files"
    )


def source_dir_from(processed_dir: Path) -> Path:
    return (
        project_root_from(processed_dir)
        / "cda_knowledge_base"
        / "measurements"
        / "other_hm_monitoring"
        / "source_files"
    )


def source_files(processed_dir: Path) -> list[Path]:
    source_dir = source_dir_from(processed_dir)
    return [
        source_dir / "2026-05-11_TD517_CD-A_260507__Minutes.pdf",
        source_dir / "CD-A_TD_2026_sc.pdf",
        source_dir / "Folien_Niv_TD_CDA_2026.pdf",
        source_dir / "2024-12-19_Input_HERMES_BGR_20241217.pdf",
        source_dir / "VisualisationCDA.dat",
    ]


def unique_join(values: pd.Series) -> str:
    seen: list[str] = []
    for value in values.dropna():
        text = str(value).strip()
        if text and text.lower() != "nan" and text not in seen:
            seen.append(text)
    return "; ".join(seen)


def build_request_table(
    summary: dict[str, Any],
    zones: pd.DataFrame,
    levelling: pd.DataFrame,
) -> pd.DataFrame:
    zone_counts = summary.get("zone_counts_by_measurement_type", {})
    rows: list[dict[str, Any]] = []
    for spec in REQUEST_SPECS:
        measurement_type = spec["measurement_type"]
        support_types = [measurement_type]
        if measurement_type == "crackmeter":
            support_types = ["fracture_or_crack_geometry"]
        elif measurement_type == "boundary_context":
            support_types = ["rh_suction_support", "evapometer"]
        support_zone_count = int(sum(int(zone_counts.get(item, 0)) for item in support_types))
        support_zone_names = ""
        if not zones.empty:
            support_zone_names = unique_join(
                zones.loc[zones["measurement_type"].astype(str).isin(support_types), "zone_name"]
            )
        if measurement_type == "precision_levelling":
            support_zone_count = int(len(levelling))
            support_zone_names = unique_join(levelling["point_name"]) if not levelling.empty else ""
        rows.append(
            {
                **spec,
                "catalogue_status": "not_present_as_numeric_export",
                "available_structured_support_count": support_zone_count,
                "available_structured_support_labels": support_zone_names,
                "hard_residual_gate": (
                    "Do not assign a hard likelihood weight until numeric export, support geometry, "
                    "units, reference convention, and quality flags are present."
                ),
            }
        )
    return pd.DataFrame(rows)


def build_evidence_table(qualitative: pd.DataFrame, levelling: pd.DataFrame) -> pd.DataFrame:
    evidence_rows: list[dict[str, Any]] = []
    if not qualitative.empty:
        missing_mask = qualitative["readiness"].astype(str).str.contains(
            "missing|not_in_catalogue|scope_documented|pending|maintenance_caveat", case=False, na=False
        )
        for _, row in qualitative[missing_mask].iterrows():
            evidence_rows.append(
                {
                    "evidence_type": "qualitative_source_statement",
                    "source_file": row.get("source_file"),
                    "source_page": row.get("source_page"),
                    "measurement_type": row.get("measurement_type"),
                    "evidence_id": row.get("target_id"),
                    "evidence_text": row.get("observation"),
                    "current_use": row.get("model_use"),
                    "readiness": row.get("readiness"),
                }
            )
    if not levelling.empty:
        evidence_rows.append(
            {
                "evidence_type": "numeric_slide_summary",
                "source_file": unique_join(levelling["source_file"]),
                "source_page": unique_join(levelling["source_page"]),
                "measurement_type": "precision_levelling",
                "evidence_id": "levelling_slide_summary_12_points",
                "evidence_text": (
                    f"Slide-summary table has {len(levelling)} points; full campaign table "
                    "with covariance/reference-frame metadata is still preferred."
                ),
                "current_use": "sign/order-of-magnitude deformation validation only",
                "readiness": "numeric_summary_available_full_table_missing",
            }
        )
    return pd.DataFrame(evidence_rows)


def build_summary(
    request: pd.DataFrame,
    evidence: pd.DataFrame,
    inventory_summary: dict[str, Any],
    outputs: dict[str, str],
    copied: list[str] | None = None,
) -> dict[str, Any]:
    priority_counts = request["priority"].value_counts().sort_index().to_dict() if not request.empty else {}
    status_counts = (
        request["current_activation_status"].value_counts().sort_index().to_dict()
        if not request.empty
        else {}
    )
    return {
        "status": "request_package_ready_numeric_exports_still_missing",
        "request_rows": int(request.shape[0]),
        "evidence_rows": int(evidence.shape[0]),
        "priority_counts": {str(key): int(value) for key, value in priority_counts.items()},
        "activation_status_counts": {str(key): int(value) for key, value in status_counts.items()},
        "inventory_status": inventory_summary.get("status"),
        "inventory_zone_rows": inventory_summary.get("zone_rows"),
        "inventory_levelling_rows": inventory_summary.get("levelling_rows"),
        "inventory_qualitative_target_rows": inventory_summary.get("qualitative_target_rows"),
        "active_objective_rows": 0,
        "remaining_blocker": (
            "Numeric Geoscope and laser-scan exports are still absent from the catalogue; "
            "the request package states exactly what is needed before hard pressure/"
            "deformation residuals can be assigned."
        ),
        "outputs": outputs,
        "catalogue_copies": copied or [],
    }


def table_lines(request: pd.DataFrame) -> list[str]:
    lines = [
        "| Request | Priority | Scope | Model quantity | Current status |",
        "| --- | --- | --- | --- | --- |",
    ]
    for _, row in request.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['request_id']}`",
                    str(row["priority"]),
                    str(row["known_labels_or_scope"]).replace("|", "\\|"),
                    str(row["model_quantity"]).replace("|", "\\|"),
                    f"`{row['current_activation_status']}`",
                ]
            )
            + " |"
        )
    return lines


def write_markdown(
    path: Path,
    request: pd.DataFrame,
    evidence: pd.DataFrame,
    summary: dict[str, Any],
    raw_sources: list[Path],
) -> None:
    lines = [
        "# Missing Numeric Other-HM Monitoring Request",
        "",
        "This package turns the remaining secondary hydromechanical monitoring gap into",
        "specific file requests.  The current catalogue has layout geometry, levelling",
        "slide values, and qualitative TD statements, but not the numeric Geoscope and",
        "laser-scan exports needed for hard pressure/deformation residuals.",
        "",
        "## Current State",
        "",
        f"- Request rows: {summary['request_rows']}",
        f"- Evidence rows: {summary['evidence_rows']}",
        f"- Active objective rows from this stream: {summary['active_objective_rows']}",
        f"- Inventory status: `{summary['inventory_status']}`",
        "",
        "## Request Table",
        "",
        *table_lines(request),
        "",
        "## What To Ask BGR/Gesa For",
        "",
        "Email-ready text:",
        "",
        "```text",
        "Could you please provide the numeric CD-A monitoring exports behind the 2026 Geoscope/laser-scan update?",
        "",
        "The current catalogue has the meeting minutes, layout geometry, and levelling slide summary, but not the raw numeric exports needed for model residuals. We need Geoscope time series for mini-piezometers BCD-A28 to BCD-A31, extensometers including BCD-A9/B10 status and failure metadata since September 2025, crackmeters, and auxiliary RH/temperature/door/suction logs if these are separate from the already shared RH files. We also need the laser-scan statistical interpretation files from the 2026-04-20 update, ideally with the registered point clouds or surface-difference products.",
        "",
        "For time series, please include timestamps, units, instrument ids, coordinates/support ids, zero/reference conventions, calibration or conversion used by Geoscope, quality/status flags, and raw-file provenance. For laser scans, please include scan dates, coordinate frame, registration transform/targets, displacement or difference statistics, uncertainty/registration error, and masks/excluded areas.",
        "```",
        "",
        "## Detailed Requests",
        "",
    ]
    for _, row in request.iterrows():
        lines.extend(
            [
                f"### `{row['request_id']}`",
                "",
                f"- Priority: `{row['priority']}`",
                f"- Scope: {row['known_labels_or_scope']}",
                f"- Requested files: {row['requested_files']}",
                f"- Required fields: {row['requested_fields']}",
                f"- Model entry if provided: {row['model_entry_if_provided']}",
                f"- Current evidence: {row['current_evidence']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Evidence Rows",
            "",
            "| Evidence id | Type | Source | Page | Readiness |",
            "| --- | --- | --- | ---: | --- |",
        ]
    )
    for _, row in evidence.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['evidence_id']}`",
                    str(row["evidence_type"]),
                    f"`{row['source_file']}`",
                    str(row["source_page"]),
                    f"`{row['readiness']}`",
                ]
            )
            + " |"
        )
    lines.extend(["", "## Source Files Checked", ""])
    for source in raw_sources:
        lines.append(f"- `{source}`")
    lines.extend(["", "## Generated Files", ""])
    for label, output_path in summary["outputs"].items():
        lines.append(f"- `{label}`: `{output_path}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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

    zones = read_csv(processed / "other_hm_visualisation_zones.csv")
    levelling = read_csv(processed / "other_hm_levelling_displacements.csv")
    qualitative = read_csv(processed / "other_hm_qualitative_targets.csv")
    inventory_summary = read_json(processed / "other_hm_monitoring_summary.json")
    if zones.empty or qualitative.empty or not inventory_summary:
        raise SystemExit("other-HM inventory outputs are required before building the request package")

    output_paths = {
        "request_csv": output_dir / "other_hm_missing_numeric_request.csv",
        "evidence_csv": output_dir / "other_hm_missing_numeric_evidence.csv",
        "summary_json": output_dir / "other_hm_missing_numeric_request_summary.json",
        "markdown": output_dir / "other_hm_missing_numeric_request.md",
    }
    outputs = {key: str(value) for key, value in output_paths.items()}
    request = build_request_table(inventory_summary, zones, levelling)
    evidence = build_evidence_table(qualitative, levelling)

    request.to_csv(output_paths["request_csv"], index=False)
    evidence.to_csv(output_paths["evidence_csv"], index=False)
    summary = build_summary(request, evidence, inventory_summary, outputs)
    write_markdown(output_paths["markdown"], request, evidence, summary, source_files(processed))
    output_paths["summary_json"].write_text(
        json.dumps(json_ready(summary), indent=2, sort_keys=True),
        encoding="utf-8",
    )

    copied = copy_to_catalogue(list(output_paths.values()), catalogue_dir)
    summary = build_summary(request, evidence, inventory_summary, outputs, copied)
    output_paths["summary_json"].write_text(
        json.dumps(json_ready(summary), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    shutil.copy2(output_paths["summary_json"], catalogue_dir / output_paths["summary_json"].name)

    print(f"wrote request_csv: {outputs['request_csv']}")
    print(f"wrote evidence_csv: {outputs['evidence_csv']}")
    print(f"wrote summary_json: {outputs['summary_json']}")
    print(f"wrote markdown: {outputs['markdown']}")
    print(f"catalogue copies: {len(copied)}")
    print(f"request rows: {summary['request_rows']}")
    print(f"evidence rows: {summary['evidence_rows']}")


if __name__ == "__main__":
    main()
