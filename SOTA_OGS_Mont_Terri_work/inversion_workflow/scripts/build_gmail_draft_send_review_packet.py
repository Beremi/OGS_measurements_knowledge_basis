#!/usr/bin/env python3
"""Build a consolidated review packet for unsent Gmail gate drafts."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/gmail_draft_send_review_packet.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/gmail_draft_send_review_packet_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/gmail_draft_send_review_packet.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files"),
        help="Optional catalogue derived_files directory to receive review-packet copies.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def join_values(values: list[Any], separator: str = "; ") -> str:
    clean: list[str] = []
    for value in values:
        if pd.isna(value):
            continue
        text = str(value)
        if text and text not in {"nan", "None"} and text not in clean:
            clean.append(text)
    return separator.join(clean)


def text_preview(path: str, max_lines: int = 16) -> str:
    candidate = Path(path)
    if not candidate.exists():
        return ""
    lines = candidate.read_text(encoding="utf-8", errors="ignore").splitlines()
    # Keep header and salutation/request lead without embedding the full draft.
    return "\n".join(lines[:max_lines])


def related_rows(frame: pd.DataFrame, ids: list[str]) -> pd.DataFrame:
    if frame.empty or "request_id" not in frame.columns:
        return pd.DataFrame()
    return frame[frame["request_id"].isin(ids)].copy()


def build_rows() -> tuple[pd.DataFrame, dict[str, Any]]:
    external_drafts = read_csv(Path("inversion_workflow/external_gate_gmail_drafts.csv"))
    cte_drafts = read_csv(Path("inversion_workflow/cte_confirmation_gmail_draft.csv"))
    blockers = read_csv(Path("inversion_workflow/external_blocker_dashboard.csv"))
    dispatch = read_csv(Path("inversion_workflow/external_gate_dispatch_audit.csv"))
    dispatch_summary = read_json(Path("inversion_workflow/external_gate_dispatch_audit_summary.json"))
    live_state = read_json(Path("inversion_workflow/gmail_gate_live_state_audit_summary.json"))
    closeout = read_json(Path("inversion_workflow/final_inversion_closeout_playbook_summary.json"))

    rows: list[dict[str, Any]] = []
    if not external_drafts.empty:
        for draft_id, group in external_drafts.groupby("gmail_draft_id", sort=True):
            request_ids = group["request_id"].dropna().astype(str).tolist()
            blockers_for_draft = related_rows(blockers, request_ids)
            dispatch_for_draft = related_rows(dispatch, request_ids)
            draft_files = group.get("recipient_draft", pd.Series(dtype=str)).dropna().astype(str).unique().tolist()
            rows.append(
                {
                    "draft_id": draft_id,
                    "draft_type": "external_measurement_gate",
                    "request_ids": join_values(request_ids, ","),
                    "subject": join_values(group.get("subject", pd.Series(dtype=str)).tolist()),
                    "to": join_values(group.get("to", pd.Series(dtype=str)).tolist()),
                    "cc": join_values(group.get("cc", pd.Series(dtype=str)).tolist()),
                    "message_id": join_values(group.get("gmail_message_id", pd.Series(dtype=str)).tolist()),
                    "thread_id": join_values(group.get("gmail_thread_id", pd.Series(dtype=str)).tolist()),
                    "created_at": join_values(group.get("created_at", pd.Series(dtype=str)).tolist()),
                    "send_status": join_values(group.get("send_status", pd.Series(dtype=str)).tolist()),
                    "local_draft_files": join_values(draft_files),
                    "all_dispatch_checks_ready": bool(
                        not dispatch_for_draft.empty
                        and dispatch_for_draft.get("ready", pd.Series(dtype=bool)).astype(bool).all()
                    ),
                    "response_note_locations": join_values(
                        blockers_for_draft.get("response_notes_md", pd.Series(dtype=str)).tolist()
                    ),
                    "intake_directories": join_values(
                        blockers_for_draft.get("intake_dir", pd.Series(dtype=str)).tolist()
                    ),
                    "acceptance_tests": join_values(
                        blockers_for_draft.get("acceptance_test", pd.Series(dtype=str)).tolist()
                    ),
                    "current_blockers": join_values(
                        blockers_for_draft.get("current_blocker_or_caveat", pd.Series(dtype=str)).tolist()
                    ),
                    "next_action": join_values(blockers_for_draft.get("next_action", pd.Series(dtype=str)).tolist()),
                    "draft_preview": text_preview(draft_files[0]) if draft_files else "",
                }
            )

    if not cte_drafts.empty:
        for draft_id, group in cte_drafts.groupby("gmail_draft_id", sort=True):
            request_ids = group["request_id"].dropna().astype(str).tolist()
            blockers_for_draft = related_rows(blockers, request_ids)
            rows.append(
                {
                    "draft_id": draft_id,
                    "draft_type": "model_provenance_confirmation",
                    "request_ids": join_values(request_ids, ","),
                    "subject": join_values(group.get("subject", pd.Series(dtype=str)).tolist()),
                    "to": join_values(group.get("to", pd.Series(dtype=str)).tolist()),
                    "cc": join_values(group.get("cc", pd.Series(dtype=str)).tolist()),
                    "message_id": join_values(group.get("gmail_message_id", pd.Series(dtype=str)).tolist()),
                    "thread_id": join_values(group.get("gmail_thread_id", pd.Series(dtype=str)).tolist()),
                    "created_at": join_values(group.get("created_at", pd.Series(dtype=str)).tolist()),
                    "send_status": join_values(group.get("send_status", pd.Series(dtype=str)).tolist()),
                    "local_draft_files": "inversion_workflow/cte_confirmation_request.md",
                    "all_dispatch_checks_ready": True,
                    "response_note_locations": join_values(
                        blockers_for_draft.get("response_notes_md", pd.Series(dtype=str)).tolist()
                    )
                    or "inversion_workflow/cte_confirmation_request.md",
                    "intake_directories": "not_applicable",
                    "acceptance_tests": join_values(
                        blockers_for_draft.get("acceptance_test", pd.Series(dtype=str)).tolist()
                    ),
                    "current_blockers": join_values(
                        blockers_for_draft.get("current_blocker_or_caveat", pd.Series(dtype=str)).tolist()
                    ),
                    "next_action": join_values(blockers_for_draft.get("next_action", pd.Series(dtype=str)).tolist()),
                    "draft_preview": text_preview("inversion_workflow/cte_confirmation_request.md"),
                }
            )

    frame = pd.DataFrame(rows).sort_values(["draft_type", "subject"]).reset_index(drop=True)
    unsent = int((frame["send_status"] == "gmail_draft_created_not_sent").sum()) if not frame.empty else 0
    ready = int(frame["all_dispatch_checks_ready"].sum()) if not frame.empty else 0
    summary = {
        "status": "gmail_draft_send_review_packet_generated_not_sent",
        "draft_count": int(frame.shape[0]),
        "unsent_draft_count": unsent,
        "ready_for_user_review_count": ready,
        "external_measurement_draft_count": int((frame["draft_type"] == "external_measurement_gate").sum())
        if not frame.empty
        else 0,
        "cte_confirmation_draft_count": int((frame["draft_type"] == "model_provenance_confirmation").sum())
        if not frame.empty
        else 0,
        "request_count": int(sum(len(str(ids).split(",")) for ids in frame.get("request_ids", pd.Series(dtype=str)))),
        "draft_ids": frame["draft_id"].tolist() if not frame.empty else [],
        "all_expected_drafts_observed": live_state.get("all_expected_drafts_observed"),
        "gmail_live_state_checked_at": live_state.get("checked_at"),
        "sent_subject_search_result_count": live_state.get("sent_subject_search_result_count"),
        "provider_reply_search_result_count": live_state.get("provider_reply_search_result_count"),
        "external_dispatch_status": dispatch_summary.get("status"),
        "external_dispatch_failed_check_count": dispatch_summary.get("failed_check_count"),
        "closeout_open_criterion_count": closeout.get("open_criterion_count"),
        "next_action": (
            "Review the six drafts in Gmail, send only after user approval, then file replies/files "
            "in the listed response-note locations and rerun the close-out audits."
        ),
        "source_artifacts": [
            "inversion_workflow/external_gate_gmail_drafts.csv",
            "inversion_workflow/cte_confirmation_gmail_draft.csv",
            "inversion_workflow/external_blocker_dashboard.csv",
            "inversion_workflow/external_gate_dispatch_audit.csv",
            "inversion_workflow/gmail_gate_live_state_audit_summary.json",
            "inversion_workflow/final_inversion_closeout_playbook.md",
        ],
    }
    return frame, summary


def write_outputs(frame: pd.DataFrame, summary: dict[str, Any], args: argparse.Namespace) -> None:
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output_csv, index=False)
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Gmail Draft Send Review Packet",
        "",
        "This packet consolidates the local review state for the six Gmail drafts that",
        "block final inversion promotion. It does not send, archive, delete, or label",
        "email.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Drafts: {summary['draft_count']}",
        f"- Unsent drafts: {summary['unsent_draft_count']}",
        f"- Ready for user review: {summary['ready_for_user_review_count']}",
        f"- External measurement drafts: {summary['external_measurement_draft_count']}",
        f"- CTE confirmation drafts: {summary['cte_confirmation_draft_count']}",
        f"- Gmail live-state checked at: `{summary.get('gmail_live_state_checked_at')}`",
        f"- Sent-subject hits: {summary.get('sent_subject_search_result_count')}",
        f"- Provider-reply hits: {summary.get('provider_reply_search_result_count')}",
        "",
        "## Drafts",
        "",
        "| Draft | Type | Requests | To | Cc | Subject | Ready | Response notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in frame.to_dict(orient="records"):
        lines.append(
            f"| `{row['draft_id']}` | `{row['draft_type']}` | `{row['request_ids']}` | "
            f"{row['to']} | {row['cc'] or 'none'} | {row['subject']} | "
            f"`{row['all_dispatch_checks_ready']}` | {row['response_note_locations']} |"
        )
    lines.extend(["", "## Review Notes", ""])
    for row in frame.to_dict(orient="records"):
        lines.extend(
            [
                f"### `{row['draft_id']}`",
                "",
                f"- Subject: {row['subject']}",
                f"- To: {row['to']}",
                f"- Cc: {row['cc'] or 'none'}",
                f"- Local draft file(s): {row['local_draft_files']}",
                f"- Request ids: {row['request_ids']}",
                f"- Current blocker: {row['current_blockers']}",
                f"- Acceptance evidence: {row['acceptance_tests']}",
                f"- Response/intake location: {row['response_note_locations']}",
                f"- Next action: {row['next_action']}",
                "",
                "Preview:",
                "",
                "```text",
                row["draft_preview"],
                "```",
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
    frame, summary = build_rows()
    write_outputs(frame, summary, args)


if __name__ == "__main__":
    main()
