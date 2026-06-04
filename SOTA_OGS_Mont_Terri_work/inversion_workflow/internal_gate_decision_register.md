# Internal Gate Decision Register

This register records local modelling decisions for the internal or internal-with-optional-confirmation items in the measurement gate-closure package.
It does not close external source requests for ERT, RH provenance, Taupe unit calibration, or other-HM numeric exports.

## Summary

- Status: `internal_gate_decision_register_generated`
- Internal decisions represented: 7
- Local policies recorded: 7
- Active/ready internal policies: 2
- Diagnostic or boundary-only policies: 3
- Diagnostic/boundary policies still gated before hard activation: 3
- Rows with optional confirmation caveats: 5

## Decision Table

| Request | Stream | Local status | Activation effect | External confirmation |
| --- | --- | --- | --- | --- |
| `nmr_bound_water` | `nmr_water_content` | `local_policy_recorded_executable_mode_available` | Executable for future candidate evaluations with --state-objective-mode nmr_within_label_trend_anomaly; see nmr_default_promotion for the separate default-objective policy. | Optional check with BGR/NMR source on bound/interlayer-water interpretation. |
| `nmr_default_promotion` | `nmr_water_content` | `local_policy_recorded_not_promoted_default` | The historical raw-objective combined files stay authoritative for the active incumbent; trend/anomaly rankings are reported as provisional scenario evidence and must be invoked by explicit mode or scenario audit. | No external reply is needed for the current not-default policy; re-open if collaborators want to promote trend/anomaly NMR as the reporting/search default. |
| `perm_error_model` | `permeability_pulse_tests` | `local_policy_recorded_current_objective_approved` | Direct permeability remains an active objective stream; do not describe the values as water hydraulic conductivity, relative permeability, or cell-wise tensor components. | Optional BGR check on gas/slip correction and liquid-equivalent wording. |
| `perm_likelihood_policy` | `permeability_pulse_tests` | `local_policy_recorded_not_promoted_default` | No default objective change. More routine OGS runs under the current smooth/local-basis family should wait until either this rowwise policy is explicitly accepted with a new parameterization or a robust/aggregated likelihood scenario is approved and reranked. | Optional BGR/Gesa confirmation if the policy depends on gas-pulse interpretation, scalar interval support, or the treatment of configured-scalar-range outliers. |
| `rh_uncertainty` | `relative_humidity_suction` | `local_policy_recorded_external_provenance_still_required` | RH remains boundary-audit-only. Candidate curves may be run as future forcing scenarios only after provenance/extension policy is accepted. | BGR/Gesa provenance for active curve generation, constants, time axis, and sensor screening required. |
| `taupe_group_weights` | `taupe_tdr` | `local_policy_recorded_diagnostic_only` | Does not activate Taupe until unit/calibration and uncertainty gates close; gives the future weighting rule so the internal grouping question is no longer implicit. | Taupe/TDR provider confirmation of unit calibration and uncertainty still required. |
| `taupe_support` | `taupe_tdr` | `local_policy_recorded_support_mask_fixed_for_current_mesh` | Taupe support decision is explicit for the current mesh, but hard-residual activation still depends on unit/calibration and uncertainty confirmation. | Provider confirmation useful for A7/A8 geometry/support if those sensors should be included. |

## Details

### `nmr_bound_water`

- Gate: `NMR_BOUND_WATER` (`warn`)
- Local policy: Use within-label trend/anomaly residuals as the preferred provisional NMR likelihood for reporting/search scenarios; keep raw absolute-theta NMR as an archival/conditional objective for the current active files.
- Objective/operator: (theta_model - weighted_label_mean(theta_model)) - (theta_NMR_obs - weighted_label_mean(theta_NMR_obs)) within observation_family + measurement_label.
- Weights/uncertainty: Use existing NMR sigma values for centered residuals; do not fit absolute offsets.
- Activation effect: Executable for future candidate evaluations with --state-objective-mode nmr_within_label_trend_anomaly; see nmr_default_promotion for the separate default-objective policy.
- External confirmation: Optional check with BGR/NMR source on bound/interlayer-water interpretation.
- Key evidence: recommended=within_label_trend_anomaly; executable_status=nmr_trend_anomaly_active_objective_mode_implemented_provisional; best_run=broad_continuous_001_003_length_0p021m; validation_delta=5.684341886080802e-14; followup=pause_new_trend_anomaly_ogs_batch.
- Source artifacts: inversion_workflow/nmr_objective_decision.md; inversion_workflow/nmr_trend_anomaly_active_objective.md; inversion_workflow/runs/nmr_trend_anomaly_followup_plan/NMR_TREND_ANOMALY_FOLLOWUP_PLAN.md

### `nmr_default_promotion`

- Gate: `NMR_DEFAULT_PROMOTION` (`internal_policy`)
- Local policy: Do not promote the within-label trend/anomaly NMR mode to the default objective for the current report state. Keep it as the preferred provisional NMR likelihood and as an explicit scenario/sensitivity path until the modelling team accepts changing the objective semantics.
- Objective/operator: Default objective remains raw absolute-theta NMR plus direct permeability. The promoted-mode candidate operator is the centered within-label NMR trend/anomaly residual.
- Weights/uncertainty: No new default weights are assigned. The explicit trend/anomaly mode reuses NMR sigma values inside centered observation-family/measurement-label groups.
- Activation effect: The historical raw-objective combined files stay authoritative for the active incumbent; trend/anomaly rankings are reported as provisional scenario evidence and must be invoked by explicit mode or scenario audit.
- External confirmation: No external reply is needed for the current not-default policy; re-open if collaborators want to promote trend/anomaly NMR as the reporting/search default.
- Key evidence: active_objective_changed=False; recommended=within_label_trend_anomaly; best_recommended_run=broad_continuous_001_003_length_0p021m; executable_best=broad_continuous_001_003_length_0p021m; raw_incumbent_rank_under_trend=14.0; trend_winner_raw_rank=56.0; followup=pause_new_trend_anomaly_ogs_batch; median_state_beating_candidates=0.
- Source artifacts: inversion_workflow/nmr_objective_decision.md; inversion_workflow/nmr_trend_anomaly_active_objective.md; inversion_workflow/runs/nmr_trend_anomaly_followup_plan/NMR_TREND_ANOMALY_FOLLOWUP_PLAN.md; inversion_workflow/conditional_field_selection_scenarios.md

### `perm_error_model`

- Gate: `PERM_ERROR_MODEL` (`warn`)
- Local policy: Approve the current first-pass gas-pulse residual as log10 intrinsic permeability, with duplicate-aware interval weights and sigma=0.5 log10 units. Keep the gas/slip/liquid-equivalent caveat explicit.
- Objective/operator: residual = log10(e^T K e interval/support response) - log10(k_obs); K remains the intrinsic permeability tensor field.
- Weights/uncertainty: sigma=0.5 log10 units; duplicate observations with same campaign, segment, depth, and value share total weight 1.
- Activation effect: Direct permeability remains an active objective stream; do not describe the values as water hydraulic conductivity, relative permeability, or cell-wise tensor components.
- External confirmation: Optional BGR check on gas/slip correction and liquid-equivalent wording.
- Key evidence: target_rows=204; active_rows=75; permeability semantics audit records scalar interval intrinsic-permeability interpretation.
- Source artifacts: inversion_workflow/processed_observations/permeability_measurement_semantics.md; inversion_workflow/scripts/evaluate_permeability_targets.py

### `perm_likelihood_policy`

- Gate: `PERM_LIKELIHOOD_POLICY` (`internal_policy`)
- Local policy: Keep the current duplicate-weighted rowwise Gaussian direct-permeability objective as the recorded default for the current report state. Treat robust row likelihoods, support-cell aggregation, and configured-scalar-range outlier handling as explicit scenario/decision options until the modelling team changes the objective semantics.
- Objective/operator: Default remains residual = log10(e^T K e interval/support response) - log10(k_obs) with duplicate-aware row weights. Candidate alternatives are robust row residuals, support-cell mean/median aggregation, configured-scalar-range outlier gating, or a new parameterization gate.
- Weights/uncertainty: Default sigma remains 0.5 log10 units. Non-default policies must state their kernel/grouping, weights, outlier disposition, and reranking rule before they are used for field selection.
- Activation effect: No default objective change. More routine OGS runs under the current smooth/local-basis family should wait until either this rowwise policy is explicitly accepted with a new parameterization or a robust/aggregated likelihood scenario is approved and reranked.
- External confirmation: Optional BGR/Gesa confirmation if the policy depends on gas-pulse interpretation, scalar interval support, or the treatment of configured-scalar-range outliers.
- Key evidence: policy_status=permeability_likelihood_policy_audit_generated; current_gaussian_objective=269.8180571059851; support_mean_objective=1.7670484276950664e-28; support_median_objective=134.72779043641356; conflict_groups=16; top10_loss_share=0.49400403343820803; decision_request=permeability_likelihood_decision_request_generated.
- Source artifacts: inversion_workflow/permeability_likelihood_policy_audit.md; inversion_workflow/permeability_likelihood_decision_request.md; inversion_workflow/permeability_residual_conflict_audit.md

### `rh_uncertainty`

- Gate: `RH_UNCERTAINTY` (`fail`)
- Local policy: Keep RH/suction as boundary-provenance and uncertainty-envelope evidence only. Do not replace the active OGS XML boundary curve, activate a suction/retention residual, or release retention parameters until active-curve provenance is confirmed.
- Objective/operator: Local RH-derived curves remain candidate boundary scenarios and diagnostics, not hard residuals.
- Weights/uncertainty: Use the RH5/RH6 median/mean policy envelope to quantify uncertainty; no likelihood sigma assigned.
- Activation effect: RH remains boundary-audit-only. Candidate curves may be run as future forcing scenarios only after provenance/extension policy is accepted.
- External confirmation: BGR/Gesa provenance for active curve generation, constants, time axis, and sensor screening required.
- Key evidence: candidate_curves=6; envelope_dates=1064; active_outside_envelope=575; overlap_p50_range=2.103967930926996 MPa.
- Source artifacts: inversion_workflow/processed_observations/rh_boundary_uncertainty.md; inversion_workflow/processed_observations/rh_boundary_provenance_request.md

### `taupe_group_weights`

- Gate: `TAUPE_GROUP_WEIGHTS` (`warn`)
- Local policy: For diagnostics, report aggregate-row and grouped-weight sensitivity side by side; if Taupe is later activated as a trend likelihood, use grouped weights so A3/A4 sensors and EDZ bands are not over-weighted by row count.
- Objective/operator: Trend/anomaly residual over mapped Taupe/TDR bands; absolute water-content residual remains inactive.
- Weights/uncertainty: Preferred future hard-likelihood baseline: equal sensor or equal series/EDZ-band groups with row weights normalized within group; keep aggregate-row weighting as sensitivity.
- Activation effect: Does not activate Taupe until unit/calibration and uncertainty gates close; gives the future weighting rule so the internal grouping question is no longer implicit.
- External confirmation: Taupe/TDR provider confirmation of unit calibration and uncertainty still required.
- Key evidence: runs=66; compared_series=12; distinct_winners=8; best_mean_rank_run=adaptive_combined_001_length_0p050m.
- Source artifacts: inversion_workflow/taupe_series_weight_sensitivity.md; inversion_workflow/processed_observations/taupe_tdr_observation_operator.md

### `taupe_support`

- Gate: `TAUPE_SUPPORT` (`warn`)
- Local policy: Limit current Taupe/TDR model comparisons to A3/A4 mapped Niche-4 support. Keep A7/A8 and outside-support rows as documented exclusions/validation context until a larger mesh or approved support mapping exists.
- Objective/operator: Band-average OGS theta trend over mapped A3/A4 intervals only; no fallback projection for A7/A8.
- Weights/uncertainty: A3/A4 groups only for current diagnostics; excluded support must not contribute residual weight.
- Activation effect: Taupe support decision is explicit for the current mesh, but hard-residual activation still depends on unit/calibration and uncertainty confirmation.
- External confirmation: Provider confirmation useful for A7/A8 geometry/support if those sensors should be included.
- Key evidence: mapped_trend_rows=2544; outside_mesh_rows=2544; trend_ready_series=12; series-weight audit compared A3/A4 and left A7/A8 outside current mesh support.
- Source artifacts: inversion_workflow/processed_observations/taupe_tdr_semantics.md; inversion_workflow/taupe_series_weight_sensitivity.md
