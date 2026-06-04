# Taupe / TDR Measurement Information

This folder collects Taupe differential TDR measurement data, coordinates, borehole figures, and technical discussion material. In the CD-A email/slides, Taupe is treated as a water-content or saturation-related measurement stream.

## Copied Source Files

- [Taupe_WC.xlsx](source_files/Taupe_WC.xlsx) - Taupe water-content/proxy workbook extracted from the TeamBeam `003_Nov_2025.zip` archive.
- [003_Nov_2025.zip](source_files/003_Nov_2025.zip) - original multi-measurement TeamBeam archive containing the Taupe workbook and location figures.
- [Coordinates_NMR_Taupe_characborehole.xlsx](source_files/Coordinates_NMR_Taupe_characborehole.xlsx) - NMR/Taupe/characterization borehole coordinate table.
- [NMR_Taupe_Char_brg_1.png](source_files/NMR_Taupe_Char_brg_1.png), [NMR_Taupe_Char_brg_2.png](source_files/NMR_Taupe_Char_brg_2.png), [NMR_Taupe_Char_brg_3.png](source_files/NMR_Taupe_Char_brg_3.png) - borehole/location figures.
- [2604_TD_CD-A_ISU.pdf](source_files/2604_TD_CD-A_ISU.pdf) - April 2026 ISU technical discussion presentation with Taupe/TDR interpretation.
- [CD-A_Slides_TD_260427x.pdf](source_files/CD-A_Slides_TD_260427x.pdf) - April 2026 TD slides with broader measurement/modelling context.
- [VisualisationCDA.dat](source_files/VisualisationCDA.dat) - Tecplot layout file containing Taupe labels/geometry among other CD-A objects.

Original locations:

- [TeamBeam additional measurements archive](../../file_transfers/collected/2025-11-07_additional_measurements/003_Nov_2025.zip)
- [TeamBeam December CD-A data folder](../../file_transfers/collected/2025-12-03_cda_data)
- [Thunderbird-recovered TD presentation package](../../attachments/thunderbird_recovered/2026-05-11_Presentations_CD-A_TD_260428.zip)

Detailed file-level extraction from this pass is in
[derived_files/deep_source_pass/source_file_deep_summary.md](derived_files/deep_source_pass/source_file_deep_summary.md),
including Taupe workbook sheet summaries, searchable presentation text, Tecplot
file headers, and ZIP member checks.

## Workbook Contents

`Taupe_WC.xlsx` contains four sheets:

- `A3`
- `A4`
- `A7`
- `A8`

Each sheet has 212 data rows and covers the date range from 2019-12-01 to 2025-10-10. Columns include:

- `Datum`
- `MV EDZ 0-50`
- `MV EDZ 0-10`
- `MV EDZ 10-20`
- `MV EDZ 20-30`
- `MV EDZ 30-40`
- `MV EDZ 40-50`

The columns appear to summarize mean values over EDZ distance bands from the niche wall. The values are water-content/proxy values or apparent relative dielectric permittivity-related values rather than directly documented volumetric saturation.

Observed value ranges:

- `A3`: `MV EDZ 0-50` ranges 10.180355204899033 to 10.258827128946395; `MV EDZ 0-10` ranges 10.076536191930849 to 10.193064805758329; `MV EDZ 40-50` ranges 10.320521919658123 to 10.457128084040871.
- `A4`: `MV EDZ 0-50` ranges 10.219847562987436 to 10.266094941878563; `MV EDZ 0-10` ranges 10.170141415639051 to 10.287483828325001.
- `A7`: `MV EDZ 0-50` ranges 10.267565303610823 to 10.708115418764308; `MV EDZ 0-10` ranges 10.154201427210745 to 10.567156820315084; `MV EDZ 40-50` ranges 10.426096653161157 to 11.004376182086776.
- `A8`: `MV EDZ 0-50` ranges 9.974866232146457 to 10.21660016071013; `MV EDZ 0-10` ranges 9.87126613789583 to 10.169160816692315.

## Interpretation From Technical Discussion Material

The 2026 ISU presentation describes Taupe as differential TDR using TAUPE sensor cables.

Closed twin:

- No significant changes in ARDP over more than 6 years.
- Local increased ARDP is visible near horizontal/vertical boreholes.
- Closed horizontal EDZ is interpreted as narrow.
- Moderate ARDP is present in most parts.
- Medium ARDP around 40-110 cm depth is slightly increasing.
- Closed vertical EDZ is more pronounced.
- Medium ARDP occurs around 150 cm and near the borehole end.

Open twin:

- Major ARDP variations are attributed to meteorological effects.
- Variations are stronger in the horizontal direction.
- A significant reduction from the start of 2025 appears in most open-twin positions, with a noted exception around S7front.

Earlier modelling slides include the TDR/dielectric relation:

`epsilon_r = epsilon_rock * (1 - phi) + epsilon_w * phi * S_w`

where `epsilon_w` is approximately 80, `phi` is porosity, and `S_w` is water saturation.

## Modelling Relevance

Taupe/TDR is another saturation/water-content-related measurement stream. Its usefulness is different from ERT/NMR:

- It gives time-dependent behaviour along specific Taupe sensor cables or borehole sections.
- It appears sensitive to open-twin meteorological forcing.
- It may capture EDZ depth-band behaviour via the workbook's `0-10`, `10-20`, ..., `40-50` columns.
- It can help validate whether simulated saturation changes show correct relative behaviour between open and closed twins.

Possible modelling uses:

- Compare simulated saturation changes in EDZ depth bands against Taupe band time series.
- Use closed-twin stability as a qualitative validation target.
- Use open-twin seasonal amplitudes and reductions as a qualitative or semi-quantitative target.
- Use Taupe together with RH/suction and NMR to decide whether ERT-derived water-content changes are physically plausible.

## Model-Facing Operator Status

The SOTA/OGS workflow now contains a dedicated Taupe/TDR operator artifact:

- [taupe_tdr_trend_operator.csv](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/taupe_tdr_trend_operator.csv)
- [taupe_tdr_series_summary.csv](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/taupe_tdr_series_summary.csv)
- [taupe_tdr_observation_operator.md](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/taupe_tdr_observation_operator.md)
- [taupe_tdr_semantics.md](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/taupe_tdr_semantics.md)

The catalogue also keeps local copies of the Taupe/TDR semantics audit in
`derived_files/`:

- [taupe_tdr_semantics.md](derived_files/taupe_tdr_semantics.md)
- [taupe_tdr_semantics_summary.json](derived_files/taupe_tdr_semantics_summary.json)
- [taupe_tdr_semantics_row_audit.csv](derived_files/taupe_tdr_semantics_row_audit.csv)
- [taupe_tdr_semantics_series_audit.csv](derived_files/taupe_tdr_semantics_series_audit.csv)
- [taupe_tdr_semantics_group_summary.csv](derived_files/taupe_tdr_semantics_group_summary.csv)

It also keeps local copies of the cross-run candidate discrimination audit:

- [taupe_candidate_discrimination.md](derived_files/taupe_candidate_discrimination.md)
- [taupe_candidate_discrimination_summary.json](derived_files/taupe_candidate_discrimination_summary.json)
- [taupe_candidate_discrimination_audit.csv](derived_files/taupe_candidate_discrimination_audit.csv)
- [taupe_candidate_discrimination_series.csv](derived_files/taupe_candidate_discrimination_series.csv)

It also keeps local copies of the series/grouped-weight sensitivity audit:

- [taupe_series_weight_sensitivity.md](derived_files/taupe_series_weight_sensitivity.md)
- [taupe_series_weight_sensitivity_summary.json](derived_files/taupe_series_weight_sensitivity_summary.json)
- [taupe_series_weight_sensitivity_audit.csv](derived_files/taupe_series_weight_sensitivity_audit.csv)
- [taupe_series_weight_sensitivity_series.csv](derived_files/taupe_series_weight_sensitivity_series.csv)

The current operator uses baseline-normalized trends rather than absolute saturation. For each sensor and EDZ band, the first three finite workbook values define a baseline; later values are stored as raw differences, relative changes, and robust standardized anomalies. The intended model comparison is against the matching trend in band-averaged `theta_model = porosity * liquid_saturation`.

Current diagnostics:

- 5,088 Taupe rows and 24 sensor/EDZ-band time series are represented.
- A3 and A4 map into the current local OGS mesh support, giving 2,544 trend-ready rows.
- A7 and A8 are retained but flagged outside the current local mesh support.
- The run-local OGS trend diagnostic compares 1,860 mapped A3/A4 rows across 12 series for both the direct reference run and the current local-basis incumbent; 684 mapped rows fall outside the present OGS output time horizon.
- The direct-run standardized trend residual has MAE 1.8632. This is a candidate-screening diagnostic, not an active likelihood term.
- The cross-run candidate audit compares 74 executed runs with sampled OGS state outputs, including 66 runs with the full active combined objective.
- The Taupe standardized-trend MAE range across those runs is only 0.03687076560014302, so the current candidate family is a weak Taupe discriminator.
- The best Taupe-only run is `adaptive_combined_001_length_0p050m` with MAE 1.829884354078035; the best active-objective run is `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` with Taupe MAE 1.863211058631399.
- The series/grouped-weight audit compares 66 full active-objective runs over the 12 mapped A3/A4 series. Aggregate, equal-series, equal-sensor, equal-EDZ-band, and robust trimmed scores keep `adaptive_combined_001_length_0p050m` as the top trend-screen run, but A3-only and A4-only scores pick different winners and the 12 series have 8 distinct best runs.
- The semantics audit classifies those rows explicitly: 2,544 A3/A4 rows are trend-diagnostic-ready after OGS state outputs, and 2,544 A7/A8 rows are excluded from the current mesh support.
- The combined state-target table has 5,088 Taupe/TDR rows and 0 active absolute Taupe state residuals in the current candidate objective.
- Treating the workbook value as volumetric water-content percent gives physical mapped-band saturation for 2,120 rows.
- Treating the value as a generic Topp dielectric permittivity gives physical mapped-band saturation for 0 rows.
- The local linear dielectric mixing formula with `epsilon_rock = 6` gives physical mapped-band saturation for 2,544 rows.

These counts are sanity checks, not a calibration decision. Absolute Taupe residual weights still require confirmation of whether `Taupe_WC.xlsx` contains calibrated volumetric water-content percent, apparent relative dielectric permittivity, or another ARDP-derived proxy.

## Caveats

- The workbook does not by itself document the exact physical unit of every Taupe column. Treat the numbers as Taupe-derived water-content/proxy values until the instrument-specific conversion is confirmed.
- ARDP terminology in the slides should be mapped carefully to the workbook quantities before numerical inversion.
- Sensor positions and borehole labels must be connected through the coordinate workbook and figures before comparison with OGS cells or mesh regions.
