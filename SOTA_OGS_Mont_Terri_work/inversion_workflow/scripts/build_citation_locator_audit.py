#!/usr/bin/env python3
"""Audit active report citations for checkable locators and source tracking."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


REPORT_SOURCES = [Path("main.tex"), Path("measurement_chapter.tex")]
LOCATOR_RE = re.compile(
    r"\b("
    r"p\.|pp\.|PDF\s+p|PDF\s+pp|Sec\.|Sect\.|Sects\.|Section|Eq\.|Table|Tables|Fig\.|Chapter|"
    r"Governing equations|MeshElement|MeshNode"
    r")",
    flags=re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bib", type=Path, default=Path("opalinus_clay.bib"))
    parser.add_argument("--unavailable", type=Path, default=Path("Library/unavailable_fulltexts.md"))
    parser.add_argument("--output-csv", type=Path, default=Path("Library/citation_locator_audit.csv"))
    parser.add_argument("--output-json", type=Path, default=Path("Library/citation_locator_audit_summary.json"))
    parser.add_argument("--output-md", type=Path, default=Path("Library/citation_locator_audit.md"))
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def parse_bib_entries(path: Path) -> dict[str, str]:
    text = read_text(path)
    starts = list(re.finditer(r"@\w+\{([^,]+),", text))
    entries: dict[str, str] = {}
    for index, match in enumerate(starts):
        key = match.group(1).strip()
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        entries[key] = text[match.start() : end]
    return entries


def parse_unavailable_keys(path: Path) -> set[str]:
    text = read_text(path)
    keys = set()
    for line in text.splitlines():
        if not line.startswith("| `"):
            continue
        match = re.match(r"\| `([^`]+)`", line)
        if match:
            keys.add(match.group(1))
    return keys


def fulltext_status(key: str, bib_entry: str, unavailable_keys: set[str]) -> str:
    lowered = bib_entry.lower()
    if key in unavailable_keys:
        return "unavailable_tracked"
    if "fulltext saved" in lowered or "local fulltext copied" in lowered:
        return "local_fulltext_available"
    if "official ogs" in lowered or "opengeosys.org" in lowered:
        return "official_web_documentation"
    return "not_classified"


def locator_status(locator: str) -> str:
    if not locator:
        return "missing_locator"
    if LOCATOR_RE.search(locator):
        return "checkable_locator"
    return "weak_locator"


def find_citations(path: Path) -> list[dict[str, Any]]:
    text = read_text(path)
    rows: list[dict[str, Any]] = []
    pattern = re.compile(r"\\cite(?:\[(?P<locator>[^\]]*)\])?\{(?P<keys>[^}]+)\}", flags=re.DOTALL)
    for citation_index, match in enumerate(pattern.finditer(text), start=1):
        line_number = text.count("\n", 0, match.start()) + 1
        command = " ".join(match.group(0).split())
        locator = " ".join((match.group("locator") or "").split())
        keys = [key.strip() for key in match.group("keys").split(",") if key.strip()]
        for key in keys:
            rows.append(
                {
                    "source_file": str(path),
                    "line_number": line_number,
                    "citation_index": citation_index,
                    "citation_key": key,
                    "citation_command": command,
                    "locator": locator,
                    "locator_status": locator_status(locator),
                }
            )
    return rows


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def build_audit(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    bib_entries = parse_bib_entries(args.bib)
    unavailable_keys = parse_unavailable_keys(args.unavailable)
    rows: list[dict[str, Any]] = []
    for source in REPORT_SOURCES:
        rows.extend(find_citations(source))

    for row in rows:
        key = row["citation_key"]
        bib_entry = bib_entries.get(key, "")
        row["bibliography_status"] = "present" if bib_entry else "missing_bib_entry"
        row["fulltext_status"] = fulltext_status(key, bib_entry, unavailable_keys) if bib_entry else "unknown"
        row["source_location"] = f"{row['source_file']}:{row['line_number']}"

    cited_keys = sorted({row["citation_key"] for row in rows})
    locator_failures = [row for row in rows if row["locator_status"] != "checkable_locator"]
    missing_bib = sorted(key for key in cited_keys if key not in bib_entries)
    unavailable_missing_log = sorted(
        key
        for key in cited_keys
        if key in bib_entries
        and ("fulltext not downloaded" in bib_entries[key].lower() or "download blocked" in bib_entries[key].lower())
        and key not in unavailable_keys
    )
    summary = {
        "status": "citation_locator_audit_generated",
        "report_sources": [str(path) for path in REPORT_SOURCES],
        "citation_key_instance_count": len(rows),
        "unique_cited_key_count": len(cited_keys),
        "citation_commands_with_keys_count": len({(row["source_file"], row["citation_index"]) for row in rows}),
        "missing_or_weak_locator_count": len(locator_failures),
        "missing_bib_entry_count": len(missing_bib),
        "unavailable_fulltext_missing_log_count": len(unavailable_missing_log),
        "locator_status_counts": count_by(rows, "locator_status"),
        "bibliography_status_counts": count_by(rows, "bibliography_status"),
        "fulltext_status_counts": count_by(rows, "fulltext_status"),
        "cited_keys": cited_keys,
        "missing_or_weak_locator_rows": [
            {
                "source_location": row["source_location"],
                "citation_key": row["citation_key"],
                "locator": row["locator"],
                "locator_status": row["locator_status"],
            }
            for row in locator_failures
        ],
        "missing_bib_entries": missing_bib,
        "unavailable_fulltexts_missing_from_log": unavailable_missing_log,
        "notes": [
            "A checkable locator may be a page range, PDF page, section, equation, table, or named official documentation section.",
            "Official OGS documentation is treated separately from PDF fulltexts because the source is a web manual section.",
            "Unavailable fulltexts are acceptable only when their citation keys are tracked in Library/unavailable_fulltexts.md.",
        ],
    }
    return rows, summary


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "source_location",
        "citation_key",
        "locator",
        "locator_status",
        "bibliography_status",
        "fulltext_status",
        "citation_command",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_markdown(path: Path, rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Citation Locator Audit",
        "",
        "This audit checks whether every active report citation has a page, PDF-page,",
        "section, equation, table, or named documentation locator.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Citation key instances: {summary['citation_key_instance_count']}",
        f"- Unique cited keys: {summary['unique_cited_key_count']}",
        f"- Citation commands with keys: {summary['citation_commands_with_keys_count']}",
        f"- Missing or weak locator count: {summary['missing_or_weak_locator_count']}",
        f"- Missing BibTeX entries: {summary['missing_bib_entry_count']}",
        f"- Unavailable fulltexts missing from log: {summary['unavailable_fulltext_missing_log_count']}",
        f"- Locator statuses: {summary['locator_status_counts']}",
        f"- Fulltext statuses: {summary['fulltext_status_counts']}",
        "",
    ]
    if summary["missing_or_weak_locator_rows"]:
        lines.extend(["## Locator Gaps", ""])
        lines.extend(
            f"- `{row['source_location']}` `{row['citation_key']}`: `{row['locator_status']}` `{row['locator']}`"
            for row in summary["missing_or_weak_locator_rows"]
        )
        lines.append("")
    else:
        lines.extend(["No missing or weak citation locators were found in the active report sources.", ""])

    lines.extend(
        [
            "## Citation Rows",
            "",
            "| Location | Key | Locator | Locator status | BibTeX | Fulltext |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["source_location"].replace("|", "\\|"),
                    f"`{row['citation_key']}`",
                    row["locator"].replace("|", "\\|"),
                    f"`{row['locator_status']}`",
                    f"`{row['bibliography_status']}`",
                    f"`{row['fulltext_status']}`",
                ]
            )
            + " |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows, summary = build_audit(args)
    write_csv(args.output_csv, rows)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_markdown(args.output_md, rows, summary)


if __name__ == "__main__":
    main()
