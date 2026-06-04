# Conditional Field Difference Audit

This audit compares every conditional scenario-winning permeability field to
the current active-objective field using the geometric-mean log10
permeability of the `k_i_rd` tensor in each mesh cell.

- Status: `conditional_field_difference_audit_generated`
- Reference run: `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000`
- Compared candidate fields: 4
- Cell count per field: 10239

## Candidate Differences

| Candidate | Scenarios | Mean abs delta log10 k | RMS delta log10 k | Max abs delta | Cells >0.05 log10 | Cells >0.10 log10 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `local_bracketed_003_length_0p031m` | S04_active_plus_taupe_screen;S07_diagnostics_only_nmr_ert_taupe | 0.0377448 | 0.139681 | 5.80413 | 241 | 233 |
| `production_sampler_round3_002_length_0p028m_shift_1p050` | S05_active_plus_ert_taupe_screen;S06_active_plus_promoted_nmr_ert_taupe | 0.035565 | 0.142017 | 6.09433 | 224 | 208 |
| `broad_continuous_001_003_length_0p021m` | S02_promoted_nmr_trend_anomaly | 0.0184723 | 0.0804252 | 5.80413 | 112 | 111 |
| `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | S03_active_plus_ert_screen;S08_rank_consensus_all_streams | 8.50527e-06 | 0.000105325 | 0.0170941 | 0 | 0 |

## Interpretation

- All comparisons are against the current active-objective field, not against the frozen source model.
- Small local-basis differences indicate nearly identical permeability tensors with different diagnostic ranks.
- Large smooth-field differences identify gate-dependent alternatives that would need explicit acceptance before promotion.

## Files

- Candidate summary CSV: `inversion_workflow/conditional_field_candidates/conditional_field_difference_summary.csv`
- Top changed cells CSV: `inversion_workflow/conditional_field_candidates/conditional_field_difference_top_cells.csv`
- JSON summary: `inversion_workflow/conditional_field_candidates/CONDITIONAL_FIELD_DIFFERENCE_AUDIT.json`
