#!/usr/bin/env python3
"""Audit whether permeability likelihood-policy winners have cross-stream evidence.

The likelihood rerank scores materialized permeability fields without running OGS.
This audit joins those direct-permeability policy winners to the executed-run
cross-stream scorecard where possible, so direct-only policy winners are not
promoted as all-measurement candidates.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--policy-winners",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_scenario_rerank_policy_winners.csv"),
    )
    parser.add_argument(
        "--rerank-summary",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_scenario_rerank_summary.json"),
    )
    parser.add_argument(
        "--cross-stream-scorecard",
        type=Path,
        default=Path("inversion_workflow/cross_stream_candidate_scorecard.csv"),
    )
    parser.add_argument(
        "--cross-stream-summary",
        type=Path,
        default=Path("inversion_workflow/cross_stream_candidate_scorecard_summary.json"),
    )
    parser.add_argument(
        "--current-field-summary",
        type=Path,
        default=Path("inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD_SUMMARY.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_winner_cross_stream_audit.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_winner_cross_stream_audit_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_winner_cross_stream_audit.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/permeability_likelihood_policy_audit"),
    )
    return parser.parse_args()


def resolve(repo: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo / path


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, Path):
        return str(value)
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


def fmt(value: Any, digits: int = 6) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if not np.isfinite(number):
        return "n/a"
    if digits == 0:
        if abs(number - round(number)) < 1.0e-9:
            return str(int(round(number)))
        return f"{number:.0f}"
    if abs(number) < 1.0e-5 and number != 0.0:
        return f"{number:.3e}"
    return f"{number:.{digits}g}"


def fmt_decimal(value: Any, digits: int = 1) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if not np.isfinite(number):
        return "n/a"
    text = f"{number:.{digits}f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes"}


def relative(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def path_from_mesh(repo: Path, mesh_text: str) -> Path:
    path = Path(str(mesh_text))
    return path if path.is_absolute() else repo / path


def run_dir_from_mesh(repo: Path, mesh_text: str) -> Path | None:
    mesh = path_from_mesh(repo, mesh_text)
    if mesh.name != "bulk_w_projections.vtu":
        return None
    return mesh.parent


def read_scorecard(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    if "run_id" not in frame.columns:
        return pd.DataFrame()
    return frame


def scorecard_match(
    scorecard: pd.DataFrame,
    *,
    candidate_id: str,
    mesh: str,
    current_run_id: str | None,
) -> tuple[pd.Series | None, str | None, list[str]]:
    candidates: list[str] = []
    if candidate_id == "current_permeability_field/current_best" and current_run_id:
        candidates.append(current_run_id)
    candidates.append(candidate_id)
    candidates.append(candidate_id.split("/")[-1])
    mesh_path = Path(str(mesh))
    if "runs" in mesh_path.parts:
        candidates.append(mesh_path.parent.name)
        try:
            index = mesh_path.parts.index("runs")
            candidates.append("/".join(mesh_path.parts[index + 1 : -1]))
        except ValueError:
            pass
    seen: list[str] = []
    for item in candidates:
        if item and item not in seen:
            seen.append(item)
    if scorecard.empty:
        return None, None, seen
    for item in seen:
        match = scorecard[scorecard["run_id"].astype(str).eq(item)]
        if not match.empty:
            return match.iloc[0], item, seen
    return None, None, seen


def file_status(run_dir: Path | None, filename: str) -> bool:
    return bool(run_dir and (run_dir / filename).exists())


def execution_status(run_dir: Path | None) -> str:
    if run_dir is None:
        return "no_run_directory"
    path = run_dir / "OGS_EXECUTION_STATUS.json"
    if not path.exists():
        return "no_ogs_execution_record"
    status = read_json(path)
    if status.get("returncode") == 0 and not status.get("dry_run", False):
        return "ogs_executed_successfully"
    if status.get("dry_run", False):
        return "dry_run_only"
    return f"ogs_execution_record_returncode_{status.get('returncode')}"


def add_scorecard_columns(row: dict[str, Any], score_row: pd.Series | None, current_row: pd.Series | None) -> None:
    columns = [
        "current_combined_objective",
        "direct_permeability_objective",
        "label_bias_combined_objective",
        "trend_anomaly_combined_objective",
        "ert_residual_mae_log10",
        "taupe_trend_mae",
        "active_objective_rank",
        "nmr_label_bias_rank",
        "nmr_trend_anomaly_rank",
        "ert_mae_rank",
        "taupe_mae_rank",
        "mean_rank_all_streams",
        "mean_rank_diagnostics_only",
        "worst_rank_all_streams",
        "top10_stream_count",
        "top10_diagnostic_stream_count",
        "pareto_all_streams",
        "pareto_diagnostics_only",
    ]
    for column in columns:
        row[column] = math.nan if score_row is None else score_row.get(column, math.nan)
    if score_row is not None and current_row is not None:
        row["delta_active_rank_vs_current_accepted"] = (
            float(score_row.get("active_objective_rank", math.nan))
            - float(current_row.get("active_objective_rank", math.nan))
        )
        row["delta_mean_rank_all_streams_vs_current_accepted"] = (
            float(score_row.get("mean_rank_all_streams", math.nan))
            - float(current_row.get("mean_rank_all_streams", math.nan))
        )
        row["delta_taupe_rank_vs_current_accepted"] = (
            float(score_row.get("taupe_mae_rank", math.nan)) - float(current_row.get("taupe_mae_rank", math.nan))
        )
        row["delta_ert_rank_vs_current_accepted"] = (
            float(score_row.get("ert_mae_rank", math.nan)) - float(current_row.get("ert_mae_rank", math.nan))
        )
        row["delta_nmr_trend_rank_vs_current_accepted"] = (
            float(score_row.get("nmr_trend_anomaly_rank", math.nan))
            - float(current_row.get("nmr_trend_anomaly_rank", math.nan))
        )
    else:
        row["delta_active_rank_vs_current_accepted"] = math.nan
        row["delta_mean_rank_all_streams_vs_current_accepted"] = math.nan
        row["delta_taupe_rank_vs_current_accepted"] = math.nan
        row["delta_ert_rank_vs_current_accepted"] = math.nan
        row["delta_nmr_trend_rank_vs_current_accepted"] = math.nan


def disposition(row: dict[str, Any], current_run_id: str | None) -> str:
    if not row["has_cross_stream_scorecard"]:
        return "direct_only_winner_requires_ogs_before_stream_promotion"
    if row.get("matched_run_id") == current_run_id:
        return "current_accepted_field_with_cross_stream_evidence"
    if bool_value(row.get("winner_in_current_gaussian_best_tie_set")):
        return "executed_direct_tie_representative_not_current_active_preferred"
    return "executed_nondefault_policy_winner_needs_policy_decision_before_promotion"


def build_rows(
    *,
    winners: pd.DataFrame,
    scorecard: pd.DataFrame,
    current_summary: dict[str, Any],
    repo: Path,
) -> pd.DataFrame:
    current_run_id = current_summary.get("run_id")
    current_score_row = None
    if current_run_id and not scorecard.empty:
        current_match = scorecard[scorecard["run_id"].astype(str).eq(str(current_run_id))]
        if not current_match.empty:
            current_score_row = current_match.iloc[0]

    rows: list[dict[str, Any]] = []
    for _, winner in winners.iterrows():
        candidate_id = str(winner["winner_candidate_id"])
        mesh = str(winner["winner_mesh"])
        run_dir = run_dir_from_mesh(repo, mesh)
        if candidate_id == "current_permeability_field/current_best" and current_summary.get("source_run_dir"):
            source_run_dir = Path(str(current_summary["source_run_dir"]))
            run_dir = source_run_dir if source_run_dir.is_absolute() else repo / source_run_dir
        score_row, matched_run_id, candidates = scorecard_match(
            scorecard,
            candidate_id=candidate_id,
            mesh=mesh,
            current_run_id=str(current_run_id) if current_run_id else None,
        )
        row: dict[str, Any] = {
            "policy_id": winner["policy_id"],
            "winner_candidate_id": candidate_id,
            "winner_candidate_family": winner.get("winner_candidate_family", ""),
            "winner_source_kind": winner.get("winner_source_kind", ""),
            "winner_mesh": mesh,
            "winner_objective_like_value": winner.get("winner_objective_like_value", math.nan),
            "winner_rmse_log10": winner.get("winner_rmse_log10", math.nan),
            "current_accepted_rank_under_policy": winner.get("current_accepted_rank", math.nan),
            "winner_in_current_gaussian_best_tie_set": bool_value(
                winner.get("winner_in_current_gaussian_best_tie_set", False)
            ),
            "differs_from_current_gaussian_best_set": bool_value(
                winner.get("differs_from_current_gaussian_best_set", False)
            ),
            "run_dir": "" if run_dir is None else relative(repo, run_dir),
            "matched_run_id": matched_run_id or "",
            "scorecard_match_candidates": ";".join(candidates),
            "has_cross_stream_scorecard": score_row is not None,
            "ogs_execution_status": execution_status(run_dir),
            "has_combined_objective_summary": file_status(run_dir, "combined_objective_summary.json"),
            "has_state_observation_summary": file_status(run_dir, "state_observation_evaluation_summary.json"),
            "has_ert_diagnostic_summary": file_status(run_dir, "ert_resistivity_diagnostic_summary.json"),
            "has_taupe_diagnostic_summary": file_status(run_dir, "taupe_tdr_trend_diagnostic_summary.json"),
        }
        add_scorecard_columns(row, score_row, current_score_row)
        row["cross_stream_disposition"] = disposition(row, str(current_run_id) if current_run_id else None)
        rows.append(row)
    return pd.DataFrame(rows)


def copy_outputs(paths: list[Path], catalogue_dir: Path, repo: Path) -> list[dict[str, str]]:
    derived = catalogue_dir / "derived_files"
    derived.mkdir(parents=True, exist_ok=True)
    copies: list[dict[str, str]] = []
    for source in paths:
        if not source.exists():
            continue
        target = derived / source.name
        shutil.copy2(source, target)
        copies.append(
            {
                "source": os.path.relpath(source.resolve(), repo),
                "catalogue_copy": os.path.relpath(target.resolve(), repo),
            }
        )
    return copies


def write_markdown(path: Path, rows: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# Permeability Likelihood Winner Cross-Stream Audit",
        "",
        "This audit joins the direct-permeability likelihood-policy winners to the executed-run cross-stream scorecard where possible. It does not run OGS and does not change the active likelihood policy.",
        "",
        "## Summary",
        "",
        f"- Policy winner rows: {summary['policy_winner_rows']}",
        f"- Unique winner fields: {summary['unique_winner_count']}",
        f"- Winner rows with cross-stream scorecard evidence: {summary['policy_winner_rows_with_cross_stream_scorecard']}",
        f"- Unique winner fields with cross-stream scorecard evidence: {summary['unique_winners_with_cross_stream_scorecard']}",
        f"- Direct-only winner rows without OGS cross-stream evidence: {summary['direct_only_policy_winner_rows']}",
        f"- Diagnostic winners outside the row-Gaussian best tie set and lacking cross-stream evidence: {summary['outside_tie_direct_only_policy_winner_rows']}",
        f"- Current accepted source run: `{summary['current_accepted_run_id']}`",
        "",
        "## Policy Winner Evidence",
        "",
        "| Policy | Winner | Cross-stream evidence | Active rank | Mean rank | ERT rank | Taupe rank | NMR trend rank | Disposition |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for _, row in rows.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["policy_id"]),
                    f"`{row['winner_candidate_id']}`",
                    "`yes`" if bool_value(row["has_cross_stream_scorecard"]) else "`no`",
                    fmt(row.get("active_objective_rank"), 0),
                    fmt_decimal(row.get("mean_rank_all_streams"), 1),
                    fmt(row.get("ert_mae_rank"), 0),
                    fmt(row.get("taupe_mae_rank"), 0),
                    fmt(row.get("nmr_trend_anomaly_rank"), 0),
                    str(row["cross_stream_disposition"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- The direct likelihood rerank scored {summary['rerank_candidate_fields_scored']} materialized fields, but only {summary['unique_winners_with_cross_stream_scorecard']} unique policy-winner fields currently have executed-run cross-stream scorecard evidence.",
            f"- The active row-Gaussian representative selected by candidate-id sorting has active-objective rank {fmt(summary['row_gaussian_representative_active_rank'], 0)} and mean all-stream rank {fmt_decimal(summary['row_gaussian_representative_mean_rank'], 1)}, while the current accepted field has active-objective rank {fmt(summary['current_accepted_active_rank'], 0)} and mean all-stream rank {fmt_decimal(summary['current_accepted_mean_rank'], 1)}.",
            "- The non-default diagnostic winners outside the active row-Gaussian best tie set are direct-only materialized fields in this audit. They require OGS execution plus state/ERT/Taupe/NMR diagnostics before any all-measurement promotion.",
            "- The current report should therefore keep the rowwise Gaussian default until the likelihood decision is explicit, and should not replace the current accepted field with a direct-only diagnostic winner.",
            "",
            "## Output Files",
            "",
            f"- Audit CSV: `{summary['outputs']['audit_csv']}`",
            f"- Summary JSON: `{summary['outputs']['summary_json']}`",
            f"- Markdown: `{summary['outputs']['markdown']}`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo = Path.cwd()
    winners_path = resolve(repo, args.policy_winners).resolve()
    rerank_summary_path = resolve(repo, args.rerank_summary).resolve()
    scorecard_path = resolve(repo, args.cross_stream_scorecard).resolve()
    scorecard_summary_path = resolve(repo, args.cross_stream_summary).resolve()
    current_summary_path = resolve(repo, args.current_field_summary).resolve()
    output_csv = resolve(repo, args.output_csv).resolve()
    summary_output = resolve(repo, args.summary_output).resolve()
    markdown_output = resolve(repo, args.markdown_output).resolve()
    catalogue_dir = resolve(repo, args.catalogue_dir).resolve()

    winners = pd.read_csv(winners_path)
    rerank_summary = read_json(rerank_summary_path)
    scorecard = read_scorecard(scorecard_path)
    scorecard_summary = read_json(scorecard_summary_path)
    current_summary = read_json(current_summary_path)

    rows = build_rows(winners=winners, scorecard=scorecard, current_summary=current_summary, repo=repo)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    rows.to_csv(output_csv, index=False)

    current_run_id = current_summary.get("run_id")
    current_row = rows[rows["matched_run_id"].astype(str).eq(str(current_run_id))] if current_run_id else pd.DataFrame()
    row_gaussian = rows[rows["policy_id"].astype(str).eq("current_duplicate_weighted_gaussian")]
    direct_only = rows[~rows["has_cross_stream_scorecard"].map(bool_value)]
    outside_tie_direct_only = direct_only[direct_only["differs_from_current_gaussian_best_set"].map(bool_value)]
    summary: dict[str, Any] = {
        "status": "permeability_likelihood_winner_cross_stream_audit_generated",
        "policy_winner_rows": int(rows.shape[0]),
        "unique_winner_count": int(rows["winner_candidate_id"].nunique()),
        "policy_winner_rows_with_cross_stream_scorecard": int(rows["has_cross_stream_scorecard"].map(bool_value).sum()),
        "unique_winners_with_cross_stream_scorecard": int(
            rows[rows["has_cross_stream_scorecard"].map(bool_value)]["winner_candidate_id"].nunique()
        ),
        "direct_only_policy_winner_rows": int(direct_only.shape[0]),
        "outside_tie_direct_only_policy_winner_rows": int(outside_tie_direct_only.shape[0]),
        "current_accepted_run_id": current_run_id,
        "current_accepted_active_rank": None
        if current_row.empty
        else current_row.iloc[0].get("active_objective_rank"),
        "current_accepted_mean_rank": None
        if current_row.empty
        else current_row.iloc[0].get("mean_rank_all_streams"),
        "row_gaussian_representative_run_id": None
        if row_gaussian.empty
        else row_gaussian.iloc[0].get("matched_run_id"),
        "row_gaussian_representative_active_rank": None
        if row_gaussian.empty
        else row_gaussian.iloc[0].get("active_objective_rank"),
        "row_gaussian_representative_mean_rank": None
        if row_gaussian.empty
        else row_gaussian.iloc[0].get("mean_rank_all_streams"),
        "rerank_candidate_fields_scored": rerank_summary.get("candidate_fields_scored"),
        "rerank_current_gaussian_best_tie_count": rerank_summary.get("current_gaussian_best_tie_count"),
        "rerank_alt_policy_winners_outside_tie_set": rerank_summary.get(
            "alternate_policy_winner_outside_current_gaussian_best_set_count"
        ),
        "cross_stream_joined_run_count": scorecard_summary.get("joined_run_count"),
        "cross_stream_best_mean_rank_run": scorecard_summary.get("stream_winners", {})
        .get("mean_rank_all_streams", {})
        .get("run_id"),
        "disposition_counts": rows["cross_stream_disposition"].value_counts().sort_index().to_dict(),
        "outputs": {
            "audit_csv": relative(repo, output_csv),
            "summary_json": relative(repo, summary_output),
            "markdown": relative(repo, markdown_output),
        },
        "source_artifacts": [
            relative(repo, winners_path),
            relative(repo, rerank_summary_path),
            relative(repo, scorecard_path),
            relative(repo, scorecard_summary_path),
            relative(repo, current_summary_path),
        ],
        "notes": [
            "No OGS execution is performed by this audit.",
            "A policy winner without a cross-stream scorecard row is a direct-field candidate only.",
            "Current accepted field scorecard evidence is matched through CURRENT_PERMEABILITY_FIELD_SUMMARY.source run_id.",
        ],
    }
    summary_output.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(markdown_output, rows, summary)
    summary["catalogue_copies"] = copy_outputs([output_csv, summary_output, markdown_output], catalogue_dir, repo)
    summary_output.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(markdown_output, rows, summary)
    copy_outputs([summary_output, markdown_output], catalogue_dir, repo)

    print(f"policy winner rows: {rows.shape[0]}")
    print(f"unique winners: {rows['winner_candidate_id'].nunique()}")
    print(f"rows with cross-stream evidence: {summary['policy_winner_rows_with_cross_stream_scorecard']}")
    print(f"direct-only rows: {summary['direct_only_policy_winner_rows']}")
    print(f"wrote {output_csv}")
    print(f"wrote {summary_output}")
    print(f"wrote {markdown_output}")


if __name__ == "__main__":
    main()
