#!/usr/bin/env python3
"""Audit a prepared OGS run directory before execution."""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import meshio
import numpy as np


REQUIRED_OUTPUT_VARIABLES = ["pressure", "saturation", "temperature", "displacement", "porosity"]
REQUIRED_CELL_FIELDS = {
    "k_i_rd": {"components": 4},
    "n_rd": {"components": 1},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=Path("inversion_workflow/runs/candidate_smooth_0p025m_search_driver"),
    )
    parser.add_argument("--project-file", default="cd_a_open_niche_quad.prj")
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Defaults to <run-dir>/OGS_RUN_INPUT_AUDIT.json.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        help="Defaults to <run-dir>/OGS_RUN_INPUT_AUDIT.md.",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def clean_xml_text(text: str) -> str:
    return text.strip() if text is not None else ""


def parse_xml_or_fragment(path: Path) -> ET.Element:
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        return ET.fromstring(text)
    except ET.ParseError:
        return ET.fromstring(f"<_wrapped_ogs_fragment>\n{text}\n</_wrapped_ogs_fragment>")


def parse_project_meshes(project_file: Path) -> list[str]:
    root = ET.parse(project_file).getroot()
    return [clean_xml_text(node.text) for node in root.findall(".//meshes/mesh") if clean_xml_text(node.text)]


def parse_process_variable_meshes(path: Path) -> list[str]:
    root = parse_xml_or_fragment(path)
    return sorted({clean_xml_text(node.text) for node in root.findall(".//mesh") if clean_xml_text(node.text)})


def parse_output_variables(path: Path) -> list[str]:
    root = parse_xml_or_fragment(path)
    return [clean_xml_text(node.text) for node in root.findall(".//variables/variable") if clean_xml_text(node.text)]


def parse_mesh_element_parameters(path: Path) -> list[dict[str, str]]:
    root = parse_xml_or_fragment(path)
    rows: list[dict[str, str]] = []
    for parameter in root.findall(".//parameter"):
        name = clean_xml_text(parameter.findtext("name"))
        type_name = clean_xml_text(parameter.findtext("type"))
        field_name = clean_xml_text(parameter.findtext("field_name"))
        if type_name == "MeshElement" or field_name:
            rows.append({"name": name, "type": type_name, "field_name": field_name})
    return rows


def parse_vtu_header(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    header = text.split("<AppendedData", 1)[0]
    piece = re.search(r"<Piece\s+([^>]+)>", header)
    number_of_points = None
    number_of_cells = None
    if piece:
        attrs = dict(re.findall(r'([A-Za-z0-9_:-]+)="([^"]*)"', piece.group(1)))
        number_of_points = int(attrs["NumberOfPoints"]) if attrs.get("NumberOfPoints", "").isdigit() else None
        number_of_cells = int(attrs["NumberOfCells"]) if attrs.get("NumberOfCells", "").isdigit() else None
    data_arrays = []
    for match in re.finditer(r"<DataArray\s+([^>/]+?)(?:/|>)", header):
        attrs = dict(re.findall(r'([A-Za-z0-9_:-]+)="([^"]*)"', match.group(1)))
        data_arrays.append(
            {
                "name": attrs.get("Name", ""),
                "type": attrs.get("type", ""),
                "components": int(attrs.get("NumberOfComponents", "1") or "1"),
                "format": attrs.get("format", ""),
                "offset": attrs.get("offset", ""),
            }
        )
    return {
        "number_of_points": number_of_points,
        "number_of_cells": number_of_cells,
        "data_arrays": data_arrays,
    }


def summarize_mesh(path: Path) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": str(path),
        "exists": path.is_file(),
        "header": {},
        "meshio_readable": False,
        "meshio_error": "",
        "points": None,
        "cells": [],
        "cell_data": [],
        "point_data": [],
    }
    if not path.is_file():
        return record
    try:
        record["header"] = parse_vtu_header(path)
    except Exception as exc:  # noqa: BLE001
        record["header_error"] = f"{type(exc).__name__}: {exc}"
    try:
        mesh = meshio.read(path)
        record["meshio_readable"] = True
        record["points"] = int(mesh.points.shape[0])
        record["cells"] = [{"type": block.type, "count": int(block.data.shape[0])} for block in mesh.cells]
        record["cell_data"] = sorted(mesh.cell_data_dict.keys())
        record["point_data"] = sorted(mesh.point_data.keys())
        record["cell_field_shapes"] = {
            name: list(np.asarray(values[next(iter(values))]).shape)
            for name, values in mesh.cell_data_dict.items()
            if values
        }
    except Exception as exc:  # noqa: BLE001
        record["meshio_error"] = f"{type(exc).__name__}: {exc}"
    return record


def array_names(mesh_record: dict[str, Any]) -> set[str]:
    header = mesh_record.get("header", {})
    return {
        str(array.get("name", ""))
        for array in header.get("data_arrays", [])
        if array.get("name")
    }


def field_check(mesh_record: dict[str, Any], field_name: str, components: int) -> dict[str, Any]:
    shape = mesh_record.get("cell_field_shapes", {}).get(field_name)
    ok = False
    if shape:
        ok = len(shape) == 2 and int(shape[1]) == components
    return {"field_name": field_name, "expected_components": components, "shape": shape, "ok": ok}


def derive_status(
    checks: list[dict[str, Any]],
    mesh_records: list[dict[str, Any]],
    execution_status: dict[str, Any],
) -> str:
    if any(check.get("severity") == "error" for check in checks):
        return "run_inputs_have_errors"
    if any(not mesh.get("meshio_readable") for mesh in mesh_records):
        if execution_status.get("returncode") == 0:
            return "run_inputs_ogs_accepted_with_meshio_submesh_warnings"
        return "run_inputs_present_with_meshio_submesh_warnings"
    return "run_inputs_ready_for_ogs_execution"


def write_markdown(path: Path, audit: dict[str, Any]) -> None:
    lines = [
        "# OGS Run Input Audit",
        "",
        f"- Run directory: `{audit['run_dir']}`",
        f"- Project file: `{audit['project_file']}`",
        f"- Status: `{audit['status']}`",
        "",
        "## Checks",
        "",
        "| Check | Severity | Result |",
        "| --- | --- | --- |",
    ]
    for check in audit["checks"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(check["name"]).replace("|", "/"),
                    str(check["severity"]),
                    str(check["message"]).replace("|", "/"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Meshes",
            "",
            "| Mesh | Header points | Header cells | Header arrays | meshio readable | Error |",
            "| --- | ---: | ---: | --- | --- | --- |",
        ]
    )
    for mesh in audit["meshes"]:
        header = mesh.get("header", {})
        names = ", ".join(array.get("name", "") for array in header.get("data_arrays", []) if array.get("name"))
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{Path(mesh['path']).name}`",
                    str(header.get("number_of_points", "")),
                    str(header.get("number_of_cells", "")),
                    names.replace("|", "/"),
                    str(mesh.get("meshio_readable")),
                    str(mesh.get("meshio_error", "")).replace("|", "/"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The primary projected bulk mesh must be readable and contain `k_i_rd` and",
            "  `n_rd` cell fields before a candidate can be evaluated.",
            "- Boundary/support VTU files are present, referenced, and header-checked for",
            "  point/cell counts plus OGS bulk id arrays. If those files fail `meshio`",
            "  decoding, downstream Python tooling should regenerate them with",
            "  `identifySubdomains` before relying on `meshio` reads.",
            "- This audit does not execute OGS. When an `OGS_EXECUTION_STATUS.json` file",
            "  exists, the audit records whether the target OGS run accepted these inputs.",
            "",
            "## OGS Execution Evidence",
            "",
            f"- Execution status file: `{audit['execution_status_file'] or 'not_found'}`",
            f"- Return code: `{audit['execution_returncode']}`",
            f"- Backend: `{audit['execution_backend'] or 'not_recorded'}`",
            f"- SIF image: `{audit['sif_image'] or 'not_recorded'}`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    project_file = run_dir / args.project_file
    output_json = (args.output_json or (run_dir / "OGS_RUN_INPUT_AUDIT.json")).resolve()
    output_md = (args.output_md or (run_dir / "OGS_RUN_INPUT_AUDIT.md")).resolve()
    execution_status_path = run_dir / "OGS_EXECUTION_STATUS.json"
    execution_status = read_json(execution_status_path)

    checks: list[dict[str, Any]] = []
    if not project_file.is_file():
        raise SystemExit(f"project file not found: {project_file}")

    project_meshes = parse_project_meshes(project_file)
    process_mesh_refs = parse_process_variable_meshes(run_dir / "02_process_variables_TRM.xml")
    output_variables = parse_output_variables(run_dir / "05_time_loop_TRM.xml")
    mesh_parameters = parse_mesh_element_parameters(run_dir / "03_parameters_TRM.xml")
    mesh_records = [summarize_mesh(run_dir / mesh_name) for mesh_name in project_meshes]
    mesh_by_name = {Path(record["path"]).name: record for record in mesh_records}
    primary_mesh = mesh_by_name.get("bulk_w_projections.vtu", {})

    missing_mesh_files = [name for name in project_meshes if not (run_dir / name).is_file()]
    checks.append(
        {
            "name": "project_mesh_files_exist",
            "severity": "error" if missing_mesh_files else "ok",
            "message": "missing: " + ", ".join(missing_mesh_files) if missing_mesh_files else "all project mesh files exist",
        }
    )
    project_mesh_names = {Path(name).stem for name in project_meshes}
    unresolved_refs = [name for name in process_mesh_refs if name not in project_mesh_names]
    checks.append(
        {
            "name": "process_variable_mesh_references",
            "severity": "error" if unresolved_refs else "ok",
            "message": "unresolved: " + ", ".join(unresolved_refs) if unresolved_refs else "all process-variable mesh references are in the project mesh list",
        }
    )
    missing_outputs = [name for name in REQUIRED_OUTPUT_VARIABLES if name not in output_variables]
    checks.append(
        {
            "name": "required_output_variables",
            "severity": "warning" if missing_outputs else "ok",
            "message": "missing: " + ", ".join(missing_outputs) if missing_outputs else "required observation-output variables are requested",
        }
    )
    field_checks = [
        field_check(primary_mesh, field_name, spec["components"])
        for field_name, spec in REQUIRED_CELL_FIELDS.items()
    ]
    bad_fields = [check for check in field_checks if not check["ok"]]
    checks.append(
        {
            "name": "projected_bulk_mesh_fields",
            "severity": "error" if bad_fields else "ok",
            "message": "bad fields: " + ", ".join(check["field_name"] for check in bad_fields) if bad_fields else "bulk_w_projections.vtu contains required k_i_rd and n_rd cell fields",
        }
    )
    unreadable = [Path(mesh["path"]).name for mesh in mesh_records if mesh["exists"] and not mesh["meshio_readable"]]
    checks.append(
        {
            "name": "meshio_readability",
            "severity": "warning" if unreadable else "ok",
            "message": "meshio cannot decode: " + ", ".join(unreadable) if unreadable else "all project meshes are meshio-readable",
        }
    )
    bad_headers = [
        Path(mesh["path"]).name
        for mesh in mesh_records
        if mesh["exists"]
        and (
            mesh.get("header", {}).get("number_of_points") is None
            or mesh.get("header", {}).get("number_of_cells") is None
            or not mesh.get("header", {}).get("data_arrays")
        )
    ]
    checks.append(
        {
            "name": "vtu_header_integrity",
            "severity": "error" if bad_headers else "ok",
            "message": "bad VTU headers: " + ", ".join(bad_headers) if bad_headers else "all VTU XML headers expose point/cell counts and DataArray declarations",
        }
    )
    submesh_names = [name for name in project_meshes if Path(name).name != "bulk_w_projections.vtu"]
    missing_bulk_ids = []
    for name in submesh_names:
        names = array_names(mesh_by_name.get(Path(name).name, {}))
        if "bulk_node_ids" not in names or "bulk_element_ids" not in names:
            missing_bulk_ids.append(Path(name).name)
    checks.append(
        {
            "name": "submesh_bulk_id_arrays",
            "severity": "error" if missing_bulk_ids else "ok",
            "message": "missing bulk id arrays: " + ", ".join(missing_bulk_ids) if missing_bulk_ids else "all boundary/support submeshes expose bulk_node_ids and bulk_element_ids in their VTU headers",
        }
    )
    execution_returncode = execution_status.get("returncode")
    checks.append(
        {
            "name": "ogs_execution_acceptance",
            "severity": "ok" if execution_returncode == 0 else "warning",
            "message": (
                "recorded OGS execution accepted the project inputs with returncode 0"
                if execution_returncode == 0
                else f"recorded OGS execution returncode={execution_returncode}"
                if execution_status
                else "no OGS_EXECUTION_STATUS.json recorded for this run directory"
            ),
        }
    )

    audit = {
        "run_dir": str(run_dir),
        "project_file": str(project_file),
        "status": derive_status(checks, mesh_records, execution_status),
        "execution_status_file": str(execution_status_path) if execution_status_path.exists() else "",
        "execution_returncode": execution_returncode,
        "execution_backend": execution_status.get("execution_backend", ""),
        "sif_image": execution_status.get("sif_image", ""),
        "project_meshes": project_meshes,
        "process_variable_mesh_references": process_mesh_refs,
        "output_variables": output_variables,
        "mesh_element_parameters": mesh_parameters,
        "field_checks": field_checks,
        "checks": checks,
        "meshes": mesh_records,
        "notes": [
            "This audit checks run-input consistency before OGS execution.",
            "Meshio decoding warnings do not prove OGS will reject the file, but they are a reproducibility risk for downstream tooling.",
        ],
    }
    output_json.write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(output_md, audit)
    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    print(f"status: {audit['status']}")


if __name__ == "__main__":
    main()
