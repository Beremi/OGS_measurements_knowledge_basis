# Missing Numeric Other-HM Monitoring Request

This package turns the remaining secondary hydromechanical monitoring gap into
specific file requests.  The current catalogue has layout geometry, levelling
slide values, and qualitative TD statements, but not the numeric Geoscope and
laser-scan exports needed for hard pressure/deformation residuals.

## Current State

- Request rows: 6
- Evidence rows: 8
- Active objective rows from this stream: 0
- Inventory status: `layout_and_qualitative_targets_ready_numeric_series_missing`

## Request Table

| Request | Priority | Scope | Model quantity | Current status |
| --- | --- | --- | --- | --- |
| `geoscope_mini_piezometer_time_series` | high | BCD-A28 to BCD-A31 | liquid pore pressure or hydraulic head | `blocked_numeric_series_missing` |
| `geoscope_extensometer_time_series` | high | all CD-A extensometers, with BCD-A9/B10 failure metadata | displacement or strain | `blocked_numeric_series_missing` |
| `geoscope_crackmeter_time_series` | medium | closed-niche ongoing trend and open-niche seasonal variation | crack aperture or local relative displacement | `blocked_numeric_series_missing` |
| `laser_scan_statistical_interpretation_2026_04_20` | medium | open_twin_LS and closed_twin_LS surfaces/statistical update | surface displacement or scan-difference field | `blocked_statistical_export_missing` |
| `precision_levelling_full_survey_table` | low | points 57, 58, CDA-C1 to CDA-C5, CDA-O1 to CDA-O5 | vertical displacement | `partial_slide_summary_available_full_table_missing` |
| `geoscope_boundary_and_auxiliary_context` | medium | RH, temperature, door/opening times, suction from Geoscope update | boundary-condition forcing and disturbance context | `blocked_or_unverified_auxiliary_exports` |

## What To Ask BGR/Gesa For

Email-ready text:

```text
Could you please provide the numeric CD-A monitoring exports behind the 2026 Geoscope/laser-scan update?

The current catalogue has the meeting minutes, layout geometry, and levelling slide summary, but not the raw numeric exports needed for model residuals. We need Geoscope time series for mini-piezometers BCD-A28 to BCD-A31, extensometers including BCD-A9/B10 status and failure metadata since September 2025, crackmeters, and auxiliary RH/temperature/door/suction logs if these are separate from the already shared RH files. We also need the laser-scan statistical interpretation files from the 2026-04-20 update, ideally with the registered point clouds or surface-difference products.

For time series, please include timestamps, units, instrument ids, coordinates/support ids, zero/reference conventions, calibration or conversion used by Geoscope, quality/status flags, and raw-file provenance. For laser scans, please include scan dates, coordinate frame, registration transform/targets, displacement or difference statistics, uncertainty/registration error, and masks/excluded areas.
```

## Detailed Requests

### `geoscope_mini_piezometer_time_series`

- Priority: `high`
- Scope: BCD-A28 to BCD-A31
- Requested files: Geoscope pressure time-series exports for BCD-A28, BCD-A29, BCD-A30, and BCD-A31, including calibration/status metadata.
- Required fields: timestamp with timezone or stated local time; instrument id; measured value; unit; coordinate or trace/support id; zero/reference convention; calibration or conversion used by Geoscope; quality/status flags; maintenance/failure flags; sampling interval; and raw file provenance. Pressure convention must state absolute/gauge/head, pressure unit, temperature compensation, sensor elevation/depth, and whether values are liquid pore pressure or hydraulic head.
- Model entry if provided: Candidate pressure residuals against OGS liquid_pressure/pressure-head samples after sensor coordinates and reference pressure are confirmed.
- Current evidence: 2026 TD minutes say mini-piezometers BCD-A28 to BCD-A31 were working well; the HERMES input note lists pore-water pressure and piezometer/extensometer measurements as available CD-A data.

### `geoscope_extensometer_time_series`

- Priority: `high`
- Scope: all CD-A extensometers, with BCD-A9/B10 failure metadata
- Requested files: Geoscope extensometer displacement/strain time-series exports, including instrument geometry and the September 2025 BCD-A9/B10 failure/status record.
- Required fields: timestamp with timezone or stated local time; instrument id; measured value; unit; coordinate or trace/support id; zero/reference convention; calibration or conversion used by Geoscope; quality/status flags; maintenance/failure flags; sampling interval; and raw file provenance. Include anchor/collar geometry, orientation, gauge length, whether the reported value is displacement or strain, sign convention, and restart/zero changes after maintenance.
- Model entry if provided: Mechanical validation residuals or rejection gates against OGS displacement/strain diagnostics, respecting post-failure data-quality boundaries.
- Current evidence: 2026 TD minutes report horizontal and vertical extensometers BCD-A9/B10 in the closed niche failed since September 2025; BGR modelling slides set displacements/strains from extensometers as a priority validation stream.

### `geoscope_crackmeter_time_series`

- Priority: `medium`
- Scope: closed-niche ongoing trend and open-niche seasonal variation
- Requested files: Geoscope crackmeter time-series exports for all CD-A crackmeter positions, including position labels and data-quality/status flags.
- Required fields: timestamp with timezone or stated local time; instrument id; measured value; unit; coordinate or trace/support id; zero/reference convention; calibration or conversion used by Geoscope; quality/status flags; maintenance/failure flags; sampling interval; and raw file provenance. Include crackmeter location, measured aperture/displacement component, positive sign convention, zero/reference date, and any temperature correction.
- Model entry if provided: Qualitative or numeric deformation gates for open/closed twin contrast; hard residual only if support and sign convention can be matched to model output.
- Current evidence: 2026 TD minutes state crackmeter data show one ongoing trend in the closed niche and seasonal variation in the open niche.

### `laser_scan_statistical_interpretation_2026_04_20`

- Priority: `medium`
- Scope: open_twin_LS and closed_twin_LS surfaces/statistical update
- Requested files: Laser-scan statistical interpretation files from the 2026-04-20 update, plus raw/registered point clouds or surface-difference products if available.
- Required fields: scan date/time; open/closed twin surface id; coordinate frame; registration targets and transform; displacement/difference statistic; uncertainty or registration error; masked/excluded areas; and raw/statistical file provenance.
- Model entry if provided: Surface-displacement validation or qualitative mechanical plausibility gate after OGS displacement output and survey frame are aligned.
- Current evidence: 2026 TD minutes say laser scans with statistical interpretation were sent in the 2026-04-20 Geoscope update; VisualisationCDA.dat contains open_twin_LS and closed_twin_LS surface zones.

### `precision_levelling_full_survey_table`

- Priority: `low`
- Scope: points 57, 58, CDA-C1 to CDA-C5, CDA-O1 to CDA-O5
- Requested files: Spreadsheet/table export of precision-levelling campaigns, including all campaign dates and reference-frame/covariance information.
- Required fields: point id; campaign date; elevation or height change; unit; reference point/frame; covariance or standard uncertainty; instrument/procedure metadata; and flags for excluded or adjusted points.
- Model entry if provided: Weighted displacement-validation residuals; the current slide-summary rows can only support sign/order-of-magnitude checks.
- Current evidence: The levelling presentation gives a 12-point slide summary, but not a full survey table with all dates, covariance/reference frame, and processing details.

### `geoscope_boundary_and_auxiliary_context`

- Priority: `medium`
- Scope: RH, temperature, door/opening times, suction from Geoscope update
- Requested files: Auxiliary Geoscope exports for RH, temperature, door/opening times, and suction if they are distinct from the already catalogued RH/suction files.
- Required fields: timestamp with timezone or stated local time; instrument id; measured value; unit; coordinate or trace/support id; zero/reference convention; calibration or conversion used by Geoscope; quality/status flags; maintenance/failure flags; sampling interval; and raw file provenance. Include sensor location, whether RH is percent or fraction, temperature unit, door/opening event definition, and suction conversion convention.
- Model entry if provided: Boundary-condition provenance check for RH/temperature forcing and event exclusion windows, not a separate hard residual by default.
- Current evidence: 2026 TD minutes say the Geoscope update covered RH, temperature, door opening times, and suction in addition to deformation/pressure streams.

## Evidence Rows

| Evidence id | Type | Source | Page | Readiness |
| --- | --- | --- | ---: | --- |
| `geoscope_update_scope_2026_04_20` | qualitative_source_statement | `cda_knowledge_base/measurements/other_hm_monitoring/source_files/2026-05-11_TD517_CD-A_260507__Minutes.pdf` | 3 | `source_mentions_numeric_streams_raw_series_not_in_catalogue` |
| `closed_extensometer_failure_since_2025_09` | qualitative_source_statement | `cda_knowledge_base/measurements/other_hm_monitoring/source_files/2026-05-11_TD517_CD-A_260507__Minutes.pdf` | 3 | `maintenance_caveat_structured` |
| `mini_piezometers_working_well_2026` | qualitative_source_statement | `cda_knowledge_base/measurements/other_hm_monitoring/source_files/2026-05-11_TD517_CD-A_260507__Minutes.pdf` | 3 | `instrument_status_ready_numeric_series_missing` |
| `crackmeter_closed_trend_open_seasonal` | qualitative_source_statement | `cda_knowledge_base/measurements/other_hm_monitoring/source_files/2026-05-11_TD517_CD-A_260507__Minutes.pdf` | 3 | `qualitative_trend_ready_numeric_series_missing` |
| `levelling_cda_o1_settlement_c4_heave` | qualitative_source_statement | `cda_knowledge_base/measurements/other_hm_monitoring/source_files/Folien_Niv_TD_CDA_2026.pdf` | 6 | `numeric_summary_rows_extracted_reference_frame_pending` |
| `bgr_edf_next_measurement_focus` | qualitative_source_statement | `cda_knowledge_base/measurements/other_hm_monitoring/source_files/CD-A_TD_2026_sc.pdf` | 2 | `operator_scope_ready_numeric_series_missing` |
| `hermes_available_monitoring_scope` | qualitative_source_statement | `cda_knowledge_base/measurements/other_hm_monitoring/source_files/2024-12-19_Input_HERMES_BGR_20241217.pdf` | 5 | `scope_documented_raw_exports_partly_missing` |
| `levelling_slide_summary_12_points` | numeric_slide_summary | `cda_knowledge_base/measurements/other_hm_monitoring/source_files/Folien_Niv_TD_CDA_2026.pdf` | 5 | `numeric_summary_available_full_table_missing` |

## Source Files Checked

- `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/2026-05-11_TD517_CD-A_260507__Minutes.pdf`
- `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/CD-A_TD_2026_sc.pdf`
- `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/Folien_Niv_TD_CDA_2026.pdf`
- `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/2024-12-19_Input_HERMES_BGR_20241217.pdf`
- `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/VisualisationCDA.dat`

## Generated Files

- `request_csv`: `inversion_workflow/processed_observations/other_hm_missing_numeric_request.csv`
- `evidence_csv`: `inversion_workflow/processed_observations/other_hm_missing_numeric_evidence.csv`
- `summary_json`: `inversion_workflow/processed_observations/other_hm_missing_numeric_request_summary.json`
- `markdown`: `inversion_workflow/processed_observations/other_hm_missing_numeric_request.md`
