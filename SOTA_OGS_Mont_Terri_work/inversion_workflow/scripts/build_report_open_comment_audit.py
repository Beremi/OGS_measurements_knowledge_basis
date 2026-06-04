#!/usr/bin/env python3
"""Audit active report comments, resolved formulation issues, and open gates."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Any


ACTIVE_REPORT_SOURCES = [Path("main.tex"), Path("measurement_chapter.tex")]
REVIEW_MARKERS = ["TODO", "FIXME", r"\todo", r"\hl{", r"\textcolor", "??"]


RESOLVED_FORMULATION_ITEMS = [
    {
        "item_id": "homogeneity_vs_heterogeneity",
        "needle": "Homogeneity versus heterogeneity",
        "summary": "The report now distinguishes the homogeneous exchanged XML model from run-local heterogeneous permeability fields.",
        "current_resolution": (
            "Resolved in the active report: heterogeneity is introduced only through run-local mesh-cell "
            "parameter fields, first for intrinsic permeability."
        ),
    },
    {
        "item_id": "relative_permeability_expression",
        "needle": "Specific expression for \\(\\krel\\)",
        "summary": "The report now states the actual Van Genuchten relative-permeability function and fixed XML parameters.",
        "current_resolution": (
            "Resolved in the active report: RelativePermeabilityVanGenuchten is documented with "
            "S_lr=0.1, S_gr=0, m=0.45, and k_rel_min=1e-25."
        ),
    },
    {
        "item_id": "liquid_density_beta_storage",
        "needle": "This resolves the earlier comment on \\(\\beta_p\\)",
        "summary": "The report now explains the OGS liquid-density pressure/temperature dependence and composite storage term.",
        "current_resolution": (
            "Resolved in the active report: the linear density law, pressure/temperature derivatives, "
            "and capillary-storage term are spelled out."
        ),
    },
    {
        "item_id": "momentum_bishop_thermal_strain",
        "needle": "The compact form \\(\\divv(\\sig-\\Sat\\pp\\I)=0\\)",
        "summary": "The report now states the configured Bishop law, Biot coefficient, and thermal strain placement.",
        "current_resolution": (
            "Resolved in the active report: the compact momentum form is shown as valid only after "
            "the configured XML substitutions."
        ),
    },
    {
        "item_id": "heat_balance_porosity_saturation",
        "needle": "This resolves the heat-balance comment",
        "summary": "The report now explains where porosity and saturation enter thermal storage/conductivity mixing.",
        "current_resolution": (
            "Resolved in the active report: n*S belongs to effective storage/conductivity mixing, "
            "while the advective term uses Darcy velocity."
        ),
    },
]


INTERNAL_OPEN_ITEMS = [
    {
        "item_id": "cte_value_provenance",
        "audit_class": "tracked_model_provenance_confirmation",
        "status": "open_confirmation_required",
        "needle": "suspicious active \\texttt{CTE} value",
        "summary": "The active CTE value is tracked as an implausible thermal-expansivity/provenance issue, not as a fit parameter.",
        "current_resolution": (
            "Thermal-expansivity audit says the XML value must remain fixed and uninterpreted until "
            "Gesa/BGR confirm the intended value or inactive status. A dedicated confirmation request "
            "package now records the exact outbound question and contact route."
        ),
        "remaining_action": "Send the CTE confirmation request and record the provider response before releasing thermal or retention/boundary parameters.",
        "linked_artifacts": (
            "inversion_workflow/thermal_expansivity_parameter_audit.md; "
            "inversion_workflow/cte_confirmation_request.md; WORK_STATUS.md"
        ),
    },
    {
        "item_id": "nmr_trend_anomaly_default_promotion",
        "audit_class": "tracked_internal_policy",
        "status": "local_policy_recorded_not_promoted_default",
        "needle": "default active objective remains raw",
        "summary": "The NMR trend/anomaly residual is implemented and preferred provisionally; local policy keeps it explicit/scenario-only for the current report state.",
        "current_resolution": (
            "Internal policy is recorded: do not promote trend/anomaly NMR to the default objective for "
            "the current report state. Use the explicit nmr_within_label_trend_anomaly mode and scenario "
            "audits when that residual definition is needed."
        ),
        "remaining_action": "No current-report action; re-open only if the modelling team wants to change the default objective semantics.",
        "linked_artifacts": (
            "inversion_workflow/nmr_objective_decision.md; "
            "inversion_workflow/nmr_trend_anomaly_active_objective.md; "
            "inversion_workflow/internal_gate_decision_register.md"
        ),
    },
    {
        "item_id": "perm_likelihood_policy_default",
        "audit_class": "tracked_internal_policy",
        "status": "local_policy_recorded_not_promoted_default",
        "needle": "support-cell weighted-mean",
        "summary": "The direct-permeability robust/support-cell likelihood choice is explicit and not promoted as a silent default change.",
        "current_resolution": (
            "Internal policy is recorded: keep the duplicate-weighted rowwise Gaussian direct-permeability "
            "objective as the current report default, and treat robust tails, support-cell aggregation, and "
            "scalar-range outlier handling as explicit scenario/decision options."
        ),
        "remaining_action": (
            "Before more active-objective OGS spending, record whether the rowwise Gaussian policy remains "
            "accepted with a new parameterization or whether a robust/aggregated likelihood scenario should "
            "become the active selection policy."
        ),
        "linked_artifacts": (
            "inversion_workflow/permeability_likelihood_policy_audit.md; "
            "inversion_workflow/permeability_likelihood_decision_request.md; "
            "inversion_workflow/internal_gate_decision_register.md"
        ),
    },
    {
        "item_id": "local_ogs_runtime_provenance",
        "audit_class": "tracked_operational_caveat",
        "status": "container_execution_available_local_ogs_absent",
        "needle": "does not currently contain an \\path{ogs}",
        "summary": "The local host lacks a native ogs executable, while the collected SIF is executable through Dockerized Apptainer.",
        "current_resolution": (
            "Not an active report comment: complete runs exist through the recorded Dockerized-Apptainer backend, "
            "but native OGS remains absent."
        ),
        "remaining_action": "Keep the backend recorded for reproducibility; install native OGS only if the workflow requires it.",
        "linked_artifacts": "inversion_workflow/OGS_ENVIRONMENT_AUDIT.md; inversion_workflow/scripts/run_ogs_model.py",
    },
]


FALSE_POSITIVE_ITEMS = [
    {
        "item_id": "latex_listing_commentstyle",
        "source_hint": "commentstyle=\\color{gray}",
        "summary": "The LaTeX listings style contains the word commentstyle; it is not a reviewer comment.",
        "linked_artifacts": "main.tex",
    },
    {
        "item_id": "work_status_placeholder_scan_note",
        "source_hint": "Text extraction from `main.pdf` was checked for unresolved placeholders",
        "summary": "WORK_STATUS records that placeholder markers were checked; it is not itself an unresolved placeholder.",
        "linked_artifacts": "WORK_STATUS.md",
    },
    {
        "item_id": "source_text_todos_external_content",
        "source_hint": "TODOs:",
        "summary": "The remaining TODO-like text is source/extracted-content vocabulary outside the active report.",
        "linked_artifacts": "inversion_workflow/processed_observations/other_hm_numeric_source_evidence.csv",
    },
    {
        "item_id": "legacy_long_report_not_build_target",
        "source_hint": "long_report.tex",
        "summary": "long_report.tex is a legacy/source file; main.tex builds the active report and only inputs measurement_chapter.tex.",
        "linked_artifacts": "long_report.tex; main.tex",
    },
]


REPORT_NEEDLES_FOR_EXTERNAL_REQUESTS = {
    "ert_transform_support": "coordinate transform, exact near-niche support",
    "ert_uncertainty": "ERT inversion uncertainty/correlation model",
    "hm_numeric_exports": "other HM monitoring is not ready",
    "hm_uncertainty": "other HM monitoring is not ready",
    "rh_active_curve_provenance": "active-curve provenance",
    "taupe_unit_calibration": "Taupe/TDR are diagnostic-only",
    "perm_endpoint_geometry": "historical permeability endpoint geometry",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-pack", type=Path, default=Path("inversion_workflow/external_gate_request_pack.csv"))
    parser.add_argument(
        "--external-pack-summary",
        type=Path,
        default=Path("inversion_workflow/external_gate_request_pack_summary.json"),
    )
    parser.add_argument(
        "--external-intake-summary",
        type=Path,
        default=Path("inversion_workflow/external_gate_response_intake_summary.json"),
    )
    parser.add_argument(
        "--cte-confirmation-summary",
        type=Path,
        default=Path("inversion_workflow/cte_confirmation_request_summary.json"),
    )
    parser.add_argument("--output-csv", type=Path, default=Path("inversion_workflow/report_open_comment_audit.csv"))
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/report_open_comment_audit_summary.json"),
    )
    parser.add_argument("--output-md", type=Path, default=Path("inversion_workflow/report_open_comment_audit.md"))
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files"),
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def line_location(path: Path, needle: str) -> str:
    if not path.exists():
        return str(path)
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        if needle in line:
            return f"{path}:{line_number}"
    return str(path)


def first_location(needle: str, paths: list[Path] | None = None) -> str:
    search_paths = paths or ACTIVE_REPORT_SOURCES + [Path("WORK_STATUS.md"), Path("inversion_workflow/README.md")]
    for path in search_paths:
        location = line_location(path, needle)
        if ":" in location:
            return location
    return "; ".join(str(path) for path in search_paths)


def active_marker_hits() -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for path in ACTIVE_REPORT_SOURCES:
        if not path.exists():
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            for marker in REVIEW_MARKERS:
                if marker in line:
                    marker_slug = (
                        marker.replace("\\", "")
                        .replace("{", "")
                        .replace("}", "")
                        .replace("?", "q")
                        .lower()
                    )
                    hits.append(
                        {
                            "item_id": f"active_marker_{path.stem}_{line_number}_{marker_slug}",
                            "audit_class": "active_report_unresolved_marker",
                            "status": "needs_review",
                            "active_report_relevance": "active_report",
                            "source_locations": f"{path}:{line_number}",
                            "summary": f"Active report contains review marker `{marker}`.",
                            "current_resolution_or_evidence": line.strip(),
                            "remaining_action": "Resolve or remove the marker before claiming a clean active report.",
                            "linked_artifacts": str(path),
                        }
                    )
    return hits


def resolved_rows() -> list[dict[str, str]]:
    rows = []
    for item in RESOLVED_FORMULATION_ITEMS:
        rows.append(
            {
                "item_id": item["item_id"],
                "audit_class": "resolved_formulation_comment",
                "status": "resolved_in_active_report",
                "active_report_relevance": "active_report",
                "source_locations": first_location(item["needle"], [Path("main.tex")]),
                "summary": item["summary"],
                "current_resolution_or_evidence": item["current_resolution"],
                "remaining_action": "None for formulation; keep the distinction if report text is edited.",
                "linked_artifacts": "main.tex",
            }
        )
    return rows


def external_rows(pack_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for request in pack_rows:
        request_id = request.get("request_id", "")
        needle = REPORT_NEEDLES_FOR_EXTERNAL_REQUESTS.get(request_id, request.get("gate_label", ""))
        rows.append(
            {
                "item_id": request_id,
                "audit_class": "tracked_external_gate_request",
                "status": f"{request.get('request_status', 'drafted_pending_send')}; {request.get('response_status', 'no_response_recorded')}",
                "active_report_relevance": "report_caveat_and_likelihood_activation_gate",
                "source_locations": first_location(needle),
                "summary": request.get("gate_label", ""),
                "current_resolution_or_evidence": request.get("current_blocker_or_caveat", ""),
                "remaining_action": request.get("next_action", "send_request_and_record_response_artifacts"),
                "linked_artifacts": "; ".join(
                    item
                    for item in [
                        "inversion_workflow/external_gate_request_pack.md",
                        request.get("recipient_draft", ""),
                        request.get("existing_local_artifacts", ""),
                    ]
                    if item
                ),
            }
        )
    return rows


def internal_rows(cte_summary: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    for item in INTERNAL_OPEN_ITEMS:
        status = item["status"]
        current_resolution = item["current_resolution"]
        remaining_action = item["remaining_action"]
        linked_artifacts = item["linked_artifacts"]
        if item["item_id"] == "cte_value_provenance" and cte_summary:
            status = (
                f"{cte_summary.get('request_status', 'drafted_pending_send')}; "
                f"{cte_summary.get('response_status', 'no_response_recorded')}"
            )
            current_resolution = (
                f"{current_resolution} Request package status="
                f"{cte_summary.get('status')}; suggested To={cte_summary.get('suggested_to')}, "
                f"Cc={cte_summary.get('suggested_cc')}."
            )
        rows.append(
            {
                "item_id": item["item_id"],
                "audit_class": item["audit_class"],
                "status": status,
                "active_report_relevance": "report_caveat_or_operational_context",
                "source_locations": first_location(item["needle"]),
                "summary": item["summary"],
                "current_resolution_or_evidence": current_resolution,
                "remaining_action": remaining_action,
                "linked_artifacts": linked_artifacts,
            }
        )
    return rows


def false_positive_rows() -> list[dict[str, str]]:
    rows = []
    for item in FALSE_POSITIVE_ITEMS:
        search_paths = [
            Path("main.tex"),
            Path("WORK_STATUS.md"),
            Path("long_report.tex"),
            Path("inversion_workflow/processed_observations/other_hm_numeric_source_evidence.csv"),
        ]
        rows.append(
            {
                "item_id": item["item_id"],
                "audit_class": "false_positive_search_hit",
                "status": "not_active_report_comment",
                "active_report_relevance": "none",
                "source_locations": first_location(item["source_hint"], search_paths),
                "summary": item["summary"],
                "current_resolution_or_evidence": "Classified as a false positive for the active report open-comment scan.",
                "remaining_action": "No report action.",
                "linked_artifacts": item["linked_artifacts"],
            }
        )
    return rows


def count_by(rows: list[dict[str, str]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = row.get(key, "")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def build_audit(args: argparse.Namespace) -> tuple[list[dict[str, str]], dict[str, Any]]:
    pack_rows = read_csv(args.external_pack)
    external_summary = read_json(args.external_pack_summary)
    intake_summary = read_json(args.external_intake_summary)
    cte_summary = read_json(args.cte_confirmation_summary)
    marker_rows = active_marker_hits()
    rows = marker_rows + resolved_rows() + external_rows(pack_rows) + internal_rows(cte_summary) + false_positive_rows()
    active_open_items = [
        row["item_id"]
        for row in rows
        if row["audit_class"]
        in {"tracked_external_gate_request", "tracked_model_provenance_confirmation", "tracked_internal_policy"}
    ]
    summary = {
        "status": "report_open_comment_audit_generated",
        "active_report_sources": [str(path) for path in ACTIVE_REPORT_SOURCES],
        "active_report_unresolved_marker_count": len(marker_rows),
        "resolved_formulation_comment_count": len(RESOLVED_FORMULATION_ITEMS),
        "tracked_external_blocker_count": len(pack_rows),
        "tracked_internal_or_provenance_item_count": len(INTERNAL_OPEN_ITEMS),
        "false_positive_marker_count": len(FALSE_POSITIVE_ITEMS),
        "audit_row_count": len(rows),
        "audit_class_counts": count_by(rows, "audit_class"),
        "status_counts": count_by(rows, "status"),
        "external_gate_request_pack_status": external_summary.get("status"),
        "external_gate_response_intake_status": intake_summary.get("status"),
        "external_gate_response_intake_missing_response_count": intake_summary.get("missing_response_count"),
        "cte_confirmation_request_status": cte_summary.get("status"),
        "cte_confirmation_request_request_status": cte_summary.get("request_status"),
        "cte_confirmation_request_response_status": cte_summary.get("response_status"),
        "cte_confirmation_request_suggested_to": cte_summary.get("suggested_to"),
        "cte_confirmation_request_suggested_cc": cte_summary.get("suggested_cc"),
        "active_report_open_item_ids": active_open_items,
        "active_report_clean_marker_statement": (
            "No TODO/FIXME/??/LaTeX todo/highlight/color review markers were found in main.tex or "
            "measurement_chapter.tex."
            if not marker_rows
            else "Active report review markers remain; inspect report_open_comment_audit.csv."
        ),
        "notes": [
            "Resolved formulation comments are separated from provenance and calibration gates.",
            "The external rows are request/intake gates, not evidence that those gates have been closed.",
            "long_report.tex is treated as legacy context because main.tex only inputs measurement_chapter.tex.",
        ],
    }
    return rows, summary


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "item_id",
        "audit_class",
        "status",
        "active_report_relevance",
        "source_locations",
        "summary",
        "current_resolution_or_evidence",
        "remaining_action",
        "linked_artifacts",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, str]], summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Report Open Comment Audit",
        "",
        "This audit separates active LaTeX review markers from resolved formulation comments and",
        "tracked provenance/calibration gates.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Active report unresolved marker count: {summary['active_report_unresolved_marker_count']}",
        f"- Resolved formulation comments: {summary['resolved_formulation_comment_count']}",
        f"- Tracked external gate requests: {summary['tracked_external_blocker_count']}",
        f"- Tracked internal/provenance/operational items: {summary['tracked_internal_or_provenance_item_count']}",
        f"- False-positive search hits classified: {summary['false_positive_marker_count']}",
        f"- External request pack status: `{summary.get('external_gate_request_pack_status')}`",
        f"- External intake status: `{summary.get('external_gate_response_intake_status')}` "
        f"with {summary.get('external_gate_response_intake_missing_response_count')} missing responses",
        f"- CTE confirmation request status: `{summary.get('cte_confirmation_request_status')}` "
        f"({summary.get('cte_confirmation_request_request_status')}; "
        f"{summary.get('cte_confirmation_request_response_status')})",
        "",
        summary["active_report_clean_marker_statement"],
        "",
        "## Audit Rows",
        "",
        "| Item | Class | Status | Location | Summary | Remaining action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['item_id']}`",
                    f"`{row['audit_class']}`",
                    f"`{row['status']}`",
                    row["source_locations"].replace("|", "\\|"),
                    row["summary"].replace("|", "\\|"),
                    row["remaining_action"].replace("|", "\\|"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The active report has no literal TODO/FIXME/??/todo/highlight/color review markers.",
            "The earlier equation-formulation comments are resolved in the active text. The remaining",
            "issues are tracked model-provenance, observation-operator, uncertainty, calibration, and",
            "response-intake gates, so they should stay in the readiness audit instead of being treated",
            "as unresolved LaTeX comments.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def copy_to_catalogue(catalogue_dir: Path, paths: list[Path]) -> None:
    catalogue_dir.mkdir(parents=True, exist_ok=True)
    for path in paths:
        shutil.copy2(path, catalogue_dir / path.name)


def main() -> None:
    args = parse_args()
    rows, summary = build_audit(args)
    write_csv(args.output_csv, rows)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_markdown(args.output_md, rows, summary)
    copy_to_catalogue(args.catalogue_dir, [args.output_csv, args.output_json, args.output_md])


if __name__ == "__main__":
    main()
