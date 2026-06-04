#!/usr/bin/env python3
"""Package scenario-winning permeability fields for conditional inspection."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd

from build_current_permeability_field_package import SUMMARY_FILES, field_stats, json_ready, write_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario-summary",
        type=Path,
        default=Path("inversion_workflow/conditional_field_selection_scenarios_summary.json"),
    )
    parser.add_argument(
        "--scenario-csv",
        type=Path,
        default=Path("inversion_workflow/conditional_field_selection_scenarios.csv"),
    )
    parser.add_argument(
        "--scorecard",
        type=Path,
        default=Path("inversion_workflow/cross_stream_candidate_scorecard.csv"),
    )
    parser.add_argument(
        "--nmr-audit",
        type=Path,
        default=Path("inversion_workflow/nmr_candidate_bias_sensitivity_audit.csv"),
    )
    parser.add_argument(
        "--ert-audit",
        type=Path,
        default=Path("inversion_workflow/ert_candidate_discrimination_audit.csv"),
    )
    parser.add_argument(
        "--taupe-audit",
        type=Path,
        default=Path("inversion_workflow/taupe_candidate_discrimination_audit.csv"),
    )
    parser.add_argument("--runs-dir", type=Path, default=Path("inversion_workflow/runs"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/conditional_field_candidates"),
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def safe_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result


def scenario_memberships(frame: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    memberships: dict[str, list[dict[str, Any]]] = {}
    for _, row in frame.iterrows():
        run_id = str(row["winner_run_id"])
        memberships.setdefault(run_id, []).append(
            {
                "scenario_id": row["scenario_id"],
                "title": row["title"],
                "gate_status": row["gate_status"],
                "winner_score": safe_float(row["winner_score"]),
                "winner_active_rank": safe_float(row["winner_active_rank"]),
                "winner_nmr_trend_rank": safe_float(row["winner_nmr_trend_rank"]),
                "winner_ert_rank": safe_float(row["winner_ert_rank"]),
                "winner_taupe_rank": safe_float(row["winner_taupe_rank"]),
            }
        )
    return memberships


def scorecard_rows(scorecard: pd.DataFrame) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for _, row in scorecard.iterrows():
        rows[str(row["run_id"])] = {
            "run_id": row["run_id"],
            "run_kind": row.get("run_kind"),
            "current_combined_objective": safe_float(row.get("current_combined_objective")),
            "direct_permeability_objective": safe_float(row.get("direct_permeability_objective")),
            "raw_nmr_state_objective": safe_float(row.get("current_nmr_objective_from_summary")),
            "nmr_trend_anomaly_combined_objective": safe_float(row.get("trend_anomaly_combined_objective")),
            "ert_residual_mae_log10": safe_float(row.get("ert_residual_mae_log10")),
            "taupe_trend_mae": safe_float(row.get("taupe_trend_mae")),
            "active_objective_rank": safe_float(row.get("active_objective_rank")),
            "nmr_trend_anomaly_rank": safe_float(row.get("nmr_trend_anomaly_rank")),
            "ert_mae_rank": safe_float(row.get("ert_mae_rank")),
            "taupe_mae_rank": safe_float(row.get("taupe_mae_rank")),
            "mean_rank_all_streams": safe_float(row.get("mean_rank_all_streams")),
            "worst_rank_all_streams": safe_float(row.get("worst_rank_all_streams")),
        }
    return rows


def audit_rows(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if frame.empty or "run_id" not in frame.columns:
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for _, row in frame.iterrows():
        rows[str(row["run_id"])] = row.fillna("").to_dict()
    return rows


def metric_row(
    *,
    run_id: str,
    stream: str,
    status: str,
    objective_or_loss: Any = "",
    rank: Any = "",
    rows_used: Any = "",
    groups_or_series: Any = "",
    rmse_or_mae: Any = "",
    source_artifact: str = "",
    caveat: str = "",
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "stream": stream,
        "status": status,
        "objective_or_loss": objective_or_loss,
        "rank": rank,
        "rows_used": rows_used,
        "groups_or_series": groups_or_series,
        "rmse_or_mae": rmse_or_mae,
        "source_artifact": source_artifact,
        "caveat": caveat,
    }


def diagnostic_metric_evidence(
    run_id: str,
    *,
    nmr_rows: dict[str, dict[str, Any]],
    ert_rows: dict[str, dict[str, Any]],
    taupe_rows: dict[str, dict[str, Any]],
    nmr_audit_path: Path,
    ert_audit_path: Path,
    taupe_audit_path: Path,
) -> list[dict[str, Any]]:
    nmr = nmr_rows.get(run_id, {})
    ert = ert_rows.get(run_id, {})
    taupe = taupe_rows.get(run_id, {})
    evidence: list[dict[str, Any]] = []
    if nmr:
        evidence.extend(
            [
                metric_row(
                    run_id=run_id,
                    stream="active_direct_permeability_plus_raw_nmr",
                    status="available_from_nmr_bias_audit",
                    objective_or_loss=nmr.get("current_combined_objective"),
                    rank=nmr.get("current_combined_rank"),
                    rows_used=nmr.get("active_nmr_rows"),
                    groups_or_series=nmr.get("active_nmr_label_groups"),
                    rmse_or_mae=nmr.get("current_nmr_rmse_normalized_residual"),
                    source_artifact=str(nmr_audit_path),
                    caveat="active objective includes direct pulse-test permeability plus raw absolute NMR theta residuals",
                ),
                metric_row(
                    run_id=run_id,
                    stream="nmr_label_bias",
                    status="available_from_nmr_bias_audit",
                    objective_or_loss=nmr.get("label_bias_combined_objective"),
                    rank=nmr.get("label_bias_combined_rank"),
                    rows_used=nmr.get("active_nmr_rows"),
                    groups_or_series=nmr.get("active_nmr_label_groups"),
                    rmse_or_mae=nmr.get("label_bias_rmse_normalized_residual"),
                    source_artifact=str(nmr_audit_path),
                    caveat="diagnostic alternative for label/campaign bias; not the current default objective",
                ),
                metric_row(
                    run_id=run_id,
                    stream="nmr_within_label_trend_anomaly",
                    status="available_from_nmr_bias_audit",
                    objective_or_loss=nmr.get("trend_anomaly_combined_objective"),
                    rank=nmr.get("trend_anomaly_combined_rank"),
                    rows_used=nmr.get("trend_anomaly_rows"),
                    groups_or_series=nmr.get("trend_anomaly_groups"),
                    rmse_or_mae=nmr.get("trend_anomaly_rmse_normalized_residual"),
                    source_artifact=str(nmr_audit_path),
                    caveat="preferred provisional NMR policy, but final NMR policy is not selected",
                ),
            ]
        )
    else:
        evidence.append(
            metric_row(
                run_id=run_id,
                stream="nmr_streams",
                status="missing_from_nmr_bias_audit",
                source_artifact=str(nmr_audit_path),
                caveat="scenario winner is not present in the NMR audit table",
            )
        )
    if ert:
        evidence.append(
            metric_row(
                run_id=run_id,
                stream="ert_log_resistivity_diagnostic",
                status="available_from_ert_discrimination_audit",
                objective_or_loss=ert.get("ert_residual_mae_log10"),
                rank=ert.get("ert_mae_rank"),
                rows_used=ert.get("compared_rows"),
                groups_or_series=ert.get("compared_output_times"),
                rmse_or_mae=ert.get("ert_residual_rmse_log10"),
                source_artifact=str(ert_audit_path),
                caveat="ERT remains diagnostic until transform/support and uncertainty gates are closed",
            )
        )
    else:
        evidence.append(
            metric_row(
                run_id=run_id,
                stream="ert_log_resistivity_diagnostic",
                status="missing_from_ert_discrimination_audit",
                source_artifact=str(ert_audit_path),
                caveat="scenario winner is not present in the ERT audit table",
            )
        )
    if taupe:
        evidence.append(
            metric_row(
                run_id=run_id,
                stream="taupe_tdr_trend_diagnostic",
                status="available_from_taupe_discrimination_audit",
                objective_or_loss=taupe.get("taupe_trend_mae"),
                rank=taupe.get("taupe_mae_rank"),
                rows_used=taupe.get("compared_rows"),
                groups_or_series=taupe.get("compared_series"),
                rmse_or_mae=taupe.get("taupe_trend_rmse"),
                source_artifact=str(taupe_audit_path),
                caveat="Taupe/TDR remains diagnostic until unit/calibration and uncertainty gates are closed",
            )
        )
    else:
        evidence.append(
            metric_row(
                run_id=run_id,
                stream="taupe_tdr_trend_diagnostic",
                status="missing_from_taupe_discrimination_audit",
                source_artifact=str(taupe_audit_path),
                caveat="scenario winner is not present in the Taupe/TDR audit table",
            )
        )
    return evidence


def copy_candidate_files(run_dir: Path, candidate_dir: Path) -> dict[str, str]:
    candidate_dir.mkdir(parents=True, exist_ok=True)
    copied: dict[str, str] = {}
    mesh_source = run_dir / "bulk_w_projections.vtu"
    mesh_dest = candidate_dir / "bulk_w_projections.vtu"
    shutil.copy2(mesh_source, mesh_dest)
    copied[str(mesh_source)] = str(mesh_dest)
    for name in SUMMARY_FILES:
        source = run_dir / name
        if source.exists():
            dest = candidate_dir / name
            shutil.copy2(source, dest)
            copied[str(source)] = str(dest)
    return copied


def write_inventory(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "run_id",
        "run_kind",
        "scenario_count",
        "scenario_ids",
        "candidate_dir",
        "packaged_mesh",
        "active_objective_rank",
        "nmr_trend_anomaly_rank",
        "ert_mae_rank",
        "taupe_mae_rank",
        "mean_rank_all_streams",
        "worst_rank_all_streams",
        "current_combined_objective",
        "direct_permeability_objective",
        "raw_nmr_state_objective",
        "nmr_trend_anomaly_combined_objective",
        "ert_residual_mae_log10",
        "taupe_trend_mae",
        "triangle6_cell_count",
        "positive_definite_cell_count",
        "log10_k_eigen_min_p50",
        "log10_k_eigen_max_p50",
        "anisotropy_ratio_p50",
        "theta_deg_p50",
        "porosity_p50",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_markdown(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Conditional Field Candidate Package",
        "",
        "This package copies the unique scenario-winning permeability fields into one",
        "inspection folder. It does not select a final field; it makes the conditional",
        "field alternatives concrete and comparable.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Scenario count: {summary['scenario_count']}",
        f"- Candidate count: {summary['candidate_count']}",
        f"- Current packaged field wins: {summary['current_field_winning_scenario_count']} scenarios",
        f"- Selection stability: `{summary['selection_stability']}`",
        f"- Diagnostic metric evidence rows: {summary['metric_evidence_row_count']}",
        f"- Missing diagnostic metric evidence rows: {summary['metric_evidence_missing_row_count']}",
        "",
        "## Candidates",
        "",
        "| Candidate | Scenarios | Active rank | NMR rank | ERT rank | Taupe rank | Mean rank | Mesh |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for candidate in summary["candidates"]:
        metrics = candidate.get("scorecard_metrics", {})
        lines.append(
            f"| `{candidate['run_id']}` | {', '.join(candidate['scenario_ids'])} | "
            f"{metrics.get('active_objective_rank')} | {metrics.get('nmr_trend_anomaly_rank')} | "
            f"{metrics.get('ert_mae_rank')} | {metrics.get('taupe_mae_rank')} | "
            f"{metrics.get('mean_rank_all_streams')} | `{candidate['packaged_mesh']}` |"
        )
    lines.extend(["", "## Interpretation", ""])
    for item in summary["interpretation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Files", ""])
    lines.append(f"- Inventory: `{summary['inventory_csv']}`")
    lines.append(f"- Metric evidence: `{summary['metric_evidence_csv']}`")
    lines.append(f"- Summary: `{summary['summary_json']}`")
    for candidate in summary["candidates"]:
        lines.append(
            f"- Candidate `{candidate['run_id']}`: `{candidate['candidate_dir']}` "
            f"(metric evidence: `{candidate['diagnostic_metric_evidence_csv']}`)"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_package(args: argparse.Namespace) -> dict[str, Any]:
    scenario_summary = read_json(args.scenario_summary)
    scenario_frame = pd.read_csv(args.scenario_csv)
    scorecard_frame = pd.read_csv(args.scorecard)
    nmr_frame = pd.read_csv(args.nmr_audit)
    ert_frame = pd.read_csv(args.ert_audit)
    taupe_frame = pd.read_csv(args.taupe_audit)
    memberships = scenario_memberships(scenario_frame)
    score_rows = scorecard_rows(scorecard_frame)
    nmr_rows = audit_rows(nmr_frame)
    ert_rows = audit_rows(ert_frame)
    taupe_rows = audit_rows(taupe_frame)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    candidate_summaries: list[dict[str, Any]] = []
    inventory_rows: list[dict[str, Any]] = []
    all_metric_evidence_rows: list[dict[str, Any]] = []
    for run_id in sorted(memberships):
        run_dir = args.runs_dir / run_id
        if not run_dir.exists():
            raise FileNotFoundError(f"Missing run directory for scenario winner: {run_dir}")
        if not (run_dir / "bulk_w_projections.vtu").exists():
            raise FileNotFoundError(f"Missing scenario-winner mesh: {run_dir / 'bulk_w_projections.vtu'}")
        candidate_dir = output_dir / run_id
        copied = copy_candidate_files(run_dir, candidate_dir)
        mesh_dest = candidate_dir / "bulk_w_projections.vtu"
        stats_rows, field_summary = field_stats(mesh_dest)
        stats_csv = candidate_dir / "field_stats.csv"
        write_csv(stats_csv, stats_rows)
        metric_evidence_rows = diagnostic_metric_evidence(
            run_id,
            nmr_rows=nmr_rows,
            ert_rows=ert_rows,
            taupe_rows=taupe_rows,
            nmr_audit_path=args.nmr_audit,
            ert_audit_path=args.ert_audit,
            taupe_audit_path=args.taupe_audit,
        )
        metric_evidence_csv = candidate_dir / "diagnostic_metric_evidence.csv"
        pd.DataFrame(metric_evidence_rows).to_csv(metric_evidence_csv, index=False)
        all_metric_evidence_rows.extend(metric_evidence_rows)

        score = score_rows.get(run_id, {})
        metrics = field_summary.get("field_metrics", {})
        candidate_summary = {
            "run_id": run_id,
            "run_kind": score.get("run_kind"),
            "source_run_dir": str(run_dir),
            "candidate_dir": str(candidate_dir),
            "packaged_mesh": str(mesh_dest),
            "field_stats_csv": str(stats_csv),
            "diagnostic_metric_evidence_csv": str(metric_evidence_csv),
            "diagnostic_metric_evidence": metric_evidence_rows,
            "scenario_memberships": memberships[run_id],
            "scenario_ids": [item["scenario_id"] for item in memberships[run_id]],
            "scenario_count": len(memberships[run_id]),
            "scorecard_metrics": score,
            "field": field_summary,
            "copied_files": copied,
        }
        (candidate_dir / "CANDIDATE_FIELD_SUMMARY.json").write_text(
            json.dumps(json_ready(candidate_summary), indent=2) + "\n", encoding="utf-8"
        )
        candidate_summaries.append(json_ready(candidate_summary))
        inventory_rows.append(
            {
                "run_id": run_id,
                "run_kind": score.get("run_kind"),
                "scenario_count": len(memberships[run_id]),
                "scenario_ids": ";".join(candidate_summary["scenario_ids"]),
                "candidate_dir": str(candidate_dir),
                "packaged_mesh": str(mesh_dest),
                "active_objective_rank": score.get("active_objective_rank"),
                "nmr_trend_anomaly_rank": score.get("nmr_trend_anomaly_rank"),
                "ert_mae_rank": score.get("ert_mae_rank"),
                "taupe_mae_rank": score.get("taupe_mae_rank"),
                "mean_rank_all_streams": score.get("mean_rank_all_streams"),
                "worst_rank_all_streams": score.get("worst_rank_all_streams"),
                "current_combined_objective": score.get("current_combined_objective"),
                "direct_permeability_objective": score.get("direct_permeability_objective"),
                "raw_nmr_state_objective": score.get("raw_nmr_state_objective"),
                "nmr_trend_anomaly_combined_objective": score.get("nmr_trend_anomaly_combined_objective"),
                "ert_residual_mae_log10": score.get("ert_residual_mae_log10"),
                "taupe_trend_mae": score.get("taupe_trend_mae"),
                "triangle6_cell_count": field_summary.get("triangle6_cell_count"),
                "positive_definite_cell_count": field_summary.get("positive_definite_cell_count"),
                "log10_k_eigen_min_p50": metrics.get("log10_k_eigen_min", {}).get("p50"),
                "log10_k_eigen_max_p50": metrics.get("log10_k_eigen_max", {}).get("p50"),
                "anisotropy_ratio_p50": metrics.get("k_eigen_ratio", {}).get("p50"),
                "theta_deg_p50": metrics.get("k_theta_deg_rd", {}).get("p50"),
                "porosity_p50": metrics.get("n_rd", {}).get("p50"),
            }
        )

    inventory_csv = output_dir / "conditional_field_candidate_inventory.csv"
    metric_evidence_csv = output_dir / "conditional_field_candidate_metric_evidence.csv"
    summary_json = output_dir / "CONDITIONAL_FIELD_CANDIDATES_SUMMARY.json"
    markdown = output_dir / "CONDITIONAL_FIELD_CANDIDATES.md"
    write_inventory(inventory_csv, inventory_rows)
    pd.DataFrame(all_metric_evidence_rows).to_csv(metric_evidence_csv, index=False)
    selection_stability = (
        "unstable_across_defined_scenarios"
        if int(scenario_summary.get("unique_winner_count", 0) or 0) > 1
        else "stable_across_defined_scenarios"
    )
    summary = {
        "status": "conditional_field_candidate_package_generated",
        "output_dir": str(output_dir),
        "scenario_count": scenario_summary.get("scenario_count"),
        "candidate_count": len(candidate_summaries),
        "unique_winners": scenario_summary.get("unique_winners"),
        "current_run_id": scenario_summary.get("current_run_id"),
        "current_field_winning_scenario_count": scenario_summary.get("current_field_winning_scenario_count"),
        "selection_stability": selection_stability,
        "scenario_final_decision": scenario_summary.get("final_decision"),
        "inventory_csv": str(inventory_csv),
        "metric_evidence_csv": str(metric_evidence_csv),
        "metric_evidence_row_count": len(all_metric_evidence_rows),
        "metric_evidence_missing_row_count": sum(
            1 for row in all_metric_evidence_rows if str(row.get("status", "")).startswith("missing")
        ),
        "summary_json": str(summary_json),
        "markdown": str(markdown),
        "candidates": candidate_summaries,
        "interpretation": [
            "Each package subdirectory is a copied scenario winner with mesh, objective summaries, and field statistics.",
            "The packages are conditional alternatives, not a final all-measurement inversion field.",
            "Selection remains unstable until NMR promotion and ERT/Taupe/RH/other-HM gates are resolved or explicitly excluded.",
        ],
        "source_artifacts": [
            str(args.scenario_summary),
            str(args.scenario_csv),
            str(args.scorecard),
            str(args.nmr_audit),
            str(args.ert_audit),
            str(args.taupe_audit),
        ],
    }
    summary_json.write_text(json.dumps(json_ready(summary), indent=2) + "\n", encoding="utf-8")
    write_markdown(markdown, json_ready(summary))
    return summary


def main() -> None:
    args = parse_args()
    build_package(args)


if __name__ == "__main__":
    main()
