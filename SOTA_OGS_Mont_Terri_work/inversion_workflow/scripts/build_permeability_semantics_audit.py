#!/usr/bin/env python3
"""Build a detailed semantics audit for CD-A permeability pulse-test targets."""

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
        "--processed-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
    )
    return parser.parse_args()


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


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
        return {key: None for key in ["min", "p10", "p25", "p50", "p75", "p90", "max"]}
    return {
        "min": float(clean.min()),
        "p10": float(clean.quantile(0.10)),
        "p25": float(clean.quantile(0.25)),
        "p50": float(clean.quantile(0.50)),
        "p75": float(clean.quantile(0.75)),
        "p90": float(clean.quantile(0.90)),
        "max": float(clean.max()),
    }


def value_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    if frame.empty or column not in frame.columns:
        return {}
    return {
        str(key): int(value)
        for key, value in frame[column].fillna("missing").value_counts().sort_index().items()
    }


def bool_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].astype(str).str.lower().isin({"true", "1", "yes"}).sum())


def classify_gate(row: pd.Series) -> str:
    status = str(row.get("target_status", ""))
    positive = bool(row.get("positive_permeability", True))
    if status == "mapped_inside_mesh" and positive:
        return "active_direct_log_intrinsic_permeability_candidate"
    if status == "mapped_outside_mesh":
        return "excluded_current_mesh_outside_domain"
    if status == "missing_segment_geometry":
        return "excluded_pending_endpoint_geometry_or_digitized_trace"
    if status == "not_usable_missing_or_nonpositive_permeability" or not positive:
        return "excluded_missing_or_nonpositive_interpreted_value"
    return "excluded_pending_manual_review"


def build_row_audit(targets: pd.DataFrame) -> pd.DataFrame:
    if targets.empty:
        return pd.DataFrame()
    frame = targets.copy()
    frame["positive_permeability"] = pd.to_numeric(frame["permeability_m2"], errors="coerce").gt(0)
    frame["semantic_activation_gate"] = frame.apply(classify_gate, axis=1)
    frame["measured_physical_quantity"] = (
        "nitrogen pulse-decay interpreted scalar interval permeability/transmissibility"
    )
    frame["model_comparison_quantity"] = (
        "interval-weighted directional intrinsic permeability e^T K e from k_i_rd"
    )
    frame["not_a_direct_measurement_of"] = (
        "hydraulic conductivity K_h; liquid relative permeability; saturation; cell-wise tensor component"
    )
    frame["recommended_residual"] = "log10(k_pred_m2) - log10(k_obs_m2)"
    frame["recommended_sigma_log10"] = 0.5
    frame["key_caveats"] = (
        "gas slippage/Klinkenberg correction provenance; finite 3D interval support; "
        "scalar response projected onto anisotropic tensor; endpoint geometry required for cell objective"
    )
    keep = [
        "observation_id",
        "source_file",
        "source_sheet",
        "source_row_1based",
        "campaign_year",
        "campaign_note",
        "block_label",
        "normalized_segment_label",
        "twin",
        "direction_inferred_from_label",
        "borehole_depth_m",
        "interval_length_m",
        "permeability_m2",
        "transmissibility_m3",
        "log10_permeability_m2",
        "positive_permeability",
        "target_status",
        "usable_for_current_ogs_fit",
        "fit_use_recommendation",
        "geometry_evidence_status",
        "selected_sample_count",
        "inside_cell_sample_count",
        "fallback_sample_count",
        "outside_sample_count",
        "selected_cell_ids",
        "semantic_activation_gate",
        "measured_physical_quantity",
        "model_comparison_quantity",
        "not_a_direct_measurement_of",
        "recommended_residual",
        "recommended_sigma_log10",
        "key_caveats",
    ]
    return frame[[column for column in keep if column in frame.columns]]


def summarize_group(group: pd.DataFrame, group_columns: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column in group_columns:
        value = group[column].iloc[0]
        result[column] = "missing" if pd.isna(value) else value
    positive = group[pd.to_numeric(group["permeability_m2"], errors="coerce").gt(0)].copy()
    result.update(
        {
            "rows": int(group.shape[0]),
            "positive_rows": int(positive.shape[0]),
            "usable_current_rows": bool_count(group, "usable_for_current_ogs_fit"),
            "mapped_inside_rows": int(group["target_status"].astype(str).eq("mapped_inside_mesh").sum()),
            "mapped_outside_rows": int(group["target_status"].astype(str).eq("mapped_outside_mesh").sum()),
            "missing_geometry_rows": int(group["target_status"].astype(str).eq("missing_segment_geometry").sum()),
            "nonpositive_or_missing_rows": int(
                group["target_status"].astype(str).eq("not_usable_missing_or_nonpositive_permeability").sum()
            ),
            "depth_min_m": float(pd.to_numeric(group["borehole_depth_m"], errors="coerce").min())
            if group["borehole_depth_m"].notna().any()
            else np.nan,
            "depth_max_m": float(pd.to_numeric(group["borehole_depth_m"], errors="coerce").max())
            if group["borehole_depth_m"].notna().any()
            else np.nan,
            "log10_permeability_min": float(positive["log10_permeability_m2"].min())
            if not positive.empty
            else np.nan,
            "log10_permeability_median": float(positive["log10_permeability_m2"].median())
            if not positive.empty
            else np.nan,
            "log10_permeability_max": float(positive["log10_permeability_m2"].max())
            if not positive.empty
            else np.nan,
        }
    )
    return result


def build_group_summary(row_audit: pd.DataFrame) -> pd.DataFrame:
    if row_audit.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    group_specs = [
        ("target_status", ["target_status"]),
        ("campaign_twin_direction", ["campaign_year", "twin", "direction_inferred_from_label"]),
        ("segment", ["normalized_segment_label"]),
        ("source_sheet", ["source_sheet"]),
    ]
    for group_type, columns in group_specs:
        for _, group in row_audit.groupby(columns, dropna=False):
            summary = summarize_group(group, columns)
            summary["group_type"] = group_type
            summary["group_key"] = " | ".join(str(summary[column]) for column in columns)
            rows.append(summary)
    return pd.DataFrame(rows)


def pressure_decay_summary(pressure: pd.DataFrame) -> dict[str, Any]:
    if pressure.empty:
        return {"rows": 0}
    rows: dict[str, Any] = {"rows": int(pressure.shape[0])}
    rows["source_sheet_counts"] = value_counts(pressure, "source_sheet")
    rows["interval_count"] = int(
        pressure[["source_sheet", "interval_label"]].drop_duplicates().shape[0]
    )
    rows["interval_depth_quantiles_m"] = quantiles(pressure["interval_depth_m"])
    rows["time_quantiles_s"] = quantiles(pressure["time_s"])
    rows["normalized_pressure_quantiles_pa"] = quantiles(pressure["normalized_interval_pressure_pa"])
    return rows


def top_rows(frame: pd.DataFrame, ascending: bool, limit: int = 8) -> list[dict[str, Any]]:
    positive = frame[pd.to_numeric(frame["permeability_m2"], errors="coerce").gt(0)].copy()
    if positive.empty:
        return []
    columns = [
        "observation_id",
        "campaign_year",
        "block_label",
        "normalized_segment_label",
        "twin",
        "direction_inferred_from_label",
        "borehole_depth_m",
        "permeability_m2",
        "log10_permeability_m2",
        "target_status",
        "usable_for_current_ogs_fit",
    ]
    ordered = positive.sort_values("log10_permeability_m2", ascending=ascending).head(limit)
    return ordered[columns].to_dict(orient="records")


def build_summary(
    row_audit: pd.DataFrame,
    group_summary: pd.DataFrame,
    pressure: pd.DataFrame,
    missing: pd.DataFrame,
    target_summary: dict[str, Any],
    outputs: dict[str, str],
) -> dict[str, Any]:
    positive = row_audit[pd.to_numeric(row_audit["permeability_m2"], errors="coerce").gt(0)].copy()
    usable = row_audit[row_audit["usable_for_current_ogs_fit"].astype(str).str.lower().isin({"true", "1", "yes"})]
    summary = {
        "target_rows": int(row_audit.shape[0]),
        "positive_rows": int(positive.shape[0]),
        "usable_current_rows": int(usable.shape[0]),
        "target_status_counts": value_counts(row_audit, "target_status"),
        "semantic_activation_gate_counts": value_counts(row_audit, "semantic_activation_gate"),
        "campaign_counts": value_counts(row_audit, "campaign_year"),
        "twin_counts": value_counts(row_audit, "twin"),
        "direction_counts": value_counts(row_audit, "direction_inferred_from_label"),
        "log10_permeability_quantiles_all_positive": quantiles(positive["log10_permeability_m2"]),
        "log10_permeability_quantiles_usable": quantiles(usable["log10_permeability_m2"]),
        "permeability_m2_quantiles_all_positive": quantiles(positive["permeability_m2"]),
        "permeability_m2_quantiles_usable": quantiles(usable["permeability_m2"]),
        "pressure_decay": pressure_decay_summary(pressure),
        "missing_geometry_groups": int(missing.shape[0]),
        "target_builder_summary": target_summary,
        "lowest_positive_rows": top_rows(row_audit, ascending=True),
        "highest_positive_rows": top_rows(row_audit, ascending=False),
        "outputs": outputs,
        "activation_rules": [
            "Treat the workbook value as a noisy scalar interval-scale observation of intrinsic permeability.",
            "Do not treat the nitrogen pulse-test value as hydraulic conductivity, relative permeability, saturation, or a direct tensor component.",
            "Compare active rows in log10 permeability space against an interval-weighted directional tensor response e^T K e.",
            "Keep the broad first-pass sigma of 0.5 log10 units unless collaborator-provided test uncertainties justify a different row-level scale.",
            "Exclude missing-geometry and outside-mesh rows from the current OGS cell objective until their support is reconstructed.",
        ],
    }
    if not group_summary.empty:
        usable_segments = group_summary[
            group_summary["group_type"].eq("segment") & group_summary["usable_current_rows"].gt(0)
        ]
        summary["usable_segment_count"] = int(usable_segments.shape[0])
        summary["usable_segments"] = sorted(str(value) for value in usable_segments["normalized_segment_label"].dropna())
    return summary


def fmt_number(value: Any, digits: int = 3) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if not np.isfinite(number):
        return "n/a"
    return f"{number:.{digits}g}"


def table_from_records(records: list[dict[str, Any]]) -> list[str]:
    def render(value: Any) -> str:
        if value is None or pd.isna(value):
            return "missing"
        return str(value)

    lines = [
        "| Observation | Segment | Twin | Direction | Depth m | k m2 | log10 k | Status |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in records:
        lines.append(
            "| "
            + " | ".join(
                [
                    render(row.get("observation_id", "")),
                    render(row.get("normalized_segment_label", "")),
                    render(row.get("twin", "")),
                    render(row.get("direction_inferred_from_label", "")),
                    fmt_number(row.get("borehole_depth_m"), 3),
                    f"{float(row.get('permeability_m2')):.3e}",
                    fmt_number(row.get("log10_permeability_m2"), 4),
                    render(row.get("target_status", "")),
                ]
            )
            + " |"
        )
    return lines


def write_markdown(path: Path, summary: dict[str, Any], group_summary: pd.DataFrame) -> None:
    status_counts = summary["target_status_counts"]
    activation_counts = summary["semantic_activation_gate_counts"]
    logq = summary["log10_permeability_quantiles_all_positive"]
    usable_logq = summary["log10_permeability_quantiles_usable"]
    pressure = summary["pressure_decay"]
    lines = [
        "# Permeability Measurement Semantics Audit",
        "",
        "This audit records how the CD-A permeability pulse-test rows should be interpreted",
        "before they are used as inverse-problem observations.  It is deliberately stricter",
        "than a workbook inventory because the measurements are gas pulse tests on finite",
        "borehole intervals, while the OGS unknown is an intrinsic permeability tensor field.",
        "",
        "## Key Counts",
        "",
        f"- Interpreted target rows: {summary['target_rows']}",
        f"- Positive interpreted permeability rows: {summary['positive_rows']}",
        f"- Rows usable in the current OGS direct objective: {summary['usable_current_rows']}",
        f"- Missing-geometry groups: {summary['missing_geometry_groups']}",
        f"- Pressure-decay rows retained separately: {pressure.get('rows', 0)}",
        f"- Pressure-decay interval count: {pressure.get('interval_count', 0)}",
        "",
        "Target status counts:",
        "",
        "| Status | Rows |",
        "| --- | ---: |",
    ]
    for key, value in status_counts.items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(["", "Semantic activation gates:", "", "| Gate | Rows |", "| --- | ---: |"])
    for key, value in activation_counts.items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## What The Test Observes",
            "",
            "- Source workbooks report interpreted permeability/transmissibility values and raw pressure-decay traces.",
            "- The local HERMES slides describe a modified COMDRILL double-piston packer, 10 cm static interval, nitrogen injection up to 1 bar, and pressure monitoring after injection.",
            "- The CD-A characterization paper states that the pulse tests determine intrinsic permeability of a 3D volume around the 10 cm borehole interval, with about half an order of magnitude experimental/evaluation error.",
            "- Klinkenberg's gas-permeability result means the apparent gas permeability is pressure dependent; a liquid-equivalent/intrinsic value requires slippage/test-condition interpretation.",
            "",
            "Therefore the active row is a noisy scalar interval observation of intrinsic",
            "permeability.  It is not hydraulic conductivity, not liquid relative",
            "permeability, not saturation, and not a direct cell-wise tensor component.",
            "",
            "## Model-Side Operator",
            "",
            "Current active comparison:",
            "",
            "```text",
            "residual = log10(k_pred_m2) - log10(k_obs_m2)",
            "k_pred  = interval-weighted directional response e^T K e from k_i_rd",
            "sigma   = 0.5 log10 units for the first-pass likelihood",
            "```",
            "",
            "The directional response is a pragmatic first observation operator.  A stricter",
            "future operator would replace the nominal 10 cm along-borehole window with a",
            "test-specific pressure-transient sensitivity kernel, but the current data do not",
            "contain enough test-geometry and interpretation metadata to justify that level.",
            "",
            "## Value Ranges",
            "",
            f"- All positive rows log10(k/m2): min={fmt_number(logq['min'], 5)}, p50={fmt_number(logq['p50'], 5)}, max={fmt_number(logq['max'], 5)}",
            f"- Currently usable rows log10(k/m2): min={fmt_number(usable_logq['min'], 5)}, p50={fmt_number(usable_logq['p50'], 5)}, max={fmt_number(usable_logq['max'], 5)}",
            "",
            "Lowest positive interpreted rows:",
            "",
            *table_from_records(summary["lowest_positive_rows"]),
            "",
            "Highest positive interpreted rows:",
            "",
            *table_from_records(summary["highest_positive_rows"]),
            "",
            "## Coverage By Segment",
            "",
        ]
    )
    segment = group_summary[group_summary["group_type"].eq("segment")].copy()
    if segment.empty:
        lines.append("No segment summary was generated.")
    else:
        lines.extend(
            [
                "| Segment | Rows | Usable | Missing geometry | Outside mesh | log10 k min | log10 k median | log10 k max |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        segment = segment.sort_values(["usable_current_rows", "rows"], ascending=[False, False])
        for _, row in segment.iterrows():
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{row.get('normalized_segment_label', '')}`",
                        str(int(row["rows"])),
                        str(int(row["usable_current_rows"])),
                        str(int(row["missing_geometry_rows"])),
                        str(int(row["mapped_outside_rows"])),
                        fmt_number(row["log10_permeability_min"], 5),
                        fmt_number(row["log10_permeability_median"], 5),
                        fmt_number(row["log10_permeability_max"], 5),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Activation Rules",
            "",
            "- Use only positive, in-mesh rows with labelled endpoint geometry for the current direct objective.",
            "- Keep missing-geometry BCD-A24/25/26/27 and BFM-D19 rows visible, but inactive until endpoint geometry or an approved digitized trace exists.",
            "- Keep mapped-outside rows inactive for the current Niche-4 mesh unless the model domain is expanded or a deliberate support mapping is approved.",
            "- Keep the residual in log10 permeability space because values span many orders of magnitude and the stated measurement/evaluation error is multiplicative.",
            "- Treat horizontal/vertical contrasts as evidence for anisotropy and EDZ heterogeneity, not as proof of a single tensor component at a single cell.",
            "",
            "## Source Basis",
            "",
            "- Local HERMES modelling slides: permeability method details on PDF p. 5.",
            "- Ziefle et al. characterization paper: pulse-test setup/results in Section 4.3 and permeability interpretation in later discussion sections.",
            "- Klinkenberg 1941: gas apparent permeability depends on reciprocal mean pressure; extrapolated infinite-pressure value is the medium permeability constant.",
            "- Marschall et al. 2005: Opalinus Clay gas transport depends on intrinsic permeability, capillary threshold, saturation, and possible dilatancy at high gas pressure; this supports keeping gas-test interpretation separate from OGS liquid relative permeability.",
            "",
            "## Generated Files",
            "",
        ]
    )
    for label, output_path in summary["outputs"].items():
        lines.append(f"- `{label}`: `{output_path}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    processed = args.processed_dir
    output_dir = args.output_dir
    targets = read_csv(processed / "permeability_observation_targets.csv")
    pressure = read_csv(processed / "permeability_pressure_decay.csv")
    missing = read_csv(processed / "permeability_missing_geometry_audit.csv")
    target_summary = read_json(processed / "permeability_target_summary.json")

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "row_audit": str(output_dir / "permeability_measurement_semantics_audit.csv"),
        "group_summary": str(output_dir / "permeability_measurement_semantics_group_summary.csv"),
        "summary": str(output_dir / "permeability_measurement_semantics_summary.json"),
        "markdown": str(output_dir / "permeability_measurement_semantics.md"),
    }
    row_frame = build_row_audit(targets)
    group_frame = build_group_summary(row_frame)
    summary = build_summary(row_frame, group_frame, pressure, missing, target_summary, outputs)

    row_frame.to_csv(outputs["row_audit"], index=False)
    group_frame.to_csv(outputs["group_summary"], index=False)
    Path(outputs["summary"]).write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(Path(outputs["markdown"]), summary, group_frame)
    print(f"wrote {outputs['row_audit']}")
    print(f"wrote {outputs['group_summary']}")
    print(f"wrote {outputs['summary']}")
    print(f"wrote {outputs['markdown']}")
    print(f"permeability target rows: {summary['target_rows']}")
    print(f"usable current rows: {summary['usable_current_rows']}")


if __name__ == "__main__":
    main()
