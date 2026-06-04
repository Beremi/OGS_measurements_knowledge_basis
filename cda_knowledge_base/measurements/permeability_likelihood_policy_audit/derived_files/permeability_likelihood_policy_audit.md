# Permeability Likelihood Policy Audit

This audit compares objective semantics for the existing direct pulse-test residuals.
It does not change the active objective, alter any permeability field, or run OGS.

## Current Active Policy

- Active direct rows: 75
- Effective duplicate-weighted objective weight: 52
- Current Gaussian objective: 269.818057
- Weighted RMSE: 1.610715 log10(k)
- Rows with |residual| >= 1 log10: 48
- Rows with |residual| >= 2 log10: 21
- Rows outside configured scalar range: 2
- Top 5 row-loss share: 0.311
- Top 10 row-loss share: 0.494

## Policy Comparison

| Policy | Type | Count | Effective weight | Objective-like value | RMSE | Rows/groups >=1 | Interpretation |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `current_duplicate_weighted_gaussian` | active_current_policy | 75 | 52.000 | 269.818 | 1.611 | 48 | Retained active semantics: duplicate-weighted Gaussian rows with sigma=0.5 log10. |
| `capped_gaussian_abs1_log10` | robust_row_policy_diagnostic | 75 | 52.000 | 65.3119 | 0.792 | 48 | Diagnostic only: caps each row at one log10 unit so large conflicts cannot dominate the objective. |
| `huber_delta_2sigma` | robust_row_policy_diagnostic | 75 | 52.000 | 183.671 | 1.611 | 48 | Diagnostic only: Huber transition at 2.0 sigma, equal to one log10 unit here. |
| `student_t_nu4` | robust_row_policy_diagnostic | 75 | 52.000 | 121.169 | 1.611 | 48 | Diagnostic only: Student-t heavy-tail kernel with nu=4. |
| `support_cell_weighted_mean_unit_gaussian` | support_aggregation_diagnostic | 30 | 30.000 | 1.76705e-28 | 0.000 | 0 | Diagnostic only: collapses rows sharing one model support cell to their objective-weighted mean. A near-zero value means the current field fits support-cell averages while rowwise conflicts remain. |
| `support_cell_weighted_median_unit_gaussian` | support_aggregation_diagnostic | 30 | 30.000 | 134.728 | 1.498 | 16 | Diagnostic only: support-cell median aggregation is less forgiving when repeated rows favor one extreme. |
| `configured_scalar_inside_only_gaussian` | bounds_gate_diagnostic | 73 | 51.000 | 245.675 | 1.552 | 46 | Diagnostic only: removes rows outside the configured scalar tensor range instead of fitting them as ordinary Gaussian rows. |

## Support-Cell Conflict Summary

- Support-cell groups: 30
- Repeated-row support-cell groups: 24
- Support-cell groups with observed range >= 1 log10: 16
- Current row Gaussian loss in top two support cells: 0.356

| Cell | Rows | Segment | Depth range [m] | Observed range | Row loss | Mean-residual loss | Median-residual loss | Class |
| ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| 4648 | 3 | `BCD-A32` | 0.85-0.87 | 6.949 | 48.286 | 0 | 24.143 | configured_scalar_range_decision_required |
| 8057 | 3 | `BCD-A33` | 0.55-0.59 | 6.903 | 47.653 | 0 | 23.826 | within_support_conflict_group |
| 7188 | 3 | `BCD-A32` | 0.95-1.01 | 4.574 | 20.922 | 0 | 10.461 | within_support_conflict_group |
| 5040 | 3 | `BCD-A32` | 1.15-1.15 | 4.301 | 18.499 | 2.52e-29 | 9.249 | within_support_conflict_group |
| 5896 | 3 | `BCD-A32` | 1.25-1.29 | 4.301 | 18.499 | 0 | 9.249 | within_support_conflict_group |
| 4317 | 3 | `BCD-A33` | 1.70-1.70 | 4.097 | 16.785 | 2.52e-29 | 8.392 | within_support_conflict_group |
| 6191 | 3 | `BCD-A32` | 0.65-0.73 | 4.000 | 16.000 | 0 | 8.000 | within_support_conflict_group |
| 5030 | 3 | `BCD-A33` | 1.15-1.15 | 3.891 | 15.139 | 0 | 7.569 | within_support_conflict_group |
| 8051 | 3 | `BCD-A32` | 0.25-0.31 | 3.824 | 14.622 | 2.52e-29 | 7.311 | within_support_conflict_group |
| 8371 | 3 | `BCD-A32` | 0.45-0.45 | 3.398 | 11.546 | 0 | 5.773 | within_support_conflict_group |
| 5749 | 3 | `BCD-A33` | 1.25-1.29 | 3.176 | 10.088 | 2.52e-29 | 5.044 | within_support_conflict_group |
| 3600 | 3 | `BCD-A33` | 0.45-0.45 | 3.000 | 9.000 | 0 | 4.500 | within_support_conflict_group |

## Dominant Rows

| Observation | Segment | Depth [m] | Cell | Observed | Predicted | Residual | Weight | Row loss | Class |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `perm_0169` | `BCD-A32` | 0.85 | 4648 | -19.046 | -15.571 | +3.474 | 1.000 | 24.143 | large_residual_heavy_tail_or_support_review |
| `perm_0195` | `BCD-A33` | 0.59 | 8057 | -21.000 | -17.548 | +3.452 | 1.000 | 23.826 | large_residual_heavy_tail_or_support_review |
| `perm_0005` | `BCD-A32` | 0.87 | 4648 | -12.097 | -15.571 | -3.474 | 0.500 | 12.072 | configured_scalar_range_decision_required |
| `perm_0155` | `BCD-A32` | 0.87 | 4648 | -12.097 | -15.571 | -3.474 | 0.500 | 12.072 | configured_scalar_range_decision_required |
| `perm_0015` | `BCD-A33` | 0.55 | 8057 | -14.097 | -17.548 | -3.452 | 0.500 | 11.913 | large_residual_heavy_tail_or_support_review |
| `perm_0181` | `BCD-A33` | 0.55 | 8057 | -14.097 | -17.548 | -3.452 | 0.500 | 11.913 | large_residual_heavy_tail_or_support_review |
| `perm_0170` | `BCD-A32` | 0.95 | 7188 | -19.097 | -16.810 | +2.287 | 1.000 | 10.461 | large_residual_heavy_tail_or_support_review |
| `perm_0172` | `BCD-A32` | 1.15 | 5040 | -19.398 | -17.247 | +2.151 | 1.000 | 9.249 | large_residual_heavy_tail_or_support_review |
| `perm_0173` | `BCD-A32` | 1.25 | 5896 | -20.699 | -18.548 | +2.151 | 1.000 | 9.249 | large_residual_heavy_tail_or_support_review |
| `perm_0201` | `BCD-A33` | 1.70 | 4317 | -20.398 | -18.349 | +2.048 | 1.000 | 8.392 | large_residual_heavy_tail_or_support_review |
| `perm_0167` | `BCD-A32` | 0.65 | 6191 | -19.301 | -17.301 | +2.000 | 1.000 | 8.000 | large_residual_heavy_tail_or_support_review |
| `perm_0199` | `BCD-A33` | 1.15 | 5030 | -19.046 | -17.100 | +1.945 | 1.000 | 7.569 | moderate_residual_uncertainty_review |

## Recommendation

Keep the current Gaussian row policy as the recorded active objective for reproducibility, but do not treat more spatial sampling as the next default step. First decide whether the direct permeability likelihood should use robust tails, support-cell aggregation, or explicit exclusion/reinterpretation of configured-scalar-range outliers. The support-cell weighted-mean diagnostic changes the objective-like value from 269.818 to 1.76705e-28, which shows that the current field is fitting mapped support averages while row-level pulse-test conflicts dominate the active Gaussian loss.

## Outputs

- Policy comparison: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/permeability_likelihood_policy_audit.csv`
- Row audit: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/permeability_likelihood_policy_row_audit.csv`
- Support-cell group summary: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/permeability_likelihood_policy_group_summary.csv`
- Machine-readable summary: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/permeability_likelihood_policy_audit_summary.json`
