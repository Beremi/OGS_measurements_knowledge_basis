# Measurement Model-Entry Matrix

This generated matrix joins the measurement coverage audit, the likelihood
model, the stream activation-gate audit, and the final objective decision
register. It records how each collected measurement class currently enters
the frozen OGS workflow and why several streams remain diagnostic, support
only, boundary-audit only, or not ready for hard residuals.

## Summary

- Measurement classes: 9
- Active measurement classes: 2
- Active objective rows: 267
- Diagnostic/boundary classes: 3
- Support/prior classes: 3
- Not-ready hard-residual classes: 1
- Rows without a likelihood row: 1

## Compact Matrix

| Measurement | Entry class | Active rows | Current allowed use | Primary blocker or next action | Measurement-info note |
| --- | --- | ---: | --- | --- | --- |
| ERT / electrical resistivity | `diagnostic_only` | 0 | `diagnostic_only` | ERT-to-OGS transform and exact near-niche support mask remain assumed, not confirmed.; No defensible ERT residual sigma/correlation model is available; pixels cannot be treated as independent rows. | `cda_knowledge_base/measurements_info/ert/MEASUREMENT_INFO.md` |
| NMR water content | `active_objective` | 192 | `active_raw_absolute_theta_with_provisional_trend_scenario` | recommended=within_label_trend_anomaly; executable_status=nmr_trend_anomaly_active_objective_mode_implemented_provisional; best_run=broad_continuous_001_003_length_0p021m; validation_delta=5.684341886080802e-14; followup=pause_new_trend_anomaly_ogs_batch.; active_objective_changed=False; recommended=within_label_trend_anomaly; best_recommended_run=broad_continuous_001_003_length_0p021m; executable_best=broad_continuous_001_003_length_0p021m; raw_incumbent_rank_under_trend=14.0; trend_winner_raw_rank=56.0; followup=pause_new_trend_anomaly_ogs_batch; median_state_beating_candidates=0. | `cda_knowledge_base/measurements_info/nmr/MEASUREMENT_INFO.md` |
| Taupe / TDR EDZ bands | `diagnostic_only` | 0 | `diagnostic_only` | Taupe values are not confirmed as volumetric water-content percent, permittivity, or another ARDP-derived proxy. | `cda_knowledge_base/measurements_info/taupe_tdr/MEASUREMENT_INFO.md` |
| Suction / relative humidity | `boundary_audit_only` | 0 | `boundary_audit_only` | Active boundary curve generation, sensor screening, time axis, constants, and extension policy are not confirmed. | `cda_knowledge_base/measurements_info/suction_relative_humidity/MEASUREMENT_INFO.md` |
| Permeability pulse tests | `active_objective` | 75 | `partial_active_support` | Historical permeability endpoints are needed only if these older rows should enter the fit.; support-conflict audit=permeability_support_conflict_spatial_audit_generated; active/repeated/range>=2 support cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes | `cda_knowledge_base/measurements_info/permeability_pulse_tests/MEASUREMENT_INFO.md` |
| Other HM monitoring | `not_ready_for_hard_residual` | 0 | `not_ready_for_hard_residual` | Local source scan found layout geometry, laser surface geometry, extracted levelling slide rows, and report/minute evidence, but no hard-residual-ready Geoscope time series, laser statistical interpretation product, or full levelling survey table.; Required metadata for hard HM residual weights are absent from the current local bundle. | `cda_knowledge_base/measurements_info/other_hm_monitoring/MEASUREMENT_INFO.md` |
| Coordinates / geometry / layout | `support_or_prior_layer` | 0 | `support_layer_ready` | Add missing endpoint geometry for older permeability intervals if those rows should enter the same target format. | `cda_knowledge_base/measurements_info/coordinates_geometry_layout/MEASUREMENT_INFO.md` |
| Bedding / geology / structure | `support_or_prior_layer` | 0 | `support_or_prior_layer` | Decide whether future optimization should release anisotropy angle spatially or keep a global bedding-informed angle. | `cda_knowledge_base/measurements_info/bedding_geology_structure/MEASUREMENT_INFO.md` |
| Model projection inputs | `support_or_prior_layer` | 0 | `frozen_uninterpreted_caveat` | The XML binds CTE to solid thermal_expansivity, but the value and comment look like a copied heat-capacity entry. The model must remain frozen, so this needs provenance confirmation rather than a local correction. | `cda_knowledge_base/measurements_info/model_projection_inputs/MEASUREMENT_INFO.md` |

## Detailed Rows

### ERT / electrical resistivity

- Measurement folder: `ert`
- Observation id: `ert_open_time_series`
- Model-entry class: `diagnostic_only`
- Coverage status: `resistivity_diagnostic_generated_transform_support_unconfirmed`
- Likelihood activation: `resistivity_diagnostic_evaluated_transform_support_unconfirmed`
- Stream promotion decision: `diagnostic_only`
- Final decision status: `pending_user_send_and_provider_response_or_explicit_exclusion`
- Current allowed use: `diagnostic_only`
- Manifest model role: resistivity observation operator from OGS saturation/water content to ERT mesh or projected common mesh
- Primary measured quantity: electrical resistivity / resistivity change
- Model quantity: n*S_l mapped to resistivity by empirical Archie-type relation
- Model link: project OGS theta field to ERT mesh/support and convert theta to resistivity
- Prediction quantity: rho_pred = a * theta_model ** b on ERT/common mesh
- Residual definition: log10(rho_pred) - log10(rho_ERT_inverted)
- Residual transform: multiplicative/log-resistivity residual; no active sigma yet
- Likelihood scale: defer numerical sigma until ERT-to-OGS transform, support mask, and inversion-field uncertainty are confirmed; support-sensitivity ranks are diagnostic only
- Weighting rule: future weights should aggregate ERT cells by support/time to avoid treating correlated pixels as independent
- Bias/model-error terms: empirical theta-resistivity calibration; clay surface conduction; ERT inversion smoothing; coordinate transform and OGS/ERT domain mismatch
- Activation gate: Confirm ERT-to-OGS coordinate transform, exact near-niche support mask, and ERT inversion uncertainty/correlation before activation.
- Rows raw/target/mapped/active/current-objective: 1691/1691/2035/0/0
- Gate pass/warn/fail/missing: pass=1, warn=0, fail=2, missing=0
- Blocker or next action: ERT-to-OGS transform and exact near-niche support mask remain assumed, not confirmed.; No defensible ERT residual sigma/correlation model is available; pixels cannot be treated as independent rows.
- Include consequence: If the transform/support mask and covariance model are accepted, ERT can move from provisional log-resistivity diagnostic evidence into a weighted final stream or accepted scenario screen.
- Exclude consequence: If excluded, keep ERT as diagnostic field-consistency evidence only and state that the final objective is not selected by the dense ERT VTK series.
- Report wording requirement: State whether the final permeability field includes ERT, keeps it diagnostic, or excludes it; keep the provisional-transform caveat unless the provider closes it.
- Measurement-info note: `cda_knowledge_base/measurements_info/ert/MEASUREMENT_INFO.md`
- Source artifacts: ert_timesteps.csv; ert_archive_inventory.csv; ert_nmr_resistivity_pairs.csv; ert_water_content_resistivity_operator.csv; ert_spatial_projection_lookup.csv; ert_spatial_projection_operator.md; state_observation_targets.csv; direct_fit_observation_run/ert_resistivity_diagnostic.md; ert_candidate_discrimination.md; ert_support_sensitivity.md; ert_measurement_semantics.md; ert_observation_operator.md; ert_resistivity_diagnostic_summary.json; ert_support_sensitivity_summary.json; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses/ert_transform_support_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses/ert_uncertainty_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses

### NMR water content

- Measurement folder: `nmr`
- Observation id: `nmr_weekly_and_seasonal`
- Model-entry class: `active_objective`
- Coverage status: `active_state_residual_from_sampled_ogs_outputs`
- Likelihood activation: `active_state_likelihood_from_sampled_ogs_outputs`
- Stream promotion decision: `active_with_tracked_caveats`
- Final decision status: `pending_modelling_team_final_policy`
- Current allowed use: `active_raw_absolute_theta_with_provisional_trend_scenario`
- Manifest model role: sparse water-content anchor with bound/interlayer-water bias term
- Primary measured quantity: NMR-derived volumetric water content and T2
- Model quantity: n*S_l plus measurement/bound-water model
- Model link: sample OGS porosity*saturation at mapped NMR labels
- Prediction quantity: theta_model = porosity * liquid_saturation
- Residual definition: theta_model - theta_NMR_obs
- Residual transform: Gaussian residual in volumetric water-content fraction after bias treatment
- Likelihood scale: row sigma from reported 95 percent confidence interval with 0.01 fraction floor; absolute-residual activation must include the generated bound-water/bias audit, with usable-row required-offset p95=0.0402
- Weighting rule: one point target per dated NMR row; seasonal Niche 3 rows stay outside current Niche 4 fit
- Bias/model-error terms: NMR detects hydrogen-bearing water, including bound/interlayer contributions that may not belong to mobile liquid saturation in the OGS Richards equation
- Activation gate: requires sampled OGS state outputs and the generated bound-water sensitivity audit; prefer trend/anomaly residuals before absolute theta residuals
- Rows raw/target/mapped/active/current-objective: 464/464/287/192/192
- Gate pass/warn/fail/missing: pass=1, warn=1, fail=0, missing=0
- Blocker or next action: recommended=within_label_trend_anomaly; executable_status=nmr_trend_anomaly_active_objective_mode_implemented_provisional; best_run=broad_continuous_001_003_length_0p021m; validation_delta=5.684341886080802e-14; followup=pause_new_trend_anomaly_ogs_batch.; active_objective_changed=False; recommended=within_label_trend_anomaly; best_recommended_run=broad_continuous_001_003_length_0p021m; executable_best=broad_continuous_001_003_length_0p021m; raw_incumbent_rank_under_trend=14.0; trend_winner_raw_rank=56.0; followup=pause_new_trend_anomaly_ogs_batch; median_state_beating_candidates=0.
- Include consequence: The final objective must choose raw absolute theta with caveats, within-label trend/anomaly residuals, a label-bias/free-water correction, or another recorded NMR policy before promotion.
- Exclude consequence: If NMR is excluded from final field selection, the report must say the active raw-NMR incumbent is no longer an all-measurement field and must rerun selection without NMR.
- Report wording requirement: State the final NMR free-water/bound-water policy and the exact residual form used for final selection.
- Measurement-info note: `cda_knowledge_base/measurements_info/nmr/MEASUREMENT_INFO.md`
- Source artifacts: nmr_weekly.csv; nmr_seasonal_profiles.csv; state_observation_targets.csv; state_observation_samples.csv; nmr_bound_water_sensitivity.md; nmr_candidate_bias_sensitivity.md; state_observation_evaluation_summary.json; nmr_bound_water_sensitivity_summary.json; inversion_workflow/nmr_objective_decision.md; inversion_workflow/nmr_trend_anomaly_active_objective.md; inversion_workflow/runs/nmr_trend_anomaly_followup_plan/NMR_TREND_ANOMALY_FOLLOWUP_PLAN.md; inversion_workflow/conditional_field_selection_scenarios.md

### Taupe / TDR EDZ bands

- Measurement folder: `taupe_tdr`
- Observation id: `taupe_tdr_edz_bands`
- Model-entry class: `diagnostic_only`
- Coverage status: `trend_operator_ready_absolute_calibration_pending`
- Likelihood activation: `trend_diagnostic_evaluated_pending_absolute_calibration`
- Stream promotion decision: `diagnostic_only`
- Final decision status: `pending_user_send_and_provider_response_or_explicit_exclusion`
- Current allowed use: `diagnostic_only`
- Manifest model role: semi-quantitative EDZ-band water-content trend validation
- Primary measured quantity: Taupe/TDR water-content or dielectric proxy by EDZ distance band
- Model quantity: band averages of S_l or n*S_l
- Model link: band-average OGS theta along mapped Taupe borehole intervals
- Prediction quantity: baseline-normalized theta_model trend by sensor and EDZ band
- Residual definition: model trend anomaly - observed Taupe/TDR anomaly
- Residual transform: within-series trend diagnostic; absolute saturation residual inactive
- Likelihood scale: no absolute sigma assigned; future trend sigma should be estimated per sensor/band after unit calibration; grouped-weight sensitivity remains diagnostic
- Weighting rule: aggregate by sensor, EDZ band, and time; A7/A8 remain outside current mesh support
- Bias/model-error terms: workbook unit not confirmed; TDR dielectric response is not automatically volumetric water content in claystone; band-average support differs from OGS cells
- Activation gate: Confirm whether Taupe_WC workbook values are calibrated volumetric water-content percent, apparent relative dielectric permittivity, or another ARDP-derived proxy before assigning absolute saturation or water-content residual weights.
- Rows raw/target/mapped/active/current-objective: 5088/5088/2544/0/0
- Gate pass/warn/fail/missing: pass=1, warn=2, fail=1, missing=0
- Blocker or next action: Taupe values are not confirmed as volumetric water-content percent, permittivity, or another ARDP-derived proxy.
- Include consequence: If units/calibration and uncertainty are accepted, Taupe can become a grouped trend residual over mapped A3/A4 EDZ bands or an explicitly calibrated absolute water-content residual.
- Exclude consequence: If excluded, keep Taupe as mapped trend-diagnostic evidence and do not let A3/A4 or A7/A8 select the final field.
- Report wording requirement: State whether Taupe workbook values are final water-content evidence, trend-only evidence, or excluded from the final likelihood.
- Measurement-info note: `cda_knowledge_base/measurements_info/taupe_tdr/MEASUREMENT_INFO.md`
- Source artifacts: taupe_tdr_bands.csv; taupe_tdr_trend_operator.csv; taupe_tdr_observation_operator.md; borehole_line_mesh_samples.csv; state_observation_targets.csv; state_observation_samples.csv; direct_fit_observation_run/taupe_tdr_trend_diagnostic.md; taupe_candidate_discrimination.md; taupe_series_weight_sensitivity.md; taupe_tdr_semantics.md; taupe_tdr_trend_diagnostic_summary.json; taupe_series_weight_sensitivity_summary.json; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/provider_responses/taupe_unit_calibration_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/provider_responses

### Suction / relative humidity

- Measurement folder: `suction_relative_humidity`
- Observation id: `suction_relative_humidity_open_twin`
- Model-entry class: `boundary_audit_only`
- Coverage status: `boundary_forcing_audited_not_point_residual`
- Likelihood activation: `boundary_forcing_audit_not_point_likelihood`
- Stream promotion decision: `boundary_audit_only`
- Final decision status: `pending_user_send_and_provider_response_or_explicit_exclusion`
- Current allowed use: `boundary_audit_only`
- Manifest model role: Kelvin-equation pressure boundary reconstruction and retention validation
- Primary measured quantity: relative humidity time series
- Model quantity: liquid-pressure boundary p_l or capillary pressure p_c
- Model link: hydraulic boundary pressure curve and retention-curve consistency check
- Prediction quantity: liquid pressure/capillary pressure implied by RH through Kelvin relation
- Residual definition: active OGS boundary curve - RH-derived Kelvin pressure
- Residual transform: boundary provenance audit; not a cell residual in current objective
- Likelihood scale: no point-residual sigma assigned; sensor reliability split must enter any future curve-fit likelihood
- Weighting rule: filter invalid/low-RH outliers; keep high-RH open-twin caution flag
- Bias/model-error terms: temperature and density assumptions in Kelvin conversion; sensor reliability above 95 percent RH; unknown preprocessing used for 08_08_open_niche_seasonal.xml
- Activation gate: Obtain or reconstruct the generation history for 08_08_open_niche_seasonal.xml before treating the active open-niche pressure curve as verified RH-derived forcing or using RH as a retention-parameter likelihood.
- Rows raw/target/mapped/active/current-objective: 4247/4247/4228/0/0
- Gate pass/warn/fail/missing: pass=1, warn=0, fail=2, missing=0
- Blocker or next action: Active boundary curve generation, sensor screening, time axis, constants, and extension policy are not confirmed.
- Include consequence: If provenance, constants, time axis, sensor screening, and uncertainty are accepted, RH can drive accepted boundary-forcing scenarios or a later retention/boundary release.
- Exclude consequence: If excluded from the final objective, keep RH as boundary-provenance evidence and do not replace or fit the active open-niche pressure curve from local workbook curves.
- Report wording requirement: State whether RH is a final boundary condition source, a scenario-only forcing, or a provenance audit with no residual weight.
- Measurement-info note: `cda_knowledge_base/measurements_info/suction_relative_humidity/MEASUREMENT_INFO.md`
- Source artifacts: rh_open_twin_kelvin.csv; rh_boundary_curve_audit_summary.json; rh_measurement_semantics_summary.json; rh_boundary_provenance_request.md; rh_boundary_provenance_request.csv; rh_boundary_candidate_curves.md; rh_boundary_candidate_curve_summary.json; rh_boundary_uncertainty.md; rh_boundary_uncertainty_summary.json; state_observation_targets.csv; rh_boundary_curve_audit.csv; rh_measurement_semantics.md; rh_boundary_provenance_request_summary.json; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/provider_responses/rh_active_curve_provenance_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/provider_responses

### Permeability pulse tests

- Measurement folder: `permeability_pulse_tests`
- Observation id: `permeability_pulse_tests`
- Model-entry class: `active_objective`
- Coverage status: `active_parameter_objective`
- Likelihood activation: `active_direct_parameter_likelihood`
- Stream promotion decision: `active_with_tracked_caveats`
- Final decision status: `pending_user_send_and_provider_response_or_explicit_exclusion`
- Current allowed use: `partial_active_support`
- Manifest model role: direct noisy log-permeability constraints on interval-scale effective directional averages
- Primary measured quantity: nitrogen pulse-test apparent/intrinsic permeability or transmissibility
- Model quantity: local average of e^T k(x) e over test influence volume
- Model link: direct constraint on run-local intrinsic permeability tensor field k_i_rd
- Prediction quantity: interval-weighted directional permeability e^T K e
- Residual definition: log10(k_pred_m2) - log10(k_obs_m2)
- Residual transform: Gaussian residual in log10 permeability space
- Likelihood scale: current evaluator uses sigma = 0.5 log10 units; this is an intentionally broad first-pass scale; robust-tail and support-cell aggregation alternatives are diagnostic only unless explicitly approved
- Weighting rule: duplicates with same campaign, segment, depth and observed log10(k) share unit weight; support-cell repeated/conflicting rows are now audited separately by the likelihood-policy diagnostic
- Bias/model-error terms: gas pulse interpretation versus liquid-equivalent intrinsic permeability; Klinkenberg/slip correction provenance; 3D interval support represented in 2D; scalar interval value projected onto directional tensor response; gas transport in claystone can involve capillary water displacement and is not liquid relative permeability
- Activation gate: already active for rows with positive interpreted k and inside-mesh interval mapping
- Rows raw/target/mapped/active/current-objective: 204/204/75/75/75
- Gate pass/warn/fail/missing: pass=2, warn=1, fail=0, missing=0
- Blocker or next action: Historical permeability endpoints are needed only if these older rows should enter the fit.; support-conflict audit=permeability_support_conflict_spatial_audit_generated; active/repeated/range>=2 support cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes
- Include consequence: If endpoint traces/geometries are accepted, the blocked historical BCD-A24/25/26/27 and BFM-D19 rows can be projected to OGS support cells or interval traces.
- Exclude consequence: If excluded, the final permeability objective stays limited to currently projected active pulse-test rows and the historical rows remain visible but inactive.
- Report wording requirement: State whether historical endpoint-missing rows enter the final fit, remain inactive, or are superseded by the current active support definition.
- Measurement-info note: `cda_knowledge_base/measurements_info/permeability_pulse_tests/MEASUREMENT_INFO.md`
- Source artifacts: permeability_observation_targets.csv; permeability_observation_cells.csv; permeability_missing_geometry_audit.csv; smooth_permeability_candidate_search/SMOOTH_FIT_SUMMARY.json; candidate_smooth_0p025m_search_driver/permeability_fit_summary.json; permeability_measurement_semantics.md; permeability_fit_evaluation.csv; permeability_fit_summary.json; permeability_residual_conflict_audit.md; permeability_likelihood_policy_audit.md; permeability_likelihood_decision_request.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/permeability_pulse_tests/source_files/provider_responses/perm_endpoint_geometry_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/permeability_pulse_tests/source_files/provider_responses; inversion_workflow/permeability_support_conflict_spatial_audit.md; inversion_workflow/permeability_support_lower_bound_audit.md; inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md; inversion_workflow/permeability_next_field_fit_gate.md

### Other HM monitoring

- Measurement folder: `other_hm_monitoring`
- Observation id: `other_hm_monitoring`
- Model-entry class: `not_ready_for_hard_residual`
- Coverage status: `layout_and_qualitative_targets_ready_numeric_series_missing`
- Likelihood activation: `qualitative_validation_layer_numeric_series_missing`
- Stream promotion decision: `not_ready_for_hard_residual`
- Final decision status: `pending_user_send_and_provider_response_or_explicit_exclusion`
- Current allowed use: `not_ready_for_hard_residual`
- Manifest model role: secondary pressure/deformation validation gates where numeric data become available
- Primary measured quantity: extensometer, mini-piezometer, crackmeter, laser scan, levelling context
- Model quantity: displacement, strain, pressure and qualitative trend checks
- Model link: mechanical plausibility checks on displacement/stress and pressure responses
- Prediction quantity: candidate-dependent displacement, pressure, and qualitative trend diagnostics
- Residual definition: not yet a numerical residual except future levelling/geoscope series comparisons
- Residual transform: validation gates before hard likelihood
- Likelihood scale: no hard sigma assigned until Geoscope/laser-scan/extensometer time series are located
- Weighting rule: avoid hard weighting of qualitative statements; use as rejection/diagnostic gates
- Bias/model-error terms: simplified 2D model cannot explain every 3D deformation or crack/scan observation
- Activation gate: Numeric Geoscope and laser-scan exports are still absent from the catalogue; the request package states exactly what is needed before hard pressure/deformation residuals can be assigned.
- Rows raw/target/mapped/active/current-objective: 95/22/22/0/0
- Gate pass/warn/fail/missing: pass=1, warn=0, fail=2, missing=0
- Blocker or next action: Local source scan found layout geometry, laser surface geometry, extracted levelling slide rows, and report/minute evidence, but no hard-residual-ready Geoscope time series, laser statistical interpretation product, or full levelling survey table.; Required metadata for hard HM residual weights are absent from the current local bundle.
- Include consequence: If numeric exports and uncertainty metadata arrive, selected extensometer, mini-piezometer, crackmeter, laser, levelling, or Geoscope rows can become mechanical/hydraulic validation or residual streams.
- Exclude consequence: If excluded, keep the report, slides, Tecplot layout, and levelling snippets as qualitative validation context only.
- Report wording requirement: State that other-HM streams are not final likelihood terms unless hard-residual-ready time series, support definitions, and weights are accepted.
- Measurement-info note: `cda_knowledge_base/measurements_info/other_hm_monitoring/MEASUREMENT_INFO.md`
- Source artifacts: other_hm_visualisation_zones.csv; other_hm_levelling_displacements.csv; other_hm_qualitative_targets.csv; other_hm_monitoring.md; other_hm_missing_numeric_request.md; other_hm_missing_numeric_request.csv; other_hm_numeric_source_audit.md; other_hm_numeric_source_audit_summary.json; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses/hm_numeric_exports_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses/hm_uncertainty_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses

### Coordinates / geometry / layout

- Measurement folder: `coordinates_geometry_layout`
- Observation id: `coordinates_and_geometry`
- Model-entry class: `support_or_prior_layer`
- Coverage status: `support_layer_ready`
- Likelihood activation: `support_and_prior_layer`
- Stream promotion decision: `support_layer_ready`
- Final decision status: `none`
- Current allowed use: `support_layer_ready`
- Manifest model role: coordinate transform and measurement-to-mesh lookup for all observation operators
- Primary measured quantity: measurement positions and labels
- Model quantity: 2D_Model (x/y) coordinates and BGR model coordinates
- Model link: observation support mapping and anisotropy-orientation prior
- Prediction quantity: no direct physical residual
- Residual definition: not a likelihood term
- Residual transform: support/prior metadata
- Likelihood scale: not applicable
- Weighting rule: propagate mapping status to downstream measurement residuals
- Bias/model-error terms: coordinate-frame mismatch and missing endpoint geometry dominate downstream risk
- Activation gate: continue using as required support; add endpoint geometry for older permeability rows
- Rows raw/target/mapped/active/current-objective: 142/0/107/0/0
- Gate pass/warn/fail/missing: pass=1, warn=0, fail=0, missing=0
- Blocker or next action: Add missing endpoint geometry for older permeability intervals if those rows should enter the same target format.
- Include consequence: none
- Exclude consequence: none
- Report wording requirement: none
- Measurement-info note: `cda_knowledge_base/measurements_info/coordinates_geometry_layout/MEASUREMENT_INFO.md`
- Source artifacts: measurement_coordinates_xy.csv; borehole_coordinates.csv; measurement_mesh_lookup.csv; borehole_line_mesh_samples.csv; borehole_mesh_lookup.csv

### Bedding / geology / structure

- Measurement folder: `bedding_geology_structure`
- Observation id: `bedding_structure`
- Model-entry class: `support_or_prior_layer`
- Coverage status: `structural_prior_ready`
- Likelihood activation: `support_and_prior_layer`
- Stream promotion decision: `none`
- Final decision status: `none`
- Current allowed use: `support_or_prior_layer`
- Manifest model role: anisotropy-angle prior and structural uncertainty flags
- Primary measured quantity: bedding/fault orientation context
- Model quantity: rotation angle theta and local uncertainty inflation
- Model link: observation support mapping and anisotropy-orientation prior
- Prediction quantity: no direct physical residual
- Residual definition: not a likelihood term
- Residual transform: support/prior metadata
- Likelihood scale: not applicable
- Weighting rule: propagate mapping status to downstream measurement residuals
- Bias/model-error terms: coordinate-frame mismatch and missing endpoint geometry dominate downstream risk
- Activation gate: continue using as required support; add endpoint geometry for older permeability rows
- Rows raw/target/mapped/active/current-objective: 0/0/0/0/0
- Gate pass/warn/fail/missing: none
- Blocker or next action: Decide whether future optimization should release anisotropy angle spatially or keep a global bedding-informed angle.
- Include consequence: none
- Exclude consequence: none
- Report wording requirement: none
- Measurement-info note: `cda_knowledge_base/measurements_info/bedding_geology_structure/MEASUREMENT_INFO.md`
- Source artifacts: bedding_geology_structure source files; run_config.example.json; direct_permeability_prior_sweep/SWEEP_SUMMARY.json; measurement_mesh_lookup.csv; borehole_mesh_lookup.csv; borehole_line_mesh_samples.csv

### Model projection inputs

- Measurement folder: `model_projection_inputs`
- Observation id: `model_projection_inputs`
- Model-entry class: `support_or_prior_layer`
- Coverage status: `workflow_support_ready`
- Likelihood activation: `none`
- Stream promotion decision: `support_layer_ready`
- Final decision status: `pending_user_send_and_provider_response_or_explicit_exclusion`
- Current allowed use: `frozen_uninterpreted_caveat`
- Manifest model role: mesh-cell parameter-field injection and OGS output/measurement timestep alignment
- Primary measured quantity: projection script, model archives, projected mesh
- Model quantity: MeshElement fields n_rd and k_i_rd
- Model link: none
- Prediction quantity: none
- Residual definition: none
- Residual transform: none
- Likelihood scale: none
- Weighting rule: none
- Bias/model-error terms: none
- Activation gate: Keep using release-gated run preparation; do not release later parameters until stream gates pass.
- Rows raw/target/mapped/active/current-objective: 10239/0/10239/0/0
- Gate pass/warn/fail/missing: pass=1, warn=0, fail=0, missing=0
- Blocker or next action: The XML binds CTE to solid thermal_expansivity, but the value and comment look like a copied heat-capacity entry. The model must remain frozen, so this needs provenance confirmation rather than a local correction.
- Include consequence: If confirmed, record whether CTE=1254.74 is intended, inactive, copied heat capacity, or another convention; keep the exchanged model frozen unless a separate approved model-version decision is made.
- Exclude consequence: If scoped out, state that the final permeability fit does not interpret or calibrate thermal expansivity and that CTE remains a frozen-source caveat.
- Report wording requirement: State the CTE response or the explicit scope-out decision before making broad thermo-mechanical interpretation claims.
- Measurement-info note: `cda_knowledge_base/measurements_info/model_projection_inputs/MEASUREMENT_INFO.md`
- Source artifacts: GESA_model_original/projection_on_mesh_2025-09-05; prepare_ogs_run.py; evaluate_inversion_candidate.py; OGS_ENVIRONMENT_AUDIT.json; OGS_RUN_INPUT_AUDIT.json; inversion_release_gate_audit.md; inversion_parameter_release_plan.md; inversion_workflow/cte_confirmation_request.md

## Interpretation

The matrix confirms that all nine collected measurement classes have an explicit
place in the modelling workflow, but only direct permeability and NMR currently
contribute active objective rows. ERT and Taupe/TDR are diagnostic streams,
RH/suction is a boundary/provenance audit, other-HM remains blocked by missing
numeric exports, and the geometry, bedding, and model-projection folders are
support/prior layers. The final field therefore remains an active-objective
incumbent rather than a final all-measurement inversion result.
