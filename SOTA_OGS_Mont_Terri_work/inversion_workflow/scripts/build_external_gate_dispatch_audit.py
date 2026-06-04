#!/usr/bin/env python3
"""Audit whether external measurement-gate request drafts are ready to send."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--request-pack",
        type=Path,
        default=Path("inversion_workflow/external_gate_request_pack.csv"),
    )
    parser.add_argument(
        "--response-intake",
        type=Path,
        default=Path("inversion_workflow/external_gate_response_intake.csv"),
    )
    parser.add_argument(
        "--gmail-drafts",
        type=Path,
        default=Path("inversion_workflow/external_gate_gmail_drafts.csv"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/external_gate_dispatch_audit.csv"),
    )
    parser.add_argument(
        "--output-summary",
        type=Path,
        default=Path("inversion_workflow/external_gate_dispatch_audit_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/external_gate_dispatch_audit.md"),
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def resolve_repo_path(repo: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo / path


def nonempty(value: str | None) -> bool:
    return bool((value or "").strip())


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def draft_checks(request_id: str, draft_path: Path) -> dict[str, bool]:
    text = draft_path.read_text(encoding="utf-8", errors="ignore") if draft_path.exists() else ""
    return {
        "draft_exists": draft_path.is_file(),
        "draft_has_subject": "Subject:" in text,
        "draft_has_suggested_to": "Suggested To:" in text,
        "draft_has_contact_route": "Contact route:" in text,
        "draft_has_salutation": "Dear " in text,
        "draft_mentions_request_id": request_id in text,
        "draft_has_request_heading": f"## `{request_id}`" in text,
        "draft_has_minimum_acceptance_criteria": "Minimum acceptance criteria:" in text,
        "draft_has_model_relevance": "Why this matters:" in text,
        "draft_has_current_evidence": "Current local evidence/blocker:" in text,
        "draft_has_signoff": "Best," in text,
    }


def build_audit_rows(
    repo: Path,
    request_rows: list[dict[str, str]],
    intake_rows: list[dict[str, str]],
    gmail_draft_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    intake_by_id = {row["request_id"]: row for row in intake_rows}
    gmail_by_id = {row["request_id"]: row for row in gmail_draft_rows}
    audit_rows: list[dict[str, str]] = []
    for request in request_rows:
        request_id = request["request_id"]
        intake = intake_by_id.get(request_id, {})
        gmail = gmail_by_id.get(request_id, {})
        draft_path = resolve_repo_path(repo, request.get("recipient_draft", ""))
        checks = draft_checks(request_id, draft_path)

        intake_dir = Path(intake.get("intake_dir", ""))
        response_notes = Path(intake.get("response_notes_md", ""))
        intake_checks = {
            "intake_row_exists": bool(intake),
            "intake_dir_exists": intake_dir.is_dir(),
            "response_notes_exists": response_notes.is_file(),
            "acceptance_test_present": nonempty(intake.get("acceptance_test")),
            "refresh_commands_present": nonempty(intake.get("refresh_commands")),
            "response_files_recorded_empty": not nonempty(intake.get("response_files_recorded")),
        }
        status_checks = {
            "suggested_to_present": nonempty(request.get("suggested_to")),
            "request_status_is_pending_send": request.get("request_status") == "drafted_pending_send",
            "pack_response_status_is_no_response": request.get("response_status") == "no_response_recorded",
            "intake_response_status_is_missing": intake.get("response_status") == "missing_response",
        }
        gmail_checks = (
            {
                "gmail_draft_tracker_row_exists": bool(gmail),
                "gmail_draft_id_present": nonempty(gmail.get("gmail_draft_id")),
                "gmail_message_id_present": nonempty(gmail.get("gmail_message_id")),
                "gmail_thread_id_present": nonempty(gmail.get("gmail_thread_id")),
                "gmail_draft_not_sent": gmail.get("send_status") == "gmail_draft_created_not_sent",
            }
            if gmail_draft_rows
            else {}
        )
        all_checks = {**checks, **intake_checks, **status_checks, **gmail_checks}
        failures = [name for name, passed in all_checks.items() if not passed]
        ready = not failures
        gmail_draft_created = bool(gmail) and gmail.get("send_status") == "gmail_draft_created_not_sent"
        audit_rows.append(
            {
                "request_id": request_id,
                "priority": request.get("priority", ""),
                "stream": request.get("stream", ""),
                "gate_id": request.get("gate_id", ""),
                "audience": request.get("audience", ""),
                "suggested_to": request.get("suggested_to", ""),
                "suggested_cc": request.get("suggested_cc", ""),
                "contact_route_status": request.get("contact_route_status", ""),
                "contact_caveat": request.get("contact_caveat", ""),
                "draft_path": str(draft_path.relative_to(repo) if draft_path.is_relative_to(repo) else draft_path),
                "intake_dir": str(intake_dir),
                "response_notes_md": str(response_notes),
                "request_pack_status": request.get("request_status", ""),
                "request_pack_response_status": request.get("response_status", ""),
                "intake_response_status": intake.get("response_status", ""),
                "gmail_draft_id": gmail.get("gmail_draft_id", ""),
                "gmail_message_id": gmail.get("gmail_message_id", ""),
                "gmail_thread_id": gmail.get("gmail_thread_id", ""),
                "gmail_send_status": gmail.get("send_status", ""),
                **{name: bool_text(passed) for name, passed in all_checks.items()},
                "blocking_check_count": str(len(failures)),
                "check_failures": "; ".join(failures),
                "ready_for_dispatch": bool_text(ready),
                "dispatch_status": (
                    "gmail_draft_created_not_sent_waiting_response"
                    if ready and gmail_draft_created
                    else "ready_to_send_waiting_response"
                    if ready
                    else "not_ready_check_failed"
                ),
                "next_action": (
                    "review_or_send_gmail_draft_then_file_response_in_intake_tracker"
                    if ready and gmail_draft_created
                    else "send_request_then_file_response_in_intake_tracker"
                    if ready
                    else "fix_failed_dispatch_audit_checks_before_send"
                ),
            }
        )
    return audit_rows


def determine_status(rows: list[dict[str, str]], summary_checks: dict[str, bool]) -> str:
    failed_rows = [row for row in rows if row["ready_for_dispatch"] != "true"]
    if failed_rows or not all(summary_checks.values()):
        return "external_gate_dispatch_not_ready"
    gmail_rows = [row for row in rows if row.get("gmail_send_status")]
    if gmail_rows and all(row["gmail_send_status"] == "gmail_draft_created_not_sent" for row in rows):
        return "external_gate_dispatch_gmail_drafts_created_waiting_user_send_and_responses"
    if all(row["request_pack_status"] == "drafted_pending_send" for row in rows):
        return "external_gate_dispatch_ready_not_sent_waiting_for_responses"
    return "external_gate_dispatch_ready_mixed_request_status"


def write_markdown(path: Path, rows: list[dict[str, str]], summary: dict[str, Any]) -> None:
    lines = [
        "# External Gate Dispatch Audit",
        "",
        "This audit checks that the external measurement-gate request drafts, request-pack rows, and response-intake templates match before any request is sent.",
        "It is not evidence that the emails were sent or that any external gate was answered.",
        "",
        "## Summary",
        "",
        f"- Status: `{summary['status']}`",
        f"- Requests audited: {summary['request_count']}",
        f"- Recipient drafts: {summary['draft_count']}",
        f"- Ready requests: {summary['ready_request_count']}",
        f"- Failed per-request checks: {summary['failed_check_count']}",
        f"- Request rows with suggested To: {summary['suggested_to_present_count']}",
        f"- Request rows with suggested Cc: {summary['suggested_cc_present_count']}",
        f"- Not-yet-sent requests: {summary['not_sent_request_count']}",
        f"- Gmail draft rows: {summary['gmail_draft_request_count']}",
        f"- Unique Gmail drafts: {summary['unique_gmail_draft_count']}",
        f"- Missing responses: {summary['missing_response_count']}",
        "",
        "## Cross-Checks",
        "",
    ]
    for name, value in summary["summary_checks"].items():
        lines.append(f"- `{name}`: `{bool_text(value)}`")
    lines.extend(
        [
            "",
            "## Dispatch Table",
            "",
        "| Request | Draft | Gmail draft | Intake notes | Ready | Failures |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        failures = row["check_failures"] or "none"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['request_id']}`",
                    f"`{row['draft_path']}`",
                    f"`{row['gmail_draft_id'] or 'none'}`",
                    f"`{row['response_notes_md']}`",
                    f"`{row['ready_for_dispatch']}`",
                    failures.replace("|", "\\|"),
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
                f"- Suggested To: `{row['suggested_to']}`",
                f"- Suggested Cc: `{row['suggested_cc'] or 'none'}`",
                f"- Contact route: `{row['contact_route_status']}`",
                f"- Contact caveat: {row['contact_caveat'] or 'none'}",
                f"- Gate: `{row['gate_id']}`",
                f"- Draft: `{row['draft_path']}`",
                f"- Intake directory: `{row['intake_dir']}`",
                f"- Response notes: `{row['response_notes_md']}`",
                f"- Gmail draft id: `{row['gmail_draft_id'] or 'none'}`",
                f"- Gmail message/thread: `{row['gmail_message_id'] or 'none'}` / `{row['gmail_thread_id'] or 'none'}`",
                f"- Gmail send status: `{row['gmail_send_status'] or 'none'}`",
                f"- Dispatch status: `{row['dispatch_status']}`",
                f"- Request status: `{row['request_pack_status']}`",
                f"- Pack response status: `{row['request_pack_response_status']}`",
                f"- Intake response status: `{row['intake_response_status']}`",
                f"- Failed checks: {row['check_failures'] or 'none'}",
                f"- Next action: `{row['next_action']}`",
                "",
            ]
        )
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


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[2]
    request_pack = (repo / args.request_pack if not args.request_pack.is_absolute() else args.request_pack).resolve()
    response_intake = (
        repo / args.response_intake if not args.response_intake.is_absolute() else args.response_intake
    ).resolve()
    gmail_drafts = (repo / args.gmail_drafts if not args.gmail_drafts.is_absolute() else args.gmail_drafts).resolve()
    output_csv = (repo / args.output_csv if not args.output_csv.is_absolute() else args.output_csv).resolve()
    output_summary = (
        repo / args.output_summary if not args.output_summary.is_absolute() else args.output_summary
    ).resolve()
    output_md = (repo / args.output_md if not args.output_md.is_absolute() else args.output_md).resolve()
    catalogue_dir = (repo / args.catalogue_dir if not args.catalogue_dir.is_absolute() else args.catalogue_dir).resolve()

    request_rows = read_csv(request_pack)
    intake_rows = read_csv(response_intake)
    gmail_draft_rows = read_csv(gmail_drafts) if gmail_drafts.exists() else []
    rows = build_audit_rows(repo, request_rows, intake_rows, gmail_draft_rows)

    request_ids = [row["request_id"] for row in request_rows]
    intake_ids = [row["request_id"] for row in intake_rows]
    draft_paths = sorted({row["draft_path"] for row in rows})
    ready_rows = [row for row in rows if row["ready_for_dispatch"] == "true"]
    failed_check_count = sum(int(row["blocking_check_count"]) for row in rows)
    request_status_counts = Counter(row.get("request_status", "") for row in request_rows)
    response_status_counts = Counter(row.get("response_status", "") for row in request_rows)
    intake_response_counts = Counter(row.get("response_status", "") for row in intake_rows)
    contact_route_counts = Counter(row.get("contact_route_status", "") for row in request_rows)
    gmail_send_status_counts = Counter(row.get("send_status", "") for row in gmail_draft_rows)
    summary_checks = {
        "request_ids_match_intake": set(request_ids) == set(intake_ids),
        "request_id_counts_match_intake": len(request_ids) == len(intake_ids),
        "request_ids_unique": len(request_ids) == len(set(request_ids)),
        "intake_request_ids_unique": len(intake_ids) == len(set(intake_ids)),
        "all_recipient_drafts_exist": all(row["draft_exists"] == "true" for row in rows),
        "all_suggested_to_present": all(row["suggested_to_present"] == "true" for row in rows),
        "all_response_notes_exist": all(row["response_notes_exists"] == "true" for row in rows),
        "all_acceptance_tests_present": all(row["acceptance_test_present"] == "true" for row in rows),
        "all_refresh_commands_present": all(row["refresh_commands_present"] == "true" for row in rows),
        "all_request_rows_have_gmail_draft": (
            not gmail_draft_rows or all(row.get("gmail_draft_tracker_row_exists") == "true" for row in rows)
        ),
    }
    summary: dict[str, Any] = {
        "status": determine_status(rows, summary_checks),
        "generated_on": date.today().isoformat(),
        "request_count": len(rows),
        "ready_request_count": len(ready_rows),
        "not_ready_request_count": len(rows) - len(ready_rows),
        "failed_check_count": failed_check_count,
        "draft_count": len(draft_paths),
        "draft_paths": draft_paths,
        "suggested_to_present_count": sum(1 for row in rows if nonempty(row["suggested_to"])),
        "suggested_cc_present_count": sum(1 for row in rows if nonempty(row["suggested_cc"])),
        "contact_route_status_counts": dict(sorted(contact_route_counts.items())),
        "intake_directory_count": len({row["intake_dir"] for row in rows}),
        "response_note_template_count": len({row["response_notes_md"] for row in rows}),
        "not_sent_request_count": int(request_status_counts.get("drafted_pending_send", 0)),
        "gmail_draft_tracker": str(gmail_drafts.relative_to(repo)) if gmail_drafts.exists() else "",
        "gmail_draft_request_count": len(gmail_draft_rows),
        "unique_gmail_draft_count": len(
            {row.get("gmail_draft_id", "") for row in gmail_draft_rows if row.get("gmail_draft_id")}
        ),
        "gmail_send_status_counts": dict(sorted(gmail_send_status_counts.items())),
        "no_response_recorded_count": int(response_status_counts.get("no_response_recorded", 0)),
        "missing_response_count": int(intake_response_counts.get("missing_response", 0)),
        "request_status_counts": dict(sorted(request_status_counts.items())),
        "request_pack_response_status_counts": dict(sorted(response_status_counts.items())),
        "intake_response_status_counts": dict(sorted(intake_response_counts.items())),
        "request_ids": request_ids,
        "summary_checks": summary_checks,
        "generated_files": [
            str(gmail_drafts.relative_to(repo)) if gmail_drafts.exists() else "",
            str(output_csv.relative_to(repo)),
            str(output_summary.relative_to(repo)),
            str(output_md.relative_to(repo)),
        ],
    }
    write_csv(output_csv, rows)
    write_markdown(output_md, rows, summary)
    output_summary.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    catalogue_sources = [path for path in [gmail_drafts, output_csv, output_summary, output_md] if path.exists()]
    summary["catalogue_copies"] = copy_outputs(catalogue_dir, catalogue_sources)
    output_summary.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    copy_outputs(catalogue_dir, [output_summary])
    print(json.dumps(json_ready(summary), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
