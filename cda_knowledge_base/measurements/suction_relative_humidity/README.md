# Suction / Relative Humidity Measurement Information

This folder collects suction and relative-humidity material for CD-A, especially open-twin thermo-hygrometer sheets and the 2025 report/2026 meeting material.

## Copied Source Files

- [OT_RH5.xlsx](source_files/OT_RH5.xlsx), [OT_RH6.xlsx](source_files/OT_RH6.xlsx), [OT_RH7.xlsx](source_files/OT_RH7.xlsx), [OT_RH8.xlsx](source_files/OT_RH8.xlsx) - open-twin relative humidity spreadsheets extracted from `003_Nov_2025.zip`.
- [003_Nov_2025.zip](source_files/003_Nov_2025.zip) - original multi-measurement TeamBeam archive containing the RH workbooks and suction location image.
- [Location_suc.png](source_files/Location_suc.png) - suction/RH location image extracted from `003_Nov_2025.zip`.
- [RO_2013.4_3974_CD-A3 Phase 30_A21_TN-2025-12_signed.pdf](<source_files/RO_2013.4_3974_CD-A3 Phase 30_A21_TN-2025-12_signed.pdf>) - CD-A phase 30 annual/report material from the TD package.
- [2026-05-11_TD517_CD-A_260507__Minutes.pdf](source_files/2026-05-11_TD517_CD-A_260507__Minutes.pdf) - May 2026 TD minutes.
- [CD-A_Slides_TD_260427x.pdf](source_files/CD-A_Slides_TD_260427x.pdf) - April 2026 TD slides with suction/RH reliability and modelling notes.

Original locations:

- [TeamBeam additional measurements archive](../../file_transfers/collected/2025-11-07_additional_measurements/003_Nov_2025.zip)
- [Thunderbird-recovered TD presentation package](../../attachments/thunderbird_recovered/2026-05-11_Presentations_CD-A_TD_260428.zip)
- [Gmail TD minutes](../../attachments/2026-05-11_TD517_CD-A_260507__Minutes.pdf)

Detailed file-level extraction from this pass is in
[derived_files/deep_source_pass/source_file_deep_summary.md](derived_files/deep_source_pass/source_file_deep_summary.md),
including RH workbook sheet summaries, searchable TD/report text, and ZIP member
checks.

## Relative Humidity Workbooks

The open-twin RH sheets contain date/time rows and relative humidity values. Extracted ranges:

- `OT_RH5.xlsx`: 1,042 rows, date range 2022-01-11 to 2025-09-04, RH range 94.0807375963905 to 95.9927206227757.
- `OT_RH6.xlsx`: 1,064 rows, date range 2021-12-16 to 2025-09-04, RH range 93.322527442857 to 94.9882577361112.
- `OT_RH7.xlsx`: 1,071 rows, date range 2021-12-16 to 2025-09-04, RH range 13.18797 to 97.27216088.
- `OT_RH8.xlsx`: 1,070 rows, date range 2021-12-16 to 2025-09-04, RH range 13.20271 to 96.2193812777774.

The low RH values near 13% in RH7/RH8 are likely outliers, sensor/logger failures, or invalid periods rather than physical niche behaviour. They should be screened before use.

## Instrumentation And Data Flow

The phase 30 report describes the suction measurement system:

- 8 psychrometers and 8 thermo-hygrometers are installed inside boreholes drilled in the twin niches.
- Installation depths reach up to about 70 cm.
- Psychrometers are connected to a PSS datalogger.
- Thermo-hygrometers are connected to the RH cabinet.
- Data are collected through a minicomputer.
- Data folders include `PSS_CDA2`, `RH_CDA2`, and `RH&Suction_CDA2`.
- Data transfer to Geoscope is by FTP.
- Phase 30 covers 2025-01-01 to 2025-12-31, including a maintenance visit on 2025-06-19.

Reported system issues:

- Problems with the PSS datalogger and psychrometer software.
- Thermo-hygrometers generally show smoother behaviour.
- In the closed twin, high saturation can push thermo-hygrometers above their reliable upper range, causing unrealistic drift/upward trends.
- Recommendations include adding a serial switch and replacing the computer.

## Reliability Notes From 2026 Slides

The April 2026 TD slides state:

- Open Twin: thermo-hygrometers are reliable at RH below 95%.
- Closed Twin: psychrometers are reliable at RH above 95%.
- Data transfer from the PSS was not yet fully available at Geoscope.
- Sensor/data connection should be preserved.
- Continued interpretation is listed as a TODO.

## Modelling Relevance

Suction/RH data are important because they connect directly to hydraulic boundary and state variables:

- RH can be converted to pressure boundary conditions through the Kelvin equation.
- Saturation can be linked through a retention curve, especially a van Genuchten-type pressure-capillary/saturation relation.
- Suction/RH can help constrain desaturation and resaturation near the open niche.
- RH data can provide meteorological boundary forcing or validation for open-twin simulations.

The September 2025 HERMES slides explicitly mention pressure boundary conditions at the surface derived from RH measurements and the Kelvin equation, and retention-curve fitting as part of the ERT/saturation inverse problem.

## Model-Facing Semantics And Boundary Audit

The SOTA/OGS workflow now keeps a dedicated RH semantics/provenance audit:

- [rh_measurement_semantics.md](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/rh_measurement_semantics.md)
- [rh_measurement_semantics_row_audit.csv](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/rh_measurement_semantics_row_audit.csv)
- [rh_measurement_semantics_sensor_summary.csv](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/rh_measurement_semantics_sensor_summary.csv)
- [rh_boundary_curve_semantics.csv](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/rh_boundary_curve_semantics.csv)

The catalogue also keeps local copies in `derived_files/`:

- [rh_measurement_semantics.md](derived_files/rh_measurement_semantics.md)
- [rh_measurement_semantics_summary.json](derived_files/rh_measurement_semantics_summary.json)
- [rh_measurement_semantics_row_audit.csv](derived_files/rh_measurement_semantics_row_audit.csv)
- [rh_measurement_semantics_sensor_summary.csv](derived_files/rh_measurement_semantics_sensor_summary.csv)
- [rh_boundary_curve_semantics.csv](derived_files/rh_boundary_curve_semantics.csv)
- [rh_boundary_provenance_request.md](derived_files/rh_boundary_provenance_request.md)
- [rh_boundary_provenance_request.csv](derived_files/rh_boundary_provenance_request.csv)
- [rh_boundary_provenance_evidence.csv](derived_files/rh_boundary_provenance_evidence.csv)
- [rh_boundary_provenance_request_summary.json](derived_files/rh_boundary_provenance_request_summary.json)
- [rh_boundary_candidate_curves.md](derived_files/rh_boundary_candidate_curves.md)
- [rh_boundary_candidate_curves.csv](derived_files/rh_boundary_candidate_curves.csv)
- [rh_boundary_candidate_curve_summary.csv](derived_files/rh_boundary_candidate_curve_summary.csv)
- [rh_boundary_candidate_curve_summary.json](derived_files/rh_boundary_candidate_curve_summary.json)
- [rh_boundary_candidate_curve_xml/](derived_files/rh_boundary_candidate_curve_xml/) - OGS-style XML snippets for local RH-derived candidate forcings.
- [rh_boundary_uncertainty.md](derived_files/rh_boundary_uncertainty.md)
- [rh_boundary_uncertainty_envelope.csv](derived_files/rh_boundary_uncertainty_envelope.csv)
- [rh_boundary_uncertainty_audit.csv](derived_files/rh_boundary_uncertainty_audit.csv)
- [rh_boundary_uncertainty_summary.json](derived_files/rh_boundary_uncertainty_summary.json)

Current model-facing interpretation:

- RH measures vapour relative humidity, not permeability, saturation, or a mesh-cell liquid pressure directly.
- The processed table converts RH to a Kelvin-equation gauge liquid-pressure candidate using `T = 298.15 K` and `rho_l = 1095 kg/m3`.
- 4,228 rows are valid non-low-outlier boundary-forcing evidence.
- 19 RH7/RH8 rows below 50% RH are excluded as likely outlier/logger/sensor episodes.
- 2,492 rows are above the open-twin 95% thermo-hygrometer caution threshold.
- RH5/RH6 are the cleanest open-twin boundary-reconstruction sensors in the copied workbooks.
- The active OGS open-niche curve is not a verified direct reconstruction of these workbooks: 772 of 845 active curve rows imply RH below the clean RH5/RH6 minimum when inverted through the same Kelvin coefficient.
- The provenance request package records six concrete BGR/Gesa questions and ten evidence rows. It asks for the active curve generation source/script, time axis and extension policy, sensor screening, Kelvin constants, open/closed curve mapping, and retention-calibration policy.
- The generated summary dates the active curve from 2019-09-18 to 2023-12-26 in model time, while the copied RH workbook data continue to 2025-09-04.
- The local candidate-curve builder now records six RH-derived boundary policies. The policy-preferred candidate is `rh5_rh6_median`; it has 1,063 daily rows from 2021-12-16 to 2025-09-04, 576 overlap rows against the active curve, 487 rows after the active curve ends, and overlap MAE 15.15 MPa. These curves are reproducible candidate forcings only, not verified replacements for `08_08_open_niche_seasonal.xml`.
- The candidate-envelope audit compares the six local policies day by day. It has 1,064 envelope dates, with 577 overlapping the active curve and 487 after the active curve. In the overlap, the local candidate pressure-envelope width is 2.10 MPa at p50 and 2.20 MPa at p90; the active curve is outside the envelope on 575 of 577 overlap dates and has 15.22 MPa mean absolute mismatch to the envelope median. This quantifies the RH boundary gate but does not activate RH as a likelihood term.

## Caveats

- Instrument reliability depends on RH range and niche state.
- Open-twin thermo-hygrometer data below 95% RH are preferred; closed-twin high-RH thermo-hygrometer data may be unreliable.
- RH7/RH8 low outliers should be filtered or flagged before numerical use.
- Psychrometer data are discussed in reports, but the copied numeric sheets here are the open-twin RH sheets from the November 2025 TeamBeam archive.
