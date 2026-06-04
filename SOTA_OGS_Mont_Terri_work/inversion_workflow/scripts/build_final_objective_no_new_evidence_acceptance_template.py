#!/usr/bin/env python3
"""Build a fillable acceptance-record template for the no-new-evidence closeout."""

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
        "--draft-csv",
        type=Path,
        default=Path("inversion_workflow/final_objective_no_new_evidence_closeout_draft.csv"),
    )
    parser.add_argument(
        "--draft-summary",
        type=Path,
        default=Path("inversion_workflow/final_objective_no_new_evidence_closeout_draft_summary.json"),
    )
    parser.add_argument(
        "--decision-register",
        type=Path,
        default=Path("inversion_workflow/final_objective_decision_register.csv"),
    )
    parser.add_argument(
        "--scenario-matrix",
        type=Path,
        default=Path("inversion_workflow/final_objective_scenario_matrix.csv"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/final_objective_no_new_evidence_acceptance_record_template.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/final_objective_no_new_evidence_acceptance_record_template_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/final_objective_no_new_evidence_acceptance_record_template.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files"),
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


def first_row(frame: pd.DataFrame, column: str, value: str) -> dict[str, Any]:
    if frame.empty or column not in frame.columns:
        return {}
    match = frame[frame[column].astype(str) == value]
    return match.iloc[0].to_dict() if not match.empty else {}


def build_rows(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    draft = read_csv(args.draft_csv)
    draft_summary = read_json(args.draft_summary)
    decision_register = read_csv(args.decision_register)
    scenario_matrix = read_csv(args.scenario_matrix)
    f01 = first_row(scenario_matrix, "option_id", "F01_current_raw_nmr_exclude_gated_streams")

    rows: list[dict[str, Any]] = []
    for _, item in draft.iterrows():
        criterion_id = clean(item.get("criterion_id"))
        register_row = first_row(decision_register, "criterion_id", criterion_id)
        rows.append(
            {
                "criterion_id": criterion_id,
                "stream": clean(item.get("stream")),
                "decision_item": clean(item.get("decision_item")),
                "current_decision_status": clean(item.get("existing_decision_status")),
                "approval_status": APPROVAL_STATUS,
                "approval_required_from": clean(item.get("approval_required_from")),
                "approver_name": "",
                "approval_date": "",
                "approval_reference": "",
                "accepted_closeout_choice": clean(item.get("draft_closeout_choice")),
                "exact_decision_text_to_record": clean(item.get("exact_decision_record_text")),
                "decision_register_action_after_approval": clean(item.get("decision_register_action")),
                "exact_report_wording_after_approval": clean(item.get("exact_report_wording")),
                "scenario_effect_after_approval": clean(item.get("scenario_option_effect")),
                "model_consequence_after_approval": clean(item.get("interpretation_after_acceptance")),
                "current_evidence_before_approval": clean(item.get("current_evidence")),
                "source_evidence_locations": clean(item.get("source_locations")),
                "related_blocker_or_decision_ids": clean(register_row.get("related_blocker_or_decision_ids")),
                "must_regenerate_after_approval": clean(item.get("refresh_after_acceptance")),
                "guardrail": (
                    "Template row only. Do not treat this as an accepted decision until approval_status, "
                    "approver_name, approval_date, and approval_reference are filled from a real decision."
                ),
            }
        )

    frame = pd.DataFrame(rows)
    approved_rows = int(frame["approval_status"].eq("approved").sum()) if not frame.empty else 0
    required_rows = int(frame.shape[0])
    summary: dict[str, Any] = {
        "status": "final_objective_no_new_evidence_acceptance_record_template_generated",
        "template_row_count": required_rows,
        "approval_rows_required": required_rows,
        "approval_rows_recorded": approved_rows,
        "ready_to_apply_decisions": approved_rows == required_rows and required_rows > 0,
        "records_actual_decisions": False,
        "promotes_current_field": False,
        "sends_or_modifies_email": False,
        "approval_status": "awaiting_user_or_modelling_team_signoff",
        "approval_status_counts": frame["approval_status"].value_counts().sort_index().to_dict()
        if not frame.empty
        else {},
        "would_select_scenario_after_full_approval": f01.get(
            "option_id",
            draft_summary.get("would_select_scenario_if_all_rows_approved_and_audits_rerun"),
        ),
        "would_select_winner_after_full_approval": f01.get(
            "winner_run_id",
            draft_summary.get("would_select_winner_if_all_rows_approved_and_audits_rerun"),
        ),
        "current_field_is_winner_after_full_approval": bool(
            f01.get("current_is_winner", draft_summary.get("current_field_is_winner_in_draft_scenario", False))
        ),
        "open_blocker_count_before_approval": draft_summary.get("open_blocker_count"),
        "missing_response_blocker_count_before_approval": draft_summary.get("missing_response_blocker_count"),
        "unsent_gmail_draft_count_before_approval": draft_summary.get("gmail_unsent_draft_count"),
        "permeability_support_conflict_spatial_audit_status": draft_summary.get(
            "permeability_support_conflict_spatial_audit_status"
        ),
        "permeability_support_conflict_spatial_active_support_cell_count": draft_summary.get(
            "permeability_support_conflict_spatial_active_support_cell_count"
        ),
        "permeability_support_conflict_spatial_repeated_support_cell_count": draft_summary.get(
            "permeability_support_conflict_spatial_repeated_support_cell_count"
        ),
        "permeability_support_conflict_spatial_range_ge_2_log10_cell_count": draft_summary.get(
            "permeability_support_conflict_spatial_range_ge_2_log10_cell_count"
        ),
        "permeability_support_conflict_spatial_top_conflict_cell": draft_summary.get(
            "permeability_support_conflict_spatial_top_conflict_cell", {}
        ),
        "permeability_likelihood_policy_primary_approvals_recorded": draft_summary.get(
            "permeability_likelihood_policy_primary_approvals_recorded"
        ),
        "permeability_likelihood_policy_primary_approvals_required": draft_summary.get(
            "permeability_likelihood_policy_primary_approvals_required"
        ),
        "permeability_likelihood_policy_ready_to_apply": draft_summary.get(
            "permeability_likelihood_policy_ready_to_apply"
        ),
        "permeability_next_field_fit_gate_same_support_batch_executable_now": draft_summary.get(
            "permeability_next_field_fit_gate_same_support_batch_executable_now"
        ),
        "refresh_after_full_approval": draft_summary.get("refresh_after_acceptance"),
        "next_action": (
            "Use this as a fillable signoff record only if the user/model team chooses the "
            "conservative no-new-evidence closeout. Until every approval field is filled from "
            "a real decision, leave final promotion blocked."
        ),
        "source_artifacts": list(
            dict.fromkeys(
                [
                    "inversion_workflow/final_objective_no_new_evidence_closeout_draft.csv",
                    "inversion_workflow/final_objective_no_new_evidence_closeout_draft_summary.json",
                    "inversion_workflow/final_objective_decision_register.csv",
                    "inversion_workflow/final_objective_scenario_matrix.csv",
                ]
                + list(draft_summary.get("source_artifacts", []))
            )
        ),
    }
    return frame, summary


def write_outputs(frame: pd.DataFrame, summary: dict[str, Any], args: argparse.Namespace) -> None:
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output_csv, index=False)
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Final Objective No-New-Evidence Acceptance Record Template",
        "",
        "This generated file is a fillable signoff template for the conservative",
        "no-new-evidence closeout path. It is not an approval record, does not close",
        "provider gates, does not send email, and does not promote the current field.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Template rows: {summary['template_row_count']}",
        f"- Approval rows required: {summary['approval_rows_required']}",
        f"- Approval rows recorded: {summary['approval_rows_recorded']}",
        f"- Ready to apply decisions: `{summary['ready_to_apply_decisions']}`",
        f"- Records actual decisions: `{summary['records_actual_decisions']}`",
        f"- Promotes current field: `{summary['promotes_current_field']}`",
        f"- Sends or modifies email: `{summary['sends_or_modifies_email']}`",
        f"- Would select scenario after full approval: `{summary['would_select_scenario_after_full_approval']}`",
        f"- Would select winner after full approval: `{summary['would_select_winner_after_full_approval']}`",
        f"- Current field is winner after full approval: `{summary['current_field_is_winner_after_full_approval']}`",
        f"- Direct-permeability support-conflict audit: `{summary.get('permeability_support_conflict_spatial_audit_status')}`",
        (
            "- Direct-permeability active/repeated/range>=2 support cells: "
            f"{summary.get('permeability_support_conflict_spatial_active_support_cell_count')}/"
            f"{summary.get('permeability_support_conflict_spatial_repeated_support_cell_count')}/"
            f"{summary.get('permeability_support_conflict_spatial_range_ge_2_log10_cell_count')}"
        ),
        (
            "- Direct-permeability policy approvals before approval: "
            f"{summary.get('permeability_likelihood_policy_primary_approvals_recorded')}/"
            f"{summary.get('permeability_likelihood_policy_primary_approvals_required')}; "
            f"ready=`{summary.get('permeability_likelihood_policy_ready_to_apply')}`"
        ),
        (
            "- Same-support active-objective batch executable before approval: "
            f"`{summary.get('permeability_next_field_fit_gate_same_support_batch_executable_now')}`"
        ),
        "",
        "## Required Approval Fields",
        "",
        "Each row must have all of the following fields filled from a real user or",
        "modelling-team decision before the closeout can be applied:",
        "",
        "- `approval_status=approved`",
        "- `approver_name`",
        "- `approval_date`",
        "- `approval_reference`",
        "",
        "## Template Rows",
        "",
        "| Criterion | Stream | Approval status | Required approver | Closeout choice |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in frame.to_dict(orient="records"):
        lines.append(
            f"| `{row['criterion_id']}` {row['decision_item']} | {row['stream']} | "
            f"`{row['approval_status']}` | {row['approval_required_from']} | "
            f"`{row['accepted_closeout_choice']}` |"
        )

    lines.extend(["", "## Exact Decision Text", ""])
    for row in frame.to_dict(orient="records"):
        lines.extend(
            [
                f"### `{row['criterion_id']}` {row['decision_item']}",
                "",
                f"- Exact decision text to record: {row['exact_decision_text_to_record']}",
                f"- Decision-register action after approval: {row['decision_register_action_after_approval']}",
                f"- Exact report wording after approval: {row['exact_report_wording_after_approval']}",
                f"- Scenario effect after approval: {row['scenario_effect_after_approval']}",
                f"- Model consequence after approval: {row['model_consequence_after_approval']}",
                f"- Current evidence before approval: {row['current_evidence_before_approval'] or 'none recorded'}",
                f"- Source evidence locations: {row['source_evidence_locations'] or 'none recorded'}",
                f"- Related blockers/decisions: {row['related_blocker_or_decision_ids'] or 'none'}",
                "",
            ]
        )

    lines.extend(
        [
            "## After Full Approval",
            "",
            "Only after every row is approved and the decision layer has been updated, rerun:",
            "",
            "```bash",
            str(summary["refresh_after_full_approval"]).replace("; ", " \\\n  && "),
            "```",
            "",
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
