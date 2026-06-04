# RH Boundary Curve Provenance Request

This package turns the open RH boundary caveat into specific questions for BGR/Gesa.
The local workflow can convert the copied OT_RH5-8 workbooks to Kelvin liquid pressure,
but that conversion does not reproduce the active OGS open-niche pressure curve.

## Current State

- Request rows: 6
- Evidence rows: 10
- Active objective rows from RH: 0
- RH semantics status: `boundary_forcing_semantics_ready_curve_provenance_unverified`
- Active curve date span from model time origin: 2019-09-18 to 2023-12-26
- Active curve rows: 845
- Active curve implied RH range: 70.23 to 96.59 percent
- Active curve rows below clean RH5/RH6 workbook minimum: 772 of 845
- RH rows compared to active curve: 2280
- Later RH rows outside active curve range: 1948
- Median absolute boundary mismatch: 13.00 MPa

## Request Table

| Request | Priority | Category | Current status |
| --- | --- | --- | --- |
| `active_open_niche_curve_generation` | high | curve_generation | `blocked_curve_generation_provenance_missing` |
| `time_range_and_curve_extension` | high | time_axis | `blocked_late_measurements_outside_active_curve_range` |
| `sensor_selection_and_quality_screening` | high | sensor_quality | `blocked_sensor_selection_not_documented` |
| `kelvin_temperature_density_assumptions` | medium | physical_conversion | `blocked_conversion_constants_unverified` |
| `open_closed_boundary_mapping` | medium | model_curve_mapping | `blocked_curve_mapping_needs_confirmation` |
| `retention_validation_and_parameter_release_gate` | medium | inversion_gate | `blocked_retention_use_policy_unconfirmed` |

## What To Ask BGR/Gesa For

Email-ready text:

```text
Could you please help reconstruct or document how the CD-A open-niche pressure boundary curve 08_08_open_niche_seasonal.xml was generated?

Using the copied OT_RH5 to OT_RH8 workbooks, we can reproduce a Kelvin-equation liquid-pressure candidate, but it does not reproduce the active OGS curve. The overlap audit compares 2,280 RH rows and gives a median absolute mismatch of about 13 MPa. Inverting the active curve with the same Kelvin coefficient gives an implied RH range of about 70.23 to 96.59 percent, and 772 of 845 active curve rows are drier than the clean RH5/RH6 workbook minimum.

Could you provide the original source data and processing used for the active curve, including the script/spreadsheet if available? We need the sensor selection, time origin and timezone, interpolation or smoothing, outlier handling, pressure sign/unit convention, gauge versus absolute convention, gas pressure convention, temperature/density constants, and whether the shifted open curve is obsolete or an alternative. Please also confirm whether later RH/temperature data through 2025-09-04 should extend the boundary curve, and whether RH/suction should be used only as boundary forcing or also as retention validation/calibration.
```

## Detailed Requests

### `active_open_niche_curve_generation`

- Priority: `high`
- Scope: 08_08_open_niche_seasonal.xml / open_niche_seasonal_curve
- Requested files or answers: Original source time series, spreadsheet, script, or processing notebook used to generate the active open-niche pressure curve; include intermediate tables if the curve was smoothed, filtered, averaged, shifted, or manually edited.
- Requested details: Sensor/source identifiers; date/time origin; interpolation grid; smoothing/filtering; outlier handling; formula; pressure sign convention; whether values are gauge or absolute; unit conversion; gas-pressure convention; temperature and density assumptions; and exact software/script version.
- Current evidence: Active curve rows=845 with implied RH 70.23-96.59 percent; 772 of 845 rows imply RH below the clean RH5/RH6 workbook minimum; overlap residual median abs=13.00 MPa; curve date span from model time origin 2019-09-18 is 2019-09-18 to 2023-12-26.
- Model impact if resolved: Allows the active OGS open-niche pressure curve to be classified as a verified boundary forcing or replaced by a reproducible RH-derived forcing.
- Activation gate: Do not use RH as a point residual or release retention/boundary parameters until the curve-generation provenance, time axis, sensor quality policy, and conversion constants are documented.

### `time_range_and_curve_extension`

- Priority: `high`
- Scope: active curve coverage versus OT_RH5-8 measurements through 2025-09-04
- Requested files or answers: Decision on whether the active curve should stop at its current end time, be extended with later RH/temperature data, or be replaced by a new boundary series for 2022-2025 runs.
- Requested details: Confirm the model-time zero date, timezone/local-time convention, timestep interpolation rule, extrapolation policy after the active curve end, and the intended curve for any post-2022 simulation period.
- Current evidence: Active curve rows=845 with implied RH 70.23-96.59 percent; 772 of 845 rows imply RH below the clean RH5/RH6 workbook minimum; overlap residual median abs=13.00 MPa; curve date span from model time origin 2019-09-18 is 2019-09-18 to 2023-12-26.
- Model impact if resolved: Prevents silent extrapolation or stale forcing when comparing 2023-2025 RH/NMR/ERT/Taupe measurements to candidate OGS runs.
- Activation gate: Do not use RH as a point residual or release retention/boundary parameters until the curve-generation provenance, time axis, sensor quality policy, and conversion constants are documented.

### `sensor_selection_and_quality_screening`

- Priority: `high`
- Scope: OT_RH5, OT_RH6, OT_RH7, OT_RH8 and any older/open-niche RH streams
- Requested files or answers: Quality-screening rule and sensor selection used for the active curve, including whether RH5/RH6, RH7/RH8, psychrometers, Geoscope auxiliary logs, or older sheets were used.
- Requested details: Calibration certificates or quality flags; handling of RH7/RH8 low values near 13 percent; handling of open-twin thermo-hygrometer values above 95 percent RH; missing-data filling; sensor averaging/weighting; and periods rejected due to maintenance or door/opening events.
- Current evidence: Active curve rows=845 with implied RH 70.23-96.59 percent; 772 of 845 rows imply RH below the clean RH5/RH6 workbook minimum; overlap residual median abs=13.00 MPa; curve date span from model time origin 2019-09-18 is 2019-09-18 to 2023-12-26.
- Model impact if resolved: Defines the measurement-error model and decides whether high-RH open-twin data are retained, downweighted, or excluded from any future forcing reconstruction.
- Activation gate: Do not use RH as a point residual or release retention/boundary parameters until the curve-generation provenance, time axis, sensor quality policy, and conversion constants are documented.

### `kelvin_temperature_density_assumptions`

- Priority: `medium`
- Scope: Kelvin RH-to-liquid-pressure conversion and auxiliary temperature data
- Requested files or answers: Temperature series and constants used in the original conversion, or confirmation that a fixed temperature and fixed liquid density were used.
- Requested details: Temperature source and unit; water density; molar mass; gas constant; vapour pressure/RH definition; whether RH is percent or fraction before conversion; whether atmospheric pressure is added; and whether suction/capillary pressure or liquid pressure is stored in XML.
- Current evidence: Active curve rows=845 with implied RH 70.23-96.59 percent; 772 of 845 rows imply RH below the clean RH5/RH6 workbook minimum; overlap residual median abs=13.00 MPa; curve date span from model time origin 2019-09-18 is 2019-09-18 to 2023-12-26.
- Model impact if resolved: Makes the RH-to-pressure conversion reproducible and determines whether current 298.15 K / 1095 kg/m3 assumptions are adequate for uncertainty propagation.
- Activation gate: Do not use RH as a point residual or release retention/boundary parameters until the curve-generation provenance, time axis, sensor quality policy, and conversion constants are documented.

### `open_closed_boundary_mapping`

- Priority: `medium`
- Scope: open and closed niche curve includes in 08_curves.xml
- Requested files or answers: Confirmation of which XML curve files are active, deprecated, or alternatives for open and closed niches, including the status of open_niche_seasonal_curve_shifted.xml.
- Requested details: Open/closed niche source streams; whether the shifted open curve is an obsolete absolute-time variant or a candidate to use; whether closed_niche_seasonal_curve_shifted.xml is derived from separate closed-twin sensors; and boundary-surface assignment in the model.
- Current evidence: Active curve rows=845 with implied RH 70.23-96.59 percent; 772 of 845 rows imply RH below the clean RH5/RH6 workbook minimum; overlap residual median abs=13.00 MPa; curve date span from model time origin 2019-09-18 is 2019-09-18 to 2023-12-26.
- Model impact if resolved: Avoids mixing active, shifted, open, and closed boundary curves when preparing candidate runs.
- Activation gate: Do not use RH as a point residual or release retention/boundary parameters until the curve-generation provenance, time axis, sensor quality policy, and conversion constants are documented.

### `retention_validation_and_parameter_release_gate`

- Priority: `medium`
- Scope: using RH/suction for retention validation or calibration
- Requested files or answers: Decision on whether the shared RH/suction data should be used only as boundary forcing, as retention validation, or as a future calibration target for van Genuchten parameters.
- Requested details: Sensor support/locations for retention validation; accepted uncertainty model; whether the active p_b and exponent values are fixed; and which checks must pass before releasing retention parameters in the inverse problem.
- Current evidence: Active curve rows=845 with implied RH 70.23-96.59 percent; 772 of 845 rows imply RH below the clean RH5/RH6 workbook minimum; overlap residual median abs=13.00 MPa; curve date span from model time origin 2019-09-18 is 2019-09-18 to 2023-12-26.
- Model impact if resolved: Keeps retention parameters frozen unless provenance, uncertainty, and OGS state outputs make a defensible RH/suction likelihood possible.
- Activation gate: Do not use RH as a point residual or release retention/boundary parameters until the curve-generation provenance, time axis, sensor quality policy, and conversion constants are documented.

## Evidence Rows

| Evidence id | Type | Source artifact | Status |
| --- | --- | --- | --- |
| `active_curve_quantiles` | generated_curve_semantics | `rh_boundary_curve_semantics.csv; rh_measurement_semantics_summary.json` | `provenance_unverified` |
| `curve_below_clean_sensor_range` | range_mismatch | `rh_boundary_curve_semantics.csv` | `mismatch_requires_external_confirmation` |
| `boundary_overlap_residual` | boundary_audit_statistic | `rh_measurement_semantics_summary.json; rh_boundary_curve_audit_summary.json` | `large_mismatch` |
| `curve_include_mapping` | ogs_xml_include_audit | `ogs_settings/08_curves.xml` | `mapping_observed_confirmation_requested` |
| `kelvin_conversion_assumptions` | conversion_assumption | `rh_measurement_semantics_summary.json` | `constants_unverified_against_original_curve` |
| `sensor_RH5_summary` | sensor_quality_summary | `rh_measurement_semantics_sensor_summary.csv` | `quality_policy_requested` |
| `sensor_RH6_summary` | sensor_quality_summary | `rh_measurement_semantics_sensor_summary.csv` | `quality_policy_requested` |
| `sensor_RH7_summary` | sensor_quality_summary | `rh_measurement_semantics_sensor_summary.csv` | `quality_policy_requested` |
| `sensor_RH8_summary` | sensor_quality_summary | `rh_measurement_semantics_sensor_summary.csv` | `quality_policy_requested` |
| `raw_source_workbooks` | source_file_set | `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/Location_suc.png; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/OT_RH5.xlsx; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/OT_RH6.xlsx; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/OT_RH7.xlsx; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/OT_RH8.xlsx` | `source_files_catalogued` |

## Source Files Checked

- `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/ogs_settings/08_curves.xml`
- `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/ogs_settings/08_08_open_niche_seasonal.xml`
- `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/ogs_settings/open_niche_seasonal_curve_shifted.xml`
- `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/ogs_settings/closed_niche_seasonal_curve_shifted.xml`
- `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/GESA_model_original/projection_on_mesh_2025-09-05/08_curves.xml`
- `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/GESA_model_original/projection_on_mesh_2025-09-05/08_08_open_niche_seasonal.xml`
- `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/Location_suc.png`
- `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/OT_RH5.xlsx`
- `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/OT_RH6.xlsx`
- `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/OT_RH7.xlsx`
- `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/OT_RH8.xlsx`

## Generated Files

- `request_csv`: `inversion_workflow/processed_observations/rh_boundary_provenance_request.csv`
- `evidence_csv`: `inversion_workflow/processed_observations/rh_boundary_provenance_evidence.csv`
- `summary_json`: `inversion_workflow/processed_observations/rh_boundary_provenance_request_summary.json`
- `markdown`: `inversion_workflow/processed_observations/rh_boundary_provenance_request.md`

Remaining blocker: Obtain or reconstruct the generation history for 08_08_open_niche_seasonal.xml before treating the active open-niche pressure curve as verified RH-derived forcing or using RH as a retention-parameter likelihood.
