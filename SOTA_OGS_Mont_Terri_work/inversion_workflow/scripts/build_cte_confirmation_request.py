#!/usr/bin/env python3
"""Build an outbound confirmation request for the suspicious OGS CTE value."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import date
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--thermal-audit",
        type=Path,
        default=Path("inversion_workflow/thermal_expansivity_parameter_audit_summary.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/cte_confirmation_request.csv"),
    )
    parser.add_argument(
        "--output-summary",
        type=Path,
        default=Path("inversion_workflow/cte_confirmation_request_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/cte_confirmation_request.md"),
    )
    parser.add_argument(
        "--gmail-draft",
        type=Path,
        default=Path("inversion_workflow/cte_confirmation_gmail_draft.csv"),
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_row(audit: dict[str, Any]) -> dict[str, str]:
    cte_value = audit.get("cte_value")
    cps_value = audit.get("c_p_s_value")
    ratio_high = audit.get("ratio_to_reference_high")
    return {
        "request_id": "cte_value_confirmation",
        "priority": "high",
        "issue_type": "model_provenance_confirmation",
        "subject": "CD-A OGS CTE value/provenance confirmation needed before thermal-parameter interpretation",
        "suggested_to": "Gesa.Ziefle@bgr.de",
        "suggested_cc": "Tuanny.Cajuhi@bgr.de",
        "contact_route_status": "coordinator_with_model_setup_cc",
        "contact_evidence": (
            "Gesa is the main CD-A coordination sender; Tuanny Cajuhi sent direct model-setup "
            "messages and discussed OGS support for distributed fields."
        ),
        "request_status": "drafted_pending_send",
        "response_status": "no_response_recorded",
        "current_evidence": (
            f"The active audit reads CTE={cte_value}, c_p_s={cps_value}, "
            f"CTE equals c_p_s={audit.get('cte_equals_c_p_s')}, bound property="
            f"{audit.get('cte_bound_property')}, expected unit={audit.get('expected_ogs_unit')}, "
            f"and CTE/reference-high ratio={ratio_high}."
        ),
        "current_blocker": (
            "The XML binds CTE to solid thermal_expansivity, but the value and comment look like "
            "a copied heat-capacity entry. The model must remain frozen, so this needs provenance "
            "confirmation rather than a local correction."
        ),
        "exact_request": (
            "Please confirm whether the XML parameter CTE=1254.74 in the CD-A OGS model is "
            "intended to be a solid linear thermal-expansivity value in 1/K, a mistaken copy of "
            "the solid heat capacity c_p_s, an inactive/irrelevant parameter in the intended run, "
            "or a value with another unit/convention."
        ),
        "minimum_acceptance_criteria": (
            "Written confirmation of the intended CTE meaning, unit, active/inactive status in the "
            "shared TRM setup, and the value that should be cited if the report discusses thermal "
            "expansivity or later releases thermal/retention/boundary parameters."
        ),
        "why_needed_for_model": (
            "The current inversion keeps thermal parameters fixed, but the report must not physically "
            "interpret CTE or release thermal/retention/boundary parameters while this XML value is "
            "unconfirmed."
        ),
        "would_unlock": (
            "A closed model-provenance note for the SOTA report and a clear release-gate decision for "
            "thermal expansivity."
        ),
        "local_artifacts": (
            "inversion_workflow/thermal_expansivity_parameter_audit.md; "
            "inversion_workflow/runs/direct_fit_observation_run/03_parameters_TRM.xml; "
            "inversion_workflow/runs/direct_fit_observation_run/04_media_TRM.xml"
        ),
        "acceptance_test": (
            "The CTE row in the report open-comment audit can move from open_confirmation_required "
            "to confirmed_inactive, confirmed_typo_not_changed, or confirmed_value_recorded with "
            "the provider response cited."
        ),
        "next_action": "send_confirmation_request_and_record_provider_response",
    }


def write_markdown(path: Path, row: dict[str, str], summary: dict[str, Any]) -> None:
    lines = [
        "# CTE Confirmation Request",
        "",
        "This request packages the suspicious CD-A OGS `CTE` value as a model-provenance confirmation item.",
        "It does not modify the frozen GESA model and does not claim that the value has been confirmed.",
        "",
        "## Summary",
        "",
        f"- Status: `{summary['status']}`",
        f"- Request id: `{row['request_id']}`",
        f"- Suggested To: `{row['suggested_to']}`",
        f"- Suggested Cc: `{row['suggested_cc']}`",
        f"- Contact route: `{row['contact_route_status']}`",
        f"- Request status: `{row['request_status']}`",
        f"- Response status: `{row['response_status']}`",
        f"- Gmail draft id: `{summary.get('gmail_draft_id') or 'none'}`",
        f"- Gmail send status: `{summary.get('gmail_send_status') or 'none'}`",
        "",
        "## Draft",
        "",
        f"Subject: {row['subject']}",
        f"Suggested To: {row['suggested_to']}",
        f"Suggested Cc: {row['suggested_cc']}",
        f"Contact route: {row['contact_route_status']}",
        f"Contact evidence: {row['contact_evidence']}",
        "",
        "Dear Gesa, Tuanny,",
        "",
        "While checking the recovered CD-A OGS XML against the report text, I found a thermal-expansivity provenance issue that should be confirmed before it is interpreted physically.",
        "",
        f"Request: {row['exact_request']}",
        "",
        f"Current local evidence/blocker: {row['current_evidence']} {row['current_blocker']}",
        "",
        f"Minimum acceptance criteria: {row['minimum_acceptance_criteria']}",
        "",
        f"Why this matters: {row['why_needed_for_model']}",
        "",
        f"Local artifacts we can share if useful: {row['local_artifacts']}",
        "",
        "Best,",
        "",
        "## Tracking Row",
        "",
        "| Field | Value |",
        "| --- | --- |",
    ]
    for key, value in row.items():
        lines.append(f"| `{key}` | {str(value).replace('|', '\\|')} |")
    path.write_text("\n".join(lines), encoding="utf-8")


def copy_outputs(catalogue_dir: Path, paths: list[Path]) -> list[dict[str, str]]:
    catalogue_dir.mkdir(parents=True, exist_ok=True)
    copies = []
    for source in paths:
        target = catalogue_dir / source.name
        if source.exists():
            shutil.copy2(source, target)
        copies.append({"source": str(source), "catalogue_copy": str(target)})
    return copies


def read_optional_gmail_draft(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    return rows[0] if rows else {}


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[2]
    thermal_audit = (repo / args.thermal_audit if not args.thermal_audit.is_absolute() else args.thermal_audit).resolve()
    output_csv = (repo / args.output_csv if not args.output_csv.is_absolute() else args.output_csv).resolve()
    output_summary = (repo / args.output_summary if not args.output_summary.is_absolute() else args.output_summary).resolve()
    output_md = (repo / args.output_md if not args.output_md.is_absolute() else args.output_md).resolve()
    gmail_draft = (repo / args.gmail_draft if not args.gmail_draft.is_absolute() else args.gmail_draft).resolve()
    catalogue_dir = (repo / args.catalogue_dir if not args.catalogue_dir.is_absolute() else args.catalogue_dir).resolve()

    audit = read_json(thermal_audit)
    row = build_row(audit)
    gmail = read_optional_gmail_draft(gmail_draft)
    summary: dict[str, Any] = {
        "status": (
            "cte_confirmation_gmail_draft_created_waiting_user_send_and_response"
            if gmail.get("send_status") == "gmail_draft_created_not_sent"
            else "cte_confirmation_request_generated_not_sent"
        ),
        "generated_on": date.today().isoformat(),
        "request_id": row["request_id"],
        "request_status": row["request_status"],
        "response_status": row["response_status"],
        "gmail_draft_tracker": str(gmail_draft.relative_to(repo)) if gmail else "",
        "gmail_draft_id": gmail.get("gmail_draft_id", ""),
        "gmail_message_id": gmail.get("gmail_message_id", ""),
        "gmail_thread_id": gmail.get("gmail_thread_id", ""),
        "gmail_send_status": gmail.get("send_status", ""),
        "suggested_to": row["suggested_to"],
        "suggested_cc": row["suggested_cc"],
        "contact_route_status": row["contact_route_status"],
        "thermal_audit_status": audit.get("status"),
        "cte_value": audit.get("cte_value"),
        "c_p_s_value": audit.get("c_p_s_value"),
        "cte_equals_c_p_s": audit.get("cte_equals_c_p_s"),
        "ratio_to_reference_high": audit.get("ratio_to_reference_high"),
        "generated_files": [
            str(gmail_draft.relative_to(repo)) if gmail else "",
            str(output_csv.relative_to(repo)),
            str(output_summary.relative_to(repo)),
            str(output_md.relative_to(repo)),
        ],
    }
    write_csv(output_csv, [row])
    write_markdown(output_md, row, summary)
    output_summary.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    catalogue_sources = [path for path in [gmail_draft, output_csv, output_summary, output_md] if path.exists()]
    summary["catalogue_copies"] = copy_outputs(catalogue_dir, catalogue_sources)
    output_summary.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    copy_outputs(catalogue_dir, [output_summary])
    print(json.dumps(json_ready(summary), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
