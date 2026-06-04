#!/usr/bin/env python3
"""Rerank materialized permeability fields under alternative likelihood policies.

This audit is intentionally no-OGS: it only reads existing VTU fields or cached
direct-permeability row evaluations, then recomputes objective-like scores under
the likelihood policies used in the policy decision request.
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

from evaluate_permeability_targets import evaluate_targets


POLICIES: tuple[tuple[str, str], ...] = (
    (
        "current_duplicate_weighted_gaussian",
        "Active default: duplicate-weighted Gaussian row residuals in log10(k), sigma=0.5.",
    ),
    (
        "capped_gaussian_abs1_log10",
        "Diagnostic: row Gaussian loss capped at one log10 unit.",
    ),
    (
        "huber_delta_2sigma",
        "Diagnostic: row Huber loss with transition at two normalized sigma.",
    ),
    (
        "student_t_nu4",
        "Diagnostic: row Student-t negative log kernel with nu=4.",
    ),
    (
        "support_cell_weighted_mean_unit_gaussian",
        "Diagnostic: collapse rows sharing one model support cell to weighted mean observation, unit group weight.",
    ),
    (
        "support_cell_weighted_median_unit_gaussian",
        "Diagnostic: collapse rows sharing one model support cell to weighted median observation, unit group weight.",
    ),
    (
        "configured_scalar_inside_only_gaussian",
        "Diagnostic: score only rows whose current-field audit marked them inside configured scalar bounds.",
    ),
)

REQUIRED_EVALUATION_COLUMNS = {
    "observation_id",
    "used_in_objective",
    "observed_log10_permeability_m2",
    "predicted_log10_permeability_m2",
    "log10_residual_pred_minus_obs",
    "objective_weight",
    "selected_cell_ids",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=Path("inversion_workflow/runs"),
        help="Root searched recursively for bulk_w_projections.vtu candidate fields.",
    )
    parser.add_argument(
        "--current-field",
        type=Path,
        default=Path("inversion_workflow/current_permeability_field/current_best_bulk_w_projections.vtu"),
        help="Accepted current field to include explicitly even though it is outside the runs tree.",
    )
    parser.add_argument(
        "--targets",
        type=Path,
        default=Path("inversion_workflow/processed_observations/permeability_observation_targets.csv"),
    )
    parser.add_argument(
        "--target-cells",
        type=Path,
        default=Path("inversion_workflow/processed_observations/permeability_observation_cells.csv"),
    )
    parser.add_argument(
        "--residual-audit",
        type=Path,
        default=Path("inversion_workflow/permeability_residual_conflict_audit.csv"),
        help="Current-field residual audit used only for configured-scalar row status annotations.",
    )
    parser.add_argument("--field-name", default="k_i_rd")
    parser.add_argument("--log10-sigma", type=float, default=0.5)
    parser.add_argument("--huber-delta-normalized", type=float, default=2.0)
    parser.add_argument("--student-t-nu", type=float, default=4.0)
    parser.add_argument("--cap-abs-log10", type=float, default=1.0)
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=0,
        help="Optional development cap; 0 means evaluate every discovered candidate.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore same-directory permeability_fit_evaluation.csv files and evaluate meshes directly.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_scenario_rerank.csv"),
    )
    parser.add_argument(
        "--winner-output",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_scenario_rerank_policy_winners.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_scenario_rerank_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/permeability_likelihood_scenario_rerank.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/permeability_likelihood_policy_audit"),
    )
    return parser.parse_args()


def resolve(repo: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo / path


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


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes"}


def bool_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(False, index=frame.index)
    return frame[column].map(bool_value)


def first_cell_id(value: Any) -> int | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    first = text.split(";")[0].split(",")[0].strip()
    try:
        number = int(float(first))
    except ValueError:
        return None
    return number if number >= 0 else None


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0.0)
    if not mask.any():
        return math.nan
    values = values[mask]
    weights = weights[mask]
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cumulative = np.cumsum(weights) / float(np.sum(weights))
    return float(values[np.searchsorted(cumulative, 0.5, side="left")])


def weighted_average(values: np.ndarray, weights: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0.0)
    if not mask.any():
        return math.nan
    return float(np.average(values[mask], weights=weights[mask]))


def weighted_rmse(residuals: np.ndarray, weights: np.ndarray) -> float:
    residuals = np.asarray(residuals, dtype=float)
    weights = np.asarray(weights, dtype=float)
    mask = np.isfinite(residuals) & np.isfinite(weights) & (weights > 0.0)
    if not mask.any():
        return math.nan
    return float(math.sqrt(np.average(residuals[mask] ** 2, weights=weights[mask])))


def weighted_mae(residuals: np.ndarray, weights: np.ndarray) -> float:
    residuals = np.asarray(residuals, dtype=float)
    weights = np.asarray(weights, dtype=float)
    mask = np.isfinite(residuals) & np.isfinite(weights) & (weights > 0.0)
    if not mask.any():
        return math.nan
    return float(np.average(np.abs(residuals[mask]), weights=weights[mask]))


def gaussian_loss(z: np.ndarray) -> np.ndarray:
    return 0.5 * z**2


def capped_gaussian_loss(z: np.ndarray, cap_z: float) -> np.ndarray:
    return 0.5 * np.minimum(z**2, cap_z**2)


def huber_loss(z: np.ndarray, delta: float) -> np.ndarray:
    abs_z = np.abs(z)
    return np.where(abs_z <= delta, 0.5 * z**2, delta * (abs_z - 0.5 * delta))


def student_t_loss(z: np.ndarray, nu: float) -> np.ndarray:
    return 0.5 * (nu + 1.0) * np.log1p((z**2) / nu)


def relative(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def discover_candidates(repo: Path, runs_root: Path, current_field: Path, max_candidates: int) -> list[dict[str, Any]]:
    candidates: list[Path] = []
    if current_field.exists():
        candidates.append(current_field.resolve())
    candidates.extend(sorted(path.resolve() for path in runs_root.rglob("bulk_w_projections.vtu")))

    seen: set[Path] = set()
    rows: list[dict[str, Any]] = []
    for mesh_path in candidates:
        if mesh_path in seen:
            continue
        seen.add(mesh_path)
        rel_mesh = relative(repo, mesh_path)
        if mesh_path == current_field.resolve():
            candidate_id = "current_permeability_field/current_best"
            family = "current_permeability_field"
            source_kind = "current_accepted_field"
        else:
            parent = mesh_path.parent
            try:
                run_rel = parent.relative_to(runs_root.resolve())
                candidate_id = run_rel.as_posix()
                family = run_rel.parts[0] if run_rel.parts else candidate_id
            except ValueError:
                candidate_id = parent.name
                family = parent.parent.name if parent.parent != parent else parent.name
            source_kind = "materialized_run_field"
        rows.append(
            {
                "candidate_id": candidate_id,
                "candidate_family": family,
                "source_kind": source_kind,
                "mesh_path": str(mesh_path),
                "mesh": rel_mesh,
            }
        )
        if max_candidates > 0 and len(rows) >= max_candidates:
            break
    return rows


def load_status_map(residual_audit: Path) -> dict[str, str]:
    if not residual_audit.exists():
        return {}
    frame = pd.read_csv(residual_audit)
    if "observation_id" not in frame.columns or "configured_scalar_feasibility_status" not in frame.columns:
        return {}
    return {
        str(row["observation_id"]): str(row["configured_scalar_feasibility_status"])
        for _, row in frame.iterrows()
    }


def cached_evaluation_valid(frame: pd.DataFrame) -> bool:
    return REQUIRED_EVALUATION_COLUMNS.issubset(set(frame.columns))


def load_or_evaluate(
    *,
    mesh_path: Path,
    field_name: str,
    targets_path: Path,
    target_cells_path: Path,
    sigma: float,
    use_cache: bool,
) -> tuple[pd.DataFrame, str, str]:
    cached = mesh_path.parent / "permeability_fit_evaluation.csv"
    if use_cache and cached.exists():
        frame = pd.read_csv(cached)
        if cached_evaluation_valid(frame):
            return frame, "cached_csv", str(cached)
    frame, _summary = evaluate_targets(
        mesh_path=mesh_path,
        field_name=field_name,
        targets_path=targets_path,
        target_cells_path=target_cells_path,
        log10_sigma=sigma,
        include_non_usable=True,
    )
    return frame, "evaluated_from_mesh", str(mesh_path)


def active_rows(evaluation: pd.DataFrame, status_map: dict[str, str]) -> pd.DataFrame:
    rows = evaluation.copy()
    for column in [
        "observed_log10_permeability_m2",
        "predicted_log10_permeability_m2",
        "log10_residual_pred_minus_obs",
        "objective_weight",
        "borehole_depth_m",
    ]:
        if column in rows.columns:
            rows[column] = pd.to_numeric(rows[column], errors="coerce")
    rows["configured_scalar_feasibility_status"] = (
        rows["observation_id"].astype(str).map(status_map).fillna("status_unknown_from_current_field_audit")
    )
    rows["primary_cell_id"] = rows["selected_cell_ids"].map(first_cell_id)
    used = bool_series(rows, "used_in_objective")
    finite = (
        np.isfinite(rows["log10_residual_pred_minus_obs"])
        & np.isfinite(rows["observed_log10_permeability_m2"])
        & np.isfinite(rows["predicted_log10_permeability_m2"])
        & np.isfinite(rows["objective_weight"])
        & (rows["objective_weight"] > 0.0)
    )
    return rows[used & finite].copy()


def support_scores(active: pd.DataFrame, sigma: float) -> dict[str, Any]:
    groups: list[dict[str, float]] = []
    grouped = active.dropna(subset=["primary_cell_id"]).groupby("primary_cell_id")
    for _cell_id, group in grouped:
        observed = group["observed_log10_permeability_m2"].to_numpy(dtype=float)
        predicted = group["predicted_log10_permeability_m2"].to_numpy(dtype=float)
        weights = group["objective_weight"].to_numpy(dtype=float)
        predicted_mean = weighted_average(predicted, weights)
        observed_mean = weighted_average(observed, weights)
        observed_median = weighted_median(observed, weights)
        mean_residual = predicted_mean - observed_mean
        median_residual = predicted_mean - observed_median
        groups.append(
            {
                "support_mean_residual_log10": mean_residual,
                "support_median_residual_log10": median_residual,
                "observed_range_log10": float(np.nanmax(observed) - np.nanmin(observed))
                if observed.size
                else math.nan,
            }
        )
    if not groups:
        return {
            "support_group_count": 0,
            "support_observed_range_ge_1_count": 0,
            "objective_support_cell_weighted_mean_unit_gaussian": math.nan,
            "objective_support_cell_weighted_median_unit_gaussian": math.nan,
            "rmse_support_cell_weighted_mean_unit_gaussian": math.nan,
            "rmse_support_cell_weighted_median_unit_gaussian": math.nan,
            "mae_support_cell_weighted_mean_unit_gaussian": math.nan,
            "mae_support_cell_weighted_median_unit_gaussian": math.nan,
            "max_abs_support_cell_weighted_mean_unit_gaussian": math.nan,
            "max_abs_support_cell_weighted_median_unit_gaussian": math.nan,
        }

    group_frame = pd.DataFrame(groups)
    mean_residual = group_frame["support_mean_residual_log10"].to_numpy(dtype=float)
    median_residual = group_frame["support_median_residual_log10"].to_numpy(dtype=float)
    unit_weight = np.ones_like(mean_residual, dtype=float)
    return {
        "support_group_count": int(group_frame.shape[0]),
        "support_observed_range_ge_1_count": int((group_frame["observed_range_log10"] >= 1.0).sum()),
        "objective_support_cell_weighted_mean_unit_gaussian": float(np.nansum(gaussian_loss(mean_residual / sigma))),
        "objective_support_cell_weighted_median_unit_gaussian": float(np.nansum(gaussian_loss(median_residual / sigma))),
        "rmse_support_cell_weighted_mean_unit_gaussian": weighted_rmse(mean_residual, unit_weight),
        "rmse_support_cell_weighted_median_unit_gaussian": weighted_rmse(median_residual, unit_weight),
        "mae_support_cell_weighted_mean_unit_gaussian": weighted_mae(mean_residual, unit_weight),
        "mae_support_cell_weighted_median_unit_gaussian": weighted_mae(median_residual, unit_weight),
        "max_abs_support_cell_weighted_mean_unit_gaussian": float(np.nanmax(np.abs(mean_residual))),
        "max_abs_support_cell_weighted_median_unit_gaussian": float(np.nanmax(np.abs(median_residual))),
    }


def score_candidate(active: pd.DataFrame, sigma: float, cap_abs: float, huber_delta: float, student_nu: float) -> dict[str, Any]:
    residual = active["log10_residual_pred_minus_obs"].to_numpy(dtype=float)
    weights = active["objective_weight"].to_numpy(dtype=float)
    z = residual / sigma
    cap_z = cap_abs / sigma
    inside_mask = active["configured_scalar_feasibility_status"].astype(str).eq(
        "observed_inside_configured_scalar_range"
    )
    inside = active[inside_mask].copy()
    inside_residual = inside["log10_residual_pred_minus_obs"].to_numpy(dtype=float)
    inside_weights = inside["objective_weight"].to_numpy(dtype=float)

    row_losses = weights * gaussian_loss(z)
    scores: dict[str, Any] = {
        "active_row_count": int(active.shape[0]),
        "effective_objective_weight": float(np.sum(weights)),
        "outside_configured_scalar_row_count": int((~inside_mask).sum()),
        "rows_ge_1_log10": int((np.abs(residual) >= 1.0).sum()),
        "rows_ge_2_log10": int((np.abs(residual) >= 2.0).sum()),
        "top_5_current_row_loss_share": top_loss_share(row_losses, 5),
        "top_10_current_row_loss_share": top_loss_share(row_losses, 10),
        "objective_current_duplicate_weighted_gaussian": float(np.sum(row_losses)),
        "objective_capped_gaussian_abs1_log10": float(np.sum(weights * capped_gaussian_loss(z, cap_z))),
        "objective_huber_delta_2sigma": float(np.sum(weights * huber_loss(z, huber_delta))),
        "objective_student_t_nu4": float(np.sum(weights * student_t_loss(z, student_nu))),
        "objective_configured_scalar_inside_only_gaussian": float(
            np.sum(inside_weights * gaussian_loss(inside_residual / sigma))
        )
        if inside.shape[0]
        else math.nan,
        "rmse_current_duplicate_weighted_gaussian": weighted_rmse(residual, weights),
        "rmse_capped_gaussian_abs1_log10": weighted_rmse(np.clip(residual, -cap_abs, cap_abs), weights),
        "rmse_huber_delta_2sigma": weighted_rmse(residual, weights),
        "rmse_student_t_nu4": weighted_rmse(residual, weights),
        "rmse_configured_scalar_inside_only_gaussian": weighted_rmse(inside_residual, inside_weights),
        "mae_current_duplicate_weighted_gaussian": weighted_mae(residual, weights),
        "mae_capped_gaussian_abs1_log10": weighted_mae(np.clip(residual, -cap_abs, cap_abs), weights),
        "mae_huber_delta_2sigma": weighted_mae(residual, weights),
        "mae_student_t_nu4": weighted_mae(residual, weights),
        "mae_configured_scalar_inside_only_gaussian": weighted_mae(inside_residual, inside_weights),
        "max_abs_current_duplicate_weighted_gaussian": float(np.max(np.abs(residual))),
        "max_abs_capped_gaussian_abs1_log10": cap_abs,
        "max_abs_huber_delta_2sigma": float(np.max(np.abs(residual))),
        "max_abs_student_t_nu4": float(np.max(np.abs(residual))),
        "max_abs_configured_scalar_inside_only_gaussian": float(np.max(np.abs(inside_residual)))
        if inside_residual.size
        else math.nan,
    }
    scores.update(support_scores(active, sigma))
    return scores


def top_loss_share(losses: np.ndarray, count: int) -> float:
    losses = np.asarray(losses, dtype=float)
    losses = losses[np.isfinite(losses) & (losses >= 0.0)]
    total = float(np.sum(losses))
    if total <= 0.0:
        return math.nan
    return float(np.sum(np.sort(losses)[-count:]) / total)


def best_row(frame: pd.DataFrame, policy_id: str) -> pd.Series | None:
    column = f"objective_{policy_id}"
    finite = frame[np.isfinite(frame[column])].copy()
    if finite.empty:
        return None
    finite = finite.sort_values([column, "candidate_id"], ascending=[True, True])
    return finite.iloc[0]


def best_candidate_ids(frame: pd.DataFrame, policy_id: str) -> set[str]:
    column = f"objective_{policy_id}"
    finite = frame[np.isfinite(frame[column])].copy()
    if finite.empty:
        return set()
    best = float(finite[column].min())
    atol = max(1.0e-12, abs(best) * 1.0e-12)
    tied = finite[np.isclose(finite[column].astype(float), best, rtol=1.0e-12, atol=atol)]
    return set(tied["candidate_id"].astype(str))


def add_ranks(frame: pd.DataFrame) -> pd.DataFrame:
    rows = frame.copy()
    for policy_id, _description in POLICIES:
        column = f"objective_{policy_id}"
        rows[f"rank_{policy_id}"] = rows[column].rank(method="min", ascending=True, na_option="bottom")
    return rows


def build_winners(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    current_winner = best_row(frame, "current_duplicate_weighted_gaussian")
    current_winner_id = None if current_winner is None else str(current_winner["candidate_id"])
    current_best_ids = best_candidate_ids(frame, "current_duplicate_weighted_gaussian")
    current_accepted = frame[frame["source_kind"].astype(str).eq("current_accepted_field")]
    current_accepted_id = None if current_accepted.empty else str(current_accepted.iloc[0]["candidate_id"])
    for policy_id, description in POLICIES:
        winner = best_row(frame, policy_id)
        if winner is None:
            continue
        winner_id = str(winner["candidate_id"])
        accepted_rank = math.nan
        accepted_objective = math.nan
        if not current_accepted.empty:
            accepted_rank = current_accepted.iloc[0].get(f"rank_{policy_id}", math.nan)
            accepted_objective = current_accepted.iloc[0].get(f"objective_{policy_id}", math.nan)
        rows.append(
            {
                "policy_id": policy_id,
                "policy_description": description,
                "winner_candidate_id": winner["candidate_id"],
                "winner_candidate_family": winner["candidate_family"],
                "winner_source_kind": winner["source_kind"],
                "winner_mesh": winner["mesh"],
                "winner_objective_like_value": winner[f"objective_{policy_id}"],
                "winner_rmse_log10": winner.get(f"rmse_{policy_id}", math.nan),
                "winner_effective_objective_weight": winner.get("effective_objective_weight", math.nan),
                "winner_active_row_count": winner.get("active_row_count", math.nan),
                "current_accepted_candidate_id": current_accepted_id,
                "current_accepted_rank": accepted_rank,
                "current_accepted_objective_like_value": accepted_objective,
                "differs_from_current_gaussian_winner": bool(str(winner["candidate_id"]) != current_winner_id),
                "winner_in_current_gaussian_best_tie_set": bool(winner_id in current_best_ids),
                "differs_from_current_gaussian_best_set": bool(winner_id not in current_best_ids),
            }
        )
    return pd.DataFrame(rows)


def write_markdown(
    path: Path,
    ranked: pd.DataFrame,
    winners: pd.DataFrame,
    summary: dict[str, Any],
) -> None:
    lines: list[str] = [
        "# Permeability Likelihood Scenario Rerank",
        "",
        "This audit reranks already materialized permeability-field VTUs under alternative direct-permeability likelihood semantics. It does not run OGS and does not change the active objective.",
        "",
        "## Candidate Inventory",
        "",
        f"- Discovered candidate fields: {summary['candidate_fields_discovered']}",
        f"- Successfully evaluated/reread: {summary['candidate_fields_scored']}",
        f"- Failed candidates: {summary['candidate_fields_failed']}",
        f"- Cached row-evaluation CSVs used: {summary['cached_evaluation_count']}",
        f"- Fresh mesh evaluations: {summary['fresh_mesh_evaluation_count']}",
        f"- Active direct-permeability rows per valid candidate: {summary.get('active_rows_per_candidate', 'n/a')}",
        "",
        "The configured-scalar inside-only policy uses the current-field configured-scalar outlier labels from `permeability_residual_conflict_audit.csv`; it is a diagnostic mask, not a per-candidate tensor-bound recomputation.",
        "",
        "## Policy Winners",
        "",
        f"The active row-Gaussian policy has {summary['current_gaussian_best_tie_count']} tied best materialized fields at objective-like value {fmt(summary['current_gaussian_winner_objective'])}.",
        "",
        "| Policy | Winner | Family | Objective-like value | Current accepted rank | Outside row-Gaussian best tie set |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for _, row in winners.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["policy_id"]),
                    f"`{row['winner_candidate_id']}`",
                    str(row["winner_candidate_family"]),
                    fmt(row["winner_objective_like_value"]),
                    fmt(row["current_accepted_rank"], 0),
                    str(bool(row["differs_from_current_gaussian_best_set"])),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Current Accepted Field",
            "",
            "| Policy | Rank | Objective-like value |",
            "| --- | ---: | ---: |",
        ]
    )
    current = ranked[ranked["source_kind"].astype(str).eq("current_accepted_field")]
    if current.empty:
        lines.append("| current accepted field | n/a | n/a |")
    else:
        current_row = current.iloc[0]
        for policy_id, _description in POLICIES:
            lines.append(
                f"| {policy_id} | {fmt(current_row.get(f'rank_{policy_id}'), 0)} | "
                f"{fmt(current_row.get(f'objective_{policy_id}'))} |"
            )

    row_winner = winners[winners["policy_id"].eq("current_duplicate_weighted_gaussian")]
    changed = winners[winners["differs_from_current_gaussian_best_set"].astype(bool)]
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
        ]
    )
    if not row_winner.empty:
        lines.append(
            f"- The active row-Gaussian policy has {summary['current_gaussian_best_tie_count']} tied best materialized fields; "
            f"`{row_winner.iloc[0]['winner_candidate_id']}` is the first representative after candidate-id sorting."
        )
    if changed.empty:
        lines.append("- The diagnostic policies do not select a winner outside the active row-Gaussian best tie set.")
    else:
        changed_ids = ", ".join(f"`{item}`" for item in changed["policy_id"].astype(str))
        lines.append(
            f"- These diagnostic policies select a winner outside the active row-Gaussian best tie set: {changed_ids}."
        )
    lines.append(
        "- This is only a reranking of existing fields. A policy change still needs a written likelihood decision before it becomes the default fitting objective."
    )

    lines.extend(
        [
            "",
            "## Top Row-Gaussian Candidates",
            "",
            "| Rank | Candidate | Family | Objective | RMSE log10 | Mesh |",
            "| ---: | --- | --- | ---: | ---: | --- |",
        ]
    )
    top = ranked.sort_values(
        ["objective_current_duplicate_weighted_gaussian", "candidate_id"],
        ascending=[True, True],
    ).head(10)
    for _, row in top.iterrows():
        lines.append(
            f"| {fmt(row['rank_current_duplicate_weighted_gaussian'], 0)} | "
            f"`{row['candidate_id']}` | {row['candidate_family']} | "
            f"{fmt(row['objective_current_duplicate_weighted_gaussian'])} | "
            f"{fmt(row['rmse_current_duplicate_weighted_gaussian'])} | `{row['mesh']}` |"
        )

    lines.extend(
        [
            "",
            "## Output Files",
            "",
            f"- Full ranked table: `{summary['outputs']['ranked_csv']}`",
            f"- Policy winner table: `{summary['outputs']['winner_csv']}`",
            f"- Summary JSON: `{summary['outputs']['summary_json']}`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_outputs(paths: list[Path], catalogue_dir: Path) -> list[str]:
    derived = catalogue_dir / "derived_files"
    derived.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for source in paths:
        if source.exists():
            target = derived / source.name
            shutil.copy2(source, target)
            copied.append(str(target))
    return copied


def main() -> None:
    args = parse_args()
    repo = Path.cwd()
    runs_root = resolve(repo, args.runs_root).resolve()
    current_field = resolve(repo, args.current_field).resolve()
    targets_path = resolve(repo, args.targets).resolve()
    target_cells_path = resolve(repo, args.target_cells).resolve()
    residual_audit = resolve(repo, args.residual_audit).resolve()
    output_csv = resolve(repo, args.output_csv).resolve()
    winner_output = resolve(repo, args.winner_output).resolve()
    summary_output = resolve(repo, args.summary_output).resolve()
    markdown_output = resolve(repo, args.markdown_output).resolve()
    catalogue_dir = resolve(repo, args.catalogue_dir).resolve()

    status_map = load_status_map(residual_audit)
    candidates = discover_candidates(repo, runs_root, current_field, args.max_candidates)
    scored_rows: list[dict[str, Any]] = []
    failed_rows: list[dict[str, Any]] = []
    cached_count = 0
    fresh_count = 0

    for index, candidate in enumerate(candidates, start=1):
        mesh_path = Path(candidate["mesh_path"]).resolve()
        try:
            evaluation, source_type, source_path = load_or_evaluate(
                mesh_path=mesh_path,
                field_name=args.field_name,
                targets_path=targets_path,
                target_cells_path=target_cells_path,
                sigma=args.log10_sigma,
                use_cache=not args.no_cache,
            )
            if source_type == "cached_csv":
                cached_count += 1
            else:
                fresh_count += 1
            active = active_rows(evaluation, status_map)
            if active.empty:
                raise ValueError("no finite active direct-permeability rows available")
            row = {
                **candidate,
                "candidate_index": index,
                "evaluation_source": source_type,
                "evaluation_source_path": relative(repo, Path(source_path)),
            }
            row.update(
                score_candidate(
                    active,
                    sigma=args.log10_sigma,
                    cap_abs=args.cap_abs_log10,
                    huber_delta=args.huber_delta_normalized,
                    student_nu=args.student_t_nu,
                )
            )
            scored_rows.append(row)
        except Exception as exc:  # noqa: BLE001 - preserve failed candidate inventory in audit output.
            failed_rows.append(
                {
                    **candidate,
                    "candidate_index": index,
                    "error_type": exc.__class__.__name__,
                    "error_message": str(exc),
                }
            )

    if not scored_rows:
        raise RuntimeError("no candidates could be scored")

    ranked = add_ranks(pd.DataFrame(scored_rows))
    winners = build_winners(ranked)
    ranked = ranked.sort_values(
        ["rank_current_duplicate_weighted_gaussian", "candidate_id"],
        ascending=[True, True],
    )
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    ranked.to_csv(output_csv, index=False)
    winners.to_csv(winner_output, index=False)

    current_accepted = ranked[ranked["source_kind"].astype(str).eq("current_accepted_field")]
    row_winner = best_row(ranked, "current_duplicate_weighted_gaussian")
    current_gaussian_best_ids = best_candidate_ids(ranked, "current_duplicate_weighted_gaussian")
    active_counts = sorted(set(ranked["active_row_count"].astype(int).tolist()))
    winner_map = {
        row["policy_id"]: {
            "winner_candidate_id": row["winner_candidate_id"],
            "winner_candidate_family": row["winner_candidate_family"],
            "winner_objective_like_value": row["winner_objective_like_value"],
            "winner_mesh": row["winner_mesh"],
            "current_accepted_rank": row["current_accepted_rank"],
            "differs_from_current_gaussian_winner": row["differs_from_current_gaussian_winner"],
            "winner_in_current_gaussian_best_tie_set": row["winner_in_current_gaussian_best_tie_set"],
            "differs_from_current_gaussian_best_set": row["differs_from_current_gaussian_best_set"],
        }
        for _, row in winners.iterrows()
    }
    summary: dict[str, Any] = {
        "status": "permeability_likelihood_scenario_rerank_generated",
        "method": "no_ogs_existing_vtu_or_cached_row_evaluation_rerank",
        "field_name": args.field_name,
        "log10_sigma": args.log10_sigma,
        "cap_abs_log10": args.cap_abs_log10,
        "huber_delta_normalized": args.huber_delta_normalized,
        "student_t_nu": args.student_t_nu,
        "candidate_fields_discovered": len(candidates),
        "candidate_fields_scored": int(ranked.shape[0]),
        "candidate_fields_failed": len(failed_rows),
        "cached_evaluation_count": cached_count,
        "fresh_mesh_evaluation_count": fresh_count,
        "active_rows_per_candidate": active_counts[0] if len(active_counts) == 1 else active_counts,
        "current_accepted_candidate_id": None if current_accepted.empty else str(current_accepted.iloc[0]["candidate_id"]),
        "current_accepted_rank_current_gaussian": None
        if current_accepted.empty
        else current_accepted.iloc[0].get("rank_current_duplicate_weighted_gaussian"),
        "current_accepted_objective_current_gaussian": None
        if current_accepted.empty
        else current_accepted.iloc[0].get("objective_current_duplicate_weighted_gaussian"),
        "current_gaussian_winner_candidate_id": None if row_winner is None else str(row_winner["candidate_id"]),
        "current_gaussian_winner_objective": None
        if row_winner is None
        else row_winner.get("objective_current_duplicate_weighted_gaussian"),
        "current_gaussian_best_tie_count": len(current_gaussian_best_ids),
        "current_accepted_in_current_gaussian_best_tie_set": None
        if current_accepted.empty
        else str(current_accepted.iloc[0]["candidate_id"]) in current_gaussian_best_ids,
        "policy_winners": winner_map,
        "alternate_policy_winner_outside_current_gaussian_best_set_count": int(
            winners[
                winners["policy_id"].ne("current_duplicate_weighted_gaussian")
                & winners["differs_from_current_gaussian_best_set"].astype(bool)
            ].shape[0]
        ),
        "failed_candidates": failed_rows,
        "outputs": {
            "ranked_csv": relative(repo, output_csv),
            "winner_csv": relative(repo, winner_output),
            "summary_json": relative(repo, summary_output),
            "markdown": relative(repo, markdown_output),
        },
        "notes": [
            "No OGS state solve is run; this is a direct-permeability row-residual rerank.",
            "Cached same-directory permeability_fit_evaluation.csv files are reused when compatible.",
            "The configured-scalar inside-only policy reuses current-field outlier labels from the residual conflict audit.",
        ],
    }

    summary_output.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(markdown_output, ranked, winners, summary)
    copied = copy_outputs([output_csv, winner_output, summary_output, markdown_output], catalogue_dir)
    if copied:
        summary["catalogue_copies"] = [relative(repo, Path(path)) for path in copied]
        summary_output.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
        write_markdown(markdown_output, ranked, winners, summary)
        copy_outputs([summary_output, markdown_output], catalogue_dir)

    print(f"discovered candidate fields: {len(candidates)}")
    print(f"scored candidate fields: {ranked.shape[0]}")
    print(f"failed candidate fields: {len(failed_rows)}")
    print(f"cached evaluations: {cached_count}")
    print(f"fresh mesh evaluations: {fresh_count}")
    if row_winner is not None:
        print(f"row-Gaussian winner: {row_winner['candidate_id']}")
        print(f"row-Gaussian objective: {row_winner['objective_current_duplicate_weighted_gaussian']:.6g}")
    print(f"wrote {output_csv}")
    print(f"wrote {winner_output}")
    print(f"wrote {summary_output}")
    print(f"wrote {markdown_output}")


if __name__ == "__main__":
    main()
