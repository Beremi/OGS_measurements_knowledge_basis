#!/usr/bin/env python3
"""Generate mined data-content summaries for each measurement folder."""

from __future__ import annotations

import csv
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MEASUREMENTS = ROOT / "cda_knowledge_base" / "measurements"

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

TITLES = {
    "ert": "ERT / Electrical Resistivity",
    "nmr": "NMR Water Content",
    "taupe_tdr": "Taupe / TDR",
    "suction_relative_humidity": "Suction / Relative Humidity",
    "permeability_pulse_tests": "Permeability Pulse Tests",
    "other_hm_monitoring": "Other HM Monitoring",
    "coordinates_geometry_layout": "Coordinates / Geometry / Layout",
    "bedding_geology_structure": "Bedding / Geology / Structure",
    "model_projection_inputs": "Model Projection Inputs",
}

MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "mär": 3,
    "mrz": 3,
    "apr": 4,
    "may": 5,
    "mai": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "okt": 10,
    "nov": 11,
    "dec": 12,
    "dez": 12,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def link(from_dir: Path, target: Path, label: str | None = None) -> str:
    label = label or target.name
    try:
        target_rel = target.relative_to(from_dir).as_posix()
    except ValueError:
        target_rel = target.relative_to(ROOT).as_posix()
        target_rel = Path(*([".."] * len(from_dir.relative_to(ROOT).parts)), target_rel).as_posix()
    target_rel = re.sub(r"/+", "/", target_rel)
    if any(ch in target_rel for ch in " ()"):
        return f"[{label}](<{target_rel}>)"
    return f"[{label}]({target_rel})"


def fmt_num(value: float | int | None, digits: int = 4) -> str:
    if value is None:
        return "not detected"
    value = float(value)
    if not math.isfinite(value):
        return "not finite"
    if value == 0:
        return "0"
    if abs(value) >= 10000 or abs(value) < 0.001:
        return f"{value:.{digits}g}"
    return f"{value:.{digits}f}".rstrip("0").rstrip(".")


def fmt_range(values: list[float], unit: str = "") -> str:
    if not values:
        return "not detected"
    suffix = f" {unit}" if unit else ""
    return (
        f"n={len(values)}, min={fmt_num(min(values))}{suffix}, "
        f"mean={fmt_num(statistics.fmean(values))}{suffix}, max={fmt_num(max(values))}{suffix}"
    )


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", ".")
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def parse_german_datetime(text: str) -> datetime | None:
    match = re.match(
        r"(?P<day>\d{1,2})-(?P<month>[A-Za-zÄÖÜäöü]{3})-(?P<year>\d{4})\s+(?P<time>\d{2}:\d{2}:\d{2})",
        text.strip(),
    )
    if not match:
        return None
    month = MONTHS.get(match.group("month").lower())
    if not month:
        return None
    return datetime.strptime(
        f"{match.group('year')}-{month:02d}-{int(match.group('day')):02d} {match.group('time')}",
        "%Y-%m-%d %H:%M:%S",
    )


def clean_cell(text: str) -> str:
    return " ".join(str(text or "").replace("|", "\\|").split())


def source_links(md_dir: Path, sources: list[Path]) -> str:
    if not sources:
        return ""
    return ", ".join(link(md_dir, source, source.name) for source in sources)


def add_fact(
    rows: list[dict[str, Any]],
    measurement: str,
    category: str,
    item: str,
    value: str,
    sources: list[Path] | None = None,
    comment: str = "",
) -> None:
    rows.append(
        {
            "measurement": measurement,
            "category": category,
            "item": item,
            "value": value,
            "sources": "; ".join(rel(source) for source in sources or []),
            "comment": comment,
        }
    )


def rows_for_measurement(rows: list[dict[str, str]], measurement: str) -> list[dict[str, str]]:
    return [row for row in rows if row.get("measurement") == measurement]


def path_from_row(row: dict[str, str], key: str = "source_path") -> Path:
    return ROOT / row[key]


def parse_nmr_weekly(path: Path) -> dict[str, Any]:
    dates: list[datetime] = []
    wc: list[float] = []
    ci: list[float] = []
    t2: list[float] = []
    t2_ci: list[float] = []
    with path.open(newline="", encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            parsed_date = parse_german_datetime(row.get("Date", ""))
            if parsed_date:
                dates.append(parsed_date)
            for target, key in [
                (wc, "Vol.Wat.Content[%]"),
                (ci, "WC-Conf.Int.95%"),
                (t2, "T2[ms]"),
                (t2_ci, "T2-Conf.Int.95%"),
            ]:
                value = parse_float(row.get(key))
                if value is not None:
                    target.append(value)
    return {
        "rows": len(wc),
        "date_start": min(dates).isoformat(sep=" ") if dates else "",
        "date_end": max(dates).isoformat(sep=" ") if dates else "",
        "water_content": wc,
        "water_content_ci": ci,
        "t2": t2,
        "t2_ci": t2_ci,
    }


def parse_nmr_seasonal(path: Path) -> dict[str, Any]:
    wc: list[float] = []
    ci: list[float] = []
    positions: set[str] = set()
    with path.open(newline="", encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            if row.get("Position"):
                positions.add(row["Position"])
            value = parse_float(row.get("Vol.Wat.Content[%]"))
            if value is not None:
                wc.append(value)
            value = parse_float(row.get("WC-95%Conf.Int."))
            if value is not None:
                ci.append(value)
    match = re.search(r"Niche(?P<niche>\d)_Y_(?P<year>\d{4})_M_(?P<month>\d{2})_D_(?P<day>\d{2})", path.name)
    campaign = ""
    niche = ""
    if match:
        niche = f"Niche {match.group('niche')}"
        campaign = f"{match.group('year')}-{match.group('month')}-{match.group('day')}"
    return {
        "niche": niche,
        "campaign": campaign,
        "rows": len(wc),
        "positions": sorted(positions),
        "water_content": wc,
        "water_content_ci": ci,
    }


def summarize_nmr(
    measurement: str,
    rows: list[dict[str, str]],
    workbook_rows: list[dict[str, str]],
    archive_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    weekly_paths = [
        path_from_row(row)
        for row in rows
        if row.get("filename", "").startswith("2025-09-15_Weekly") and row.get("extension") == ".dat"
    ]
    for path in weekly_paths:
        summary = parse_nmr_weekly(path)
        add_fact(
            facts,
            measurement,
            "weekly NMR table",
            path.name,
            (
                f"{summary['rows']} records; {summary['date_start']} to {summary['date_end']}; "
                f"water content {fmt_range(summary['water_content'], '%')}; "
                f"95% CI {fmt_range(summary['water_content_ci'], '%')}; T2 {fmt_range(summary['t2'], 'ms')}"
            ),
            [path],
            "Columns are Date, volumetric water content, water-content 95% confidence interval, T2, and T2 95% confidence interval.",
        )

    seasonal_paths = [
        path_from_row(row)
        for row in rows
        if "/seasonal_nmr/" in row.get("source_path", "") and row.get("extension") == ".dat"
    ]
    by_niche: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seasonal_wc: list[float] = []
    seasonal_ci: list[float] = []
    all_positions: set[str] = set()
    for path in seasonal_paths:
        summary = parse_nmr_seasonal(path)
        if summary["niche"]:
            by_niche[summary["niche"]].append(summary)
        seasonal_wc.extend(summary["water_content"])
        seasonal_ci.extend(summary["water_content_ci"])
        all_positions.update(summary["positions"])
    if seasonal_paths:
        campaigns = []
        for niche, items in sorted(by_niche.items()):
            dates = sorted(item["campaign"] for item in items if item["campaign"])
            campaigns.append(f"{niche}: {len(dates)} campaigns ({dates[0]} to {dates[-1]})")
        add_fact(
            facts,
            measurement,
            "seasonal NMR archive data tables",
            "seasonal_nmr/saisonally/data_table_ascii",
            (
                f"{len(seasonal_paths)} campaign tables; {sum(len(items) for items in by_niche.values())} niche-campaign files; "
                f"positions {', '.join(sorted(all_positions))}; water content {fmt_range(seasonal_wc, '%')}; "
                f"95% CI {fmt_range(seasonal_ci, '%')}; {'; '.join(campaigns)}"
            ),
            seasonal_paths[:4],
            "These .dat files were extracted from the Thunderbird-recovered saisonally.zip archive and are copied under source_files.",
        )

    nmr_archives = [row for row in archive_rows if row.get("measurement_class") == "nmr"]
    ext_counts = Counter(row.get("extension", "") for row in nmr_archives)
    if ext_counts:
        add_fact(
            facts,
            measurement,
            "archive members",
            "NMR-related extracted archive members",
            ", ".join(f"{ext or '[none]'}={count}" for ext, count in sorted(ext_counts.items())),
            [],
            "The member catalogue records the original ZIP provenance for each extracted NMR seasonal table and figure.",
        )

    for row in workbook_rows:
        if row.get("measurement") != measurement:
            continue
        add_fact(
            facts,
            measurement,
            "coordinate workbook",
            f"{Path(row.get('workbook', '')).name} / {row.get('sheet', '')}",
            (
                f"{row.get('max_row')} x {row.get('max_column')} sheet; "
                f"{row.get('non_empty_cells')} non-empty cells; numeric ranges: {row.get('numeric_summary')}"
            ),
            [ROOT / row["workbook"]],
            "This workbook locates NMR/Taupe/characterization borehole labels in original and BGR model coordinates.",
        )
    return facts


def summarize_workbook_measurement(
    measurement: str,
    workbook_rows: list[dict[str, str]],
    category: str,
    note: str,
) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for row in workbook_rows:
        if row.get("measurement") != measurement:
            continue
        value_parts = [
            f"{row.get('max_row')} x {row.get('max_column')}",
            f"{row.get('non_empty_cells')} non-empty cells",
        ]
        if row.get("date_range"):
            value_parts.append(f"dates {row['date_range']}")
        if row.get("numeric_summary"):
            value_parts.append(f"numeric ranges: {row['numeric_summary']}")
        elif row.get("first_non_empty_values"):
            value_parts.append(f"headers: {row['first_non_empty_values']}")
        facts.append(
            {
                "measurement": measurement,
                "category": category,
                "item": f"{Path(row.get('workbook', '')).name} / {row.get('sheet', '')}",
                "value": "; ".join(value_parts),
                "sources": row.get("workbook", ""),
                "comment": note,
            }
        )
    return facts


def summarize_ert(
    measurement: str,
    rows: list[dict[str, str]],
    workbook_rows: list[dict[str, str]],
    archive_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    ert_archive = [
        row
        for row in archive_rows
        if row.get("archive", "").endswith("ERT_meas_Niche_open.zip")
    ]
    if ert_archive:
        ext_counts = Counter(row.get("extension", "") for row in ert_archive)
        month_counts: Counter[str] = Counter()
        for row in ert_archive:
            match = re.search(r"Niche open/(?P<year>\d{4})/(?P<month>[^/]+)/", row.get("archive_member", ""))
            if match:
                month_counts[f"{match.group('year')}/{match.group('month')}"] += 1
        months = sorted(month_counts)
        add_fact(
            facts,
            measurement,
            "ERT TeamBeam ZIP",
            "ERT_meas_Niche_open.zip",
            (
                f"{len(ert_archive)} indexed members; extension counts "
                + ", ".join(f"{ext or '[none]'}={count}" for ext, count in sorted(ext_counts.items()))
                + f"; {len(months)} dated year/month folders from {months[0]} to {months[-1]}"
            ),
            [ROOT / "cda_knowledge_base/file_transfers/collected/2025-04-03_ert_open_twin/ERT_meas_Niche_open.zip"],
            "The archive is intentionally kept compressed because it contains a large VTK time-series; each member is still indexed in archive_member_catalog.csv.",
        )
    for row in rows:
        if row.get("extension") in {".tx0", ".ohm", ".txt"}:
            add_fact(
                facts,
                measurement,
                "raw ERT text/data file",
                row.get("filename", ""),
                f"{row.get('lines') or 'unknown'} lines; first extracted content: {row.get('first_lines', '')[:260]}",
                [path_from_row(row)],
                "These Thunderbird-recovered raw/example files anchor the open/closed split and electrode geometry.",
            )
    facts.extend(
        summarize_workbook_measurement(
            measurement,
            workbook_rows,
            "ERT workbook/PDF support",
            "Workbook rows summarize resistivity/water-content relation material and ERT missing-data notes.",
        )
    )
    return facts


def summarize_model_projection(
    measurement: str,
    rows: list[dict[str, str]],
    archive_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    by_ext = Counter(row.get("extension", "") for row in rows)
    add_fact(
        facts,
        measurement,
        "copied model/projection files",
        "source_files",
        ", ".join(f"{ext or '[none]'}={count}" for ext, count in sorted(by_ext.items())),
        [],
        "These files are model-support inputs rather than measurements, but they define the mesh, projection support, output timesteps, and exchanged OGS configurations used to place the measurement data.",
    )
    for row in rows:
        if row.get("filename") in {"specifications.pptx", "generate_projections.py", "README.txt", "cd_a_open_niche_quad.prj"}:
            add_fact(
                facts,
                measurement,
                "projection workflow reference",
                row.get("filename", ""),
                f"type {row.get('kind')}; {row.get('size_bytes')} bytes; extracted note: {row.get('first_lines', '')[:280]}",
                [path_from_row(row)],
                "Use these files to understand how measured points/intervals are projected to the frozen OGS mesh and timesteps.",
            )
    archive_counts: Counter[str] = Counter()
    for row in archive_rows:
        if "model_projection_inputs" in row.get("measurement_class", ""):
            archive_counts[row.get("archive", "")] += 1
    for archive, count in sorted(archive_counts.items()):
        add_fact(
            facts,
            measurement,
            "model/archive member coverage",
            Path(archive).name,
            f"{count} indexed model/projection/report-context members",
            [ROOT / archive],
            "The member catalogue links each ZIP member to the copied model_projection_inputs source tree where it was extracted or preserved.",
        )
    return facts


def summarize_generic_sources(
    measurement: str,
    rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    pdfs = [row for row in rows if row.get("kind") == "pdf"]
    ppts = [row for row in rows if row.get("kind") == "pptx"]
    text_rows = [row for row in rows if row.get("kind") == "text/data"]
    for row in pdfs + ppts:
        add_fact(
            facts,
            measurement,
            "document/presentation extract",
            row.get("filename", ""),
            (
                f"type {row.get('kind')}; pages/slides {row.get('pages') or row.get('slides') or 'not recorded'}; "
                f"keywords {row.get('keywords') or 'not detected'}; extract {row.get('extract_path') or 'not generated'}"
            ),
            [path_from_row(row)],
            "Generated text extracts make these documents searchable without opening the PDF/PPTX manually.",
        )
    for row in text_rows:
        if row.get("extension") in {".dat", ".txt", ".md"}:
            add_fact(
                facts,
                measurement,
                "text/data source",
                row.get("filename", ""),
                f"{row.get('lines') or 'unknown'} lines; first extracted content: {row.get('first_lines', '')[:260]}",
                [path_from_row(row)],
                "Header/first-line extraction is recorded in derived_files/deep_source_pass/extracted_text.",
            )
    return facts


def facts_for_measurement(
    measurement: str,
    deep_rows: list[dict[str, str]],
    workbook_rows: list[dict[str, str]],
    archive_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    rows = rows_for_measurement(deep_rows, measurement)
    facts: list[dict[str, Any]] = []
    kind_counts = Counter(row.get("kind", "") for row in rows)
    total_bytes = sum(int(row.get("size_bytes") or 0) for row in rows)
    add_fact(
        facts,
        measurement,
        "catalogue scope",
        "copied source files",
        (
            f"{len(rows)} files; total copied source bytes {total_bytes}; file kinds "
            + ", ".join(f"{kind or '[none]'}={count}" for kind, count in sorted(kind_counts.items()))
        ),
        [],
        "Counts are from cda_knowledge_base/measurements/deep_source_index.csv.",
    )

    if measurement == "nmr":
        facts.extend(summarize_nmr(measurement, rows, workbook_rows, archive_rows))
    elif measurement == "ert":
        facts.extend(summarize_ert(measurement, rows, workbook_rows, archive_rows))
    elif measurement == "model_projection_inputs":
        facts.extend(summarize_model_projection(measurement, rows, archive_rows))
    elif measurement in {"taupe_tdr", "suction_relative_humidity", "coordinates_geometry_layout", "permeability_pulse_tests"}:
        notes = {
            "taupe_tdr": "The Taupe/TDR workbook sheets give date ranges and EDZ band summaries; current model use remains trend/anomaly based until units/calibration are confirmed.",
            "suction_relative_humidity": "The RH workbooks provide sensor-specific time series; current model use is boundary-condition evidence until active-curve provenance is confirmed.",
            "coordinates_geometry_layout": "These sheets are geometry support for projecting measurement labels into the BGR/OGS modelling frame.",
            "permeability_pulse_tests": "These sheets combine interpreted permeability/transmissibility rows with raw pressure-decay blocks and chart sheets.",
        }
        facts.extend(summarize_workbook_measurement(measurement, workbook_rows, "workbook content", notes[measurement]))

    if measurement not in {"nmr", "ert", "model_projection_inputs"}:
        facts.extend(summarize_generic_sources(measurement, rows))
    else:
        facts.extend(
            [
                fact
                for fact in summarize_generic_sources(measurement, rows)
                if fact["category"] == "document/presentation extract"
            ]
        )
    return facts


def build_measurement_md(measurement: str, facts: list[dict[str, Any]]) -> str:
    out_file = MEASUREMENTS / measurement / "DATA_CONTENT_SUMMARY.md"
    md_dir = out_file.parent
    lines = [
        f"# {TITLES[measurement]} Data Content Summary",
        "",
        f"Generated: {date.today().isoformat()}.",
        "",
        "This file is the deep content pass over the copied measurement material: workbooks, raw tables, extracted ZIP members, presentation/PDF text extracts, and archive indexes.",
        "Use it together with `MEASUREMENT_INFO.md` in the measurement-info mirror and with the raw files in `source_files/`.",
        "",
        "## Mined Findings",
        "",
        "| Category | Item | Data content mined | Source files | Note |",
        "| --- | --- | --- | --- | --- |",
    ]
    for fact in facts:
        sources = []
        for item in str(fact.get("sources", "")).split(";"):
            item = item.strip()
            if item:
                sources.append(ROOT / item)
        lines.append(
            "| "
            + " | ".join(
                [
                    clean_cell(fact.get("category", "")),
                    clean_cell(fact.get("item", "")),
                    clean_cell(fact.get("value", "")),
                    source_links(md_dir, sources).replace("|", "\\|"),
                    clean_cell(fact.get("comment", "")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Navigation",
            "",
            f"- Source files: {link(md_dir, MEASUREMENTS / measurement / 'source_files', 'source_files/')}",
            f"- Generated deep source pass: {link(md_dir, MEASUREMENTS / measurement / 'derived_files/deep_source_pass/source_file_deep_summary.md', 'source_file_deep_summary.md')}",
            f"- Machine-readable facts: {link(md_dir, MEASUREMENTS / measurement / 'derived_files/content_deep_dive/content_summary.csv', 'content_summary.csv')}",
            "",
        ]
    )
    return "\n".join(lines)


def build_global_md(all_facts: list[dict[str, Any]], deep_rows: list[dict[str, str]]) -> str:
    md_dir = MEASUREMENTS
    by_measurement = Counter(fact["measurement"] for fact in all_facts)
    by_kind = Counter(row.get("kind", "") for row in deep_rows)
    lines = [
        "# Measurement Content Deep Dive",
        "",
        f"Generated: {date.today().isoformat()}.",
        "",
        "This is the top-level index for the second-pass content mining of the measurement folders. It complements `deep_source_index.md`, which is file-oriented, by adding measurement-oriented facts from the actual copied tables, archives, and extracted document text.",
        "",
        "## Scope",
        "",
        f"- Measurement folders covered: {len(by_measurement)}.",
        f"- Mined fact rows: {len(all_facts)}.",
        "- Source file kinds in the underlying deep index: "
        + ", ".join(f"`{kind}`={count}" for kind, count in sorted(by_kind.items()) if kind)
        + ".",
        "",
        "## Per-Measurement Content Files",
        "",
        "| Measurement | Fact rows | Content summary | Source folder |",
        "| --- | ---: | --- | --- |",
    ]
    for measurement in MEASUREMENT_DIRS:
        lines.append(
            "| "
            + " | ".join(
                [
                    TITLES[measurement],
                    str(by_measurement.get(measurement, 0)),
                    link(md_dir, MEASUREMENTS / measurement / "DATA_CONTENT_SUMMARY.md", "DATA_CONTENT_SUMMARY.md"),
                    link(md_dir, MEASUREMENTS / measurement / "source_files", "source_files/"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Machine-Readable Files",
            "",
            "- [measurement_content_deep_dive.csv](measurement_content_deep_dive.csv): all mined fact rows.",
            "- [measurement_content_deep_dive_summary.json](measurement_content_deep_dive_summary.json): counts and generated-file list.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    deep_rows = read_csv(MEASUREMENTS / "deep_source_index.csv")
    workbook_rows = read_csv(MEASUREMENTS / "workbook_sheet_deep_index.csv")
    archive_rows = read_csv(MEASUREMENTS / "archive_member_catalog.csv")
    if not deep_rows:
        raise SystemExit("Missing deep_source_index.csv; run build_measurement_deep_source_index.py first.")

    all_facts: list[dict[str, Any]] = []
    generated: list[str] = []
    fields = ["measurement", "category", "item", "value", "sources", "comment"]
    for measurement in MEASUREMENT_DIRS:
        facts = facts_for_measurement(measurement, deep_rows, workbook_rows, archive_rows)
        all_facts.extend(facts)
        content_dir = MEASUREMENTS / measurement / "derived_files" / "content_deep_dive"
        write_csv(content_dir / "content_summary.csv", facts, fields)
        write_text(content_dir / "content_summary.json", json.dumps(facts, indent=2, sort_keys=True))
        write_text(MEASUREMENTS / measurement / "DATA_CONTENT_SUMMARY.md", build_measurement_md(measurement, facts))
        generated.extend(
            [
                rel(content_dir / "content_summary.csv"),
                rel(content_dir / "content_summary.json"),
                rel(MEASUREMENTS / measurement / "DATA_CONTENT_SUMMARY.md"),
            ]
        )

    write_csv(MEASUREMENTS / "measurement_content_deep_dive.csv", all_facts, fields)
    write_text(MEASUREMENTS / "measurement_content_deep_dive.md", build_global_md(all_facts, deep_rows))
    summary = {
        "generated": sorted(generated + [
            rel(MEASUREMENTS / "measurement_content_deep_dive.csv"),
            rel(MEASUREMENTS / "measurement_content_deep_dive.md"),
            rel(MEASUREMENTS / "measurement_content_deep_dive_summary.json"),
        ]),
        "measurement_fact_counts": dict(Counter(fact["measurement"] for fact in all_facts)),
        "total_fact_rows": len(all_facts),
    }
    write_text(MEASUREMENTS / "measurement_content_deep_dive_summary.json", json.dumps(summary, indent=2, sort_keys=True))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
