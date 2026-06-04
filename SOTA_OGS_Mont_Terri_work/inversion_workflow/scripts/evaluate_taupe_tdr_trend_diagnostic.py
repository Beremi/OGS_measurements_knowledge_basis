#!/usr/bin/env python3
"""Evaluate Taupe/TDR trend anomalies against sampled OGS state outputs.

This diagnostic keeps Taupe/TDR out of the active likelihood.  It compares the
baseline-normalized Taupe workbook trend with the matching baseline-normalized
model trend in theta = porosity * liquid_saturation for each mapped sensor and
EDZ band.
"""

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
STATE_QUANTITY = "theta_from_porosity_times_saturation"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--taupe-operator",
        type=Path,
        default=Path("inversion_workflow/processed_observations/taupe_tdr_trend_operator.csv"),
    )
    parser.add_argument(
        "--taupe-bands",
        type=Path,
        default=Path("inversion_workflow/processed_observations/taupe_tdr_bands.csv"),
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
        "--state-quantity",
        default=STATE_QUANTITY,
        help="Sampled OGS state-sample column to compare as the model-side theta proxy.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/taupe_tdr_trend_diagnostic.csv"),
    )
    parser.add_argument(
        "--series-output",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/taupe_tdr_trend_diagnostic_series.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/taupe_tdr_trend_diagnostic_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/taupe_tdr_trend_diagnostic.md"),
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
        help="Maximum allowed absolute time mismatch between Taupe row and nearest OGS output.",
    )
    return parser.parse_args()


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
    return outputs.loc[deltas.idxmin()]


def robust_scale(values: pd.Series, fallback_center: float, fallback_floor: float = 1e-4) -> float:
    numeric = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    numeric = numeric[np.isfinite(numeric)]
    if numeric.size == 0:
        return fallback_floor
    median = float(np.median(numeric))
    mad = float(1.4826 * np.median(np.abs(numeric - median)))
    if mad > 1e-12:
        return mad
    if numeric.size > 1:
        std = float(np.std(numeric, ddof=1))
        if std > 1e-12:
            return std
    if finite(fallback_center):
        return max(abs(float(fallback_center)) * 0.01, fallback_floor)
    return fallback_floor


def add_target_ids(operator: pd.DataFrame, taupe_bands: pd.DataFrame) -> pd.DataFrame:
    bands = taupe_bands.reset_index(names="source_row_key").copy()
    merge_columns = [
        "source_file",
        "source_sheet",
        "sensor",
        "date_iso",
        "source_column",
        "edz_band_cm",
        "edz_min_cm",
        "edz_max_cm",
        "taupe_value",
    ]
    merged = operator.merge(
        bands[merge_columns + ["source_row_key"]],
        on=merge_columns,
        how="left",
        validate="many_to_one",
    )
    merged["source_row_key"] = pd.to_numeric(merged["source_row_key"], errors="coerce")
    merged["target_id"] = merged["source_row_key"].map(
        lambda value: f"taupe_{int(value):05d}" if np.isfinite(value) else ""
    )
    return merged


def build_state_index(state_samples: pd.DataFrame) -> pd.DataFrame:
    if state_samples.empty:
        return pd.DataFrame()
    return (
        state_samples.sort_values(["output_file", "lookup_cell_id"])
        .drop_duplicates(["output_file", "lookup_cell_id"])
        .set_index(["output_file", "lookup_cell_id"])
    )


def weighted_state_average(
    target_id: str,
    target_samples: pd.DataFrame,
    state_by_output_cell: pd.DataFrame,
    output_file: str,
    quantity: str,
) -> tuple[float, int, float]:
    rows = target_samples[target_samples["target_id"].astype(str).eq(target_id)]
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


def compare_rows(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], str]:
    operator = add_target_ids(pd.read_csv(args.taupe_operator), pd.read_csv(args.taupe_bands))
    target_samples = pd.read_csv(args.target_samples)
    origin = datetime.fromisoformat(args.time_origin)
    state_samples = load_state_samples(args.ogs_state_samples, origin)
    outputs = output_times(state_samples)
    state_by_output_cell = build_state_index(state_samples)
    max_delta_seconds = args.max_time_delta_days * 86400.0

    rows: list[dict[str, Any]] = []
    for _, row in operator.iterrows():
        target_time = parse_datetime(row["date_iso"])
        matched = nearest_output(target_time, outputs)
        output_file = "" if matched is None else str(matched["output_file"])
        matched_time = pd.NaT if matched is None else pd.Timestamp(matched["simulated_datetime"])
        time_delta_seconds = math.nan if matched is None or pd.isna(target_time) else float(
            (matched_time - target_time).total_seconds()
        )
        predicted, sample_count, sample_weight = (math.nan, 0, math.nan)
        status = "not_evaluated"

        if state_samples.empty:
            status = "no_ogs_state_samples"
        elif not str(row.get("operator_status", "")).startswith("trend_operator_ready"):
            status = "operator_not_mapped_for_current_mesh"
        elif not str(row.get("target_id", "")):
            status = "missing_taupe_target_id"
        elif matched is None:
            status = "no_matching_ogs_output_time"
        elif not finite(time_delta_seconds) or abs(time_delta_seconds) > max_delta_seconds:
            status = "outside_time_tolerance"
        else:
            predicted, sample_count, sample_weight = weighted_state_average(
                str(row["target_id"]),
                target_samples,
                state_by_output_cell,
                output_file,
                args.state_quantity,
            )
            status = "trend_compared" if finite(predicted) and sample_count > 0 else "missing_model_state_quantity"

        rows.append(
            {
                "target_id": row.get("target_id", ""),
                "source_row_key": row.get("source_row_key", math.nan),
                "series_id": row["series_id"],
                "sensor": row["sensor"],
                "edz_band_cm": row["edz_band_cm"],
                "date_iso": row["date_iso"],
                "matched_output_file": output_file,
                "matched_model_time_s": math.nan if matched is None else float(matched["time_s"]),
                "matched_model_datetime": "" if pd.isna(matched_time) else matched_time.isoformat(),
                "time_delta_days_model_minus_obs": (
                    time_delta_seconds / 86400.0 if finite(time_delta_seconds) else math.nan
                ),
                "diagnostic_status": status,
                "operator_status": row["operator_status"],
                "mapping_status": row["mapping_status"],
                "taupe_value": row["taupe_value"],
                "taupe_baseline_value": row["baseline_taupe_value"],
                "taupe_delta_from_baseline": row["taupe_delta_from_baseline"],
                "taupe_relative_change_percent": row["taupe_relative_change_percent"],
                "taupe_robust_scale": row["taupe_robust_scale"],
                "taupe_standardized_anomaly": row["taupe_standardized_anomaly"],
                "model_quantity": args.state_quantity,
                "model_theta_value": predicted,
                "sample_count": sample_count,
                "sample_weight_sum": sample_weight,
                "band_mean_porosity": row["band_mean_porosity"],
                "absolute_calibration_note": row["absolute_calibration_note"],
            }
        )

    diagnostic = pd.DataFrame(rows)
    diagnostic = add_model_trends(diagnostic)
    series = summarize_series(diagnostic)
    summary = build_summary(args, diagnostic, series, state_samples, outputs)
    markdown = write_markdown_text(summary, series)
    return diagnostic, series, summary, markdown


def add_model_trends(diagnostic: pd.DataFrame) -> pd.DataFrame:
    frame = diagnostic.copy()
    frame["model_theta_baseline"] = math.nan
    frame["model_theta_delta_from_baseline"] = math.nan
    frame["model_theta_relative_change_percent"] = math.nan
    frame["model_theta_robust_scale"] = math.nan
    frame["model_theta_standardized_anomaly"] = math.nan
    frame["trend_residual_standardized_model_minus_taupe"] = math.nan
    frame["abs_trend_residual_standardized"] = math.nan

    compared = frame["diagnostic_status"].astype(str).eq("trend_compared")
    for series_id, group in frame[compared].groupby("series_id", sort=False):
        baseline_start = pd.to_datetime(group["date_iso"], errors="coerce").min()
        # The Taupe operator uses the first three finite dates as the baseline.
        baseline_dates = (
            group.sort_values("date_iso")["date_iso"].drop_duplicates().head(3).astype(str).tolist()
        )
        baseline_group = group[group["date_iso"].astype(str).isin(baseline_dates)]
        baseline = float(pd.to_numeric(baseline_group["model_theta_value"], errors="coerce").mean())
        scale = robust_scale(pd.to_numeric(group["model_theta_value"], errors="coerce"), baseline)
        idx = group.index
        model = pd.to_numeric(frame.loc[idx, "model_theta_value"], errors="coerce")
        delta = model - baseline
        frame.loc[idx, "model_theta_baseline"] = baseline
        frame.loc[idx, "model_theta_delta_from_baseline"] = delta
        frame.loc[idx, "model_theta_relative_change_percent"] = np.where(
            finite(baseline) and baseline != 0.0,
            100.0 * delta / baseline,
            math.nan,
        )
        frame.loc[idx, "model_theta_robust_scale"] = scale
        frame.loc[idx, "model_theta_standardized_anomaly"] = delta / scale if scale > 0.0 else math.nan
        frame.loc[idx, "trend_residual_standardized_model_minus_taupe"] = (
            frame.loc[idx, "model_theta_standardized_anomaly"]
            - pd.to_numeric(frame.loc[idx, "taupe_standardized_anomaly"], errors="coerce")
        )
        frame.loc[idx, "abs_trend_residual_standardized"] = frame.loc[
            idx, "trend_residual_standardized_model_minus_taupe"
        ].abs()

        if pd.isna(baseline_start):
            continue
    return frame


def correlation(x: pd.Series, y: pd.Series) -> float:
    clean = pd.DataFrame({"x": pd.to_numeric(x, errors="coerce"), "y": pd.to_numeric(y, errors="coerce")}).dropna()
    if clean.shape[0] < 3:
        return math.nan
    if clean["x"].std(ddof=1) <= 1e-12 or clean["y"].std(ddof=1) <= 1e-12:
        return math.nan
    return float(clean["x"].corr(clean["y"]))


def sign_agreement(x: pd.Series, y: pd.Series) -> float:
    clean = pd.DataFrame({"x": pd.to_numeric(x, errors="coerce"), "y": pd.to_numeric(y, errors="coerce")}).dropna()
    clean = clean[(clean["x"].abs() > 1e-12) & (clean["y"].abs() > 1e-12)]
    if clean.empty:
        return math.nan
    return float((np.sign(clean["x"]) == np.sign(clean["y"])).mean())


def summarize_series(diagnostic: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for series_id, group in diagnostic.groupby("series_id", sort=True):
        compared = group[group["diagnostic_status"].eq("trend_compared")]
        residual = pd.to_numeric(compared["trend_residual_standardized_model_minus_taupe"], errors="coerce")
        rows.append(
            {
                "series_id": series_id,
                "sensor": str(group["sensor"].iloc[0]),
                "edz_band_cm": str(group["edz_band_cm"].iloc[0]),
                "row_count": int(group.shape[0]),
                "compared_rows": int(compared.shape[0]),
                "diagnostic_statuses": "; ".join(
                    f"{key}={value}" for key, value in group["diagnostic_status"].value_counts().sort_index().items()
                ),
                "date_min": str(pd.to_datetime(group["date_iso"], errors="coerce").min().date()),
                "date_max": str(pd.to_datetime(group["date_iso"], errors="coerce").max().date()),
                "compared_date_min": (
                    str(pd.to_datetime(compared["date_iso"], errors="coerce").min().date())
                    if not compared.empty
                    else ""
                ),
                "compared_date_max": (
                    str(pd.to_datetime(compared["date_iso"], errors="coerce").max().date())
                    if not compared.empty
                    else ""
                ),
                "mean_abs_time_delta_days": json_number(
                    pd.to_numeric(compared["time_delta_days_model_minus_obs"], errors="coerce").abs().mean()
                ),
                "model_taupe_standardized_pearson": json_number(
                    correlation(compared["model_theta_standardized_anomaly"], compared["taupe_standardized_anomaly"])
                ),
                "delta_sign_agreement_fraction": json_number(
                    sign_agreement(compared["model_theta_delta_from_baseline"], compared["taupe_delta_from_baseline"])
                ),
                "standardized_residual_mean": json_number(residual.mean()),
                "standardized_residual_mae": json_number(residual.abs().mean()),
                "standardized_residual_rmse": json_number(np.sqrt(np.mean(residual.dropna() ** 2)) if residual.notna().any() else math.nan),
                "taupe_standardized_min": json_number(compared["taupe_standardized_anomaly"].min()),
                "taupe_standardized_max": json_number(compared["taupe_standardized_anomaly"].max()),
                "model_standardized_min": json_number(compared["model_theta_standardized_anomaly"].min()),
                "model_standardized_max": json_number(compared["model_theta_standardized_anomaly"].max()),
                "model_theta_min": json_number(compared["model_theta_value"].min()),
                "model_theta_max": json_number(compared["model_theta_value"].max()),
                "model_theta_baseline": json_number(compared["model_theta_baseline"].dropna().iloc[0])
                if compared["model_theta_baseline"].notna().any()
                else None,
                "model_theta_robust_scale": json_number(compared["model_theta_robust_scale"].dropna().iloc[0])
                if compared["model_theta_robust_scale"].notna().any()
                else None,
            }
        )
    return pd.DataFrame(rows)


def value_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    if frame.empty or column not in frame.columns:
        return {}
    return {str(key): int(value) for key, value in frame[column].value_counts().sort_index().items()}


def build_summary(
    args: argparse.Namespace,
    diagnostic: pd.DataFrame,
    series: pd.DataFrame,
    state_samples: pd.DataFrame,
    outputs: pd.DataFrame,
) -> dict[str, Any]:
    compared = diagnostic[diagnostic["diagnostic_status"].eq("trend_compared")]
    residual = pd.to_numeric(compared["trend_residual_standardized_model_minus_taupe"], errors="coerce")
    return {
        "status": "taupe_trend_diagnostic_generated_not_active_likelihood",
        "taupe_operator": str(args.taupe_operator),
        "taupe_bands": str(args.taupe_bands),
        "target_samples": str(args.target_samples),
        "ogs_state_samples": str(args.ogs_state_samples),
        "state_quantity": args.state_quantity,
        "time_origin": args.time_origin,
        "max_time_delta_days": args.max_time_delta_days,
        "state_sample_rows": int(state_samples.shape[0]),
        "ogs_output_times": int(outputs.shape[0]),
        "diagnostic_rows": int(diagnostic.shape[0]),
        "compared_rows": int(compared.shape[0]),
        "series_rows": int(series.shape[0]),
        "compared_series": int(series["compared_rows"].gt(0).sum()) if "compared_rows" in series else 0,
        "diagnostic_status_counts": value_counts(diagnostic, "diagnostic_status"),
        "mean_abs_time_delta_days": json_number(
            pd.to_numeric(compared["time_delta_days_model_minus_obs"], errors="coerce").abs().mean()
        ),
        "standardized_residual": {
            "mean": json_number(residual.mean()),
            "mae": json_number(residual.abs().mean()),
            "rmse": json_number(np.sqrt(np.mean(residual.dropna() ** 2)) if residual.notna().any() else math.nan),
            "p50_abs": json_number(residual.abs().quantile(0.50)),
            "p90_abs": json_number(residual.abs().quantile(0.90)),
        },
        "notes": [
            "This file is diagnostic only and is not assembled into the active objective.",
            "Taupe/TDR absolute residuals remain blocked until the Taupe_WC workbook unit and sensor calibration are documented.",
            "Rows after the available OGS output time horizon are marked outside_time_tolerance.",
            "A7/A8 rows remain outside the current local mesh support; A3/A4 mapped rows can be compared as trends.",
        ],
    }


def write_markdown_text(summary: dict[str, Any], series: pd.DataFrame) -> str:
    residual = summary["standardized_residual"]
    lines = [
        "# Taupe/TDR Trend Diagnostic",
        "",
        "This run-local diagnostic compares the Taupe/TDR baseline-normalized trend operator with sampled OGS `theta = porosity * liquid_saturation`. It is not part of the active objective.",
        "",
        "## Status",
        "",
        f"- Status: `{summary['status']}`",
        f"- OGS state samples: `{summary['ogs_state_samples']}`",
        f"- State sample rows: {summary['state_sample_rows']}",
        f"- OGS output times: {summary['ogs_output_times']}",
        f"- Diagnostic rows: {summary['diagnostic_rows']}",
        f"- Compared rows: {summary['compared_rows']}",
        f"- Compared series: {summary['compared_series']} of {summary['series_rows']}",
        f"- Mean absolute time mismatch: {summary['mean_abs_time_delta_days']}",
        "",
        "## Status Counts",
        "",
        "| Diagnostic status | Rows |",
        "| --- | ---: |",
    ]
    for key, value in summary["diagnostic_status_counts"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Standardized Trend Residual",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| Mean | {residual['mean']} |",
            f"| MAE | {residual['mae']} |",
            f"| RMSE | {residual['rmse']} |",
            f"| Median absolute | {residual['p50_abs']} |",
            f"| 90th percentile absolute | {residual['p90_abs']} |",
            "",
            "The residual is `model_theta_standardized_anomaly - taupe_standardized_anomaly`. It is useful for comparing trend shape and timing, not for assigning calibrated Taupe absolute water-content or saturation weights.",
            "",
            "## Series Summary",
            "",
            "| Series | Compared | Corr | Sign agree | MAE | Taupe std min/max | Model std min/max | Compared dates |",
            "| --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    if not series.empty:
        for _, row in series.sort_values("series_id").iterrows():
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(row["series_id"]),
                        str(int(row["compared_rows"])),
                        str(row["model_taupe_standardized_pearson"]),
                        str(row["delta_sign_agreement_fraction"]),
                        str(row["standardized_residual_mae"]),
                        f"{row['taupe_standardized_min']} / {row['taupe_standardized_max']}",
                        f"{row['model_standardized_min']} / {row['model_standardized_max']}",
                        f"{row['compared_date_min']} to {row['compared_date_max']}",
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Interpretation Gate",
            "",
            "Use this as a diagnostic screen for whether the current OGS candidate produces Taupe-like temporal trends in mapped A3/A4 EDZ bands. Do not promote it to a likelihood until the Taupe workbook unit/calibration and an uncertainty model are confirmed.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    diagnostic, series, summary, markdown = compare_rows(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    diagnostic.to_csv(args.output, index=False)
    series.to_csv(args.series_output, index=False)
    args.summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    args.markdown_output.write_text(markdown, encoding="utf-8")
    print(f"wrote {args.output}")
    print(f"wrote {args.series_output}")
    print(f"wrote {args.summary_output}")
    print(f"wrote {args.markdown_output}")
    print(f"compared rows: {summary['compared_rows']}")


if __name__ == "__main__":
    main()
