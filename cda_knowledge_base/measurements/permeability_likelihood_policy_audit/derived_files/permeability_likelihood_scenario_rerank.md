# Permeability Likelihood Scenario Rerank

This audit reranks already materialized permeability-field VTUs under alternative direct-permeability likelihood semantics. It does not run OGS and does not change the active objective.

## Candidate Inventory

- Discovered candidate fields: 522
- Successfully evaluated/reread: 522
- Failed candidates: 0
- Cached row-evaluation CSVs used: 521
- Fresh mesh evaluations: 1
- Active direct-permeability rows per valid candidate: 75

The configured-scalar inside-only policy uses the current-field configured-scalar outlier labels from `permeability_residual_conflict_audit.csv`; it is a diagnostic mask, not a per-candidate tensor-bound recomputation.

## Policy Winners

The active row-Gaussian policy has 40 tied best materialized fields at objective-like value 269.818.

| Policy | Winner | Family | Objective-like value | Current accepted rank | Outside row-Gaussian best tie set |
| --- | --- | --- | ---: | ---: | --- |
| current_duplicate_weighted_gaussian | `broad_continuous_loop_001_001_length_0p015m` | broad_continuous_loop_001_001_length_0p015m | 269.818 | 1 | False |
| capped_gaussian_abs1_log10 | `local_anisotropy_sampler_plan/local_anis_residual_sign_l0p0015_s0p5_r2p5` | local_anisotropy_sampler_plan | 64.8123 | 183 | True |
| huber_delta_2sigma | `broad_continuous_loop_001_001_length_0p015m` | broad_continuous_loop_001_001_length_0p015m | 183.671 | 1 | False |
| student_t_nu4 | `broad_continuous_loop_001_001_length_0p015m` | broad_continuous_loop_001_001_length_0p015m | 121.169 | 1 | False |
| support_cell_weighted_mean_unit_gaussian | `current_permeability_field/current_best` | current_permeability_field | 1.073e-28 | 1 | False |
| support_cell_weighted_median_unit_gaussian | `local_anisotropy_sampler_plan/local_anis_perpendicular_all_l0p0015_s1_r12` | local_anisotropy_sampler_plan | 81.8284 | 228 | True |
| configured_scalar_inside_only_gaussian | `lower_support_continuous_candidate_plan/length_0p007m_shift_0p946` | lower_support_continuous_candidate_plan | 244.318 | 110 | True |

## Current Accepted Field

| Policy | Rank | Objective-like value |
| --- | ---: | ---: |
| current_duplicate_weighted_gaussian | 1 | 269.818 |
| capped_gaussian_abs1_log10 | 183 | 65.3119 |
| huber_delta_2sigma | 1 | 183.671 |
| student_t_nu4 | 1 | 121.169 |
| support_cell_weighted_mean_unit_gaussian | 1 | 1.073e-28 |
| support_cell_weighted_median_unit_gaussian | 228 | 134.728 |
| configured_scalar_inside_only_gaussian | 110 | 245.675 |

## Interpretation

- The active row-Gaussian policy has 40 tied best materialized fields; `broad_continuous_loop_001_001_length_0p015m` is the first representative after candidate-id sorting.
- These diagnostic policies select a winner outside the active row-Gaussian best tie set: `capped_gaussian_abs1_log10`, `support_cell_weighted_median_unit_gaussian`, `configured_scalar_inside_only_gaussian`.
- This is only a reranking of existing fields. A policy change still needs a written likelihood decision before it becomes the default fitting objective.

## Top Row-Gaussian Candidates

| Rank | Candidate | Family | Objective | RMSE log10 | Mesh |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | `broad_continuous_loop_001_001_length_0p015m` | broad_continuous_loop_001_001_length_0p015m | 269.818 | 1.61072 | `inversion_workflow/runs/broad_continuous_loop_001_001_length_0p015m/bulk_w_projections.vtu` |
| 1 | `broad_continuous_loop_001_003_length_0p010m` | broad_continuous_loop_001_003_length_0p010m | 269.818 | 1.61072 | `inversion_workflow/runs/broad_continuous_loop_001_003_length_0p010m/bulk_w_projections.vtu` |
| 1 | `candidate_direct_fit_driver` | candidate_direct_fit_driver | 269.818 | 1.61072 | `inversion_workflow/runs/candidate_direct_fit_driver/bulk_w_projections.vtu` |
| 1 | `continuous_bayesian_candidate_plan/length_0p007m` | continuous_bayesian_candidate_plan | 269.818 | 1.61072 | `inversion_workflow/runs/continuous_bayesian_candidate_plan/length_0p007m/bulk_w_projections.vtu` |
| 1 | `continuous_bayesian_candidate_plan/length_0p010m` | continuous_bayesian_candidate_plan | 269.818 | 1.61072 | `inversion_workflow/runs/continuous_bayesian_candidate_plan/length_0p010m/bulk_w_projections.vtu` |
| 1 | `continuous_bayesian_candidate_plan/length_0p013m` | continuous_bayesian_candidate_plan | 269.818 | 1.61072 | `inversion_workflow/runs/continuous_bayesian_candidate_plan/length_0p013m/bulk_w_projections.vtu` |
| 1 | `continuous_bayesian_candidate_plan/length_0p015m` | continuous_bayesian_candidate_plan | 269.818 | 1.61072 | `inversion_workflow/runs/continuous_bayesian_candidate_plan/length_0p015m/bulk_w_projections.vtu` |
| 1 | `continuous_bayesian_candidate_plan/length_0p018m` | continuous_bayesian_candidate_plan | 269.818 | 1.61072 | `inversion_workflow/runs/continuous_bayesian_candidate_plan/length_0p018m/bulk_w_projections.vtu` |
| 1 | `continuous_proposed_002_length_0p007m` | continuous_proposed_002_length_0p007m | 269.818 | 1.61072 | `inversion_workflow/runs/continuous_proposed_002_length_0p007m/bulk_w_projections.vtu` |
| 1 | `cross_stream_hybrid_field_plan/cross_hybrid_mean_rank_all_streams_plus2_a0p25` | cross_stream_hybrid_field_plan | 269.818 | 1.61072 | `inversion_workflow/runs/cross_stream_hybrid_field_plan/cross_hybrid_mean_rank_all_streams_plus2_a0p25/bulk_w_projections.vtu` |

## Output Files

- Full ranked table: `inversion_workflow/permeability_likelihood_scenario_rerank.csv`
- Policy winner table: `inversion_workflow/permeability_likelihood_scenario_rerank_policy_winners.csv`
- Summary JSON: `inversion_workflow/permeability_likelihood_scenario_rerank_summary.json`
