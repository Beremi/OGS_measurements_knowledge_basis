# Permeability Pulse-Test Measurement Information

This folder collects permeability and transmissibility information from pulse tests around the CD-A niches, including 2021, 2024, and 2025 workbook material plus method references.

## Copied Source Files

- [2025-09-05_CD-A_Permeability.xlsx](source_files/2025-09-05_CD-A_Permeability.xlsx) - permeability workbook shared in the September 2025 HERMES thread.
- [Permeability_CDA_all_2025.xlsx](source_files/Permeability_CDA_all_2025.xlsx) - TeamBeam workbook with consolidated 2021/2024 permeability data.
- [2025-09-05_CD-A_for_hermes_2D_250904x.pdf](source_files/2025-09-05_CD-A_for_hermes_2D_250904x.pdf) - slides with permeability pulse-test method and modelling-domain questions.
- [2025-09-05_Ziefle_et_al_2023_Characterization.pdf](source_files/2025-09-05_Ziefle_et_al_2023_Characterization.pdf) - characterization paper shared by email.
- [Perm_Sec_4-3_Ziefle_et_al_2023_Characterization.pdf](source_files/Perm_Sec_4-3_Ziefle_et_al_2023_Characterization.pdf) - same or related characterization paper from TeamBeam.

Original locations:

- [Gmail permeability attachments](../../attachments)
- [TeamBeam December CD-A data folder](../../file_transfers/collected/2025-12-03_cda_data)

Detailed file-level extraction from this pass is in
[derived_files/deep_source_pass/source_file_deep_summary.md](derived_files/deep_source_pass/source_file_deep_summary.md),
including workbook sheet/range summaries for the permeability workbooks and
searchable text from the permeability PDFs.

## Workbook Contents

`2025-09-05_CD-A_Permeability.xlsx` contains sheets including:

- `2024_OT`
- `2024_CT`
- `2021_BCDA27_19`
- `Messdaten_BCDA26`
- `Messdaten_BCDA27`

The workbook combines interpreted permeability/transmissibility values with raw or normalized interval pressure-time data. Sheet names and column blocks distinguish open/closed twin, campaign year, borehole, and measurement interval.

`Permeability_CDA_all_2025.xlsx` contains consolidated 2021 and 2024 sheets:

- `2021`: includes BCDA_24 vertical and BCDA_25 horizontal data.
- `2024`: includes BCDA_32 horizontal and BCDA_33 vertical data.
- Depth values are given at interval positions such as 0.15, 0.25, 0.35 m, etc.
- Positive numerical values include permeability and transmissibility terms. Interpreted permeability values span roughly from very low values near 1e-20 m2 up to high near-field values around 1e-13 m2 depending on interval and campaign.
- The 2024 horizontal data include a high value around 8e-13 at depth 0.87 m.
- The 2024 vertical data include values such as around 8e-15 at depth 0.55 m.

## Measurement Method Notes

The September 2025 slides describe the pulse-test method:

- Modified COMDRILL double-piston packer.
- 10 cm test interval.
- Nitrogen injection up to 1 bar.
- Pressure evolution monitored after injection.
- The result is an intrinsic permeability estimate for a 3D volume around a 10 cm long borehole interval.
- Maximum error from experimental and evaluation sources is about half an order of magnitude.
- Two measurements in each direction were made at each 10 cm interval.
- Measurements are available about 1.5 years after excavation/installation in 2021 and about 4.5 years after excavation/installation in 2024.

The February 2025 slides summarize the open/closed contrast:

- Open twin permeability is approximately 1e-15 m2.
- Closed twin permeability is approximately 1e-19 m2.
- The difference is clearer in the vertical direction.
- The difference becomes more evident over time.
- Significant differences are visible up to about 1.5 m from the niche.

## Modelling Relevance

Permeability pulse tests are direct constraints on a material parameter rather than a process state. The discussion with Gesa highlights:

- Bedding controls anisotropy.
- The near field is affected by the EDZ.
- Permeability may evolve or self-heal over time, but the advised starting point is to begin without time dependency.
- Subdomain definition is a modelling question: rings around the niche, segmentation, and constant scalar permeability within subdomains were discussed.
- A natural first inverse-problem setup is to treat permeability as the parameter being inferred while keeping other OGS inputs fixed or separately verified.

Possible modelling use:

- Build radial or borehole-interval-based permeability zones around the niche.
- Compare 2021 and 2024 as early and later EDZ states.
- Use open/closed twin contrast as a calibration or validation target.
- Treat vertical/horizontal differences as evidence of anisotropy related to bedding and EDZ.

Derived model-facing artifacts in the OGS report workspace:

- [permeability_interpreted_values.csv](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/permeability_interpreted_values.csv) normalizes 204 interpreted workbook rows.
- [permeability_observation_targets.csv](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/permeability_observation_targets.csv) maps rows with labelled borehole geometry to first-pass interval targets.
- [permeability_missing_geometry_audit.md](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/permeability_missing_geometry_audit.md) groups the 98 interpreted rows that have orientation evidence but cannot yet be projected to OGS cells.
- [permeability_endpoint_geometry_request.md](derived_files/permeability_endpoint_geometry_request.md) is the email-ready request for the five missing historical endpoint traces.
- [permeability_endpoint_geometry_request.csv](derived_files/permeability_endpoint_geometry_request.csv) lists the requested endpoints and activation metadata for BCD-A24, BCD-A25, BCD-A26, BCD-A27, and BFM-D19.
- [permeability_endpoint_geometry_blocked_rows.csv](derived_files/permeability_endpoint_geometry_blocked_rows.csv) lists all 98 blocked interpreted rows with source workbook row references.
- [permeability_endpoint_geometry_request_summary.json](derived_files/permeability_endpoint_geometry_request_summary.json) is the machine-readable summary of the endpoint request package.
- [permeability_measurement_semantics.md](derived_files/permeability_measurement_semantics.md) records the gas-pulse/scalar-to-tensor interpretation gate for every interpreted row.
- [permeability_measurement_semantics_summary.json](derived_files/permeability_measurement_semantics_summary.json) is the machine-readable version of the same audit.
- [permeability_measurement_semantics_audit.csv](derived_files/permeability_measurement_semantics_audit.csv) is the row-level audit.
- [permeability_measurement_semantics_group_summary.csv](derived_files/permeability_measurement_semantics_group_summary.csv) summarizes status, segment, source-sheet, and campaign/orientation coverage.

The missing-geometry audit keeps the historical BCD-A24/25/26/27 and BFM-D19 rows visible. BCD-A24 and BCD-A26 are retained as vertical, BCD-A25 and BCD-A27 as horizontal, and BFM-D19 as nearly horizontal evapometer data, but none of these rows is activated as an interval target until labelled endpoint geometry or an approved digitized trace is available.

The endpoint request package makes that follow-up explicit. It asks for start/collar
and end/tip coordinates, the coordinate frame, depth-zero reference, along-borehole
direction, interval-position convention, and uncertainty for each missing trace. The
collected workbooks and characterization paper provide the measurement values and
orientation evidence, but not a label-resolved coordinate table for these five traces.

The semantics audit currently records 204 interpreted rows, 200 positive interpreted
permeability rows, 75 active direct candidates, 27 rows outside the current mesh, and
98 rows blocked by missing endpoint geometry.  The active rows are treated as nitrogen
pulse-decay scalar interval observations of intrinsic permeability.  They are not
hydraulic conductivity, liquid relative permeability, saturation, or direct tensor
components; the OGS comparison is a log-space directional/interval response of the
intrinsic permeability tensor.

## Caveats

- The measurement volume is a local 3D volume around a 10 cm borehole interval, not a direct cell-wise model parameter.
- Nitrogen gas-pulse values require gas-test/slippage interpretation before they can be treated as liquid-equivalent intrinsic permeability.
- Workbook columns mix interpreted values and raw pressure/time data; confirm column semantics before automated import.
- Experimental/evaluation uncertainty is non-trivial, about half an order of magnitude.
- Time dependency is observed conceptually, but Gesa suggested starting without time-dependent permeability.
- For BCD-A24/25/26/27 and BFM-D19, the current source set supplies orientation evidence but not labelled start/end geometry in the local OGS frame.
