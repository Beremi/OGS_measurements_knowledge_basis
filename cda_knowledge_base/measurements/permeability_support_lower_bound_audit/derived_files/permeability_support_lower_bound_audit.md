# Permeability Support Lower-Bound Audit

This audit quantifies the part of the active direct pulse-test objective that cannot be reduced by
another permeability field as long as rows sharing the same current OGS support cell are fitted by
one effective support value. It does not change the active objective and does not run OGS.

## Summary

- Status: `permeability_support_lower_bound_audit_generated`
- Active direct rows: 75
- Support groups: 30
- Repeated support groups: 24
- Support groups with observed range >= 1 log10: 16
- Support groups with observed range >= 2 log10: 16
- Current row-Gaussian objective: 269.818057
- Single-support lower-bound objective: 269.818057
- Same-support reducible objective gap: 0
- Same-support reducible fraction: 0
- Current field at lower bound: True
- Top two support-group loss share: 0.356
- Top five support-group loss share: 0.570

## Dominant Support Groups

| Cell | Rows | Segment | Depth range [m] | Observed range | Current loss | Lower-bound loss | Reducible gap | Class |
| ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| 4648 | 3 | `BCD-A32` | 0.85-0.87 | 6.949 | 48.286 | 48.286 | 0 | irreducible_large_same_support_conflict |
| 8057 | 3 | `BCD-A33` | 0.55-0.59 | 6.903 | 47.653 | 47.653 | 0 | irreducible_large_same_support_conflict |
| 7188 | 3 | `BCD-A32` | 0.95-1.01 | 4.574 | 20.922 | 20.922 | 0 | irreducible_large_same_support_conflict |
| 5040 | 3 | `BCD-A32` | 1.15-1.15 | 4.301 | 18.499 | 18.499 | 0 | irreducible_large_same_support_conflict |
| 5896 | 3 | `BCD-A32` | 1.25-1.29 | 4.301 | 18.499 | 18.499 | 0 | irreducible_large_same_support_conflict |
| 4317 | 3 | `BCD-A33` | 1.70-1.70 | 4.097 | 16.785 | 16.785 | 0 | irreducible_large_same_support_conflict |
| 6191 | 3 | `BCD-A32` | 0.65-0.73 | 4.000 | 16.000 | 16.000 | 0 | irreducible_large_same_support_conflict |
| 5030 | 3 | `BCD-A33` | 1.15-1.15 | 3.891 | 15.139 | 15.139 | 0 | irreducible_large_same_support_conflict |
| 8051 | 3 | `BCD-A32` | 0.25-0.31 | 3.824 | 14.622 | 14.622 | 0 | irreducible_large_same_support_conflict |
| 8371 | 3 | `BCD-A32` | 0.45-0.45 | 3.398 | 11.546 | 11.546 | 0 | irreducible_large_same_support_conflict |
| 5749 | 3 | `BCD-A33` | 1.25-1.29 | 3.176 | 10.088 | 10.088 | 0 | irreducible_large_same_support_conflict |
| 3600 | 3 | `BCD-A33` | 0.45-0.45 | 3.000 | 9.000 | 9.000 | 0 | irreducible_large_same_support_conflict |
| 4650 | 3 | `BCD-A33` | 0.95-1.01 | 2.778 | 7.718 | 7.718 | -8.88e-16 | irreducible_large_same_support_conflict |
| 4096 | 3 | `BCD-A33` | 0.25-0.31 | 2.398 | 5.750 | 5.750 | 0 | irreducible_large_same_support_conflict |
| 4649 | 3 | `BCD-A33` | 0.85-0.87 | 2.000 | 4.000 | 4.000 | 0 | irreducible_large_same_support_conflict |

## Dominant Rows

| Observation | Cell | Segment | Depth [m] | Observed | Current pred. | Lower-bound pred. | Current loss | Lower-bound loss |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `perm_0169` | 4648 | `BCD-A32` | 0.85 | -19.046 | -15.571 | -15.571 | 24.143 | 24.143 |
| `perm_0195` | 8057 | `BCD-A33` | 0.59 | -21.000 | -17.548 | -17.548 | 23.826 | 23.826 |
| `perm_0005` | 4648 | `BCD-A32` | 0.87 | -12.097 | -15.571 | -15.571 | 12.072 | 12.072 |
| `perm_0155` | 4648 | `BCD-A32` | 0.87 | -12.097 | -15.571 | -15.571 | 12.072 | 12.072 |
| `perm_0015` | 8057 | `BCD-A33` | 0.55 | -14.097 | -17.548 | -17.548 | 11.913 | 11.913 |
| `perm_0181` | 8057 | `BCD-A33` | 0.55 | -14.097 | -17.548 | -17.548 | 11.913 | 11.913 |
| `perm_0170` | 7188 | `BCD-A32` | 0.95 | -19.097 | -16.810 | -16.810 | 10.461 | 10.461 |
| `perm_0172` | 5040 | `BCD-A32` | 1.15 | -19.398 | -17.247 | -17.247 | 9.249 | 9.249 |
| `perm_0173` | 5896 | `BCD-A32` | 1.25 | -20.699 | -18.548 | -18.548 | 9.249 | 9.249 |
| `perm_0201` | 4317 | `BCD-A33` | 1.70 | -20.398 | -18.349 | -18.349 | 8.392 | 8.392 |
| `perm_0167` | 6191 | `BCD-A32` | 0.65 | -19.301 | -17.301 | -17.301 | 8.000 | 8.000 |
| `perm_0199` | 5030 | `BCD-A33` | 1.15 | -19.046 | -17.100 | -17.100 | 7.569 | 7.569 |
| `perm_0163` | 8051 | `BCD-A32` | 0.25 | -19.523 | -17.611 | -17.611 | 7.311 | 7.311 |
| `perm_0165` | 8371 | `BCD-A32` | 0.45 | -19.097 | -17.398 | -17.398 | 5.773 | 5.773 |
| `perm_0006` | 7188 | `BCD-A32` | 1.01 | -14.523 | -16.810 | -16.810 | 5.230 | 5.230 |

## Interpretation

The current accepted permeability field is already at the duplicate-weighted row-Gaussian lower bound for the current one-value-per-support-cell mapping. The direct permeability mismatch is therefore irreducible by additional same-support spatial sampling: the dominant loss comes from mutually inconsistent pulse-test values assigned to the same model support cells, plus the separate configured scalar-range cases. The next defensible move is a support/likelihood/measurement-interpretation or bounds/tensor-shape decision, not another routine OGS batch in the same parameter family.

## Outputs

- Group audit: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/permeability_support_lower_bound_audit.csv`
- Row audit: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/permeability_support_lower_bound_row_audit.csv`
- Machine-readable summary: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/permeability_support_lower_bound_audit_summary.json`
