# Final Objective No-New-Evidence Acceptance Record Template

This generated file is a fillable signoff template for the conservative
no-new-evidence closeout path. It is not an approval record, does not close
provider gates, does not send email, and does not promote the current field.

- Status: `final_objective_no_new_evidence_acceptance_record_template_generated`
- Template rows: 9
- Approval rows required: 9
- Approval rows recorded: 0
- Ready to apply decisions: `False`
- Records actual decisions: `False`
- Promotes current field: `False`
- Sends or modifies email: `False`
- Would select scenario after full approval: `F01_current_raw_nmr_exclude_gated_streams`
- Would select winner after full approval: `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000`
- Current field is winner after full approval: `True`
- Direct-permeability support-conflict audit: `permeability_support_conflict_spatial_audit_generated`
- Direct-permeability active/repeated/range>=2 support cells: 30/24/16
- Direct-permeability policy approvals before approval: 0/1; ready=`False`
- Same-support active-objective batch executable before approval: `False`

## Required Approval Fields

Each row must have all of the following fields filled from a real user or
modelling-team decision before the closeout can be applied:

- `approval_status=approved`
- `approver_name`
- `approval_date`
- `approval_reference`

## Template Rows

| Criterion | Stream | Approval status | Required approver | Closeout choice |
| --- | --- | --- | --- | --- |
| `P08_nmr_residual_policy` Final NMR residual policy | NMR water content | `not_approved_template_only` | modelling_team | `retain_raw_absolute_theta_default_with_caveats` |
| `P09_ert_gate` ERT transform/support and uncertainty | ERT resistivity | `not_approved_template_only` | user_and_modelling_team | `keep_diagnostic_only_exclude_from_final_likelihood` |
| `P10_taupe_gate` Taupe/TDR unit calibration and uncertainty | Taupe/TDR | `not_approved_template_only` | user_and_modelling_team | `keep_trend_diagnostic_exclude_absolute_values` |
| `P11_rh_gate` RH active boundary-curve provenance and uncertainty | RH/suction | `not_approved_template_only` | user_and_modelling_team | `keep_boundary_audit_only_no_residual_or_curve_replacement` |
| `P12_other_hm_gate` Other-HM numeric exports, metadata, and uncertainty | Other HM monitoring | `not_approved_template_only` | user_and_modelling_team | `qualitative_context_only_no_hard_residual` |
| `P13_perm_endpoint_gate` Historical permeability endpoint geometry/provenance | Historical permeability pulse tests | `not_approved_template_only` | user_and_modelling_team | `use_current_supported_rows_keep_endpoint_missing_historical_rows_inactive` |
| `P14_cte_confirmation` Suspicious CTE value confirmation | Frozen OGS model provenance | `not_approved_template_only` | user_and_modelling_team | `scope_out_cte_from_permeability_objective_keep_frozen_caveat` |
| `P15_conditional_field_stability` Accepted scenario set and winner stability | Final objective scenario set | `not_approved_template_only` | modelling_team | `select_F01_only_if_prior_draft_rows_are_approved_and_audits_rerun` |
| `P16_final_field_decision` Promote or keep active-only field label | Final field approval | `not_approved_template_only` | modelling_team_final_approval | `keep_active_incumbent_label_until_post_acceptance_audits` |

## Exact Decision Text

### `P08_nmr_residual_policy` Final NMR residual policy

- Exact decision text to record: Retain raw absolute NMR water-content residuals for the current no-new-evidence objective, with explicit bound-water/mobile-water caveats. Do not promote the within-label trend/anomaly policy, label-bias correction, or free-water correction as final unless a separate NMR policy decision is recorded.
- Decision-register action after approval: Record a modelling-team policy row that accepts raw absolute theta with caveats for the no-new-evidence closeout scenario only.
- Exact report wording after approval: NMR is retained in the current active objective as raw absolute water content with bound-water caveats.  No final NMR residual policy is selected; within-label trend/anomaly remains the preferred provisional candidate.
- Scenario effect after approval: supports F01 only after explicit acceptance
- Model consequence after approval: The active objective can remain raw-NMR based for the narrow no-new-evidence scenario, but the report must say that the mobile/free-water interpretation is caveated and that the trend/anomaly result is provisional evidence.
- Current evidence before approval: recommended=within_label_trend_anomaly; executable_status=nmr_trend_anomaly_active_objective_mode_implemented_provisional; best_run=broad_continuous_001_003_length_0p021m; validation_delta=5.684341886080802e-14; followup=pause_new_trend_anomaly_ogs_batch.; active_objective_changed=False; best_recommended_run=broad_continuous_001_003_length_0p021m; executable_best=broad_continuous_001_003_length_0p021m; raw_incumbent_rank_under_trend=14.0; trend_winner_raw_rank=56.0; followup=pause_new_trend_anomaly_ogs_batch; median_state_beating_candidates=0.; NMR final policy selected=False; recommended candidate=within_label_trend_anomaly; recommended run=broad_continuous_001_003_length_0p021m; follow-up=pause_new_trend_anomaly_ogs_batch
- Source evidence locations: inversion_workflow/nmr_objective_decision.md; inversion_workflow/nmr_trend_anomaly_active_objective.md; inversion_workflow/runs/nmr_trend_anomaly_followup_plan/NMR_TREND_ANOMALY_FOLLOWUP_PLAN.md; inversion_workflow/conditional_field_selection_scenarios.md
- Related blockers/decisions: nmr_bound_water,nmr_default_promotion

### `P09_ert_gate` ERT transform/support and uncertainty

- Exact decision text to record: Keep ERT as diagnostic log-resistivity field-consistency evidence and exclude it from final likelihood weights because the ERT-to-OGS transform/support and uncertainty/correlation model are not confirmed.
- Decision-register action after approval: Record ERT as diagnostic-only/excluded from final likelihood for the no-new-evidence closeout scenario.
- Exact report wording after approval: ERT was retained as diagnostic field-consistency evidence and excluded from the final likelihood because the ERT-to-OGS transform/support and uncertainty/correlation model were not confirmed.
- Scenario effect after approval: excludes F03, F05, and F06 unless provider evidence later arrives
- Model consequence after approval: The final selected field is not selected by dense ERT VTK residuals, and ERT diagnostic plots/ranks cannot be described as accepted likelihood terms.
- Current evidence before approval: ERT-to-OGS transform and exact near-niche support mask remain assumed, not confirmed.; No defensible ERT residual sigma/correlation model is available; pixels cannot be treated as independent rows.
- Source evidence locations: /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses/ert_transform_support_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses/ert_uncertainty_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses
- Related blockers/decisions: ert_transform_support,ert_uncertainty

### `P10_taupe_gate` Taupe/TDR unit calibration and uncertainty

- Exact decision text to record: Keep Taupe/TDR as mapped baseline-normalized trend diagnostic evidence and exclude absolute Taupe values from final water-content likelihood terms because units, calibration, and uncertainty are not confirmed.
- Decision-register action after approval: Record Taupe/TDR as diagnostic-only/excluded from final likelihood for the no-new-evidence closeout scenario.
- Exact report wording after approval: Taupe/TDR was retained as a mapped trend diagnostic and excluded from the final likelihood because unit calibration and residual uncertainty were not confirmed.
- Scenario effect after approval: excludes F04, F05, and F06 unless provider evidence later arrives
- Model consequence after approval: Taupe/TDR cannot select the final field as an absolute saturation or water-content target; A3/A4 and A7/A8 remain diagnostic comparisons.
- Current evidence before approval: Taupe values are not confirmed as volumetric water-content percent, permittivity, or another ARDP-derived proxy.
- Source evidence locations: /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/provider_responses/taupe_unit_calibration_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/provider_responses
- Related blockers/decisions: taupe_unit_calibration

### `P11_rh_gate` RH active boundary-curve provenance and uncertainty

- Exact decision text to record: Keep RH/suction as boundary-provenance and scenario-audit evidence only. Do not replace, fit, or weight the active pressure curve from local RH workbooks because the active-curve provenance, constants, time axis, sensor screening, extension policy, and uncertainty are not confirmed.
- Decision-register action after approval: Record RH/suction as boundary-audit-only and excluded from final residual weights for the no-new-evidence closeout scenario.
- Exact report wording after approval: RH/suction was retained as boundary-provenance and scenario evidence only; it was not used as a weighted residual or to replace the active pressure curve because the active-curve provenance and uncertainty remain unconfirmed.
- Scenario effect after approval: keeps F09 unscored until provider evidence later arrives
- Model consequence after approval: The active pressure curve stays frozen; RH-derived candidate curves can document boundary uncertainty but cannot redefine the forward problem.
- Current evidence before approval: Active boundary curve generation, sensor screening, time axis, constants, and extension policy are not confirmed.
- Source evidence locations: /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/provider_responses/rh_active_curve_provenance_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/provider_responses
- Related blockers/decisions: rh_active_curve_provenance

### `P12_other_hm_gate` Other-HM numeric exports, metadata, and uncertainty

- Exact decision text to record: Keep other HM monitoring as qualitative or geometric context only and exclude it from final hard residuals because local files do not contain hard-residual-ready numeric exports, support definitions, metadata, and uncertainties.
- Decision-register action after approval: Record other-HM monitoring as qualitative-only/excluded from final likelihood for the no-new-evidence closeout scenario.
- Exact report wording after approval: Other HM streams were retained as qualitative or geometric context only and excluded from the final likelihood because hard-residual-ready numeric exports, support definitions, and uncertainties were not available locally.
- Scenario effect after approval: keeps F09 unscored until numeric exports later arrive
- Model consequence after approval: Geoscope, laser, levelling, extensometer, mini-piezometer, and crackmeter evidence can orient the report but cannot carry mechanical or hydraulic likelihood weights.
- Current evidence before approval: Local source scan found layout geometry, laser surface geometry, extracted levelling slide rows, and report/minute evidence, but no hard-residual-ready Geoscope time series, laser statistical interpretation product, or full levelling survey table.; Required metadata for hard HM residual weights are absent from the current local bundle.
- Source evidence locations: /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses/hm_numeric_exports_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses/hm_uncertainty_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses
- Related blockers/decisions: hm_numeric_exports,hm_uncertainty

### `P13_perm_endpoint_gate` Historical permeability endpoint geometry/provenance

- Exact decision text to record: Use only currently projected active permeability pulse-test rows and keep endpoint-missing historical BCD-A24/25/26/27 and BFM-D19 rows visible but inactive because labelled endpoint geometry or an approved digitized trace is not available.
- Decision-register action after approval: Record endpoint-missing historical permeability rows as inactive/excluded from the no-new-evidence final residual set.
- Exact report wording after approval: Endpoint-missing historical permeability rows were kept inactive and excluded from the final hard residual set; the direct permeability objective used only rows with current accepted projection support.
- Scenario effect after approval: supports F01/F08 current-support interpretations only
- Model consequence after approval: The direct permeability objective remains limited to rows with accepted projection support; historical scalar values without interval geometry are not projected.
- Current evidence before approval: Historical permeability endpoints are needed only if these older rows should enter the fit.; support-conflict audit=permeability_support_conflict_spatial_audit_generated; active/repeated/range>=2 support cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes
- Source evidence locations: /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/permeability_pulse_tests/source_files/provider_responses/perm_endpoint_geometry_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/permeability_pulse_tests/source_files/provider_responses; inversion_workflow/permeability_support_conflict_spatial_audit.md; inversion_workflow/permeability_support_lower_bound_audit.md; inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md; inversion_workflow/permeability_next_field_fit_gate.md
- Related blockers/decisions: perm_endpoint_geometry

### `P14_cte_confirmation` Suspicious CTE value confirmation

- Exact decision text to record: Scope the suspicious CTE value out of the permeability-field objective and keep it as an uninterpreted frozen-source caveat. Do not correct, calibrate, or make thermo-mechanical interpretation claims that depend on CTE=1254.74 without a provider response.
- Decision-register action after approval: Record CTE as scoped out of final permeability selection for the no-new-evidence closeout scenario.
- Exact report wording after approval: The CTE value remains a frozen-source caveat and was not interpreted or calibrated in the permeability-field objective.
- Scenario effect after approval: keeps CTE outside all current field-selection options
- Model consequence after approval: The exchanged OGS model remains frozen; the field fit does not interpret thermal expansivity and does not create a corrected model version.
- Current evidence before approval: The XML binds CTE to solid thermal_expansivity, but the value and comment look like a copied heat-capacity entry. The model must remain frozen, so this needs provenance confirmation rather than a local correction.
- Source evidence locations: inversion_workflow/cte_confirmation_request.md
- Related blockers/decisions: cte_value_confirmation

### `P15_conditional_field_stability` Accepted scenario set and winner stability

- Exact decision text to record: If all preceding no-new-evidence draft rows are approved, select F01_current_raw_nmr_exclude_gated_streams as the only accepted no-new-evidence final-objective scenario. This is a narrow objective, not an all-measurement likelihood, and must be regenerated through the scenario and current-field audits.
- Decision-register action after approval: Record F01 as the explicit no-new-evidence scenario only after the individual stream exclusions/policies are recorded.
- Exact report wording after approval: The accepted final objective scenario was not selected; therefore the current field remains an active-objective incumbent, not a final all-measurement field.
- Scenario effect after approval: selects F01 only after prior approvals and regeneration
- Model consequence after approval: The current field can only be discussed under the narrow raw-NMR/direct-permeability objective with excluded gated streams; other scenario winners remain diagnostic.
- Current evidence before approval: scenarios=8; unique winners=5; current-field wins=1; final decision=single_field_not_stable_across_gate_scenarios; support-conflict audit=permeability_support_conflict_spatial_audit_generated; active/repeated/range>=2 support cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes
- Source evidence locations: inversion_workflow/conditional_field_selection_scenarios.md; inversion_workflow/current_field_selection_audit.md; inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md; inversion_workflow/permeability_next_field_fit_gate.md; inversion_workflow/permeability_support_conflict_spatial_audit.md
- Related blockers/decisions: none

### `P16_final_field_decision` Promote or keep active-only field label

- Exact decision text to record: This draft does not promote the current field. Keep the packaged field labelled as the active direct-permeability/raw-NMR incumbent until the no-new-evidence decisions are recorded, the scenario/current-field/promotion audits are rerun, and a separate final approval is recorded.
- Decision-register action after approval: Keep the final-field decision as not promoted in this draft; promote only through a later regenerated audit and approval record.
- Exact report wording after approval: The current field is not a final all-measurement inversion result; it is the active-objective incumbent under the current direct-permeability/raw-NMR setup.
- Scenario effect after approval: does not promote the field by itself
- Model consequence after approval: The report remains protected against overclaiming; any later final label must be restricted to the accepted no-new-evidence scenario and not called an all-measurement inversion.
- Current evidence before approval: active decision=accept_as_current_active_objective_incumbent; final decision=do_not_promote_to_final_all_measurement_field; status counts={'pass': 2, 'pass_with_caveat': 2, 'fails_final_promotion': 2, 'blocked_or_gated': 4}; support-conflict audit=permeability_support_conflict_spatial_audit_generated; active/repeated/range>=2 support cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes; current-field final decision=do_not_promote_to_final_all_measurement_field
- Source evidence locations: inversion_workflow/conditional_field_selection_scenarios.md; inversion_workflow/current_field_selection_audit.md; inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md; inversion_workflow/permeability_next_field_fit_gate.md; inversion_workflow/permeability_support_conflict_spatial_audit.md
- Related blockers/decisions: none

## After Full Approval

Only after every row is approved and the decision layer has been updated, rerun:

```bash
python inversion_workflow/scripts/build_internal_gate_decision_register.py \
  && python inversion_workflow/scripts/build_external_gate_response_intake.py \
  && python inversion_workflow/scripts/build_external_gate_dispatch_audit.py \
  && python inversion_workflow/scripts/build_external_blocker_dashboard.py \
  && python inversion_workflow/scripts/build_measurement_stream_gate_audit.py \
  && python inversion_workflow/scripts/build_conditional_field_selection_scenarios.py \
  && python inversion_workflow/scripts/build_current_field_selection_audit.py \
  && python inversion_workflow/scripts/build_final_inversion_promotion_checklist.py \
  && python inversion_workflow/scripts/build_final_inversion_closeout_playbook.py \
  && python inversion_workflow/scripts/build_final_objective_decision_register.py \
  && python inversion_workflow/scripts/build_final_objective_scenario_matrix.py \
  && python inversion_workflow/scripts/build_final_objective_include_exclude_recommendations.py \
  && python inversion_workflow/scripts/build_final_objective_no_new_evidence_closeout_draft.py \
  && python inversion_workflow/scripts/build_objective_readiness_audit.py
```

## Source Artifacts

- `inversion_workflow/final_objective_no_new_evidence_closeout_draft.csv`
- `inversion_workflow/final_objective_no_new_evidence_closeout_draft_summary.json`
- `inversion_workflow/final_objective_decision_register.csv`
- `inversion_workflow/final_objective_scenario_matrix.csv`
- `inversion_workflow/final_objective_include_exclude_recommendations.csv`
- `inversion_workflow/final_inversion_promotion_checklist_summary.json`
- `inversion_workflow/current_field_selection_audit_summary.json`
- `inversion_workflow/external_blocker_dashboard_summary.json`
- `inversion_workflow/gmail_draft_send_review_packet_summary.json`
- `inversion_workflow/permeability_support_conflict_spatial_audit_summary.json`
- `inversion_workflow/permeability_likelihood_policy_acceptance_record_template_summary.json`
- `inversion_workflow/permeability_next_field_fit_gate_summary.json`
