# Final Objective Include/Exclude Recommendations

This generated packet converts the open final-objective decision register into
conservative local recommendations for the current no-new-provider-evidence state.
It does not send email, close gates, record user approval, change OGS inputs,
or promote a permeability field.

- Status: `final_objective_include_exclude_recommendations_generated`
- Recommendations: 9
- External measurement/provenance recommendations: 6
- Internal policy recommendations: 1
- Scenario/final recommendations: 2
- Diagnostic or exclude without new evidence: 5
- Waivers not recommended: 8
- Final promotion unblocked by this packet: `False`
- Open blockers before packet: 8 (ert_transform_support, ert_uncertainty, hm_numeric_exports, hm_uncertainty, rh_active_curve_provenance, taupe_unit_calibration, perm_endpoint_geometry, cte_value_confirmation)
- Direct-permeability active/repeated/range>=2 support cells: 30/24/16
- Direct-permeability policy approvals: 0/1; ready=`False`
- Same-support active-objective batch executable: `False`

## Recommendation Table

| Criterion | Stream | Current use | Recommendation class | Recommended use without new evidence |
| --- | --- | --- | --- | --- |
| `P08_nmr_residual_policy` Final NMR residual policy | NMR water content | `active_raw_absolute_theta_with_provisional_trend_scenario` | `internal_policy_not_final` | Retain raw absolute NMR theta only as the current-report active-objective default with caveats; keep within-label trend/anomaly as the preferred provisional final-policy candidate, not as a promoted default. |
| `P09_ert_gate` ERT transform/support and uncertainty | ERT resistivity | `diagnostic_only` | `diagnostic_only_until_provider_acceptance` | Keep ERT as log-resistivity field-consistency diagnostic evidence only; exclude it from the final likelihood and final field-selection weights. |
| `P10_taupe_gate` Taupe/TDR unit calibration and uncertainty | Taupe/TDR | `diagnostic_only` | `diagnostic_only_until_provider_acceptance` | Keep Taupe/TDR as baseline-normalized trend diagnostic evidence only; exclude absolute Taupe values from final water-content likelihood terms. |
| `P11_rh_gate` RH active boundary-curve provenance and uncertainty | RH/suction | `boundary_audit_only` | `boundary_audit_only_until_provenance_acceptance` | Keep RH/suction as boundary provenance and scenario-audit evidence only; do not replace, fit, or weight the active pressure curve from local RH workbooks in the final objective. |
| `P12_other_hm_gate` Other-HM numeric exports, metadata, and uncertainty | Other HM monitoring | `not_ready_for_hard_residual` | `qualitative_context_until_numeric_exports_arrive` | Keep other HM monitoring as qualitative validation context and geometry/layout support only; exclude it from final hard residuals. |
| `P13_perm_endpoint_gate` Historical permeability endpoint geometry/provenance | Historical permeability pulse tests | `partial_active_support` | `partial_support_keep_endpoint_missing_rows_inactive` | Use only currently projected active pulse-test rows for the final direct permeability objective; keep historical endpoint-missing rows visible but inactive, and keep the current rowwise-Gaussian support/likelihood policy active-only until a policy decision is approved. |
| `P14_cte_confirmation` Suspicious CTE value confirmation | Frozen OGS model provenance | `frozen_uninterpreted_caveat` | `model_provenance_scope_out` | Scope the suspicious CTE value out of the final permeability objective; keep the exchanged OGS model frozen and record CTE as an uninterpreted source caveat. |
| `P15_conditional_field_stability` Accepted scenario set and winner stability | Final objective scenario set | `unstable_scenario_winners` | `do_not_promote_until_scenario_explicit` | Keep the current field active-only; no final scenario is stable enough for implicit promotion. |
| `P16_final_field_decision` Promote or keep active-only field label | Final field approval | `active_objective_incumbent_only` | `keep_active_incumbent_label` | Do not promote the packaged field.  Keep it labelled as the active direct-permeability/raw-NMR incumbent. |

## Detailed Recommendations

### `P08_nmr_residual_policy` Final NMR residual policy

- Conservative recommendation: Do not change the NMR default or call the current raw-NMR residual final until the modelling team records the free-water/bound-water policy and regenerates the scenario/current-field audits.
- Include requires: A recorded final NMR residual policy: raw absolute theta with caveats, within-label trend/anomaly, label/campaign bias, explicit free-water correction, or exclusion from final field selection.
- Report wording if no new evidence: NMR is retained in the current active objective as raw absolute water content with bound-water caveats.  No final NMR residual policy is selected; within-label trend/anomaly remains the preferred provisional candidate.
- Waiver position: `not_applicable_internal_policy_required`
- Why waiver is not recommended: The unresolved issue is not missing provider evidence but the physical semantics of total versus mobile/free water in the OGS state residual.
- Current evidence: recommended=within_label_trend_anomaly; executable_status=nmr_trend_anomaly_active_objective_mode_implemented_provisional; best_run=broad_continuous_001_003_length_0p021m; validation_delta=5.684341886080802e-14; followup=pause_new_trend_anomaly_ogs_batch.; active_objective_changed=False; recommended=within_label_trend_anomaly; best_recommended_run=broad_continuous_001_003_length_0p021m; executable_best=broad_continuous_001_003_length_0p021m; raw_incumbent_rank_under_trend=14.0; trend_winner_raw_rank=56.0; followup=pause_new_trend_anomaly_ogs_batch; median_state_beating_candidates=0.; NMR final policy selected=False; recommended candidate=within_label_trend_anomaly; recommended run=broad_continuous_001_003_length_0p021m; follow-up=pause_new_trend_anomaly_ogs_batch
- Related blockers/decisions: nmr_bound_water,nmr_default_promotion
- Response or decision locations: inversion_workflow/nmr_objective_decision.md; inversion_workflow/nmr_trend_anomaly_active_objective.md; inversion_workflow/runs/nmr_trend_anomaly_followup_plan/NMR_TREND_ANOMALY_FOLLOWUP_PLAN.md; inversion_workflow/nmr_objective_decision.md; inversion_workflow/nmr_trend_anomaly_active_objective.md; inversion_workflow/runs/nmr_trend_anomaly_followup_plan/NMR_TREND_ANOMALY_FOLLOWUP_PLAN.md; inversion_workflow/conditional_field_selection_scenarios.md
- Promotion effect: This packet does not unblock promotion. It provides a conservative recommendation that still must be recorded as a modelling decision, then refreshed through scenario/current-field/promotion audits.
- Refresh after decision: `python inversion_workflow/scripts/build_internal_gate_decision_register.py; python inversion_workflow/scripts/build_conditional_field_selection_scenarios.py; python inversion_workflow/scripts/build_current_field_selection_audit.py; python inversion_workflow/scripts/build_final_inversion_promotion_checklist.py; python inversion_workflow/scripts/build_final_inversion_closeout_playbook.py; python inversion_workflow/scripts/build_final_objective_decision_register.py; python inversion_workflow/scripts/build_final_objective_scenario_matrix.py; python inversion_workflow/scripts/build_objective_readiness_audit.py`

### `P09_ert_gate` ERT transform/support and uncertainty

- Conservative recommendation: Do not use the dense ERT VTK pixels as independent final residual rows until the coordinate transform, near-niche support mask, and uncertainty/correlation model are accepted.
- Include requires: Provider or modelling-team acceptance of the ERT-to-OGS transform, exact support mask, and covariance/weighting model. Acceptance tests: A reproducible ERT-to-OGS transform and accepted support mask can be encoded without freehand interpretation; the ERT spatial projection and support-sensitivity audits can be regenerated with no provisional-transform caveat.; The ERT likelihood can assign defensible row/group weights without treating dense VTK cells as independent observations.
- Report wording if no new evidence: ERT was retained as diagnostic field-consistency evidence and excluded from the final likelihood because the ERT-to-OGS transform/support and uncertainty/correlation model were not confirmed.
- Waiver position: `not_recommended`
- Why waiver is not recommended: The current bridge is provisional and the VTK cells are spatially dense, correlated inversion outputs rather than independent measurements.
- Current evidence: ERT-to-OGS transform and exact near-niche support mask remain assumed, not confirmed.; No defensible ERT residual sigma/correlation model is available; pixels cannot be treated as independent rows.
- Related blockers/decisions: ert_transform_support,ert_uncertainty
- Response or decision locations: /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses/ert_transform_support_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses/ert_uncertainty_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses
- Promotion effect: This packet does not unblock promotion. It provides a conservative recommendation that still must be recorded as a modelling decision, then refreshed through scenario/current-field/promotion audits.
- Refresh after decision: `python inversion_workflow/scripts/build_external_gate_response_intake.py; python inversion_workflow/scripts/build_external_gate_dispatch_audit.py; python inversion_workflow/scripts/build_external_blocker_dashboard.py; python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; python inversion_workflow/scripts/build_conditional_field_selection_scenarios.py; python inversion_workflow/scripts/build_current_field_selection_audit.py; python inversion_workflow/scripts/build_final_inversion_promotion_checklist.py; python inversion_workflow/scripts/build_final_inversion_closeout_playbook.py; python inversion_workflow/scripts/build_final_objective_decision_register.py; python inversion_workflow/scripts/build_final_objective_scenario_matrix.py; python inversion_workflow/scripts/build_objective_readiness_audit.py`

### `P10_taupe_gate` Taupe/TDR unit calibration and uncertainty

- Conservative recommendation: Do not activate Taupe/TDR as an absolute saturation or water-content residual until units, calibration, and uncertainty are confirmed.
- Include requires: Provider confirmation of whether workbook values are volumetric water content, dielectric/permittivity proxy, ARDP-derived index, or trend-only quantity, plus uncertainty/weighting guidance. Acceptance tests: The Taupe semantics audit can decide whether absolute Taupe values are water content, permittivity/proxy, or trend-only evidence.
- Report wording if no new evidence: Taupe/TDR was retained as a mapped trend diagnostic and excluded from the final likelihood because unit calibration and residual uncertainty were not confirmed.
- Waiver position: `not_recommended`
- Why waiver is not recommended: The same workbook values can imply different physical residuals depending on calibration; treating them as absolute water content would overstate the current evidence.
- Current evidence: Taupe values are not confirmed as volumetric water-content percent, permittivity, or another ARDP-derived proxy.
- Related blockers/decisions: taupe_unit_calibration
- Response or decision locations: /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/provider_responses/taupe_unit_calibration_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/provider_responses
- Promotion effect: This packet does not unblock promotion. It provides a conservative recommendation that still must be recorded as a modelling decision, then refreshed through scenario/current-field/promotion audits.
- Refresh after decision: `python inversion_workflow/scripts/build_external_gate_response_intake.py; python inversion_workflow/scripts/build_external_gate_dispatch_audit.py; python inversion_workflow/scripts/build_external_blocker_dashboard.py; python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; python inversion_workflow/scripts/build_conditional_field_selection_scenarios.py; python inversion_workflow/scripts/build_current_field_selection_audit.py; python inversion_workflow/scripts/build_final_inversion_promotion_checklist.py; python inversion_workflow/scripts/build_final_inversion_closeout_playbook.py; python inversion_workflow/scripts/build_final_objective_decision_register.py; python inversion_workflow/scripts/build_final_objective_scenario_matrix.py; python inversion_workflow/scripts/build_objective_readiness_audit.py`

### `P11_rh_gate` RH active boundary-curve provenance and uncertainty

- Conservative recommendation: Do not release retention or boundary parameters from RH until the active curve provenance, constants, time axis, sensor screening, extension policy, and uncertainty are accepted.
- Include requires: Accepted provenance for the active XML pressure curve and an uncertainty model for any RH-derived boundary forcing or retention target. Acceptance tests: The active XML pressure curve can be regenerated or explained well enough that replacement curves/retention targets are no longer based on unknown provenance.
- Report wording if no new evidence: RH/suction was retained as boundary-provenance and scenario evidence only; it was not used as a weighted residual or to replace the active pressure curve because the active-curve provenance and uncertainty remain unconfirmed.
- Waiver position: `not_recommended`
- Why waiver is not recommended: Changing boundary forcing changes the forward problem, and the current active curve is not yet reproducible from confirmed local RH processing.
- Current evidence: Active boundary curve generation, sensor screening, time axis, constants, and extension policy are not confirmed.
- Related blockers/decisions: rh_active_curve_provenance
- Response or decision locations: /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/provider_responses/rh_active_curve_provenance_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/provider_responses
- Promotion effect: This packet does not unblock promotion. It provides a conservative recommendation that still must be recorded as a modelling decision, then refreshed through scenario/current-field/promotion audits.
- Refresh after decision: `python inversion_workflow/scripts/build_external_gate_response_intake.py; python inversion_workflow/scripts/build_external_gate_dispatch_audit.py; python inversion_workflow/scripts/build_external_blocker_dashboard.py; python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; python inversion_workflow/scripts/build_conditional_field_selection_scenarios.py; python inversion_workflow/scripts/build_current_field_selection_audit.py; python inversion_workflow/scripts/build_final_inversion_promotion_checklist.py; python inversion_workflow/scripts/build_final_inversion_closeout_playbook.py; python inversion_workflow/scripts/build_final_objective_decision_register.py; python inversion_workflow/scripts/build_final_objective_scenario_matrix.py; python inversion_workflow/scripts/build_objective_readiness_audit.py`

### `P12_other_hm_gate` Other-HM numeric exports, metadata, and uncertainty

- Conservative recommendation: Do not assign mechanical/hydraulic likelihood weights to Geoscope, laser, levelling, extensometer, mini-piezometer, or crackmeter evidence until numeric time series, support definitions, metadata, and uncertainty arrive.
- Include requires: Hard-residual-ready numeric exports with timestamps or epochs, units, instrument/support definitions, coordinate frame, quality flags, and uncertainty/registration metadata. Acceptance tests: The other-HM source audit finds at least one hard-residual-ready numeric request class with time/epoch and model-facing support.; Each candidate other-HM residual has enough metadata to state which OGS quantity/support it measures and what residual weight it receives.
- Report wording if no new evidence: Other HM streams were retained as qualitative or geometric context only and excluded from the final likelihood because hard-residual-ready numeric exports, support definitions, and uncertainties were not available locally.
- Waiver position: `not_recommended`
- Why waiver is not recommended: The local bundle does not yet contain enough numeric support and uncertainty metadata to define a reproducible OGS residual.
- Current evidence: Local source scan found layout geometry, laser surface geometry, extracted levelling slide rows, and report/minute evidence, but no hard-residual-ready Geoscope time series, laser statistical interpretation product, or full levelling survey table.; Required metadata for hard HM residual weights are absent from the current local bundle.
- Related blockers/decisions: hm_numeric_exports,hm_uncertainty
- Response or decision locations: /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses/hm_numeric_exports_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses/hm_uncertainty_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses
- Promotion effect: This packet does not unblock promotion. It provides a conservative recommendation that still must be recorded as a modelling decision, then refreshed through scenario/current-field/promotion audits.
- Refresh after decision: `python inversion_workflow/scripts/build_external_gate_response_intake.py; python inversion_workflow/scripts/build_external_gate_dispatch_audit.py; python inversion_workflow/scripts/build_external_blocker_dashboard.py; python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; python inversion_workflow/scripts/build_conditional_field_selection_scenarios.py; python inversion_workflow/scripts/build_current_field_selection_audit.py; python inversion_workflow/scripts/build_final_inversion_promotion_checklist.py; python inversion_workflow/scripts/build_final_inversion_closeout_playbook.py; python inversion_workflow/scripts/build_final_objective_decision_register.py; python inversion_workflow/scripts/build_final_objective_scenario_matrix.py; python inversion_workflow/scripts/build_objective_readiness_audit.py`

### `P13_perm_endpoint_gate` Historical permeability endpoint geometry/provenance

- Conservative recommendation: Do not include BCD-A24/25/26/27 or BFM-D19 historical rows as hard residuals until labelled endpoint geometry or an approved digitized trace is accepted.
- Include requires: Label-resolved start/end or collar/tip geometry, coordinate frame, depth-zero reference, interval-position convention, and uncertainty for the blocked historical traces; plus an explicit support/likelihood policy if the final objective is meant to change the current one-value-per-support-cell treatment. Acceptance tests: Inactive historical rows can be projected to OGS cells with a trace/support definition rather than excluded for missing geometry.; Direct-permeability policy evidence: support-conflict audit=permeability_support_conflict_spatial_audit_generated; active/repeated/range>=2 support cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes
- Report wording if no new evidence: Endpoint-missing historical permeability rows were kept inactive and excluded from the final hard residual set; the direct permeability objective used only rows with current accepted projection support.
- Waiver position: `not_recommended`
- Why waiver is not recommended: A scalar interval permeability value cannot be projected defensibly to an OGS support cell or trace without the missing borehole endpoint geometry, and the current active support map already contains repeated-row conflicts that require a separate likelihood/support decision.
- Current evidence: Historical permeability endpoints are needed only if these older rows should enter the fit.; support-conflict audit=permeability_support_conflict_spatial_audit_generated; active/repeated/range>=2 support cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes
- Related blockers/decisions: perm_endpoint_geometry
- Response or decision locations: /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/permeability_pulse_tests/source_files/provider_responses/perm_endpoint_geometry_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/permeability_pulse_tests/source_files/provider_responses; inversion_workflow/permeability_support_conflict_spatial_audit.md; inversion_workflow/permeability_support_lower_bound_audit.md; inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md; inversion_workflow/permeability_next_field_fit_gate.md
- Promotion effect: This packet does not unblock promotion. It provides a conservative recommendation that still must be recorded as a modelling decision, then refreshed through scenario/current-field/promotion audits.
- Refresh after decision: `python inversion_workflow/scripts/build_external_gate_response_intake.py; python inversion_workflow/scripts/build_external_gate_dispatch_audit.py; python inversion_workflow/scripts/build_external_blocker_dashboard.py; python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; python inversion_workflow/scripts/build_conditional_field_selection_scenarios.py; python inversion_workflow/scripts/build_current_field_selection_audit.py; python inversion_workflow/scripts/build_final_inversion_promotion_checklist.py; python inversion_workflow/scripts/build_final_inversion_closeout_playbook.py; python inversion_workflow/scripts/build_final_objective_decision_register.py; python inversion_workflow/scripts/build_final_objective_scenario_matrix.py; python inversion_workflow/scripts/build_objective_readiness_audit.py`

### `P14_cte_confirmation` Suspicious CTE value confirmation

- Conservative recommendation: Do not interpret, calibrate, or correct thermal expansivity locally.  The permeability-field result must avoid claims that depend on the suspicious CTE value unless a provider response confirms it.
- Include requires: Provider confirmation of whether CTE=1254.74 is intended, inactive, copied from heat capacity, or subject to a convention not visible in the XML. Acceptance tests: The CTE row in the report open-comment audit can move from open_confirmation_required to confirmed_inactive, confirmed_typo_not_changed, or confirmed_value_recorded with the provider response cited.
- Report wording if no new evidence: The CTE value remains a frozen-source caveat and was not interpreted or calibrated in the permeability-field objective.
- Waiver position: `not_recommended`
- Why waiver is not recommended: The model is required to remain frozen; local correction would create a new model version rather than documenting the exchanged model.
- Current evidence: The XML binds CTE to solid thermal_expansivity, but the value and comment look like a copied heat-capacity entry. The model must remain frozen, so this needs provenance confirmation rather than a local correction.
- Related blockers/decisions: cte_value_confirmation
- Response or decision locations: inversion_workflow/cte_confirmation_request.md
- Promotion effect: This packet does not unblock promotion. It provides a conservative recommendation that still must be recorded as a modelling decision, then refreshed through scenario/current-field/promotion audits.
- Refresh after decision: `python inversion_workflow/scripts/build_external_gate_response_intake.py; python inversion_workflow/scripts/build_external_gate_dispatch_audit.py; python inversion_workflow/scripts/build_external_blocker_dashboard.py; python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; python inversion_workflow/scripts/build_conditional_field_selection_scenarios.py; python inversion_workflow/scripts/build_current_field_selection_audit.py; python inversion_workflow/scripts/build_final_inversion_promotion_checklist.py; python inversion_workflow/scripts/build_final_inversion_closeout_playbook.py; python inversion_workflow/scripts/build_final_objective_decision_register.py; python inversion_workflow/scripts/build_final_objective_scenario_matrix.py; python inversion_workflow/scripts/build_objective_readiness_audit.py`

### `P15_conditional_field_stability` Accepted scenario set and winner stability

- Conservative recommendation: If the conservative exclusions above are accepted, record them explicitly and rerun the conditional scenario and current-field audits before changing any field label.
- Include requires: A single accepted final objective scenario or a regenerated scenario matrix showing a stable winner after all include/exclude decisions are recorded.; Direct-permeability policy evidence: support-conflict audit=permeability_support_conflict_spatial_audit_generated; active/repeated/range>=2 support cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes
- Report wording if no new evidence: The accepted final objective scenario was not selected; therefore the current field remains an active-objective incumbent, not a final all-measurement field.
- Waiver position: `not_recommended`
- Why waiver is not recommended: Current scored scenarios select multiple winners, so implicit promotion would hide a real objective-dependence.
- Current evidence: scenarios=8; unique winners=5; current-field wins=1; final decision=single_field_not_stable_across_gate_scenarios; support-conflict audit=permeability_support_conflict_spatial_audit_generated; active/repeated/range>=2 support cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes
- Related blockers/decisions: none
- Response or decision locations: inversion_workflow/conditional_field_selection_scenarios.md; inversion_workflow/current_field_selection_audit.md; inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md; inversion_workflow/permeability_next_field_fit_gate.md
- Promotion effect: This packet does not unblock promotion. It provides a conservative recommendation that still must be recorded as a modelling decision, then refreshed through scenario/current-field/promotion audits.
- Refresh after decision: `python inversion_workflow/scripts/build_conditional_field_selection_scenarios.py; python inversion_workflow/scripts/build_conditional_field_candidate_package.py; python inversion_workflow/scripts/build_conditional_field_difference_audit.py; python inversion_workflow/scripts/build_current_field_selection_audit.py; python inversion_workflow/scripts/build_final_inversion_promotion_checklist.py; python inversion_workflow/scripts/build_final_inversion_closeout_playbook.py; python inversion_workflow/scripts/build_final_objective_decision_register.py; python inversion_workflow/scripts/build_final_objective_scenario_matrix.py; python inversion_workflow/scripts/build_objective_readiness_audit.py`

### `P16_final_field_decision` Promote or keep active-only field label

- Conservative recommendation: Only promote a field after the promotion checklist and current-field selection audit both record final approval under an accepted final objective.
- Include requires: Closed, explicitly excluded, or explicitly waived upstream rows plus regenerated promotion and current-field selection audits recording final approval.; Direct-permeability policy evidence: support-conflict audit=permeability_support_conflict_spatial_audit_generated; active/repeated/range>=2 support cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes
- Report wording if no new evidence: The current field is not a final all-measurement inversion result; it is the active-objective incumbent under the current direct-permeability/raw-NMR setup.
- Waiver position: `not_recommended`
- Why waiver is not recommended: The promotion checklist still contains open criteria and the current-field selection audit currently rejects final promotion.
- Current evidence: active decision=accept_as_current_active_objective_incumbent; final decision=do_not_promote_to_final_all_measurement_field; status counts={'pass': 2, 'pass_with_caveat': 2, 'fails_final_promotion': 2, 'blocked_or_gated': 4}; support-conflict audit=permeability_support_conflict_spatial_audit_generated; active/repeated/range>=2 support cells=30/24/16; top conflict cell=4648 (BCD-A32 0.85-0.87 m, observed range=6.948847477552619); same-support lower-bound gap=0.0; current at lower bound=True; policy approvals=0/1; policy ready=False; same-support batch executable=False; next recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes; current-field final decision=do_not_promote_to_final_all_measurement_field
- Related blockers/decisions: none
- Response or decision locations: inversion_workflow/conditional_field_selection_scenarios.md; inversion_workflow/current_field_selection_audit.md; inversion_workflow/permeability_likelihood_policy_acceptance_record_template.md; inversion_workflow/permeability_next_field_fit_gate.md
- Promotion effect: This packet does not unblock promotion. It provides a conservative recommendation that still must be recorded as a modelling decision, then refreshed through scenario/current-field/promotion audits.
- Refresh after decision: `python inversion_workflow/scripts/build_conditional_field_selection_scenarios.py; python inversion_workflow/scripts/build_conditional_field_candidate_package.py; python inversion_workflow/scripts/build_conditional_field_difference_audit.py; python inversion_workflow/scripts/build_current_field_selection_audit.py; python inversion_workflow/scripts/build_final_inversion_promotion_checklist.py; python inversion_workflow/scripts/build_final_inversion_closeout_playbook.py; python inversion_workflow/scripts/build_final_objective_decision_register.py; python inversion_workflow/scripts/build_final_objective_scenario_matrix.py; python inversion_workflow/scripts/build_objective_readiness_audit.py`

## Interpretation

- Without new provider evidence, the conservative local position is to keep ERT, Taupe/TDR, RH/suction, other-HM monitoring, endpoint-missing historical permeability rows, and CTE out of final hard likelihood weights.
- The direct-permeability current-support objective is also policy-gated: repeated support-cell conflicts and zero same-support reducible gap require an explicit support/likelihood decision before more same-support OGS spending or final promotion.
- NMR remains an internal policy decision: the report can keep the current raw-theta default with caveats, but final promotion still needs an accepted NMR residual policy.
- Recording these recommendations as actual decisions would still require a rerun of the scenario, current-field, and final-promotion audits.
- Until that happens, the current field label remains active-objective incumbent only.

## Source Artifacts

- `inversion_workflow/final_objective_decision_register.csv`
- `inversion_workflow/external_blocker_dashboard.csv`
- `inversion_workflow/nmr_final_residual_policy_gate_summary.json`
- `inversion_workflow/final_inversion_promotion_checklist_summary.json`
- `inversion_workflow/current_field_selection_audit_summary.json`
- `inversion_workflow/permeability_support_conflict_spatial_audit_summary.json`
- `inversion_workflow/permeability_support_lower_bound_audit_summary.json`
- `inversion_workflow/permeability_likelihood_policy_acceptance_record_template_summary.json`
- `inversion_workflow/permeability_next_field_fit_gate_summary.json`
