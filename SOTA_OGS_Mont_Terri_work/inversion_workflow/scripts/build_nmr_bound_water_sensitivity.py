#!/usr/bin/env python3
"""Quantify the NMR bound/interlayer-water caveat before activating NMR residuals."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import numpy as np
import pandas as pd


DEFAULT_OFFSETS = [0.0, 0.005, 0.01, 0.015, 0.02, 0.03, 0.04, 0.05, 0.075, 0.10]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state-targets",
        type=Path,
        default=Path("inversion_workflow/processed_observations/state_observation_targets.csv"),
    )
    parser.add_argument(
        "--parameters",
        type=Path,
        default=Path("ogs_settings/03_parameters_TRM.xml"),
    )
    parser.add_argument(
        "--offsets",
        default=",".join(str(value) for value in DEFAULT_OFFSETS),
        help="Comma-separated candidate bound/interlayer-water offsets as volumetric fractions.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
    )
    return parser.parse_args()


def parse_xml_fragment(path: Path) -> ET.Element:
    text = path.read_text(encoding="utf-8")
    return ET.fromstring(f"<root>\n{text}\n</root>")


def direct_text(element: ET.Element, tag: str) -> str:
    values = [child.text.strip() for child in element.findall(tag) if child.text and child.text.strip()]
    return " | ".join(values)


def read_phi(path: Path) -> float:
    root = parse_xml_fragment(path)
    for parameter in root.findall("parameter"):
        if direct_text(parameter, "name") != "phi":
            continue
        value = direct_text(parameter, "values") or direct_text(parameter, "value")
        match = re.search(r"[-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?", value)
        if not match:
            break
        return float(match.group(0))
    raise RuntimeError(f"could not parse scalar phi from {path}")


def parse_offsets(text: str) -> list[float]:
    offsets = []
    for item in text.split(","):
        item = item.strip()
        if not item:
            continue
        offsets.append(float(item))
    if not offsets:
        raise ValueError("at least one offset must be supplied")
    return sorted(set(offsets))


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


def quantiles(series: pd.Series) -> dict[str, float | None]:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return {key: None for key in ["min", "p25", "p50", "p75", "p90", "p95", "p99", "max"]}
    return {
        "min": float(clean.min()),
        "p25": float(clean.quantile(0.25)),
        "p50": float(clean.quantile(0.50)),
        "p75": float(clean.quantile(0.75)),
        "p90": float(clean.quantile(0.90)),
        "p95": float(clean.quantile(0.95)),
        "p99": float(clean.quantile(0.99)),
        "max": float(clean.max()),
    }


def classify_free_theta(free_theta: pd.Series, phi: float) -> pd.Series:
    conditions = [
        free_theta.lt(0),
        free_theta.gt(phi),
    ]
    choices = ["overcorrected_negative_free_water", "still_exceeds_fixed_porosity"]
    return pd.Series(np.select(conditions, choices, default="physical_0_to_phi"), index=free_theta.index)


def row_audit(nmr: pd.DataFrame, phi: float) -> pd.DataFrame:
    output = nmr.copy()
    output["fixed_phi"] = phi
    output["observed_theta_fraction"] = output["observed_value"].astype(float)
    output["uncorrected_implied_saturation_if_theta_mobile"] = output["observed_theta_fraction"] / phi
    output["excess_theta_over_fixed_phi"] = (output["observed_theta_fraction"] - phi).clip(lower=0.0)
    output["minimum_nonnegative_bound_offset_for_saturation_le_1"] = output["excess_theta_over_fixed_phi"]
    output["uncorrected_physical_if_saturation_le_1"] = output["observed_theta_fraction"].between(0.0, phi)
    output["suggested_first_use"] = np.where(
        output["uncorrected_physical_if_saturation_le_1"],
        "absolute_or_trend_after_ogs_outputs_with_bound_water_error_floor",
        "trend_or_bias_augmented_absolute_likelihood_only",
    )
    keep = [
        "target_id",
        "observation_family",
        "measurement_label",
        "mapping_label",
        "date_iso",
        "source_file",
        "source_member",
        "target_status",
        "usable_for_current_state_fit",
        "observed_theta_fraction",
        "observed_sigma",
        "fixed_phi",
        "uncorrected_implied_saturation_if_theta_mobile",
        "uncorrected_physical_if_saturation_le_1",
        "excess_theta_over_fixed_phi",
        "minimum_nonnegative_bound_offset_for_saturation_le_1",
        "suggested_first_use",
    ]
    return output[keep]


def scenario_rows(nmr: pd.DataFrame, phi: float, offsets: list[float]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    scopes = [("all_nmr_targets", nmr), ("usable_current_mesh_targets", nmr[nmr["usable_for_current_state_fit"]])]
    for offset in offsets:
        for scope, frame in scopes:
            free_theta = frame["observed_value"].astype(float) - offset
            status = classify_free_theta(free_theta, phi)
            rows.append(
                {
                    "offset_fraction": offset,
                    "scope": scope,
                    "row_count": int(frame.shape[0]),
                    "physical_0_to_phi_rows": int(status.eq("physical_0_to_phi").sum()),
                    "still_exceeds_fixed_porosity_rows": int(status.eq("still_exceeds_fixed_porosity").sum()),
                    "overcorrected_negative_free_water_rows": int(status.eq("overcorrected_negative_free_water").sum()),
                    "physical_fraction": float(status.eq("physical_0_to_phi").mean()) if len(status) else np.nan,
                    "free_theta_min": float(free_theta.min()) if len(free_theta) else np.nan,
                    "free_theta_median": float(free_theta.median()) if len(free_theta) else np.nan,
                    "free_theta_max": float(free_theta.max()) if len(free_theta) else np.nan,
                    "implied_saturation_median": float((free_theta / phi).median()) if len(free_theta) else np.nan,
                    "implied_saturation_max": float((free_theta / phi).max()) if len(free_theta) else np.nan,
                }
            )
        for family, frame in nmr.groupby("observation_family"):
            free_theta = frame["observed_value"].astype(float) - offset
            status = classify_free_theta(free_theta, phi)
            rows.append(
                {
                    "offset_fraction": offset,
                    "scope": f"family:{family}",
                    "row_count": int(frame.shape[0]),
                    "physical_0_to_phi_rows": int(status.eq("physical_0_to_phi").sum()),
                    "still_exceeds_fixed_porosity_rows": int(status.eq("still_exceeds_fixed_porosity").sum()),
                    "overcorrected_negative_free_water_rows": int(status.eq("overcorrected_negative_free_water").sum()),
                    "physical_fraction": float(status.eq("physical_0_to_phi").mean()) if len(status) else np.nan,
                    "free_theta_min": float(free_theta.min()) if len(free_theta) else np.nan,
                    "free_theta_median": float(free_theta.median()) if len(free_theta) else np.nan,
                    "free_theta_max": float(free_theta.max()) if len(free_theta) else np.nan,
                    "implied_saturation_median": float((free_theta / phi).median()) if len(free_theta) else np.nan,
                    "implied_saturation_max": float((free_theta / phi).max()) if len(free_theta) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def group_offsets(row_frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    group_specs = [
        ("observation_family", ["observation_family"]),
        ("mapping_label", ["mapping_label"]),
        ("family_mapping_label", ["observation_family", "mapping_label"]),
    ]
    for group_type, columns in group_specs:
        for keys, group in row_frame.groupby(columns, dropna=False):
            if not isinstance(keys, tuple):
                keys = (keys,)
            rendered_keys = ["missing_mapping_label" if pd.isna(key) else str(key) for key in keys]
            excess = group["excess_theta_over_fixed_phi"]
            usable = group["usable_for_current_state_fit"].astype(bool)
            rows.append(
                {
                    "group_type": group_type,
                    "group_key": " | ".join(rendered_keys),
                    "row_count": int(group.shape[0]),
                    "usable_rows": int(usable.sum()),
                    "uncorrected_rows_above_fixed_phi": int(group["uncorrected_physical_if_saturation_le_1"].eq(False).sum()),
                    "required_offset_mean": float(excess.mean()),
                    "required_offset_p50": float(excess.quantile(0.50)),
                    "required_offset_p75": float(excess.quantile(0.75)),
                    "required_offset_p90": float(excess.quantile(0.90)),
                    "required_offset_p95": float(excess.quantile(0.95)),
                    "required_offset_max": float(excess.max()),
                    "observed_theta_min": float(group["observed_theta_fraction"].min()),
                    "observed_theta_median": float(group["observed_theta_fraction"].median()),
                    "observed_theta_max": float(group["observed_theta_fraction"].max()),
                }
            )
    return pd.DataFrame(rows)


def build_summary(
    row_frame: pd.DataFrame,
    scenarios: pd.DataFrame,
    groups: pd.DataFrame,
    phi: float,
    offsets: list[float],
    outputs: dict[str, str],
) -> dict[str, Any]:
    usable = row_frame[row_frame["usable_for_current_state_fit"].astype(bool)].copy()
    family_rows = {}
    for family, group in row_frame.groupby("observation_family"):
        family_rows[family] = {
            "rows": int(group.shape[0]),
            "usable_rows": int(group["usable_for_current_state_fit"].astype(bool).sum()),
            "uncorrected_rows_above_fixed_phi": int((~group["uncorrected_physical_if_saturation_le_1"]).sum()),
            "observed_theta_quantiles": quantiles(group["observed_theta_fraction"]),
            "required_offset_quantiles": quantiles(group["excess_theta_over_fixed_phi"]),
        }
    scenario_all = scenarios[scenarios["scope"].eq("all_nmr_targets")].copy()
    scenario_usable = scenarios[scenarios["scope"].eq("usable_current_mesh_targets")].copy()
    scenario_usable = scenario_usable.assign(
        nonphysical_rows=(
            scenario_usable["still_exceeds_fixed_porosity_rows"]
            + scenario_usable["overcorrected_negative_free_water_rows"]
        )
    )
    best_usable = scenario_usable.sort_values(
        ["nonphysical_rows", "overcorrected_negative_free_water_rows", "offset_fraction"]
    ).head(1)
    best_record = best_usable.iloc[0].to_dict() if not best_usable.empty else {}
    return {
        "fixed_phi": phi,
        "offsets_tested": offsets,
        "nmr_target_rows": int(row_frame.shape[0]),
        "usable_current_mesh_rows": int(usable.shape[0]),
        "uncorrected_rows_above_fixed_phi": int((~row_frame["uncorrected_physical_if_saturation_le_1"]).sum()),
        "uncorrected_usable_rows_above_fixed_phi": int((~usable["uncorrected_physical_if_saturation_le_1"]).sum()),
        "observed_theta_quantiles_all": quantiles(row_frame["observed_theta_fraction"]),
        "observed_theta_quantiles_usable": quantiles(usable["observed_theta_fraction"]),
        "required_offset_quantiles_all": quantiles(row_frame["excess_theta_over_fixed_phi"]),
        "required_offset_quantiles_usable": quantiles(usable["excess_theta_over_fixed_phi"]),
        "family_summary": family_rows,
        "best_uniform_offset_by_simple_physical_count_usable": json_ready(best_record),
        "scenario_rows_all_scope": json_ready(scenario_all.to_dict(orient="records")),
        "scenario_rows_usable_scope": json_ready(scenario_usable.to_dict(orient="records")),
        "high_offset_groups": json_ready(
            groups[
                groups["group_type"].eq("mapping_label")
                & groups["usable_rows"].gt(0)
                & groups["required_offset_p95"].fillna(0).gt(0.03)
            ]
            .sort_values("required_offset_p95", ascending=False)
            .to_dict(orient="records")
        ),
        "recommended_activation": [
            "Do not activate absolute NMR theta residuals as theta_obs = phi*S_l without a bound/interlayer-water bias or error term.",
            "Use trend/anomaly residuals within each station/position as the first OGS-backed NMR comparison because constant bound-water offsets cancel to first order.",
            "If absolute NMR residuals are used, compare theta_obs = phi*S_l + b_label + epsilon with a non-negative label/campaign bias term or a group-specific model-error floor.",
            "Do not infer porosity from NMR alone; porosity remains fixed in the current stage because theta observations trade off directly with saturation and bound water.",
        ],
        "outputs": outputs,
    }


def write_markdown(path: Path, summary: dict[str, Any], scenarios: pd.DataFrame, groups: pd.DataFrame) -> None:
    q_usable = summary["required_offset_quantiles_usable"]
    lines = [
        "# NMR Bound-Water Sensitivity",
        "",
        "This audit quantifies the NMR caveat before NMR water-content rows are promoted",
        "to numerical OGS state residuals.  The fixed current porosity is used as the",
        "maximum model water content for saturated cells, because the model-side proxy is",
        "`theta_model = porosity * liquid_saturation` and `S_l <= 1`.",
        "",
        f"- Fixed porosity used for the audit: `{summary['fixed_phi']:.6g}`",
        f"- NMR target rows: {summary['nmr_target_rows']}",
        f"- Usable current-mesh rows: {summary['usable_current_mesh_rows']}",
        f"- Rows whose uncorrected NMR water content exceeds fixed porosity: {summary['uncorrected_rows_above_fixed_phi']}",
        f"- Usable rows whose uncorrected NMR water content exceeds fixed porosity: {summary['uncorrected_usable_rows_above_fixed_phi']}",
        f"- Usable-row required positive offset quantiles: p50={q_usable['p50']:.4f}, p75={q_usable['p75']:.4f}, p90={q_usable['p90']:.4f}, p95={q_usable['p95']:.4f}, max={q_usable['max']:.4f}",
        "",
        "## Offset Scenarios",
        "",
        "| Offset | Scope | Physical rows | Still above phi | Negative free-water rows | Physical fraction |",
        "| ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    display = scenarios[scenarios["scope"].isin(["all_nmr_targets", "usable_current_mesh_targets"])].copy()
    for _, row in display.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"{float(row['offset_fraction']):.3f}",
                    f"`{row['scope']}`",
                    str(int(row["physical_0_to_phi_rows"])),
                    str(int(row["still_exceeds_fixed_porosity_rows"])),
                    str(int(row["overcorrected_negative_free_water_rows"])),
                    f"{float(row['physical_fraction']):.3f}",
                ]
            )
            + " |"
        )

    high_groups = groups[
        groups["group_type"].eq("mapping_label")
        & groups["usable_rows"].gt(0)
        & groups["required_offset_p95"].fillna(0).gt(0.03)
    ].sort_values("required_offset_p95", ascending=False)
    lines.extend(
        [
            "",
            "## High-Offset Mapping Labels",
            "",
            "| Label | Rows | Required offset p95 | Required offset max | Observed theta max |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in high_groups.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['group_key']}`",
                    str(int(row["row_count"])),
                    f"{float(row['required_offset_p95']):.4f}",
                    f"{float(row['required_offset_max']):.4f}",
                    f"{float(row['observed_theta_max']):.4f}",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Activation Recommendation",
            "",
        ]
    )
    for item in summary["recommended_activation"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A single global bound-water subtraction is not a clean solution: large offsets",
            "are needed for some seasonal labels, while the low seasonal values would become",
            "negative free-water contents.  The safer first residual is therefore a",
            "within-label trend/anomaly comparison, or an absolute comparison with explicit",
            "label/campaign bias terms and an additional model-error floor.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    phi = read_phi(args.parameters)
    offsets = parse_offsets(args.offsets)
    targets = pd.read_csv(args.state_targets)
    nmr = targets[targets["observation_family"].astype(str).str.startswith("NMR")].copy()
    if nmr.empty:
        raise SystemExit("no NMR rows found in state observation targets")
    nmr["usable_for_current_state_fit"] = nmr["usable_for_current_state_fit"].astype(str).str.lower().isin({"true", "1", "yes"})

    rows = row_audit(nmr, phi)
    scenarios = scenario_rows(nmr, phi, offsets)
    groups = group_offsets(rows)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    row_path = args.output_dir / "nmr_bound_water_target_audit.csv"
    scenario_path = args.output_dir / "nmr_bound_water_offset_scenarios.csv"
    group_path = args.output_dir / "nmr_bound_water_group_offsets.csv"
    summary_path = args.output_dir / "nmr_bound_water_sensitivity_summary.json"
    markdown_path = args.output_dir / "nmr_bound_water_sensitivity.md"
    outputs = {
        "row_audit": str(row_path),
        "offset_scenarios": str(scenario_path),
        "group_offsets": str(group_path),
        "summary": str(summary_path),
        "markdown": str(markdown_path),
    }
    summary = build_summary(rows, scenarios, groups, phi, offsets, outputs)

    rows.to_csv(row_path, index=False)
    scenarios.to_csv(scenario_path, index=False)
    groups.to_csv(group_path, index=False)
    summary_path.write_text(json.dumps(json_ready(summary), indent=2), encoding="utf-8")
    write_markdown(markdown_path, summary, scenarios, groups)


if __name__ == "__main__":
    main()
