# Measurement Likelihood And Activation Model

This file records how each measurement stream should enter the inversion objective.
It is deliberately stricter than a data inventory: a row can be present and mapped
but still inactive if the measurement physics, support, or uncertainty model is not
defensible yet.

- Measurement streams: 7
- Streams active in the objective now: 2
- Total current objective rows: 267
- Current candidate total active objective: 3159.6643814648755

| Stream | Activation state | Residual / transform | Scale / weighting | Activation gate |
| --- | --- | --- | --- | --- |
| permeability_pulse_tests | active_direct_parameter_likelihood | log10(k_pred_m2) - log10(k_obs_m2); Gaussian residual in log10 permeability space | current evaluator uses sigma = 0.5 log10 units; this is an intentionally broad first-pass scale; robust-tail and support-cell aggregation alternatives are diagnostic only unless explicitly approved; duplicates with same campaign, segment, depth and observed log10(k) share unit weight; support-cell repeated/conflicting rows are now audited separately by the likelihood-policy diagnostic | already active for rows with positive interpreted k and inside-mesh interval mapping |
| NMR weekly and seasonal water content | active_state_likelihood_from_sampled_ogs_outputs | theta_model - theta_NMR_obs; Gaussian residual in volumetric water-content fraction after bias treatment | row sigma from reported 95 percent confidence interval with 0.01 fraction floor; absolute-residual activation must include the generated bound-water/bias audit, with usable-row required-offset p95=0.0402; one point target per dated NMR row; seasonal Niche 3 rows stay outside current Niche 4 fit | requires sampled OGS state outputs and the generated bound-water sensitivity audit; prefer trend/anomaly residuals before absolute theta residuals |
| ERT open-niche resistivity field | resistivity_diagnostic_evaluated_transform_support_unconfirmed | log10(rho_pred) - log10(rho_ERT_inverted); multiplicative/log-resistivity residual; no active sigma yet | defer numerical sigma until ERT-to-OGS transform, support mask, and inversion-field uncertainty are confirmed; support-sensitivity ranks are diagnostic only; future weights should aggregate ERT cells by support/time to avoid treating correlated pixels as independent | Confirm ERT-to-OGS coordinate transform, exact near-niche support mask, and ERT inversion uncertainty/correlation before activation. |
| Taupe/TDR EDZ bands | trend_diagnostic_evaluated_pending_absolute_calibration | model trend anomaly - observed Taupe/TDR anomaly; within-series trend diagnostic; absolute saturation residual inactive | no absolute sigma assigned; future trend sigma should be estimated per sensor/band after unit calibration; grouped-weight sensitivity remains diagnostic; aggregate by sensor, EDZ band, and time; A7/A8 remain outside current mesh support | Confirm whether Taupe_WC workbook values are calibrated volumetric water-content percent, apparent relative dielectric permittivity, or another ARDP-derived proxy before assigning absolute saturation or water-content residual weights. |
| suction/relative humidity | boundary_forcing_audit_not_point_likelihood | active OGS boundary curve - RH-derived Kelvin pressure; boundary provenance audit; not a cell residual in current objective | no point-residual sigma assigned; sensor reliability split must enter any future curve-fit likelihood; filter invalid/low-RH outliers; keep high-RH open-twin caution flag | Obtain or reconstruct the generation history for 08_08_open_niche_seasonal.xml before treating the active open-niche pressure curve as verified RH-derived forcing or using RH as a retention-parameter likelihood. |
| other HM monitoring and levelling | qualitative_validation_layer_numeric_series_missing | not yet a numerical residual except future levelling/geoscope series comparisons; validation gates before hard likelihood | no hard sigma assigned until Geoscope/laser-scan/extensometer time series are located; avoid hard weighting of qualitative statements; use as rejection/diagnostic gates | Numeric Geoscope and laser-scan exports are still absent from the catalogue; the request package states exactly what is needed before hard pressure/deformation residuals can be assigned. |
| coordinates, borehole geometry, and bedding | support_and_prior_layer | not a likelihood term; support/prior metadata | not applicable; propagate mapping status to downstream measurement residuals | continue using as required support; add endpoint geometry for older permeability rows |

## Stream Details

### permeability_pulse_tests

- Candidate rows: 204
- Usable or mapped rows: 75
- Current objective rows: 75
- Model link: direct constraint on run-local intrinsic permeability tensor field k_i_rd
- Prediction quantity: interval-weighted directional permeability e^T K e
- Bias/model-error terms: gas pulse interpretation versus liquid-equivalent intrinsic permeability; Klinkenberg/slip correction provenance; 3D interval support represented in 2D; scalar interval value projected onto directional tensor response; gas transport in claystone can involve capillary water displacement and is not liquid relative permeability
- Current artifacts: `permeability_observation_targets.csv; permeability_observation_cells.csv; permeability_measurement_semantics.md; permeability_fit_evaluation.csv; permeability_fit_summary.json; permeability_residual_conflict_audit.md; permeability_likelihood_policy_audit.md; permeability_likelihood_decision_request.md`
- Source basis: local permeability workbook, characterization slides/paper, Klinkenberg1941, Marschall2005
- Notes: Current candidate direct objective: 269.8180571059851; effective weight: 52.0. Semantics audit rows: 204; positive rows: 200; usable current rows: 75; usable segments: BCD-A32, BCD-A33. Likelihood policy audit status: permeability_likelihood_policy_audit_generated; top-10 row-loss share: 0.49400403343820803; support-cell mean diagnostic objective: 1.7670484276950664e-28; conflicting support groups: 16; active row-Gaussian policy remains unchanged without a modelling-team decision; the decision request records robust/support-cell/scalar-outlier alternatives for future reranking.

### NMR weekly and seasonal water content

- Candidate rows: 464
- Usable or mapped rows: 287
- Current objective rows: 192
- Model link: sample OGS porosity*saturation at mapped NMR labels
- Prediction quantity: theta_model = porosity * liquid_saturation
- Bias/model-error terms: NMR detects hydrogen-bearing water, including bound/interlayer contributions that may not belong to mobile liquid saturation in the OGS Richards equation
- Current artifacts: `nmr_weekly.csv; nmr_seasonal_profiles.csv; state_observation_targets.csv; state_observation_samples.csv; nmr_bound_water_sensitivity.md; nmr_candidate_bias_sensitivity.md`
- Source basis: WaterContentEDZ2024; NMR2026Local; Kleinberg1996NMR; Elsayed2020ClayNMR
- Notes: Current sampled OGS evaluation uses 192 NMR rows in the state objective. Delta/trend residuals remain safer than absolute saturation if no free-water correction is available. Bound-water sensitivity audit: fixed phi=0.105; 162 of 287 currently usable mapped rows exceed phi if interpreted as mobile theta without correction; usable-row required positive offset p95=0.0402; best tested uniform subtraction by simple physical-row count is 0.050, leaving 7 nonphysical usable rows; cross-run bias/anomaly audit spans 66 runs, best label-bias run=broad_continuous_001_003_length_0p021m with diagnostic combined objective=505.614305828437, best anomaly run=broad_continuous_001_003_length_0p021m, current-vs-bias rank correlation=0.6351529067946979.

### ERT open-niche resistivity field

- Candidate rows: 1691
- Usable or mapped rows: 2035
- Current objective rows: 0
- Model link: project OGS theta field to ERT mesh/support and convert theta to resistivity
- Prediction quantity: rho_pred = a * theta_model ** b on ERT/common mesh
- Bias/model-error terms: empirical theta-resistivity calibration; clay surface conduction; ERT inversion smoothing; coordinate transform and OGS/ERT domain mismatch
- Current artifacts: `ert_timesteps.csv; ert_water_content_resistivity_operator.csv; ert_spatial_projection_lookup.csv; ert_measurement_semantics.md; ert_observation_operator.md; ert_spatial_projection_operator.md; direct_fit_observation_run/ert_resistivity_diagnostic.md; ert_candidate_discrimination.md; ert_support_sensitivity.md`
- Source basis: WaterContentEDZ2024; Archie1942; CDAModellingSlides2025
- Notes: Recommended relation: kruschwitz_model_data2019; timestep rows: 1691; with matching VTK: 1675; missing VTK: 16; projection-ready rows: 2035; direct-run compared rows: 162800; compared output times: 80; log10 residual MAE: 0.2541801957739222; log10 residual RMSE: 0.29996586160456457; cross-run audited runs: 66; full active-objective runs: 66; cross-run ERT MAE range: 0.019635573360798686; best active-objective ERT MAE: 0.2541796182834413; combined-objective/ERT-MAE correlation: 0.8894403368395667; support-sensitivity selected runs: 6; support variants: 9; best mean support-rank run: broad_continuous_001_001_length_0p023m_shift_1p004.

### Taupe/TDR EDZ bands

- Candidate rows: 5088
- Usable or mapped rows: 2544
- Current objective rows: 0
- Model link: band-average OGS theta along mapped Taupe borehole intervals
- Prediction quantity: baseline-normalized theta_model trend by sensor and EDZ band
- Bias/model-error terms: workbook unit not confirmed; TDR dielectric response is not automatically volumetric water content in claystone; band-average support differs from OGS cells
- Current artifacts: `taupe_tdr_bands.csv; taupe_tdr_trend_operator.csv; taupe_tdr_semantics.md; taupe_tdr_observation_operator.md; direct_fit_observation_run/taupe_tdr_trend_diagnostic.md; taupe_candidate_discrimination.md; taupe_series_weight_sensitivity.md`
- Source basis: TaupeISU2026Local; CDAModellingSlides2025; Topp1980TDR
- Notes: Mapped trend rows: 2544; outside current mesh rows: 2544; trend-ready series: 12; outside-support series: 12; direct-run compared trend rows: 1860; compared series: 12; trend diagnostic MAE: 1.8632108603748923; cross-run audited runs: 74; full active-objective runs: 66; cross-run Taupe MAE range: 0.03687076560014302; best active-objective Taupe MAE: 1.863211058631399; series-weight sensitivity runs: 66; compared A3/A4 series: 12; uncompared A7/A8 series: 12; distinct per-series winners: 8; best mean weighting-rank run: adaptive_combined_001_length_0p050m; absolute candidate conversions remain sanity checks (WC-percent physical rows: 2120; Topp physical rows: 0; linear eps6 physical rows: 2544).

### suction/relative humidity

- Candidate rows: 4247
- Usable or mapped rows: 4228
- Current objective rows: 0
- Model link: hydraulic boundary pressure curve and retention-curve consistency check
- Prediction quantity: liquid pressure/capillary pressure implied by RH through Kelvin relation
- Bias/model-error terms: temperature and density assumptions in Kelvin conversion; sensor reliability above 95 percent RH; unknown preprocessing used for 08_08_open_niche_seasonal.xml
- Current artifacts: `rh_open_twin_kelvin.csv; rh_boundary_curve_audit.csv; rh_measurement_semantics.md; rh_measurement_semantics_summary.json; rh_boundary_provenance_request.md; rh_boundary_provenance_request.csv; rh_boundary_candidate_curves.md; rh_boundary_candidate_curve_summary.json; rh_boundary_uncertainty.md; rh_boundary_uncertainty_summary.json`
- Source basis: WaterContentEDZ2024; Thomson1871Kelvin; TDMinutes2026Local
- Notes: RH rows: 4247; valid non-low-outlier rows: 4228; low-RH outliers: 19; >95% open-twin caution rows: 2492; compared rows: 2280; median absolute mismatch MPa: 12.99802291936514; active-curve implied RH rows below clean RH5/RH6 minimum: 772; provenance request rows: 6; evidence rows: 10; candidate boundary curves: 6; preferred candidate: rh5_rh6_median; preferred overlap MAE MPa: 15.145716829491423; candidate rows after active curve: 2922; candidate-envelope dates: 1064; overlap pressure-range p50 MPa: 2.103967930926996; active outside candidate envelope rows: 575; active curve date span: 2019-09-18 to 2023-12-26.

### other HM monitoring and levelling

- Candidate rows: 22
- Usable or mapped rows: 22
- Current objective rows: 0
- Model link: mechanical plausibility checks on displacement/stress and pressure responses
- Prediction quantity: candidate-dependent displacement, pressure, and qualitative trend diagnostics
- Bias/model-error terms: simplified 2D model cannot explain every 3D deformation or crack/scan observation
- Current artifacts: `other_hm_monitoring.md; other_hm_qualitative_targets.csv; other_hm_levelling_displacements.csv; other_hm_missing_numeric_request.md; other_hm_missing_numeric_request.csv; other_hm_numeric_source_audit.md; other_hm_numeric_source_audit_summary.json`
- Source basis: InputHERMES2024Local; BGRModellingTD2026Local; LevellingTD2026Local
- Notes: Use to reject mechanically implausible permeability-only fits once OGS displacement outputs exist. Missing numeric request rows: 6; evidence rows: 8; numeric source audit requests: 6; hard-residual-ready requests: 0; support-ready requests: 6; zip numeric-candidate members: 0.

### coordinates, borehole geometry, and bedding

- Candidate rows: 142
- Usable or mapped rows: 448
- Current objective rows: 0
- Model link: observation support mapping and anisotropy-orientation prior
- Prediction quantity: no direct physical residual
- Bias/model-error terms: coordinate-frame mismatch and missing endpoint geometry dominate downstream risk
- Current artifacts: `measurement_mesh_lookup.csv; borehole_mesh_lookup.csv; borehole_line_mesh_samples.csv`
- Source basis: coordinate workbooks; Ziefle2024Characterization; CDAModellingSlides2025
- Notes: This layer prevents outside-mesh and nearest-cell fallbacks from silently entering active objectives.

## Practical Consequences

- Do not convert every prepared target row into an active residual automatically.
- Keep direct permeability in log-space because the measurement and parameter range span orders of magnitude.
- Treat NMR absolute water content as biased unless a free-water/bound-water correction is accepted.
- Treat ERT and Taupe/TDR as forward observation operators, not direct saturation or permeability measurements.
- Treat RH as boundary-condition evidence unless the boundary curve generation is reconstructed.
