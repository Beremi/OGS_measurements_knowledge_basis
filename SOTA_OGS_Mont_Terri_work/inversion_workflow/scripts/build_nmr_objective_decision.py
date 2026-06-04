#!/usr/bin/env python3
"""Build a provisional NMR objective decision package.

The current active NMR residual is intentionally still conditional because raw NMR
water content includes bound/interlayer-water effects that are not part of the OGS
transport proxy theta = porosity * liquid_saturation.  This script turns the
existing bound-water and candidate-bias audits into a concise decision package.
It does not change the default raw-theta active objective.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("inversion_workflow"))
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/nmr/derived_files"),
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def display_path(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def fmt(value: Any, digits: int = 6) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "n/a"
    return f"{number:.{digits}f}"


def build_rows(bias: dict[str, Any]) -> list[dict[str, Any]]:
    bound = bias.get("bound_water_summary", {})
    best_current = bias.get("best_current_combined", {})
    best_label = bias.get("best_label_bias_combined", {})
    best_trend = bias.get("best_trend_anomaly_combined", {})
    offset_best = bias.get("best_by_uniform_offset", {}).get("0.05", {})
    zero_offset = bias.get("best_by_uniform_offset", {}).get("0", {})
    best_offset_physical = bound.get("best_uniform_offset_by_simple_physical_count_usable", {})
    fixed_phi = bound.get("fixed_phi")
    required_offsets = bound.get("required_offset_quantiles_usable", {})
    common_rows = int(bias.get("active_nmr_rows_per_run", 0) or best_current.get("active_nmr_rows", 0) or 0)
    groups = int(best_current.get("active_nmr_label_groups", 0) or best_trend.get("trend_anomaly_groups", 0) or 0)

    return [
        {
            "option_id": "raw_absolute_current",
            "decision": "current_active_but_conditional",
            "recommended_for_final_objective": "no",
            "residual_definition": "theta_model - raw theta_NMR_obs",
            "nuisance_terms": "none",
            "candidate_selected_by_this_option": best_current.get("run_id"),
            "candidate_current_combined_rank": best_current.get("current_combined_rank"),
            "candidate_bias_safe_rank": best_current.get("label_bias_combined_rank"),
            "combined_objective": best_current.get("current_combined_objective"),
            "nmr_objective": best_current.get("current_nmr_objective_from_rows"),
            "nmr_rmse_normalized": best_current.get("current_nmr_rmse_normalized_residual"),
            "active_rows": common_rows,
            "label_groups": groups,
            "nonphysical_or_caveated_rows": zero_offset.get("corrected_nonphysical_rows"),
            "main_rationale": (
                "This is the implemented active residual, but it compares total NMR-visible water "
                "content to mobile OGS theta without a bound/interlayer-water term."
            ),
            "acceptance_criteria": (
                "Do not call this final unless a bound/interlayer-water model-error term is accepted "
                "and the report states that the residual is conditional."
            ),
        },
        {
            "option_id": "global_uniform_offset",
            "decision": "stress_test_only_not_recommended",
            "recommended_for_final_objective": "no",
            "residual_definition": "theta_model - (theta_NMR_obs - global_offset)",
            "nuisance_terms": f"single global offset, best physical-count offset={best_offset_physical.get('offset_fraction')}",
            "candidate_selected_by_this_option": offset_best.get("run_id"),
            "candidate_current_combined_rank": "",
            "candidate_bias_safe_rank": "",
            "combined_objective": offset_best.get("combined_offset_objective"),
            "nmr_objective": offset_best.get("nmr_offset_objective"),
            "nmr_rmse_normalized": offset_best.get("nmr_offset_rmse_normalized_residual"),
            "active_rows": common_rows,
            "label_groups": groups,
            "nonphysical_or_caveated_rows": offset_best.get("corrected_nonphysical_rows"),
            "main_rationale": (
                "A single subtraction improves physical-row counts but still leaves nonphysical rows "
                "and overcorrects low-water labels; it is useful only as a sensitivity check."
            ),
            "acceptance_criteria": "Reject as final unless collaborators provide one physically justified global offset.",
        },
        {
            "option_id": "absolute_with_label_bias",
            "decision": "acceptable_if_absolute_nmr_is_required",
            "recommended_for_final_objective": "conditional",
            "residual_definition": "theta_model + b_label - theta_NMR_obs",
            "nuisance_terms": "non-negative label/campaign bias per observation_family + measurement_label",
            "candidate_selected_by_this_option": best_label.get("run_id"),
            "candidate_current_combined_rank": best_label.get("current_combined_rank"),
            "candidate_bias_safe_rank": best_label.get("label_bias_combined_rank"),
            "combined_objective": best_label.get("label_bias_combined_objective"),
            "nmr_objective": best_label.get("label_bias_objective"),
            "nmr_rmse_normalized": best_label.get("label_bias_rmse_normalized_residual"),
            "active_rows": common_rows,
            "label_groups": groups,
            "nonphysical_or_caveated_rows": (
                f"bias_mean={fmt(best_label.get('fitted_label_bias_mean'))}; "
                f"bias_p90={fmt(best_label.get('fitted_label_bias_p90'))}; "
                f"bias_max={fmt(best_label.get('fitted_label_bias_max'))}"
            ),
            "main_rationale": (
                "This preserves absolute information while explicitly absorbing constant bound/"
                "interlayer-water and campaign offsets."
            ),
            "acceptance_criteria": (
                "Requires an approved prior/penalty or reporting policy for bias terms; biases must "
                "not be silently interpreted as transport water."
            ),
        },
        {
            "option_id": "within_label_trend_anomaly",
            "decision": "recommended_provisional_nmr_residual",
            "recommended_for_final_objective": "yes_after_acceptance",
            "residual_definition": (
                "(theta_model - mean_label(theta_model)) - "
                "(theta_NMR_obs - mean_label(theta_NMR_obs))"
            ),
            "nuisance_terms": "constant label/campaign offsets cancel by centering",
            "candidate_selected_by_this_option": best_trend.get("run_id"),
            "candidate_current_combined_rank": best_trend.get("current_combined_rank"),
            "candidate_bias_safe_rank": best_trend.get("trend_anomaly_combined_rank"),
            "combined_objective": best_trend.get("trend_anomaly_combined_objective"),
            "nmr_objective": best_trend.get("trend_anomaly_objective"),
            "nmr_rmse_normalized": best_trend.get("trend_anomaly_rmse_normalized_residual"),
            "active_rows": common_rows,
            "label_groups": groups,
            "nonphysical_or_caveated_rows": "absolute offsets removed; absolute water content not fitted",
            "main_rationale": (
                "This is the safest first OGS-backed NMR residual because constant bound/interlayer-"
                "water offsets cancel to first order and no porosity release is needed."
            ),
            "acceptance_criteria": (
                "The executable assembler mode and ranking package now exist; accepting this option "
                "means promoting it to the reporting/search default and stating that NMR contributes "
                "trends/anomalies, not absolute mobile water content."
            ),
        },
    ]


def build_summary(
    rows: list[dict[str, Any]],
    bias: dict[str, Any],
    activation: dict[str, Any],
) -> dict[str, Any]:
    bound = bias.get("bound_water_summary", {})
    best_current = bias.get("best_current_combined", {})
    best_trend = bias.get("best_trend_anomaly_combined", {})
    best_activation = activation.get("best_trend_anomaly_active_objective", {})
    recommended = next(row for row in rows if row["option_id"] == "within_label_trend_anomaly")
    return {
        "status": "nmr_objective_decision_generated_active_objective_unchanged",
        "recommended_option_id": recommended["option_id"],
        "recommended_policy": "Use within-label trend/anomaly NMR residuals as the first provisional final NMR likelihood; keep raw absolute NMR conditional.",
        "active_objective_changed": False,
        "active_nmr_rows_per_run": bias.get("active_nmr_rows_per_run"),
        "active_nmr_label_groups": best_current.get("active_nmr_label_groups"),
        "active_nmr_weekly_rows": best_current.get("active_nmr_weekly_rows"),
        "active_nmr_seasonal_rows": best_current.get("active_nmr_seasonal_rows"),
        "fixed_phi": bound.get("fixed_phi"),
        "usable_current_mesh_rows": bound.get("usable_current_mesh_rows"),
        "uncorrected_usable_rows_above_fixed_phi": bound.get("uncorrected_usable_rows_above_fixed_phi"),
        "required_offset_quantiles_usable": bound.get("required_offset_quantiles_usable"),
        "best_current_raw_run": best_current.get("run_id"),
        "best_current_raw_objective": best_current.get("current_combined_objective"),
        "best_recommended_run": best_trend.get("run_id"),
        "best_recommended_combined_objective": best_trend.get("trend_anomaly_combined_objective"),
        "best_recommended_current_rank": best_trend.get("current_combined_rank"),
        "current_incumbent_recommended_rank": best_current.get("trend_anomaly_combined_rank"),
        "current_vs_recommended_rank_correlation": bias.get("current_vs_trend_anomaly_rank_correlation"),
        "executable_mode_status": activation.get("status"),
        "executable_mode": activation.get("state_objective_mode"),
        "executable_full_active_runs": activation.get("runs_with_full_active_trend_objective"),
        "executable_best_run": best_activation.get("run_id"),
        "executable_best_objective": best_activation.get("nmr_trend_anomaly_active_objective"),
        "executable_validation_max_abs_delta": activation.get("diagnostic_validation_max_abs_delta"),
        "diagnostic_objective_range": bias.get("trend_anomaly_objective_range"),
        "decision_implication": (
            "The present permeability-field incumbent remains the best raw absolute-theta candidate, "
            "but it is only rank 14 under the recommended NMR trend/anomaly treatment. The best "
            "trend/anomaly candidate is rank 56 under the raw active objective, so the NMR residual "
            "definition materially affects candidate selection."
        ),
        "implementation_gate": (
            "Do not change the default active objective silently. The centered-label anomaly "
            "assembler mode and regenerated ranking package now exist; promotion to the default "
            "reporting/search objective still requires an explicit modelling decision."
        ),
    }


def write_markdown(path: Path, rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    lines = [
        "# NMR Objective Decision",
        "",
        "This package turns the existing NMR bound-water and candidate-bias audits into a",
        "provisional objective decision. It does not change the default raw-theta active objective.",
        "",
        "## Recommendation",
        "",
        f"- Recommended option: `{summary['recommended_option_id']}`.",
        f"- Active objective changed: `{summary['active_objective_changed']}`.",
        f"- Active NMR rows per run: {summary['active_nmr_rows_per_run']}.",
        f"- Active NMR label groups: {summary['active_nmr_label_groups']}.",
        f"- Fixed model porosity used in audits: {summary['fixed_phi']}.",
        f"- Usable mapped NMR rows above fixed porosity before correction: "
        f"{summary['uncorrected_usable_rows_above_fixed_phi']} of {summary['usable_current_mesh_rows']}.",
        f"- Current-vs-recommended rank correlation: {summary['current_vs_recommended_rank_correlation']}.",
        f"- Executable mode status: `{summary.get('executable_mode_status')}`.",
        f"- Executable best run: `{summary.get('executable_best_run')}` with objective "
        f"{fmt(summary.get('executable_best_objective'))}.",
        f"- Executable-vs-diagnostic validation max abs delta: "
        f"{fmt(summary.get('executable_validation_max_abs_delta'), 12)}.",
        "",
        summary["recommended_policy"],
        "",
        "The recommended first final NMR likelihood is a within-label trend/anomaly",
        "residual. It compares temporal/spatial changes after centering each",
        "`observation_family + measurement_label` group. This removes constant",
        "bound/interlayer-water and campaign offsets to first order and avoids treating",
        "total NMR-visible water as mobile transport water.",
        "",
        "## Decision Table",
        "",
        "| Option | Decision | Final? | Selected run | Combined objective | Caveat |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['option_id']}`",
                    f"`{row['decision']}`",
                    f"`{row['recommended_for_final_objective']}`",
                    f"`{row['candidate_selected_by_this_option']}`",
                    fmt(row["combined_objective"]),
                    str(row["main_rationale"]).replace("|", "\\|"),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Option Details", ""])
    for row in rows:
        lines.extend(
            [
                f"### `{row['option_id']}`",
                "",
                f"- Residual definition: {row['residual_definition']}",
                f"- Nuisance terms: {row['nuisance_terms']}",
                f"- Selected candidate: `{row['candidate_selected_by_this_option']}`",
                f"- Current-objective rank of selected candidate: {row['candidate_current_combined_rank']}",
                f"- Bias/anomaly-safe rank of selected candidate: {row['candidate_bias_safe_rank']}",
                f"- NMR objective: {row['nmr_objective']}",
                f"- Normalized residual RMSE: {row['nmr_rmse_normalized']}",
                f"- Nonphysical/caveated rows or offsets: {row['nonphysical_or_caveated_rows']}",
                f"- Acceptance criteria: {row['acceptance_criteria']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Implication",
            "",
            summary["decision_implication"],
            "",
            summary["implementation_gate"],
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[2]
    output_dir = (repo / args.output_dir if not args.output_dir.is_absolute() else args.output_dir).resolve()
    catalogue_dir = (repo / args.catalogue_dir if not args.catalogue_dir.is_absolute() else args.catalogue_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    catalogue_dir.mkdir(parents=True, exist_ok=True)

    bias = read_json(repo / "inversion_workflow/nmr_candidate_bias_sensitivity_summary.json")
    activation = read_json(repo / "inversion_workflow/nmr_trend_anomaly_active_objective_summary.json")
    rows = build_rows(bias)
    summary = build_summary(rows, bias, activation)

    fields = [
        "option_id",
        "decision",
        "recommended_for_final_objective",
        "residual_definition",
        "nuisance_terms",
        "candidate_selected_by_this_option",
        "candidate_current_combined_rank",
        "candidate_bias_safe_rank",
        "combined_objective",
        "nmr_objective",
        "nmr_rmse_normalized",
        "active_rows",
        "label_groups",
        "nonphysical_or_caveated_rows",
        "main_rationale",
        "acceptance_criteria",
    ]
    csv_path = output_dir / "nmr_objective_decision.csv"
    json_path = output_dir / "nmr_objective_decision_summary.json"
    md_path = output_dir / "nmr_objective_decision.md"
    write_csv(csv_path, rows, fields)
    write_markdown(md_path, rows, summary)

    copies = []
    for source in [csv_path, md_path]:
        target = catalogue_dir / source.name
        shutil.copy2(source, target)
        copies.append({"source": display_path(source, repo), "catalogue_copy": display_path(target, repo)})
    summary["generated_files"] = [display_path(path, repo) for path in [csv_path, json_path, md_path]]
    summary["catalogue_copies"] = copies
    json_path.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    target = catalogue_dir / json_path.name
    shutil.copy2(json_path, target)
    summary["catalogue_copies"].append({"source": display_path(json_path, repo), "catalogue_copy": display_path(target, repo)})
    json_path.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shutil.copy2(json_path, target)
    print(json.dumps(json_ready(summary), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
