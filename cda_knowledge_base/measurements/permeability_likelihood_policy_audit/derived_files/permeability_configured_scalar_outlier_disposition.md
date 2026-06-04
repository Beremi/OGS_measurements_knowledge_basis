# Permeability Configured-Scalar Outlier Disposition

This artifact classifies the active direct-permeability rows that fall outside
the configured scalar tensor envelope. It is a local disposition record only:
it does not change the active objective, run OGS, or modify the frozen GESA model.

- Status: `permeability_configured_scalar_outlier_disposition_generated`
- Active outlier rows: 2
- Unique physical outlier groups: 1
- Max envelope excess: 0.107 log10 (factor 1.28)
- Max same-support observed range: 6.95 log10 (factor 8.89e+06)
- Bounds release recommended now: False
- Tensor-shape release recommended now: False

## Disposition

Record the two active scalar-envelope outlier rows as one duplicated high-permeability BCD-A32 support-cell value that is only slightly above the configured upper envelope, but embedded in a much larger same-support conflict with a low-permeability row. Keep the active rowwise Gaussian objective unchanged for reproducibility; do not widen bounds or release tensor shape on this evidence alone.

Before new OGS spending or final promotion, the modelling team still has to accept this local disposition or choose a robust/capped/support-aggregation/outlier policy explicitly.

## Row Table

| Observation | Source | Segment | Depth m | Cell | Observed log10 | Feasible max log10 | Excess log10 | Residual log10 | Support range log10 | Classification |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `perm_0005` | `2025-09-05_CD-A_Permeability.xlsx:2024_OT:9` | `BCD-A32` | 0.87 | `4648` | -12.1 | -12.2 | 0.1072 | -3.474 | 6.949 | `minor_upper_envelope_duplicate_inside_major_same_support_conflict` |
| `perm_0155` | `Permeability_CDA_all_2025.xlsx:2024:8` | `BCD-A32` | 0.87 | `4648` | -12.1 | -12.2 | 0.1072 | -3.474 | 6.949 | `minor_upper_envelope_duplicate_inside_major_same_support_conflict` |

## Interpretation

- The two rows are the same BCD-A32 0.87 m high-permeability value recorded in two source workbooks.
- The value is only about 0.107 log10 above the configured scalar upper envelope, but it shares model support cell 4648 with an active low-permeability row near 0.85 m.
- The same-support spread is about 6.949 log10, so the dominant problem is not this small envelope exceedance; it is incompatible row-level pulse-test values mapped to one OGS support cell.
- The local recommendation is therefore no immediate eigenvalue-bound widening or tensor-shape release from these rows alone. Treat them through an explicit likelihood/support decision before any new OGS spending.

## Source Artifacts

- `inversion_workflow/permeability_residual_conflict_audit.csv`
- `inversion_workflow/permeability_residual_support_cell_audit.csv`
- `inversion_workflow/processed_observations/permeability_measurement_semantics_audit.csv`
- `inversion_workflow/permeability_likelihood_policy_row_audit.csv`
- `inversion_workflow/permeability_likelihood_policy_audit_summary.json`
