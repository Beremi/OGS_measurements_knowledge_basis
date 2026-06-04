# NMR Final Residual Policy Acceptance Record Template

This generated file is a fillable signoff template for the final NMR residual
policy. It is not an approval record, does not change the active objective,
does not recommend a new OGS batch, and does not promote a permeability field.

- Status: `nmr_final_residual_policy_acceptance_record_template_generated`
- Template rows: 4
- Primary policy approvals required: 1
- Primary policy approvals recorded: 0
- Ready to apply policy: `False`
- Records actual decision: `False`
- Changes active objective: `False`
- Promotes current field: `False`
- New OGS batch recommended now: `False`
- Current-report default before approval: `retain_raw_absolute_theta_current_report_default_with_caveats`
- Recommended candidate before approval: `within_label_trend_anomaly`
- Recommended candidate run before approval: `broad_continuous_001_003_length_0p021m`
- Follow-up recommendation before approval: `pause_new_trend_anomaly_ogs_batch`

## Required Approval Fields

Exactly one row must be selected as the primary final NMR policy and must
have all of the following fields filled from a real modelling-team decision:

- `approval_status=approved`
- `primary_policy_selection=selected`
- `approver_name`
- `approval_date`
- `approval_reference`
- `accepted_residual_definition`

For absolute or bias-corrected policies, also fill the bound/free-water,
bias/offset, reporting wording, and next-OGS materiality fields.

## Template Rows

| Option | Decision | Approval status | Current final recommendation | Selected run | Combined objective |
| --- | --- | --- | --- | --- | ---: |
| `raw_absolute_current` | `current_active_but_conditional` | `not_approved_template_only` | `no` | `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | 3156.353066948979 |
| `global_uniform_offset` | `stress_test_only_not_recommended` | `not_approved_template_only` | `no` | `regularized_ogs_candidate_001_length_0p025m` | 665.7113665537574 |
| `absolute_with_label_bias` | `acceptable_if_absolute_nmr_is_required` | `not_approved_template_only` | `conditional` | `broad_continuous_001_003_length_0p021m` | 505.614305828437 |
| `within_label_trend_anomaly` | `recommended_provisional_nmr_residual` | `not_approved_template_only` | `yes_after_acceptance` | `broad_continuous_001_003_length_0p021m` | 505.614305828437 |

## Acceptance Criteria

### `raw_absolute_current`

- Residual definition: theta_model - raw theta_NMR_obs
- Nuisance terms: none
- Main rationale: This is the implemented active residual, but it compares total NMR-visible water content to mobile OGS theta without a bound/interlayer-water term.
- Nonphysical or caveated rows/offsets: 120
- Acceptance criteria: Do not call this final unless a bound/interlayer-water model-error term is accepted and the report states that the residual is conditional.
- Post-approval reruns: Rerun conditional field selection, final objective scenario matrix, final promotion checklist, open-question matrix, and objective readiness audit before changing any final field label. Rerun candidate scoring if the accepted residual formula differs from the audited options.

### `global_uniform_offset`

- Residual definition: theta_model - (theta_NMR_obs - global_offset)
- Nuisance terms: single global offset, best physical-count offset=0.05
- Main rationale: A single subtraction improves physical-row counts but still leaves nonphysical rows and overcorrects low-water labels; it is useful only as a sensitivity check.
- Nonphysical or caveated rows/offsets: 3
- Acceptance criteria: Reject as final unless collaborators provide one physically justified global offset.
- Post-approval reruns: Rerun conditional field selection, final objective scenario matrix, final promotion checklist, open-question matrix, and objective readiness audit before changing any final field label. Rerun candidate scoring if the accepted residual formula differs from the audited options.

### `absolute_with_label_bias`

- Residual definition: theta_model + b_label - theta_NMR_obs
- Nuisance terms: non-negative label/campaign bias per observation_family + measurement_label
- Main rationale: This preserves absolute information while explicitly absorbing constant bound/interlayer-water and campaign offsets.
- Nonphysical or caveated rows/offsets: bias_mean=0.053584; bias_p90=0.072046; bias_max=0.075639
- Acceptance criteria: Requires an approved prior/penalty or reporting policy for bias terms; biases must not be silently interpreted as transport water.
- Post-approval reruns: Rerun conditional field selection, final objective scenario matrix, final promotion checklist, open-question matrix, and objective readiness audit before changing any final field label. Rerun candidate scoring if the accepted residual formula differs from the audited options.

### `within_label_trend_anomaly`

- Residual definition: (theta_model - mean_label(theta_model)) - (theta_NMR_obs - mean_label(theta_NMR_obs))
- Nuisance terms: constant label/campaign offsets cancel by centering
- Main rationale: This is the safest first OGS-backed NMR residual because constant bound/interlayer-water offsets cancel to first order and no porosity release is needed.
- Nonphysical or caveated rows/offsets: absolute offsets removed; absolute water content not fitted
- Acceptance criteria: The executable assembler mode and ranking package now exist; accepting this option means promoting it to the reporting/search default and stating that NMR contributes trends/anomalies, not absolute mobile water content.
- Post-approval reruns: Rerun conditional field selection, final objective scenario matrix, final promotion checklist, open-question matrix, and objective readiness audit before changing any final field label. Rerun candidate scoring if the accepted residual formula differs from the audited options.

## Source Artifacts

- `inversion_workflow/nmr_objective_decision.csv`
- `inversion_workflow/nmr_objective_decision_summary.json`
- `inversion_workflow/nmr_final_residual_policy_gate_summary.json`
