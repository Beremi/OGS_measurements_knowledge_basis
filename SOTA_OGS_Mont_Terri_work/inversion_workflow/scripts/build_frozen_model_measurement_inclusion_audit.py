#!/usr/bin/env python3
"""Audit the frozen OGS model boundary and measurement-inclusion evidence."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/frozen_model_measurement_inclusion_audit.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/frozen_model_measurement_inclusion_audit_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/frozen_model_measurement_inclusion_audit.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/model_formulation_audit/derived_files"),
    )
    parser.add_argument(
        "--measurement-info-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements_info"),
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


def count_csv_rows(path: Path) -> int:
    return len(read_csv_rows(path))


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def status_rank(status: str) -> int:
    return {"pass": 0, "warning": 1, "fail": 2}.get(status, 2)


def add_row(
    rows: list[dict[str, str]],
    *,
    audit_area: str,
    check_id: str,
    status: str,
    severity: str,
    detail: str,
    source_artifacts: list[str],
) -> None:
    rows.append(
        {
            "audit_area": audit_area,
            "check_id": check_id,
            "status": status,
            "severity": severity,
            "detail": detail,
            "source_artifacts": "; ".join(source_artifacts),
        }
    )


def discover_run_manifests(run_root: Path) -> list[Path]:
    if not run_root.exists():
        return []
    return sorted(path for path in run_root.rglob("RUN_MANIFEST.json") if path.is_file())


def check_manifest_projection_sources(manifests: list[Path], expected_suffix: str) -> tuple[int, list[str]]:
    missing_or_wrong: list[str] = []
    for manifest_path in manifests:
        manifest = read_json(manifest_path)
        source_dir = str(manifest.get("source_projection_model_dir", ""))
        if not source_dir.endswith(expected_suffix):
            missing_or_wrong.append(str(manifest_path))
    return len(manifests), missing_or_wrong


def count_measurement_info_folders(measurement_info_dir: Path) -> int:
    if not measurement_info_dir.exists():
        return 0
    return sum(
        1
        for path in measurement_info_dir.iterdir()
        if path.is_dir() and (path / "MEASUREMENT_INFO.md").is_file()
    )


def summarize_measurement_info(measurement_info_dir: Path) -> dict[str, Any]:
    manifest_path = measurement_info_dir / "measurement_info_manifest.csv"
    archive_path = measurement_info_dir / "archive_member_catalog.csv"
    workbook_path = measurement_info_dir / "workbook_sheet_deep_index.csv"
    manifest_rows = read_csv_rows(manifest_path)
    source_rows = len(manifest_rows)
    kinds: dict[str, int] = {}
    for row in manifest_rows:
        kind = row.get("kind", "")
        kinds[kind] = kinds.get(kind, 0) + 1
    return {
        "folder_count": count_measurement_info_folders(measurement_info_dir),
        "source_file_rows": source_rows,
        "archive_member_rows": count_csv_rows(archive_path),
        "workbook_sheet_rows": count_csv_rows(workbook_path),
        "kind_counts": dict(sorted(kinds.items())),
        "manifest_path": str(manifest_path),
        "archive_catalog_path": str(archive_path),
        "workbook_index_path": str(workbook_path),
    }


def build_rows(args: argparse.Namespace) -> tuple[list[dict[str, str]], dict[str, Any]]:
    rows: list[dict[str, str]] = []

    projection_dir = Path("GESA_model_original/projection_on_mesh_2025-09-05")
    source_model_dirs = [
        Path("GESA_model_original/2025-04-03_CDA_N4_2D_250403"),
        Path("GESA_model_original/2025-05-09_CDA_N4_2D_250509"),
        projection_dir,
    ]
    missing_source_dirs = [str(path) for path in source_model_dirs if not path.exists()]
    add_row(
        rows,
        audit_area="source_model",
        check_id="source_model_directories_present",
        status="pass" if not missing_source_dirs else "fail",
        severity="error" if missing_source_dirs else "info",
        detail=(
            "April, May, and projection model directories are present."
            if not missing_source_dirs
            else "Missing source model directories: " + "; ".join(missing_source_dirs)
        ),
        source_artifacts=[str(path) for path in source_model_dirs],
    )

    projection_files = [
        projection_dir / "README.txt",
        projection_dir / "03_parameters_TRM.xml",
        projection_dir / "04_media_TRM.xml",
        projection_dir / "04_2_media_twophase.xml",
        projection_dir / "05_time_loop_TRM.xml",
        projection_dir / "bulk.vtu",
        projection_dir / "bulk_w_projections.vtu",
        projection_dir / "cd_a_open_niche_quad.prj",
    ]
    missing_projection_files = [str(path) for path in projection_files if not path.exists()]
    add_row(
        rows,
        audit_area="source_model",
        check_id="projection_reference_files_present",
        status="pass" if not missing_projection_files else "fail",
        severity="error" if missing_projection_files else "info",
        detail=(
            f"Projection reference files present={len(projection_files)}."
            if not missing_projection_files
            else "Missing projection reference files: " + "; ".join(missing_projection_files)
        ),
        source_artifacts=[str(path) for path in projection_files],
    )

    formulation = read_json(Path("inversion_workflow/ogs_formulation_consistency_audit_summary.json"))
    formulation_pass = (
        formulation.get("status") == "ogs_formulation_consistency_audit_generated"
        and formulation.get("all_hard_checks_pass") is True
        and int(formulation.get("fail_count", 0) or 0) == 0
    )
    add_row(
        rows,
        audit_area="source_model",
        check_id="formulation_consistency_passed",
        status="pass" if formulation_pass else "fail",
        severity="error" if not formulation_pass else "info",
        detail=(
            f"status={formulation.get('status')}; checks={formulation.get('check_count')}; "
            f"failures={formulation.get('fail_count')}; process={formulation.get('process_type')}; "
            f"run-local mesh fields={formulation.get('run_local_field_parameters')}; "
            f"tracked caveats={formulation.get('tracked_caveat_count')}."
        ),
        source_artifacts=[
            "inversion_workflow/ogs_formulation_consistency_audit.md",
            "inversion_workflow/ogs_formulation_consistency_audit_summary.json",
        ],
    )

    run_manifests = discover_run_manifests(Path("inversion_workflow/runs"))
    manifest_count, wrong_manifests = check_manifest_projection_sources(
        run_manifests,
        "GESA_model_original/projection_on_mesh_2025-09-05",
    )
    add_row(
        rows,
        audit_area="source_model",
        check_id="run_manifests_reference_projection_model",
        status="pass" if manifest_count > 0 and not wrong_manifests else "fail",
        severity="error" if wrong_manifests or manifest_count == 0 else "info",
        detail=(
            f"RUN_MANIFEST files checked={manifest_count}; all declare the recovered projection model as source."
            if manifest_count > 0 and not wrong_manifests
            else f"RUN_MANIFEST files checked={manifest_count}; missing/wrong source_projection_model_dir="
            + "; ".join(wrong_manifests[:10])
        ),
        source_artifacts=["inversion_workflow/runs/*/RUN_MANIFEST.json"],
    )

    release_plan = read_json(Path("inversion_workflow/inversion_parameter_release_plan_summary.json"))
    stage_counts = release_plan.get("stage_counts", {})
    active_fields = release_plan.get("active_field_parameters_now", [])
    fixed_fields = release_plan.get("fixed_first_stage_parameters", [])
    release_plan_pass = (
        int(release_plan.get("parameter_release_rows", 0) or 0) == 14
        and int(stage_counts.get("stage_1_active_field", 0) or 0) == 1
        and int(stage_counts.get("stage_1_fixed_support_field", 0) or 0) == 1
        and "intrinsic permeability tensor magnitude field" in active_fields
    )
    add_row(
        rows,
        audit_area="parameter_release",
        check_id="stage_one_release_scope_is_narrow",
        status="pass" if release_plan_pass else "fail",
        severity="error" if not release_plan_pass else "info",
        detail=(
            f"rows={release_plan.get('parameter_release_rows')}; active_fields={active_fields}; "
            f"fixed_first_stage={fixed_fields}; stage_counts={stage_counts}."
        ),
        source_artifacts=[
            "inversion_workflow/inversion_parameter_release_plan.md",
            "inversion_workflow/inversion_parameter_release_plan_summary.json",
        ],
    )

    release_gate = read_json(Path("inversion_workflow/inversion_release_gate_audit.json"))
    release_gate_pass = (
        release_gate.get("status") == "pass"
        and int(release_gate.get("failure_count", 0) or 0) == 0
        and int(release_gate.get("warning_count", 0) or 0) == 0
        and int(release_gate.get("run_count", 0) or 0) > 0
    )
    add_row(
        rows,
        audit_area="parameter_release",
        check_id="prepared_runs_release_gate_passed",
        status="pass" if release_gate_pass else "fail",
        severity="error" if not release_gate_pass else "info",
        detail=(
            f"status={release_gate.get('status')}; runs={release_gate.get('run_count')}; "
            f"checks={release_gate.get('check_count')}; failures={release_gate.get('failure_count')}; "
            f"warnings={release_gate.get('warning_count')}."
        ),
        source_artifacts=[
            "inversion_workflow/inversion_release_gate_audit.md",
            "inversion_workflow/inversion_release_gate_audit.json",
        ],
    )

    current_field = read_json(Path("inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD_SUMMARY.json"))
    current_field_repro = read_json(
        Path("inversion_workflow/current_permeability_field/CURRENT_FIELD_REPRODUCIBILITY_AUDIT.json")
    )
    field_summary = current_field.get("field", {})
    current_mesh = Path(str(current_field.get("packaged_mesh", "")))
    stats_csv = Path(str(current_field.get("stats_csv", "")))
    cell_count = int(field_summary.get("triangle6_cell_count", 0) or 0)
    positive_cells = int(field_summary.get("positive_definite_cell_count", 0) or 0)
    nonpositive_cells = int(field_summary.get("non_positive_definite_cell_count", 0) or 0)
    max_asymmetry = float(field_summary.get("max_tensor_asymmetry_abs", 1.0) or 0.0)
    current_field_pass = (
        current_field.get("status") == "current_permeability_field_package_generated"
        and current_mesh.is_file()
        and stats_csv.is_file()
        and cell_count > 0
        and positive_cells == cell_count
        and nonpositive_cells == 0
        and max_asymmetry == 0.0
    )
    add_row(
        rows,
        audit_area="current_field",
        check_id="current_field_package_is_positive_definite",
        status="pass" if current_field_pass else "fail",
        severity="error" if not current_field_pass else "info",
        detail=(
            f"status={current_field.get('status')}; run={current_field.get('run_id')}; "
            f"mesh_exists={yes_no(current_mesh.is_file())}; stats_exists={yes_no(stats_csv.is_file())}; "
            f"cells={cell_count}; positive_definite={positive_cells}; non_positive_definite={nonpositive_cells}; "
            f"max_asymmetry={max_asymmetry}; deliverable_status="
            f"{current_field.get('interpretation', {}).get('deliverable_status')}."
        ),
        source_artifacts=[
            "inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD.md",
            "inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD_SUMMARY.json",
            str(current_mesh),
            str(stats_csv),
        ],
    )

    current_repro_pass = (
        current_field_repro.get("status") == "current_field_reproducibility_verified"
        and int(current_field_repro.get("required_failure_count", 1) or 0) == 0
    )
    add_row(
        rows,
        audit_area="current_field",
        check_id="current_field_reproducibility_audit_verified",
        status="pass" if current_repro_pass else "fail",
        severity="error" if not current_repro_pass else "info",
        detail=(
            f"status={current_field_repro.get('status')}; checks={current_field_repro.get('check_count')}; "
            f"required_failures={current_field_repro.get('required_failure_count')}; "
            f"manifest_rows={current_field_repro.get('manifest_row_count')}; "
            f"run_input_snapshot_files={current_field_repro.get('run_input_snapshot_file_count')}; "
            f"project_refs={current_field_repro.get('project_reference_count')}; "
            f"direct/state rows={current_field_repro.get('direct_used_rows')}/"
            f"{current_field_repro.get('state_used_rows')}."
        ),
        source_artifacts=[
            "inversion_workflow/current_permeability_field/CURRENT_FIELD_REPRODUCIBILITY_AUDIT.md",
            "inversion_workflow/current_permeability_field/CURRENT_FIELD_REPRODUCIBILITY_AUDIT.json",
            "inversion_workflow/current_permeability_field/packaged_file_manifest.csv",
            "inversion_workflow/current_permeability_field/ogs_run_inputs/",
        ],
    )

    measurement_info = summarize_measurement_info(args.measurement_info_dir)
    measurement_info_pass = (
        measurement_info["folder_count"] == 9
        and measurement_info["source_file_rows"] >= 200
        and measurement_info["archive_member_rows"] >= 1800
        and measurement_info["workbook_sheet_rows"] >= 30
    )
    add_row(
        rows,
        audit_area="measurements",
        check_id="measurement_info_mirror_indexes_available",
        status="pass" if measurement_info_pass else "fail",
        severity="error" if not measurement_info_pass else "info",
        detail=(
            f"folders={measurement_info['folder_count']}; source rows={measurement_info['source_file_rows']}; "
            f"archive-member rows={measurement_info['archive_member_rows']}; workbook sheet rows="
            f"{measurement_info['workbook_sheet_rows']}; kind_counts={measurement_info['kind_counts']}."
        ),
        source_artifacts=[
            str(args.measurement_info_dir / "README.md"),
            measurement_info["manifest_path"],
            measurement_info["archive_catalog_path"],
            measurement_info["workbook_index_path"],
        ],
    )

    coverage = read_json(Path("inversion_workflow/measurement_operator_coverage_summary.json"))
    coverage_status_counts = coverage.get("coverage_status_counts", {})
    coverage_pass = (
        int(coverage.get("observation_groups", 0) or 0) == 9
        and int(coverage.get("active_objective_groups", 0) or 0) >= 2
        and len(coverage_status_counts) == 9
    )
    add_row(
        rows,
        audit_area="measurements",
        check_id="all_measurement_groups_have_model_entry_status",
        status="pass" if coverage_pass else "fail",
        severity="error" if not coverage_pass else "info",
        detail=(
            f"observation_groups={coverage.get('observation_groups')}; active_objective_groups="
            f"{coverage.get('active_objective_groups')}; coverage_status_counts={coverage_status_counts}; "
            f"state_target_rows={coverage.get('state_target_rows')}; state_sample_rows="
            f"{coverage.get('state_sample_rows')}."
        ),
        source_artifacts=[
            "inversion_workflow/measurement_operator_coverage.md",
            "inversion_workflow/measurement_operator_coverage_summary.json",
        ],
    )

    traceability = read_json(Path("inversion_workflow/measurement_report_traceability_audit_summary.json"))
    traceability_pass = (
        traceability.get("all_observations_traceable") is True
        and int(traceability.get("observation_count", 0) or 0) == 9
        and int(traceability.get("missing_expected_artifact_observation_count", 0) or 0) == 0
    )
    add_row(
        rows,
        audit_area="measurements",
        check_id="measurement_catalogue_report_traceability_passed",
        status="pass" if traceability_pass else "fail",
        severity="error" if not traceability_pass else "info",
        detail=(
            f"status={traceability.get('status')}; observations={traceability.get('observation_count')}; "
            f"traceability_status_counts={traceability.get('traceability_status_counts')}; "
            f"missing sections/tables/model-entry/artifacts="
            f"{traceability.get('missing_chapter_section_count')}/"
            f"{traceability.get('missing_inventory_table_reference_count')}/"
            f"{traceability.get('missing_model_entry_statement_count')}/"
            f"{traceability.get('missing_expected_artifact_observation_count')}."
        ),
        source_artifacts=[
            "inversion_workflow/measurement_report_traceability_audit.md",
            "inversion_workflow/measurement_report_traceability_audit_summary.json",
        ],
    )

    likelihood = read_json(Path("inversion_workflow/measurement_likelihood_model_summary.json"))
    likelihood_pass = (
        int(likelihood.get("measurement_streams", 0) or 0) == 7
        and int(likelihood.get("active_streams_now", 0) or 0) >= 2
        and int(likelihood.get("total_current_objective_rows", 0) or 0) > 0
    )
    add_row(
        rows,
        audit_area="measurements",
        check_id="likelihood_activation_distinguishes_active_and_gated_streams",
        status="pass" if likelihood_pass else "fail",
        severity="error" if not likelihood_pass else "info",
        detail=(
            f"measurement_streams={likelihood.get('measurement_streams')}; active_streams_now="
            f"{likelihood.get('active_streams_now')}; total_current_objective_rows="
            f"{likelihood.get('total_current_objective_rows')}; activation_state_counts="
            f"{likelihood.get('activation_state_counts')}."
        ),
        source_artifacts=[
            "inversion_workflow/measurement_likelihood_model.md",
            "inversion_workflow/measurement_likelihood_model_summary.json",
        ],
    )

    final_promotion = read_json(Path("inversion_workflow/final_inversion_promotion_checklist_summary.json"))
    promotion_guard_pass = (
        final_promotion.get("promotion_decision") == "do_not_promote_current_field"
        and int(final_promotion.get("open_blocker_count", 0) or 0) > 0
        and final_promotion.get("current_field_final_decision") == "do_not_promote_to_final_all_measurement_field"
    )
    add_row(
        rows,
        audit_area="promotion_guard",
        check_id="gated_streams_prevent_final_promotion",
        status="pass" if promotion_guard_pass else "fail",
        severity="error" if not promotion_guard_pass else "info",
        detail=(
            f"promotion_decision={final_promotion.get('promotion_decision')}; current_field_final_decision="
            f"{final_promotion.get('current_field_final_decision')}; open_blockers="
            f"{final_promotion.get('open_blocker_count')}; open_blocker_ids="
            f"{final_promotion.get('open_blocker_ids')}; status_counts="
            f"{final_promotion.get('status_counts')}."
        ),
        source_artifacts=[
            "inversion_workflow/final_inversion_promotion_checklist.md",
            "inversion_workflow/final_inversion_promotion_checklist_summary.json",
        ],
    )

    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    worst = max((status_rank(row["status"]) for row in rows), default=2)
    overall_status = {0: "pass", 1: "warning", 2: "fail"}[worst]
    nonpassing = [row["check_id"] for row in rows if row["status"] != "pass"]
    summary = {
        "status": overall_status,
        "check_count": len(rows),
        "pass_count": sum(1 for row in rows if row["status"] == "pass"),
        "warning_count": sum(1 for row in rows if row["status"] == "warning"),
        "failure_count": sum(1 for row in rows if row["status"] == "fail"),
        "status_counts": dict(sorted(status_counts.items())),
        "nonpassing_check_ids": nonpassing,
        "source_model_run_manifest_count": manifest_count,
        "source_model_wrong_manifest_count": len(wrong_manifests),
        "release_gate_run_count": release_gate.get("run_count"),
        "release_gate_check_count": release_gate.get("check_count"),
        "current_field_run_id": current_field.get("run_id"),
        "current_field_triangle6_cell_count": cell_count,
        "current_field_positive_definite_cell_count": positive_cells,
        "measurement_info": measurement_info,
        "measurement_operator_coverage_status_counts": coverage_status_counts,
        "measurement_likelihood_activation_state_counts": likelihood.get("activation_state_counts", {}),
        "final_promotion_decision": final_promotion.get("promotion_decision"),
        "final_promotion_open_blocker_ids": final_promotion.get("open_blocker_ids", []),
        "outputs": {
            "checks_csv": str(args.output_csv),
            "summary_json": str(args.output_json),
            "markdown": str(args.output_md),
        },
        "notes": [
            "This audit checks evidence wiring and guardrails, not new scientific acceptance.",
            "A pass means the source model is frozen, only staged run-local fields are released, all measurement groups are catalogued and model-entry classified, and gated streams still block final promotion.",
            "The current field remains an active-objective incumbent until external and modelling gates are closed or explicitly excluded.",
        ],
    }
    return rows, summary


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["audit_area", "check_id", "status", "severity", "detail", "source_artifacts"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, str]], summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Frozen Model and Measurement-Inclusion Audit",
        "",
        "This audit checks the current evidence chain for the CD-A modelling workflow:",
        "the exchanged GESA OGS model stays frozen, candidate runs only use the staged",
        "run-local fields, all measurement classes are represented in the catalogue and",
        "model-entry layer, and gated streams still prevent a final all-measurement field",
        "claim.",
        "",
        f"- Overall status: `{summary['status']}`",
        f"- Checks: {summary['check_count']}",
        f"- Pass/warning/failure counts: {summary['pass_count']}/"
        f"{summary['warning_count']}/{summary['failure_count']}",
        f"- RUN_MANIFEST files checked: {summary['source_model_run_manifest_count']}",
        f"- Release-gate runs/checks: {summary['release_gate_run_count']}/"
        f"{summary['release_gate_check_count']}",
        f"- Current field run: `{summary['current_field_run_id']}`",
        f"- Current field positive-definite cells: {summary['current_field_positive_definite_cell_count']}/"
        f"{summary['current_field_triangle6_cell_count']}",
        f"- Measurement-info source/archive/workbook rows: "
        f"{summary['measurement_info']['source_file_rows']}/"
        f"{summary['measurement_info']['archive_member_rows']}/"
        f"{summary['measurement_info']['workbook_sheet_rows']}",
        f"- Final promotion decision: `{summary['final_promotion_decision']}`",
        f"- Open promotion blockers: {', '.join(summary['final_promotion_open_blocker_ids']) or 'none'}",
        "",
        "## Checks",
        "",
        "| Area | Check | Status | Detail | Source artifacts |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        detail = row["detail"].replace("|", "\\|")
        sources = row["source_artifacts"].replace("|", "\\|")
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['audit_area']}`",
                    f"`{row['check_id']}`",
                    f"`{row['status']}`",
                    detail,
                    sources,
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A passing row here is a guardrail result. It means the artefact wiring supports",
            "the modelling interpretation; it is not a collaborator sign-off and it is not a",
            "final inversion acceptance. The current permeability field remains the best",
            "executed active-objective incumbent, while ERT, Taupe/TDR, RH, other-HM, CTE,",
            "and endpoint-geometry gates must still be closed or explicitly excluded before",
            "a final all-measurement claim.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def copy_to_catalogue(catalogue_dir: Path, paths: list[Path]) -> list[dict[str, str]]:
    catalogue_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for path in paths:
        target = catalogue_dir / path.name
        shutil.copy2(path, target)
        copied.append({"source": str(path), "catalogue_copy": str(target)})
    return copied


def main() -> None:
    args = parse_args()
    rows, summary = build_rows(args)
    write_csv(args.output_csv, rows)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_markdown(args.output_md, rows, summary)
    catalogue_copies = copy_to_catalogue(args.catalogue_dir, [args.output_csv, args.output_json, args.output_md])
    summary["catalogue_copies"] = catalogue_copies
    args.output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    shutil.copy2(args.output_json, args.catalogue_dir / args.output_json.name)


if __name__ == "__main__":
    main()
