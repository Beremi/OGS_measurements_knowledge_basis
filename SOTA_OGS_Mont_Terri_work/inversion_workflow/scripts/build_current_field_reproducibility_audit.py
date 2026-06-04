#!/usr/bin/env python3
"""Verify the current permeability-field package is reproducible and traceable."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


REQUIRED_PACKAGED_FILES = {
    "current_best_bulk_w_projections.vtu",
    "current_best_field_stats.csv",
    "combined_objective_summary.json",
    "combined_objective_components.csv",
    "permeability_fit_summary.json",
    "permeability_fit_evaluation.csv",
    "state_observation_evaluation_summary.json",
    "state_observation_evaluation.csv",
    "ogs_state_samples.csv",
    "ogs_output_inventory.csv",
    "INVERSION_RELEASE_GATE_AUDIT.json",
    "OGS_RUN_INPUT_AUDIT.json",
    "OGS_RUN_INPUT_AUDIT.md",
    "OGS_EXECUTION_STATUS.json",
    "RUN_MANIFEST.json",
}
REQUIRED_RUN_INPUT_FILES = {
    "cd_a_open_niche_quad.prj",
    "01_processes_TRM.xml",
    "02_process_variables_TRM.xml",
    "03_parameters_TRM.xml",
    "03_parameters_TRM_orig.xml",
    "04_media_TRM.xml",
    "04_1_media_aqu_liq.xml",
    "04_2_media_twophase.xml",
    "05_time_loop_TRM.xml",
    "06_nonlinear_solver_T.xml",
    "07_linear_solver_T.xml",
    "08_curves.xml",
    "08_08_open_niche_seasonal.xml",
    "bulk_w_projections.vtu",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package-dir",
        type=Path,
        default=Path("inversion_workflow/current_permeability_field"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/current_permeability_field/CURRENT_FIELD_REPRODUCIBILITY_AUDIT.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/current_permeability_field/current_field_reproducibility_audit.csv"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/current_permeability_field/CURRENT_FIELD_REPRODUCIBILITY_AUDIT.md"),
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_xml(text: str) -> str:
    return text.strip() if text else ""


def parse_xml_or_fragment(path: Path) -> ET.Element:
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        return ET.fromstring(text)
    except ET.ParseError:
        return ET.fromstring(f"<_wrapped_ogs_fragment>\n{text}\n</_wrapped_ogs_fragment>")


def project_references(project_file: Path) -> tuple[list[str], list[str]]:
    root = ET.parse(project_file).getroot()
    meshes = [clean_xml(node.text) for node in root.findall(".//meshes/mesh") if clean_xml(node.text)]
    includes = [clean_xml(node.attrib.get("file", "")) for node in root.findall(".//include") if clean_xml(node.attrib.get("file", ""))]
    return meshes, includes


def nested_includes(path: Path) -> list[str]:
    if not path.exists():
        return []
    root = parse_xml_or_fragment(path)
    return [clean_xml(node.attrib.get("file", "")) for node in root.findall(".//include") if clean_xml(node.attrib.get("file", ""))]


def as_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def as_int(value: Any, default: int = -1) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def add_check(
    checks: list[dict[str, Any]],
    check_id: str,
    group: str,
    passed: bool,
    details: str,
    evidence: str,
    severity: str = "required",
) -> None:
    checks.append(
        {
            "check_id": check_id,
            "group": group,
            "severity": severity,
            "status": "pass" if passed else "fail",
            "details": details,
            "evidence": evidence,
        }
    )


def component_by_name(summary: dict[str, Any], component: str) -> dict[str, Any]:
    for row in summary.get("components", []):
        if row.get("component") == component:
            return row
    return {}


def count_used_rows(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows if as_bool(row.get("used_in_objective", "")))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = ["check_id", "group", "severity", "status", "details", "evidence"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, audit: dict[str, Any]) -> None:
    lines = [
        "# Current Field Reproducibility Audit",
        "",
        "This audit verifies that the packaged current permeability-field deliverable",
        "contains enough local evidence to inspect and rerun the active-objective",
        "incumbent without modifying the frozen source model.",
        "",
        f"- Status: `{audit['status']}`",
        f"- Required failures: `{audit['required_failure_count']}`",
        f"- Warning failures: `{audit['warning_failure_count']}`",
        f"- Package directory: `{audit['package_dir']}`",
        f"- Run id: `{audit['run_id']}`",
        f"- Manifest rows: `{audit['manifest_row_count']}`",
        f"- Run-input snapshot files: `{audit['run_input_snapshot_file_count']}`",
        "",
        "## Checks",
        "",
        "| Check | Group | Severity | Status | Details |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in audit["checks"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['check_id']}`",
                    f"`{row['group']}`",
                    f"`{row['severity']}`",
                    f"`{row['status']}`",
                    str(row["details"]).replace("|", "/"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A pass means the package can be treated as a reproducible active-objective",
            "  incumbent: the field mesh, residual tables, OGS run inputs, execution status,",
            "  and checksum manifest are internally consistent.",
            "- This audit does not promote the field to a final all-measurement inversion",
            "  result.  Stream gates and modelling-policy approvals remain separate.",
            "",
            "## Key Evidence",
            "",
            f"- Active objective: `{audit['total_active_objective_value']}`",
            f"- Direct rows: `{audit['direct_used_rows']}`",
            f"- State rows: `{audit['state_used_rows']}`",
            f"- OGS return code: `{audit['ogs_returncode']}`",
            f"- Field cells: `{audit['field_triangle6_cell_count']}`",
            f"- Positive-definite cells: `{audit['field_positive_definite_cell_count']}`",
            f"- Project file: `{audit['project_file']}`",
            f"- Project references checked: `{audit['project_reference_count']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    package_dir = args.package_dir
    summary_path = package_dir / "CURRENT_PERMEABILITY_FIELD_SUMMARY.json"
    manifest_path = package_dir / "packaged_file_manifest.csv"
    summary = read_json(summary_path)
    checks: list[dict[str, Any]] = []

    add_check(
        checks,
        "summary_exists",
        "package",
        summary_path.exists(),
        f"summary path exists={summary_path.exists()}",
        str(summary_path),
    )
    add_check(
        checks,
        "package_status",
        "package",
        summary.get("status") == "current_permeability_field_package_generated",
        f"status={summary.get('status')}",
        str(summary_path),
    )
    add_check(
        checks,
        "markdown_exists",
        "package",
        (package_dir / "CURRENT_PERMEABILITY_FIELD.md").exists(),
        "current field package markdown exists",
        str(package_dir / "CURRENT_PERMEABILITY_FIELD.md"),
    )

    manifest_rows = read_csv_rows(manifest_path)
    summary_manifest = summary.get("packaged_file_manifest", [])
    add_check(
        checks,
        "manifest_exists",
        "manifest",
        manifest_path.exists(),
        f"manifest rows={len(manifest_rows)}",
        str(manifest_path),
    )
    add_check(
        checks,
        "manifest_row_count_matches_summary",
        "manifest",
        len(manifest_rows) == len(summary_manifest) and len(manifest_rows) > 0,
        f"csv rows={len(manifest_rows)}, summary rows={len(summary_manifest)}",
        f"{manifest_path}; {summary_path}",
    )

    missing_or_bad_hashes = []
    for row in manifest_rows:
        path = Path(row.get("packaged_path", ""))
        expected_sha = row.get("sha256", "")
        expected_size = int(row.get("size_bytes", "0") or 0)
        if not path.exists():
            missing_or_bad_hashes.append(f"{path}: missing")
            continue
        actual_size = path.stat().st_size
        actual_sha = sha256_file(path)
        if actual_size != expected_size or actual_sha != expected_sha:
            missing_or_bad_hashes.append(f"{path}: size/sha mismatch")
    add_check(
        checks,
        "manifest_hashes_verify",
        "manifest",
        not missing_or_bad_hashes and bool(manifest_rows),
        "all manifest sizes and SHA256 values verify" if not missing_or_bad_hashes else "; ".join(missing_or_bad_hashes[:8]),
        str(manifest_path),
    )

    manifest_names = {row.get("file_name", "") for row in manifest_rows}
    missing_required_packaged = sorted(REQUIRED_PACKAGED_FILES - manifest_names)
    add_check(
        checks,
        "required_packaged_files_present",
        "manifest",
        not missing_required_packaged,
        "all required packaged evidence files are present" if not missing_required_packaged else "missing: " + ", ".join(missing_required_packaged),
        str(manifest_path),
    )

    run_input_dir = Path(summary.get("run_input_dir", package_dir / "ogs_run_inputs"))
    run_input_files = sorted(path.name for path in run_input_dir.iterdir() if path.is_file()) if run_input_dir.exists() else []
    missing_run_inputs = sorted(REQUIRED_RUN_INPUT_FILES - set(run_input_files))
    add_check(
        checks,
        "run_input_snapshot_required_files",
        "run_input_snapshot",
        run_input_dir.exists() and not missing_run_inputs,
        f"snapshot files={len(run_input_files)}" if not missing_run_inputs else "missing: " + ", ".join(missing_run_inputs),
        str(run_input_dir),
    )

    project_file = run_input_dir / "cd_a_open_niche_quad.prj"
    project_ref_count = 0
    missing_project_refs: list[str] = []
    if project_file.exists():
        meshes, includes = project_references(project_file)
        project_refs = meshes + includes
        project_ref_count = len(project_refs)
        for ref in project_refs:
            if not (run_input_dir / ref.replace("./", "")).exists():
                missing_project_refs.append(ref)
    else:
        meshes = []
        includes = []
        missing_project_refs.append("cd_a_open_niche_quad.prj")
    add_check(
        checks,
        "project_references_resolve",
        "run_input_snapshot",
        not missing_project_refs and project_ref_count > 0,
        f"project refs={project_ref_count}" if not missing_project_refs else "missing refs: " + ", ".join(missing_project_refs),
        str(project_file),
    )

    missing_nested_includes = []
    for include in includes:
        include_path = run_input_dir / include.replace("./", "")
        for nested in nested_includes(include_path):
            if not (run_input_dir / nested.replace("./", "")).exists():
                missing_nested_includes.append(f"{include}->{nested}")
    add_check(
        checks,
        "nested_includes_resolve",
        "run_input_snapshot",
        not missing_nested_includes,
        "all nested include files resolve" if not missing_nested_includes else "missing nested refs: " + ", ".join(missing_nested_includes),
        str(run_input_dir),
    )

    combined = read_json(package_dir / "combined_objective_summary.json")
    direct_component = component_by_name(combined, "direct_permeability_pulse_tests")
    state_component = component_by_name(combined, "state_observations")
    objective_sum = sum(
        float(row.get("objective_value") or 0.0)
        for row in combined.get("components", [])
        if row.get("active_in_combined_objective")
    )
    total = float(combined.get("total_active_objective_value") or math.nan)
    add_check(
        checks,
        "combined_objective_components_sum",
        "objective",
        math.isfinite(total) and abs(objective_sum - total) <= 1e-9,
        f"component sum={objective_sum}; total={total}",
        str(package_dir / "combined_objective_summary.json"),
    )
    add_check(
        checks,
        "expected_active_components",
        "objective",
        int(combined.get("active_component_count", -1) or -1) == 2,
        f"active_component_count={combined.get('active_component_count')}",
        str(package_dir / "combined_objective_summary.json"),
    )

    direct_rows = read_csv_rows(package_dir / "permeability_fit_evaluation.csv")
    state_rows = read_csv_rows(package_dir / "state_observation_evaluation.csv")
    direct_used = count_used_rows(direct_rows)
    state_used = count_used_rows(state_rows)
    add_check(
        checks,
        "direct_residual_rows_match_summary",
        "objective",
        direct_used == int(direct_component.get("used_rows", -1) or -1),
        f"csv used rows={direct_used}; component used rows={direct_component.get('used_rows')}",
        str(package_dir / "permeability_fit_evaluation.csv"),
    )
    add_check(
        checks,
        "state_residual_rows_match_summary",
        "objective",
        state_used == int(state_component.get("used_rows", -1) or -1),
        f"csv used rows={state_used}; component used rows={state_component.get('used_rows')}",
        str(package_dir / "state_observation_evaluation.csv"),
    )

    release = read_json(package_dir / "INVERSION_RELEASE_GATE_AUDIT.json")
    add_check(
        checks,
        "release_gate_passed",
        "release_gate",
        release.get("status") == "pass" and as_int(release.get("failure_count"), -1) == 0,
        f"status={release.get('status')}; failures={release.get('failure_count')}",
        str(package_dir / "INVERSION_RELEASE_GATE_AUDIT.json"),
    )

    execution = read_json(package_dir / "OGS_EXECUTION_STATUS.json")
    add_check(
        checks,
        "ogs_execution_returncode_zero",
        "ogs_execution",
        execution.get("returncode") == 0,
        f"returncode={execution.get('returncode')}",
        str(package_dir / "OGS_EXECUTION_STATUS.json"),
    )

    input_audit = read_json(package_dir / "OGS_RUN_INPUT_AUDIT.json")
    input_status = input_audit.get("status", "")
    input_errors = [
        row.get("name", "")
        for row in input_audit.get("checks", [])
        if row.get("severity") == "error"
    ]
    add_check(
        checks,
        "ogs_run_input_audit_accepts_inputs",
        "run_input_snapshot",
        input_status in {"run_inputs_ogs_accepted_with_meshio_submesh_warnings", "run_inputs_ready_for_ogs_execution"} and not input_errors,
        f"status={input_status}; error checks={input_errors}",
        str(package_dir / "OGS_RUN_INPUT_AUDIT.json"),
    )

    field = summary.get("field", {})
    cells = as_int(field.get("triangle6_cell_count"), 0)
    positive = as_int(field.get("positive_definite_cell_count"), 0)
    non_positive = as_int(field.get("non_positive_definite_cell_count"), -1)
    add_check(
        checks,
        "field_positive_definite",
        "field",
        cells > 0 and positive == cells and non_positive == 0,
        f"cells={cells}; positive={positive}; non_positive={non_positive}",
        str(summary_path),
    )
    add_check(
        checks,
        "fixed_porosity_support",
        "field",
        field.get("field_metrics", {}).get("n_rd", {}).get("min") == 0.105
        and field.get("field_metrics", {}).get("n_rd", {}).get("max") == 0.105,
        (
            "n_rd min/max="
            f"{field.get('field_metrics', {}).get('n_rd', {}).get('min')}/"
            f"{field.get('field_metrics', {}).get('n_rd', {}).get('max')}"
        ),
        str(summary_path),
    )

    required_failures = [row for row in checks if row["severity"] == "required" and row["status"] != "pass"]
    warning_failures = [row for row in checks if row["severity"] == "warning" and row["status"] != "pass"]
    status = "current_field_reproducibility_verified" if not required_failures else "current_field_reproducibility_failed"
    audit = {
        "status": status,
        "package_dir": str(package_dir),
        "run_id": summary.get("run_id"),
        "required_failure_count": len(required_failures),
        "warning_failure_count": len(warning_failures),
        "check_count": len(checks),
        "manifest_row_count": len(manifest_rows),
        "run_input_snapshot_file_count": len(run_input_files),
        "project_reference_count": project_ref_count,
        "project_file": str(project_file),
        "total_active_objective_value": combined.get("total_active_objective_value"),
        "direct_used_rows": direct_used,
        "state_used_rows": state_used,
        "ogs_returncode": execution.get("returncode"),
        "field_triangle6_cell_count": cells,
        "field_positive_definite_cell_count": positive,
        "checks": checks,
        "source_artifacts": [
            str(summary_path),
            str(manifest_path),
            str(package_dir / "current_best_bulk_w_projections.vtu"),
            str(package_dir / "permeability_fit_evaluation.csv"),
            str(package_dir / "state_observation_evaluation.csv"),
            str(package_dir / "ogs_state_samples.csv"),
            str(package_dir / "OGS_EXECUTION_STATUS.json"),
            str(package_dir / "OGS_RUN_INPUT_AUDIT.json"),
            str(run_input_dir),
        ],
    }
    args.output_json.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    write_csv(args.output_csv, checks)
    write_markdown(args.output_md, audit)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.output_md}")
    print(f"status: {status}")


if __name__ == "__main__":
    main()
