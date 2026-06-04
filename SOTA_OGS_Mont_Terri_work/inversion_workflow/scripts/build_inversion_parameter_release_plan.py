#!/usr/bin/env python3
"""Build a staged parameter-release plan from OGS XML and measurement readiness."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-parameters",
        type=Path,
        default=Path("ogs_settings/03_parameters_TRM.xml"),
    )
    parser.add_argument(
        "--projection-parameters",
        type=Path,
        default=Path("GESA_model_original/projection_on_mesh_2025-09-05/03_parameters_TRM.xml"),
    )
    parser.add_argument(
        "--candidate-parameters",
        type=Path,
        default=Path(
            "inversion_workflow/runs/regularized_ogs_candidate_001_length_0p025m/"
            "03_parameters_TRM.xml"
        ),
    )
    parser.add_argument(
        "--media",
        type=Path,
        default=Path("ogs_settings/04_media_TRM.xml"),
    )
    parser.add_argument(
        "--liquid-media",
        type=Path,
        default=Path("ogs_settings/04_1_media_aqu_liq.xml"),
    )
    parser.add_argument(
        "--twophase-media",
        type=Path,
        default=Path("ogs_settings/04_2_media_twophase.xml"),
    )
    parser.add_argument(
        "--likelihood-summary",
        type=Path,
        default=Path("inversion_workflow/measurement_likelihood_model_summary.json"),
    )
    parser.add_argument(
        "--likelihood-csv",
        type=Path,
        default=Path("inversion_workflow/measurement_likelihood_model.csv"),
    )
    parser.add_argument(
        "--candidate-set-summary",
        type=Path,
        default=Path(
            "inversion_workflow/runs/regularized_ogs_candidate_set/"
            "REGULARIZED_OGS_CANDIDATE_SET.json"
        ),
    )
    parser.add_argument(
        "--current-combined-summary",
        type=Path,
        default=Path("inversion_workflow/current_permeability_field/combined_objective_summary.json"),
    )
    parser.add_argument(
        "--current-state-summary",
        type=Path,
        default=Path("inversion_workflow/current_permeability_field/state_observation_evaluation_summary.json"),
    )
    parser.add_argument(
        "--next-field-fit-gate",
        type=Path,
        default=Path("inversion_workflow/permeability_next_field_fit_gate_summary.json"),
    )
    parser.add_argument(
        "--nmr-final-policy-gate",
        type=Path,
        default=Path("inversion_workflow/nmr_final_residual_policy_gate_summary.json"),
    )
    parser.add_argument(
        "--external-blocker-dashboard",
        type=Path,
        default=Path("inversion_workflow/external_blocker_dashboard_summary.json"),
    )
    parser.add_argument(
        "--objective-readiness",
        type=Path,
        default=Path("inversion_workflow/objective_readiness_audit_summary.json"),
    )
    parser.add_argument(
        "--thermal-expansivity-audit",
        type=Path,
        default=Path("inversion_workflow/thermal_expansivity_parameter_audit_summary.json"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/inversion_parameter_release_plan.csv"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("inversion_workflow/inversion_parameter_release_plan_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("inversion_workflow/inversion_parameter_release_plan.md"),
    )
    return parser.parse_args()


def parse_xml_fragment(path: Path) -> ET.Element:
    text = path.read_text(encoding="utf-8")
    return ET.fromstring(f"<root>\n{text}\n</root>")


def direct_text(element: ET.Element, tag: str) -> str:
    values = [child.text.strip() for child in element.findall(tag) if child.text and child.text.strip()]
    return " | ".join(values)


def parse_parameters(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    root = parse_xml_fragment(path)
    parameters: dict[str, dict[str, str]] = {}
    for parameter in root.findall("parameter"):
        name = direct_text(parameter, "name")
        if not name:
            continue
        record: dict[str, str] = {
            "name": name,
            "type": direct_text(parameter, "type"),
            "value": direct_text(parameter, "values") or direct_text(parameter, "value"),
            "field_name": direct_text(parameter, "field_name"),
            "expression": direct_text(parameter, "expression"),
            "curve": direct_text(parameter, "curve"),
            "base_parameter": direct_text(parameter, "parameter"),
            "source_file": str(path),
        }
        parameters[name] = {key: value for key, value in record.items() if value}
    return parameters


def parse_properties(path: Path) -> dict[str, list[dict[str, str]]]:
    if not path.exists():
        return {}
    root = parse_xml_fragment(path)
    properties: dict[str, list[dict[str, str]]] = {}
    for property_node in root.iter("property"):
        name = direct_text(property_node, "name")
        if not name:
            continue
        record: dict[str, str] = {
            "name": name,
            "type": direct_text(property_node, "type"),
            "parameter_name": direct_text(property_node, "parameter_name"),
            "source_file": str(path),
        }
        for child in property_node:
            tag = child.tag
            if tag in {"name", "type", "parameter_name"}:
                continue
            text = child.text.strip() if child.text and child.text.strip() else ""
            if text:
                record[tag] = text
        properties.setdefault(name, []).append(record)
    return properties


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_likelihood_rows(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    frame = pd.read_csv(path)
    if "measurement_stream" not in frame.columns:
        return {}
    return {
        str(row["measurement_stream"]): row.dropna().to_dict()
        for _, row in frame.iterrows()
    }


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
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return json_number(value)
    if value is pd.NA or value is None:
        return None
    return value


def describe_parameter(parameters: dict[str, dict[str, str]], name: str) -> str:
    parameter = parameters.get(name, {})
    if not parameter:
        return "not found"
    bits = []
    if parameter.get("type"):
        bits.append(parameter["type"])
    if parameter.get("value"):
        bits.append(parameter["value"])
    if parameter.get("field_name"):
        bits.append(f"field_name={parameter['field_name']}")
    if parameter.get("expression"):
        bits.append(f"expression={parameter['expression']}")
    if parameter.get("curve"):
        bits.append(f"curve={parameter['curve']}")
    if parameter.get("base_parameter"):
        bits.append(f"base_parameter={parameter['base_parameter']}")
    return "; ".join(bits) if bits else "present"


def get_property(properties: dict[str, list[dict[str, str]]], name: str, property_type: str | None = None) -> dict[str, str]:
    candidates = properties.get(name, [])
    if property_type is None:
        return candidates[0] if candidates else {}
    for candidate in candidates:
        if candidate.get("type") == property_type:
            return candidate
    return candidates[0] if candidates else {}


def format_property(property_row: dict[str, str], keys: list[str] | None = None) -> str:
    if not property_row:
        return "not found"
    bits = [property_row.get("type", "")]
    for key in keys or []:
        value = property_row.get(key)
        if value:
            bits.append(f"{key}={value}")
    return "; ".join(bit for bit in bits if bit)


def stream_stat(likelihood_rows: dict[str, dict[str, Any]], stream: str, field: str, default: Any = "n/a") -> Any:
    row = likelihood_rows.get(stream, {})
    return row.get(field, default)


def component_by_name(summary: dict[str, Any], component: str) -> dict[str, Any]:
    for row in summary.get("components", []):
        if row.get("component") == component:
            return row
    return {}


def add_row(
    rows: list[dict[str, str]],
    *,
    release_order: int,
    parameter_group: str,
    ogs_entry: str,
    base_definition: str,
    projection_or_run_definition: str,
    release_stage: str,
    recommendation: str,
    model_quantity_affected: str,
    measurement_evidence: str,
    identifiability_risk: str,
    activation_gate: str,
    source_files: str,
) -> None:
    rows.append(
        {
            "release_order": str(release_order),
            "parameter_group": parameter_group,
            "ogs_entry": ogs_entry,
            "base_definition": base_definition,
            "projection_or_run_definition": projection_or_run_definition,
            "release_stage": release_stage,
            "recommendation": recommendation,
            "model_quantity_affected": model_quantity_affected,
            "measurement_evidence": measurement_evidence,
            "identifiability_risk": identifiability_risk,
            "activation_gate": activation_gate,
            "source_files": source_files,
        }
    )


def build_rows(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    base_parameters = parse_parameters(args.base_parameters)
    projection_parameters = parse_parameters(args.projection_parameters)
    candidate_parameters = parse_parameters(args.candidate_parameters)
    media_properties = parse_properties(args.media)
    liquid_properties = parse_properties(args.liquid_media)
    twophase_properties = parse_properties(args.twophase_media)
    likelihood_summary = read_json(args.likelihood_summary)
    likelihood_rows = read_likelihood_rows(args.likelihood_csv)
    candidate_set = read_json(args.candidate_set_summary)
    current_combined = read_json(args.current_combined_summary)
    current_state = read_json(args.current_state_summary)
    next_field_gate = read_json(args.next_field_fit_gate)
    nmr_final_gate = read_json(args.nmr_final_policy_gate)
    external_blockers = read_json(args.external_blocker_dashboard)
    readiness = read_json(args.objective_readiness)
    thermal_audit = read_json(args.thermal_expansivity_audit)

    saturation = get_property(twophase_properties, "saturation", "SaturationVanGenuchten")
    relative_permeability = get_property(
        twophase_properties,
        "relative_permeability",
        "RelativePermeabilityVanGenuchten",
    )
    bishop = get_property(twophase_properties, "bishops_effective_stress", "BishopsPowerLaw")
    swelling = get_property(media_properties, "swelling_stress_rate", "SaturationDependentSwelling")
    liquid_density = get_property(liquid_properties, "density", "Linear")
    cte_ratio = thermal_audit.get("ratio_to_reference_high")
    cte_ratio_text = f"{float(cte_ratio):.3e}" if isinstance(cte_ratio, (int, float)) else "many"

    direct_rows = stream_stat(likelihood_rows, "permeability_pulse_tests", "current_objective_rows", 0)
    direct_candidates = stream_stat(likelihood_rows, "permeability_pulse_tests", "candidate_rows", 0)
    total_objective = current_combined.get(
        "total_active_objective_value",
        likelihood_summary.get("current_candidate_total_active_objective", "n/a"),
    )
    direct_component = component_by_name(current_combined, "direct_permeability_pulse_tests")
    state_component = component_by_name(current_combined, "state_observations")
    active_component_count = current_combined.get(
        "active_component_count",
        likelihood_summary.get("active_streams_now", "n/a"),
    )
    direct_objective = direct_component.get("objective_value", "n/a")
    state_objective = state_component.get("objective_value", "n/a")
    state_used_rows = state_component.get("used_rows", current_state.get("used_in_objective_rows", "n/a"))
    sampled_outputs = current_state.get("ogs_output_times", "n/a")
    nmr_policy_selected = nmr_final_gate.get("final_nmr_policy_selected")
    nmr_default_policy = nmr_final_gate.get("current_report_default_policy", "n/a")
    next_field_recommendation = next_field_gate.get("overall_recommendation", "n/a")
    same_support_executable = next_field_gate.get("executable_same_support_active_objective_batch_now")
    support_conflict_active = next_field_gate.get("support_conflict_spatial_active_support_cell_count", "n/a")
    support_conflict_repeated = next_field_gate.get("support_conflict_spatial_repeated_support_cell_count", "n/a")
    support_conflict_range2 = next_field_gate.get("support_conflict_spatial_range_ge_2_log10_cell_count", "n/a")
    open_blockers = external_blockers.get("open_blocker_count", "n/a")
    key_numbers = readiness.get("key_numbers", {})
    anisotropy_best = key_numbers.get("anisotropy_sensitivity_best_candidate", "n/a")
    anisotropy_delta = key_numbers.get("anisotropy_sensitivity_best_delta_vs_baseline", "n/a")
    local_anisotropy_best = key_numbers.get("local_anisotropy_sampler_best_candidate", "n/a")
    local_anisotropy_delta = key_numbers.get("local_anisotropy_sampler_best_delta_vs_baseline", "n/a")
    nmr_rows = stream_stat(likelihood_rows, "NMR weekly and seasonal water content", "candidate_rows", 0)
    ert_rows = stream_stat(likelihood_rows, "ERT open-niche resistivity field", "candidate_rows", 0)
    taupe_rows = stream_stat(likelihood_rows, "Taupe/TDR EDZ bands", "candidate_rows", 0)
    rh_rows = stream_stat(likelihood_rows, "suction/relative humidity", "candidate_rows", 0)

    common_xml_sources = "; ".join(
        [
            str(args.base_parameters),
            str(args.media),
            str(args.liquid_media),
            str(args.twophase_media),
        ]
    )
    projection_sources = "; ".join([str(args.projection_parameters), str(args.candidate_parameters)])

    rows: list[dict[str, str]] = []
    add_row(
        rows,
        release_order=1,
        parameter_group="intrinsic permeability tensor magnitude field",
        ogs_entry="medium property permeability -> parameter k_i / MeshElement field k_i_rd",
        base_definition=describe_parameter(base_parameters, "k_i"),
        projection_or_run_definition=(
            "projection: "
            + describe_parameter(projection_parameters, "k_i")
            + "; selected run: "
            + describe_parameter(candidate_parameters, "k_i")
        ),
        release_stage="stage_1_active_field",
        recommendation=(
            "Fit now as a run-local MeshElement tensor field. The current deterministic "
            "candidates multiply the existing four-component tensor by scalar cell factors, "
            "preserving tensor symmetry, orientation, and anisotropy ratio while changing magnitude."
        ),
        model_quantity_affected=(
            "Darcy mobility through intrinsic permeability K in v = -(k_rel K / mu) grad p; "
            "also controls saturation, theta, RH-response, ERT, Taupe/TDR, and HM state outputs after OGS runs."
        ),
        measurement_evidence=(
            f"Direct pulse-test likelihood is active with {direct_rows} objective rows from "
            f"{direct_candidates} candidate rows; the current active objective has {active_component_count} "
            f"components and totals {total_objective}, with direct objective {direct_objective} "
            f"plus sampled-state objective {state_objective}."
        ),
        identifiability_risk=(
            "Pulse tests are scalar interval-scale constraints on e^T K e, not full tensor observations. "
            "Gas/slip interpretation, 3D-to-2D support, and duplicate intervals remain explicit model-error terms."
        ),
        activation_gate="Already active for inside-mesh positive-k intervals; next gate is OGS-backed state-output plausibility.",
        source_files="; ".join([str(args.base_parameters), projection_sources, str(args.likelihood_csv)]),
    )
    add_row(
        rows,
        release_order=2,
        parameter_group="permeability tensor shape: anisotropy ratio, orientation, off-diagonal terms",
        ogs_entry="same k_i_rd tensor components k_xx k_xy k_yx k_yy",
        base_definition=describe_parameter(base_parameters, "k_i"),
        projection_or_run_definition=describe_parameter(candidate_parameters, "k_i"),
        release_stage="stage_2_candidate_tensor_shape",
        recommendation=(
            "Do not release tensor shape in the first fit. Keep the current bedding-parallel tensor geometry "
            "and test scalar magnitude fields first; release anisotropy ratio or orientation only after directional "
            "permeability/support evidence and OGS state diagnostics justify the extra degrees of freedom."
        ),
        model_quantity_affected="Directional Darcy response and lateral redistribution of pressure/saturation around the niche.",
        measurement_evidence=(
            "Bedding/geometry layers constrain orientation qualitatively; direct pulse-test residuals currently "
            "constrain only interval-projected directional permeability. The global anisotropy screen selected "
            f"{anisotropy_best} with direct delta {anisotropy_delta}, while the local tensor-anisotropy screen "
            f"best candidate {local_anisotropy_best} has direct delta {local_anisotropy_delta}; this is not "
            "enough to release tensor shape before support/likelihood and stream-gate decisions."
        ),
        identifiability_risk=(
            "A scalar interval value can be fit by many tensor combinations. Releasing angle and anisotropy too early "
            "would trade off against support mapping and local magnitude updates."
        ),
        activation_gate=(
            "Activate only after the direct support/likelihood policy is approved, repeated-support conflicts "
            "are resolved or explicitly retained, and OGS-backed state diagnostics show material benefit from "
            "tensor-shape degrees of freedom."
        ),
        source_files="; ".join([projection_sources, "inversion_workflow/processed_observations/borehole_line_mesh_samples.csv"]),
    )
    add_row(
        rows,
        release_order=3,
        parameter_group="porosity support field",
        ogs_entry="medium property porosity -> parameter phi / MeshElement field n_rd",
        base_definition=describe_parameter(base_parameters, "phi"),
        projection_or_run_definition=(
            "projection: "
            + describe_parameter(projection_parameters, "phi")
            + "; selected run: "
            + describe_parameter(candidate_parameters, "phi")
        ),
        release_stage="stage_1_fixed_support_field",
        recommendation=(
            "Keep fixed in the first permeability inversion. The projection machinery can read n_rd, "
            "but the current field is a fixed porosity support, not an active unknown."
        ),
        model_quantity_affected="Storage, theta = porosity * liquid_saturation, and effective thermal conductivity.",
        measurement_evidence=(
            f"NMR has {nmr_rows} candidate water-content rows; the current field samples {sampled_outputs} "
            f"OGS output times and uses {state_used_rows} NMR rows in the state objective.  The default "
            f"NMR policy remains {nmr_default_policy}, final policy selected={nmr_policy_selected}, so "
            "porosity is still support, not an active unknown."
        ),
        identifiability_risk=(
            "Porosity trades directly against saturation in theta observations and against permeability in hydraulic response. "
            "NMR measures hydrogen-bearing water, not only mobile free water in the Richards saturation variable."
        ),
        activation_gate=(
            "Release as scalar or field only after the final NMR residual policy is approved, ERT/Taupe "
            "uncertainty gates are closed or excluded, and a sensitivity audit separates porosity from "
            "saturation and bound/interlayer-water effects."
        ),
        source_files="; ".join([str(args.base_parameters), projection_sources, str(args.likelihood_csv)]),
    )
    add_row(
        rows,
        release_order=4,
        parameter_group="van Genuchten air-entry pressure",
        ogs_entry="property saturation / p_b",
        base_definition=format_property(saturation, ["p_b", "residual_liquid_saturation", "residual_gas_saturation", "exponent"]),
        projection_or_run_definition="fixed XML property in all prepared runs",
        release_stage="stage_2_candidate_scalar",
        recommendation=(
            "Treat as a later scalar retention parameter, not as an active first-stage unknown. "
            "It should be released only after RH boundary provenance and state-output sampling are settled."
        ),
        model_quantity_affected="Capillary pressure-saturation relation, storage derivative dS/dp_c, and liquid saturation state.",
        measurement_evidence=(
            f"RH/Kelvin table has {rh_rows} rows and NMR/ERT/Taupe provide theta diagnostics, but RH currently exposes "
            f"a boundary-curve provenance mismatch rather than a clean retention likelihood; {open_blockers} "
            "external/provenance blockers remain open."
        ),
        identifiability_risk="Strongly correlated with open-niche pressure boundary, permeability, exponent, residual saturation, and porosity.",
        activation_gate=(
            "Confirm or reconstruct 08_08_open_niche_seasonal.xml, select the NMR residual policy, and close "
            "or explicitly exclude ERT/Taupe/RH gates before fitting."
        ),
        source_files="; ".join([str(args.twophase_media), str(args.likelihood_csv)]),
    )
    add_row(
        rows,
        release_order=5,
        parameter_group="van Genuchten exponent",
        ogs_entry="properties saturation and relative_permeability / exponent",
        base_definition=(
            "saturation: "
            + format_property(saturation, ["exponent"])
            + "; relative_permeability: "
            + format_property(relative_permeability, ["exponent"])
        ),
        projection_or_run_definition="fixed XML property in all prepared runs",
        release_stage="stage_2_candidate_scalar",
        recommendation=(
            "Keep fixed in the first OGS comparison set. Consider a scalar release together with p_b only after "
            "retention-sensitive state residuals are active."
        ),
        model_quantity_affected="Shape of S(p_c) and k_rel(S), hence drying/wetting response around the open niche.",
        measurement_evidence=(
            "NMR, ERT, Taupe/TDR, and RH are retention-sensitive, but they are still gated by NMR policy, "
            "ERT support/uncertainty, Taupe absolute calibration, and RH boundary-curve provenance."
        ),
        identifiability_risk="The exponent is poorly separated from p_b and residual saturation without independent retention or suction data.",
        activation_gate="Release only as a paired retention calibration after the p_b, NMR-policy, and RH-provenance gates are satisfied.",
        source_files=str(args.twophase_media),
    )
    add_row(
        rows,
        release_order=6,
        parameter_group="residual saturations",
        ogs_entry="relative_permeability and saturation / residual_liquid_saturation, residual_gas_saturation",
        base_definition=(
            "saturation: "
            + format_property(saturation, ["residual_liquid_saturation", "residual_gas_saturation"])
            + "; relative_permeability: "
            + format_property(relative_permeability, ["residual_liquid_saturation", "residual_gas_saturation"])
        ),
        projection_or_run_definition="fixed XML property in all prepared runs",
        release_stage="stage_2_fixed_until_retention_data",
        recommendation=(
            "Keep fixed for current and near-term runs. Residual saturations should not be inferred from the present "
            "field data unless independent retention/hysteresis constraints are added."
        ),
        model_quantity_affected="Effective saturation, retention curve limits, and relative permeability endpoints.",
        measurement_evidence="No active observation currently isolates residual saturation.",
        identifiability_risk="Highly nonlinear and confounded with p_b, exponent, boundary pressure, NMR bound water, and sensor calibration.",
        activation_gate="Require dedicated retention information or a sensitivity study proving state residuals can distinguish residual saturation.",
        source_files=str(args.twophase_media),
    )
    add_row(
        rows,
        release_order=7,
        parameter_group="relative-permeability numerical floor",
        ogs_entry="relative_permeability / minimum_relative_permeability_liquid",
        base_definition=format_property(relative_permeability, ["minimum_relative_permeability_liquid"]),
        projection_or_run_definition="fixed XML property in all prepared runs",
        release_stage="fixed_numerical_control",
        recommendation="Keep fixed. Treat this as a numerical floor, not a physical calibration parameter.",
        model_quantity_affected="Minimum liquid mobility under very low liquid saturation.",
        measurement_evidence="Current experiment evidence does not constrain the numerical lower bound.",
        identifiability_risk="Changing it can alter solver behavior and dry-end mobility without clear observability.",
        activation_gate="Only revisit in a numerical robustness study if very dry cells appear in OGS outputs.",
        source_files=str(args.twophase_media),
    )
    add_row(
        rows,
        release_order=8,
        parameter_group="open-niche pressure boundary curve",
        ogs_entry="parameter open_niche_seasonal / pressure_scaling_factor / open_niche_seasonal_curve",
        base_definition=(
            "open_niche_seasonal: "
            + describe_parameter(base_parameters, "open_niche_seasonal")
            + "; pressure_scaling_factor: "
            + describe_parameter(base_parameters, "pressure_scaling_factor")
        ),
        projection_or_run_definition="same boundary parameter copied into prepared runs",
        release_stage="blocked_or_confirm_provenance",
        recommendation=(
            "Do not treat as an ordinary material parameter. Reconstruct the curve from RH/T data or obtain its "
            "preprocessing provenance before fitting or scaling it."
        ),
        model_quantity_affected="Dirichlet pressure boundary on the open niche; drives pressure and saturation transients.",
        measurement_evidence=(
            "RH audit compares RH-derived Kelvin pressures against the active OGS curve and finds a large mismatch "
            "over the overlapping time range."
        ),
        identifiability_risk="Boundary pressure can mimic permeability and retention changes, so fitting it blindly would contaminate material inference.",
        activation_gate="Confirm how 08_08_open_niche_seasonal.xml was generated; then decide whether to fit only a documented scaling/bias term.",
        source_files="; ".join([str(args.base_parameters), "ogs_settings/08_08_open_niche_seasonal.xml", str(args.likelihood_csv)]),
    )
    add_row(
        rows,
        release_order=9,
        parameter_group="orthotropic elasticity",
        ogs_entry="parameters E, G, nu / LinearElasticOrthotropic",
        base_definition=(
            "E: "
            + describe_parameter(base_parameters, "E")
            + "; G: "
            + describe_parameter(base_parameters, "G")
            + "; nu: "
            + describe_parameter(base_parameters, "nu")
        ),
        projection_or_run_definition="fixed XML parameters in all prepared permeability runs",
        release_stage="stage_3_candidate_mechanical",
        recommendation=(
            "Keep fixed for hydraulic calibration. Consider scalar or facies-level mechanical release only after "
            "numerical displacement/pressure outputs are compared with levelling, extensometer, piezometer, and scan data."
        ),
        model_quantity_affected="Stress-displacement response, pore-pressure coupling through volumetric strain, and swelling constraint.",
        measurement_evidence="Other HM monitoring is structured as qualitative/secondary validation; key Geoscope and laser-scan numeric exports are still missing.",
        identifiability_risk="The 2D model cannot uniquely explain full 3D deformation, crack, and scan observations; hydraulic changes can also alter pore-pressure-driven strain.",
        activation_gate="Locate numeric HM time series, sample displacement/pressure OGS outputs, then run sensitivity checks before release.",
        source_files="; ".join([str(args.base_parameters), "inversion_workflow/processed_observations/other_hm_monitoring.md"]),
    )
    add_row(
        rows,
        release_order=10,
        parameter_group="Biot coupling coefficient",
        ogs_entry="medium property biot_coefficient -> parameter biot",
        base_definition=describe_parameter(base_parameters, "biot"),
        projection_or_run_definition="fixed XML parameter in all prepared permeability runs",
        release_stage="stage_3_candidate_mechanical",
        recommendation="Keep fixed at 1.0 unless a dedicated poromechanical identifiability study supports release.",
        model_quantity_affected="Effective stress coupling and pressure-strain coupling in the TRM process.",
        measurement_evidence="No active numerical mechanical likelihood is available yet.",
        identifiability_risk="Biot trades against elasticity, storage, initial stress, pressure boundary, and saturation state.",
        activation_gate="Require active pressure/displacement residuals and mechanical calibration data before fitting.",
        source_files="; ".join([str(args.base_parameters), str(args.media)]),
    )
    add_row(
        rows,
        release_order=11,
        parameter_group="saturation-dependent swelling",
        ogs_entry="solid property swelling_stress_rate / SaturationDependentSwelling",
        base_definition=format_property(
            swelling,
            ["swelling_pressures", "exponents", "lower_saturation_limit", "upper_saturation_limit"],
        ),
        projection_or_run_definition="fixed XML property in all prepared permeability runs",
        release_stage="stage_3_validation_only",
        recommendation=(
            "Keep fixed and use as a mechanical plausibility check first. Releasing swelling parameters needs "
            "calibrated saturation/displacement evidence, not only hydraulic pulse-test misfit."
        ),
        model_quantity_affected="Moisture-induced stress/strain source term and mechanical response to wetting.",
        measurement_evidence="Levelling and qualitative HM evidence can screen implausible swelling response after OGS outputs exist.",
        identifiability_risk="Swelling is entangled with saturation, elasticity, boundary constraints, and 2D geometry simplifications.",
        activation_gate="Activate only after displacement outputs and numeric HM series support a mechanical likelihood.",
        source_files=str(args.media),
    )
    add_row(
        rows,
        release_order=12,
        parameter_group="thermal and liquid transport constants",
        ogs_entry="rho_s, kappa_th_s, c_p_s, c_p_l, kappa_l, eta, liquid density, thermal mixing",
        base_definition=(
            "rho_s: "
            + describe_parameter(base_parameters, "rho_s")
            + "; kappa_th_s: "
            + describe_parameter(base_parameters, "kappa_th_s")
            + "; c_p_s: "
            + describe_parameter(base_parameters, "c_p_s")
            + "; c_p_l: "
            + describe_parameter(base_parameters, "c_p_l")
            + "; kappa_l: "
            + describe_parameter(base_parameters, "kappa_l")
            + "; eta: "
            + describe_parameter(base_parameters, "eta")
            + "; liquid density: "
            + format_property(liquid_density, ["reference_value"])
        ),
        projection_or_run_definition="fixed XML parameters/properties in all prepared permeability runs",
        release_stage="fixed_for_current_experiment",
        recommendation=(
            "Keep fixed. The current measurement catalogue is hydraulic/water-content dominated and does not "
            "support fitting thermal constants or water viscosity/density law."
        ),
        model_quantity_affected="Heat storage/conduction, density/storage terms, and Darcy mobility through viscosity.",
        measurement_evidence="No thermal perturbation likelihood or viscosity/density-specific measurement stream is active.",
        identifiability_risk="Changes would be poorly observed and could compensate hydraulic parameters without physical support.",
        activation_gate="Revisit only if a real thermal experiment or temperature-gradient likelihood is added.",
        source_files=common_xml_sources,
    )
    add_row(
        rows,
        release_order=13,
        parameter_group="solid thermal expansivity",
        ogs_entry="solid property thermal_expansivity -> parameter CTE",
        base_definition=describe_parameter(base_parameters, "CTE"),
        projection_or_run_definition="fixed XML parameter in all prepared permeability runs",
        release_stage="blocked_or_confirm_value",
        recommendation=(
            "Confirm the XML value and units before any physical interpretation. The generated thermal-expansivity "
            "audit shows that CTE equals c_p_s in the base file, has a heat-capacity-like XML comment, and is "
            f"{cte_ratio_text} times the high end of the cited HE-D solid "
            "thermal-expansion range."
        ),
        model_quantity_affected="Thermal strain and thermal pressurization terms if temperature changes occur.",
        measurement_evidence="Current runs are near-isothermal; this is a model-provenance caveat rather than an active likelihood term.",
        identifiability_risk="If thermal gradients appear, the current value could dominate THM coupling nonphysically.",
        activation_gate=thermal_audit.get(
            "release_gate",
            "Ask Gesa/BGR whether CTE should be approximately 1e-5 1/K, a different value, or inactive.",
        ),
        source_files="; ".join(
            [str(args.base_parameters), str(args.media), str(args.thermal_expansivity_audit)]
        ),
    )
    add_row(
        rows,
        release_order=14,
        parameter_group="initial pressure and stress setup",
        ogs_entry="ic_pressure, ic_sigma0, bc_top_pressure, load_top",
        base_definition=(
            "ic_pressure: "
            + describe_parameter(base_parameters, "ic_pressure")
            + "; ic_sigma0: "
            + describe_parameter(base_parameters, "ic_sigma0")
            + "; bc_top_pressure: "
            + describe_parameter(base_parameters, "bc_top_pressure")
            + "; load_top: "
            + describe_parameter(base_parameters, "load_top")
        ),
        projection_or_run_definition="same setup copied into prepared runs; load_top and initial stress remain model-provenance checks",
        release_stage="fixed_model_setup_confirm_before_mechanics",
        recommendation=(
            "Keep fixed for permeability fitting. Treat initial pressure/stress expressions as provenance items to audit before "
            "any mechanical or pressure-boundary calibration."
        ),
        model_quantity_affected="Initial pore pressure, possible initial stress if activated, and top pressure/load boundary assumptions.",
        measurement_evidence="Pressure/deformation monitoring can eventually test the initialization, but those residuals are not active now.",
        identifiability_risk="Changing initial and boundary states can imitate permeability and storage effects over early times.",
        activation_gate="Audit active process-variable references and numeric HM/pressure data before release.",
        source_files="; ".join([str(args.base_parameters), "ogs_settings/01_processes_TRM.xml", "ogs_settings/02_process_variables_TRM.xml"]),
    )

    frame = pd.DataFrame(rows).sort_values("release_order", key=lambda col: col.astype(int)).reset_index(drop=True)
    stage_counts = Counter(frame["release_stage"])
    summary = {
        "parameter_release_rows": int(frame.shape[0]),
        "stage_counts": dict(sorted(stage_counts.items())),
        "active_field_parameters_now": [
            row["parameter_group"]
            for row in rows
            if row["release_stage"] == "stage_1_active_field"
        ],
        "fixed_first_stage_parameters": [
            row["parameter_group"]
            for row in rows
            if row["release_stage"]
            in {
                "stage_1_fixed_support_field",
                "stage_2_fixed_until_retention_data",
                "fixed_numerical_control",
                "fixed_for_current_experiment",
                "fixed_model_setup_confirm_before_mechanics",
            }
        ],
        "blocked_or_confirm_items": [
            row["parameter_group"]
            for row in rows
            if row["release_stage"].startswith("blocked_or_confirm")
        ],
        "stage_gate_summary": [
            "Stage 1 releases only k_i_rd magnitude fields against active direct permeability rows and sampled NMR state residuals.",
            "Porosity n_rd is field-capable but fixed until the final NMR residual policy and a porosity/saturation/bound-water separation audit are approved.",
            "Do not run more same-support active-objective OGS batches until support, likelihood, bounds, or stream gates change.",
            "Retention parameters require final NMR policy selection plus RH boundary-curve provenance before release.",
            "Mechanical, swelling, Biot, and initial-stress parameters require numeric HM/pressure residuals before release.",
            "CTE and open-niche pressure curve remain confirmation/provenance blockers, not calibration targets.",
        ],
        "current_evidence": {
            "active_released_parameter_groups": [
                "intrinsic permeability tensor magnitude field"
            ],
            "active_component_count": active_component_count,
            "total_active_objective_value": total_objective,
            "direct_permeability_objective_value": direct_objective,
            "direct_permeability_objective_rows": direct_rows,
            "state_observation_objective_value": state_objective,
            "state_observation_used_rows": state_used_rows,
            "sampled_ogs_output_times": sampled_outputs,
            "nmr_final_policy_selected": nmr_policy_selected,
            "nmr_current_report_default_policy": nmr_default_policy,
            "next_field_fit_recommendation": next_field_recommendation,
            "same_support_active_objective_batch_executable_now": same_support_executable,
            "support_conflict_cell_counts": {
                "active_support_cells": support_conflict_active,
                "repeated_support_cells": support_conflict_repeated,
                "range_ge_2_log10_cells": support_conflict_range2,
            },
            "open_external_or_provenance_blockers": open_blockers,
            "candidate_set_ogs_mode": candidate_set.get("ogs_mode"),
            "candidate_set_selected_candidate_count": candidate_set.get("selected_candidate_count"),
        },
        "measurement_context": {
            "likelihood_summary": likelihood_summary,
            "candidate_set_summary": {
                "selected_candidate_count": candidate_set.get("selected_candidate_count"),
                "ogs_mode": candidate_set.get("ogs_mode"),
                "results_csv": candidate_set.get("results_csv"),
            },
        },
        "source_files": {
            "base_parameters": str(args.base_parameters),
            "projection_parameters": str(args.projection_parameters),
            "candidate_parameters": str(args.candidate_parameters),
            "media": str(args.media),
            "liquid_media": str(args.liquid_media),
            "twophase_media": str(args.twophase_media),
            "likelihood_summary": str(args.likelihood_summary),
            "likelihood_csv": str(args.likelihood_csv),
            "candidate_set_summary": str(args.candidate_set_summary),
            "current_combined_summary": str(args.current_combined_summary),
            "current_state_summary": str(args.current_state_summary),
            "next_field_fit_gate": str(args.next_field_fit_gate),
            "nmr_final_policy_gate": str(args.nmr_final_policy_gate),
            "external_blocker_dashboard": str(args.external_blocker_dashboard),
            "objective_readiness": str(args.objective_readiness),
        },
    }
    return frame, summary


def write_markdown(path: Path, frame: pd.DataFrame, summary: dict[str, Any]) -> None:
    current = summary.get("current_evidence", {})
    conflicts = current.get("support_conflict_cell_counts", {})
    lines = [
        "# Inversion Parameter Release Plan",
        "",
        "This audit records which OGS parameters are allowed to vary in the current",
        "measurement-driven workflow and which ones must remain fixed until the",
        "corresponding observation operators, state outputs, or provenance checks exist.",
        "It is generated from the local OGS XML, the projection parameter files, the",
        "measurement likelihood model, and the regularized OGS candidate-set handoff.",
        "",
        "## Current Decision",
        "",
        "- Fit only the intrinsic permeability tensor magnitude field `k_i_rd` as the active released field in stage 1.",
        "- Use sampled NMR state residuals in the current active objective, but do not release porosity `n_rd` because the final NMR policy is unapproved and porosity, saturation, and bound/interlayer water remain non-identifiable.",
        "- Keep tensor shape, van Genuchten, relative-permeability, elastic, swelling, Biot, thermal, and initialization values fixed until their gates are approved.",
        "- Do not spend more same-support active-objective OGS batches until support, likelihood, bounds, or stream-gate evidence changes.",
        "- Treat the open-niche pressure curve and suspicious `CTE` value as provenance/confirmation blockers, not as ordinary fit parameters.",
        "",
        "## Current Evidence Snapshot",
        "",
        f"- Active objective components: `{current.get('active_component_count', 'n/a')}`.",
        f"- Current total active objective: `{current.get('total_active_objective_value', 'n/a')}`.",
        f"- Direct permeability objective: `{current.get('direct_permeability_objective_value', 'n/a')}` over `{current.get('direct_permeability_objective_rows', 'n/a')}` rows.",
        f"- Sampled-state objective: `{current.get('state_observation_objective_value', 'n/a')}` over `{current.get('state_observation_used_rows', 'n/a')}` NMR rows from `{current.get('sampled_ogs_output_times', 'n/a')}` OGS output times.",
        f"- NMR final policy selected: `{current.get('nmr_final_policy_selected', 'n/a')}`; current report policy: `{current.get('nmr_current_report_default_policy', 'n/a')}`.",
        f"- Same-support active-objective batch executable now: `{current.get('same_support_active_objective_batch_executable_now', 'n/a')}`; recommendation: `{current.get('next_field_fit_recommendation', 'n/a')}`.",
        f"- Support-conflict cells: active `{conflicts.get('active_support_cells', 'n/a')}`, repeated `{conflicts.get('repeated_support_cells', 'n/a')}`, range >=2 log10 `{conflicts.get('range_ge_2_log10_cells', 'n/a')}`.",
        f"- Open external/provenance blockers: `{current.get('open_external_or_provenance_blockers', 'n/a')}`.",
        f"- Candidate-set OGS mode: `{current.get('candidate_set_ogs_mode', 'n/a')}` with `{current.get('candidate_set_selected_candidate_count', 'n/a')}` selected candidates.",
        "",
        "## Stage Counts",
        "",
        "| Stage | Rows |",
        "| --- | ---: |",
    ]
    for stage, count in summary["stage_counts"].items():
        lines.append(f"| `{stage}` | {count} |")

    lines.extend(
        [
            "",
            "## Release Table",
            "",
            "| Order | Parameter group | OGS entry | Stage | Recommendation | Gate |",
            "| ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for _, row in frame.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["release_order"]),
                    row["parameter_group"],
                    f"`{row['ogs_entry']}`",
                    f"`{row['release_stage']}`",
                    row["recommendation"],
                    row["activation_gate"],
                ]
            )
            + " |"
        )

    lines.extend(["", "## Parameter Details", ""])
    for _, row in frame.iterrows():
        lines.extend(
            [
                f"### {row['release_order']}. {row['parameter_group']}",
                "",
                f"- OGS entry: `{row['ogs_entry']}`",
                f"- Base definition: `{row['base_definition']}`",
                f"- Projection/run definition: `{row['projection_or_run_definition']}`",
                f"- Release stage: `{row['release_stage']}`",
                f"- Model quantity affected: {row['model_quantity_affected']}",
                f"- Measurement evidence: {row['measurement_evidence']}",
                f"- Identifiability risk: {row['identifiability_risk']}",
                f"- Activation gate: {row['activation_gate']}",
                f"- Source files: `{row['source_files']}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Gate Checklist",
            "",
        ]
    )
    for item in summary["stage_gate_summary"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Practical Consequence",
            "",
            "The current inverse problem is not a free calibration of all XML constants.",
            "It is a staged workflow: first fit a heterogeneous anisotropic permeability",
            "field in `k_i_rd`; then use OGS state outputs to decide whether porosity,",
            "retention, boundary, or mechanical parameters are identifiable enough to release.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    frame, summary = build_rows(args)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output_csv, index=False)
    args.output_json.write_text(json.dumps(json_ready(summary), indent=2), encoding="utf-8")
    write_markdown(args.output_md, frame, summary)


if __name__ == "__main__":
    main()
