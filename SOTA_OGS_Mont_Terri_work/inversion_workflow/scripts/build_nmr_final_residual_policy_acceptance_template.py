#!/usr/bin/env python3
"""Build a fillable acceptance template for the final NMR residual policy."""

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
        default=Path("inversion_workflow/nmr_objective_decision.csv"),
    )
    parser.add_argument(
        "--decision-summary",
        type=Path,
        default=Path("inversion_workflow/nmr_objective_decision_summary.json"),
    )
    parser.add_argument(
        "--gate-summary",
        type=Path,
        default=Path("inversion_workflow/nmr_final_residual_policy_gate_summary.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/nmr_final_residual_policy_acceptance_record_template.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/nmr_final_residual_policy_acceptance_record_template_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/nmr_final_residual_policy_acceptance_record_template.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/nmr/derived_files"),
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
    decisions = read_csv(args.decision_csv)
    decision_summary = read_json(args.decision_summary)
    gate_summary = read_json(args.gate_summary)

    rows: list[dict[str, Any]] = []
    for _, item in decisions.iterrows():
        option_id = clean(item.get("option_id"))
        rows.append(
            {
                "option_id": option_id,
                "decision": clean(item.get("decision")),
                "current_recommended_for_final_objective": clean(item.get("recommended_for_final_objective")),
                "residual_definition": clean(item.get("residual_definition")),
                "nuisance_terms": clean(item.get("nuisance_terms")),
                "candidate_selected_by_this_option": clean(item.get("candidate_selected_by_this_option")),
                "candidate_current_combined_rank": item.get("candidate_current_combined_rank"),
                "candidate_bias_safe_rank": item.get("candidate_bias_safe_rank"),
                "combined_objective": item.get("combined_objective"),
                "nmr_objective": item.get("nmr_objective"),
                "nmr_rmse_normalized": item.get("nmr_rmse_normalized"),
                "active_rows": item.get("active_rows"),
                "label_groups": item.get("label_groups"),
                "nonphysical_or_caveated_rows": clean(item.get("nonphysical_or_caveated_rows")),
                "main_rationale": clean(item.get("main_rationale")),
                "acceptance_criteria": clean(item.get("acceptance_criteria")),
                "approval_status": APPROVAL_STATUS,
                "primary_policy_selection": "",
                "approver_name": "",
                "approval_date": "",
                "approval_reference": "",
                "accepted_residual_definition": "",
                "accepted_bound_or_free_water_policy": "",
                "accepted_bias_or_offset_policy": "",
                "accepted_reporting_wording": "",
                "accepted_next_ogs_materiality_rule": "",
                "post_approval_required_reruns": (
                    "Rerun conditional field selection, final objective scenario matrix, final promotion "
                    "checklist, open-question matrix, and objective readiness audit before changing any final "
                    "field label. Rerun candidate scoring if the accepted residual formula differs from the "
                    "audited options."
                ),
                "guardrail": (
                    "Template row only. This does not approve a final NMR policy until "
                    "approval_status=approved, primary_policy_selection=selected for exactly one row, and all "
                    "approval/provenance fields are filled from a real modelling-team decision."
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
        "accepted_residual_definition",
    ]
    mandatory_complete = bool(
        approved_primary_count == 1
        and approved_primary[mandatory_columns].astype(str).apply(lambda col: col.str.len().gt(0)).all().all()
    )
    selected_policy = clean(approved_primary.iloc[0].get("option_id")) if approved_primary_count == 1 else ""

    summary: dict[str, Any] = {
        "status": "nmr_final_residual_policy_acceptance_record_template_generated",
        "template_row_count": int(frame.shape[0]),
        "primary_policy_approval_rows_required": required_primary_count,
        "primary_policy_approval_rows_recorded": approved_primary_count,
        "ready_to_apply_policy": mandatory_complete,
        "selected_policy_option_id": selected_policy,
        "records_actual_decision": False,
        "changes_active_objective": False,
        "promotes_current_field": False,
        "new_ogs_batch_recommended_now": False,
        "sends_or_modifies_email": False,
        "current_report_default_policy_before_approval": gate_summary.get("current_report_default_policy"),
        "recommended_candidate_policy_before_approval": gate_summary.get("recommended_candidate_policy"),
        "recommended_candidate_run_before_approval": gate_summary.get("recommended_candidate_policy_run"),
        "final_nmr_policy_selected_before_approval": gate_summary.get("final_nmr_policy_selected"),
        "followup_recommendation_before_approval": gate_summary.get("followup_recommendation"),
        "decision_package_status": decision_summary.get("status"),
        "gate_status": gate_summary.get("status"),
        "approval_status_counts": frame["approval_status"].value_counts().sort_index().to_dict()
        if not frame.empty
        else {},
        "next_action": (
            "Fill this template only after the modelling team chooses the final NMR residual semantics. "
            "Until exactly one primary policy row is approved with provenance, keep raw absolute theta as "
            "the current-report default with caveats and keep trend/anomaly NMR as scenario/provisional "
            "evidence only."
        ),
        "source_artifacts": [
            "inversion_workflow/nmr_objective_decision.csv",
            "inversion_workflow/nmr_objective_decision_summary.json",
            "inversion_workflow/nmr_final_residual_policy_gate_summary.json",
        ],
    }
    return frame, summary


def write_outputs(frame: pd.DataFrame, summary: dict[str, Any], args: argparse.Namespace) -> None:
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output_csv, index=False)
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# NMR Final Residual Policy Acceptance Record Template",
        "",
        "This generated file is a fillable signoff template for the final NMR residual",
        "policy. It is not an approval record, does not change the active objective,",
        "does not recommend a new OGS batch, and does not promote a permeability field.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Template rows: {summary['template_row_count']}",
        f"- Primary policy approvals required: {summary['primary_policy_approval_rows_required']}",
        f"- Primary policy approvals recorded: {summary['primary_policy_approval_rows_recorded']}",
        f"- Ready to apply policy: `{summary['ready_to_apply_policy']}`",
        f"- Records actual decision: `{summary['records_actual_decision']}`",
        f"- Changes active objective: `{summary['changes_active_objective']}`",
        f"- Promotes current field: `{summary['promotes_current_field']}`",
        f"- New OGS batch recommended now: `{summary['new_ogs_batch_recommended_now']}`",
        f"- Current-report default before approval: `{summary['current_report_default_policy_before_approval']}`",
        f"- Recommended candidate before approval: `{summary['recommended_candidate_policy_before_approval']}`",
        f"- Recommended candidate run before approval: `{summary['recommended_candidate_run_before_approval']}`",
        f"- Follow-up recommendation before approval: `{summary['followup_recommendation_before_approval']}`",
        "",
        "## Required Approval Fields",
        "",
        "Exactly one row must be selected as the primary final NMR policy and must",
        "have all of the following fields filled from a real modelling-team decision:",
        "",
        "- `approval_status=approved`",
        "- `primary_policy_selection=selected`",
        "- `approver_name`",
        "- `approval_date`",
        "- `approval_reference`",
        "- `accepted_residual_definition`",
        "",
        "For absolute or bias-corrected policies, also fill the bound/free-water,",
        "bias/offset, reporting wording, and next-OGS materiality fields.",
        "",
        "## Template Rows",
        "",
        "| Option | Decision | Approval status | Current final recommendation | Selected run | Combined objective |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for row in frame.to_dict(orient="records"):
        lines.append(
            f"| `{row['option_id']}` | `{row['decision']}` | `{row['approval_status']}` | "
            f"`{row['current_recommended_for_final_objective']}` | "
            f"`{row['candidate_selected_by_this_option']}` | {row['combined_objective']} |"
        )

    lines.extend(["", "## Acceptance Criteria", ""])
    for row in frame.to_dict(orient="records"):
        lines.extend(
            [
                f"### `{row['option_id']}`",
                "",
                f"- Residual definition: {row['residual_definition']}",
                f"- Nuisance terms: {row['nuisance_terms'] or 'none'}",
                f"- Main rationale: {row['main_rationale']}",
                f"- Nonphysical or caveated rows/offsets: {row['nonphysical_or_caveated_rows']}",
                f"- Acceptance criteria: {row['acceptance_criteria']}",
                f"- Post-approval reruns: {row['post_approval_required_reruns']}",
                "",
            ]
        )

    lines.extend(["## Source Artifacts", ""])
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
