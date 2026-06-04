#!/usr/bin/env python3
"""Audit measurement-catalogue to report/workflow traceability."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Any


TRACE_EXPECTATIONS: dict[str, dict[str, Any]] = {
    "ert_open_time_series": {
        "catalogue_folder": "ert",
        "chapter_needle": r"\subsection{ERT: resistivity, water content, and saturation}",
        "table_needle": r"\path{ert/source_files}",
        "model_needles": [r"\mathcal O_{\rm ERT}", r"\log_{10}\rho_{\rm pred}-\log_{10}\rho_{\rm ERT}"],
        "expected_artifacts": [
            "processed_observations/ert_archive_inventory.csv",
            "processed_observations/ert_timesteps.csv",
            "processed_observations/ert_nmr_resistivity_pairs.csv",
            "processed_observations/ert_water_content_resistivity_operator.csv",
            "processed_observations/ert_spatial_projection_lookup.csv",
            "processed_observations/ert_measurement_semantics.md",
            "ert_support_sensitivity.md",
        ],
    },
    "nmr_weekly_and_seasonal": {
        "catalogue_folder": "nmr",
        "chapter_needle": r"\subsection{NMR: total water signal versus OGS liquid saturation}",
        "table_needle": r"\path{nmr/source_files}",
        "model_needles": [r"\theta_{\rm NMR}^{\rm obs}", "bound/interlayer-water", "within-label trend/anomaly"],
        "expected_artifacts": [
            "processed_observations/nmr_weekly.csv",
            "processed_observations/nmr_seasonal_profiles.csv",
            "processed_observations/nmr_seasonal_zip_inventory.csv",
            "processed_observations/nmr_bound_water_sensitivity.md",
            "nmr_objective_decision.md",
            "nmr_trend_anomaly_active_objective.md",
        ],
    },
    "permeability_pulse_tests": {
        "catalogue_folder": "permeability_pulse_tests",
        "chapter_needle": r"\subsection{Permeability pulse tests: scalar interval data versus tensor field}",
        "table_needle": r"\path{permeability_pulse_tests/source_files}",
        "model_needles": ["scalar interval", "intrinsic permeability tensor", "duplicate-aware"],
        "expected_artifacts": [
            "processed_observations/permeability_interpreted_values.csv",
            "processed_observations/permeability_pressure_decay.csv",
            "processed_observations/permeability_observation_targets.csv",
            "processed_observations/permeability_measurement_semantics.md",
            "processed_observations/permeability_missing_geometry_audit.md",
        ],
    },
    "taupe_tdr_edz_bands": {
        "catalogue_folder": "taupe_tdr",
        "chapter_needle": r"\subsection{Taupe/TDR: dielectric proxy and EDZ-band trends}",
        "table_needle": r"\path{taupe_tdr/source_files}",
        "model_needles": ["baseline-normalized", r"r_{\rm Taupe,trend}", "absolute Taupe values"],
        "expected_artifacts": [
            "processed_observations/taupe_tdr_bands.csv",
            "processed_observations/taupe_tdr_trend_operator.csv",
            "processed_observations/taupe_tdr_semantics.md",
            "processed_observations/taupe_tdr_observation_operator.md",
            "taupe_candidate_discrimination.md",
            "taupe_series_weight_sensitivity.md",
        ],
    },
    "suction_relative_humidity_open_twin": {
        "catalogue_folder": "suction_relative_humidity",
        "chapter_needle": r"\subsection{Suction and relative humidity: pressure boundary and retention curve}",
        "table_needle": r"\path{suction_relative_humidity/source_files}",
        "model_needles": ["Kelvin", "boundary forcing", "active-curve provenance"],
        "expected_artifacts": [
            "processed_observations/rh_open_twin_kelvin.csv",
            "processed_observations/rh_measurement_semantics.md",
            "processed_observations/rh_boundary_candidate_curves.md",
            "processed_observations/rh_boundary_uncertainty.md",
            "processed_observations/rh_boundary_provenance_request.md",
        ],
    },
    "coordinates_and_geometry": {
        "catalogue_folder": "coordinates_geometry_layout",
        "chapter_needle": r"\subsection{Coordinates, bedding, and structural constraints}",
        "table_needle": r"\path{coordinates_geometry_layout/source_files}",
        "model_needles": ["measurement-to-model map", r"2D\_Model", "borehole"],
        "expected_artifacts": [
            "processed_observations/measurement_coordinates_xy.csv",
            "processed_observations/borehole_coordinates.csv",
            "processed_observations/measurement_mesh_lookup.csv",
            "processed_observations/borehole_mesh_lookup.csv",
            "processed_observations/borehole_line_mesh_samples.csv",
        ],
    },
    "bedding_structure": {
        "catalogue_folder": "bedding_geology_structure",
        "chapter_needle": r"\subsection{Coordinates, bedding, and structural constraints}",
        "table_needle": r"\path{bedding_geology_structure/source_files}",
        "model_needles": ["bedding", "structural", "anisotropic"],
        "expected_artifacts": [
            "../cda_knowledge_base/measurements/bedding_geology_structure/README.md",
            "../cda_knowledge_base/measurements/bedding_geology_structure/derived_files/deep_source_pass/source_file_deep_summary.md",
        ],
    },
    "model_projection_inputs": {
        "catalogue_folder": "model_projection_inputs",
        "chapter_needle": r"\subsection{Projection workflow and mesh-based parameter fields}",
        "table_needle": r"\path{model_projection_inputs/source_files}",
        "model_needles": ["MeshElement", "k_i_rd", "n_rd"],
        "expected_artifacts": [
            "../cda_knowledge_base/measurements/model_projection_inputs/README.md",
            "../cda_knowledge_base/measurements/model_projection_inputs/source_files/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip",
            "scripts/prepare_ogs_run.py",
            "inversion_release_gate_audit.md",
        ],
    },
    "other_hm_monitoring": {
        "catalogue_folder": "other_hm_monitoring",
        "chapter_needle": r"\subsection{Other HM monitoring}",
        "table_needle": r"\path{other_hm_monitoring/source_files}",
        "model_needles": ["hard-residual-ready", "Geoscope", "laser-scan"],
        "expected_artifacts": [
            "processed_observations/other_hm_monitoring.md",
            "processed_observations/other_hm_levelling_displacements.csv",
            "processed_observations/other_hm_qualitative_targets.csv",
            "processed_observations/other_hm_missing_numeric_request.md",
            "processed_observations/other_hm_numeric_source_audit.md",
        ],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("inversion_workflow/observation_manifest.json"))
    parser.add_argument(
        "--manifest-validation",
        type=Path,
        default=Path("inversion_workflow/observation_manifest_validation.json"),
    )
    parser.add_argument("--coverage", type=Path, default=Path("inversion_workflow/measurement_operator_coverage.csv"))
    parser.add_argument("--chapter", type=Path, default=Path("measurement_chapter.tex"))
    parser.add_argument("--output-csv", type=Path, default=Path("inversion_workflow/measurement_report_traceability_audit.csv"))
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/measurement_report_traceability_audit_summary.json"),
    )
    parser.add_argument("--output-md", type=Path, default=Path("inversion_workflow/measurement_report_traceability_audit.md"))
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files"),
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def count_files(path: Path, *, exclude_provider_responses: bool = False) -> int:
    if not path.exists():
        return 0
    count = 0
    for candidate in path.rglob("*"):
        if not candidate.is_file():
            continue
        if exclude_provider_responses and "provider_responses" in candidate.parts:
            continue
        count += 1
    return count


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def resolve_artifact(repo: Path, artifact: str) -> Path:
    raw = Path(artifact)
    if raw.is_absolute():
        return raw
    candidates = [
        repo / raw,
        repo / "inversion_workflow" / raw,
        repo / "inversion_workflow" / "processed_observations" / raw,
        repo / "inversion_workflow" / "runs" / raw,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def validation_counts(validation: dict[str, Any]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for check in validation.get("checks", []):
        observation_id = str(check.get("observation_id", ""))
        bucket = counts.setdefault(observation_id, {"ok": 0, "fail": 0, "total": 0})
        bucket["total"] += 1
        if check.get("status") == "ok":
            bucket["ok"] += 1
        else:
            bucket["fail"] += 1
    return counts


def chapter_line(chapter_text: str, needle: str) -> int | None:
    for line_number, line in enumerate(chapter_text.splitlines(), start=1):
        if needle in line:
            return line_number
    return None


def bool_status(value: bool) -> str:
    return "yes" if value else "no"


def build_rows(repo: Path, args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest = read_json(args.manifest)
    validation_summary = read_json(args.manifest_validation)
    coverage_rows = {row["observation_id"]: row for row in read_csv(args.coverage) if row.get("observation_id")}
    chapter_text = args.chapter.read_text(encoding="utf-8", errors="ignore")
    measurement_root = (repo / "../cda_knowledge_base/measurements").resolve()
    vcounts = validation_counts(validation_summary)
    rows: list[dict[str, Any]] = []

    for observation in manifest.get("observations", []):
        observation_id = observation["id"]
        expected = TRACE_EXPECTATIONS[observation_id]
        folder = measurement_root / expected["catalogue_folder"]
        source_dir = folder / "source_files"
        derived_dir = folder / "derived_files"
        readme = folder / "README.md"
        data_content_summary = folder / "DATA_CONTENT_SUMMARY.md"
        data_content_csv = derived_dir / "content_deep_dive" / "content_summary.csv"
        chapter_found = expected["chapter_needle"] in chapter_text
        table_found = expected["table_needle"] in chapter_text
        model_needles_found = [needle for needle in expected["model_needles"] if needle in chapter_text]
        missing_model_needles = [needle for needle in expected["model_needles"] if needle not in chapter_text]
        artifact_paths = [resolve_artifact(repo, artifact) for artifact in expected["expected_artifacts"]]
        missing_artifacts = [
            expected["expected_artifacts"][index]
            for index, artifact_path in enumerate(artifact_paths)
            if not artifact_path.exists()
        ]
        coverage = coverage_rows.get(observation_id, {})
        check_counts = vcounts.get(observation_id, {"ok": 0, "fail": 0, "total": 0})
        pass_conditions = [
            folder.exists(),
            source_dir.exists(),
            readme.exists(),
            data_content_summary.exists(),
            data_content_csv.exists(),
            check_counts["fail"] == 0 and check_counts["total"] > 0,
            bool(coverage),
            chapter_found,
            table_found,
            not missing_model_needles,
            not missing_artifacts,
        ]
        rows.append(
            {
                "observation_id": observation_id,
                "measurement_type": observation.get("measurement_type", ""),
                "catalogue_folder": expected["catalogue_folder"],
                "catalogue_folder_exists": bool_status(folder.exists()),
                "catalogue_readme_exists": bool_status(readme.exists()),
                "data_content_summary_exists": bool_status(data_content_summary.exists()),
                "data_content_csv_exists": bool_status(data_content_csv.exists()),
                "data_content_fact_rows": count_csv_rows(data_content_csv),
                "source_file_count": count_files(source_dir, exclude_provider_responses=True),
                "provider_response_file_count": count_files(source_dir / "provider_responses"),
                "derived_file_count": count_files(derived_dir),
                "manifest_check_count": len(observation.get("checks", [])),
                "validation_ok_checks": check_counts["ok"],
                "validation_failed_checks": check_counts["fail"],
                "coverage_status": coverage.get("coverage_status", "missing_coverage_row"),
                "raw_or_processed_rows": coverage.get("raw_or_processed_rows", ""),
                "target_rows": coverage.get("target_rows", ""),
                "mapped_or_usable_rows": coverage.get("mapped_or_usable_rows", ""),
                "active_objective_rows": coverage.get("active_objective_rows", ""),
                "chapter_section_found": bool_status(chapter_found),
                "chapter_section_line": chapter_line(chapter_text, expected["chapter_needle"]) or "",
                "inventory_table_reference_found": bool_status(table_found),
                "model_entry_needles_found": "; ".join(model_needles_found),
                "missing_model_entry_needles": "; ".join(missing_model_needles),
                "expected_artifact_count": len(expected["expected_artifacts"]),
                "missing_expected_artifacts": "; ".join(missing_artifacts),
                "traceability_status": "pass" if all(pass_conditions) else "needs_attention",
                "current_model_use": coverage.get("current_model_use", observation.get("model_role", "")),
                "blocking_next_step": coverage.get("blocking_next_step", ""),
            }
        )

    return rows, summarize(rows, validation_summary, coverage_rows)


def summarize(rows: list[dict[str, Any]], validation: dict[str, Any], coverage_rows: dict[str, dict[str, str]]) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    coverage_status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["traceability_status"]] = status_counts.get(row["traceability_status"], 0) + 1
        coverage_status = str(row["coverage_status"])
        coverage_status_counts[coverage_status] = coverage_status_counts.get(coverage_status, 0) + 1

    missing_sections = [row["observation_id"] for row in rows if row["chapter_section_found"] != "yes"]
    missing_tables = [row["observation_id"] for row in rows if row["inventory_table_reference_found"] != "yes"]
    missing_model_entry = [row["observation_id"] for row in rows if row["missing_model_entry_needles"]]
    missing_artifacts = [row["observation_id"] for row in rows if row["missing_expected_artifacts"]]
    missing_catalogue = [row["observation_id"] for row in rows if row["catalogue_folder_exists"] != "yes"]
    missing_readme = [row["observation_id"] for row in rows if row["catalogue_readme_exists"] != "yes"]
    missing_data_content = [
        row["observation_id"]
        for row in rows
        if row["data_content_summary_exists"] != "yes" or row["data_content_csv_exists"] != "yes"
    ]
    validation_failures = [row["observation_id"] for row in rows if int(row["validation_failed_checks"]) > 0]
    total_data_content_rows = sum(int(row["data_content_fact_rows"]) for row in rows)

    return {
        "status": "measurement_report_traceability_audit_generated",
        "observation_count": len(rows),
        "manifest_validation_check_count": validation.get("check_count"),
        "manifest_validation_failures": validation.get("failures"),
        "coverage_row_count": len(coverage_rows),
        "traceability_status_counts": dict(sorted(status_counts.items())),
        "coverage_status_counts": dict(sorted(coverage_status_counts.items())),
        "missing_catalogue_folder_count": len(missing_catalogue),
        "missing_catalogue_readme_count": len(missing_readme),
        "missing_data_content_summary_count": len(missing_data_content),
        "data_content_fact_row_count": total_data_content_rows,
        "missing_chapter_section_count": len(missing_sections),
        "missing_inventory_table_reference_count": len(missing_tables),
        "missing_model_entry_statement_count": len(missing_model_entry),
        "missing_expected_artifact_observation_count": len(missing_artifacts),
        "validation_failure_observation_count": len(validation_failures),
        "all_observations_traceable": (
            len(rows) > 0
            and all(row["traceability_status"] == "pass" for row in rows)
            and validation.get("failures") == 0
        ),
        "missing_chapter_sections": missing_sections,
        "missing_inventory_table_references": missing_tables,
        "missing_model_entry_statements": missing_model_entry,
        "missing_data_content_summaries": missing_data_content,
        "missing_expected_artifacts": {
            row["observation_id"]: row["missing_expected_artifacts"]
            for row in rows
            if row["missing_expected_artifacts"]
        },
        "validation_failure_observations": validation_failures,
        "notes": [
            "Traceability pass means the catalogue folder, README, mined data-content summary, manifest validation, coverage row, report section, inventory-table reference, model-entry statement, and expected workflow artifacts are all present.",
            "Scientific activation status is separate: ERT, Taupe/TDR, RH, and other-HM may be traceable while still gated out of the active likelihood.",
        ],
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Measurement Report Traceability Audit",
        "",
        "This audit checks whether every manifest observation group is represented from",
        "catalogued source files through the report chapter and workflow artifacts.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Observations audited: {summary['observation_count']}",
        f"- Manifest validation checks: {summary['manifest_validation_check_count']}",
        f"- Manifest validation failures: {summary['manifest_validation_failures']}",
        f"- Coverage rows: {summary['coverage_row_count']}",
        f"- Traceability status counts: {summary['traceability_status_counts']}",
        f"- Data-content fact rows: {summary['data_content_fact_row_count']}",
        f"- Missing data-content summaries: {summary['missing_data_content_summary_count']}",
        f"- Missing chapter sections: {summary['missing_chapter_section_count']}",
        f"- Missing inventory table references: {summary['missing_inventory_table_reference_count']}",
        f"- Missing model-entry statements: {summary['missing_model_entry_statement_count']}",
        f"- Observations with missing expected artifacts: {summary['missing_expected_artifact_observation_count']}",
        f"- All observations traceable: `{summary['all_observations_traceable']}`",
        "",
        "## Observation Rows",
        "",
        "| Observation | Folder | Status | Coverage | Source files | Content facts | Active rows | Missing items |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        missing_bits = []
        if row["data_content_summary_exists"] != "yes" or row["data_content_csv_exists"] != "yes":
            missing_bits.append("data-content summary")
        if row["chapter_section_found"] != "yes":
            missing_bits.append("chapter section")
        if row["inventory_table_reference_found"] != "yes":
            missing_bits.append("inventory table reference")
        if row["missing_model_entry_needles"]:
            missing_bits.append("model-entry wording")
        if row["missing_expected_artifacts"]:
            missing_bits.append("expected artifacts")
        if int(row["validation_failed_checks"]) > 0:
            missing_bits.append("manifest checks")
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['observation_id']}`",
                    f"`{row['catalogue_folder']}`",
                    f"`{row['traceability_status']}`",
                    f"`{row['coverage_status']}`",
                    str(row["source_file_count"]),
                    str(row["data_content_fact_rows"]),
                    str(row["active_objective_rows"]),
                    ", ".join(missing_bits) or "none",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A passing traceability row is not the same as an active likelihood row. It means the",
            "source catalogue, mined data-content summary, manifest validation, report coverage,",
            "model-entry statement, and workflow artifacts are present. Activation gates remain governed by the likelihood,",
            "stream-gate, external request, and response-intake audits.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def copy_to_catalogue(catalogue_dir: Path, paths: list[Path]) -> None:
    catalogue_dir.mkdir(parents=True, exist_ok=True)
    for path in paths:
        shutil.copy2(path, catalogue_dir / path.name)


def main() -> None:
    args = parse_args()
    repo = Path.cwd()
    rows, summary = build_rows(repo, args)
    write_csv(args.output_csv, rows)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_markdown(args.output_md, rows, summary)
    copy_to_catalogue(args.catalogue_dir, [args.output_csv, args.output_json, args.output_md])


if __name__ == "__main__":
    main()
