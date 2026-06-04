#!/usr/bin/env python3
"""Check report formulation claims against the active OGS XML inputs."""

from __future__ import annotations

import argparse
import filecmp
import json
import math
import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path("ogs_settings"))
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run"),
        help="Representative run-local OGS directory used for active output/field substitutions.",
    )
    parser.add_argument(
        "--current-field-stats",
        type=Path,
        default=Path("inversion_workflow/current_permeability_field/current_best_field_stats.csv"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/ogs_formulation_consistency_audit.csv"),
    )
    parser.add_argument(
        "--inventory-output",
        type=Path,
        default=Path("inversion_workflow/ogs_formulation_xml_inventory.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/ogs_formulation_consistency_audit_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/ogs_formulation_consistency_audit.md"),
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("../cda_knowledge_base/measurements/model_formulation_audit"),
    )
    return parser.parse_args()


def resolve(repo: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo / path


def parse_fragment(path: Path) -> ET.Element:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return ET.fromstring(f"<root>{text}</root>")


def child_text(element: ET.Element | None, name: str, default: str = "") -> str:
    if element is None:
        return default
    child = element.find(name)
    if child is None or child.text is None:
        return default
    return child.text.strip()


def find_first(root: ET.Element, path: str) -> ET.Element | None:
    return root.find(path)


def all_texts(root: ET.Element, path: str) -> list[str]:
    return [item.text.strip() for item in root.findall(path) if item.text and item.text.strip()]


def parameter_map(root: ET.Element) -> dict[str, dict[str, Any]]:
    params: dict[str, dict[str, Any]] = {}
    for parameter in root.findall("parameter"):
        name = child_text(parameter, "name")
        if not name:
            continue
        expressions = all_texts(parameter, "expression")
        params[name] = {
            "type": child_text(parameter, "type"),
            "value": child_text(parameter, "value"),
            "values": child_text(parameter, "values"),
            "field_name": child_text(parameter, "field_name"),
            "curve": child_text(parameter, "curve"),
            "parameter": child_text(parameter, "parameter"),
            "expression": "; ".join(expressions),
        }
    return params


def process_variable_map(root: ET.Element) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for variable in root.findall("process_variable"):
        name = child_text(variable, "name")
        bcs = []
        for bc in variable.findall("./boundary_conditions/boundary_condition"):
            bcs.append(
                {
                    "mesh": child_text(bc, "mesh"),
                    "type": child_text(bc, "type"),
                    "component": child_text(bc, "component"),
                    "parameter": child_text(bc, "parameter"),
                }
            )
        result[name] = {
            "components": child_text(variable, "components"),
            "order": child_text(variable, "order"),
            "initial_condition": child_text(variable, "initial_condition"),
            "boundary_conditions": bcs,
        }
    return result


def property_details(prop: ET.Element) -> dict[str, Any]:
    return {
        "type": child_text(prop, "type"),
        "parameter_name": child_text(prop, "parameter_name"),
        "residual_liquid_saturation": child_text(prop, "residual_liquid_saturation"),
        "residual_gas_saturation": child_text(prop, "residual_gas_saturation"),
        "exponent": child_text(prop, "exponent"),
        "minimum_relative_permeability_liquid": child_text(prop, "minimum_relative_permeability_liquid"),
        "p_b": child_text(prop, "p_b"),
        "reference_value": child_text(prop, "reference_value"),
    }


def direct_property_map(parent: ET.Element | None) -> dict[str, dict[str, Any]]:
    properties: dict[str, dict[str, Any]] = {}
    if parent is None:
        return properties
    for prop in parent.findall("property"):
        name = child_text(prop, "name")
        if not name:
            continue
        properties[name] = property_details(prop)
    return properties


def medium_property_map(root: ET.Element) -> dict[str, dict[str, Any]]:
    medium = root.find("medium")
    return direct_property_map(medium.find("properties") if medium is not None else None)


def phase_property_map(root: ET.Element) -> dict[str, dict[str, dict[str, Any]]]:
    phases: dict[str, dict[str, dict[str, Any]]] = {}
    for phase in root.findall("./medium/phases/phase"):
        phase_type = child_text(phase, "type", "unknown")
        phases[phase_type] = direct_property_map(phase.find("properties"))
    return phases


def phase_fragment_property_map(root: ET.Element) -> dict[str, dict[str, Any]]:
    phase = root.find("phase")
    return direct_property_map(phase.find("properties") if phase is not None else None)


def direct_root_property_map(root: ET.Element) -> dict[str, dict[str, Any]]:
    return direct_property_map(root)


def density_linear_details(aqueous_root: ET.Element) -> dict[str, Any]:
    density = None
    for prop in aqueous_root.findall(".//property"):
        if child_text(prop, "name") == "density":
            density = prop
            break
    if density is None:
        return {}
    independent = {}
    for item in density.findall("independent_variable"):
        variable = child_text(item, "variable_name")
        independent[variable] = {
            "reference_condition": child_text(item, "reference_condition"),
            "slope": child_text(item, "slope"),
        }
    return {
        "type": child_text(density, "type"),
        "reference_value": child_text(density, "reference_value"),
        "independent_variables": independent,
    }


def numeric_equal(text: str, expected: float, *, rtol: float = 1.0e-12, atol: float = 1.0e-12) -> bool:
    try:
        return bool(math.isclose(float(text), expected, rel_tol=rtol, abs_tol=atol))
    except (TypeError, ValueError):
        return False


def numeric_list(text: str) -> list[float]:
    values: list[float] = []
    for token in str(text).replace(",", " ").split():
        try:
            values.append(float(token))
        except ValueError:
            continue
    return values


def add_check(
    rows: list[dict[str, Any]],
    *,
    check_id: str,
    category: str,
    status: str,
    report_claim: str,
    xml_evidence: str,
    implication: str,
    source_files: str,
) -> None:
    rows.append(
        {
            "check_id": check_id,
            "category": category,
            "status": status,
            "report_claim": report_claim,
            "xml_evidence": xml_evidence,
            "implication": implication,
            "source_files": source_files,
        }
    )


def status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return dict(sorted(counts.items()))


def read_stats(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    frame = pd.read_csv(path)
    if "metric" not in frame.columns:
        return {}
    return {str(row["metric"]): row.to_dict() for _, row in frame.iterrows()}


def file_same(left: Path, right: Path) -> bool:
    return left.exists() and right.exists() and filecmp.cmp(left, right, shallow=False)


def build_inventory(
    *,
    process: ET.Element,
    process_variables: dict[str, dict[str, Any]],
    source_params: dict[str, dict[str, Any]],
    run_params: dict[str, dict[str, Any]],
    medium_props: dict[str, dict[str, Any]],
    phase_props: dict[str, dict[str, dict[str, Any]]],
    twophase_props: dict[str, dict[str, Any]],
    aqueous_props: dict[str, dict[str, Any]],
    source_output_variables: list[str],
    run_output_variables: list[str],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    rows.append({"item_type": "process", "name": child_text(process, "name"), "type": child_text(process, "type"), "value": ""})
    rows.append(
        {
            "item_type": "process",
            "name": "specific_body_force",
            "type": "vector",
            "value": child_text(process, "specific_body_force"),
        }
    )
    for name, details in process_variables.items():
        rows.append(
            {
                "item_type": "process_variable",
                "name": name,
                "type": f"components={details['components']}; order={details['order']}",
                "value": f"ic={details['initial_condition']}; bcs={len(details['boundary_conditions'])}",
            }
        )
    for source, props in [("medium", medium_props), ("twophase", twophase_props), ("aqueous", aqueous_props)]:
        for name, details in sorted(props.items()):
            rows.append(
                {
                    "item_type": f"{source}_property",
                    "name": name,
                    "type": details.get("type", ""),
                    "value": details.get("parameter_name", "")
                    or details.get("exponent", "")
                    or details.get("reference_value", ""),
                }
            )
    for phase_name, props in sorted(phase_props.items()):
        for name, details in sorted(props.items()):
            rows.append(
                {
                    "item_type": "phase_property",
                    "name": f"{phase_name}.{name}",
                    "type": details.get("type", ""),
                    "value": details.get("parameter_name", "")
                    or details.get("exponent", "")
                    or details.get("reference_value", ""),
                }
            )
    for source, params in [("source_parameter", source_params), ("run_parameter", run_params)]:
        for name, details in sorted(params.items()):
            rows.append(
                {
                    "item_type": source,
                    "name": name,
                    "type": details.get("type", ""),
                    "value": details.get("field_name") or details.get("values") or details.get("value") or details.get("curve") or details.get("expression"),
                }
            )
    rows.append({"item_type": "source_output", "name": "variables", "type": "VTK", "value": ";".join(source_output_variables)})
    rows.append({"item_type": "run_output", "name": "variables", "type": "VTK", "value": ";".join(run_output_variables)})
    return pd.DataFrame(rows)


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return None if not np.isfinite(number) else number
    if value is None or value is pd.NA:
        return None
    return value


def copy_outputs(paths: list[Path], catalogue_dir: Path, repo: Path) -> list[dict[str, str]]:
    derived = catalogue_dir / "derived_files"
    derived.mkdir(parents=True, exist_ok=True)
    copies: list[dict[str, str]] = []
    for source in paths:
        if not source.exists():
            continue
        target = derived / source.name
        shutil.copy2(source, target)
        copies.append(
            {
                "source": os.path.relpath(source.resolve(), repo),
                "catalogue_copy": os.path.relpath(target.resolve(), repo),
            }
        )
    return copies


def write_markdown(path: Path, checks: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# OGS Formulation Consistency Audit",
        "",
        "This audit checks the report's formulation statements against the active source XML and the representative run-local XML used by the workflow.",
        "",
        "## Summary",
        "",
        f"- Status: `{summary['status']}`",
        f"- Check count: {summary['check_count']}",
        f"- Pass count: {summary['pass_count']}",
        f"- Tracked caveat count: {summary['tracked_caveat_count']}",
        f"- Fail count: {summary['fail_count']}",
        f"- Source process type: `{summary['process_type']}`",
        f"- Primary variables: {', '.join(summary['primary_variables'])}",
        f"- Run-local output variables: {', '.join(summary['run_output_variables'])}",
        f"- Run-local optimized/field parameters: {summary['run_local_field_parameters']}",
        "",
        "## Checks",
        "",
        "| Check | Status | XML evidence | Implication |",
        "| --- | --- | --- | --- |",
    ]
    for _, row in checks.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['check_id']}`",
                    f"`{row['status']}`",
                    str(row["xml_evidence"]).replace("|", "\\|"),
                    str(row["implication"]).replace("|", "\\|"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The exchanged source XML is a THERMO_RICHARDS_MECHANICS model with displacement, pressure, and temperature as primary variables; gravity is disabled.",
            "- The active run-local workflow changes parameter representation for permeability and porosity to mesh-element fields, while preserving the OGS process, phase laws, boundary-condition structure, and constitutive relation semantics.",
            "- The permeability field is the actual heterogeneous tensor field used for fitting; the porosity mesh field is fixed support in the current field package (`n_rd` is spatially constant at 0.105).",
            "- The CTE value remains a tracked provenance caveat, not a formulation blocker and not a released fit parameter.",
            "",
            "## Source Artifacts",
            "",
        ]
    )
    for artifact in summary["source_artifacts"]:
        lines.append(f"- `{artifact}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo = Path.cwd()
    source_dir = resolve(repo, args.source_dir).resolve()
    run_dir = resolve(repo, args.run_dir).resolve()
    stats_path = resolve(repo, args.current_field_stats).resolve()
    output_csv = resolve(repo, args.output_csv).resolve()
    inventory_output = resolve(repo, args.inventory_output).resolve()
    summary_output = resolve(repo, args.summary_output).resolve()
    markdown_output = resolve(repo, args.markdown_output).resolve()
    catalogue_dir = resolve(repo, args.catalogue_dir).resolve()

    source_process_root = parse_fragment(source_dir / "01_processes_TRM.xml")
    source_process_variables_root = parse_fragment(source_dir / "02_process_variables_TRM.xml")
    source_params_root = parse_fragment(source_dir / "03_parameters_TRM.xml")
    source_media_root = parse_fragment(source_dir / "04_media_TRM.xml")
    source_aqueous_root = parse_fragment(source_dir / "04_1_media_aqu_liq.xml")
    source_twophase_root = parse_fragment(source_dir / "04_2_media_twophase.xml")
    source_time_root = parse_fragment(source_dir / "05_time_loop_TRM.xml")
    run_params_root = parse_fragment(run_dir / "03_parameters_TRM.xml")
    run_time_root = parse_fragment(run_dir / "05_time_loop_TRM.xml")

    process = find_first(source_process_root, "process")
    if process is None:
        raise ValueError("source process XML does not contain <process>")
    process_variables = process_variable_map(source_process_variables_root)
    source_params = parameter_map(source_params_root)
    run_params = parameter_map(run_params_root)
    medium_props = medium_property_map(source_media_root)
    phase_props = phase_property_map(source_media_root)
    aqueous_props = phase_fragment_property_map(source_aqueous_root)
    twophase_props = direct_root_property_map(source_twophase_root)
    density = density_linear_details(source_aqueous_root)
    source_output_variables = all_texts(source_time_root, ".//output/variables/variable")
    run_output_variables = all_texts(run_time_root, ".//output/variables/variable")
    stats = read_stats(stats_path)

    rows: list[dict[str, Any]] = []
    process_type = child_text(process, "type")
    primary_variables = [
        child_text(find_first(process, "process_variables"), name)
        for name in ["displacement", "pressure", "temperature"]
    ]
    add_check(
        rows,
        check_id="process_type_and_primary_variables",
        category="process",
        status="pass"
        if process_type == "THERMO_RICHARDS_MECHANICS"
        and primary_variables == ["displacement", "pressure", "temperature"]
        else "fail",
        report_claim="The model is an OGS TRM model with displacement, liquid pressure, and temperature as primary variables.",
        xml_evidence=f"type={process_type}; variables={primary_variables}",
        implication="The report's primary variable list matches the process XML.",
        source_files="ogs_settings/01_processes_TRM.xml",
    )
    add_check(
        rows,
        check_id="gravity_specific_body_force_off",
        category="process",
        status="pass" if numeric_list(child_text(process, "specific_body_force")) == [0.0, 0.0] else "fail",
        report_claim="Gravity/body force is disabled, so Darcy velocity has no rho*g term.",
        xml_evidence=f"specific_body_force={child_text(process, 'specific_body_force')}",
        implication="The no-gravity Darcy expression in the report is consistent with the XML.",
        source_files="ogs_settings/01_processes_TRM.xml",
    )
    add_check(
        rows,
        check_id="process_variable_orders_and_bcs",
        category="process_variables",
        status="pass"
        if process_variables.get("displacement", {}).get("components") == "2"
        and process_variables.get("displacement", {}).get("order") == "2"
        and process_variables.get("pressure", {}).get("order") == "1"
        and process_variables.get("temperature", {}).get("order") == "1"
        else "fail",
        report_claim="Displacement is a 2-component second-order variable; pressure and temperature are first-order scalar variables.",
        xml_evidence=(
            f"displacement={process_variables.get('displacement')}; "
            f"pressure={process_variables.get('pressure')}; temperature={process_variables.get('temperature')}"
        ),
        implication="The active finite-element variable orders and boundary-condition assignment are traceable.",
        source_files="ogs_settings/02_process_variables_TRM.xml",
    )
    density_ok = (
        density.get("type") == "Linear"
        and density.get("reference_value") == "1095"
        and density.get("independent_variables", {}).get("temperature", {}).get("slope") == "-5E-4"
        and density.get("independent_variables", {}).get("liquid_phase_pressure", {}).get("slope") == "3.2e-10"
    )
    add_check(
        rows,
        check_id="liquid_density_linear_temperature_pressure",
        category="aqueous_phase",
        status="pass" if density_ok else "fail",
        report_claim="Liquid density is a linear temperature- and pressure-dependent law, not a constant.",
        xml_evidence=json.dumps(density, sort_keys=True),
        implication="The report's storage and thermal-coupling discussion should retain density derivatives.",
        source_files="ogs_settings/04_1_media_aqu_liq.xml",
    )
    active_vapor_names = {
        name
        for name in aqueous_props
        if "vapour" in name.lower() or "vapor" in name.lower() or name == "latent_heat"
    }
    add_check(
        rows,
        check_id="vapor_terms_absent_from_active_phase",
        category="aqueous_phase",
        status="pass" if not active_vapor_names else "fail",
        report_claim="The active OGS TRM model is the no-vapor formulation.",
        xml_evidence=f"active vapor-like properties={sorted(active_vapor_names)}",
        implication="Vapor-density, vapor-diffusion, and latent-heat terms must not be included as active equations.",
        source_files="ogs_settings/04_1_media_aqu_liq.xml",
    )
    relperm = twophase_props.get("relative_permeability", {})
    saturation = twophase_props.get("saturation", {})
    add_check(
        rows,
        check_id="relative_permeability_van_genuchten",
        category="twophase",
        status="pass"
        if relperm.get("type") == "RelativePermeabilityVanGenuchten"
        and relperm.get("residual_liquid_saturation") == "0.1"
        and relperm.get("residual_gas_saturation") == "0"
        and relperm.get("exponent") == "0.45"
        and relperm.get("minimum_relative_permeability_liquid") == "1e-25"
        else "fail",
        report_claim="Relative permeability is fixed Van Genuchten with S_lr=0.1, S_gr=0, m=0.45, and k_rel_min=1e-25.",
        xml_evidence=str(relperm),
        implication="The permeability fitting should alter intrinsic permeability, not the relative-permeability function.",
        source_files="ogs_settings/04_2_media_twophase.xml",
    )
    add_check(
        rows,
        check_id="saturation_van_genuchten_retention",
        category="twophase",
        status="pass"
        if saturation.get("type") == "SaturationVanGenuchten"
        and saturation.get("p_b") == "10e6"
        and saturation.get("exponent") == "0.45"
        else "fail",
        report_claim="Retention/saturation is fixed Van Genuchten in the current permeability-focused workflow.",
        xml_evidence=str(saturation),
        implication="Retention parameters should stay gated unless an explicit release decision is recorded.",
        source_files="ogs_settings/04_2_media_twophase.xml",
    )
    bishop = twophase_props.get("bishops_effective_stress", {})
    add_check(
        rows,
        check_id="bishop_power_law_saturation",
        category="mechanics",
        status="pass" if bishop.get("type") == "BishopsPowerLaw" and bishop.get("exponent") == "1" else "fail",
        report_claim="Bishop coefficient is saturation to power one.",
        xml_evidence=str(bishop),
        implication="The compact pore-stress term b(S) alpha p I becomes S p I only after XML substitutions.",
        source_files="ogs_settings/04_2_media_twophase.xml",
    )
    add_check(
        rows,
        check_id="linear_elastic_orthotropic",
        category="mechanics",
        status="pass"
        if all(
            child_text(relation, "type") == "LinearElasticOrthotropic"
            for relation in process.findall("constitutive_relation")
        )
        else "fail",
        report_claim="The solid relation is orthotropic linear elasticity, not isotropic elasticity.",
        xml_evidence=f"constitutive_relation_types={[child_text(r, 'type') for r in process.findall('constitutive_relation')]}",
        implication="Report equations should keep the generalized Hooke-law representation.",
        source_files="ogs_settings/01_processes_TRM.xml; ogs_settings/03_parameters_TRM.xml",
    )
    add_check(
        rows,
        check_id="swelling_stress_active",
        category="mechanics",
        status="pass"
        if phase_props.get("Solid", {}).get("swelling_stress_rate", {}).get("type") == "SaturationDependentSwelling"
        else "fail",
        report_claim="Saturation-dependent swelling strain/stress is active.",
        xml_evidence=str(phase_props.get("Solid", {}).get("swelling_stress_rate", {})),
        implication="The mechanical equation should not be presented as purely thermoelastic.",
        source_files="ogs_settings/04_media_TRM.xml",
    )
    add_check(
        rows,
        check_id="thermal_conductivity_effective_porosity_mixing",
        category="thermal",
        status="pass"
        if medium_props.get("thermal_conductivity", {}).get("type") == "EffectiveThermalConductivityPorosityMixing"
        else "fail",
        report_claim="Thermal conductivity uses OGS effective porosity mixing.",
        xml_evidence=str(medium_props.get("thermal_conductivity", {})),
        implication="The heat-balance section should keep porosity/saturation in effective storage and conduction.",
        source_files="ogs_settings/04_media_TRM.xml",
    )
    add_check(
        rows,
        check_id="biot_coefficient_one",
        category="mechanics",
        status="pass"
        if medium_props.get("biot_coefficient", {}).get("parameter_name") == "biot"
        and source_params.get("biot", {}).get("values") == "1"
        else "fail",
        report_claim="Biot coefficient is fixed to one.",
        xml_evidence=f"media={medium_props.get('biot_coefficient')}; parameter={source_params.get('biot')}",
        implication="The report's alpha_B=1 substitution is valid for this model.",
        source_files="ogs_settings/04_media_TRM.xml; ogs_settings/03_parameters_TRM.xml",
    )
    source_k = source_params.get("k_i", {})
    run_k = run_params.get("k_i", {})
    add_check(
        rows,
        check_id="intrinsic_permeability_source_constant_run_mesh_field",
        category="run_local_parameterization",
        status="pass"
        if source_k.get("type") == "Constant" and run_k.get("type") == "MeshElement" and run_k.get("field_name") == "k_i_rd"
        else "fail",
        report_claim="The source model has constant intrinsic permeability; the inversion workflow supplies run-local heterogeneous tensor fields through k_i_rd.",
        xml_evidence=f"source k_i={source_k}; run k_i={run_k}",
        implication="This is a parameter-field substitution, not a change to the OGS process equations.",
        source_files="ogs_settings/03_parameters_TRM.xml; inversion_workflow/runs/direct_fit_observation_run/03_parameters_TRM.xml",
    )
    source_phi = source_params.get("phi", {})
    run_phi = run_params.get("phi", {})
    n_stats = stats.get("n_rd", {})
    n_constant = bool(n_stats) and numeric_equal(str(n_stats.get("std", "")), 0.0) and numeric_equal(
        str(n_stats.get("min", "")),
        0.105,
    ) and numeric_equal(str(n_stats.get("max", "")), 0.105)
    add_check(
        rows,
        check_id="porosity_run_mesh_field_fixed_support",
        category="run_local_parameterization",
        status="pass_with_caveat"
        if source_phi.get("type") == "Constant"
        and run_phi.get("type") == "MeshElement"
        and run_phi.get("field_name") == "n_rd"
        and n_constant
        else "fail",
        report_claim="Porosity is not an active fitted heterogeneous field; any run-local mesh representation is fixed support.",
        xml_evidence=f"source phi={source_phi}; run phi={run_phi}; n_rd stats={n_stats}",
        implication="Report wording should distinguish mesh-element representation from released/optimized porosity.",
        source_files="ogs_settings/03_parameters_TRM.xml; inversion_workflow/runs/direct_fit_observation_run/03_parameters_TRM.xml; inversion_workflow/current_permeability_field/current_best_field_stats.csv",
    )
    cte = source_params.get("CTE", {})
    cps = source_params.get("c_p_s", {})
    add_check(
        rows,
        check_id="cte_value_tracked_provenance_caveat",
        category="thermal",
        status="tracked_caveat" if cte.get("values") == cps.get("values") and cte.get("values") else "pass",
        report_claim="The active CTE value is suspicious and should remain a provenance caveat rather than a release parameter.",
        xml_evidence=f"CTE={cte}; c_p_s={cps}",
        implication="The report should not infer a physically accepted thermal-expansivity calibration from this XML value.",
        source_files="ogs_settings/03_parameters_TRM.xml",
    )
    output_required = {"pressure", "saturation", "temperature", "displacement", "porosity"}
    add_check(
        rows,
        check_id="run_local_output_variables_for_observation_operators",
        category="run_local_output",
        status="pass" if output_required.issubset(set(run_output_variables)) else "fail",
        report_claim="Run-local OGS output exposes pressure, saturation, temperature, displacement, and porosity for measurement operators.",
        xml_evidence=f"source output variables={source_output_variables}; run output variables={run_output_variables}",
        implication="State, ERT, Taupe/TDR, and NMR operators can sample the needed run-local VTU quantities.",
        source_files="ogs_settings/05_time_loop_TRM.xml; inversion_workflow/runs/direct_fit_observation_run/05_time_loop_TRM.xml",
    )
    unchanged_files = [
        "01_processes_TRM.xml",
        "02_process_variables_TRM.xml",
        "04_media_TRM.xml",
        "04_1_media_aqu_liq.xml",
        "04_2_media_twophase.xml",
    ]
    changed = [name for name in unchanged_files if not file_same(source_dir / name, run_dir / name)]
    add_check(
        rows,
        check_id="run_local_process_and_media_semantics_unchanged",
        category="non_modification_constraint",
        status="pass" if not changed else "fail",
        report_claim="The run-local workflow preserves the OGS process, process-variable, media, and phase-law semantics.",
        xml_evidence=f"changed core XML files={changed}",
        implication="The workflow changes field values and output selection, not the governing process definition.",
        source_files="ogs_settings/; inversion_workflow/runs/direct_fit_observation_run/",
    )
    active_bc_params = sorted(
        {
            bc["parameter"]
            for details in process_variables.values()
            for bc in details["boundary_conditions"]
            if bc.get("parameter")
        }
    )
    add_check(
        rows,
        check_id="active_boundary_conditions_and_inactive_defined_parameters",
        category="boundary_conditions",
        status="pass"
        if set(active_bc_params) == {"bc_displacement", "bc_temperature_outside", "bc_top_pressure", "open_niche_seasonal"}
        else "fail",
        report_claim="Pressure BCs are top pressure plus open-niche seasonal pressure; outside pressure/load/initial stress are defined but inactive.",
        xml_evidence=f"active BC parameters={active_bc_params}; defined inactive examples=bc_pressure_outside, load_top, ic_sigma0",
        implication="Inactive XML parameters should not be described as active forcing terms.",
        source_files="ogs_settings/02_process_variables_TRM.xml; ogs_settings/03_parameters_TRM.xml",
    )

    checks = pd.DataFrame(rows)
    inventory = build_inventory(
        process=process,
        process_variables=process_variables,
        source_params=source_params,
        run_params=run_params,
        medium_props=medium_props,
        phase_props=phase_props,
        twophase_props=twophase_props,
        aqueous_props=aqueous_props,
        source_output_variables=source_output_variables,
        run_output_variables=run_output_variables,
    )
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    checks.to_csv(output_csv, index=False)
    inventory.to_csv(inventory_output, index=False)

    counts = status_counts(rows)
    fail_count = int(counts.get("fail", 0))
    summary: dict[str, Any] = {
        "status": "ogs_formulation_consistency_audit_generated",
        "check_count": int(checks.shape[0]),
        "status_counts": counts,
        "pass_count": int(counts.get("pass", 0) + counts.get("pass_with_caveat", 0)),
        "tracked_caveat_count": int(counts.get("tracked_caveat", 0) + counts.get("pass_with_caveat", 0)),
        "fail_count": fail_count,
        "all_hard_checks_pass": fail_count == 0,
        "process_type": process_type,
        "primary_variables": primary_variables,
        "specific_body_force": child_text(process, "specific_body_force"),
        "source_output_variables": source_output_variables,
        "run_output_variables": run_output_variables,
        "run_local_field_parameters": {
            name: details.get("field_name")
            for name, details in run_params.items()
            if details.get("type") == "MeshElement"
        },
        "source_artifacts": [
            "ogs_settings/01_processes_TRM.xml",
            "ogs_settings/02_process_variables_TRM.xml",
            "ogs_settings/03_parameters_TRM.xml",
            "ogs_settings/04_media_TRM.xml",
            "ogs_settings/04_1_media_aqu_liq.xml",
            "ogs_settings/04_2_media_twophase.xml",
            "ogs_settings/05_time_loop_TRM.xml",
            "inversion_workflow/runs/direct_fit_observation_run/03_parameters_TRM.xml",
            "inversion_workflow/runs/direct_fit_observation_run/05_time_loop_TRM.xml",
            "inversion_workflow/current_permeability_field/current_best_field_stats.csv",
        ],
        "outputs": {
            "checks_csv": os.path.relpath(output_csv, repo),
            "inventory_csv": os.path.relpath(inventory_output, repo),
            "summary_json": os.path.relpath(summary_output, repo),
            "markdown": os.path.relpath(markdown_output, repo),
        },
        "notes": [
            "Hard checks compare active XML elements, not commented-out alternatives.",
            "The representative run-local directory may change parameter representation and output selection while preserving process/media semantics.",
        ],
    }
    summary_output.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(markdown_output, checks, summary)
    summary["catalogue_copies"] = copy_outputs([output_csv, inventory_output, summary_output, markdown_output], catalogue_dir, repo)
    summary_output.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(markdown_output, checks, summary)
    copy_outputs([summary_output, markdown_output], catalogue_dir, repo)

    print(f"checks: {checks.shape[0]}")
    print(f"hard failures: {fail_count}")
    print(f"wrote {output_csv}")
    print(f"wrote {inventory_output}")
    print(f"wrote {summary_output}")
    print(f"wrote {markdown_output}")


if __name__ == "__main__":
    main()
