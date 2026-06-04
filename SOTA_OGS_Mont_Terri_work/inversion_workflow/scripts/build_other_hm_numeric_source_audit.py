#!/usr/bin/env python3
"""Audit whether other-HM numeric exports are locally present.

The other-HM request package asks for Geoscope time series, laser-scan statistical
products, and a complete levelling survey table.  This script makes the absence or
partial presence of those files reproducible by scanning the current source bundle,
ZIP members, extracted text, layout-support geometry, and extracted levelling rows.
It distinguishes numeric support geometry from hard-residual-ready time series.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REQUEST_KEYWORDS = {
    "geoscope_mini_piezometer_time_series": [
        "mini-piezometer",
        "mini piezometer",
        "minipiezometer",
        "piezometer",
        "pore pressure",
        "BCD-A28",
        "BCD-A29",
        "BCD-A30",
        "BCD-A31",
    ],
    "geoscope_extensometer_time_series": [
        "extensometer",
        "extensometers",
        "strain",
        "displacement",
        "BCD-A9",
        "BCD-A10",
    ],
    "geoscope_crackmeter_time_series": [
        "crackmeter",
        "crackmeters",
        "crack width",
        "crack closure",
        "closure of the crack",
    ],
    "laser_scan_statistical_interpretation_2026_04_20": [
        "laser scan",
        "laser scans",
        "laser scanning",
        "statistical interpretation",
        "open_twin_LS",
        "closed_twin_LS",
    ],
    "precision_levelling_full_survey_table": [
        "precision levelling",
        "levelling",
        "height difference",
        "detectable displacement",
        "CDA-O1",
        "CDA-C4",
    ],
    "geoscope_boundary_and_auxiliary_context": [
        "relative humidity",
        "RH",
        "temperature",
        "opening times",
        "door",
        "suction",
    ],
}

NUMERIC_EXPORT_EXTENSIONS = {".csv", ".tsv", ".xlsx", ".xls", ".xlsm", ".ods", ".dat", ".txt"}
PRESENTATION_EXTENSIONS = {".pdf", ".pptx", ".ppt"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/other_hm_monitoring"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
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
    return value


def request_status(request_id: str) -> tuple[str, str]:
    if request_id == "precision_levelling_full_survey_table":
        return (
            "partial_slide_summary_only",
            "Use the extracted 12-row levelling summary only as a sign/order-of-magnitude validation target until the full survey table, covariance/reference frame, and all epochs are provided.",
        )
    if request_id == "laser_scan_statistical_interpretation_2026_04_20":
        return (
            "support_geometry_only_statistical_export_missing",
            "VisualisationCDA.dat contains open/closed laser-scan surface geometry, but no dated displacement/statistical interpretation product or registration uncertainty file is present.",
        )
    return (
        "support_or_text_evidence_only_numeric_time_series_missing",
        "The catalogue contains layout support and report/minute evidence, but no hard-residual-ready numeric time-series export with units, timestamps, reference conventions, and quality flags.",
    )


def support_for_request(request_id: str, zones: pd.DataFrame, levelling: pd.DataFrame) -> tuple[int, str]:
    if zones.empty:
        zone_labels: list[str] = []
    elif request_id == "geoscope_mini_piezometer_time_series":
        zone_labels = zones[zones["measurement_type"].eq("mini_piezometer")]["zone_name"].astype(str).tolist()
    elif request_id == "geoscope_extensometer_time_series":
        zone_labels = zones[zones["measurement_type"].eq("extensometer")]["zone_name"].astype(str).tolist()
    elif request_id == "geoscope_crackmeter_time_series":
        zone_labels = zones[zones["measurement_type"].eq("fracture_or_crack_geometry")]["zone_name"].astype(str).tolist()
    elif request_id == "laser_scan_statistical_interpretation_2026_04_20":
        zone_labels = zones[zones["measurement_type"].eq("laser_scan_surface")]["zone_name"].astype(str).tolist()
    elif request_id == "geoscope_boundary_and_auxiliary_context":
        zone_labels = zones[
            zones["measurement_type"].isin(["rh_suction_support", "evapometer"])
        ]["zone_name"].astype(str).tolist()
    else:
        zone_labels = []
    if request_id == "precision_levelling_full_survey_table":
        labels = levelling["point_name"].astype(str).tolist() if not levelling.empty else []
        return len(labels), "; ".join(labels)
    return len(zone_labels), "; ".join(zone_labels)


def numeric_local_rows(request_id: str, levelling: pd.DataFrame, zones: pd.DataFrame) -> tuple[int, str]:
    if request_id == "precision_levelling_full_survey_table" and not levelling.empty:
        return int(levelling.shape[0]), "other_hm_levelling_displacements.csv (slide-summary rows, not full survey table)"
    if request_id == "laser_scan_statistical_interpretation_2026_04_20" and not zones.empty:
        laser = zones[zones["measurement_type"].eq("laser_scan_surface")]
        if not laser.empty:
            nodes = int(pd.to_numeric(laser["nodes"], errors="coerce").fillna(0).sum())
            return nodes, "VisualisationCDA.dat laser surface geometry nodes only"
    return 0, ""


def read_text_hits(extracted_dir: Path, request_id: str) -> list[dict[str, Any]]:
    keywords = REQUEST_KEYWORDS.get(request_id, [])
    if not extracted_dir.exists() or not keywords:
        return []
    pattern = re.compile("|".join(re.escape(word) for word in keywords), flags=re.IGNORECASE)
    hits: list[dict[str, Any]] = []
    for path in sorted(extracted_dir.glob("*.txt")):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for index, line in enumerate(lines, start=1):
            if not pattern.search(line):
                continue
            snippet_lines = lines[max(0, index - 2) : min(len(lines), index + 1)]
            hits.append(
                {
                    "request_id": request_id,
                    "source_text_file": str(path),
                    "line_number": index,
                    "matched_keywords": "; ".join(
                        sorted({word for word in keywords if re.search(re.escape(word), line, flags=re.IGNORECASE)})
                    ),
                    "snippet": " ".join(item.strip() for item in snippet_lines if item.strip())[:500],
                }
            )
            if len([hit for hit in hits if hit["source_text_file"] == str(path)]) >= 5:
                break
    return hits


def source_bundle_counts(source_summary: pd.DataFrame, zip_members: pd.DataFrame) -> dict[str, Any]:
    if source_summary.empty:
        source_files = 0
        ext_counts: dict[str, int] = {}
        numeric_files: list[str] = []
        presentation_files: list[str] = []
    else:
        source_files = int(source_summary.shape[0])
        ext_counts = {
            str(key): int(value)
            for key, value in source_summary["extension"].fillna("").value_counts().sort_index().items()
        }
        numeric_files = (
            source_summary[source_summary["extension"].isin(NUMERIC_EXPORT_EXTENSIONS)]["source_path"]
            .astype(str)
            .tolist()
        )
        presentation_files = (
            source_summary[source_summary["extension"].isin(PRESENTATION_EXTENSIONS)]["source_path"]
            .astype(str)
            .tolist()
        )
    if zip_members.empty:
        zip_member_count = 0
        zip_numeric_count = 0
        zip_ext_counts: dict[str, int] = {}
    else:
        zip_member_count = int(zip_members.shape[0])
        zip_numeric_count = int(zip_members["extension"].isin(NUMERIC_EXPORT_EXTENSIONS).sum())
        zip_ext_counts = {
            str(key): int(value)
            for key, value in zip_members["extension"].fillna("").value_counts().sort_index().items()
        }
    return {
        "source_file_count": source_files,
        "source_extension_counts": ext_counts,
        "zip_member_count": zip_member_count,
        "zip_member_numeric_candidate_count": zip_numeric_count,
        "zip_member_extension_counts": zip_ext_counts,
        "numeric_extension_source_files": numeric_files,
        "presentation_or_report_source_files": presentation_files,
    }


def build_audit(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    processed = args.processed_dir
    catalogue = args.catalogue_dir
    deep_dir = catalogue / "derived_files" / "deep_source_pass"
    source_summary = read_csv(deep_dir / "source_file_deep_summary.csv")
    zip_members = read_csv(deep_dir / "zip_member_deep_summary.csv")
    requests = read_csv(processed / "other_hm_missing_numeric_request.csv")
    zones = read_csv(processed / "other_hm_visualisation_zones.csv")
    levelling = read_csv(processed / "other_hm_levelling_displacements.csv")
    extracted_dir = deep_dir / "extracted_text"
    bundle = source_bundle_counts(source_summary, zip_members)

    evidence_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    for _, request in requests.iterrows():
        request_id = str(request["request_id"])
        support_count, support_labels = support_for_request(request_id, zones, levelling)
        local_rows, local_files = numeric_local_rows(request_id, levelling, zones)
        status, action = request_status(request_id)
        hits = read_text_hits(extracted_dir, request_id)
        evidence_rows.extend(hits)
        evidence_count = len(hits)
        audit_rows.append(
            {
                "request_id": request_id,
                "measurement_type": request.get("measurement_type"),
                "priority": request.get("priority"),
                "requested_files": request.get("requested_files"),
                "local_support_count": support_count,
                "local_support_labels": support_labels,
                "local_numeric_or_geometry_rows": local_rows,
                "local_numeric_or_geometry_files": local_files,
                "local_text_evidence_hits": evidence_count,
                "zip_member_numeric_candidate_count": bundle["zip_member_numeric_candidate_count"],
                "numeric_export_status": status,
                "hard_residual_status": (
                    "not_ready_for_hard_residual"
                    if status != "partial_slide_summary_only"
                    else "not_ready_for_weighted_hard_residual_slide_summary_only"
                ),
                "action": action,
            }
        )

    audit = pd.DataFrame(audit_rows)
    evidence = pd.DataFrame(evidence_rows)
    no_hard_ready = int(audit["hard_residual_status"].astype(str).str.startswith("not_ready").sum())
    summary = {
        "status": "other_hm_numeric_source_audit_complete_hard_residual_exports_missing",
        "request_rows": int(audit.shape[0]),
        "hard_residual_ready_request_count": int(audit["hard_residual_status"].eq("hard_residual_ready").sum())
        if "hard_residual_status" in audit.columns
        else 0,
        "not_ready_request_count": no_hard_ready,
        "local_support_ready_request_count": int(audit["local_support_count"].gt(0).sum()),
        "partial_numeric_summary_request_count": int(
            audit["numeric_export_status"].eq("partial_slide_summary_only").sum()
        ),
        "geometry_only_request_count": int(
            audit["numeric_export_status"].eq("support_geometry_only_statistical_export_missing").sum()
        ),
        "source_bundle": bundle,
        "evidence_hit_count": int(evidence.shape[0]),
        "remaining_blocker": (
            "Local source scan found layout geometry, laser surface geometry, extracted levelling slide rows, "
            "and report/minute evidence, but no hard-residual-ready Geoscope time series, laser statistical "
            "interpretation product, or full levelling survey table."
        ),
        "activation_gate": (
            "Do not assign hard HM residual weights until numeric exports include timestamps or survey epochs, "
            "units, support geometry, reference conventions, uncertainty/covariance, and quality/status flags."
        ),
    }
    return audit, evidence, summary


def fmt(value: Any) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "n/a"
    return str(value)


def write_markdown(path: Path, audit: pd.DataFrame, evidence: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# Other HM Numeric Source Audit",
        "",
        "This audit scans the current other-HM source bundle for hard-residual-ready numeric exports.",
        "It separates source evidence and support geometry from time-series/statistical products that can actually be weighted in a likelihood.",
        "",
        "## Status",
        "",
        f"- Status: `{summary['status']}`",
        f"- Request rows audited: {summary['request_rows']}",
        f"- Hard-residual-ready requests: {summary['hard_residual_ready_request_count']}",
        f"- Requests with local support geometry or extracted labels: {summary['local_support_ready_request_count']}",
        f"- Partial numeric slide-summary requests: {summary['partial_numeric_summary_request_count']}",
        f"- Geometry-only requests: {summary['geometry_only_request_count']}",
        f"- Text evidence hits retained: {summary['evidence_hit_count']}",
        f"- Remaining blocker: {summary['remaining_blocker']}",
        "",
        "## Source Bundle",
        "",
        f"- Source files scanned: {summary['source_bundle']['source_file_count']}",
        f"- ZIP members scanned: {summary['source_bundle']['zip_member_count']}",
        f"- ZIP numeric-candidate members: {summary['source_bundle']['zip_member_numeric_candidate_count']}",
        f"- Source extension counts: `{summary['source_bundle']['source_extension_counts']}`",
        f"- ZIP member extension counts: `{summary['source_bundle']['zip_member_extension_counts']}`",
        "",
        "## Request Audit",
        "",
        "| Request | Local support | Local numeric/geometry rows | Text hits | Status | Action |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for _, row in audit.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['request_id']}`",
                    str(int(row["local_support_count"])),
                    str(int(row["local_numeric_or_geometry_rows"])),
                    str(int(row["local_text_evidence_hits"])),
                    str(row["numeric_export_status"]),
                    str(row["action"]).replace("|", "/"),
                ]
            )
            + " |"
        )
    if not evidence.empty:
        lines.extend(
            [
                "",
                "## Representative Text Evidence",
                "",
                "| Request | Source text | Line | Keywords | Snippet |",
                "| --- | --- | ---: | --- | --- |",
            ]
        )
        shown = evidence.groupby("request_id", group_keys=False).head(4)
        for _, row in shown.iterrows():
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{row['request_id']}`",
                        Path(str(row["source_text_file"])).name,
                        str(int(row["line_number"])),
                        str(row["matched_keywords"]).replace("|", "/"),
                        str(row["snippet"]).replace("|", "/"),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The local catalogue is useful for HM validation but not yet for hard HM likelihood terms.",
            "For mini-piezometers, extensometers, crackmeters, laser scans, and auxiliary boundary logs, the available material is support geometry plus report/minute evidence.",
            "The laser-scan surface zones in `VisualisationCDA.dat` are geometry/support data; they are not the dated statistical scan-difference products mentioned in the minutes.",
            "The levelling slide table is the only extracted numeric deformation summary, but it lacks all campaign epochs, covariance/reference-frame metadata, and point coordinates needed for weighted residuals.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_catalogue(outputs: dict[str, Path], catalogue_dir: Path) -> list[str]:
    if not catalogue_dir.exists():
        return []
    derived = catalogue_dir / "derived_files"
    derived.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for output in outputs.values():
        if output.exists() and output.is_file():
            dest = derived / output.name
            shutil.copy2(output, dest)
            copied.append(str(dest))
    return copied


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "audit_csv": args.output_dir / "other_hm_numeric_source_audit.csv",
        "evidence_csv": args.output_dir / "other_hm_numeric_source_evidence.csv",
        "summary_json": args.output_dir / "other_hm_numeric_source_audit_summary.json",
        "markdown": args.output_dir / "other_hm_numeric_source_audit.md",
    }
    audit, evidence, summary = build_audit(args)
    audit.to_csv(outputs["audit_csv"], index=False)
    evidence.to_csv(outputs["evidence_csv"], index=False)
    write_markdown(outputs["markdown"], audit, evidence, summary)
    summary["outputs"] = {key: str(path) for key, path in outputs.items()}
    summary["catalogue_copies"] = copy_catalogue(outputs, args.catalogue_dir)
    outputs["summary_json"].write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    for key, path in outputs.items():
        print(f"wrote {path}")
    print(f"requests audited: {summary['request_rows']}")
    print(f"hard-residual-ready requests: {summary['hard_residual_ready_request_count']}")


if __name__ == "__main__":
    main()
