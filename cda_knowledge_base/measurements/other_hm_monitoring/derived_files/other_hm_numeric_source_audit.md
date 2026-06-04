# Other HM Numeric Source Audit

This audit scans the current other-HM source bundle for hard-residual-ready numeric exports.
It separates source evidence and support geometry from time-series/statistical products that can actually be weighted in a likelihood.

## Status

- Status: `other_hm_numeric_source_audit_complete_hard_residual_exports_missing`
- Request rows audited: 6
- Hard-residual-ready requests: 0
- Requests with local support geometry or extracted labels: 6
- Partial numeric slide-summary requests: 1
- Geometry-only requests: 1
- Text evidence hits retained: 82
- Remaining blocker: Local source scan found layout geometry, laser surface geometry, extracted levelling slide rows, and report/minute evidence, but no hard-residual-ready Geoscope time series, laser statistical interpretation product, or full levelling survey table.

## Source Bundle

- Source files scanned: 10
- ZIP members scanned: 7
- ZIP numeric-candidate members: 0
- Source extension counts: `{'.dat': 1, '.pdf': 5, '.pptx': 3, '.zip': 1}`
- ZIP member extension counts: `{'.pdf': 7}`

## Request Audit

| Request | Local support | Local numeric/geometry rows | Text hits | Status | Action |
| --- | ---: | ---: | ---: | --- | --- |
| `geoscope_mini_piezometer_time_series` | 1 | 0 | 16 | support_or_text_evidence_only_numeric_time_series_missing | The catalogue contains layout support and report/minute evidence, but no hard-residual-ready numeric time-series export with units, timestamps, reference conventions, and quality flags. |
| `geoscope_extensometer_time_series` | 5 | 0 | 21 | support_or_text_evidence_only_numeric_time_series_missing | The catalogue contains layout support and report/minute evidence, but no hard-residual-ready numeric time-series export with units, timestamps, reference conventions, and quality flags. |
| `geoscope_crackmeter_time_series` | 22 | 0 | 7 | support_or_text_evidence_only_numeric_time_series_missing | The catalogue contains layout support and report/minute evidence, but no hard-residual-ready numeric time-series export with units, timestamps, reference conventions, and quality flags. |
| `laser_scan_statistical_interpretation_2026_04_20` | 2 | 2727958 | 11 | support_geometry_only_statistical_export_missing | VisualisationCDA.dat contains open/closed laser-scan surface geometry, but no dated displacement/statistical interpretation product or registration uncertainty file is present. |
| `precision_levelling_full_survey_table` | 12 | 12 | 15 | partial_slide_summary_only | Use the extracted 12-row levelling summary only as a sign/order-of-magnitude validation target until the full survey table, covariance/reference frame, and all epochs are provided. |
| `geoscope_boundary_and_auxiliary_context` | 7 | 0 | 12 | support_or_text_evidence_only_numeric_time_series_missing | The catalogue contains layout support and report/minute evidence, but no hard-residual-ready numeric time-series export with units, timestamps, reference conventions, and quality flags. |

## Representative Text Evidence

| Request | Source text | Line | Keywords | Snippet |
| --- | --- | ---: | --- | --- |
| `geoscope_mini_piezometer_time_series` | 2024-12-19_Input_HERMES_BGR_20241217_a3a7ba63.pdf.txt | 229 | piezometer | water content, pore  water pressures, crack width, etc. There exist pointwise measurements (as piezometer, extensometer) and two -dimensional measurements, as |
| `geoscope_mini_piezometer_time_series` | 2026-05-11_TD517_CD-A_260507__Minutes_382ada29.pdf.txt | 102 | mini-piezometer; piezometer | Geoscope (relative humidity, temperature, opening times of door, extensometer, Mini-Piezometer, crackmeter, suction measurements) plus Laser scans with statistical |
| `geoscope_mini_piezometer_time_series` | 2026-05-11_TD517_CD-A_260507__Minutes_382ada29.pdf.txt | 113 | BCD-A28; BCD-A31; mini-piezometer; piezometer | September 2025 – next steps? • Mini-Piezometers BCD-A28 to BCD-A31 are working well • Crackmeter indicate ongoing trend in closed niche (1 |
| `geoscope_mini_piezometer_time_series` | 2026-05-11_TD517_CD-A_260507__Minutes_382ada29.pdf.txt | 341 | pore pressure | model. Finally targets to compare with extensometer and pore pressure measurement data. |
| `geoscope_extensometer_time_series` | 2024-12-19_Input_HERMES_BGR_20241217_a3a7ba63.pdf.txt | 230 | extensometer | There exist pointwise measurements (as piezometer, extensometer) and two -dimensional measurements, as ERT, TDR and laser scans. Especially for the water content |
| `geoscope_extensometer_time_series` | 2024-12-19_Input_HERMES_BGR_20241217_a3a7ba63.pdf.txt | 321 | strain | that not all targets can be achieved in the planned time. This could be caused by capacity constraints, especially in t erms of personnel. The proposed development of strategies for near field effects is based on the existence |
| `geoscope_extensometer_time_series` | 2026-05-11_TD517_CD-A_260507__Minutes_382ada29.pdf.txt | 102 | extensometer | Geoscope (relative humidity, temperature, opening times of door, extensometer, Mini-Piezometer, crackmeter, suction measurements) plus Laser scans with statistical |
| `geoscope_extensometer_time_series` | 2026-05-11_TD517_CD-A_260507__Minutes_382ada29.pdf.txt | 110 | extensometer; extensometers | and low RH during the winter 25/26 • Data failure of horizontal and vertical extensometers (BCD-A9 and BCD-A10) in the closed niche since |
| `geoscope_crackmeter_time_series` | 2024-12-19_Input_HERMES_BGR_20241217_a3a7ba63.pdf.txt | 228 | crack width | term, ongoing measurements on deformation, humidity, water content, pore  water pressures, crack width, etc. There exist pointwise measurements (as piezometer, |
| `geoscope_crackmeter_time_series` | 2026-05-11_TD517_CD-A_260507__Minutes_382ada29.pdf.txt | 102 | crackmeter | Geoscope (relative humidity, temperature, opening times of door, extensometer, Mini-Piezometer, crackmeter, suction measurements) plus Laser scans with statistical |
| `geoscope_crackmeter_time_series` | 2026-05-11_TD517_CD-A_260507__Minutes_382ada29.pdf.txt | 114 | crackmeter | • Mini-Piezometers BCD-A28 to BCD-A31 are working well • Crackmeter indicate ongoing trend in closed niche (1 measuring point) and seasonal variation in open niche |
| `geoscope_crackmeter_time_series` | 2026-05-11_TD517_CD-A_260507__Minutes_382ada29.pdf.txt | 357 | crackmeter | (extensometer, pore pressure, suction, …). The crackmeter measurements at one position in the CT indicate ongoing closure of the crack. Possible |
| `laser_scan_statistical_interpretation_2026_04_20` | 2024-12-19_Input_HERMES_BGR_20241217_a3a7ba63.pdf.txt | 231 | laser scan; laser scans | extensometer) and two -dimensional measurements, as ERT, TDR and laser scans. Especially for the water content evolution different results from different measurement |
| `laser_scan_statistical_interpretation_2026_04_20` | 2026-05-11_TD517_CD-A_260507__Minutes_382ada29.pdf.txt | 68 | laser scan; laser scans | Update of measurements (Geoscope and laser scans) has been sent (20.04.26) |
| `laser_scan_statistical_interpretation_2026_04_20` | 2026-05-11_TD517_CD-A_260507__Minutes_382ada29.pdf.txt | 103 | laser scan; laser scans | of door, extensometer, Mini-Piezometer, crackmeter, suction measurements) plus Laser scans with statistical interpretation has been sent to all partners (Mail sent by |
| `laser_scan_statistical_interpretation_2026_04_20` | 2026-05-11_TD517_CD-A_260507__Minutes_382ada29.pdf.txt | 224 | laser scan; laser scanning | • Measurements over a longer time period • Direct comparison with laser scanning measurements |
| `precision_levelling_full_survey_table` | 2026-05-11_TD517_CD-A_260507__Minutes_382ada29.pdf.txt | 76 | levelling | 3. Taupe (Franz) 4. Levelling (Sebastian, Senecio, today: Gesa) 5. Suction (Susana, Jose Luis, today: Gesa) |
| `precision_levelling_full_survey_table` | 2026-05-11_TD517_CD-A_260507__Minutes_382ada29.pdf.txt | 203 | levelling | 4. Levelling |
| `precision_levelling_full_survey_table` | 2026-05-11_TD517_CD-A_260507__Minutes_382ada29.pdf.txt | 208 | levelling; precision levelling | Precision Levelling Twin Niches Summary: Detectable displacement: from 0.1 to 0.2 mm |
| `precision_levelling_full_survey_table` | 2026-05-11_TD517_CD-A_260507__Minutes_382ada29.pdf.txt | 209 | detectable displacement | Precision Levelling Twin Niches Summary: Detectable displacement: from 0.1 to 0.2 mm (depending on the point; Confidence level 95%) |
| `geoscope_boundary_and_auxiliary_context` | 2026-05-11_TD517_CD-A_260507__Minutes_382ada29.pdf.txt | 77 | suction | 4. Levelling (Sebastian, Senecio, today: Gesa) 5. Suction (Susana, Jose Luis, today: Gesa) 6. Hannover Meeting focusing on measuring techniques |
| `geoscope_boundary_and_auxiliary_context` | 2026-05-11_TD517_CD-A_260507__Minutes_382ada29.pdf.txt | 94 | suction | Stephan, Franz, Sebastian, Shuang) as well as the current report on suction measurements (Susana) are send by mail (11.05.26). |
| `geoscope_boundary_and_auxiliary_context` | 2026-05-11_TD517_CD-A_260507__Minutes_382ada29.pdf.txt | 101 | opening times; relative humidity; temperature | • An update of all measurements that are handled via Geoscope (relative humidity, temperature, opening times of door, extensometer, Mini-Piezometer, crackmeter, |
| `geoscope_boundary_and_auxiliary_context` | 2026-05-11_TD517_CD-A_260507__Minutes_382ada29.pdf.txt | 102 | door | Geoscope (relative humidity, temperature, opening times of door, extensometer, Mini-Piezometer, crackmeter, suction measurements) plus Laser scans with statistical |

## Interpretation

The local catalogue is useful for HM validation but not yet for hard HM likelihood terms.
For mini-piezometers, extensometers, crackmeters, laser scans, and auxiliary boundary logs, the available material is support geometry plus report/minute evidence.
The laser-scan surface zones in `VisualisationCDA.dat` are geometry/support data; they are not the dated statistical scan-difference products mentioned in the minutes.
The levelling slide table is the only extracted numeric deformation summary, but it lacks all campaign epochs, covariance/reference-frame metadata, and point coordinates needed for weighted residuals.
