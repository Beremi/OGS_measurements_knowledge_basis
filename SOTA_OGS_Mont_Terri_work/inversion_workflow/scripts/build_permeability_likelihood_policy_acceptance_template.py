#!/usr/bin/env python3
"""Build a fillable acceptance template for permeability likelihood policy choices."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd


APPROVAL_STATUS = "not_approved_template_only"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--decision-csv",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_decision_request.csv"),
    )
    parser.add_argument(
        "--decision-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_decision_request_summary.json"),
    )
    parser.add_argument(
        "--recommendation-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_support_recommendations_summary.json"),
    )
    parser.add_argument(
        "--support-spatial-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_support_conflict_spatial_audit_summary.json"),
    )
    parser.add_argument(
        "--next-gate-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_next_field_fit_gate_summary.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_policy_acceptance_record_template.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_policy_acceptance_record_template_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/permeability_likelihood_policy_audit/derived_files"),
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def clean(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def build_rows(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    decision_rows = read_csv(args.decision_csv)
    decision = read_json(args.decision_summary)
    recommendations = read_json(args.recommendation_summary)
    support_spatial = read_json(args.support_spatial_summary)
    next_gate = read_json(args.next_gate_summary)
    top_conflict = support_spatial.get("top_conflict_cell", {})
    support_conflict_evidence = (
        f"Spatial support-conflict audit status={support_spatial.get('status')}; "
        f"active/repeated/range>=2 support cells="
        f"{support_spatial.get('active_support_cell_count')}/"
        f"{support_spatial.get('repeated_support_cell_count')}/"
        f"{support_spatial.get('support_cells_observed_range_ge_2_log10')}; "
        f"top conflict cell={top_conflict.get('primary_cell_id')} "
        f"({top_conflict.get('segments')} at {top_conflict.get('depth_min_m')}-"
        f"{top_conflict.get('depth_max_m')} m, observed range="
        f"{top_conflict.get('observed_log10_range')})"
    )

    rows: list[dict[str, Any]] = []
    for _, item in decision_rows.iterrows():
        option_id = clean(item.get("option_id"))
        recommended_default = bool(item.get("recommended_default"))
        rows.append(
            {
                "option_id": option_id,
                "decision_type": clean(item.get("decision_type")),
                "current_recommended_default": recommended_default,
                "objective_policy": clean(item.get("objective_policy")),
                "diagnostic_value": item.get("diagnostic_value"),
                "risk_or_caveat": clean(item.get("risk_or_caveat")),
                "acceptance_criteria": clean(item.get("acceptance_criteria")),
                "support_conflict_evidence_to_acknowledge": support_conflict_evidence,
                "approval_status": APPROVAL_STATUS,
                "primary_policy_selection": "",
                "approver_name": "",
                "approval_date": "",
                "approval_reference": "",
                "accepted_formula_or_policy_text": "",
                "accepted_weighting_or_grouping_rule": "",
                "accepted_outlier_or_bounds_disposition": "",
                "accepted_next_ogs_materiality_rule": "",
                "post_approval_required_reruns": (
                    "Rerun permeability likelihood rerank if the accepted formula differs from the audited "
                    "diagnostic policies; rerun current-field, scenario, promotion, open-question, and "
                    "readiness audits before changing any field label or reopening OGS spending."
                ),
                "guardrail": (
                    "Template row only. This does not approve a direct-permeability policy until "
                    "approval_status=approved, primary_policy_selection=selected for exactly one row, "
                    "and all approval/provenance fields are filled from a real modelling-team decision."
                ),
            }
        )

    frame = pd.DataFrame(rows)
    approved_primary = frame[
        frame["approval_status"].eq("approved") & frame["primary_policy_selection"].eq("selected")
    ]
    required_primary_count = 1 if not frame.empty else 0
    approved_primary_count = int(approved_primary.shape[0])
    mandatory_columns = [
        "approver_name",
        "approval_date",
        "approval_reference",
        "accepted_formula_or_policy_text",
    ]
    mandatory_complete = bool(
        approved_primary_count == 1
        and approved_primary[mandatory_columns].astype(str).apply(lambda col: col.str.len().gt(0)).all().all()
    )
    selected_policy = clean(approved_primary.iloc[0].get("option_id")) if approved_primary_count == 1 else ""

    summary: dict[str, Any] = {
        "status": "permeability_likelihood_policy_acceptance_record_template_generated",
        "template_row_count": int(frame.shape[0]),
        "primary_policy_approval_rows_required": required_primary_count,
        "primary_policy_approval_rows_recorded": approved_primary_count,
        "ready_to_apply_policy": mandatory_complete,
        "selected_policy_option_id": selected_policy,
        "records_actual_decision": False,
        "changes_active_objective": False,
        "promotes_current_field": False,
        "same_support_batch_executable_now": False,
        "sends_or_modifies_email": False,
        "current_report_policy_before_approval": recommendations.get(
            "current_report_policy",
            decision.get("recommended_current_report_policy"),
        ),
        "recommendation_packet_status": recommendations.get("status"),
        "recommendation_count": recommendations.get("recommendation_count"),
        "same_support_reducible_objective_gap": recommendations.get("same_support_reducible_objective_gap"),
        "support_conflict_spatial_audit_status": support_spatial.get("status"),
        "support_conflict_spatial_active_support_cell_count": support_spatial.get("active_support_cell_count"),
        "support_conflict_spatial_repeated_support_cell_count": support_spatial.get("repeated_support_cell_count"),
        "support_conflict_spatial_range_ge_2_log10_cell_count": support_spatial.get(
            "support_cells_observed_range_ge_2_log10"
        ),
        "support_conflict_spatial_top_conflict_cell": top_conflict,
        "next_field_fit_gate_status": next_gate.get("status"),
        "next_field_fit_gate_recommendation": next_gate.get("overall_recommendation"),
        "next_field_fit_gate_executable_same_support_batch_now": next_gate.get(
            "executable_same_support_active_objective_batch_now"
        ),
        "approval_status_counts": frame["approval_status"].value_counts().sort_index().to_dict()
        if not frame.empty
        else {},
        "next_action": (
            "Fill this template only after the modelling team chooses the direct-permeability "
            "likelihood/support/outlier policy. Until exactly one primary policy row is approved "
            "with provenance, keep the rowwise Gaussian policy as the current-report default and "
            "keep same-support active-objective OGS spending paused."
        ),
        "source_artifacts": [
            "inversion_workflow/permeability_likelihood_decision_request.csv",
            "inversion_workflow/permeability_likelihood_decision_request_summary.json",
            "inversion_workflow/permeability_likelihood_support_recommendations_summary.json",
            "inversion_workflow/permeability_support_conflict_spatial_audit_summary.json",
            "inversion_workflow/permeability_next_field_fit_gate_summary.json",
        ],
    }
    return frame, summary


def write_outputs(frame: pd.DataFrame, summary: dict[str, Any], args: argparse.Namespace) -> None:
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output_csv, index=False)
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Permeability Likelihood Policy Acceptance Record Template",
        "",
        "This generated file is a fillable signoff template for the direct-permeability",
        "likelihood/support/outlier policy. It is not an approval record, does not",
        "change the active objective, does not reopen OGS spending, and does not promote",
        "a permeability field.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Template rows: {summary['template_row_count']}",
        f"- Primary policy approvals required: {summary['primary_policy_approval_rows_required']}",
        f"- Primary policy approvals recorded: {summary['primary_policy_approval_rows_recorded']}",
        f"- Ready to apply policy: `{summary['ready_to_apply_policy']}`",
        f"- Records actual decision: `{summary['records_actual_decision']}`",
        f"- Changes active objective: `{summary['changes_active_objective']}`",
        f"- Promotes current field: `{summary['promotes_current_field']}`",
        f"- Same-support batch executable now: `{summary['same_support_batch_executable_now']}`",
        f"- Current-report policy before approval: `{summary['current_report_policy_before_approval']}`",
        f"- Spatial support cells active/repeated/range>=2 log10: "
        f"{summary['support_conflict_spatial_active_support_cell_count']}/"
        f"{summary['support_conflict_spatial_repeated_support_cell_count']}/"
        f"{summary['support_conflict_spatial_range_ge_2_log10_cell_count']}",
        f"- Next field-fit gate recommendation: `{summary['next_field_fit_gate_recommendation']}`",
        "",
        "## Required Approval Fields",
        "",
        "Exactly one row must be selected as the primary policy and must have all of the",
        "following fields filled from a real modelling-team decision:",
        "",
        "- `approval_status=approved`",
        "- `primary_policy_selection=selected`",
        "- `approver_name`",
        "- `approval_date`",
        "- `approval_reference`",
        "- `accepted_formula_or_policy_text`",
        "",
        "For non-default policies, also fill the applicable grouping, outlier/bounds,",
        "or materiality fields before rerunning downstream audits.",
        "",
        "## Template Rows",
        "",
        "| Option | Type | Approval status | Recommended default | Diagnostic value |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for row in frame.to_dict(orient="records"):
        lines.append(
            f"| `{row['option_id']}` | `{row['decision_type']}` | `{row['approval_status']}` | "
            f"`{row['current_recommended_default']}` | {row['diagnostic_value']} |"
        )

    lines.extend(["", "## Acceptance Criteria", ""])
    for row in frame.to_dict(orient="records"):
        lines.extend(
            [
                f"### `{row['option_id']}`",
                "",
                f"- Objective policy: {row['objective_policy']}",
                f"- Risk or caveat: {row['risk_or_caveat']}",
                f"- Acceptance criteria: {row['acceptance_criteria']}",
                f"- Support-conflict evidence to acknowledge: {row['support_conflict_evidence_to_acknowledge']}",
                f"- Post-approval reruns: {row['post_approval_required_reruns']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Source Artifacts",
            "",
        ]
    )
    for artifact in summary["source_artifacts"]:
        lines.append(f"- `{artifact}`")
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    generated = [args.output_csv, args.output_json, args.output_md]
    if args.catalogue_dir:
        args.catalogue_dir.mkdir(parents=True, exist_ok=True)
        copies = []
        for path in generated:
            target = args.catalogue_dir / path.name
            shutil.copy2(path, target)
            copies.append({"source": str(path), "catalogue_copy": str(target)})
        summary["catalogue_copies"] = copies
        args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        shutil.copy2(args.output_json, args.catalogue_dir / args.output_json.name)


def main() -> None:
    args = parse_args()
    frame, summary = build_rows(args)
    write_outputs(frame, summary, args)


if __name__ == "__main__":
    main()
