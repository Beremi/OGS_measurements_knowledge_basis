#!/usr/bin/env python3
"""Build a consolidated request package for closing measurement activation gates."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any


REQUEST_SPECS: dict[str, dict[str, str]] = {
    "ERT_TRANSFORM_SUPPORT": {
        "priority": "high",
        "request_type": "support_geometry_and_transform",
        "audience": "BGR ERT provider / Markus Furche via Gesa Ziefle",
        "owner_or_source": "BGR ERT processing source",
        "external_or_internal": "external",
        "exact_request": (
            "Confirm the coordinate frame of the ERT inversion VTK fields and electrode files, "
            "the exact transform into the local OGS 2D x/y frame, and the accepted near-niche "
            "support mask for model comparison. The current local operator assumes model_x = "
            "raw_x and model_y = raw_y + 500 and uses a provisional central support mask."
        ),
        "minimum_acceptance_criteria": (
            "A written transform definition or script; coordinate-frame origin and axes; tunnel/"
            "niche contour or support polygon; accepted handling of the 35 cm rock-depth "
            "recommendation; and a decision on whether the current 1.5 m/radial support variants "
            "are acceptable or must be replaced."
        ),
        "why_needed_for_model": (
            "ERT can only become a weighted log-resistivity residual if each inversion cell is "
            "placed on the same physical support as the OGS cells. The support-sensitivity audit "
            "shows that changing support can change candidate rankings."
        ),
        "would_unlock": "Promote ERT from diagnostic field check to candidate active residual support.",
        "existing_local_artifacts": (
            "inversion_workflow/processed_observations/ert_spatial_projection_operator.md; "
            "inversion_workflow/ert_support_sensitivity.md; "
            "cda_knowledge_base/measurements/ert/source_files/ERT_meas_Niche_open.zip"
        ),
        "related_request_package": "",
    },
    "ERT_UNCERTAINTY": {
        "priority": "high",
        "request_type": "uncertainty_model",
        "audience": "BGR ERT provider / Markus Furche via Gesa Ziefle",
        "owner_or_source": "BGR ERT inversion/evaluation source",
        "external_or_internal": "external",
        "exact_request": (
            "Provide or approve an ERT inversion-field uncertainty and correlation model for "
            "log10 resistivity residuals: per-cell or region-level sigma, time correlation, "
            "spatial correlation/effective degrees of freedom, and any recommended filtering "
            "or aggregation before comparison to OGS theta-derived resistivity."
        ),
        "minimum_acceptance_criteria": (
            "Either a covariance/error export or an agreed simplified weighting rule, including "
            "units/log base, independence assumptions, date grouping, and rules for unstable or "
            "fracture-dominated cells."
        ),
        "why_needed_for_model": (
            "The archive has dense ERT fields, but VTK pixels cannot be treated as independent "
            "observations without over-weighting ERT relative to sparse NMR/permeability data."
        ),
        "would_unlock": "Defensible ERT likelihood weight or downweighted diagnostic residual.",
        "existing_local_artifacts": (
            "inversion_workflow/ert_candidate_discrimination.md; "
            "inversion_workflow/measurement_likelihood_model.md"
        ),
        "related_request_package": "",
    },
    "NMR_BOUND_WATER": {
        "priority": "high",
        "request_type": "internal_method_decision",
        "audience": "internal modelling decision, optionally checked with Stephan Costabel",
        "owner_or_source": "IGN/UGN modelling team plus BGR NMR source if needed",
        "external_or_internal": "internal_with_optional_external_confirmation",
        "exact_request": (
            "Choose the final NMR residual definition before reporting an all-measurement fit: "
            "raw absolute theta with an added model-error floor, label/campaign bias residual, "
            "within-position trend/anomaly residual, or a free-water correction based on "
            "bound/interlayer-water evidence."
        ),
        "minimum_acceptance_criteria": (
            "A documented objective formula, bias/offset parameter handling, sigma/error floor, "
            "which weekly/seasonal rows are active, and whether the known February-April 2025 "
            "4E detuning issue is excluded, corrected, or downweighted."
        ),
        "why_needed_for_model": (
            "NMR measures total NMR-visible water content, while the OGS state proxy is mobile "
            "theta = porosity * liquid_saturation. Many NMR rows exceed fixed model porosity "
            "unless a bound/interlayer-water or bias term is included."
        ),
        "would_unlock": "A final NMR likelihood definition instead of a conditional active state residual.",
        "existing_local_artifacts": (
            "inversion_workflow/processed_observations/nmr_bound_water_sensitivity.md; "
            "inversion_workflow/nmr_candidate_bias_sensitivity.md"
        ),
        "related_request_package": "",
    },
    "PERM_ERROR_MODEL": {
        "priority": "medium",
        "request_type": "method_decision_and_optional_source_confirmation",
        "audience": "internal modelling decision, optionally checked with Gesa Ziefle/BGR",
        "owner_or_source": "IGN/UGN modelling team plus BGR permeability source if needed",
        "external_or_internal": "internal_with_optional_external_confirmation",
        "exact_request": (
            "Approve the gas-pulse permeability residual model: log10 intrinsic permeability "
            "space, duplicate-aware interval weights, current sigma = 0.5 log10 units, and the "
            "policy for gas/slip/liquid-equivalent caveats."
        ),
        "minimum_acceptance_criteria": (
            "A written statement of whether the nitrogen pulse-test values are used as intrinsic "
            "permeability constraints on the OGS base permeability tensor magnitude, whether any "
            "Klinkenberg/slip correction is needed, and how scalar interval measurements are mapped "
            "to the anisotropic tensor field."
        ),
        "why_needed_for_model": (
            "The active field is a tensor-valued intrinsic permeability. The measurements are gas "
            "pulse-test interval estimates with directional/support effects, so the residual must "
            "not be described as direct water hydraulic conductivity or as all tensor components."
        ),
        "would_unlock": "Cleaner wording for active permeability residuals and defensible sigma/caveat handling.",
        "existing_local_artifacts": (
            "inversion_workflow/processed_observations/permeability_measurement_semantics.md; "
            "inversion_workflow/processed_observations/permeability_observation_targets.csv"
        ),
        "related_request_package": (
            "inversion_workflow/processed_observations/permeability_endpoint_geometry_request.md"
        ),
    },
    "PERM_LIKELIHOOD_POLICY": {
        "priority": "high",
        "request_type": "likelihood_policy_decision",
        "audience": "internal modelling decision, optionally checked with Gesa Ziefle/BGR",
        "owner_or_source": "IGN/UGN modelling team plus BGR permeability source if needed",
        "external_or_internal": "internal_with_optional_external_confirmation",
        "exact_request": (
            "Choose the direct-permeability likelihood policy before more active-objective OGS spending: "
            "keep the current duplicate-weighted rowwise Gaussian default, promote a robust row likelihood, "
            "aggregate rows by model support cell, gate configured-scalar-range outliers, or require a new "
            "parameterization before running more candidates."
        ),
        "minimum_acceptance_criteria": (
            "A written policy choice, residual formula, row/group weights, outlier handling, reranking rule "
            "for existing candidates, and the condition under which the current rowwise Gaussian objective "
            "remains the report default."
        ),
        "why_needed_for_model": (
            "The current field fits duplicate-weighted means of repeated rows sharing the same support cell, "
            "while individual pulse-test rows within those cells conflict by several log units. More smooth "
            "field sampling is not the same thing as resolving the likelihood semantics."
        ),
        "would_unlock": "A defensible direct-permeability objective policy for the next search or scenario reranking.",
        "existing_local_artifacts": (
            "inversion_workflow/permeability_likelihood_policy_audit.md; "
            "inversion_workflow/permeability_likelihood_decision_request.md"
        ),
        "related_request_package": "inversion_workflow/permeability_likelihood_decision_request.md",
    },
    "PERM_ENDPOINT_GEOMETRY": {
        "priority": "medium",
        "request_type": "source_file_request",
        "audience": "Gesa Ziefle / BGR permeability source",
        "owner_or_source": "BGR permeability measurement source",
        "external_or_internal": "external",
        "exact_request": (
            "Provide labelled endpoint geometry or approved digitized traces for the historical "
            "BCD-A24, BCD-A25, BCD-A26, BCD-A27, and BFM-D19 permeability intervals that are "
            "currently retained but inactive."
        ),
        "minimum_acceptance_criteria": (
            "For each interval: borehole id, open/closed assignment, start/end coordinates or "
            "depths with convention, orientation, interval length/support, date/source table, "
            "permeability value, and uncertainty/evaluation note."
        ),
        "why_needed_for_model": (
            "These older rows cannot be projected to OGS cells until the measured 3D interval "
            "volume is known. They are useful because they broaden the permeability evidence "
            "outside the currently active mapped rows."
        ),
        "would_unlock": "Additional permeability pulse-test rows for direct parameter fitting.",
        "existing_local_artifacts": (
            "inversion_workflow/processed_observations/permeability_missing_geometry_audit.md"
        ),
        "related_request_package": (
            "inversion_workflow/processed_observations/permeability_endpoint_geometry_request.md"
        ),
    },
    "RH_ACTIVE_CURVE_PROVENANCE": {
        "priority": "high",
        "request_type": "provenance_and_processing_files",
        "audience": "Gesa Ziefle / BGR RH or OGS boundary-curve source",
        "owner_or_source": "BGR OGS/RH processing source",
        "external_or_internal": "external",
        "exact_request": (
            "Provide the provenance for the active open-niche pressure curve in "
            "08_08_open_niche_seasonal.xml: source sensors, input sheets, scripts/notebooks, "
            "time-axis origin, smoothing/filtering, manual edits, Kelvin constants, sign "
            "convention, and open/closed curve mapping."
        ),
        "minimum_acceptance_criteria": (
            "Original or intermediate table/script, sensor selection rule, model-time zero and "
            "timezone, RH percent/fraction convention, temperature/density constants, pressure "
            "unit/sign, extrapolation policy, and decision for post-active-curve dates."
        ),
        "why_needed_for_model": (
            "RH/suction affects the OGS boundary forcing. The local RH-derived candidate envelope "
            "does not reproduce the active curve, so replacing or trusting the curve requires "
            "provenance."
        ),
        "would_unlock": "Verified boundary forcing or a reproducible replacement curve.",
        "existing_local_artifacts": (
            "inversion_workflow/processed_observations/rh_boundary_candidate_curves.md; "
            "inversion_workflow/processed_observations/rh_boundary_uncertainty.md"
        ),
        "related_request_package": (
            "inversion_workflow/processed_observations/rh_boundary_provenance_request.md"
        ),
    },
    "RH_UNCERTAINTY": {
        "priority": "high",
        "request_type": "uncertainty_model_and_policy",
        "audience": "internal modelling decision with BGR confirmation if possible",
        "owner_or_source": "IGN/UGN modelling team plus BGR RH source if needed",
        "external_or_internal": "internal_with_optional_external_confirmation",
        "exact_request": (
            "Decide whether RH/suction enters only as boundary forcing, as a retention validation "
            "target, or as a future calibration target; approve the boundary/retention uncertainty "
            "model and replacement policy for RH-derived curves."
        ),
        "minimum_acceptance_criteria": (
            "Accepted sensor subset; uncertainty bands for RH-to-pressure conversion; treatment of "
            "RH7/RH8 low outliers and high-RH values; whether candidate curves replace or only audit "
            "the active XML curve; and release gates for retention parameters."
        ),
        "why_needed_for_model": (
            "A pressure boundary can move the entire desaturation response. It should not be fitted "
            "or replaced without a clear uncertainty and provenance policy."
        ),
        "would_unlock": "Boundary-forcing replacement decision and possible retention-parameter gate.",
        "existing_local_artifacts": (
            "inversion_workflow/processed_observations/rh_boundary_uncertainty.md; "
            "inversion_workflow/processed_observations/rh_boundary_candidate_curves.md"
        ),
        "related_request_package": (
            "inversion_workflow/processed_observations/rh_boundary_provenance_request.md"
        ),
    },
    "TAUPE_UNIT_CALIBRATION": {
        "priority": "high",
        "request_type": "calibration_confirmation",
        "audience": "Taupe/TDR provider via Gesa Ziefle",
        "owner_or_source": "BGR/ISU Taupe processing source",
        "external_or_internal": "external",
        "exact_request": (
            "Confirm what the values in Taupe_WC.xlsx physically represent: calibrated volumetric "
            "water-content percent, relative dielectric permittivity, ARDP-derived proxy, or another "
            "quantity. Provide the sensor-specific calibration equations and uncertainty."
        ),
        "minimum_acceptance_criteria": (
            "Workbook unit for every sheet/column; calibration equation and constants; whether "
            "values are already corrected for rock porosity/mineral matrix; uncertainty by sensor/"
            "band; baseline/reference date; and ARDP-to-water or dielectric conversion details."
        ),
        "why_needed_for_model": (
            "The current workbook values pass some sanity checks if interpreted as water-content "
            "percent but fail if interpreted through a generic Topp permittivity conversion. Absolute "
            "Taupe residuals would be misleading without calibration."
        ),
        "would_unlock": "Possible absolute Taupe water-content/saturation residual, or confirmed trend-only use.",
        "existing_local_artifacts": (
            "inversion_workflow/processed_observations/taupe_tdr_semantics.md; "
            "cda_knowledge_base/measurements/taupe_tdr/source_files/Taupe_WC.xlsx"
        ),
        "related_request_package": "",
    },
    "TAUPE_GROUP_WEIGHTS": {
        "priority": "medium",
        "request_type": "uncertainty_model",
        "audience": "internal modelling decision with Taupe/TDR provider confirmation if possible",
        "owner_or_source": "IGN/UGN modelling team plus BGR/ISU Taupe source if needed",
        "external_or_internal": "internal_with_optional_external_confirmation",
        "exact_request": (
            "Approve Taupe/TDR grouped weighting before objective activation: aggregate weighting, "
            "equal-series, equal-sensor, equal-EDZ-band, robust/trimmed score, or a provider-supplied "
            "series uncertainty model."
        ),
        "minimum_acceptance_criteria": (
            "Series grouping rule, sigma/error model, handling of strongly correlated EDZ bands, "
            "sensor-specific downweighting, and whether A3/A4 only or all sensors should contribute."
        ),
        "why_needed_for_model": (
            "The series-weight audit shows different Taupe subseries prefer different permeability "
            "candidates. A naive row count would over-weight dense correlated bands."
        ),
        "would_unlock": "Taupe trend likelihood weights or a clearly scoped diagnostic score.",
        "existing_local_artifacts": (
            "inversion_workflow/taupe_series_weight_sensitivity.md; "
            "inversion_workflow/taupe_candidate_discrimination.md"
        ),
        "related_request_package": "",
    },
    "TAUPE_SUPPORT": {
        "priority": "medium",
        "request_type": "support_geometry_decision",
        "audience": "internal modelling decision with Taupe/TDR provider confirmation if possible",
        "owner_or_source": "IGN/UGN modelling team plus BGR/ISU Taupe source if needed",
        "external_or_internal": "internal_with_optional_external_confirmation",
        "exact_request": (
            "Decide how to handle A7/A8 Taupe sensors that are outside the current Niche-4 OGS "
            "support: exclude them, use them only qualitatively, expand the geometry/model scope, "
            "or map them to a separate support if justified."
        ),
        "minimum_acceptance_criteria": (
            "Sensor/borehole support decision for A3, A4, A7, and A8; explicit inclusion/exclusion "
            "flags; and a statement that excluded sensors must not be counted as active residuals."
        ),
        "why_needed_for_model": (
            "Half of the Taupe workbook series are outside the current local mesh support. Including "
            "them without matching OGS support would create nonphysical residuals."
        ),
        "would_unlock": "A clean Taupe activation mask and report wording for excluded sensors.",
        "existing_local_artifacts": (
            "inversion_workflow/processed_observations/taupe_tdr_semantics.md; "
            "inversion_workflow/taupe_series_weight_sensitivity.md"
        ),
        "related_request_package": "",
    },
    "HM_NUMERIC_EXPORTS": {
        "priority": "high",
        "request_type": "source_file_request",
        "audience": "Gesa Ziefle / BGR Geoscope, laser-scan, and levelling source",
        "owner_or_source": "BGR other-HM monitoring source",
        "external_or_internal": "external",
        "exact_request": (
            "Provide hard-residual-ready numeric exports for Geoscope mini-piezometers, "
            "extensometers, crackmeters, the 2026-04-20 laser-scan statistical interpretation, "
            "and the full precision-levelling survey table."
        ),
        "minimum_acceptance_criteria": (
            "Machine-readable tables with timestamps or survey epochs, instrument ids, measured "
            "values, units, coordinates/support ids, reference/zero conventions, calibration or "
            "processing provenance, quality/status flags, and uncertainty/covariance where available."
        ),
        "why_needed_for_model": (
            "The local catalogue has layout geometry and qualitative HM statements, but no numeric "
            "time series or statistical exports that can be sampled against OGS pressure/displacement "
            "states."
        ),
        "would_unlock": "Potential pressure/deformation/laser/levelling validation residuals.",
        "existing_local_artifacts": (
            "inversion_workflow/processed_observations/other_hm_numeric_source_audit.md; "
            "cda_knowledge_base/measurements/other_hm_monitoring/source_files/"
        ),
        "related_request_package": (
            "inversion_workflow/processed_observations/other_hm_missing_numeric_request.md"
        ),
    },
    "HM_UNCERTAINTY": {
        "priority": "high",
        "request_type": "metadata_and_uncertainty_model",
        "audience": "Gesa Ziefle / BGR Geoscope, laser-scan, and levelling source",
        "owner_or_source": "BGR other-HM monitoring source",
        "external_or_internal": "external",
        "exact_request": (
            "For every provided other-HM export, include the metadata required for residual weights: "
            "units, epochs, coordinate/support geometry, reference conventions, uncertainty/covariance, "
            "quality flags, and failure/maintenance intervals."
        ),
        "minimum_acceptance_criteria": (
            "Each table has self-contained units and reference conventions; failed sensors such as "
            "BCD-A9/B10 are flagged; laser registration uncertainty and masks are included; and "
            "levelling covariance/reference frame are documented."
        ),
        "why_needed_for_model": (
            "Even if numeric values are found, they cannot become hard residuals without metadata "
            "that states what OGS quantity and support they measure."
        ),
        "would_unlock": "Defensible weights and activation gates for other-HM residuals.",
        "existing_local_artifacts": (
            "inversion_workflow/processed_observations/other_hm_missing_numeric_request.md; "
            "inversion_workflow/processed_observations/other_hm_numeric_source_audit.md"
        ),
        "related_request_package": (
            "inversion_workflow/processed_observations/other_hm_missing_numeric_request.md"
        ),
    },
}


EXTRA_REQUEST_GATES = {
    "PERM_LIKELIHOOD_POLICY": {
        "stream": "permeability_pulse_tests",
        "gate_id": "PERM_LIKELIHOOD_POLICY",
        "gate_label": "direct permeability robust/support-cell likelihood policy before more OGS",
        "status": "internal_policy",
        "required_for_active_likelihood": "False",
        "evidence": (
            "The likelihood-policy audit finds 75 active direct rows, current Gaussian objective 269.818057, "
            "top-10 row-loss share 0.494, 16 support-cell groups with observed range >=1 log10, and a "
            "support-cell weighted-mean diagnostic objective near zero."
        ),
        "blocker_or_caveat": (
            "The active rowwise Gaussian policy is retained for reproducibility, but robust tails, support-cell "
            "aggregation, and scalar-range outlier handling are explicit modelling decisions before more "
            "active-objective OGS spending."
        ),
        "authoritative_artifacts": (
            "permeability_likelihood_policy_audit.md; permeability_likelihood_decision_request.md"
        ),
    },
    "PERM_ENDPOINT_GEOMETRY": {
        "stream": "permeability_pulse_tests",
        "gate_id": "PERM_SUPPORT",
        "gate_label": "missing historical endpoint geometry for inactive permeability rows",
        "status": "tracked_caveat",
        "required_for_active_likelihood": "False",
        "evidence": "98 older permeability rows are retained but inactive because labelled endpoint geometry is missing.",
        "blocker_or_caveat": "Historical permeability endpoints are needed only if these older rows should enter the fit.",
        "authoritative_artifacts": "permeability_missing_geometry_audit.md; permeability_endpoint_geometry_request.md",
    }
}


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("inversion_workflow"))
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files"),
    )
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def display_path(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def build_request_rows(repo: Path) -> list[dict[str, Any]]:
    gate_rows = read_csv(repo / "inversion_workflow/measurement_stream_activation_gate_checks.csv")
    gate_rows = [
        row
        for row in gate_rows
        if row.get("required_for_active_likelihood") == "True" and row.get("status") in {"fail", "warn"}
    ]
    for request_id, row in EXTRA_REQUEST_GATES.items():
        extra = dict(row)
        extra["_request_id_override"] = request_id
        gate_rows.append(extra)

    request_rows: list[dict[str, Any]] = []
    for row in gate_rows:
        gate_id = row["gate_id"]
        request_id = row.get("_request_id_override") or gate_id
        spec = REQUEST_SPECS[request_id]
        request_rows.append(
            {
                "request_id": request_id.lower(),
                "priority": spec["priority"],
                "stream": row["stream"],
                "gate_id": gate_id,
                "gate_label": row["gate_label"],
                "gate_status": row["status"],
                "required_for_active_likelihood": row["required_for_active_likelihood"],
                "request_type": spec["request_type"],
                "audience": spec["audience"],
                "owner_or_source": spec["owner_or_source"],
                "external_or_internal": spec["external_or_internal"],
                "exact_request": spec["exact_request"],
                "minimum_acceptance_criteria": spec["minimum_acceptance_criteria"],
                "current_evidence": row["evidence"],
                "current_blocker_or_caveat": row["blocker_or_caveat"],
                "why_needed_for_model": spec["why_needed_for_model"],
                "would_unlock": spec["would_unlock"],
                "existing_local_artifacts": spec["existing_local_artifacts"],
                "related_request_package": spec["related_request_package"],
                "source_gate_artifacts": row["authoritative_artifacts"],
            }
        )
    return sorted(
        request_rows,
        key=lambda row: (
            PRIORITY_ORDER.get(str(row["priority"]), 99),
            str(row["external_or_internal"]),
            str(row["stream"]),
            str(row["request_id"]),
        ),
    )


def summarize(rows: list[dict[str, Any]], audit_summary: dict[str, Any]) -> dict[str, Any]:
    priority_counts = Counter(row["priority"] for row in rows)
    stream_counts = Counter(row["stream"] for row in rows)
    type_counts = Counter(row["request_type"] for row in rows)
    external_counts = Counter(row["external_or_internal"] for row in rows)
    failed = [row for row in rows if row["gate_status"] == "fail"]
    warnings = [row for row in rows if row["gate_status"] == "warn"]
    high = [row["request_id"] for row in rows if row["priority"] == "high"]
    gates = {(row["stream"], row["gate_id"]) for row in rows}
    return {
        "status": "measurement_gate_closure_request_generated",
        "request_count": len(rows),
        "failed_gate_request_count": len(failed),
        "warning_gate_request_count": len(warnings),
        "tracked_caveat_request_count": len([row for row in rows if row["gate_status"] == "tracked_caveat"]),
        "gates_represented_count": len(gates),
        "required_failed_gates_from_audit": audit_summary.get("required_gate_fail_count"),
        "required_warning_gates_from_audit": audit_summary.get("required_gate_warn_count"),
        "request_counts_by_priority": dict(sorted(priority_counts.items())),
        "request_counts_by_stream": dict(sorted(stream_counts.items())),
        "request_counts_by_type": dict(sorted(type_counts.items())),
        "request_counts_by_external_or_internal": dict(sorted(external_counts.items())),
        "external_request_count": sum(1 for row in rows if row["external_or_internal"] == "external"),
        "internal_decision_count": sum(1 for row in rows if row["external_or_internal"].startswith("internal")),
        "high_priority_request_ids": high,
    }


def markdown_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Priority | Request | Stream | Gate | Audience | Unlocks |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['priority']}`",
                    f"`{row['request_id']}`",
                    f"`{row['stream']}`",
                    f"`{row['gate_id']}` ({row['gate_status']})",
                    str(row["audience"]).replace("|", "\\|"),
                    str(row["would_unlock"]).replace("|", "\\|"),
                ]
            )
            + " |"
        )
    return lines


def write_markdown(path: Path, rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    lines = [
        "# Measurement Gate Closure Request",
        "",
        "This package converts the stream activation-gate audit into concrete requests and",
        "internal decisions needed before diagnostic measurement streams are promoted to",
        "hard residuals in the frozen OGS workflow.",
        "",
        "## Summary",
        "",
        f"- Requests: {summary['request_count']}",
        f"- Failed-gate requests: {summary['failed_gate_request_count']}",
        f"- Warning-gate requests: {summary['warning_gate_request_count']}",
        f"- External requests: {summary['external_request_count']}",
        f"- Internal or internal-with-confirmation decisions: {summary['internal_decision_count']}",
        f"- High-priority request ids: {', '.join(summary['high_priority_request_ids'])}",
        "",
        "Only direct permeability and NMR currently provide active objective rows. ERT,",
        "Taupe/TDR, RH/suction, and other-HM monitoring must remain diagnostic,",
        "boundary-audit, or qualitative streams until the requests below are closed.",
        "",
        "## Priority Table",
        "",
    ]
    lines.extend(markdown_table(rows))
    lines.extend(["", "## Requests By Stream", ""])
    for stream in sorted({row["stream"] for row in rows}):
        lines.extend([f"### `{stream}`", ""])
        for row in [item for item in rows if item["stream"] == stream]:
            lines.extend(
                [
                    f"#### `{row['request_id']}`",
                    "",
                    f"- Priority: `{row['priority']}`",
                    f"- Gate: `{row['gate_id']}` / {row['gate_label']} (`{row['gate_status']}`)",
                    f"- Request type: `{row['request_type']}`",
                    f"- Audience: {row['audience']}",
                    f"- Owner/source: {row['owner_or_source']}",
                    f"- External/internal: `{row['external_or_internal']}`",
                    f"- Exact request: {row['exact_request']}",
                    f"- Minimum acceptance criteria: {row['minimum_acceptance_criteria']}",
                    f"- Current evidence: {row['current_evidence']}",
                    f"- Current blocker/caveat: {row['current_blocker_or_caveat']}",
                    f"- Why needed for model: {row['why_needed_for_model']}",
                    f"- Would unlock: {row['would_unlock']}",
                    f"- Existing local artifacts: {row['existing_local_artifacts']}",
                    f"- Related request package: {row['related_request_package'] or 'none'}",
                    f"- Source gate artifacts: {row['source_gate_artifacts']}",
                    "",
                ]
            )
    lines.extend(
        [
            "## Email-Ready Grouping",
            "",
            "### External BGR / Provider Requests",
            "",
        ]
    )
    for row in [item for item in rows if item["external_or_internal"] == "external"]:
        lines.append(
            f"- `{row['request_id']}` to {row['audience']}: {row['exact_request']} "
            f"Minimum acceptance: {row['minimum_acceptance_criteria']}"
        )
    lines.extend(["", "### Internal Decisions", ""])
    for row in [item for item in rows if item["external_or_internal"].startswith("internal")]:
        lines.append(
            f"- `{row['request_id']}`: {row['exact_request']} "
            f"Minimum acceptance: {row['minimum_acceptance_criteria']}"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_email_draft(path: Path, rows: list[dict[str, Any]]) -> None:
    external_rows = [row for row in rows if row["external_or_internal"] == "external"]
    lines = [
        "# Draft: CD-A Measurement Gate Closure Requests",
        "",
        "Subject: CD-A modelling: files and confirmations needed for measurement-stream activation",
        "",
        "Dear Gesa,",
        "",
        "We have now catalogued the CD-A measurement files and built preliminary OGS comparison",
        "operators. Before we can describe ERT, Taupe/TDR, RH/suction, and other HM monitoring",
        "as hard residuals in the inversion objective, we need a few source confirmations and",
        "numeric exports. The current inversion can only be described as direct permeability plus",
        "conditional NMR, with the other streams used as diagnostics.",
        "",
    ]
    by_audience: dict[str, list[dict[str, Any]]] = {}
    for row in external_rows:
        by_audience.setdefault(row["audience"], []).append(row)
    for audience, group_rows in sorted(by_audience.items()):
        lines.extend([f"## {audience}", ""])
        for row in group_rows:
            lines.extend(
                [
                    f"- `{row['request_id']}` ({row['priority']}): {row['exact_request']}",
                    f"  Acceptance criteria: {row['minimum_acceptance_criteria']}",
                    f"  Why: {row['why_needed_for_model']}",
                ]
            )
        lines.append("")
    lines.extend(
        [
            "I can send the current local audit tables if useful. The main point is to avoid",
            "overstating a final all-measurement inversion before the support, calibration,",
            "uncertainty, and provenance gates are closed.",
            "",
            "Best,",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[2]
    output_dir = (repo / args.output_dir if not args.output_dir.is_absolute() else args.output_dir).resolve()
    catalogue_dir = (repo / args.catalogue_dir if not args.catalogue_dir.is_absolute() else args.catalogue_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    catalogue_dir.mkdir(parents=True, exist_ok=True)

    audit_summary = json.loads(
        (repo / "inversion_workflow/measurement_stream_activation_gate_audit_summary.json").read_text(
            encoding="utf-8"
        )
    )
    rows = build_request_rows(repo)
    summary = summarize(rows, audit_summary)

    csv_path = output_dir / "measurement_gate_closure_request.csv"
    json_path = output_dir / "measurement_gate_closure_request_summary.json"
    md_path = output_dir / "measurement_gate_closure_request.md"
    email_path = output_dir / "measurement_gate_closure_email_draft.md"
    fields = [
        "request_id",
        "priority",
        "stream",
        "gate_id",
        "gate_label",
        "gate_status",
        "required_for_active_likelihood",
        "request_type",
        "audience",
        "owner_or_source",
        "external_or_internal",
        "exact_request",
        "minimum_acceptance_criteria",
        "current_evidence",
        "current_blocker_or_caveat",
        "why_needed_for_model",
        "would_unlock",
        "existing_local_artifacts",
        "related_request_package",
        "source_gate_artifacts",
    ]
    write_csv(csv_path, rows, fields)
    write_markdown(md_path, rows, summary)
    write_email_draft(email_path, rows)

    copies = []
    for source in [csv_path, json_path, md_path, email_path]:
        if source == json_path:
            continue
        target = catalogue_dir / source.name
        shutil.copy2(source, target)
        copies.append({"source": display_path(source, repo), "catalogue_copy": display_path(target, repo)})
    summary["generated_files"] = [display_path(path, repo) for path in [csv_path, json_path, md_path, email_path]]
    summary["catalogue_copies"] = copies
    json_path.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    target = catalogue_dir / json_path.name
    shutil.copy2(json_path, target)
    summary["catalogue_copies"].append({"source": display_path(json_path, repo), "catalogue_copy": display_path(target, repo)})
    json_path.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shutil.copy2(json_path, target)

    print(json.dumps(json_ready(summary), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
