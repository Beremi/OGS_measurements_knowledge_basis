# Final Objective Scenario Matrix

This matrix maps explicit final-objective include/exclude choices to the
currently scored scenario consequences. It is not a promotion decision and it
does not change the frozen OGS model.

- Status: `final_objective_scenario_matrix_generated`
- Options: 9
- Current field winning options: 2
- Unique winners: 5
- Unscored future options: 1
- Current field final decision: `do_not_promote_to_final_all_measurement_field`
- Direct-permeability active/repeated/range>=2 support cells: 30/24/16
- Direct-permeability policy approvals: 0/1; ready=`False`
- Same-support active-objective batch executable: `False`

## Options

| Option | Classification | Winner | Current rank | Current wins? | Blocked by |
| --- | --- | --- | ---: | --- | --- |
| `F01_current_raw_nmr_exclude_gated_streams` Current raw-NMR active objective, all gated streams excluded or diagnostic-only | `eligible_only_after_explicit_exclusions` | `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | 1.0 | True | all explicit exclusions/diagnostic-only decisions are still pending |
| `F02_promoted_nmr_trend_only` Promote NMR trend/anomaly, exclude external diagnostics from final objective | `requires_internal_policy_change` | `broad_continuous_001_003_length_0p021m` | 14.0 | False | NMR default-promotion decision is still pending |
| `F03_raw_nmr_plus_ert` Raw-NMR active objective plus accepted ERT screen | `requires_external_ert_gate` | `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | 3.0 | False | ERT transform/support and uncertainty gates are unanswered |
| `F04_raw_nmr_plus_taupe` Raw-NMR active objective plus accepted Taupe/TDR screen | `requires_external_taupe_gate` | `local_bracketed_003_length_0p031m` | 21.0 | False | Taupe/TDR unit/calibration gate is unanswered |
| `F05_raw_nmr_plus_ert_taupe` Raw-NMR active objective plus accepted ERT and Taupe/TDR screens | `requires_external_ert_and_taupe_gates` | `production_sampler_round3_002_length_0p028m_shift_1p050` | 19.0 | False | ERT and Taupe/TDR external gates are unanswered |
| `F06_promoted_nmr_plus_ert_taupe` Promoted NMR trend/anomaly plus accepted ERT and Taupe/TDR | `requires_internal_and_external_gate_closure` | `production_sampler_round3_002_length_0p028m_shift_1p050` | 18.0 | False | NMR policy, ERT, and Taupe/TDR gates are open |
| `F07_rank_consensus_diagnostic_selection` Explicit diagnostic rank-consensus selection | `not_a_likelihood_without_explicit_waiver` | `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | 2.0 | False | no waiver has been recorded; diagnostics are not accepted hard residuals |
| `F08_exclude_nmr_direct_permeability_only` Exclude NMR and select by direct permeability only | `requires_new_selection_policy_or_tie_break` | `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | 1.0 | True | no final NMR-exclusion scenario or direct-only tie-break policy is recorded |
| `F09_wait_for_rh_other_hm_endpoint_expansion` Wait for RH, other-HM, or endpoint-missing historical permeability expansion | `requires_new_data_and_new_scenario_build` | `` |  | False | external provider responses/files are missing |

## Decision Consequences

### `F01_current_raw_nmr_exclude_gated_streams` Current raw-NMR active objective, all gated streams excluded or diagnostic-only

- Required decisions: retain raw absolute NMR default with caveats; keep ERT diagnostic-only; keep Taupe diagnostic-only; keep RH boundary-audit-only; exclude other-HM hard residuals; exclude endpoint-missing historical permeability rows or accept current support; scope out CTE from field selection
- Scenario source: `S01_current_active_raw_nmr`
- Winner: `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000`
- Current score/rank: `0.0` / `1.0`
- Score delta current minus winner: `0.0`
- Best-tie count: ``
- Direct-permeability support/likelihood evidence: support-conflict active/repeated/range>=2 cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes
- Promotion consequence: The current packaged field can only become final under this narrow objective if the report explicitly says the final field does not include ERT, Taupe/TDR, RH, other-HM, or endpoint-missing historical rows.

### `F02_promoted_nmr_trend_only` Promote NMR trend/anomaly, exclude external diagnostics from final objective

- Required decisions: promote within-label NMR trend/anomaly as final NMR residual; keep ERT/Taupe/RH/other-HM diagnostic-only or excluded; exclude endpoint-missing historical permeability rows
- Scenario source: `S02_promoted_nmr_trend_anomaly`
- Winner: `broad_continuous_001_003_length_0p021m`
- Current score/rank: `0.0001883443770363` / `14.0`
- Score delta current minus winner: `0.0001883443770363`
- Best-tie count: ``
- Direct-permeability support/likelihood evidence: support-conflict active/repeated/range>=2 cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes
- Promotion consequence: The current raw-NMR field would not be the selected field; the promoted-NMR winner would need a field package and current-field selection refresh.

### `F03_raw_nmr_plus_ert` Raw-NMR active objective plus accepted ERT screen

- Required decisions: accept ERT transform/support and uncertainty; retain raw NMR default; keep Taupe/RH/other-HM diagnostic-only or excluded; decide endpoint-missing historical rows
- Scenario source: `S03_active_plus_ert_screen`
- Winner: `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000`
- Current score/rank: `0.0027380497298203` / `3.0`
- Score delta current minus winner: `2.6583552277569325e-06`
- Best-tie count: ``
- Direct-permeability support/likelihood evidence: support-conflict active/repeated/range>=2 cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes
- Promotion consequence: The current field is close but not the scenario winner; the ERT-screen winner would need to be treated as the candidate selected by this objective.

### `F04_raw_nmr_plus_taupe` Raw-NMR active objective plus accepted Taupe/TDR screen

- Required decisions: accept Taupe/TDR unit calibration and uncertainty; retain raw NMR default; keep ERT/RH/other-HM diagnostic-only or excluded; decide endpoint-missing historical rows
- Scenario source: `S04_active_plus_taupe_screen`
- Winner: `local_bracketed_003_length_0p031m`
- Current score/rank: `0.4519394161052462` / `21.0`
- Score delta current minus winner: `0.2627039208366881`
- Best-tie count: ``
- Direct-permeability support/likelihood evidence: support-conflict active/repeated/range>=2 cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes
- Promotion consequence: The current field is not selected; the Taupe-screen winner is a broader smooth-family field and would need field packaging before any promotion.

### `F05_raw_nmr_plus_ert_taupe` Raw-NMR active objective plus accepted ERT and Taupe/TDR screens

- Required decisions: accept ERT transform/support/uncertainty; accept Taupe/TDR calibration/uncertainty; retain raw NMR default; keep RH/other-HM diagnostic-only or excluded; decide endpoint rows
- Scenario source: `S05_active_plus_ert_taupe_screen`
- Winner: `production_sampler_round3_002_length_0p028m_shift_1p050`
- Current score/rank: `0.303118310556711` / `19.0`
- Score delta current minus winner: `0.0850698727444818`
- Best-tie count: ``
- Direct-permeability support/likelihood evidence: support-conflict active/repeated/range>=2 cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes
- Promotion consequence: The current field is not selected; the production-round winner would need a field package and promotion audit under the accepted ERT/Taupe objective.

### `F06_promoted_nmr_plus_ert_taupe` Promoted NMR trend/anomaly plus accepted ERT and Taupe/TDR

- Required decisions: promote NMR trend/anomaly; accept ERT and Taupe/TDR gates; keep RH/other-HM diagnostic-only or excluded; decide endpoint-missing historical rows
- Scenario source: `S06_active_plus_promoted_nmr_ert_taupe`
- Winner: `production_sampler_round3_002_length_0p028m_shift_1p050`
- Current score/rank: `0.2273858190117923` / `18.0`
- Score delta current minus winner: `0.0612863269779676`
- Best-tie count: ``
- Direct-permeability support/likelihood evidence: support-conflict active/repeated/range>=2 cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes
- Promotion consequence: The current field is not selected; this is the closest currently scored all-numeric scenario but still excludes RH, other-HM, and endpoint-missing historical rows.

### `F07_rank_consensus_diagnostic_selection` Explicit diagnostic rank-consensus selection

- Required decisions: record a modelling-team waiver that diagnostic ranks, not a likelihood, are the final selection rule; keep all gated streams labelled diagnostic-only
- Scenario source: `S08_rank_consensus_all_streams`
- Winner: `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000`
- Current score/rank: `13.2` / `2.0`
- Score delta current minus winner: `2.799999999999999`
- Best-tie count: ``
- Direct-permeability support/likelihood evidence: support-conflict active/repeated/range>=2 cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes
- Promotion consequence: The current field is not the rank-consensus winner. This option should remain a screening aid unless the report explicitly chooses a diagnostic-consensus final rule.

### `F08_exclude_nmr_direct_permeability_only` Exclude NMR and select by direct permeability only

- Required decisions: explicitly exclude NMR from final field selection; decide tie-breaking across direct-only best fields; keep ERT/Taupe/RH/other-HM diagnostic-only or excluded
- Scenario source: `direct_permeability_only_not_in_conditional_scenarios`
- Winner: `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000`
- Current score/rank: `269.8180571059851` / `1.0`
- Score delta current minus winner: `0.0`
- Best-tie count: `12`
- Direct-permeability support/likelihood evidence: support-conflict active/repeated/range>=2 cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes
- Promotion consequence: Direct-only selection is not stable without a tie-break: multiple fields share the same direct objective at numerical precision, including the current field.

### `F09_wait_for_rh_other_hm_endpoint_expansion` Wait for RH, other-HM, or endpoint-missing historical permeability expansion

- Required decisions: obtain RH provenance/uncertainty if it should become accepted forcing; obtain other-HM numeric exports/metadata if they should become residuals; obtain endpoint geometry if historical permeability rows should enter the final fit
- Scenario source: `not_currently_scored`
- Winner: ``
- Current score/rank: `` / ``
- Score delta current minus winner: ``
- Best-tie count: ``
- Direct-permeability support/likelihood evidence: support-conflict active/repeated/range>=2 cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes
- Promotion consequence: No final winner can be selected for this option from the current scenario audit; the observation tables and scenario audit must be rebuilt after new evidence is filed.

## Interpretation

- The current field wins only the current raw-NMR option and ties the direct-only option.
- Every option that includes promoted NMR, ERT, or Taupe selects a different field.
- RH, other-HM, and endpoint-missing historical permeability cannot select a field yet because their required evidence is not in the scored scenario set.
- The direct-permeability support/likelihood policy is not approved, and the same-support active-objective batch gate remains closed.

## Source Artifacts

- `inversion_workflow/conditional_field_selection_scenarios.csv`
- `inversion_workflow/conditional_field_selection_scenarios_summary.json`
- `inversion_workflow/cross_stream_candidate_scorecard.csv`
- `inversion_workflow/final_objective_decision_register_summary.json`
- `inversion_workflow/current_field_selection_audit_summary.json`
- `inversion_workflow/permeability_support_conflict_spatial_audit_summary.json`
- `inversion_workflow/permeability_support_lower_bound_audit_summary.json`
- `inversion_workflow/permeability_likelihood_policy_acceptance_record_template_summary.json`
- `inversion_workflow/permeability_next_field_fit_gate_summary.json`
