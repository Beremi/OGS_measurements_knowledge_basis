#!/usr/bin/env python3
"""Search collected local sources for evidence that could close measurement gates.

This is intentionally conservative: it records local evidence candidates, but it
does not promote a failed stream gate unless the source appears to satisfy the
gate-specific acceptance criteria.  The main purpose is to prove whether a gate is
still external after re-scanning source files, ZIP members, workbook outlines, and
extracted PDF/Office text.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


GATE_SPECS: dict[str, dict[str, Any]] = {
    "ert_transform_support": {
        "stream": "ert_resistivity",
        "gate": "ERT_TRANSFORM_SUPPORT",
        "acceptance": "ERT coordinate frame, exact transform into OGS local frame, and accepted support mask/polygon.",
        "search_terms": [
            "ert",
            "resistivity",
            "electrode",
            "elecs",
            "coordinate",
            "coordinates",
            "origin",
            "axis",
            "axes",
            "transform",
            "projection",
            "support",
            "mask",
            "polygon",
            "35 cm",
        ],
        "required_groups": [
            ["ert", "resistivity", "electrode", "elecs"],
            ["coordinate", "coordinates", "origin", "axis", "axes", "transform", "projection"],
            ["support", "mask", "polygon", "35 cm"],
        ],
        "hard_closure_terms": [
            "coordinate frame of the ert",
            "model_x",
            "model y",
            "support mask",
            "accepted support",
            "transform into the local ogs",
        ],
    },
    "ert_uncertainty": {
        "stream": "ert_resistivity",
        "gate": "ERT_UNCERTAINTY",
        "acceptance": "ERT residual uncertainty/covariance or an approved simplified weighting rule.",
        "search_terms": [
            "ert",
            "resistivity",
            "uncertainty",
            "error",
            "covariance",
            "correlation",
            "sigma",
            "standard deviation",
            "inversion error",
        ],
        "required_groups": [
            ["ert", "resistivity"],
            ["uncertainty", "error", "covariance", "correlation", "sigma", "standard deviation", "inversion error"],
        ],
        "hard_closure_terms": [
            "ert uncertainty model",
            "inversion-field uncertainty",
            "covariance matrix",
            "per-cell sigma",
            "spatial correlation length",
            "effective degrees of freedom",
        ],
    },
    "taupe_unit_calibration": {
        "stream": "taupe_tdr",
        "gate": "TAUPE_UNIT_CALIBRATION",
        "acceptance": "Physical unit of Taupe_WC.xlsx plus calibration equations, constants, and sensor uncertainty.",
        "search_terms": [
            "taupe",
            "tdr",
            "ardp",
            "calibration",
            "calibrated",
            "unit",
            "units",
            "water content",
            "volumetric",
            "permittivity",
            "dielectric",
            "equation",
            "uncertainty",
        ],
        "required_groups": [
            ["taupe", "tdr", "ardp"],
            ["calibration", "calibrated", "equation", "unit", "units"],
            ["water content", "volumetric", "permittivity", "dielectric"],
        ],
        "hard_closure_terms": [
            "taupe_wc",
            "taupe wc",
            "workbook unit",
            "sensor-specific calibration",
            "calibration equation",
            "ardp-to-water",
        ],
    },
    "rh_active_curve_provenance": {
        "stream": "relative_humidity_suction",
        "gate": "RH_ACTIVE_CURVE_PROVENANCE",
        "acceptance": "Source table or script for active 08_08 open-niche pressure curve, sensor screening, constants, sign and time convention.",
        "search_terms": [
            "08_08_open_niche_seasonal",
            "open_niche_seasonal",
            "boundary curve",
            "pressure curve",
            "relative humidity",
            "rh5",
            "rh6",
            "rh7",
            "rh8",
            "kelvin",
            "suction",
            "sensor screening",
            "time axis",
            "seasonal curve",
        ],
        "required_groups": [
            ["08_08_open_niche_seasonal", "open_niche_seasonal", "boundary curve", "pressure curve", "seasonal curve"],
            ["relative humidity", "rh5", "rh6", "rh7", "rh8", "kelvin", "suction"],
            ["script", "source", "sensor screening", "time axis", "constant", "conversion"],
        ],
        "hard_closure_terms": [
            "source sensors",
            "sensor selection rule",
            "08_08_open_niche_seasonal.xml",
            "curve generation",
            "smoothing",
            "manual edits",
            "time-axis origin",
        ],
    },
    "hm_numeric_exports": {
        "stream": "other_hm_monitoring",
        "gate": "HM_NUMERIC_EXPORTS",
        "acceptance": "Hard-residual-ready Geoscope/laser/levelling numeric exports with epochs and instrument ids.",
        "search_terms": [
            "geoscope",
            "mini-piezometer",
            "piezometer",
            "extensometer",
            "crackmeter",
            "laser",
            "laser scan",
            "levelling",
            "leveling",
            "time series",
            "timeseries",
            "export",
            "csv",
            "xlsx",
            "survey",
            "epoch",
        ],
        "required_groups": [
            ["geoscope", "mini-piezometer", "piezometer", "extensometer", "crackmeter", "laser", "laser scan", "levelling", "leveling"],
            ["time series", "timeseries", "export", "csv", "xlsx", "survey", "epoch"],
        ],
        "hard_closure_terms": [
            "geoscope export",
            "time-series export",
            "timestamps",
            "instrument id",
            "quality/status flags",
            "raw file provenance",
            "laser-scan statistical",
            "full survey table",
        ],
    },
    "hm_uncertainty": {
        "stream": "other_hm_monitoring",
        "gate": "HM_UNCERTAINTY",
        "acceptance": "Units, epochs, reference conventions, uncertainty/covariance, quality flags, and failed-sensor intervals.",
        "search_terms": [
            "geoscope",
            "extensometer",
            "piezometer",
            "crackmeter",
            "laser",
            "levelling",
            "uncertainty",
            "covariance",
            "quality",
            "status",
            "reference",
            "zero",
            "calibration",
            "failed",
            "failure",
        ],
        "required_groups": [
            ["geoscope", "extensometer", "piezometer", "crackmeter", "laser", "levelling"],
            ["uncertainty", "covariance", "quality", "status", "reference", "zero", "calibration", "failed", "failure"],
        ],
        "hard_closure_terms": [
            "uncertainty/covariance",
            "quality/status flags",
            "failure intervals",
            "laser registration uncertainty",
            "levelling covariance",
            "reference convention",
        ],
    },
    "perm_endpoint_geometry": {
        "stream": "permeability_pulse_tests",
        "gate": "PERM_SUPPORT",
        "acceptance": "Labelled start/end geometry for historical BCD-A24/25/26/27 and BFM-D19 permeability intervals.",
        "search_terms": [
            "bcd-a24",
            "bcd-a25",
            "bcd-a26",
            "bcd-a27",
            "bfm-d19",
            "permeability",
            "endpoint",
            "end point",
            "interval",
            "coordinate",
            "depth",
            "length",
            "trace",
        ],
        "required_groups": [
            ["bcd-a24", "bcd-a25", "bcd-a26", "bcd-a27", "bfm-d19"],
            ["endpoint", "end point", "interval", "coordinate", "depth", "length", "trace"],
        ],
        "hard_closure_terms": [
            "endpoint coordinates",
            "start/end coordinates",
            "start coordinate",
            "end coordinate",
            "approved digitized trace",
            "collar coordinate",
            "interval endpoints",
        ],
    },
}


EXCLUDED_PARTS = {
    "provider_responses",
    "stream_activation_gate_audit",
}

EXCLUDED_NAME_PARTS = {
    "external_gate",
    "measurement_gate_closure",
    "response_notes",
    "request_pack",
    "request_summary",
    "request.md",
    "dispatch_audit",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measurements-root", type=Path, default=Path("../cda_knowledge_base/measurements"))
    parser.add_argument("--output-csv", type=Path, default=Path("inversion_workflow/local_gate_recovery_audit.csv"))
    parser.add_argument("--output-json", type=Path, default=Path("inversion_workflow/local_gate_recovery_audit_summary.json"))
    parser.add_argument("--output-md", type=Path, default=Path("inversion_workflow/local_gate_recovery_audit.md"))
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files"),
    )
    return parser.parse_args()


def normalized(text: str) -> str:
    text = text.lower()
    text = text.replace("–", "-").replace("—", "-").replace("_", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def should_skip(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    if parts & EXCLUDED_PARTS:
        return True
    lower_name = path.name.lower()
    return any(part in lower_name for part in EXCLUDED_NAME_PARTS)


def read_text(path: Path, max_chars: int = 250_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except OSError:
        return ""


def collect_documents(root: Path) -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []

    for path in sorted(root.glob("**/source_files/**/*")):
        if not path.is_file() or should_skip(path):
            continue
        measurement = path.relative_to(root).parts[0] if path.is_relative_to(root) else ""
        documents.append(
            {
                "measurement_folder": measurement,
                "source_kind": "source_file_name",
                "source_path": rel(path, root.parent),
                "context": path.name,
                "text": path.name,
            }
        )
        suffix = path.suffix.lower()
        if suffix in {".txt", ".dat", ".csv", ".xml", ".prj", ".py", ".md", ".ohm", ".tx0"}:
            text = read_text(path)
            if text:
                documents.append(
                    {
                        "measurement_folder": measurement,
                        "source_kind": "source_file_text",
                        "source_path": rel(path, root.parent),
                        "context": path.name,
                        "text": text,
                    }
                )

    for path in sorted(root.glob("**/derived_files/deep_source_pass/extracted_text/*")):
        if not path.is_file() or should_skip(path):
            continue
        try:
            measurement = path.relative_to(root).parts[0]
        except ValueError:
            measurement = ""
        text = read_text(path)
        if not text:
            continue
        documents.append(
            {
                "measurement_folder": measurement,
                "source_kind": "deep_extracted_text",
                "source_path": rel(path, root.parent),
                "context": path.name,
                "text": text,
            }
        )

    for index_name in ["archive_member_catalog.csv", "workbook_sheet_deep_index.csv", "deep_source_index.csv"]:
        path = root / index_name
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8", errors="ignore") as handle:
            for row_number, row in enumerate(csv.DictReader(handle), start=2):
                row_text = " ".join(str(value or "") for value in row.values())
                if should_skip(Path(row_text)):
                    continue
                documents.append(
                    {
                        "measurement_folder": row.get("measurement_folder") or row.get("measurement") or "",
                        "source_kind": index_name,
                        "source_path": rel(path, root.parent),
                        "context": f"row {row_number}",
                        "text": row_text,
                    }
                )
    return documents


def matched_terms(text_norm: str, terms: list[str]) -> list[str]:
    return sorted({term for term in terms if normalized(term) in text_norm})


def required_group_hits(text_norm: str, groups: list[list[str]]) -> list[str]:
    hits: list[str] = []
    for group in groups:
        group_hits = [term for term in group if normalized(term) in text_norm]
        hits.append(", ".join(group_hits))
    return hits


def excerpt_for(text: str, terms: list[str], max_len: int = 360) -> str:
    text_one_line = re.sub(r"\s+", " ", text).strip()
    lower = text_one_line.lower()
    positions = [lower.find(term.lower()) for term in terms if lower.find(term.lower()) >= 0]
    start = max(min(positions) - 100, 0) if positions else 0
    excerpt = text_one_line[start : start + max_len]
    if start > 0:
        excerpt = "..." + excerpt
    if start + max_len < len(text_one_line):
        excerpt += "..."
    return excerpt


def likely_time_series_file(row: dict[str, str]) -> bool:
    path = row["source_path"].lower()
    context = row["context"].lower()
    return any(ext in path or ext in context for ext in [".csv", ".xlsx", ".xls", ".dat", ".txt"]) and any(
        term in normalized(row["text"])
        for term in ["timestamp", "date", "epoch", "time series", "timeseries", "survey", "geoscope"]
    )


def hard_closure_signal(gate_id: str, spec: dict[str, Any], row: dict[str, str], text_norm: str) -> bool:
    hard_terms = [normalized(term) for term in spec.get("hard_closure_terms", [])]
    if not any(term in text_norm for term in hard_terms):
        return False
    source_path = row["source_path"].lower()
    source_kind = row["source_kind"]
    if gate_id == "hm_numeric_exports":
        return source_kind in {"source_file_text", "deep_extracted_text"} and likely_time_series_file(row)
    if gate_id == "perm_endpoint_geometry":
        return "coordinate" in text_norm or "endpoint" in text_norm or "trace" in text_norm
    if gate_id == "rh_active_curve_provenance":
        return not source_path.endswith(".xml")
    return True


def classify_hit(gate_id: str, group_hits: list[str], row: dict[str, str]) -> tuple[str, str]:
    all_groups_hit = all(bool(hit) for hit in group_hits)
    if not all_groups_hit:
        return (
            "supporting_context_only",
            "Search terms match, but not all gate-specific acceptance groups are present in this local context.",
        )
    spec = GATE_SPECS[gate_id]
    text_norm = normalized(row["text"])
    if hard_closure_signal(gate_id, spec, row, text_norm):
        return (
            "possible_gate_closure_evidence_requires_review",
            "All gate-specific search groups plus a hard closure signal are present; inspect manually before changing the stream gate.",
        )
    if gate_id == "hm_numeric_exports" and not likely_time_series_file(row):
        return (
            "keyword_candidate_not_gate_closure",
            "The context names the HM instruments, but it is not a clear machine-readable time-series/statistical export.",
        )
    if gate_id == "rh_active_curve_provenance" and row["source_path"].endswith(".xml"):
        return (
            "keyword_candidate_not_gate_closure",
            "The active OGS curve is present, but this is not provenance for how the curve was generated.",
        )
    return (
        "keyword_candidate_not_gate_closure",
        "All gate-specific search groups are present, but the context does not contain a hard closure signal for the gate acceptance criteria.",
    )


def audit_documents(documents: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for doc in documents:
        text_norm = normalized(doc["text"])
        for gate_id, spec in GATE_SPECS.items():
            terms = matched_terms(text_norm, spec["search_terms"])
            if not terms:
                continue
            group_hits = required_group_hits(text_norm, spec["required_groups"])
            evidence_status, caveat = classify_hit(gate_id, group_hits, doc)
            key = (gate_id, doc["source_kind"], doc["source_path"], doc["context"])
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "gate_id": gate_id,
                    "stream": spec["stream"],
                    "gate": spec["gate"],
                    "measurement_folder": doc["measurement_folder"],
                    "source_kind": doc["source_kind"],
                    "source_path": doc["source_path"],
                    "context": doc["context"],
                    "matched_terms": "; ".join(terms),
                    "required_group_hits": " | ".join(group_hits),
                    "matched_required_group_count": str(sum(bool(hit) for hit in group_hits)),
                    "required_group_count": str(len(group_hits)),
                    "evidence_status": evidence_status,
                    "caveat": caveat,
                    "acceptance_needed": spec["acceptance"],
                    "excerpt": excerpt_for(doc["text"], terms),
                }
            )
    rows.sort(
        key=lambda row: (
            row["gate_id"],
            row["evidence_status"] != "local_closure_candidate_requires_review",
            row["measurement_folder"],
            row["source_path"],
            row["context"],
        )
    )
    return rows


def summarize(rows: list[dict[str, str]], documents: list[dict[str, str]]) -> dict[str, Any]:
    rows_by_gate: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        rows_by_gate[row["gate_id"]].append(row)

    gate_summaries: dict[str, dict[str, Any]] = {}
    for gate_id, spec in GATE_SPECS.items():
        gate_rows = rows_by_gate.get(gate_id, [])
        status_counts = Counter(row["evidence_status"] for row in gate_rows)
        closure_candidates = status_counts.get("possible_gate_closure_evidence_requires_review", 0)
        keyword_candidates = status_counts.get("keyword_candidate_not_gate_closure", 0)
        if closure_candidates:
            local_status = "possible_local_gate_closure_requires_manual_review"
        elif keyword_candidates:
            local_status = "keyword_context_found_but_gate_still_external"
        elif gate_rows:
            local_status = "supporting_local_context_only_gate_still_external"
        else:
            local_status = "no_local_evidence_found_gate_still_external"
        top_rows = gate_rows[:8]
        gate_summaries[gate_id] = {
            "stream": spec["stream"],
            "gate": spec["gate"],
            "local_status": local_status,
            "candidate_evidence_count": len(gate_rows),
            "possible_closure_evidence_count": closure_candidates,
            "keyword_candidate_not_closure_count": keyword_candidates,
            "status_counts": dict(status_counts),
            "top_sources": [
                {
                    "source_kind": row["source_kind"],
                    "source_path": row["source_path"],
                    "context": row["context"],
                    "evidence_status": row["evidence_status"],
                    "matched_terms": row["matched_terms"],
                }
                for row in top_rows
            ],
        }

    return {
        "status": "local_gate_recovery_audit_generated",
        "document_count": len(documents),
        "evidence_row_count": len(rows),
        "gate_count": len(GATE_SPECS),
        "gates_with_closure_candidates": sorted(
            gate_id for gate_id, summary in gate_summaries.items() if summary["possible_closure_evidence_count"]
        ),
        "gates_still_external_after_local_rescan": sorted(
            gate_id for gate_id, summary in gate_summaries.items() if not summary["possible_closure_evidence_count"]
        ),
        "gate_summaries": gate_summaries,
        "notes": [
            "This audit excludes provider response templates and generated request drafts to avoid circular evidence.",
            "A possible_gate_closure_evidence_requires_review row is not a closed gate; it is a candidate for manual inspection.",
            "Supporting context confirms why a stream matters but does not satisfy the gate acceptance criteria.",
        ],
    }


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else [
        "gate_id",
        "stream",
        "gate",
        "measurement_folder",
        "source_kind",
        "source_path",
        "context",
        "matched_terms",
        "required_group_hits",
        "matched_required_group_count",
        "required_group_count",
        "evidence_status",
        "caveat",
        "acceptance_needed",
        "excerpt",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, str]], summary: dict[str, Any]) -> None:
    lines = [
        "# Local Gate Recovery Audit",
        "",
        "This audit re-scans the collected local measurement sources for evidence that could close the failed measurement-stream activation gates.",
        "It excludes generated request drafts and provider-response templates, so matches are evidence from source files or source indexes rather than circular restatements of the blockers.",
        "",
        "## Summary",
        "",
        f"- Status: `{summary['status']}`",
        f"- Local source/index documents scanned: {summary['document_count']}",
        f"- Evidence rows: {summary['evidence_row_count']}",
        f"- Gates audited: {summary['gate_count']}",
        f"- Gates with possible local closure evidence requiring manual review: {len(summary['gates_with_closure_candidates'])}",
        f"- Gates still external after local rescan: {len(summary['gates_still_external_after_local_rescan'])}",
        "",
        "## Gate Results",
        "",
        "| Gate | Local status | Evidence rows | Possible closure evidence | Top source hints |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for gate_id, gate_summary in summary["gate_summaries"].items():
        top = "; ".join(
            f"{item['source_path']} ({item['context']})"
            for item in gate_summary["top_sources"][:3]
        ) or "none"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{gate_id}`",
                    f"`{gate_summary['local_status']}`",
                    str(gate_summary["candidate_evidence_count"]),
                    str(gate_summary["possible_closure_evidence_count"]),
                    top.replace("|", "\\|"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Possible Closure Evidence Rows",
            "",
        ]
    )
    closure_rows = [row for row in rows if row["evidence_status"] == "possible_gate_closure_evidence_requires_review"]
    if closure_rows:
        lines.extend(
            [
                "| Gate | Source | Context | Matched terms | Caveat |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for row in closure_rows[:40]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{row['gate_id']}`",
                        f"`{row['source_path']}`",
                        row["context"].replace("|", "\\|"),
                        row["matched_terms"].replace("|", "\\|"),
                        row["caveat"].replace("|", "\\|"),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No row satisfied the gate-specific hard closure checks.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The audit is deliberately conservative.  A row with supporting context is useful provenance, but it is not sufficient to promote a stream to a hard residual.  A closure-candidate row should be inspected against the acceptance criteria before changing the stream activation gate.",
            "",
            "The full row-level table is `local_gate_recovery_audit.csv`; the machine-readable summary is `local_gate_recovery_audit_summary.json`.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def copy_outputs(paths: list[Path], catalogue_dir: Path) -> None:
    catalogue_dir.mkdir(parents=True, exist_ok=True)
    for path in paths:
        if path.exists():
            shutil.copy2(path, catalogue_dir / path.name)


def main() -> None:
    args = parse_args()
    documents = collect_documents(args.measurements_root)
    rows = audit_documents(documents)
    summary = summarize(rows, documents)
    write_csv(args.output_csv, rows)
    args.output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_markdown(args.output_md, rows, summary)
    if args.catalogue_dir:
        copy_outputs([args.output_csv, args.output_json, args.output_md], args.catalogue_dir)


if __name__ == "__main__":
    main()
