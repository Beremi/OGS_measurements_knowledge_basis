# Conditional Field Candidate Package

This package copies the unique scenario-winning permeability fields into one
inspection folder. It does not select a final field; it makes the conditional
field alternatives concrete and comparable.

- Status: `conditional_field_candidate_package_generated`
- Scenario count: 8
- Candidate count: 5
- Current packaged field wins: 1 scenarios
- Selection stability: `unstable_across_defined_scenarios`
- Diagnostic metric evidence rows: 25
- Missing diagnostic metric evidence rows: 0

## Candidates

| Candidate | Scenarios | Active rank | NMR rank | ERT rank | Taupe rank | Mean rank | Mesh |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `broad_continuous_001_003_length_0p021m` | S02_promoted_nmr_trend_anomaly | 56.0 | 1.0 | 60.0 | 62.0 | 36.0 | `inversion_workflow/conditional_field_candidates/broad_continuous_001_003_length_0p021m/bulk_w_projections.vtu` |
| `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | S01_current_active_raw_nmr | 1.0 | 14.0 | 8.0 | 29.0 | 13.2 | `inversion_workflow/conditional_field_candidates/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/bulk_w_projections.vtu` |
| `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | S03_active_plus_ert_screen, S08_rank_consensus_all_streams | 2.0 | 13.0 | 6.0 | 18.0 | 10.4 | `inversion_workflow/conditional_field_candidates/local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000/bulk_w_projections.vtu` |
| `local_bracketed_003_length_0p031m` | S04_active_plus_taupe_screen, S07_diagnostics_only_nmr_ert_taupe | 62.0 | 41.0 | 63.0 | 3.0 | 42.0 | `inversion_workflow/conditional_field_candidates/local_bracketed_003_length_0p031m/bulk_w_projections.vtu` |
| `production_sampler_round3_002_length_0p028m_shift_1p050` | S05_active_plus_ert_taupe_screen, S06_active_plus_promoted_nmr_ert_taupe | 53.0 | 48.0 | 49.0 | 4.0 | 40.4 | `inversion_workflow/conditional_field_candidates/production_sampler_round3_002_length_0p028m_shift_1p050/bulk_w_projections.vtu` |

## Interpretation

- Each package subdirectory is a copied scenario winner with mesh, objective summaries, and field statistics.
- The packages are conditional alternatives, not a final all-measurement inversion field.
- Selection remains unstable until NMR promotion and ERT/Taupe/RH/other-HM gates are resolved or explicitly excluded.

## Files

- Inventory: `inversion_workflow/conditional_field_candidates/conditional_field_candidate_inventory.csv`
- Metric evidence: `inversion_workflow/conditional_field_candidates/conditional_field_candidate_metric_evidence.csv`
- Summary: `inversion_workflow/conditional_field_candidates/CONDITIONAL_FIELD_CANDIDATES_SUMMARY.json`
- Candidate `broad_continuous_001_003_length_0p021m`: `inversion_workflow/conditional_field_candidates/broad_continuous_001_003_length_0p021m` (metric evidence: `inversion_workflow/conditional_field_candidates/broad_continuous_001_003_length_0p021m/diagnostic_metric_evidence.csv`)
- Candidate `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000`: `inversion_workflow/conditional_field_candidates/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` (metric evidence: `inversion_workflow/conditional_field_candidates/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/diagnostic_metric_evidence.csv`)
- Candidate `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000`: `inversion_workflow/conditional_field_candidates/local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` (metric evidence: `inversion_workflow/conditional_field_candidates/local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000/diagnostic_metric_evidence.csv`)
- Candidate `local_bracketed_003_length_0p031m`: `inversion_workflow/conditional_field_candidates/local_bracketed_003_length_0p031m` (metric evidence: `inversion_workflow/conditional_field_candidates/local_bracketed_003_length_0p031m/diagnostic_metric_evidence.csv`)
- Candidate `production_sampler_round3_002_length_0p028m_shift_1p050`: `inversion_workflow/conditional_field_candidates/production_sampler_round3_002_length_0p028m_shift_1p050` (metric evidence: `inversion_workflow/conditional_field_candidates/production_sampler_round3_002_length_0p028m_shift_1p050/diagnostic_metric_evidence.csv`)
