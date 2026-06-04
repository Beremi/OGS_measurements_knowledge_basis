# Permeability Likelihood Decision Request

This request converts the direct-permeability likelihood-policy audit into modelling-team decisions.
It does not change the active objective by itself.

## Summary

- Status: `permeability_likelihood_decision_request_generated`
- Active direct rows: 75
- Current row-Gaussian objective: 269.818
- Support-cell mean diagnostic objective: 1.767e-28
- Support-cell median diagnostic objective: 134.728
- Support groups with observed range >= 1 log10: 16
- Active rows outside configured scalar range: 2
- Top-10 row-loss share: 0.494

## Existing-Field Rerank Evidence

- Rerank status: `permeability_likelihood_scenario_rerank_generated`
- Candidate fields scored: 522
- Current row-Gaussian best-tie count: 40
- Current accepted field tied for row-Gaussian best: True
- Diagnostic policy winners outside the row-Gaussian best tie set: 3

## Winner Cross-Stream Evidence

- Cross-stream audit status: `permeability_likelihood_winner_cross_stream_audit_generated`
- Policy winner rows with cross-stream scorecard evidence: 4
- Unique winner fields with cross-stream scorecard evidence: 2
- Direct-only policy winner rows: 3
- Outside-tie direct-only policy winner rows: 3
- Row-Gaussian representative active rank: 45.0
- Current accepted active rank: 1.0

## Decision Options

| Option | Default? | Policy | Diagnostic value | Required action | Acceptance criteria |
| --- | --- | --- | ---: | --- | --- |
| `keep_rowwise_gaussian_default` | `yes` | duplicate-weighted Gaussian row residuals in log10 intrinsic permeability with sigma=0.5 | 269.818 | Keep the active objective unchanged for reproducibility; report large row conflicts explicitly; do not claim that further smooth field sampling is the primary remedy. | A modelling-team statement that the current rowwise Gaussian objective remains the default despite support-cell conflicts, plus wording that the field is not final for all measurement streams. |
| `use_robust_row_likelihood` | `no` | Huber, capped-Gaussian, or Student-t row residuals in log10 permeability | 121.169 | Review the existing-field capped/Huber/Student-t rerank, then choose the robust kernel, scale, and whether it becomes the default or only a sensitivity scenario; refresh readiness/field-selection audits and rerank again if the accepted formula or scale differs. | A written kernel formula, scale, outlier treatment, and rule for comparing historical row-Gaussian candidate objectives to the new policy. |
| `aggregate_by_model_support_cell` | `no` | collapse rows sharing one active model support cell before scoring | 1.767e-28 | Review the existing-field support-mean/support-median rerank, then choose mean, median, or another support aggregate; define whether observations at nearby depths but the same OGS support cell should be one datum; rerank again if the accepted grouping, statistic, or weights differ. | A written grouping key, aggregation statistic, group weight, and reporting rule for within-support observation ranges. |
| `gate_configured_scalar_outliers` | `no` | treat rows outside configured scalar tensor range separately from ordinary Gaussian rows | 245.675 | Decide whether out-of-range rows are source-interpretation issues, require wider tensor eigenvalue bounds, or require tensor-shape release; do not force them into the existing scalar-bounded family silently. | A written outlier disposition for each configured-scalar-range row and an explicit release decision if bounds or tensor shape change. |
| `new_parameterization_before_more_ogs` | `no` | do not spend more routine OGS on current smooth/local-basis family without a new field family | 269.818 | If the rowwise objective remains default, propose a genuinely new parameterization or support model before more OGS batches; otherwise use the existing-field rerank as the first screen and refresh it if the newly accepted likelihood policy differs from the diagnostic policies. | A next-run gate that names the accepted likelihood policy, the field family to be tested, and the materiality threshold for spending additional OGS runs. |

## Recommended Local Policy For Current Report State

Keep `keep_rowwise_gaussian_default` as the recorded active objective for reproducibility.
Report robust row likelihoods, support-cell aggregation, and scalar-range outlier handling as explicit
decision/scenario options, not as silent replacements for the active objective.

## Required Answer

Before more active-objective OGS spending, record one of the following:

- The rowwise Gaussian objective remains the default and the next run uses a genuinely new parameterization.
- A robust row likelihood becomes the default or an explicit scenario, with formula and scale.
- A support-cell aggregation policy becomes the default or an explicit scenario, with grouping and weights.
- Configured-scalar-range outliers are excluded, reinterpreted, or used to release bounds/tensor shape.

## Source Artifacts

- Policy audit: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/permeability_likelihood_policy_audit_summary.json`
- Policy comparison: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/permeability_likelihood_policy_audit.csv`
- Group summary: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/permeability_likelihood_policy_group_summary.csv`
- Existing-field rerank summary: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/permeability_likelihood_scenario_rerank_summary.json`
- Winner cross-stream audit summary: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/permeability_likelihood_winner_cross_stream_audit_summary.json`
- Decision CSV: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/permeability_likelihood_decision_request.csv`
