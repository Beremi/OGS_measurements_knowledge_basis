#!/usr/bin/env python3
"""Join measurement coverage, likelihood, gate, and final-decision status."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


WORK_ROOT = Path(__file__).resolve().parents[2]

MEASUREMENT_ROWS: list[dict[str, str]] = [
    {
        "measurement_folder": "ert",
        "measurement_label": "ERT / electrical resistivity",
        "observation_id": "ert_open_time_series",
        "likelihood_stream": "ERT open-niche resistivity field",
        "gate_stream": "ert_resistivity",
        "final_criterion_id": "P09_ert_gate",
    },
    {
        "measurement_folder": "nmr",
        "measurement_label": "NMR water content",
        "observation_id": "nmr_weekly_and_seasonal",
        "likelihood_stream": "NMR weekly and seasonal water content",
        "gate_stream": "nmr_water_content",
        "final_criterion_id": "P08_nmr_residual_policy",
    },
    {
        "measurement_folder": "taupe_tdr",
        "measurement_label": "Taupe / TDR EDZ bands",
        "observation_id": "taupe_tdr_edz_bands",
        "likelihood_stream": "Taupe/TDR EDZ bands",
        "gate_stream": "taupe_tdr",
        "final_criterion_id": "P10_taupe_gate",
    },
    {
        "measurement_folder": "suction_relative_humidity",
        "measurement_label": "Suction / relative humidity",
        "observation_id": "suction_relative_humidity_open_twin",
        "likelihood_stream": "suction/relative humidity",
        "gate_stream": "relative_humidity_suction",
        "final_criterion_id": "P11_rh_gate",
    },
    {
        "measurement_folder": "permeability_pulse_tests",
        "measurement_label": "Permeability pulse tests",
        "observation_id": "permeability_pulse_tests",
        "likelihood_stream": "permeability_pulse_tests",
        "gate_stream": "permeability_pulse_tests",
        "final_criterion_id": "P13_perm_endpoint_gate",
    },
    {
        "measurement_folder": "other_hm_monitoring",
        "measurement_label": "Other HM monitoring",
        "observation_id": "other_hm_monitoring",
        "likelihood_stream": "other HM monitoring and levelling",
        "gate_stream": "other_hm_monitoring",
        "final_criterion_id": "P12_other_hm_gate",
    },
    {
        "measurement_folder": "coordinates_geometry_layout",
        "measurement_label": "Coordinates / geometry / layout",
        "observation_id": "coordinates_and_geometry",
        "likelihood_stream": "coordinates, borehole geometry, and bedding",
        "gate_stream": "geometry_support",
        "final_criterion_id": "",
    },
    {
        "measurement_folder": "bedding_geology_structure",
        "measurement_label": "Bedding / geology / structure",
        "observation_id": "bedding_structure",
        "likelihood_stream": "coordinates, borehole geometry, and bedding",
        "gate_stream": "",
        "final_criterion_id": "",
    },
    {
        "measurement_folder": "model_projection_inputs",
        "measurement_label": "Model projection inputs",
        "observation_id": "model_projection_inputs",
        "likelihood_stream": "",
        "gate_stream": "model_projection_inputs",
        "final_criterion_id": "P14_cte_confirmation",
    },
]

FIELDNAMES = [
    "measurement_folder",
    "measurement_label",
    "observation_id",
    "measurement_type",
    "model_entry_class",
    "coverage_status",
    "likelihood_stream",
    "likelihood_activation_state",
    "stream_promotion_decision",
    "final_criterion_id",
    "final_decision_status",
    "current_allowed_use",
    "manifest_model_role",
    "manifest_primary_quantity",
    "manifest_model_quantity",
    "model_link",
    "prediction_quantity",
    "residual_definition",
    "residual_transform",
    "likelihood_scale",
    "weighting_rule",
    "bias_or_model_error_terms",
    "activation_gate",
    "raw_or_processed_rows",
    "target_rows",
    "mapped_or_usable_rows",
    "active_objective_rows",
    "current_objective_rows",
    "gate_pass_warn_fail_missing",
    "hard_blockers",
    "tracked_caveats",
    "blocking_next_step",
    "include_path_consequence",
    "exclude_path_consequence",
    "report_wording_requirement",
    "primary_artifacts",
    "source_artifacts",
    "catalogue_measurement_info",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--coverage-csv",
        type=Path,
        default=Path("inversion_workflow/measurement_operator_coverage.csv"),
    )
    parser.add_argument(
        "--likelihood-csv",
        type=Path,
        default=Path("inversion_workflow/measurement_likelihood_model.csv"),
    )
    parser.add_argument(
        "--stream-gate-csv",
        type=Path,
        default=Path("inversion_workflow/measurement_stream_activation_gate_audit.csv"),
    )
    parser.add_argument(
        "--final-decision-csv",
        type=Path,
        default=Path("inversion_workflow/final_objective_decision_register.csv"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/measurement_model_entry_matrix.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/measurement_model_entry_matrix_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/measurement_model_entry_matrix.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files"),
    )
    return parser.parse_args()


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else WORK_ROOT / path


def read_csv(path: Path) -> pd.DataFrame:
    resolved = resolve(path)
    if not resolved.exists():
        return pd.DataFrame()
    return pd.read_csv(resolved, dtype=str, keep_default_na=False)


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return None if not np.isfinite(number) else number
    if value is None or value is pd.NA:
        return None
    return value


def index_by(frame: pd.DataFrame, column: str) -> dict[str, dict[str, str]]:
    if frame.empty or column not in frame.columns:
        return {}
    return {
        str(row[column]): {str(key): str(value) for key, value in row.items()}
        for _, row in frame.iterrows()
        if str(row.get(column, ""))
    }


def to_int(value: Any) -> int:
    try:
        if str(value).strip() == "":
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def join_nonempty(*items: Any) -> str:
    seen: set[str] = set()
    values: list[str] = []
    for item in items:
        for part in str(item or "").split(";"):
            cleaned = part.strip()
            if cleaned and cleaned not in seen:
                values.append(cleaned)
                seen.add(cleaned)
    return "; ".join(values)


def compact_blocker(coverage: dict[str, str], gate: dict[str, str], decision: dict[str, str]) -> str:
    return (
        decision.get("current_evidence")
        or gate.get("hard_blockers")
        or gate.get("tracked_caveats")
        or coverage.get("blocking_next_step")
        or gate.get("next_action")
        or "none"
    )


def model_entry_class(row: dict[str, Any]) -> str:
    active_rows = to_int(row.get("active_objective_rows"))
    promotion = str(row.get("stream_promotion_decision") or "")
    coverage = str(row.get("coverage_status") or "")
    if active_rows > 0:
        return "active_objective"
    if promotion in {"diagnostic_only", "boundary_audit_only", "not_ready_for_hard_residual"}:
        return promotion
    if promotion == "support_layer_ready":
        return "support_or_prior_layer"
    if coverage in {"structural_prior_ready", "support_layer_ready", "workflow_support_ready"}:
        return "support_or_prior_layer"
    if "diagnostic" in coverage:
        return "diagnostic_only"
    if "boundary" in coverage:
        return "boundary_audit_only"
    return "not_active"


def count_values(frame: pd.DataFrame, column: str) -> dict[str, int]:
    if frame.empty or column not in frame.columns:
        return {}
    series = frame[column].astype(str)
    series = series[series.ne("")]
    return {str(key): int(value) for key, value in series.value_counts().sort_index().items()}


def build_matrix(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    coverage_by_id = index_by(read_csv(args.coverage_csv), "observation_id")
    likelihood_by_stream = index_by(read_csv(args.likelihood_csv), "measurement_stream")
    gate_by_stream = index_by(read_csv(args.stream_gate_csv), "stream")
    decision_by_id = index_by(read_csv(args.final_decision_csv), "criterion_id")

    rows: list[dict[str, Any]] = []
    for spec in MEASUREMENT_ROWS:
        coverage = coverage_by_id.get(spec["observation_id"], {})
        likelihood = likelihood_by_stream.get(spec["likelihood_stream"], {})
        gate = gate_by_stream.get(spec["gate_stream"], {})
        decision = decision_by_id.get(spec["final_criterion_id"], {})
        active_rows = to_int(coverage.get("active_objective_rows") or gate.get("active_objective_rows"))
        current_rows = to_int(likelihood.get("current_objective_rows"))
        gate_counts = ""
        if gate:
            gate_counts = (
                f"pass={to_int(gate.get('pass_count'))}, warn={to_int(gate.get('warn_count'))}, "
                f"fail={to_int(gate.get('fail_count'))}, missing={to_int(gate.get('missing_evidence_count'))}"
            )
        row = {
            "measurement_folder": spec["measurement_folder"],
            "measurement_label": spec["measurement_label"],
            "observation_id": spec["observation_id"],
            "measurement_type": coverage.get("measurement_type", ""),
            "coverage_status": coverage.get("coverage_status", ""),
            "likelihood_stream": spec["likelihood_stream"],
            "likelihood_activation_state": likelihood.get("activation_state", ""),
            "stream_promotion_decision": gate.get("promotion_decision", ""),
            "final_criterion_id": spec["final_criterion_id"],
            "final_decision_status": decision.get("decision_status", ""),
            "current_allowed_use": decision.get("current_allowed_use", gate.get("promotion_decision", "")),
            "manifest_model_role": coverage.get("manifest_model_role", ""),
            "manifest_primary_quantity": coverage.get("manifest_primary_quantity", ""),
            "manifest_model_quantity": coverage.get("manifest_model_quantity", ""),
            "model_link": likelihood.get("model_link", ""),
            "prediction_quantity": likelihood.get("prediction_quantity", ""),
            "residual_definition": likelihood.get("residual_definition", ""),
            "residual_transform": likelihood.get("residual_transform", ""),
            "likelihood_scale": likelihood.get("likelihood_scale", ""),
            "weighting_rule": likelihood.get("weighting_rule", ""),
            "bias_or_model_error_terms": likelihood.get("bias_or_model_error_terms", ""),
            "activation_gate": likelihood.get("activation_gate", gate.get("next_action", "")),
            "raw_or_processed_rows": to_int(coverage.get("raw_or_processed_rows")),
            "target_rows": to_int(coverage.get("target_rows")),
            "mapped_or_usable_rows": to_int(coverage.get("mapped_or_usable_rows")),
            "active_objective_rows": active_rows,
            "current_objective_rows": current_rows,
            "gate_pass_warn_fail_missing": gate_counts,
            "hard_blockers": gate.get("hard_blockers", ""),
            "tracked_caveats": gate.get("tracked_caveats", ""),
            "blocking_next_step": compact_blocker(coverage, gate, decision),
            "include_path_consequence": decision.get("include_path_consequence", ""),
            "exclude_path_consequence": decision.get("exclude_path_consequence", ""),
            "report_wording_requirement": decision.get("report_wording_requirement", ""),
            "primary_artifacts": gate.get("primary_artifacts", ""),
            "source_artifacts": join_nonempty(
                coverage.get("evidence_files", ""),
                likelihood.get("current_artifacts", ""),
                gate.get("primary_artifacts", ""),
                decision.get("response_or_decision_locations", ""),
            ),
            "catalogue_measurement_info": (
                f"cda_knowledge_base/measurements_info/{spec['measurement_folder']}/MEASUREMENT_INFO.md"
            ),
        }
        row["model_entry_class"] = model_entry_class(row)
        if not row["current_allowed_use"]:
            row["current_allowed_use"] = row["model_entry_class"]
        rows.append(row)

    frame = pd.DataFrame(rows, columns=FIELDNAMES)
    summary = {
        "status": "measurement_model_entry_matrix_generated",
        "row_count": int(frame.shape[0]),
        "coverage_status_counts": count_values(frame, "coverage_status"),
        "likelihood_activation_state_counts": count_values(frame, "likelihood_activation_state"),
        "stream_promotion_decision_counts": count_values(frame, "stream_promotion_decision"),
        "final_decision_status_counts": count_values(frame, "final_decision_status"),
        "model_entry_class_counts": count_values(frame, "model_entry_class"),
        "current_allowed_use_counts": count_values(frame, "current_allowed_use"),
        "active_objective_row_total": int(frame["active_objective_rows"].astype(int).sum()),
        "current_objective_row_total": int(frame["current_objective_rows"].astype(int).sum()),
        "active_measurement_count": int(frame["active_objective_rows"].astype(int).gt(0).sum()),
        "diagnostic_or_boundary_measurement_count": int(
            frame["model_entry_class"].isin(["diagnostic_only", "boundary_audit_only"]).sum()
        ),
        "support_or_prior_measurement_count": int(frame["model_entry_class"].eq("support_or_prior_layer").sum()),
        "not_ready_for_hard_residual_count": int(frame["model_entry_class"].eq("not_ready_for_hard_residual").sum()),
        "rows_with_final_decision_gate": int(frame["final_criterion_id"].astype(str).ne("").sum()),
        "rows_without_likelihood_row": int(frame["likelihood_activation_state"].astype(str).eq("").sum()),
        "source_artifacts": [
            str(resolve(args.coverage_csv).relative_to(WORK_ROOT)),
            str(resolve(args.likelihood_csv).relative_to(WORK_ROOT)),
            str(resolve(args.stream_gate_csv).relative_to(WORK_ROOT)),
            str(resolve(args.final_decision_csv).relative_to(WORK_ROOT)),
        ],
        "notes": [
            "This matrix is a bridge artifact: it joins coverage, residual semantics, activation gates, and final include/exclude decisions.",
            "It does not close any external provider gate and does not promote the current field to a final all-measurement inversion result.",
            "Direct permeability and NMR are the only active objective contributors in the current matrix.",
        ],
    }
    return frame, summary


def md_cell(value: Any) -> str:
    return str(value or "").replace("\n", " ").replace("|", "\\|")


def write_markdown(path: Path, frame: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# Measurement Model-Entry Matrix",
        "",
        "This generated matrix joins the measurement coverage audit, the likelihood",
        "model, the stream activation-gate audit, and the final objective decision",
        "register. It records how each collected measurement class currently enters",
        "the frozen OGS workflow and why several streams remain diagnostic, support",
        "only, boundary-audit only, or not ready for hard residuals.",
        "",
        "## Summary",
        "",
        f"- Measurement classes: {summary['row_count']}",
        f"- Active measurement classes: {summary['active_measurement_count']}",
        f"- Active objective rows: {summary['active_objective_row_total']}",
        f"- Diagnostic/boundary classes: {summary['diagnostic_or_boundary_measurement_count']}",
        f"- Support/prior classes: {summary['support_or_prior_measurement_count']}",
        f"- Not-ready hard-residual classes: {summary['not_ready_for_hard_residual_count']}",
        f"- Rows without a likelihood row: {summary['rows_without_likelihood_row']}",
        "",
        "## Compact Matrix",
        "",
        "| Measurement | Entry class | Active rows | Current allowed use | Primary blocker or next action | Measurement-info note |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for _, row in frame.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(row["measurement_label"]),
                    f"`{md_cell(row['model_entry_class'])}`",
                    str(int(row["active_objective_rows"])),
                    f"`{md_cell(row['current_allowed_use'])}`",
                    md_cell(row["blocking_next_step"]),
                    f"`{md_cell(row['catalogue_measurement_info'])}`",
                ]
            )
            + " |"
        )

    lines.extend(["", "## Detailed Rows", ""])
    for _, row in frame.iterrows():
        blocker = row["blocking_next_step"] or "none"
        sources = row["source_artifacts"] or "none"
        lines.extend(
            [
                f"### {row['measurement_label']}",
                "",
                f"- Measurement folder: `{row['measurement_folder']}`",
                f"- Observation id: `{row['observation_id']}`",
                f"- Model-entry class: `{row['model_entry_class']}`",
                f"- Coverage status: `{row['coverage_status']}`",
                f"- Likelihood activation: `{row['likelihood_activation_state'] or 'none'}`",
                f"- Stream promotion decision: `{row['stream_promotion_decision'] or 'none'}`",
                f"- Final decision status: `{row['final_decision_status'] or 'none'}`",
                f"- Current allowed use: `{row['current_allowed_use'] or 'none'}`",
                f"- Manifest model role: {row['manifest_model_role'] or 'none'}",
                f"- Primary measured quantity: {row['manifest_primary_quantity'] or 'none'}",
                f"- Model quantity: {row['manifest_model_quantity'] or 'none'}",
                f"- Model link: {row['model_link'] or 'none'}",
                f"- Prediction quantity: {row['prediction_quantity'] or 'none'}",
                f"- Residual definition: {row['residual_definition'] or 'none'}",
                f"- Residual transform: {row['residual_transform'] or 'none'}",
                f"- Likelihood scale: {row['likelihood_scale'] or 'none'}",
                f"- Weighting rule: {row['weighting_rule'] or 'none'}",
                f"- Bias/model-error terms: {row['bias_or_model_error_terms'] or 'none'}",
                f"- Activation gate: {row['activation_gate'] or 'none'}",
                f"- Rows raw/target/mapped/active/current-objective: {row['raw_or_processed_rows']}/"
                f"{row['target_rows']}/{row['mapped_or_usable_rows']}/"
                f"{row['active_objective_rows']}/{row['current_objective_rows']}",
                f"- Gate pass/warn/fail/missing: {row['gate_pass_warn_fail_missing'] or 'none'}",
                f"- Blocker or next action: {blocker}",
                f"- Include consequence: {row['include_path_consequence'] or 'none'}",
                f"- Exclude consequence: {row['exclude_path_consequence'] or 'none'}",
                f"- Report wording requirement: {row['report_wording_requirement'] or 'none'}",
                f"- Measurement-info note: `{row['catalogue_measurement_info']}`",
                f"- Source artifacts: {sources}",
                "",
            ]
        )

    lines.extend(
        [
            "## Interpretation",
            "",
            "The matrix confirms that all nine collected measurement classes have an explicit",
            "place in the modelling workflow, but only direct permeability and NMR currently",
            "contribute active objective rows. ERT and Taupe/TDR are diagnostic streams,",
            "RH/suction is a boundary/provenance audit, other-HM remains blocked by missing",
            "numeric exports, and the geometry, bedding, and model-projection folders are",
            "support/prior layers. The final field therefore remains an active-objective",
            "incumbent rather than a final all-measurement inversion result.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def copy_outputs(catalogue_dir: Path, paths: list[Path]) -> list[dict[str, str]]:
    catalogue_dir.mkdir(parents=True, exist_ok=True)
    copies = []
    for path in paths:
        target = catalogue_dir / path.name
        shutil.copy2(path, target)
        copies.append(
            {
                "source": display_path(path),
                "catalogue_copy": display_path(target),
            }
        )
    return copies


def display_path(path: Path) -> str:
    for base in [WORK_ROOT, WORK_ROOT.parent]:
        try:
            return str(path.relative_to(base))
        except ValueError:
            continue
    return str(path)


def main() -> None:
    args = parse_args()
    output_csv = resolve(args.output_csv)
    output_json = resolve(args.output_json)
    output_md = resolve(args.output_md)
    catalogue_dir = resolve(args.catalogue_dir)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    frame, summary = build_matrix(args)
    frame.to_csv(output_csv, index=False)
    output_json.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(output_md, frame, summary)
    summary["catalogue_copies"] = copy_outputs(catalogue_dir, [output_csv, output_json, output_md])
    output_json.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    shutil.copy2(output_json, catalogue_dir / output_json.name)

    print(f"wrote {output_csv.relative_to(WORK_ROOT)}")
    print(f"wrote {output_json.relative_to(WORK_ROOT)}")
    print(f"wrote {output_md.relative_to(WORK_ROOT)}")
    print(f"measurement rows: {summary['row_count']}")
    print(f"active objective rows: {summary['active_objective_row_total']}")


if __name__ == "__main__":
    main()
