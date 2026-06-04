#!/usr/bin/env python3
"""Build structured inventory tables for secondary CD-A HM monitoring sources."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd


FLOAT_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("inversion_workflow/observation_manifest.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
    )
    return parser.parse_args()


def resolve_path(base: Path, rel: str | Path) -> Path:
    path = Path(rel)
    if path.is_absolute():
        return path
    return (base / path).resolve()


def relative_to_repo(path: Path, repo_root: Path) -> str:
    path = path.resolve()
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def read_manifest(manifest_path: Path) -> tuple[Path, Path]:
    manifest_path = manifest_path.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    data_root = resolve_path(manifest_path.parent, manifest["data_root"])
    repo_root = manifest_path.parents[2]
    return data_root, repo_root


def classify_zone(name: str) -> tuple[str, str, str]:
    token = name.lower().replace(" ", "_")
    if token.startswith("mini_piezo"):
        return (
            "mini_piezometer",
            "pore-pressure validation",
            "liquid pore pressure or hydraulic head trend",
        )
    if token.startswith("ext") or "extensometer" in token:
        return (
            "extensometer",
            "mechanical validation",
            "displacement or strain trend",
        )
    if token.startswith("kluft"):
        return (
            "fracture_or_crack_geometry",
            "structural/deformation support",
            "crack or fracture aperture/geometry context",
        )
    if token.startswith("konvergenz"):
        return (
            "convergence_points",
            "mechanical validation",
            "niche convergence displacement trend",
        )
    if token.startswith("miniprisma"):
        return (
            "miniprisma_geodesy",
            "geodetic deformation validation",
            "3D point displacement trend",
        )
    if token in {"ltm1", "ltm2", "agi1"}:
        return (
            "laser_scan_geodetic_support",
            "laser/scan registration support",
            "survey target geometry",
        )
    if token.endswith("_ls"):
        return (
            "laser_scan_surface",
            "mechanical validation",
            "niche surface displacement or scan-difference field",
        )
    if token.startswith("evapometer"):
        return (
            "evapometer",
            "boundary-condition context",
            "evaporation/climate disturbance proxy",
        )
    if token.startswith("taupe"):
        return (
            "taupe_tdr_support",
            "water-content trend support",
            "Taupe/TDR borehole layout",
        )
    if token.startswith("nmr"):
        return (
            "nmr_support",
            "water-content point support",
            "NMR station/measurement layout",
        )
    if token.startswith("rh"):
        return (
            "rh_suction_support",
            "hydraulic boundary/pressure support",
            "relative humidity or suction sensor layout",
        )
    if token.startswith("permeability"):
        return (
            "permeability_support",
            "parameter-observation support",
            "pulse-test borehole or measurement layout",
        )
    if token.startswith("mg_") or "twin" in token:
        return (
            "niche_geometry",
            "geometric support",
            "open/closed niche or model-geometry surface",
        )
    return (
        "layout_geometry",
        "geometric support",
        "Tecplot layout geometry",
    )


def parse_int_from_line(pattern: str, line: str) -> int | None:
    match = re.search(pattern, line, re.IGNORECASE)
    return int(match.group(1)) if match else None


def parse_value_from_line(pattern: str, line: str) -> str:
    match = re.search(pattern, line, re.IGNORECASE)
    return match.group(1) if match else ""


def init_stats() -> dict[str, float]:
    return {
        "min": math.inf,
        "max": -math.inf,
        "sum": 0.0,
    }


def update_stats(stats: dict[str, float], value: float) -> None:
    stats["min"] = min(stats["min"], value)
    stats["max"] = max(stats["max"], value)
    stats["sum"] += value


def finite_or_nan(value: float) -> float:
    return value if math.isfinite(value) else math.nan


def parse_visualisation_zones(path: Path, repo_root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    header_lines: list[str] = []
    coordinate_index = 0

    def finish_current() -> None:
        nonlocal current, coordinate_index
        if current is None:
            return
        nodes = int(current["nodes"] or 0)
        x_stats = current["x_stats"]
        y_stats = current["y_stats"]
        z_stats = current["z_stats"]
        measurement_type, model_role, model_quantity = classify_zone(str(current["zone_name"]))
        rows.append(
            {
                "source_file": relative_to_repo(path, repo_root),
                "zone_name": current["zone_name"],
                "measurement_type": measurement_type,
                "model_role": model_role,
                "model_quantity": model_quantity,
                "nodes": nodes,
                "elements": int(current["elements"] or 0),
                "zonetype": current["zonetype"],
                "datapacking": current["datapacking"],
                "coordinate_values_read": int(current["coordinate_values_read"]),
                "coordinate_complete": bool(current["coordinate_values_read"] == nodes * 3),
                "x_min": finite_or_nan(x_stats["min"]),
                "x_max": finite_or_nan(x_stats["max"]),
                "x_mean": x_stats["sum"] / nodes if nodes else math.nan,
                "y_min": finite_or_nan(y_stats["min"]),
                "y_max": finite_or_nan(y_stats["max"]),
                "y_mean": y_stats["sum"] / nodes if nodes else math.nan,
                "z_min": finite_or_nan(z_stats["min"]),
                "z_max": finite_or_nan(z_stats["max"]),
                "z_mean": z_stats["sum"] / nodes if nodes else math.nan,
            }
        )
        current = None
        coordinate_index = 0

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.startswith("ZONE T="):
                if current is not None:
                    finish_current()
                current = {
                    "zone_name": parse_value_from_line(r'ZONE\s+T="([^"]+)"', stripped),
                    "nodes": None,
                    "elements": None,
                    "zonetype": "",
                    "datapacking": "",
                    "x_stats": init_stats(),
                    "y_stats": init_stats(),
                    "z_stats": init_stats(),
                    "coordinate_values_read": 0,
                    "reading_header": True,
                }
                header_lines = [stripped]
                coordinate_index = 0
                continue

            if current is None:
                continue

            if current["reading_header"]:
                header_lines.append(stripped)
                nodes = parse_int_from_line(r"Nodes\s*=\s*(\d+)", stripped)
                elements = parse_int_from_line(r"Elements\s*=\s*(\d+)", stripped)
                if nodes is not None:
                    current["nodes"] = nodes
                if elements is not None:
                    current["elements"] = elements
                zonetype = parse_value_from_line(r"ZONETYPE\s*=\s*([A-Za-z0-9_]+)", stripped)
                datapacking = parse_value_from_line(r"DATAPACKING\s*=\s*([A-Za-z0-9_]+)", stripped)
                if zonetype:
                    current["zonetype"] = zonetype
                if datapacking:
                    current["datapacking"] = datapacking
                if stripped.startswith("DT="):
                    current["reading_header"] = False
                continue

            nodes = int(current["nodes"] or 0)
            total_needed = nodes * 3
            if coordinate_index >= total_needed:
                continue

            for match in FLOAT_RE.finditer(stripped):
                if coordinate_index >= total_needed:
                    finish_current()
                    break
                value = float(match.group(0))
                variable_index = coordinate_index // nodes if nodes else 0
                if variable_index == 0:
                    update_stats(current["x_stats"], value)
                elif variable_index == 1:
                    update_stats(current["y_stats"], value)
                else:
                    update_stats(current["z_stats"], value)
                coordinate_index += 1
                current["coordinate_values_read"] = coordinate_index
                if coordinate_index >= total_needed:
                    finish_current()
                    break

    if current is not None:
        finish_current()
    return pd.DataFrame(rows)


def parse_visualisation_text_labels(path: Path, repo_root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    def finish_text() -> None:
        nonlocal current
        if current and current.get("label"):
            rows.append(
                {
                    "source_file": relative_to_repo(path, repo_root),
                    "label": current.get("label", ""),
                    "frame_x": current.get("frame_x", math.nan),
                    "frame_y": current.get("frame_y", math.nan),
                }
            )
        current = None

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped == "TEXT":
                finish_text()
                current = {}
                continue
            if stripped.startswith("ZONE T="):
                finish_text()
                break
            if current is None:
                continue
            xy_match = re.search(r"X=([^,]+),Y=([^,\s]+)", stripped)
            if xy_match:
                current["frame_x"] = float(xy_match.group(1))
                current["frame_y"] = float(xy_match.group(2))
            label_match = re.search(r'T="([^"]+)"', stripped)
            if label_match:
                current["label"] = label_match.group(1)
    finish_text()
    return pd.DataFrame(rows)


def build_levelling_targets(repo_root: Path) -> pd.DataFrame:
    source = Path(
        "cda_knowledge_base/measurements/other_hm_monitoring/source_files/"
        "Folien_Niv_TD_CDA_2026.pdf"
    )
    rows = [
        ("57", "Galerie 18", -0.1),
        ("58", "Galerie 18", 0.3),
        ("CDA-C1", "Closed Twin", 0.6),
        ("CDA-C2", "Closed Twin", 0.8),
        ("CDA-C3", "Closed Twin", 0.6),
        ("CDA-C4", "Closed Twin", 1.3),
        ("CDA-C5", "Closed Twin", 0.5),
        ("CDA-O1", "Open Twin", -2.1),
        ("CDA-O2", "Open Twin", 0.2),
        ("CDA-O3", "Open Twin", 0.4),
        ("CDA-O4", "Open Twin", 0.4),
        ("CDA-O5", "Open Twin", 0.9),
    ]
    return pd.DataFrame(
        [
            {
                "source_file": source.as_posix(),
                "source_page": 5,
                "campaign_reference": "initial measurement 2022-08-29/30 to 2026-03 campaign",
                "point_name": point,
                "location": location,
                "height_difference_mm": value,
                "detectable_displacement_mm": "0.1-0.2 at 95% confidence, point-dependent",
                "model_quantity": "vertical displacement",
                "validation_role": "numeric deformation validation; compare sign and order of magnitude after model geometry/output support is confirmed",
            }
            for point, location, value in rows
        ]
    )


def build_qualitative_targets(repo_root: Path) -> pd.DataFrame:
    minutes = (
        "cda_knowledge_base/measurements/other_hm_monitoring/source_files/"
        "2026-05-11_TD517_CD-A_260507__Minutes.pdf"
    )
    modelling = (
        "cda_knowledge_base/measurements/other_hm_monitoring/source_files/"
        "CD-A_TD_2026_sc.pdf"
    )
    hermes = (
        "cda_knowledge_base/measurements/other_hm_monitoring/source_files/"
        "2024-12-19_Input_HERMES_BGR_20241217.pdf"
    )
    return pd.DataFrame(
        [
            {
                "target_id": "geoscope_update_scope_2026_04_20",
                "source_file": minutes,
                "source_page": 3,
                "measurement_type": "multi_stream_geoscope_and_laser",
                "observation": "Geoscope update covers RH, temperature, door opening times, extensometer, mini-piezometer, crackmeter, suction; laser scans with statistical interpretation were also sent.",
                "model_quantity": "boundary forcing, displacement, pressure and deformation context",
                "model_use": "Inventory check: these raw time series/statistical laser products are still needed before hard residuals can be formed.",
                "readiness": "source_mentions_numeric_streams_raw_series_not_in_catalogue",
            },
            {
                "target_id": "closed_extensometer_failure_since_2025_09",
                "source_file": minutes,
                "source_page": 3,
                "measurement_type": "extensometer",
                "observation": "Horizontal and vertical extensometers BCD-A9 and BCD-A10 in the closed niche failed since September 2025.",
                "model_quantity": "displacement/strain",
                "model_use": "Do not treat closed-niche extensometer data after September 2025 as an unqualified calibration target.",
                "readiness": "maintenance_caveat_structured",
            },
            {
                "target_id": "mini_piezometers_working_well_2026",
                "source_file": minutes,
                "source_page": 3,
                "measurement_type": "mini_piezometer",
                "observation": "Mini-piezometers BCD-A28 to BCD-A31 were reported as working well.",
                "model_quantity": "pore pressure",
                "model_use": "Good candidates for future pressure residuals once the Geoscope numeric time series are located.",
                "readiness": "instrument_status_ready_numeric_series_missing",
            },
            {
                "target_id": "crackmeter_closed_trend_open_seasonal",
                "source_file": minutes,
                "source_page": 3,
                "measurement_type": "crackmeter",
                "observation": "Crackmeter data indicate an ongoing trend at one closed-niche measuring point and seasonal variation in the open niche.",
                "model_quantity": "crack aperture or local displacement",
                "model_use": "Use as a qualitative deformation sanity check until crackmeter series are collected.",
                "readiness": "qualitative_trend_ready_numeric_series_missing",
            },
            {
                "target_id": "open_twin_ongoing_trend_2026",
                "source_file": minutes,
                "source_page": 7,
                "measurement_type": "multi_stream_open_twin",
                "observation": "Open twin shows ongoing trend in extensometer, suction and Taupe measurements; no experimental adjustments were planned.",
                "model_quantity": "coupled hydraulic/deformation trend",
                "model_use": "The model should not predict a fully static open twin over the same period.",
                "readiness": "qualitative_validation_gate_ready",
            },
            {
                "target_id": "closed_twin_mostly_static_with_crack_closure",
                "source_file": minutes,
                "source_page": 7,
                "measurement_type": "multi_stream_closed_twin",
                "observation": "Closed twin is mostly static in extensometer, pore-pressure and suction observations, except one crackmeter position indicating ongoing crack closure.",
                "model_quantity": "pressure, suction and deformation trend",
                "model_use": "The model should preserve the open/closed twin contrast and should not force broad closed-twin transient deformation where observations are static.",
                "readiness": "qualitative_validation_gate_ready",
            },
            {
                "target_id": "levelling_cda_o1_settlement_c4_heave",
                "source_file": "cda_knowledge_base/measurements/other_hm_monitoring/source_files/Folien_Niv_TD_CDA_2026.pdf",
                "source_page": 6,
                "measurement_type": "precision_levelling",
                "observation": "Largest levelling deformations are CDA-O1 -2.1 mm settlement and CDA-C4 +1.3 mm heave/uplift; most other points tend toward uplift.",
                "model_quantity": "vertical displacement",
                "model_use": "Numeric levelling rows are extracted separately; use as deformation validation after matching the survey reference frame to OGS displacement output.",
                "readiness": "numeric_summary_rows_extracted_reference_frame_pending",
            },
            {
                "target_id": "bgr_edf_next_measurement_focus",
                "source_file": modelling,
                "source_page": 2,
                "measurement_type": "modelling_validation_scope",
                "observation": "BGR-EDF comparison focus is displacements/strains from extensometers, pore pressure from mini-piezometers, and pore pressure in the desaturated zone from suction.",
                "model_quantity": "displacement/strain and pore pressure",
                "model_use": "Defines the priority order for future HM observation operators beyond permeability, NMR, ERT, Taupe and RH.",
                "readiness": "operator_scope_ready_numeric_series_missing",
            },
            {
                "target_id": "perfect_ring_strain_discrepancy",
                "source_file": modelling,
                "source_page": 15,
                "measurement_type": "extensometer_model_comparison",
                "observation": "The simplified perfect-ring 2D model produced simulated strain discrepancies versus extensometer measurements.",
                "model_quantity": "strain",
                "model_use": "Use as a warning that simplified geometry/constitutive choices can fail mechanical validation even if hydraulic fits look plausible.",
                "readiness": "qualitative_model_caveat_ready",
            },
            {
                "target_id": "hermes_available_monitoring_scope",
                "source_file": hermes,
                "source_page": 5,
                "measurement_type": "long_term_monitoring_scope",
                "observation": "BGR reports access to long-term deformation, humidity, water content, pore-water pressure, crack-width, piezometer/extensometer, ERT, TDR and laser-scan measurements.",
                "model_quantity": "multi-physics validation data",
                "model_use": "Confirms that the catalogue should keep seeking Geoscope and laser-scan raw exports, not just the water-content and permeability files already normalized.",
                "readiness": "scope_documented_raw_exports_partly_missing",
            },
        ]
    )


def write_markdown(
    path: Path,
    zones: pd.DataFrame,
    labels: pd.DataFrame,
    levelling: pd.DataFrame,
    targets: pd.DataFrame,
    summary: dict[str, Any],
) -> None:
    zone_counts = zones["measurement_type"].value_counts().sort_index().to_dict()
    lines = [
        "# Other HM Monitoring Inventory",
        "",
        "This inventory structures the secondary CD-A hydromechanical monitoring material",
        "that is present as meeting reports, presentations and the Tecplot layout.",
        "",
        "## Generated Tables",
        "",
        "| File | Rows | Contents |",
        "| --- | ---: | --- |",
        f"| `other_hm_visualisation_zones.csv` | {len(zones)} | Tecplot zones from `VisualisationCDA.dat`, classified by measurement/support role and coordinate bounds. |",
        f"| `other_hm_visualisation_text_labels.csv` | {len(labels)} | Display labels from the Tecplot layout legend. |",
        f"| `other_hm_levelling_displacements.csv` | {len(levelling)} | Pointwise vertical displacement values from the precision-levelling slides. |",
        f"| `other_hm_qualitative_targets.csv` | {len(targets)} | Structured HM validation statements from the 2026 minutes, modelling slides and HERMES input note. |",
        f"| `other_hm_monitoring_summary.json` | 1 | Machine-readable counts and readiness status. |",
        "",
        "## Layout Content",
        "",
        f"- Tecplot zones parsed: {summary['zone_rows']}.",
        f"- Layout labels parsed: {summary['text_label_rows']}.",
        f"- Largest zone by nodes: `{summary['largest_zone_by_nodes']['zone_name']}` with {summary['largest_zone_by_nodes']['nodes']:,} nodes.",
        "",
        "| Classified role | Zones |",
        "| --- | ---: |",
    ]
    for key, value in zone_counts.items():
        lines.append(f"| `{key}` | {int(value)} |")

    levelling_sorted = levelling.sort_values("height_difference_mm")
    lines.extend(
        [
            "",
            "## Numeric Levelling Summary",
            "",
            "The levelling slides provide the only pointwise numeric deformation values in",
            "this secondary-HM bundle. Values are height differences from the first",
            "measurement on 2022-08-29/30 to the 2026-03 campaign.",
            "",
            "| Point | Location | Height difference [mm] |",
            "| --- | --- | ---: |",
        ]
    )
    for _, row in levelling_sorted.iterrows():
        lines.append(
            f"| `{row['point_name']}` | {row['location']} | {row['height_difference_mm']:.1f} |"
        )

    lines.extend(
        [
            "",
            "## Model-Entry Status",
            "",
            "- Mini-piezometers are the cleanest future pressure residual candidates, but",
            "  the Geoscope numeric series are not in the currently collected files.",
            "- Extensometer and crackmeter information is currently trend/status evidence;",
            "  the closed-niche BCD-A9/A10 extensometer failure since September 2025 must",
            "  be respected before using those records.",
            "- Levelling values can become displacement-validation targets after the survey",
            "  reference frame and OGS displacement output support are aligned.",
            "- Laser-scan objects are present in the Tecplot layout, but the statistical",
            "  laser-scan update mentioned in the minutes is not present as a raw data",
            "  export in this catalogue.",
            "",
            "## Immediate Missing Raw Exports",
            "",
            "- Geoscope time series for mini-piezometers BCD-A28 to BCD-A31.",
            "- Geoscope extensometer and crackmeter time series, including instrument-status",
            "  metadata around the September 2025 closed-niche failure.",
            "- Laser-scan statistical interpretation files from the 2026-04-20 update.",
            "- A table/spreadsheet version of the levelling survey if residual weighting",
            "  beyond the slide-summary values is needed.",
            "",
            "Run `build_other_hm_missing_numeric_request.py` to turn this list into an",
            "email-ready request package with requested fields, source evidence, and",
            "catalogue copies.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    data_root, repo_root = read_manifest(args.manifest)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    visualisation = data_root / "other_hm_monitoring" / "source_files" / "VisualisationCDA.dat"
    zones = parse_visualisation_zones(visualisation, repo_root)
    labels = parse_visualisation_text_labels(visualisation, repo_root)
    levelling = build_levelling_targets(repo_root)
    targets = build_qualitative_targets(repo_root)

    outputs = {
        "other_hm_visualisation_zones.csv": zones,
        "other_hm_visualisation_text_labels.csv": labels,
        "other_hm_levelling_displacements.csv": levelling,
        "other_hm_qualitative_targets.csv": targets,
    }
    for name, frame in outputs.items():
        frame.to_csv(output_dir / name, index=False)

    largest = zones.sort_values("nodes", ascending=False).iloc[0].to_dict() if not zones.empty else {}
    summary = {
        "status": "layout_and_qualitative_targets_ready_numeric_series_missing",
        "zone_rows": int(zones.shape[0]),
        "text_label_rows": int(labels.shape[0]),
        "levelling_rows": int(levelling.shape[0]),
        "qualitative_target_rows": int(targets.shape[0]),
        "model_facing_rows": int(levelling.shape[0] + targets.shape[0]),
        "zone_counts_by_measurement_type": {
            str(key): int(value)
            for key, value in zones["measurement_type"].value_counts().sort_index().to_dict().items()
        },
        "largest_zone_by_nodes": {
            "zone_name": str(largest.get("zone_name", "")),
            "measurement_type": str(largest.get("measurement_type", "")),
            "nodes": int(largest.get("nodes", 0) or 0),
            "elements": int(largest.get("elements", 0) or 0),
        },
        "active_objective_rows": 0,
        "remaining_blocker": (
            "Locate Geoscope mini-piezometer/extensometer/crackmeter time-series "
            "exports and laser-scan statistical interpretation files before assigning "
            "hard numerical residual weights."
        ),
    }
    (output_dir / "other_hm_monitoring_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_markdown(output_dir / "other_hm_monitoring.md", zones, labels, levelling, targets, summary)

    print(f"wrote {len(outputs)} CSV tables to {output_dir}")
    print(f"zones: {summary['zone_rows']}; labels: {summary['text_label_rows']}")
    print(f"levelling rows: {summary['levelling_rows']}; qualitative targets: {summary['qualitative_target_rows']}")


if __name__ == "__main__":
    main()
