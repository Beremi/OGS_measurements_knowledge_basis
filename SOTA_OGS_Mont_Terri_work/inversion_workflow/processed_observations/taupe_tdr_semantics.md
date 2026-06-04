# Taupe/TDR Measurement Semantics Audit

This audit is the model-facing interpretation layer for the Taupe/TDR EDZ-band workbook.
It separates a defensible trend diagnostic from unsupported absolute saturation or water-content use.

## Source Files

- Raw Taupe workbook: [Taupe_WC.xlsx](/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/Taupe_WC.xlsx)
- Coordinate workbook: [Coordinates_NMR_Taupe_characborehole.xlsx](/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/Coordinates_NMR_Taupe_characborehole.xlsx)
- Location figures: [NMR_Taupe_Char_brg_1.png](/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/NMR_Taupe_Char_brg_1.png), [NMR_Taupe_Char_brg_2.png](/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/NMR_Taupe_Char_brg_2.png), [NMR_Taupe_Char_brg_3.png](/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/NMR_Taupe_Char_brg_3.png)
- ISU Taupe/TDR discussion slides: [2604_TD_CD-A_ISU.pdf](/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/2604_TD_CD-A_ISU.pdf)
- TD modelling slides: [CD-A_Slides_TD_260427x.pdf](/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/CD-A_Slides_TD_260427x.pdf)

## Current Status

- Status: `trend_semantics_ready_absolute_calibration_blocked`
- Workbook rows: 5088
- Operator/audit rows: 5088
- Sensor/EDZ-band series: 24
- Date range: 2019-12-01 to 2025-10-10
- Mapped trend-ready rows: 2544
- Outside current local OGS mesh support: 2544
- State-target rows in the combined state table: 5088 (0 active in the current state fit).

The current defensible use is a same-series temporal trend diagnostic.  For each sensor and EDZ band, the Taupe operator compares the observed baseline-normalized Taupe anomaly with a matching baseline-normalized trend in band-averaged `theta_model = porosity * liquid_saturation`.  It is not yet an absolute saturation likelihood.

## Semantics

| Item | Interpretation |
| --- | --- |
| Measured/workbook quantity | Taupe/TDR EDZ-band value, treated as an ARDP/dielectric water-content proxy until the unit is confirmed. |
| Model quantity | Band-average `theta_model = porosity * liquid_saturation`. |
| Recommended residual | Same-series standardized model-theta anomaly minus Taupe standardized anomaly. |
| Not a direct measurement of | Absolute saturation, calibrated volumetric water content unless confirmed, permeability, or pressure. |
| Absolute residual gate | Blocked until `Taupe_WC.xlsx` unit and sensor-specific calibration are documented. |

## Row Activation Counts

| Gate | Rows |
| --- | ---: |
| `excluded_current_mesh_outside_support` | 2544 |
| `trend_diagnostic_ready_pending_ogs_outputs_absolute_calibration_blocked` | 2544 |

A3 and A4 account for the 2,544 mapped rows.  A7 and A8 are preserved in the archive and in the operator table, but they are outside the current local OGS mesh support and therefore are not active model targets in this setup.

## Absolute Conversion Sanity Checks

| Candidate interpretation | Physical rows within saturation [0, 1] | Role |
| --- | ---: | --- |
| Taupe value as volumetric water-content percent | 2120 | Plausibility check only. |
| Taupe value as Topp dielectric permittivity | 0 | Rejected as a default absolute conversion for this dataset. |
| Local linear dielectric mixing, `epsilon_rock = 6` | 2544 | Sensitivity check only. |

These counts do not establish a calibration.  They only show which interpretations stay in a physical saturation range with the current porosity support.

## Series-Level Audit

| Series | Gate | Rows | Mapped | Outside mesh | Baseline | Scale | Taupe min | Taupe max | Net std change | WC% physical | Topp physical | Linear eps6 physical |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A3_0-10cm | `trend_series_ready_pending_ogs_outputs_absolute_calibration_blocked` | 212 | 212 | 0 | 10.1725 | 0.015973 | 10.0765 | 10.1931 | -3.756 | 212 | 0 | 212 |
| A3_0-50cm | `trend_series_ready_pending_ogs_outputs_absolute_calibration_blocked` | 212 | 212 | 0 | 10.2415 | 0.0118847 | 10.1804 | 10.2588 | -4.366 | 212 | 0 | 212 |
| A3_10-20cm | `trend_series_ready_pending_ogs_outputs_absolute_calibration_blocked` | 212 | 212 | 0 | 10.1965 | 0.0202854 | 10.1023 | 10.2138 | -4.220 | 0 | 0 | 212 |
| A3_20-30cm | `trend_series_ready_pending_ogs_outputs_absolute_calibration_blocked` | 212 | 212 | 0 | 10.239 | 0.019986 | 10.1438 | 10.2486 | -3.655 | 212 | 0 | 212 |
| A3_30-40cm | `trend_series_ready_pending_ogs_outputs_absolute_calibration_blocked` | 212 | 212 | 0 | 10.2608 | 0.0140617 | 10.199 | 10.2864 | -4.430 | 0 | 0 | 212 |
| A3_40-50cm | `trend_series_ready_pending_ogs_outputs_absolute_calibration_blocked` | 212 | 212 | 0 | 10.3421 | 0.0173421 | 10.3205 | 10.4571 | 1.524 | 212 | 0 | 212 |
| A4_0-10cm | `trend_series_ready_pending_ogs_outputs_absolute_calibration_blocked` | 212 | 212 | 0 | 10.2024 | 0.0286862 | 10.1701 | 10.2875 | 1.599 | 212 | 0 | 212 |
| A4_0-50cm | `trend_series_ready_pending_ogs_outputs_absolute_calibration_blocked` | 212 | 212 | 0 | 10.2409 | 0.00906439 | 10.2198 | 10.2661 | 0.959 | 212 | 0 | 212 |
| A4_10-20cm | `trend_series_ready_pending_ogs_outputs_absolute_calibration_blocked` | 212 | 212 | 0 | 10.2559 | 0.0104129 | 10.1985 | 10.2746 | -6.640 | 212 | 0 | 212 |
| A4_20-30cm | `trend_series_ready_pending_ogs_outputs_absolute_calibration_blocked` | 212 | 212 | 0 | 10.2625 | 0.0176038 | 10.1942 | 10.3181 | 2.495 | 212 | 0 | 212 |
| A4_30-40cm | `trend_series_ready_pending_ogs_outputs_absolute_calibration_blocked` | 212 | 212 | 0 | 10.3454 | 0.0150993 | 10.2465 | 10.3574 | -4.570 | 212 | 0 | 212 |
| A4_40-50cm | `trend_series_ready_pending_ogs_outputs_absolute_calibration_blocked` | 212 | 212 | 0 | 10.3896 | 0.0229423 | 10.2463 | 10.407 | -6.649 | 212 | 0 | 212 |
| A7_0-10cm | `excluded_current_mesh_outside_support` | 212 | 0 | 212 | 10.189 | 0.159096 | 10.1542 | 10.5672 | 2.132 | 0 | 0 | 0 |
| A7_0-50cm | `excluded_current_mesh_outside_support` | 212 | 0 | 212 | 10.3043 | 0.126816 | 10.2676 | 10.7081 | 2.908 | 0 | 0 | 0 |
| A7_10-20cm | `excluded_current_mesh_outside_support` | 212 | 0 | 212 | 10.3295 | 0.113298 | 10.2896 | 10.7126 | 3.051 | 0 | 0 | 0 |
| A7_20-30cm | `excluded_current_mesh_outside_support` | 212 | 0 | 212 | 10.4058 | 0.090901 | 10.3659 | 10.8617 | 4.644 | 0 | 0 | 0 |
| A7_30-40cm | `excluded_current_mesh_outside_support` | 212 | 0 | 212 | 10.4203 | 0.0937399 | 10.3823 | 10.8947 | 4.499 | 0 | 0 | 0 |
| A7_40-50cm | `excluded_current_mesh_outside_support` | 212 | 0 | 212 | 10.4714 | 0.0799219 | 10.4261 | 11.0044 | 6.048 | 0 | 0 | 0 |
| A8_0-10cm | `excluded_current_mesh_outside_support` | 212 | 0 | 212 | 9.91933 | 0.108016 | 9.87127 | 10.1692 | 2.247 | 0 | 0 | 0 |
| A8_0-50cm | `excluded_current_mesh_outside_support` | 212 | 0 | 212 | 10.0063 | 0.0847028 | 9.97487 | 10.2166 | 1.936 | 0 | 0 | 0 |
| A8_10-20cm | `excluded_current_mesh_outside_support` | 212 | 0 | 212 | 10.0388 | 0.0884125 | 10.001 | 10.2454 | 1.630 | 0 | 0 | 0 |
| A8_20-30cm | `excluded_current_mesh_outside_support` | 212 | 0 | 212 | 10.0725 | 0.0683313 | 10.036 | 10.251 | 1.447 | 0 | 0 | 0 |
| A8_30-40cm | `excluded_current_mesh_outside_support` | 212 | 0 | 212 | 10.0876 | 0.0714612 | 10.0348 | 10.2635 | 1.344 | 0 | 0 | 0 |
| A8_40-50cm | `excluded_current_mesh_outside_support` | 212 | 0 | 212 | 10.0415 | 0.067734 | 10.0205 | 10.2252 | 1.569 | 0 | 0 | 0 |

## Sensor Summary

| Sensor | Rows | Mapped | Outside mesh | Taupe min | Taupe median | Taupe max | Anomaly min | Anomaly max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A3 | 1272 | 1272 | 0 | 10.0765 | 10.2104 | 10.4571 | -6.006 | 6.635 |
| A4 | 1272 | 1272 | 0 | 10.1701 | 10.26 | 10.407 | -6.553 | 3.163 |
| A7 | 1272 | 0 | 1272 | 10.1542 | 10.6731 | 11.0044 | -0.567 | 6.668 |
| A8 | 1272 | 0 | 1272 | 9.87127 | 10.1212 | 10.2635 | -0.740 | 2.712 |

## First Model Use

After OGS state outputs exist, sample `theta_model = porosity * liquid_saturation` over the same Taupe EDZ-band support, normalize each model series against the same baseline dates, and compare trend anomalies by sensor, EDZ band, and time.  Use grouped weights by sensor/EDZ/time rather than treating every band row as independent if strong temporal or spatial correlation is retained.

## Remaining Blocker

Confirm whether Taupe_WC workbook values are calibrated volumetric water-content percent, apparent relative dielectric permittivity, or another ARDP-derived proxy before assigning absolute saturation or water-content residual weights.

## Generated Audit Files

- `row_audit`: `inversion_workflow/processed_observations/taupe_tdr_semantics_row_audit.csv`
- `series_audit`: `inversion_workflow/processed_observations/taupe_tdr_semantics_series_audit.csv`
- `group_summary`: `inversion_workflow/processed_observations/taupe_tdr_semantics_group_summary.csv`
- `summary`: `inversion_workflow/processed_observations/taupe_tdr_semantics_summary.json`
- `markdown`: `inversion_workflow/processed_observations/taupe_tdr_semantics.md`
