# Cross-Stream Candidate Scorecard

This scorecard joins the active permeability+NMR objective with the current diagnostic streams.
It does not change candidate objectives or promote gated streams into the likelihood.

## Status

- Status: `cross_stream_scorecard_generated_active_objective_unchanged`
- Joined executed runs: 66
- Source rows: NMR=66, ERT=66, Taupe=74
- Pareto candidates across active objective plus diagnostics: 23
- Pareto candidates across diagnostics only: 16
- Candidates in the top 10 of every stream: 0
- Activation gate: Diagnostic only: the scorecard does not change the active objective. It shows how executed candidate fields rank under NMR offset-robust alternatives, provisional ERT log-resistivity residuals, and Taupe/TDR trend residuals so field selection is not based on the active permeability+raw-NMR objective alone.

## Stream Winners

| Stream | Run | Active rank | NMR-bias rank | NMR-anomaly rank | ERT rank | Taupe rank | Mean rank |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Active objective | `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | 1.00 | 14.00 | 14.00 | 8.00 | 29.00 | 13.20 |
| NMR per-label bias | `broad_continuous_001_003_length_0p021m` | 56.00 | 1.00 | 1.00 | 60.00 | 62.00 | 36.00 |
| NMR within-label anomaly | `broad_continuous_001_003_length_0p021m` | 56.00 | 1.00 | 1.00 | 60.00 | 62.00 | 36.00 |
| ERT log10 MAE | `broad_continuous_001_001_length_0p023m_shift_1p004` | 38.00 | 25.00 | 25.00 | 1.00 | 10.00 | 19.80 |
| Taupe trend MAE | `adaptive_combined_001_length_0p050m` | 63.00 | 62.00 | 62.00 | 65.00 | 1.00 | 50.60 |
| Best mean rank | `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | 2.00 | 13.00 | 13.00 | 6.00 | 18.00 | 10.40 |
| Best diagnostic mean rank | `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | 2.00 | 13.00 | 13.00 | 6.00 | 18.00 | 10.40 |
| Best worst rank | `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | 2.00 | 13.00 | 13.00 | 6.00 | 18.00 | 10.40 |
| Best normalized loss | `production_sampler_round3_002_length_0p028m_shift_1p050` | 53.00 | 48.00 | 48.00 | 49.00 | 4.00 | 40.40 |

## Top By Mean Rank Across All Streams

| Run | Kind | Active obj | NMR bias obj | ERT MAE | Taupe MAE | Active rank | Bias rank | ERT rank | Taupe rank | Mean rank | Worst rank | Pareto |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | local_basis | 3156.354266 | 505.637437 | 0.254179 | 1.863203 | 2.0000 | 13.0000 | 6.0000 | 18.0000 | 10.4000 | 18.0000 | yes |
| `production_sampler_round4_002_basis_009_det_l_0p0025_s_1p000` | production_sampler_round | 3156.361470 | 505.637404 | 0.254180 | 1.863211 | 12.0000 | 8.0000 | 14.0000 | 24.0000 | 13.2000 | 24.0000 | yes |
| `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | local_basis | 3156.353067 | 505.637442 | 0.254180 | 1.863211 | 1.0000 | 14.0000 | 8.0000 | 29.0000 | 13.2000 | 29.0000 | yes |
| `production_sampler_round2_003_basis_013_det_l_0p0035_s_0p750` | production_sampler_round | 3156.361079 | 505.638503 | 0.254180 | 1.863204 | 6.0000 | 15.0000 | 12.0000 | 20.0000 | 13.6000 | 20.0000 | no |
| `production_sampler_round2_004_basis_018_det_l_0p0050_s_0p750` | production_sampler_round | 3156.361079 | 505.638503 | 0.254180 | 1.863204 | 4.0000 | 17.0000 | 9.0000 | 21.0000 | 13.6000 | 21.0000 | no |
| `local_basis_sampler_001_basis_004_det_l_0p0015_s_1p000` | local_basis | 3156.361470 | 505.637404 | 0.254180 | 1.863211 | 10.0000 | 9.0000 | 16.0000 | 25.0000 | 13.8000 | 25.0000 | yes |
| `production_sampler_round2_002_basis_008_det_l_0p0025_s_0p750` | production_sampler_round | 3156.361079 | 505.638503 | 0.254180 | 1.863204 | 5.0000 | 16.0000 | 11.0000 | 22.0000 | 14.0000 | 22.0000 | no |
| `production_sampler_round3_005_basis_019_det_l_0p0050_s_1p000` | production_sampler_round | 3156.361470 | 505.637404 | 0.254180 | 1.863211 | 9.0000 | 10.0000 | 15.0000 | 26.0000 | 14.0000 | 26.0000 | yes |
| `production_sampler_round2_005_basis_023_det_l_0p0075_s_0p750` | production_sampler_round | 3156.354758 | 505.638532 | 0.254179 | 1.863204 | 3.0000 | 19.0000 | 7.0000 | 23.0000 | 14.2000 | 23.0000 | no |
| `production_sampler_round3_006_basis_014_det_l_0p0035_s_1p000` | production_sampler_round | 3156.361470 | 505.637404 | 0.254180 | 1.863211 | 8.0000 | 11.0000 | 13.0000 | 28.0000 | 14.2000 | 28.0000 | yes |
| `production_sampler_round2_001_basis_003_det_l_0p0015_s_0p750` | production_sampler_round | 3156.361079 | 505.638503 | 0.254180 | 1.863204 | 7.0000 | 18.0000 | 10.0000 | 19.0000 | 14.4000 | 19.0000 | no |
| `lower_support_loop_001_001_length_0p003m_shift_1p006` | lower_support | 3156.373009 | 505.654876 | 0.254179 | 1.863182 | 13.0000 | 22.0000 | 5.0000 | 17.0000 | 15.8000 | 22.0000 | yes |
| `direct_fit_observation_run` | direct_reference | 3156.361470 | 505.637404 | 0.254180 | 1.863211 | 11.0000 | 12.0000 | 17.0000 | 27.0000 | 15.8000 | 27.0000 | no |
| `lower_support_loop_001_003_length_0p004m_shift_1p014` | lower_support | 3156.443974 | 505.733724 | 0.254177 | 1.863144 | 17.0000 | 28.0000 | 4.0000 | 16.0000 | 18.6000 | 28.0000 | yes |
| `lower_support_loop_002_002_length_0p004m_shift_1p020` | lower_support | 3156.534153 | 505.829476 | 0.254176 | 1.863117 | 20.0000 | 30.0000 | 3.0000 | 15.0000 | 19.6000 | 30.0000 | yes |

## Pareto Candidates Across All Streams

| Run | Kind | Active rank | NMR-bias rank | NMR-anomaly rank | ERT rank | Taupe rank | Mean rank | Worst rank |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | local_basis | 2.0000 | 13.0000 | 13.0000 | 6.0000 | 18.0000 | 10.4000 | 18.0000 |
| `production_sampler_round4_002_basis_009_det_l_0p0025_s_1p000` | production_sampler_round | 12.0000 | 8.0000 | 8.0000 | 14.0000 | 24.0000 | 13.2000 | 24.0000 |
| `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | local_basis | 1.0000 | 14.0000 | 14.0000 | 8.0000 | 29.0000 | 13.2000 | 29.0000 |
| `local_basis_sampler_001_basis_004_det_l_0p0015_s_1p000` | local_basis | 10.0000 | 9.0000 | 9.0000 | 16.0000 | 25.0000 | 13.8000 | 25.0000 |
| `production_sampler_round3_005_basis_019_det_l_0p0050_s_1p000` | production_sampler_round | 9.0000 | 10.0000 | 10.0000 | 15.0000 | 26.0000 | 14.0000 | 26.0000 |
| `production_sampler_round3_006_basis_014_det_l_0p0035_s_1p000` | production_sampler_round | 8.0000 | 11.0000 | 11.0000 | 13.0000 | 28.0000 | 14.2000 | 28.0000 |
| `lower_support_loop_001_001_length_0p003m_shift_1p006` | lower_support | 13.0000 | 22.0000 | 22.0000 | 5.0000 | 17.0000 | 15.8000 | 22.0000 |
| `lower_support_loop_001_003_length_0p004m_shift_1p014` | lower_support | 17.0000 | 28.0000 | 28.0000 | 4.0000 | 16.0000 | 18.6000 | 28.0000 |
| `lower_support_loop_002_002_length_0p004m_shift_1p020` | lower_support | 20.0000 | 30.0000 | 30.0000 | 3.0000 | 15.0000 | 19.6000 | 30.0000 |
| `broad_continuous_001_001_length_0p023m_shift_1p004` | broad_continuous | 38.0000 | 25.0000 | 25.0000 | 1.0000 | 10.0000 | 19.8000 | 38.0000 |
| `continuous_proposed_002_length_0p007m` | continuous_proposed | 33.0000 | 6.0000 | 6.0000 | 34.0000 | 30.0000 | 21.8000 | 34.0000 |
| `production_sampler_round5_005_length_0p004m_shift_1p031` | production_sampler_round | 24.0000 | 37.0000 | 37.0000 | 2.0000 | 14.0000 | 22.8000 | 37.0000 |
| `broad_continuous_loop_001_003_length_0p010m` | broad_continuous | 32.0000 | 7.0000 | 7.0000 | 41.0000 | 57.0000 | 28.8000 | 57.0000 |
| `local_refined_001_length_0p013m` | local_smooth | 40.0000 | 3.0000 | 3.0000 | 46.0000 | 56.0000 | 29.6000 | 56.0000 |
| `broad_continuous_loop_001_001_length_0p015m` | broad_continuous | 45.0000 | 4.0000 | 4.0000 | 48.0000 | 51.0000 | 30.4000 | 51.0000 |
| `regularized_ogs_candidate_001_length_0p025m` | regularized_ogs | 49.0000 | 27.0000 | 27.0000 | 58.0000 | 9.0000 | 34.0000 | 58.0000 |
| `local_refined_002_length_0p019m` | local_smooth | 47.0000 | 2.0000 | 2.0000 | 55.0000 | 64.0000 | 34.0000 | 64.0000 |
| `broad_continuous_001_003_length_0p021m` | broad_continuous | 56.0000 | 1.0000 | 1.0000 | 60.0000 | 62.0000 | 36.0000 | 62.0000 |
| `production_sampler_round3_001_length_0p028m` | production_sampler_round | 52.0000 | 39.0000 | 39.0000 | 51.0000 | 7.0000 | 37.6000 | 52.0000 |
| `production_sampler_round3_002_length_0p028m_shift_1p050` | production_sampler_round | 53.0000 | 48.0000 | 48.0000 | 49.0000 | 4.0000 | 40.4000 | 53.0000 |
| `local_bracketed_003_length_0p031m` | local_smooth | 62.0000 | 41.0000 | 41.0000 | 63.0000 | 3.0000 | 42.0000 | 63.0000 |
| `adaptive_combined_001_length_0p050m` | adaptive_combined | 63.0000 | 62.0000 | 62.0000 | 65.0000 | 1.0000 | 50.6000 | 65.0000 |
| `adaptive_combined_002_length_0p050m_shift_0p750` | adaptive_combined | 65.0000 | 64.0000 | 64.0000 | 64.0000 | 2.0000 | 51.8000 | 65.0000 |

## Interpretation

The active incumbent `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` is the best run under the current direct-permeability plus raw NMR objective, but its cross-stream ranks are ERT=8.00 and Taupe=29.00.
The best mean-rank compromise is `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` with mean rank 10.40 and worst rank 18.00.
This mismatch is evidence that the current permeability field should remain conditional on the unresolved stream gates rather than being reported as the final all-measurement inversion.

## Source Artefacts

- `nmr_candidate_bias_sensitivity_audit.csv`: active raw-theta NMR objective plus offset-robust NMR alternatives.
- `ert_candidate_discrimination_audit.csv`: provisional theta-to-log-resistivity residuals over projected ERT support.
- `taupe_candidate_discrimination_audit.csv`: baseline-normalized Taupe/TDR trend residuals over mapped A3/A4 EDZ-band support.
