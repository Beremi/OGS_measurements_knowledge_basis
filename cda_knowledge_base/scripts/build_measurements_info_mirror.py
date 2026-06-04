#!/usr/bin/env python3
"""Build a measurement-info mirror with copied source files and detailed notes."""

from __future__ import annotations

import csv
import os
import shutil
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MEASUREMENTS = ROOT / "cda_knowledge_base" / "measurements"
INFO_ROOT = ROOT / "cda_knowledge_base" / "measurements_info"
WORK_ROOT = ROOT / "SOTA_OGS_Mont_Terri_work"
INVERSION = WORK_ROOT / "inversion_workflow"

MEASUREMENT_DIRS = [
    "ert",
    "nmr",
    "taupe_tdr",
    "suction_relative_humidity",
    "permeability_pulse_tests",
    "other_hm_monitoring",
    "coordinates_geometry_layout",
    "bedding_geology_structure",
    "model_projection_inputs",
]

ROOT_INDEX_FILES = [
    "archive_inventory.md",
    "archive_member_catalog.csv",
    "catalog_verification.md",
    "deep_source_index.md",
    "deep_source_index.csv",
    "measurement_content_deep_dive.md",
    "measurement_content_deep_dive.csv",
    "measurement_content_deep_dive_summary.json",
    "source_file_manifest.csv",
    "workbook_sheet_deep_index.csv",
]

FOLDER_TO_COVERAGE_ID = {
    "ert": "ert_open_time_series",
    "nmr": "nmr_weekly_and_seasonal",
    "taupe_tdr": "taupe_tdr_edz_bands",
    "suction_relative_humidity": "suction_relative_humidity_open_twin",
    "permeability_pulse_tests": "permeability_pulse_tests",
    "other_hm_monitoring": "other_hm_monitoring",
    "coordinates_geometry_layout": "coordinates_and_geometry",
    "bedding_geology_structure": "bedding_structure",
    "model_projection_inputs": "model_projection_inputs",
}

FOLDER_TO_STREAM_ID = {
    "ert": "ert_resistivity",
    "nmr": "nmr_water_content",
    "taupe_tdr": "taupe_tdr",
    "suction_relative_humidity": "relative_humidity_suction",
    "permeability_pulse_tests": "permeability_pulse_tests",
    "other_hm_monitoring": "other_hm_monitoring",
    "coordinates_geometry_layout": "geometry_support",
    "model_projection_inputs": "model_projection_inputs",
}

FOLDER_TO_FINAL_CRITERION_ID = {
    "ert": "P09_ert_gate",
    "nmr": "P08_nmr_residual_policy",
    "taupe_tdr": "P10_taupe_gate",
    "suction_relative_humidity": "P11_rh_gate",
    "permeability_pulse_tests": "P13_perm_endpoint_gate",
    "other_hm_monitoring": "P12_other_hm_gate",
    "model_projection_inputs": "P14_cte_confirmation",
}

MEASUREMENT_NOTES: dict[str, dict[str, list[str] | str]] = {
    "ert": {
        "title": "ERT / Electrical Resistivity",
        "purpose": (
            "Electrical resistivity tomography and resistivity monitoring around the CD-A niches, "
            "mainly for spatial water-content/saturation-related behaviour in the open twin."
        ),
        "details": [
            "The large TeamBeam ERT archive is retained as a raw ZIP and indexed member-by-member; it contains 1,675 VTK result files plus timestep/list files.",
            "The Thunderbird-recovered 2022-09-01 raw example includes a combined .tx0 file, open/closed .ohm files, and electrode-position files.",
            "Gesa's raw-file note splits the combined .tx0 measurements into #1-#2592 for the open niche and #2593-#5184 for the closed niche.",
            "The local workbook/PDF material documents the provisional water-content/resistivity relation and explicitly keeps ERT as resistivity evidence, not direct saturation.",
            "Model use requires a confirmed ERT-to-OGS coordinate transform, a support mask, an uncertainty model, and a chosen theta-to-rho relation before ERT should become an active residual.",
        ],
    },
    "nmr": {
        "title": "NMR Water Content",
        "purpose": (
            "Nuclear magnetic resonance measurements used as the most direct local water-content evidence "
            "around the CD-A open and closed niches."
        ),
        "details": [
            "Weekly 4S/4E tables provide time-series water content, confidence interval, and T2 information; columns 4 and 5 were flagged as ignorable for modelling in the email caveats.",
            "The seasonal NMR archive was extracted because it is small and contains campaign data tables plus figures for Niche 3 and Niche 4 from 2019 to 2025.",
            "Known caveats include February-April 2025 detuning/overestimation at 4E, missing winter 2024 seasonal data, and incomplete older floor/ceiling coverage.",
            "The 2025/2026 NMR presentation material documents the interlayer/bound-water uncertainty and cut-off discussion around roughly 0.5-0.6 ms.",
            "Model use should prefer within-position trends/anomalies or explicit bias/offset treatment rather than a naive raw absolute theta residual against porosity times liquid saturation.",
        ],
    },
    "taupe_tdr": {
        "title": "Taupe / TDR",
        "purpose": (
            "Taupe differential TDR evidence, with water-content/proxy behaviour by sensor and EDZ depth band."
        ),
        "details": [
            "The main workbook Taupe_WC.xlsx has sheets A3, A4, A7, and A8, each with 212 rows from 2019-12-01 to 2025-10-10.",
            "Columns summarize EDZ bands such as 0-50, 0-10, 10-20, 20-30, 30-40, and 40-50 cm from the niche wall.",
            "The 2026 ISU presentation interprets closed-twin changes as limited over more than six years and open-twin variations as strongly meteorological, especially in horizontal directions.",
            "The physical unit/calibration of the workbook values is still a gate: values may be calibrated water-content percent, apparent dielectric/ARDP proxy, or another processed Taupe quantity.",
            "The model-facing operator currently treats Taupe as baseline-normalized trend evidence rather than an absolute saturation residual.",
        ],
    },
    "suction_relative_humidity": {
        "title": "Suction / Relative Humidity",
        "purpose": (
            "Open-twin thermo-hygrometer/RH data and suction instrumentation evidence for pressure-boundary and retention-curve interpretation."
        ),
        "details": [
            "The OT_RH5-RH8 workbooks provide open-twin RH time series through 2025-09-04; RH5/RH6 are the cleanest local open-twin sensors in the current source set.",
            "RH7/RH8 contain low values near 13 percent that are treated as outliers or invalid periods, not as physical niche behaviour.",
            "The 2026 slides state that open-twin thermo-hygrometers are reliable below 95 percent RH, while closed-twin psychrometers are preferred above 95 percent RH.",
            "RH can be converted to gauge pressure through the Kelvin equation, but the active OGS boundary curve is not yet proven to be a direct reconstruction of the copied workbooks.",
            "Model use should keep RH as boundary-condition evidence until the active-curve generation source, constants, sensor screening, and extension policy are confirmed.",
        ],
    },
    "permeability_pulse_tests": {
        "title": "Permeability Pulse Tests",
        "purpose": (
            "Gas pulse-test permeability/transmissibility evidence used as direct material-parameter constraints for EDZ and anisotropy modelling."
        ),
        "details": [
            "The copied workbooks combine 2021, 2024, and 2025 interpreted permeability/transmissibility values with raw or normalized pressure-time blocks.",
            "The method notes describe a modified COMDRILL double-piston packer, 10 cm test intervals, nitrogen injection up to 1 bar, and pressure-decay monitoring.",
            "Experimental and evaluation uncertainty is documented at about half an order of magnitude.",
            "Slides summarize a strong open/closed contrast, with open-twin permeability around 1e-15 m2 and closed-twin permeability around 1e-19 m2 in the discussed material.",
            "The current model-facing use treats the observations as scalar gas-pulse intrinsic-permeability interval evidence; missing endpoint geometry still blocks several historical rows from direct OGS-cell projection.",
        ],
    },
    "other_hm_monitoring": {
        "title": "Other HM Monitoring",
        "purpose": (
            "Hydromechanical monitoring context outside the main ERT/NMR/RH/Taupe/permeability streams, including deformation, pore pressure, crackmeter, laser scan, levelling, and project-overview evidence."
        ),
        "details": [
            "The HERMES and TD material mention deformation, humidity, water content, pore water pressures, crack width, piezometers, extensometers, ERT, TDR, and laser scans.",
            "The May 2026 minutes record RH/T, extensometer data failures, functioning mini-piezometers, crackmeter trends, open/closed twin qualitative behaviour, and future planned work.",
            "The precision-levelling presentation provides 12 extracted pointwise vertical displacement values with detectable displacement around 0.1-0.2 mm at 95 percent confidence.",
            "VisualisationCDA.dat gives geometry/labels for many monitoring objects but is a layout file, not a clean time-series export.",
            "Full numeric exports for Geoscope, laser-scan statistics, and several HM streams are still separate external gates before hard residual weighting.",
        ],
    },
    "coordinates_geometry_layout": {
        "title": "Coordinates / Geometry / Layout",
        "purpose": (
            "Coordinate and layout files that place NMR, Taupe, suction/RH, permeability, ERT, and other HM evidence into the modelling frame."
        ),
        "details": [
            "Mess_Koord_XY.xlsx groups NMR, suction, Taupe, and permeability points and contains original/3D, 2D_Model x/z, and 2D_Model x/y coordinate blocks.",
            "Email context says the relevant coordinates for the current 2D modelling work are the 2D_Model x/y columns; closed-twin coordinates can be ignored for the current open-niche focus unless the scope changes.",
            "Coordinates_NMR_Taupe_characborehole.xlsx bridges NMR/Taupe/characterization borehole labels to original and BGR model coordinates.",
            "VisualisationCDA.dat contains broad Tecplot-style geometry and labels for monitoring objects, faults/fractures, open/closed twin geometry, and support features.",
            "This folder is the first stop before importing any point, line, interval, or layout measurement into the OGS mesh.",
        ],
    },
    "bedding_geology_structure": {
        "title": "Bedding / Geology / Structure",
        "purpose": (
            "Structural and bedding evidence used to interpret anisotropy, EDZ heterogeneity, fault/fracture controls, and local measurement anomalies."
        ),
        "details": [
            "The bedding-angle note records a relevant bedding angle of approximately 144 degrees.",
            "The GETE/Ziefle material describes a major bedding-parallel structure/fault zone in the open twin, including scaly clay and visible shear bands around NM 4.5.",
            "The structure orientation is recorded in the local notes as approximately 145/59, but coordinate convention must be checked before using it as a tensor orientation.",
            "The characterization paper links ERT, NMR/CCM, Taupe/TDR, permeability, suction/pore pressure, deformation, and modelling as an integrated interpretation problem.",
            "Bedding/structure should inform permeability anisotropy, local EDZ/fault-zone interpretation, and the selection or rejection of calibration points.",
        ],
    },
    "model_projection_inputs": {
        "title": "Model Projection Inputs",
        "purpose": (
            "OGS model, mesh, projection, and timestep files that are not measurements themselves but are needed to map measurements into the CDA OGS workflow."
        ),
        "details": [
            "The projection-on-mesh archive contains generate_projections.py, VTU meshes, OGS XML files, cd_a_open_niche_quad.prj, comparison.pvsm, and specifications.pptx.",
            "The README inside the projection archive records that bulk_all.vtu domain identification needs to be redone with bulk.vtu.",
            "specifications.pptx documents simulation timestep interpretation: ts_0000 is 2019-09-18, early steps cover 10-day/monthly alignment, and monthly lengths use 365.25/12 days.",
            "The April 2025 and May 2025 TeamBeam OGS model ZIPs preserve exchanged model versions and seasonal open/closed curve inputs.",
            "Use this folder to reproduce model-data projection, inspect the OGS inputs exchanged with collaborators, and align observations to output timesteps.",
        ],
    },
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def link(from_dir: Path, target: Path, label: str | None = None) -> str:
    label = label or target.name
    target_rel = os.path.relpath(target, from_dir).replace(os.sep, "/")
    if any(ch in target_rel for ch in " ()"):
        return f"[{label}](<{target_rel}>)"
    return f"[{label}]({target_rel})"


def copy_path(src: Path, dst: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def copy_catalogue() -> None:
    INFO_ROOT.mkdir(parents=True, exist_ok=True)
    for name in ROOT_INDEX_FILES:
        src = MEASUREMENTS / name
        if src.exists():
            copy_path(src, INFO_ROOT / name)
    for measurement in MEASUREMENT_DIRS:
        src_dir = MEASUREMENTS / measurement
        dst_dir = INFO_ROOT / measurement
        copy_path(src_dir / "README.md", dst_dir / "README.md")
        content_summary = src_dir / "DATA_CONTENT_SUMMARY.md"
        if content_summary.exists():
            copy_path(content_summary, dst_dir / "DATA_CONTENT_SUMMARY.md")
        for subdir in ["source_files", "derived_files"]:
            src = src_dir / subdir
            if src.exists():
                copy_path(src, dst_dir / subdir)


def copied_path_for(source_path: str) -> Path:
    path = ROOT / source_path
    parts = path.parts
    try:
        idx = parts.index("measurements")
    except ValueError:
        return path
    return ROOT.joinpath(*parts[:idx], "measurements_info", *parts[idx + 1 :])


def copied_rel_for(source_path: str) -> str:
    copied = copied_path_for(source_path)
    return rel(copied)


def build_manifest(deep_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in deep_rows:
        source_path = row.get("source_path", "")
        if not source_path:
            continue
        rows.append(
            {
                "measurement": row.get("measurement", ""),
                "copied_path": copied_rel_for(source_path),
                "source_catalogue_path": source_path,
                "filename": row.get("filename", ""),
                "kind": row.get("kind", ""),
                "extension": row.get("extension", ""),
                "size_bytes": row.get("size_bytes", ""),
                "sha1": row.get("sha1", ""),
                "raw_original_or_archive_provenance": row.get("provenance", ""),
                "searchable_extract_or_outline": copied_rel_for(row["extract_path"])
                if row.get("extract_path")
                else "",
                "zip_member_index": copied_rel_for(row["zip_member_csv"])
                if row.get("zip_member_csv")
                else "",
            }
        )
    return rows


def truncate(text: str, limit: int = 280) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def by_key(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows if row.get(key)}


def fmt_value(value: str) -> str:
    value = str(value or "").strip()
    return value if value else "not recorded"


def bullet_value(label: str, value: str) -> str:
    return f"- {label}: {fmt_value(value)}"


def section_model_entry_status(
    measurement: str,
    coverage_rows: dict[str, dict[str, str]],
    gate_rows: dict[str, dict[str, str]],
    final_rows: dict[str, dict[str, str]],
    out_dir: Path,
) -> list[str]:
    coverage = coverage_rows.get(FOLDER_TO_COVERAGE_ID.get(measurement, ""), {})
    gate = gate_rows.get(FOLDER_TO_STREAM_ID.get(measurement, ""), {})
    final = final_rows.get(FOLDER_TO_FINAL_CRITERION_ID.get(measurement, ""), {})
    if not coverage and not gate and not final:
        return []

    lines = [
        "## Current Model-Entry And Gate Status",
        "",
        "This section is generated from the current workflow audits. It records how this",
        "measurement class is allowed to enter the frozen OGS workflow today; it does not",
        "turn provisional or externally gated evidence into accepted final residuals.",
        "",
    ]
    if coverage:
        lines.extend(
            [
                "### Coverage / model-use row",
                "",
                bullet_value("Observation id", coverage.get("observation_id", "")),
                bullet_value("Coverage status", coverage.get("coverage_status", "")),
                bullet_value("Current model use", coverage.get("current_model_use", "")),
                bullet_value("Raw or processed rows", coverage.get("raw_or_processed_rows", "")),
                bullet_value("Target rows", coverage.get("target_rows", "")),
                bullet_value("Mapped or usable rows", coverage.get("mapped_or_usable_rows", "")),
                bullet_value("Active objective rows", coverage.get("active_objective_rows", "")),
                bullet_value("Active objective value", coverage.get("active_objective_value", "")),
                bullet_value("Blocking next step", coverage.get("blocking_next_step", "")),
                bullet_value("Audit detail", coverage.get("audit_detail", "")),
                "",
            ]
        )
    if gate:
        lines.extend(
            [
                "### Stream activation gate row",
                "",
                bullet_value("Stream", gate.get("stream", "")),
                bullet_value("Promotion decision", gate.get("promotion_decision", "")),
                bullet_value("Current model role", gate.get("current_model_role", "")),
                bullet_value("Gate counts", f"{gate.get('pass_count', '0')} pass / {gate.get('warn_count', '0')} warn / {gate.get('fail_count', '0')} fail"),
                bullet_value("Hard blockers", gate.get("hard_blockers", "")),
                bullet_value("Tracked caveats", gate.get("tracked_caveats", "")),
                bullet_value("Next action", gate.get("next_action", "")),
                "",
            ]
        )
    if final:
        lines.extend(
            [
                "### Final-objective decision row",
                "",
                bullet_value("Criterion", final.get("criterion_id", "")),
                bullet_value("Criterion status", final.get("criterion_status", "")),
                bullet_value("Decision status", final.get("decision_status", "")),
                bullet_value("Default current decision", final.get("default_current_decision", "")),
                bullet_value("Current allowed use", final.get("current_allowed_use", "")),
                bullet_value("Decision choices", final.get("decision_choices", "")),
                bullet_value("Acceptance evidence", final.get("acceptance_evidence", "")),
                bullet_value("Report wording requirement", final.get("report_wording_requirement", "")),
                "",
            ]
        )
    lines.extend(
        [
            "### Workflow audit links",
            "",
            f"- {link(out_dir, INVERSION / 'measurement_operator_coverage.md', 'measurement_operator_coverage.md')}",
            f"- {link(out_dir, INVERSION / 'measurement_stream_activation_gate_audit.md', 'measurement_stream_activation_gate_audit.md')}",
            f"- {link(out_dir, INVERSION / 'final_objective_decision_register.md', 'final_objective_decision_register.md')}",
            f"- {link(out_dir, INVERSION / 'frozen_model_measurement_inclusion_audit.md', 'frozen_model_measurement_inclusion_audit.md')}",
            "",
        ]
    )
    return lines


def provenance_items(provenance: str) -> list[str]:
    archives: Counter[str] = Counter()
    ordinary: list[str] = []
    for item in (provenance or "").split(";"):
        item = item.strip()
        if not item:
            continue
        if item.startswith("archive member "):
            archive_and_member = item.removeprefix("archive member ").strip()
            archive = archive_and_member.split("::", 1)[0]
            archives[archive] += 1
        else:
            ordinary.append(item)
    grouped = [f"archive {archive} ({count} indexed member{'s' if count != 1 else ''})" for archive, count in sorted(archives.items())]
    return grouped + list(dict.fromkeys(ordinary))


def provenance_display(provenance: str, limit: int = 240) -> str:
    items = provenance_items(provenance)
    if not items:
        return "not identified beyond copied catalogue source"
    return truncate("; ".join(items), limit)


def source_location_items(row: dict[str, str]) -> list[str]:
    if row.get("kind") == "zip" and row.get("members"):
        for item in provenance_items(row.get("provenance", "")):
            if item.startswith("archive "):
                archive = item.removeprefix("archive ").split(" (", 1)[0]
                return [f"{archive} ({row['members']} ZIP members indexed)"]
    return provenance_items(row.get("provenance", ""))


def section_file_inventory(measurement: str, rows: list[dict[str, str]], out_dir: Path) -> list[str]:
    lines = [
        "## Copied Source Files",
        "",
        "| File | Type | Size | Raw/original location | Searchable extract |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in rows:
        copied = copied_path_for(row["source_path"])
        extract = copied_path_for(row["extract_path"]) if row.get("extract_path") else None
        provenance_items_for_row = source_location_items(row)
        provenance = (
            truncate("; ".join(provenance_items_for_row), 240)
            if provenance_items_for_row
            else "not identified beyond copied catalogue source"
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    link(out_dir, copied, row.get("filename", copied.name)),
                    f"`{row.get('kind') or row.get('extension')}`",
                    str(row.get("size_bytes", "")),
                    provenance.replace("|", "\\|"),
                    link(out_dir, extract, "extract/outline") if extract else "",
                ]
            )
            + " |"
        )
    lines.append("")
    lines.append(
        "The copied files above are local working copies in this `measurements_info` folder. "
        "The raw/original location column points back to the Gmail attachment, Thunderbird-recovered file, "
        "TeamBeam transfer, or archive-member provenance where available."
    )
    lines.append("")
    return lines


def section_workbooks(measurement: str, workbook_rows: list[dict[str, str]], out_dir: Path) -> list[str]:
    rows = [row for row in workbook_rows if row.get("measurement") == measurement]
    if not rows:
        return []
    lines = [
        "## Workbook Sheet Details",
        "",
        "| Workbook | Sheet | Rows x Cols | Non-empty cells | Date range | Numeric ranges / headers |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        workbook = copied_path_for(row["workbook"])
        dims = f"{row.get('max_row', '')} x {row.get('max_column', '')}"
        summary = row.get("numeric_summary") or row.get("first_non_empty_values") or ""
        lines.append(
            "| "
            + " | ".join(
                [
                    link(out_dir, workbook, Path(row["workbook"]).name),
                    row.get("sheet", "").replace("|", "\\|"),
                    dims,
                    row.get("non_empty_cells", ""),
                    truncate(row.get("date_range", ""), 150).replace("|", "\\|"),
                    truncate(summary, 260).replace("|", "\\|"),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def section_archives(measurement: str, rows: list[dict[str, str]], out_dir: Path) -> list[str]:
    zip_rows = [row for row in rows if row.get("kind") == "zip"]
    if not zip_rows:
        return []
    lines = ["## ZIP / Archive Pass", ""]
    for row in zip_rows:
        copied = copied_path_for(row["source_path"])
        member_csv = copied_path_for(row["zip_member_csv"]) if row.get("zip_member_csv") else None
        lines.extend(
            [
                f"### {row.get('filename', copied.name)}",
                "",
                f"- Copied archive: {link(out_dir, copied)}",
                f"- Members indexed in this pass: {row.get('members', '')}",
                f"- Total uncompressed bytes recorded: {row.get('total_uncompressed_bytes', '')}",
                f"- Extension counts: {row.get('extension_counts', '') or 'not recorded'}",
            ]
        )
        if member_csv:
            lines.append(f"- Per-member index: {link(out_dir, member_csv)}")
        if row.get("first_lines"):
            lines.append(f"- First/interesting members: {truncate(row['first_lines'], 700)}")
        if row.get("potential_missing_loose_members"):
            lines.append(
                f"- Potential members without loose copies: {truncate(row['potential_missing_loose_members'], 500)}"
            )
        else:
            lines.append("- Office/data/image members from this archive have same-name loose source copies somewhere in the measurement catalogue, where appropriate.")
        lines.append("")
    return lines


def section_extracted_text(measurement: str, rows: list[dict[str, str]], out_dir: Path) -> list[str]:
    extract_rows = [row for row in rows if row.get("extract_path")]
    if not extract_rows:
        return []
    by_kind = Counter(row.get("kind", "") for row in extract_rows)
    lines = [
        "## Searchable Extracts And Outlines",
        "",
        "Copied `derived_files/deep_source_pass/extracted_text/` material gives quick text access to PDFs, PPTX decks, workbook outlines, and raw text/data headers.",
        "",
        "Extract counts: "
        + ", ".join(f"`{kind}`={count}" for kind, count in sorted(by_kind.items())),
        "",
    ]
    return lines


def build_measurement_info(
    measurement: str,
    rows_by_measurement: dict[str, list[dict[str, str]]],
    workbook_rows: list[dict[str, str]],
    coverage_rows: dict[str, dict[str, str]],
    gate_rows: dict[str, dict[str, str]],
    final_rows: dict[str, dict[str, str]],
) -> None:
    out_dir = INFO_ROOT / measurement
    rows = rows_by_measurement.get(measurement, [])
    note = MEASUREMENT_NOTES[measurement]
    kind_counts = Counter(row.get("kind", "") for row in rows)
    total_bytes = sum(int(row.get("size_bytes") or 0) for row in rows)
    raw_locations = sorted(
        {item for row in rows for item in source_location_items(row)}
    )
    lines: list[str] = [
        f"# {note['title']} Measurement Info",
        "",
        str(note["purpose"]),
        "",
        "This folder was generated as a measurement-info mirror from the curated CD-A measurement catalogue. "
        "It contains copied source files, copied derived/extracted indexes, and this detailed orientation note.",
        "",
        "## At A Glance",
        "",
        f"- Measurement folder: `{measurement}`",
        f"- Source/data/info files copied here: {len(rows)}",
        f"- Total copied source-file bytes: {total_bytes}",
        "- File kind counts: "
        + ", ".join(f"`{kind}`={count}" for kind, count in sorted(kind_counts.items())),
        f"- Original curated README copied here: {link(out_dir, out_dir / 'README.md', 'README.md')}",
        f"- Deep-source per-file summary copied here: {link(out_dir, out_dir / 'derived_files/deep_source_pass/source_file_deep_summary.md', 'source_file_deep_summary.md')}"
        if (out_dir / "derived_files/deep_source_pass/source_file_deep_summary.md").exists()
        else "- Deep-source per-file summary: not present for this folder",
        f"- Data-content deep-dive summary copied here: {link(out_dir, out_dir / 'DATA_CONTENT_SUMMARY.md', 'DATA_CONTENT_SUMMARY.md')}"
        if (out_dir / "DATA_CONTENT_SUMMARY.md").exists()
        else "- Data-content deep-dive summary: not present for this folder",
        "",
        "## Measurement Interpretation Notes",
        "",
    ]
    for detail in note["details"]:  # type: ignore[index]
        lines.append(f"- {detail}")
    lines.append("")
    lines.extend(section_model_entry_status(measurement, coverage_rows, gate_rows, final_rows, out_dir))
    lines.extend(section_file_inventory(measurement, rows, out_dir))
    lines.extend(section_workbooks(measurement, workbook_rows, out_dir))
    lines.extend(section_archives(measurement, rows, out_dir))
    lines.extend(section_extracted_text(measurement, rows, out_dir))
    lines.extend(
        [
            "## Raw / Original Provenance Links",
            "",
        ]
    )
    if raw_locations:
        for loc in raw_locations:
            lines.append(f"- `{loc}`")
    else:
        lines.append("- No provenance beyond the copied catalogue path was recorded.")
    lines.extend(
        [
            "",
            "## Orientation",
            "",
            "Use `source_files/` for the copied raw or near-raw material, `derived_files/` for generated source extracts and model-facing audits, and the tables above to jump from a measurement stream to the exact file, sheet, ZIP member index, or extracted text where the original information can be checked.",
            "",
        ]
    )
    write_text(out_dir / "MEASUREMENT_INFO.md", "\n".join(lines))


def build_root_readme(manifest_rows: list[dict[str, Any]]) -> None:
    by_measurement = Counter(row["measurement"] for row in manifest_rows)
    by_kind = Counter(row["kind"] for row in manifest_rows)
    lines = [
        "# CD-A Measurement Info Mirror",
        "",
        f"Generated: {date.today().isoformat()}.",
        "",
        "This folder is the requested measurement-info workspace. It mirrors the curated source material from `cda_knowledge_base/measurements` into one navigation tree for detailed reading and modelling orientation.",
        "",
        "Each measurement-type subfolder contains:",
        "",
        "- `source_files/`: copied files with raw data, source workbooks, presentations, PDFs, figures, archives, model/projection files, or layout information.",
        "- `derived_files/`: copied generated extracts, workbook outlines, ZIP-member indexes, and model-facing audit products where available.",
        "- `README.md`: the existing curated measurement narrative copied from the main catalogue.",
        "- `MEASUREMENT_INFO.md`: the detailed inventory generated for this mirror, with links to copied files, raw/original provenance, and current model-entry/gate status from the workflow audits.",
        "- `DATA_CONTENT_SUMMARY.md`: second-pass mined facts from the actual copied workbooks, raw tables, ZIP members, and document extracts.",
        "",
        "Top-level indexes copied/generated here:",
        "",
        "- [measurement_info_manifest.csv](measurement_info_manifest.csv): all copied source files with original catalogue and raw provenance links.",
        "- [archive_inventory.md](archive_inventory.md): human-readable ZIP/archive pass.",
        "- [archive_member_catalog.csv](archive_member_catalog.csv): row-level archive member index.",
        "- [deep_source_index.md](deep_source_index.md): deep-source extraction summary.",
        "- [deep_source_index.csv](deep_source_index.csv): machine-readable per-file deep-source index.",
        "- [measurement_content_deep_dive.md](measurement_content_deep_dive.md): measurement-oriented mined content summary across all measurement folders.",
        "- [measurement_content_deep_dive.csv](measurement_content_deep_dive.csv): machine-readable mined fact rows.",
        "- [workbook_sheet_deep_index.csv](workbook_sheet_deep_index.csv): workbook sheet outlines and numeric/date summaries.",
        "- [catalog_verification.md](catalog_verification.md): completeness check against Gmail, Thunderbird, TeamBeam, and workspace sources.",
        "",
        "## Measurement Type Folders",
        "",
        "| Folder | Files | Main note |",
        "| --- | ---: | --- |",
    ]
    for measurement in MEASUREMENT_DIRS:
        out_dir = INFO_ROOT / measurement
        title = str(MEASUREMENT_NOTES[measurement]["title"])
        lines.append(
            f"| {link(INFO_ROOT, out_dir, title)} | {by_measurement.get(measurement, 0)} | {link(INFO_ROOT, out_dir / 'MEASUREMENT_INFO.md', 'MEASUREMENT_INFO.md')} |"
        )
    lines.extend(
        [
            "",
            "## Coverage Snapshot",
            "",
            f"- Measurement/source files copied and indexed: {len(manifest_rows)}.",
            "- File kind counts: "
            + ", ".join(f"`{kind}`={count}" for kind, count in sorted(by_kind.items())),
            "- The ZIP/archive pass covers the known Gmail, Thunderbird-recovered, TeamBeam, and workspace ZIPs in `archive_member_catalog.csv`.",
            "- The large ERT VTK archive remains as a copied raw ZIP and is indexed row by row rather than exploded into another loose 925 MB VTK tree.",
            "",
            "The original collection locations remain under `cda_knowledge_base/attachments`, `cda_knowledge_base/attachments/thunderbird_recovered`, and `cda_knowledge_base/file_transfers/collected`.",
            "",
        ]
    )
    write_text(INFO_ROOT / "README.md", "\n".join(lines))


def main() -> None:
    deep_rows = read_csv(MEASUREMENTS / "deep_source_index.csv")
    workbook_rows = read_csv(MEASUREMENTS / "workbook_sheet_deep_index.csv")
    coverage_rows = by_key(read_csv(INVERSION / "measurement_operator_coverage.csv"), "observation_id")
    gate_rows = by_key(read_csv(INVERSION / "measurement_stream_activation_gate_audit.csv"), "stream")
    final_rows = by_key(read_csv(INVERSION / "final_objective_decision_register.csv"), "criterion_id")
    if not deep_rows:
        raise SystemExit("Missing deep_source_index.csv; run build_measurement_deep_source_index.py first.")

    copy_catalogue()

    rows_by_measurement: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in deep_rows:
        measurement = row.get("measurement", "")
        if measurement in MEASUREMENT_DIRS:
            rows_by_measurement[measurement].append(row)

    manifest_rows = build_manifest(
        [row for rows in rows_by_measurement.values() for row in rows]
    )
    write_csv(
        INFO_ROOT / "measurement_info_manifest.csv",
        manifest_rows,
        [
            "measurement",
            "copied_path",
            "source_catalogue_path",
            "filename",
            "kind",
            "extension",
            "size_bytes",
            "sha1",
            "raw_original_or_archive_provenance",
            "searchable_extract_or_outline",
            "zip_member_index",
        ],
    )
    for measurement in MEASUREMENT_DIRS:
        build_measurement_info(measurement, rows_by_measurement, workbook_rows, coverage_rows, gate_rows, final_rows)
    build_root_readme(manifest_rows)

    print(
        {
            "measurements_info_root": rel(INFO_ROOT),
            "measurement_folders": MEASUREMENT_DIRS,
            "copied_source_rows": len(manifest_rows),
            "manifest": rel(INFO_ROOT / "measurement_info_manifest.csv"),
        }
    )


if __name__ == "__main__":
    main()
