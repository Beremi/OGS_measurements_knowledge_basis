#!/usr/bin/env python3
"""Scan the local Downloads folder for evidence that could close open gates.

The curated measurement catalogue is the authoritative source set.  This audit is
only a recovery sweep over raw Downloads so that duplicate TeamBeam archives,
uncatalogued run-output folders, and possible gate-closing files are recorded in a
repeatable way.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

from build_local_gate_recovery_audit import GATE_SPECS, audit_documents, copy_outputs, read_text, summarize


SKIP_DIR_NAMES = {
    ".cache",
    ".git",
    ".local",
    "__pycache__",
    "node_modules",
    "squashfs-root",
    "t3pa_analysis",
    "Tile Reference (1st edition) - Wikicarpedia the Carcassonne game rules wiki_files",
    "venv",
}
SKIP_FILE_NAMES = {
    "main.docx",
    "main.md",
    "main2.docx",
    "main3.docx",
    "main4.docx",
}
HIGH_SIGNAL_TERMS = {
    "003 nov 2025",
    "bcd a24",
    "bcd a25",
    "bcd a26",
    "bcd a27",
    "bfm d19",
    "bgr",
    "cd a",
    "cda",
    "crackmeter",
    "electrode",
    "ert",
    "extensometer",
    "gesa",
    "geoscope",
    "hermes",
    "laser scan",
    "levelling",
    "leveling",
    "mini piezometer",
    "mont terri",
    "niche",
    "nmr",
    "permeability",
    "piezometer",
    "relative humidity",
    "resistivity",
    "rh5",
    "rh6",
    "rh7",
    "rh8",
    "suction",
    "taupe",
    "tdr",
    "teambeam",
    "visualisationcda",
    "ziefle",
}

TEXT_SUFFIXES = {".csv", ".dat", ".md", ".ohm", ".prj", ".txt", ".tx0", ".xml", ".py"}
ARCHIVE_SUFFIXES = {".zip", ".docx", ".pptx", ".xlsx", ".xlsm"}
OFFICE_TEXT_PREFIXES = (
    "docProps/",
    "word/",
    "xl/sharedStrings.xml",
    "xl/worksheets/",
    "xl/workbook.xml",
    "ppt/slides/",
    "ppt/notesSlides/",
)
KNOWN_TEAMBEAM_FILENAMES = {
    "ERT_meas_Niche_open.zip",
    "CDA_N4_2D_250403.zip",
    "apptainer_ogs6.5.4.sif",
    "ReadMe.md",
    "docker_ogs6.5.4.tar.gz",
    "Dockerfile",
    "CDA_N4_2D_250509.zip",
    "003_Nov_2025.zip",
    "VisualisationCDA.dat",
    "Perm_Sec_4-3_Ziefle_et_al_2023_Characterization.pdf",
    "Permeability_CDA_all_2025.xlsx",
    "bedding_angle_ERT.png",
    "bedding_page_4_Ziefle_GETE_2022.pdf",
}
GENERIC_CATALOGUE_FILENAMES = {"Dockerfile", "ReadMe.md", "main.tex"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--downloads-root", type=Path, default=Path("/home/ber0061/Downloads"))
    parser.add_argument(
        "--catalogue-manifest",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/source_file_manifest.csv"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/download_gate_recovery_audit.csv"),
    )
    parser.add_argument(
        "--output-inventory-csv",
        type=Path,
        default=Path("inversion_workflow/download_gate_recovery_inventory.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/download_gate_recovery_audit_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/download_gate_recovery_audit.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files"),
    )
    parser.add_argument("--max-text-bytes", type=int, default=2_000_000)
    parser.add_argument("--max-archive-members", type=int, default=10_000)
    parser.add_argument("--max-office-member-bytes", type=int, default=4_000_000)
    return parser.parse_args()


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def normalized_duplicate_name(name: str) -> str:
    return re.sub(r" \(\d+\)(?=\.[^.]+$)", "", name)


def normalized_signal_text(text: str) -> str:
    text = text.lower()
    text = text.replace("–", "-").replace("—", "-").replace("_", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def has_high_signal(text: str) -> bool:
    normalized = normalized_signal_text(text)
    return any(re.search(rf"\b{re.escape(term)}\b", normalized) for term in HIGH_SIGNAL_TERMS)


def should_skip(path: Path, root: Path) -> bool:
    if any(part in SKIP_DIR_NAMES for part in path.parts):
        return True
    if any(part == "eurad_final" for part in path.parts):
        return True
    if path.name in SKIP_FILE_NAMES and (path.parent == root or any(part == "eurad_final" for part in path.parts)):
        return True
    return False


def sha1_for(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def load_catalogue_manifest(path: Path) -> tuple[dict[str, list[dict[str, str]]], dict[tuple[str, int], list[dict[str, str]]]]:
    by_name: dict[str, list[dict[str, str]]] = {}
    by_name_size: dict[tuple[str, int], list[dict[str, str]]] = {}
    if not path.exists():
        return by_name, by_name_size
    with path.open(newline="", encoding="utf-8", errors="ignore") as handle:
        for row in csv.DictReader(handle):
            name = row.get("filename") or ""
            if not name:
                continue
            size = int(row.get("size_bytes") or 0)
            by_name.setdefault(name, []).append(row)
            by_name_size.setdefault((name, size), []).append(row)
    return by_name, by_name_size


def iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if should_skip(path, root):
            continue
        if path.is_file():
            files.append(path)
    return files


def strip_xml_text(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="ignore")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def archive_member_documents(path: Path, root: Path, max_members: int, max_member_bytes: int) -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()[:max_members]
            member_names = [info.filename for info in infos if not info.is_dir()]
            if member_names:
                chunk_size = 500
                for start in range(0, len(member_names), chunk_size):
                    chunk = member_names[start : start + chunk_size]
                    text = "\n".join(chunk)
                    if not (has_high_signal(str(path)) or has_high_signal(text)):
                        continue
                    documents.append(
                        {
                            "measurement_folder": "downloads",
                            "source_kind": "downloads_archive_member_names",
                            "source_path": rel(path, root.parent),
                            "context": f"{path.name} members {start + 1}-{start + len(chunk)}",
                            "text": text,
                        }
                    )
            if path.suffix.lower() in {".docx", ".pptx", ".xlsx", ".xlsm"}:
                extracted_text: list[str] = []
                for info in infos:
                    if info.is_dir() or info.file_size > max_member_bytes:
                        continue
                    if not info.filename.startswith(OFFICE_TEXT_PREFIXES):
                        continue
                    try:
                        extracted_text.append(strip_xml_text(archive.read(info)))
                    except (OSError, RuntimeError, zipfile.BadZipFile):
                        continue
                text = "\n".join(part for part in extracted_text if part)
                if text and (has_high_signal(str(path)) or has_high_signal(text)):
                    documents.append(
                        {
                            "measurement_folder": "downloads",
                            "source_kind": "downloads_office_xml_text",
                            "source_path": rel(path, root.parent),
                            "context": path.name,
                            "text": text[:250_000],
                        }
                    )
    except (OSError, RuntimeError, zipfile.BadZipFile):
        documents.append(
            {
                "measurement_folder": "downloads",
                "source_kind": "downloads_archive_read_error",
                "source_path": rel(path, root.parent),
                "context": path.name,
                "text": path.name,
            }
        )
    return documents


def collect_documents(root: Path, max_text_bytes: int, max_archive_members: int, max_office_member_bytes: int) -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []
    for path in iter_files(root):
        path_text = f"{rel(path, root)} {path.name}"
        if has_high_signal(path_text):
            documents.append(
                {
                    "measurement_folder": "downloads",
                    "source_kind": "downloads_file_name",
                    "source_path": rel(path, root.parent),
                    "context": path.name,
                    "text": path_text,
                }
            )
        suffix = path.suffix.lower()
        if suffix in TEXT_SUFFIXES and path.stat().st_size <= max_text_bytes:
            text = read_text(path, max_chars=250_000)
            if text and (has_high_signal(path_text) or has_high_signal(text)):
                documents.append(
                    {
                        "measurement_folder": "downloads",
                        "source_kind": "downloads_file_text",
                        "source_path": rel(path, root.parent),
                        "context": path.name,
                        "text": text,
                    }
                )
        if suffix in ARCHIVE_SUFFIXES:
            documents.extend(archive_member_documents(path, root, max_archive_members, max_office_member_bytes))
    return documents


def inventory_row_for(
    path: Path,
    root: Path,
    by_name: dict[str, list[dict[str, str]]],
    by_name_size: dict[tuple[str, int], list[dict[str, str]]],
) -> dict[str, str] | None:
    name = path.name
    normalized_name = normalized_duplicate_name(name)
    size = path.stat().st_size
    manifest_rows = by_name_size.get((normalized_name, size), [])
    name_rows = by_name.get(normalized_name, [])
    has_relevant_name = has_high_signal(f"{path} {normalized_name}")
    is_known_teambeam = normalized_name in KNOWN_TEAMBEAM_FILENAMES and (
        has_relevant_name or normalized_name not in GENERIC_CATALOGUE_FILENAMES
    )
    is_name_match = bool(name_rows) and (has_relevant_name or normalized_name not in GENERIC_CATALOGUE_FILENAMES)
    if not (is_known_teambeam or is_name_match or has_relevant_name):
        return None
    sha1 = ""
    sha1_match = ""
    if manifest_rows or is_known_teambeam:
        sha1 = sha1_for(path)
        catalogue_hashes = {row.get("sha1", "") for row in manifest_rows if row.get("sha1")}
        sha1_match = str(bool(sha1 and sha1 in catalogue_hashes)).lower() if catalogue_hashes else ""
    if manifest_rows and sha1_match == "true":
        status = "catalogued_duplicate_sha1_verified"
    elif manifest_rows:
        status = "catalogue_name_size_match_hash_mismatch_or_unchecked"
    elif name_rows:
        status = "catalogue_name_match_size_differs"
    elif is_known_teambeam:
        status = "known_teambeam_name_not_in_measurement_manifest"
    else:
        status = "downloads_relevant_name_candidate"
    return {
        "downloads_path": str(path),
        "relative_path": rel(path, root),
        "filename": name,
        "normalized_filename": normalized_name,
        "size_bytes": str(size),
        "sha1": sha1,
        "catalogue_status": status,
        "catalogue_sha1_match": sha1_match,
        "matching_catalogue_paths": "; ".join(sorted({row.get("relative_path", "") for row in manifest_rows or name_rows})),
    }


def build_inventory(root: Path, manifest_path: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    by_name, by_name_size = load_catalogue_manifest(manifest_path)
    file_rows = []
    for path in iter_files(root):
        row = inventory_row_for(path, root, by_name, by_name_size)
        if row:
            file_rows.append(row)

    directory_rows: list[dict[str, str]] = []
    cda_run_dir = root / "CDA_N4_2D_250403"
    if cda_run_dir.exists() and cda_run_dir.is_dir():
        files = [path for path in cda_run_dir.rglob("*") if path.is_file()]
        size = sum(path.stat().st_size for path in files)
        suffix_counts = Counter(path.suffix.lower() or "[none]" for path in files)
        directory_rows.append(
            {
                "downloads_path": str(cda_run_dir),
                "relative_path": rel(cda_run_dir, root),
                "filename": cda_run_dir.name,
                "normalized_filename": cda_run_dir.name,
                "size_bytes": str(size),
                "sha1": "",
                "catalogue_status": "uncatalogued_extracted_or_run_output_directory",
                "catalogue_sha1_match": "",
                "matching_catalogue_paths": f"{len(files)} files; suffixes={dict(suffix_counts)}",
            }
        )
    return sorted(file_rows, key=lambda row: row["downloads_path"]), directory_rows


def write_inventory(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "downloads_path",
        "relative_path",
        "filename",
        "normalized_filename",
        "size_bytes",
        "sha1",
        "catalogue_status",
        "catalogue_sha1_match",
        "matching_catalogue_paths",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(
    path: Path,
    rows: list[dict[str, str]],
    inventory_rows: list[dict[str, str]],
    summary: dict[str, Any],
) -> None:
    lines = [
        "# Download Gate Recovery Audit",
        "",
        "This audit scans `/home/ber0061/Downloads` for raw local files that could close the currently open external measurement gates.",
        "It is separate from the curated local-gate scan, because Downloads may contain duplicates, extracted run folders, and unrelated project files.",
        "",
        "## Summary",
        "",
        f"- Status: `{summary['status']}`",
        f"- Download documents scanned: {summary['document_count']}",
        f"- Downloads evidence rows: {summary['evidence_row_count']}",
        f"- Gates with possible gate-closing evidence: {len(summary['gates_with_closure_candidates'])}",
        f"- Gates still external after Downloads scan: {len(summary['gates_still_external_after_downloads_scan'])}",
        f"- Inventory rows: {len(inventory_rows)}",
        "",
        "## Gate Results",
        "",
        "| Gate | Downloads status | Evidence rows | Possible closure evidence | Top source hints |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for gate_id, gate_summary in summary["gate_summaries"].items():
        top = "; ".join(
            f"{item['source_path']} ({item['context']})"
            for item in gate_summary["top_sources"][:3]
        ) or "none"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{gate_id}`",
                    f"`{gate_summary['local_status']}`",
                    str(gate_summary["candidate_evidence_count"]),
                    str(gate_summary["possible_closure_evidence_count"]),
                    top.replace("|", "\\|"),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Downloads Inventory Highlights", ""])
    highlight_rows = [row for row in inventory_rows if row["catalogue_status"] != "downloads_relevant_name_candidate"]
    if highlight_rows:
        lines.extend(
            [
                "| File or directory | Status | Notes |",
                "| --- | --- | --- |",
            ]
        )
        for row in highlight_rows[:120]:
            notes = row["matching_catalogue_paths"] or row["sha1"]
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{row['relative_path']}`",
                        f"`{row['catalogue_status']}`",
                        notes.replace("|", "\\|"),
                    ]
                )
                + " |"
            )
        omitted = len(inventory_rows) - len(highlight_rows)
        if omitted:
            lines.extend(
                [
                    "",
                    f"{omitted} additional relevant-name candidates are listed in `download_gate_recovery_inventory.csv`; none produced a gate-closing evidence row.",
                ]
            )
    else:
        lines.append("No TeamBeam, catalogue-name, or gate-keyword candidates were found.")
    lines.extend(["", "## Possible Closure Evidence Rows", ""])
    closure_rows = [row for row in rows if row["evidence_status"] == "possible_gate_closure_evidence_requires_review"]
    if closure_rows:
        lines.extend(["| Gate | Source | Context | Matched terms | Caveat |", "| --- | --- | --- | --- | --- |"])
        for row in closure_rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{row['gate_id']}`",
                        f"`{row['source_path']}`",
                        row["context"].replace("|", "\\|"),
                        row["matched_terms"].replace("|", "\\|"),
                        row["caveat"].replace("|", "\\|"),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No Downloads row satisfied the gate-specific hard closure checks.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The Downloads scan found candidate context and duplicate archives, but a duplicate or keyword hit is not enough to close a gate.  A gate can be promoted only after the required transform, uncertainty, provenance, calibration, or endpoint-geometry evidence is filed in the relevant provider-response directory and the stream-gate audit is regenerated.",
            "",
            "The row-level evidence table is `download_gate_recovery_audit.csv`; the inventory is `download_gate_recovery_inventory.csv`; the machine-readable summary is `download_gate_recovery_audit_summary.json`.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    documents = collect_documents(
        args.downloads_root,
        max_text_bytes=args.max_text_bytes,
        max_archive_members=args.max_archive_members,
        max_office_member_bytes=args.max_office_member_bytes,
    )
    rows = audit_documents(documents)
    summary = summarize(rows, documents)
    summary["status"] = "download_gate_recovery_audit_generated"
    summary["downloads_root"] = str(args.downloads_root)
    summary["gates_still_external_after_downloads_scan"] = summary.pop("gates_still_external_after_local_rescan")
    inventory_rows, directory_rows = build_inventory(args.downloads_root, args.catalogue_manifest)
    all_inventory_rows = inventory_rows + directory_rows
    status_counts = Counter(row["catalogue_status"] for row in all_inventory_rows)
    summary["inventory_row_count"] = len(all_inventory_rows)
    summary["inventory_status_counts"] = dict(status_counts)
    summary["catalogued_duplicate_sha1_verified_count"] = status_counts.get("catalogued_duplicate_sha1_verified", 0)
    summary["uncatalogued_extracted_or_run_output_directory_count"] = status_counts.get(
        "uncatalogued_extracted_or_run_output_directory", 0
    )

    from build_local_gate_recovery_audit import write_csv

    write_csv(args.output_csv, rows)
    write_inventory(args.output_inventory_csv, all_inventory_rows)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_markdown(args.output_md, rows, all_inventory_rows, summary)
    if args.catalogue_dir:
        copy_outputs([args.output_csv, args.output_inventory_csv, args.output_json, args.output_md], args.catalogue_dir)


if __name__ == "__main__":
    main()
