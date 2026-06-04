#!/usr/bin/env python3
"""Build recipient-specific drafts for external measurement-gate requests."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


RECIPIENT_NOTES = {
    "BGR ERT provider / Markus Furche via Gesa Ziefle": {
        "slug": "bgr_ert_markus_furche_via_gesa_ziefle",
        "subject": "CD-A ERT transform, support, and uncertainty needed for OGS comparison",
        "salutation": "Dear Gesa, Markus,",
        "suggested_to": ["Gesa.Ziefle@bgr.de"],
        "suggested_cc": ["Markus.Furche@bgr.de"],
        "contact_route_status": "coordinator_with_named_provider_cc",
        "contact_evidence": (
            "Gesa is the main CD-A sender; Markus.Furche@bgr.de is found in ERT and "
            "meeting-related messages and Gesa relayed Markus' ERT explanation in Gmail "
            "message 1994cb5d2bcefa24."
        ),
        "contact_caveat": (
            "No direct Gmail sender messages from Markus were found in the scan, so the "
            "request is routed through Gesa with Markus as suggested CC."
        ),
        "context": (
            "We can already run a provisional ERT diagnostic against sampled OGS water-content "
            "outputs, but it should not become an inversion residual until the coordinate support "
            "and uncertainty model are confirmed."
        ),
    },
    "Gesa Ziefle / BGR Geoscope, laser-scan, and levelling source": {
        "slug": "bgr_other_hm_exports_via_gesa_ziefle",
        "subject": "CD-A Geoscope, laser-scan, and levelling numeric exports needed for model validation",
        "salutation": "Dear Gesa,",
        "suggested_to": ["Gesa.Ziefle@bgr.de"],
        "suggested_cc": [],
        "contact_route_status": "coordinator_only_specific_provider_unresolved",
        "contact_evidence": (
            "Gesa is the main CD-A sender and sent the April 2026 technical-discussion "
            "minutes/presentations in Gmail message 19e1688564149e24; the current local scan "
            "does not identify a direct Geoscope, laser-scan, or levelling data owner address."
        ),
        "contact_caveat": (
            "Ask Gesa to forward to the appropriate BGR Geoscope, laser-scan, and levelling "
            "data owners if she is not the source."
        ),
        "context": (
            "The local catalogue contains HM layout geometry and qualitative evidence, but no "
            "hard-residual-ready numeric time series or statistical exports for these streams."
        ),
    },
    "Gesa Ziefle / BGR RH or OGS boundary-curve source": {
        "slug": "bgr_rh_boundary_curve_provenance_via_gesa_ziefle",
        "subject": "CD-A RH/suction boundary-curve provenance needed for OGS forcing",
        "salutation": "Dear Gesa,",
        "suggested_to": ["Gesa.Ziefle@bgr.de"],
        "suggested_cc": [],
        "contact_route_status": "coordinator_only_processing_owner_unresolved",
        "contact_evidence": (
            "Gesa sent the CD-A modelling slides, RH/suction material, and model-transfer "
            "threads that define the active boundary-curve context."
        ),
        "contact_caveat": (
            "The scan does not identify a separate RH/OGS pressure-curve processing owner, so "
            "Gesa remains the routing contact."
        ),
        "context": (
            "The local RH-derived pressure curves do not reproduce the active XML pressure boundary, "
            "so we need the source/provenance before using RH as anything stronger than a boundary audit."
        ),
    },
    "Taupe/TDR provider via Gesa Ziefle": {
        "slug": "taupe_tdr_calibration_via_gesa_ziefle",
        "subject": "CD-A Taupe/TDR workbook units and calibration needed before objective activation",
        "salutation": "Dear Gesa,",
        "suggested_to": ["Gesa.Ziefle@bgr.de"],
        "suggested_cc": [],
        "contact_route_status": "coordinator_only_provider_unresolved",
        "contact_evidence": (
            "Gesa's 2025-11-07 measurement overview says the TeamBeam transfer includes "
            "Taupe data and context, but the current scan does not identify a direct Taupe/TDR "
            "provider address."
        ),
        "contact_caveat": (
            "Ask Gesa to forward to the Taupe/TDR provider or confirm the unit/calibration "
            "source directly."
        ),
        "context": (
            "We can compare Taupe/TDR temporal trends diagnostically, but the workbook values need "
            "unit and calibration confirmation before any absolute water-content or saturation residual."
        ),
    },
    "Gesa Ziefle / BGR permeability source": {
        "slug": "bgr_historical_permeability_geometry_via_gesa_ziefle",
        "subject": "CD-A historical permeability endpoint geometry needed for inactive intervals",
        "salutation": "Dear Gesa,",
        "suggested_to": ["Gesa.Ziefle@bgr.de"],
        "suggested_cc": [],
        "contact_route_status": "coordinator_only_source_owner_unresolved",
        "contact_evidence": (
            "Gesa sent permeability spreadsheets, characterization material, and the later "
            "updated permeability transfer; the local scan does not identify a direct historical "
            "pulse-test geometry owner address."
        ),
        "contact_caveat": (
            "Ask Gesa to forward to the BGR permeability data owner if labelled interval endpoints "
            "come from another source."
        ),
        "context": (
            "The current direct permeability objective uses only rows with mapped interval support. "
            "The older retained rows need endpoint geometry before they can be projected to OGS cells."
        ),
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--closure-request",
        type=Path,
        default=Path("inversion_workflow/measurement_gate_closure_request.csv"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/external_gate_request_pack.csv"),
    )
    parser.add_argument(
        "--output-summary",
        type=Path,
        default=Path("inversion_workflow/external_gate_request_pack_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/external_gate_request_pack.md"),
    )
    parser.add_argument(
        "--draft-dir",
        type=Path,
        default=Path("inversion_workflow/external_gate_requests"),
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


def slugify(text: str) -> str:
    text = text.lower()
    text = text.replace("/", " ")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "external_request"


def recipient_info(audience: str) -> dict[str, str]:
    if audience in RECIPIENT_NOTES:
        return RECIPIENT_NOTES[audience]
    return {
        "slug": slugify(audience),
        "subject": "CD-A measurement gate closure request",
        "salutation": "Dear Gesa,",
        "suggested_to": ["Gesa.Ziefle@bgr.de"],
        "suggested_cc": [],
        "contact_route_status": "fallback_coordinator_only",
        "contact_evidence": "Gesa is the main CD-A coordination contact in the scanned mailbox.",
        "contact_caveat": "Specific provider contact was not resolved for this fallback audience.",
        "context": (
            "This request closes one of the source, provenance, support, calibration, or uncertainty "
            "gates needed before promoting diagnostic measurement streams to hard residuals."
        ),
    }


def read_external_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    rows = [row for row in rows if row.get("external_or_internal") == "external"]
    return sorted(
        rows,
        key=lambda row: (
            PRIORITY_RANK.get(row.get("priority", ""), 99),
            row.get("audience", ""),
            row.get("request_id", ""),
        ),
    )


def render_request_block(row: dict[str, str]) -> list[str]:
    return [
        f"### `{row['request_id']}`",
        "",
        f"- Priority: `{row['priority']}`",
        f"- Stream/gate: `{row['stream']}` / `{row['gate_id']}` (`{row['gate_status']}`)",
        f"- Request type: `{row['request_type']}`",
        f"- Requested answer or file: {row['exact_request']}",
        f"- Minimum acceptance criteria: {row['minimum_acceptance_criteria']}",
        f"- Current evidence: {row['current_evidence']}",
        f"- Current blocker: {row['current_blocker_or_caveat']}",
        f"- Why needed for the model: {row['why_needed_for_model']}",
        f"- Would unlock: {row['would_unlock']}",
        f"- Local artifacts to share if useful: {row['existing_local_artifacts'] or 'none listed'}",
        f"- Related local request package: {row['related_request_package'] or 'none'}",
        "",
    ]


def render_email_draft(audience: str, rows: list[dict[str, str]]) -> str:
    info = recipient_info(audience)
    lines = [
        f"# Draft: {info['subject']}",
        "",
        f"Subject: {info['subject']}",
        f"Suggested To: {', '.join(info['suggested_to'])}",
        f"Suggested Cc: {', '.join(info['suggested_cc']) if info['suggested_cc'] else 'none'}",
        f"Contact route: {info['contact_route_status']}",
        f"Contact evidence: {info['contact_evidence']}",
        f"Contact caveat: {info['contact_caveat']}",
        "",
        info["salutation"],
        "",
        info["context"],
        "",
        "Could you please help with the items below? These are the minimum pieces we need before "
        "we can describe the corresponding stream as a defensible hard residual in the CD-A OGS "
        "inversion workflow.",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"## `{row['request_id']}`",
                "",
                f"Request: {row['exact_request']}",
                "",
                f"Minimum acceptance criteria: {row['minimum_acceptance_criteria']}",
                "",
                f"Why this matters: {row['why_needed_for_model']}",
                "",
                f"Current local evidence/blocker: {row['current_evidence']} {row['current_blocker_or_caveat']}",
                "",
                f"Local artifacts we can share if useful: {row['existing_local_artifacts'] or 'none listed'}",
                "",
            ]
        )
    lines.extend(
        [
            "Best,",
            "",
        ]
    )
    return "\n".join(lines)


def write_overview(path: Path, rows: list[dict[str, str]], grouped: dict[str, list[dict[str, str]]], summary: dict[str, Any]) -> None:
    lines = [
        "# External Gate Request Pack",
        "",
        "This pack splits the external rows from the measurement gate-closure request package into recipient-specific drafts.",
        "It is a request/tracking artifact only; it does not record that any request has been sent or answered.",
        "",
        "## Summary",
        "",
        f"- Status: `{summary['status']}`",
        f"- External request rows: {summary['external_request_count']}",
        f"- Recipient drafts: {summary['recipient_count']}",
        f"- High-priority external requests: {summary['high_priority_external_request_count']}",
        f"- Medium-priority external requests: {summary['medium_priority_external_request_count']}",
        "",
        "## Recipient Drafts",
        "",
        "| Recipient/audience | Requests | Draft |",
        "| --- | --- | --- |",
    ]
    for audience, audience_rows in grouped.items():
        info = recipient_info(audience)
        draft = Path("inversion_workflow/external_gate_requests") / f"{info['slug']}.md"
        request_ids = ", ".join(f"`{row['request_id']}`" for row in audience_rows)
        lines.append(f"| {audience} | {request_ids} | `{draft}` |")
    lines.extend(
        [
            "",
            "## Contact Routing",
            "",
            "| Recipient/audience | Suggested To | Suggested Cc | Route status | Evidence/caveat |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for audience in grouped:
        info = recipient_info(audience)
        suggested_to = ", ".join(f"`{item}`" for item in info["suggested_to"])
        suggested_cc = ", ".join(f"`{item}`" for item in info["suggested_cc"]) or "none"
        evidence = f"{info['contact_evidence']} Caveat: {info['contact_caveat']}".replace("|", "\\|")
        lines.append(
            f"| {audience} | {suggested_to} | {suggested_cc} | "
            f"`{info['contact_route_status']}` | {evidence} |"
        )
    lines.extend(["", "## Request Details", ""])
    for row in rows:
        lines.extend(render_request_block(row))
    path.write_text("\n".join(lines), encoding="utf-8")


def copy_outputs(catalogue_dir: Path, paths: list[Path], draft_dir: Path) -> list[dict[str, str]]:
    catalogue_dir.mkdir(parents=True, exist_ok=True)
    copies = []
    for source in paths:
        target = catalogue_dir / source.name
        if source.exists():
            shutil.copy2(source, target)
        copies.append({"source": str(source), "catalogue_copy": str(target)})
    if draft_dir.exists():
        target_dir = catalogue_dir / draft_dir.name
        target_dir.mkdir(parents=True, exist_ok=True)
        for source in sorted(draft_dir.glob("*.md")):
            target = target_dir / source.name
            shutil.copy2(source, target)
            copies.append({"source": str(source), "catalogue_copy": str(target)})
    return copies


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[2]
    closure_path = (repo / args.closure_request if not args.closure_request.is_absolute() else args.closure_request).resolve()
    output_csv = (repo / args.output_csv if not args.output_csv.is_absolute() else args.output_csv).resolve()
    output_summary = (repo / args.output_summary if not args.output_summary.is_absolute() else args.output_summary).resolve()
    output_md = (repo / args.output_md if not args.output_md.is_absolute() else args.output_md).resolve()
    draft_dir = (repo / args.draft_dir if not args.draft_dir.is_absolute() else args.draft_dir).resolve()
    catalogue_dir = (repo / args.catalogue_dir if not args.catalogue_dir.is_absolute() else args.catalogue_dir).resolve()

    rows = read_external_rows(closure_path)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["audience"]].append(row)

    draft_dir.mkdir(parents=True, exist_ok=True)
    draft_paths: dict[str, Path] = {}
    for audience, audience_rows in grouped.items():
        info = recipient_info(audience)
        draft_path = draft_dir / f"{info['slug']}.md"
        draft_path.write_text(render_email_draft(audience, audience_rows), encoding="utf-8")
        draft_paths[audience] = draft_path

    output_rows = []
    for row in rows:
        draft_path = draft_paths[row["audience"]]
        output_row = dict(row)
        info = recipient_info(row["audience"])
        output_row.update(
            {
                "suggested_to": ", ".join(info["suggested_to"]),
                "suggested_cc": ", ".join(info["suggested_cc"]),
                "contact_route_status": info["contact_route_status"],
                "contact_evidence": info["contact_evidence"],
                "contact_caveat": info["contact_caveat"],
                "request_status": "drafted_pending_send",
                "response_status": "no_response_recorded",
                "recipient_draft": str(draft_path.relative_to(repo)),
                "next_action": "send_request_and_record_response_artifacts",
            }
        )
        output_rows.append(output_row)

    fieldnames = list(output_rows[0].keys()) if output_rows else []
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    priority_counts = Counter(row["priority"] for row in rows)
    route_counts = Counter(recipient_info(audience)["contact_route_status"] for audience in grouped)
    audiences_with_to = [
        audience for audience in grouped if recipient_info(audience).get("suggested_to")
    ]
    audiences_with_cc = [
        audience for audience in grouped if recipient_info(audience).get("suggested_cc")
    ]
    summary = {
        "status": "external_gate_request_pack_generated_not_sent",
        "generated_on": date.today().isoformat(),
        "external_request_count": len(rows),
        "recipient_count": len(grouped),
        "high_priority_external_request_count": int(priority_counts.get("high", 0)),
        "medium_priority_external_request_count": int(priority_counts.get("medium", 0)),
        "request_ids": [row["request_id"] for row in rows],
        "request_counts_by_audience": {audience: len(audience_rows) for audience, audience_rows in grouped.items()},
        "recipient_with_suggested_to_count": len(audiences_with_to),
        "recipient_with_suggested_cc_count": len(audiences_with_cc),
        "contact_route_counts": dict(sorted(route_counts.items())),
        "draft_files": [str(path.relative_to(repo)) for path in sorted(draft_paths.values())],
        "generated_files": [
            str(output_csv.relative_to(repo)),
            str(output_summary.relative_to(repo)),
            str(output_md.relative_to(repo)),
        ],
    }
    write_overview(output_md, rows, grouped, summary)
    summary["catalogue_copies"] = copy_outputs(catalogue_dir, [output_csv, output_summary, output_md], draft_dir)
    output_summary.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    copy_outputs(catalogue_dir, [output_summary], draft_dir)
    print(json.dumps(json_ready(summary), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
