#!/usr/bin/env python3
"""Evaluate state-observation targets against sampled OGS state outputs."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_ORIGIN = "2019-09-18T00:00:00"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--targets",
        type=Path,
        default=Path("inversion_workflow/processed_observations/state_observation_targets.csv"),
    )
    parser.add_argument(
        "--target-samples",
        type=Path,
        default=Path("inversion_workflow/processed_observations/state_observation_samples.csv"),
    )
    parser.add_argument(
        "--ogs-state-samples",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/ogs_state_samples.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/state_observation_evaluation.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/state_observation_evaluation_summary.json"),
    )
    parser.add_argument(
        "--time-origin",
        default=DEFAULT_ORIGIN,
        help="Model time origin for converting OGS seconds to calendar dates.",
    )
    parser.add_argument(
        "--max-time-delta-days",
        type=float,
        default=20.0,
        help="Maximum allowed absolute time mismatch for numerical state residuals.",
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


def parse_datetime(value: Any) -> pd.Timestamp:
    return pd.to_datetime(value, errors="coerce")


def load_state_samples(path: Path, origin: datetime) -> pd.DataFrame:
    samples = pd.read_csv(path)
    if samples.empty:
        return samples
    samples["time_s"] = pd.to_numeric(samples["time_s"], errors="coerce")
    samples["simulated_datetime"] = [
        origin + timedelta(seconds=float(seconds)) if np.isfinite(seconds) else pd.NaT
        for seconds in samples["time_s"].to_numpy(dtype=float)
    ]
    return samples


def output_times(samples: pd.DataFrame) -> pd.DataFrame:
    if samples.empty:
        return pd.DataFrame(columns=["output_file", "time_s", "simulated_datetime"])
    return samples[["output_file", "time_s", "simulated_datetime"]].drop_duplicates().sort_values("time_s")


def nearest_output(target_time: pd.Timestamp, outputs: pd.DataFrame) -> pd.Series | None:
    if pd.isna(target_time) or outputs.empty:
        return None
    deltas = outputs["simulated_datetime"].map(lambda value: abs((pd.Timestamp(value) - target_time).total_seconds()))
    index = deltas.idxmin()
    return outputs.loc[index]


def weighted_state_average(
    target_id: str,
    target_samples: pd.DataFrame,
    state_by_output_cell: pd.DataFrame,
    output_file: str,
    quantity: str,
) -> tuple[float, int, float]:
    rows = target_samples[target_samples["target_id"] == target_id]
    if rows.empty:
        return math.nan, 0, math.nan

    weighted_sum = 0.0
    weight_sum = 0.0
    used = 0
    for _, row in rows.iterrows():
        cell_id = int(row["lookup_cell_id"])
        key = (output_file, cell_id)
        if key not in state_by_output_cell.index:
            continue
        value = state_by_output_cell.loc[key].get(quantity, math.nan)
        if isinstance(value, pd.Series):
            value = value.iloc[0]
        if not finite(value):
            continue
        weight = float(row["cell_weight"])
        weighted_sum += weight * float(value)
        weight_sum += weight
        used += 1
    if weight_sum <= 0.0:
        return math.nan, used, math.nan
    return weighted_sum / weight_sum, used, weight_sum


def target_model_quantity(family: str) -> tuple[str, str]:
    if family.startswith("NMR"):
        return "theta_from_porosity_times_saturation", "numerical_residual"
    if family == "Taupe/TDR":
        return "theta_from_porosity_times_saturation", "diagnostic_prediction_only"
    if family == "Suction/RH":
        return "pressure", "boundary_forcing_not_cell_residual"
    if family == "ERT open-niche time series":
        return "theta_from_porosity_times_saturation", "external_projection_required"
    return "", "unsupported_family"


def evaluate(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    targets = pd.read_csv(args.targets)
    target_samples = pd.read_csv(args.target_samples)
    origin = datetime.fromisoformat(args.time_origin)
    state_samples = load_state_samples(args.ogs_state_samples, origin)
    outputs = output_times(state_samples)

    if state_samples.empty:
        state_by_output_cell = pd.DataFrame()
    else:
        # Multiple generic sampler rows can point to the same cell.  Keep the first
        # finite state sample per output/cell; target-specific weights are applied below.
        state_by_output_cell = (
            state_samples.sort_values(["output_file", "lookup_cell_id"])
            .drop_duplicates(["output_file", "lookup_cell_id"])
            .set_index(["output_file", "lookup_cell_id"])
        )

    rows: list[dict[str, Any]] = []
    max_delta_seconds = args.max_time_delta_days * 86400.0

    for _, target in targets.iterrows():
        family = str(target["observation_family"])
        quantity, evaluation_role = target_model_quantity(family)
        target_time = parse_datetime(target["date_iso"])
        matched = nearest_output(target_time, outputs)
        output_file = "" if matched is None else str(matched["output_file"])
        model_time_s = math.nan if matched is None else float(matched["time_s"])
        matched_time = pd.NaT if matched is None else pd.Timestamp(matched["simulated_datetime"])
        time_delta_seconds = math.nan if matched is None or pd.isna(target_time) else float((matched_time - target_time).total_seconds())

        predicted, sample_count, sample_weight = (math.nan, 0, math.nan)
        status = "not_evaluated"
        used_in_objective = False
        residual = math.nan
        normalized = math.nan
        objective = math.nan

        target_usable = bool_value(target["usable_for_current_state_fit"])
        if state_samples.empty:
            status = "no_ogs_state_samples"
        elif evaluation_role == "boundary_forcing_not_cell_residual":
            status = "boundary_forcing_target_no_state_residual"
        elif evaluation_role == "external_projection_required":
            status = "external_projection_required"
        elif not target_usable:
            status = "target_not_usable_for_current_state_fit"
        elif matched is None:
            status = "no_matching_ogs_output_time"
        elif not finite(time_delta_seconds) or abs(time_delta_seconds) > max_delta_seconds:
            status = "outside_time_tolerance"
        else:
            predicted, sample_count, sample_weight = weighted_state_average(
                str(target["target_id"]),
                target_samples,
                state_by_output_cell,
                output_file,
                quantity,
            )
            if sample_count == 0 or not finite(predicted):
                status = "missing_model_state_quantity"
            elif evaluation_role == "diagnostic_prediction_only":
                status = "diagnostic_prediction_only"
            else:
                observed = float(target["observed_value"])
                sigma = float(target["observed_sigma"]) if finite(target["observed_sigma"]) else math.nan
                if not finite(observed) or not finite(sigma) or sigma <= 0.0:
                    status = "missing_observation_or_sigma"
                else:
                    residual = float(predicted) - observed
                    normalized = residual / sigma
                    objective = 0.5 * normalized**2
                    status = "evaluated"
                    used_in_objective = True

        rows.append(
            {
                "target_id": target["target_id"],
                "observation_family": family,
                "measurement_label": target["measurement_label"],
                "target_date_iso": target["date_iso"],
                "matched_output_file": output_file,
                "matched_model_time_s": model_time_s,
                "matched_model_datetime": "" if pd.isna(matched_time) else matched_time.isoformat(),
                "time_delta_days_model_minus_obs": (
                    time_delta_seconds / 86400.0 if finite(time_delta_seconds) else math.nan
                ),
                "target_status": target["target_status"],
                "evaluation_status": status,
                "evaluation_role": evaluation_role,
                "used_in_objective": used_in_objective,
                "observed_quantity": target["observed_quantity"],
                "observed_value": target["observed_value"],
                "observed_sigma": target["observed_sigma"],
                "model_quantity": quantity,
                "predicted_value": predicted,
                "sample_count": sample_count,
                "sample_weight_sum": sample_weight,
                "residual_pred_minus_obs": residual,
                "normalized_residual": normalized,
                "objective_contribution": objective,
                "uncertainty_note": target["uncertainty_note"],
                "caveat": target["caveat"],
            }
        )

    evaluation = pd.DataFrame(rows)
    finite_objective = evaluation[evaluation["used_in_objective"] & np.isfinite(evaluation["objective_contribution"])].copy()
    objective_value = finite_objective["objective_contribution"].sum() if not finite_objective.empty else math.nan
    rmse_normalized = (
        np.sqrt(np.mean(finite_objective["normalized_residual"] ** 2)) if not finite_objective.empty else math.nan
    )
    summary = {
        "targets": str(args.targets),
        "target_samples": str(args.target_samples),
        "ogs_state_samples": str(args.ogs_state_samples),
        "time_origin": args.time_origin,
        "max_time_delta_days": args.max_time_delta_days,
        "state_sample_rows": int(state_samples.shape[0]),
        "ogs_output_times": int(outputs.shape[0]),
        "evaluation_rows": int(evaluation.shape[0]),
        "used_in_objective_rows": int(finite_objective.shape[0]),
        "objective_value": json_number(objective_value),
        "rmse_normalized_residual": json_number(rmse_normalized),
        "evaluation_status_counts": evaluation["evaluation_status"].value_counts().to_dict(),
        "status_by_family": {
            str(key): int(value)
            for key, value in evaluation.groupby(["observation_family", "evaluation_status"]).size().to_dict().items()
        },
        "notes": [
            "NMR residuals compare observed volumetric water content to model porosity*saturation.",
            "Taupe/TDR rows are diagnostic predictions only; taupe_tdr_trend_operator.csv defines the baseline-normalized trend operator while absolute calibration remains pending.",
            "RH rows are boundary-forcing targets and are not treated as point residuals here.",
            "ERT rows have theta-to-resistivity calibration and ERT-to-OGS spatial lookup artifacts, but still require transform/support confirmation and OGS state outputs before numerical residuals.",
        ],
    }
    return evaluation, summary


def main() -> None:
    args = parse_args()
    evaluation, summary = evaluate(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    evaluation.to_csv(args.output, index=False)
    args.summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {args.output}")
    print(f"wrote {args.summary_output}")
    print(f"used state objective rows: {summary['used_in_objective_rows']}")


if __name__ == "__main__":
    main()
