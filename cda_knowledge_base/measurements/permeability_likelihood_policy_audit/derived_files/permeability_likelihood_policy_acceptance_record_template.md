# Permeability Likelihood Policy Acceptance Record Template

This generated file is a fillable signoff template for the direct-permeability
likelihood/support/outlier policy. It is not an approval record, does not
change the active objective, does not reopen OGS spending, and does not promote
a permeability field.

- Status: `permeability_likelihood_policy_acceptance_record_template_generated`
- Template rows: 5
- Primary policy approvals required: 1
- Primary policy approvals recorded: 0
- Ready to apply policy: `False`
- Records actual decision: `False`
- Changes active objective: `False`
- Promotes current field: `False`
- Same-support batch executable now: `False`
- Current-report policy before approval: `keep_rowwise_gaussian_default`
- Spatial support cells active/repeated/range>=2 log10: 30/24/16
- Next field-fit gate recommendation: `pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes`

## Required Approval Fields

Exactly one row must be selected as the primary policy and must have all of the
following fields filled from a real modelling-team decision:

- `approval_status=approved`
- `primary_policy_selection=selected`
- `approver_name`
- `approval_date`
- `approval_reference`
- `accepted_formula_or_policy_text`

For non-default policies, also fill the applicable grouping, outlier/bounds,
or materiality fields before rerunning downstream audits.

## Template Rows

| Option | Type | Approval status | Recommended default | Diagnostic value |
| --- | --- | --- | --- | ---: |
| `keep_rowwise_gaussian_default` | `retain_current_default` | `not_approved_template_only` | `True` | 269.8180571059851 |
| `use_robust_row_likelihood` | `change_default_or_create_scenario` | `not_approved_template_only` | `False` | 121.16896116540622 |
| `aggregate_by_model_support_cell` | `change_default_or_create_scenario` | `not_approved_template_only` | `False` | 1.767048427695066e-28 |
| `gate_configured_scalar_outliers` | `source_or_parameterization_decision` | `not_approved_template_only` | `False` | 245.67481647284035 |
| `new_parameterization_before_more_ogs` | `future_search_gate` | `not_approved_template_only` | `False` | 269.8180571059851 |

## Acceptance Criteria

### `keep_rowwise_gaussian_default`

- Objective policy: duplicate-weighted Gaussian row residuals in log10 intrinsic permeability with sigma=0.5
- Risk or caveat: Top-10 row-loss share is 0.494 and 16 support groups span at least one log10 unit, so the active objective over-emphasizes conflicting rows unless this is intentional.
- Acceptance criteria: A modelling-team statement that the current rowwise Gaussian objective remains the default despite support-cell conflicts, plus wording that the field is not final for all measurement streams.
- Support-conflict evidence to acknowledge: Spatial support-conflict audit status=permeability_support_conflict_spatial_audit_generated; active/repeated/range>=2 support cells=30/24/16; top conflict cell=4648 (BCD-A32 at 0.85-0.87 m, observed range=6.948847477552619)
- Post-approval reruns: Rerun permeability likelihood rerank if the accepted formula differs from the audited diagnostic policies; rerun current-field, scenario, promotion, open-question, and readiness audits before changing any field label or reopening OGS spending.

### `use_robust_row_likelihood`

- Objective policy: Huber, capped-Gaussian, or Student-t row residuals in log10 permeability
- Risk or caveat: Diagnostic objective-like values: capped=65.3119, Huber=183.671, Student-t=121.169. These values are not identical likelihood normalizations.
- Acceptance criteria: A written kernel formula, scale, outlier treatment, and rule for comparing historical row-Gaussian candidate objectives to the new policy.
- Support-conflict evidence to acknowledge: Spatial support-conflict audit status=permeability_support_conflict_spatial_audit_generated; active/repeated/range>=2 support cells=30/24/16; top conflict cell=4648 (BCD-A32 at 0.85-0.87 m, observed range=6.948847477552619)
- Post-approval reruns: Rerun permeability likelihood rerank if the accepted formula differs from the audited diagnostic policies; rerun current-field, scenario, promotion, open-question, and readiness audits before changing any field label or reopening OGS spending.

### `aggregate_by_model_support_cell`

- Objective policy: collapse rows sharing one active model support cell before scoring
- Risk or caveat: Support-cell weighted-mean objective is 1.767e-28 while median objective is 134.728; this difference shows that the aggregation rule itself is consequential.
- Acceptance criteria: A written grouping key, aggregation statistic, group weight, and reporting rule for within-support observation ranges.
- Support-conflict evidence to acknowledge: Spatial support-conflict audit status=permeability_support_conflict_spatial_audit_generated; active/repeated/range>=2 support cells=30/24/16; top conflict cell=4648 (BCD-A32 at 0.85-0.87 m, observed range=6.948847477552619)
- Post-approval reruns: Rerun permeability likelihood rerank if the accepted formula differs from the audited diagnostic policies; rerun current-field, scenario, promotion, open-question, and readiness audits before changing any field label or reopening OGS spending.

### `gate_configured_scalar_outliers`

- Objective policy: treat rows outside configured scalar tensor range separately from ordinary Gaussian rows
- Risk or caveat: 2 active rows are outside the configured scalar range; inside-only Gaussian objective is 245.675 and does not remove the broader support-cell conflicts.
- Acceptance criteria: A written outlier disposition for each configured-scalar-range row and an explicit release decision if bounds or tensor shape change.
- Support-conflict evidence to acknowledge: Spatial support-conflict audit status=permeability_support_conflict_spatial_audit_generated; active/repeated/range>=2 support cells=30/24/16; top conflict cell=4648 (BCD-A32 at 0.85-0.87 m, observed range=6.948847477552619)
- Post-approval reruns: Rerun permeability likelihood rerank if the accepted formula differs from the audited diagnostic policies; rerun current-field, scenario, promotion, open-question, and readiness audits before changing any field label or reopening OGS spending.

### `new_parameterization_before_more_ogs`

- Objective policy: do not spend more routine OGS on current smooth/local-basis family without a new field family
- Risk or caveat: Existing anisotropy, local-basis, production, cross-stream hybrid, and structural/EDZ screens did not find a material direct-improving follow-up family.
- Acceptance criteria: A next-run gate that names the accepted likelihood policy, the field family to be tested, and the materiality threshold for spending additional OGS runs.
- Support-conflict evidence to acknowledge: Spatial support-conflict audit status=permeability_support_conflict_spatial_audit_generated; active/repeated/range>=2 support cells=30/24/16; top conflict cell=4648 (BCD-A32 at 0.85-0.87 m, observed range=6.948847477552619)
- Post-approval reruns: Rerun permeability likelihood rerank if the accepted formula differs from the audited diagnostic policies; rerun current-field, scenario, promotion, open-question, and readiness audits before changing any field label or reopening OGS spending.

## Source Artifacts

- `inversion_workflow/permeability_likelihood_decision_request.csv`
- `inversion_workflow/permeability_likelihood_decision_request_summary.json`
- `inversion_workflow/permeability_likelihood_support_recommendations_summary.json`
- `inversion_workflow/permeability_support_conflict_spatial_audit_summary.json`
- `inversion_workflow/permeability_next_field_fit_gate_summary.json`
