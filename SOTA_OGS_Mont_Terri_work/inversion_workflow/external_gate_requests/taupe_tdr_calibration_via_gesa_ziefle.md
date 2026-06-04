# Draft: CD-A Taupe/TDR workbook units and calibration needed before objective activation

Subject: CD-A Taupe/TDR workbook units and calibration needed before objective activation
Suggested To: Gesa.Ziefle@bgr.de
Suggested Cc: none
Contact route: coordinator_only_provider_unresolved
Contact evidence: Gesa's 2025-11-07 measurement overview says the TeamBeam transfer includes Taupe data and context, but the current scan does not identify a direct Taupe/TDR provider address.
Contact caveat: Ask Gesa to forward to the Taupe/TDR provider or confirm the unit/calibration source directly.

Dear Gesa,

We can compare Taupe/TDR temporal trends diagnostically, but the workbook values need unit and calibration confirmation before any absolute water-content or saturation residual.

Could you please help with the items below? These are the minimum pieces we need before we can describe the corresponding stream as a defensible hard residual in the CD-A OGS inversion workflow.

## `taupe_unit_calibration`

Request: Confirm what the values in Taupe_WC.xlsx physically represent: calibrated volumetric water-content percent, relative dielectric permittivity, ARDP-derived proxy, or another quantity. Provide the sensor-specific calibration equations and uncertainty.

Minimum acceptance criteria: Workbook unit for every sheet/column; calibration equation and constants; whether values are already corrected for rock porosity/mineral matrix; uncertainty by sensor/band; baseline/reference date; and ARDP-to-water or dielectric conversion details.

Why this matters: The current workbook values pass some sanity checks if interpreted as water-content percent but fail if interpreted through a generic Topp permittivity conversion. Absolute Taupe residuals would be misleading without calibration.

Current local evidence/blocker: absolute candidate conversions remain sanity checks; Topp physical rows are zero in current audit Taupe values are not confirmed as volumetric water-content percent, permittivity, or another ARDP-derived proxy.

Local artifacts we can share if useful: inversion_workflow/processed_observations/taupe_tdr_semantics.md; cda_knowledge_base/measurements/taupe_tdr/source_files/Taupe_WC.xlsx

Best,
