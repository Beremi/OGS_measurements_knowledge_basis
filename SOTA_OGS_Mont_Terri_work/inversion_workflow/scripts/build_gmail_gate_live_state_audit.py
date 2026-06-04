#!/usr/bin/env python3
"""Summarize point-in-time Gmail connector checks for open gate requests.

The Gmail connector is queried interactively by the operator/agent.  This script
turns the recorded observations into reproducible local audit artifacts so the
readiness audit can distinguish "drafts exist but were not sent" from actual
provider responses.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--observations",
        type=Path,
        default=Path("inversion_workflow/gmail_gate_live_state_observations.csv"),
    )
    parser.add_argument(
        "--external-drafts",
        type=Path,
        default=Path("inversion_workflow/external_gate_gmail_drafts.csv"),
    )
    parser.add_argument(
        "--cte-summary",
        type=Path,
        default=Path("inversion_workflow/cte_confirmation_request_summary.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/gmail_gate_live_state_audit_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/gmail_gate_live_state_audit.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files"),
    )
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def split_ids(value: str) -> set[str]:
    return {item.strip() for item in (value or "").split(";") if item.strip()}


def determine_status(summary: dict[str, Any]) -> str:
    if not summary["all_expected_drafts_observed"]:
        return "gmail_gate_live_state_incomplete_expected_draft_observation"
    if summary["sent_subject_search_result_count"] != 0:
        return "gmail_gate_live_state_sent_candidates_require_review"
    if summary["provider_reply_search_result_count"] != 0:
        return "gmail_gate_live_state_provider_reply_candidates_require_review"
    if summary["teambeam_context_non_draft_result_count"] != 0:
        return "gmail_gate_live_state_teambeam_candidates_require_review"
    return "gmail_gate_live_state_checked_drafts_still_not_sent_no_responses_found"


def build_summary(
    observations: list[dict[str, str]],
    external_drafts: list[dict[str, str]],
    cte_summary: dict[str, Any],
) -> dict[str, Any]:
    observation_by_id = {row["check_id"]: row for row in observations}
    expected_external_draft_ids = {row["gmail_draft_id"] for row in external_drafts if row.get("gmail_draft_id")}
    cte_draft_id = cte_summary.get("gmail_draft_id") or ""
    expected_all_draft_ids = set(expected_external_draft_ids)
    if cte_draft_id:
        expected_all_draft_ids.add(cte_draft_id)
    observed_draft_ids: set[str] = set()
    for row in observations:
        observed_draft_ids.update(split_ids(row.get("matched_draft_ids", "")))
    missing_expected_draft_ids = sorted(expected_all_draft_ids - observed_draft_ids)

    sent_row = observation_by_id.get("sent_subject_search", {})
    provider_row = observation_by_id.get("provider_reply_search", {})
    teambeam_row = observation_by_id.get("teambeam_context_search", {})
    teambeam_ids = split_ids(teambeam_row.get("matched_draft_ids", ""))
    teambeam_result_count = int(teambeam_row.get("result_count") or 0)
    teambeam_non_draft_count = max(teambeam_result_count - len(teambeam_ids), 0)

    send_status_counts = Counter(row.get("send_status", "") for row in external_drafts)
    summary: dict[str, Any] = {
        "checked_at": max((row.get("checked_at", "") for row in observations), default=""),
        "observation_count": len(observations),
        "external_request_row_count": len(external_drafts),
        "unique_external_draft_count": len(expected_external_draft_ids),
        "cte_draft_present_in_tracker": bool(cte_draft_id),
        "expected_draft_count_including_cte": len(expected_all_draft_ids),
        "observed_draft_count": len(expected_all_draft_ids & observed_draft_ids),
        "all_expected_drafts_observed": not missing_expected_draft_ids,
        "missing_expected_draft_ids": missing_expected_draft_ids,
        "external_gmail_send_status_counts": dict(send_status_counts),
        "sent_subject_search_result_count": int(sent_row.get("result_count") or 0),
        "provider_reply_search_result_count": int(provider_row.get("result_count") or 0),
        "teambeam_context_search_result_count": teambeam_result_count,
        "teambeam_context_non_draft_result_count": teambeam_non_draft_count,
        "draft_ids_observed": sorted(expected_all_draft_ids & observed_draft_ids),
        "observations": observations,
        "notes": [
            "This is a point-in-time Gmail connector check, not a mailbox automation.",
            "No Gmail send/archive/delete/label operation is performed by this audit.",
            "A zero result in the provider reply search is evidence for current triage, not proof that no reply can arrive later.",
        ],
    }
    summary["status"] = determine_status(summary)
    return summary


def write_markdown(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Gmail Gate Live-State Audit",
        "",
        "This audit records a point-in-time Gmail connector check for the external gate drafts and CTE confirmation draft.",
        "It does not send, archive, delete, or label any email.",
        "",
        "## Summary",
        "",
        f"- Status: `{summary['status']}`",
        f"- Checked at: `{summary['checked_at']}`",
        f"- External request rows: {summary['external_request_row_count']}",
        f"- Unique external drafts: {summary['unique_external_draft_count']}",
        f"- Expected drafts including CTE: {summary['expected_draft_count_including_cte']}",
        f"- Expected drafts observed in Gmail DRAFT results: {summary['observed_draft_count']}",
        f"- Sent-subject search results: {summary['sent_subject_search_result_count']}",
        f"- Provider-reply search results: {summary['provider_reply_search_result_count']}",
        f"- Recent CD-A/HERMES/TeamBeam non-draft results: {summary['teambeam_context_non_draft_result_count']}",
        "",
        "## Interpretation",
        "",
    ]
    if summary["status"] == "gmail_gate_live_state_checked_drafts_still_not_sent_no_responses_found":
        lines.append(
            "The five external gate drafts and separate CTE confirmation draft are still observed as Gmail drafts. "
            "No sent copies of the generated subjects and no recent provider replies were found by the recorded searches, so the local response-intake status remains missing-response."
        )
    else:
        lines.append(
            "At least one Gmail observation requires manual review before the response-intake status can be trusted."
        )
    lines.extend(
        [
            "",
            "## Observed Draft IDs",
            "",
        ]
    )
    for draft_id in summary["draft_ids_observed"]:
        lines.append(f"- `{draft_id}`")
    if summary["missing_expected_draft_ids"]:
        lines.extend(["", "## Missing Expected Draft IDs", ""])
        for draft_id in summary["missing_expected_draft_ids"]:
            lines.append(f"- `{draft_id}`")
    lines.extend(
        [
            "",
            "## Connector Observations",
            "",
            "| Check | Tool | Results | Interpretation |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for row in summary["observations"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['check_id']}`",
                    f"`{row['connector_tool']}`",
                    row["result_count"],
                    row["interpretation"].replace("|", "\\|"),
                ]
            )
            + " |"
        )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def copy_outputs(paths: list[Path], catalogue_dir: Path) -> list[dict[str, str]]:
    catalogue_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for path in paths:
        if path.exists():
            target = catalogue_dir / path.name
            shutil.copy2(path, target)
            copied.append({"source": str(path), "catalogue_copy": str(target)})
    return copied


def main() -> None:
    args = parse_args()
    observations = read_csv(args.observations)
    external_drafts = read_csv(args.external_drafts)
    cte_summary = read_json(args.cte_summary)
    summary = build_summary(observations, external_drafts, cte_summary)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(args.output_md, summary)
    args.output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary["catalogue_copies"] = copy_outputs(
        [args.observations, args.output_json, args.output_md],
        args.catalogue_dir,
    )
    args.output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if args.catalogue_dir:
        shutil.copy2(args.output_json, args.catalogue_dir / args.output_json.name)


if __name__ == "__main__":
    main()
