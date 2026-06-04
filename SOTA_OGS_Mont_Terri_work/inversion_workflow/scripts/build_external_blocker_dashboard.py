#!/usr/bin/env python3
"""Build one dashboard for open external measurement and CTE blockers."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


MISSING_RESPONSE_STATUSES = {"missing_response", "no_response_recorded", ""}
UNSENT_STATUSES = {"gmail_draft_created_not_sent", "drafted_pending_send"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--external-intake",
        type=Path,
        default=Path("inversion_workflow/external_gate_response_intake.csv"),
    )
    parser.add_argument(
        "--external-drafts",
        type=Path,
        default=Path("inversion_workflow/external_gate_gmail_drafts.csv"),
    )
    parser.add_argument(
        "--dispatch-summary",
        type=Path,
        default=Path("inversion_workflow/external_gate_dispatch_audit_summary.json"),
    )
    parser.add_argument(
        "--gmail-live-summary",
        type=Path,
        default=Path("inversion_workflow/gmail_gate_live_state_audit_summary.json"),
    )
    parser.add_argument(
        "--local-recovery-summary",
        type=Path,
        default=Path("inversion_workflow/local_gate_recovery_audit_summary.json"),
    )
    parser.add_argument(
        "--download-recovery-summary",
        type=Path,
        default=Path("inversion_workflow/download_gate_recovery_audit_summary.json"),
    )
    parser.add_argument(
        "--cte-request",
        type=Path,
        default=Path("inversion_workflow/cte_confirmation_request.csv"),
    )
    parser.add_argument(
        "--cte-draft",
        type=Path,
        default=Path("inversion_workflow/cte_confirmation_gmail_draft.csv"),
    )
    parser.add_argument(
        "--cte-summary",
        type=Path,
        default=Path("inversion_workflow/cte_confirmation_request_summary.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/external_blocker_dashboard.csv"),
    )
    parser.add_argument(
        "--output-summary",
        type=Path,
        default=Path("inversion_workflow/external_blocker_dashboard_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/external_blocker_dashboard.md"),
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


def resolve(repo: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo / path


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_status(value: str | None) -> str:
    return (value or "").strip()


def row_status(send_status: str, response_status: str, draft_observed: bool) -> str:
    response_status = normalize_status(response_status)
    send_status = normalize_status(send_status)
    if response_status not in MISSING_RESPONSE_STATUSES:
        return "response_recorded_requires_gate_refresh"
    if send_status in UNSENT_STATUSES:
        if not draft_observed:
            return "blocked_waiting_user_send_provider_response_and_draft_review"
        return "blocked_waiting_user_send_and_provider_response"
    if not send_status:
        return "blocked_missing_draft_or_response_route"
    return "blocked_waiting_provider_response"


def gate_summary_value(summary: dict[str, Any], request_id: str, key: str, default: str | int = "") -> Any:
    gate_summaries = summary.get("gate_summaries", {})
    if not isinstance(gate_summaries, dict):
        return default
    gate_summary = gate_summaries.get(request_id, {})
    if not isinstance(gate_summary, dict):
        return default
    return gate_summary.get(key, default)


def build_external_rows(
    intake_rows: list[dict[str, str]],
    draft_rows: list[dict[str, str]],
    gmail_live_state: dict[str, Any],
    local_recovery: dict[str, Any],
    download_recovery: dict[str, Any],
) -> list[dict[str, str]]:
    drafts_by_request = {row["request_id"]: row for row in draft_rows}
    observed_draft_ids = set(gmail_live_state.get("draft_ids_observed", []))
    rows: list[dict[str, str]] = []
    for intake in intake_rows:
        request_id = intake["request_id"]
        draft = drafts_by_request.get(request_id, {})
        draft_id = draft.get("gmail_draft_id", "")
        send_status = draft.get("send_status", intake.get("request_status", ""))
        response_status = intake.get("response_status", "")
        draft_observed = bool(draft_id and draft_id in observed_draft_ids)
        local_possible_count = int(gate_summary_value(local_recovery, request_id, "possible_closure_evidence_count", 0) or 0)
        download_possible_count = int(
            gate_summary_value(download_recovery, request_id, "possible_closure_evidence_count", 0) or 0
        )
        rows.append(
            {
                "request_id": request_id,
                "blocker_type": "external_measurement_gate",
                "priority": intake.get("priority", ""),
                "stream": intake.get("stream", ""),
                "gate_id": intake.get("gate_id", ""),
                "subject": draft.get("subject", ""),
                "suggested_to": draft.get("to", intake.get("suggested_to", "")),
                "suggested_cc": draft.get("cc", intake.get("suggested_cc", "")),
                "contact_route_status": intake.get("contact_route_status", ""),
                "gmail_draft_id": draft_id,
                "gmail_message_id": draft.get("gmail_message_id", ""),
                "gmail_thread_id": draft.get("gmail_thread_id", ""),
                "gmail_send_status": send_status,
                "observed_in_gmail_live_state": str(draft_observed).lower(),
                "sent_subject_search_result_count": str(gmail_live_state.get("sent_subject_search_result_count", 0)),
                "provider_reply_search_result_count": str(gmail_live_state.get("provider_reply_search_result_count", 0)),
                "teambeam_context_non_draft_result_count": str(
                    gmail_live_state.get("teambeam_context_non_draft_result_count", 0)
                ),
                "request_status": intake.get("request_status", ""),
                "response_status": response_status,
                "blocker_status": row_status(send_status, response_status, draft_observed),
                "intake_dir": intake.get("intake_dir", ""),
                "response_notes_md": intake.get("response_notes_md", ""),
                "response_files_recorded": intake.get("response_files_recorded", ""),
                "local_recovery_status": str(
                    gate_summary_value(local_recovery, request_id, "local_status", "not_checked")
                ),
                "local_possible_closure_evidence_count": str(local_possible_count),
                "downloads_recovery_status": str(
                    gate_summary_value(download_recovery, request_id, "local_status", "not_checked")
                ),
                "downloads_possible_closure_evidence_count": str(download_possible_count),
                "acceptance_test": intake.get("acceptance_test", ""),
                "current_blocker_or_caveat": intake.get("current_blocker_or_caveat", ""),
                "next_action": "review_send_gmail_draft_then_file_provider_response_in_intake_dir",
                "source_tracker": "inversion_workflow/external_gate_response_intake.csv",
            }
        )
    return rows


def build_cte_row(
    cte_request_rows: list[dict[str, str]],
    cte_draft_rows: list[dict[str, str]],
    cte_summary: dict[str, Any],
    gmail_live_state: dict[str, Any],
) -> list[dict[str, str]]:
    if not cte_request_rows and not cte_summary:
        return []
    request = cte_request_rows[0] if cte_request_rows else {}
    draft = cte_draft_rows[0] if cte_draft_rows else {}
    draft_id = draft.get("gmail_draft_id") or str(cte_summary.get("gmail_draft_id", "") or "")
    observed_draft_ids = set(gmail_live_state.get("draft_ids_observed", []))
    draft_observed = bool(draft_id and draft_id in observed_draft_ids)
    send_status = draft.get("send_status") or str(cte_summary.get("gmail_send_status", "") or "")
    response_status = request.get("response_status") or str(cte_summary.get("response_status", "") or "")
    return [
        {
            "request_id": request.get("request_id") or str(cte_summary.get("request_id", "cte_value_confirmation")),
            "blocker_type": "model_provenance_confirmation",
            "priority": request.get("priority", "high"),
            "stream": "model_provenance",
            "gate_id": "CTE_VALUE_CONFIRMATION",
            "subject": draft.get("subject") or request.get("subject", ""),
            "suggested_to": draft.get("to") or request.get("suggested_to", ""),
            "suggested_cc": draft.get("cc") or request.get("suggested_cc", ""),
            "contact_route_status": request.get("contact_route_status") or str(
                cte_summary.get("contact_route_status", "")
            ),
            "gmail_draft_id": draft_id,
            "gmail_message_id": draft.get("gmail_message_id") or str(cte_summary.get("gmail_message_id", "") or ""),
            "gmail_thread_id": draft.get("gmail_thread_id") or str(cte_summary.get("gmail_thread_id", "") or ""),
            "gmail_send_status": send_status,
            "observed_in_gmail_live_state": str(draft_observed).lower(),
            "sent_subject_search_result_count": str(gmail_live_state.get("sent_subject_search_result_count", 0)),
            "provider_reply_search_result_count": str(gmail_live_state.get("provider_reply_search_result_count", 0)),
            "teambeam_context_non_draft_result_count": str(
                gmail_live_state.get("teambeam_context_non_draft_result_count", 0)
            ),
            "request_status": request.get("request_status") or str(cte_summary.get("request_status", "") or ""),
            "response_status": response_status,
            "blocker_status": row_status(send_status, response_status, draft_observed),
            "intake_dir": "",
            "response_notes_md": "inversion_workflow/cte_confirmation_request.md",
            "response_files_recorded": "",
            "local_recovery_status": "not_applicable_model_provenance_confirmation",
            "local_possible_closure_evidence_count": "not_applicable",
            "downloads_recovery_status": "not_applicable_model_provenance_confirmation",
            "downloads_possible_closure_evidence_count": "not_applicable",
            "acceptance_test": request.get("acceptance_test", ""),
            "current_blocker_or_caveat": request.get("current_blocker", ""),
            "next_action": "review_send_cte_confirmation_draft_then_record_provider_response",
            "source_tracker": "inversion_workflow/cte_confirmation_request.csv",
        }
    ]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def count_possible_closure_rows(summary: dict[str, Any]) -> int:
    gate_summaries = summary.get("gate_summaries", {})
    if not isinstance(gate_summaries, dict):
        return 0
    return sum(
        int(value.get("possible_closure_evidence_count", 0) or 0)
        for value in gate_summaries.values()
        if isinstance(value, dict)
    )


def build_summary(
    rows: list[dict[str, str]],
    gmail_live_state: dict[str, Any],
    dispatch_summary: dict[str, Any],
    local_recovery: dict[str, Any],
    download_recovery: dict[str, Any],
) -> dict[str, Any]:
    status_counts = Counter(row["blocker_status"] for row in rows)
    send_status_counts = Counter(row["gmail_send_status"] for row in rows)
    response_status_counts = Counter(row["response_status"] for row in rows)
    priority_counts = Counter(row["priority"] for row in rows)
    type_counts = Counter(row["blocker_type"] for row in rows)
    open_rows = [
        row
        for row in rows
        if row["blocker_status"] != "response_recorded_requires_gate_refresh"
    ]
    unsent_rows = [row for row in rows if row["gmail_send_status"] in UNSENT_STATUSES]
    missing_response_rows = [row for row in rows if row["response_status"] in MISSING_RESPONSE_STATUSES]
    external_rows = [row for row in rows if row["blocker_type"] == "external_measurement_gate"]
    cte_rows = [row for row in rows if row["blocker_type"] == "model_provenance_confirmation"]
    summary = {
        "status": (
            "external_blocker_dashboard_generated_waiting_user_send_and_responses"
            if open_rows
            else "external_blocker_dashboard_no_open_blockers"
        ),
        "generated_on": date.today().isoformat(),
        "blocker_count": len(rows),
        "external_measurement_blocker_count": len(external_rows),
        "cte_confirmation_blocker_count": len(cte_rows),
        "open_blocker_count": len(open_rows),
        "unsent_blocker_count": len(unsent_rows),
        "missing_response_blocker_count": len(missing_response_rows),
        "status_counts": dict(status_counts),
        "gmail_send_status_counts": dict(send_status_counts),
        "response_status_counts": dict(response_status_counts),
        "priority_counts": dict(priority_counts),
        "blocker_type_counts": dict(type_counts),
        "draft_ids": sorted({row["gmail_draft_id"] for row in rows if row["gmail_draft_id"]}),
        "observed_draft_ids": sorted(
            {row["gmail_draft_id"] for row in rows if row["observed_in_gmail_live_state"] == "true"}
        ),
        "all_expected_drafts_observed": bool(gmail_live_state.get("all_expected_drafts_observed", False)),
        "gmail_live_state_checked_at": gmail_live_state.get("checked_at", ""),
        "gmail_live_state_expected_draft_count_including_cte": gmail_live_state.get(
            "expected_draft_count_including_cte", 0
        ),
        "gmail_live_state_observed_draft_count": gmail_live_state.get("observed_draft_count", 0),
        "gmail_live_state_sent_subject_search_result_count": gmail_live_state.get(
            "sent_subject_search_result_count", 0
        ),
        "gmail_live_state_provider_reply_search_result_count": gmail_live_state.get(
            "provider_reply_search_result_count", 0
        ),
        "gmail_live_state_teambeam_context_non_draft_result_count": gmail_live_state.get(
            "teambeam_context_non_draft_result_count", 0
        ),
        "external_dispatch_status": dispatch_summary.get("status", ""),
        "external_dispatch_ready_request_count": dispatch_summary.get("ready_request_count", 0),
        "external_dispatch_failed_check_count": dispatch_summary.get("failed_check_count", 0),
        "external_dispatch_unique_gmail_draft_count": dispatch_summary.get("unique_gmail_draft_count", 0),
        "external_dispatch_not_sent_request_count": dispatch_summary.get("not_sent_request_count", 0),
        "external_dispatch_missing_response_count": dispatch_summary.get("missing_response_count", 0),
        "local_gate_recovery_status": local_recovery.get("status", ""),
        "local_gate_recovery_document_count": local_recovery.get("document_count", 0),
        "local_gate_recovery_evidence_row_count": local_recovery.get("evidence_row_count", 0),
        "local_gate_recovery_possible_closure_evidence_count": count_possible_closure_rows(local_recovery),
        "local_gate_recovery_gates_still_external_count": len(
            local_recovery.get("gates_still_external_after_local_rescan", [])
        ),
        "download_gate_recovery_status": download_recovery.get("status", ""),
        "download_gate_recovery_document_count": download_recovery.get("document_count", 0),
        "download_gate_recovery_evidence_row_count": download_recovery.get("evidence_row_count", 0),
        "download_gate_recovery_possible_closure_evidence_count": count_possible_closure_rows(download_recovery),
        "download_gate_recovery_gates_still_external_count": len(
            download_recovery.get("gates_still_external_after_downloads_scan", [])
        ),
        "download_gate_recovery_verified_duplicate_catalogue_rows": download_recovery.get(
            "catalogued_duplicate_sha1_verified_count", 0
        ),
        "download_gate_recovery_uncatalogued_run_output_dirs": download_recovery.get(
            "uncatalogued_extracted_or_run_output_directory_count", 0
        ),
        "open_blocker_ids": [row["request_id"] for row in open_rows],
        "next_action": (
            "Review/send the six Gmail drafts, then file provider responses in the tracker intake locations "
            "and rerun the gate/readiness audits."
            if open_rows
            else "Refresh dependent gate/readiness audits after recorded responses are accepted."
        ),
        "source_artifacts": [
            "inversion_workflow/external_gate_response_intake.csv",
            "inversion_workflow/external_gate_gmail_drafts.csv",
            "inversion_workflow/external_gate_dispatch_audit_summary.json",
            "inversion_workflow/gmail_gate_live_state_audit_summary.json",
            "inversion_workflow/local_gate_recovery_audit_summary.json",
            "inversion_workflow/download_gate_recovery_audit_summary.json",
            "inversion_workflow/cte_confirmation_request.csv",
            "inversion_workflow/cte_confirmation_gmail_draft.csv",
            "inversion_workflow/cte_confirmation_request_summary.json",
        ],
    }
    return summary


def escape_md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_markdown(path: Path, rows: list[dict[str, str]], summary: dict[str, Any]) -> None:
    lines = [
        "# External Blocker Dashboard",
        "",
        "This dashboard consolidates the external measurement-gate requests and the separate CTE confirmation request.",
        "It does not send, archive, delete, or label email; it only joins the local trackers and point-in-time Gmail live-state audit.",
        "",
        "## Summary",
        "",
        f"- Status: `{summary['status']}`",
        f"- Blockers: {summary['blocker_count']} total, {summary['external_measurement_blocker_count']} external measurement gates, {summary['cte_confirmation_blocker_count']} CTE confirmation row",
        f"- Open blockers: {summary['open_blocker_count']}",
        f"- Unsent blockers: {summary['unsent_blocker_count']}",
        f"- Missing-response blockers: {summary['missing_response_blocker_count']}",
        f"- Gmail live-state check: `{summary['gmail_live_state_checked_at']}`",
        f"- Expected drafts observed: {summary['gmail_live_state_observed_draft_count']}/{summary['gmail_live_state_expected_draft_count_including_cte']}",
        f"- Sent-subject hits: {summary['gmail_live_state_sent_subject_search_result_count']}",
        f"- Provider-reply hits: {summary['gmail_live_state_provider_reply_search_result_count']}",
        f"- Recent CD-A/HERMES/TeamBeam non-draft hits: {summary['gmail_live_state_teambeam_context_non_draft_result_count']}",
        f"- Local gate recovery possible gate-closing rows: {summary['local_gate_recovery_possible_closure_evidence_count']}",
        f"- Downloads recovery possible gate-closing rows: {summary['download_gate_recovery_possible_closure_evidence_count']}",
        "",
        "## Blocker Table",
        "",
        "| Request | Type | Priority | Stream | Gate | Status | Draft | Observed | Response | Next action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{escape_md(row['request_id'])}`",
                    f"`{escape_md(row['blocker_type'])}`",
                    escape_md(row["priority"]),
                    f"`{escape_md(row['stream'])}`",
                    f"`{escape_md(row['gate_id'])}`",
                    f"`{escape_md(row['blocker_status'])}`",
                    f"`{escape_md(row['gmail_draft_id'])}`",
                    f"`{escape_md(row['observed_in_gmail_live_state'])}`",
                    f"`{escape_md(row['response_status'])}`",
                    escape_md(row["next_action"]),
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
                f"- Blocker type: `{row['blocker_type']}`",
                f"- Priority: `{row['priority']}`",
                f"- Stream/gate: `{row['stream']}` / `{row['gate_id']}`",
                f"- Subject: {row['subject']}",
                f"- Suggested To: `{row['suggested_to']}`",
                f"- Suggested Cc: `{row['suggested_cc'] or 'none'}`",
                f"- Contact route: `{row['contact_route_status']}`",
                f"- Gmail draft/message/thread: `{row['gmail_draft_id']}` / `{row['gmail_message_id']}` / `{row['gmail_thread_id']}`",
                f"- Gmail send status: `{row['gmail_send_status']}`",
                f"- Observed in Gmail live-state audit: `{row['observed_in_gmail_live_state']}`",
                f"- Request/response status: `{row['request_status']}` / `{row['response_status']}`",
                f"- Intake directory: `{row['intake_dir'] or 'not_applicable'}`",
                f"- Response notes: `{row['response_notes_md']}`",
                f"- Local recovery: `{row['local_recovery_status']}`, possible closure rows `{row['local_possible_closure_evidence_count']}`",
                f"- Downloads recovery: `{row['downloads_recovery_status']}`, possible closure rows `{row['downloads_possible_closure_evidence_count']}`",
                f"- Acceptance test: {row['acceptance_test']}",
                f"- Current blocker/caveat: {row['current_blocker_or_caveat']}",
                f"- Next action: `{row['next_action']}`",
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
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def copy_outputs(catalogue_dir: Path, paths: list[Path]) -> list[dict[str, str]]:
    catalogue_dir.mkdir(parents=True, exist_ok=True)
    copies: list[dict[str, str]] = []
    for path in paths:
        if not path.exists():
            continue
        target = catalogue_dir / path.name
        shutil.copy2(path, target)
        copies.append({"source": str(path), "catalogue_copy": str(target)})
    return copies


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[2]

    external_intake = read_csv(resolve(repo, args.external_intake))
    external_drafts = read_csv(resolve(repo, args.external_drafts))
    dispatch_summary = read_json(resolve(repo, args.dispatch_summary))
    gmail_live_state = read_json(resolve(repo, args.gmail_live_summary))
    local_recovery = read_json(resolve(repo, args.local_recovery_summary))
    download_recovery = read_json(resolve(repo, args.download_recovery_summary))
    cte_request = read_csv(resolve(repo, args.cte_request))
    cte_draft = read_csv(resolve(repo, args.cte_draft))
    cte_summary = read_json(resolve(repo, args.cte_summary))

    rows = build_external_rows(
        external_intake,
        external_drafts,
        gmail_live_state,
        local_recovery,
        download_recovery,
    )
    rows.extend(build_cte_row(cte_request, cte_draft, cte_summary, gmail_live_state))

    output_csv = resolve(repo, args.output_csv)
    output_summary = resolve(repo, args.output_summary)
    output_md = resolve(repo, args.output_md)
    catalogue_dir = resolve(repo, args.catalogue_dir).resolve()
    write_csv(output_csv, rows)
    summary = build_summary(rows, gmail_live_state, dispatch_summary, local_recovery, download_recovery)
    summary["generated_files"] = [
        str(output_csv.relative_to(repo)),
        str(output_summary.relative_to(repo)),
        str(output_md.relative_to(repo)),
    ]
    write_markdown(output_md, rows, summary)
    summary["catalogue_copies"] = copy_outputs(catalogue_dir, [output_csv, output_summary, output_md])
    output_summary.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary["catalogue_copies"] = copy_outputs(catalogue_dir, [output_csv, output_summary, output_md])
    output_summary.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    copy_outputs(catalogue_dir, [output_summary])
    print(json.dumps(json_ready(summary), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
