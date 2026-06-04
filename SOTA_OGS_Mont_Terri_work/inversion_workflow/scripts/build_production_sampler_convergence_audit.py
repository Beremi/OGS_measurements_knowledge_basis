#!/usr/bin/env python3
"""Build a cross-family sampler/convergence audit over accepted OGS evidence."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_predict


SMOOTH_CANDIDATE_TABLES = [
    Path("inversion_workflow/runs/adaptive_combined_candidate_plan/all_candidate_scores.csv"),
    Path("inversion_workflow/runs/bayesian_candidate_proposal/optimizer_candidate_scores.csv"),
    Path("inversion_workflow/runs/continuous_bayesian_candidate_plan/continuous_optimizer_candidate_scores.csv"),
    Path("inversion_workflow/runs/lower_support_continuous_candidate_plan/continuous_optimizer_candidate_scores.csv"),
]

FEATURE_COLUMNS = [
    "direct_objective",
    "direct_weighted_rmse_log10",
    "length_scale_m",
    "log_length_scale_m",
    "shift_or_shrink",
    "affected_cells",
    "log1p_affected_cells",
    "update_sse",
    "log1p_update_sse",
    "mean_abs_update",
    "rms_update",
    "family_is_smooth",
    "family_is_local_basis",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smooth-executed-evidence",
        type=Path,
        default=Path("inversion_workflow/runs/adaptive_combined_candidate_plan/executed_candidate_evidence.csv"),
    )
    parser.add_argument(
        "--local-basis-executed-evidence",
        type=Path,
        default=Path("inversion_workflow/runs/local_basis_sampler_candidate_search/inversion_candidate_search_results.csv"),
    )
    parser.add_argument(
        "--production-executed-evidence",
        type=Path,
        action="append",
        help="Optional executed production handoff results to fold into the cross-family evidence.",
    )
    parser.add_argument(
        "--local-basis-candidates",
        type=Path,
        default=Path("inversion_workflow/runs/local_basis_sampler_plan/local_basis_sampler_scores.csv"),
    )
    parser.add_argument(
        "--smooth-candidate-table",
        action="append",
        type=Path,
        dest="smooth_candidate_tables",
        help="Smooth-family candidate table. Can be passed multiple times.",
    )
    parser.add_argument(
        "--release-gate-summary",
        type=Path,
        default=Path("inversion_workflow/inversion_release_gate_audit.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/runs/production_sampler_convergence"),
    )
    parser.add_argument("--execution-batch-size", type=int, default=6)
    parser.add_argument("--max-proposals", type=int, default=12)
    parser.add_argument("--lcb-kappa", type=float, default=1.0)
    parser.add_argument("--xi", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=20260531)
    parser.add_argument("--pause-min-production-candidates", type=int, default=24)
    parser.add_argument("--pause-max-top-probability", type=float, default=0.05)
    parser.add_argument("--pause-max-top-expected-improvement", type=float, default=0.02)
    return parser.parse_args()


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


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def numeric(series: pd.Series | Any) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def first_existing(frame: pd.DataFrame, names: list[str], default: Any = np.nan) -> pd.Series:
    for name in names:
        if name in frame.columns:
            return frame[name]
    return pd.Series([default] * len(frame), index=frame.index)


def stage_for_run_id(run_id: str) -> tuple[int, str]:
    run_id = str(run_id)
    stage_patterns = [
        (10, "regularized candidate set", r"^regularized_ogs_candidate_"),
        (20, "first adaptive broad support", r"^adaptive_combined_"),
        (30, "local smooth refinement", r"^local_refined_"),
        (40, "local smooth bracketing", r"^local_bracketed_"),
        (50, "finite smooth Bayesian batch", r"^optimizer_proposed_"),
        (60, "first continuous smooth batch", r"^continuous_proposed_"),
        (70, "lower-support continuous batch", r"^lower_support_continuous_"),
        (80, "lower-support loop 1", r"^lower_support_loop_001_"),
        (81, "lower-support loop 2", r"^lower_support_loop_002_"),
        (90, "broad continuous batch", r"^broad_continuous_001_"),
        (100, "broad continuous loop", r"^broad_continuous_loop_001_"),
        (110, "local-basis sampler batch", r"^local_basis_sampler_"),
        (120, "production sampler batches", r"^production_sampler_"),
    ]
    for order, label, pattern in stage_patterns:
        if re.search(pattern, run_id):
            return order, label
    return 999, "unclassified"


def standardize_smooth_executed(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"smooth executed evidence not found: {path}")
    frame = pd.read_csv(path)
    if frame.empty:
        raise SystemExit(f"smooth executed evidence is empty: {path}")
    out = pd.DataFrame(index=frame.index)
    out["candidate_id"] = frame["candidate_id"].astype(str)
    out["candidate_family"] = "smooth"
    out["candidate_key"] = "smooth:" + out["candidate_id"]
    out["run_id"] = first_existing(frame, ["run_id"], "").astype(str)
    out["run_dir"] = first_existing(frame, ["run_dir"], "")
    out["summary_json"] = first_existing(frame, ["summary_json"], "")
    out["executed_source"] = first_existing(frame, ["executed_source"], "smooth_executed_evidence")
    out["executed_results_path"] = first_existing(frame, ["executed_results_path"], str(path))
    out["ogs_mode"] = first_existing(frame, ["ogs_mode"], "")
    out["active_component_count"] = numeric(first_existing(frame, ["active_component_count"]))
    out["total_active_objective_value"] = numeric(frame["total_active_objective_value"])
    out["direct_permeability_objective"] = numeric(
        first_existing(frame, ["direct_permeability_objective", "source_direct_objective"])
    )
    out["state_objective_value"] = numeric(first_existing(frame, ["state_objective_value"]))
    missing_state = out["state_objective_value"].isna()
    out.loc[missing_state, "state_objective_value"] = (
        out.loc[missing_state, "total_active_objective_value"]
        - out.loc[missing_state, "direct_permeability_objective"]
    )
    out["direct_permeability_weighted_rmse_log10"] = numeric(
        first_existing(frame, ["direct_permeability_weighted_rmse_log10", "source_weighted_rmse_log10"])
    )
    out["state_active_objective_rows"] = numeric(first_existing(frame, ["state_active_objective_rows"]))
    out["run_input_audit_status"] = first_existing(frame, ["run_input_audit_status"], "")
    out["release_gate_status"] = first_existing(frame, ["release_gate_status"], "")
    out["mesh_override"] = first_existing(frame, ["mesh_override"], "")
    out["length_scale_m"] = numeric(first_existing(frame, ["source_length_scale_m", "length_scale_m"]))
    out["shift_scale"] = numeric(first_existing(frame, ["source_shift_scale", "shift_scale"]))
    out["global_shrink"] = np.nan
    out["shift_or_shrink"] = out["shift_scale"]
    out["affected_cells"] = numeric(first_existing(frame, ["source_affected_cells", "affected_cells"]))
    out["source_direct_objective"] = numeric(first_existing(frame, ["source_direct_objective", "direct_permeability_objective"]))
    out["source_weighted_rmse_log10"] = numeric(
        first_existing(frame, ["source_weighted_rmse_log10", "direct_permeability_weighted_rmse_log10"])
    )
    stages = out["run_id"].map(stage_for_run_id)
    out["execution_stage_order"] = [item[0] for item in stages]
    out["execution_stage"] = [item[1] for item in stages]
    return out


def standardize_local_basis_executed(path: Path, candidate_features: pd.DataFrame) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    if frame.empty:
        return pd.DataFrame()
    out = pd.DataFrame(index=frame.index)
    out["candidate_id"] = frame["source_candidate_id"].astype(str)
    out["candidate_family"] = "local_basis"
    out["candidate_key"] = "local_basis:" + out["candidate_id"]
    out["run_id"] = first_existing(frame, ["run_id"], "").astype(str)
    out["run_dir"] = first_existing(frame, ["run_dir"], "")
    out["summary_json"] = first_existing(frame, ["summary_json"], "")
    out["executed_source"] = "local_basis_sampler_search"
    out["executed_results_path"] = str(path)
    out["ogs_mode"] = first_existing(frame, ["ogs_mode"], "")
    out["active_component_count"] = numeric(first_existing(frame, ["active_component_count"]))
    out["total_active_objective_value"] = numeric(frame["total_active_objective_value"])
    out["direct_permeability_objective"] = numeric(
        first_existing(frame, ["direct_permeability_objective", "source_direct_objective"])
    )
    out["state_objective_value"] = (
        out["total_active_objective_value"] - out["direct_permeability_objective"]
    )
    out["direct_permeability_weighted_rmse_log10"] = numeric(
        first_existing(frame, ["direct_permeability_weighted_rmse_log10", "source_weighted_rmse_log10"])
    )
    out["state_active_objective_rows"] = numeric(first_existing(frame, ["state_active_objective_rows"]))
    out["run_input_audit_status"] = first_existing(frame, ["run_input_audit_status"], "")
    out["release_gate_status"] = first_existing(frame, ["release_gate_status"], "")
    out["mesh_override"] = first_existing(frame, ["mesh_override"], "")
    out["length_scale_m"] = numeric(first_existing(frame, ["source_length_scale_m", "length_scale_m"]))
    out["shift_scale"] = numeric(first_existing(frame, ["source_shift_scale", "shift_scale"]))
    out["global_shrink"] = np.nan
    out["shift_or_shrink"] = out["shift_scale"]
    out["affected_cells"] = numeric(first_existing(frame, ["source_affected_cells", "affected_cells"]))
    out["source_direct_objective"] = numeric(first_existing(frame, ["source_direct_objective", "direct_permeability_objective"]))
    out["source_weighted_rmse_log10"] = numeric(
        first_existing(frame, ["source_weighted_rmse_log10", "direct_permeability_weighted_rmse_log10"])
    )
    if not candidate_features.empty:
        lookup_columns = [
            "candidate_id",
            "global_shrink",
            "length_scale_m",
            "affected_cells",
            "mesh",
            "evaluation_csv",
            "summary_json",
        ]
        lookup = candidate_features[[column for column in lookup_columns if column in candidate_features.columns]].copy()
        lookup = lookup.drop_duplicates("candidate_id", keep="first")
        out = out.merge(lookup, on="candidate_id", how="left", suffixes=("", "_candidate"))
        for column in ["global_shrink", "length_scale_m", "affected_cells"]:
            candidate_column = f"{column}_candidate"
            if candidate_column in out.columns:
                out[column] = out[column].where(out[column].notna(), numeric(out[candidate_column]))
                out = out.drop(columns=[candidate_column])
        if "mesh" in out.columns:
            out["mesh_override"] = out["mesh_override"].where(out["mesh_override"].astype(str).str.len() > 0, out["mesh"])
            out = out.drop(columns=["mesh"])
        if "summary_json_candidate" in out.columns:
            out = out.drop(columns=["summary_json_candidate"])
        if "evaluation_csv" in out.columns:
            out = out.drop(columns=["evaluation_csv"])
    out["shift_or_shrink"] = out["global_shrink"].where(out["global_shrink"].notna(), out["shift_scale"])
    stages = out["run_id"].map(stage_for_run_id)
    out["execution_stage_order"] = [item[0] for item in stages]
    out["execution_stage"] = [item[1] for item in stages]
    return out


def family_from_candidate_id(candidate_id: Any) -> str:
    return "local_basis" if str(candidate_id).startswith("basis_") else "smooth"


def standardize_search_executed(path: Path, executed_source: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    if frame.empty:
        return pd.DataFrame()
    out = pd.DataFrame(index=frame.index)
    out["candidate_id"] = frame["source_candidate_id"].astype(str)
    out["candidate_family"] = out["candidate_id"].map(family_from_candidate_id)
    out["candidate_key"] = out["candidate_family"] + ":" + out["candidate_id"]
    out["run_id"] = first_existing(frame, ["run_id"], "").astype(str)
    out["run_dir"] = first_existing(frame, ["run_dir"], "")
    out["summary_json"] = first_existing(frame, ["summary_json"], "")
    out["executed_source"] = executed_source
    out["executed_results_path"] = str(path)
    out["ogs_mode"] = first_existing(frame, ["ogs_mode"], "")
    out["active_component_count"] = numeric(first_existing(frame, ["active_component_count"]))
    out["total_active_objective_value"] = numeric(frame["total_active_objective_value"])
    out["direct_permeability_objective"] = numeric(
        first_existing(frame, ["direct_permeability_objective", "source_direct_objective"])
    )
    out["state_objective_value"] = (
        out["total_active_objective_value"] - out["direct_permeability_objective"]
    )
    out["direct_permeability_weighted_rmse_log10"] = numeric(
        first_existing(frame, ["direct_permeability_weighted_rmse_log10", "source_weighted_rmse_log10"])
    )
    out["state_active_objective_rows"] = numeric(first_existing(frame, ["state_active_objective_rows"]))
    out["run_input_audit_status"] = first_existing(frame, ["run_input_audit_status"], "")
    out["release_gate_status"] = first_existing(frame, ["release_gate_status"], "")
    out["mesh_override"] = first_existing(frame, ["mesh_override"], "")
    out["length_scale_m"] = numeric(first_existing(frame, ["source_length_scale_m", "length_scale_m"]))
    out["shift_scale"] = numeric(first_existing(frame, ["source_shift_scale", "shift_scale"]))
    out["global_shrink"] = np.nan
    out["shift_or_shrink"] = out["shift_scale"]
    out["affected_cells"] = numeric(first_existing(frame, ["source_affected_cells", "affected_cells"]))
    out["source_direct_objective"] = numeric(
        first_existing(frame, ["source_direct_objective", "direct_permeability_objective"])
    )
    out["source_weighted_rmse_log10"] = numeric(
        first_existing(frame, ["source_weighted_rmse_log10", "direct_permeability_weighted_rmse_log10"])
    )
    stages = out["run_id"].map(stage_for_run_id)
    out["execution_stage_order"] = [item[0] for item in stages]
    out["execution_stage"] = [item[1] for item in stages]
    return out


def standardize_smooth_candidates(paths: list[Path]) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for path in paths:
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        if frame.empty or "candidate_id" not in frame.columns:
            continue
        out = pd.DataFrame(index=frame.index)
        out["candidate_id"] = frame["candidate_id"].astype(str)
        out["candidate_family"] = "smooth"
        out["candidate_key"] = "smooth:" + out["candidate_id"]
        out["candidate_source_table"] = str(path)
        out["direct_objective"] = numeric(first_existing(frame, ["objective_value", "direct_permeability_objective"]))
        out["direct_weighted_rmse_log10"] = numeric(
            first_existing(frame, ["weighted_rmse_log10", "direct_permeability_weighted_rmse_log10"])
        )
        out["length_scale_m"] = numeric(first_existing(frame, ["length_scale_m", "source_length_scale_m"]))
        out["shift_scale"] = numeric(first_existing(frame, ["shift_scale", "source_shift_scale"]))
        out["global_shrink"] = np.nan
        out["shift_or_shrink"] = out["shift_scale"]
        out["affected_cells"] = numeric(first_existing(frame, ["affected_cells", "source_affected_cells"]))
        out["update_sse"] = numeric(first_existing(frame, ["sum_squared_applied_log10_shift_all_cells"]))
        out["mean_abs_update"] = numeric(first_existing(frame, ["mean_abs_applied_log10_shift_affected"]))
        out["rms_update"] = numeric(first_existing(frame, ["rms_applied_log10_shift_affected"]))
        out["mesh"] = first_existing(frame, ["mesh", "mesh_override"], "")
        out["evaluation_csv"] = first_existing(frame, ["evaluation_csv"], "")
        out["summary_json"] = first_existing(frame, ["summary_json"], "")
        out["candidate_sample_source"] = first_existing(frame, ["proposal_sample_source", "candidate_table_source"], "")
        rows.append(out)
    if not rows:
        return pd.DataFrame()
    combined = pd.concat(rows, ignore_index=True, sort=False)
    combined = combined[combined["direct_objective"].notna()].copy()
    combined["feature_nonnull_count"] = combined[FEATURE_COLUMNS_BASE_FOR_DEDUP].notna().sum(axis=1)
    combined = combined.sort_values(
        ["candidate_key", "feature_nonnull_count", "direct_objective"],
        ascending=[True, False, True],
    )
    return combined.drop_duplicates("candidate_key", keep="first").drop(columns=["feature_nonnull_count"])


FEATURE_COLUMNS_BASE_FOR_DEDUP = [
    "direct_objective",
    "direct_weighted_rmse_log10",
    "length_scale_m",
    "shift_or_shrink",
    "affected_cells",
    "update_sse",
    "mean_abs_update",
    "rms_update",
]


def standardize_local_basis_candidates(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    if frame.empty:
        return pd.DataFrame()
    out = pd.DataFrame(index=frame.index)
    out["candidate_id"] = frame["candidate_id"].astype(str)
    out["candidate_family"] = "local_basis"
    out["candidate_key"] = "local_basis:" + out["candidate_id"]
    out["candidate_source_table"] = str(path)
    out["direct_objective"] = numeric(first_existing(frame, ["objective_value"]))
    out["direct_weighted_rmse_log10"] = numeric(first_existing(frame, ["weighted_rmse_log10"]))
    out["length_scale_m"] = numeric(first_existing(frame, ["length_scale_m"]))
    out["shift_scale"] = np.nan
    out["global_shrink"] = numeric(first_existing(frame, ["global_shrink"]))
    out["shift_or_shrink"] = out["global_shrink"]
    out["affected_cells"] = numeric(first_existing(frame, ["affected_cells"]))
    out["update_sse"] = numeric(first_existing(frame, ["sum_squared_applied_log10_increment_all_cells"]))
    out["mean_abs_update"] = numeric(first_existing(frame, ["mean_abs_applied_log10_increment_affected"]))
    out["rms_update"] = np.nan
    out["mesh"] = first_existing(frame, ["mesh"], "")
    out["evaluation_csv"] = first_existing(frame, ["evaluation_csv"], "")
    out["summary_json"] = first_existing(frame, ["summary_json"], "")
    out["candidate_sample_source"] = first_existing(frame, ["sample_source"], "")
    out["basis_anchor_count"] = numeric(first_existing(frame, ["basis_anchor_count"]))
    out["direct_objective_delta_vs_baseline"] = numeric(first_existing(frame, ["direct_objective_delta_vs_baseline"]))
    return out[out["direct_objective"].notna()].drop_duplicates("candidate_key", keep="first")


def ensure_executed_candidates(candidate_pool: pd.DataFrame, executed: pd.DataFrame) -> pd.DataFrame:
    existing = set(candidate_pool["candidate_key"].astype(str))
    missing = executed[~executed["candidate_key"].astype(str).isin(existing)].copy()
    if missing.empty:
        return candidate_pool
    rows = pd.DataFrame()
    rows["candidate_id"] = missing["candidate_id"]
    rows["candidate_family"] = missing["candidate_family"]
    rows["candidate_key"] = missing["candidate_key"]
    rows["candidate_source_table"] = "executed_evidence_fallback"
    rows["direct_objective"] = missing["direct_permeability_objective"]
    rows["direct_weighted_rmse_log10"] = missing["direct_permeability_weighted_rmse_log10"]
    rows["length_scale_m"] = missing["length_scale_m"]
    rows["shift_scale"] = missing["shift_scale"]
    rows["global_shrink"] = missing["global_shrink"]
    rows["shift_or_shrink"] = missing["shift_or_shrink"]
    rows["affected_cells"] = missing["affected_cells"]
    rows["update_sse"] = np.nan
    rows["mean_abs_update"] = np.nan
    rows["rms_update"] = np.nan
    rows["mesh"] = missing["mesh_override"]
    rows["evaluation_csv"] = ""
    rows["summary_json"] = missing["summary_json"]
    rows["candidate_sample_source"] = "executed_evidence_fallback"
    return pd.concat([candidate_pool, rows], ignore_index=True, sort=False)


def build_feature_frame(scored: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    features = scored.copy()
    for column in [
        "direct_objective",
        "direct_weighted_rmse_log10",
        "length_scale_m",
        "shift_or_shrink",
        "affected_cells",
        "update_sse",
        "mean_abs_update",
        "rms_update",
    ]:
        features[column] = numeric(features[column])
    features["log_length_scale_m"] = np.log(features["length_scale_m"].where(features["length_scale_m"] > 0))
    features["log1p_affected_cells"] = np.log1p(features["affected_cells"].where(features["affected_cells"] >= 0))
    features["log1p_update_sse"] = np.log1p(features["update_sse"].where(features["update_sse"] >= 0))
    features["family_is_smooth"] = (features["candidate_family"] == "smooth").astype(float)
    features["family_is_local_basis"] = (features["candidate_family"] == "local_basis").astype(float)
    feature_frame = features[FEATURE_COLUMNS].replace([np.inf, -np.inf], np.nan)
    medians = feature_frame.median(numeric_only=True)
    feature_frame = feature_frame.fillna(medians).fillna(0.0)
    return feature_frame, FEATURE_COLUMNS


def expected_improvement(best: float, mean: np.ndarray, std: np.ndarray, xi: float) -> np.ndarray:
    std = np.asarray(std, dtype=float)
    mean = np.asarray(mean, dtype=float)
    improvement = best - mean - xi
    output = np.zeros_like(mean, dtype=float)
    positive_std = std > 0.0
    if positive_std.any():
        z = improvement[positive_std] / std[positive_std]
        output[positive_std] = improvement[positive_std] * norm.cdf(z) + std[positive_std] * norm.pdf(z)
    output[~positive_std] = np.maximum(improvement[~positive_std], 0.0)
    return np.maximum(output, 0.0)


def fit_cross_family_surrogate(
    scored: pd.DataFrame,
    feature_frame: pd.DataFrame,
    seed: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    training_mask = scored["state_objective_value"].notna()
    training_count = int(training_mask.sum())
    if training_count < 8:
        raise SystemExit("at least eight executed candidates are required for the cross-family sampler audit")
    x_train = feature_frame.loc[training_mask].to_numpy(dtype=float)
    y_train = numeric(scored.loc[training_mask, "state_objective_value"]).to_numpy(dtype=float)
    model = RandomForestRegressor(
        n_estimators=600,
        min_samples_leaf=2,
        random_state=seed,
        n_jobs=-1,
    )
    cv_splits = min(5, training_count)
    cv = KFold(n_splits=cv_splits, shuffle=True, random_state=seed)
    cv_pred = cross_val_predict(model, x_train, y_train, cv=cv, n_jobs=-1)
    cv_resid = cv_pred - y_train
    model.fit(x_train, y_train)
    all_features = feature_frame.to_numpy(dtype=float)
    tree_predictions = np.vstack([tree.predict(all_features) for tree in model.estimators_])
    state_mean = tree_predictions.mean(axis=0)
    state_std = tree_predictions.std(axis=0, ddof=1)
    output = scored.copy()
    output["rf_state_objective_mean"] = state_mean
    output["rf_state_objective_std"] = state_std
    output["rf_combined_objective_mean"] = output["direct_objective"] + output["rf_state_objective_mean"]
    output["rf_combined_objective_std"] = output["rf_state_objective_std"]
    diagnostics = {
        "model": "RandomForestRegressor over smooth and local-basis families, target=state objective",
        "training_candidate_count": training_count,
        "cv_splits": cv_splits,
        "cv_state_objective_mae": float(np.mean(np.abs(cv_resid))),
        "cv_state_objective_rmse": float(math.sqrt(np.mean(np.square(cv_resid)))),
        "cv_state_objective_bias": float(np.mean(cv_resid)),
        "feature_columns": FEATURE_COLUMNS,
        "random_state": seed,
    }
    return output, diagnostics


def add_acquisition(scored: pd.DataFrame, best_objective: float, xi: float, lcb_kappa: float) -> pd.DataFrame:
    output = scored.copy()
    mean = output["rf_combined_objective_mean"].to_numpy(dtype=float)
    std = output["rf_combined_objective_std"].clip(lower=1e-12).to_numpy(dtype=float)
    output["expected_improvement"] = expected_improvement(best_objective, mean, std, xi)
    output["probability_of_improvement"] = norm.cdf((best_objective - mean) / std)
    output["lower_confidence_bound"] = mean - lcb_kappa * std
    output["is_executed_ogs_candidate"] = output["total_active_objective_value"].notna()
    mesh_text = output["mesh"].fillna("").astype(str)
    output["has_executable_mesh"] = (mesh_text.str.len() > 0) & (mesh_text.str.lower() != "nan")
    return output


def build_convergence_history(executed: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    history = executed.copy()
    history = history.sort_values(
        ["execution_stage_order", "run_id", "total_active_objective_value"],
        ascending=[True, True, True],
    ).reset_index(drop=True)
    history["execution_order"] = np.arange(1, len(history) + 1)
    history["best_objective_so_far"] = history["total_active_objective_value"].cummin()
    history["best_candidate_so_far"] = [
        history.loc[:idx].sort_values("total_active_objective_value").iloc[0]["candidate_id"]
        for idx in history.index
    ]
    history["is_new_incumbent"] = history["total_active_objective_value"] <= history["best_objective_so_far"]

    stage_rows = []
    for (stage_order, stage), group in history.groupby(["execution_stage_order", "execution_stage"], sort=True):
        best_row = group.sort_values("total_active_objective_value").iloc[0]
        stage_rows.append(
            {
                "execution_stage_order": int(stage_order),
                "execution_stage": stage,
                "run_count": int(group.shape[0]),
                "stage_best_candidate": best_row["candidate_id"],
                "stage_best_objective": float(best_row["total_active_objective_value"]),
                "best_after_stage_candidate": group.iloc[-1]["best_candidate_so_far"],
                "best_after_stage_objective": float(group.iloc[-1]["best_objective_so_far"]),
            }
        )
    stage_summary = pd.DataFrame(stage_rows)

    smooth_best = history[history["candidate_family"] == "smooth"].sort_values("total_active_objective_value").iloc[0]
    global_best = history.sort_values("total_active_objective_value").iloc[0]
    before_local_basis = history[history["execution_stage_order"] < 110]
    previous_best = before_local_basis.sort_values("total_active_objective_value").iloc[0]
    local_basis_rows = history[history["candidate_family"] == "local_basis"]
    local_basis_best = local_basis_rows.sort_values("total_active_objective_value").iloc[0]
    convergence = {
        "executed_candidate_count": int(history.shape[0]),
        "smooth_executed_candidate_count": int((history["candidate_family"] == "smooth").sum()),
        "local_basis_executed_candidate_count": int((history["candidate_family"] == "local_basis").sum()),
        "best_candidate": str(global_best["candidate_id"]),
        "best_candidate_family": str(global_best["candidate_family"]),
        "best_combined_objective": float(global_best["total_active_objective_value"]),
        "best_state_objective": float(global_best["state_objective_value"]),
        "best_direct_objective": float(global_best["direct_permeability_objective"]),
        "best_smooth_candidate": str(smooth_best["candidate_id"]),
        "best_smooth_objective": float(smooth_best["total_active_objective_value"]),
        "previous_pre_local_basis_best_candidate": str(previous_best["candidate_id"]),
        "previous_pre_local_basis_best_objective": float(previous_best["total_active_objective_value"]),
        "local_basis_best_candidate": str(local_basis_best["candidate_id"]),
        "local_basis_best_objective": float(local_basis_best["total_active_objective_value"]),
        "local_basis_improvement_vs_previous_best": float(
            previous_best["total_active_objective_value"] - local_basis_best["total_active_objective_value"]
        ),
        "last_stage_best_candidate": str(stage_summary.iloc[-1]["stage_best_candidate"]),
        "last_stage_best_objective": float(stage_summary.iloc[-1]["stage_best_objective"]),
    }
    return history, stage_summary, convergence


def write_markdown(path: Path, summary: dict[str, Any], proposals: pd.DataFrame, stage_summary: pd.DataFrame) -> None:
    decision = summary.get("production_decision", {})
    lines = [
        "# Production Sampler And Convergence Audit",
        "",
        "This artifact consolidates the accepted OGS evidence across the smooth-field",
        "and local-basis permeability families. It does not execute OGS and it is not",
        "a posterior sampler; it is the current production-facing handoff record for",
        "choosing whether another release-gated candidate batch is worth running.",
        "",
        "## Evidence",
        "",
        f"- Executed OGS candidates: {summary['executed_candidate_count']} "
        f"({summary['smooth_executed_candidate_count']} smooth, "
        f"{summary['local_basis_executed_candidate_count']} local-basis)",
        f"- Release-gate status: `{summary['release_gate_status']}` "
        f"({summary['release_gate_check_count']} checks, "
        f"{summary['release_gate_failure_count']} failures)",
        f"- Current accepted best: `{summary['best_candidate']}` "
        f"({summary['best_candidate_family']}), objective {summary['best_combined_objective']:.5f}",
        f"- Previous smooth-family incumbent: `{summary['best_smooth_candidate']}`, "
        f"objective {summary['best_smooth_objective']:.5f}",
        f"- Local-basis improvement versus the previous accepted best: "
        f"{summary['local_basis_improvement_vs_previous_best']:.5f} objective units",
        f"- Cross-family candidate pool: {summary['candidate_pool_count']} rows "
        f"({summary['unexecuted_candidate_count']} unexecuted; "
        f"{summary['unexecuted_executable_candidate_count']} with materialized meshes)",
        f"- Surrogate CV state-objective RMSE: {summary['cv_state_objective_rmse']:.5f}; "
        f"MAE: {summary['cv_state_objective_mae']:.5f}",
        "",
        "## Convergence By Stage",
        "",
        "| Stage | Runs | Stage best | Stage objective | Best after stage |",
        "| --- | ---: | --- | ---: | --- |",
    ]
    for _, row in stage_summary.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["execution_stage"]),
                    str(int(row["run_count"])),
                    f"`{row['stage_best_candidate']}`",
                    f"{float(row['stage_best_objective']):.5f}",
                    f"`{row['best_after_stage_candidate']}` ({float(row['best_after_stage_objective']):.5f})",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Stop/Continue Decision",
            "",
            f"- Decision: `{decision.get('recommendation', 'not_evaluated')}`",
            f"- Reason: {decision.get('reason', 'No decision evidence was generated.')}",
            f"- Production candidates executed: {decision.get('production_candidate_count')}",
            f"- Top next-batch probability of improvement: {decision.get('top_probability_of_improvement')}",
            f"- Top next-batch expected improvement: {decision.get('top_expected_improvement')}",
            f"- All proposed batch LCB values above incumbent: {decision.get('all_proposed_batch_lcb_above_incumbent')}",
            "",
            "## Proposed Next Batch",
            "",
            "Rows are ranked by lower confidence bound from a cross-family random-forest",
            "state-objective surrogate plus the known direct permeability objective.",
            "The probabilities are diagnostic because the surrogate is trained on",
            f"only {summary['executed_candidate_count']} executed OGS rows "
            f"({summary['local_basis_executed_candidate_count']} local-basis).",
            "",
            "| Rank | Family | Candidate | Direct objective | Predicted combined | Std | LCB | P(improve) |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in proposals.head(int(summary["execution_batch_size"])).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row["production_rank"])),
                    str(row["candidate_family"]),
                    f"`{row['candidate_id']}`",
                    f"{float(row['direct_objective']):.5f}",
                    f"{float(row['rf_combined_objective_mean']):.5f}",
                    f"{float(row['rf_combined_objective_std']):.5f}",
                    f"{float(row['lower_confidence_bound']):.5f}",
                    f"{float(row['probability_of_improvement']):.4g}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Execution Handoff",
            "",
            "Use this only if the stop/continue decision says another convergence stress-test is",
            "worth the OGS cost, or if a human explicitly wants one more active-objective batch.",
            "",
            "```bash",
            "python inversion_workflow/scripts/run_inversion_candidate_search.py \\",
            "  --candidate-table inversion_workflow/runs/production_sampler_convergence/next_production_candidate_batch.csv \\",
            "  --sort-column production_rank \\",
            f"  --max-candidates {summary['execution_batch_size']} \\",
            "  --run-id-prefix production_sampler \\",
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
            f"- The accepted field improved only {summary['local_basis_improvement_vs_previous_best']:.5f} "
            "objective units when moving from",
            "  the best smooth-family row to the best local-basis row.",
            f"- The latest executed stage is `{summary['last_stage_best_candidate']}` at "
            f"{summary['last_stage_best_objective']:.5f}, so it does not replace the accepted best.",
            "- The active objective still contains direct permeability plus sampled NMR rows;",
            "  ERT, Taupe/TDR, RH, and other HM streams remain gated.",
            f"- Stop/continue decision: `{decision.get('recommendation', 'not_evaluated')}`.",
            "  This is a decision about the active direct-permeability plus NMR objective only;",
            "  it is not a final inversion claim while other measurement streams remain gated.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_best_round_row(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    frame = pd.read_csv(path)
    if frame.empty or "total_active_objective_value" not in frame.columns:
        return {}
    frame = frame.copy()
    frame["total_active_objective_value"] = numeric(frame["total_active_objective_value"])
    return frame.sort_values("total_active_objective_value", na_position="last").iloc[0].to_dict()


def build_stop_continue_decision(
    *,
    summary: dict[str, Any],
    proposals: pd.DataFrame,
    production_evidence_paths: list[Path],
    executed: pd.DataFrame,
    min_production_candidates: int,
    max_top_probability: float,
    max_top_expected_improvement: float,
) -> dict[str, Any]:
    production_rows = executed[executed["execution_stage"] == "production sampler batches"].copy()
    production_count = int(production_rows.shape[0])
    incumbent_objective = float(summary["best_combined_objective"])
    production_best = (
        production_rows.sort_values("total_active_objective_value").iloc[0].to_dict()
        if not production_rows.empty
        else {}
    )
    production_best_objective = production_best.get("total_active_objective_value")
    production_best_delta_vs_incumbent = (
        float(production_best_objective) - incumbent_objective
        if production_best_objective is not None
        else None
    )
    latest_round_path = production_evidence_paths[-1] if production_evidence_paths else None
    latest_round_best = read_best_round_row(latest_round_path) if latest_round_path else {}
    latest_round_best_objective = latest_round_best.get("total_active_objective_value")
    latest_round_delta_vs_incumbent = (
        float(latest_round_best_objective) - incumbent_objective
        if latest_round_best_objective is not None
        else None
    )
    batch = proposals.head(int(summary["execution_batch_size"])).copy()
    top = batch.iloc[0].to_dict() if not batch.empty else {}
    top_probability = top.get("probability_of_improvement")
    top_expected_improvement = top.get("expected_improvement")
    all_batch_lcb_above = bool((batch["lower_confidence_bound"] > incumbent_objective).all()) if not batch.empty else False
    criteria = {
        "minimum_production_candidates_reached": production_count >= min_production_candidates,
        "production_best_did_not_improve_incumbent": (
            production_best_delta_vs_incumbent is not None and production_best_delta_vs_incumbent > 0.0
        ),
        "latest_round_did_not_improve_incumbent": (
            latest_round_delta_vs_incumbent is not None and latest_round_delta_vs_incumbent > 0.0
        ),
        "top_probability_below_threshold": (
            top_probability is not None and float(top_probability) < max_top_probability
        ),
        "top_expected_improvement_below_threshold": (
            top_expected_improvement is not None and float(top_expected_improvement) < max_top_expected_improvement
        ),
        "all_proposed_batch_lcb_above_incumbent": all_batch_lcb_above,
        "release_gate_clean": (
            summary.get("release_gate_status") == "pass"
            and int(summary.get("release_gate_failure_count") or 0) == 0
        ),
    }
    pause = all(criteria.values())
    recommendation = "pause_active_production_sampling" if pause else "run_or_review_next_production_batch"
    reason = (
        "Five production handoff rounds have not improved the local-basis incumbent, "
        "the next batch has low diagnostic improvement probability, and every proposed "
        "batch LCB is worse than the incumbent; prioritize measurement-stream gates or "
        "a new field family before spending more OGS runs on the current smooth handoff."
        if pause
        else "At least one pause criterion is not satisfied; review the next batch before deciding."
    )
    return {
        "recommendation": recommendation,
        "reason": reason,
        "incumbent_candidate": summary.get("best_candidate"),
        "incumbent_objective": incumbent_objective,
        "production_round_count": len(production_evidence_paths),
        "production_candidate_count": production_count,
        "production_best_candidate": production_best.get("candidate_id"),
        "production_best_objective": production_best_objective,
        "production_best_delta_vs_incumbent": production_best_delta_vs_incumbent,
        "latest_round_results_csv": str(latest_round_path) if latest_round_path else None,
        "latest_round_best_candidate": latest_round_best.get("source_candidate_id"),
        "latest_round_best_objective": latest_round_best_objective,
        "latest_round_best_delta_vs_incumbent": latest_round_delta_vs_incumbent,
        "next_top_candidate": top.get("candidate_id"),
        "next_top_family": top.get("candidate_family"),
        "top_probability_of_improvement": top_probability,
        "top_expected_improvement": top_expected_improvement,
        "top_lower_confidence_bound": top.get("lower_confidence_bound"),
        "all_proposed_batch_lcb_above_incumbent": all_batch_lcb_above,
        "pause_thresholds": {
            "min_production_candidates": min_production_candidates,
            "max_top_probability_of_improvement": max_top_probability,
            "max_top_expected_improvement": max_top_expected_improvement,
        },
        "criteria": criteria,
        "scope": "active objective only: direct permeability plus sampled NMR rows",
        "not_a_final_inversion_reason": "ERT, Taupe/TDR, RH, other HM streams, and later parameter fields remain gated.",
    }


def write_decision_markdown(path: Path, decision: dict[str, Any]) -> None:
    criteria = decision.get("criteria", {})
    lines = [
        "# Production Sampler Stop/Continue Decision",
        "",
        f"- Recommendation: `{decision.get('recommendation')}`",
        f"- Scope: {decision.get('scope')}",
        f"- Reason: {decision.get('reason')}",
        f"- Incumbent: `{decision.get('incumbent_candidate')}` at {decision.get('incumbent_objective')}",
        f"- Best production candidate: `{decision.get('production_best_candidate')}` at "
        f"{decision.get('production_best_objective')} "
        f"(delta {decision.get('production_best_delta_vs_incumbent')})",
        f"- Latest round best: `{decision.get('latest_round_best_candidate')}` at "
        f"{decision.get('latest_round_best_objective')} "
        f"(delta {decision.get('latest_round_best_delta_vs_incumbent')})",
        f"- Next top proposal: `{decision.get('next_top_candidate')}` "
        f"({decision.get('next_top_family')}); P(improve)="
        f"{decision.get('top_probability_of_improvement')}; EI={decision.get('top_expected_improvement')}; "
        f"LCB={decision.get('top_lower_confidence_bound')}",
        f"- Not final inversion: {decision.get('not_a_final_inversion_reason')}",
        "",
        "## Criteria",
        "",
        "| Criterion | Value |",
        "| --- | ---: |",
    ]
    for key, value in criteria.items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    smooth_tables = args.smooth_candidate_tables or SMOOTH_CANDIDATE_TABLES
    production_evidence_paths = args.production_executed_evidence
    if production_evidence_paths is None:
        production_evidence_paths = sorted(
            Path().glob("inversion_workflow/runs/production_sampler*_candidate_search/inversion_candidate_search_results.csv")
        )
    local_basis_candidates = standardize_local_basis_candidates(args.local_basis_candidates)
    smooth_executed = standardize_smooth_executed(args.smooth_executed_evidence)
    local_basis_executed = standardize_local_basis_executed(
        args.local_basis_executed_evidence,
        local_basis_candidates,
    )
    production_executed_rows = [
        standardize_search_executed(path, executed_source=f"production_sampler_search_{index}")
        for index, path in enumerate(production_evidence_paths, start=1)
    ]
    production_executed = pd.concat(production_executed_rows, ignore_index=True, sort=False)
    executed = pd.concat([smooth_executed, local_basis_executed, production_executed], ignore_index=True, sort=False)
    if executed.empty:
        raise SystemExit("no executed evidence rows were found")
    executed = executed.sort_values("total_active_objective_value").drop_duplicates("candidate_key", keep="first")

    smooth_candidates = standardize_smooth_candidates(smooth_tables)
    candidate_pool = pd.concat([smooth_candidates, local_basis_candidates], ignore_index=True, sort=False)
    if candidate_pool.empty:
        raise SystemExit("no candidate pool rows were found")
    candidate_pool = ensure_executed_candidates(candidate_pool, executed)
    candidate_pool = candidate_pool.sort_values(["candidate_key", "direct_objective"]).drop_duplicates(
        "candidate_key",
        keep="first",
    )

    merge_columns = [
        "candidate_key",
        "run_id",
        "run_dir",
        "executed_source",
        "executed_results_path",
        "ogs_mode",
        "active_component_count",
        "total_active_objective_value",
        "direct_permeability_objective",
        "state_objective_value",
        "direct_permeability_weighted_rmse_log10",
        "state_active_objective_rows",
        "run_input_audit_status",
        "release_gate_status",
        "execution_stage",
        "execution_stage_order",
    ]
    scored = candidate_pool.merge(executed[merge_columns], on="candidate_key", how="left")
    feature_frame, _ = build_feature_frame(scored)
    scored, model_diagnostics = fit_cross_family_surrogate(scored, feature_frame, seed=args.seed)
    history, stage_summary, convergence = build_convergence_history(executed)
    best_objective = float(convergence["best_combined_objective"])
    scored = add_acquisition(scored, best_objective, xi=args.xi, lcb_kappa=args.lcb_kappa)
    all_unexecuted = scored[~scored["is_executed_ogs_candidate"]].copy()
    proposals = all_unexecuted[
        all_unexecuted["direct_objective"].notna() & all_unexecuted["has_executable_mesh"]
    ].copy()
    proposals = proposals.sort_values(
        [
            "lower_confidence_bound",
            "rf_combined_objective_mean",
            "expected_improvement",
            "direct_objective",
            "candidate_key",
        ],
        ascending=[True, True, False, True, True],
    ).reset_index(drop=True)
    proposals["production_rank"] = np.arange(1, proposals.shape[0] + 1)
    batch = proposals.head(args.execution_batch_size).copy()

    release_gate = read_json(args.release_gate_summary)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    executed_path = output_dir / "executed_evidence_accepted.csv"
    history_path = output_dir / "convergence_history.csv"
    stage_path = output_dir / "convergence_by_stage.csv"
    scores_path = output_dir / "cross_family_candidate_scores.csv"
    batch_path = output_dir / "next_production_candidate_batch.csv"
    summary_path = output_dir / "PRODUCTION_SAMPLER_CONVERGENCE.json"
    markdown_path = output_dir / "PRODUCTION_SAMPLER_CONVERGENCE.md"
    decision_path = output_dir / "PRODUCTION_SAMPLER_DECISION.json"
    decision_markdown_path = output_dir / "PRODUCTION_SAMPLER_DECISION.md"

    executed.sort_values(["execution_stage_order", "run_id"]).to_csv(executed_path, index=False)
    history.to_csv(history_path, index=False)
    stage_summary.to_csv(stage_path, index=False)
    scored.sort_values(["is_executed_ogs_candidate", "lower_confidence_bound", "candidate_key"]).to_csv(
        scores_path,
        index=False,
    )
    batch.to_csv(batch_path, index=False)

    top_proposals = proposals.head(args.max_proposals)
    summary = {
        **convergence,
        **model_diagnostics,
        "candidate_pool_count": int(scored.shape[0]),
        "unexecuted_candidate_count": int(all_unexecuted.shape[0]),
        "unexecuted_executable_candidate_count": int(proposals.shape[0]),
        "nonexecutable_diagnostic_candidate_count": int((~all_unexecuted["has_executable_mesh"]).sum()),
        "proposal_count": int(min(args.max_proposals, proposals.shape[0])),
        "execution_batch_size": int(batch.shape[0]),
        "release_gate_status": release_gate.get("status"),
        "release_gate_run_count": release_gate.get("run_count"),
        "release_gate_check_count": release_gate.get("check_count"),
        "release_gate_failure_count": release_gate.get("failure_count"),
        "release_gate_warning_count": release_gate.get("warning_count"),
        "lcb_kappa": float(args.lcb_kappa),
        "xi": float(args.xi),
        "smooth_candidate_tables": [str(path) for path in smooth_tables],
        "local_basis_candidate_table": str(args.local_basis_candidates),
        "production_executed_evidence_tables": [str(path) for path in production_evidence_paths],
        "executed_evidence_csv": str(executed_path),
        "convergence_history_csv": str(history_path),
        "convergence_by_stage_csv": str(stage_path),
        "cross_family_candidate_scores_csv": str(scores_path),
        "next_production_candidate_batch_csv": str(batch_path),
        "summary_markdown": str(markdown_path),
        "top_proposals": json_ready(top_proposals.to_dict(orient="records")),
        "notes": [
            f"This artifact merges {convergence['smooth_executed_candidate_count']} accepted smooth-family OGS rows "
            f"and {convergence['local_basis_executed_candidate_count']} local-basis OGS rows.",
            "The random-forest surrogate predicts the sampled NMR state objective and adds the known direct permeability objective.",
            "The emitted batch is a handoff; it is not accepted evidence until run through OGS and release-gate checks.",
        ],
    }
    decision = build_stop_continue_decision(
        summary=summary,
        proposals=proposals,
        production_evidence_paths=production_evidence_paths,
        executed=executed,
        min_production_candidates=args.pause_min_production_candidates,
        max_top_probability=args.pause_max_top_probability,
        max_top_expected_improvement=args.pause_max_top_expected_improvement,
    )
    summary["production_decision"] = json_ready(decision)
    summary["production_sampler_decision_json"] = str(decision_path)
    summary["production_sampler_decision_markdown"] = str(decision_markdown_path)
    summary_path.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(markdown_path, json_ready(summary), batch, stage_summary)
    decision_path.write_text(json.dumps(json_ready(decision), indent=2, sort_keys=True), encoding="utf-8")
    write_decision_markdown(decision_markdown_path, json_ready(decision))
    print(f"wrote {executed_path}")
    print(f"wrote {history_path}")
    print(f"wrote {stage_path}")
    print(f"wrote {scores_path}")
    print(f"wrote {batch_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {markdown_path}")
    print(f"wrote {decision_path}")
    print(f"wrote {decision_markdown_path}")
    if not batch.empty:
        print(f"top production proposal: {batch.iloc[0]['candidate_id']}")


if __name__ == "__main__":
    main()
