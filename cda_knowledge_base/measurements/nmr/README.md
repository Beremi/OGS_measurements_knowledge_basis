# NMR Measurement Information

NMR here means nuclear magnetic resonance measurements used to estimate water content in and around the CD-A niches. The archive contains weekly monitoring tables, seasonal campaign data, figures, positions, and interpretation slides.

## Copied Source Files

- [2025-09-15_Weekly_2021-2022_at_4S.dat](source_files/2025-09-15_Weekly_2021-2022_at_4S.dat) - weekly NMR water-content data at 4S.
- [2025-09-15_Weekly_2022-2025_at_4E.dat](source_files/2025-09-15_Weekly_2022-2025_at_4E.dat) - weekly NMR water-content data at 4E.
- [2025-09-15_4S-4E-NMRmonitoring_until_Sep2025.png](source_files/2025-09-15_4S-4E-NMRmonitoring_until_Sep2025.png) - plot of 4S/4E monitoring through September 2025.
- [2025-09-15_saisonally.zip](source_files/2025-09-15_saisonally.zip) - seasonal NMR campaign archive recovered from Thunderbird.
- [seasonal_nmr/](source_files/seasonal_nmr) - extracted copy of the seasonal NMR archive.
- [003_Nov_2025.zip](source_files/003_Nov_2025.zip) - original multi-measurement TeamBeam archive containing the coordinate/borehole material used here.
- [2025-09-05_NMR2025.pdf](source_files/2025-09-05_NMR2025.pdf) - NMR 2025 presentation.
- [NMR2026.pdf](source_files/NMR2026.pdf) - NMR 2026 presentation from the TD package.
- [2025-08-25_NMR_meas.png](source_files/2025-08-25_NMR_meas.png) - NMR measurement figure.
- [Coordinates_NMR_Taupe_characborehole.xlsx](source_files/Coordinates_NMR_Taupe_characborehole.xlsx) - NMR/Taupe/characterization borehole coordinate table.
- [CD-A_Slides_TD_260427x.pdf](source_files/CD-A_Slides_TD_260427x.pdf) - TD slides with cross-measurement interpretation.

## Derived Analysis Files

These are generated from the copied source files and the current OGS/inversion
workflow.  Keep the files below as orientation products; the original data remain in
`source_files/`.

- [nmr_bound_water_sensitivity.md](derived_files/nmr_bound_water_sensitivity.md) - detailed bound/interlayer-water activation audit for using NMR against OGS water content.
- [nmr_bound_water_sensitivity_summary.json](derived_files/nmr_bound_water_sensitivity_summary.json) - machine-readable summary of the same audit.
- [nmr_bound_water_target_audit.csv](derived_files/nmr_bound_water_target_audit.csv) - row-level NMR target audit with fixed-porosity exceedance and required offset columns.
- [nmr_bound_water_offset_scenarios.csv](derived_files/nmr_bound_water_offset_scenarios.csv) - tested uniform bound-water/free-water subtraction scenarios.
- [nmr_bound_water_group_offsets.csv](derived_files/nmr_bound_water_group_offsets.csv) - mapping-label/group summaries for high-offset NMR positions.
- [nmr_candidate_bias_sensitivity.md](derived_files/nmr_candidate_bias_sensitivity.md) - cross-run candidate ranking audit under NMR bound-water/bias-safe diagnostics.
- [nmr_candidate_bias_sensitivity_summary.json](derived_files/nmr_candidate_bias_sensitivity_summary.json) - machine-readable summary of the candidate bias/anomaly audit.
- [nmr_candidate_bias_sensitivity_audit.csv](derived_files/nmr_candidate_bias_sensitivity_audit.csv) - run-level NMR candidate bias/anomaly sensitivity table.
- [nmr_candidate_bias_sensitivity_offsets.csv](derived_files/nmr_candidate_bias_sensitivity_offsets.csv) - uniform-offset candidate ranking stress test.
- [nmr_candidate_bias_sensitivity_label_biases.csv](derived_files/nmr_candidate_bias_sensitivity_label_biases.csv) - fitted per-label bias diagnostics for each executed run.
- [nmr_objective_decision.md](derived_files/nmr_objective_decision.md) - provisional decision package recommending within-label trend/anomaly residuals as the first final NMR likelihood candidate.
- [nmr_objective_decision.csv](derived_files/nmr_objective_decision.csv) - machine-readable comparison of raw absolute, global-offset, label-bias, and trend/anomaly NMR objective options.
- [nmr_objective_decision_summary.json](derived_files/nmr_objective_decision_summary.json) - machine-readable summary of the provisional NMR objective recommendation.
- [nmr_trend_anomaly_active_objective.md](derived_files/nmr_trend_anomaly_active_objective.md) - executable provisional ranking produced by the objective assembler's NMR trend/anomaly mode.
- [nmr_trend_anomaly_active_objective_ranking.csv](derived_files/nmr_trend_anomaly_active_objective_ranking.csv) - run-level ranking under the executable direct-permeability plus NMR trend/anomaly objective.
- [nmr_trend_anomaly_active_objective_summary.json](derived_files/nmr_trend_anomaly_active_objective_summary.json) - machine-readable summary and validation of the executable trend/anomaly objective path.
- [nmr_final_residual_policy_gate.md](derived_files/nmr_final_residual_policy_gate.md) - final-policy gate separating the current raw-NMR default from the preferred provisional trend/anomaly policy.
- [nmr_final_residual_policy_gate.csv](derived_files/nmr_final_residual_policy_gate.csv) - machine-readable gate rows for current default, promoted trend/anomaly option, no-new-batch recommendation, and final-promotion dependency.
- [nmr_final_residual_policy_gate_summary.json](derived_files/nmr_final_residual_policy_gate_summary.json) - machine-readable summary of the final NMR policy gate.
- [nmr_final_residual_policy_acceptance_record_template.md](derived_files/nmr_final_residual_policy_acceptance_record_template.md) - fillable signoff guardrail for selecting exactly one final NMR residual policy.
- [nmr_final_residual_policy_acceptance_record_template.csv](derived_files/nmr_final_residual_policy_acceptance_record_template.csv) - machine-readable template rows for raw absolute, global-offset, label-bias, and trend/anomaly policies.
- [nmr_final_residual_policy_acceptance_record_template_summary.json](derived_files/nmr_final_residual_policy_acceptance_record_template_summary.json) - machine-readable summary of the NMR policy acceptance template.

Original locations:

- [Gmail NMR attachments](../../attachments)
- [Thunderbird-recovered seasonal NMR archive](../../attachments/thunderbird_recovered/2025-09-15_saisonally.zip)
- [Thunderbird-recovered TD presentation package](../../attachments/thunderbird_recovered/2026-05-11_Presentations_CD-A_TD_260428.zip)
- [TeamBeam additional measurements archive](../../file_transfers/collected/2025-11-07_additional_measurements/003_Nov_2025.zip)

Detailed file-level extraction from this pass is in
[derived_files/deep_source_pass/source_file_deep_summary.md](derived_files/deep_source_pass/source_file_deep_summary.md),
including searchable text from the NMR PDFs, seasonal `.dat` headers, workbook
outlines, and ZIP member checks.

## Weekly Monitoring Tables

Both weekly `.dat` files are comma-separated tables. They contain dates and NMR-derived water-content values plus confidence information and relaxation-time information.

`2025-09-15_Weekly_2021-2022_at_4S.dat`:

- 21 rows.
- Time range: `12-Okt-2021 23:10:20` to `20-Mrz-2022 00:00:34`.
- Water content range: 9.89727386792565 to 13.1692156631058 vol%.
- 95% confidence interval range: 0.356484295144263 to 0.606629869220532.
- T2 range: 0.478565509888136 to 0.622418803418794 ms.

`2025-09-15_Weekly_2022-2025_at_4E.dat`:

- 149 rows.
- Time range: `06-Okt-2021 09:35:30` to `09-Sep-2025 11:24:25`.
- Water content range: 8.5093422098135 to 12.2289643335788 vol%.
- 95% confidence interval range: 0.328202047679996 to 1.52169349213518.
- T2 range: 0.470022283127565 to 0.667363367048101 ms.

Stephan Costabel's email caveats for these monitoring tables:

- Columns 4 and 5 can be ignored for modelling.
- Gaps are due to technical failures.
- From February to April 2025, the device was detuned to a wrong frequency and likely overestimated water content by about 1 vol%.
- Seasonal measurements before autumn 2021 are only floor/ceiling measurements.
- September 2020 has floor only.
- Winter 2024 is missing.

## Seasonal NMR Archive

The seasonal archive contains:

- 47 ZIP entries.
- 44 files and 3 directories.
- 22 `.dat` data files and 22 figures.
- Approx. 1.1 MB uncompressed.
- Dates and file names cover Niche 3 and Niche 4 seasonal measurement campaigns from 2019 through 2025.

The seasonal `.dat` tables use columns including:

- `Position`
- `Vol.Wat.Content[%]`
- `WC-95%Conf.Int.`

Use the extracted folder [source_files/seasonal_nmr](source_files/seasonal_nmr) when browsing the seasonal campaign files; keep the ZIP as the raw archive reference.

## Information Extracted From Presentations

`NMR2025.pdf` discusses:

- Weekly monitoring in the open niche.
- Comparison to relative humidity.
- Seasonal measurements and correlation with ERT.
- Ongoing/further laboratory experiments.
- The unresolved question of interlayer water and how it affects NMR interpretation.

`NMR2026.pdf` adds:

- Laboratory analysis on clay powders.
- Cut-off values for interlayer water around 0.5 to 0.6 ms.
- Natural Opalinus Clay can show bimodal response.
- Quantification of interlayer water is challenging.
- Seasonal NMR measurements are compared with ERT in the presentation pages.

The September 2025 HERMES slides explicitly say NMR can be included in the inverse problem. The motivation is that NMR is sparse, but it measures water content more directly than ERT plus an Archie conversion. It can therefore anchor or validate ERT-derived water-content fields.

## Modelling Relevance

NMR is the most direct water-content measurement in this local dataset. It is especially useful for:

- Anchoring ERT-derived water content.
- Checking whether ERT apparent noise comes from the resistivity-water-content conversion, homogenization, or real spatial variability.
- Providing point/line time series for selected measurement positions.
- Supporting calibration of saturation or water-content state variables in the near field.

NMR should not simply be treated as a dense spatial field. It is sparse, position-dependent, and campaign-dependent. The coordinate file must be used to place each NMR measurement into the model geometry.

## OGS Water-Content Activation Decision

The current OGS proxy for mobile water content is `theta_model = porosity *
liquid_saturation`.  The current model porosity is fixed at 0.105, so saturated cells
cannot exceed `theta_model = 0.105`.

The generated bound-water audit shows:

- 464 total NMR target rows: 170 weekly rows plus 294 seasonal rows.
- 287 rows are usable in the current Niche-4 mapped target set.
- 315 of all 464 NMR target rows exceed fixed porosity if treated as mobile water without correction.
- 162 of the 287 currently usable mapped rows exceed fixed porosity before correction.
- For usable rows, the required positive offset has p50 = 0.0019, p75 = 0.0108, p90 = 0.0259, p95 = 0.0402, and max = 0.1231.
- A tested uniform subtraction of 0.05 gives the highest simple physical-row count for the usable rows, but still leaves 7 nonphysical usable rows.
- The 66-run candidate bias/anomaly audit shows that this caveat changes the diagnostic ranking: the raw absolute-theta objective is led by `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000`, while per-label bias and within-label anomaly diagnostics are led by `broad_continuous_001_003_length_0p021m`.
- The best bias/anomaly diagnostic combined objective is 505.614305828437, and the current-vs-label-bias rank correlation is 0.6351529067946979.

Consequence for modelling: do not activate a naive absolute residual
`theta_model - theta_NMR_obs` against raw NMR water content.  The first safer
OGS-backed use is a within-position trend/anomaly residual.  The generated
`nmr_objective_decision` package formalizes that as the provisional recommendation:
use within-label centered anomalies for the first final NMR likelihood, keep the
current raw absolute-theta objective conditional, and reject a single global NMR
offset unless collaborators provide a physical justification.  If absolute residuals
are required, include a label/campaign bias term or an explicit bound/interlayer-water
model-error floor, and treat the current raw-NMR permeability ranking as conditional.
The implementation path now exists in the OGS inversion workflow as
`assemble_inversion_objective.py --state-objective-mode nmr_within_label_trend_anomaly`;
the generated executable ranking validates against the diagnostic audit to numerical
roundoff and preserves the same trend/anomaly winner
`broad_continuous_001_003_length_0p021m`. Promotion to the default reporting/search
objective is still a modelling decision. The generated final residual-policy gate
keeps raw absolute theta as the current-report default with caveats, records
within-label trend/anomaly as the preferred provisional final-policy candidate, and
recommends no new OGS batch for the promoted-NMR mode before that policy is accepted.
The generated acceptance-record template currently records 0/1 primary approvals,
is not ready to apply, records no actual decision, changes no active objective,
promotes no field, and recommends no new OGS batch.

## Caveats

- Weekly and seasonal datasets are not equivalent. Do not merge them without checking measurement position, campaign mode, and date.
- The 4E weekly table has a known February-April 2025 overestimation issue.
- Older seasonal campaigns have incomplete spatial coverage.
- T2/interlayer-water interpretation remains an uncertainty, especially for translating NMR signal into total/free water content.
