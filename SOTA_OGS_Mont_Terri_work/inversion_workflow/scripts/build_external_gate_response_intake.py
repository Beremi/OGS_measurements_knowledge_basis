#!/usr/bin/env python3
"""Build a response-intake tracker for external measurement-gate requests."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Any


INTAKE_POLICIES: dict[str, dict[str, str]] = {
    "ert_transform_support": {
        "intake_dir": "cda_knowledge_base/measurements/ert/source_files/provider_responses",
        "expected_response_artifacts": (
            "Coordinate-frame note or transform script; electrode/inversion coordinate reference; "
            "accepted tunnel/niche support polygon or mask; decision on 35 cm rock-depth handling "
            "and the current radial support variants."
        ),
        "minimum_intake_metadata": (
            "source contact, response date, coordinate origin/axes, unit convention, support-mask "
            "definition, and whether the current local transform model_x=raw_x/model_y=raw_y+500 is accepted."
        ),
        "acceptance_test": (
            "A reproducible ERT-to-OGS transform and accepted support mask can be encoded without "
            "freehand interpretation; the ERT spatial projection and support-sensitivity audits can "
            "be regenerated with no provisional-transform caveat."
        ),
        "refresh_commands": (
            "python inversion_workflow/scripts/build_ert_spatial_projection_lookup.py; "
            "python inversion_workflow/scripts/build_ert_support_sensitivity_audit.py; "
            "python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; "
            "python inversion_workflow/scripts/build_measurement_gate_closure_request.py; "
            "python inversion_workflow/scripts/build_external_gate_request_pack.py; "
            "python inversion_workflow/scripts/build_objective_readiness_audit.py"
        ),
        "gate_closure_effect": "May close ERT_TRANSFORM_SUPPORT and make ERT support ready for weighted residual design.",
    },
    "ert_uncertainty": {
        "intake_dir": "cda_knowledge_base/measurements/ert/source_files/provider_responses",
        "expected_response_artifacts": (
            "Per-cell, region, or time-level ERT uncertainty/covariance export, or written simplified "
            "weighting rule with log base, filtering, spatial correlation, and effective degrees of freedom."
        ),
        "minimum_intake_metadata": (
            "sigma units/log base, temporal grouping, spatial correlation assumptions, filtering rules, "
            "unstable-cell handling, and whether cells may be aggregated before comparison."
        ),
        "acceptance_test": (
            "The ERT likelihood can assign defensible row/group weights without treating dense VTK cells "
            "as independent observations."
        ),
        "refresh_commands": (
            "python inversion_workflow/scripts/build_measurement_likelihood_model.py; "
            "python inversion_workflow/scripts/build_ert_candidate_discrimination_audit.py; "
            "python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; "
            "python inversion_workflow/scripts/build_measurement_gate_closure_request.py; "
            "python inversion_workflow/scripts/build_external_gate_request_pack.py; "
            "python inversion_workflow/scripts/build_objective_readiness_audit.py"
        ),
        "gate_closure_effect": "May close ERT_UNCERTAINTY and allow ERT to move from diagnostic screen toward a hard residual.",
    },
    "hm_numeric_exports": {
        "intake_dir": "cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses",
        "expected_response_artifacts": (
            "Machine-readable Geoscope mini-piezometer, extensometer, crackmeter, laser-scan statistical "
            "interpretation, and precision-levelling tables."
        ),
        "minimum_intake_metadata": (
            "instrument id, timestamp or survey epoch, measured value, unit, coordinate/support id, "
            "reference/zero convention, processing provenance, and quality/status flag."
        ),
        "acceptance_test": (
            "The other-HM source audit finds at least one hard-residual-ready numeric request class with "
            "time/epoch and model-facing support."
        ),
        "refresh_commands": (
            "python inversion_workflow/scripts/build_other_hm_monitoring_inventory.py; "
            "python inversion_workflow/scripts/build_other_hm_missing_numeric_request.py; "
            "python inversion_workflow/scripts/build_measurement_operator_coverage.py; "
            "python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; "
            "python inversion_workflow/scripts/build_measurement_gate_closure_request.py; "
            "python inversion_workflow/scripts/build_external_gate_request_pack.py; "
            "python inversion_workflow/scripts/build_objective_readiness_audit.py"
        ),
        "gate_closure_effect": "May close HM_NUMERIC_EXPORTS and create candidate pressure/deformation/laser/levelling validation residuals.",
    },
    "hm_uncertainty": {
        "intake_dir": "cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses",
        "expected_response_artifacts": (
            "Uncertainty/covariance or accepted simplified weighting notes for every supplied other-HM "
            "numeric export, including failed-sensor and maintenance intervals."
        ),
        "minimum_intake_metadata": (
            "unit/reference convention, uncertainty model, covariance or independence assumptions, quality "
            "flags, failure periods, laser registration uncertainty/masks, and levelling covariance frame."
        ),
        "acceptance_test": (
            "Each candidate other-HM residual has enough metadata to state which OGS quantity/support it "
            "measures and what residual weight it receives."
        ),
        "refresh_commands": (
            "python inversion_workflow/scripts/build_other_hm_missing_numeric_request.py; "
            "python inversion_workflow/scripts/build_measurement_likelihood_model.py; "
            "python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; "
            "python inversion_workflow/scripts/build_measurement_gate_closure_request.py; "
            "python inversion_workflow/scripts/build_external_gate_request_pack.py; "
            "python inversion_workflow/scripts/build_objective_readiness_audit.py"
        ),
        "gate_closure_effect": "May close HM_UNCERTAINTY after numeric exports exist and residual weights are defensible.",
    },
    "rh_active_curve_provenance": {
        "intake_dir": "cda_knowledge_base/measurements/suction_relative_humidity/source_files/provider_responses",
        "expected_response_artifacts": (
            "Active open-niche pressure-curve source table, script/notebook, sensor selection note, Kelvin "
            "conversion constants, time-axis origin/timezone, smoothing/manual-edit policy, sign convention, "
            "and open/closed curve mapping."
        ),
        "minimum_intake_metadata": (
            "source sensors/sheets, model-time zero, RH percent/fraction convention, temperature/density "
            "constants, pressure unit/sign, extension/extrapolation policy, and post-active-curve decision."
        ),
        "acceptance_test": (
            "The active XML pressure curve can be regenerated or explained well enough that replacement "
            "curves/retention targets are no longer based on unknown provenance."
        ),
        "refresh_commands": (
            "python inversion_workflow/scripts/audit_rh_boundary_curve.py; "
            "python inversion_workflow/scripts/build_rh_semantics_audit.py; "
            "python inversion_workflow/scripts/build_rh_boundary_candidate_curves.py; "
            "python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; "
            "python inversion_workflow/scripts/build_measurement_gate_closure_request.py; "
            "python inversion_workflow/scripts/build_external_gate_request_pack.py; "
            "python inversion_workflow/scripts/build_objective_readiness_audit.py"
        ),
        "gate_closure_effect": "May close RH_ACTIVE_CURVE_PROVENANCE and make RH boundary forcing reproducible.",
    },
    "taupe_unit_calibration": {
        "intake_dir": "cda_knowledge_base/measurements/taupe_tdr/source_files/provider_responses",
        "expected_response_artifacts": (
            "Taupe_WC unit definition, sensor/band calibration equations, uncertainty by sensor/band, "
            "baseline/reference date, and ARDP/dielectric/water-content conversion notes."
        ),
        "minimum_intake_metadata": (
            "workbook sheet/column unit, whether values are volumetric water-content percent or a proxy, "
            "matrix/porosity correction status, calibration constants, and uncertainty model."
        ),
        "acceptance_test": (
            "The Taupe semantics audit can decide whether absolute Taupe values are water content, "
            "permittivity/proxy, or trend-only evidence."
        ),
        "refresh_commands": (
            "python inversion_workflow/scripts/build_taupe_semantics_audit.py; "
            "python inversion_workflow/scripts/build_taupe_observation_operator.py; "
            "python inversion_workflow/scripts/build_taupe_candidate_discrimination_audit.py; "
            "python inversion_workflow/scripts/build_taupe_series_weight_sensitivity_audit.py; "
            "python inversion_workflow/scripts/build_measurement_likelihood_model.py; "
            "python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; "
            "python inversion_workflow/scripts/build_measurement_gate_closure_request.py; "
            "python inversion_workflow/scripts/build_external_gate_request_pack.py; "
            "python inversion_workflow/scripts/build_objective_readiness_audit.py"
        ),
        "gate_closure_effect": "May close TAUPE_UNIT_CALIBRATION and allow Taupe to become trend-only or absolute residual evidence.",
    },
    "perm_endpoint_geometry": {
        "intake_dir": "cda_knowledge_base/measurements/permeability_pulse_tests/source_files/provider_responses",
        "expected_response_artifacts": (
            "Endpoint coordinates, labelled digitized traces, or interval geometry tables for historical "
            "BCD-A24, BCD-A25, BCD-A26, BCD-A27, and BFM-D19 permeability intervals."
        ),
        "minimum_intake_metadata": (
            "borehole id, open/closed assignment, start/end coordinates or depths, orientation convention, "
            "interval length/support, date/source table, permeability value, and uncertainty/evaluation note."
        ),
        "acceptance_test": (
            "Inactive historical rows can be projected to OGS cells with a trace/support definition rather "
            "than excluded for missing geometry."
        ),
        "refresh_commands": (
            "python inversion_workflow/scripts/build_permeability_observation_targets.py; "
            "python inversion_workflow/scripts/build_permeability_semantics_audit.py; "
            "python inversion_workflow/scripts/evaluate_permeability_targets.py; "
            "python inversion_workflow/scripts/build_measurement_operator_coverage.py; "
            "python inversion_workflow/scripts/build_measurement_likelihood_model.py; "
            "python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; "
            "python inversion_workflow/scripts/build_measurement_gate_closure_request.py; "
            "python inversion_workflow/scripts/build_external_gate_request_pack.py; "
            "python inversion_workflow/scripts/build_objective_readiness_audit.py"
        ),
        "gate_closure_effect": "May close the tracked PERM_SUPPORT caveat and add historical pulse-test rows to the direct parameter objective.",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--request-pack",
        type=Path,
        default=Path("inversion_workflow/external_gate_request_pack.csv"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/external_gate_response_intake.csv"),
    )
    parser.add_argument(
        "--output-summary",
        type=Path,
        default=Path("inversion_workflow/external_gate_response_intake_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/external_gate_response_intake.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files"),
    )
    return parser.parse_args()


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def read_request_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def build_rows(repo_root: Path, request_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    intake_rows = []
    for request in request_rows:
        request_id = request["request_id"]
        policy = INTAKE_POLICIES[request_id]
        intake_dir = repo_root.parent / policy["intake_dir"]
        intake_dir.mkdir(parents=True, exist_ok=True)
        intake_rows.append(
            {
                "request_id": request_id,
                "stream": request["stream"],
                "gate_id": request["gate_id"],
                "priority": request["priority"],
                "audience": request["audience"],
                "suggested_to": request.get("suggested_to", ""),
                "suggested_cc": request.get("suggested_cc", ""),
                "contact_route_status": request.get("contact_route_status", ""),
                "request_status": request.get("request_status", "drafted_pending_send"),
                "response_status": "missing_response",
                "intake_dir": str(intake_dir),
                "expected_response_artifacts": policy["expected_response_artifacts"],
                "minimum_intake_metadata": policy["minimum_intake_metadata"],
                "acceptance_test": policy["acceptance_test"],
                "refresh_commands": policy["refresh_commands"],
                "gate_closure_effect": policy["gate_closure_effect"],
                "current_blocker_or_caveat": request["current_blocker_or_caveat"],
                "recipient_draft": request["recipient_draft"],
                "response_files_recorded": "",
                "response_notes_md": str(intake_dir / f"{request_id}_response_notes.md"),
                "next_action": "send_request_then_place_response_files_in_intake_dir_and_record_notes",
            }
        )
    return intake_rows


def write_markdown(path: Path, rows: list[dict[str, str]], summary: dict[str, Any]) -> None:
    lines = [
        "# External Gate Response Intake",
        "",
        "This tracker says where each external response should be filed, what minimum metadata is needed, and which generated artifacts need refreshing after a response arrives.",
        "It does not indicate that the requests have been sent or answered.",
        "",
        "## Summary",
        "",
        f"- Status: `{summary['status']}`",
        f"- External request rows tracked: {summary['tracked_request_count']}",
        f"- Missing responses: {summary['missing_response_count']}",
        f"- Intake directories created: {summary['intake_directory_count']}",
        "",
        "## Intake Table",
        "",
        "| Request | Gate | Status | Intake directory | Acceptance test |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['request_id']}`",
                    f"`{row['gate_id']}`",
                    f"`{row['response_status']}`",
                    f"`{row['intake_dir']}`",
                    row["acceptance_test"].replace("|", "\\|"),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Details", ""])
    for row in rows:
        lines.extend(
            [
                f"### `{row['request_id']}`",
                "",
                f"- Audience: {row['audience']}",
                f"- Suggested To: `{row.get('suggested_to', '')}`",
                f"- Suggested Cc: `{row.get('suggested_cc', '') or 'none'}`",
                f"- Contact route: `{row.get('contact_route_status', '')}`",
                f"- Recipient draft: `{row['recipient_draft']}`",
                f"- Intake directory: `{row['intake_dir']}`",
                f"- Expected response artifacts: {row['expected_response_artifacts']}",
                f"- Minimum intake metadata: {row['minimum_intake_metadata']}",
                f"- Acceptance test: {row['acceptance_test']}",
                f"- Refresh commands after intake: `{row['refresh_commands']}`",
                f"- Gate-closure effect: {row['gate_closure_effect']}",
                f"- Current blocker/caveat: {row['current_blocker_or_caveat']}",
                f"- Response notes file to create/update: `{row['response_notes_md']}`",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def ensure_response_note_templates(rows: list[dict[str, str]]) -> list[Path]:
    paths = []
    for row in rows:
        path = Path(row["response_notes_md"])
        paths.append(path)
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            f"# Response Notes: {row['request_id']}",
            "",
            "- Response status: `missing_response`",
            "- Request status: `drafted_pending_send`",
            f"- Gate: `{row['gate_id']}`",
            f"- Audience: {row['audience']}",
            f"- Suggested To: `{row.get('suggested_to', '')}`",
            f"- Suggested Cc: `{row.get('suggested_cc', '') or 'none'}`",
            f"- Contact route: `{row.get('contact_route_status', '')}`",
            f"- Recipient draft: `{row['recipient_draft']}`",
            "",
            "## Received Files Or Answers",
            "",
            "- None recorded yet.",
            "",
            "## Intake Metadata Checklist",
            "",
            f"- {row['minimum_intake_metadata']}",
            "",
            "## Acceptance Test",
            "",
            row["acceptance_test"],
            "",
            "## Refresh Commands After Acceptance",
            "",
            f"`{row['refresh_commands']}`",
            "",
            "## Gate Decision",
            "",
            f"- Current effect if accepted: {row['gate_closure_effect']}",
            "- Decision: `not_evaluated`",
            "- Evaluated by/date: not recorded",
            "",
        ]
        path.write_text("\n".join(lines), encoding="utf-8")
    return paths


def copy_outputs(catalogue_dir: Path, paths: list[Path]) -> list[dict[str, str]]:
    catalogue_dir.mkdir(parents=True, exist_ok=True)
    copies = []
    for source in paths:
        target = catalogue_dir / source.name
        if source.exists():
            shutil.copy2(source, target)
        copies.append({"source": str(source), "catalogue_copy": str(target)})
    return copies


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[2]
    request_pack = (repo / args.request_pack if not args.request_pack.is_absolute() else args.request_pack).resolve()
    output_csv = (repo / args.output_csv if not args.output_csv.is_absolute() else args.output_csv).resolve()
    output_summary = (repo / args.output_summary if not args.output_summary.is_absolute() else args.output_summary).resolve()
    output_md = (repo / args.output_md if not args.output_md.is_absolute() else args.output_md).resolve()
    catalogue_dir = (repo / args.catalogue_dir if not args.catalogue_dir.is_absolute() else args.catalogue_dir).resolve()

    request_rows = read_request_rows(request_pack)
    rows = build_rows(repo, request_rows)
    response_note_templates = ensure_response_note_templates(rows)
    write_csv(output_csv, rows)

    intake_dirs = sorted({row["intake_dir"] for row in rows})
    missing = [row for row in rows if row["response_status"] == "missing_response"]
    rows_with_to = [row for row in rows if row.get("suggested_to")]
    summary = {
        "status": "external_gate_response_intake_generated_waiting_for_responses",
        "tracked_request_count": len(rows),
        "missing_response_count": len(missing),
        "tracked_request_with_suggested_to_count": len(rows_with_to),
        "intake_directory_count": len(intake_dirs),
        "intake_directories": intake_dirs,
        "response_note_template_count": len(response_note_templates),
        "response_note_templates": [str(path) for path in response_note_templates],
        "request_ids": [row["request_id"] for row in rows],
        "generated_files": [
            str(output_csv.relative_to(repo)),
            str(output_summary.relative_to(repo)),
            str(output_md.relative_to(repo)),
        ],
    }
    write_markdown(output_md, rows, summary)
    summary["catalogue_copies"] = copy_outputs(catalogue_dir, [output_csv, output_summary, output_md])
    output_summary.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    copy_outputs(catalogue_dir, [output_summary])
    print(json.dumps(json_ready(summary), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
