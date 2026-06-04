#!/usr/bin/env python3
"""Build a semantics/activation audit for ERT resistivity observations."""

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


def ert_targets(state_targets: pd.DataFrame) -> pd.DataFrame:
    if state_targets.empty or "observation_family" not in state_targets.columns:
        return pd.DataFrame()
    return state_targets[state_targets["observation_family"].astype(str).eq("ERT open-niche time series")].copy()


def build_timestep_audit(timesteps: pd.DataFrame) -> pd.DataFrame:
    if timesteps.empty:
        return pd.DataFrame()
    output = timesteps.copy()
    output["measured_physical_quantity"] = "ERT inverted bulk electrical resistivity field"
    output["model_comparison_path"] = (
        "OGS liquid saturation and porosity -> theta_model -> empirical rho(theta) -> ERT/common-mesh log-resistivity"
    )
    output["not_a_direct_measurement_of"] = "saturation; water content; permeability; OGS pressure"
    output["recommended_residual"] = "log10(rho_pred_ohm_m) - log10(rho_ert_ohm_m)"
    output["semantic_activation_gate"] = np.where(
        output["has_matching_vtk"].astype(bool),
        "prepared_timestep_pending_ogs_output_transform_support_and_uncertainty",
        "blocked_missing_matching_vtk_member",
    )
    keep = [
        "source_file",
        "source_member",
        "folder",
        "timestep_index_in_file",
        "data_filename",
        "timestamp_iso",
        "matching_vtk_member",
        "has_matching_vtk",
        "measured_physical_quantity",
        "model_comparison_path",
        "not_a_direct_measurement_of",
        "recommended_residual",
        "semantic_activation_gate",
    ]
    return output[keep]


def build_relation_audit(relations: pd.DataFrame, operator_summary: dict[str, Any]) -> pd.DataFrame:
    if relations.empty:
        return pd.DataFrame()
    recommended = str(operator_summary.get("recommended_relation_id", ""))
    output = relations.copy()
    output["semantic_role"] = np.where(
        output["relation_id"].astype(str).eq(recommended),
        "default_first_test_theta_to_resistivity_relation",
        "diagnostic_or_rejected_calibration_relation",
    )
    output["activation_gate"] = np.where(
        output["relation_id"].astype(str).eq(recommended),
        "usable_after_ogs_theta_sampling_and_spatial_support_confirmation",
        "retain_for_sensitivity_or_diagnostics_only",
    )
    output["not_a_direct_measurement_of"] = "saturation or permeability; this is a calibration relation from theta to resistivity"
    keep = [
        "relation_id",
        "source_table",
        "source_subset",
        "recommended_for_current_niche",
        "semantic_role",
        "activation_gate",
        "model_input_quantity",
        "predicted_quantity",
        "relation_form",
        "inverse_form",
        "n_points",
        "coefficient_a",
        "exponent_b",
        "rmse_log10_resistivity",
        "mean_abs_log10_residual",
        "r2_log10",
        "theta_min",
        "theta_max",
        "resistivity_min_ohm_m",
        "resistivity_max_ohm_m",
        "not_a_direct_measurement_of",
        "use_caveat",
    ]
    return output[[column for column in keep if column in output.columns]]


def build_projection_group_summary(projection: pd.DataFrame) -> pd.DataFrame:
    if projection.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    group_specs = [
        ("lookup_status", ["ogs_lookup_status"]),
        ("central_support_and_ready", ["within_approx_1p5m_center_support", "ready_for_residual_after_ogs_output"]),
        ("material_and_support", ["ogs_lookup_material_id", "within_approx_1p5m_center_support"]),
    ]
    for group_type, columns in group_specs:
        for keys, group in projection.groupby(columns, dropna=False):
            if not isinstance(keys, tuple):
                keys = (keys,)
            rendered = ["missing" if pd.isna(key) else str(key) for key in keys]
            rows.append(
                {
                    "group_type": group_type,
                    "group_key": " | ".join(rendered),
                    "rows": int(group.shape[0]),
                    "inside_ogs_cell_rows": bool_count(group, "inside_ogs_cell"),
                    "inside_approx_1p5m_support_rows": bool_count(group, "within_approx_1p5m_center_support"),
                    "ready_after_ogs_output_rows": bool_count(group, "ready_for_residual_after_ogs_output"),
                    "sample_log10_resistivity_min": float(group["sample_log10_resistivity"].min()),
                    "sample_log10_resistivity_median": float(group["sample_log10_resistivity"].median()),
                    "sample_log10_resistivity_max": float(group["sample_log10_resistivity"].max()),
                    "area_m2_sum": float(group["ert_cell_area_m2_transformed"].sum()),
                    "nearest_ogs_distance_m_median": float(group["ogs_nearest_centroid_distance_m"].median()),
                    "nearest_ogs_distance_m_max": float(group["ogs_nearest_centroid_distance_m"].max()),
                }
            )
    return pd.DataFrame(rows)


def build_summary(
    *,
    archive: pd.DataFrame,
    timesteps: pd.DataFrame,
    timestep_audit: pd.DataFrame,
    pairs: pd.DataFrame,
    kruschwitz: pd.DataFrame,
    relations: pd.DataFrame,
    projection: pd.DataFrame,
    projection_groups: pd.DataFrame,
    state_ert: pd.DataFrame,
    operator_summary: dict[str, Any],
    projection_summary: dict[str, Any],
    outputs: dict[str, str],
) -> dict[str, Any]:
    matching = bool_count(timesteps, "has_matching_vtk")
    missing = int(timesteps.shape[0] - matching)
    recommended = operator_summary.get("recommended_relation", {})
    summary: dict[str, Any] = {
        "archive_folders": int(archive.shape[0]),
        "archive_vtk_files": int(pd.to_numeric(archive.get("vtk_files", pd.Series(dtype=int)), errors="coerce").sum()),
        "archive_timestep_entries": int(
            pd.to_numeric(archive.get("timestep_entries", pd.Series(dtype=int)), errors="coerce").sum()
        ),
        "timestep_rows": int(timesteps.shape[0]),
        "timesteps_with_matching_vtk": matching,
        "timesteps_missing_matching_vtk": missing,
        "timestep_activation_gate_counts": value_counts(timestep_audit, "semantic_activation_gate"),
        "state_ert_target_rows": int(state_ert.shape[0]),
        "state_ert_target_status_counts": value_counts(state_ert, "target_status"),
        "paired_nmr_resistivity_rows": int(pairs.shape[0]),
        "paired_nmr_resistivity_niche_counts": value_counts(pairs, "niche"),
        "kruschwitz_relation_rows": int(kruschwitz.shape[0]),
        "operator_relation_rows": int(relations.shape[0]),
        "recommended_relation_id": operator_summary.get("recommended_relation_id"),
        "recommended_relation": recommended,
        "n4_pair_rmse_log10_resistivity": None,
        "projection_lookup_rows": int(projection.shape[0]),
        "projection_lookup_status_counts": value_counts(projection, "ogs_lookup_status"),
        "projection_inside_ogs_cell_rows": bool_count(projection, "inside_ogs_cell"),
        "projection_inside_approx_1p5m_support_rows": bool_count(projection, "within_approx_1p5m_center_support"),
        "projection_ready_after_ogs_output_rows": bool_count(projection, "ready_for_residual_after_ogs_output"),
        "projection_sample_log10_resistivity_quantiles": quantiles(projection["sample_log10_resistivity"])
        if not projection.empty
        else {},
        "projection_summary": projection_summary,
        "remaining_blocker": operator_summary.get("remaining_blocker") or projection_summary.get("remaining_blocker"),
        "outputs": outputs,
        "activation_rules": [
            "ERT measures an electrical resistivity field, not water content, saturation, pressure, or permeability directly.",
            "Use OGS theta = porosity * liquid_saturation as the model input to a local empirical rho(theta) relation.",
            "Use log10-resistivity residuals after projection to the ERT/common support because the calibration is multiplicative.",
            "Do not activate ERT residuals until OGS outputs exist and the ERT-to-OGS transform plus exact near-niche support mask are confirmed.",
            "Aggregate or regularize ERT cells before weighting because neighbouring inversion cells are spatially correlated.",
        ],
    }
    if not relations.empty and "relation_id" in relations.columns:
        n4 = relations[relations["relation_id"].astype(str).eq("nmr_pairs_N4")]
        if not n4.empty:
            summary["n4_pair_rmse_log10_resistivity"] = float(n4["rmse_log10_resistivity"].iloc[0])
    if not archive.empty:
        summary["archive_first_timestamp_iso"] = str(archive["first_timestamp_iso"].dropna().min())
        summary["archive_last_timestamp_iso"] = str(archive["last_timestamp_iso"].dropna().max())
    if not projection_groups.empty:
        support = projection_groups[projection_groups["group_type"].eq("central_support_and_ready")]
        summary["projection_support_group_rows"] = support.to_dict(orient="records")
    return summary


def fmt(value: Any, digits: int = 4) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if not np.isfinite(number):
        return "n/a"
    return f"{number:.{digits}g}"


def write_markdown(
    path: Path,
    summary: dict[str, Any],
    relation_audit: pd.DataFrame,
    projection_groups: pd.DataFrame,
) -> None:
    rec = summary.get("recommended_relation", {})
    logq = summary.get("projection_sample_log10_resistivity_quantiles", {})
    lines = [
        "# ERT Measurement Semantics Audit",
        "",
        "This audit keeps the electrical-resistivity measurement stream separate from",
        "water content, saturation, and permeability.  ERT can become a strong spatial",
        "state residual only after the calibration, projection support, and OGS output",
        "sampling gates are all satisfied.",
        "",
        "## Key Counts",
        "",
        f"- ERT archive folders: {summary['archive_folders']}",
        f"- VTK files in archive inventory: {summary['archive_vtk_files']}",
        f"- Timestep rows: {summary['timestep_rows']}",
        f"- Timesteps with matching VTK: {summary['timesteps_with_matching_vtk']}",
        f"- Timesteps missing matching VTK: {summary['timesteps_missing_matching_vtk']}",
        f"- State-target ERT rows: {summary['state_ert_target_rows']}",
        f"- Paired NMR/resistivity calibration rows: {summary['paired_nmr_resistivity_rows']}",
        f"- ERT projection lookup rows: {summary['projection_lookup_rows']}",
        f"- ERT cells inside an OGS cell: {summary['projection_inside_ogs_cell_rows']}",
        f"- ERT cells inside approximate 1.5 m support: {summary['projection_inside_approx_1p5m_support_rows']}",
        f"- Rows ready after OGS output and current support screen: {summary['projection_ready_after_ogs_output_rows']}",
        "",
        "## What ERT Observes",
        "",
        "ERT observes an electrical response that has already been inverted to a bulk",
        "resistivity field on the ERT inversion mesh.  It is not a direct measurement",
        "of saturation, volumetric water content, pressure, or permeability.  In the",
        "current workflow it enters only through a forward observation path:",
        "",
        "```text",
        "OGS S_l and porosity -> theta_model = porosity * S_l",
        "theta_model -> rho_pred using a local empirical theta-resistivity relation",
        "rho_pred -> ERT/common support -> log10-resistivity residual",
        "```",
        "",
        "## Calibration Relation",
        "",
        f"- Recommended relation: `{summary.get('recommended_relation_id')}`",
        f"- Equation: `rho_ohm_m = {fmt(rec.get('coefficient_a'), 6)} * theta_fraction ** {fmt(rec.get('exponent_b'), 6)}`",
        f"- Calibrated theta range: {fmt(rec.get('theta_min'), 4)} to {fmt(rec.get('theta_max'), 4)}",
        f"- Recommended-relation resistivity range: {fmt(rec.get('resistivity_min_ohm_m'), 5)} to {fmt(rec.get('resistivity_max_ohm_m'), 5)} ohm m",
        f"- Niche-4 paired NMR/resistivity diagnostic RMSE: {fmt(summary.get('n4_pair_rmse_log10_resistivity'), 4)} log10 resistivity units",
        "",
        "| Relation | Role | Points | a | b | RMSE log10 rho | Theta range | Gate |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for _, row in relation_audit.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['relation_id']}`",
                    str(row["semantic_role"]),
                    str(int(row["n_points"])),
                    fmt(row["coefficient_a"], 5),
                    fmt(row["exponent_b"], 5),
                    fmt(row["rmse_log10_resistivity"], 4),
                    f"{fmt(row['theta_min'], 3)}-{fmt(row['theta_max'], 3)}",
                    str(row["activation_gate"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Spatial Support",
            "",
            "The current projection is a centroid lookup from a reference ERT VTK mesh to",
            "the OGS bulk mesh.  It uses the explicit provisional transform",
            "`model_x = raw_x`, `model_y = raw_y + 500`.  This is a reproducible support",
            "bridge, not a full ERT forward solver.",
            "",
            f"- Sample log10 resistivity range in the reference VTK: min={fmt(logq.get('min'), 5)}, p50={fmt(logq.get('p50'), 5)}, max={fmt(logq.get('max'), 5)}",
            "",
            "| Projection group | Rows | Inside OGS cell | Approx. support | Ready after OGS output | Median nearest OGS distance m |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    support_rows = projection_groups[projection_groups["group_type"].eq("central_support_and_ready")].copy()
    for _, row in support_rows.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['group_key']}`",
                    str(int(row["rows"])),
                    str(int(row["inside_ogs_cell_rows"])),
                    str(int(row["inside_approx_1p5m_support_rows"])),
                    str(int(row["ready_after_ogs_output_rows"])),
                    fmt(row["nearest_ogs_distance_m_median"], 5),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Activation Decision",
            "",
            "- Do not use ERT as measured saturation or measured permeability.",
            "- Do not activate field residuals for the 16 timestep rows without matching VTK members.",
            "- Do not activate numerical ERT residuals until OGS outputs are sampled and the coordinate transform plus exact 35 cm-in-rock/near-niche support mask are confirmed.",
            "- When activated, use log10-resistivity residuals with aggregation or support weights; neighbouring ERT inversion cells are correlated and should not be counted as independent point measurements.",
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
    archive = read_csv(processed / "ert_archive_inventory.csv")
    timesteps = read_csv(processed / "ert_timesteps.csv")
    pairs = read_csv(processed / "ert_nmr_resistivity_pairs.csv")
    kruschwitz = read_csv(processed / "ert_kruschwitz2004_relation.csv")
    relations = read_csv(processed / "ert_water_content_resistivity_operator.csv")
    projection = read_csv(processed / "ert_spatial_projection_lookup.csv")
    state_targets = read_csv(processed / "state_observation_targets.csv")
    operator_summary = read_json(processed / "ert_observation_operator_summary.json")
    projection_summary = read_json(processed / "ert_spatial_projection_summary.json")
    state_ert = ert_targets(state_targets)

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "timestep_audit": str(output_dir / "ert_measurement_semantics_timestep_audit.csv"),
        "relation_audit": str(output_dir / "ert_measurement_semantics_relation_audit.csv"),
        "projection_group_summary": str(output_dir / "ert_measurement_semantics_projection_groups.csv"),
        "summary": str(output_dir / "ert_measurement_semantics_summary.json"),
        "markdown": str(output_dir / "ert_measurement_semantics.md"),
    }
    timestep_audit = build_timestep_audit(timesteps)
    relation_audit = build_relation_audit(relations, operator_summary)
    projection_groups = build_projection_group_summary(projection)
    summary = build_summary(
        archive=archive,
        timesteps=timesteps,
        timestep_audit=timestep_audit,
        pairs=pairs,
        kruschwitz=kruschwitz,
        relations=relations,
        projection=projection,
        projection_groups=projection_groups,
        state_ert=state_ert,
        operator_summary=operator_summary,
        projection_summary=projection_summary,
        outputs=outputs,
    )
    timestep_audit.to_csv(outputs["timestep_audit"], index=False)
    relation_audit.to_csv(outputs["relation_audit"], index=False)
    projection_groups.to_csv(outputs["projection_group_summary"], index=False)
    Path(outputs["summary"]).write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(Path(outputs["markdown"]), summary, relation_audit, projection_groups)
    print(f"wrote {outputs['timestep_audit']}")
    print(f"wrote {outputs['relation_audit']}")
    print(f"wrote {outputs['projection_group_summary']}")
    print(f"wrote {outputs['summary']}")
    print(f"wrote {outputs['markdown']}")
    print(f"ERT timestep rows: {summary['timestep_rows']}")
    print(f"projection-ready rows after OGS output: {summary['projection_ready_after_ogs_output_rows']}")


if __name__ == "__main__":
    main()
