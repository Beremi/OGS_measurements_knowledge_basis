#!/usr/bin/env python3
"""Audit the uncertainty envelope of local RH-derived boundary candidates.

The candidate-curve builder makes several reproducible RH-derived open-niche
boundary forcings from the copied OT_RH5--8 workbooks.  This script treats those
candidates as a local policy ensemble.  It quantifies the daily spread among
sensor-selection policies, checks where the active OGS curve falls inside that
local envelope over the overlap, and records the post-active-curve extension
evidence.  It is diagnostic only; it does not activate RH/suction as a likelihood.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PREFERRED_CANDIDATE = "rh5_rh6_median"
AFTER_ACTIVE_STATUS = "after_active_curve_time_range_requires_curve_extension_or_new_forcing"
OVERLAP_STATUS = "compared_to_active_curve"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate-curves",
        type=Path,
        default=Path("inversion_workflow/processed_observations/rh_boundary_candidate_curves.csv"),
    )
    parser.add_argument(
        "--candidate-summary",
        type=Path,
        default=Path("inversion_workflow/processed_observations/rh_boundary_candidate_curve_summary.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/suction_relative_humidity"),
        help="Measurement-catalogue directory where derived audit copies are stored.",
    )
    return parser.parse_args()


def finite(value: Any) -> bool:
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


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
        return None if not np.isfinite(float(value)) else float(value)
    if value is pd.NA or value is None:
        return None
    return value


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def quantile_stats(series: pd.Series) -> dict[str, float | None]:
    values = pd.to_numeric(series, errors="coerce")
    values = values[np.isfinite(values)]
    if values.empty:
        return {key: None for key in ["min", "p10", "p25", "p50", "p75", "p90", "max", "mean"]}
    return {
        "min": float(values.min()),
        "p10": float(values.quantile(0.10)),
        "p25": float(values.quantile(0.25)),
        "p50": float(values.quantile(0.50)),
        "p75": float(values.quantile(0.75)),
        "p90": float(values.quantile(0.90)),
        "max": float(values.max()),
        "mean": float(values.mean()),
    }


def metric_stats(series: pd.Series) -> dict[str, float | None]:
    values = pd.to_numeric(series, errors="coerce")
    values = values[np.isfinite(values)]
    if values.empty:
        return {key: None for key in ["min", "median", "mean", "mae", "rmse", "max", "p90"]}
    return {
        "min": float(values.min()),
        "median": float(values.median()),
        "mean": float(values.mean()),
        "mae": float(values.abs().mean()),
        "rmse": float(np.sqrt(np.mean(np.square(values)))),
        "max": float(values.max()),
        "p90": float(values.quantile(0.90)),
    }


def require_columns(frame: pd.DataFrame, path: Path) -> None:
    required = {
        "candidate_id",
        "date",
        "model_time_s",
        "rh_percent_aggregate",
        "liquid_pressure_gauge_mpa_kelvin",
        "source_row_count",
        "source_sensors",
        "comparison_status",
        "active_ogs_pressure_pa_interp",
        "residual_candidate_minus_active_mpa",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")


def build_envelope(curves: pd.DataFrame, preferred_id: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for date, group in curves.groupby("date", sort=True):
        pressure = pd.to_numeric(group["liquid_pressure_gauge_mpa_kelvin"], errors="coerce")
        rh_percent = pd.to_numeric(group["rh_percent_aggregate"], errors="coerce")
        active = pd.to_numeric(group["active_ogs_pressure_pa_interp"], errors="coerce") / 1.0e6
        active = active[np.isfinite(active)]
        pressure = pressure[np.isfinite(pressure)]
        rh_percent = rh_percent[np.isfinite(rh_percent)]
        if pressure.empty:
            continue
        statuses = sorted(group["comparison_status"].dropna().astype(str).unique().tolist())
        preferred = group[group["candidate_id"].astype(str).eq(preferred_id)]
        preferred_pressure = None
        preferred_minus_envelope_median = None
        if not preferred.empty:
            preferred_values = pd.to_numeric(preferred["liquid_pressure_gauge_mpa_kelvin"], errors="coerce")
            preferred_values = preferred_values[np.isfinite(preferred_values)]
            if not preferred_values.empty:
                preferred_pressure = float(preferred_values.iloc[0])
                preferred_minus_envelope_median = float(preferred_pressure - pressure.median())
        active_pressure = float(active.iloc[0]) if not active.empty else None
        active_inside = None
        active_minus_median = None
        if active_pressure is not None:
            active_inside = bool(pressure.min() <= active_pressure <= pressure.max())
            active_minus_median = float(active_pressure - pressure.median())
        rows.append(
            {
                "date": str(date),
                "model_time_s_min": float(pd.to_numeric(group["model_time_s"], errors="coerce").min()),
                "model_time_s_max": float(pd.to_numeric(group["model_time_s"], errors="coerce").max()),
                "comparison_regime": ";".join(statuses),
                "candidate_count": int(group["candidate_id"].nunique()),
                "candidate_ids": ";".join(sorted(group["candidate_id"].astype(str).unique().tolist())),
                "source_sensors": ";".join(sorted(group["source_sensors"].astype(str).unique().tolist())),
                "source_row_count_total": int(pd.to_numeric(group["source_row_count"], errors="coerce").fillna(0).sum()),
                "rh_percent_min": float(rh_percent.min()) if not rh_percent.empty else None,
                "rh_percent_median": float(rh_percent.median()) if not rh_percent.empty else None,
                "rh_percent_max": float(rh_percent.max()) if not rh_percent.empty else None,
                "rh_percent_range": float(rh_percent.max() - rh_percent.min()) if not rh_percent.empty else None,
                "pressure_mpa_min": float(pressure.min()),
                "pressure_mpa_median": float(pressure.median()),
                "pressure_mpa_max": float(pressure.max()),
                "pressure_mpa_range": float(pressure.max() - pressure.min()),
                "pressure_mpa_std": float(pressure.std(ddof=0)) if len(pressure) > 1 else 0.0,
                "preferred_candidate_id": preferred_id,
                "preferred_pressure_mpa": preferred_pressure,
                "preferred_minus_envelope_median_mpa": preferred_minus_envelope_median,
                "active_ogs_pressure_mpa": active_pressure,
                "active_inside_candidate_envelope": active_inside,
                "active_minus_envelope_median_mpa": active_minus_median,
                "active_abs_minus_envelope_median_mpa": abs(active_minus_median)
                if active_minus_median is not None
                else None,
            }
        )
    return pd.DataFrame(rows)


def candidate_policy_rows(curves: pd.DataFrame, preferred_id: str) -> pd.DataFrame:
    preferred = curves[curves["candidate_id"].astype(str).eq(preferred_id)][
        ["date", "liquid_pressure_gauge_mpa_kelvin"]
    ].rename(columns={"liquid_pressure_gauge_mpa_kelvin": "preferred_pressure_mpa"})
    rows: list[dict[str, Any]] = []
    for candidate_id, group in curves.groupby("candidate_id", sort=True):
        compared = group[group["comparison_status"].astype(str).eq(OVERLAP_STATUS)]
        after_active = group[group["comparison_status"].astype(str).eq(AFTER_ACTIVE_STATUS)]
        joined = group[["date", "liquid_pressure_gauge_mpa_kelvin"]].merge(preferred, on="date", how="inner")
        delta = pd.to_numeric(joined["liquid_pressure_gauge_mpa_kelvin"], errors="coerce") - pd.to_numeric(
            joined["preferred_pressure_mpa"], errors="coerce"
        )
        abs_delta = delta.abs()
        overlap_residual = pd.to_numeric(compared["residual_candidate_minus_active_mpa"], errors="coerce")
        abs_overlap_residual = overlap_residual.abs()
        rows.append(
            {
                "candidate_id": str(candidate_id),
                "rows": int(group.shape[0]),
                "date_min": str(group["date"].min()),
                "date_max": str(group["date"].max()),
                "compared_to_active_curve_rows": int(compared.shape[0]),
                "after_active_curve_rows": int(after_active.shape[0]),
                "source_row_count_total": int(pd.to_numeric(group["source_row_count"], errors="coerce").fillna(0).sum()),
                "source_sensors": ";".join(sorted(group["source_sensors"].astype(str).unique().tolist())),
                "median_sensor_count": float(pd.to_numeric(group["sensor_count"], errors="coerce").median())
                if "sensor_count" in group.columns
                else None,
                "pressure_mpa_p50": quantile_stats(group["liquid_pressure_gauge_mpa_kelvin"])["p50"],
                "pressure_mpa_range": float(
                    pd.to_numeric(group["liquid_pressure_gauge_mpa_kelvin"], errors="coerce").max()
                    - pd.to_numeric(group["liquid_pressure_gauge_mpa_kelvin"], errors="coerce").min()
                ),
                "overlap_abs_residual_mpa_mae": metric_stats(overlap_residual)["mae"],
                "overlap_abs_residual_mpa_median": metric_stats(abs_overlap_residual)["median"],
                "overlap_residual_mpa_rmse": metric_stats(overlap_residual)["rmse"],
                "dates_with_preferred_overlap": int(joined.shape[0]),
                "abs_delta_vs_preferred_mpa_median": metric_stats(abs_delta)["median"],
                "abs_delta_vs_preferred_mpa_mae": metric_stats(delta)["mae"],
                "abs_delta_vs_preferred_mpa_p90": metric_stats(abs_delta)["p90"],
            }
        )
    return pd.DataFrame(rows)


def regime_summary(envelope: pd.DataFrame, regime: str) -> dict[str, Any]:
    subset = envelope[envelope["comparison_regime"].astype(str).str.contains(regime, regex=False)].copy()
    if subset.empty:
        return {
            "date_count": 0,
            "candidate_count_quantiles": quantile_stats(pd.Series(dtype=float)),
            "pressure_range_mpa": quantile_stats(pd.Series(dtype=float)),
        }
    active_known = subset[pd.to_numeric(subset["active_ogs_pressure_mpa"], errors="coerce").notna()]
    if not active_known.empty:
        outside = active_known["active_inside_candidate_envelope"].astype(str).str.lower().isin({"false", "0"})
        active_inside_fraction = float(1.0 - outside.mean())
        active_outside_count = int(outside.sum())
    else:
        active_inside_fraction = None
        active_outside_count = 0
    return {
        "date_count": int(subset.shape[0]),
        "date_min": str(subset["date"].min()),
        "date_max": str(subset["date"].max()),
        "candidate_count_quantiles": quantile_stats(subset["candidate_count"]),
        "pressure_range_mpa": quantile_stats(subset["pressure_mpa_range"]),
        "rh_range_percent": quantile_stats(subset["rh_percent_range"]),
        "preferred_abs_minus_envelope_median_mpa": metric_stats(
            subset["preferred_minus_envelope_median_mpa"].abs()
        ),
        "active_abs_minus_envelope_median_mpa": metric_stats(subset["active_abs_minus_envelope_median_mpa"]),
        "active_inside_candidate_envelope_fraction": active_inside_fraction,
        "active_outside_candidate_envelope_count": active_outside_count,
    }


def top_envelope_dates(envelope: pd.DataFrame, limit: int = 10) -> list[dict[str, Any]]:
    columns = [
        "date",
        "comparison_regime",
        "candidate_count",
        "pressure_mpa_range",
        "pressure_mpa_min",
        "pressure_mpa_median",
        "pressure_mpa_max",
        "active_ogs_pressure_mpa",
        "active_inside_candidate_envelope",
    ]
    if envelope.empty:
        return []
    top = envelope.sort_values(["pressure_mpa_range", "date"], ascending=[False, True]).head(limit)
    return json_ready(top[columns].to_dict(orient="records"))


def build_summary(
    envelope: pd.DataFrame,
    policies: pd.DataFrame,
    candidate_json: dict[str, Any],
    preferred_id: str,
) -> dict[str, Any]:
    overlap = envelope[envelope["comparison_regime"].astype(str).str.contains(OVERLAP_STATUS, regex=False)]
    after = envelope[envelope["comparison_regime"].astype(str).str.contains(AFTER_ACTIVE_STATUS, regex=False)]
    active_known = overlap[pd.to_numeric(overlap["active_ogs_pressure_mpa"], errors="coerce").notna()]
    if active_known.empty:
        active_outside_fraction = None
        active_outside_count = 0
    else:
        outside = active_known["active_inside_candidate_envelope"].astype(str).str.lower().isin({"false", "0"})
        active_outside_fraction = float(outside.mean())
        active_outside_count = int(outside.sum())
    preferred_row = policies[policies["candidate_id"].astype(str).eq(preferred_id)]
    preferred_policy = preferred_row.iloc[0].to_dict() if not preferred_row.empty else {}
    return {
        "status": "rh_boundary_uncertainty_envelope_generated_provenance_still_unverified",
        "candidate_count": int(policies["candidate_id"].nunique()) if not policies.empty else 0,
        "candidate_curve_rows": int(candidate_json.get("candidate_curve_rows", 0)),
        "envelope_date_count": int(envelope.shape[0]),
        "preferred_policy_candidate": preferred_id,
        "preferred_policy": json_ready(preferred_policy),
        "lowest_overlap_mae_candidate": candidate_json.get("lowest_overlap_mae_candidate"),
        "overlap": regime_summary(envelope, OVERLAP_STATUS),
        "after_active_curve": regime_summary(envelope, AFTER_ACTIVE_STATUS),
        "active_curve_outside_envelope_count": active_outside_count,
        "active_curve_outside_envelope_fraction": active_outside_fraction,
        "largest_pressure_range_dates": top_envelope_dates(envelope, limit=10),
        "activation_gate": (
            "Diagnostic only: the local RH candidate envelope quantifies sensor-policy spread and active-curve mismatch. "
            "RH boundary forcing and any retention/suction likelihood remain gated until BGR/Gesa confirm the active "
            "curve provenance, sensor screening, time axis, Kelvin constants, and extension policy."
        ),
    }


def fmt(value: Any, digits: int = 3) -> str:
    if value is None or not finite(value):
        return "n/a"
    return f"{float(value):.{digits}f}"


def write_markdown(
    path: Path,
    envelope: pd.DataFrame,
    policies: pd.DataFrame,
    summary: dict[str, Any],
    outputs: dict[str, Path],
) -> None:
    overlap = summary.get("overlap", {})
    after = summary.get("after_active_curve", {})
    preferred = summary.get("preferred_policy", {})
    lines = [
        "# RH Boundary Uncertainty Envelope Audit",
        "",
        "This audit treats the six locally generated RH-derived boundary curves as a policy ensemble.",
        "It quantifies sensor-policy spread and active-curve mismatch; it does not activate RH/suction in the likelihood.",
        "",
        "## Status",
        "",
        f"- Status: `{summary['status']}`",
        f"- Candidate curves: {summary.get('candidate_count', 0)}",
        f"- Envelope dates: {summary.get('envelope_date_count', 0)}",
        f"- Preferred policy candidate: `{summary.get('preferred_policy_candidate', 'n/a')}`",
        f"- Lowest overlap-MAE candidate: `{summary.get('lowest_overlap_mae_candidate', 'n/a')}`",
        f"- Activation gate: {summary['activation_gate']}",
        "",
        "## Envelope Statistics",
        "",
        "| Regime | Dates | Date range | Candidate count p50 | Pressure range p50 MPa | Pressure range p90 MPa | Active outside envelope | Active abs mismatch MAE MPa |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
        "| Overlap with active curve | "
        f"{overlap.get('date_count', 0)} | {overlap.get('date_min', 'n/a')} to {overlap.get('date_max', 'n/a')} | "
        f"{fmt(overlap.get('candidate_count_quantiles', {}).get('p50'), 1)} | "
        f"{fmt(overlap.get('pressure_range_mpa', {}).get('p50'))} | "
        f"{fmt(overlap.get('pressure_range_mpa', {}).get('p90'))} | "
        f"{summary.get('active_curve_outside_envelope_count', 0)} | "
        f"{fmt(overlap.get('active_abs_minus_envelope_median_mpa', {}).get('mae'))} |",
        "| After active curve | "
        f"{after.get('date_count', 0)} | {after.get('date_min', 'n/a')} to {after.get('date_max', 'n/a')} | "
        f"{fmt(after.get('candidate_count_quantiles', {}).get('p50'), 1)} | "
        f"{fmt(after.get('pressure_range_mpa', {}).get('p50'))} | "
        f"{fmt(after.get('pressure_range_mpa', {}).get('p90'))} | "
        "n/a | n/a |",
        "",
        "## Candidate Policies",
        "",
        "| Candidate | Rows | Date range | Compared | After active | Pressure p50 MPa | Overlap MAE MPa | Delta to preferred MAE MPa | Delta p90 MPa |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in policies.sort_values("candidate_id").iterrows():
        lines.append(
            "| "
            f"`{row['candidate_id']}` | {int(row['rows'])} | {row['date_min']} to {row['date_max']} | "
            f"{int(row['compared_to_active_curve_rows'])} | {int(row['after_active_curve_rows'])} | "
            f"{fmt(row['pressure_mpa_p50'])} | {fmt(row['overlap_abs_residual_mpa_mae'])} | "
            f"{fmt(row['abs_delta_vs_preferred_mpa_mae'])} | {fmt(row['abs_delta_vs_preferred_mpa_p90'])} |"
        )
    lines.extend(
        [
            "",
            "## Largest Daily Candidate Spread",
            "",
            "| Date | Regime | Candidates | Pressure range MPa | Pressure min | Pressure median | Pressure max | Active pressure | Active inside envelope |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in summary.get("largest_pressure_range_dates", []):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("date", "n/a")),
                    str(row.get("comparison_regime", "n/a")),
                    str(row.get("candidate_count", "n/a")),
                    fmt(row.get("pressure_mpa_range")),
                    fmt(row.get("pressure_mpa_min")),
                    fmt(row.get("pressure_mpa_median")),
                    fmt(row.get("pressure_mpa_max")),
                    fmt(row.get("active_ogs_pressure_mpa")),
                    str(row.get("active_inside_candidate_envelope", "n/a")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The preferred RH5/RH6-median curve is a policy choice based on the cleanest copied open-twin sensors, not a fit to the active OGS curve.",
            f"Over the overlap, the active curve is outside the local candidate pressure envelope on {summary.get('active_curve_outside_envelope_count', 0)} daily envelope rows.",
            "That mismatch is larger than an implementation detail: it means the active OGS boundary curve likely used different source data, filtering, constants, or time handling than the copied RH workbooks.",
            "",
            "The post-active rows show that the copied RH workbooks can extend the boundary candidate beyond the current 2023-12-26 active curve end, but no extension should be accepted until the provenance and sensor-screening questions are answered.",
            "",
            "## Generated Files",
            "",
        ]
    )
    for key, output in outputs.items():
        lines.append(f"- `{key}`: `{output}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_catalogue(outputs: dict[str, Path], catalogue_dir: Path) -> list[str]:
    if not catalogue_dir.exists():
        return []
    derived = catalogue_dir / "derived_files"
    derived.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for output in outputs.values():
        if output.exists() and output.is_file():
            dest = derived / output.name
            shutil.copy2(output, dest)
            copied.append(str(dest))
    return copied


def main() -> None:
    args = parse_args()
    curves = pd.read_csv(args.candidate_curves)
    require_columns(curves, args.candidate_curves)
    candidate_json = read_json(args.candidate_summary)
    preferred_id = str(candidate_json.get("preferred_policy_candidate") or PREFERRED_CANDIDATE)
    if preferred_id not in set(curves["candidate_id"].astype(str)):
        preferred_id = PREFERRED_CANDIDATE if PREFERRED_CANDIDATE in set(curves["candidate_id"].astype(str)) else str(curves["candidate_id"].iloc[0])

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "envelope_csv": output_dir / "rh_boundary_uncertainty_envelope.csv",
        "candidate_audit_csv": output_dir / "rh_boundary_uncertainty_audit.csv",
        "summary_json": output_dir / "rh_boundary_uncertainty_summary.json",
        "markdown": output_dir / "rh_boundary_uncertainty.md",
    }
    envelope = build_envelope(curves, preferred_id)
    policies = candidate_policy_rows(curves, preferred_id)
    summary = build_summary(envelope, policies, candidate_json, preferred_id)

    envelope.to_csv(outputs["envelope_csv"], index=False)
    policies.to_csv(outputs["candidate_audit_csv"], index=False)
    summary["outputs"] = {key: str(path) for key, path in outputs.items()}
    write_markdown(outputs["markdown"], envelope, policies, summary, outputs)
    copied = copy_catalogue(outputs, args.catalogue_dir)
    summary["catalogue_copies"] = copied
    outputs["summary_json"].write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")

    for key, path in outputs.items():
        print(f"wrote {path}")
    print(f"candidate curves: {summary['candidate_count']}")
    print(f"envelope dates: {summary['envelope_date_count']}")
    print(f"active outside envelope: {summary['active_curve_outside_envelope_count']}")


if __name__ == "__main__":
    main()
