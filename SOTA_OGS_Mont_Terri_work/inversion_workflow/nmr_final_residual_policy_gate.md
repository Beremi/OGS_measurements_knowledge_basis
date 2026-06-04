# NMR Final Residual Policy Gate

This gate separates the current-report NMR default from a future final NMR
likelihood decision. It does not change the active objective, run OGS, or
modify the frozen GESA model.

- Status: `nmr_final_residual_policy_gate_generated`
- Final NMR policy selected: False
- Current-report default policy: `retain_raw_absolute_theta_current_report_default_with_caveats`
- Recommended candidate policy: `within_label_trend_anomaly`
- Recommended candidate run: `broad_continuous_001_003_length_0p021m`
- Current raw incumbent rank under trend/anomaly: 14.0
- Trend/anomaly winner raw rank: 56.0
- Follow-up recommendation: `pause_new_trend_anomaly_ogs_batch`

## Gate Table

| Gate | Type | Status | Decision | Evidence | Required acceptance |
| --- | --- | --- | --- | --- | --- |
| `NMR01_current_report_default` | `default_policy_gate` | `raw_absolute_nmr_retained_as_current_report_default_not_final` | Keep the historical raw absolute-theta NMR objective as the current-report default for reproducibility, but do not call it final without an accepted bound/free-water or model-error policy. | active_objective_changed=False; raw incumbent=local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000 objective=3156.353066948979; raw incumbent rank under trend/anomaly=14.0; usable mapped rows above fixed porosity=162/287 | A final decision must either accept raw absolute theta with explicit bound/free-water/model-error caveats, or select another NMR residual policy. |
| `NMR02_promoted_trend_anomaly_option` | `candidate_final_policy_gate` | `executable_trend_anomaly_policy_available_requires_acceptance` | Within-label trend/anomaly is the preferred provisional final NMR likelihood candidate if the modelling team accepts that NMR contributes changes/anomalies rather than absolute mobile water content. | mode=nmr_within_label_trend_anomaly; status=nmr_trend_anomaly_active_objective_mode_implemented_provisional; full-active runs=66; best trend run=broad_continuous_001_003_length_0p021m objective=505.614305828437; validation max abs delta=5.684341886080802e-14; trend winner raw rank=56.0 | Record promotion to the reporting/search default, regenerate conditional field selection, and state that absolute NMR water content is not being fitted. |
| `NMR03_promoted_mode_new_ogs_spending` | `execution_gate` | `no_new_trend_anomaly_ogs_batch_recommended_now` | Do not spend a new OGS batch solely to refine the promoted-NMR trend/anomaly mode until the final NMR policy is accepted and the materiality threshold is met. | follow-up recommendation=pause_new_trend_anomaly_ogs_batch; materiality threshold=0.7394950176895989; best unevaluated direct advantage=0.011974871836514467; median-state beating candidates=0; runnable unevaluated candidates=305 | Reopen only after final NMR semantics are chosen and a candidate has a material improvement under that accepted objective. |
| `NMR04_final_promotion_dependency` | `final_promotion_gate` | `blocks_final_promotion_until_nmr_policy_selected` | Do not promote any permeability field as final while the final NMR residual policy is still open. | scenario decision=single_field_not_stable_across_gate_scenarios; scenarios=8; unique winners=5; current-field wins=1; promoted-NMR scenario winner=broad_continuous_001_003_length_0p021m; promotion decision=do_not_promote_current_field; open promotion criteria=['P08_nmr_residual_policy', 'P09_ert_gate', 'P10_taupe_gate', 'P11_rh_gate', 'P12_other_hm_gate', 'P13_perm_endpoint_gate', 'P14_cte_confirmation', 'P15_conditional_field_stability', 'P16_final_field_decision'] | Choose raw absolute theta, within-label trend/anomaly, label-bias/free-water correction, or explicit NMR exclusion; then rerun scenario and promotion audits. |

## Next Decision Sequence

- Keep raw absolute theta as the current-report default for reproducibility until a final NMR policy is selected.
- If promoted, use within-label trend/anomaly as the preferred provisional final NMR residual and state that absolute water content is not fitted.
- Do not run a new trend/anomaly OGS batch now because the best unevaluated direct advantage is below the materiality threshold.
- After selecting the final NMR policy, regenerate conditional field selection, final promotion, final objective, and readiness audits.

## Interpretation

The executable within-label trend/anomaly residual is the safer provisional NMR policy because constant bound/interlayer-water and campaign offsets cancel to first order. It is not automatically the final default because it changes the selected field relative to the raw absolute-theta objective. Use `nmr_final_residual_policy_acceptance_record_template.md` as the separate signoff guardrail before treating any NMR residual option as accepted. The follow-up screen also says not to spend another OGS batch merely to refine this mode before the policy is accepted.

## Source Artifacts

- `inversion_workflow/nmr_objective_decision_summary.json`
- `inversion_workflow/nmr_trend_anomaly_active_objective_summary.json`
- `inversion_workflow/runs/nmr_trend_anomaly_followup_plan/NMR_TREND_ANOMALY_FOLLOWUP_PLAN.json`
- `inversion_workflow/conditional_field_selection_scenarios_summary.json`
- `inversion_workflow/final_inversion_promotion_checklist_summary.json`
