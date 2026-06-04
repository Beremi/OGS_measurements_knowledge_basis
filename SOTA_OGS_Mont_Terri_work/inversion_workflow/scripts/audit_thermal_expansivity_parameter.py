#!/usr/bin/env python3
"""Audit the suspicious OGS solid thermal-expansivity parameter."""

from __future__ import annotations

import argparse
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REFERENCE_EXPANSIVITY_RANGE_K_INV = (1.0e-5, 2.6e-5)
GENS2017_ADOPTED_EXPANSIVITY_K_INV = 1.4e-5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--parameters",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/03_parameters_TRM.xml"),
    )
    parser.add_argument(
        "--media",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/04_media_TRM.xml"),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("inversion_workflow/thermal_expansivity_parameter_audit.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/thermal_expansivity_parameter_audit_summary.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("inversion_workflow/thermal_expansivity_parameter_audit.md"),
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
    if value is None or value is pd.NA:
        return None
    return value


def parse_parameter_comments(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    comments: dict[str, str] = {}
    for block in re.findall(r"<parameter>(.*?)</parameter>", text, flags=re.DOTALL):
        name_match = re.search(r"<name>\s*([^<]+?)\s*</name>\s*(?:<!--(.*?)-->)?", block, flags=re.DOTALL)
        if not name_match:
            continue
        name = name_match.group(1).strip()
        comment = " ".join((name_match.group(2) or "").split())
        comments[name] = comment
    return comments


def read_parameters(path: Path) -> dict[str, dict[str, Any]]:
    root = ET.fromstring(f"<root>{path.read_text(encoding='utf-8')}</root>")
    comments = parse_parameter_comments(path)
    parameters: dict[str, dict[str, Any]] = {}
    for parameter in root.findall("parameter"):
        name = (parameter.findtext("name") or "").strip()
        if not name:
            continue
        parameter_type = (parameter.findtext("type") or "").strip()
        raw_value = (parameter.findtext("values") or parameter.findtext("value") or "").strip()
        values = [float(item) for item in raw_value.split()] if raw_value else []
        parameters[name] = {
            "name": name,
            "type": parameter_type,
            "raw_value": raw_value,
            "values": values,
            "first_value": values[0] if values else math.nan,
            "xml_comment": comments.get(name, ""),
        }
    return parameters


def media_property_bindings(path: Path) -> pd.DataFrame:
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    rows: list[dict[str, str]] = []
    media = [root] if root.tag == "medium" else root.findall(".//medium")
    for medium_index, medium in enumerate(media):
        for phase in medium.findall(".//phase"):
            phase_type = (phase.findtext("type") or "").strip()
            for prop in phase.findall(".//property"):
                name = (prop.findtext("name") or "").strip()
                prop_type = (prop.findtext("type") or "").strip()
                parameter_name = (prop.findtext("parameter_name") or "").strip()
                if name or parameter_name:
                    rows.append(
                        {
                            "medium_index": str(medium_index),
                            "phase": phase_type,
                            "property_name": name,
                            "property_type": prop_type,
                            "parameter_name": parameter_name,
                        }
                    )
    return pd.DataFrame(rows)


def build_audit(parameters_path: Path, media_path: Path) -> tuple[pd.DataFrame, dict[str, Any], str]:
    parameters = read_parameters(parameters_path)
    bindings = media_property_bindings(media_path)
    cte = parameters.get("CTE", {})
    cps = parameters.get("c_p_s", {})
    cte_value = float(cte.get("first_value", math.nan))
    cps_value = float(cps.get("first_value", math.nan))
    ref_min, ref_max = REFERENCE_EXPANSIVITY_RANGE_K_INV
    ratio_to_ref_max = cte_value / ref_max if finite(cte_value) else math.nan
    ratio_to_gens = cte_value / GENS2017_ADOPTED_EXPANSIVITY_K_INV if finite(cte_value) else math.nan
    cte_binding = bindings[bindings["parameter_name"].astype(str).eq("CTE")].copy()
    bound_property = "; ".join(
        f"{row.phase}:{row.property_name}:{row.property_type}" for _, row in cte_binding.iterrows()
    )
    likely_copy_from_cps = finite(cte_value) and finite(cps_value) and math.isclose(cte_value, cps_value)
    plausible = finite(cte_value) and ref_min <= cte_value <= ref_max
    rows = [
        {
            "audit_item": "solid thermal expansivity parameter",
            "xml_name": "CTE",
            "bound_ogs_property": bound_property,
            "xml_value": cte_value,
            "expected_unit_from_ogs_property": "1/K",
            "xml_comment": cte.get("xml_comment", ""),
            "reference_low_1_per_K": ref_min,
            "reference_high_1_per_K": ref_max,
            "reference_source": "Garitte2017 PDF p. 12; Gens2017 PDF p. 14",
            "ratio_to_reference_high": ratio_to_ref_max,
            "ratio_to_gens2017_adopted": ratio_to_gens,
            "equals_solid_specific_heat_capacity": likely_copy_from_cps,
            "plausibility_status": "implausible_by_units_and_magnitude" if not plausible else "within_reference_range",
            "release_gate": "blocked_confirm_value_with_Gesa_or_BGR",
        },
        {
            "audit_item": "solid specific heat capacity comparison",
            "xml_name": "c_p_s",
            "bound_ogs_property": "; ".join(
                f"{row.phase}:{row.property_name}:{row.property_type}"
                for _, row in bindings[bindings["parameter_name"].astype(str).eq("c_p_s")].iterrows()
            ),
            "xml_value": cps_value,
            "expected_unit_from_ogs_property": "J/(kg K)",
            "xml_comment": cps.get("xml_comment", ""),
            "reference_low_1_per_K": math.nan,
            "reference_high_1_per_K": math.nan,
            "reference_source": "XML comparison row only",
            "ratio_to_reference_high": math.nan,
            "ratio_to_gens2017_adopted": math.nan,
            "equals_solid_specific_heat_capacity": True,
            "plausibility_status": "plausible_as_heat_capacity_not_as_expansivity",
            "release_gate": "fixed_thermal_constant_not_fitted",
        },
    ]
    audit = pd.DataFrame(rows)
    summary = {
        "status": "blocked_confirm_cte_value",
        "parameters_file": str(parameters_path),
        "media_file": str(media_path),
        "cte_value": cte_value,
        "c_p_s_value": cps_value,
        "cte_xml_comment": cte.get("xml_comment", ""),
        "cte_bound_property": bound_property,
        "expected_ogs_unit": "1/K",
        "cte_equals_c_p_s": likely_copy_from_cps,
        "reference_expansivity_range_1_per_K": {
            "low": ref_min,
            "high": ref_max,
            "source": "Garitte2017 PDF p. 12 lists linear solid thermal expansion coefficients 1.0e-5 to 2.6e-5 1/K across HE-D modelling teams.",
        },
        "gens2017_adopted_expansivity_1_per_K": {
            "value": GENS2017_ADOPTED_EXPANSIVITY_K_INV,
            "source": "Gens2017 PDF p. 14 reports adopting 1.4e-5 1/K for Opalinus Clay thermal-loading analysis.",
        },
        "ratio_to_reference_high": ratio_to_ref_max,
        "ratio_to_gens2017_adopted": ratio_to_gens,
        "release_gate": "Do not release or physically interpret CTE until Gesa/BGR confirms whether the XML value should be near 1e-5 1/K, a different value, or inactive in the intended run.",
        "reason": (
            "The active XML binds CTE to solid thermal_expansivity, but the value equals c_p_s and the XML comment "
            "uses heat-capacity-like units. The magnitude is about 4.8e7 times the high end of the cited HE-D "
            "solid thermal-expansion range."
        ),
        "outputs": {
            "csv": "inversion_workflow/thermal_expansivity_parameter_audit.csv",
            "summary": "inversion_workflow/thermal_expansivity_parameter_audit_summary.json",
            "markdown": "inversion_workflow/thermal_expansivity_parameter_audit.md",
        },
    }
    markdown = write_markdown(summary, audit)
    return audit, summary, markdown


def write_markdown(summary: dict[str, Any], audit: pd.DataFrame) -> str:
    ref = summary["reference_expansivity_range_1_per_K"]
    gens = summary["gens2017_adopted_expansivity_1_per_K"]
    lines = [
        "# Thermal Expansivity Parameter Audit",
        "",
        "This audit isolates the suspicious `CTE` parameter in the recovered OGS model.",
        "",
        "## Current Finding",
        "",
        f"- Status: `{summary['status']}`",
        f"- XML parameter: `CTE = {summary['cte_value']}`",
        f"- Bound OGS property: `{summary['cte_bound_property']}`",
        f"- Expected unit from the OGS property role: `{summary['expected_ogs_unit']}`",
        f"- XML comment: `{summary['cte_xml_comment']}`",
        f"- Solid heat capacity in the same file: `c_p_s = {summary['c_p_s_value']}`",
        f"- `CTE` equals `c_p_s`: {summary['cte_equals_c_p_s']}",
        "",
        "The value is not plausible as a solid thermal expansivity.  It appears to be a copied heat-capacity number or a unit/provenance error, because the same numeric value is used for `c_p_s`.",
        "",
        "## Reference Scale",
        "",
        f"- Garitte et al. HE-D modelling table range: {ref['low']:.2e} to {ref['high']:.2e} 1/K.",
        f"- Gens et al. thermal-loading analysis adopted value: {gens['value']:.2e} 1/K.",
        f"- XML `CTE` / high end of HE-D range: {summary['ratio_to_reference_high']:.3e}.",
        f"- XML `CTE` / Gens et al. adopted value: {summary['ratio_to_gens2017_adopted']:.3e}.",
        "",
        "## Release Gate",
        "",
        summary["release_gate"],
        "",
        "## Audit Rows",
        "",
        "| Item | XML name | XML value | Expected unit | Plausibility | Gate |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for _, row in audit.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["audit_item"]),
                    f"`{row['xml_name']}`",
                    f"{float(row['xml_value']):.6g}" if finite(row["xml_value"]) else "",
                    str(row["expected_unit_from_ogs_property"]),
                    f"`{row['plausibility_status']}`",
                    f"`{row['release_gate']}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Source Basis",
            "",
            "- OGS binding: `04_media_TRM.xml` solid `thermal_expansivity` property points to `CTE`.",
            "- XML value/comment: `03_parameters_TRM.xml` defines `CTE = 1254.74` with a heat-capacity-like comment.",
            "- Literature scale: Garitte2017 PDF p. 12; Gens2017 PDF p. 14.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    audit, summary, markdown = build_audit(args.parameters, args.media)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(args.output_csv, index=False)
    args.summary_output.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    args.markdown_output.write_text(markdown, encoding="utf-8")
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.summary_output}")
    print(f"wrote {args.markdown_output}")
    print(f"status: {summary['status']}")


if __name__ == "__main__":
    main()
