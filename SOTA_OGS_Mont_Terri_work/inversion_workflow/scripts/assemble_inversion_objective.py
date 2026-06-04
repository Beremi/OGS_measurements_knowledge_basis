#!/usr/bin/env python3
"""Assemble permeability and state-observation objective components."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

STATE_OBJECTIVE_RAW = "raw_absolute_theta"
STATE_OBJECTIVE_NMR_TREND = "nmr_within_label_trend_anomaly"
NMR_GROUP_COLUMNS = ["observation_family", "measurement_label"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--permeability-evaluation",
        type=Path,
        default=Path("inversion_workflow/runs/direct_permeability_fit/permeability_fit_evaluation.csv"),
    )
    parser.add_argument(
        "--permeability-summary",
        type=Path,
        default=Path("inversion_workflow/runs/direct_permeability_fit/permeability_fit_summary.json"),
    )
    parser.add_argument(
        "--state-evaluation",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/state_observation_evaluation.csv"),
    )
    parser.add_argument(
        "--state-summary",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/state_observation_evaluation_summary.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/combined_objective_components.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/combined_objective_summary.json"),
    )
    parser.add_argument(
        "--state-objective-mode",
        choices=[STATE_OBJECTIVE_RAW, STATE_OBJECTIVE_NMR_TREND],
        default=STATE_OBJECTIVE_RAW,
        help=(
            "State-observation residual definition. The default preserves the historical raw "
            "absolute-theta NMR objective. The trend/anomaly mode removes a weighted mean from "
            "each NMR observation_family/measurement_label group before forming residuals."
        ),
    )
    return parser.parse_args()


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def finite(value: Any) -> bool:
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def json_number(value: Any) -> float | None:
    if not finite(value):
        return None
    return float(value)


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return json_number(value)
    if value is pd.NA or value is None:
        return None
    return value


def read_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def finite_sum(frame: pd.DataFrame, column: str) -> float:
    if column not in frame.columns:
        return math.nan
    values = pd.to_numeric(frame[column], errors="coerce")
    values = values[np.isfinite(values)]
    if values.empty:
        return math.nan
    return float(values.sum())


def objective_from_residual(residual: pd.Series | np.ndarray, sigma: pd.Series | np.ndarray) -> float:
    residual_values = pd.to_numeric(pd.Series(residual), errors="coerce").to_numpy(dtype=float)
    sigma_values = pd.to_numeric(pd.Series(sigma), errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(residual_values) & np.isfinite(sigma_values) & (sigma_values > 0.0)
    if not mask.any():
        return math.nan
    normalized = residual_values[mask] / sigma_values[mask]
    return float(0.5 * np.sum(normalized**2))


def rmse_from_objective(objective: float, rows: int) -> float | None:
    if rows <= 0 or not finite(objective):
        return None
    return float(np.sqrt(2.0 * float(objective) / rows))


def status_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    if column not in frame.columns:
        return {}
    return {str(key): int(value) for key, value in frame[column].fillna("").value_counts().to_dict().items()}


def bool_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(False, index=frame.index)
    return frame[column].map(bool_value)


def permeability_component(args: argparse.Namespace) -> dict[str, Any]:
    evaluation = pd.read_csv(args.permeability_evaluation)
    summary = read_summary(args.permeability_summary)
    used = bool_series(evaluation, "used_in_objective")
    objective = finite_sum(evaluation.loc[used], "objective_contribution")
    active = finite(objective)
    return {
        "component": "direct_permeability_pulse_tests",
        "active_in_combined_objective": active,
        "objective_value": json_number(objective),
        "used_rows": int(used.sum()),
        "candidate_rows": int(evaluation.shape[0]),
        "effective_weight": json_number(finite_sum(evaluation.loc[used], "objective_weight")),
        "primary_metric": "weighted_rmse_log10",
        "primary_metric_value": json_number(summary.get("weighted_rmse_log10")),
        "status": "evaluated" if active else "no_finite_objective_rows",
        "source_evaluation": str(args.permeability_evaluation),
        "source_summary": str(args.permeability_summary),
        "notes": "Direct fit of measured pulse-test permeabilities to directional tensor permeability.",
    }


def state_component(args: argparse.Namespace) -> dict[str, Any]:
    evaluation = pd.read_csv(args.state_evaluation)
    summary = read_summary(args.state_summary)
    used = bool_series(evaluation, "used_in_objective")
    mode = getattr(args, "state_objective_mode", STATE_OBJECTIVE_RAW)
    if mode == STATE_OBJECTIVE_NMR_TREND:
        return state_component_nmr_trend(args, evaluation, summary, used)
    objective = finite_sum(evaluation.loc[used], "objective_contribution")
    active = finite(objective)
    counts = status_counts(evaluation, "evaluation_status")
    if active:
        status = "evaluated"
    elif counts == {"no_ogs_state_samples": int(evaluation.shape[0])}:
        status = "waiting_for_ogs_state_outputs"
    else:
        status = "no_finite_objective_rows"
    return {
        "component": "state_observations",
        "active_in_combined_objective": active,
        "objective_value": json_number(objective),
        "used_rows": int(used.sum()),
        "candidate_rows": int(evaluation.shape[0]),
        "effective_weight": json_number(float(used.sum()) if used.sum() else math.nan),
        "primary_metric": "rmse_normalized_residual",
        "primary_metric_value": json_number(summary.get("rmse_normalized_residual")),
        "status": status,
        "source_evaluation": str(args.state_evaluation),
        "source_summary": str(args.state_summary),
        "state_objective_mode": STATE_OBJECTIVE_RAW,
        "notes": (
            "NMR residual layer is prepared, but the sampled OGS outputs must cover usable observation times "
            "and required model quantities before finite rows activate; RH is boundary forcing, Taupe/TDR has "
            "a trend diagnostic, and ERT has calibration plus spatial lookup but still needs support confirmation."
        ),
    }


def nmr_trend_anomaly_objective(active: pd.DataFrame) -> dict[str, Any]:
    if active.empty:
        return {
            "objective": math.nan,
            "rmse_normalized_residual": None,
            "row_count": 0,
            "group_count": 0,
            "excluded_singleton_groups": 0,
        }
    residual_pieces = []
    sigma_pieces = []
    row_count = 0
    group_count = 0
    excluded_singleton_groups = 0
    active = active.copy()
    for column in ["observed_value", "observed_sigma", "predicted_value"]:
        active[column] = pd.to_numeric(active[column], errors="coerce")
    active["observed_sigma"] = active["observed_sigma"].where(active["observed_sigma"] > 0.0, 0.01)
    active["label_group"] = active[NMR_GROUP_COLUMNS].astype(str).agg(" | ".join, axis=1)

    for _label, group in active.groupby("label_group", dropna=False):
        if group.shape[0] < 2:
            excluded_singleton_groups += 1
            continue
        sigma = group["observed_sigma"].to_numpy(dtype=float)
        weights = np.where(np.isfinite(sigma) & (sigma > 0.0), 1.0 / sigma**2, 0.0)
        if weights.sum() <= 0.0:
            continue
        observed = group["observed_value"].to_numpy(dtype=float)
        predicted = group["predicted_value"].to_numpy(dtype=float)
        observed_mean = float(np.average(observed, weights=weights))
        predicted_mean = float(np.average(predicted, weights=weights))
        residual = pd.Series((predicted - predicted_mean) - (observed - observed_mean))
        residual_pieces.append(residual)
        sigma_pieces.append(group["observed_sigma"].reset_index(drop=True))
        row_count += int(group.shape[0])
        group_count += 1

    residual_all = pd.concat(residual_pieces, ignore_index=True) if residual_pieces else pd.Series(dtype=float)
    sigma_all = pd.concat(sigma_pieces, ignore_index=True) if sigma_pieces else pd.Series(dtype=float)
    objective = objective_from_residual(residual_all, sigma_all)
    return {
        "objective": objective,
        "rmse_normalized_residual": rmse_from_objective(objective, row_count),
        "row_count": row_count,
        "group_count": group_count,
        "excluded_singleton_groups": excluded_singleton_groups,
    }


def state_component_nmr_trend(
    args: argparse.Namespace,
    evaluation: pd.DataFrame,
    summary: dict[str, Any],
    used: pd.Series,
) -> dict[str, Any]:
    counts = status_counts(evaluation, "evaluation_status")
    family = evaluation["observation_family"].astype(str) if "observation_family" in evaluation.columns else pd.Series("", index=evaluation.index)
    status = evaluation["evaluation_status"].astype(str) if "evaluation_status" in evaluation.columns else pd.Series("", index=evaluation.index)
    nmr_mask = used & family.str.startswith("NMR") & status.eq("evaluated")
    non_nmr_mask = used & ~family.str.startswith("NMR")
    raw_nmr_objective = finite_sum(evaluation.loc[nmr_mask], "objective_contribution")
    non_nmr_objective = finite_sum(evaluation.loc[non_nmr_mask], "objective_contribution")
    trend = nmr_trend_anomaly_objective(evaluation.loc[nmr_mask])

    objective_terms = []
    if finite(non_nmr_objective):
        objective_terms.append(non_nmr_objective)
    if finite(trend["objective"]):
        objective_terms.append(float(trend["objective"]))
    objective = float(sum(objective_terms)) if objective_terms else math.nan
    active = finite(objective)
    if active:
        component_status = "evaluated"
    elif counts == {"no_ogs_state_samples": int(evaluation.shape[0])}:
        component_status = "waiting_for_ogs_state_outputs"
    else:
        component_status = "no_finite_objective_rows"

    non_nmr_used_rows = int(non_nmr_mask.sum())
    used_rows = non_nmr_used_rows + int(trend["row_count"])
    effective_weight = float(used_rows) if used_rows else math.nan
    return {
        "component": "state_observations",
        "active_in_combined_objective": active,
        "objective_value": json_number(objective),
        "used_rows": used_rows,
        "candidate_rows": int(evaluation.shape[0]),
        "effective_weight": json_number(effective_weight),
        "primary_metric": "nmr_within_label_trend_anomaly_rmse_normalized_residual",
        "primary_metric_value": json_number(trend["rmse_normalized_residual"]),
        "status": component_status,
        "source_evaluation": str(args.state_evaluation),
        "source_summary": str(args.state_summary),
        "state_objective_mode": STATE_OBJECTIVE_NMR_TREND,
        "raw_summary_rmse_normalized_residual": json_number(summary.get("rmse_normalized_residual")),
        "raw_nmr_objective_value": json_number(raw_nmr_objective),
        "non_nmr_state_objective_value": json_number(non_nmr_objective),
        "nmr_trend_anomaly_objective_value": json_number(trend["objective"]),
        "nmr_trend_anomaly_rows": int(trend["row_count"]),
        "nmr_trend_anomaly_groups": int(trend["group_count"]),
        "nmr_trend_anomaly_excluded_singleton_groups": int(trend["excluded_singleton_groups"]),
        "notes": (
            "NMR rows use within-label trend/anomaly residuals: "
            "(theta_model - weighted label mean(theta_model)) - "
            "(theta_NMR_obs - weighted label mean(theta_NMR_obs)). This removes constant "
            "bound/interlayer-water and campaign offsets to first order while preserving the "
            "frozen OGS state variable theta = porosity * liquid_saturation. Non-NMR state rows, "
            "if later activated, retain their precomputed objective contributions."
        ),
    }


def assemble(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    components = pd.DataFrame([permeability_component(args), state_component(args)])
    active = components["active_in_combined_objective"].map(bool_value)
    objective_values = pd.to_numeric(components.loc[active, "objective_value"], errors="coerce")
    objective_values = objective_values[np.isfinite(objective_values)]
    total = float(objective_values.sum()) if not objective_values.empty else math.nan
    summary = {
        "component_count": int(components.shape[0]),
        "active_component_count": int(active.sum()),
        "inactive_component_count": int((~active).sum()),
        "total_active_objective_value": json_number(total),
        "state_objective_mode": getattr(args, "state_objective_mode", STATE_OBJECTIVE_RAW),
        "components": json_ready(components.to_dict(orient="records")),
        "notes": [
            "The combined total includes only components with finite objective rows.",
            "State observations become active only after sampled OGS state outputs cover usable observation times and quantities so numerical residuals can be formed.",
        ],
    }
    return components, summary


def main() -> None:
    args = parse_args()
    components, summary = assemble(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    components.to_csv(args.output, index=False)
    args.summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {args.output}")
    print(f"wrote {args.summary_output}")
    print(f"active objective: {summary['total_active_objective_value']}")


if __name__ == "__main__":
    main()
