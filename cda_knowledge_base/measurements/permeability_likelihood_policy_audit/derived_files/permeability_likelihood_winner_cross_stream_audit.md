# Permeability Likelihood Winner Cross-Stream Audit

This audit joins the direct-permeability likelihood-policy winners to the executed-run cross-stream scorecard where possible. It does not run OGS and does not change the active likelihood policy.

## Summary

- Policy winner rows: 7
- Unique winner fields: 5
- Winner rows with cross-stream scorecard evidence: 4
- Unique winner fields with cross-stream scorecard evidence: 2
- Direct-only winner rows without OGS cross-stream evidence: 3
- Diagnostic winners outside the row-Gaussian best tie set and lacking cross-stream evidence: 3
- Current accepted source run: `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000`

## Policy Winner Evidence

| Policy | Winner | Cross-stream evidence | Active rank | Mean rank | ERT rank | Taupe rank | NMR trend rank | Disposition |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| current_duplicate_weighted_gaussian | `broad_continuous_loop_001_001_length_0p015m` | `yes` | 45 | 30.4 | 48 | 51 | 4 | executed_direct_tie_representative_not_current_active_preferred |
| capped_gaussian_abs1_log10 | `local_anisotropy_sampler_plan/local_anis_residual_sign_l0p0015_s0p5_r2p5` | `no` | n/a | n/a | n/a | n/a | n/a | direct_only_winner_requires_ogs_before_stream_promotion |
| huber_delta_2sigma | `broad_continuous_loop_001_001_length_0p015m` | `yes` | 45 | 30.4 | 48 | 51 | 4 | executed_direct_tie_representative_not_current_active_preferred |
| student_t_nu4 | `broad_continuous_loop_001_001_length_0p015m` | `yes` | 45 | 30.4 | 48 | 51 | 4 | executed_direct_tie_representative_not_current_active_preferred |
| support_cell_weighted_mean_unit_gaussian | `current_permeability_field/current_best` | `yes` | 1 | 13.2 | 8 | 29 | 14 | current_accepted_field_with_cross_stream_evidence |
| support_cell_weighted_median_unit_gaussian | `local_anisotropy_sampler_plan/local_anis_perpendicular_all_l0p0015_s1_r12` | `no` | n/a | n/a | n/a | n/a | n/a | direct_only_winner_requires_ogs_before_stream_promotion |
| configured_scalar_inside_only_gaussian | `lower_support_continuous_candidate_plan/length_0p007m_shift_0p946` | `no` | n/a | n/a | n/a | n/a | n/a | direct_only_winner_requires_ogs_before_stream_promotion |

## Interpretation

- The direct likelihood rerank scored 522 materialized fields, but only 2 unique policy-winner fields currently have executed-run cross-stream scorecard evidence.
- The active row-Gaussian representative selected by candidate-id sorting has active-objective rank 45 and mean all-stream rank 30.4, while the current accepted field has active-objective rank 1 and mean all-stream rank 13.2.
- The non-default diagnostic winners outside the active row-Gaussian best tie set are direct-only materialized fields in this audit. They require OGS execution plus state/ERT/Taupe/NMR diagnostics before any all-measurement promotion.
- The current report should therefore keep the rowwise Gaussian default until the likelihood decision is explicit, and should not replace the current accepted field with a direct-only diagnostic winner.

## Output Files

- Audit CSV: `inversion_workflow/permeability_likelihood_winner_cross_stream_audit.csv`
- Summary JSON: `inversion_workflow/permeability_likelihood_winner_cross_stream_audit_summary.json`
- Markdown: `inversion_workflow/permeability_likelihood_winner_cross_stream_audit.md`
