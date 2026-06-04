#!/usr/bin/env python3
"""Plan the next OGS candidate batch from executed combined-objective evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate-table",
        type=Path,
        default=Path("inversion_workflow/runs/smooth_permeability_candidate_search/smooth_fit_results.csv"),
        help="Primary table of available smooth permeability candidate fields.",
    )
    parser.add_argument(
        "--extra-candidate-table",
        type=Path,
        action="append",
        default=[
            Path("inversion_workflow/runs/local_refinement_permeability_candidate_search/smooth_fit_results.csv"),
            Path("inversion_workflow/runs/continuous_bayesian_candidate_plan/continuous_direct_candidate_scores.csv"),
            Path("inversion_workflow/runs/lower_support_continuous_candidate_plan/continuous_direct_candidate_scores.csv"),
        ],
        help="Optional additional candidate table. May be repeated.",
    )
    parser.add_argument(
        "--executed-results",
        type=Path,
        default=Path("inversion_workflow/runs/regularized_ogs_candidate_set/regularized_ogs_candidate_set_results.csv"),
        help="Executed regularized OGS candidate-set result table with combined objective values.",
    )
    parser.add_argument(
        "--adaptive-search-results",
        type=Path,
        default=Path("inversion_workflow/runs/adaptive_combined_candidate_search/inversion_candidate_search_results.csv"),
        help="Optional executed adaptive search result table with combined objective values.",
    )
    parser.add_argument(
        "--local-refinement-results",
        type=Path,
        default=Path("inversion_workflow/runs/local_refinement_candidate_search/inversion_candidate_search_results.csv"),
        help="Optional executed local-refinement search result table with combined objective values.",
    )
    parser.add_argument(
        "--local-bracketing-results",
        type=Path,
        default=Path("inversion_workflow/runs/local_bracketing_candidate_search/inversion_candidate_search_results.csv"),
        help="Optional executed local-bracketing search result table with combined objective values.",
    )
    parser.add_argument(
        "--optimizer-search-results",
        type=Path,
        default=Path("inversion_workflow/runs/optimizer_candidate_search/inversion_candidate_search_results.csv"),
        help="Optional executed optimizer-proposed search result table with combined objective values.",
    )
    parser.add_argument(
        "--continuous-search-results",
        type=Path,
        default=Path("inversion_workflow/runs/continuous_candidate_search/inversion_candidate_search_results.csv"),
        help="Optional executed continuous-proposal search result table with combined objective values.",
    )
    parser.add_argument(
        "--lower-support-continuous-search-results",
        type=Path,
        default=Path("inversion_workflow/runs/lower_support_continuous_candidate_search/inversion_candidate_search_results.csv"),
        help="Optional executed lower-support continuous-proposal search result table with combined objective values.",
    )
    parser.add_argument(
        "--additional-executed-results",
        type=Path,
        action="append",
        default=[Path("inversion_workflow/runs/continuous_inversion_loop/lower_support_cumulative_search_results.csv")],
        help=(
            "Additional executed search result table with combined objective values. "
            "May be repeated; missing paths are ignored."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/runs/adaptive_combined_candidate_plan"),
    )
    parser.add_argument("--max-proposals", type=int, default=6)
    parser.add_argument("--direct-weight", type=float, default=1.0)
    parser.add_argument("--update-weight", type=float, default=0.25)
    parser.add_argument("--diversity-weight", type=float, default=0.20)
    parser.add_argument("--best-proximity-weight", type=float, default=0.35)
    parser.add_argument(
        "--state-flat-relative-threshold",
        type=float,
        default=0.001,
        help="Relative state-objective range below which the state term is treated as flat over executed candidates.",
    )
    return parser.parse_args()


def norm01(values: pd.Series, lower_is_better: bool = True) -> pd.Series:
    data = pd.to_numeric(values, errors="coerce").astype(float)
    finite = np.isfinite(data)
    if not finite.any():
        return pd.Series(np.zeros(len(data)), index=values.index)
    lo = float(data[finite].min())
    hi = float(data[finite].max())
    if np.isclose(hi, lo):
        scaled = pd.Series(np.zeros(len(data)), index=values.index)
    else:
        scaled = (data - lo) / (hi - lo)
    scaled = scaled.fillna(1.0)
    return scaled if lower_is_better else 1.0 - scaled


def nearest_executed_distance(candidates: pd.DataFrame, executed: pd.DataFrame) -> pd.Series:
    if executed.empty:
        return pd.Series(np.ones(candidates.shape[0]), index=candidates.index)
    cols = ["length_scale_m", "shift_scale", "sum_squared_applied_log10_shift_all_cells"]
    matrix = candidates[cols].astype(float).copy()
    executed_matrix = executed[cols].astype(float).copy()
    for col in cols:
        fill_value = float(matrix[col].median()) if matrix[col].notna().any() else 0.0
        matrix[col] = matrix[col].fillna(fill_value)
        executed_matrix[col] = executed_matrix[col].fillna(fill_value)
        lo = float(matrix[col].min())
        hi = float(matrix[col].max())
        scale = hi - lo if not np.isclose(hi, lo) else 1.0
        matrix[col] = (matrix[col] - lo) / scale
        executed_matrix[col] = (executed_matrix[col] - lo) / scale
    distances = []
    executed_values = executed_matrix.to_numpy(dtype=float)
    for row in matrix.to_numpy(dtype=float):
        distances.append(float(np.linalg.norm(executed_values - row, axis=1).min()))
    output = pd.Series(distances, index=candidates.index)
    max_distance = float(output.max()) if np.isfinite(output).any() else 1.0
    return output / (max_distance if max_distance > 0.0 else 1.0)


def distance_to_reference(candidates: pd.DataFrame, reference: pd.Series | None) -> pd.Series:
    if reference is None or reference.empty:
        return pd.Series(np.ones(candidates.shape[0]), index=candidates.index)
    cols = ["length_scale_m", "shift_scale", "sum_squared_applied_log10_shift_all_cells"]
    matrix = candidates[cols].astype(float).copy()
    ref = reference[cols].astype(float).copy()
    for col in cols:
        fill_value = float(matrix[col].median()) if matrix[col].notna().any() else 0.0
        matrix[col] = matrix[col].fillna(fill_value)
        if pd.isna(ref[col]):
            ref[col] = fill_value
        lo = float(matrix[col].min())
        hi = float(matrix[col].max())
        scale = hi - lo if not np.isclose(hi, lo) else 1.0
        matrix[col] = (matrix[col] - lo) / scale
        ref[col] = (float(ref[col]) - lo) / scale
    output = pd.Series(
        np.linalg.norm(matrix.to_numpy(dtype=float) - ref.to_numpy(dtype=float), axis=1),
        index=candidates.index,
    )
    max_distance = float(output.max()) if np.isfinite(output).any() else 1.0
    return output / (max_distance if max_distance > 0.0 else 1.0)


def normalize_executed_table(path: Path, source_label: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    if frame.empty:
        return pd.DataFrame()
    frame = frame.copy()
    if "candidate_id" not in frame.columns and "source_candidate_id" in frame.columns:
        frame["candidate_id"] = frame["source_candidate_id"]
    required = ["candidate_id", "total_active_objective_value", "direct_permeability_objective"]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"executed result table {path} is missing required columns: {missing}")
    frame["executed_source"] = source_label
    frame["executed_results_path"] = str(path)
    keep = [
        "candidate_id",
        "run_id",
        "run_dir",
        "summary_json",
        "executed_source",
        "executed_results_path",
        "ogs_mode",
        "active_component_count",
        "total_active_objective_value",
        "direct_permeability_objective",
        "direct_permeability_weighted_rmse_log10",
        "state_active_objective_rows",
        "run_input_audit_status",
        "release_gate_status",
        "mesh_override",
        "source_length_scale_m",
        "source_shift_scale",
        "source_affected_cells",
        "source_direct_objective",
        "source_weighted_rmse_log10",
    ]
    existing = [column for column in keep if column in frame.columns]
    output = frame[existing].copy()
    output["candidate_id"] = output["candidate_id"].astype(str)
    output["total_active_objective_value"] = pd.to_numeric(
        output["total_active_objective_value"], errors="coerce"
    )
    output["direct_permeability_objective"] = pd.to_numeric(
        output["direct_permeability_objective"], errors="coerce"
    )
    output["state_objective_value"] = (
        output["total_active_objective_value"] - output["direct_permeability_objective"]
    )
    return output


def read_candidate_tables(primary: Path, extras: list[Path] | None) -> tuple[pd.DataFrame, list[str]]:
    paths = [primary] + [path for path in (extras or []) if path != primary]
    frames: list[pd.DataFrame] = []
    used_paths: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        if frame.empty:
            continue
        frame = frame.copy()
        frame["candidate_table_source"] = str(path)
        frames.append(frame)
        used_paths.append(str(path))
    if not frames:
        raise SystemExit(f"no candidate tables found, primary was: {primary}")
    combined = pd.concat(frames, ignore_index=True)
    combined["objective_value"] = pd.to_numeric(combined["objective_value"], errors="coerce")
    combined = (
        combined.sort_values(["candidate_id", "objective_value", "candidate_table_source"])
        .drop_duplicates("candidate_id", keep="first")
        .reset_index(drop=True)
    )
    return combined, used_paths


def executed_fallback_candidate_rows(executed: pd.DataFrame, existing_ids: set[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if executed.empty:
        return pd.DataFrame()
    for _, row in executed.iterrows():
        candidate_id = str(row.get("candidate_id", ""))
        if not candidate_id or candidate_id in existing_ids:
            continue
        direct_objective = row.get("source_direct_objective", row.get("direct_permeability_objective", np.nan))
        direct_rmse = row.get(
            "source_weighted_rmse_log10",
            row.get("direct_permeability_weighted_rmse_log10", np.nan),
        )
        rows.append(
            {
                "rank_by_objective": np.nan,
                "candidate_id": candidate_id,
                "length_scale_m": row.get("source_length_scale_m", np.nan),
                "shift_scale": row.get("source_shift_scale", np.nan),
                "cutoff_factor": 3.0,
                "affected_cells": row.get("source_affected_cells", np.nan),
                "objective_value": direct_objective,
                "weighted_rmse_log10": direct_rmse,
                "mesh": row.get("mesh_override", ""),
                "summary_json": row.get("summary_json", ""),
                "candidate_table_source": str(row.get("executed_results_path", "")) + "#executed_feature_fallback",
                "fallback_candidate_features": True,
                "fallback_feature_reason": (
                    "candidate was executed but its original proposal table is no longer present; "
                    "features were reconstructed from the executed search result"
                ),
            }
        )
    return pd.DataFrame(rows)


def reason(row: pd.Series, best_unexecuted_id: str, executed_lengths: set[float], state_flat: bool) -> str:
    if row["candidate_id"] == best_unexecuted_id:
        if state_flat:
            return "best unexecuted direct-fit candidate; tests whether broader support changes the NMR state term"
        return "best remaining direct-fit candidate, kept as a bracket after broader supports worsened the NMR state term"
    length = float(row["length_scale_m"])
    shift = float(row["shift_scale"])
    if not state_flat and length in executed_lengths and shift <= 0.75:
        return "local damping refinement at an already tested support after the state term showed sensitivity"
    if not state_flat and length not in executed_lengths and shift < 0.75:
        return "tests stronger damping while avoiding another full-shift broad-support jump"
    if length not in executed_lengths and np.isclose(shift, 1.0):
        return "broadens the full-shift support beyond the already executed fields"
    if length not in executed_lengths and np.isclose(shift, 0.75):
        return "tests the moderate damping scenario at a broader spatial support"
    if length not in executed_lengths and np.isclose(shift, 0.5):
        return "tests whether stronger regularization at broader support changes the state term"
    return "surrogate-ranked unexecuted candidate balancing direct fit, update size, and diversity"


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
    if value is pd.NA or value is None:
        return None
    return value


def write_markdown(path: Path, proposals: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# Adaptive Combined Candidate Plan",
        "",
        "This is the next-batch planner for moving from a fixed three-candidate OGS",
        "comparison toward an optimizer/sampler workflow.  It does not execute OGS by",
        "itself; it ranks unexecuted candidate fields using the current executed",
        "combined-objective evidence and writes a candidate table that can be passed to",
        "`run_inversion_candidate_search.py --ogs-mode execute`.",
        "",
        "## Executed Evidence",
        "",
        f"- Executed candidates: {summary['executed_candidate_count']}",
        f"- Best executed candidate: `{summary['best_executed_candidate']}`",
        f"- Best executed combined objective: {summary['best_executed_combined_objective']:.2f}",
        f"- Executed state objective range: {summary['executed_state_objective_min']:.2f} to {summary['executed_state_objective_max']:.2f}",
        f"- State term treated as flat over executed candidates: `{summary['state_objective_flat_over_executed_candidates']}`",
        f"- Proposal mode: `{summary['proposal_mode']}`",
        "",
        "## Proposed Next Batch",
        "",
        "| Rank | Candidate | Length [m] | Shift | Direct objective | Expected combined | Update SSE | Diversity | Reason |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for _, row in proposals.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row["proposal_rank"])),
                    f"`{row['candidate_id']}`",
                    f"{float(row['length_scale_m']):.3f}",
                    f"{float(row['shift_scale']):.2f}",
                    f"{float(row['objective_value']):.2f}",
                    f"{float(row['surrogate_expected_combined_objective']):.2f}",
                    f"{float(row['sum_squared_applied_log10_shift_all_cells']):.2f}",
                    f"{float(row['nearest_executed_distance_norm']):.2f}",
                    str(row["proposal_reason"]).replace("|", "/"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Execution Command",
            "",
            "Use the emitted `next_candidate_batch.csv` as the candidate table for the",
            "existing candidate-search harness.  Example:",
            "",
            "```bash",
            "python inversion_workflow/scripts/run_inversion_candidate_search.py \\",
            "  --candidate-table inversion_workflow/runs/adaptive_combined_candidate_plan/next_candidate_batch.csv \\",
            "  --sort-column proposal_rank \\",
            "  --max-candidates 3 \\",
            "  --run-id-prefix adaptive_combined \\",
            "  --ogs-mode execute \\",
            "  --sif /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/apptainer_ogs6.5.4.sif \\",
            "  --docker-apptainer-image ghcr.io/apptainer/apptainer:latest \\",
            "  --docker-workspace-root /home/ber0061/Repositories/gesa_mails \\",
            "  --ogs-timeout-s 7200 \\",
            "  --overwrite",
            "```",
            "",
            "## Interpretation",
            "",
        ]
    )
    if summary["state_objective_flat_over_executed_candidates"]:
        lines.extend(
            [
                "- The executed state objective remains nearly flat; the next batch therefore",
                "  rewards diversity around the unexecuted direct-fit candidates.",
            ]
        )
    else:
        lines.extend(
            [
                "- The executed state objective is no longer flat across the executed batches.",
                "  Broader supports and local bracketing changed the sampled NMR state objective,",
                "  so the next batch remains a local evidence-gathering step rather than another",
                "  diversity-only expansion.",
            ]
        )
    lines.extend(
        [
            "- The surrogate expected combined objective is direct objective plus the",
            "  median executed state objective. It is only a planning score, not an OGS",
            "  result.",
            "- After the next executed batch, regenerate this plan so proposals respond to",
            "  actual state-objective changes.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    candidates, candidate_table_paths = read_candidate_tables(args.candidate_table, args.extra_candidate_table)
    executed_tables = [
        normalize_executed_table(args.executed_results, "regularized_candidate_set"),
        normalize_executed_table(args.adaptive_search_results, "adaptive_candidate_search"),
        normalize_executed_table(args.local_refinement_results, "local_refinement_search"),
        normalize_executed_table(args.local_bracketing_results, "local_bracketing_search"),
        normalize_executed_table(args.optimizer_search_results, "optimizer_candidate_search"),
        normalize_executed_table(args.continuous_search_results, "continuous_candidate_search"),
        normalize_executed_table(args.lower_support_continuous_search_results, "lower_support_continuous_search"),
        *[
            normalize_executed_table(path, f"additional_executed_results_{index + 1}")
            for index, path in enumerate(args.additional_executed_results or [])
        ],
    ]
    executed = pd.concat([frame for frame in executed_tables if not frame.empty], ignore_index=True)
    if candidates.empty:
        raise SystemExit(f"candidate table is empty: {args.candidate_table}")

    if not executed.empty:
        executed = (
            executed.sort_values("total_active_objective_value")
            .drop_duplicates("candidate_id", keep="first")
            .reset_index(drop=True)
        )
    executed_ids = set(executed.get("candidate_id", pd.Series(dtype=str)).astype(str))
    executed_state = pd.to_numeric(executed.get("state_objective_value", pd.Series(dtype=float)), errors="coerce")

    candidates = candidates.copy()
    fallback_candidates = executed_fallback_candidate_rows(
        executed,
        set(candidates["candidate_id"].astype(str)),
    )
    fallback_candidate_count = int(fallback_candidates.shape[0])
    if not fallback_candidates.empty:
        candidates = pd.concat([candidates, fallback_candidates], ignore_index=True, sort=False)
        candidate_table_paths.append("executed_search_result_feature_fallback_rows")
    for column in [
        "sum_squared_applied_log10_shift_all_cells",
        "mean_abs_applied_log10_shift_affected",
        "rms_applied_log10_shift_affected",
        "applied_log10_shift_min",
        "applied_log10_shift_max",
        "objective_value",
        "weighted_rmse_log10",
        "length_scale_m",
        "shift_scale",
        "affected_cells",
        "cutoff_factor",
    ]:
        if column in candidates.columns:
            candidates[column] = pd.to_numeric(candidates[column], errors="coerce")
    candidates["is_executed_ogs_candidate"] = candidates["candidate_id"].astype(str).isin(executed_ids)
    candidates["direct_objective_norm"] = norm01(candidates["objective_value"], lower_is_better=True)
    candidates["update_complexity_norm"] = norm01(
        candidates["sum_squared_applied_log10_shift_all_cells"], lower_is_better=True
    )
    candidates["nearest_executed_distance_norm"] = nearest_executed_distance(
        candidates,
        candidates[candidates["is_executed_ogs_candidate"]],
    )
    best_executed = (
        executed.sort_values("total_active_objective_value").iloc[0]
        if not executed.empty and "total_active_objective_value" in executed.columns
        else None
    )
    best_executed_candidate = str(best_executed["candidate_id"]) if best_executed is not None else None
    best_executed_candidate_row = None
    if best_executed_candidate is not None:
        best_rows = candidates[candidates["candidate_id"].astype(str) == best_executed_candidate]
        if not best_rows.empty:
            best_executed_candidate_row = best_rows.iloc[0]
    candidates["best_executed_distance_norm"] = distance_to_reference(candidates, best_executed_candidate_row)

    median_state = float(executed_state.dropna().median()) if executed_state.notna().any() else 0.0
    state_min = float(executed_state.dropna().min()) if executed_state.notna().any() else 0.0
    state_max = float(executed_state.dropna().max()) if executed_state.notna().any() else 0.0
    state_mean = float(executed_state.dropna().mean()) if executed_state.notna().any() else 0.0
    state_range = state_max - state_min
    state_flat = bool(
        executed_state.notna().sum() >= 2
        and state_mean != 0.0
        and abs(state_range / state_mean) <= args.state_flat_relative_threshold
    )
    candidates["surrogate_expected_state_objective"] = median_state
    candidates["surrogate_expected_combined_objective"] = candidates["objective_value"].astype(float) + median_state
    if state_flat:
        proposal_mode = "diversity_after_flat_state_term"
        candidates["proposal_score"] = (
            args.direct_weight * candidates["direct_objective_norm"]
            + args.update_weight * candidates["update_complexity_norm"]
            - args.diversity_weight * candidates["nearest_executed_distance_norm"]
        )
    else:
        proposal_mode = "local_refinement_after_state_response"
        candidates["proposal_score"] = (
            args.direct_weight * candidates["direct_objective_norm"]
            + args.update_weight * candidates["update_complexity_norm"]
            + args.best_proximity_weight * candidates["best_executed_distance_norm"]
            - 0.05 * candidates["nearest_executed_distance_norm"]
        )

    unexecuted = candidates[~candidates["is_executed_ogs_candidate"]].copy()
    if unexecuted.empty:
        raise SystemExit("all candidates have already been executed")
    best_unexecuted_id = str(unexecuted.sort_values("objective_value").iloc[0]["candidate_id"])
    executed_lengths = {float(v) for v in candidates.loc[candidates["is_executed_ogs_candidate"], "length_scale_m"]}
    unexecuted["proposal_reason"] = unexecuted.apply(
        lambda row: reason(row, best_unexecuted_id, executed_lengths, state_flat), axis=1
    )
    proposals = (
        unexecuted.sort_values(["proposal_score", "objective_value", "candidate_id"])
        .head(args.max_proposals)
        .reset_index(drop=True)
    )
    proposals["proposal_rank"] = range(1, proposals.shape[0] + 1)

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    all_scored_path = output_dir / "all_candidate_scores.csv"
    proposals_path = output_dir / "next_candidate_batch.csv"
    executed_evidence_path = output_dir / "executed_candidate_evidence.csv"
    summary_path = output_dir / "ADAPTIVE_COMBINED_CANDIDATE_PLAN.json"
    md_path = output_dir / "ADAPTIVE_COMBINED_CANDIDATE_PLAN.md"
    candidates.sort_values(["is_executed_ogs_candidate", "proposal_score", "objective_value"]).to_csv(
        all_scored_path, index=False
    )
    proposals.to_csv(proposals_path, index=False)
    executed.to_csv(executed_evidence_path, index=False)

    best_executed_objective = (
        float(executed["total_active_objective_value"].min())
        if not executed.empty and "total_active_objective_value" in executed.columns
        else None
    )
    summary = {
        "candidate_table": str(args.candidate_table),
        "extra_candidate_tables": [str(path) for path in args.extra_candidate_table or []],
        "candidate_tables_used": candidate_table_paths,
        "executed_results": str(args.executed_results),
        "adaptive_search_results": str(args.adaptive_search_results),
        "local_refinement_results": str(args.local_refinement_results),
        "local_bracketing_results": str(args.local_bracketing_results),
        "optimizer_search_results": str(args.optimizer_search_results),
        "continuous_search_results": str(args.continuous_search_results),
        "lower_support_continuous_search_results": str(args.lower_support_continuous_search_results),
        "additional_executed_results": [str(path) for path in args.additional_executed_results or []],
        "executed_result_tables": [
            str(path)
            for path in [
                args.executed_results,
                args.adaptive_search_results,
                args.local_refinement_results,
                args.local_bracketing_results,
                args.optimizer_search_results,
                args.continuous_search_results,
                args.lower_support_continuous_search_results,
                *(args.additional_executed_results or []),
            ]
            if path.exists()
        ],
        "output_dir": str(output_dir),
        "all_candidate_scores_csv": str(all_scored_path),
        "next_candidate_batch_csv": str(proposals_path),
        "executed_candidate_evidence_csv": str(executed_evidence_path),
        "summary_markdown": str(md_path),
        "candidate_count": int(candidates.shape[0]),
        "fallback_candidate_feature_count": fallback_candidate_count,
        "executed_candidate_count": int(len(executed_ids)),
        "proposed_candidate_count": int(proposals.shape[0]),
        "best_executed_candidate": best_executed_candidate,
        "best_executed_combined_objective": best_executed_objective,
        "executed_state_objective_min": state_min,
        "executed_state_objective_max": state_max,
        "executed_state_objective_range": state_range,
        "executed_state_objective_median": median_state,
        "state_flat_relative_threshold": args.state_flat_relative_threshold,
        "state_objective_flat_over_first_batch": state_flat,
        "state_objective_flat_over_executed_candidates": state_flat,
        "proposal_mode": proposal_mode,
        "proposal_weights": {
            "direct_weight": args.direct_weight,
            "update_weight": args.update_weight,
            "diversity_weight": args.diversity_weight,
            "best_proximity_weight": args.best_proximity_weight,
        },
        "top_proposals": json_ready(proposals.to_dict(orient="records")),
        "notes": [
            "This is a planning artifact, not an OGS result.",
            "The surrogate combined objective is direct objective plus the median executed state objective.",
            "Execute proposed candidates with run_inversion_candidate_search.py before using them as evidence.",
        ],
    }
    summary_path.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(md_path, proposals, summary)
    print(f"wrote {all_scored_path}")
    print(f"wrote {proposals_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {md_path}")
    print(f"top proposal: {proposals.iloc[0]['candidate_id']}")


if __name__ == "__main__":
    main()
