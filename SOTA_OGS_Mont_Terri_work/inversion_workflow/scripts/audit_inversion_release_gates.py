#!/usr/bin/env python3
"""Audit prepared OGS runs against the staged inversion parameter-release plan."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import numpy as np


MEDIA_FILES = ["04_media_TRM.xml", "04_1_media_aqu_liq.xml", "04_2_media_twophase.xml"]
ACTIVE_PARAMETER_FIELDS = {"k_i": "k_i_rd"}
FIXED_SUPPORT_FIELDS = {"phi": "n_rd"}
BLOCKED_OR_LATER_ENTRIES = {
    "open_niche_seasonal",
    "pressure_scaling_factor",
    "CTE",
    "E",
    "G",
    "nu",
    "biot",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release-plan",
        type=Path,
        default=Path("inversion_workflow/inversion_parameter_release_plan.csv"),
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        action="append",
        help=(
            "Prepared OGS run directory to audit. May be repeated. If omitted, "
            "regularized_ogs_candidate_* run directories are audited."
        ),
    )
    parser.add_argument(
        "--reference-dir",
        type=Path,
        default=Path("GESA_model_original/projection_on_mesh_2025-09-05"),
        help="Projection model directory used as the fixed XML reference.",
    )
    parser.add_argument(
        "--base-parameters",
        type=Path,
        default=Path("ogs_settings/03_parameters_TRM.xml"),
        help="Base XML parameter file used to read fixed scalar support values such as phi.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/inversion_release_gate_audit.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/inversion_release_gate_audit.md"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/inversion_release_gate_audit.csv"),
    )
    return parser.parse_args()


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_xml_fragment(path: Path) -> ET.Element:
    text = path.read_text(encoding="utf-8")
    return ET.fromstring(f"<root>\n{text}\n</root>")


def direct_text(element: ET.Element, tag: str) -> str:
    values = [child.text.strip() for child in element.findall(tag) if child.text and child.text.strip()]
    return " | ".join(values)


def parse_parameters(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    root = parse_xml_fragment(path)
    parameters: dict[str, dict[str, str]] = {}
    for parameter in root.findall("parameter"):
        name = direct_text(parameter, "name")
        if not name:
            continue
        record = {
            "type": direct_text(parameter, "type"),
            "value": direct_text(parameter, "values") or direct_text(parameter, "value"),
            "field_name": direct_text(parameter, "field_name"),
            "expression": direct_text(parameter, "expression"),
            "curve": direct_text(parameter, "curve"),
            "base_parameter": direct_text(parameter, "parameter"),
        }
        parameters[name] = {key: value for key, value in record.items() if value}
    return parameters


def parse_property_records(path: Path) -> dict[str, list[dict[str, str]]]:
    if not path.exists():
        return {}
    root = parse_xml_fragment(path)
    output: dict[str, list[dict[str, str]]] = {}
    for property_node in root.iter("property"):
        name = direct_text(property_node, "name")
        if not name:
            continue
        record: dict[str, str] = {
            "type": direct_text(property_node, "type"),
            "parameter_name": direct_text(property_node, "parameter_name"),
        }
        for child in property_node:
            if child.tag in {"name", "type", "parameter_name"}:
                continue
            if child.text and child.text.strip():
                record[child.tag] = child.text.strip()
        output.setdefault(name, []).append({key: value for key, value in record.items() if value})
    return output


def normalized_text_hash(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    normalized = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def read_release_plan(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def status_rank(status: str) -> int:
    return {"pass": 0, "warning": 1, "fail": 2}.get(status, 2)


def add_check(
    checks: list[dict[str, Any]],
    *,
    run_id: str,
    check_name: str,
    status: str,
    severity: str,
    detail: str,
    source_file: str = "",
) -> None:
    checks.append(
        {
            "run_id": run_id,
            "check_name": check_name,
            "status": status,
            "severity": severity,
            "detail": detail,
            "source_file": source_file,
        }
    )


def load_mesh_field(mesh_path: Path, field_name: str) -> np.ndarray | None:
    try:
        import meshio  # type: ignore
    except ImportError:
        return None
    mesh = meshio.read(mesh_path)
    if field_name not in mesh.cell_data:
        return None
    arrays = [np.asarray(array) for array in mesh.cell_data[field_name]]
    if not arrays:
        return None
    return np.concatenate(arrays, axis=0)


def compare_numeric_arrays(left: np.ndarray, right: np.ndarray) -> dict[str, Any]:
    same_shape = tuple(left.shape) == tuple(right.shape)
    if not same_shape:
        return {
            "same_shape": False,
            "max_abs_difference": None,
            "left_shape": tuple(left.shape),
            "right_shape": tuple(right.shape),
            "allclose": False,
        }
    diff = np.asarray(left, dtype=float) - np.asarray(right, dtype=float)
    max_abs = float(np.nanmax(np.abs(diff))) if diff.size else 0.0
    return {
        "same_shape": True,
        "max_abs_difference": max_abs,
        "left_shape": tuple(left.shape),
        "right_shape": tuple(right.shape),
        "allclose": bool(np.allclose(left, right, rtol=0.0, atol=1e-14)),
    }


def read_output_variables(path: Path) -> list[str]:
    if not path.exists():
        return []
    root = parse_xml_fragment(path)
    variables = []
    for variables_node in root.iter("variables"):
        for child in variables_node.findall("variable"):
            if child.text and child.text.strip():
                variables.append(child.text.strip())
        if variables:
            break
    return variables


def discover_run_dirs(repo: Path, explicit: list[Path] | None) -> list[Path]:
    if explicit:
        return [path.resolve() for path in explicit]
    run_root = repo / "inversion_workflow" / "runs"
    candidates = sorted(path.resolve() for path in run_root.glob("regularized_ogs_candidate_*") if path.is_dir())
    return [
        path
        for path in candidates
        if (path / "RUN_MANIFEST.json").is_file() and (path / "03_parameters_TRM.xml").is_file()
    ]


def numeric_scalar(value: str | None) -> float | None:
    if value is None:
        return None
    parts = str(value).replace(",", " ").split()
    if len(parts) != 1:
        return None
    try:
        return float(parts[0])
    except ValueError:
        return None


def audit_one_run(
    run_dir: Path,
    reference_dir: Path,
    base_parameters_path: Path,
    release_plan: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    run_id = run_dir.name
    checks: list[dict[str, Any]] = []
    run_parameters_path = run_dir / "03_parameters_TRM.xml"
    reference_parameters_path = reference_dir / "03_parameters_TRM.xml"
    run_parameters = parse_parameters(run_parameters_path)
    reference_parameters = parse_parameters(reference_parameters_path)
    base_parameters = parse_parameters(base_parameters_path)
    base_phi_value = numeric_scalar(base_parameters.get("phi", {}).get("value"))

    if not release_plan:
        add_check(
            checks,
            run_id=run_id,
            check_name="release_plan_present",
            status="fail",
            severity="error",
            detail="release plan CSV is missing or empty",
        )
    else:
        active_rows = [row for row in release_plan if row.get("release_stage") == "stage_1_active_field"]
        active_text = "; ".join(row.get("parameter_group", "") for row in active_rows)
        expected = "intrinsic permeability tensor magnitude field"
        status = "pass" if expected in active_text else "fail"
        add_check(
            checks,
            run_id=run_id,
            check_name="release_plan_active_field",
            status=status,
            severity="error" if status == "fail" else "info",
            detail=f"stage-1 active rows: {active_text or 'none'}",
            source_file="inversion_workflow/inversion_parameter_release_plan.csv",
        )

    if not run_parameters:
        add_check(
            checks,
            run_id=run_id,
            check_name="run_parameter_file_present",
            status="fail",
            severity="error",
            detail="03_parameters_TRM.xml is missing or empty",
            source_file=str(run_parameters_path),
        )
    if not reference_parameters:
        add_check(
            checks,
            run_id=run_id,
            check_name="reference_parameter_file_present",
            status="fail",
            severity="error",
            detail="reference 03_parameters_TRM.xml is missing or empty",
            source_file=str(reference_parameters_path),
        )

    for parameter_name, field_name in ACTIVE_PARAMETER_FIELDS.items():
        record = run_parameters.get(parameter_name, {})
        status = "pass" if record.get("type") == "MeshElement" and record.get("field_name") == field_name else "fail"
        add_check(
            checks,
            run_id=run_id,
            check_name=f"active_field_{parameter_name}",
            status=status,
            severity="error" if status == "fail" else "info",
            detail=f"{parameter_name} definition: {record}",
            source_file=str(run_parameters_path),
        )

    for parameter_name, field_name in FIXED_SUPPORT_FIELDS.items():
        record = run_parameters.get(parameter_name, {})
        status = "pass" if record.get("type") == "MeshElement" and record.get("field_name") == field_name else "fail"
        add_check(
            checks,
            run_id=run_id,
            check_name=f"fixed_support_field_{parameter_name}",
            status=status,
            severity="error" if status == "fail" else "info",
            detail=f"{parameter_name} definition: {record}",
            source_file=str(run_parameters_path),
        )

    drift_parameters = []
    for name in sorted(set(reference_parameters) | set(run_parameters)):
        if reference_parameters.get(name) != run_parameters.get(name):
            drift_parameters.append(name)
    status = "pass" if not drift_parameters else "fail"
    add_check(
        checks,
        run_id=run_id,
        check_name="parameter_xml_matches_projection_reference",
        status=status,
        severity="error" if status == "fail" else "info",
        detail=(
            "03_parameters_TRM.xml matches projection reference"
            if not drift_parameters
            else "changed parameter definitions: " + ", ".join(drift_parameters)
        ),
        source_file=str(run_parameters_path),
    )

    for name in sorted(BLOCKED_OR_LATER_ENTRIES):
        if name in run_parameters or name in reference_parameters:
            status = "pass" if run_parameters.get(name) == reference_parameters.get(name) else "fail"
            add_check(
                checks,
                run_id=run_id,
                check_name=f"blocked_or_later_parameter_fixed_{name}",
                status=status,
                severity="error" if status == "fail" else "info",
                detail=f"run={run_parameters.get(name)}; reference={reference_parameters.get(name)}",
                source_file=str(run_parameters_path),
            )

    for file_name in MEDIA_FILES:
        run_file = run_dir / file_name
        ref_file = reference_dir / file_name
        if not run_file.exists() or not ref_file.exists():
            add_check(
                checks,
                run_id=run_id,
                check_name=f"media_xml_present_{file_name}",
                status="fail",
                severity="error",
                detail=f"run exists={run_file.exists()}, reference exists={ref_file.exists()}",
                source_file=str(run_file),
            )
            continue
        status = "pass" if normalized_text_hash(run_file) == normalized_text_hash(ref_file) else "fail"
        add_check(
            checks,
            run_id=run_id,
            check_name=f"media_xml_matches_reference_{file_name}",
            status=status,
            severity="error" if status == "fail" else "info",
            detail=(
                "media XML matches projection reference"
                if status == "pass"
                else "media XML differs from projection reference"
            ),
            source_file=str(run_file),
        )

    # Explicit retention and swelling property records make any future release drift easy to see.
    run_twophase = parse_property_records(run_dir / "04_2_media_twophase.xml")
    ref_twophase = parse_property_records(reference_dir / "04_2_media_twophase.xml")
    for property_name in ["saturation", "relative_permeability", "bishops_effective_stress"]:
        status = "pass" if run_twophase.get(property_name) == ref_twophase.get(property_name) else "fail"
        add_check(
            checks,
            run_id=run_id,
            check_name=f"retention_property_fixed_{property_name}",
            status=status,
            severity="error" if status == "fail" else "info",
            detail=f"run={run_twophase.get(property_name)}; reference={ref_twophase.get(property_name)}",
            source_file=str(run_dir / "04_2_media_twophase.xml"),
        )

    run_mesh = run_dir / "bulk_w_projections.vtu"
    reference_mesh = reference_dir / "bulk_w_projections.vtu"
    if not run_mesh.exists():
        add_check(
            checks,
            run_id=run_id,
            check_name="run_mesh_present",
            status="fail",
            severity="error",
            detail="bulk_w_projections.vtu is missing",
            source_file=str(run_mesh),
        )
    elif not reference_mesh.exists():
        add_check(
            checks,
            run_id=run_id,
            check_name="reference_mesh_present",
            status="fail",
            severity="error",
            detail="reference bulk_w_projections.vtu is missing",
            source_file=str(reference_mesh),
        )
    else:
        run_phi = load_mesh_field(run_mesh, "n_rd")
        if run_phi is None:
            add_check(
                checks,
                run_id=run_id,
                check_name="fixed_porosity_field_n_rd_readable",
                status="warning",
                severity="warning",
                detail="could not read n_rd from run mesh; meshio may be unavailable or field missing",
                source_file=str(run_mesh),
            )
        elif base_phi_value is None:
            add_check(
                checks,
                run_id=run_id,
                check_name="fixed_porosity_field_n_rd_has_base_reference",
                status="warning",
                severity="warning",
                detail=f"could not parse scalar phi value from {base_parameters_path}",
                source_file=str(base_parameters_path),
            )
        else:
            expected = np.full_like(run_phi.astype(float), base_phi_value, dtype=float)
            comparison = compare_numeric_arrays(run_phi.astype(float), expected)
            status = "pass" if comparison["allclose"] else "fail"
            detail = dict(comparison)
            detail["expected_phi"] = base_phi_value
            detail["observed_min"] = float(np.nanmin(run_phi.astype(float)))
            detail["observed_max"] = float(np.nanmax(run_phi.astype(float)))
            add_check(
                checks,
                run_id=run_id,
                check_name="fixed_porosity_field_n_rd_unchanged",
                status=status,
                severity="error" if status == "fail" else "info",
                detail=json.dumps(detail, sort_keys=True),
                source_file=str(run_mesh),
            )
        run_k = load_mesh_field(run_mesh, "k_i_rd")
        if run_k is None:
            add_check(
                checks,
                run_id=run_id,
                check_name="active_permeability_field_k_i_rd_present",
                status="fail",
                severity="error",
                detail="could not read k_i_rd from run mesh",
                source_file=str(run_mesh),
            )
        else:
            finite = np.isfinite(run_k.astype(float))
            status = "pass" if bool(finite.all()) and run_k.size > 0 else "fail"
            add_check(
                checks,
                run_id=run_id,
                check_name="active_permeability_field_k_i_rd_present",
                status=status,
                severity="error" if status == "fail" else "info",
                detail=json.dumps(
                    {
                        "shape": tuple(run_k.shape),
                        "finite_values": int(finite.sum()),
                        "total_values": int(run_k.size),
                        "min": float(np.nanmin(run_k.astype(float))),
                        "max": float(np.nanmax(run_k.astype(float))),
                    },
                    sort_keys=True,
                ),
                source_file=str(run_mesh),
            )

    output_variables = read_output_variables(run_dir / "05_time_loop_TRM.xml")
    add_check(
        checks,
        run_id=run_id,
        check_name="output_variables_recorded",
        status="pass" if output_variables else "warning",
        severity="info" if output_variables else "warning",
        detail=", ".join(output_variables) if output_variables else "no output variables parsed",
        source_file=str(run_dir / "05_time_loop_TRM.xml"),
    )

    worst = max((status_rank(check["status"]) for check in checks), default=2)
    status = {0: "pass", 1: "warning", 2: "fail"}[worst]
    run_summary = {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "status": status,
        "check_count": len(checks),
        "failure_count": sum(1 for check in checks if check["status"] == "fail"),
        "warning_count": sum(1 for check in checks if check["status"] == "warning"),
        "output_variables": output_variables,
    }
    return checks, run_summary


def write_markdown(path: Path, summary: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    lines = [
        "# Inversion Release Gate Audit",
        "",
        "This audit verifies that prepared OGS runs still obey the staged parameter-release plan.",
        "The current allowed release is narrow: `k_i_rd` may vary as the active permeability",
        "tensor-magnitude field, while `n_rd` porosity and all retention, mechanical, thermal,",
        "boundary, and initialization parameters remain fixed until their gates are satisfied.",
        "",
        f"- Overall status: `{summary['status']}`",
        f"- Runs audited: {summary['run_count']}",
        f"- Checks: {summary['check_count']}",
        f"- Failures: {summary['failure_count']}",
        f"- Warnings: {summary['warning_count']}",
        "",
        "## Run Summary",
        "",
        "| Run | Status | Failures | Warnings | Output variables |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for run in summary["runs"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{run['run_id']}`",
                    f"`{run['status']}`",
                    str(run["failure_count"]),
                    str(run["warning_count"]),
                    "`" + ", ".join(run.get("output_variables", [])) + "`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Non-Passing Checks",
            "",
            "| Run | Check | Status | Detail |",
            "| --- | --- | --- | --- |",
        ]
    )
    nonpassing = [check for check in checks if check["status"] != "pass"]
    if not nonpassing:
        lines.append("| all | all checks | `pass` | no warnings or failures |")
    for check in nonpassing:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{check['run_id']}`",
                    f"`{check['check_name']}`",
                    f"`{check['status']}`",
                    str(check["detail"]).replace("|", "\\|"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A passing audit means the candidate run varies the mesh permeability field while",
            "  preserving the staged fixed-parameter assumptions recorded in the release plan.",
            "- It does not mean OGS has executed or that the fit is physically accepted; state",
            "  residuals still require actual OGS output VTU files.",
            "- Any failure here should be treated as a hard stop before ranking the candidate,",
            "  because it means the inverse problem no longer matches the documented stage.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo = repo_root_from_script()
    run_dirs = discover_run_dirs(repo, args.run_dir)
    release_plan = read_release_plan(args.release_plan)
    all_checks: list[dict[str, Any]] = []
    run_summaries: list[dict[str, Any]] = []

    for run_dir in run_dirs:
        checks, run_summary = audit_one_run(
            run_dir,
            args.reference_dir.resolve(),
            args.base_parameters.resolve(),
            release_plan,
        )
        all_checks.extend(checks)
        run_summaries.append(run_summary)

    worst = max((status_rank(run["status"]) for run in run_summaries), default=2)
    status = {0: "pass", 1: "warning", 2: "fail"}[worst]
    summary = {
        "status": status,
        "run_count": len(run_summaries),
        "check_count": len(all_checks),
        "failure_count": sum(1 for check in all_checks if check["status"] == "fail"),
        "warning_count": sum(1 for check in all_checks if check["status"] == "warning"),
        "runs": run_summaries,
        "release_plan": str(args.release_plan),
        "reference_dir": str(args.reference_dir),
        "base_parameters": str(args.base_parameters),
        "notes": [
            "The release gate allows k_i_rd as the active stage-1 parameter field.",
            "n_rd must remain fixed support; retention, mechanical, thermal, boundary, and initialization parameters must match the projection reference.",
            "This audit checks candidate-run configuration, not physical acceptance of the OGS result.",
        ],
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    with args.output_csv.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["run_id", "check_name", "status", "severity", "detail", "source_file"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_checks)
    write_markdown(args.output_md, summary, all_checks)

    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.output_md}")
    print(f"status: {status}")
    if status == "fail":
        sys.exit(1)


if __name__ == "__main__":
    main()
