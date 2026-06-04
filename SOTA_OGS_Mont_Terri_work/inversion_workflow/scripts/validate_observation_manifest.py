#!/usr/bin/env python3
"""Validate the local CD-A observation manifest against collected measurement files."""

from __future__ import annotations

import argparse
import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("inversion_workflow/observation_manifest.json"),
    )
    parser.add_argument(
        "--write-report",
        type=Path,
        default=Path("inversion_workflow/observation_manifest_validation.json"),
    )
    return parser.parse_args()


def resolve_path(base: Path, rel: str) -> Path:
    path = Path(rel)
    if path.is_absolute():
        return path
    return (base / path).resolve()


def ok_result(check: dict[str, Any], path: Path, details: dict[str, Any]) -> dict[str, Any]:
    return {"status": "ok", "type": check["type"], "path": str(path), "details": details}


def fail_result(check: dict[str, Any], path: Path, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "status": "fail",
        "type": check["type"],
        "path": str(path),
        "message": message,
        "details": details or {},
    }


def validate_file(check: dict[str, Any], path: Path) -> dict[str, Any]:
    if not path.exists():
        return fail_result(check, path, "file missing")
    if not path.is_file():
        return fail_result(check, path, "path is not a file")
    return ok_result(check, path, {"size_bytes": path.stat().st_size})


def validate_text(check: dict[str, Any], path: Path) -> dict[str, Any]:
    base = validate_file(check, path)
    if base["status"] != "ok":
        return base
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    details = {"line_count": len(lines), "size_bytes": path.stat().st_size}
    min_lines = check.get("min_lines")
    if min_lines is not None and len(lines) < min_lines:
        return fail_result(check, path, f"line count {len(lines)} < {min_lines}", details)
    needle = check.get("contains")
    if needle and needle not in text:
        return fail_result(check, path, f"missing required text {needle!r}", details)
    return ok_result(check, path, details)


def validate_zip(check: dict[str, Any], path: Path) -> dict[str, Any]:
    base = validate_file(check, path)
    if base["status"] != "ok":
        return base
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
    file_names = [name for name in names if not name.endswith("/")]
    suffix_counts: dict[str, int] = {}
    for name in file_names:
        suffix = Path(name).suffix.lower() or "<none>"
        suffix_counts[suffix] = suffix_counts.get(suffix, 0) + 1
    details = {
        "entries": len(names),
        "files": len(file_names),
        "suffix_counts": suffix_counts,
    }
    min_files = check.get("min_files")
    if min_files is not None and len(file_names) < min_files:
        return fail_result(check, path, f"file count {len(file_names)} < {min_files}", details)
    for suffix, required in check.get("suffix_counts_min", {}).items():
        actual = suffix_counts.get(suffix, 0)
        if actual < required:
            return fail_result(check, path, f"suffix {suffix} count {actual} < {required}", details)
    return ok_result(check, path, details)


def validate_csv(check: dict[str, Any], path: Path) -> dict[str, Any]:
    base = validate_file(check, path)
    if base["status"] != "ok":
        return base
    df = pd.read_csv(path, sep=check.get("delimiter", ","))
    details = {"rows": int(df.shape[0]), "columns": list(map(str, df.columns))}
    min_rows = check.get("min_rows")
    if min_rows is not None and df.shape[0] < min_rows:
        return fail_result(check, path, f"row count {df.shape[0]} < {min_rows}", details)
    missing = [col for col in check.get("required_columns", []) if col not in df.columns]
    if missing:
        return fail_result(check, path, f"missing columns {missing}", details)
    return ok_result(check, path, details)


def validate_xlsx(check: dict[str, Any], path: Path) -> dict[str, Any]:
    base = validate_file(check, path)
    if base["status"] != "ok":
        return base
    workbook = pd.ExcelFile(path)
    details: dict[str, Any] = {"sheets": workbook.sheet_names, "sheet_shapes": {}}
    missing_sheets = [sheet for sheet in check.get("required_sheets", []) if sheet not in workbook.sheet_names]
    if missing_sheets:
        return fail_result(check, path, f"missing sheets {missing_sheets}", details)

    sheet_names = check.get("required_sheets", workbook.sheet_names)
    required_columns = check.get("required_columns_by_sheet", {})
    min_rows = check.get("min_rows_by_sheet", {})
    for sheet in sheet_names:
        df = pd.read_excel(path, sheet_name=sheet)
        columns = list(map(str, df.columns))
        details["sheet_shapes"][sheet] = {"rows": int(df.shape[0]), "columns": columns}
        missing = [col for col in required_columns.get(sheet, []) if col not in columns]
        if missing:
            return fail_result(check, path, f"sheet {sheet!r} missing columns {missing}", details)
        required_rows = min_rows.get(sheet)
        if required_rows is not None and df.shape[0] < required_rows:
            return fail_result(check, path, f"sheet {sheet!r} row count {df.shape[0]} < {required_rows}", details)
    return ok_result(check, path, details)


def validate_mesh(check: dict[str, Any], path: Path) -> dict[str, Any]:
    base = validate_file(check, path)
    if base["status"] != "ok":
        return base
    root = ET.parse(path).getroot()
    piece = root.find(".//Piece")
    if piece is None:
        return fail_result(check, path, "VTU Piece element not found")
    cell_count = int(piece.attrib.get("NumberOfCells", "0"))
    point_count = int(piece.attrib.get("NumberOfPoints", "0"))
    cell_data_names = [
        node.attrib.get("Name", "")
        for node in root.findall(".//CellData/DataArray")
        if node.attrib.get("Name")
    ]
    cell_type = check.get("cell_type", "cells")
    details = {
        "points": point_count,
        "cell_counts": {cell_type: cell_count},
        "cell_data": sorted(cell_data_names),
    }
    if cell_count < check.get("min_cells", 0):
        return fail_result(check, path, f"{cell_type} cell count {cell_count} below required", details)
    missing_data = [name for name in check.get("required_cell_data", []) if name not in cell_data_names]
    if missing_data:
        return fail_result(check, path, f"missing cell data {missing_data}", details)
    return ok_result(check, path, details)


VALIDATORS = {
    "file": validate_file,
    "text": validate_text,
    "zip": validate_zip,
    "csv": validate_csv,
    "xlsx": validate_xlsx,
    "mesh": validate_mesh,
}


def main() -> None:
    args = parse_args()
    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    data_root = resolve_path(manifest_path.parent, manifest["data_root"])

    report: dict[str, Any] = {
        "manifest": str(manifest_path),
        "data_root": str(data_root),
        "observation_count": len(manifest["observations"]),
        "checks": [],
    }
    failures = 0
    for observation in manifest["observations"]:
        for check in observation["checks"]:
            validator = VALIDATORS[check["type"]]
            path = resolve_path(data_root, check["path"])
            result = validator(check, path)
            result["observation_id"] = observation["id"]
            report["checks"].append(result)
            if result["status"] != "ok":
                failures += 1

    report["check_count"] = len(report["checks"])
    report["failures"] = failures
    args.write_report.parent.mkdir(parents=True, exist_ok=True)
    args.write_report.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"validated {report['check_count']} checks across {report['observation_count']} observations")
    print(f"failures: {failures}")
    print(f"wrote {args.write_report}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
