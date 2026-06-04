# Work Status

## Built Artifacts

- Editable report source: `main.tex`
- Added measurement chapter: `measurement_chapter.tex`
- Bibliography: `opalinus_clay.bib`
- Built PDF: `main.pdf`
- Source literature folder: `Library/`
- Citation/source coverage audit: `Library/source_coverage_audit.md`
- Original Gesa model copies: `GESA_model_original/`
- Copied projection workflow: `GESA_model_original/projection_on_mesh_2025-09-05/`
- Reproducible anisotropic permeability-field prototype:
  `inversion_workflow/scripts/generate_anisotropic_permeability_field.py`
- OGS run-directory preparation script:
  `inversion_workflow/scripts/prepare_ogs_run.py`
- Machine-checkable observation manifest:
  `inversion_workflow/observation_manifest.json`
- Processed observation-table builder and generated CSVs:
  `inversion_workflow/scripts/build_processed_observations.py` and
  `inversion_workflow/processed_observations/`
- ERT observation-operator builder and generated calibration artifacts:
  `inversion_workflow/scripts/build_ert_observation_operator.py`,
  `ert_water_content_resistivity_operator.csv`,
  `ert_observation_operator_summary.json`, and
  `ert_observation_operator.md`
- ERT spatial-projection lookup builder and generated geometry artifacts:
  `inversion_workflow/scripts/build_ert_spatial_projection_lookup.py`,
  `ert_spatial_projection_lookup.csv`, `ert_spatial_projection_summary.json`, and
  `ert_spatial_projection_operator.md`
- ERT measurement-semantics audit:
  `inversion_workflow/scripts/build_ert_semantics_audit.py`,
  `ert_measurement_semantics_timestep_audit.csv`,
  `ert_measurement_semantics_relation_audit.csv`,
  `ert_measurement_semantics_projection_groups.csv`,
  `ert_measurement_semantics_summary.json`, and
  `ert_measurement_semantics.md`
- ERT resistivity diagnostic against sampled OGS outputs:
  `inversion_workflow/scripts/evaluate_ert_resistivity_diagnostic.py`,
  `runs/direct_fit_observation_run/ert_resistivity_diagnostic.csv`,
  `ert_resistivity_diagnostic_timesteps.csv`,
  `ert_resistivity_diagnostic_summary.json`, and
  `ert_resistivity_diagnostic.md`
- ERT candidate discrimination audit across executed OGS runs:
  `inversion_workflow/scripts/build_ert_candidate_discrimination_audit.py`,
  `ert_candidate_discrimination_audit.csv`,
  `ert_candidate_discrimination_timesteps.csv`,
  `ert_candidate_discrimination_summary.json`, and
  `ert_candidate_discrimination.md`
- ERT support-sensitivity audit:
  `inversion_workflow/scripts/build_ert_support_sensitivity_audit.py`,
  `ert_support_sensitivity_audit.csv`,
  `ert_support_sensitivity_timesteps.csv`,
  `ert_support_sensitivity_summary.json`, and
  `ert_support_sensitivity.md`
- Taupe/TDR observation-operator builder and generated trend artifacts:
  `inversion_workflow/scripts/build_taupe_observation_operator.py`,
  `taupe_tdr_trend_operator.csv`, `taupe_tdr_series_summary.csv`,
  `taupe_tdr_observation_operator_summary.json`, and
  `taupe_tdr_observation_operator.md`
- Taupe/TDR semantics audit:
  `inversion_workflow/scripts/build_taupe_semantics_audit.py`,
  `taupe_tdr_semantics_row_audit.csv`, `taupe_tdr_semantics_series_audit.csv`,
  `taupe_tdr_semantics_group_summary.csv`, `taupe_tdr_semantics_summary.json`, and
  `taupe_tdr_semantics.md`
- Taupe/TDR candidate discrimination audit across executed OGS runs:
  `inversion_workflow/scripts/build_taupe_candidate_discrimination_audit.py`,
  `taupe_candidate_discrimination_audit.csv`,
  `taupe_candidate_discrimination_series.csv`,
  `taupe_candidate_discrimination_summary.json`, and
  `taupe_candidate_discrimination.md`
- Taupe/TDR series-weight sensitivity audit:
  `inversion_workflow/scripts/build_taupe_series_weight_sensitivity_audit.py`,
  `taupe_series_weight_sensitivity_audit.csv`,
  `taupe_series_weight_sensitivity_series.csv`,
  `taupe_series_weight_sensitivity_summary.json`, and
  `taupe_series_weight_sensitivity.md`
- Other HM monitoring inventory builder and generated validation artifacts:
  `inversion_workflow/scripts/build_other_hm_monitoring_inventory.py`,
  `other_hm_visualisation_zones.csv`, `other_hm_visualisation_text_labels.csv`,
  `other_hm_levelling_displacements.csv`, `other_hm_qualitative_targets.csv`,
  `other_hm_monitoring_summary.json`, and `other_hm_monitoring.md`
- Other HM missing numeric-export request package:
  `inversion_workflow/scripts/build_other_hm_missing_numeric_request.py`,
  `other_hm_missing_numeric_request.csv`,
  `other_hm_missing_numeric_evidence.csv`,
  `other_hm_missing_numeric_request_summary.json`, and
  `other_hm_missing_numeric_request.md`
- Mesh observation-lookup builder and generated lookup CSVs:
  `inversion_workflow/scripts/build_mesh_observation_lookup.py`,
  `measurement_mesh_lookup.csv`, `borehole_mesh_lookup.csv`,
  `borehole_line_mesh_samples.csv`, and `ogs_bulk_mesh_cells.csv`
- Direct permeability target builder and generated target CSVs:
  `inversion_workflow/scripts/build_permeability_observation_targets.py`,
  `permeability_observation_targets.csv`, `permeability_observation_cells.csv`,
  `permeability_segment_geometry.csv`, `permeability_missing_geometry_audit.csv`,
  and `permeability_missing_geometry_audit.md`
- Historical permeability endpoint-geometry request package:
  `inversion_workflow/scripts/build_permeability_endpoint_geometry_request.py`,
  `permeability_endpoint_geometry_request.csv`,
  `permeability_endpoint_geometry_blocked_rows.csv`,
  `permeability_endpoint_geometry_request_summary.json`, and
  `permeability_endpoint_geometry_request.md`
- Permeability measurement-semantics audit:
  `inversion_workflow/scripts/build_permeability_semantics_audit.py`,
  `permeability_measurement_semantics_audit.csv`,
  `permeability_measurement_semantics_group_summary.csv`,
  `permeability_measurement_semantics_summary.json`, and
  `permeability_measurement_semantics.md`
- State-observation target builder and generated target/sample CSVs:
  `inversion_workflow/scripts/build_state_observation_targets.py`,
  `state_observation_targets.csv`, `state_observation_samples.csv`, and
  `state_observation_target_summary.json`
- Direct permeability target evaluator:
  `inversion_workflow/scripts/evaluate_permeability_targets.py`, with smoke-test
  outputs in `inversion_workflow/runs/smoke_test/permeability_fit_evaluation.csv`
  and `permeability_fit_summary.json`
- Direct permeability field-fit diagnostic:
  `inversion_workflow/scripts/fit_permeability_field_from_targets.py`, with fitted
  mesh and reports in `inversion_workflow/runs/direct_permeability_fit/`
- Direct permeability prior/proposal sweep:
  `inversion_workflow/scripts/run_direct_permeability_prior_sweep.py` with ranked
  outputs in `inversion_workflow/runs/direct_permeability_prior_sweep/`
- Smooth interval-anchored permeability fit:
  `inversion_workflow/scripts/fit_smooth_permeability_field_from_targets.py` with
  length-scale results in `inversion_workflow/runs/smooth_permeability_fit/`,
  extended length/shift-scale search results in
  `inversion_workflow/runs/smooth_permeability_candidate_search/`, and a run-ready
  dry candidate in `inversion_workflow/runs/candidate_smooth_0p025m_search_driver/`
- OGS-ready observation run preparation and execution wrapper:
  `inversion_workflow/scripts/prepare_ogs_run.py`,
  `inversion_workflow/scripts/audit_ogs_run_inputs.py`,
  `inversion_workflow/scripts/run_ogs_model.py`,
  `inversion_workflow/scripts/sample_ogs_state_outputs.py`, and
  `inversion_workflow/runs/direct_fit_observation_run/`
- OGS environment audit:
  `inversion_workflow/scripts/audit_ogs_environment.py`,
  `inversion_workflow/OGS_ENVIRONMENT_AUDIT.json`, and
  `inversion_workflow/OGS_ENVIRONMENT_AUDIT.md`
- State-observation evaluator and combined objective assembler:
  `inversion_workflow/scripts/evaluate_state_observation_targets.py`,
  `inversion_workflow/scripts/assemble_inversion_objective.py`,
  `state_observation_evaluation.csv`, `combined_objective_components.csv`, and
  `combined_objective_summary.json`
- RH boundary-curve audit:
  `inversion_workflow/scripts/audit_rh_boundary_curve.py`,
  `rh_boundary_curve_audit.csv`, and `rh_boundary_curve_audit_summary.json`
- RH measurement-semantics audit:
  `inversion_workflow/scripts/build_rh_semantics_audit.py`,
  `rh_measurement_semantics_row_audit.csv`,
  `rh_measurement_semantics_sensor_summary.csv`,
  `rh_boundary_curve_semantics.csv`,
  `rh_measurement_semantics_summary.json`, and
  `rh_measurement_semantics.md`
- RH boundary-provenance request package:
  `inversion_workflow/scripts/build_rh_boundary_provenance_request.py`,
  `rh_boundary_provenance_request.csv`,
  `rh_boundary_provenance_evidence.csv`,
  `rh_boundary_provenance_request_summary.json`, and
  `rh_boundary_provenance_request.md`
- RH boundary-candidate curve builder:
  `inversion_workflow/scripts/build_rh_boundary_candidate_curves.py`,
  `rh_boundary_candidate_curves.csv`,
  `rh_boundary_candidate_curve_summary.csv`,
  `rh_boundary_candidate_curve_summary.json`,
  `rh_boundary_candidate_curves.md`, and
  `rh_boundary_candidate_curve_xml/`
- Thermal-expansivity parameter audit:
  `inversion_workflow/scripts/audit_thermal_expansivity_parameter.py`,
  `thermal_expansivity_parameter_audit.csv`,
  `thermal_expansivity_parameter_audit_summary.json`, and
  `thermal_expansivity_parameter_audit.md`
- CTE confirmation request package:
  `inversion_workflow/scripts/build_cte_confirmation_request.py`,
  `cte_confirmation_request.csv`, `cte_confirmation_request_summary.json`, and
  `cte_confirmation_request.md`, with catalogue copies under
  `cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files/`
- Candidate evaluation driver:
  `inversion_workflow/scripts/evaluate_inversion_candidate.py` with verified
  dry-run and execute-mode artifacts in `inversion_workflow/runs/`
- Inversion candidate search driver:
  `inversion_workflow/scripts/run_inversion_candidate_search.py` with ranked dry-run
  artifacts in `inversion_workflow/runs/inversion_candidate_search/`
- Regularized permeability-candidate ranking:
  `inversion_workflow/scripts/rank_regularized_permeability_candidates.py` with
  tradeoff artifacts in
  `inversion_workflow/runs/regularized_permeability_candidate_ranking/`
- Regularized OGS candidate-set handoff:
  `inversion_workflow/scripts/run_regularized_ogs_candidate_set.py` with selected
  run directories and summaries in
  `inversion_workflow/runs/regularized_ogs_candidate_set/`
- Adaptive combined-candidate next-batch planner:
  `inversion_workflow/scripts/build_adaptive_combined_candidate_plan.py` with
  ranked planning artifacts in
  `inversion_workflow/runs/adaptive_combined_candidate_plan/`
- Executed adaptive combined-candidate search:
  `inversion_workflow/runs/adaptive_combined_candidate_search/` plus run
  directories `adaptive_combined_001_length_0p050m`,
  `adaptive_combined_002_length_0p050m_shift_0p750`, and
  `adaptive_combined_003_length_0p075m`
- Repeatable continuous inversion-loop driver:
  `inversion_workflow/scripts/run_continuous_inversion_loop.py` with loop summaries,
  cumulative lower-support evidence, and command logs in
  `inversion_workflow/runs/continuous_inversion_loop/`
- Direct anisotropy sensitivity planner:
  `inversion_workflow/scripts/build_anisotropy_sensitivity_plan.py` with angle/ratio
  sweep artifacts in `inversion_workflow/runs/anisotropy_sensitivity_plan/`
- Local-basis permeability sampler:
  `inversion_workflow/scripts/build_local_basis_sampler_plan.py` with residual-anchor
  direct-objective scores and batch handoff artifacts in
  `inversion_workflow/runs/local_basis_sampler_plan/`, plus executed combined-search
  results in `inversion_workflow/runs/local_basis_sampler_candidate_search/`
- Local anisotropy permeability sampler:
  `inversion_workflow/scripts/build_local_anisotropy_sampler_plan.py` with
  local tensor-orientation/ratio direct-objective scores and batch handoff artifacts
  in `inversion_workflow/runs/local_anisotropy_sampler_plan/`
- Production sampler/convergence audit:
  `inversion_workflow/scripts/build_production_sampler_convergence_audit.py` with
  cross-family evidence, stage-convergence history, scored candidate table,
  executable next-batch handoff, and active-objective stop/continue decision in
  `inversion_workflow/runs/production_sampler_convergence/`
- Current permeability field package:
  `inversion_workflow/scripts/build_current_permeability_field_package.py` with the
  copied accepted mesh, direct and sampled-NMR residual tables, run summaries, tensor
  statistics, caveat note, run-local OGS input snapshot, and SHA256 file manifest in
  `inversion_workflow/current_permeability_field/`
- Current field reproducibility audit:
  `inversion_workflow/scripts/build_current_field_reproducibility_audit.py`,
  `inversion_workflow/current_permeability_field/CURRENT_FIELD_REPRODUCIBILITY_AUDIT.md`,
  and `inversion_workflow/current_permeability_field/current_field_reproducibility_audit.csv`
  verify 19 package, manifest, run-input snapshot, objective, release-gate,
  execution, and field checks with zero required failures.
- Current field visual inspection:
  `inversion_workflow/scripts/build_current_field_visual_inspection.py` with
  six rendered PNG maps and metric summaries under
  `inversion_workflow/current_permeability_field/visual_inspection/`
- Current field selection audit:
  `inversion_workflow/scripts/build_current_field_selection_audit.py`,
  `inversion_workflow/current_field_selection_audit.csv`,
  `inversion_workflow/current_field_selection_audit_summary.json`, and
  `inversion_workflow/current_field_selection_audit.md`
- Conditional field-selection scenarios:
  `inversion_workflow/scripts/build_conditional_field_selection_scenarios.py`,
  `inversion_workflow/conditional_field_selection_scenarios.csv`,
  `inversion_workflow/conditional_field_selection_scenarios_summary.json`, and
  `inversion_workflow/conditional_field_selection_scenarios.md`
- Conditional field-candidate package:
  `inversion_workflow/scripts/build_conditional_field_candidate_package.py` with
  five copied scenario-winning meshes, per-field summaries, 25 extracted diagnostic
  metric-evidence rows, zero missing metric rows, and inventory under
  `inversion_workflow/conditional_field_candidates/`
- Conditional field-difference audit:
  `inversion_workflow/scripts/build_conditional_field_difference_audit.py`,
  `inversion_workflow/conditional_field_candidates/CONDITIONAL_FIELD_DIFFERENCE_AUDIT.md`,
  `inversion_workflow/conditional_field_candidates/conditional_field_difference_summary.csv`,
  and `inversion_workflow/conditional_field_candidates/conditional_field_difference_top_cells.csv`
  compare the four non-current scenario-winning meshes to the current field over
  10,239 `triangle6` cells.
- Final inversion promotion checklist:
  `inversion_workflow/scripts/build_final_inversion_promotion_checklist.py`,
  `inversion_workflow/final_inversion_promotion_checklist.md`, and
  `inversion_workflow/final_inversion_promotion_checklist_summary.json` consolidate
  the promotion gate for calling any field a final all-measurement inversion result.
  Current decision: `do_not_promote_current_field`.
- Final inversion close-out playbook:
  `inversion_workflow/scripts/build_final_inversion_closeout_playbook.py`,
  `inversion_workflow/final_inversion_closeout_playbook.md`, and
  `inversion_workflow/final_inversion_closeout_playbook_summary.json` route the nine
  open promotion criteria to six draft/response actions, one internal NMR policy
  action, and two scenario/final-field decision actions.
- Final objective decision register:
  `inversion_workflow/scripts/build_final_objective_decision_register.py`,
  `inversion_workflow/final_objective_decision_register.md`, and
  `inversion_workflow/final_objective_decision_register_summary.json` record the
  explicit include, diagnostic-only, exclusion, or waiver decision paths needed
  before any open stream can be treated as settled for final field promotion.
- Final objective scenario matrix:
  `inversion_workflow/scripts/build_final_objective_scenario_matrix.py`,
  `inversion_workflow/final_objective_scenario_matrix.md`, and
  `inversion_workflow/final_objective_scenario_matrix_summary.json` map those
  include/exclude choices to nine explicit final-objective options and their current
  winners.
- Final objective include/exclude recommendations:
  `inversion_workflow/scripts/build_final_objective_include_exclude_recommendations.py`,
  `inversion_workflow/final_objective_include_exclude_recommendations.md`, and
  `inversion_workflow/final_objective_include_exclude_recommendations_summary.json`
  record the conservative no-new-evidence recommendation for each open row.  The
  packet recommends diagnostic-only, inactive, or scope-out handling for the
  unresolved external/provenance streams unless accepted provider evidence or an
  explicit modelling decision is recorded, and it does not unblock final promotion.
- Final objective no-new-evidence closeout draft:
  `inversion_workflow/scripts/build_final_objective_no_new_evidence_closeout_draft.py`,
  `inversion_workflow/final_objective_no_new_evidence_closeout_draft.md`, and
  `inversion_workflow/final_objective_no_new_evidence_closeout_draft_summary.json`
  turn the conservative recommendations into exact user/modelling-team review text.
  It contains nine draft decision rows and would select
  `F01_current_raw_nmr_exclude_gated_streams` only after explicit approval and
  regenerated audits. It records no actual decisions, sends no email, does not
  promote the current field, and does not unblock final promotion.
- Final objective no-new-evidence acceptance-record template:
  `inversion_workflow/scripts/build_final_objective_no_new_evidence_acceptance_template.py`,
  `inversion_workflow/final_objective_no_new_evidence_acceptance_record_template.md`,
  and
  `inversion_workflow/final_objective_no_new_evidence_acceptance_record_template_summary.json`
  provide the fillable signoff guardrail for the same F01 path. It currently records
  0/9 approvals, is not ready to apply, records no actual decisions, and does not
  promote the current field.
- Gmail draft send-review packet:
  `inversion_workflow/scripts/build_gmail_draft_send_review_packet.py`,
  `inversion_workflow/gmail_draft_send_review_packet.md`, and
  `inversion_workflow/gmail_draft_send_review_packet_summary.json` consolidate the
  six unsent Gmail drafts covering the seven external gate requests plus the CTE
  confirmation request for user review.
- Measurement-operator coverage audit:
  `inversion_workflow/scripts/build_measurement_operator_coverage.py`,
  `inversion_workflow/measurement_operator_coverage.csv`,
  `inversion_workflow/measurement_operator_coverage_summary.json`, and
  `inversion_workflow/measurement_operator_coverage.md`
- Measurement model-entry matrix:
  `inversion_workflow/scripts/build_measurement_model_entry_matrix.py`,
  `inversion_workflow/measurement_model_entry_matrix.csv`,
  `inversion_workflow/measurement_model_entry_matrix_summary.json`, and
  `inversion_workflow/measurement_model_entry_matrix.md`, with catalogue copies
  under `cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files/`
- Measurement likelihood/activation model:
  `inversion_workflow/scripts/build_measurement_likelihood_model.py`,
  `inversion_workflow/measurement_likelihood_model.csv`,
  `inversion_workflow/measurement_likelihood_model_summary.json`, and
  `inversion_workflow/measurement_likelihood_model.md`
- Measurement stream activation-gate audit:
  `inversion_workflow/scripts/build_measurement_stream_gate_audit.py`,
  `inversion_workflow/measurement_stream_activation_gate_audit.csv`,
  `inversion_workflow/measurement_stream_activation_gate_checks.csv`,
  `inversion_workflow/measurement_stream_activation_gate_audit_summary.json`, and
  `inversion_workflow/measurement_stream_activation_gate_audit.md`, with catalogue
  copies under `cda_knowledge_base/measurements/stream_activation_gate_audit/`
- Measurement gate-closure request package:
  `inversion_workflow/scripts/build_measurement_gate_closure_request.py`,
  `inversion_workflow/measurement_gate_closure_request.csv`,
  `inversion_workflow/measurement_gate_closure_request_summary.json`,
  `inversion_workflow/measurement_gate_closure_request.md`, and
  `inversion_workflow/measurement_gate_closure_email_draft.md`, with catalogue
  copies under `cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files/`
- External gate request pack:
  `inversion_workflow/scripts/build_external_gate_request_pack.py`,
  `inversion_workflow/external_gate_request_pack.csv`,
  `inversion_workflow/external_gate_request_pack_summary.json`,
  `inversion_workflow/external_gate_request_pack.md`, and recipient drafts in
  `inversion_workflow/external_gate_requests/`, with catalogue copies under
  `cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files/`
- External gate response-intake tracker:
  `inversion_workflow/scripts/build_external_gate_response_intake.py`,
  `inversion_workflow/external_gate_response_intake.csv`,
  `inversion_workflow/external_gate_response_intake_summary.json`, and
  `inversion_workflow/external_gate_response_intake.md`, with catalogue copies under
  `cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files/`
- External gate dispatch-readiness audit:
  `inversion_workflow/scripts/build_external_gate_dispatch_audit.py`,
  `inversion_workflow/external_gate_gmail_drafts.csv`,
  `inversion_workflow/external_gate_dispatch_audit.csv`,
  `inversion_workflow/external_gate_dispatch_audit_summary.json`, and
  `inversion_workflow/external_gate_dispatch_audit.md`, with catalogue copies under
  `cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files/`
- Gmail live-state audit for gate requests:
  `inversion_workflow/scripts/build_gmail_gate_live_state_audit.py`,
  `inversion_workflow/gmail_gate_live_state_observations.csv`,
  `inversion_workflow/gmail_gate_live_state_audit_summary.json`, and
  `inversion_workflow/gmail_gate_live_state_audit.md`, with catalogue copies under
  `cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files/`
- External blocker dashboard:
  `inversion_workflow/scripts/build_external_blocker_dashboard.py`,
  `inversion_workflow/external_blocker_dashboard.csv`,
  `inversion_workflow/external_blocker_dashboard_summary.json`, and
  `inversion_workflow/external_blocker_dashboard.md`, with catalogue copies under
  `cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files/`
- Local and Downloads gate recovery audits:
  `inversion_workflow/scripts/build_local_gate_recovery_audit.py`,
  `inversion_workflow/local_gate_recovery_audit.csv`,
  `inversion_workflow/local_gate_recovery_audit_summary.json`,
  `inversion_workflow/local_gate_recovery_audit.md`,
  `inversion_workflow/scripts/build_download_gate_recovery_audit.py`,
  `inversion_workflow/download_gate_recovery_audit.csv`,
  `inversion_workflow/download_gate_recovery_inventory.csv`,
  `inversion_workflow/download_gate_recovery_audit_summary.json`, and
  `inversion_workflow/download_gate_recovery_audit.md`, with catalogue copies under
  `cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files/`
- Internal gate decision register:
  `inversion_workflow/scripts/build_internal_gate_decision_register.py`,
  `inversion_workflow/internal_gate_decision_register.csv`,
  `inversion_workflow/internal_gate_decision_register_summary.json`, and
  `inversion_workflow/internal_gate_decision_register.md`, with catalogue copies
  under `cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files/`
- NMR bound-water sensitivity audit:
  `inversion_workflow/scripts/build_nmr_bound_water_sensitivity.py`,
  `inversion_workflow/processed_observations/nmr_bound_water_target_audit.csv`,
  `inversion_workflow/processed_observations/nmr_bound_water_offset_scenarios.csv`,
  `inversion_workflow/processed_observations/nmr_bound_water_group_offsets.csv`,
  `inversion_workflow/processed_observations/nmr_bound_water_sensitivity_summary.json`,
  and `inversion_workflow/processed_observations/nmr_bound_water_sensitivity.md`
- NMR candidate bias/anomaly sensitivity audit:
  `inversion_workflow/scripts/build_nmr_candidate_bias_sensitivity_audit.py`,
  `inversion_workflow/nmr_candidate_bias_sensitivity_audit.csv`,
  `inversion_workflow/nmr_candidate_bias_sensitivity_offsets.csv`,
  `inversion_workflow/nmr_candidate_bias_sensitivity_label_biases.csv`,
  `inversion_workflow/nmr_candidate_bias_sensitivity_summary.json`, and
  `inversion_workflow/nmr_candidate_bias_sensitivity.md`
- NMR objective decision package:
  `inversion_workflow/scripts/build_nmr_objective_decision.py`,
  `inversion_workflow/nmr_objective_decision.csv`,
  `inversion_workflow/nmr_objective_decision_summary.json`, and
  `inversion_workflow/nmr_objective_decision.md`, with catalogue copies under
  `cda_knowledge_base/measurements/nmr/derived_files/`
- NMR trend/anomaly executable objective package:
  `inversion_workflow/scripts/build_nmr_trend_anomaly_active_objective_ranking.py`,
  `inversion_workflow/nmr_trend_anomaly_active_objective_ranking.csv`,
  `inversion_workflow/nmr_trend_anomaly_active_objective_summary.json`, and
  `inversion_workflow/nmr_trend_anomaly_active_objective.md`, with catalogue copies
  under `cda_knowledge_base/measurements/nmr/derived_files/`
- NMR trend/anomaly follow-up planner:
  `inversion_workflow/scripts/build_nmr_trend_anomaly_followup_plan.py`,
  `inversion_workflow/runs/nmr_trend_anomaly_followup_plan/NMR_TREND_ANOMALY_FOLLOWUP_PLAN.md`,
  `NMR_TREND_ANOMALY_FOLLOWUP_PLAN.json`, and
  `nmr_trend_anomaly_followup_candidates.csv`
- NMR final residual-policy gate:
  `inversion_workflow/scripts/build_nmr_final_residual_policy_gate.py`,
  `inversion_workflow/nmr_final_residual_policy_gate.md`,
  `nmr_final_residual_policy_gate_summary.json`, and
  `nmr_final_residual_policy_gate.csv`, with catalogue copies under
  `cda_knowledge_base/measurements/nmr/derived_files/`. It records that no final
  NMR policy is selected yet, raw absolute theta remains the current-report default
  with caveats, within-label trend/anomaly is the preferred provisional candidate
  policy, and no new trend/anomaly OGS batch is recommended before policy acceptance.
- NMR final residual-policy acceptance-record template:
  `inversion_workflow/scripts/build_nmr_final_residual_policy_acceptance_template.py`,
  `inversion_workflow/nmr_final_residual_policy_acceptance_record_template.md`,
  `nmr_final_residual_policy_acceptance_record_template_summary.json`, and
  `nmr_final_residual_policy_acceptance_record_template.csv`, with catalogue copies
  under `cda_knowledge_base/measurements/nmr/derived_files/`. It records four
  template rows, 0/1 primary approvals, `ready_to_apply_policy=False`, no actual
  decision, no active-objective change, no field promotion, and no new OGS batch
  recommended.
- Cross-stream candidate scorecard:
  `inversion_workflow/scripts/build_cross_stream_candidate_scorecard.py`,
  `inversion_workflow/cross_stream_candidate_scorecard.csv`,
  `inversion_workflow/cross_stream_candidate_scorecard_summary.json`, and
  `inversion_workflow/cross_stream_candidate_scorecard.md`
- Cross-stream hybrid field screen:
  `inversion_workflow/scripts/build_cross_stream_hybrid_field_plan.py`,
  `inversion_workflow/runs/cross_stream_hybrid_field_plan/CROSS_STREAM_HYBRID_FIELD_PLAN.json`,
  `CROSS_STREAM_HYBRID_FIELD_PLAN.md`,
  `cross_stream_hybrid_candidate_scores.csv`, and
  `next_cross_stream_hybrid_candidate_batch.csv`
- Inversion parameter-release plan:
  `inversion_workflow/scripts/build_inversion_parameter_release_plan.py`,
  `inversion_workflow/inversion_parameter_release_plan.csv`,
  `inversion_workflow/inversion_parameter_release_plan_summary.json`, and
  `inversion_workflow/inversion_parameter_release_plan.md`
- Inversion release-gate audit:
  `inversion_workflow/scripts/audit_inversion_release_gates.py`,
  `inversion_workflow/inversion_release_gate_audit.csv`,
  `inversion_workflow/inversion_release_gate_audit.json`, and
  `inversion_workflow/inversion_release_gate_audit.md`, with per-run
  `INVERSION_RELEASE_GATE_AUDIT.*` artifacts written by the candidate driver
- Frozen-model and measurement-inclusion audit:
  `inversion_workflow/scripts/build_frozen_model_measurement_inclusion_audit.py`,
  `inversion_workflow/frozen_model_measurement_inclusion_audit.csv`,
  `inversion_workflow/frozen_model_measurement_inclusion_audit_summary.json`, and
  `inversion_workflow/frozen_model_measurement_inclusion_audit.md`, with catalogue
  copies under
  `../cda_knowledge_base/measurements/model_formulation_audit/derived_files/`
- Objective readiness audit:
  `inversion_workflow/scripts/build_objective_readiness_audit.py`,
  `inversion_workflow/objective_readiness_audit.csv`,
  `inversion_workflow/objective_readiness_audit_summary.json`, and
  `inversion_workflow/objective_readiness_audit.md`, with catalogue copies under
  `../cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files/`
- Open-question resolution matrix:
  `inversion_workflow/scripts/build_open_question_resolution_matrix.py`,
  `inversion_workflow/open_question_resolution_matrix.csv`,
  `inversion_workflow/open_question_resolution_matrix_summary.json`, and
  `inversion_workflow/open_question_resolution_matrix.md`, with catalogue copies under
  `../cda_knowledge_base/measurements/stream_activation_gate_audit/derived_files/`
  and a knowledge-base copy at `../cda_knowledge_base/open_questions_resolution_matrix.md`
- Model provenance/audit note: `MODEL_AUDIT.md`

## Verification

- `pdflatex -> bibtex -> pdflatex -> pdflatex` completed.
- Final `main.pdf` has 36 pages.
- The final LaTeX log has no unresolved citations, fatal errors, warnings matching
  `undefined`, and no overfull or underfull boxes.
- Text extraction from `main.pdf` was checked for unresolved placeholders such as
  `??`, `TODO`, `FIXME`, and stale comment markers.
- Active report citations now use page or section locators. Additional cited
  supporting fulltexts were downloaded or copied from the local catalogue where
  available; blocked sources are listed in `Library/unavailable_fulltexts.md`.
- Local measurement sources used by the measurement chapter now have BibTeX entries
  and Library copies. The source coverage audit currently finds 29 cited keys, 0
  missing BibTeX entries, and 0 cited blocked/fulltext-unavailable keys missing from
  `Library/unavailable_fulltexts.md`. The citation locator audit classifies the
  active citation instances as 56 local fulltexts, 5 official web-documentation
  citations, and 2 unavailable-but-tracked fulltexts.
- A 2026-05-31 source-recovery retry rechecked the remaining active blocked sources
  (`Topp1980TDR` and `Kleinberg1996NMR`) against their publisher/metadata routes and
  retained the returned HTML blocker pages under `Library/fulltexts/`. The inactive
  `Elsayed2020ClayNMR` tracker entry was also refreshed: ACS marks the article as
  open access, but automated PDF retrieval still returns a Cloudflare blocker.
- The anisotropic field generator was smoke-tested against
  `GESA_model_original/projection_on_mesh_2025-09-05/bulk.vtu`; the output VTU
  contained `k_i_rd` as a four-component tensor field on all 10,239 `triangle6`
  elements.
- The observation manifest validator passed: 28 checks across 9 observation groups,
  0 failures. The generated validation report is
  `inversion_workflow/observation_manifest_validation.json`.
- The processed-observation builder generated 16 normalized CSV tables. Key row
  counts are: NMR weekly 170, NMR seasonal profiles 294, ERT timesteps 1,691,
  interpreted permeability 204, permeability pressure decay 6,687, RH Kelvin 4,247,
  and Taupe/TDR EDZ bands 5,088.
- The ERT observation-operator builder made the theta-to-resistivity calibration
  explicit. It wrote 6 fitted power-law relation rows and currently uses
  `kruschwitz_model_data2019` as the default first-test relation:
  `rho_ohm_m = 1.108 * theta_fraction^-1.58`, where
  `theta_fraction = porosity * liquid_saturation`. The direct Niche-4 paired
  NMR/resistivity fit is retained as a high-scatter diagnostic. The ERT report text
  now also cites a local fulltext on shaly-sand electrical conductivity to document
  why clay/surface conduction prevents treating the CD-A resistivity relation as a
  universal saturation transform.
- The ERT spatial-projection lookup builder created the geometry bridge from the ERT
  inversion mesh to the OGS mesh. It reads the reference VTK
  `Niche open/2019/11-2019/dcinv.result_01.vtk`, records 3,126 ERT points and 5,966
  triangular ERT cells, applies the explicit provisional transform
  `model_x = raw_x` and `model_y = raw_y + 500`, and maps ERT cell centroids to OGS
  cells. The lookup has 4,676 rows inside an OGS cell, 2,194 rows inside the
  approximate 1.5 m central support, and 2,035 rows satisfying both conditions. ERT
  still needs transform/support confirmation and an uncertainty/correlation model
  before numerical log-resistivity residuals become active.
- The new run-local ERT resistivity diagnostic
  `runs/direct_fit_observation_run/ert_resistivity_diagnostic.md` samples OGS
  `theta = porosity * saturation` on those 2,035 support cells, converts it with the
  default Kruschwitz relation, and compares against nearest ERT fields within a
  10-day tolerance. It compares 162,800 cell-time rows across 80 OGS output times
  with area-weighted log10 MAE 0.2541801957739222 and RMSE 0.29996586160456457.
  This closes the OGS-output sampling step, but ERT remains diagnostic until the
  transform, exact near-niche support, and uncertainty/correlation gates are accepted.
- The ERT candidate discrimination audit
  `inversion_workflow/scripts/build_ert_candidate_discrimination_audit.py` applies
  that same compact log-resistivity diagnostic to 66 executed OGS runs with output
  fields. Each run compares 162,800 cell-time rows over 80 output times. Across the
  current candidate family, ERT MAE spans 0.019635573360798686 log10 units. The
  ERT-only best run is `broad_continuous_001_001_length_0p023m_shift_1p004` with MAE
  0.25407209193077057, while the best active-objective run
  `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` has ERT MAE
  0.2541796182834413. The combined-objective/ERT-MAE correlation is 0.8894403368395667,
  meaning candidates that fit the active permeability+NMR objective better generally
  do not improve the provisional ERT residual.
- The ERT support-sensitivity audit
  `inversion_workflow/scripts/build_ert_support_sensitivity_audit.py` evaluates six
  representative runs across nine radial support variants inside the current
  provisional 1.5 m ERT mask. The ERT-only broad-continuous run remains the best
  mean support-rank candidate with mean rank 1.67 and worst rank 4.0, but the
  tightest/outer support subsets can swap the winner with
  `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000`. This quantifies the
  support sensitivity without closing the transform/support/covariance gate.
- The ERT semantics audit records the activation split in row-level terms: 1,691
  timestep rows, 1,675 with matching VTK files, 16 blocked by missing VTK matches,
  5,966 projected ERT cells, and 2,035 cells that satisfy both current support
  screens. It records ERT as a log-resistivity residual after theta-to-rho conversion,
  not as measured saturation, water content, pressure, or permeability.
- The Taupe/TDR observation-operator builder made the trend use explicit. It wrote
  5,088 baseline-normalized Taupe rows and 24 sensor/EDZ-band series summaries.
  A3 and A4 are mapped in the current local OGS mesh support, giving 2,544
  trend-ready rows; A7 and A8 are retained but flagged outside the current mesh
  support. Candidate absolute interpretations are recorded only as sanity checks:
  value-as-water-content-percent gives physical mapped-band saturation for 2,120
  rows, Topp-style dielectric conversion for 0 rows, and the local linear dielectric
  mix with `epsilon_rock = 6` for 2,544 rows. Taupe is now evaluated through a
  trend diagnostic for runs with sampled OGS outputs, but absolute residual weights
  still require confirmed Taupe unit/calibration.
- The new run-local Taupe/TDR trend diagnostic
  `inversion_workflow/scripts/evaluate_taupe_tdr_trend_diagnostic.py` now compares
  the mapped A3/A4 Taupe trend rows against sampled OGS
  `theta = porosity * saturation`. For the direct reference run and the current
  local-basis incumbent it compares 1,860 rows across 12 A3/A4 series, marks 684
  mapped Taupe rows outside the available OGS output time horizon, and leaves 2,544
  A7/A8 rows outside the current mesh support. The direct-run standardized trend
  MAE is 1.8632, but this remains diagnostic only and is not assembled into the
  active objective.
- The Taupe/TDR semantics audit adds row, series, and grouped activation files. It
  classifies 2,544 A3/A4 rows as trend-diagnostic-ready after OGS state outputs and
  2,544 A7/A8 rows as outside the current local mesh support. The combined
  state-target table still has 5,088 Taupe/TDR rows and 0 active absolute state
  residuals, so Taupe remains a trend diagnostic until unit/calibration evidence is
  available.
- The Taupe/TDR candidate discrimination audit now runs the same trend diagnostic
  across 74 executed runs with sampled OGS state outputs, including 66 runs with the
  full active combined objective. The cross-run Taupe standardized-trend MAE range is
  only 0.03687076560014302; the best Taupe-only run is
  `adaptive_combined_001_length_0p050m` with MAE 1.829884354078035, while the best
  active-objective run `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` has
  Taupe MAE 1.863211058631399. This makes Taupe a weak discriminator for the current
  executed candidate family, even before the unit/calibration gate is solved.
- The Taupe/TDR series-weight sensitivity audit checks the 12 compared A3/A4
  series across 66 full active-objective runs. Aggregate row weighting, equal-series,
  equal-sensor, equal-EDZ-band, and robust trimmed scores all keep
  `adaptive_combined_001_length_0p050m` as the top trend-screen run, but A3-only and
  A4-only scores pick different winners and the 12 individual series have 8 distinct
  best runs. This makes grouped weighting and sensor-specific uncertainty an explicit
  activation gate rather than an implementation detail; A7/A8 remain outside the
  current local mesh support.
- The cross-stream candidate scorecard joins the 66 common executed runs across the
  active direct-permeability/raw-NMR objective, the NMR bias/anomaly diagnostic, ERT
  log-resistivity MAE, and Taupe trend MAE. No candidate is top-10 in every stream.
  The active incumbent `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` is
  ranked 1st by the active objective but 14th by NMR bias/anomaly, 8th by ERT, and
  29th by Taupe. The best mean-rank compromise is
  `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000`, with mean rank 10.4 and
  worst rank 18, so the current field remains conditional on unresolved diagnostic
  gates rather than a final all-measurement inversion.
- The final inversion promotion checklist now consolidates that stop condition into
  17 explicit promotion criteria. Five pass, one passes with the source-model caveat,
  and two pass only for the active objective; six are blocked by unsent/unanswered
  external requests, one is blocked by the NMR residual-policy decision, and two fail
  final promotion because the field is scenario-unstable and the current selection
  audit refuses final promotion. Its current decision is
  `do_not_promote_current_field`.
- The final close-out playbook turns those nine open criteria into concrete action
  routes: six existing Gmail draft/response paths, one internal NMR default-promotion
  decision, and two scenario/final-field decision steps, with response-note locations,
  acceptance evidence, and refresh commands.
- The final objective decision register adds the missing include/exclude layer for
  the same open criteria. It currently records nine pending or not-ready rows: six
  external stream/provenance decisions, one internal NMR policy decision, and two
  scenario/final-field decisions. Seven rows have an explicit exclusion path, so a
  stream can be kept diagnostic-only only if that decision is recorded and the
  scenario/current-field audits are regenerated.
- The final objective scenario matrix converts those unresolved choices into nine
  explicit final-objective options. The current packaged field wins only the narrow
  raw-NMR objective and the direct-only tie case; all currently scored options that
  promote NMR trend/anomaly or accept ERT or Taupe/TDR select another run. RH,
  other-HM, and endpoint-missing historical permeability remain unscored until their
  provider evidence is filed.
- The final objective include/exclude recommendation packet now records the
  conservative no-new-evidence position: nine recommendations, six external or
  model-provenance rows, one internal NMR policy row, two scenario/final-field rows,
  and eight waivers not recommended. It keeps the current field labelled as the
  active-objective incumbent and explicitly does not unblock promotion.
- The final objective no-new-evidence closeout draft now gives exact decision text
  for a possible conservative closeout. It has nine draft rows and a single-block
  acceptance text that would choose the narrow F01 current raw-NMR scenario only if
  those decisions are approved and the audits are regenerated. It is not an
  approval record and does not change the current field label.
- The no-new-evidence acceptance-record template now turns that draft into a
  concrete signoff checklist: nine rows, 0 approvals recorded, not ready to apply,
  no email action, and no final-field promotion.
- The Gmail draft send-review packet now lists the six unsent draft ids, To/Cc
  routes, subjects, response-note paths, acceptance tests, and short draft previews.
  It is a review artifact only; no mail was sent or modified.
- The cross-stream hybrid field screen tested 15 geometry-preserving magnitude
  blends between the active incumbent and cross-stream diagnostic winner patterns.
  The best hybrid,
  `cross_hybrid_mean_rank_all_streams_plus2_a0p25`, ties the active direct
  permeability objective at 269.818057 with delta 0.0, so it remains a diagnostic
  probe rather than a reason to spend more OGS runs.
- The structural/EDZ field-family screen now tests an explicitly geometric
  alternative family before any additional OGS: central EDZ caps, central shells,
  bedding-parallel bands at the documented 144 degree orientation, and broad
  BCD-A32/BCD-A33 open-twin corridors. It scored 234 run-local fields against the
  direct pulse-test layer, catalogued 30 active permeability support cells, 1,928
  ERT ready-support cells, and the mapped A32/A33 line geometry, and found 0
  improving candidates. The best row,
  `struct_bedding_parallel_band_bed_om0p75_w0p25_a0p5`, ties the active direct
  objective at 269.818057, so the generated batch is marked
  `do_not_run_for_active_objective_without_new_modelling_decision`.
- The permeability residual conflict audit now explains the remaining direct
  pulse-test mismatch for the packaged field. It finds 75 active direct rows,
  weighted RMSE 1.610715 log10(k), 48 rows with absolute residual at least 1 log10,
  21 rows at least 2 log10, and 2 rows above the configured scalar tensor range.
  It also records 24 support cells with repeated active rows and 16 support cells
  where the active observations span at least 1 log10 unit. This points to
  support geometry, gas-to-water interpretation, uncertainty, or an explicitly new
  parameterization before more active-objective OGS sampling.
- The permeability likelihood-policy audit keeps the current rowwise Gaussian
  objective as the recorded active policy, but shows why it should not be mistaken
  for a pure field-search residual: the top 10 rows contribute 49.4% of the direct
  Gaussian loss, 16 support-cell groups have at least 1 log10 observed range, and
  collapsing rows to their duplicate-weighted support-cell means changes the
  objective-like value from 269.818057 to effectively zero. Robust tails,
  support-cell aggregation, or scalar-range outlier handling now require an explicit
  modelling-team likelihood decision.
- The permeability support lower-bound audit now proves the same point as a
  field-search limit: under the current one-value-per-support-cell map, the accepted
  field's direct row-Gaussian objective is 269.818057 and the single-support lower
  bound is also 269.818057, leaving zero same-support reducible gap. All 30 support
  groups are already at their lower bound; 16 groups span at least 2 log10 units and
  the top two groups carry 35.6% of the direct loss. More same-support OGS sampling
  cannot reduce that part of the active objective without a support mapping,
  measurement interpretation, likelihood, bound, or tensor-shape decision.
- The permeability likelihood decision request now makes that decision actionable:
  it lists five options (`keep_rowwise_gaussian_default`,
  `use_robust_row_likelihood`, `aggregate_by_model_support_cell`,
  `gate_configured_scalar_outliers`, and `new_parameterization_before_more_ogs`)
  and keeps `keep_rowwise_gaussian_default` as the current-report policy until a
  non-default policy is explicitly approved.
- The configured-scalar outlier disposition now classifies the two active rows
  outside the configured scalar tensor envelope. They are one duplicated BCD-A32
  0.87 m high-permeability value, only 0.107 log10 above the configured upper
  envelope, but mapped to support cell 4648 where active values span 6.949 log10.
  The local recommendation is therefore no immediate eigenvalue-bound widening or
  tensor-shape release from these rows alone; they remain a visible policy caveat
  under the rowwise Gaussian default.
- The no-OGS permeability likelihood scenario rerank now scores 522 existing
  materialized VTU fields under the diagnostic likelihood policies. The current
  accepted field is one of 40 active row-Gaussian best ties. Huber and Student-t
  keep their winners inside that tie set, while capped row loss, support-cell
  median aggregation, and configured-scalar inside-only scoring select winners
  outside it. Use this as likelihood-decision evidence; refresh it only if the
  accepted formula changes.
- The permeability likelihood winner cross-stream audit now checks those policy
  winners against executed-run scorecard evidence. Four of seven policy-winner
  rows have cross-stream evidence, representing two unique fields; all three
  outside-tie non-default winners are direct-only fields with no OGS/state/ERT/
  Taupe/NMR scorecard row. The row-Gaussian representative has active rank 45 and
  mean all-stream rank 30.4, while the current accepted field has active rank 1 and
  mean all-stream rank 13.2. Do not promote a direct-only non-default winner
  without OGS execution and stream diagnostics.
- The permeability next field-fit gate now turns those checks into explicit
  next-action rules. It records eight gates and the recommendation
  `pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes`.
  Under the current rowwise Gaussian policy, no same-support active-objective OGS
  batch is executable now. Reopening OGS spending requires an approved likelihood,
  support mapping, configured-bound/tensor-shape, or measurement-stream objective
  change; direct-only non-default policy winners require OGS/state/diagnostic
  evidence before any promotion.
- The permeability likelihood/support recommendation packet now consolidates the
  direct-permeability stop rule into eight decision-support rows. It keeps
  `keep_rowwise_gaussian_default` as the current-report policy, records zero
  same-support reducible gap, no same-support batch executable now, no immediate
  bounds or tensor-shape release, and no final-promotion unblocking from this
  packet.
- The permeability likelihood-policy acceptance-record template now adds the
  fillable signoff guardrail for those five policy options. It records five
  template rows, 0/1 primary approvals, `ready_to_apply_policy=False`, no actual
  decision, no active-objective change, no field promotion, and no same-support OGS
  spending unblocked.
- The other HM monitoring inventory builder parsed the large
  `VisualisationCDA.dat` Tecplot file and structured the secondary pressure and
  deformation evidence. It wrote 84 layout zones, 11 text labels, 12 precision
  levelling displacement rows, and 10 qualitative validation targets from the 2026
  minutes, modelling slides, levelling slides, and HERMES input note. The stream now
  has status `layout_and_qualitative_targets_ready_numeric_series_missing`; the
  remaining blocker is locating Geoscope mini-piezometer/extensometer/crackmeter
  series and laser-scan statistical exports before assigning hard residual weights.
- The other-HM missing-export request builder now makes that blocker actionable. It
  writes 6 request rows for Geoscope mini-piezometer, extensometer, crackmeter,
  boundary/context, laser-scan statistical interpretation, and full levelling survey
  exports, plus 8 evidence rows from the TD minutes, BGR modelling slides, levelling
  slides, and HERMES input note. Active objective rows remain 0 until numeric exports
  and support metadata are available.
- The other-HM numeric source audit verifies the local absence claim. It scans 10
  other-HM source files, 7 PDF ZIP members, extracted text, Tecplot support geometry,
  and extracted levelling rows. All 6 missing-export request classes have local
  support geometry or extracted labels, but 0 are hard-residual-ready. The scan found
  1 numeric-extension source file, `VisualisationCDA.dat`, which is support geometry,
  and 0 numeric-candidate ZIP members. The levelling slide summary remains a
  12-row sign/order-of-magnitude check, not a full weighted survey residual.
- The mesh lookup script parsed the projection bulk mesh directly and generated:
  107 measurement point lookups, 35 borehole endpoint lookups, 341 borehole/Taupe
  line samples across 8 segments, and 10,239 bulk-cell centroids. The lookup summary
  flags 50 of 107 catalogue measurement points as outside the local `[-5,5]` by
  `[-5,5]` OGS mesh bounding box.
- The direct permeability target builder mapped the 204 interpreted pulse-test rows
  into first-pass inversion targets. It marks 75 rows as usable for the current local
  OGS fit, 27 rows as mapped outside the current mesh, 98 rows as missing segment
  geometry, and 4 rows as missing/non-positive interpreted permeability. The
  missing-geometry rows are now grouped into a 5-entry audit that retains
  source-backed orientation evidence for BCD-A24/25/26/27 and BFM-D19 without
  converting those rows into unsupported cell targets.
- The endpoint request builder now turns that five-segment geometry gap into a
  concrete external request package. It lists requested start/end labels for
  BCD-A24, BCD-A25, BCD-A26, BCD-A27, and BFM-D19, keeps all 98 blocked rows in a
  row-level table, and records that the collected workbooks/PDF provide values and
  orientation but not labelled endpoint coordinates.
- The permeability semantics audit now records the physical interpretation gate for
  all 204 interpreted rows: 200 positive rows, 75 active direct candidates, 27
  outside-mesh rows, and 98 rows blocked by missing endpoint geometry. It labels the
  active value as a nitrogen pulse-decay scalar interval observation of intrinsic
  permeability and explicitly excludes hydraulic conductivity, liquid relative
  permeability, saturation, and direct tensor-component interpretations.
- The state-observation target builder generated 11,490 non-permeability target rows
  and 11,311 target-to-cell/sample rows. This includes 170 mapped weekly NMR rows, 294
  seasonal NMR rows with 117 mapped in the current Niche-4 mesh, 4,247 RH
  Kelvin-pressure boundary-forcing rows, 5,088 Taupe/TDR semi-quantitative EDZ-band
  rows, and 1,691 ERT open-niche field-comparison rows.
- The permeability evaluator compared the smoke-test `k_i_rd` tensor field with the
  direct target layer. Duplicate-aware effective objective weight is 52 rows; weighted
  RMSE is 2.70 log10 permeability units. A best single global multiplier of 16.92
  only reduces RMSE to 2.40 log10 units, showing that the first field is a prior
  diagnostic rather than a fit.
- The direct permeability field-fit diagnostic adjusted 30 selected cells while
  preserving tensor orientation/anisotropy. It reduced the duplicate-aware direct
  target RMSE from 2.70 to 1.61 log10 units, with applied log10 multipliers from
  -1.48 to +5.80. This is a traceable target-field diagnostic, not an OGS inversion.
- The direct permeability prior/proposal sweep generated and evaluated 12
  heterogeneous anisotropic fields against the direct pulse-test objective. The best
  generated prior has objective 605.00 and weighted RMSE 2.41 log10 units; its best
  uniform multiplier is only 1.15 and does not materially improve RMSE. This confirms
  that the direct pulse-test data need local interval-tied structure rather than only
  a global multiplier or generic random anisotropic prior.
- The smooth interval-anchored permeability fit generated five Gaussian-smoothed
  target-multiplier fields. The best length scale is 0.05 m: it affects 471 cells,
  preserves tensor orientation/anisotropy by scalar multiplication, and reaches
  objective 291.29 with weighted RMSE 1.67 log10 units. Larger length scales smooth
  too broadly and increase RMSE up to 2.13 at 0.80 m. The 0.05 m field was also
  prepared through the candidate driver as `candidate_smooth_0p050m_driver`.
- The extended smooth candidate search generated 18 length/shift-scale candidates.
  The best direct candidate is the 0.025 m full-shift field: it affects 208 cells,
  preserves tensor orientation/anisotropy, and reaches objective 269.97 with weighted
  RMSE 1.61 log10 units. It was prepared through the candidate driver as
  `candidate_smooth_0p025m_search_driver`. Damped-shift candidates are retained as
  deliberately under-fit regularized proposals for later OGS/state-observation
  comparison.
- The regularized permeability-candidate ranking separates direct pulse-test misfit
  from field-update complexity for the 18 smooth candidates. The Pareto tradeoff
  candidates are all 0.025 m support fields: full shift, 0.75 shift, and 0.5 shift.
  Under a weak update penalty the full-shift candidate remains preferred; under a
  moderate update penalty the 0.75-shift candidate is preferred; under a strong update
  penalty the 0.5-shift candidate is preferred. These scores are explicitly
  mesh-resolution-dependent selection aids, not calibrated geological priors, and are
  meant to choose multiple candidates for first OGS state-observation comparison.
- The regularized OGS candidate-set handoff now executed all three
  Pareto/scenario-winner fields through Dockerized Apptainer. The selected run
  directories are `regularized_ogs_candidate_001_length_0p025m`,
  `regularized_ogs_candidate_002_length_0p025m_shift_0p750`, and
  `regularized_ogs_candidate_003_length_0p025m_shift_0p500`. All three carry the same
  copied-submesh `meshio` warning tracked by the direct-run input audit, have
  release-gate status `pass`, 83 OGS output VTUs, 37,184 sampled state rows, and 192
  active sampled NMR state rows. The combined objectives are 3166.61, 3198.49, and 3289.65 respectively;
  the NMR state term is similar across the three, so this first combined ranking is
  still driven mainly by the direct permeability component.
- The first adaptive combined-candidate batch executed the top broader-support
  proposals through the same Dockerized-Apptainer harness. `length_0p050m`,
  `length_0p050m_shift_0p750`, and `length_0p075m` each produced 83 OGS output VTUs,
  37,184 sampled state rows, and 192 active NMR objective rows. Their combined
  objectives are 3276.57, 3300.91, and 3353.88 respectively, so none improves on the
  earlier `length_0p025m` objective of 3166.61. The sampled NMR state objective was no
  longer flat over that six-candidate set; broader 0.05--0.075 m support worsens
  the current NMR residual layer.
- The local-refinement permeability grid around the then-best 0.025 m field adds
  0.0125--0.0375 m support lengths with 0.875/1.0/1.125 shift scaling. The top direct rows are
  `length_0p013m` and `length_0p019m`, both with objective 269.82 and weighted RMSE
  1.61 log10 units.
- The first local-refinement execute-mode batch ran `length_0p013m` and
  `length_0p019m` through the full OGS harness. Each produced 83 OGS output VTUs,
  37,184 sampled state rows, and 192 active NMR objective rows. Their combined
  objectives are 3159.66 and 3164.96 respectively.
- The first local-bracketing execute-mode batch ran `length_0p013m_shift_0p875`,
  `length_0p013m_shift_1p125`, and `length_0p031m`. Each produced 83 OGS output VTUs,
  37,184 sampled state rows, and 192 active NMR objective rows. Their combined
  objectives are 3167.34, 3167.21, and 3219.35 respectively, so none improves on
  `length_0p013m`.
- The finite-candidate Bayesian proposal batch then ran
  `length_0p019m_shift_1p125`, `length_0p019m_shift_0p875`, and
  `length_0p025m_shift_1p125` through the same OGS harness. Each produced the normal
  state-output and sampling products and passed the release gate. Their combined
  objectives are 3172.69, 3172.37, and 3173.39 respectively, so none improves on
  `length_0p013m`.
- The first continuous smooth-field proposal batch then ran
  `length_0p006m_shift_0p992`, `length_0p007m`, and
  `length_0p007m_shift_0p972` through OGS. All three passed the release gate and
  sampled 192 active NMR objective rows. Their combined objectives are 3156.78,
  3157.74, and 3158.16 respectively, so the best continuous row improves on the
  previous `length_0p013m` best by about 2.88 objective units.
- A lower-support continuous batch then ran `length_0p004m_shift_0p995`,
  `length_0p003m_shift_0p986`, and `length_0p004m_shift_0p994`. All three passed
  the release gate and sampled 192 active NMR objective rows. Their combined
  objectives are 3156.38, 3156.47, and 3156.38 respectively, making
  `length_0p004m_shift_0p995` the best field at that stage.
- A repeatable lower-support continuous loop was then added in
  `inversion_workflow/scripts/run_continuous_inversion_loop.py`. The first loop
  iteration refreshed the lower-support proposal, executed
  `length_0p003m_shift_1p006`, `length_0p005m_shift_0p985`, and
  `length_0p004m_shift_1p014`, merged those rows into
  `inversion_workflow/runs/continuous_inversion_loop/lower_support_cumulative_search_results.csv`,
  and regenerated the planning/readiness artifacts. All three passed the release
  gate and sampled 192 active NMR objective rows. Their combined objectives are
  3156.37, 3156.49, and 3156.44 respectively, so the current best is
  `length_0p003m_shift_1p006` with objective 3156.37.
- The second lower-support loop then executed `length_0p004m_shift_0p992`,
  `length_0p004m_shift_1p020`, and `length_0p006m_shift_0p975`. All three passed
  the release gate and sampled 192 active NMR objective rows. Their combined
  objectives are 3156.40, 3156.53, and 3156.70 respectively, so none improves on
  `length_0p003m_shift_1p006`.
- A broad continuous evidence batch then executed `length_0p023m_shift_1p004`,
  `length_0p022m_shift_0p998`, and `length_0p021m`. All three passed the release
  gate and sampled 192 active NMR objective rows. Their combined objectives are
  3159.06, 3169.30, and 3169.31 respectively, so none improves on
  `length_0p003m_shift_1p006`. The first row is still useful evidence because it
  removes the previous broad uncertainty-driven top proposal.
- The generalized continuous-loop driver then ran a repeatable broad iteration over
  `length_0p015m`, `length_0p016m_shift_0p968`, and `length_0p010m`. All three
  passed the release gate and sampled 192 active NMR objective rows. Their combined
  objectives are 3161.36, 3165.33, and 3157.70 respectively, so the incumbent remains
  `length_0p003m_shift_1p006`.
- The adaptive planner still treats 32 smooth-family executed candidates as evidence
  and writes `executed_candidate_evidence.csv`. The next proposed local batch is led by
  `length_0p008m_shift_1p011`, `length_0p007m_shift_1p020`, and
  `length_0p007m_shift_1p022`; these are proposals only until run through OGS.
- The finite/continuous candidate Bayesian proposal layer now records the 32
  executed candidates as evidence and retains all 32 in the generated-candidate score
  table, including 3 reconstructed fallback feature rows from executed search
  results whose proposal directories had been overwritten. After the broad loop, the
  finite-candidate Bayesian proposal top is `length_0p003m_shift_0p972` with
  effectively zero probability of improvement. The refreshed broad continuous plan
  now proposes `length_0p009m_shift_0p979`, `length_0p008m_shift_1p040`, and
  `length_0p010m_shift_1p050`, while the refreshed lower-support continuous plan proposes
  `length_0p003m_shift_0p972`, `length_0p004m_shift_1p031`, and
  `length_0p006m_shift_0p970`. This is still a proposal layer, not a production
  sampler.
- The anisotropy sensitivity planner tested 35 global angle/ratio perturbations of
  the incumbent `length_0p003m_shift_1p006` field while preserving each cell's
  geometric-mean permeability. The best direct pulse-test candidate is the baseline
  tensor itself, `anis_theta_144p0_ratio_2p50`, with objective 269.83549 and zero
  improvement over the input field. The nearest angle perturbation,
  `anis_theta_140p0_ratio_2p50`, is already worse by 0.05086 objective units, so a
  global anisotropy-angle/ratio-only OGS batch is not justified by the direct
  permeability layer.
- The local-basis sampler scored 131 residual-anchor candidates around the incumbent
  field, using 30 basis anchor cells and preserving the frozen OGS model. The best
  direct candidate is `basis_004_det_l_0p0015_s_1p000`, with direct objective
  269.81806, delta -0.01743 against the baseline direct objective, and weighted RMSE
  1.610715 log10 units. Its three-candidate OGS batch then executed successfully:
  all three runs returned code 0, passed the release gate, and sampled 192 active NMR
  rows. The best row is `basis_024_det_l_0p0075_s_1p000` with combined objective
  3156.35307, so the executed combined-candidate count reached 35 at that stage and
  this row remains the current accepted best.
- Five production sampler handoff rounds then executed thirty additional
  candidates through the same OGS harness: six smooth rows in round 1, five
  local-basis rows plus one smooth row in round 2, four smooth rows plus two
  local-basis rows in round 3, and five smooth rows plus one local-basis row in
  round 4, followed by six smooth rows in round 5. All thirty returned code 0, passed the release
  gate, produced the expected OGS VTUs, and sampled 192 active NMR objective rows.
  The best production row is still `basis_023_det_l_0p0075_s_0p750` with combined
  objective 3156.35476, and round 5's best row is
  `length_0p004m_shift_1p031` at 3156.78544, so the production rounds still do
  not improve the accepted local-basis incumbent
  `basis_024_det_l_0p0075_s_1p000` at 3156.35307.
- The production sampler/convergence audit now standardizes 65 accepted OGS rows
  across smooth and local-basis families, writes a stage-by-stage best-so-far
  history, and scores a 394-row cross-family candidate pool. Of the 329 unexecuted
  rows, 210 have materialized mesh files and are eligible for an executable handoff;
  119 random local-basis diagnostics are retained in the score table but excluded
  from the batch because no mesh file was written for them. The refreshed top
  executable handoff row is `length_0p007m_shift_1p020`, with lower-confidence-bound
  objective 3156.94007 and diagnostic probability of improvement 0.0166. The
  surrogate cross-validation state-objective RMSE is 10.43, so any next batch should be
  interpreted as convergence evidence, not as a final inversion claim. The generated
  stop/continue decision recommends `pause_active_production_sampling` for the active
  direct-permeability plus NMR objective, because all pause criteria are satisfied.
- The OGS run-preparation smoke test created
  `inversion_workflow/runs/smoke_test/`. Its `bulk_w_projections.vtu` contains
  `k_i_rd` with shape `(10239, 4)` and `n_rd` with shape `(10239, 1)`, matching the
  projection XML's mesh-field requirements.
- The OGS-ready direct-fit observation run created
  `inversion_workflow/runs/direct_fit_observation_run/` from the fitted mesh. Its
  run-local `05_time_loop_TRM.xml` activates output variables `pressure`,
  `saturation`, `temperature`, `displacement`, and `porosity` for later
  measurement-observation comparison. The source GESA model is unchanged.
- The OGS run-input audit confirms that project mesh files exist, process-variable
  mesh references resolve, required output variables are requested, and the active
  `bulk_w_projections.vtu` contains `k_i_rd` and `n_rd`. It now flags status
  `run_inputs_ogs_accepted_with_meshio_submesh_warnings`: the copied
  boundary/support VTU headers and bulk-id arrays are intact, and the recorded
  Dockerized-Apptainer OGS execution returned code 0, but `bulk_all.vtu` and the
  copied boundary/support VTUs still fail local `meshio` decoding due appended
  base64 padding. Regenerate those submeshes with `identifySubdomains` if downstream
  Python tooling must read them through `meshio`.
- No host `ogs` executable was found on `PATH` or under the local search paths. The
  file-transfer catalogue does contain the BGR/Gesa SIF
  `cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/apptainer_ogs6.5.4.sif`,
  whose embedded metadata identifies `ogs/ogs@6.5.4`
  (`cb5b3235101edecf3ba55e1039fe3c19bc13c636`).
- The OGS environment audit searched `PATH`, `/usr/bin`, `/usr/local/bin`, `/opt`,
  `/home/ber0061`, and the collected file-transfer/measurement folders. It records
  status `ogs_container_found_runtime_available`: the SIF is present, no host
  Apptainer/Singularity/`run-singularity` runtime is installed locally, and the
  preferred backend is the already used Dockerized-Apptainer path
  `docker_apptainer_sif` through `/usr/bin/docker` and
  `ghcr.io/apptainer/apptainer:latest`.
- The collected SIF now runs successfully through `ghcr.io/apptainer/apptainer:latest`
  via Dockerized Apptainer. The direct-fit observation run completed with return code
  0, wrote 83 VTU outputs from model time 0 to 140,000,000 s, and recorded
  `execution_backend: docker_apptainer_sif`.
- The post-run state sampler reads full OGS VTU output sets. Because OGS output VTUs
  contain pressure, saturation, temperature, and displacement but not an explicit
  porosity field, the sampler uses fixed support-mesh cell field `n_rd` from
  `bulk_w_projections.vtu` as the porosity fallback. The direct and regularized
  executed runs each produce 37,184 sampled state rows.
- The state-observation evaluator now activates sampled NMR residuals where output
  times and fixed support quantities are usable. For the best lower-support loop
  candidate, 192 NMR rows are active in the state objective with state objective
  2886.54; 4,247 RH rows remain boundary forcing, 1,691 ERT rows require external
  projection/support confirmation, 95 rows are outside time tolerance, and 5,265 rows
  are not usable for the current state fit.
- The combined objective assembler now writes two active components for the best
  executed local-basis candidate: 75 direct permeability rows with objective 269.82
  and 192 sampled NMR state rows, for total active objective 3156.35307.
- The RH boundary-curve audit compared 2,280 RH-derived Kelvin pressure rows against
  the active OGS open-niche curve. It flags 1,948 later RH rows as outside the active
  curve time range and 19 rows as low-RH outliers. Median absolute residual over the
  overlap is 13.00 MPa, so the curve should be treated as an existing boundary
  condition needing provenance/audit rather than a verified reconstruction of the
  collected OT_RH5--8 workbooks.
- The RH semantics audit makes that provenance problem row-level and invertible. It
  records 4,228 valid non-low-outlier RH rows, 2,492 open-twin rows above the 95%
  thermo-hygrometer caution threshold, 1,736 preferred-range rows, and an active-curve
  implied RH span of 70.23--96.59%. Of 845 active curve rows, 772 imply RH below the
  clean RH5/RH6 workbook minimum, so the curve may be older/filtered/different
  boundary data but is not a direct reconstruction of the current OT_RH5--8 sheets.
- The RH provenance request package turns that mismatch into six BGR/Gesa questions
  and ten evidence rows. It asks for the active curve source data/script, time axis and
  extension policy, sensor screening, Kelvin constants, open/closed curve mapping, and
  retention-calibration policy. The active curve spans 2019-09-18 to 2023-12-26 in
  model time; copied RH workbook rows continue to 2025-09-04.
- The new RH boundary-candidate curve builder writes six reproducible local
  RH-derived curve policies and OGS-style XML snippets. The policy-preferred
  candidate is `rh5_rh6_median`; it has 1,063 daily rows from 2021-12-16 to
  2025-09-04, 576 overlap rows against the active curve, 487 post-active-curve
  extension rows, and overlap MAE 15.15 MPa. These are candidate forcings and
  extension evidence only; they do not replace the active curve until the provenance,
  sensor-selection, time-axis, conversion-constant, and extension-policy gates are
  answered.
- The RH boundary uncertainty-envelope audit compares those six candidate policies
  day by day. It writes `rh_boundary_uncertainty_envelope.csv`,
  `rh_boundary_uncertainty_audit.csv`, `rh_boundary_uncertainty_summary.json`, and
  `rh_boundary_uncertainty.md`, with catalogue copies under the suction/RH
  `derived_files` folder. Across 1,064 envelope dates, 577 overlap the active curve
  and 487 extend beyond it. In the overlap, the candidate pressure envelope has p50
  width 2.10 MPa and p90 width 2.20 MPa, while the active curve is outside that
  local RH-derived envelope on 575 of 577 dates and has 15.22 MPa mean absolute
  mismatch to the envelope median. This quantifies the boundary uncertainty but does
  not activate RH as a likelihood term.
- The candidate evaluation driver was verified on the direct-fit diagnostic mesh in
  `inversion_workflow/runs/candidate_direct_fit_driver/` and on the current best
  smooth-search mesh in `candidate_smooth_0p025m_search_driver/`, then used in
  execute mode for the regularized, adaptive, local-refinement, continuous-loop, and
  local-basis candidate sets. It
  prepares run copies, audits run inputs, runs the inversion release-gate audit,
  evaluates direct permeability, records or executes the OGS command, samples
  state-output directories, audits the RH boundary curve, evaluates state targets, and
  assembles the combined objective. The best executed smooth-family candidate remains
  `length_0p003m_shift_1p006` with combined objective 3156.37; the best executed
  candidate overall is now the local-basis row `basis_024_det_l_0p0075_s_1p000` with
  combined objective 3156.35307 from direct permeability plus sampled NMR rows.
- The inversion candidate search driver evaluated the top four smooth-search meshes
  through the full dry-run candidate harness and ranked them in
  `inversion_workflow/runs/inversion_candidate_search/`. The current dry ranking is
  permeability-only because these search runs did not execute OGS: `length_0p025m` remains first
  with objective 269.97, followed by `length_0p050m` at 291.29 and the 0.75
  shift-damped variants at 301.16 and 329.40. All four refreshed search candidates
  have release-gate status `pass`. The adaptive execute-mode search now uses this
  same driver and confirms that the first broader-support batch is worse than the
  0.025 m regularized best, the local-refinement execute-mode batch improves the
  smooth-field best to `length_0p013m`, and the later local-basis execute-mode batch
  slightly improves the active best to `basis_024_det_l_0p0075_s_1p000`.
- The measurement-operator coverage audit writes one row for each of the 9 observation
  groups. For the best executed local-basis candidate, two groups have active
  objective rows: 75 direct permeability pulse-test rows and 192 sampled NMR rows.
  ERT now has calibration, spatial lookup, direct-run and 66-run log-resistivity
  diagnostics, but still needs transform/support/uncertainty confirmation before
  assigning residual weights, Taupe/TDR has a trend operator but still needs
  absolute unit/calibration confirmation, RH is audited as boundary
  forcing with a provenance mismatch, and the coordinate, bedding, model projection,
  and other-HM rows are support or structured validation layers. Other HM contributes
  22 model-facing validation rows but 0 active objective rows.
- The measurement likelihood/activation model writes 7 stream-level rows that record
  the residual form, transform, scale/weighting rule, bias or model-error terms, and
  activation gate for each measurement class. It confirms that direct permeability
  and NMR are active now: 267 total objective rows, made of 75 direct permeability
  rows and 192 sampled NMR rows. The bound-water sensitivity audit
  rules out a naive absolute theta residual: 162 of 287
  usable mapped NMR rows exceed fixed `phi=0.105` before correction, usable-row
  required-offset p95 is 0.0402, and the best tested uniform subtraction still leaves
  7 nonphysical usable rows. The new 66-run NMR candidate bias/anomaly audit shows
  this matters for field ranking: the current raw absolute-theta best remains
  `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000`, but both the per-label
  bias and within-label anomaly diagnostics are led by
  `broad_continuous_001_003_length_0p021m`, with diagnostic combined objective
  505.614305828437 and current-vs-label-bias rank correlation 0.6351529067946979.
  The NMR objective decision package now recommends within-label trend/anomaly
  residuals as the first provisional final NMR likelihood. The objective assembler
  now has an explicit `nmr_within_label_trend_anomaly` mode and a separate executable
  ranking package that validates against the diagnostic audit to numerical roundoff
  without overwriting the historical raw-objective files. Under that recommended
  treatment, the raw-objective incumbent is rank 14 and the best trend/anomaly run
  `broad_continuous_001_003_length_0p021m` is rank 56 in the raw active objective,
  so the residual definition materially changes candidate selection. The current
  internal policy is explicit: do not promote this mode to the default objective for
  the present report state; keep it as scenario/provisional likelihood evidence
  unless the modelling team reopens that decision. The NMR final residual-policy
  acceptance template now records the four selectable residual policies, 0/1
  primary approvals, no actual decision, no active-objective change, no field
  promotion, and no new OGS batch recommendation.
  A promoted-mode follow-up screen now checks 489 unique candidate-pool rows and
  305 unevaluated runnable mesh files; it recommends
  `pause_new_trend_anomaly_ogs_batch` because the best unevaluated direct-objective
  advantage is only 0.011975, below the 0.739495 materiality threshold from the
  observed NMR trend/anomaly state-objective spread, and no unevaluated candidate
  beats the incumbent under the median observed NMR state term.
  ERT and Taupe/TDR remain forward-operator diagnostics
  until support/calibration choices are confirmed; RH remains a boundary-condition
  provenance audit; other-HM residuals remain inactive because the local numeric
  source audit found 0 hard-ready request classes.
- The measurement stream activation-gate audit makes those activation decisions
  explicit as 20 stream gate checks. It records 2 active streams with tracked caveats,
  2 diagnostic-only streams, 1 boundary-audit-only stream, 1 stream not ready for
  hard residuals, and 2 support layers. There are 7 required failed gates: ERT
  transform/support and uncertainty, Taupe unit/calibration, RH active-curve
  provenance and uncertainty, and other-HM numeric/metadata readiness. This is the
  current machine-readable blocker list for promoting diagnostic streams into hard
  residuals.
- The local gate recovery audit now rescans the collected source files, extracted
  ZIP/workbook/PDF text, and source indexes before treating those failed stream
  gates as external-only. It checked 2540 local source/index documents and recorded
  4553 keyword evidence rows, including 62 keyword-only candidates, but found 0
  possible gate-closing evidence rows. The same 7 gates therefore remain external
  blockers unless provider answers/files arrive or new local files are added.
- The Downloads recovery audit now applies the same open-gate checks to raw
  `/home/ber0061/Downloads` content without treating it as curated catalogue
  evidence. It scanned 533 CD-A/HERMES-relevant filename/archive/Office/text
  documents, recorded 381 keyword evidence rows, found 0 possible gate-closing
  evidence rows, and records 25 SHA1-verified duplicate/catalogue rows plus one
  uncatalogued extracted/run-output directory (`/home/ber0061/Downloads/CDA_N4_2D_250403`).
  The duplicate rows include `ERT_meas_Niche_open (1).zip`,
  `ERT_meas_Niche_open (2).zip`, and `003_Nov_2025 (1).zip`.
- The measurement gate-closure request package turns those blockers into 13 concrete
  requests: 9 high-priority and 4 medium-priority items. Seven are external requests
  for BGR/provider files or confirmations, and six are internal modelling decisions
  that may still need BGR confirmation. The high-priority set covers ERT
  transform/support and uncertainty, Taupe unit calibration, RH active-curve
  provenance and uncertainty policy, other-HM numeric exports/metadata, and the final
  NMR bound/interlayer-water residual definition. A separate email-ready draft is in
  `inversion_workflow/measurement_gate_closure_email_draft.md`.
- The external gate request pack splits the seven external rows into five
  recipient-specific drafts, contact-routing fields, and a tracking CSV. The drafts cover BGR ERT
  transform/support and covariance, BGR other-HM numeric exports and metadata, BGR
  RH/OGS boundary-curve provenance, Taupe/TDR workbook calibration, and historical
  permeability endpoint geometry. Suggested `To` routes are now present for all five
  drafts. The ERT draft routes through `Gesa.Ziefle@bgr.de` with
  `Markus.Furche@bgr.de` as suggested CC; the other four route through Gesa with
  explicit forwarding caveats because no more specific provider sender was resolved
  locally. Its status is
  `external_gate_request_pack_generated_not_sent`, so it is an outbound-request
  artifact rather than evidence that the external gates are closed.
- The external gate response-intake tracker records where incoming answers/files
  should be filed and what must be refreshed after each response. It created
  stream-local `provider_responses/` folders under ERT, other-HM monitoring,
  suction/RH, Taupe/TDR, and permeability pulse-test source catalogues. Its status is
  `external_gate_response_intake_generated_waiting_for_responses`, with seven
  missing responses and seven non-overwriting response-note templates.
- The external gate dispatch-readiness audit checks the request-pack rows,
  recipient drafts, response-intake rows, acceptance tests, refresh commands, and
  response-note templates before sending. Its status is
  `external_gate_dispatch_gmail_drafts_created_waiting_user_send_and_responses`:
  all seven request rows are ready across the five drafts, suggested `To` routes
  exist for all seven request rows, zero dispatch checks fail, five Gmail drafts now
  exist and cover all seven external request rows, the requests are still not sent,
  and seven responses remain missing.
- A 2026-06-01 03:55:46 CEST Gmail live-state connector check found all five external
  gate drafts plus the separate CTE confirmation draft still present as Gmail
  drafts. The sent-subject search returned 0 sent copies, the recent provider-reply
  search returned 0 messages from the named Gesa/Markus/Tuanny routes, and the recent
  CD-A/HERMES/TeamBeam context search returned only the six generated drafts. The
  response-intake status therefore remains missing-response.
- The external blocker dashboard consolidates those logistics into one current
  send/response worklist. It records eight open blocker rows: seven external
  measurement gates and the separate CTE confirmation row. All eight are still
  unsent and missing-response rows; all six expected Gmail drafts were observed by
  the live-state audit, and both local and Downloads recovery scans still show zero
  gate-closing evidence rows.
- The internal gate decision register now records local policies for seven
  internal or internal-with-confirmation items. It keeps NMR trend/anomaly residuals
  as the preferred provisional NMR likelihood, records a separate not-default policy
  for the current report objective, approves the current direct
  gas-pulse permeability residual as log10 intrinsic permeability with a 0.5-log10
  broad sigma and explicit gas/slip caveat, keeps RH as boundary/provenance evidence
  only, fixes Taupe/TDR grouping as a grouped-weight future policy, and limits
  current Taupe/TDR support to mapped A3/A4 rows. These local policies do not close
  external ERT, RH provenance, Taupe calibration, other-HM numeric-export, or
  historical permeability endpoint requests.
- The report open-comment audit now separates active report hygiene from the
  measurement-gate issues. It records zero active `TODO`/`FIXME`/`??` or LaTeX
  todo/highlight/color markers in `main.tex` and `measurement_chapter.tex`, five
  resolved formulation comments, seven tracked external gate requests, four
  internal/provenance/operational tracked items, and four false-positive search
  hits from earlier broad scans. The remaining CTE, RH, ERT, Taupe/TDR, other-HM,
  historical permeability, and NMR-default items are therefore readiness gates rather
  than unresolved LaTeX comments.
- The open-question resolution matrix now consolidates the scattered
  `cda_knowledge_base/open_questions.md` items with the report-comment audit,
  citation/source checks, measurement gates, Gmail draft state, and final-promotion
  trackers. It records 23 rows: 6 locally resolved/current-scope rows, 9 external
  send/response rows, 6 internal policy/final-decision rows, 1 tracked current-policy
  caveat, 1 deferred time-dependency row, and an explicit no-new-evidence closeout
  decision row. It also records zero active report
  markers, zero weak citation locators, zero missing BibTeX entries, 8 open external
  blockers, and `do_not_promote_current_field`.
- The citation locator audit now proves the checkability side of the source
  requirement. It scans the active `main.tex` plus `measurement_chapter.tex` citations
  and records 63 citation key instances, 29 unique cited keys, zero missing/weak
  locators, zero missing BibTeX entries, and zero unavailable cited fulltexts missing
  from `Library/unavailable_fulltexts.md`. The source-library pass recovered clean
  PDFs for `Thomson1871Kelvin`, `ThermalEffectsOPA2010`, `Cui2022DualScaleNMR`,
  `Revil1998ShalySands`, and the newly added `Robinson2003TDRReview`; the active Van Loon
  porosity-property citation now uses the locally downloaded Nagra NTB 03-07 report
  (`VanLoon2004Nagra`) instead of the publisher-blocked journal article.
  The remaining two unavailable fulltext instances (`Topp1980TDR` and
  `Kleinberg1996NMR`) were rechecked on 2026-05-31 and remain known/tracked access
  issues rather than undocumented citation gaps. The inactive `Elsayed2020ClayNMR`
  entry now records that ACS HTML is reachable but PDF retrieval still returned a
  blocker.
- The measurement-report traceability audit now proves the catalogue-to-chapter side
  of the measurement requirement. It checks all nine manifest observation groups
  against catalogue folders/READMEs, the 28 manifest validation checks, coverage rows,
  report subsection and inventory-table references, model-entry wording, and expected
  workflow artifacts. All nine groups pass traceability, with zero missing chapter
  sections, zero missing inventory-table references, zero missing model-entry
  statements, and zero observations missing expected workflow artifacts. This does
  not promote gated streams; it proves that the chapter and workflow now account for
  the available catalogue consistently.
- The inversion parameter-release plan writes 14 XML-linked rows. It makes the
  current calibration scope explicit: `k_i_rd` tensor-magnitude fields are the only
  stage-1 active unknown, with the current active objective split into 269.818057
  direct permeability plus 2886.535010 sampled NMR state objective over 192 NMR rows
  from 83 OGS output times. `n_rd` porosity is a fixed support field because the final
  NMR policy and porosity/saturation separation gate are not approved; van Genuchten
  `p_b` and exponent are later scalar candidates after NMR/RH gates; elasticity and
  Biot are later mechanical candidates after numeric HM residuals; and the open-niche
  pressure curve plus suspicious `CTE` value are provenance/confirmation blockers.
  The plan also records that no same-support active-objective OGS batch is executable
  until support, likelihood, bounds, or stream-gate evidence changes.
- The thermal-expansivity audit now makes the `CTE` blocker explicit. The active XML
  binds `CTE = 1254.74` to the solid `thermal_expansivity` property, the XML comment
  has heat-capacity-like units, and the same value is used for `c_p_s`. Against the
  cited HE-D solid thermal-expansion range `1.0e-5`--`2.6e-5 1/K`, the active value
  is `4.83e7` times the high end. It must remain fixed/uninterpreted until Gesa/BGR
  confirm whether the intended value is near `1e-5 1/K`, different, or inactive.
- The CTE confirmation request package makes that confirmation actionable. It has
  status `cte_confirmation_gmail_draft_created_waiting_user_send_and_response`, routes the draft to
  `Gesa.Ziefle@bgr.de` with `Tuanny.Cajuhi@bgr.de` as suggested CC, and asks whether
  `CTE=1254.74` is an intended `1/K` thermal-expansivity value, a copied
  heat-capacity value, inactive in the intended run, or another unit/convention. It
  now has Gmail draft `r2947727639429158073`; it does not modify the frozen model or
  close the blocker until the draft is sent and a response is recorded.
- The inversion release-gate audit turns that plan into an executable guard for
  prepared runs. The current global audit checks the three regularized OGS candidate
  directories, the first three adaptive candidate directories, the two
  local-refinement candidate directories, the three local-bracketing candidate
  directories, the three optimizer-proposed candidate directories, the three
  continuous-proposed candidate directories, the three lower-support continuous
  candidate directories, the six lower-support loop candidate directories, and the
  six broad continuous candidate directories, plus the three local-basis candidate
  directories and thirty production sampler candidate directories, passing 1300 of 1300
  checks: `k_i` is the
  active `MeshElement`
  `k_i_rd`, `phi` remains fixed support `n_rd = 0.105`, media/retention/mechanical
  XML definitions match the projection reference, and no blocked/later parameter has
  been silently released.
- The objective readiness audit maps the original user objective to 13 requirement
  rows and records `completion_state: not_complete`. It marks the clean report,
  raw measurement inventory, processed measurement tables, and parameter-release
  control as achieved; source model recovery/formulation, source/fulltext,
  measurement semantics, observation operators, likelihood gates, and OGS execution
  as achieved with tracked caveats; and the deterministic permeability field
  comparison, full combined inversion, and remaining open questions as partial. It
  now lists those three partial rows explicitly as non-complete requirements:
  `R10_permeability_field_fit`, `R12_full_combined_inversion`, and
  `R13_open_questions`. It also distinguishes the seven recorded internal local
  policies from the five
  recipient-specific drafts,
  dispatch-readiness checks, response-intake rows, the local gate recovery audit,
  and the Downloads recovery audit covering the seven external requests that still
  block hard activation of ERT, Taupe/RH/other-HM streams. The local recovery pass
  records 2540 rescanned documents, 4553 keyword evidence rows, 62 keyword-only
  candidates, 0 gate-closing rows, and 7 gates still external after rescan; the
  Downloads pass records 533 scanned raw-download documents, 381 keyword evidence
  rows, 0 gate-closing rows, 25 verified duplicate/catalogue rows, and one
  uncatalogued extracted/run-output directory. The external blocker dashboard now
  joins these checks with the six observed Gmail drafts into one eight-row worklist
  with eight open, unsent, missing-response blockers. The final objective decision
  register then turns those blockers into include/exclude choices, but all nine
  decision rows remain pending or not-ready. Dispatch/readiness artifacts are
  therefore request logistics rather than closure evidence.
- The top-level report now resolves the earlier homogeneity/heterogeneity and
  relative-permeability formulation comments explicitly. It records that the exchanged
  OGS TRM equations remain fixed and homogeneous in their base XML form, while the
  active inversion workflow introduces heterogeneity only through run-local
  permeability mesh fields. Porosity and van Genuchten parameters are documented as
  later scalar release options, not as already-active fitted unknowns.
- The OGS formulation consistency audit now parses the source XML and representative
  run-local XML, writes `inversion_workflow/ogs_formulation_consistency_audit.md`,
  `inversion_workflow/ogs_formulation_consistency_audit.csv`,
  `inversion_workflow/ogs_formulation_xml_inventory.csv`, and
  `inversion_workflow/ogs_formulation_consistency_audit_summary.json`, and copies the
  same outputs into
  `../cda_knowledge_base/measurements/model_formulation_audit/derived_files/`. It
  records 18 checks with zero hard failures: the process is
  `THERMO_RICHARDS_MECHANICS`, primary variables are displacement, pressure, and
  temperature, gravity is disabled, vapor terms are inactive, Van Genuchten
  relative-permeability/retention and Bishop power-law semantics are fixed, swelling
  and OGS effective thermal-conductivity mixing are active, and the run-local
  workflow only substitutes mesh fields `k_i_rd` and fixed-support `n_rd`.
- The email-derived knowledge-base open-questions file was synchronized with these
  working decisions: first inversion parameter set is permeability only, direct
  permeability data are likelihood terms rather than hard cell constraints, bedding is
  a structural prior/candidate direction, the projection archive is incorporated, and
  the May 2025 model is the current best baseline within the scanned scope.

## Remaining Follow-Up Items

- Obtain clean PDFs for the blocked/missing references listed in
  `Library/unavailable_fulltexts.md` if institutional access is available.
- Refresh `inversion_workflow/objective_readiness_audit.md` after any major workflow
  change and do not treat the full objective as complete while it reports
  `blocked_external`, `incomplete`, or `partial` rows.
- Send/close the CTE confirmation request before interpreting XML
  `CTE = 1254.74` physically; the local audit proves it is not a plausible
  thermal-expansivity value as written.
- Send/use `rh_boundary_provenance_request.md` to ask Gesa/BGR how
  `08_08_open_niche_seasonal.xml` was generated, because the local OT_RH5--8 Kelvin
  conversion does not reproduce the active open-niche pressure curve within the
  overlapping time range.
- Follow `inversion_workflow/inversion_parameter_release_plan.md` when extending the
  inverse problem: vary `k_i_rd` magnitude fields first, and release tensor shape,
  porosity, retention, boundary, or mechanical parameters only after their recorded
  activation gates are satisfied.
- Refine numerical likelihood scales on top of the new likelihood/activation model.
  The current stream-level model records residual semantics and activation gates, but
  NMR bound-water, ERT inversion/support, Taupe calibration, and RH boundary-curve
  uncertainty still need calibrated sigma values before they can become production
  likelihood terms.
- The continuous proposal batches and repeatable lower-support loop improved
  the current best active objective from 3159.66 to 3156.37. The second lower-support
  loop and broad continuous evidence batches did not improve the incumbent. The
  regenerated finite, focused lower-support, and broad continuous proposals now have
  negligible probability of improvement; the top broad proposal is
  `length_0p009m_shift_0p979` with predicted combined objective about 3158.11 and
  probability of improvement about `2.8e-7`. A direct anisotropy sensitivity sweep
  also found no improvement over the baseline 144 degree, 2.5:1 tensor. A first
  local-basis direct sampler found only a tiny direct pulse-test improvement, but its
  executed three-candidate OGS batch further improves the active best to 3156.35307.
  Five cross-family production handoff rounds did not improve the incumbent; the
  refreshed sampler now leads with `length_0p007m_shift_1p020` among unexecuted
  candidates that already have mesh files, but the stop/continue audit recommends
  pausing that active-objective production sampler. Cross-stream hybrid and
  structural/EDZ direct screens also found no direct-improving follow-up family, and
  the residual conflict, likelihood-policy, and support lower-bound audits show many
  remaining direct residuals need support/interpretation, robust or aggregated
  likelihood semantics, or bound/tensor-shape decisions. The lower-bound gap is
  zero for the current support map, so the next useful step is to prioritize
  ERT/RH/Taupe gates or a genuinely different support/likelihood/parameterization
  decision rather than spending more OGS runs on the current smooth handoff.
  ERT/RH/Taupe and any absolute NMR terms should only be activated as hard residuals
  after output-time/quantity and stream-specific gates are satisfied.
- Locate or reconstruct endpoint geometry for older BCD-A24/25/26/27 and BFM-D19
  permeability rows if those historical pulse tests should be included in the same
  interval-target format. The current audit preserves the source-backed orientation
  evidence, and `permeability_endpoint_geometry_request.md` now gives an email-ready
  request package, but activation still needs labelled endpoints or an approved
  digitized trace with uncertainty.
- The current field generator, direct target fit, deterministic candidate search, and
  executed adaptive batch are parameter-field prototypes. A full inversion still
  needs a sampler or optimizer that proposes new fields against the combined
  measurement objective, runs OGS for each accepted candidate, samples outputs, and
  assembles the objective consistently.
